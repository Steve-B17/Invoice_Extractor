import cv2
import numpy as np

MAX_PIXELS = 8_000_000   # keeps OCR fast on huge phone photos
MIN_SIDE = 1000          # small images get upscaled so text is big enough
MAX_UPSCALE = 3.0


def resize_for_ocr(gray: np.ndarray) -> np.ndarray:
    """Downscale huge images, upscale tiny ones."""
    h, w = gray.shape[:2]
    pixels = h * w

    if pixels > MAX_PIXELS:
        scale = (MAX_PIXELS / pixels) ** 0.5
        interpolation = cv2.INTER_AREA
    elif min(h, w) < MIN_SIDE:
        scale = min(MIN_SIDE / min(h, w), MAX_UPSCALE, (MAX_PIXELS / pixels) ** 0.5)
        interpolation = cv2.INTER_CUBIC
    else:
        return gray

    if abs(scale - 1.0) < 0.01:
        return gray
    new_size = (int(round(w * scale)), int(round(h * scale)))
    return cv2.resize(gray, new_size, interpolation=interpolation)


def remove_shadows(gray: np.ndarray) -> np.ndarray:
    """Estimate the page background (paper plus shadows) and divide it out,
    leaving dark text on an evenly white page. Assumes dark text on light paper."""
    dilated = cv2.dilate(gray, np.ones((7, 7), np.uint8))   # erases thin dark text
    background = cv2.medianBlur(dilated, 21)                # smooth paper + shadows
    diff = 255 - cv2.absdiff(gray, background)
    return cv2.normalize(diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)


def estimate_skew(gray: np.ndarray, max_angle: float = 10.0, step: float = 0.5) -> float:
    """Projection-profile method. Rotate a binarized copy through candidate angles
    and keep the one where the text rows line up most sharply. Rows of text give
    a spiky horizontal projection (high variance) only when the page is straight."""
    h, w = gray.shape[:2]
    if w > 800:
        gray = cv2.resize(gray, (800, int(h * 800 / w)), interpolation=cv2.INTER_AREA)

    binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    h, w = binary.shape
    center = (w / 2, h / 2)

    def score(angle: float) -> float:
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(binary, matrix, (w, h), flags=cv2.INTER_NEAREST)
        return float(np.var(rotated.sum(axis=1, dtype=np.float64)))

    baseline = score(0.0)
    best_angle, best_score = 0.0, baseline
    for angle in np.arange(-max_angle, max_angle + step, step):
        current = score(float(angle))
        if current > best_score:
            best_angle, best_score = float(angle), current

    # Only trust a rotation that is clearly better than leaving the page alone
    if best_score <= baseline * 1.02:
        return 0.0
    return best_angle


def deskew_image(gray: np.ndarray, max_angle: float = 10.0) -> np.ndarray:
    angle = estimate_skew(gray, max_angle)
    if abs(angle) < 0.3:
        return gray
    h, w = gray.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(
        gray,
        matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )


def preprocess(
    gray: np.ndarray,
    *,
    remove_shadow: bool = True,
    deskew: bool = True,
    binarize: bool = False,
) -> np.ndarray:
    """Grayscale image in, cleaned grayscale image out.
    The flags exist so Day 6's evaluation can switch each step on and off."""
    out = resize_for_ocr(gray)
    if remove_shadow:
        out = remove_shadows(out)
    if deskew:
        out = deskew_image(out)
    if binarize:
        out = cv2.threshold(out, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    return out