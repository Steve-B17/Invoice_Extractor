from app.models.invoice import Invoice, ValidationFlag
from app.schemas.extraction import ExtractedInvoice, ExtractedLineItem
from app.services.validation import ERROR, Flag, validate_invoice


def invoice_to_data(invoice: Invoice) -> ExtractedInvoice:
    """Rebuild the validator's input from what is currently stored (including user edits)."""
    return ExtractedInvoice(
        vendor_name=invoice.vendor_name,
        gstin=invoice.gstin,
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        subtotal=invoice.subtotal,
        cgst=invoice.cgst,
        sgst=invoice.sgst,
        igst=invoice.igst,
        round_off=invoice.round_off,
        total=invoice.total,
        line_items=[
            ExtractedLineItem(
                description=item.description,
                hsn_code=item.hsn_code,
                quantity=item.quantity,
                rate=item.rate,
                amount=item.amount,
            )
            for item in invoice.line_items
        ],
    )


def _store(invoice: Invoice, flags: list[Flag]) -> None:
    invoice.flags.clear()   # old flags are replaced, never accumulated
    for flag in flags:
        invoice.flags.append(
            ValidationFlag(
                field=flag.field,
                code=flag.code,
                severity=flag.severity,
                message=flag.message[:500],
            )
        )


def revalidate(invoice: Invoice) -> None:
    flags = validate_invoice(invoice_to_data(invoice), ocr_confidence=invoice.confidence)
    _store(invoice, flags)


def mark_extraction_failed(invoice: Invoice, message: str) -> None:
    _store(invoice, [Flag("invoice", "EXTRACTION_FAILED", ERROR, message)])