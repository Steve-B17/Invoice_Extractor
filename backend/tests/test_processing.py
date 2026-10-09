import pytest

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