from datetime import date

from app.schemas.extraction import ExtractedInvoice
from app.services.validation import ERROR, WARNING, gstin_checksum, validate_invoice

TODAY = date(2026, 10, 9)

GOOD = {
    "vendor_name": "KARTHIK MESS",
    "gstin": "33BECPS1148N1ZB",
    "invoice_number": "501",
    "invoice_date": "2026-09-15",
    "line_items": [
        {"description": "Meals", "quantity": "3", "rate": "47.62", "amount": "142.86"},
        {"description": "Tea", "quantity": "4", "rate": "14.29", "amount": "57.16"},
        {"description": "Curry", "quantity": "2", "rate": "76.19", "amount": "152.38"},
    ],
    "subtotal": "352.40",
    "cgst": "8.81",
    "sgst": "8.81",
    "round_off": "-0.02",
    "total": "370.00",
}


def make(**overrides) -> ExtractedInvoice:
    return ExtractedInvoice.model_validate({**GOOD, **overrides})


def run(data: ExtractedInvoice, confidence: float | None = 0.9):
    return validate_invoice(data, ocr_confidence=confidence, today=TODAY)


def codes(flags) -> set[str]:
    return {flag.code for flag in flags}


def severity_of(flags, code: str) -> str:
    return next(flag.severity for flag in flags if flag.code == code)


def test_clean_invoice_has_no_flags():
    assert run(make()) == []


def test_gstin_checksum_algorithm_matches_real_gstins():
    assert gstin_checksum("33BECPS1148N1Z") == "B"
    assert gstin_checksum("33PUSNZ3586L1Z") == "7"


def test_wrong_gstin_character_is_caught_by_the_checksum():
    flags = run(make(gstin="33BECPS1148N1Z8"))
    assert codes(flags) == {"GSTIN_CHECKSUM"}
    assert severity_of(flags, "GSTIN_CHECKSUM") == ERROR


def test_gstin_with_a_bad_shape_is_flagged_as_format():
    # a digit zero where a letter must be, the classic O/0 mix-up
    assert codes(run(make(gstin="33BEC0S1148N1ZB"))) == {"GSTIN_FORMAT"}


def test_gstin_with_an_unknown_state_code():
    first14 = "50BECPS1148N1Z"
    flags = run(make(gstin=first14 + gstin_checksum(first14)))
    assert codes(flags) == {"GSTIN_STATE"}


def test_missing_gstin_is_only_a_warning():
    flags = run(make(gstin=None))
    assert codes(flags) == {"GSTIN_MISSING"}
    assert severity_of(flags, "GSTIN_MISSING") == WARNING


def test_line_item_arithmetic_is_checked():
    items = [dict(item) for item in GOOD["line_items"]]
    items[0]["amount"] = "1428.60"   # decimal point in the wrong place
    flags = run(make(line_items=items))
    assert "LINE_ITEM_MATH" in codes(flags)
    assert "ITEMS_SUBTOTAL_MISMATCH" in codes(flags)


def test_items_may_add_up_to_the_total_on_tax_inclusive_bills():
    items = [{"description": "Lunch", "quantity": "1", "rate": "370.00", "amount": "370.00"}]
    assert "ITEMS_SUBTOTAL_MISMATCH" not in codes(run(make(line_items=items)))


def test_dropped_decimal_in_a_tax_amount_is_caught():
    flags = codes(run(make(cgst="881")))
    assert {"CGST_SGST_MISMATCH", "TOTAL_MISMATCH", "TAX_RATE_UNUSUAL"} <= flags


def test_total_rounding_versus_a_real_mismatch():
    # 352.40 + 17.62 = 370.02, so 370.00 is within a few paise even without a round-off line
    assert run(make(round_off=None)) == []

    rounding = run(make(round_off=None, total="369.50"))
    assert "TOTAL_ROUNDING" in codes(rounding)
    assert "TOTAL_MISMATCH" not in codes(rounding)
    assert severity_of(rounding, "TOTAL_ROUNDING") == WARNING

    assert "TOTAL_MISMATCH" in codes(run(make(total="3700.00")))


def test_missing_total_is_an_error():
    flags = run(make(total=None))
    assert "TOTAL_MISSING" in codes(flags)
    assert severity_of(flags, "TOTAL_MISSING") == ERROR


def test_date_checks():
    assert "DATE_FUTURE" in codes(run(make(invoice_date="2027-01-01")))
    assert "DATE_BEFORE_GST" in codes(run(make(invoice_date="2015-05-01")))
    assert "DATE_MISSING" in codes(run(make(invoice_date=None)))


def test_low_ocr_confidence_is_a_warning():
    flags = run(make(), confidence=0.4)
    assert codes(flags) == {"LOW_OCR_CONFIDENCE"}
    assert severity_of(flags, "LOW_OCR_CONFIDENCE") == WARNING
    assert run(make(), confidence=None) == []


def test_errors_are_listed_before_warnings():
    flags = run(make(gstin="33BECPS1148N1Z8", cgst="881"), confidence=0.49)
    severities = [flag.severity for flag in flags]
    assert ERROR in severities and WARNING in severities
    assert severities == sorted(severities, key=lambda value: value != ERROR)

def test_a_missing_value_in_an_item_is_suggested_from_the_other_two():
    items = [dict(item) for item in GOOD["line_items"]]
    items[2]["quantity"] = None
    flags = run(make(line_items=items))
    assert codes(flags) == {"LINE_ITEM_INCOMPLETE"}
    assert "suggest 2" in flags[0].message

    items = [dict(item) for item in GOOD["line_items"]]
    items[0]["rate"] = None
    flags = run(make(line_items=items))
    assert codes(flags) == {"LINE_ITEM_INCOMPLETE"}
    assert "Rs 47.62" in flags[0].message

    items = [dict(item) for item in GOOD["line_items"]]
    items[1]["amount"] = None
    assert {"LINE_ITEM_INCOMPLETE", "ITEM_AMOUNT_MISSING"} <= codes(run(make(line_items=items)))