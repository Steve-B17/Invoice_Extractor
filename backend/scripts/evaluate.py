"""End-to-end accuracy: OCR -> LLM extraction -> validators, scored against ground-truth JSON.

Every bill in eval/synthetic and eval/bills that has an answer file is processed.
OCR text and LLM answers are cached in eval/cache, so re-running is fast and free.
After you change the OCR code or preprocessing, add --refresh.

Run from backend/ with the venv active:
    python -m scripts.evaluate --label baseline
    python -m scripts.evaluate --label no-preprocess --no-preprocess
    python -m scripts.evaluate --label gpt-oss-120b --model openai/gpt-oss-120b --delay 3
    python -m scripts.evaluate --label real-only --only bill
"""
import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from pathlib import Path

from app.core.config import settings
from app.schemas.extraction import ExtractedInvoice
from app.services import extraction, image_preprocess
from app.services.llm import LlmError, is_configured
from app.services.ocr import OcrError, extract_text
from app.services.validation import ERROR, validate_invoice

EVAL_DIR = Path(__file__).resolve().parents[2] / "eval"
CACHE_DIR = EVAL_DIR / "cache"
RESULTS_DIR = EVAL_DIR / "results"

MIME_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".webp": "image/webp", ".pdf": "application/pdf",
}
SCALARS = [
    "vendor_name", "gstin", "invoice_number", "invoice_date",
    "subtotal", "cgst", "sgst", "igst", "round_off", "total",
]
TEXT_FIELDS = {"vendor_name", "gstin", "invoice_number", "invoice_date"}
CRITICAL = ("gstin", "invoice_date", "total")
NUMERIC_FIELDS = ("gstin", "invoice_date", "subtotal", "cgst", "sgst", "igst", "round_off", "total")
# flags that say nothing about a misread number
UNRELATED_FLAGS = {"VENDOR_MISSING", "INVOICE_NUMBER_MISSING", "LOW_OCR_CONFIDENCE"}
GROUPS = ("synthetic-clean", "synthetic-photo", "real")


@dataclass
class Case:
    path: Path
    content_type: str
    truth_path: Path
    group: str

    @property
    def name(self) -> str:
        return self.path.name


@dataclass
class CaseResult:
    name: str
    group: str
    ocr_confidence: float | None = None
    error: str | None = None
    fields: dict = field(default_factory=dict)       # scalar -> correct?
    items: dict = field(default_factory=dict)        # key -> [correct, total]
    item_count_ok: bool = False
    flag_codes: list = field(default_factory=list)
    flagged: bool = False                            # any flag about the numbers
    flagged_error: bool = False                      # any error-level flag about the numbers
    numbers_wrong: bool = False
    skipped: bool = False                            # the LLM call failed, so this bill is not scored

    @property
    def critical_ok(self) -> bool:
        return all(self.fields.get(name) for name in CRITICAL)


# ---------- finding the bills ----------

def find_truth(path: Path) -> Path | None:
    candidates = [path.with_suffix(".json")]
    for suffix in ("_clean", "_photo"):
        if path.stem.endswith(suffix):
            candidates.append(path.with_name(path.stem[: -len(suffix)] + ".json"))
    return next((c for c in candidates if c.exists()), None)


def find_cases(only: str | None) -> list[Case]:
    cases = []
    for folder in ("synthetic", "bills"):
        directory = EVAL_DIR / folder
        if not directory.exists():
            continue
        for path in sorted(directory.iterdir()):
            content_type = MIME_TYPES.get(path.suffix.lower())
            if content_type is None or path.stem.endswith("_preprocessed"):
                continue
            truth_path = find_truth(path)
            if truth_path is None or (only and only not in path.name):
                continue
            if folder == "bills":
                group = "real"
            else:
                group = "synthetic-clean" if path.stem.endswith("_clean") else "synthetic-photo"
            cases.append(Case(path, content_type, truth_path, group))
    return cases


# ---------- caching ----------

def digest(*parts) -> str:
    return hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:16]


def cached(kind: str, key: str, refresh: bool, compute):
    """Return (value, was_cached). Failures are never cached, so a rate-limited call is retried."""
    path = CACHE_DIR / f"{kind}_{key}.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8")), True
    value = compute()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return value, False


# ---------- scoring ----------

def norm_text(value) -> str:
    return " ".join(str(value).split()).upper()


def same(field_name: str, got, want) -> bool:
    if got is None and want is None:
        return True
    if got is None or want is None:
        return False
    if field_name in TEXT_FIELDS:
        return norm_text(got) == norm_text(want)
    return same_number(got, want)


def same_number(got, want) -> bool:
    try:
        return Decimal(str(got)) == Decimal(str(want))
    except InvalidOperation:
        return False


def score_items(got_items: list, want_items: list) -> dict:
    """Compare line items by position. Returns key -> [correct, total]."""
    scores = {"amount": [0, 0], "quantity": [0, 0], "rate": [0, 0], "description": [0, 0]}
    for index, want in enumerate(want_items):
        got = got_items[index] if index < len(got_items) else {}
        for key in ("amount", "quantity", "rate"):
            if want.get(key) is not None:
                scores[key][1] += 1
                if got.get(key) is not None and same_number(got[key], want[key]):
                    scores[key][0] += 1
        if want.get("description"):
            scores["description"][1] += 1
            got_text = got.get("description")
            if got_text and SequenceMatcher(
                None, norm_text(got_text), norm_text(want["description"])
            ).ratio() >= 0.8:
                scores["description"][0] += 1
    return scores


def score_case(case: Case, extracted: dict, truth: dict, confidence: float | None, error: str | None) -> CaseResult:
    result = CaseResult(case.name, case.group, ocr_confidence=confidence, error=error)

    for name in SCALARS:
        result.fields[name] = same(name, extracted.get(name), truth.get(name))

    got_items = extracted.get("line_items") or []
    want_items = truth.get("line_items") or []
    result.items = score_items(got_items, want_items)
    result.item_count_ok = len(got_items) == len(want_items)

    result.numbers_wrong = (
        any(not result.fields[name] for name in NUMERIC_FIELDS)
        or any(c < t for key in ("amount", "quantity", "rate") for c, t in [result.items[key]])
    )

    data = ExtractedInvoice.model_validate(extracted)
    flags = validate_invoice(data, ocr_confidence=confidence)
    result.flag_codes = [flag.code for flag in flags]
    relevant = [flag for flag in flags if flag.code not in UNRELATED_FLAGS]
    result.flagged = bool(relevant)
    result.flagged_error = any(flag.severity == ERROR for flag in relevant)
    return result


# ---------- running the pipeline ----------

def run_case(case: Case, args, truth: dict) -> tuple[CaseResult, str, str]:
    """Returns (result, ocr_status, llm_status), each 'new', 'cached', 'failed' or 'none'."""
    ocr_key = digest(
        case.path.resolve(), case.path.stat().st_mtime_ns, not args.no_preprocess,
        settings.ocr_language, settings.ocr_psm, image_preprocess.TARGET_GLYPH_HEIGHT,
    )

    def compute_ocr():
        try:
            out = extract_text(str(case.path), case.content_type, use_preprocess=not args.no_preprocess)
            return {"text": out.text, "confidence": out.confidence, "method": out.method, "error": None}
        except OcrError as exc:
            return {"text": "", "confidence": None, "method": "failed", "error": str(exc)}

    ocr, ocr_was_cached = cached("ocr", ocr_key, args.refresh, compute_ocr)
    ocr_status = "cached" if ocr_was_cached else "new"

    empty = ExtractedInvoice().model_dump(mode="json")
    if not ocr["text"].strip():
        result = score_case(case, empty, truth, ocr["confidence"], ocr["error"] or "No text read")
        return result, ocr_status, "none"

    llm_key = digest(ocr["text"], settings.llm_model, extraction.SYSTEM_PROMPT)
    try:
        extracted, llm_was_cached = cached(
            "llm", llm_key, args.refresh,
            lambda: extraction.extract_invoice_fields(ocr["text"]).model_dump(mode="json"),
        )
    except LlmError as exc:
        # an infrastructure problem (rate limit, network), not an extraction mistake:
        # the bill is left out of the scores, and the next run retries it
        result = score_case(case, empty, truth, ocr["confidence"], f"LLM: {exc}")
        result.skipped = True
        return result, ocr_status, "failed"

    if not llm_was_cached and args.delay:
        time.sleep(args.delay)   # stay under the provider's rate limit
    llm_status = "cached" if llm_was_cached else "new"
    return score_case(case, extracted, truth, ocr["confidence"], None), ocr_status, llm_status


# ---------- reporting ----------

def pct(correct: int, total: int) -> str:
    return f"{correct / total:.0%}" if total else "n/a"


def summarise(results: list[CaseResult]) -> dict:
    wrong = [r for r in results if r.numbers_wrong]
    right = [r for r in results if not r.numbers_wrong]
    confs = [r.ocr_confidence for r in results if r.ocr_confidence is not None]
    item_amounts = [sum(r.items["amount"][0] for r in results), sum(r.items["amount"][1] for r in results)]
    return {
        "bills": len(results),
        "ocr_confidence": sum(confs) / len(confs) if confs else None,
        "critical_ok": [sum(r.critical_ok for r in results), len(results)],
        "numbers_ok": [len(right), len(results)],
        "item_amounts": item_amounts,
        "wrong_flagged": [sum(r.flagged for r in wrong), len(wrong)],
        "false_errors": [sum(r.flagged_error for r in right), len(right)],
        "failures": sum(1 for r in results if r.error),
    }


def build_report(label: str, args, all_results: list[CaseResult]) -> str:
    results = [r for r in all_results if not r.skipped]
    skipped = [r for r in all_results if r.skipped]
    lines = [
        f"# Evaluation: {label} ({date.today()})",
        "",
        f"- OCR language: `{settings.ocr_language}`, layout mode: `{settings.ocr_psm}`, "
        f"preprocessing: `{'off' if args.no_preprocess else 'on'}`, "
        f"character height: `{image_preprocess.TARGET_GLYPH_HEIGHT:g}`",
        f"- LLM model: `{settings.llm_model}`",
        f"- Bills scored: {len(results)}"
        + (f" (skipped because the LLM call failed, run again to retry: {', '.join(r.name for r in skipped)})"
           if skipped else ""),
        "",
        "## Summary by group",
        "",
        "| Group | Bills | OCR confidence | GSTIN, date and total right | Every number right | "
        "Item amounts right | Wrong-number bills flagged | Right-number bills with a false error flag |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for group in (*GROUPS, "ALL"):
        subset = results if group == "ALL" else [r for r in results if r.group == group]
        if not subset:
            continue
        s = summarise(subset)
        conf = f"{s['ocr_confidence']:.2f}" if s["ocr_confidence"] is not None else "n/a"
        lines.append(
            f"| {group} | {s['bills']} | {conf} | {pct(*s['critical_ok'])} | {pct(*s['numbers_ok'])} | "
            f"{pct(*s['item_amounts'])} | {pct(*s['wrong_flagged'])} ({s['wrong_flagged'][0]}/{s['wrong_flagged'][1]}) | "
            f"{pct(*s['false_errors'])} ({s['false_errors'][0]}/{s['false_errors'][1]}) |"
        )

    lines += ["", "## Accuracy per field", "", "| Field | " + " | ".join(GROUPS) + " | ALL |",
              "|---|" + "---:|" * (len(GROUPS) + 1)]
    for name in SCALARS:
        cells = []
        for group in (*GROUPS, "ALL"):
            subset = results if group == "ALL" else [r for r in results if r.group == group]
            cells.append(pct(sum(r.fields[name] for r in subset), len(subset)) if subset else "-")
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    for key in ("quantity", "rate", "amount", "description"):
        cells = []
        for group in (*GROUPS, "ALL"):
            subset = results if group == "ALL" else [r for r in results if r.group == group]
            total = sum(r.items[key][1] for r in subset)
            cells.append(pct(sum(r.items[key][0] for r in subset), total) if subset else "-")
        lines.append(f"| line item {key} | " + " | ".join(cells) + " |")

    lines += ["", "## Per bill", "", "| Bill | OCR conf | Fields right | Missed | Flags |", "|---|---:|---:|---|---|"]
    for r in all_results:
        missed = [name for name in SCALARS if not r.fields[name]]
        conf = f"{r.ocr_confidence:.2f}" if r.ocr_confidence is not None else "n/a"
        note = f" ({r.error})" if r.error else ""
        lines.append(
            f"| {r.name} | {conf} | {sum(r.fields.values())}/{len(SCALARS)} | "
            f"{', '.join(missed) or '-'}{note} | {', '.join(r.flag_codes) or '-'} |"
        )
    return "\n".join(lines)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    parser.add_argument("--model", help="override LLM_MODEL for this run")
    parser.add_argument("--no-preprocess", action="store_true")
    parser.add_argument("--refresh", action="store_true", help="ignore cached OCR text and LLM answers")
    parser.add_argument("--delay", type=float, default=0, help="seconds to wait after each new LLM call")
    parser.add_argument("--only", help="only bills whose file name contains this text")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    if args.model:
        settings.llm_model = args.model
    if not is_configured():
        sys.exit("The LLM is not configured. Set LLM_BASE_URL, LLM_API_KEY and LLM_MODEL in .env.")

    cases = find_cases(args.only)
    if args.limit:
        cases = cases[: args.limit]
    if not cases:
        sys.exit("No bills with an answer file found. Make synthetic bills with "
                 "'python -m scripts.make_sample_bills' and add JSON answer files for real ones.")

    results: list[CaseResult] = []
    for number, case in enumerate(cases, start=1):
        truth = json.loads(case.truth_path.read_text(encoding="utf-8"))
        result, ocr_status, llm_status = run_case(case, args, truth)
        results.append(result)
        scored = "SKIPPED" if result.skipped else f"fields {sum(result.fields.values())}/{len(SCALARS)}"
        print(f"[{number}/{len(cases)}] {case.name:<34} {scored:<14} flags={len(result.flag_codes)}"
              f"  (ocr {ocr_status}, llm {llm_status}){'  ' + result.error if result.error else ''}")

    report = build_report(args.label, args, results)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / f"{args.label}.md").write_text(report + "\n", encoding="utf-8")
    (RESULTS_DIR / f"{args.label}.json").write_text(
        json.dumps([asdict(r) for r in results], ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n" + report)
    print(f"\nSaved to {RESULTS_DIR / (args.label + '.md')}")


if __name__ == "__main__":
    main()