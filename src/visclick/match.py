"""Map natural-language instruction to the best detected box.

Scoring (higher = better):
  - text similarity (rapidfuzz partial_ratio, 0–100) is the dominant term.
  - +bonus for clickable-class detections (button > icon > menu > text_input).
    The teacher fires `text` on every word, so without this bonus a "click Save"
    instruction would happily click any *text* label that contains "Save"
    (e.g. the word "Save" written inside a tooltip), instead of the actual
    Save button beside it.
  - small +bonus for higher detector confidence.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from rapidfuzz import fuzz

Box4 = Tuple[float, float, float, float]


_CLASS_BONUS: dict[int, float] = {
    0: 12.0,  # button
    3: 8.0,   # icon
    4: 6.0,   # menu
    2: 6.0,   # text_input
    1: 0.0,   # text  (penalised relative to clickables — the teacher fires on every word)
    5: 4.0,   # checkbox
}

_VERBS = {"click", "press", "tap", "hit", "select", "open", "toggle", "check", "uncheck"}


def _target_phrase(instruction: str) -> str:
    """Strip leading verbs ("click", "press", ...) and quotes; lower-case the rest."""
    s = instruction.strip().lower()
    s = re.sub(r"['\"`]", "", s)
    tokens = s.split()
    while tokens and tokens[0] in _VERBS:
        tokens = tokens[1:]
    return " ".join(tokens) or s


def best_box(
    instruction: str,
    boxes_with_text: List[Tuple[int, Box4, float, str]],
) -> Optional[Tuple[float, int, Box4, float, str]]:
    """boxes_with_text: (cls, xyxy, det_conf, ocr_text).

    Returns (match_score, cls, xyxy, det_conf, ocr_text) or None if list empty.
    """
    if not boxes_with_text:
        return None

    target = _target_phrase(instruction)
    scored: List[Tuple[float, int, Box4, float, str]] = []
    for cls, xyxy, det_conf, text in boxes_with_text:
        haystack = (text or "").lower()
        if target and haystack:
            sim = float(fuzz.partial_ratio(target, haystack))
        else:
            sim = 0.0
        score = sim + _CLASS_BONUS.get(cls, 0.0) + 5.0 * float(det_conf)
        scored.append((score, cls, xyxy, det_conf, text))

    scored.sort(reverse=True, key=lambda t: t[0])
    return scored[0]
