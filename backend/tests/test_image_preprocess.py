import cv2
import numpy as np

from app.services.image_preprocess import (
    deskew_image,
    estimate_skew,
    preprocess,
    resize_for_ocr,
)


def make_text_lines_image(width: int = 800, height: int = 1000) -> np.ndarray:
    """White page with black horizontal bars standing in for lines of text."""
    img = np.full((height, width), 255, dtype=np.uint8)
    rng = np.random.default_rng(0)
    for y in range(60, height - 60, 40):
        x_end = int(rng.integers(300, width - 60))
        cv2.rectangle(img, (50, y), (x_end, y + 8), 0, thickness=-1)
    return img


def rotate(img: np.ndarray, angle: float) -> np.ndarray:
    h, w = img.shape
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(
        img, matrix, (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )


def test_resize_upscales_small_images():
    small = np.zeros((200, 300), dtype=np.uint8)
    out = resize_for_ocr(small)
    assert out.shape[0] > 200 and out.shape[1] > 300


def test_resize_downscales_huge_images():
    huge = np.full((4000, 4000), 255, dtype=np.uint8)
    out = resize_for_ocr(huge)
    assert out.shape[0] * out.shape[1] <= 8_000_000 * 1.01


def test_resize_leaves_normal_images_alone():
    normal = np.full((1200, 1000), 255, dtype=np.uint8)
    assert resize_for_ocr(normal).shape == normal.shape


def test_deskew_straightens_a_rotated_page():
    skewed = rotate(make_text_lines_image(), 6.0)
    assert abs(estimate_skew(skewed)) >= 4.0     # the tilt is detected
    fixed = deskew_image(skewed)
    assert abs(estimate_skew(fixed)) <= 1.0      # and mostly removed


def test_straight_page_is_left_alone():
    assert abs(estimate_skew(make_text_lines_image())) <= 0.5


def test_blank_page_has_no_skew():
    blank = np.full((1000, 800), 255, dtype=np.uint8)
    assert estimate_skew(blank) == 0.0


def test_preprocess_returns_a_2d_uint8_image():
    out = preprocess(make_text_lines_image())
    assert out.ndim == 2
    assert out.dtype == np.uint8