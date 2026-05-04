"""CLI orchestrator: screenshot → detect → OCR → match → click.

Examples:
  # Live: capture screen, click "Save"
  python -m visclick.bot --instruction "click Save"

  # Dry-run on a saved screenshot (no clicks)
  python -m visclick.bot --instruction "click Save" --image screenshots/test.png --dry-run

  # Save an overlay PNG with all detection boxes for debugging
  python -m visclick.bot --instruction "click Save" --image screenshots/test.png \
      --dry-run --save-overlay screenshots/overlay.png
"""
from __future__ import annotations

import argparse
import os
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from visclick.act import click_box
from visclick.capture import grab, set_dpi_awareness
from visclick.detect import CLASS_NAMES, Detector
from visclick.match import best_box
from visclick.ocr import ocr_box

Box4 = Tuple[float, float, float, float]


_COLORS: list[tuple[int, int, int]] = [
    (255, 107, 107), (78, 205, 196), (255, 230, 109),
    (160, 108, 213), (6, 167, 125), (255, 166, 43),
]


def _load_image(path: str) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    return np.array(img)


def _save_overlay(
    img_rgb: np.ndarray,
    boxes_with_text: List[Tuple[int, Box4, float, str]],
    picked_index: int,
    out_path: str,
) -> None:
    pil = Image.fromarray(img_rgb).copy()
    draw = ImageDraw.Draw(pil)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    for i, (cls, xyxy, conf, text) in enumerate(boxes_with_text):
        color = _COLORS[cls % len(_COLORS)]
        x1, y1, x2, y2 = (int(round(v)) for v in xyxy)
        width = 4 if i == picked_index else 2
        draw.rectangle([x1, y1, x2, y2], outline=color, width=width)
        label = f"{CLASS_NAMES[cls]} {conf:.2f}"
        if text:
            label += f" | {text[:30]}"
        draw.text((x1, max(0, y1 - 16)), label, fill=color, font=font)
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    pil.save(out_path)


def main() -> int:
    ap = argparse.ArgumentParser(description="VisClick instruction-driven GUI click bot")
    ap.add_argument("--instruction", required=True, help='e.g. "click Save"')
    ap.add_argument("--weights", default="weights/visclick.onnx",
                    help="Path to ONNX weights (default: weights/visclick.onnx)")
    ap.add_argument("--image", default=None,
                    help="Run on a saved screenshot instead of capturing screen")
    ap.add_argument("--conf", type=float, default=0.25, help="Detection confidence threshold")
    ap.add_argument("--iou",  type=float, default=0.50, help="NMS IoU threshold")
    ap.add_argument("--dry-run", action="store_true", help="Do not send a real click")
    ap.add_argument("--save-overlay", default=None,
                    help="If set, save annotated screenshot with all detection boxes "
                         "(picked one drawn thicker)")
    ap.add_argument("--no-ocr", action="store_true",
                    help="Skip OCR (match against class names only — faster, less specific)")
    args = ap.parse_args()

    if not os.path.isfile(args.weights):
        print(f"ERROR: weights not found: {args.weights}")
        print(f"Hint: download from <DRIVE>/weights/desktop_finetune/best_desktop_v8s.onnx "
              f"or git pull (notebook 07 commits weights/visclick.onnx)")
        return 2

    if args.image:
        if not os.path.isfile(args.image):
            print(f"ERROR: image not found: {args.image}")
            return 2
        print(f"loading saved image: {args.image}")
        img = _load_image(args.image)
    else:
        set_dpi_awareness()
        img = grab()
        print(f"captured screen: {img.shape[1]}x{img.shape[0]}")

    print(f"loading detector: {args.weights}")
    det = Detector(args.weights)
    raw = det.predict(img, conf=args.conf, iou=args.iou)
    print(f"detector returned {len(raw)} box(es)")
    if not raw:
        print("FAIL: detector found no candidates above conf threshold")
        if args.save_overlay:
            _save_overlay(img, [], -1, args.save_overlay)
            print(f"saved empty overlay to {args.save_overlay}")
        return 1

    boxes_with_text: List[Tuple[int, Box4, float, str]] = []
    for cls, xyxy, conf in raw:
        if args.no_ocr:
            text = ""
        else:
            text = ocr_box(img, xyxy)
        boxes_with_text.append((cls, xyxy, conf, text))
        print(f"  cls={CLASS_NAMES[cls]:11s} conf={conf:.2f} text={text!r}")

    pick = best_box(args.instruction, boxes_with_text)
    picked_index = -1
    if pick is not None:
        score, cls, xyxy, conf, text = pick
        for i, (c, b, cf, t) in enumerate(boxes_with_text):
            if c == cls and b == xyxy:
                picked_index = i
                break

    if args.save_overlay:
        _save_overlay(img, boxes_with_text, picked_index, args.save_overlay)
        print(f"saved overlay to {args.save_overlay}")

    if pick is None:
        print("FAIL: no candidates after matching")
        return 1
    score, cls, xyxy, conf, text = pick
    print(f"PICKED cls={CLASS_NAMES[cls]} text={text!r} det_conf={conf:.2f} match_score={score}")

    if args.dry_run:
        print(f"DRY-RUN: would click center of xyxy={xyxy}")
        return 0

    if args.image:
        print("WARN: --image was set but --dry-run was not. Refusing to click; the screen "
              "may not match the image. Re-run live without --image, or add --dry-run.")
        return 0

    click_box(xyxy)
    print(f"CLICKED center of xyxy={xyxy}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
