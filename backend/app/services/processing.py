import time

from app.core.database import SessionLocal
from app.models.invoice import Invoice, InvoiceStatus


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
            # Placeholder. Days 3 to 5 replace this with OCR + LLM + validation.
            time.sleep(3)
            invoice.status = InvoiceStatus.NEEDS_REVIEW.value
        except Exception as exc:
            invoice.status = InvoiceStatus.FAILED.value
            invoice.error_message = str(exc)[:500]
        db.commit()
    finally:
        db.close()