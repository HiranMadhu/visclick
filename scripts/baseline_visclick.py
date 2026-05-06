"""Phase 2.1 — VisClick full pipeline as a "fourth baseline" in the runner.

Same ``predict(image_rgb, instruction, **kwargs) -> BaselineResult`` API as
the three Phase-1.C baselines, so the orchestrator can run all four side
by side on each task and the comparison CSV / chart pick up VisClick
automatically. This is **not** a baseline — it is the headline approach;
calling it "baseline_visclick" for code-symmetry only.

Pipeline (matches ``src/visclick/bot.py``):
  1. ONNX detector → list of (cls, xyxy, det_conf).
  2. EasyOCR per box → ocr text.
  3. ``match.best_box`` ranks by text similarity + class bonus + det_conf.
  4. If matcher returns None (no detection's text resembles the target),
     fall back to ``visclick.ocr.text_ground`` — full-image OCR for the
     target keyword.
  5. Return ``BaselineResult`` with the chosen (cx, cy) + bbox.

Weights live at ``weights/visclick.onnx`` (committed; ~44 MB). Tracked
loaded singleton so the runner pays the model load cost once across all
15 tasks, not 15 times.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple

import numpy as np

from baseline_common import (
    BaselineResult,
    add_repo_to_path,
    autopick_monitor,
    baseline_argparser,
    load_image,
    maybe_click,
    parse_target_words,
    print_result,
    time_call,
)

REPO = Path(__file__).resolve().parent.parent
DEFAULT_WEIGHTS = REPO / "weights" / "visclick.onnx"

_DETECTOR = None  # lazy singleton


def _detector(weights: Path):
    global _DETECTOR
    if _DETECTOR is None:
        add_repo_to_path()
        from visclick.detect import Detector
        _DETECTOR = Detector(str(weights))
    return _DETECTOR


def _run_pipeline(image_rgb: np.ndarray,
                  instruction: str,
                  weights: Path,
                  conf: float,
                  iou: float,
                  ocr_engine: str,
                  min_text_similarity: int) -> dict:
    """Return a dict with diagnostic fields used by predict() to build the
    BaselineResult and notes string."""
    add_repo_to_path()
    from visclick.match import best_box
    from visclick.ocr import ocr_box, text_ground

    det = _detector(weights)
    raw = det.predict(image_rgb, conf=conf, iou=iou)

    boxes_with_text: List[Tuple[int, Tuple[float, float, float, float], float, str]] = []
    for cls, xyxy, det_conf in raw:
        text = ""
        if ocr_engine != "none":
            try:
                text = ocr_box(image_rgb, xyxy, engine=ocr_engine) or ""
            except Exception:
                text = ""
        boxes_with_text.append((int(cls), tuple(xyxy), float(det_conf), text))

    chosen = best_box(instruction, boxes_with_text, min_text_similarity=min_text_similarity)
    fallback_used = False
    if chosen is None and ocr_engine != "none":
        words = parse_target_words(instruction)
        target = " ".join(words) if words else ""
        if target:
            hits = text_ground(image_rgb, target, engine=ocr_engine,
                               min_similarity=min_text_similarity)
            if hits:
                fallback_used = True
                (x1, y1, x2, y2), found_text, sim, ocr_conf = hits[0]
                chosen = (
                    float(sim),
                    1,  # treat as 'text' class for reporting
                    (float(x1), float(y1), float(x2), float(y2)),
                    float(ocr_conf) / 100.0,
                    found_text,
                )

    return {
        "raw_detections": raw,
        "n_det": len(raw),
        "chosen": chosen,
        "fallback_used": fallback_used,
    }


def predict(image_rgb: np.ndarray,
            instruction: str,
            *,
            offset: Tuple[int, int] = (0, 0),
            weights: Optional[Path] = None,
            conf: float = 0.25,
            iou: float = 0.5,
            ocr_engine: str = "easyocr",
            min_text_similarity: int = 60,
            **_: object) -> BaselineResult:
    r = BaselineResult(method="visclick", found=False)

    w_path = Path(weights) if weights else DEFAULT_WEIGHTS
    if not w_path.is_file():
        r.notes = f"weights not found at {w_path}"
        return r

    out, ms = time_call(_run_pipeline, image_rgb, instruction, w_path,
                        conf, iou, ocr_engine, min_text_similarity)
    r.elapsed_ms = ms

    chosen = out["chosen"]
    n_det = out["n_det"]
    if chosen is None:
        r.notes = (f"detector returned {n_det} boxes; matcher refused "
                   f"(no box's text >= {min_text_similarity}% similarity to instruction; "
                   f"text_ground fallback also empty)")
        return r

    score, cls, xyxy, det_conf, text = chosen
    x1, y1, x2, y2 = xyxy
    cx_local = (x1 + x2) / 2
    cy_local = (y1 + y2) / 2
    r.found = True
    r.confidence = min(1.0, max(0.0, score / 100.0))
    r.bbox = (int(x1), int(y1), int(x2), int(y2))
    r.xy = (int(cx_local + offset[0]), int(cy_local + offset[1]))

    add_repo_to_path()
    from visclick.detect import CLASS_NAMES
    cls_name = CLASS_NAMES[cls] if 0 <= cls < len(CLASS_NAMES) else str(cls)

    src = "fallback (full-image OCR)" if out["fallback_used"] else "detector+OCR"
    text_show = (text[:30] + "…") if text and len(text) > 30 else (text or "")
    r.notes = (f"VisClick ({src}): {n_det} det, picked cls={cls_name} "
               f"det_conf={det_conf:.2f} text='{text_show}' score={score:.1f}")
    return r


def main(argv: Optional[List[str]] = None) -> int:
    p = baseline_argparser("visclick")
    p.add_argument("--weights", default=None,
                   help=f"path to ONNX weights (default {DEFAULT_WEIGHTS}).")
    p.add_argument("--conf", type=float, default=0.25)
    p.add_argument("--iou", type=float, default=0.5)
    p.add_argument("--ocr-engine", choices=["easyocr", "tesseract", "both", "none"],
                   default="easyocr")
    p.add_argument("--min-text-similarity", type=int, default=60)
    args = p.parse_args(argv)

    monitor = autopick_monitor(args.monitor)
    img, offset = load_image(args.image, monitor)

    r = predict(
        img, args.instruction,
        offset=offset,
        weights=Path(args.weights) if args.weights else None,
        conf=args.conf,
        iou=args.iou,
        ocr_engine=args.ocr_engine,
        min_text_similarity=args.min_text_similarity,
    )
    print_result(r)
    if r.found:
        maybe_click(r, args.dry_run)
    return 0 if r.found else 1


if __name__ == "__main__":
    sys.exit(main())
