"""Deterministic checks on extracted invoice data.

The LLM reads the bill; this module decides what to trust. Nothing here changes a
value. It only reports flags so a human can compare them with the image.
"""
import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from app.schemas.extraction import ExtractedInvoice

ERROR = "error"
WARNING = "warning"

GSTIN_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# 2 digits state, 5 letters + 4 digits + 1 letter (the PAN), entity number, 'Z', check char
GSTIN_PATTERN = re.compile(r"^(\d{2})[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
VALID_STATE_CODES = {f"{n:02d}" for n in range(1, 39)} | {"97", "99"}
GST_LAUNCH_DATE = date(2017, 7, 1)

# Combined tax rates seen on Indian bills (CGST + SGST, or IGST). The slabs have changed
# over the years, so this is a union of old and new ones, and an odd rate is only a warning.
PLAUSIBLE_TAX_RATES = tuple(
    Decimal(rate) for rate in ("0", "0.25", "1", "1.5", "3", "5", "12", "18", "28", "40")
)
RATE_TOLERANCE = Decimal("0.3")             # percentage points
MIN_SUBTOTAL_FOR_RATE_CHECK = Decimal("10")  # rounding noise dominates tiny bills

CENT = Decimal("0.01")
LINE_TOLERANCE = Decimal("0.05")
SUM_TOLERANCE = Decimal("1.00")
TAX_SPLIT_TOLERANCE = Decimal("0.02")
TOTAL_TOLERANCE = Decimal("0.05")
LOW_OCR_CONFIDENCE = 0.6


@dataclass(frozen=True)
class Flag:
    field: str
    code: str
    severity: str
    message: str


def rs(value: Decimal) -> str:
    return f"Rs {value:,.2f}"


def gstin_checksum(first14: str) -> str:
    """The 15th character of a GSTIN (a Luhn-style mod-36 check character)."""
    total = 0
    for i, char in enumerate(first14):
        product = GSTIN_CHARS.index(char) * (1 if i % 2 == 0 else 2)
        total += product // 36 + product % 36
    return GSTIN_CHARS[(36 - total % 36) % 36]


def _check_identity(data: ExtractedInvoice) -> list[Flag]:
    flags = []
    if data.vendor_name is None:
        flags.append(Flag("vendor_name", "VENDOR_MISSING", WARNING, "No vendor name was found."))
    if data.invoice_number is None:
        flags.append(
            Flag("invoice_number", "INVOICE_NUMBER_MISSING", WARNING, "No invoice number was found.")
        )
    return flags


def _check_gstin(gstin: str | None) -> list[Flag]:
    if gstin is None:
        return [
            Flag(
                "gstin",
                "GSTIN_MISSING",
                WARNING,
                "No GSTIN was found. That is normal for unregistered sellers, "
                "otherwise check the bill.",
            )
        ]

    match = GSTIN_PATTERN.match(gstin)
    if not match:
        return [
            Flag(
                "gstin",
                "GSTIN_FORMAT",
                ERROR,
                f"'{gstin}' is not shaped like a GSTIN (15 characters: 2 digits, 5 letters, "
                "4 digits, 1 letter, 1 letter or digit, Z, 1 check character). "
                "OCR often confuses 0/O, 1/I, 5/S and 8/B.",
            )
        ]

    flags = []
    if match.group(1) not in VALID_STATE_CODES:
        flags.append(
            Flag("gstin", "GSTIN_STATE", ERROR, f"State code {match.group(1)} is not a valid GST state code.")
        )
    if gstin[14] != gstin_checksum(gstin[:14]):
        flags.append(
            Flag(
                "gstin",
                "GSTIN_CHECKSUM",
                ERROR,
                "The GSTIN check character does not match, so at least one character is "
                "probably misread. Compare it with the image.",
            )
        )
    return flags


def _check_date(invoice_date: date | None, today: date) -> list[Flag]:
    if invoice_date is None:
        return [Flag("invoice_date", "DATE_MISSING", WARNING, "No invoice date was found.")]
    if invoice_date > today + timedelta(days=1):
        return [
            Flag("invoice_date", "DATE_FUTURE", ERROR, f"The date {invoice_date} is in the future.")
        ]
    if invoice_date < GST_LAUNCH_DATE:
        return [
            Flag(
                "invoice_date",
                "DATE_BEFORE_GST",
                WARNING,
                f"The date {invoice_date} is before GST began (July 2017). Check the year.",
            )
        ]
    return []

def _check_incomplete_items(items) -> list[Flag]:
    """If exactly one of quantity, rate and amount is missing, say what the other two imply.
    This only suggests: the stored value stays empty until a person confirms it."""
    flags = []
    for position, item in enumerate(items):
        missing = [name for name in ("quantity", "rate", "amount") if getattr(item, name) is None]
        if len(missing) != 1:
            continue

        name = missing[0]
        if name == "quantity" and item.rate:
            suggestion = f"{item.amount / item.rate:.3f}".rstrip("0").rstrip(".")
        elif name == "rate" and item.quantity:
            suggestion = rs(item.amount / item.quantity)
        elif name == "amount":
            suggestion = rs(item.quantity * item.rate)
        else:
            continue

        flags.append(
            Flag(
                f"line_items.{position}",
                "LINE_ITEM_INCOMPLETE",
                WARNING,
                f"Item {position + 1}: the {name} is missing. "
                f"The other two values suggest {suggestion}.",
            )
        )
    return flags

def _check_line_items(data: ExtractedInvoice) -> list[Flag]:
    items = data.line_items
    if not items:
        return [Flag("line_items", "NO_LINE_ITEMS", WARNING, "No line items were extracted.")]

    flags = []
    for position, item in enumerate(items):
        if item.quantity is None or item.rate is None or item.amount is None:
            continue
        expected = (item.quantity * item.rate).quantize(CENT, rounding=ROUND_HALF_UP)
        tolerance = max(LINE_TOLERANCE, abs(item.amount) * Decimal("0.01"))
        if abs(expected - item.amount) > tolerance:
            flags.append(
                Flag(
                    f"line_items.{position}",
                    "LINE_ITEM_MATH",
                    ERROR,
                    f"Item {position + 1}: {item.quantity:g} x {item.rate} = {rs(expected)}, "
                    f"but the amount is {rs(item.amount)}.",
                )
            )
    flags.extend(_check_incomplete_items(items))
    amounts = [item.amount for item in items]
    if any(amount is None for amount in amounts):
        flags.append(
            Flag(
                "line_items",
                "ITEM_AMOUNT_MISSING",
                WARNING,
                "Some items have no amount, so the items could not be added up.",
            )
        )
        return flags

    references = [value for value in (data.subtotal, data.total) if value is not None]
    if references:
        items_sum = sum(amounts, Decimal("0"))
        # Tax-inclusive bills list prices that add up to the total, not the subtotal
        if not any(abs(items_sum - reference) <= SUM_TOLERANCE for reference in references):
            shown, label = (
                (data.subtotal, "subtotal") if data.subtotal is not None else (data.total, "total")
            )
            flags.append(
                Flag(
                    "line_items",
                    "ITEMS_SUBTOTAL_MISMATCH",
                    ERROR,
                    f"Line items add up to {rs(items_sum)}, but the bill's {label} is {rs(shown)}.",
                )
            )
    return flags


def _check_taxes(data: ExtractedInvoice) -> list[Flag]:
    flags = []
    cgst, sgst, igst = data.cgst, data.sgst, data.igst

    if cgst is not None and sgst is not None:
        if abs(cgst - sgst) > TAX_SPLIT_TOLERANCE:
            flags.append(
                Flag(
                    "cgst",
                    "CGST_SGST_MISMATCH",
                    ERROR,
                    f"CGST ({rs(cgst)}) and SGST ({rs(sgst)}) should be equal. "
                    "A digit or decimal point is probably misread.",
                )
            )
    elif (cgst is None) != (sgst is None):
        flags.append(
            Flag("cgst", "CGST_SGST_INCOMPLETE", WARNING, "Only one of CGST and SGST was found.")
        )

    if igst is not None and (cgst is not None or sgst is not None):
        flags.append(
            Flag("igst", "TAX_TYPE_CONFLICT", WARNING, "The bill shows IGST together with CGST or SGST.")
        )

    taxes = sum((v for v in (cgst, sgst, igst) if v is not None), Decimal("0"))
    if data.subtotal is not None and data.subtotal >= MIN_SUBTOTAL_FOR_RATE_CHECK and taxes > 0:
        rate = taxes / data.subtotal * 100
        if not any(abs(rate - known) <= RATE_TOLERANCE for known in PLAUSIBLE_TAX_RATES):
            flags.append(
                Flag(
                    "subtotal",
                    "TAX_RATE_UNUSUAL",
                    WARNING,
                    f"Taxes are {rate:.1f}% of the subtotal, which is not a standard GST rate.",
                )
            )
    return flags


def _check_totals(data: ExtractedInvoice) -> list[Flag]:
    if data.total is None:
        return [Flag("total", "TOTAL_MISSING", ERROR, "No total amount was found.")]
    if data.subtotal is None:
        return [
            Flag(
                "subtotal",
                "SUBTOTAL_MISSING",
                WARNING,
                "No subtotal was found, so the total could not be cross-checked.",
            )
        ]

    taxes = sum((v for v in (data.cgst, data.sgst, data.igst) if v is not None), Decimal("0"))
    expected = data.subtotal + taxes + (data.round_off or Decimal("0"))
    difference = abs(data.total - expected)

    if difference <= TOTAL_TOLERANCE:
        return []
    if data.round_off is None and difference < SUM_TOLERANCE:
        return [
            Flag(
                "total",
                "TOTAL_ROUNDING",
                WARNING,
                f"The total differs from subtotal + taxes by {rs(difference)}. This looks like "
                "rounding, but no round-off line was found.",
            )
        ]
    return [
        Flag(
            "total",
            "TOTAL_MISMATCH",
            ERROR,
            f"Subtotal + taxes + round-off = {rs(expected)}, but the bill's total is {rs(data.total)}.",
        )
    ]


def _check_ocr(confidence: float | None) -> list[Flag]:
    if confidence is not None and confidence < LOW_OCR_CONFIDENCE:
        return [
            Flag(
                "invoice",
                "LOW_OCR_CONFIDENCE",
                WARNING,
                f"OCR confidence is low ({confidence:.0%}), so check every field against the image.",
            )
        ]
    return []


def validate_invoice(
    data: ExtractedInvoice,
    *,
    ocr_confidence: float | None = None,
    today: date | None = None,
) -> list[Flag]:
    today = today or date.today()
    flags = [
        *_check_identity(data),
        *_check_gstin(data.gstin),
        *_check_date(data.invoice_date, today),
        *_check_line_items(data),
        *_check_taxes(data),
        *_check_totals(data),
        *_check_ocr(ocr_confidence),
    ]
    # stable sort: errors first, each group keeps its natural order
    return sorted(flags, key=lambda flag: flag.severity != ERROR)