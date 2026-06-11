"""Standalone D-04: simplified SHOT UDA on a Linux GPU box.

Mirrors notebooks/14_uda_shot.ipynb (8 epochs, freeze=15).

Usage:
  export VISCLICK_DATA=$HOME/visclick_data
  python scripts/run_uda_shot_local.py --data-root "$VISCLICK_DATA"
"""
from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from ultralytics import YOLO

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CLASSES = ["button", "text", "text_input", "icon", "menu", "checkbox"]
IMG_EXT = (".png", ".jpg", ".jpeg")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data-root", default=os.environ.get("VISCLICK_DATA"))
    p.add_argument("--repo-root", default=str(REPO))
    p.add_argument("--epochs", type=int, default=8)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--device", default="0")
    p.add_argument("--skip-train", action="store_true")
    return p.parse_args()


def materialise_screenspot(data_root: Path) -> Path:
    out_dir = data_root / "screenspot_desktop_pngs"
    out_dir.mkdir(parents=True, exist_ok=True)
    if sum(1 for f in out_dir.iterdir() if f.suffix.lower() in IMG_EXT) >= 100:
        return out_dir
    from datasets import load_dataset
    cache = Path(tempfile.gettempdir()) / "visclick_hf_cache"
    ds = load_dataset("rootsautomation/ScreenSpot", split="test", cache_dir=str(cache))
    for i, row in enumerate(ds):
        if row.get("data_source") not in ("macos", "windows"):
            continue
        p = out_dir / f"ss_{i:04d}.png"
        if not p.is_file():
            row["image"].save(p)
    return out_dir


def collect_targets(data_root: Path, repo_root: Path) -> list[str]:
    paths = []
    for d in (materialise_screenspot(data_root), repo_root / "samples" / "desktop_seed"):
        if d.is_dir():
            paths.extend(str(f) for f in d.iterdir() if f.suffix.lower() in IMG_EXT)
    paths = sorted(set(paths))
    assert len(paths) >= 100
    return paths


def pseudo_label_and_train(source_wts: Path, targets: list[str], shot_dir: Path,
                           epochs: int, batch: int, device: str) -> tuple[Path, int, float]:
    work = Path("/tmp/uda_shot_data")
    img_dir = work / "images" / "train"
    lbl_dir = work / "labels" / "train"
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    teacher = YOLO(str(source_wts))
    n_box = 0
    for path in targets:
        r = teacher.predict(path, imgsz=640, conf=0.50, verbose=False)[0]
        if len(r.boxes) == 0:
            continue
        stem = Path(path).stem
        dst = img_dir / Path(path).name
        if not dst.is_file():
            shutil.copy2(path, dst)
        with open(lbl_dir / f"{stem}.txt", "w") as fh:
            for cls, xyxy in zip(r.boxes.cls.tolist(), r.boxes.xyxyn.tolist()):
                x1, y1, x2, y2 = xyxy
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                fh.write(f"{int(cls)} {cx:.6f} {cy:.6f} {x2-x1:.6f} {y2-y1:.6f}\n")
        n_box += 1
    print(f"pseudo-labels: {n_box}/{len(targets)}")

    import yaml
    data_yaml = work / "data.yaml"
    data_yaml.write_text(yaml.safe_dump({
        "path": str(work), "train": "images/train", "val": "images/train",
        "names": CLASSES, "nc": len(CLASSES),
    }, sort_keys=False))

    t0 = time.time()
    YOLO(str(source_wts)).train(
        data=str(data_yaml), epochs=epochs, imgsz=640, batch=batch,
        device=device, cache=True, workers=4,
        project=str(shot_dir), name="shot_run", freeze=15,
        verbose=True, plots=False, exist_ok=True,
    )
    elapsed = time.time() - t0
    wts = shot_dir / "shot_run" / "weights" / "best.pt"
    if not wts.is_file():
        wts = shot_dir / "shot_run" / "weights" / "last.pt"
    return wts, n_box, elapsed


def run_cpv(weights: Path, repo_root: Path) -> tuple[float, float]:
    onnx = weights.with_suffix(".onnx")
    if not onnx.is_file():
        YOLO(str(weights)).export(format="onnx", imgsz=640, dynamic=False, opset=12)
    tag = "uda_shot"
    py = sys.executable
    tbl = repo_root / "reports" / "tables"
    for script in ("run_cpv_screenspot.py", "run_cpv.py"):
        r = subprocess.run(
            [py, str(repo_root / "scripts" / script), "--weights", str(onnx), "--tag", tag],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(r.stdout, r.stderr, file=sys.stderr)
            raise RuntimeError(f"{script} failed")
        print(r.stdout)
    ss_csv = tbl / f"cpv_screenspot_desktop_{tag}.csv"
    hc_csv = tbl / f"cpv_summary_{tag}.csv"
    with ss_csv.open() as fh:
        next(fh)
        cpv_ss = float(next(fh).strip().split(",")[-1])
    cpv_hc = float("nan")
    with hc_csv.open() as fh:
        next(fh)
        for line in fh:
            parts = line.strip().split(",")
            if parts and parts[0] == "OVERALL":
                cpv_hc = float(parts[-1])
    return cpv_ss, cpv_hc


def main() -> None:
    args = parse_args()
    if not args.data_root:
        sys.exit("ERROR: set --data-root or $VISCLICK_DATA")
    data_root = Path(args.data_root).resolve()
    repo_root = Path(args.repo_root).resolve()
    source_wts = data_root / "weights" / "baseline_source" / "best_source_v8s.pt"
    if not source_wts.is_file():
        sys.exit(f"ERROR: missing {source_wts}")

    shot_dir = data_root / "weights" / "uda_shot"
    shot_dir.mkdir(parents=True, exist_ok=True)
    adapted = shot_dir / "shot_run" / "weights" / "best.pt"
    n_box, elapsed = 0, 0.0

    if not args.skip_train and not adapted.is_file():
        targets = collect_targets(data_root, repo_root)
        adapted, n_box, elapsed = pseudo_label_and_train(
            source_wts, targets, shot_dir, args.epochs, args.batch, args.device)
        print(f"REPORT shot_train | elapsed_s = {elapsed:.1f} | weights = {adapted}")
    elif adapted.is_file():
        print(f"skip train — using {adapted}")
    else:
        sys.exit(f"ERROR: no weights at {adapted}")

    cpv_ss, cpv_hc = run_cpv(adapted, repo_root)
    print(f"REPORT shot_eval | cpv_screenspot = {cpv_ss:.2f} | cpv_handcorrected = {cpv_hc:.2f}")

    out_csv = repo_root / "reports" / "tables" / "uda_shot.csv"
    with out_csv.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["method", "epochs", "n_pseudo_imgs", "cpv_screenspot_%", "cpv_handcorrected_%"])
        w.writerow(["shot_simplified", args.epochs, n_box, f"{cpv_ss:.2f}", f"{cpv_hc:.2f}"])
    print(f"REPORT step = WRITE_CSV | path = {out_csv}")
    print("REPORT step = UDA_SHOT | status = done")


if __name__ == "__main__":
    main()
