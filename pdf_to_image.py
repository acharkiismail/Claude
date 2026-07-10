import argparse
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "libs"))

import fitz  # PyMuPDF


def pdf_to_image(input_file: str, output_file: str) -> None:
    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.is_file():
        sys.stdout.write(f"ERROR|message=input_file_not_found|file={input_path}\n")
        sys.stdout.flush()
        sys.exit(1)

    if input_path.suffix.lower() != ".pdf":
        sys.stdout.write(f"ERROR|message=input_not_a_pdf|file={input_path}\n")
        sys.stdout.flush()
        sys.exit(1)

    ext = output_path.suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        sys.stdout.write(f"ERROR|message=unsupported_output_format|ext={ext}|supported=.jpg,.jpeg,.png\n")
        sys.stdout.flush()
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        doc = fitz.open(str(input_path))
    except Exception as e:
        sys.stdout.write(f"ERROR|message=cannot_open_pdf|detail={e}\n")
        sys.stdout.flush()
        sys.exit(1)

    try:
        if doc.is_encrypted:
            sys.stdout.write(f"ERROR|message=pdf_encrypted|file={input_path}\n")
            sys.stdout.flush()
            sys.exit(1)

        if doc.page_count == 0:
            sys.stdout.write(f"ERROR|message=pdf_empty|file={input_path}\n")
            sys.stdout.flush()
            sys.exit(1)

        page = doc[0]
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        pixmap.save(str(output_path))
    except Exception as e:
        sys.stdout.write(f"ERROR|message=conversion_failed|detail={e}\n")
        sys.stdout.flush()
        sys.exit(1)
    finally:
        doc.close()

    sys.stdout.write(f"ok|output={output_path}\n")
    sys.stdout.flush()
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Convertit la première page d'un PDF en image"
    )
    parser.add_argument("--input-file", required=True, help="Chemin du fichier PDF")
    parser.add_argument("--output-file", required=True, help="Chemin du fichier image de sortie (.jpg ou .png)")

    args = parser.parse_args()
    pdf_to_image(args.input_file, args.output_file)


if __name__ == "__main__":
    main()
