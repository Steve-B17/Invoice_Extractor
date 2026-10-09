"""Run OCR + LLM extraction on a local file and compare it with its ground-truth JSON.

Run from backend/ with the venv active:
    python -m scripts.extract_try "..\\eval\\bills\\bill_01.jpg"
    python -m scripts.extract_try "..\\eval\\synthetic\\synthetic_01_photo.jpg"
"""
import argparse
import json
import sys
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.services.extraction import extract_invoice_fields
from app.services.ocr import extract_text

MIME_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".webp": "image/webp", ".pdf": "application/pdf",
}
SCALARS = [
    "vendor_name", "gstin", "invoice_number", "invoice_date",
    "subtotal", "cgst", "sgst", "igst", "round_off", "total",
]


def find_truth(path: Path) -> Path | None:
    candidates = [path.with_suffix(".json")]
    for suffix in ("_clean", "_photo"):
        if path.stem.endswith(suffix):
            candidates.append(path.with_name(path.stem[: -len(suffix)] + ".json"))
    return next((c for c in candidates if c.exists()), None)


def same(got, want) -> bool:
    if got is None and want is None:
        return True
    if got is None or want is None:
        return False
    try:
        return Decimal(str(got)) == Decimal(str(want))
    except InvalidOperation:
        return str(got).strip().upper() == str(want).strip().upper()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--no-preprocess", action="store_true")
    args = parser.parse_args()

    path = Path(args.path)
    content_type = MIME_TYPES.get(path.suffix.lower())
    if content_type is None:
        sys.exit(f"Unsupported file type: {path.suffix}")

    ocr = extract_text(str(path), content_type, use_preprocess=not args.no_preprocess)
    print(f"OCR: method={ocr.method} confidence={ocr.confidence}")

    start = time.perf_counter()
    data = extract_invoice_fields(ocr.text)
    print(f"LLM: {time.perf_counter() - start:.1f}s\n")

    got = data.model_dump(mode="json")
    print(json.dumps(got, indent=2, ensure_ascii=False))

    truth_path = find_truth(path)
    if truth_path is None:
        print("\n(no ground-truth JSON found next to the file, skipping comparison)")
        return

    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    print(f"\n=== Compared with {truth_path.name} ===")
    correct = 0
    for field in SCALARS:
        ok = same(got.get(field), truth.get(field))
        correct += ok
        print(f"{'OK  ' if ok else 'MISS'} {field:<15} got={got.get(field)!s:<22} want={truth.get(field)}")
    print(f"\n{correct}/{len(SCALARS)} fields match")
    print(f"line items: got {len(got['line_items'])}, expected {len(truth.get('line_items', []))}")


if __name__ == "__main__":
    main()