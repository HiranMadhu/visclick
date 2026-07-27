"""Map natural-language instruction to the best detected box.

Two kinds of instruction:

1. ``click <text>``  e.g. "click Save", "press OK", "tap Sign In"
   The user named a label they expect to see written on a UI element.
   We MUST match that label in the OCR text — falling back to "the most
   button-like box on screen" would silently click the wrong thing.

2. ``click <class>``  e.g. "click button", "click menu", "click checkbox"
   The user named a class only. Class bonus dominates; no text match
   needed.

Scoring (higher = better):
- text similarity (rapidfuzz partial_ratio, 0–100) — dominant for case 1.
- + bonus for clickable-class detections (button > icon > menu > text_input
  > checkbox > text). The teacher fires `text` on every word, so without
  this bonus a "click Save" instruction would happily click any *text*
  detection that contains "Save".
- + small term for higher detector confidence.

Returns ``None`` when:
- the candidate list is empty, OR
- the user named a label (case 1) and no box's OCR text resembles it
  (best partial_ratio < ``min_text_similarity``).
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
    1: 0.0,   # text
    5: 4.0,   # checkbox
}

_VERBS = {"click", "press", "tap", "hit", "select", "open", "toggle", "check", "uncheck"}

_CLASS_WORDS = {
    "button", "buttons",
    "text", "texts", "label", "labels",
    "input", "inputs", "field", "fields", "textbox", "textboxes",
    "icon", "icons",
    "menu", "menus", "dropdown", "dropdowns",
    "checkbox", "checkboxes",
}


def _target_phrase(instruction: str) -> str:
    """Strip leading verbs ("click", "press", ...) and quotes; lowercase the rest."""
    s = instruction.strip().lower()
    s = re.sub(r"['\"`]", "", s)
    tokens = s.split()
    while tokens and tokens[0] in _VERBS:
        tokens = tokens[1:]
    return " ".join(tokens) or s


def _is_class_only_target(target: str) -> bool:
    """True if every word of the target is a class word ("button", "menu", ...)."""
    if not target:
        return False
    return all(t in _CLASS_WORDS for t in target.split())


def best_box(
    instruction: str,
    boxes_with_text: List[Tuple[int, Box4, float, str]],
    min_text_similarity: int = 60,
) -> Optional[Tuple[float, int, Box4, float, str]]:
    """boxes_with_text: ``(cls, xyxy, det_conf, ocr_text)``.

    Returns ``(match_score, cls, xyxy, det_conf, ocr_text)`` or ``None``.
    Returns ``None`` when no candidate scores high enough on the text term
    for a label-style instruction (so the caller can report 'no Save found'
    rather than miss-click on the closest button).
    """
    if not boxes_with_text:
        return None

    target = _target_phrase(instruction)
    is_class_only = _is_class_only_target(target)

    scored: List[Tuple[float, float, int, Box4, float, str]] = []
    for cls, xyxy, det_conf, text in boxes_with_text:
        haystack = (text or "").lower()
        sim = float(fuzz.partial_ratio(target, haystack)) if target and haystack else 0.0
        score = sim + _CLASS_BONUS.get(cls, 0.0) + 5.0 * float(det_conf)
        scored.append((score, sim, cls, xyxy, det_conf, text))

    scored.sort(reverse=True, key=lambda t: t[0])
    best = scored[0]
    score, sim, cls, xyxy, det_conf, text = best

    # If the user named a label, refuse to click anything whose OCR text
    # doesn't actually resemble that label. The user can switch to a
    # class-only instruction ("click button") if they want the bot to pick
    # the most button-like box regardless of text.
    if not is_class_only and target and sim < min_text_similarity:
        return None

    return (score, cls, xyxy, det_conf, text)
