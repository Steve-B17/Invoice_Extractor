from dataclasses import dataclass
from statistics import mean, median

import cv2
import numpy as np
import pymupdf
import pytesseract
from PIL import Image, ImageOps
from pytesseract import Output

from app.core.config import settings
from app.services.image_preprocess import crop_to_document, preprocess

# Pillow raises an error above 2x this many pixels (decompression-bomb protection)
Image.MAX_IMAGE_PIXELS = 50_000_000

MIN_TEXT_LAYER_CHARS = 50   # fewer characters than this means the PDF is a scan
PDF_RENDER_DPI = 200

if settings.tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


class OcrError(Exception):
    """A problem we can explain to the user (shown as the invoice's error message)."""


@dataclass
class OcrResult:
    text: str
    confidence: float | None   # 0.0 to 1.0, None if nothing was read
    method: str                # "image_ocr", "pdf_text_layer" or "pdf_ocr"
    pages: int


def load_image_gray(path: str, *, crop: bool = True) -> np.ndarray:
    """Open an image, apply the phone's EXIF rotation, optionally cut it down to the
    paper, and return a grayscale array."""
    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)   # phone photos often store rotation here
            rgb = np.array(img.convert("RGB"))
    except Exception as exc:
        raise OcrError("Could not open the image file") from exc

    if crop:
        rgb = crop_to_document(rgb)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

def ocr_gray(gray: np.ndarray, *, use_preprocess: bool = True) -> tuple[str, float | None]:
    image = preprocess(gray) if use_preprocess else gray
    config = f"--oem 3 --psm {settings.ocr_psm}"

    try:
        data = pytesseract.image_to_data(
            image,
            lang=settings.ocr_language,
            config=config,
            output_type=Output.DICT,
        )
    except pytesseract.TesseractNotFoundError as exc:
        raise OcrError(
            "Tesseract is not installed or TESSERACT_CMD is wrong"
        ) from exc
    except pytesseract.TesseractError as exc:
        raise OcrError("The OCR engine failed to read this file") from exc

    lines: dict[tuple[int, int, int], list[str]] = {}
    confidences: list[float] = []
    for i, word in enumerate(data["text"]):
        word = word.strip()
        conf = float(data["conf"][i])
        if not word or conf < 0:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append(word)
        confidences.append(conf)

    text = "\n".join(" ".join(words) for _, words in sorted(lines.items()))
    confidence = median(confidences) / 100 if confidences else None
    return text, confidence


def _render_pdf_page(page: pymupdf.Page) -> np.ndarray:
    pix = page.get_pixmap(dpi=PDF_RENDER_DPI, colorspace=pymupdf.csGRAY, alpha=False)
    # rows can be padded, so reshape with the stride and then cut to the width
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.stride)
    return arr[:, : pix.width].copy()


def _extract_from_pdf(path: str, use_preprocess: bool) -> OcrResult:
    try:
        doc = pymupdf.open(path)
    except Exception as exc:
        raise OcrError("Could not open the PDF") from exc

    with doc:
        if len(doc) == 0:
            raise OcrError("The PDF has no pages")
        pages = min(len(doc), settings.max_pdf_pages)

        # Digital PDFs already contain exact text, so there is nothing to OCR
        layer = "\n".join(doc[i].get_text() for i in range(pages)).strip()
        if len(layer) >= MIN_TEXT_LAYER_CHARS:
            return OcrResult(layer, 1.0, "pdf_text_layer", pages)

        # Scanned PDF: render each page to an image and OCR it
        texts: list[str] = []
        confidences: list[float] = []
        for i in range(pages):
            gray = _render_pdf_page(doc[i])
            text, conf = ocr_gray(gray, use_preprocess=use_preprocess)
            texts.append(text)
            if conf is not None:
                confidences.append(conf)

    return OcrResult(
        "\n".join(texts).strip(),
        mean(confidences) if confidences else None,
        "pdf_ocr",
        pages,
    )


def extract_text(path: str, content_type: str, *, use_preprocess: bool = True) -> OcrResult:
    """The one function the rest of the app calls."""
    if content_type == "application/pdf":
        return _extract_from_pdf(path, use_preprocess)

    gray = load_image_gray(path, crop=use_preprocess)
    text, confidence = ocr_gray(gray, use_preprocess=use_preprocess)
    return OcrResult(text, confidence, "image_ocr", 1)