import argparse
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "libs"))

import fitz  # PyMuPDF — doit être après le sys.path.insert


def pdf_to_images(
    input_file: str,
    output_folder: str,
    fmt: str = "jpeg",
    dpi: int = 150,
    page: int = None,
) -> None:
    input_path = Path(input_file)
    output_path = Path(output_folder)

    if not input_path.is_file():
        sys.stdout.write(f"ERROR|message=input_file_not_found|file={input_path}\n")
        sys.stdout.flush()
        sys.exit(1)

    if input_path.suffix.lower() != ".pdf":
        sys.stdout.write(f"ERROR|message=input_not_a_pdf|file={input_path}\n")
        sys.stdout.flush()
        sys.exit(1)

    output_path.mkdir(parents=True, exist_ok=True)

    ext = "jpg" if fmt == "jpeg" else "png"

    try:
        doc = fitz.open(str(input_path))
    except Exception as e:
        sys.stdout.write(f"ERROR|message=cannot_open_pdf|detail={e}\n")
        sys.stdout.flush()
        sys.exit(1)

    if doc.is_encrypted:
        doc.close()
        sys.stdout.write(f"ERROR|message=pdf_encrypted|file={input_path}\n")
        sys.stdout.flush()
        sys.exit(1)

    total_pages = doc.page_count
    if total_pages == 0:
        doc.close()
        sys.stdout.write(f"ERROR|message=pdf_empty|file={input_path}\n")
        sys.stdout.flush()
        sys.exit(1)

    if page is not None:
        if page < 1 or page > total_pages:
            doc.close()
            sys.stdout.write(
                f"ERROR|message=page_out_of_range|page={page}|total={total_pages}\n"
            )
            sys.stdout.flush()
            sys.exit(1)
        pages_to_render = [page - 1]  # fitz utilise l'index 0
    else:
        pages_to_render = list(range(total_pages))

    zoom = dpi / 72  # résolution de base de fitz = 72 DPI
    matrix = fitz.Matrix(zoom, zoom)

    output_files = []
    failed_pages = []

    try:
        for idx in pages_to_render:
            page_num = idx + 1
            out_file = output_path / f"page_{page_num:03d}.{ext}"
            try:
                page_obj = doc[idx]
                pixmap = page_obj.get_pixmap(matrix=matrix, alpha=False)
                pixmap.save(str(out_file))
                output_files.append(str(out_file))
            except Exception as e:
                failed_pages.append(f"PAGE_{page_num}:{e}")
    finally:
        doc.close()

    if not output_files:
        sys.stdout.write(
            f"ERROR|message=no_pages_converted|pages_tried={len(pages_to_render)}|"
            f"failed={len(failed_pages)}\n"
        )
        sys.stdout.flush()
        sys.exit(1)

    files_join = "###".join(output_files)

    if failed_pages:
        failed_join = "###".join(failed_pages)
        sys.stdout.write(
            f"ERROR|message=partial_success|output_folder={output_path}|"
            f"pages_converted={len(output_files)}|pages_failed={len(failed_pages)}|"
            f"files={files_join}|failed_list={failed_join}\n"
        )
        sys.stdout.flush()
        sys.exit(1)

    sys.stdout.write(
        f"ok|output_folder={output_path}|pages={len(output_files)}|files={files_join}\n"
    )
    sys.stdout.flush()
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Convertit un fichier PDF en images JPEG ou PNG"
    )
    parser.add_argument(
        "--input-file",
        required=True,
        help="Chemin du fichier PDF à convertir",
    )
    parser.add_argument(
        "--output-folder",
        required=True,
        help="Dossier de destination pour les images générées",
    )
    parser.add_argument(
        "--format",
        choices=["jpeg", "png"],
        default="jpeg",
        help="Format de sortie : jpeg ou png (défaut: jpeg)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="Résolution des images en DPI (défaut: 150)",
    )
    parser.add_argument(
        "--page",
        type=int,
        default=None,
        help="Numéro de page spécifique à convertir (défaut: toutes les pages)",
    )

    args = parser.parse_args()
    pdf_to_images(
        input_file=args.input_file,
        output_folder=args.output_folder,
        fmt=args.format,
        dpi=args.dpi,
        page=args.page,
    )


if __name__ == "__main__":
    main()
