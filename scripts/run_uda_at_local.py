"""Standalone D-03: simplified Adaptive Teacher UDA on a Linux GPU box.

Mirrors notebooks/13_uda_adaptive_teacher.ipynb (Colab Free budget:
500 subsampled source images, 1 outer iteration, 5 epochs).

Prerequisites:
  export VISCLICK_DATA=$HOME/visclick_data   # or shared path
  bash scripts/setup_visclick_data.sh        # Zenodo unified bundle
  # plus best_source_v8s.pt under $VISCLICK_DATA/weights/baseline_source/

  cd <repo>
  python3 -m venv .venv && source .venv/bin/activate
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
  pip install ultralytics datasets pillow opencv-python

  python scripts/run_uda_at_local.py --data-root "$VISCLICK_DATA"

Outputs:
  $VISCLICK_DATA/weights/uda_at/iter1/weights/best.pt
  <repo>/reports/tables/uda_adaptive_teacher.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import random
import shutil
import subprocess
import sys
import tarfile
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
    p.add_argument("--data-root", default=os.environ.get("VISCLICK_DATA"),
                   help="Root with unified/, source_train_bundles/, weights/")
    p.add_argument("--repo-root", default=str(REPO))
    p.add_argument("--source-cap", type=int, default=500,
                   help="Subsample source train images. 0 = use all (~8k full Zenodo).")
    p.add_argument("--n-outer", type=int, default=1,
                   help="Outer pseudo-label/train iterations (Adaptive Teacher protocol uses 3).")
    p.add_argument("--epochs", type=int, default=5,
                   help="Epochs per outer iteration.")
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--pseudo-conf", type=float, default=0.30)
    p.add_argument("--device", default="0", help="CUDA device id, or 'cpu'")
    p.add_argument("--tag", default="uda_at",
                   help="Output tag. Weights -> weights/<tag>/, CSV -> reports/tables/<tag>*.csv")
    p.add_argument("--skip-train", action="store_true",
                   help="Skip training; only run CPV eval on existing final weights.")
    return p.parse_args()


def bootstrap_bundles_from_unified(data_root: Path) -> Path:
    """Create minimal source_train_bundles if missing (manifest-only tarballs)."""
    bundles = data_root / "source_train_bundles"
    unified = data_root / "unified"
    if bundles.is_dir() and all((bundles / f"{sp}.tar.gz").is_file() for sp in ("train", "val")):
        return bundles
    print("building minimal source_train_bundles from unified/ (first run only)...")
    import io
    bundles.mkdir(parents=True, exist_ok=True)
    for sp in ("train", "val"):
        img_dir = unified / sp / "images"
        lbl_dir = unified / sp / "labels"
        assert img_dir.is_dir(), f"missing {img_dir} — run setup_visclick_data.sh"
        names = sorted(f.name for f in img_dir.iterdir() if f.suffix.lower() in IMG_EXT)
        # write a tiny tarball: manifests/<sp>.txt + labels/<sp>/*.txt for those names
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            manifest = f"manifests/{sp}.txt"
            data = ("\n".join(names) + "\n").encode()
            info = tarfile.TarInfo(name=manifest)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
            for fn in names:
                stem = Path(fn).stem
                lp = lbl_dir / f"{stem}.txt"
                if lp.is_file():
                    tf.add(lp, arcname=f"labels/{sp}/{stem}.txt")
        out = bundles / f"{sp}.tar.gz"
        out.write_bytes(buf.getvalue())
        print(f"  wrote {out} ({len(names)} images)")
    return bundles


def bootstrap_source(data_root: Path, source_cap: int) -> Path:
    """Materialise a YOLO-format source pool. source_cap=0 means use everything."""
    unified = data_root / "unified"
    bundles = bootstrap_bundles_from_unified(data_root)
    suffix = "full" if source_cap == 0 else str(source_cap)
    source_data = Path(f"/tmp/visclick_source_train_{suffix}")
    src_yaml = source_data / "data.yaml"

    if src_yaml.is_file():
        return source_data

    import yaml
    source_data.mkdir(parents=True, exist_ok=True)
    for sp in ("train", "val"):
        with tarfile.open(bundles / f"{sp}.tar.gz", "r:gz") as tf:
            tf.extractall(source_data)
        manifest = source_data / "manifests" / f"{sp}.txt"
        names = [ln.strip() for ln in manifest.read_text().splitlines() if ln.strip()]
        if sp == "train" and source_cap > 0 and len(names) > source_cap:
            random.seed(0)
            names = sorted(random.sample(names, source_cap))
            manifest.write_text("\n".join(names) + "\n")
            print(f"subsampled train: {source_cap}")
        else:
            print(f"{sp}: using {len(names)} images")
        src_img = unified / sp / "images"
        dst_img = source_data / "images" / sp
        dst_img.mkdir(parents=True, exist_ok=True)
        for fn in names:
            dst = dst_img / fn
            if not dst.exists():
                try:
                    dst.symlink_to(src_img / fn)
                except OSError:
                    shutil.copy2(src_img / fn, dst)
    src_yaml.write_text(yaml.safe_dump({
        "path": str(source_data), "train": "images/train", "val": "images/val",
        "nc": len(CLASSES), "names": CLASSES,
    }, sort_keys=False))
    print(f"bootstrap source_train at {source_data}")
    return source_data


def materialise_screenspot(data_root: Path) -> Path:
    out_dir = data_root / "screenspot_desktop_pngs"
    out_dir.mkdir(parents=True, exist_ok=True)
    n = sum(1 for f in out_dir.iterdir() if f.suffix.lower() in IMG_EXT)
    if n >= 100:
        print(f"ScreenSpot PNGs cached: {n}")
        return out_dir
    from datasets import load_dataset
    cache = Path(tempfile.gettempdir()) / "visclick_hf_cache"
    ds = load_dataset("rootsautomation/ScreenSpot", split="test", cache_dir=str(cache))
    written = 0
    for i, row in enumerate(ds):
        if row.get("data_source") not in ("macos", "windows"):
            continue
        p = out_dir / f"ss_{i:04d}.png"
        if not p.is_file():
            row["image"].save(p)
            written += 1
    print(f"ScreenSpot PNGs written: {written} -> {out_dir}")
    return out_dir


def collect_targets(data_root: Path, repo_root: Path) -> list[str]:
    paths: list[str] = []
    ss = materialise_screenspot(data_root)
    for f in ss.iterdir():
        if f.suffix.lower() in IMG_EXT:
            paths.append(str(f))
    seed = repo_root / "samples" / "desktop_seed"
    if seed.is_dir():
        for f in seed.iterdir():
            if f.suffix.lower() in IMG_EXT:
                paths.append(str(f))
    paths = sorted(set(paths))
    print(f"REPORT target_corpus | n = {len(paths)}")
    assert len(paths) >= 100, f"too few targets ({len(paths)})"
    return paths


def write_pseudo_labels(model, target_paths: list[str], work_dir: Path,
                        conf: float, imgsz: int) -> int:
    img_dir = work_dir / "images" / "train"
    lbl_dir = work_dir / "labels" / "train"
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)
    n_box = 0
    for path in target_paths:
        r = model.predict(path, imgsz=imgsz, conf=conf, verbose=False)[0]
        if len(r.boxes) == 0:
            continue
        stem = Path(path).stem
        out_img = img_dir / Path(path).name
        if not out_img.is_file():
            shutil.copy2(path, out_img)
        with open(lbl_dir / f"{stem}.txt", "w") as fh:
            for cls, xyxy in zip(r.boxes.cls.tolist(), r.boxes.xyxyn.tolist()):
                x1, y1, x2, y2 = xyxy
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                bw, bh = x2 - x1, y2 - y1
                fh.write(f"{int(cls)} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")
        n_box += 1
    return n_box


def build_mixed_yaml(source_data: Path, target_dir: Path, out_yaml: Path) -> None:
    import yaml
    data = {
        "path": "/",
        "train": [
            str(source_data / "images" / "train"),
            str(target_dir / "images" / "train"),
        ],
        "val": str(source_data / "images" / "val"),
        "names": CLASSES,
        "nc": len(CLASSES),
    }
    out_yaml.write_text(yaml.safe_dump(data, sort_keys=False))


def run_cpv(weights: Path, repo_root: Path, tag: str) -> tuple[float, float]:
    onnx = weights.with_suffix(".onnx")
    if not onnx.is_file():
        YOLO(str(weights)).export(format="onnx", imgsz=640, dynamic=False, opset=12)
    tbl = repo_root / "reports" / "tables"
    tbl.mkdir(parents=True, exist_ok=True)
    ss_csv = tbl / f"cpv_screenspot_desktop_{tag}.csv"
    hc_csv = tbl / f"cpv_summary_{tag}.csv"
    py = sys.executable
    for script, out in [
        ("run_cpv_screenspot.py", ss_csv),
        ("run_cpv.py", hc_csv),
    ]:
        r = subprocess.run(
            [py, str(repo_root / "scripts" / script), "--weights", str(onnx), "--tag", tag],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(r.stdout, r.stderr, file=sys.stderr)
            raise RuntimeError(f"{script} failed")
        print(r.stdout)
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
                break
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

    uda_dir = data_root / "weights" / args.tag
    uda_dir.mkdir(parents=True, exist_ok=True)
    final_iter_dir = uda_dir / f"iter{args.n_outer}"
    final_wts = final_iter_dir / "weights" / "best.pt"

    history: list[dict] = []
    teacher_weights = source_wts
    total_pseudo = 0
    total_elapsed = 0.0

    if not args.skip_train:
        source_data = bootstrap_source(data_root, args.source_cap)
        targets = collect_targets(data_root, repo_root)

        for t in range(1, args.n_outer + 1):
            iter_wts = uda_dir / f"iter{t}" / "weights" / "best.pt"
            if iter_wts.is_file():
                print(f"\n=== Outer iter {t}/{args.n_outer} — already trained, skipping ===")
                teacher_weights = iter_wts
                history.append({"iter": t, "n_pseudo": None, "weights": str(iter_wts), "skipped": True})
                continue

            print(f"\n=== Outer iter {t}/{args.n_outer} ===")
            work_dir = Path(f"/tmp/uda_at_{args.tag}_iter{t}")
            if work_dir.exists():
                shutil.rmtree(work_dir)
            teacher = YOLO(str(teacher_weights))
            n_pseudo = write_pseudo_labels(teacher, targets, work_dir, args.pseudo_conf, 640)
            print(f"  pseudo-labels: {n_pseudo}/{len(targets)} at conf {args.pseudo_conf}")

            data_yaml = work_dir / "data.yaml"
            build_mixed_yaml(source_data, work_dir, data_yaml)

            t0 = time.time()
            YOLO(str(teacher_weights)).train(
                data=str(data_yaml),
                epochs=args.epochs,
                imgsz=640,
                batch=args.batch,
                device=args.device,
                cache=True,
                workers=4,
                project=str(uda_dir),
                name=f"iter{t}",
                verbose=True,
                plots=False,
                exist_ok=True,
            )
            elapsed = time.time() - t0
            new_wts = uda_dir / f"iter{t}" / "weights" / "best.pt"
            if not new_wts.is_file():
                new_wts = uda_dir / f"iter{t}" / "weights" / "last.pt"
            teacher_weights = new_wts
            total_pseudo += n_pseudo
            total_elapsed += elapsed
            history.append({"iter": t, "n_pseudo": n_pseudo, "weights": str(new_wts),
                            "elapsed_s": elapsed})
            print(f"REPORT uda_at_iter | t = {t} | n_pseudo = {n_pseudo} | elapsed_s = {elapsed:.1f}")

        final_wts = teacher_weights
    elif final_wts.is_file():
        print(f"skip train — using {final_wts}")
    else:
        sys.exit(f"ERROR: no weights at {final_wts} and --skip-train not set")

    cpv_ss, cpv_hc = run_cpv(final_wts, repo_root, args.tag)
    print(f"REPORT uda_at_eval | cpv_screenspot = {cpv_ss:.2f} | cpv_handcorrected = {cpv_hc:.2f}")

    out_csv = repo_root / "reports" / "tables" / f"uda_adaptive_teacher_{args.tag}.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["method", "outer_iters", "epochs_per_iter", "source_cap",
                    "n_pseudo_total", "cpv_screenspot_%", "cpv_handcorrected_%", "elapsed_s"])
        w.writerow([f"adaptive_teacher_{args.tag}", args.n_outer, args.epochs,
                    args.source_cap or "all",
                    total_pseudo, f"{cpv_ss:.2f}", f"{cpv_hc:.2f}", f"{total_elapsed:.1f}"])
    print(f"REPORT step = WRITE_CSV | path = {out_csv}")
    print(f"REPORT step = UDA_AT | status = done | tag = {args.tag} "
          f"| cpv_ss = {cpv_ss:.2f} | cpv_hc = {cpv_hc:.2f}")


if __name__ == "__main__":
    main()
