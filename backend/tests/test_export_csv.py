import csv
import io
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace as NS

from app.services.export import build_csv


def make_invoice(**overrides):
    values = dict(
        id=1,
        status="VERIFIED",
        created_at=datetime(2026, 10, 9, 11, 30, 5),
        vendor_name="KARTHIK MESS",
        gstin="33BECPS1148N1ZB",
        invoice_number="501",
        invoice_date=date(2026, 9, 15),
        subtotal=Decimal("352.40"),
        cgst=Decimal("8.81"),
        sgst=Decimal("8.81"),
        igst=None,
        round_off=Decimal("-0.02"),
        total=Decimal("370.00"),
        original_filename="bill.jpg",
        line_items=[
            NS(description="இட்லி", hsn_code=None, quantity=Decimal("4.000"),
               rate=Decimal("14.29"), amount=Decimal("57.16")),
        ],
        flags=[NS(severity="error"), NS(severity="warning"), NS(severity="warning")],
    )
    values.update(overrides)
    return NS(**values)


def read_rows(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text.lstrip("\ufeff"))))


def test_invoice_csv_has_one_row_per_invoice_with_plain_numbers():
    text = build_csv([make_invoice()], "invoices")
    assert text.startswith("\ufeff")
    row = read_rows(text)[0]
    assert row["invoice_id"] == "1"
    assert row["invoice_date"] == "2026-09-15"
    assert row["uploaded_at"] == "2026-10-09T11:30:05"
    assert row["total"] == "370.00"
    assert row["round_off"] == "-0.02"
    assert row["igst"] == ""
    assert (row["line_item_count"], row["error_flags"], row["warning_flags"]) == ("1", "1", "2")


def test_item_csv_has_one_row_per_line_item_and_keeps_tamil():
    rows = read_rows(build_csv([make_invoice()], "items"))
    assert len(rows) == 1
    assert rows[0]["item_no"] == "1"
    assert rows[0]["description"] == "இட்லி"
    assert rows[0]["quantity"] == "4.000"
    assert rows[0]["amount"] == "57.16"


def test_text_that_looks_like_a_formula_is_defused_but_numbers_are_not():
    evil = make_invoice(
        vendor_name='=HYPERLINK("http://evil.example","click")',
        invoice_number="-5",
        original_filename="@bill.jpg",
    )
    row = read_rows(build_csv([evil], "invoices"))[0]
    assert row["vendor_name"].startswith("'=")
    assert row["invoice_number"] == "'-5"
    assert row["original_filename"] == "'@bill.jpg"
    assert row["round_off"] == "-0.02"