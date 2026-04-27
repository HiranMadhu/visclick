"""OCR for cropped regions (Tesseract + EasyOCR fallback)."""

from __future__ import annotations

import os
from typing import Tuple

import cv2
import numpy as np

TESSERACT = os.environ.get("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
_reader = None


def ocr_box(img_rgb: np.ndarray, xyxy: Tuple[float, float, float, float]) -> str:
    """OCR the rectangle region; return stripped text."""
    x1, y1, x2, y2 = (int(a) for a in xyxy)
    crop = img_rgb[y1:y2, x1:x2]
    if crop.size == 0:
        return ""

    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = TESSERACT
        txt = pytesseract.image_to_string(crop, config="--psm 7").strip()
    except Exception:
        txt = ""

    if not txt:
        global _reader
        try:
            import easyocr
            _reader = _reader or easyocr.Reader(["en"], gpu=False)
            gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
            out = _reader.readtext(gray)
            txt = " ".join(o[1] for o in out)
        except Exception:
            txt = ""
    return txt
