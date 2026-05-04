"""Detection test — verifies the ONNX inference layer in isolation.

Usage:
    python scripts/test_detector.py screenshots/test_screen.png
    python scripts/test_detector.py path/to/img.png --weights weights/visclick.onnx
    python scripts/test_detector.py img.png --conf 0.15 --iou 0.5 --bench 50

What this proves (when it works):
1. onnxruntime can load weights/visclick.onnx.
2. The model produces detections at sane coordinates on a real screenshot.
3. Per-image latency (median + p95 across N runs) for §4.1 / §10 of the report.

Outputs:
- Prints class, confidence, and box for every detection.
- Saves an annotated copy at <input>_overlay.png next to the input.
- Writes a small CSV at tables/detector_latency.csv for §10.1 if --bench > 0.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from visclick.detect import CLASS_NAMES, Detector  # noqa: E402

_COLORS = [
    (255, 107, 107), (78, 205, 196), (255, 230, 109),
    (160, 108, 213), (6, 167, 125), (255, 166, 43),
]


def _draw(img_rgb: np.ndarray, dets: list, out_path: Path) -> None:
    pil = Image.fromarray(img_rgb).copy()
    draw = ImageDraw.Draw(pil)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    for cls, (x1, y1, x2, y2), conf in dets:
        color = _COLORS[cls % len(_COLORS)]
        draw.rectangle([int(x1), int(y1), int(x2), int(y2)], outline=color, width=2)
        draw.text((int(x1), max(0, int(y1) - 16)),
                  f"{CLASS_NAMES[cls]} {conf:.2f}", fill=color, font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pil.save(out_path)


def main() -> int:
    ap = argparse.ArgumentParser(description="ONNX detector test on a saved image")
    ap.add_argument("image", help="Path to an input image (PNG/JPG)")
    ap.add_argument("--weights", default="weights/visclick.onnx")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--iou",  type=float, default=0.50)
    ap.add_argument("--bench", type=int, default=10,
                    help="Number of timing runs after warmup (0 disables)")
    ap.add_argument("--csv", default="tables/detector_latency.csv",
                    help="Where to append latency stats")
    args = ap.parse_args()

    img_path = Path(args.image)
    if not img_path.is_file():
        print(f"ERROR: not a file: {img_path}")
        return 2
    weights = Path(args.weights)
    if not weights.is_file():
        print(f"ERROR: weights not found: {weights}")
        print("Hint: run notebook 07_export_onnx.ipynb in Colab to produce it, "
              "or git pull (07 commits weights/visclick.onnx).")
        return 2

    img = np.array(Image.open(img_path).convert("RGB"))
    print(f"loaded image: {img.shape[1]} x {img.shape[0]}")

    print(f"loading detector: {weights}  providers=CPU")
    det = Detector(str(weights))

    print(f"running inference (conf={args.conf}, iou={args.iou})")
    dets = det.predict(img, conf=args.conf, iou=args.iou)
    print(f"REPORT detector | n_detections = {len(dets)}")
    by_class: dict[int, int] = {}
    for cls, _, _ in dets:
        by_class[cls] = by_class.get(cls, 0) + 1
    for cid, name in enumerate(CLASS_NAMES):
        print(f"REPORT detector | class = {name:11s} | n = {by_class.get(cid, 0)}")
    for cls, xyxy, conf in dets[:30]:
        x1, y1, x2, y2 = (int(round(v)) for v in xyxy)
        print(f"  cls={CLASS_NAMES[cls]:11s} conf={conf:.3f} xyxy=({x1},{y1},{x2},{y2})")

    overlay_path = img_path.with_name(img_path.stem + "_overlay.png")
    _draw(img, dets, overlay_path)
    print(f"saved overlay: {overlay_path.resolve()}")

    if args.bench > 0:
        print(f"benchmarking {args.bench} runs (after 3 warmup)")
        for _ in range(3):
            det.predict(img, conf=args.conf, iou=args.iou)
        times_ms = []
        for _ in range(args.bench):
            t = time.perf_counter()
            det.predict(img, conf=args.conf, iou=args.iou)
            times_ms.append((time.perf_counter() - t) * 1000)
        arr = np.array(times_ms)
        print(f"REPORT bench | runs = {args.bench}")
        print(f"REPORT bench | median_ms = {np.median(arr):0.1f}")
        print(f"REPORT bench | p95_ms    = {np.percentile(arr, 95):0.1f}")
        print(f"REPORT bench | mean_ms   = {arr.mean():0.1f}")
        print(f"REPORT bench | min_ms    = {arr.min():0.1f}")
        print(f"REPORT bench | max_ms    = {arr.max():0.1f}")

        csv_path = Path(args.csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        new_file = not csv_path.exists()
        with csv_path.open("a", newline="") as fh:
            w = csv.writer(fh)
            if new_file:
                w.writerow(["ts", "weights", "image", "imgsz", "n_runs", "median_ms",
                            "p95_ms", "mean_ms", "min_ms", "max_ms", "n_detections"])
            w.writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"),
                str(weights), str(img_path), 640, args.bench,
                f"{np.median(arr):0.2f}", f"{np.percentile(arr, 95):0.2f}",
                f"{arr.mean():0.2f}", f"{arr.min():0.2f}", f"{arr.max():0.2f}",
                len(dets),
            ])
        print(f"appended row to {csv_path.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
