import re
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

MAX_LINE_ITEMS = 100
MONEY_LIMIT = Decimal("9999999999.99")      # fits Numeric(12, 2)
QUANTITY_LIMIT = Decimal("999999999.999")   # fits Numeric(12, 3)
NULL_WORDS = {"null", "none", "n/a", "na", "-", ""}


def _text(max_len: int):
    def clean(value: Any) -> str | None:
        if value is None:
            return None
        text = re.sub(r"\s+", " ", str(value)).strip()
        if text.lower() in NULL_WORDS:
            return None
        return text[:max_len]

    return clean


def _number(places: str, limit: Decimal):
    def clean(value: Any) -> Decimal | None:
        if value is None or isinstance(value, bool):
            return None
        text = str(value).replace("\u2212", "-")                 # unicode minus
        text = re.sub(r"(?i)\brs\.?|inr|₹|,|/-|\s", "", text)    # currency, commas, spaces
        if text.lower() in NULL_WORDS:
            return None
        try:
            number = Decimal(text)
            if not number.is_finite() or abs(number) > limit:
                return None
            return number.quantize(Decimal(places), rounding=ROUND_HALF_UP)
        except InvalidOperation:
            return None

    return clean


DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%y", "%d/%m/%y")


def _date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()[:10]
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _gstin(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"(?i)^\s*gstin(\s*no\.?)?\s*[:\-]?", "", str(value))
    text = re.sub(r"[^A-Za-z0-9]", "", text).upper()
    if not text or len(text) > 15:   # too long to be a GSTIN, and the column holds 15
        return None
    return text


def _list(value: Any) -> list:
    return value if isinstance(value, list) else []


Text255 = Annotated[str | None, BeforeValidator(_text(255))]
Text100 = Annotated[str | None, BeforeValidator(_text(100))]
Text20 = Annotated[str | None, BeforeValidator(_text(20))]
Gstin = Annotated[str | None, BeforeValidator(_gstin)]
Money = Annotated[Decimal | None, BeforeValidator(_number("0.01", MONEY_LIMIT))]
Quantity = Annotated[Decimal | None, BeforeValidator(_number("0.001", QUANTITY_LIMIT))]
Date = Annotated[date | None, BeforeValidator(_date)]


class ExtractedLineItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    description: Text255 = None
    hsn_code: Text20 = None
    quantity: Quantity = None
    rate: Money = None
    amount: Money = None

    def is_empty(self) -> bool:
        return all(
            v is None
            for v in (self.description, self.hsn_code, self.quantity, self.rate, self.amount)
        )


class ExtractedInvoice(BaseModel):
    model_config = ConfigDict(extra="ignore")

    vendor_name: Text255 = None
    gstin: Gstin = None
    invoice_number: Text100 = None
    invoice_date: Date = None
    line_items: Annotated[list[ExtractedLineItem], BeforeValidator(_list)] = Field(
        default_factory=list
    )
    subtotal: Money = None
    cgst: Money = None
    sgst: Money = None
    igst: Money = None
    round_off: Money = None
    total: Money = None

    def is_empty(self) -> bool:
        scalars = (
            self.vendor_name, self.gstin, self.invoice_number, self.invoice_date,
            self.subtotal, self.cgst, self.sgst, self.igst, self.round_off, self.total,
        )
        return all(v is None for v in scalars) and all(
            item.is_empty() for item in self.line_items
        )