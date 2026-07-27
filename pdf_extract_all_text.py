"""Outil de diagnostic (pas pour Blue Prism) : extrait tout le texte de toutes
les pages d'un PDF (get_text standard) dans un seul fichier, page par page,
pour voir d'un coup d'oeil quelles pages sont lisibles et lesquelles sortent
en charabia (encodage de police casse).

Usage: python pdf_extract_all_text.py --input-file "chemin.pdf" --output-file dump.txt
"""
import argparse
import sys
from pathlib import Path

import fitz  # PyMuPDF


def extract_all(input_file: str, output_file: str) -> None:
    input_path = Path(input_file)
    if not input_path.is_file():
        print(f"Fichier introuvable: {input_path}")
        sys.exit(1)

    output_path = Path(output_file)

    doc = fitz.open(str(input_path))

    with open(output_path, "w", encoding="utf-8") as f:
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text()
            f.write(f"\n{'=' * 60}\n")
            f.write(f"PAGE {page_num + 1} / {doc.page_count}  ({len(text)} caracteres)\n")
            f.write(f"{'=' * 60}\n")
            f.write(text)
            f.write("\n")

    doc.close()
    print(f"Termine -> {output_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Extrait tout le texte de toutes les pages d'un PDF dans un seul fichier"
    )
    ap.add_argument("--input-file", required=True, help="Chemin du PDF a analyser")
    ap.add_argument("--output-file", required=True, help="Chemin du fichier texte de sortie")
    args = ap.parse_args()
    extract_all(args.input_file, args.output_file)
