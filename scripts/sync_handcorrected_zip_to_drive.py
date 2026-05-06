#!/usr/bin/env python3
"""Copy the committed hand-corrected Roboflow zip into Google Drive.

Phase-1 notebook ``08_phase1A_handlabel.ipynb`` expects the corrected export at::

    <DRIVE>/data/desktop_test_handcorrected.zip

After ``git pull``, run this once per machine so Colab or local notebooks find it.

Examples::

    # Colab / Linux (Drive mounted at default Colab path)
    python scripts/sync_handcorrected_zip_to_drive.py \\
        --dest /content/drive/MyDrive/visclick/data

    # Windows — replace with your Drive for Desktop folder
    python scripts/sync_handcorrected_zip_to_drive.py \\
        --dest "C:\\Users\\you\\Google Drive\\My Drive\\visclick\\data"

Environment::

    VISCLICK_DRIVE_DATA  — if set, used as default ``--dest`` (directory only).
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dest",
        type=Path,
        default=None,
        help="Google Drive data folder (parent of desktop_test_handcorrected.zip). "
        "Default: VISCLICK_DRIVE_DATA env var, else common Colab path if it exists.",
    )
    ap.add_argument(
        "--name",
        default="desktop_test_handcorrected.zip",
        help="Filename to write under --dest (default matches 08_phase1A_handlabel.ipynb).",
    )
    args = ap.parse_args()

    src = _repo_root() / "datasets" / "handcorrected_desktop_test" / "visclick3.yolov8.zip"
    if not src.is_file():
        print(f"ERROR: missing committed zip: {src}", file=sys.stderr)
        print("  Run git pull — the file should come from the repo.", file=sys.stderr)
        return 2

    dest_dir = args.dest
    if dest_dir is None:
        env = os.environ.get("VISCLICK_DRIVE_DATA")
        if env:
            dest_dir = Path(env)
        elif Path("/content/drive/MyDrive").exists():
            dest_dir = Path("/content/drive/MyDrive/visclick/data")
        else:
            print(
                "ERROR: pass --dest <path-to-visclick/data> or set VISCLICK_DRIVE_DATA.",
                file=sys.stderr,
            )
            print(
                "  Example (Colab): --dest /content/drive/MyDrive/visclick/data",
                file=sys.stderr,
            )
            return 2

    dest_dir = dest_dir.expanduser().resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / args.name

    shutil.copy2(src, out)
    print(f"OK: copied\n  from {src}\n  to   {out}")
    print(f"     ({out.stat().st_size / 1024 / 1024:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
