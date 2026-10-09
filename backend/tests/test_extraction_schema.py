from datetime import date
from decimal import Decimal

from app.schemas.extraction import ExtractedInvoice, ExtractedLineItem


def test_money_parsing_handles_symbols_commas_and_junk():
    data = ExtractedInvoice.model_validate(
        {
            "total": "Rs 1,980.5",
            "subtotal": "₹ 352.40",
            "cgst": 11800,
            "sgst": "abc",
            "igst": None,
            "round_off": "-0.02",
        }
    )
    assert data.total == Decimal("1980.50")
    assert data.subtotal == Decimal("352.40")
    assert data.cgst == Decimal("11800.00")
    assert data.sgst is None
    assert data.igst is None
    assert data.round_off == Decimal("-0.02")


def test_absurdly_large_numbers_are_dropped():
    assert ExtractedInvoice.model_validate({"total": "99999999999999"}).total is None


def test_date_parsing_accepts_common_indian_formats():
    for text in ("2026-09-15", "15-09-2026", "15/09/2026"):
        assert ExtractedInvoice.model_validate({"invoice_date": text}).invoice_date == date(2026, 9, 15)
    assert ExtractedInvoice.model_validate({"invoice_date": "garbage"}).invoice_date is None


def test_gstin_is_cleaned_but_never_corrected():
    ok = ExtractedInvoice.model_validate({"gstin": " 33becps1148n1zb "})
    assert ok.gstin == "33BECPS1148N1ZB"

    labelled = ExtractedInvoice.model_validate({"gstin": "GSTIN: 33BECPS1148N1ZB"})
    assert labelled.gstin == "33BECPS1148N1ZB"

    too_long = ExtractedInvoice.model_validate({"gstin": "33BECPS1148N1ZB EXTRA TEXT 123"})
    assert too_long.gstin is None

    # a wrong character is kept as written, so Day 5's checksum can flag it
    wrong = ExtractedInvoice.model_validate({"gstin": "33BECPS1148N1Z8"})
    assert wrong.gstin == "33BECPS1148N1Z8"


def test_line_items_default_to_empty_and_long_text_is_truncated():
    assert ExtractedInvoice.model_validate({"line_items": None}).line_items == []
    assert ExtractedInvoice.model_validate({"vendor_name": "x" * 300}).vendor_name == "x" * 255
    assert ExtractedLineItem().is_empty()
    assert not ExtractedLineItem(description="Tea").is_empty()