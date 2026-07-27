"""Outil de diagnostic (pas pour Blue Prism) : verifie si l'encodage de texte
"charabia" d'un PDF est au moins COHERENT (meme glyph_id -> toujours le meme
caractere), ce qui permettrait de construire une table de correspondance
glyph_id -> vrai caractere sans passer par l'OCR/IDP.

Usage: python pdf_probe_glyphs.py --input-file "chemin.pdf" --page 0
"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

import fitz  # PyMuPDF


def probe_glyphs(input_file: str, page_num: int = 0, max_samples: int = 80) -> None:
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
    traces = page.get_texttrace()

    # glyph_id -> ensemble des caracteres unicode observes pour ce glyph
    glyph_to_chars = defaultdict(set)
    samples = []

    for span in traces:
        font_name = span.get("font", "?")
        for code, glyph_id, origin, bbox in span["chars"]:
            ch = chr(code) if code else ""
            glyph_to_chars[(font_name, glyph_id)].add(ch)
            if len(samples) < max_samples:
                samples.append((font_name, glyph_id, ch, bbox))

    print(f"Page analysee        : {page_num + 1}")
    print(f"Polices rencontrees   : {sorted(set(f for f, _ in glyph_to_chars))}")
    print(f"Glyphes uniques       : {len(glyph_to_chars)}")
    print()

    inconsistants = {k: v for k, v in glyph_to_chars.items() if len(v) > 1}
    if inconsistants:
        print(f"INCOHERENT : {len(inconsistants)} glyph_id donnent des caracteres differents selon l'endroit")
        for (font, gid), chars in list(inconsistants.items())[:10]:
            print(f"  police={font} glyph_id={gid} -> {chars}")
        print("-> le mapping n'est pas fiable, la table de correspondance ne marcherait pas")
    else:
        print("COHERENT : chaque glyph_id donne toujours le meme caractere (bon signe)")
        print("-> une table de correspondance glyph_id -> vrai caractere est possible")

    print()
    print(f"Echantillon des {len(samples)} premiers caracteres (police, glyph_id, caractere_extrait, bbox):")
    for font, gid, ch, bbox in samples:
        printable = ch if ch.isprintable() else repr(ch)
        print(f"  police={font:20s} glyph_id={gid:4d}  extrait={printable!r:8s}  bbox=({bbox[0]:.1f},{bbox[1]:.1f},{bbox[2]:.1f},{bbox[3]:.1f})")

    doc.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Verifie si le charabia extrait d'un PDF correspond a un mapping glyph_id coherent"
    )
    ap.add_argument("--input-file", required=True, help="Chemin du PDF a analyser")
    ap.add_argument("--page", type=int, default=0, help="Numero de page a analyser, 0-indexe (defaut: 0)")
    ap.add_argument("--max-samples", type=int, default=80, help="Nombre max de caracteres a afficher (defaut: 80)")
    args = ap.parse_args()
    probe_glyphs(args.input_file, args.page, args.max_samples)
