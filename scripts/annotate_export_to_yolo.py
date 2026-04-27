"""Helper: convert CVAT YOLO 1.1 export into train/val/test layout. Stub — extend as needed."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("export_zip", type=Path, help="Path to CVAT YOLO export zip or folder")
    ap.add_argument("out_root", type=Path, help="Output root (images/, labels/)")
    args = ap.parse_args()
    if not args.export_zip.exists():
        raise SystemExit(f"Missing: {args.export_zip}")
    args.out_root.mkdir(parents=True, exist_ok=True)
    # TODO: unzip and split into images/train, labels/train, etc.
    print("Stub: implement CVAT → YOLO layout; see VisClick_Detailed_Plan.md Part F.")


if __name__ == "__main__":
    main()
