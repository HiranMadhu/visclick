"""Tests for the text_ground full-image OCR fallback.

These tests don't actually run Tesseract or EasyOCR (which would require
the binaries to be installed on the test runner). Instead they exercise
the result-aggregation / sort logic by injecting a fake pytesseract
data dict.
"""
from __future__ import annotations

import sys
import types
from typing import Any


def _install_fake_pytesseract(text_data: dict[str, list[Any]]) -> None:
    """Patch sys.modules so ``import pytesseract`` returns a fake module that
    yields ``text_data`` from ``image_to_data``."""
    fake = types.ModuleType("pytesseract")

    class _Output:
        DICT = "dict"

    def _image_to_data(img, output_type=None):  # noqa: ARG001
        return text_data

    fake.Output = _Output
    fake.image_to_data = _image_to_data
    fake.pytesseract = types.SimpleNamespace(tesseract_cmd="")
    sys.modules["pytesseract"] = fake


def _install_fake_rapidfuzz() -> None:
    """Patch sys.modules with a tiny rapidfuzz stand-in for the test."""
    fake = types.ModuleType("rapidfuzz")
    fake_fuzz = types.ModuleType("rapidfuzz.fuzz")

    def partial_ratio(a: str, b: str) -> int:
        if not a or not b:
            return 0
        if a in b or b in a:
            return 100
        sa, sb = set(a), set(b)
        return int(100 * len(sa & sb) / max(len(sa), len(sb)))

    fake_fuzz.partial_ratio = partial_ratio
    fake.fuzz = fake_fuzz
    sys.modules["rapidfuzz"] = fake
    sys.modules["rapidfuzz.fuzz"] = fake_fuzz


def test_text_ground_picks_exact_word_over_substring() -> None:
    _install_fake_pytesseract({
        "text":   ["", "Save", "Save", "as", "type:", ""],
        "left":   [0,    50,     400,    480,  520,    0],
        "top":    [0,    700,    900,    900,  900,    0],
        "width":  [0,    60,     50,     30,   60,     0],
        "height": [0,    20,     22,     22,   22,     0],
        "conf":   [-1,   95,     92,     90,   88,     -1],
    })
    _install_fake_rapidfuzz()
    sys.modules.pop("visclick.ocr", None)
    import numpy as np
    from visclick.ocr import text_ground

    img = np.zeros((1000, 800, 3), dtype=np.uint8)
    hits = text_ground(img, "Save", engine="tesseract", min_similarity=70)

    assert len(hits) == 2, f"expected 2 'Save' hits, got {len(hits)}"
    # Both are exact word matches → similarity 100; tiebreaker is OCR conf
    # then box area. Both have similar areas; the higher-conf one (95) wins.
    (xyxy, text, sim, conf) = hits[0]
    assert text == "Save"
    assert sim == 100.0
    assert conf == 95.0


def test_text_ground_returns_empty_when_no_match() -> None:
    _install_fake_pytesseract({
        "text":   ["Cancel", "Documents", "Downloads"],
        "left":   [50, 100, 150],
        "top":    [10, 20, 30],
        "width":  [60, 80, 80],
        "height": [20, 20, 20],
        "conf":   [90, 88, 87],
    })
    _install_fake_rapidfuzz()
    sys.modules.pop("visclick.ocr", None)
    import numpy as np
    from visclick.ocr import text_ground

    img = np.zeros((100, 800, 3), dtype=np.uint8)
    hits = text_ground(img, "Save", engine="tesseract", min_similarity=70)
    assert hits == []
