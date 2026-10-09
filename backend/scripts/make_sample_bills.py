"""Generate synthetic GST invoices (clean + 'phone photo' versions) with ground truth.

Run from backend/ with the venv active:
    python -m scripts.make_sample_bills
    python -m scripts.make_sample_bills --count 10 --seed 7

Output goes to <repo>/eval/synthetic/ :
    synthetic_01_clean.png   synthetic_01_photo.jpg   synthetic_01.json (the answers)
"""
import argparse
import json
import random
import string
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parents[2] / "eval" / "synthetic"
GSTIN_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
PAGE_W, PAGE_H = 1240, 1754

VENDORS = [
    "Sri Murugan Hardware",
    "Kaveri Traders",
    "Annai Electricals",
    "Lakshmi Building Materials",
    "Vel Agencies",
    "Coimbatore Paints & Tools",
]

ITEMS = [  # (description, HSN code, unit rate in INR)
    ("PVC Pipe 1 inch", "3917", 145),
    ("Wall Putty 20kg", "3214", 890),
    ("LED Bulb 9W", "8539", 95),
    ("Paint Bucket 4L", "3208", 1250),
    ("Ceiling Fan", "8414", 2150),
    ("Switch Board", "8536", 310),
    ("Copper Wire 90m", "8544", 1980),
    ("Door Lock", "8301", 575),
    ("Tiles Box", "6908", 1420),
    ("Steel Hammer", "8205", 260),
]


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def gstin_checksum(first14: str) -> str:
    """The 15th character of a GSTIN (Luhn mod 36). We'll reuse this on Day 5."""
    total = 0
    for i, ch in enumerate(first14):
        product = GSTIN_CHARS.index(ch) * (1 if i % 2 == 0 else 2)
        total += product // 36 + product % 36
    return GSTIN_CHARS[(36 - total % 36) % 36]


def make_gstin(rng: random.Random) -> str:
    pan = (
        "".join(rng.choices(string.ascii_uppercase, k=5))
        + "".join(rng.choices(string.digits, k=4))
        + rng.choice(string.ascii_uppercase)
    )
    first14 = "33" + pan + "1" + "Z"      # 33 = Tamil Nadu
    return first14 + gstin_checksum(first14)


def make_invoice(rng: random.Random) -> dict:
    items = []
    for desc, hsn, rate in rng.sample(ITEMS, rng.randint(3, 5)):
        qty = rng.randint(1, 6)
        items.append({
            "description": desc,
            "hsn": hsn,
            "qty": qty,
            "rate": str(money(Decimal(rate))),
            "amount": str(money(Decimal(rate) * qty)),
        })

    subtotal = sum((Decimal(i["amount"]) for i in items), Decimal("0"))
    cgst = money(subtotal * Decimal("0.09"))
    sgst = cgst
    total = subtotal + cgst + sgst
    invoice_date = date(2026, 1, 1) + timedelta(days=rng.randint(0, 270))

    return {
        "vendor_name": rng.choice(VENDORS),
        "gstin": make_gstin(rng),
        "invoice_number": f"INV-{rng.randint(1000, 9999)}",
        "invoice_date": invoice_date.isoformat(),
        "line_items": items,
        "subtotal": str(subtotal),
        "cgst": str(cgst),
        "sgst": str(sgst),
        "igst": None,
        "total": str(total),
    }


def load_font(size: int):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def right_text(draw, x_right, y, text, font):
    draw.text((x_right - draw.textlength(text, font=font), y), text, font=font, fill="black")


def render_invoice(inv: dict) -> Image.Image:
    img = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    d = ImageDraw.Draw(img)
    title, head, body = load_font(58), load_font(36), load_font(30)

    y = 80
    d.text((80, y), inv["vendor_name"], font=title, fill="black")
    y += 85
    d.text((80, y), "TAX INVOICE", font=head, fill="black")
    y += 65
    d.text((80, y), f"GSTIN: {inv['gstin']}", font=body, fill="black")
    y += 48
    d.text((80, y), f"Invoice No: {inv['invoice_number']}", font=body, fill="black")
    y += 48
    shown_date = date.fromisoformat(inv["invoice_date"]).strftime("%d-%m-%Y")
    d.text((80, y), f"Date: {shown_date}", font=body, fill="black")
    y += 70

    d.line([(80, y), (PAGE_W - 80, y)], fill="black", width=3)
    y += 15
    col = {"desc": 80, "hsn": 640, "qty": 780, "rate": 960, "amount": PAGE_W - 80}
    d.text((col["desc"], y), "Description", font=body, fill="black")
    d.text((col["hsn"], y), "HSN", font=body, fill="black")
    d.text((col["qty"], y), "Qty", font=body, fill="black")
    right_text(d, col["rate"] + 110, y, "Rate", body)
    right_text(d, col["amount"], y, "Amount", body)
    y += 55
    d.line([(80, y), (PAGE_W - 80, y)], fill="black", width=2)
    y += 20

    for item in inv["line_items"]:
        d.text((col["desc"], y), item["description"], font=body, fill="black")
        d.text((col["hsn"], y), item["hsn"], font=body, fill="black")
        d.text((col["qty"], y), str(item["qty"]), font=body, fill="black")
        right_text(d, col["rate"] + 110, y, item["rate"], body)
        right_text(d, col["amount"], y, item["amount"], body)
        y += 55

    y += 10
    d.line([(80, y), (PAGE_W - 80, y)], fill="black", width=3)
    y += 25
    for label, value in (
        ("Subtotal", inv["subtotal"]),
        ("CGST @9%", inv["cgst"]),
        ("SGST @9%", inv["sgst"]),
    ):
        d.text((700, y), label, font=body, fill="black")
        right_text(d, PAGE_W - 80, y, value, body)
        y += 52
    d.line([(700, y), (PAGE_W - 80, y)], fill="black", width=2)
    y += 15
    d.text((700, y), "TOTAL", font=head, fill="black")
    right_text(d, PAGE_W - 80, y, inv["total"], head)
    y += 120
    d.text((80, y), "Thank you for your business. Goods once sold will not be taken back.",
           font=load_font(24), fill="black")
    return img


def phone_photo(img: Image.Image, rng: random.Random, np_rng) -> np.ndarray:
    """Imitate a quick phone snapshot: tilt, uneven lighting, blur, noise, small size."""
    arr = np.array(img)                                   # RGB
    h, w = arr.shape[:2]

    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), rng.uniform(-5, 5), 1.0)
    arr = cv2.warpAffine(arr, matrix, (w, h), flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=(190, 190, 190))

    gradient = np.linspace(rng.uniform(0.55, 0.8), 1.0, w, dtype=np.float32)   # shadow
    if rng.random() < 0.5:
        gradient = gradient[::-1]
    arr = np.clip(arr.astype(np.float32) * gradient[None, :, None], 0, 255)

    arr = cv2.GaussianBlur(arr.astype(np.uint8), (3, 3), 0)
    arr = np.clip(arr + np_rng.normal(0, 6, arr.shape), 0, 255).astype(np.uint8)

    new_w = 1000
    arr = cv2.resize(arr, (new_w, int(h * new_w / w)), interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=6)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    np_rng = np.random.default_rng(args.seed)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for n in range(1, args.count + 1):
        inv = make_invoice(rng)
        clean = render_invoice(inv)
        clean.save(OUT_DIR / f"synthetic_{n:02d}_clean.png")
        cv2.imwrite(
            str(OUT_DIR / f"synthetic_{n:02d}_photo.jpg"),
            phone_photo(clean, rng, np_rng),
            [cv2.IMWRITE_JPEG_QUALITY, 70],
        )
        (OUT_DIR / f"synthetic_{n:02d}.json").write_text(
            json.dumps(inv, indent=2), encoding="utf-8"
        )
        print(f"synthetic_{n:02d}: {inv['vendor_name']}  {inv['gstin']}  total {inv['total']}")

    print(f"\nSaved {args.count * 3} files to {OUT_DIR}")


if __name__ == "__main__":
    main()