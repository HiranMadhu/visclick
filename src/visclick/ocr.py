"""OCR for cropped regions. Two backends, selectable per call.

Engines:
- ``tesseract``  — fast, ~5 ms/box, no Python model download. Default.
                    Requires Tesseract installed on the system. Misses
                    occasionally on small text and icons but is fine for
                    standard buttons and menus.
- ``easyocr``    — Python neural model, ~50 ms/box on CPU. First use
                    triggers a ~95 MB model download (detection +
                    recognition) cached in ``~/.EasyOCR``. Robust on small
                    text but adds setup cost.
- ``both``       — try tesseract; if it returns empty, fall back to
                    easyocr. (Old behaviour; pays both costs in worst case.)
- ``none``       — skip OCR entirely. The matcher then scores boxes by
                    class + confidence only. Fastest (~0 ms) and useful when
                    your instruction names a class ("click button") rather
                    than a label ("click Save").

Use ``ocr_box(img, xyxy, engine="tesseract")`` to control per call.
"""
from __future__ import annotations

import os
from typing import Tuple

import cv2
import numpy as np

TESSERACT = os.environ.get("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
_reader = None  # cached EasyOCR Reader (lazy)

ValidEngine = str  # "tesseract" | "easyocr" | "both" | "none"


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
