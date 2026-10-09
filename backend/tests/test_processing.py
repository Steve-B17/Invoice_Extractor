import pytest
from datetime import date
from decimal import Decimal

from app.models.invoice import LineItem
from app.schemas.extraction import ExtractedInvoice
from app.services.llm import LlmError
from app.models.invoice import Invoice, InvoiceStatus
from app.models.user import User
from app.services import processing
from app.services.ocr import OcrError, OcrResult

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 100


def auth_headers(client, email="user@example.com", password="strongpass123"):
    client.post("/auth/register", json={"email": email, "password": password})
    res = client.post("/auth/login", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def upload(client, headers):
    return client.post(
        "/invoices",
        files={"file": ("bill.png", PNG_BYTES, "image/png")},
        headers=headers,
    )


def make_invoice(db) -> int:
    user = User(email="p@example.com", hashed_password="x")
    db.add(user)
    db.commit()
    invoice = Invoice(
        user_id=user.id,
        original_filename="a.png",
        file_path="x",
        content_type="image/png",
        status=InvoiceStatus.PROCESSING.value,
    )
    db.add(invoice)
    db.commit()
    return invoice.id


def test_process_invoice_saves_ocr_text(db_session, monkeypatch):
    invoice_id = make_invoice(db_session)
    monkeypatch.setattr(processing, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(
        processing,
        "extract_text",
        lambda path, content_type: OcrResult(
            "TAX INVOICE\nTotal 11800", 0.91, "image_ocr", 1
        ),
    )

    processing.process_invoice(invoice_id)

    refreshed = db_session.get(Invoice, invoice_id)
    assert refreshed.status == InvoiceStatus.NEEDS_REVIEW.value
    assert "11800" in refreshed.raw_ocr_text
    assert refreshed.confidence == pytest.approx(0.91)


def test_process_invoice_marks_failed_when_ocr_fails(db_session, monkeypatch):
    invoice_id = make_invoice(db_session)
    monkeypatch.setattr(processing, "SessionLocal", lambda: db_session)

    def boom(path, content_type):
        raise OcrError("Tesseract is not installed")

    monkeypatch.setattr(processing, "extract_text", boom)

    processing.process_invoice(invoice_id)

    refreshed = db_session.get(Invoice, invoice_id)
    assert refreshed.status == InvoiceStatus.FAILED.value
    assert "Tesseract" in refreshed.error_message


def test_process_invoice_fails_when_no_text_is_found(db_session, monkeypatch):
    invoice_id = make_invoice(db_session)
    monkeypatch.setattr(processing, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(
        processing,
        "extract_text",
        lambda path, content_type: OcrResult("   ", None, "image_ocr", 1),
    )

    processing.process_invoice(invoice_id)

    refreshed = db_session.get(Invoice, invoice_id)
    assert refreshed.status == InvoiceStatus.FAILED.value
    assert "No text" in refreshed.error_message


def test_ocr_endpoint_returns_text_for_the_owner(client, db_session):
    headers = auth_headers(client)
    invoice_id = upload(client, headers).json()["id"]

    invoice = db_session.get(Invoice, invoice_id)
    invoice.raw_ocr_text = "TAX INVOICE"
    invoice.confidence = 0.88
    db_session.commit()

    res = client.get(f"/invoices/{invoice_id}/ocr", headers=headers)
    assert res.status_code == 200
    assert res.json() == {"raw_ocr_text": "TAX INVOICE", "confidence": 0.88}


def test_ocr_endpoint_is_hidden_from_other_users(client):
    alice = auth_headers(client, "alice@example.com")
    bob = auth_headers(client, "bob@example.com")
    invoice_id = upload(client, alice).json()["id"]

    assert client.get(f"/invoices/{invoice_id}/ocr", headers=bob).status_code == 404

def test_process_invoice_stores_extracted_fields_and_line_items(db_session, monkeypatch):
    invoice_id = make_invoice(db_session)
    monkeypatch.setattr(processing, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(
        processing,
        "extract_text",
        lambda path, content_type: OcrResult("KARTHIK MESS ...", 0.9, "image_ocr", 1),
    )
    extracted = ExtractedInvoice.model_validate(
        {
            "vendor_name": "KARTHIK MESS",
            "gstin": "33BECPS1148N1ZB",
            "invoice_number": "501",
            "invoice_date": "15-09-2026",
            "subtotal": "352.40",
            "cgst": "8.81",
            "sgst": "8.81",
            "round_off": "-0.02",
            "total": "370.00",
            "line_items": [
                {"description": "Meals", "quantity": 3, "rate": "47.62", "amount": "142.86"},
                {"description": "Tea", "quantity": 4, "rate": "14.29", "amount": "57.16"},
                {"description": None},   # an empty row, which is skipped
            ],
        }
    )
    monkeypatch.setattr(processing, "extract_invoice_fields", lambda text: extracted)

    processing.process_invoice(invoice_id)

    refreshed = db_session.get(Invoice, invoice_id)
    assert refreshed.status == InvoiceStatus.NEEDS_REVIEW.value
    assert refreshed.error_message is None
    assert refreshed.vendor_name == "KARTHIK MESS"
    assert refreshed.gstin == "33BECPS1148N1ZB"
    assert refreshed.invoice_date == date(2026, 9, 15)
    assert refreshed.total == Decimal("370.00")
    assert refreshed.round_off == Decimal("-0.02")
    assert [item.description for item in refreshed.line_items] == ["Meals", "Tea"]


def test_process_invoice_keeps_ocr_text_when_extraction_fails(db_session, monkeypatch):
    invoice_id = make_invoice(db_session)
    monkeypatch.setattr(processing, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(
        processing,
        "extract_text",
        lambda path, content_type: OcrResult("TAX INVOICE Total 11800", 0.8, "image_ocr", 1),
    )

    def boom(text):
        raise LlmError("The AI service returned an error (HTTP 401)")

    monkeypatch.setattr(processing, "extract_invoice_fields", boom)

    processing.process_invoice(invoice_id)

    refreshed = db_session.get(Invoice, invoice_id)
    assert refreshed.status == InvoiceStatus.NEEDS_REVIEW.value
    assert "11800" in refreshed.raw_ocr_text
    assert refreshed.error_message.startswith("Automatic extraction failed")
    assert refreshed.vendor_name is None


def test_process_invoice_without_llm_still_reaches_review(db_session, monkeypatch):
    invoice_id = make_invoice(db_session)
    monkeypatch.setattr(processing, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(
        processing,
        "extract_text",
        lambda path, content_type: OcrResult("TAX INVOICE", 0.8, "image_ocr", 1),
    )

    processing.process_invoice(invoice_id)

    refreshed = db_session.get(Invoice, invoice_id)
    assert refreshed.status == InvoiceStatus.NEEDS_REVIEW.value
    assert "not configured" in refreshed.error_message


def test_invoice_endpoint_returns_line_items(client, db_session):
    headers = auth_headers(client)
    invoice_id = upload(client, headers).json()["id"]

    invoice = db_session.get(Invoice, invoice_id)
    invoice.line_items.append(
        LineItem(
            position=0,
            description="Tea",
            quantity=Decimal("2"),
            rate=Decimal("10.00"),
            amount=Decimal("20.00"),
        )
    )
    db_session.commit()

    body = client.get(f"/invoices/{invoice_id}", headers=headers).json()
    assert len(body["line_items"]) == 1
    assert body["line_items"][0]["description"] == "Tea"
    assert Decimal(body["line_items"][0]["amount"]) == Decimal("20.00")


def test_reprocess_requeues_own_invoice(client, db_session):
    headers = auth_headers(client)
    invoice_id = upload(client, headers).json()["id"]

    # a freshly uploaded invoice is still PROCESSING, so reprocessing is refused
    assert client.post(f"/invoices/{invoice_id}/reprocess", headers=headers).status_code == 409

    invoice = db_session.get(Invoice, invoice_id)
    invoice.status = InvoiceStatus.NEEDS_REVIEW.value
    invoice.error_message = "Automatic extraction failed: something"
    db_session.commit()

    res = client.post(f"/invoices/{invoice_id}/reprocess", headers=headers)
    assert res.status_code == 202
    assert res.json()["status"] == "PROCESSING"
    assert res.json()["error_message"] is None


def test_reprocess_is_hidden_from_other_users(client):
    alice = auth_headers(client, "alice@example.com")
    bob = auth_headers(client, "bob@example.com")
    invoice_id = upload(client, alice).json()["id"]

    assert client.post(f"/invoices/{invoice_id}/reprocess", headers=bob).status_code == 404