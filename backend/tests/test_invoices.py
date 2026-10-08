from pathlib import Path

from app.core.config import settings

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 100


def auth_headers(client, email="user@example.com", password="strongpass123"):
    client.post("/auth/register", json={"email": email, "password": password})
    res = client.post("/auth/login", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def upload(client, headers, data=PNG_BYTES, name="bill.png", mime="image/png"):
    return client.post(
        "/invoices", files={"file": (name, data, mime)}, headers=headers
    )


def test_upload_success(client):
    headers = auth_headers(client)
    res = upload(client, headers)
    assert res.status_code == 202
    body = res.json()
    assert body["status"] == "PROCESSING"
    assert body["original_filename"] == "bill.png"
    assert body["content_type"] == "image/png"
    assert "file_path" not in body
    # the file really exists on disk under the temp upload dir
    stored = list(Path(settings.upload_dir).rglob("*.png"))
    assert len(stored) == 1


def test_upload_requires_auth(client):
    res = client.post(
        "/invoices", files={"file": ("bill.png", PNG_BYTES, "image/png")}
    )
    assert res.status_code == 401


def test_upload_rejects_wrong_file_type(client):
    headers = auth_headers(client)
    # a text file pretending to be a PNG: name and content type lie
    res = upload(client, headers, data=b"just some text", name="fake.png")
    assert res.status_code == 415


def test_upload_rejects_empty_file(client):
    headers = auth_headers(client)
    res = upload(client, headers, data=b"")
    assert res.status_code == 400


def test_upload_rejects_too_large_file(client, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    headers = auth_headers(client)
    too_big = b"\x89PNG\r\n\x1a\n" + b"0" * (1024 * 1024)
    res = upload(client, headers, data=too_big)
    assert res.status_code == 413
    # the partial file was cleaned up
    assert list(Path(settings.upload_dir).rglob("*.png")) == []


def test_list_returns_only_own_invoices(client):
    alice = auth_headers(client, "alice@example.com")
    bob = auth_headers(client, "bob@example.com")
    upload(client, alice)
    upload(client, alice)
    upload(client, bob)

    assert len(client.get("/invoices", headers=alice).json()) == 2
    assert len(client.get("/invoices", headers=bob).json()) == 1


def test_cannot_read_someone_elses_invoice(client):
    alice = auth_headers(client, "alice@example.com")
    bob = auth_headers(client, "bob@example.com")
    invoice_id = upload(client, alice).json()["id"]

    assert client.get(f"/invoices/{invoice_id}", headers=alice).status_code == 200
    assert client.get(f"/invoices/{invoice_id}", headers=bob).status_code == 404


def test_get_missing_invoice_returns_404(client):
    headers = auth_headers(client)
    assert client.get("/invoices/9999", headers=headers).status_code == 404


def test_process_invoice_moves_to_needs_review(db_session, monkeypatch):
    from app.models.invoice import Invoice, InvoiceStatus
    from app.models.user import User
    from app.services import processing

    user = User(email="p@example.com", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    invoice = Invoice(
        user_id=user.id,
        original_filename="a.png",
        file_path="x",
        content_type="image/png",
        status=InvoiceStatus.PROCESSING.value,
    )
    db_session.add(invoice)
    db_session.commit()
    invoice_id = invoice.id

    # run the job against the test database, without the 3-second wait
    monkeypatch.setattr(processing, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(processing.time, "sleep", lambda seconds: None)

    processing.process_invoice(invoice_id)

    refreshed = db_session.get(Invoice, invoice_id)
    assert refreshed.status == InvoiceStatus.NEEDS_REVIEW.value