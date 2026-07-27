"""Outil de diagnostic (pas pour Blue Prism) : verifie si un PDF a une vraie
couche de texte extractible, et affiche les positions (x0,y0,x1,y1) des mots
d'une page pour calibrer un futur parseur base sur les colonnes.

Usage: python pdf_probe_text.py --input-file "chemin.pdf" --page 0
"""
import argparse
import sys
from pathlib import Path

import fitz  # PyMuPDF


def probe(input_file: str, page_num: int = 0, max_words: int = 60) -> None:
    input_path = Path(input_file)
    if not input_path.is_file():
        print(f"Fichier introuvable: {input_path}")
        sys.exit(1)

    doc = fitz.open(str(input_path))
    if page_num >= doc.page_count:
        print(f"Le PDF n'a que {doc.page_count} page(s), --page {page_num} n'existe pas")
        doc.close()
        sys.exit(1)

    page = doc[page_num]
    text = page.get_text()
    words = page.get_text("words")  # (x0, y0, x1, y1, texte, block_no, line_no, word_no)

    print(f"Pages totales      : {doc.page_count}")
    print(f"Page analysee       : {page_num + 1}")
    print(f"Taille de la page   : {page.rect.width:.0f} x {page.rect.height:.0f}")
    print(f"Caracteres extraits : {len(text)}")
    print(f"Mots extraits       : {len(words)}")
    print()

    if len(text.strip()) == 0:
        print("AUCUN TEXTE EXTRACTIBLE -> c'est probablement une image scannee, il faudra de l'OCR/IDP")
    else:
        print(f"Echantillon des {min(max_words, len(words))} premiers mots (x0, y0, x1, y1, texte):")
        for w in words[:max_words]:
            x0, y0, x1, y1, word = w[0], w[1], w[2], w[3], w[4]
            print(f"  ({x0:7.1f}, {y0:7.1f}, {x1:7.1f}, {y1:7.1f})  {word}")

    doc.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Verifie si un PDF a une vraie couche de texte et affiche les positions des mots"
    )
    ap.add_argument("--input-file", required=True, help="Chemin du PDF a analyser")
    ap.add_argument("--page", type=int, default=0, help="Numero de page a analyser, 0-indexe (defaut: 0)")
    ap.add_argument("--max-words", type=int, default=60, help="Nombre max de mots a afficher (defaut: 60)")
    args = ap.parse_args()
    probe(args.input_file, args.page, args.max_words)
