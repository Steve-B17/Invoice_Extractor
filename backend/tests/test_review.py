from app.models.invoice import Invoice, InvoiceStatus
from app.models.user import User
from app.schemas.extraction import ExtractedInvoice
from app.services import processing
from app.services.llm import LlmError
from app.services.ocr import OcrResult

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 100

# a fixed old date keeps these tests independent of today's date
GOOD = {
    "vendor_name": "KARTHIK MESS",
    "gstin": "33BECPS1148N1ZB",
    "invoice_number": "501",
    "invoice_date": "2026-01-15",
    "line_items": [
        {"description": "Meals", "quantity": "3", "rate": "47.62", "amount": "142.86"},
        {"description": "Tea", "quantity": "4", "rate": "14.29", "amount": "57.16"},
        {"description": "Curry", "quantity": "2", "rate": "76.19", "amount": "152.38"},
    ],
    "subtotal": "352.40",
    "cgst": "8.81",
    "sgst": "8.81",
    "round_off": "-0.02",
    "total": "370.00",
}


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


def review_ready_invoice(client, db_session, headers) -> int:
    invoice_id = upload(client, headers).json()["id"]
    invoice = db_session.get(Invoice, invoice_id)
    invoice.status = InvoiceStatus.NEEDS_REVIEW.value
    db_session.commit()
    return invoice_id


def flag_codes(body: dict) -> set[str]:
    return {flag["code"] for flag in body["flags"]}


def test_process_invoice_stores_validation_flags(db_session, monkeypatch):
    invoice_id = make_invoice(db_session)
    monkeypatch.setattr(processing, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(
        processing,
        "extract_text",
        lambda path, content_type: OcrResult("text", 0.9, "image_ocr", 1),
    )
    bad = ExtractedInvoice.model_validate({**GOOD, "cgst": "881"})
    monkeypatch.setattr(processing, "extract_invoice_fields", lambda text: bad)

    processing.process_invoice(invoice_id)

    refreshed = db_session.get(Invoice, invoice_id)
    stored = {flag.code for flag in refreshed.flags}
    assert {"CGST_SGST_MISMATCH", "TOTAL_MISMATCH"} <= stored


def test_failed_extraction_adds_a_flag(db_session, monkeypatch):
    invoice_id = make_invoice(db_session)
    monkeypatch.setattr(processing, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(
        processing,
        "extract_text",
        lambda path, content_type: OcrResult("text", 0.9, "image_ocr", 1),
    )

    def boom(text):
        raise LlmError("The AI service returned an error (HTTP 401)")

    monkeypatch.setattr(processing, "extract_invoice_fields", boom)

    processing.process_invoice(invoice_id)

    refreshed = db_session.get(Invoice, invoice_id)
    assert [flag.code for flag in refreshed.flags] == ["EXTRACTION_FAILED"]


def test_patch_updates_fields_and_revalidates(client, db_session):
    headers = auth_headers(client)
    invoice_id = review_ready_invoice(client, db_session, headers)

    res = client.patch(
        f"/invoices/{invoice_id}",
        json={"gstin": "33BECPS1148N1Z8", "total": "370.00"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["gstin"] == "33BECPS1148N1Z8"
    assert "GSTIN_CHECKSUM" in flag_codes(res.json())

    res = client.patch(
        f"/invoices/{invoice_id}", json={"gstin": "33becps1148n1zb"}, headers=headers
    )
    assert res.json()["gstin"] == "33BECPS1148N1ZB"   # normalised to uppercase
    assert "GSTIN_CHECKSUM" not in flag_codes(res.json())


def test_patch_replaces_line_items(client, db_session):
    headers = auth_headers(client)
    invoice_id = review_ready_invoice(client, db_session, headers)

    two = {"line_items": [
        {"description": "Tea", "quantity": "2", "rate": "10.00", "amount": "20.00"},
        {"description": "Coffee", "quantity": "1", "rate": "15.00", "amount": "15.00"},
    ]}
    res = client.patch(f"/invoices/{invoice_id}", json=two, headers=headers)
    assert [item["description"] for item in res.json()["line_items"]] == ["Tea", "Coffee"]

    one = {"line_items": [{"description": "Water", "quantity": "1", "rate": "5.00", "amount": "5.00"}]}
    res = client.patch(f"/invoices/{invoice_id}", json=one, headers=headers)
    assert [item["description"] for item in res.json()["line_items"]] == ["Water"]

    # a request without line_items leaves them alone
    res = client.patch(f"/invoices/{invoice_id}", json={"vendor_name": "X"}, headers=headers)
    assert len(res.json()["line_items"]) == 1


def test_patch_rejects_bad_input(client, db_session):
    headers = auth_headers(client)
    invoice_id = review_ready_invoice(client, db_session, headers)
    url = f"/invoices/{invoice_id}"

    assert client.patch(url, json={"total": "abc"}, headers=headers).status_code == 422
    assert client.patch(url, json={"total": "12.345"}, headers=headers).status_code == 422
    assert client.patch(url, json={"colour": "red"}, headers=headers).status_code == 422
    assert client.patch(url, json={"gstin": "A" * 16}, headers=headers).status_code == 422


def test_patch_and_verify_are_refused_while_processing(client):
    headers = auth_headers(client)
    invoice_id = upload(client, headers).json()["id"]   # a new upload is PROCESSING

    assert client.patch(
        f"/invoices/{invoice_id}", json={"vendor_name": "X"}, headers=headers
    ).status_code == 409
    assert client.post(f"/invoices/{invoice_id}/verify", headers=headers).status_code == 409


def test_verify_needs_force_while_errors_remain_and_then_locks(client, db_session):
    headers = auth_headers(client)
    invoice_id = review_ready_invoice(client, db_session, headers)
    client.patch(
        f"/invoices/{invoice_id}", json={"gstin": "33BECPS1148N1Z8"}, headers=headers
    )

    assert client.post(f"/invoices/{invoice_id}/verify", headers=headers).status_code == 409

    res = client.post(f"/invoices/{invoice_id}/verify?force=true", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "VERIFIED"

    locked = client.patch(f"/invoices/{invoice_id}", json={"vendor_name": "X"}, headers=headers)
    assert locked.status_code == 409


def test_verify_succeeds_without_force_when_there_are_no_errors(client, db_session):
    headers = auth_headers(client)
    invoice_id = review_ready_invoice(client, db_session, headers)

    res = client.patch(f"/invoices/{invoice_id}", json=GOOD, headers=headers)
    assert res.status_code == 200
    assert not [flag for flag in res.json()["flags"] if flag["severity"] == "error"]

    res = client.post(f"/invoices/{invoice_id}/verify", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "VERIFIED"


def test_other_users_cannot_patch_or_verify(client, db_session):
    alice = auth_headers(client, "alice@example.com")
    bob = auth_headers(client, "bob@example.com")
    invoice_id = review_ready_invoice(client, db_session, alice)

    assert client.patch(
        f"/invoices/{invoice_id}", json={"vendor_name": "X"}, headers=bob
    ).status_code == 404
    assert client.post(f"/invoices/{invoice_id}/verify", headers=bob).status_code == 404