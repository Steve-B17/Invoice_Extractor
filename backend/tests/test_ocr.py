import pymupdf
import pytesseract
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.services.ocr import extract_text


def tesseract_available() -> bool:
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def test_pdf_text_layer_is_used_without_ocr(tmp_path):
    pdf_path = tmp_path / "bill.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "TAX INVOICE  GSTIN 33ABCDE1234F1Z5  Total 11800.00  Thank you",
        fontsize=10,
    )
    doc.save(str(pdf_path))
    doc.close()

    result = extract_text(str(pdf_path), "application/pdf")

    assert result.method == "pdf_text_layer"
    assert "33ABCDE1234F1Z5" in result.text
    assert result.confidence == 1.0


@pytest.mark.skipif(not tesseract_available(), reason="Tesseract is not installed")
def test_image_ocr_reads_clean_text(tmp_path):
    img = Image.new("RGB", (1000, 400), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=48)
    draw.text((40, 60), "TAX INVOICE", fill="black", font=font)
    draw.text((40, 160), "TOTAL 11800", fill="black", font=font)
    path = tmp_path / "bill.png"
    img.save(path)

    result = extract_text(str(path), "image/png")

    assert result.method == "image_ocr"
    assert "INVOICE" in result.text.upper()
    assert "11800" in result.text
    assert result.confidence is not None and result.confidence > 0.5