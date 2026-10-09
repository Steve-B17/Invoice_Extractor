from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.invoice import InvoiceStatus


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    content_type: str
    status: InvoiceStatus
    error_message: str | None = None
    confidence: float | None = None

    vendor_name: str | None = None
    gstin: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    subtotal: Decimal | None = None
    cgst: Decimal | None = None
    sgst: Decimal | None = None
    igst: Decimal | None = None
    total: Decimal | None = None

    created_at: datetime
    updated_at: datetime

class InvoiceOcrOut(BaseModel):
    raw_ocr_text: str | None = None
    confidence: float | None = None