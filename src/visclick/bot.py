"""CLI orchestrator: screenshot → detect → OCR → match → click.

Examples:
  # Live with a 5-second countdown so you can switch to the target window:
  python -m visclick.bot --instruction "click Save" --countdown 5

  # Live, no countdown (immediate capture + click):
  python -m visclick.bot --instruction "click Save"

  # Multi-monitor: pick monitor 2 explicitly (run test_screen.py
  # --list-monitors to see the layout).
  python -m visclick.bot --instruction "click Save" --monitor 2 --countdown 5

  # Dry-run on a saved screenshot (no clicks)
  python -m visclick.bot --instruction "click Save" --image screenshots/test.png --dry-run

  # Save an overlay PNG with all detection boxes for debugging
  python -m visclick.bot --instruction "click Save" --image screenshots/test.png \
      --dry-run --save-overlay screenshots/overlay.png
"""
from __future__ import annotations

import argparse
import os
import time
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import pyautogui

from visclick.act import click_box, click_xy
from visclick.capture import find_pyautogui_primary, grab, set_dpi_awareness
from visclick.detect import CLASS_NAMES, Detector
from visclick.match import _is_class_only_target, _target_phrase, best_box
from visclick.ocr import ocr_box, ocr_status, text_ground

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


def _run_manual_xy(args) -> int:
    """Manual coordinate click — verifies the click plumbing in isolation."""
    set_dpi_awareness()
    tx, ty = args.xy
    pa_w, pa_h = pyautogui.size()
    print(f"manual xy mode | target=({tx}, {ty}) | pyautogui screen={pa_w}x{pa_h}")
    if args.countdown > 0:
        print("Switch to your target window now.")
        for i in range(args.countdown, 0, -1):
            print(f"  capturing in {i}...")
            time.sleep(1)
    pre = pyautogui.position()
    print(f"  cursor before move: ({pre.x}, {pre.y})")
    print(f"  delta to target:    ({tx - pre.x:+d}, {ty - pre.y:+d}) pixels")
    if args.dry_run:
        print("DRY-RUN: no click sent.")
        return 0
    t0 = time.perf_counter()
    click_xy(tx, ty, dwell=0.3)
    dt_ms = (time.perf_counter() - t0) * 1000
    post = pyautogui.position()
    err = (post.x - tx, post.y - ty)
    status = "OK" if abs(err[0]) <= 2 and abs(err[1]) <= 2 else "BAD — likely DPI scaling"
    print(f"  cursor after click: ({post.x}, {post.y})")
    print(f"  arrival error:      ({err[0]:+d}, {err[1]:+d}) pixels [{status}]")
    print(f"  move + click took {dt_ms:.0f} ms")
    return 0


def _parse_xy(s: str) -> Tuple[int, int]:
    """Accept '500,400', '500 400', or 'xy 500 400'."""
    import re
    m = re.match(r"^\s*(?:xy\s+)?(-?\d+)\s*[,\s]\s*(-?\d+)\s*$", s, re.IGNORECASE)
    if not m:
        raise argparse.ArgumentTypeError(
            f"--xy must be 'X,Y' or 'X Y' (got {s!r})")
    return int(m.group(1)), int(m.group(2))


def main() -> int:
    ap = argparse.ArgumentParser(description="VisClick instruction-driven GUI click bot")
    ap.add_argument("--instruction", default=None, help='e.g. "click Save"')
    ap.add_argument("--xy", type=_parse_xy, default=None,
                    help="Manual coordinate click. Skips capture/detection. "
                         "Example: --xy 500,400 or --xy '500 400'. "
                         "Coordinates are virtual-desktop (pyautogui-style). "
                         "Useful for verifying mouse plumbing in isolation.")
    ap.add_argument("--weights", default="weights/visclick.onnx",
                    help="Path to ONNX weights (default: weights/visclick.onnx)")
    ap.add_argument("--image", default=None,
                    help="Run on a saved screenshot instead of capturing screen")
    ap.add_argument("--monitor", type=int, default=0,
                    help="mss monitor index for screen capture (default: 0 = auto-pick "
                         "the monitor matching pyautogui's primary). Run "
                         "scripts/test_screen.py --list-monitors to see options.")
    ap.add_argument("--countdown", type=int, default=0,
                    help="Seconds to wait before capturing the screen. Useful when "
                         "running from a terminal: gives you time to bring the target "
                         "window to the front before the screenshot is taken.")
    ap.add_argument("--conf", type=float, default=0.25, help="Detection confidence threshold")
    ap.add_argument("--iou",  type=float, default=0.50, help="NMS IoU threshold")
    ap.add_argument("--dry-run", action="store_true", help="Do not send a real click")
    ap.add_argument("--save-overlay", default=None,
                    help="If set, save annotated screenshot with all detection boxes "
                         "(picked one drawn thicker)")
    ap.add_argument("--ocr-engine", choices=["tesseract", "easyocr", "both", "none"],
                    default="easyocr",
                    help="Which OCR backend to use on detected boxes. "
                         "'easyocr' (default) is pure-Python, more robust on "
                         "modern flat dark-mode UIs, downloads ~95 MB on first "
                         "use. 'tesseract' is faster (~5 ms/box) but needs a "
                         "separate Windows installer (UB-Mannheim). "
                         "'both' tries tesseract then falls back to easyocr. "
                         "'none' skips OCR (match by class + confidence only).")
    ap.add_argument("--no-ocr", action="store_true",
                    help="Alias for --ocr-engine none.")
    ap.add_argument("--no-text-fallback", action="store_true",
                    help="Disable the full-image OCR fallback that runs when "
                         "the YOLO detector misses a text-labeled element. "
                         "By default the fallback is on for text-target "
                         "instructions like 'click Save'.")
    args = ap.parse_args()
    if args.no_ocr:
        args.ocr_engine = "none"

    if args.xy is not None:
        return _run_manual_xy(args)
    if not args.instruction:
        ap.error("either --instruction or --xy is required")

    if not os.path.isfile(args.weights):
        print(f"ERROR: weights not found: {args.weights}")
        print(f"Hint: download from <DRIVE>/weights/desktop_finetune/best_desktop_v8s.onnx "
              f"or git pull (notebook 07 commits weights/visclick.onnx)")
        return 2

    monitor_offset = (0, 0)
    if args.image:
        if not os.path.isfile(args.image):
            print(f"ERROR: image not found: {args.image}")
            return 2
        print(f"loading saved image: {args.image}")
        img = _load_image(args.image)
    else:
        set_dpi_awareness()
        if args.countdown > 0:
            print(f"Switch to your target window now.")
            for i in range(args.countdown, 0, -1):
                print(f"  capturing in {i}...")
                time.sleep(1)
        mon_idx = args.monitor if args.monitor > 0 else find_pyautogui_primary()
        img, mleft, mtop = grab(mon_idx)
        monitor_offset = (mleft, mtop)
        print(f"captured monitor {mon_idx}: {img.shape[1]}x{img.shape[0]} "
              f"at virtual-desktop offset ({mleft}, {mtop})")

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

    if args.ocr_engine != "none":
        st = ocr_status()
        for name in ("tesseract", "easyocr"):
            info = st[name]
            if info.get("available"):
                tag = info.get("version", "ok")
                print(f"OCR {name:9s}: ✓ {tag}")
            else:
                print(f"OCR {name:9s}: ✗ {info.get('reason', 'unavailable')}")
        if not st[args.ocr_engine].get("available"):
            other = "easyocr" if args.ocr_engine == "tesseract" else "tesseract"
            if st[other].get("available"):
                print(f"WARNING: requested OCR={args.ocr_engine} is unavailable; "
                      f"auto-switching to {other}.")
                args.ocr_engine = other
            else:
                print(f"WARNING: no OCR backend is available; matching will use "
                      f"class + confidence only.")
                args.ocr_engine = "none"
    print(f"OCR engine: {args.ocr_engine}")
    boxes_with_text: List[Tuple[int, Box4, float, str]] = []
    for cls, xyxy, conf in raw:
        text = ocr_box(img, xyxy, engine=args.ocr_engine)
        boxes_with_text.append((cls, xyxy, conf, text))
        cxl = (xyxy[0] + xyxy[2]) / 2
        cyl = (xyxy[1] + xyxy[3]) / 2
        print(f"  cls={CLASS_NAMES[cls]:11s} center=({cxl:>6.0f},{cyl:>6.0f})  "
              f"conf={conf:.2f} text={text!r}")

    pick = best_box(args.instruction, boxes_with_text)

    if pick is None and not args.no_text_fallback:
        target = _target_phrase(args.instruction)
        if not _is_class_only_target(target):
            print(f"FALLBACK: detector miss; running full-image OCR for {target!r}…")
            hits = text_ground(img, target,
                                engine=args.ocr_engine if args.ocr_engine != "none"
                                       else "easyocr",
                                min_similarity=70)
            print(f"  text_ground found {len(hits)} hit(s)")
            for xyxy_h, text_h, sim_h, ocr_conf_h in hits[:5]:
                cxh = (xyxy_h[0] + xyxy_h[2]) / 2
                cyh = (xyxy_h[1] + xyxy_h[3]) / 2
                print(f"    {text_h!r:25s} center=({cxh:>6.0f},{cyh:>6.0f})  "
                      f"sim={sim_h:.0f}  ocr_conf={ocr_conf_h:.0f}")
            if hits:
                xyxy_h, text_h, sim_h, ocr_conf_h = hits[0]
                synth = (1, xyxy_h, ocr_conf_h / 100.0, text_h)  # cls=1=text
                boxes_with_text.append(synth)
                pick = (sim_h, 1, xyxy_h, ocr_conf_h / 100.0, text_h)

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
        target = (args.instruction or "").lower().replace("click", "").strip().strip("'\"")
        print(f"FAIL: neither detector nor full-image OCR found {target!r}.")
        print("  Try one of:")
        print("    --conf 0.10   (lower threshold; show weaker detections)")
        print("    --ocr-engine easyocr   (more robust OCR; one-time download)")
        print("    --xy X,Y      (manual coordinate click as fallback)")
        return 1
    score, cls, xyxy, conf, text = pick
    print(f"PICKED cls={CLASS_NAMES[cls]} text={text!r} det_conf={conf:.2f} match_score={score}")

    cx_local = (xyxy[0] + xyxy[2]) / 2
    cy_local = (xyxy[1] + xyxy[3]) / 2
    cx_abs = cx_local + monitor_offset[0]
    cy_abs = cy_local + monitor_offset[1]

    print(f"  monitor-local center: ({cx_local:.0f}, {cy_local:.0f})")
    print(f"  virtual-desktop:      ({cx_abs:.0f}, {cy_abs:.0f})")

    if args.dry_run:
        print(f"DRY-RUN: would click virtual-desktop ({cx_abs:.0f}, {cy_abs:.0f})")
        return 0

    if args.image:
        print("WARN: --image was set but --dry-run was not. Refusing to click; the screen "
              "may not match the image. Re-run live without --image, or add --dry-run.")
        return 0

    pre = pyautogui.position()
    print(f"  cursor before move:   ({pre.x}, {pre.y})  "
          f"delta-to-target=({cx_abs - pre.x:+.0f}, {cy_abs - pre.y:+.0f})")
    abs_xy = click_box(xyxy, offset=monitor_offset)
    post = pyautogui.position()
    err = (post.x - cx_abs, post.y - cy_abs)
    status = "OK" if abs(err[0]) <= 2 and abs(err[1]) <= 2 else "BAD — likely DPI scaling"
    print(f"  cursor after click:   ({post.x}, {post.y})")
    print(f"  arrival error:        ({err[0]:+.0f}, {err[1]:+.0f}) pixels [{status}]")
    print(f"CLICKED virtual-desktop ({abs_xy[0]:.0f}, {abs_xy[1]:.0f}) "
          f"[monitor-local ({cx_local:.0f}, {cy_local:.0f}) + offset {monitor_offset}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
