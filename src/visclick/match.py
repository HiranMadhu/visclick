"""Map natural-language instruction to best detected box."""

from __future__ import annotations

from typing import List, Optional, Set, Tuple

from rapidfuzz import fuzz

Box4 = Tuple[float, float, float, float]


def best_box(
    instruction: str,
    boxes_with_text: List[Tuple[int, Box4, float, str]],
    prefer_classes: Optional[Set[int]] = None,
) -> Optional[Tuple[int, int, Box4, float, str]]:
    """
    boxes_with_text: (cls, xyxy, det_conf, ocr_text)
    Returns (match_score, cls, xyxy, det_conf, ocr_text) or None.
    """
    target = instruction.lower().split()[-1] if instruction.split() else ""
    scored: List[Tuple[int, int, Box4, float, str]] = []
    for cls, xyxy, det_conf, text in boxes_with_text:
        s = fuzz.partial_ratio(target, (text or "").lower())
        if prefer_classes and cls in prefer_classes:
            s += 10
        scored.append((s, cls, xyxy, det_conf, text))
    scored.sort(reverse=True, key=lambda t: t[0])
    if not scored:
        return None
    s, cls, xyxy, det_conf, text = scored[0]
    return (s, cls, xyxy, det_conf, text)
