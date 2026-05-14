"""Phase 3 / D-07: Central Point Validation (CPV) on a public benchmark.

This script reuses the same CPV definition as ``scripts/run_cpv.py`` but
evaluates against an **independent, third-party-labelled** dataset:
**ScreenSpot** (Cheng et al. 2024, SeeClick paper) - specifically the
``desktop`` slice (macOS + Windows screens, ~280-310 entries depending on
the release).

Why this matters for the dissertation:
  - the hand-corrected test set is only 8 screens (n=8 is fragile);
  - ScreenSpot ground truth was labelled by an independent team and is
    used as a published benchmark by other GUI-grounding papers;
  - CPV is class-agnostic ("did any predicted box's centre fall inside
    the GT box?"), so the class-taxonomy mismatch between our 6-class
    detector and ScreenSpot's `(text|icon)` label is harmless.

Outputs:
  - ``reports/tables/cpv_screenspot_desktop.csv``      (overall + per slice)
  - ``reports/tables/cpv_screenspot_desktop_rows.csv`` (one row per entry)

Usage::

    pip install datasets pillow
    py -3 scripts/run_cpv_screenspot.py                  # default conf 0.25
    py -3 scripts/run_cpv_screenspot.py --conf 0.10 --tag conf010
    py -3 scripts/run_cpv_screenspot.py --limit 50       # smoke test

If your corporate network blocks HuggingFace, point ``--cache-dir`` at a
local snapshot you copied across and re-run; the script will use the
cached arrow files without internet. The default cache directory is under
the system temp folder (short path) so Windows ``MAX_PATH`` lock files work
when the repo lives under deep paths such as OneDrive.
"""
from __future__ import annotations

import argparse
import csv
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from visclick.detect import Detector  # noqa: E402

DEFAULT_WEIGHTS = _REPO / "weights" / "visclick.onnx"
DEFAULT_HF_ID = "rootsautomation/ScreenSpot"
# Short path avoids Windows MAX_PATH when HF `datasets` builds lock filenames
# that embed the full cache directory (OneDrive repo paths often overflow).
DEFAULT_CACHE = Path(tempfile.gettempdir()) / "visclick_hf_cache"
OUT_DIR = _REPO / "reports" / "tables"


def _bbox_to_xyxy_pixels(
    bbox: List[float], fmt: str, w: int, h: int, space: str
) -> Tuple[float, float, float, float]:
    """Convert ScreenSpot bbox list to absolute pixel (x1, y1, x2, y2).

    The HuggingFace ``rootsautomation/ScreenSpot`` rows use **fractions of
    image width/height** (not raw pixels). Default is ``space=normalized`` +
    ``fmt=xyxy`` so x1,x2 scale by ``w`` and y1,y2 by ``h``.
    """
    a, b, c, d = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
    if space == "normalized":
        if fmt == "xyxy":
            return a * w, b * h, c * w, d * h
        if fmt == "xywh":
            return a * w, b * h, (a + c) * w, (b + d) * h
    if space == "pixel":
        if fmt == "xywh":
            return a, b, a + c, b + d
        if fmt == "xyxy":
            return a, b, c, d
    raise ValueError(f"unknown bbox space/format: {space!r} {fmt!r}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compute CPV against the ScreenSpot desktop split (D-07 extra evidence)"
    )
    ap.add_argument("--weights", default=str(DEFAULT_WEIGHTS))
    ap.add_argument("--hf-id", default=DEFAULT_HF_ID,
                    help="HuggingFace dataset id (default: rootsautomation/ScreenSpot)")
    ap.add_argument("--cache-dir", default=str(DEFAULT_CACHE),
                    help="HuggingFace cache directory (data is downloaded once)")
    ap.add_argument("--platform-prefix", default="desktop",
                    help="Filter on data_source: default 'desktop' = windows OR macos "
                         "(HF ScreenSpot labels). Use 'windows', 'macos', 'web', … "
                         "for a startswith match on data_source.")
    ap.add_argument("--bbox-format", default="xyxy", choices=["xywh", "xyxy"],
                    help="BBox layout: HF ScreenSpot uses xyxy.")
    ap.add_argument(
        "--bbox-space",
        default="normalized",
        choices=["normalized", "pixel"],
        help="HF ScreenSpot bboxes are fractions of W/H (not pixels). "
             "Use ``pixel`` only if your snapshot stores absolute coordinates.",
    )
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--iou", type=float, default=0.50)
    ap.add_argument("--limit", type=int, default=0,
                    help="If > 0, evaluate only the first N entries (smoke test)")
    ap.add_argument("--tag", default="",
                    help="Suffix for output CSV filenames (e.g. --tag conf010).")
    args = ap.parse_args()

    try:
        from datasets import load_dataset
    except ImportError:
        print("[error] `datasets` not installed. Run:  pip install datasets pillow",
              file=sys.stderr)
        return 2

    cache_path = Path(args.cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    print(f"[info] loading HF dataset: {args.hf_id}  (cache={args.cache_dir})")
    ds = load_dataset(args.hf_id, cache_dir=str(cache_path))
    split_name = next(iter(ds.keys()))
    rows = ds[split_name]
    pfx = args.platform_prefix.lower()
    # HF `rootsautomation/ScreenSpot` uses data_source in {windows, macos, ...};
    # treat "desktop" as that published desktop slice (Win + macOS screens).
    if pfx == "desktop":
        def _source_match(src_norm: str) -> bool:
            return src_norm in ("windows", "macos")
        filter_desc = "data_source in {windows, macos}"
    else:
        def _source_match(src_norm: str) -> bool:
            return src_norm.startswith(pfx)
        filter_desc = f"data_source startswith '{args.platform_prefix}'"

    print(f"[info] split '{split_name}' has {len(rows)} rows; filtering ({filter_desc})")

    keep = []
    for r in rows:
        src = str(r.get("data_source", "")).lower()
        if _source_match(src):
            keep.append(r)
    if args.limit > 0:
        keep = keep[: args.limit]
    if not keep:
        print(f"[error] no rows matched filter ({filter_desc}).",
              file=sys.stderr)
        return 2
    print(f"[info] evaluating {len(keep)} rows")

    print(f"[info] weights: {args.weights}")
    det = Detector(args.weights)

    grand_total = 0
    grand_hit = 0
    # Aggregations by (data_source) and by (data_type: text|icon).
    by_source: Dict[str, List[int]] = {}   # name -> [total, hit]
    by_type: Dict[str, List[int]] = {}
    per_row: List[List[str]] = []

    for i, r in enumerate(keep):
        img = r.get("image")
        if img is None:
            # Some snapshots store images alongside; fallback to file_name in cache.
            fn = r.get("file_name", f"row_{i}")
            print(f"  [skip] no image bytes for row {i} (file_name={fn})")
            continue
        if not isinstance(img, Image.Image):
            img = Image.open(img)
        rgb = np.array(img.convert("RGB"))
        h, w = rgb.shape[:2]
        try:
            x1, y1, x2, y2 = _bbox_to_xyxy_pixels(
                r["bbox"], args.bbox_format, w, h, args.bbox_space
            )
        except Exception as e:  # noqa: BLE001
            print(f"  [skip] bad bbox row {i}: {e}")
            continue
        # Clamp to image bounds (some entries are slightly out).
        x1 = max(0.0, min(x1, w - 1))
        x2 = max(0.0, min(x2, w - 1))
        y1 = max(0.0, min(y1, h - 1))
        y2 = max(0.0, min(y2, h - 1))
        if x2 <= x1 or y2 <= y1:
            continue

        preds = det.predict(rgb, conf=args.conf, iou=args.iou)
        pred_centres = [((px1 + px2) / 2.0, (py1 + py2) / 2.0)
                        for (_cls, (px1, py1, px2, py2), _c) in preds]
        hit = 1 if any(x1 <= cx <= x2 and y1 <= cy <= y2 for cx, cy in pred_centres) else 0

        grand_total += 1
        grand_hit += hit

        src = str(r.get("data_source", "unknown"))
        dtype = str(r.get("data_type", "unknown"))
        by_source.setdefault(src, [0, 0])
        by_type.setdefault(dtype, [0, 0])
        by_source[src][0] += 1
        by_source[src][1] += hit
        by_type[dtype][0] += 1
        by_type[dtype][1] += hit

        per_row.append([
            str(r.get("file_name", f"row_{i}")),
            src,
            dtype,
            f"{x1:.1f}", f"{y1:.1f}", f"{x2:.1f}", f"{y2:.1f}",
            str(len(preds)),
            str(hit),
        ])

        if (i + 1) % 25 == 0 or i + 1 == len(keep):
            print(f"  [{i+1:4d}/{len(keep)}] running CPV "
                  f"so far = {(grand_hit / max(grand_total, 1) * 100):5.2f}%  "
                  f"({grand_hit}/{grand_total})")

    if grand_total == 0:
        print("[error] no usable rows", file=sys.stderr)
        return 2

    cpv_overall = grand_hit / grand_total * 100.0
    suffix = f"_{args.tag}" if args.tag else ""
    summary_csv = OUT_DIR / f"cpv_screenspot_{args.platform_prefix}{suffix}.csv"
    rows_csv = OUT_DIR / f"cpv_screenspot_{args.platform_prefix}{suffix}_rows.csv"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["slice_kind", "slice_name", "n_rows", "hits", "cpv_pct"])
        wr.writerow(["overall", args.platform_prefix, grand_total, grand_hit,
                     f"{cpv_overall:.2f}"])
        for name, (t, h_) in sorted(by_source.items()):
            wr.writerow(["data_source", name, t, h_, f"{(h_/t*100):.2f}"])
        for name, (t, h_) in sorted(by_type.items()):
            wr.writerow(["data_type", name, t, h_, f"{(h_/t*100):.2f}"])

    with rows_csv.open("w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["file_name", "data_source", "data_type",
                     "gt_x1", "gt_y1", "gt_x2", "gt_y2",
                     "n_predictions", "hit"])
        wr.writerows(per_row)

    print()
    print("Per data_source:")
    for name, (t, h_) in sorted(by_source.items()):
        print(f"  {name:24s} n={t:4d}  hit={h_:4d}  cpv={(h_/t*100):5.2f}%")
    print("Per data_type:")
    for name, (t, h_) in sorted(by_type.items()):
        print(f"  {name:24s} n={t:4d}  hit={h_:4d}  cpv={(h_/t*100):5.2f}%")
    print()
    print(f"[done] wrote {summary_csv}")
    print(f"[done] wrote {rows_csv}")
    print(f"REPORT cpv_screenspot | platform={args.platform_prefix}  "
          f"overall = {cpv_overall:.2f}%  ({grand_hit}/{grand_total})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
