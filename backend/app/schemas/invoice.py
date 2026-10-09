from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.invoice import InvoiceStatus


class LineItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    description: str | None = None
    hsn_code: str | None = None
    quantity: Decimal | None = None
    rate: Decimal | None = None
    amount: Decimal | None = None


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
    round_off: Decimal | None = None
    total: Decimal | None = None
    line_items: list[LineItemOut] = []

    created_at: datetime
    updated_at: datetime


class InvoiceOcrOut(BaseModel):
    raw_ocr_text: str | None = None
    confidence: float | None = None