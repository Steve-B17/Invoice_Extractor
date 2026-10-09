"""Compare OCR output with the ground truth of the synthetic bills.

Run from backend/ with the venv active:
    python -m scripts.check_ocr
    python -m scripts.check_ocr --limit 2        (only the first 2 bills, faster)
"""
import argparse
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

from app.services.ocr import extract_text

DEFAULT_DIR = Path(__file__).resolve().parents[2] / "eval" / "synthetic"

VERSIONS = (
    ("clean", "_clean.png", "image/png"),
    ("photo", "_photo.jpg", "image/jpeg"),
)


def expected_fields(truth: dict) -> dict[str, str]:
    fields = {
        "vendor": truth["vendor_name"],
        "gstin": truth["gstin"],
        "invoice_no": truth["invoice_number"],
        "date": date.fromisoformat(truth["invoice_date"]).strftime("%d-%m-%Y"),
        "subtotal": truth["subtotal"],
        "cgst": truth["cgst"],
        "sgst": truth["sgst"],
        "total": truth["total"],
    }
    for i, item in enumerate(truth["line_items"], start=1):
        fields[f"item{i}_amount"] = item["amount"]
    return fields


def squash(text: str) -> str:
    return re.sub(r"\s+", "", text.upper())


def check(text: str, expected: dict[str, str]) -> dict[str, bool]:
    haystack = squash(text)
    return {name: squash(str(value)) in haystack for name, value in expected.items()}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=str(DEFAULT_DIR))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    folder = Path(args.dir)
    truth_files = sorted(folder.glob("synthetic_*.json"))
    if args.limit:
        truth_files = truth_files[: args.limit]
    if not truth_files:
        sys.exit(f"No synthetic_*.json files in {folder}. Run: python -m scripts.make_sample_bills")

    totals: dict[str, list[int]] = {}   # mode -> [correct, total]
    started = time.perf_counter()

    for truth_file in truth_files:
        truth = json.loads(truth_file.read_text(encoding="utf-8"))
        expected = expected_fields(truth)

        for label, suffix, content_type in VERSIONS:
            image = folder / (truth_file.stem + suffix)
            if not image.exists():
                continue
            for use_preprocess in (True, False):
                mode = f"{label}/{'preprocess' if use_preprocess else 'raw'}"
                result = extract_text(str(image), content_type, use_preprocess=use_preprocess)
                found = check(result.text, expected)
                correct = sum(found.values())
                missed = [name for name, ok in found.items() if not ok]
                conf = "n/a" if result.confidence is None else f"{result.confidence:.2f}"

                bucket = totals.setdefault(mode, [0, 0])
                bucket[0] += correct
                bucket[1] += len(found)

                print(f"{truth_file.stem}  {mode:<17} conf={conf}  {correct}/{len(found)}"
                      + (f"  missed: {', '.join(missed)}" if missed else ""))

    print("\n=== Summary: share of fields found in the OCR text ===")
    for mode, (correct, total) in sorted(totals.items()):
        print(f"{mode:<18} {correct}/{total}  = {correct / total:.0%}")
    print(f"\nTook {time.perf_counter() - started:.0f}s")


if __name__ == "__main__":
    main()