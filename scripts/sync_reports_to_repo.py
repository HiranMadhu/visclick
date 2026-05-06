#!/usr/bin/env python3
"""Copy small reports / figures / training curves from Google Drive into the repo.

The notebooks write CSVs and PNGs to::

    <DRIVE>/reports/tables/
    <DRIVE>/reports/figures/
    <DRIVE>/weights/phase1B/<model>/run1/results.png

Those locations are convenient for live work but invisible outside the Colab
session. This script copies the small dissertation-grade artefacts into the
repo at::

    reports/tables/
    reports/figures/

so that ``git pull`` / GitHub view restores them and the dissertation can
cite permanent paths.

What gets copied (each is small — KB to ~100 KB):
- every ``*.csv`` under ``<DRIVE>/reports/tables/``
- every ``*.png`` under ``<DRIVE>/reports/figures/``
- ``<DRIVE>/weights/phase1B/<model>/run1/results.png`` → ``reports/figures/phase1B_<model>_curves.png``

Big artefacts that **do NOT** get copied (size or noise):
- model weights (``*.pt``) — too big, live on Drive
- training run logs (``*.txt``, ``args.yaml``, ``train_batchN.jpg``) — noise
- ``<DRIVE>/data/*`` raw datasets — too big, live on Drive

Usage on Colab::

    !python scripts/sync_reports_to_repo.py

Or with explicit paths::

    !python scripts/sync_reports_to_repo.py \\
        --drive /content/drive/MyDrive/visclick \\
        --repo /content/visclick

After the script runs, the user is responsible for the ``git add / commit /
push`` (the script does NOT push automatically — keep credentials handling
explicit).
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def _copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.is_file():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--drive",
        type=Path,
        default=Path("/content/drive/MyDrive/visclick"),
        help="Drive visclick root (default: /content/drive/MyDrive/visclick).",
    )
    ap.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Local repo root (default: parent of scripts/).",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="List what WOULD be copied without writing.",
    )
    args = ap.parse_args()

    if not args.drive.exists():
        print(f"ERROR: Drive root not found: {args.drive}", file=sys.stderr)
        return 2
    if not args.repo.exists():
        print(f"ERROR: repo root not found: {args.repo}", file=sys.stderr)
        return 2

    print(f"drive = {args.drive}")
    print(f"repo  = {args.repo}\n")

    n_copied = 0
    n_skipped = 0
    pairs: list[tuple[Path, Path]] = []

    src_tables = args.drive / "reports" / "tables"
    if src_tables.is_dir():
        for csv in sorted(src_tables.glob("*.csv")):
            dst = args.repo / "reports" / "tables" / csv.name
            pairs.append((csv, dst))

    src_figs = args.drive / "reports" / "figures"
    if src_figs.is_dir():
        for png in sorted(src_figs.glob("*.png")):
            dst = args.repo / "reports" / "figures" / png.name
            pairs.append((png, dst))

    src_phase1b = args.drive / "weights" / "phase1B"
    if src_phase1b.is_dir():
        for model_dir in sorted(src_phase1b.iterdir()):
            curve = model_dir / "run1" / "results.png"
            if curve.is_file():
                dst = args.repo / "reports" / "figures" / f"phase1B_{model_dir.name}_curves.png"
                pairs.append((curve, dst))

    src_baseline = args.drive / "weights" / "baseline_source" / "run1" / "results.png"
    if src_baseline.is_file():
        pairs.append((src_baseline, args.repo / "reports" / "figures" / "baseline_source_curves.png"))
    src_ft = args.drive / "weights" / "desktop_finetune" / "run1" / "results.png"
    if src_ft.is_file():
        pairs.append((src_ft, args.repo / "reports" / "figures" / "desktop_finetune_curves.png"))

    for src, dst in pairs:
        rel = dst.relative_to(args.repo)
        if args.dry_run:
            print(f"  [dry] {src} → {rel}")
            continue
        try:
            ok = _copy_if_exists(src, dst)
        except OSError as e:
            print(f"  FAIL {src} → {rel}: {e}", file=sys.stderr)
            n_skipped += 1
            continue
        if ok:
            print(f"  copy {src.name:40s} → {rel}")
            n_copied += 1

    print(f"\n{'[dry-run] would copy' if args.dry_run else 'copied'}: {n_copied}  skipped: {n_skipped}")
    if not args.dry_run and n_copied:
        print("\nNext step:")
        print("  git -C", args.repo, "add reports/")
        print("  git -C", args.repo, "commit -m 'reports: sync from Drive'")
        print("  git -C", args.repo, "push")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
