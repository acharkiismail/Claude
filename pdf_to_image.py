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

        matrix = fitz.Matrix(2, 2)
        pixmaps = [doc[i].get_pixmap(matrix=matrix, alpha=False) for i in range(doc.page_count)]

        # Colle toutes les pages verticalement en un seul bloc de pixels
        max_width = max(p.width for p in pixmaps)
        total_height = sum(p.height for p in pixmaps)
        n = 3  # RGB, pas d'alpha

        samples = bytearray()
        white_row_padding = bytes([255, 255, 255])
        for pix in pixmaps:
            if pix.width == max_width:
                samples += pix.samples
            else:
                padding = white_row_padding * (max_width - pix.width)
                for y in range(pix.height):
                    samples += pix.samples[y * pix.width * n : (y + 1) * pix.width * n]
                    samples += padding

        combined = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, max_width, total_height), bytes(samples))
        combined.save(str(output_path))

    except Exception as e:
        sys.stdout.write(f"ERROR|message=conversion_failed|detail={e}\n")
        sys.stdout.flush()
        sys.exit(1)
    finally:
        doc.close()

    sys.stdout.write(f"ok|output={output_path}|pages={len(pixmaps)}\n")
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
