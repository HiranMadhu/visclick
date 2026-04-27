#!/usr/bin/env python3
"""
Replace <DRIVE> in configs/yolo_*.yaml with a concrete path (e.g. Colab Drive).
Usage in Colab:
  %env VISCLICK_DRIVE=/content/drive/MyDrive/visclick
  !python scripts/patch_colab_configs.py
Or:
  python scripts/patch_colab_configs.py /content/drive/MyDrive/visclick
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    drive = os.environ.get("VISCLICK_DRIVE") or (sys.argv[1] if len(sys.argv) > 1 else "")
    if not drive:
        print("Set VISCLICK_DRIVE or pass path as first argument", file=sys.stderr)
        sys.exit(1)
    for name in ("yolo_source", "yolo_desktop_finetune"):
        p = ROOT / "configs" / f"{name}.yaml"
        if not p.exists():
            print("skip (missing):", p)
            continue
        text = p.read_text(encoding="utf-8")
        text = text.replace("<DRIVE>", drive.rstrip("/"))
        out = ROOT / "configs" / f"{name}_colab.yaml"
        out.write_text(text, encoding="utf-8")
        print("Wrote", out)


if __name__ == "__main__":
    main()
