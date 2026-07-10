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

    if output_path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
        sys.stdout.write(
            f"ERROR|message=unsupported_output_format|ext={output_path.suffix}|supported=.jpg,.jpeg,.png\n"
        )
        sys.stdout.flush()
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = None
    combined_doc = None

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
        page_width = max(doc[i].rect.width for i in range(page_count))
        total_height = sum(doc[i].rect.height for i in range(page_count))

        # Crée un PDF temporaire d'une seule page contenant toutes les pages empilées
        combined_doc = fitz.open()
        combined_page = combined_doc.new_page(width=page_width, height=total_height)

        y_offset = 0.0
        for i in range(page_count):
            src_rect = doc[i].rect
            target_rect = fitz.Rect(0, y_offset, src_rect.width, y_offset + src_rect.height)
            combined_page.show_pdf_page(target_rect, doc, i)
            y_offset += src_rect.height

        # Render en image à 2x (144 DPI)
        pix = combined_page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        pix.save(str(output_path))

    except Exception as e:
        sys.stdout.write(f"ERROR|message=conversion_failed|detail={e}\n")
        sys.stdout.flush()
        sys.exit(1)
    finally:
        if combined_doc:
            combined_doc.close()
        if doc:
            doc.close()

    sys.stdout.write(f"ok|output={output_path}|pages={page_count}\n")
    sys.stdout.flush()
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Convertit toutes les pages d'un PDF en une seule image"
    )
    parser.add_argument("--input-file", required=True, help="Chemin du fichier PDF")
    parser.add_argument("--output-file", required=True, help="Chemin du fichier image de sortie (.jpg ou .png)")

    args = parser.parse_args()
    pdf_to_image(args.input_file, args.output_file)


if __name__ == "__main__":
    main()
