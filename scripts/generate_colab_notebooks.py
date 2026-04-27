#!/usr/bin/env python3
"""Regenerate notebooks/*.ipynb. Run from repo root: python scripts/generate_colab_notebooks.py"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "notebooks"

META = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.10.12"},
}


def src(s):
    if not s.endswith("\n"):
        s += "\n"
    return [line if line.endswith("\n") else line + "\n" for line in s.splitlines(True)]


def md_cell(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": src(text)}


def code_cell(code: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": src(code),
    }


def save(name, cells):
    nb = {"nbformat": 4, "nbformat_minor": 5, "metadata": META, "cells": cells}
    path = NB_DIR / name
    path.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print("Wrote", path)


BOOT_MD = """# VisClick — Colab setup

Run cells **top to bottom**. Authorise Google Drive when prompted.

- **GitHub** → code at `/content/visclick`
- **Drive** `MyDrive/visclick` → datasets + weights (persists after disconnect)
"""

BOOT_DRIVE = """from google.colab import drive
drive.mount("/content/drive")
"""

BOOT_REPO = """import os, subprocess
REPO = "https://github.com/HiranMadhu/visclick.git"
if not os.path.isdir("/content/visclick"):
    subprocess.run(["git", "clone", REPO, "/content/visclick"], check=True)
else:
    subprocess.run("cd /content/visclick && git pull --rebase", shell=True, check=False)
%cd /content/visclick
"""

BOOT_GPU = """import subprocess
try:
    import torch
    print("torch:", torch.__version__, "| cuda:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print(torch.cuda.get_device_name(0))
        print(subprocess.check_output(["nvidia-smi"]).decode())
except Exception as e:
    print("GPU check:", e)
"""

DRIVE_MK = """import os
DRIVE = "/content/drive/MyDrive/visclick"
os.makedirs(DRIVE, exist_ok=True)
for sub in (
    "data/raw", "data/clay", "data/vins", "data/webui", "data/ui_vision",
    "data/unified", "data/source_train", "data/desktop_labeled", "data/desktop_test",
    "weights/baseline_source", "weights/experiments", "videos",
):
    os.makedirs(os.path.join(DRIVE, sub), exist_ok=True)
print("DRIVE =", DRIVE)
"""

PIPS_ML = """!pip install -q ultralytics==8.* opencv-python "huggingface_hub[cli]>=0.20" tqdm matplotlib pandas
"""


def colab_bootstrap():
    return [
        md_cell(BOOT_MD),
        code_cell(BOOT_DRIVE),
        code_cell(BOOT_REPO),
        code_cell(BOOT_GPU),
        code_cell(DRIVE_MK),
    ]


def build_00():
    c = colab_bootstrap()
    c.append(md_cell("## 00 — Data acquisition\n\nSaves to **Drive** `visclick/data/`. RICO may need a manual browser download — see cell comments."))
    c.append(code_cell(PIPS_ML))
    c.append(
        code_cell(
            r"""# --- A) CLAY labels (images need RICO separately) ---
import os, subprocess
DRIVE = "/content/drive/MyDrive/visclick"
os.chdir(os.path.join(DRIVE, "data", "raw"))
if not os.path.isdir("clay"):
    subprocess.run(["git", "clone", "https://github.com/google-research-datasets/clay.git", "clay"], check=True)
import shutil
os.makedirs(os.path.join(DRIVE, "data", "clay"), exist_ok=True)
for f in os.listdir("clay"):
    src = os.path.join("clay", f)
    dst = os.path.join(DRIVE, "data", "clay", f)
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)
print("CLAY repo files copied to", os.path.join(DRIVE, "data", "clay"))"""
        )
    )
    c.append(
        code_cell(
            r"""# --- B) UI-Vision (desktop benchmark, ~781 MB) ---
import os, subprocess
DRIVE = "/content/drive/MyDrive/visclick"
out = os.path.join(DRIVE, "data", "ui_vision")
# huggingface-cli
subprocess.run(
    f'pip install -q huggingface_hub && hf download ServiceNow/ui-vision --repo-type dataset --local-dir "{out}"',
    shell=True,
    check=False,
)
print("UI-Vision target:", out)"""
        )
    )
    c.append(
        code_cell(
            """# --- C) Zenodo unified RICO+WebUI (large). Uncomment wget/unzip. ---
# In Colab, %cd is a magic command (OK on its own line).
DRIVE = "/content/drive/MyDrive/visclick"
%cd /content/drive/MyDrive/visclick/data/raw
# !wget -c -O rico_webui_unified.zip "https://zenodo.org/records/19195885/files/dataset.zip?download=1"
# !unzip -q -o rico_webui_unified.zip -d ../unified
print("If you uncommented: data is in data/unified. Verify URL on Zenodo if download fails.")
"""
        )
    )
    c.append(
        code_cell(
            """# --- D) VINS (clone repo; image archives from VINS README) ---
DRIVE = "/content/drive/MyDrive/visclick"
%cd /content/drive/MyDrive/visclick/data/raw
# !git clone https://github.com/sbunian/VINS.git vins_repo
print("Extract VINS images to", f"{DRIVE}/data/vins", "per official README")
"""
        )
    )
    c.append(
        md_cell(
            """**RICO screenshots:** `interactionmining.org/rico` — often no stable wget. Download the zip, upload to Drive `data/raw/rico_unique_uis.zip`, then in a new cell: `!unzip -q rico_unique_uis.zip -d ../rico` from `data/raw`.\n\n**Next:** assemble `data/source_train` in YOLO format (see detailed plan C.5) or use `unified` if you downloaded Zenodo."""
        )
    )
    return c


def build_01():
    c = colab_bootstrap() + [code_cell(PIPS_ML)]
    c.append(
        md_cell(
            """## 01 — EDA (exploratory data analysis)

Expects at least one of: `DRIVE/data/unified`, `DRIVE/data/source_train`, or YOLO `images/`+`labels/` with nested train/val.\n\nSaves figures under the repo: `reports/figures/eda/`."""
        )
    )
    c.append(
        code_cell(
            r"""import os, glob, random, collections
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import cv2

DRIVE = "/content/drive/MyDrive/visclick"
REPO = "/content/visclick"
OUT = os.path.join(REPO, "reports", "figures", "eda")
os.makedirs(OUT, exist_ok=True)

# Prefer user-assembled source_train; else try unified
candidates = [
    os.path.join(DRIVE, "data", "source_train"),
    os.path.join(DRIVE, "data", "unified"),
]
root = next((p for p in candidates if os.path.isdir(os.path.join(p, "labels", "train")) or os.path.isdir(os.path.join(p, "train", "labels"))), None)
if root is None:
    # YOLO layout: dataset/images/train and dataset/labels/train
    for p in candidates:
        if p and os.path.isdir(p):
            for images_dir in [os.path.join(p, "images", "train"), os.path.join(p, "train", "images")]:
                if os.path.isdir(images_dir):
                    root = p
                    break
        if root:
            break

if not root or not os.path.isdir(root or ""):
    print("No dataset found under", candidates, "- run 00 and assemble source_train, or download Zenodo unified first.")
else:
    print("Using root:", root)
    label_files = []
    for pat in [os.path.join(root, "labels", "train", "*.txt"), os.path.join(root, "train", "labels", "*.txt")]:
        label_files.extend(glob.glob(pat))
    if not label_files:
        label_files = glob.glob(os.path.join(root, "**", "labels", "*.txt"), recursive=True)[:5000]
    class_counts = collections.Counter()
    widths, heights = [], []
    for lf in label_files[:5000]:
        try:
            h, w = 0, 0
            im_base = os.path.splitext(os.path.basename(lf))[0]
            for sub in ["images/train", "train/images", "images"]:
                for ext in (".png", ".jpg", ".jpeg"):
                    ip = os.path.join(root, sub, im_base + ext)
                    if os.path.isfile(ip):
                        im = cv2.imread(ip)
                        if im is not None:
                            h, w = im.shape[:2]
                            break
        except Exception:
            pass
        with open(lf) as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 5:
                    class_counts[int(parts[0])] += 1
        if w and h:
            widths.append(w)
            heights.append(h)
    if class_counts:
        plt.figure(figsize=(8, 4))
        cls_ids = sorted(class_counts.keys())
        plt.bar([str(x) for x in cls_ids], [class_counts[x] for x in cls_ids])
        plt.title("Instance count per class id (YOLO label files)")
        plt.xlabel("class id")
        p = os.path.join(OUT, "eda_class_balance.png")
        plt.savefig(p, dpi=150, bbox_inches="tight")
        plt.show()
        print("Saved", p)
    if widths:
        plt.figure(figsize=(8, 4))
        plt.hist(np.array(widths), bins=20, alpha=0.5, label="W")
        plt.hist(np.array(heights), bins=20, alpha=0.5, label="H")
        plt.legend()
        plt.title("Image W/H in sampled set")
        p2 = os.path.join(OUT, "eda_resolutions.png")
        plt.savefig(p2, dpi=150, bbox_inches="tight")
        plt.show()
        print("Saved", p2)"""
        )
    )
    return c


def build_02():
    c = colab_bootstrap() + [code_cell(PIPS_ML)]
    c.append(md_cell("## 02 — Train source domain (YOLOv8s)\n\nRequires `DRIVE/.../data/source_train` in YOLO layout with `images/{train,val,test}` and `labels/{...}` and `yolo_source_colab.yaml` (generated by patch script). **Edit `DRIVE` if your folder name differs.**"))
    c.append(
        code_cell(
            r"""import os
DRIVE = "/content/drive/MyDrive/visclick"
os.environ["VISCLICK_DRIVE"] = DRIVE
!python scripts/patch_colab_configs.py"""
        )
    )
    c.append(
        code_cell(
            r"""# Verify dataset path exists
import os
DRIVE = "/content/drive/MyDrive/visclick"
st = os.path.join(DRIVE, "data", "source_train")
ok = os.path.isdir(os.path.join(st, "images", "train")) and os.path.isdir(os.path.join(st, "labels", "train"))
print("source_train OK:", ok, st)
if not ok:
    print("Build source_train (see plan C.5) or point Zenodo unified to YOLO + map classes to 6 before training here.")"""
        )
    )
    c.append(
        code_cell(
            r"""# Train (writes weights to Drive)
import time
from ultralytics import YOLO

DRIVE = "/content/drive/MyDrive/visclick"
t0 = time.time()
model = YOLO("yolov8s.pt")
results = model.train(
    data="configs/yolo_source_colab.yaml",
    epochs=30,
    imgsz=640,
    batch=16,
    workers=2,
    optimizer="AdamW",
    lr0=0.001,
    cos_lr=True,
    patience=10,
    project=f"{DRIVE}/weights/baseline_source",
    name="run1",
    seed=0,
    save=True,
    plots=True,
)
print("train wall (s):", int(time.time() - t0))"""
        )
    )
    c.append(
        code_cell(
            r"""# Copy best weights to stable name
import os, shutil
DRIVE = "/content/drive/MyDrive/visclick"
src = f"{DRIVE}/weights/baseline_source/run1/weights/best.pt"
dst = f"{DRIVE}/weights/baseline_source/best_source_v8s.pt"
if os.path.isfile(src):
    shutil.copy2(src, dst)
    print("Saved", dst)
else:
    print("Missing", src, "- finish training or resume from last.pt")"""
        )
    )
    c.append(
        code_cell(
            r"""# Validate + metrics
from ultralytics import YOLO
import os
DRIVE = "/content/drive/MyDrive/visclick"
p = f"{DRIVE}/weights/baseline_source/best_source_v8s.pt"
if not os.path.isfile(p):
    p = f"{DRIVE}/weights/baseline_source/run1/weights/best.pt"
m = YOLO(p)
metrics = m.val(data="configs/yolo_source_colab.yaml", split="test")
print(metrics)"""
        )
    )
    return c


def build_03():
    c = colab_bootstrap() + [code_cell(PIPS_ML)]
    c.append(
        md_cell("## 03 — Fine-tune on desktop (YOLO)\n\nAfter CVAT export to `DRIVE/.../data/desktop_labeled` in YOLO format.")
    )
    c.append(code_cell("import os\nDRIVE = \"/content/drive/MyDrive/visclick\"\nos.environ[\"VISCLICK_DRIVE\"] = DRIVE\n!python scripts/patch_colab_configs.py"))
    c.append(
        code_cell(
            r"""from ultralytics import YOLO
import os, time
DRIVE = "/content/drive/MyDrive/visclick"
# Start from source baseline
w = f"{DRIVE}/weights/baseline_source/best_source_v8s.pt"
if not os.path.isfile(w):
    w = "yolov8s.pt"
m = YOLO(w)
t0 = time.time()
m.train(
    data="configs/yolo_desktop_finetune_colab.yaml",
    epochs=120,
    imgsz=640,
    batch=8,
    optimizer="AdamW",
    lr0=5e-4,
    cos_lr=True,
    freeze=10,
    warmup_epochs=3,
    patience=20,
    project=f"{DRIVE}/weights/experiments",
    name="M3_desktop",
    plots=True,
)
print("s:", int(time.time() - t0))"""
        )
    )
    return c


def build_04():
    c = colab_bootstrap() + [code_cell(PIPS_ML)]
    c.append(
        md_cell("## 04 — Transfer experiments (M0–M8)\n\nUncomment the block for the method you want. Requires desktop data + (for M2–M5) `best_source_v8s.pt`.\n\nLog rows in `reports/tables/transfer_experiments.csv` (create in repo, then save notebook to GitHub or copy from Colab).")
    )
    c.append(
        code_cell(
            """import os
DRIVE = "/content/drive/MyDrive/visclick"
os.environ["VISCLICK_DRIVE"] = DRIVE
!python scripts/patch_colab_configs.py
"""
        )
    )
    c.append(
        code_cell(
            r"""# M1 — COCO yolov8s -> desktop only
# from ultralytics import YOLO
# DRIVE = "/content/drive/MyDrive/visclick"
# m = YOLO("yolov8s.pt")
# m.train(data="configs/yolo_desktop_finetune_colab.yaml", epochs=80, imgsz=640, batch=8,
#         optimizer="AdamW", lr0=1e-3, patience=15, project=f"{DRIVE}/weights/experiments", name="M1")
print("Uncomment a method in the cells below. DRIVE = /content/drive/MyDrive/visclick")"""
        )
    )
    c.append(
        code_cell(
            r"""# M0 scratch YOLOv8n
# DRIVE = "/content/drive/MyDrive/visclick"
# from ultralytics import YOLO
# m = YOLO("yolov8n.pt")
# m.train(data="configs/yolo_desktop_finetune_colab.yaml", ... name="M0")
pass"""
        )
    )
    c.append(
        code_cell(
            r"""# M2 / M3 (example M3) — from source weights
# DRIVE = "/content/drive/MyDrive/visclick"
# from ultralytics import YOLO
# m = YOLO(f"{DRIVE}/weights/baseline_source/best_source_v8s.pt")
# m.train(data="configs/yolo_desktop_finetune_colab.yaml", epochs=120, imgsz=640, batch=8,
#         optimizer="AdamW", lr0=5e-4, cos_lr=True, freeze=10, warmup_epochs=3, patience=20,
#         project=f"{DRIVE}/weights/experiments", name="M3")
pass"""
        )
    )
    return c


def build_05():
    c = colab_bootstrap() + [code_cell(PIPS_ML)]
    c.append(
        md_cell("## 05 — Eval, val metrics, export ONNX\n\n`model.val()` on desktop + optional UI-Vision; `export` for Windows bot.")
    )
    c.append(code_cell("import os\nDRIVE = \"/content/drive/MyDrive/visclick\"\nos.environ[\"VISCLICK_DRIVE\"] = DRIVE\n!python scripts/patch_colab_configs.py"))
    c.append(
        code_cell(
            r"""from ultralytics import YOLO
import os
DRIVE = "/content/drive/MyDrive/visclick"
# Point to your best run
pt = f"{DRIVE}/weights/experiments/M3_desktop/weights/best.pt"  # adjust name
if not os.path.isfile(pt):
    pt = f"{DRIVE}/weights/baseline_source/best_source_v8s.pt"
m = YOLO(pt)
# Desktop set
d = m.val(data="configs/yolo_desktop_finetune_colab.yaml", split="test")
print(d)"""
        )
    )
    c.append(
        code_cell(
            r"""# Optional: UI-Vision (if yolo config prepared for that data — otherwise skip)
# m.val(data="configs/uivision_data.yaml", ...)
print("Add UI-Vision data.yaml when ready, or use predict() on sample images from ui_vision folder.")"""
        )
    )
    c.append(
        code_cell(
            r"""# Export ONNX (copy to Windows for bot)
from ultralytics import YOLO
import os
DRIVE = "/content/drive/MyDrive/visclick"
pt = f"{DRIVE}/weights/experiments/M3_desktop/weights/best.pt"
m = YOLO(pt) if os.path.isfile(pt) else YOLO(f"{DRIVE}/weights/baseline_source/best_source_v8s.pt")
m.export(format="onnx", opset=12, simplify=True)
print("best.onnx next to best.pt; download to PC into local weights/visclick.onnx")"""
        )
    )
    return c


def main() -> None:
    save("00_data_acquisition.ipynb", build_00())
    save("01_data_eda.ipynb", build_01())
    save("02_train_source.ipynb", build_02())
    save("03_finetune_desktop.ipynb", build_03())
    save("04_experiments_transfer.ipynb", build_04())
    save("05_eval_and_ablations.ipynb", build_05())
    print("Done.")


if __name__ == "__main__":
    main()
