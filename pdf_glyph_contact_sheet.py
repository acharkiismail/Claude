"""Outil de diagnostic (pas pour Blue Prism) : decoupe chaque glyphe unique
(police, glyph_id) rencontre dans un PDF en petite image agrandie, et les
assemble dans une planche-contact avec etiquette. Sert a lire visuellement
(une seule fois) ce que chaque glyphe represente vraiment, pour construire
une table de correspondance glyph_id -> vrai caractere sans OCR/IDP.

Usage: python pdf_glyph_contact_sheet.py --input-file "chemin.pdf" --output-dir out
"""
import argparse
import sys
from pathlib import Path

import fitz  # PyMuPDF

ZOOM = 12.0        # grossissement du glyphe source (les caracteres sont minuscules dans le PDF)
CELL_W = 70.0       # largeur d'une cellule dans la planche-contact
CELL_H = 90.0       # hauteur d'une cellule (image + etiquette)
IMG_H = 60.0        # hauteur reservee a l'image du glyphe dans la cellule
COLS = 12           # nombre de colonnes de la grille
SHEET_W = COLS * CELL_W


def build_contact_sheets(input_file: str, output_dir: str, first_page: int = 0, last_page: int = None) -> None:
    input_path = Path(input_file)
    if not input_path.is_file():
        print(f"Fichier introuvable: {input_path}")
        sys.exit(1)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(input_path))
    end_page = last_page if last_page is not None else doc.page_count - 1
    end_page = min(end_page, doc.page_count - 1)

    # (font, glyph_id) -> (page_num, bbox) de la premiere occurrence
    first_seen = {}
    for page_num in range(first_page, end_page + 1):
        page = doc[page_num]
        for span in page.get_texttrace():
            font_name = span.get("font", "?")
            for code, glyph_id, origin, bbox in span["chars"]:
                key = (font_name, glyph_id)
                if key not in first_seen:
                    first_seen[key] = (page_num, bbox)

    fonts = sorted(set(f for f, _ in first_seen))
    font_short = {f: chr(ord('A') + i) for i, f in enumerate(fonts)}

    print(f"Polices trouvees ({len(fonts)}):")
    for f in fonts:
        print(f"  {font_short[f]} = {f}")
    print(f"Glyphes uniques a decouper: {len(first_seen)}")

    items = sorted(first_seen.items(), key=lambda kv: (font_short[kv[0][0]], kv[0][1]))

    per_sheet = 0
    max_per_sheet = 200  # limite pour garder chaque planche lisible
    sheet_idx = 1
    sheet_doc = None
    sheet_page = None

    def new_sheet(count: int):
        nonlocal sheet_doc, sheet_page, per_sheet
        rows_needed = -(-count // COLS)
        sheet_doc = fitz.open()
        sheet_page = sheet_doc.new_page(width=SHEET_W, height=rows_needed * CELL_H + 40)
        sheet_page.insert_text((10, 20), "Legende polices: " + ", ".join(f"{font_short[f]}={f}" for f in fonts), fontsize=6)
        per_sheet = 0

    remaining = len(items)
    new_sheet(min(remaining, max_per_sheet))

    for (font_name, glyph_id), (page_num, bbox) in items:
        if per_sheet >= max_per_sheet:
            out_file = output_path / f"glyphs_sheet_{sheet_idx}.png"
            pix = sheet_page.get_pixmap(matrix=fitz.Matrix(3, 3))
            pix.save(str(out_file))
            sheet_doc.close()
            print(f"  -> {out_file}")
            sheet_idx += 1
            remaining -= max_per_sheet
            new_sheet(min(remaining, max_per_sheet))

        col = per_sheet % COLS
        row = per_sheet // COLS
        x0 = col * CELL_W
        y0 = 40 + row * CELL_H

        src_page = doc[page_num]
        pad = 1.0
        clip = fitz.Rect(bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad)
        glyph_pix = src_page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=clip)

        img_rect = fitz.Rect(x0 + 2, y0, x0 + CELL_W - 2, y0 + IMG_H)
        sheet_page.insert_image(img_rect, pixmap=glyph_pix)

        label = f"{font_short[font_name]}|{glyph_id}"
        sheet_page.insert_text((x0 + 2, y0 + IMG_H + 12), label, fontsize=7)

        per_sheet += 1

    out_file = output_path / f"glyphs_sheet_{sheet_idx}.png"
    pix = sheet_page.get_pixmap(matrix=fitz.Matrix(3, 3))
    pix.save(str(out_file))
    sheet_doc.close()
    print(f"  -> {out_file}")

    doc.close()
    print("Termine.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Decoupe chaque glyphe unique d'un PDF en planche-contact pour lecture visuelle"
    )
    ap.add_argument("--input-file", required=True, help="Chemin du PDF a analyser")
    ap.add_argument("--output-dir", required=True, help="Dossier de sortie pour les planches-contact PNG")
    ap.add_argument("--first-page", type=int, default=0, help="Premiere page a scanner, 0-indexee (defaut: 0)")
    ap.add_argument("--last-page", type=int, default=None, help="Derniere page a scanner, 0-indexee (defaut: derniere page du PDF)")
    args = ap.parse_args()
    build_contact_sheets(args.input_file, args.output_dir, args.first_page, args.last_page)
