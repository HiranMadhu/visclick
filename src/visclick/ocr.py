"""OCR for cropped regions plus full-image text grounding.

The bot uses OCR for two distinct tasks:

1. ``ocr_box(img, xyxy)`` — read the text inside a single detector box.
   Used during normal pipeline: for each YOLO detection, what does it say?
2. ``text_ground(img, target)`` — search the **full image** for words
   matching ``target``, return their bounding boxes. Used as a fallback
   when the detector misses an element entirely (e.g. a flat Windows 11
   button) but the text label "Save" is clearly visible.

Engines:
- ``tesseract``  — fast, ~5 ms/box, no Python model download. Default.
- ``easyocr``    — neural, ~50 ms/box; first use triggers ~95 MB download.
- ``both``       — Tesseract; fall back to EasyOCR if empty (per box).
- ``none``       — skip OCR entirely.
"""
from __future__ import annotations

import os
from typing import List, Tuple

import cv2
import numpy as np

TESSERACT = os.environ.get("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
_reader = None

ValidEngine = str  # "tesseract" | "easyocr" | "both" | "none"

# Tuple returned by text_ground:
#   ((x1, y1, x2, y2), found_text, similarity 0..100, ocr_conf 0..100)
TextHit = Tuple[Tuple[int, int, int, int], str, float, float]


# ---------- per-box OCR ----------

def _tesseract(crop: np.ndarray) -> str:
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = TESSERACT
        return pytesseract.image_to_string(crop, config="--psm 7").strip()
    except Exception:
        return ""


def _easyocr(crop: np.ndarray) -> str:
    global _reader
    try:
        import easyocr
        _reader = _reader or easyocr.Reader(["en"], gpu=False, verbose=False)
        gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
        out = _reader.readtext(gray)
        return " ".join(o[1] for o in out)
    except Exception:
        return ""


def ocr_box(
    img_rgb: np.ndarray,
    xyxy: Tuple[float, float, float, float],
    engine: ValidEngine = "tesseract",
) -> str:
    """OCR the rectangle region. Return stripped text (possibly empty)."""
    x1, y1, x2, y2 = (int(a) for a in xyxy)
    crop = img_rgb[y1:y2, x1:x2]
    if crop.size == 0:
        return ""

    if engine == "none":
        return ""
    if engine == "tesseract":
        return _tesseract(crop)
    if engine == "easyocr":
        return _easyocr(crop)
    if engine == "both":
        txt = _tesseract(crop)
        return txt if txt else _easyocr(crop)
    raise ValueError(
        f"Unknown OCR engine: {engine!r}. Pick one of "
        f"'tesseract', 'easyocr', 'both', 'none'."
    )


# ---------- full-image text grounding ----------

def text_ground(
    img_rgb: np.ndarray,
    target: str,
    engine: ValidEngine = "tesseract",
    min_similarity: int = 70,
) -> List[TextHit]:
    """Search the full image for words matching ``target``; return matches.

    Useful when YOLO misses a clickable element entirely — the underlying
    text label may still be readable.

    Sort order:
    1. higher similarity first (exact word > partial substring),
    2. higher OCR confidence,
    3. smaller box area (a button label is smaller than a paragraph that
       happens to contain the word).
    """
    target_lower = (target or "").strip().lower()
    if not target_lower:
        return []

    if engine == "none":
        return []
    if engine == "easyocr":
        return _ground_easyocr(img_rgb, target_lower, min_similarity)
    if engine == "both":
        hits = _ground_tesseract(img_rgb, target_lower, min_similarity)
        return hits if hits else _ground_easyocr(img_rgb, target_lower, min_similarity)
    return _ground_tesseract(img_rgb, target_lower, min_similarity)


def _ground_tesseract(img_rgb: np.ndarray, target_lower: str, min_sim: int) -> List[TextHit]:
    try:
        import pytesseract
        from rapidfuzz import fuzz
    except ImportError:
        return []
    pytesseract.pytesseract.tesseract_cmd = TESSERACT
    try:
        data = pytesseract.image_to_data(img_rgb, output_type=pytesseract.Output.DICT)
    except Exception:
        return []

    hits: List[TextHit] = []
    n = len(data.get("text", []))
    for i in range(n):
        text = (data["text"][i] or "").strip()
        if not text:
            continue
        text_lower = text.lower()
        if text_lower == target_lower:
            sim = 100.0
        else:
            sim = float(fuzz.partial_ratio(target_lower, text_lower))
        if sim < min_sim:
            continue
        try:
            x = int(data["left"][i]); y = int(data["top"][i])
            w = int(data["width"][i]); h = int(data["height"][i])
        except (TypeError, ValueError):
            continue
        try:
            conf_raw = data["conf"][i]
            conf = float(conf_raw) if str(conf_raw) not in ("-1", "") else 0.0
        except (TypeError, ValueError):
            conf = 0.0
        hits.append(((x, y, x + w, y + h), text, sim, conf))
    hits.sort(key=lambda h: (-h[2], -h[3], (h[0][2] - h[0][0]) * (h[0][3] - h[0][1])))
    return hits


def _ground_easyocr(img_rgb: np.ndarray, target_lower: str, min_sim: int) -> List[TextHit]:
    global _reader
    try:
        import easyocr
        from rapidfuzz import fuzz
    except ImportError:
        return []
    _reader = _reader or easyocr.Reader(["en"], gpu=False, verbose=False)
    try:
        results = _reader.readtext(img_rgb)
    except Exception:
        return []

    hits: List[TextHit] = []
    for bbox, text, conf in results:
        text = (text or "").strip()
        if not text:
            continue
        text_lower = text.lower()
        if text_lower == target_lower:
            sim = 100.0
        else:
            sim = float(fuzz.partial_ratio(target_lower, text_lower))
        if sim < min_sim:
            continue
        xs = [int(p[0]) for p in bbox]
        ys = [int(p[1]) for p in bbox]
        xyxy = (min(xs), min(ys), max(xs), max(ys))
        hits.append((xyxy, text, sim, float(conf) * 100))
    hits.sort(key=lambda h: (-h[2], -h[3], (h[0][2] - h[0][0]) * (h[0][3] - h[0][1])))
    return hits
