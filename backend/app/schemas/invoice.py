from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

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


class FlagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field: str
    code: str
    severity: str
    message: str


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
    flags: list[FlagOut] = []

    created_at: datetime
    updated_at: datetime


class InvoiceOcrOut(BaseModel):
    raw_ocr_text: str | None = None
    confidence: float | None = None


# Corrections come from a person, so unlike LLM output they are validated STRICTLY:
# a typo gets a 422 instead of being silently turned into null.
class LineItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str | None = Field(default=None, max_length=255)
    hsn_code: str | None = Field(default=None, max_length=20)
    quantity: Decimal | None = Field(default=None, max_digits=12, decimal_places=3)
    rate: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
    amount: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)


class InvoiceUpdate(BaseModel):
    """Only the fields you send are changed. Send null to clear a field.
    Sending line_items replaces ALL line items."""

    model_config = ConfigDict(extra="forbid")

    vendor_name: str | None = Field(default=None, max_length=255)
    gstin: str | None = Field(default=None, max_length=15)
    invoice_number: str | None = Field(default=None, max_length=100)
    invoice_date: date | None = None
    subtotal: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
    cgst: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
    sgst: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
    igst: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
    round_off: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
    total: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
    line_items: list[LineItemUpdate] | None = Field(default=None, max_length=100)

    @field_validator("gstin")
    @classmethod
    def normalise_gstin(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip().upper() or None