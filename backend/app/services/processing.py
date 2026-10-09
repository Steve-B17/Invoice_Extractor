import logging

from app.core.database import SessionLocal
from app.models.invoice import Invoice, InvoiceStatus, LineItem
from app.schemas.extraction import MAX_LINE_ITEMS, ExtractedInvoice
from app.services.extraction import extract_invoice_fields
from app.services.llm import LlmError
from app.services.ocr import OcrError, extract_text

logger = logging.getLogger(__name__)


def apply_extraction(invoice: Invoice, data: ExtractedInvoice) -> None:
    invoice.vendor_name = data.vendor_name
    invoice.gstin = data.gstin
    invoice.invoice_number = data.invoice_number
    invoice.invoice_date = data.invoice_date
    invoice.subtotal = data.subtotal
    invoice.cgst = data.cgst
    invoice.sgst = data.sgst
    invoice.igst = data.igst
    invoice.round_off = data.round_off
    invoice.total = data.total

    items = [item for item in data.line_items if not item.is_empty()][:MAX_LINE_ITEMS]
    invoice.line_items.clear()   # reprocessing replaces the old rows
    for position, item in enumerate(items):
        invoice.line_items.append(
            LineItem(
                position=position,
                description=item.description,
                hsn_code=item.hsn_code,
                quantity=item.quantity,
                rate=item.rate,
                amount=item.amount,
            )
        )


def process_invoice(invoice_id: int) -> None:
    """Runs after the HTTP response has been sent.

    It opens its OWN database session, because the request's session is
    closed as soon as the request finishes.
    """
    db = SessionLocal()
    try:
        invoice = db.get(Invoice, invoice_id)
        if invoice is None:
            return
        try:
            result = extract_text(invoice.file_path, invoice.content_type)
            if not result.text.strip():
                raise OcrError("No text could be read from this file")

            invoice.raw_ocr_text = result.text
            invoice.confidence = result.confidence
            invoice.error_message = None

            # Extraction problems never lose the OCR text: the invoice still goes
            # to review so a human can fill in the fields by hand.
            try:
                data = extract_invoice_fields(result.text)
                if data.is_empty():
                    raise LlmError("The AI found no invoice fields in the text")
                apply_extraction(invoice, data)
            except LlmError as exc:
                invoice.error_message = f"Automatic extraction failed: {exc}"[:500]
            except Exception:
                logger.exception("Extraction crashed for invoice %s", invoice_id)
                invoice.error_message = "Automatic extraction failed unexpectedly"

            # Day 5 adds validation here
            invoice.status = InvoiceStatus.NEEDS_REVIEW.value
        except OcrError as exc:
            invoice.status = InvoiceStatus.FAILED.value
            invoice.error_message = str(exc)[:500]
        except Exception:
            logger.exception("Invoice %s failed during processing", invoice_id)
            invoice.status = InvoiceStatus.FAILED.value
            invoice.error_message = "Unexpected error while processing the file"
        db.commit()
    finally:
        db.close()