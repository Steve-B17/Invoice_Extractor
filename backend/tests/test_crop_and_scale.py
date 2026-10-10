import cv2
import numpy as np

from app.services.image_preprocess import (
    TARGET_GLYPH_HEIGHT,
    crop_to_document,
    measure_glyph_height,
    normalize_scale,
)

YELLOW = (230, 180, 40)


def receipt_on_fabric() -> np.ndarray:
    """A white 'receipt' (500 x 700) lying on a saturated yellow background."""
    image = np.full((1000, 1500, 3), YELLOW, dtype=np.uint8)
    cv2.rectangle(image, (400, 150), (900, 850), (250, 250, 250), thickness=-1)
    return image


def text_page(glyph_px: int, width: int = 1600, height: int = 1200) -> np.ndarray:
    """White page covered in rows of black characters, each about glyph_px tall."""
    page = np.full((height, width), 255, dtype=np.uint8)
    scale = glyph_px / 22.0   # cv2's simplex font is about 22 px tall at scale 1.0
    for row, y in enumerate(range(glyph_px * 2, height - glyph_px, int(glyph_px * 2.2))):
        cv2.putText(page, f"TOTAL {row}234567890 ABCDEFGH", (40, y),
                    cv2.FONT_HERSHEY_SIMPLEX, scale, 0, max(1, int(scale * 1.5)))
    return page


def test_crop_cuts_a_white_receipt_out_of_a_coloured_background():
    cropped = crop_to_document(receipt_on_fabric())
    height, width = cropped.shape[:2]
    assert 700 <= height <= 780
    assert 500 <= width <= 560


def test_crop_leaves_an_all_white_page_alone():
    page = np.full((1000, 700, 3), 255, dtype=np.uint8)
    assert crop_to_document(page).shape == page.shape


def test_crop_returns_the_original_when_no_paper_is_found():
    background = np.full((1000, 1500, 3), YELLOW, dtype=np.uint8)
    assert crop_to_document(background).shape == background.shape


def test_normalize_scale_shrinks_oversized_text():
    page = text_page(glyph_px=70)
    out = normalize_scale(page)
    assert out.shape[0] < page.shape[0]
    assert abs(measure_glyph_height(out) - TARGET_GLYPH_HEIGHT) <= 5


def test_normalize_scale_enlarges_tiny_text():
    page = text_page(glyph_px=10, width=900, height=700)
    out = normalize_scale(page)
    assert out.shape[0] > page.shape[0]


def test_normalize_scale_falls_back_when_there_is_too_little_text():
    blank = np.full((500, 400), 255, dtype=np.uint8)
    assert normalize_scale(blank).shape[1] >= 400   # the old size rule upscales small images