#!/usr/bin/env python3
"""Google Colab one-shot: mount Drive, clone/pull visclick, sync hand-corrected zip.

Run in Colab as ONE cell — paste the entire file contents, OR::

    !curl -sO https://raw.githubusercontent.com/HiranMadhu/visclick/main/scripts/colab_sync_handcorrected_one_cell.py
    !python colab_sync_handcorrected_one_cell.py

Writes: ``/content/drive/MyDrive/visclick/data/desktop_test_handcorrected.zip``

Then open ``notebooks/08_phase1A_handlabel.ipynb`` and run Section 4–5.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys

try:
    from google.colab import drive

    drive.mount("/content/drive", force_remount=False)
except ImportError:
    print("(not running on Colab — Drive mount skipped)")

DRIVE_DATA = Path("/content/drive/MyDrive/visclick/data")
REPO = Path("/content/visclick")
ZIP_IN_REPO = REPO / "datasets" / "handcorrected_desktop_test" / "visclick3.yolov8.zip"
OUT = DRIVE_DATA / "desktop_test_handcorrected.zip"
REPO_URL = "https://github.com/HiranMadhu/visclick.git"

DRIVE_DATA.mkdir(parents=True, exist_ok=True)

if not REPO.exists():
    print("Cloning visclick …")
    subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(REPO)], check=True)
else:
    print("git pull …")
    subprocess.run(["git", "-C", str(REPO), "pull", "--ff-only"], check=True)

if not ZIP_IN_REPO.is_file():
    print(f"ERROR: missing {ZIP_IN_REPO}", file=sys.stderr)
    sys.exit(2)

shutil.copy2(ZIP_IN_REPO, OUT)
mb = OUT.stat().st_size / 1024 / 1024
print(f"\nOK → {OUT} ({mb:.2f} MB)")
print("Next: notebooks/08_phase1A_handlabel.ipynb → Section 4 (import) then Section 5 (verify).")
