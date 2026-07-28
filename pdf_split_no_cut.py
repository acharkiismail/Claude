import argparse
import sys
import os
from pathlib import Path

try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "libs"))
    import fitz  # PyMuPDF
except Exception as _e:
    sys.stdout.write(f"ERROR|message=import_failed|detail={_e}\n")
    sys.stdout.flush()
    sys.exit(1)


def get_occupied_bands(page, merge_tolerance: float = 1.0, bg_threshold: float = 0.95,
                        shape_height_ratio: float = 0.3) -> list:
    """Zones Y occupées par du texte ou des formes (hors arrière-plan plein écran et
    hors grands cadres/bordures), fusionnées en bandes continues : ce sont les seules
    frontières où couper sans trancher une ligne de texte ou une rangée de tableau.
    Une grande forme (ex: le cadre d'un tableau) n'est pas du contenu ligne par ligne :
    la traiter comme une bande empêcherait toute coupe sur sa hauteur, donc on ignore
    les formes qui dépassent shape_height_ratio de la hauteur de la page."""
    page_w, page_h = page.rect.width, page.rect.height
    intervals = []

    d = page.get_text("dict")
    for block in d["blocks"]:
        for line in block.get("lines", []):
            bbox = line["bbox"]
            intervals.append((bbox[1], bbox[3]))

    for dr in page.get_drawings():
        r = dr["rect"]
        if r.height <= 0:
            continue
        is_full_page_bg = (r.width >= bg_threshold * page_w and r.height >= bg_threshold * page_h)
        is_oversized_shape = r.height >= shape_height_ratio * page_h
        if is_full_page_bg or is_oversized_shape:
            continue
        intervals.append((r.y0, r.y1))

    if not intervals:
        return []

    intervals.sort()
    merged = [list(intervals[0])]
    for y0, y1 in intervals[1:]:
        if y0 <= merged[-1][1] + merge_tolerance:
            merged[-1][1] = max(merged[-1][1], y1)
        else:
            merged.append([y0, y1])
    return [tuple(m) for m in merged]


def find_safe_cut(target_y: float, bands: list, page_height: float) -> float:
    """Déplace target_y sur la frontière d'une bande occupée la plus proche,
    jamais à l'intérieur d'une bande."""
    for idx, (y0, y1) in enumerate(bands):
        if y0 <= target_y <= y1:
            before = bands[idx - 1][1] if idx > 0 else 0
            after = bands[idx + 1][0] if idx < len(bands) - 1 else page_height
            if (target_y - y0) <= (y1 - target_y):
                return (before + y0) / 2
            return (y1 + after) / 2
    return target_y


def get_header_clip(page, header_y_percent: float) -> "fitz.Rect":
    """En-tete = du tout haut de la page (y=0) jusqu'a la fin de la rangee de texte
    visee par header_y_percent (ex: la ligne des titres de colonnes 'NO DE COMPTE /
    DESIGNATION DE L'IMMEUBLE / ...'). header_y_percent doit tomber n'importe ou DANS
    cette rangee : on etend ensuite jusqu'a la fin reelle de son bloc de contenu, pour
    ne jamais couper cette ligne en plein milieu ni s'arreter juste avant sa fin."""
    h, w = page.rect.height, page.rect.width
    bands = get_occupied_bands(page)
    target_y = h * header_y_percent
    bottom = target_y
    for y0, y1 in bands:
        if y0 <= target_y <= y1:
            bottom = y1
            break
    return fitz.Rect(0, 0, w, bottom)


def split_pdf_no_cut(input_file: str, output_dir: str, parts_per_page: int = 4,
                      repeat_header: bool = False, header_page_index: int = 1,
                      header_y_percent: float = 0.12) -> None:
    input_path = Path(input_file)

    if not input_path.is_file():
        sys.stdout.write(f"ERROR|message=input_file_not_found|file={input_path}\n")
        sys.stdout.flush()
        sys.exit(1)

    if input_path.suffix.lower() != ".pdf":
        sys.stdout.write(f"ERROR|message=input_not_a_pdf|file={input_path}\n")
        sys.stdout.flush()
        sys.exit(1)

    if parts_per_page < 1:
        sys.stdout.write(f"ERROR|message=invalid_parts_per_page|value={parts_per_page}\n")
        sys.stdout.flush()
        sys.exit(1)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    doc = None
    part_count = 0

    try:
        doc = fitz.open(str(input_path))

        if doc.is_encrypted:
            sys.stdout.write(f"ERROR|message=pdf_encrypted|file={input_path}\n")
            sys.stdout.flush()
            sys.exit(1)

        if doc.page_count == 0:
            sys.stdout.write(f"ERROR|message=pdf_empty|file={input_path}\n")
            sys.stdout.flush()
            sys.exit(1)

        # En-tete capture une seule fois, depuis une page de reference explicite
        # (header_page_index, 0-indexee), puis redessine au-dessus de toutes les
        # parts suivantes -- sauf la toute premiere part de cette page de reference,
        # qui contient deja l'en-tete reel puisqu'elle commence en haut de la page
        cached_header_page_idx = None
        cached_header_clip = None
        cached_header_height = 0.0
        if repeat_header:
            if not (0 <= header_page_index < doc.page_count):
                sys.stdout.write(f"ERROR|message=invalid_header_page_index|value={header_page_index}|page_count={doc.page_count}\n")
                sys.stdout.flush()
                sys.exit(1)
            cached_header_page_idx = header_page_index
            cached_header_clip = get_header_clip(doc[header_page_index], header_y_percent)
            cached_header_height = cached_header_clip.height

        for page_idx, page in enumerate(doc):
            h, w = page.rect.height, page.rect.width
            bands = get_occupied_bands(page)

            # Points de coupe théoriques (ex: parts_per_page=4 -> [0, 25%, 50%, 75%, 100%])
            raw_cuts = [h * k / parts_per_page for k in range(parts_per_page + 1)]
            # Les bords (0 et h) restent fixes, seules les coupes internes sont ajustées
            # pour tomber entre deux bandes occupées plutôt qu'au milieu d'une ligne
            candidates = [0.0] + [find_safe_cut(c, bands, h) for c in raw_cuts[1:-1]] + [h]

            # Si une bande de contenu couvre plusieurs coupes théoriques (tableau dense,
            # sans espace vide), find_safe_cut les ramène toutes vers la même frontière :
            # on ne garde que les coupes strictement croissantes pour éviter un rectangle
            # de hauteur nulle (page produira alors moins de parts_per_page bandes)
            cuts = [candidates[0]]
            for c in candidates[1:]:
                c = min(max(c, 0.0), h)
                if c > cuts[-1] + 1e-6:
                    cuts.append(c)
            if cuts[-1] < h:
                cuts.append(h)

            for k in range(len(cuts) - 1):
                y0, y1 = cuts[k], cuts[k + 1]
                clip = fitz.Rect(0, y0, w, y1)
                base_name = f"page{page_idx + 1}_part{k + 1}"

                # La toute premiere part de la page de reference contient deja l'en-tete
                # reel (elle part du haut de cette page) -> pas besoin de le recoller dessus
                attach_header = repeat_header and not (page_idx == cached_header_page_idx and k == 0)

                # Export PDF (page recadrée, garde le texte sélectionnable)
                new_doc = fitz.open()
                if attach_header:
                    total_h = cached_header_height + (y1 - y0)
                    new_page = new_doc.new_page(width=w, height=total_h)
                    new_page.show_pdf_page(
                        fitz.Rect(0, 0, w, cached_header_height),
                        doc, cached_header_page_idx, clip=cached_header_clip,
                    )
                    new_page.show_pdf_page(
                        fitz.Rect(0, cached_header_height, w, total_h),
                        doc, page_idx, clip=clip,
                    )
                else:
                    new_page = new_doc.new_page(width=w, height=y1 - y0)
                    new_page.show_pdf_page(new_page.rect, doc, page_idx, clip=clip)
                new_doc.save(str(output_path / f"{base_name}.pdf"))
                new_doc.close()

                part_count += 1

        page_count = doc.page_count

    except Exception as e:
        sys.stdout.write(f"ERROR|message=split_failed|detail={e}\n")
        sys.stdout.flush()
        sys.exit(1)
    finally:
        if doc:
            doc.close()

    sys.stdout.write(f"ok|output_dir={output_path}|pages={page_count}|parts={part_count}\n")
    sys.stdout.flush()
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Decoupe chaque page d'un PDF en bandes horizontales sans jamais couper "
                     "une ligne de texte ou une rangee de tableau"
    )
    parser.add_argument("--input-file", required=True, help="Chemin du PDF à découper")
    parser.add_argument("--output-dir", required=True, help="Dossier de sortie pour les bandes PDF")
    parser.add_argument("--parts-per-page", type=int, default=4, help="Nombre de bandes par page (défaut: 4)")
    parser.add_argument("--repeat-header", action="store_true",
                         help="Capture l'en-tete une fois sur header-page-index et le recolle "
                              "au-dessus de toutes les autres parts")
    parser.add_argument("--header-page-index", type=int, default=1,
                         help="Page de reference pour l'en-tete, 0-indexee (défaut: 1 = la 2e page)")
    parser.add_argument("--header-y-percent", type=float, default=0.12,
                         help="Position (en %% de la hauteur de page) qui doit tomber n'importe ou "
                              "dans la ligne des titres de colonnes -- l'en-tete est etendu "
                              "automatiquement jusqu'a la fin reelle de cette ligne (défaut: 0.12)")

    args = parser.parse_args()
    split_pdf_no_cut(args.input_file, args.output_dir, args.parts_per_page,
                      args.repeat_header, args.header_page_index, args.header_y_percent)


if __name__ == "__main__":
    main()
