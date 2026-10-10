"""Try the OCR pipeline on a local file.

Run from backend/ with the venv active:
    python -m scripts.ocr_try "C:\\path\\to\\bill.jpg"
    python -m scripts.ocr_try "C:\\path\\to\\bill.jpg" --no-preprocess
    python -m scripts.ocr_try "C:\\path\\to\\bill.jpg" --save-debug
"""
import argparse
import sys
import time
from pathlib import Path

import cv2

from app.services.image_preprocess import preprocess
from app.services.ocr import extract_text, load_image_gray

MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--no-preprocess", action="store_true")
    parser.add_argument("--save-debug", action="store_true",
                        help="save the cleaned-up image next to the original")
    args = parser.parse_args()

    path = Path(args.path)
    content_type = MIME_TYPES.get(path.suffix.lower())
    if content_type is None:
        sys.exit(f"Unsupported file type: {path.suffix}")

    start = time.perf_counter()
    result = extract_text(str(path), content_type, use_preprocess=not args.no_preprocess)
    elapsed = time.perf_counter() - start

    conf = "n/a" if result.confidence is None else f"{result.confidence:.2f}"
    print(f"method={result.method}  pages={result.pages}  confidence={conf}  time={elapsed:.1f}s")
    print("-" * 60)
    print(result.text)

    if args.save_debug and content_type != "application/pdf":
        cleaned = preprocess(load_image_gray(str(path)))
        debug_path = path.with_name(path.stem + "_preprocessed.png")
        cv2.imwrite(str(debug_path), cleaned)
        print("-" * 60)
        print(f"Saved cleaned image: {debug_path}")


if __name__ == "__main__":
    main()