"""Inject typical OCR mistakes into correct invoices and count how many the validators catch.

No OCR, no LLM and no database are used, so this runs in seconds.

Run from backend/ with the venv active:
    python -m scripts.validator_stress
    python -m scripts.validator_stress --trials 30 --seed 7
"""
import argparse
import copy
import json
import random
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.schemas.extraction import ExtractedInvoice
from app.services.validation import ERROR, validate_invoice

EVAL_DIR = Path(__file__).resolve().parents[2] / "eval"
OCR_CONFUSIONS = {"0": "O", "O": "0", "1": "I", "I": "1", "5": "S", "S": "5",
                  "8": "B", "B": "8", "2": "Z", "Z": "2"}
ALNUM = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"
MONEY_FIELDS = ("subtotal", "cgst", "sgst", "total")


# ---------- helpers that damage a piece of text the way OCR does ----------

def digit_positions(text: str) -> list[int]:
    return [i for i, ch in enumerate(text) if ch.isdigit()]


def drop_decimal(text: str, rng) -> str | None:
    return text.replace(".", "") if "." in text else None


def swap_adjacent_digits(text: str, rng) -> str | None:
    pairs = [i for i in range(len(text) - 1)
             if text[i].isdigit() and text[i + 1].isdigit() and text[i] != text[i + 1]]
    if not pairs:
        return None
    i = rng.choice(pairs)
    return text[:i] + text[i + 1] + text[i] + text[i + 2:]


def lose_digit(text: str, rng) -> str | None:
    positions = digit_positions(text)
    if len(positions) < 3:
        return None
    i = rng.choice(positions)
    return text[:i] + text[i + 1:]


def add_digit(text: str, rng) -> str | None:
    positions = digit_positions(text)
    if not positions:
        return None
    i = rng.choice(positions)
    return text[:i] + rng.choice(DIGITS) + text[i:]


def change_digit(text: str, rng) -> str | None:
    positions = digit_positions(text)
    if not positions:
        return None
    i = rng.choice(positions)
    new = rng.choice([d for d in DIGITS if d != text[i]])
    return text[:i] + new + text[i + 1:]


def same_number(a: str, b: str) -> bool:
    try:
        return Decimal(a) == Decimal(b)
    except InvalidOperation:
        return a == b


# ---------- paths into the ground-truth dictionary ----------

def money_paths(truth: dict) -> list[tuple]:
    paths = [(name,) for name in MONEY_FIELDS if truth.get(name)]
    paths += [("line_items", i, "amount")
              for i, item in enumerate(truth.get("line_items", [])) if item.get("amount")]
    return paths


def get(truth: dict, path: tuple):
    node = truth
    for key in path:
        node = node[key]
    return node


def put(truth: dict, path: tuple, value) -> None:
    node = truth
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value


# ---------- mutations: each returns a damaged copy, or None if it does not apply ----------

def money_mutation(damage):
    def mutate(truth: dict, rng):
        paths = money_paths(truth)
        if not paths:
            return None
        path = rng.choice(paths)
        old = get(truth, path)
        new = damage(old, rng)
        if new is None or new == old or same_number(old, new):
            return None
        out = copy.deepcopy(truth)
        put(out, path, new)
        return out
    return mutate


def gstin_mutation(damage):
    def mutate(truth: dict, rng):
        gstin = truth.get("gstin")
        if not gstin:
            return None
        new = damage(gstin, rng)
        if new is None or new == gstin:
            return None
        out = copy.deepcopy(truth)
        out["gstin"] = new
        return out
    return mutate


def _gstin_confusion(gstin: str, rng) -> str | None:
    positions = [i for i, ch in enumerate(gstin) if ch in OCR_CONFUSIONS]
    if not positions:
        return None
    i = rng.choice(positions)
    return gstin[:i] + OCR_CONFUSIONS[gstin[i]] + gstin[i + 1:]


def _gstin_random_char(gstin: str, rng) -> str:
    i = rng.randrange(len(gstin))
    new = rng.choice([c for c in ALNUM if c != gstin[i]])
    return gstin[:i] + new + gstin[i + 1:]


def quantity_digit(truth: dict, rng):
    items = [i for i, item in enumerate(truth.get("line_items", [])) if item.get("quantity")]
    if not items:
        return None
    index = rng.choice(items)
    old = truth["line_items"][index]["quantity"]
    new = change_digit(old, rng)
    if new is None or same_number(old, new):
        return None
    out = copy.deepcopy(truth)
    out["line_items"][index]["quantity"] = new
    return out


def date_year_transposed(truth: dict, rng):
    text = truth.get("invoice_date")
    if not text or len(text) < 4 or text[2] == text[3]:
        return None
    out = copy.deepcopy(truth)
    out["invoice_date"] = text[:2] + text[3] + text[2] + text[4:]
    return out


def date_year_off_by_one(truth: dict, rng):
    text = truth.get("invoice_date")
    if not text:
        return None
    out = copy.deepcopy(truth)
    out["invoice_date"] = f"{int(text[:4]) - 1}{text[4:]}"
    return out


def vendor_typo(truth: dict, rng):
    name = truth.get("vendor_name") or ""
    pairs = [i for i in range(len(name) - 1)
             if name[i].isalpha() and name[i + 1].isalpha() and name[i] != name[i + 1]]
    if not pairs:
        return None
    i = rng.choice(pairs)
    out = copy.deepcopy(truth)
    out["vendor_name"] = name[:i] + name[i + 1] + name[i] + name[i + 2:]
    return out


def invoice_number_digit(truth: dict, rng):
    old = truth.get("invoice_number") or ""
    new = change_digit(old, rng)
    if new is None:
        return None
    out = copy.deepcopy(truth)
    out["invoice_number"] = new
    return out


CAUGHT_BY_DESIGN = {
    "GSTIN: letter/digit confusion (O/0, I/1, S/5, B/8, Z/2)": gstin_mutation(_gstin_confusion),
    "GSTIN: any single character misread": gstin_mutation(_gstin_random_char),
    "Money: decimal point lost (8.81 -> 881)": money_mutation(drop_decimal),
    "Money: two adjacent digits swapped": money_mutation(swap_adjacent_digits),
    "Money: a digit lost": money_mutation(lose_digit),
    "Money: an extra digit added": money_mutation(add_digit),
    "Money: any single digit misread": money_mutation(change_digit),
    "Quantity: a digit misread": quantity_digit,
    "Date: year digits transposed (2026 -> 2062)": date_year_transposed,
}

CONTROLS = {   # nothing in the invoice contradicts itself, so arithmetic cannot notice
    "Control: date year off by one (still plausible)": date_year_off_by_one,
    "Control: typo in the vendor name": vendor_typo,
    "Control: a digit of the invoice number misread": invoice_number_digit,
}


# ---------- running the experiment ----------

def flag_codes(truth: dict) -> set[str]:
    flags = validate_invoice(ExtractedInvoice.model_validate(truth), ocr_confidence=0.9)
    return {flag.code for flag in flags}


def error_codes(truth: dict) -> set[str]:
    flags = validate_invoice(ExtractedInvoice.model_validate(truth), ocr_confidence=0.9)
    return {flag.code for flag in flags if flag.severity == ERROR}


def load_truths() -> list[tuple[str, dict]]:
    truths = []
    for folder in ("synthetic", "bills"):
        for path in sorted((EVAL_DIR / folder).glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                continue
            if isinstance(data, dict) and "total" in data and "line_items" in data:
                truths.append((f"{folder}/{path.name}", data))
    return truths


def run_group(mutations: dict, truths, trials: int, rng) -> list[tuple[str, int, int]]:
    rows = []
    for label, mutate in mutations.items():
        tried = caught = 0
        for _, truth in truths:
            baseline = flag_codes(truth)
            for _ in range(trials):
                damaged = mutate(truth, rng)
                if damaged is None:
                    continue
                tried += 1
                if flag_codes(damaged) - baseline:   # a flag the clean bill did not have
                    caught += 1
        rows.append((label, tried, caught))
    return rows


def table(rows) -> str:
    lines = ["| Mistake injected | Trials | Caught | Rate |", "|---|---:|---:|---:|"]
    for label, tried, caught in rows:
        rate = f"{caught / tried:.0%}" if tried else "n/a"
        lines.append(f"| {label} | {tried} | {caught} | {rate} |")
    return "\n".join(lines)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=20, help="random variants per bill and mistake type")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    truths = load_truths()
    if not truths:
        sys.exit(f"No ground-truth JSON files found under {EVAL_DIR}. "
                 "Run: python -m scripts.make_sample_bills")

    rng = random.Random(args.seed)
    false_alarms = [name for name, truth in truths if error_codes(truth)]
    caught_rows = run_group(CAUGHT_BY_DESIGN, truths, args.trials, rng)
    control_rows = run_group(CONTROLS, truths, args.trials, rng)

    total_tried = sum(row[1] for row in caught_rows)
    total_caught = sum(row[2] for row in caught_rows)

    report = [
        f"# Validator stress test ({date.today()})",
        "",
        f"Clean bills used: {len(truths)}. Random variants per bill and mistake type: {args.trials}. Seed: {args.seed}.",
        f"Clean bills that raised an error-level flag (false alarms): {len(false_alarms)} of {len(truths)}"
        + (f" ({', '.join(false_alarms)})" if false_alarms else ""),
        "",
        "## Mistakes the validators are designed to catch",
        "",
        table(caught_rows),
        "",
        f"Overall: {total_caught} of {total_tried} injected mistakes caught "
        f"({total_caught / total_tried:.0%})." if total_tried else "Nothing was injected.",
        "",
        "## Controls: mistakes that no arithmetic check can notice",
        "",
        table(control_rows),
    ]
    text = "\n".join(report)
    print(text)

    out_dir = EVAL_DIR / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "validator_stress.md").write_text(text + "\n", encoding="utf-8")
    print(f"\nSaved to {out_dir / 'validator_stress.md'}")


if __name__ == "__main__":
    main()