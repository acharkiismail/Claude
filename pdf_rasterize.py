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


def rasterize_pdf(input_file: str, output_file: str, dpi: int = 200) -> None:
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

    if output_path.suffix.lower() != ".pdf":
        sys.stdout.write(f"ERROR|message=output_must_be_pdf|file={output_path}\n")
        sys.stdout.flush()
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    src = None
    out = None

    try:
        src = fitz.open(str(input_path))

        if src.is_encrypted:
            sys.stdout.write(f"ERROR|message=pdf_encrypted|file={input_path}\n")
            sys.stdout.flush()
            sys.exit(1)

        if src.page_count == 0:
            sys.stdout.write(f"ERROR|message=pdf_empty|file={input_path}\n")
            sys.stdout.flush()
            sys.exit(1)

        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        out = fitz.open()

        for page in src:
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            jpeg_bytes = pix.tobytes("jpeg", jpg_quality=75)
            new_page = out.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_image(new_page.rect, stream=jpeg_bytes)

        out.save(str(output_path), deflate=True)
        page_count = src.page_count

        size_mb = output_path.stat().st_size / (1024 * 1024)
        if size_mb > 10:
            sys.stdout.write(
                f"WARNING|message=file_size_exceeded|size_mb={size_mb:.1f}|output={output_path}|pages={page_count}\n"
            )
            sys.stdout.flush()
            sys.exit(0)

    except Exception as e:
        sys.stdout.write(f"ERROR|message=conversion_failed|detail={e}\n")
        sys.stdout.flush()
        sys.exit(1)
    finally:
        if out:
            out.close()
        if src:
            src.close()

    sys.stdout.write(f"ok|output={output_path}|pages={page_count}\n")
    sys.stdout.flush()
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Rasterise un PDF pour supprimer la couche texte (pour IDP)"
    )
    parser.add_argument("--input-file", required=True, help="Chemin du PDF source")
    parser.add_argument("--output-file", required=True, help="Chemin du PDF rasterisé en sortie")
    parser.add_argument("--dpi", type=int, default=200, help="Résolution en DPI (défaut: 200)")

    args = parser.parse_args()
    rasterize_pdf(args.input_file, args.output_file, args.dpi)


if __name__ == "__main__":
    main()
