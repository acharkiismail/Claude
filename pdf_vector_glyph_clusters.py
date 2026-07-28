"""Outil de diagnostic (pas pour Blue Prism) : quand le texte d'un PDF est en
fait dessine en vectoriel (contours de lettres convertis en courbes, aucun
objet texte reel), ce script regroupe les milliers de petites formes par
similarite visuelle (rendu en image, comparaison pixel), et produit une
planche-contact d'un exemplaire par groupe pour lecture visuelle une seule
fois. Sert a construire une table de correspondance forme -> vrai caractere
sans OCR.

Usage:
  python pdf_vector_glyph_clusters.py --input-file "chemin.pdf" --output-dir out --first-page 1 --last-page 5
"""
import argparse
import pickle
import sys
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

ZOOM = 10          # resolution de rendu de la page source
NORM = 18          # taille normalisee (NORM x NORM) de chaque forme pour comparaison
THRESH = 18.0       # distance L1 moyenne max pour considerer deux formes identiques
MAX_SIZE = 20.0     # taille max (pt, largeur ET hauteur) d'une forme pour etre consideree comme un
                    # caractere plutot qu'une bordure de tableau. Pas de taille min : un "I" ou un
                    # "-" peuvent faire moins de 1pt de large tout en etant un vrai caractere.

CELL = 70.0
IMG_H = 55.0
COLS = 12
SHEET_W = COLS * CELL


def collect_glyph_shapes(doc, first_page, last_page):
    """Retourne une liste de dicts: {page, bbox, vec} pour chaque forme candidate."""
    items = []
    for page_num in range(first_page, last_page + 1):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), colorspace=fitz.csGRAY)
        full_img = Image.frombytes("L", (pix.width, pix.height), pix.samples)

        drawings = page.get_drawings()
        for d in drawings:
            r = d["rect"]
            if r.width <= 0 or r.height <= 0 or r.width > MAX_SIZE or r.height > MAX_SIZE:
                continue
            pad = 0.15
            x0, y0 = (r.x0 - pad) * ZOOM, (r.y0 - pad) * ZOOM
            x1, y1 = (r.x1 + pad) * ZOOM, (r.y1 + pad) * ZOOM
            crop = full_img.crop((x0, y0, x1, y1)).resize((NORM, NORM), Image.LANCZOS)
            vec = list(crop.tobytes())
            items.append({"page": page_num, "bbox": (r.x0, r.y0, r.x1, r.y1), "vec": vec})
    return items


def dist(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def cluster_shapes(items):
    """Regroupe par similarite (greedy). Retourne clusters: liste de dicts
    {rep_vec, count, member_indices}. Ajoute 'cluster_id' a chaque item."""
    clusters = []  # [{rep_vec, count, indices}]
    for idx, it in enumerate(items):
        v = it["vec"]
        found = None
        for ci, c in enumerate(clusters):
            if dist(v, c["rep_vec"]) < THRESH:
                found = ci
                break
        if found is None:
            clusters.append({"rep_vec": v, "count": 1, "indices": [idx]})
            it["cluster_id"] = len(clusters) - 1
        else:
            clusters[found]["count"] += 1
            clusters[found]["indices"].append(idx)
            it["cluster_id"] = found
    return clusters


def build_contact_sheet(items, clusters, doc, output_dir):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    order = sorted(range(len(clusters)), key=lambda ci: -clusters[ci]["count"])

    max_per_sheet = 200
    sheet_idx = 1
    pos = 0
    remaining = len(order)

    def new_sheet(count):
        rows_needed = -(-count // COLS)
        d = fitz.open()
        p = d.new_page(width=SHEET_W, height=rows_needed * CELL + 30)
        p.insert_text((10, 18), "Chaque cellule = 1 groupe de formes. Etiquette = ID cluster | nb occurrences", fontsize=6)
        return d, p

    sheet_doc, sheet_page = new_sheet(min(remaining, max_per_sheet))
    per_sheet = 0

    for ci in order:
        if per_sheet >= max_per_sheet:
            out_file = output_path / f"clusters_sheet_{sheet_idx}.png"
            pix = sheet_page.get_pixmap(matrix=fitz.Matrix(3, 3))
            pix.save(str(out_file))
            sheet_doc.close()
            print(f"  -> {out_file}")
            sheet_idx += 1
            remaining -= max_per_sheet
            sheet_doc, sheet_page = new_sheet(min(remaining, max_per_sheet))
            per_sheet = 0

        col = per_sheet % COLS
        row = per_sheet // COLS
        x0 = col * CELL
        y0 = 30 + row * CELL

        c = clusters[ci]
        first_idx = c["indices"][0]
        it = items[first_idx]
        src_page = doc[it["page"]]
        bx0, by0, bx1, by1 = it["bbox"]
        pad = 0.3
        clip = fitz.Rect(bx0 - pad, by0 - pad, bx1 + pad, by1 + pad)
        glyph_pix = src_page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=clip)

        img_rect = fitz.Rect(x0 + 2, y0, x0 + CELL - 2, y0 + IMG_H)
        sheet_page.insert_image(img_rect, pixmap=glyph_pix)
        sheet_page.insert_text((x0 + 2, y0 + IMG_H + 12), f"#{ci} x{c['count']}", fontsize=7)

        per_sheet += 1

    out_file = output_path / f"clusters_sheet_{sheet_idx}.png"
    pix = sheet_page.get_pixmap(matrix=fitz.Matrix(3, 3))
    pix.save(str(out_file))
    sheet_doc.close()
    print(f"  -> {out_file}")


def main(input_file, output_dir, first_page, last_page):
    input_path = Path(input_file)
    if not input_path.is_file():
        print(f"Fichier introuvable: {input_path}")
        sys.exit(1)

    doc = fitz.open(str(input_path))
    end_page = last_page if last_page is not None else doc.page_count - 1
    end_page = min(end_page, doc.page_count - 1)

    print(f"Extraction des formes candidates pages {first_page + 1} a {end_page + 1}...")
    items = collect_glyph_shapes(doc, first_page, end_page)
    print(f"Formes candidates: {len(items)}")

    clusters = cluster_shapes(items)
    print(f"Clusters trouves: {len(clusters)}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # sauvegarde items + clusters pour l'etape suivante (decodage)
    with open(output_path / "clusters_data.pkl", "wb") as f:
        pickle.dump({"items": items, "clusters": [{"count": c["count"], "indices": c["indices"]} for c in clusters]}, f)
    print(f"Donnees sauvegardees -> {output_path / 'clusters_data.pkl'}")

    build_contact_sheet(items, clusters, doc, output_dir)
    doc.close()
    print("Termine.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Regroupe les formes vectorielles d'un PDF par similarite visuelle (sans OCR)"
    )
    ap.add_argument("--input-file", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--first-page", type=int, default=0)
    ap.add_argument("--last-page", type=int, default=None)
    args = ap.parse_args()
    main(args.input_file, args.output_dir, args.first_page, args.last_page)
