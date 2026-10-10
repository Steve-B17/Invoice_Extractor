"""Show the validators on a correct bill and on the same bill with typical OCR mistakes.

Run from backend/ with the venv active:
    python -m scripts.validate_demo
"""
from app.schemas.extraction import ExtractedInvoice
from app.services.validation import validate_invoice

CORRECT = {
    "vendor_name": "KARTHIK MESS",
    "gstin": "33BECPS1148N1ZB",
    "invoice_number": "501",
    "invoice_date": "2026-09-15",
    "line_items": [
        {"description": "Lemon Sevai", "quantity": "3", "rate": "47.62", "amount": "142.86"},
        {"description": "Idli", "quantity": "4", "rate": "14.29", "amount": "57.16"},
        {"description": "Mushroom Sevai", "quantity": "2", "rate": "76.19", "amount": "152.38"},
    ],
    "subtotal": "352.40",
    "cgst": "8.81",
    "sgst": "8.81",
    "round_off": "-0.02",
    "total": "370.00",
}


def show(title: str, raw: dict, confidence: float) -> None:
    flags = validate_invoice(ExtractedInvoice.model_validate(raw), ocr_confidence=confidence)
    print(f"\n=== {title}: {len(flags)} flag(s) ===")
    for flag in flags:
        print(f"[{flag.severity.upper():<7}] {flag.code:<24} {flag.field}: {flag.message}")


show("Correct bill", CORRECT, 0.9)
show(
    "Same bill with OCR mistakes (last GSTIN character wrong, CGST lost its decimal point)",
    {**CORRECT, "gstin": "33BECPS1148N1Z8", "cgst": "881"},
    0.49,
)