"""CLI orchestrator: screenshot → detect → OCR → match → click."""

from __future__ import annotations

import argparse
from typing import List, Tuple

from visclick.act import click_box
from visclick.capture import grab
from visclick.detect import Detector
from visclick.match import best_box
from visclick.ocr import ocr_box

Box4 = Tuple[float, float, float, float]


def main() -> None:
    ap = argparse.ArgumentParser(description="VisClick instruction-driven GUI click bot")
    ap.add_argument("--instruction", required=True, help='e.g. "click Save"')
    ap.add_argument("--weights", default="weights/visclick.onnx", help="Path to ONNX weights")
    ap.add_argument("--dry-run", action="store_true", help="Do not send a real click")
    args = ap.parse_args()

    img = grab()
    det = Detector(args.weights)
    raw = det.predict(img)
    boxes_with_text: List[Tuple[int, Box4, float, str]] = []
    for cls, xyxy, conf in raw:
        t = ocr_box(img, xyxy)
        boxes_with_text.append((cls, xyxy, conf, t))

    pick = best_box(args.instruction, boxes_with_text)
    if not pick:
        print("FAIL: no candidates")
        return
    score, cls, xyxy, conf, text = pick
    print(f"PICKED cls={cls} text={text!r} det_conf={conf:.2f} match_score={score}")
    if not args.dry_run:
        click_box(xyxy)


if __name__ == "__main__":
    main()
