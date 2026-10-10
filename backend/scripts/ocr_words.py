"""Show word-level confidence for an image.

Run from backend/ with the venv active:
    python -m scripts.ocr_words "C:\\path\\to\\bill.jpg"
    python -m scripts.ocr_words "C:\\path\\to\\bill.jpg" --no-preprocess
    python -m scripts.ocr_words "C:\\path\\to\\bill.jpg" --below 70
"""
import argparse
import sys

import pytesseract
from pytesseract import Output

from app.core.config import settings
from app.services import ocr  # noqa: F401  (applies TESSERACT_CMD)
from app.services.image_preprocess import preprocess
from app.services.ocr import load_image_gray


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--no-preprocess", action="store_true")
    parser.add_argument("--below", type=float, default=60)
    args = parser.parse_args()

        gray = load_image_gray(args.path, crop=not args.no_preprocess)
    image = gray if args.no_preprocess else preprocess(gray)
    data = pytesseract.image_to_data(
        image,
        lang=settings.ocr_language,
        config=f"--oem 3 --psm {settings.ocr_psm}",
        output_type=Output.DICT,
    )

    words = [
        (w.strip(), float(c))
        for w, c in zip(data["text"], data["conf"])
        if w.strip() and float(c) >= 0
    ]
    if not words:
        print("No words found")
        return

    confs = sorted(c for _, c in words)
    mean = sum(confs) / len(confs)
    median = confs[len(confs) // 2]
    print(f"words={len(words)}  mean={mean:.1f}  median={median:.1f}")

    low = [(w, c) for w, c in words if c < args.below]
    print(f"{len(low)} words below {args.below}:")
    for word, conf in low[:40]:
        print(f"  {conf:5.1f}  {word}")


if __name__ == "__main__":
    main()