"""OCR for cropped regions plus full-image text grounding.

The bot uses OCR for two distinct tasks:

1. ``ocr_box(img, xyxy)`` — read the text inside a single detector box.
   Used during normal pipeline: for each YOLO detection, what does it say?
2. ``text_ground(img, target)`` — search the **full image** for words
   matching ``target``, return their bounding boxes. Used as a fallback
   when the detector misses an element entirely (e.g. a flat Windows 11
   button) but the text label "Save" is clearly visible.

Engines:
- ``easyocr``    — DEFAULT. Pure-Python neural OCR, ~50 ms/box. Pip-installable;
                    first use downloads ~95 MB of recognition / detection
                    models, then cached forever in ``~/.EasyOCR``. Robust on
                    the dark-mode flat buttons in modern Windows / VS Code /
                    Chrome UIs that VisClick targets.
- ``tesseract``  — Optional speed boost: ~5 ms/box but requires a separate
                    Windows installer (UB-Mannheim build) and a working
                    binary on PATH. If you have Tesseract installed, pass
                    ``--ocr-engine tesseract`` for faster runs.
- ``both``       — Try Tesseract; fall back to EasyOCR if it returns empty.
- ``none``       — Skip OCR entirely (matcher uses class + conf only).

Object-oriented layout:
- ``OCREngine`` encapsulates both cached state (the EasyOCR reader, the
  one-shot Tesseract warning) and the four public entry points
  (``status``, ``ocr_box``, ``text_ground``, plus the two private engine
  branches). One instance is enough per process.
- The module-level ``ocr_status``, ``ocr_box``, ``text_ground`` remain as
  delegates to the default instance so existing imports keep working.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

TESSERACT = os.environ.get("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

ValidEngine = str  # "tesseract" | "easyocr" | "both" | "none"

# Tuple returned by text_ground:
#   ((x1, y1, x2, y2), found_text, similarity 0..100, ocr_conf 0..100)
TextHit = Tuple[Tuple[int, int, int, int], str, float, float]


class OCREngine:
    """Cached OCR facade for per-box reads and full-image text grounding."""

    def __init__(self, tesseract_cmd: str | None = None) -> None:
        self.tesseract_cmd: str = tesseract_cmd or TESSERACT
        self._reader = None
        self._tesseract_warned: bool = False

    def _resolve_tesseract_path(self) -> str:
        if os.path.isfile(self.tesseract_cmd):
            return self.tesseract_cmd
        on_path = shutil.which("tesseract")
        return on_path or ""

    def _warn_tesseract_once(self, detail: str) -> None:
        if self._tesseract_warned:
            return
        self._tesseract_warned = True
        binary = self._resolve_tesseract_path() or self.tesseract_cmd
        print("WARNING: Tesseract OCR is not working - every OCR call will return empty.")
        print(f"  configured path : {self.tesseract_cmd}")
        print(f"  resolved binary : {binary if os.path.isfile(binary) else '(not found)'}")
        print(f"  underlying error: {detail}")
        print("  fix one of:")
        print("    (1) install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki")
        print("        (the default install path matches the configured one above)")
        print("    (2) set the TESSERACT_CMD environment variable to your install path")
        print("    (3) use --ocr-engine easyocr  (or pick 'easyocr' in the GUI)")
        print("        first run will download ~95 MB of EasyOCR models.")

    def status(self) -> Dict[str, Dict[str, Any]]:
        """Probe OCR backends and return a small structured report.

        Used by the bot/GUI startup to print a banner and to auto-fallback
        when the user-selected engine is not available.
        """
        out: Dict[str, Dict[str, Any]] = {"tesseract": {}, "easyocr": {}}

        binary = self._resolve_tesseract_path()
        if binary:
            out["tesseract"]["binary_path"] = binary
            try:
                r = subprocess.run([binary, "--version"],
                                    capture_output=True, text=True, timeout=5)
                ver = (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr) else "unknown"
                out["tesseract"]["version"] = ver
                out["tesseract"]["available"] = True
            except Exception as e:
                out["tesseract"]["available"] = False
                out["tesseract"]["reason"] = f"binary failed: {e}"
        else:
            out["tesseract"]["available"] = False
            out["tesseract"]["binary_path"] = self.tesseract_cmd
            out["tesseract"]["reason"] = ("binary not found at configured path "
                                           "and not on PATH")
        try:
            import pytesseract  # noqa: F401
            out["tesseract"]["pytesseract"] = True
        except ImportError:
            out["tesseract"]["pytesseract"] = False
            out["tesseract"]["available"] = False
            out["tesseract"]["reason"] = "pytesseract Python package missing"

        try:
            import easyocr  # noqa: F401
            out["easyocr"]["available"] = True
            out["easyocr"]["version"] = getattr(__import__("easyocr"), "__version__", "?")
        except ImportError:
            out["easyocr"]["available"] = False
            out["easyocr"]["reason"] = "not installed (pip install easyocr)"

        return out

    def _tesseract(self, crop: np.ndarray) -> str:
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            return pytesseract.image_to_string(crop, config="--psm 7").strip()
        except Exception as e:
            self._warn_tesseract_once(repr(e))
            return ""

    def _easyocr(self, crop: np.ndarray) -> str:
        try:
            import easyocr
            if self._reader is None:
                self._reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
            out = self._reader.readtext(gray)
            return " ".join(o[1] for o in out)
        except Exception:
            return ""

    def ocr_box(
        self,
        img_rgb: np.ndarray,
        xyxy: Tuple[float, float, float, float],
        engine: ValidEngine = "easyocr",
    ) -> str:
        """OCR the rectangle region. Return stripped text (possibly empty)."""
        x1, y1, x2, y2 = (int(a) for a in xyxy)
        crop = img_rgb[y1:y2, x1:x2]
        if crop.size == 0:
            return ""

        if engine == "none":
            return ""
        if engine == "tesseract":
            return self._tesseract(crop)
        if engine == "easyocr":
            return self._easyocr(crop)
        if engine == "both":
            txt = self._tesseract(crop)
            return txt if txt else self._easyocr(crop)
        raise ValueError(
            f"Unknown OCR engine: {engine!r}. Pick one of "
            f"'tesseract', 'easyocr', 'both', 'none'."
        )

    def text_ground(
        self,
        img_rgb: np.ndarray,
        target: str,
        engine: ValidEngine = "easyocr",
        min_similarity: int = 70,
    ) -> List[TextHit]:
        """Search the full image for words matching ``target``; return matches.

        Useful when YOLO misses a clickable element entirely — the underlying
        text label may still be readable.

        Sort order:
        1. higher similarity first (exact word > partial substring),
        2. higher OCR confidence,
        3. smaller box area (a button label is smaller than a paragraph
           that happens to contain the word).
        """
        target_lower = (target or "").strip().lower()
        if not target_lower:
            return []

        if engine == "none":
            return []
        if engine == "easyocr":
            return self._ground_easyocr(img_rgb, target_lower, min_similarity)
        if engine == "both":
            hits = self._ground_tesseract(img_rgb, target_lower, min_similarity)
            return hits if hits else self._ground_easyocr(img_rgb, target_lower, min_similarity)
        return self._ground_tesseract(img_rgb, target_lower, min_similarity)

    def _ground_tesseract(self, img_rgb: np.ndarray, target_lower: str, min_sim: int) -> List[TextHit]:
        try:
            import pytesseract
            from rapidfuzz import fuzz
        except ImportError as e:
            self._warn_tesseract_once(repr(e))
            return []
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        try:
            data = pytesseract.image_to_data(img_rgb, output_type=pytesseract.Output.DICT)
        except Exception as e:
            self._warn_tesseract_once(repr(e))
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
                if sim >= 100.0:
                    sim = 99.0
            if sim < min_sim:
                continue
            try:
                x = int(data["left"][i])
                y = int(data["top"][i])
                w = int(data["width"][i])
                h = int(data["height"][i])
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

    def _ground_easyocr(self, img_rgb: np.ndarray, target_lower: str, min_sim: int) -> List[TextHit]:
        try:
            import easyocr
            from rapidfuzz import fuzz
        except ImportError:
            return []
        if self._reader is None:
            self._reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        try:
            results = self._reader.readtext(img_rgb)
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
                if sim >= 100.0:
                    sim = 99.0
            if sim < min_sim:
                continue
            xs = [int(p[0]) for p in bbox]
            ys = [int(p[1]) for p in bbox]
            xyxy = (min(xs), min(ys), max(xs), max(ys))
            hits.append((xyxy, text, sim, float(conf) * 100))
        hits.sort(key=lambda h: (-h[2], -h[3], (h[0][2] - h[0][0]) * (h[0][3] - h[0][1])))
        return hits


_default = OCREngine()


def ocr_status() -> Dict[str, Dict[str, Any]]:
    return _default.status()


def ocr_box(
    img_rgb: np.ndarray,
    xyxy: Tuple[float, float, float, float],
    engine: ValidEngine = "easyocr",
) -> str:
    return _default.ocr_box(img_rgb, xyxy, engine=engine)


def text_ground(
    img_rgb: np.ndarray,
    target: str,
    engine: ValidEngine = "easyocr",
    min_similarity: int = 70,
) -> List[TextHit]:
    return _default.text_ground(img_rgb, target, engine=engine, min_similarity=min_similarity)
