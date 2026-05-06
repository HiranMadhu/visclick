"""Phase 1.C.2 — OCR-only baseline (no detector).

Idea: run EasyOCR (or Tesseract) on the **full** screenshot, get every
recognised word with its bounding box, fuzzy-match each word against the
keywords parsed from the natural-language instruction, and click the
centre of the best-matching box.

This is essentially "VisClick without the YOLO step" — it borrows the
``text_ground`` helper that already lives in ``visclick.ocr`` because we
explicitly designed it for full-image OCR.

EXPECTED OUTCOME for the dissertation:
- Succeeds well on text-labelled targets (Save, Cancel, Properties,
  Commit) when the OCR engine reads the label correctly.
- Fails completely on icon-only clickables (close X, settings cog,
  dropdown arrows ▼) because there is no text label to read.
- Fails on textfield placeholders that vanish on focus (Chrome's
  omnibox, Explorer's address bar) — by the time the OCR runs there is
  no readable target.

USAGE:
    py -3 scripts/baseline_ocr_only.py \\
        --instruction "click Save" \\
        --image samples/test_screenshots/T01.png

    # Tesseract instead of EasyOCR (faster but more brittle)
    py -3 scripts/baseline_ocr_only.py \\
        --instruction "click Save" --engine tesseract
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np

from baseline_common import (
    BaselineResult,
    autopick_monitor,
    add_repo_to_path,
    baseline_argparser,
    load_image,
    maybe_click,
    parse_target_words,
    print_result,
    time_call,
)


def _ground(img_rgb: np.ndarray, target: str, engine: str, min_sim: int):
    add_repo_to_path()
    from visclick.ocr import text_ground
    return text_ground(img_rgb, target, engine=engine, min_similarity=min_sim)


def predict(image_rgb: np.ndarray,
            instruction: str,
            *,
            target_text: str = "",
            offset: tuple[int, int] = (0, 0),
            engine: str = "easyocr",
            min_similarity: int = 70,
            **_: object) -> BaselineResult:
    r = BaselineResult(method="ocr_only")

    if target_text:
        target = target_text
    else:
        words = parse_target_words(instruction)
        target = " ".join(words) if words else ""

    if not target:
        r.notes = f"could not parse a target from instruction '{instruction}'"
        return r

    hits, ms = time_call(_ground, image_rgb, target, engine, min_similarity)
    r.elapsed_ms = ms

    if not hits:
        r.notes = f"OCR found no '{target}' (engine={engine})"
        return r

    (x1, y1, x2, y2), found_text, sim, ocr_conf = hits[0]
    cx_local = (x1 + x2) // 2
    cy_local = (y1 + y2) // 2
    r.found = True
    r.confidence = float(sim) / 100.0
    r.bbox = (int(x1), int(y1), int(x2), int(y2))
    r.xy = (int(cx_local + offset[0]), int(cy_local + offset[1]))
    r.notes = (f"OCR matched '{found_text}' (sim={sim:.0f}, ocr_conf={ocr_conf:.0f}) "
               f"as '{target}' [{len(hits)} candidate(s)]")
    return r


def main(argv: Optional[list[str]] = None) -> int:
    p = baseline_argparser("ocr_only")
    p.add_argument("--engine", choices=["easyocr", "tesseract", "both"],
                   default="easyocr",
                   help="OCR engine. easyocr is the project default.")
    p.add_argument("--min-similarity", type=int, default=70,
                   help="rapidfuzz min match score 0..100 (default 70).")
    args = p.parse_args(argv)

    monitor = autopick_monitor(args.monitor)
    img, offset = load_image(args.image, monitor)

    r = predict(img, args.instruction,
                target_text=args.target_text,
                offset=offset,
                engine=args.engine,
                min_similarity=args.min_similarity)
    print_result(r)

    if r.found:
        maybe_click(r, args.dry_run)
    return 0 if r.found else 1


if __name__ == "__main__":
    sys.exit(main())
