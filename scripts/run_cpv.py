"""Phase 2 / D-08: Central Point Validation (CPV) on the hand-corrected test set.

CPV definition (Dardouri et al. 2024):
  For each ground-truth (GT) box, the GT is considered RECOVERED if **at least one
  predicted box's centre point falls inside that GT box**. CPV is reported as
  hits / total, overall and per class.

Why this metric: it is the right success criterion for an automation bot, which
needs a click that **lands somewhere inside the target**. It is more permissive
than mAP@0.5 and tracks closer to end-to-end Task Success Rate.

Inputs (auto-discovered, in priority order):
  1. ``datasets/handcorrected_desktop_test/_unzipped/train/{images,labels}/``
     (this script extracts ``visclick3.yolov8.zip`` once and reuses it).
  2. Override with ``--img-dir`` and ``--lbl-dir``.

ONNX detector: ``weights/visclick.onnx`` (override with ``--weights``).

Outputs:
  - ``reports/tables/cpv_summary.csv``  (one row per class + OVERALL)
  - ``reports/tables/cpv_per_image.csv`` (one row per image)

Usage::

    py -3 scripts/run_cpv.py
    py -3 scripts/run_cpv.py --conf 0.25 --weights weights/visclick.onnx
"""
from __future__ import annotations

import argparse
import csv
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from visclick.detect import CLASS_NAMES, Detector  # noqa: E402

ZIP_PATH = _REPO / "datasets" / "handcorrected_desktop_test" / "visclick3.yolov8.zip"
UNZIP_ROOT = _REPO / "datasets" / "handcorrected_desktop_test" / "_unzipped"
DEFAULT_IMG_DIR = UNZIP_ROOT / "train" / "images"
DEFAULT_LBL_DIR = UNZIP_ROOT / "train" / "labels"
DEFAULT_WEIGHTS = _REPO / "weights" / "visclick.onnx"
OUT_DIR = _REPO / "reports" / "tables"


def ensure_unzipped() -> None:
    if DEFAULT_IMG_DIR.exists() and any(DEFAULT_IMG_DIR.glob("*.png")):
        return
    if not ZIP_PATH.exists():
        print(f"[error] zip not found: {ZIP_PATH}", file=sys.stderr)
        sys.exit(2)
    UNZIP_ROOT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        zf.extractall(UNZIP_ROOT)
    print(f"[info] extracted {ZIP_PATH.name} -> {UNZIP_ROOT}")


def load_gt(lbl_path: Path, w: int, h: int) -> List[Tuple[int, float, float, float, float]]:
    """Return list of (cls_id, x1, y1, x2, y2) in pixel coordinates."""
    out: List[Tuple[int, float, float, float, float]] = []
    if not lbl_path.exists():
        return out
    for raw in lbl_path.read_text(encoding="utf-8").splitlines():
        parts = raw.strip().split()
        if len(parts) < 5:
            continue
        c, cx, cy, bw, bh = int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
        x1 = (cx - bw / 2) * w
        y1 = (cy - bh / 2) * h
        x2 = (cx + bw / 2) * w
        y2 = (cy + bh / 2) * h
        out.append((c, x1, y1, x2, y2))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute CPV (D-08) on hand-corrected test set")
    ap.add_argument("--weights", default=str(DEFAULT_WEIGHTS))
    ap.add_argument("--img-dir", default=str(DEFAULT_IMG_DIR))
    ap.add_argument("--lbl-dir", default=str(DEFAULT_LBL_DIR))
    ap.add_argument("--conf", type=float, default=0.25, help="Detector confidence threshold")
    ap.add_argument("--iou", type=float, default=0.50, help="NMS IoU threshold")
    ap.add_argument("--tag", default="",
                    help="Optional suffix for the output CSV filenames "
                         "(e.g. --tag conf010 produces cpv_summary_conf010.csv).")
    args = ap.parse_args()

    ensure_unzipped()

    img_dir = Path(args.img_dir)
    lbl_dir = Path(args.lbl_dir)
    imgs = sorted(p for p in img_dir.glob("*.png")) + sorted(p for p in img_dir.glob("*.jpg"))
    if not imgs:
        print(f"[error] no images found in {img_dir}", file=sys.stderr)
        return 2

    print(f"[info] images: {len(imgs)}  in {img_dir}")
    print(f"[info] weights: {args.weights}")
    det = Detector(args.weights)

    total: Dict[str, int] = {c: 0 for c in CLASS_NAMES}
    hits: Dict[str, int] = {c: 0 for c in CLASS_NAMES}
    per_image_rows: List[List[str]] = []

    for img_p in imgs:
        rgb = np.array(Image.open(img_p).convert("RGB"))
        h, w = rgb.shape[:2]
        preds = det.predict(rgb, conf=args.conf, iou=args.iou)
        pred_centres = [((x1 + x2) / 2.0, (y1 + y2) / 2.0)
                        for (_cls, (x1, y1, x2, y2), _c) in preds]

        gts = load_gt(lbl_dir / f"{img_p.stem}.txt", w, h)
        img_total = 0
        img_hit = 0
        for (cls, x1, y1, x2, y2) in gts:
            cls_name = CLASS_NAMES[cls] if 0 <= cls < len(CLASS_NAMES) else f"cls_{cls}"
            total.setdefault(cls_name, 0)
            hits.setdefault(cls_name, 0)
            total[cls_name] += 1
            img_total += 1
            for (cx, cy) in pred_centres:
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    hits[cls_name] += 1
                    img_hit += 1
                    break
        cpv_img = (img_hit / img_total * 100.0) if img_total else 0.0
        per_image_rows.append([img_p.name, str(img_total), str(img_hit), f"{cpv_img:.2f}",
                               str(len(preds))])
        print(f"  {img_p.name:55s} GT={img_total:3d} hit={img_hit:3d} "
              f"CPV={cpv_img:5.1f}%  (preds={len(preds)})")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = f"_{args.tag}" if args.tag else ""
    per_class_csv = OUT_DIR / f"cpv_summary{suffix}.csv"
    per_image_csv = OUT_DIR / f"cpv_per_image{suffix}.csv"

    with per_class_csv.open("w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["class", "gt_boxes", "centres_inside", "cpv_pct"])
        grand_total = 0
        grand_hit = 0
        print()
        print(f"{'class':12s} {'gt':>6s} {'hit':>6s} {'cpv_%':>7s}")
        print(f"{'-'*12} {'-'*6} {'-'*6} {'-'*7}")
        for cls_name in list(CLASS_NAMES) + [c for c in total if c not in CLASS_NAMES]:
            t = total.get(cls_name, 0)
            h_ = hits.get(cls_name, 0)
            if t == 0 and h_ == 0:
                continue
            grand_total += t
            grand_hit += h_
            cpv = (h_ / t * 100.0) if t else 0.0
            wr.writerow([cls_name, t, h_, f"{cpv:.2f}"])
            print(f"{cls_name:12s} {t:6d} {h_:6d} {cpv:7.2f}")
        cpv_overall = (grand_hit / grand_total * 100.0) if grand_total else 0.0
        wr.writerow(["OVERALL", grand_total, grand_hit, f"{cpv_overall:.2f}"])
        print(f"{'OVERALL':12s} {grand_total:6d} {grand_hit:6d} {cpv_overall:7.2f}")

    with per_image_csv.open("w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["image", "gt_boxes", "centres_inside", "cpv_pct", "n_predictions"])
        wr.writerows(per_image_rows)

    print()
    print(f"[done] wrote {per_class_csv}")
    print(f"[done] wrote {per_image_csv}")
    print(f"REPORT cpv | overall = {cpv_overall:.2f}%  (gt={grand_total}, hit={grand_hit})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
