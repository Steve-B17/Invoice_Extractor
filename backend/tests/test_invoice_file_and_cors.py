from pathlib import Path

from app.models.invoice import Invoice

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


def test_owner_can_download_the_stored_file(client):
    headers = auth_headers(client)
    invoice_id = upload(client, headers).json()["id"]

    res = client.get(f"/invoices/{invoice_id}/file", headers=headers)

    assert res.status_code == 200
    assert res.content == PNG_BYTES
    assert res.headers["content-type"] == "image/png"


def test_other_users_cannot_download_the_file(client):
    alice = auth_headers(client, "alice@example.com")
    bob = auth_headers(client, "bob@example.com")
    invoice_id = upload(client, alice).json()["id"]

    assert client.get(f"/invoices/{invoice_id}/file", headers=bob).status_code == 404
    assert client.get(f"/invoices/{invoice_id}/file").status_code == 401


def test_a_missing_file_on_disk_gives_404(client, db_session):
    headers = auth_headers(client)
    invoice_id = upload(client, headers).json()["id"]
    Path(db_session.get(Invoice, invoice_id).file_path).unlink()

    assert client.get(f"/invoices/{invoice_id}/file", headers=headers).status_code == 404


def test_the_frontend_origin_is_allowed_by_cors(client):
    res = client.options(
        "/invoices",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "http://localhost:5173"