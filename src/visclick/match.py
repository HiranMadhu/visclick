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
- text similarity (rapidfuzz partial_ratio, 0-100) — dominant for case 1.
- + bonus for clickable-class detections (button > icon > menu > text_input
  > checkbox > text). The teacher fires `text` on every word, so without
  this bonus a "click Save" instruction would happily click any *text*
  detection that contains "Save".
- + small term for higher detector confidence.

Returns ``None`` when:
- the candidate list is empty, OR
- the user named a label (case 1) and no box's OCR text resembles it
  (best partial_ratio < ``min_text_similarity``).

Object-oriented layout:
- ``Matcher`` bundles the scoring policy (``CLASS_BONUS``, verb list,
  class-word vocabulary) together with the ``best_box`` decision so that
  future variants (e.g. weighted vocabularies for other UI domains) can
  subclass and override without touching module globals.
- Module-level ``best_box``, ``_target_phrase``, ``_is_class_only_target``
  remain as delegates for backward compatibility.
"""
from __future__ import annotations

import re
from typing import Iterable, List, Optional, Tuple

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


class Matcher:
    """Scoring-plus-refusal policy for the instruction -> box pick.

    Instances hold the scoring policy (class bonus, verb vocabulary, class
    vocabulary). ``best_box`` returns the top-scoring candidate or ``None``
    when the label-style instruction has no adequately similar OCR text.
    """

    def __init__(
        self,
        class_bonus: dict[int, float] | None = None,
        verbs: Iterable[str] | None = None,
        class_words: Iterable[str] | None = None,
    ) -> None:
        self.class_bonus: dict[int, float] = dict(class_bonus) if class_bonus is not None else dict(_CLASS_BONUS)
        self.verbs: set[str] = set(verbs) if verbs is not None else set(_VERBS)
        self.class_words: set[str] = set(class_words) if class_words is not None else set(_CLASS_WORDS)

    def target_phrase(self, instruction: str) -> str:
        """Strip leading verbs ("click", "press", ...) and quotes; lowercase the rest."""
        s = instruction.strip().lower()
        s = re.sub(r"['\"`]", "", s)
        tokens = s.split()
        while tokens and tokens[0] in self.verbs:
            tokens = tokens[1:]
        return " ".join(tokens) or s

    def is_class_only_target(self, target: str) -> bool:
        """True if every word of the target is a class word ("button", "menu", ...)."""
        if not target:
            return False
        return all(t in self.class_words for t in target.split())

    def best_box(
        self,
        instruction: str,
        boxes_with_text: List[Tuple[int, Box4, float, str]],
        min_text_similarity: int = 60,
    ) -> Optional[Tuple[float, int, Box4, float, str]]:
        """boxes_with_text: ``(cls, xyxy, det_conf, ocr_text)``.

        Returns ``(match_score, cls, xyxy, det_conf, ocr_text)`` or ``None``.
        Returns ``None`` when no candidate scores high enough on the text
        term for a label-style instruction (so the caller can report
        'no Save found' rather than miss-click on the closest button).
        """
        if not boxes_with_text:
            return None

        target = self.target_phrase(instruction)
        is_class_only = self.is_class_only_target(target)

        scored: List[Tuple[float, float, int, Box4, float, str]] = []
        for cls, xyxy, det_conf, text in boxes_with_text:
            haystack = (text or "").lower()
            sim = float(fuzz.partial_ratio(target, haystack)) if target and haystack else 0.0
            score = sim + self.class_bonus.get(cls, 0.0) + 5.0 * float(det_conf)
            scored.append((score, sim, cls, xyxy, det_conf, text))

        scored.sort(reverse=True, key=lambda t: t[0])
        best = scored[0]
        score, sim, cls, xyxy, det_conf, text = best

        if not is_class_only and target and sim < min_text_similarity:
            return None

        return (score, cls, xyxy, det_conf, text)


_default = Matcher()


def _target_phrase(instruction: str) -> str:
    return _default.target_phrase(instruction)


def _is_class_only_target(target: str) -> bool:
    return _default.is_class_only_target(target)


def best_box(
    instruction: str,
    boxes_with_text: List[Tuple[int, Box4, float, str]],
    min_text_similarity: int = 60,
) -> Optional[Tuple[float, int, Box4, float, str]]:
    return _default.best_box(instruction, boxes_with_text, min_text_similarity=min_text_similarity)
