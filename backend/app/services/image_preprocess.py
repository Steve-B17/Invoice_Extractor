import cv2
import numpy as np
import os

MAX_PIXELS = 8_000_000   # keeps OCR fast on huge phone photos
MIN_SIDE = 1000          # fallback rule: small images get upscaled
MAX_UPSCALE = 3.0

# Tesseract reads best when a typical character is about this tall (in pixels).
# On a real receipt, targets from 15 to 22 all read well, and 16 scored highest.
TARGET_GLYPH_HEIGHT = float(os.getenv("OCR_GLYPH_HEIGHT", "16"))


def resize_for_ocr(gray: np.ndarray) -> np.ndarray:
    """Fallback size rule: downscale huge images, upscale tiny ones."""
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


def crop_to_document(rgb: np.ndarray) -> np.ndarray:
    """Cut a photo down to the paper. Phone photos of receipts contain hands, tables and
    fabric, and patterned backgrounds turn into junk 'words'. Paper is bright and has
    almost no colour, so we look for the biggest bright, uncoloured region."""
    h, w = rgb.shape[:2]
    scale = 1000 / max(h, w)
    small = cv2.resize(rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
    brightness = hsv[..., 2]
    brightness_floor = max(100.0, 0.6 * float(np.percentile(brightness, 95)))
    mask = ((hsv[..., 1] < 70) & (brightness > brightness_floor)).astype(np.uint8) * 255

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return rgb

    best = max(contours, key=cv2.contourArea)
    share = cv2.contourArea(best) / float(small.shape[0] * small.shape[1])
    if share < 0.10 or share > 0.90:
        return rgb   # nothing paper-like found, or the image is already just the page

    x, y, bw, bh = cv2.boundingRect(best)
    pad_x, pad_y = int(0.02 * bw), int(0.02 * bh)
    x0 = max(0, int((x - pad_x) / scale))
    y0 = max(0, int((y - pad_y) / scale))
    x1 = min(w, int((x + bw + pad_x) / scale))
    y1 = min(h, int((y + bh + pad_y) / scale))
    return rgb[y0:y1, x0:x1]


def measure_glyph_height(gray: np.ndarray) -> float | None:
    """Typical height of a character-sized blob, in pixels (None if there is too little text)."""
    h = gray.shape[0]
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 15
    )
    count, _, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)

    heights = []
    for i in range(1, count):
        _, _, bw, bh, _ = stats[i]
        if bh < 0.004 * h or bh > 0.08 * h:   # specks and big graphics
            continue
        if bw > 3 * bh or bw < 0.15 * bh:      # lines, dashes and vertical bars
            continue
        heights.append(bh)

    if len(heights) < 20:
        return None
    return float(np.median(heights))


def normalize_scale(gray: np.ndarray) -> np.ndarray:
    """Resize so characters are about TARGET_GLYPH_HEIGHT pixels tall, whatever the
    resolution of the photo. Both too-big and too-small text hurt OCR."""
    h, w = gray.shape[:2]
    work_scale = min(1.0, 2000 / max(h, w))
    work = gray
    if work_scale < 1.0:
        work = cv2.resize(gray, (int(w * work_scale), int(h * work_scale)), interpolation=cv2.INTER_AREA)

    glyph = measure_glyph_height(work)
    if glyph is None:
        return resize_for_ocr(gray)   # too little text to measure

    scale = TARGET_GLYPH_HEIGHT * work_scale / glyph
    scale = min(max(scale, 0.15), MAX_UPSCALE)
    scale = min(scale, (MAX_PIXELS / (h * w)) ** 0.5)
    if abs(scale - 1.0) < 0.03:
        return gray

    interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
    new_size = (max(1, int(round(w * scale))), max(1, int(round(h * scale))))
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
    and keep the one where the text rows line up most sharply."""
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
        gray, matrix, (w, h),
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
    out = normalize_scale(gray)
    if remove_shadow:
        out = remove_shadows(out)
    if deskew:
        out = deskew_image(out)
    if binarize:
        out = cv2.threshold(out, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    return out