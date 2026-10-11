import csv
import io
from decimal import Decimal

from app.models.invoice import Invoice, InvoiceStatus, LineItem

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


def stored_invoice(client, db_session, headers, status, vendor="KARTHIK MESS", items=()):
    invoice_id = upload(client, headers).json()["id"]
    invoice = db_session.get(Invoice, invoice_id)
    invoice.status = status.value
    invoice.vendor_name = vendor
    invoice.total = Decimal("370.00")
    invoice.round_off = Decimal("-0.02")
    for position, description in enumerate(items):
        invoice.line_items.append(
            LineItem(
                position=position,
                description=description,
                quantity=Decimal("1"),
                rate=Decimal("5.00"),
                amount=Decimal("5.00"),
            )
        )
    db_session.commit()
    return invoice_id


def download(client, headers, url) -> list[dict]:
    res = client.get(url, headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "attachment" in res.headers["content-disposition"]
    text = res.content.decode("utf-8")
    assert text.startswith("\ufeff")
    return list(csv.DictReader(io.StringIO(text.lstrip("\ufeff"))))


def test_export_defaults_to_verified_invoices_only(client, db_session):
    headers = auth_headers(client)
    stored_invoice(client, db_session, headers, InvoiceStatus.VERIFIED)
    stored_invoice(client, db_session, headers, InvoiceStatus.NEEDS_REVIEW)

    rows = download(client, headers, "/invoices/export")

    assert len(rows) == 1
    assert rows[0]["status"] == "VERIFIED"
    assert rows[0]["total"] == "370.00"
    assert rows[0]["round_off"] == "-0.02"


def test_export_can_include_every_status(client, db_session):
    headers = auth_headers(client)
    stored_invoice(client, db_session, headers, InvoiceStatus.VERIFIED)
    stored_invoice(client, db_session, headers, InvoiceStatus.NEEDS_REVIEW)

    assert len(download(client, headers, "/invoices/export?status=ALL")) == 2
    assert len(download(client, headers, "/invoices/export?status=needs_review")) == 1


def test_export_items_gives_one_row_per_line_item(client, db_session):
    headers = auth_headers(client)
    stored_invoice(
        client, db_session, headers, InvoiceStatus.VERIFIED, items=("தேநீர்", "இட்லி")
    )

    rows = download(client, headers, "/invoices/export?kind=items")

    assert [row["description"] for row in rows] == ["தேநீர்", "இட்லி"]
    assert [row["item_no"] for row in rows] == ["1", "2"]


def test_export_contains_only_the_callers_invoices(client, db_session):
    alice = auth_headers(client, "alice@example.com")
    bob = auth_headers(client, "bob@example.com")
    stored_invoice(client, db_session, alice, InvoiceStatus.VERIFIED, vendor="ALICE SHOP")
    stored_invoice(client, db_session, bob, InvoiceStatus.VERIFIED, vendor="BOB SHOP")

    rows = download(client, alice, "/invoices/export")

    assert [row["vendor_name"] for row in rows] == ["ALICE SHOP"]


def test_export_needs_a_login_and_rejects_bad_options(client):
    assert client.get("/invoices/export").status_code == 401

    headers = auth_headers(client)
    assert client.get("/invoices/export?status=nonsense", headers=headers).status_code == 422
    assert client.get("/invoices/export?kind=other", headers=headers).status_code == 422