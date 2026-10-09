from decimal import Decimal

import pytest

from app.services import extraction
from app.services.llm import LlmError

GOOD_REPLY = """{
  "vendor_name": "KARTHIK MESS",
  "gstin": "33BECPS1148N1ZB",
  "invoice_date": "2026-09-15",
  "line_items": [{"description": "Meals", "quantity": "3", "rate": "47.62", "amount": "142.86"}],
  "subtotal": "352.40",
  "total": "370.00"
}"""


def test_parse_json_object_tolerates_fences_and_chatter():
    assert extraction.parse_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert extraction.parse_json_object('Sure! Here it is: {"a": 1} Hope that helps.') == {"a": 1}
    with pytest.raises(ValueError):
        extraction.parse_json_object("no json here")


def test_extract_returns_validated_invoice(monkeypatch):
    monkeypatch.setattr(extraction, "chat", lambda messages: GOOD_REPLY)

    data = extraction.extract_invoice_fields("KARTHIK MESS ...")

    assert data.vendor_name == "KARTHIK MESS"
    assert data.total == Decimal("370.00")
    assert len(data.line_items) == 1
    assert data.line_items[0].amount == Decimal("142.86")


def test_extract_retries_once_when_the_first_reply_is_bad(monkeypatch):
    replies = iter(["I could not find an invoice, sorry.", GOOD_REPLY])
    calls = []

    def fake_chat(messages):
        calls.append(len(messages))
        return next(replies)

    monkeypatch.setattr(extraction, "chat", fake_chat)

    data = extraction.extract_invoice_fields("text")

    assert data.vendor_name == "KARTHIK MESS"
    assert calls == [2, 4]   # the retry carried the bad reply and the error message


def test_extract_gives_up_after_two_bad_replies(monkeypatch):
    monkeypatch.setattr(extraction, "chat", lambda messages: "still not json")

    with pytest.raises(LlmError):
        extraction.extract_invoice_fields("text")