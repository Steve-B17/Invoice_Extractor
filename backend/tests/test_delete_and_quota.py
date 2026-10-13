from pathlib import Path

from app.core.config import settings
from app.models.invoice import Invoice, InvoiceStatus

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


def mark_reviewed(db_session, invoice_id) -> str:
    invoice = db_session.get(Invoice, invoice_id)
    invoice.status = InvoiceStatus.NEEDS_REVIEW.value
    db_session.commit()
    return invoice.file_path


def test_deleting_removes_the_invoice_and_its_stored_file(client, db_session):
    headers = auth_headers(client)
    invoice_id = upload(client, headers).json()["id"]
    file_path = mark_reviewed(db_session, invoice_id)
    assert Path(file_path).exists()

    assert client.delete(f"/invoices/{invoice_id}", headers=headers).status_code == 204

    assert client.get(f"/invoices/{invoice_id}", headers=headers).status_code == 404
    assert not Path(file_path).exists()


def test_delete_is_hidden_from_other_users_and_refused_while_processing(client, db_session):
    alice = auth_headers(client, "alice@example.com")
    bob = auth_headers(client, "bob@example.com")
    invoice_id = upload(client, alice).json()["id"]   # still PROCESSING

    assert client.delete(f"/invoices/{invoice_id}", headers=alice).status_code == 409

    mark_reviewed(db_session, invoice_id)
    assert client.delete(f"/invoices/{invoice_id}", headers=bob).status_code == 404
    assert client.delete(f"/invoices/{invoice_id}").status_code == 401
    assert client.get(f"/invoices/{invoice_id}", headers=alice).status_code == 200


def test_the_upload_limit_blocks_extra_uploads_until_something_is_deleted(
    client, db_session, monkeypatch
):
    monkeypatch.setattr(settings, "max_invoices_per_user", 1)
    headers = auth_headers(client)

    first = upload(client, headers)
    assert first.status_code == 202
    assert upload(client, headers).status_code == 429
    assert len(list(Path(settings.upload_dir).rglob("*.png"))) == 1   # the refused file was not stored

    invoice_id = first.json()["id"]
    mark_reviewed(db_session, invoice_id)
    assert client.delete(f"/invoices/{invoice_id}", headers=headers).status_code == 204
    assert upload(client, headers).status_code == 202