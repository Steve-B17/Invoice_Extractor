import csv
import io
from typing import Literal

BOM = "\ufeff"   # makes Excel read the file as UTF-8, so Tamil text displays correctly

INVOICE_COLUMNS = [
    "invoice_id", "status", "uploaded_at", "vendor_name", "gstin", "invoice_number",
    "invoice_date", "subtotal", "cgst", "sgst", "igst", "round_off", "total",
    "line_item_count", "error_flags", "warning_flags", "original_filename",
]
ITEM_COLUMNS = [
    "invoice_id", "vendor_name", "invoice_number", "invoice_date",
    "item_no", "description", "hsn_code", "quantity", "rate", "amount",
]


def text_cell(value) -> str:
    """Text taken from a bill or typed by a user must never run as a spreadsheet formula
    (CSV injection), so anything starting with = + - @ gets a leading apostrophe."""
    if value is None:
        return ""
    text = str(value)
    if text[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


def number_cell(value) -> str:
    """Plain decimal text. Numbers are not passed through text_cell, so -0.02 stays -0.02."""
    return "" if value is None else format(value, "f")


def date_cell(value) -> str:
    return "" if value is None else value.isoformat()


def build_csv(invoices, kind: Literal["invoices", "items"]) -> str:
    buffer = io.StringIO()
    buffer.write(BOM)
    writer = csv.writer(buffer)

    if kind == "items":
        writer.writerow(ITEM_COLUMNS)
        for invoice in invoices:
            for number, item in enumerate(invoice.line_items, start=1):
                writer.writerow([
                    invoice.id,
                    text_cell(invoice.vendor_name),
                    text_cell(invoice.invoice_number),
                    date_cell(invoice.invoice_date),
                    number,
                    text_cell(item.description),
                    text_cell(item.hsn_code),
                    number_cell(item.quantity),
                    number_cell(item.rate),
                    number_cell(item.amount),
                ])
    else:
        writer.writerow(INVOICE_COLUMNS)
        for invoice in invoices:
            errors = sum(1 for flag in invoice.flags if flag.severity == "error")
            writer.writerow([
                invoice.id,
                invoice.status,
                "" if invoice.created_at is None else invoice.created_at.isoformat(timespec="seconds"),
                text_cell(invoice.vendor_name),
                text_cell(invoice.gstin),
                text_cell(invoice.invoice_number),
                date_cell(invoice.invoice_date),
                number_cell(invoice.subtotal),
                number_cell(invoice.cgst),
                number_cell(invoice.sgst),
                number_cell(invoice.igst),
                number_cell(invoice.round_off),
                number_cell(invoice.total),
                len(invoice.line_items),
                errors,
                len(invoice.flags) - errors,
                text_cell(invoice.original_filename),
            ])
    return buffer.getvalue()