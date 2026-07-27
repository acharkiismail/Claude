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


def flatten_pdf(input_file: str) -> None:
    """Aplatit un PDF en place : annotations et champs de formulaire deviennent du
    contenu permanent (comme si le PDF avait été imprimé), et la structure interne
    est nettoyée/reparée. Reste du texte/vectoriel, jamais rasterisé -> rapide."""
    input_path = Path(input_file)

    if not input_path.is_file():
        sys.stdout.write(f"ERROR|message=input_file_not_found|file={input_path}\n")
        sys.stdout.flush()
        sys.exit(1)

    if input_path.suffix.lower() != ".pdf":
        sys.stdout.write(f"ERROR|message=input_not_a_pdf|file={input_path}\n")
        sys.stdout.flush()
        sys.exit(1)

    doc = None
    tmp_path = input_path.with_suffix(f"{input_path.suffix}.tmp")

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

        page_count = doc.page_count

        # Convertit annotations/champs de formulaire en contenu permanent, exactement
        # comme si le PDF avait été imprimé : plus aucune interactivité, rendu figé
        doc.bake(annots=True, widgets=True)

        # Reconstruit les flux de contenu et purge les objets inutilisés (repare au
        # passage les PDF malformés), sans jamais re-rasteriser texte/vectoriel.
        # On ne peut pas sauvegarder un doc dans le fichier qu'il a ouvert
        # (limitation PyMuPDF) -> passage par un fichier temporaire puis remplacement
        doc.save(str(tmp_path), garbage=4, deflate=True, clean=True)
        doc.close()
        doc = None

        os.replace(str(tmp_path), str(input_path))

    except Exception as e:
        sys.stdout.write(f"ERROR|message=flatten_failed|detail={e}\n")
        sys.stdout.flush()
        sys.exit(1)
    finally:
        if doc:
            doc.close()
        if tmp_path.exists():
            tmp_path.unlink()

    sys.stdout.write(f"ok|file={input_path}|pages={page_count}\n")
    sys.stdout.flush()
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Aplatit un PDF en place (annotations/formulaires -> contenu permanent), "
                     "equivalent rapide d'un print-to-PDF, sans rasterisation"
    )
    parser.add_argument("--input-file", required=True, help="Chemin du PDF a aplatir (modifie en place)")

    args = parser.parse_args()
    flatten_pdf(args.input_file)


if __name__ == "__main__":
    main()
