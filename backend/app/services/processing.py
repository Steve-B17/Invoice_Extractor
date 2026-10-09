import logging

from app.core.database import SessionLocal
from app.models.invoice import Invoice, InvoiceStatus
from app.services.ocr import OcrError, extract_text

logger = logging.getLogger(__name__)


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
            # Day 4 adds LLM extraction here, Day 5 adds validation
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