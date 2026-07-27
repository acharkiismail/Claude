"""Outil de diagnostic/extraction (pas encore pour Blue Prism) : contourne un
encodage de police casse en rendant chaque page en image et en lisant le
texte par OCR (Tesseract), au lieu de faire confiance a la couche de texte
du PDF. Ecrit a la fois un texte brut par page ET les positions par mot
(x0,y0,x1,y1,confiance,texte) en points PDF, utilisables pour reconstruire
un tableau par colonnes plus tard.

Necessite Tesseract OCR installe sur le poste (+ le paquet de langue fra) :
  - Windows : https://github.com/UB-Mannheim/tesseract/wiki (installeur avec fra)
  - Si tesseract.exe n'est pas dans le PATH, utiliser --tesseract-cmd

Usage:
  python pdf_ocr_extract.py --input-file "chemin.pdf" --output-file dump.txt
"""
import argparse
import sys
from pathlib import Path

import fitz  # PyMuPDF

try:
    import pytesseract
    from PIL import Image
except ImportError as e:
    print(f"ERROR: dependance manquante ({e}). Installe avec: pip install pytesseract pillow")
    sys.exit(1)


def ocr_extract(input_file: str, output_file: str, first_page: int = 0, last_page: int = None,
                 dpi: int = 300, lang: str = "fra", tesseract_cmd: str = None) -> None:
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    input_path = Path(input_file)
    if not input_path.is_file():
        print(f"Fichier introuvable: {input_path}")
        sys.exit(1)

    try:
        pytesseract.get_tesseract_version()
    except Exception as e:
        print(f"Tesseract introuvable ou mal configure: {e}")
        print("Installe Tesseract OCR (avec le paquet de langue fra) et/ou passe --tesseract-cmd")
        sys.exit(1)

    doc = fitz.open(str(input_path))
    end_page = last_page if last_page is not None else doc.page_count - 1
    end_page = min(end_page, doc.page_count - 1)

    scale = dpi / 72.0  # pour reconvertir les positions pixels -> points PDF

    with open(output_file, "w", encoding="utf-8") as f:
        for page_num in range(first_page, end_page + 1):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

            data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)

            f.write(f"\n{'=' * 70}\n")
            f.write(f"PAGE {page_num + 1} / {doc.page_count}\n")
            f.write(f"{'=' * 70}\n")

            words = []
            for i, word in enumerate(data["text"]):
                if not word.strip():
                    continue
                x0 = data["left"][i] / scale
                y0 = data["top"][i] / scale
                x1 = (data["left"][i] + data["width"][i]) / scale
                y1 = (data["top"][i] + data["height"][i]) / scale
                words.append((x0, y0, x1, y1, data["conf"][i], word))

            # Regroupe par ligne VISUELLE (position Y), pas par bloc Tesseract : sur un
            # tableau a colonnes espacees, Tesseract segmente parfois par colonne plutot
            # que par ligne, ce qui donnerait un apercu texte dans le mauvais ordre.
            row_tol = 3.0
            rows = []
            for w in sorted(words, key=lambda w: w[1]):
                placed = False
                for row in rows:
                    if abs(row[0][1] - w[1]) <= row_tol:
                        row.append(w)
                        placed = True
                        break
                if not placed:
                    rows.append([w])

            f.write("\n-- Texte brut (regroupe par ligne visuelle, gauche a droite) --\n")
            for row in rows:
                row_sorted = sorted(row, key=lambda w: w[0])
                f.write(" ".join(w[5] for w in row_sorted) + "\n")

            f.write("\n-- Mots avec positions (x0, y0, x1, y1 en points PDF, confiance, texte) --\n")
            for x0, y0, x1, y1, conf, word in sorted(words, key=lambda w: (w[1], w[0])):
                f.write(f"  ({x0:7.1f}, {y0:7.1f}, {x1:7.1f}, {y1:7.1f})  conf={conf:>5}  {word}\n")

            print(f"Page {page_num + 1}/{end_page + 1} OCR terminee ({len(rows)} lignes, {len(words)} mots)")

    doc.close()
    print(f"Termine -> {output_file}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Extrait le texte d'un PDF par OCR (contourne un encodage de police casse)"
    )
    ap.add_argument("--input-file", required=True, help="Chemin du PDF a analyser")
    ap.add_argument("--output-file", required=True, help="Chemin du fichier texte de sortie")
    ap.add_argument("--first-page", type=int, default=0, help="Premiere page a traiter, 0-indexee (defaut: 0)")
    ap.add_argument("--last-page", type=int, default=None, help="Derniere page a traiter, 0-indexee (defaut: derniere page)")
    ap.add_argument("--dpi", type=int, default=300, help="Resolution de rendu avant OCR (defaut: 300)")
    ap.add_argument("--lang", default="fra", help="Langue Tesseract (defaut: fra)")
    ap.add_argument("--tesseract-cmd", default=None, help="Chemin vers tesseract.exe si pas dans le PATH")
    args = ap.parse_args()
    ocr_extract(args.input_file, args.output_file, args.first_page, args.last_page,
                args.dpi, args.lang, args.tesseract_cmd)
