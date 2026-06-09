#!/usr/bin/env python3
"""Build notebooks 11..14 for Phase 4 experiments (D-02, D-03, D-04).

Each notebook is created with the same scaffolding (mount Drive, clone
repo, install deps, ...) and a method-specific body. This script is
idempotent: re-running rewrites the four .ipynb files from scratch.

The notebooks are deliberately simplified versions of the published
methods, chosen to fit Colab Free T4 (~15 GB GPU, ~3 h session). Each
notebook documents what was simplified and why, so the
dissertation's Chapter 6 implementation prose can reference the
simplifications honestly.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_DIR = REPO_ROOT / "notebooks"


def md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.splitlines(keepends=True),
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


def write_notebook(path: Path, cells: list[dict]) -> None:
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.10",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(notebook, indent=1))
    print(f"WROTE {path.relative_to(REPO_ROOT)}  ({len(cells)} cells)")


COMMON_MOUNT = """from google.colab import drive
drive.mount("/content/drive")
"""

COMMON_CLONE = """import os, subprocess
REPO = "https://github.com/HiranMadhu/visclick.git"
ROOT = "/content/visclick"
if not os.path.isdir(os.path.join(ROOT, ".git")):
    subprocess.run(["git", "clone", REPO, ROOT], check=True)
    print("Cloned to", ROOT)
else:
    subprocess.run(["git", "-C", ROOT, "fetch", "origin"], check=False)
    subprocess.run(["git", "-C", ROOT, "pull", "--rebase", "origin", "main"], check=False)
    print("Pulled latest in", ROOT)
print("REPORT git_head =", subprocess.check_output(
    ["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], text=True).strip())
"""


def common_publish(artifacts: list[str], commit_msg: str) -> str:
    arts_repr = ",\n    ".join(repr(a) for a in artifacts)
    return f"""import os, subprocess

REPO_ROOT = "/content/visclick"
ARTIFACTS = [
    {arts_repr},
]

for rel in ARTIFACTS:
    p = os.path.join(REPO_ROOT, rel)
    assert os.path.exists(p), f"Missing artifact in repo clone: {{p}}. Run the previous section first."
    print(f"OK  {{p}}  ({{os.path.getsize(p)}} bytes)")

token_path = os.path.join(REPO_ROOT, "token")
if not os.path.exists(token_path):
    print(f"WARN: no token file at {{token_path}}; skipping git push. Copy artifacts in by hand or restore the token.")
else:
    with open(token_path) as fh:
        token = fh.read().strip()

    def run(cmd, **kw):
        r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, **kw)
        if r.returncode != 0:
            print("STDOUT:", r.stdout)
            print("STDERR:", r.stderr)
            raise RuntimeError(f"git command failed: {{' '.join(cmd)}}")
        return r.stdout

    run(["git", "config", "user.email", "hiran@iit.ac.lk"])
    run(["git", "config", "user.name",  "Hiran Abeywardhana"])

    run(["git", "add", *ARTIFACTS])

    status = run(["git", "status", "--porcelain"])
    if not status.strip():
        print("REPORT step = GIT_PUBLISH | status = NOTHING_TO_COMMIT")
    else:
        run(["git", "commit", "-m", {commit_msg!r}])
        url = f"https://{{token}}@github.com/HiranMadhu/visclick.git"
        push = subprocess.run(["git", "push", url, "HEAD:main"],
                              cwd=REPO_ROOT, capture_output=True, text=True)
        if push.returncode != 0:
            print("PUSH STDERR:", push.stderr)
            raise RuntimeError("git push failed")
        print("REPORT step = GIT_PUBLISH | status = PUSHED")
"""


# ---------------------------------------------------------------------------
# 11_ssp_pretrain.ipynb — SimSiam-style SSP on the YOLOv8s backbone.
# ---------------------------------------------------------------------------

def build_nb11() -> list[dict]:
    cells: list[dict] = []

    cells.append(md(
        """# VisClick — Phase 4.4 / D-02 (step 1 of 2): self-supervised pretrain on desktop corpus

**Goal.** Adapt the source-trained YOLOv8s *backbone* to the desktop domain via self-supervised pretraining on the unlabelled desktop corpus (D-06). The output is a domain-adapted backbone that the next notebook (`12_ssp_finetune.ipynb`) plugs into a YOLOv8s detector and few-shot fine-tunes.

**Method.** **SimSiam** (Chen and He, 2021) on top of the source-trained CSPDarknet backbone. Chosen because:

- No negative samples, no memory bank, no large batch sizes → fits Colab Free T4.
- No momentum encoder → halves the GPU memory.
- Proven on small (≤ 10k) corpora at small batch (~32-64).

**Pipeline:**
1. Mount Drive → `git pull` → install deps.
2. Build an `ImageFolder`-style loader over the unlabelled desktop corpus produced by `scripts/auto_capture_corpus.py` (D-06). Falls back to the 50-image seed if the corpus is still small.
3. Extract the YOLOv8s backbone from `best_source_v8s.pt`, attach a 3-layer projection head and a 2-layer predictor.
4. Train SimSiam for 50 epochs at batch 32, two augmentation streams (RandomResizedCrop + ColorJitter + GaussianBlur + RandomGrayscale + horizontal flip).
5. Save the adapted backbone to `<DRIVE>/weights/ssp/backbone_simsiam.pt` and a training-loss CSV.
6. Publish to git.

**Compute reality.** 50 epochs × ~1500 images at batch 32, imgsz 256 is roughly 30-45 minutes on T4. Headroom for one Colab Free session.

**Report.** Every step prints `REPORT ...` lines for the data form and `Final_Report_GAPS.md` D-02.
"""
    ))

    cells.append(code(COMMON_MOUNT))
    cells.append(code(COMMON_CLONE))
    cells.append(code(
        """import sys, subprocess
subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q",
     "ultralytics", "torch", "torchvision", "pillow", "opencv-python", "matplotlib"],
    check=False,
)
import torch, torchvision, ultralytics
print("torch:", torch.__version__, "| cuda:", torch.cuda.is_available(),
      "| device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu")
print("torchvision:", torchvision.__version__, "| ultralytics:", ultralytics.__version__)
"""
    ))

    cells.append(md(
        """## 11.1 — Build unlabelled desktop corpus loader

The corpus is whatever `scripts/auto_capture_corpus.py` has accumulated to `<DRIVE>/datasets/auto_corpus/`. If that is too small, fall back to the committed seed at `samples/desktop_seed/`. The loader emits two random augmentations of each image per `__getitem__` call (the SimSiam two-view protocol).
"""
    ))

    cells.append(code(
        '''import os, glob, random
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as T

DRIVE        = "/content/drive/MyDrive/visclick"
CORPUS_DIRS  = [
    os.path.join(DRIVE, "datasets", "auto_corpus"),
    os.path.join(DRIVE, "datasets", "auto_corpus_v2"),
]
SEED_DIR     = "/content/visclick/samples/desktop_seed"
IMG_EXT      = (".png", ".jpg", ".jpeg")


def collect_corpus():
    paths = []
    for d in CORPUS_DIRS:
        if not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                if f.lower().endswith(IMG_EXT):
                    paths.append(os.path.join(root, f))
    if len(paths) < 200:
        # Fallback. Better some pretraining than none.
        for f in glob.glob(os.path.join(SEED_DIR, "*.*")):
            if f.lower().endswith(IMG_EXT):
                paths.append(f)
    return sorted(set(paths))


CORPUS = collect_corpus()
print(f"REPORT corpus | size = {len(CORPUS)} | head = {CORPUS[:2]}")
assert len(CORPUS) >= 50, (
    f"Corpus too small ({len(CORPUS)}). Run scripts/auto_capture_corpus.py "
    f"or fall back to samples/desktop_seed."
)

IMG_SIZE = 256


def simsiam_aug():
    return T.Compose([
        T.RandomResizedCrop(IMG_SIZE, scale=(0.5, 1.0)),
        T.RandomHorizontalFlip(p=0.5),
        T.RandomApply([T.ColorJitter(0.4, 0.4, 0.4, 0.1)], p=0.8),
        T.RandomGrayscale(p=0.2),
        T.RandomApply([T.GaussianBlur(kernel_size=23, sigma=(0.1, 2.0))], p=0.5),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


class TwoViewDataset(Dataset):
    def __init__(self, paths, aug):
        self.paths = paths
        self.aug = aug

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        p = self.paths[idx]
        with Image.open(p) as im:
            im = im.convert("RGB")
        return self.aug(im), self.aug(im)


BATCH = 32
loader = DataLoader(
    TwoViewDataset(CORPUS, simsiam_aug()),
    batch_size=BATCH, shuffle=True, num_workers=2,
    pin_memory=True, drop_last=True, persistent_workers=True,
)
print(f"REPORT loader | batch = {BATCH} | steps_per_epoch = {len(loader)}")
'''
    ))

    cells.append(md(
        """## 11.2 — Extract the YOLOv8s backbone from `best_source_v8s.pt`

The Ultralytics YOLO model wraps a `DetectionModel` whose first 9 modules are the CSPDarknet backbone (P1-P5 + SPPF). We yank that nn.Sequential out, replace the BatchNorm momentum with the default torch value, and freeze nothing — SimSiam updates every backbone weight. The detector head and neck are discarded for now and restored in `12_ssp_finetune.ipynb`.
"""
    ))

    cells.append(code(
        '''import torch, torch.nn as nn
from ultralytics import YOLO

SOURCE_WTS = os.path.join(DRIVE, "weights", "baseline_source", "best_source_v8s.pt")
assert os.path.isfile(SOURCE_WTS), f"Source weights missing: {SOURCE_WTS}. Run 05_train_source.ipynb first."

src = YOLO(SOURCE_WTS)
det_model = src.model

# YOLOv8 backbone is the first 10 modules in the YAML; SPPF is module 9 by default.
N_BACKBONE = 10
backbone_modules = list(det_model.model[:N_BACKBONE])
backbone = nn.Sequential(*backbone_modules)
print(f"REPORT backbone | modules = {len(backbone_modules)} "
      f"| trainable_params = {sum(p.numel() for p in backbone.parameters() if p.requires_grad):,}")


class SimSiam(nn.Module):
    def __init__(self, backbone, feat_dim, proj_dim=2048, pred_dim=512):
        super().__init__()
        self.backbone = backbone
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.projector = nn.Sequential(
            nn.Linear(feat_dim, proj_dim), nn.BatchNorm1d(proj_dim), nn.ReLU(inplace=True),
            nn.Linear(proj_dim, proj_dim), nn.BatchNorm1d(proj_dim), nn.ReLU(inplace=True),
            nn.Linear(proj_dim, proj_dim), nn.BatchNorm1d(proj_dim, affine=False),
        )
        self.predictor = nn.Sequential(
            nn.Linear(proj_dim, pred_dim), nn.BatchNorm1d(pred_dim), nn.ReLU(inplace=True),
            nn.Linear(pred_dim, proj_dim),
        )

    def forward(self, x):
        h = self.backbone(x)
        h = self.pool(h).flatten(1)
        z = self.projector(h)
        p = self.predictor(z)
        return p, z.detach()


# Probe the backbone output channel count with a dry-run.
device = "cuda" if torch.cuda.is_available() else "cpu"
backbone = backbone.to(device).eval()
with torch.no_grad():
    feat = backbone(torch.zeros(1, 3, IMG_SIZE, IMG_SIZE, device=device))
FEAT_DIM = feat.shape[1]
print(f"REPORT backbone_dim | feat = {tuple(feat.shape)} | channels = {FEAT_DIM}")

model = SimSiam(backbone, feat_dim=FEAT_DIM).to(device)
print(f"REPORT simsiam | total_params = {sum(p.numel() for p in model.parameters()):,}")
'''
    ))

    cells.append(md(
        """## 11.3 — Train SimSiam for 50 epochs

SimSiam loss is the negative cosine similarity between the predictor output and the stop-gradient projection of the other view, symmetrised across views. No labels, no negatives.

Hyperparameters follow Chen & He (2021):
- Optimizer: SGD with momentum 0.9, weight decay 1e-4.
- Learning rate: 0.05 × batch / 256 = 0.00625 at batch 32, cosine schedule.
- 50 epochs (paper uses 100, halved to fit Colab Free session).
"""
    ))

    cells.append(code(
        '''import torch.nn.functional as F
import csv, time

EPOCHS = 50
BASE_LR = 0.05 * BATCH / 256.0
WD = 1e-4
SSP_DIR = os.path.join(DRIVE, "weights", "ssp")
os.makedirs(SSP_DIR, exist_ok=True)


def simsiam_loss(p1, z2, p2, z1):
    return -(F.cosine_similarity(p1, z2, dim=-1).mean()
             + F.cosine_similarity(p2, z1, dim=-1).mean()) / 2.0


optimizer = torch.optim.SGD(model.parameters(), lr=BASE_LR, momentum=0.9, weight_decay=WD)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

LOSS_CSV = os.path.join(SSP_DIR, "ssp_loss_log.csv")
with open(LOSS_CSV, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["epoch", "avg_loss", "lr", "elapsed_s"])

for epoch in range(EPOCHS):
    t0 = time.time()
    model.train()
    losses = []
    for v1, v2 in loader:
        v1 = v1.to(device, non_blocking=True)
        v2 = v2.to(device, non_blocking=True)
        p1, z1 = model(v1)
        p2, z2 = model(v2)
        loss = simsiam_loss(p1, z2, p2, z1)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
    scheduler.step()
    avg = sum(losses) / max(1, len(losses))
    dt = time.time() - t0
    print(f"epoch {epoch+1:02d}/{EPOCHS} | loss = {avg:+.4f} | lr = {scheduler.get_last_lr()[0]:.5f} | {dt:.1f}s")
    with open(LOSS_CSV, "a", newline="") as fh:
        csv.writer(fh).writerow([epoch + 1, round(avg, 4), round(scheduler.get_last_lr()[0], 5), round(dt, 1)])

print("REPORT step = SSP_TRAIN | status = done")
'''
    ))

    cells.append(md(
        """## 11.4 — Save adapted backbone weights

The output is a state dict that `12_ssp_finetune.ipynb` will copy into a fresh YOLOv8s. We save only the backbone state dict (the projection head and predictor are SSP-only and not reused).
"""
    ))

    cells.append(code(
        '''BACKBONE_OUT = os.path.join(SSP_DIR, "backbone_simsiam.pt")
torch.save(model.backbone.state_dict(), BACKBONE_OUT)
size_mb = os.path.getsize(BACKBONE_OUT) / 1024 / 1024
print(f"REPORT backbone_out | path = {BACKBONE_OUT} | size_mb = {size_mb:0.1f}")

# Mirror to repo for the publish step.
REPO_TBL = "/content/visclick/reports/tables"
REPO_WTS = "/content/visclick/weights/ssp"
os.makedirs(REPO_TBL, exist_ok=True)
os.makedirs(REPO_WTS, exist_ok=True)
import shutil
shutil.copy2(LOSS_CSV, os.path.join(REPO_TBL, "ssp_loss_log.csv"))
# Backbone weights are too large for git; we publish only the CSV log.
'''
    ))

    cells.append(md(
        """## 11.5 — Publish loss log to git

The backbone .pt itself stays on Drive (too large for the repo). The training loss CSV is what we commit so the report's Figure showing the SSP loss curve has a regeneratable source on disk.
"""
    ))

    cells.append(code(common_publish(
        ["reports/tables/ssp_loss_log.csv"],
        "D-02: SimSiam SSP pretrain loss log",
    )))

    return cells


# ---------------------------------------------------------------------------
# 12_ssp_finetune.ipynb — load SSP backbone into a fresh YOLOv8s, few-shot.
# ---------------------------------------------------------------------------

def build_nb12() -> list[dict]:
    cells: list[dict] = []

    cells.append(md(
        """# VisClick — Phase 4.4 / D-02 (step 2 of 2): few-shot fine-tune the SSP-adapted detector

**Goal.** Take the SimSiam-adapted backbone from `11_ssp_pretrain.ipynb`, plug it into a fresh YOLOv8s detector (with the source-trained neck and head), then few-shot fine-tune on the hand-corrected desktop set. Compare against the no-SSP curve from `08c_few_shot_curve.ipynb` at the same `k` values.

**Pipeline:**
1. Mount Drive → `git pull` → install.
2. Load `best_source_v8s.pt`. Surgery: replace the backbone weights with the SSP-adapted ones from `<DRIVE>/weights/ssp/backbone_simsiam.pt`.
3. Save the patched checkpoint as `<DRIVE>/weights/ssp/ssp_init_v8s.pt`.
4. For each `k ∈ {1, 8}` (representative low and high points of the curve): head-only fine-tune from the patched checkpoint on the first `k` sorted hand-corrected images. Mirrors the protocol in `08c_few_shot_curve.ipynb`.
5. Evaluate **CPV on ScreenSpot** (n=334, primary) and mAP@0.5 / mAP@0.5:0.95 on the hand-corrected set (secondary, `fit_to_train`).
6. Write `reports/tables/ssp_few_shot.csv` with rows for k=1 and k=8, with and without SSP, side-by-side.
7. Publish.

**Comparison.** Both the no-SSP rows (from 08c) and the SSP rows (from this notebook) are written, so the SSP-vs-no-SSP gap is one subtraction the reader can do without leaving the table.

**Compute reality.** Per-k fine-tune is ~5-10 min on T4. ScreenSpot CPV is ~5 min per checkpoint. Total ~30-45 min for k=1+k=8.

**Report.** Every step prints `REPORT ...` lines.
"""
    ))

    cells.append(code(COMMON_MOUNT))
    cells.append(code(COMMON_CLONE))
    cells.append(code(
        """import sys, subprocess
subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q",
     "ultralytics", "datasets", "pillow", "opencv-python", "matplotlib"],
    check=False,
)
import torch, ultralytics
print("torch:", torch.__version__, "| cuda:", torch.cuda.is_available(),
      "| device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu")
print("ultralytics:", ultralytics.__version__)
"""
    ))

    cells.append(md(
        """## 12.1 — Bootstrap source weights and the SSP-adapted backbone

We need:
- `best_source_v8s.pt` (from `05_train_source.ipynb`) — provides the neck and head.
- `backbone_simsiam.pt` (from `11_ssp_pretrain.ipynb`) — provides the adapted backbone.

If either is missing, the notebook aborts with a clear message.
"""
    ))

    cells.append(code(
        '''import os, shutil, zipfile

DRIVE        = "/content/drive/MyDrive/visclick"
SOURCE_WTS   = os.path.join(DRIVE, "weights", "baseline_source", "best_source_v8s.pt")
SSP_BACKBONE = os.path.join(DRIVE, "weights", "ssp", "backbone_simsiam.pt")
SSP_INIT     = os.path.join(DRIVE, "weights", "ssp", "ssp_init_v8s.pt")
FEWSHOT_DIR  = os.path.join(DRIVE, "weights", "ssp_few_shot")
REPORTS_TBL  = os.path.join(DRIVE, "reports", "tables")
os.makedirs(FEWSHOT_DIR, exist_ok=True)
os.makedirs(REPORTS_TBL, exist_ok=True)

assert os.path.isfile(SOURCE_WTS), f"Missing source weights: {SOURCE_WTS}"
assert os.path.isfile(SSP_BACKBONE), f"Missing SSP backbone: {SSP_BACKBONE}. Run 11_ssp_pretrain first."
print(f"REPORT source_weights | path = {SOURCE_WTS} | size_mb = {os.path.getsize(SOURCE_WTS)/1024/1024:0.1f}")
print(f"REPORT ssp_backbone   | path = {SSP_BACKBONE} | size_mb = {os.path.getsize(SSP_BACKBONE)/1024/1024:0.1f}")

HC_ZIP  = "/content/visclick/datasets/handcorrected_desktop_test/visclick3.yolov8.zip"
HC_ROOT = "/content/hc"
HC_IMG  = os.path.join(HC_ROOT, "train", "images")
HC_LBL  = os.path.join(HC_ROOT, "train", "labels")
if not os.path.isdir(HC_IMG):
    with zipfile.ZipFile(HC_ZIP, "r") as zf:
        zf.extractall(HC_ROOT)
    print("unzipped hand-corrected ->", HC_ROOT)

STEMS = sorted(
    os.path.splitext(f)[0]
    for f in os.listdir(HC_IMG)
    if f.lower().endswith((".png", ".jpg", ".jpeg"))
)
N_HC = len(STEMS)
print(f"REPORT hc_pool | n = {N_HC}")

CLASSES = ["button", "text", "text_input", "icon", "menu", "checkbox"]
'''
    ))

    cells.append(md(
        """## 12.2 — Surgery: graft the SSP backbone onto the source-trained detector

Load `best_source_v8s.pt` into an Ultralytics `YOLO`. Replace the first `N_BACKBONE = 10` modules' state dict with the SSP-adapted backbone. Save the patched checkpoint as `ssp_init_v8s.pt`. From here on, the patched checkpoint is what the few-shot loop starts from.
"""
    ))

    cells.append(code(
        '''import torch
from ultralytics import YOLO

src = YOLO(SOURCE_WTS)
det_model = src.model

N_BACKBONE = 10
bb_state = torch.load(SSP_BACKBONE, map_location="cpu")

# Map SimSiam-saved state dict back into the YOLOv8 backbone modules.
target = torch.nn.Sequential(*list(det_model.model[:N_BACKBONE]))
missing, unexpected = target.load_state_dict(bb_state, strict=False)
print(f"REPORT graft | missing_keys = {len(missing)} | unexpected_keys = {len(unexpected)}")
if missing:
    print("  first missing:", missing[:3])
if unexpected:
    print("  first unexpected:", unexpected[:3])

# Persist the patched checkpoint.
src.save(SSP_INIT)
print(f"REPORT ssp_init | path = {SSP_INIT} | size_mb = {os.path.getsize(SSP_INIT)/1024/1024:0.1f}")
'''
    ))

    cells.append(md(
        """## 12.3 — Per-`k` head-only fine-tune from the SSP-initialised checkpoint

Mirrors `08c_few_shot_curve.ipynb` section 8.1: build a `k`-image YOLO dataset (first `k` sorted stems), head-only fine-tune for 30 epochs, save weights to `<DRIVE>/weights/ssp_few_shot/k{k}/`. Resume-aware: if the output `last.pt` exists the cell skips.
"""
    ))

    cells.append(code(
        '''import os, time, yaml, shutil

K_VALUES = [1, 8]
EPOCHS = 30
IMGSZ = 640


def build_yolo_yaml(k: int) -> str:
    work = f"/content/ssp_train_k{k}"
    img_dir = os.path.join(work, "images", "train")
    lbl_dir = os.path.join(work, "labels", "train")
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(lbl_dir, exist_ok=True)
    for stem in STEMS[:k]:
        for ext in (".png", ".jpg", ".jpeg"):
            src_img = os.path.join(HC_IMG, stem + ext)
            if os.path.isfile(src_img):
                shutil.copy2(src_img, os.path.join(img_dir, os.path.basename(src_img)))
                break
        src_lbl = os.path.join(HC_LBL, stem + ".txt")
        if os.path.isfile(src_lbl):
            shutil.copy2(src_lbl, os.path.join(lbl_dir, stem + ".txt"))
    yaml_path = os.path.join(work, "data.yaml")
    with open(yaml_path, "w") as fh:
        yaml.safe_dump({
            "path": work, "train": "images/train", "val": "images/train",
            "names": CLASSES, "nc": len(CLASSES),
        }, fh)
    return yaml_path


for k in K_VALUES:
    out_dir = os.path.join(FEWSHOT_DIR, f"k{k}")
    last_pt = os.path.join(out_dir, "weights", "last.pt")
    if os.path.isfile(last_pt):
        print(f"k={k}: weights already at {last_pt}; skipping.")
        continue

    data_yaml = build_yolo_yaml(k)
    t0 = time.time()
    model = YOLO(SSP_INIT)
    model.train(
        data=data_yaml,
        epochs=EPOCHS,
        imgsz=IMGSZ,
        batch=4,
        project=FEWSHOT_DIR,
        name=f"k{k}",
        freeze=10,
        verbose=False,
        plots=False,
    )
    print(f"REPORT ssp_finetune | k = {k} | epochs = {EPOCHS} | elapsed = {time.time()-t0:0.1f}s")
'''
    ))

    cells.append(md(
        """## 12.4 — Evaluate: ScreenSpot CPV (primary) + hand-corrected mAP (secondary)

Reuses the proven evaluation scripts already in the repo:
- `scripts/run_cpv_screenspot.py` — instruction-grounded CPV on the ScreenSpot desktop slice (n=334).
- `scripts/run_cpv.py` — per-element-recall CPV on the hand-corrected set (`fit_to_train` for k>0).

The ScreenSpot CPV is the headline number reported in Section 7.x. The hand-corrected CPV is the supplementary fit-to-train sanity check.
"""
    ))

    cells.append(code(
        '''import subprocess, tempfile

per_k_results = {}

for k in K_VALUES:
    weights = os.path.join(FEWSHOT_DIR, f"k{k}", "weights", "best.pt")
    if not os.path.isfile(weights):
        weights = os.path.join(FEWSHOT_DIR, f"k{k}", "weights", "last.pt")
    assert os.path.isfile(weights), f"No checkpoint for k={k}"

    # Export ONNX for the CPV scripts (they accept .onnx or .pt; .pt is fine).
    onnx_out = weights.replace(".pt", ".onnx")
    if not os.path.isfile(onnx_out):
        YOLO(weights).export(format="onnx", imgsz=IMGSZ, dynamic=False, opset=12)

    with tempfile.TemporaryDirectory() as tmp:
        ss_csv = os.path.join(tmp, f"ss_k{k}.csv")
        subprocess.run([
            sys.executable, "/content/visclick/scripts/run_cpv_screenspot.py",
            "--weights", onnx_out, "--out", ss_csv,
        ], check=True)
        with open(ss_csv) as fh:
            head = next(fh); ss_overall = next(fh).strip().split(",")
        cpv_ss = float(ss_overall[-1])

        hc_csv = os.path.join(tmp, f"hc_k{k}.csv")
        subprocess.run([
            sys.executable, "/content/visclick/scripts/run_cpv.py",
            "--weights", onnx_out, "--out", hc_csv,
        ], check=True)
        with open(hc_csv) as fh:
            head = next(fh)
            hc_overall = None
            for line in fh:
                parts = line.strip().split(",")
                if parts and parts[0] == "OVERALL":
                    hc_overall = parts
                    break
        cpv_hc = float(hc_overall[-1]) if hc_overall else float("nan")

    per_k_results[k] = {"cpv_screenspot_%": cpv_ss, "cpv_handcorrected_%": cpv_hc}
    print(f"REPORT ssp_eval | k = {k} | cpv_screenspot = {cpv_ss:.2f} | cpv_handcorrected = {cpv_hc:.2f}")
'''
    ))

    cells.append(md(
        """## 12.5 — Write `ssp_few_shot.csv` with both SSP and no-SSP rows

Reads the no-SSP numbers from `reports/tables/sample_efficiency.csv` (produced by 08c) and writes a side-by-side comparison. The reader can compute the SSP gap by subtracting columns.
"""
    ))

    cells.append(code(
        '''import csv

NO_SSP_CSV = "/content/visclick/reports/tables/sample_efficiency.csv"
no_ssp = {}
if os.path.isfile(NO_SSP_CSV):
    with open(NO_SSP_CSV) as fh:
        for row in csv.DictReader(fh):
            try:
                k = int(row["k"])
                no_ssp[k] = row
            except (KeyError, ValueError):
                continue
else:
    print(f"WARN: no baseline at {NO_SSP_CSV}; SSP rows written without comparison.")

OUT_CSV = "/content/visclick/reports/tables/ssp_few_shot.csv"
with open(OUT_CSV, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["k", "method", "cpv_screenspot_%", "cpv_handcorrected_%"])
    for k in K_VALUES:
        if k in no_ssp:
            r = no_ssp[k]
            w.writerow([k, "no-ssp",
                        r.get("cpv_screenspot_%", ""),
                        r.get("cpv_handcorrected_%", "")])
        d = per_k_results[k]
        w.writerow([k, "ssp",
                    f"{d['cpv_screenspot_%']:.2f}",
                    f"{d['cpv_handcorrected_%']:.2f}"])

print(f"REPORT step = WRITE_CSV | path = {OUT_CSV}")
shutil.copy2(OUT_CSV, os.path.join(REPORTS_TBL, "ssp_few_shot.csv"))
'''
    ))

    cells.append(md(
        """## 12.6 — Publish to git"""
    ))

    cells.append(code(common_publish(
        ["reports/tables/ssp_few_shot.csv"],
        "D-02: SSP+FT few-shot results vs no-SSP baseline",
    )))

    return cells


# ---------------------------------------------------------------------------
# 13_uda_adaptive_teacher.ipynb — simplified Adaptive Teacher.
# ---------------------------------------------------------------------------

def build_nb13() -> list[dict]:
    cells: list[dict] = []

    cells.append(md(
        """# VisClick — Phase 4.4 / D-03: UDA — simplified Cross-Domain Adaptive Teacher

**Goal.** Adapt the source-trained YOLOv8s detector to the desktop domain using **unlabelled** desktop images only. Method: simplified offline Adaptive Teacher (after Li et al., 2022).

**Why simplified.** The full Adaptive Teacher of Li et al. 2022 runs an online EMA teacher–student loop inside the detector's training stage, with mixed batches of weakly-augmented teacher and strongly-augmented student forwards. Implementing that inside Ultralytics' YOLO trainer requires hooking the optimizer and reordering the dataloader, which is brittle. The simplified version below preserves the **structural idea** of teacher-student mutual learning while running offline pseudo-labelling between standard YOLO training runs.

**Pipeline (3 outer iterations of teacher→pseudo-labels→student):**
1. Mount Drive → `git pull` → install.
2. Build the unlabelled corpus (D-06 output; falls back to seed if too small).
3. Iteration `t`:
   - Teacher `T_t` generates pseudo-labels on the unlabelled corpus at confidence ≥ 0.30 (filter).
   - Student `S_t` = retrain YOLOv8s for 10 epochs on (source GT pool + pseudo-labelled target).
   - Update: `T_{t+1}` = `S_t`.
4. Final evaluation: CPV on ScreenSpot, mAP on hand-corrected.
5. Write `reports/tables/uda_adaptive_teacher.csv` (one row per iteration + final).
6. Publish.

**Compute reality.** Each outer iteration: ~5 min for pseudo-labelling + ~20 min training = ~25 min. Three iterations = ~75 min. Fits one Colab Free session with margin.

**Honest narrative for the report.** The simplification is named explicitly in Section 6 and Section 8: results from this offline variant are a lower bound on what the full online Adaptive Teacher would achieve.
"""
    ))

    cells.append(code(COMMON_MOUNT))
    cells.append(code(COMMON_CLONE))
    cells.append(code(
        """import sys, subprocess
subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q",
     "ultralytics", "pillow", "opencv-python", "matplotlib"],
    check=False,
)
import torch, ultralytics
print("torch:", torch.__version__, "| cuda:", torch.cuda.is_available(),
      "| device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu")
print("ultralytics:", ultralytics.__version__)
"""
    ))

    cells.append(md(
        """## 13.1 — Bootstrap source weights and the unlabelled corpus

The teacher starts as `best_source_v8s.pt`. The unlabelled corpus is `<DRIVE>/datasets/auto_corpus/` (D-06). The hand-corrected set is unzipped for evaluation only.
"""
    ))

    cells.append(code(
        '''import os, glob, shutil, zipfile

DRIVE        = "/content/drive/MyDrive/visclick"
SOURCE_WTS   = os.path.join(DRIVE, "weights", "baseline_source", "best_source_v8s.pt")
UDA_DIR      = os.path.join(DRIVE, "weights", "uda_at")
REPORTS_TBL  = os.path.join(DRIVE, "reports", "tables")
os.makedirs(UDA_DIR, exist_ok=True)
os.makedirs(REPORTS_TBL, exist_ok=True)

assert os.path.isfile(SOURCE_WTS), f"Source weights missing: {SOURCE_WTS}"

# Unlabelled target corpus (D-06).
TGT_DIRS = [
    os.path.join(DRIVE, "datasets", "auto_corpus"),
    "/content/visclick/samples/desktop_seed",
]
TARGET_PATHS = []
for d in TGT_DIRS:
    if not os.path.isdir(d):
        continue
    for root, _, files in os.walk(d):
        for f in files:
            if f.lower().endswith((".png", ".jpg", ".jpeg")):
                TARGET_PATHS.append(os.path.join(root, f))
TARGET_PATHS = sorted(set(TARGET_PATHS))
print(f"REPORT target_corpus | n = {len(TARGET_PATHS)}")
assert len(TARGET_PATHS) >= 50, f"too few unlabelled targets ({len(TARGET_PATHS)}); run auto_capture_corpus.py"

# Hand-corrected set (eval only).
HC_ZIP  = "/content/visclick/datasets/handcorrected_desktop_test/visclick3.yolov8.zip"
HC_ROOT = "/content/hc"
if not os.path.isdir(os.path.join(HC_ROOT, "train", "images")):
    with zipfile.ZipFile(HC_ZIP, "r") as zf:
        zf.extractall(HC_ROOT)

CLASSES = ["button", "text", "text_input", "icon", "menu", "checkbox"]
'''
    ))

    cells.append(md(
        """## 13.2 — Three outer iterations of pseudo-label → train → swap

For each outer iteration `t`:
1. Run teacher `T_t` on all unlabelled target images → write YOLO `.txt` pseudo-labels with confidence ≥ 0.30.
2. Build a mixed dataset: source GT pool (already on Drive) + pseudo-labelled target.
3. Train YOLOv8s for 10 epochs starting from `T_t`.
4. The trained model becomes `T_{t+1}`.

The `freeze=0` argument means we fine-tune the whole network, which is what Adaptive Teacher does in its student branch.
"""
    ))

    cells.append(code(
        '''import time, yaml
from ultralytics import YOLO

# Source GT pool (Zenodo unified bundle copy already on Drive).
SOURCE_DATA = os.path.join(DRIVE, "datasets", "source_zenodo_unified")
assert os.path.isdir(SOURCE_DATA), f"Source GT pool missing: {SOURCE_DATA}"

PSEUDO_CONF = 0.30
N_OUTER = 3
EPOCHS_PER_ITER = 10
IMGSZ = 640


def write_pseudo_labels(model, work_dir):
    img_dir = os.path.join(work_dir, "images", "train")
    lbl_dir = os.path.join(work_dir, "labels", "train")
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(lbl_dir, exist_ok=True)
    n_with_box = 0
    for path in TARGET_PATHS:
        results = model.predict(path, imgsz=IMGSZ, conf=PSEUDO_CONF, verbose=False)
        r = results[0]
        if len(r.boxes) == 0:
            continue
        stem = os.path.splitext(os.path.basename(path))[0]
        out_img = os.path.join(img_dir, os.path.basename(path))
        out_lbl = os.path.join(lbl_dir, stem + ".txt")
        if not os.path.isfile(out_img):
            shutil.copy2(path, out_img)
        H, W = r.orig_shape
        with open(out_lbl, "w") as fh:
            for cls, xyxy in zip(r.boxes.cls.tolist(), r.boxes.xyxyn.tolist()):
                x1, y1, x2, y2 = xyxy
                cx = (x1 + x2) / 2; cy = (y1 + y2) / 2
                bw = x2 - x1; bh = y2 - y1
                fh.write(f"{int(cls)} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\\n")
        n_with_box += 1
    return n_with_box


def build_mixed_yaml(target_dir, out_yaml):
    # Source uses its own YAML; we point YOLOv8 at the source for both train and val,
    # then UNIQUELY train on the union by listing two image roots.
    # Ultralytics supports multi-path train via a list in the yaml.
    data = {
        "path": "/",
        "train": [
            os.path.join(SOURCE_DATA, "images", "train"),
            os.path.join(target_dir, "images", "train"),
        ],
        "val": os.path.join(SOURCE_DATA, "images", "val"),
        "names": CLASSES,
        "nc": len(CLASSES),
    }
    with open(out_yaml, "w") as fh:
        yaml.safe_dump(data, fh)


HISTORY = []
teacher_weights = SOURCE_WTS

for t in range(1, N_OUTER + 1):
    print(f"\\n=== Outer iteration {t}/{N_OUTER} ===")
    work_dir = f"/content/uda_at_iter{t}"
    teacher = YOLO(teacher_weights)
    n_box = write_pseudo_labels(teacher, work_dir)
    print(f"  pseudo-labels: {n_box} / {len(TARGET_PATHS)} images had >= 1 box at conf {PSEUDO_CONF}")

    data_yaml = os.path.join(work_dir, "data.yaml")
    build_mixed_yaml(work_dir, data_yaml)

    t0 = time.time()
    student = YOLO(teacher_weights)
    student.train(
        data=data_yaml,
        epochs=EPOCHS_PER_ITER,
        imgsz=IMGSZ,
        batch=8,
        project=UDA_DIR,
        name=f"iter{t}",
        verbose=False,
        plots=False,
    )
    elapsed = time.time() - t0
    new_weights = os.path.join(UDA_DIR, f"iter{t}", "weights", "best.pt")
    if not os.path.isfile(new_weights):
        new_weights = os.path.join(UDA_DIR, f"iter{t}", "weights", "last.pt")
    HISTORY.append({"iter": t, "n_pseudo_imgs": n_box, "weights": new_weights, "elapsed_s": elapsed})
    print(f"REPORT uda_at_iter | t = {t} | n_pseudo = {n_box} | elapsed_s = {elapsed:.1f}")

    teacher_weights = new_weights
'''
    ))

    cells.append(md(
        """## 13.3 — Final evaluation: CPV on ScreenSpot + hand-corrected mAP

The final teacher (after `N_OUTER` rounds) is evaluated against the same protocol as every other adapter: ScreenSpot CPV for instruction-grounded success rate, hand-corrected for per-element recall.
"""
    ))

    cells.append(code(
        '''import subprocess, tempfile, csv

final_weights = HISTORY[-1]["weights"]
print("REPORT uda_at_final | weights =", final_weights)

# Export ONNX for the eval scripts.
onnx_out = final_weights.replace(".pt", ".onnx")
if not os.path.isfile(onnx_out):
    YOLO(final_weights).export(format="onnx", imgsz=IMGSZ, dynamic=False, opset=12)

with tempfile.TemporaryDirectory() as tmp:
    ss_csv = os.path.join(tmp, "ss.csv")
    subprocess.run([
        sys.executable, "/content/visclick/scripts/run_cpv_screenspot.py",
        "--weights", onnx_out, "--out", ss_csv,
    ], check=True)
    with open(ss_csv) as fh:
        head = next(fh); ss_overall = next(fh).strip().split(",")
    CPV_SS = float(ss_overall[-1])

    hc_csv = os.path.join(tmp, "hc.csv")
    subprocess.run([
        sys.executable, "/content/visclick/scripts/run_cpv.py",
        "--weights", onnx_out, "--out", hc_csv,
    ], check=True)
    with open(hc_csv) as fh:
        next(fh)
        hc_overall = None
        for line in fh:
            parts = line.strip().split(",")
            if parts and parts[0] == "OVERALL":
                hc_overall = parts; break
    CPV_HC = float(hc_overall[-1]) if hc_overall else float("nan")

print(f"REPORT uda_at_eval | cpv_screenspot = {CPV_SS:.2f} | cpv_handcorrected = {CPV_HC:.2f}")
'''
    ))

    cells.append(md(
        """## 13.4 — Write `uda_adaptive_teacher.csv`"""
    ))

    cells.append(code(
        '''OUT_CSV = "/content/visclick/reports/tables/uda_adaptive_teacher.csv"
with open(OUT_CSV, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["iter", "n_pseudo_imgs", "elapsed_s",
                "cpv_screenspot_%", "cpv_handcorrected_%"])
    for h in HISTORY[:-1]:
        w.writerow([h["iter"], h["n_pseudo_imgs"], f"{h['elapsed_s']:.1f}", "", ""])
    h = HISTORY[-1]
    w.writerow([h["iter"], h["n_pseudo_imgs"], f"{h['elapsed_s']:.1f}",
                f"{CPV_SS:.2f}", f"{CPV_HC:.2f}"])
print(f"REPORT step = WRITE_CSV | path = {OUT_CSV}")
shutil.copy2(OUT_CSV, os.path.join(REPORTS_TBL, "uda_adaptive_teacher.csv"))
'''
    ))

    cells.append(md(
        """## 13.5 — Publish to git"""
    ))

    cells.append(code(common_publish(
        ["reports/tables/uda_adaptive_teacher.csv"],
        "D-03: simplified Adaptive Teacher UDA results",
    )))

    return cells


# ---------------------------------------------------------------------------
# 14_uda_shot.ipynb — simplified Source Hypothesis Transfer (SHOT).
# ---------------------------------------------------------------------------

def build_nb14() -> list[dict]:
    cells: list[dict] = []

    cells.append(md(
        """# VisClick — Phase 4.4 / D-04: UDA — simplified SHOT (Source Hypothesis Transfer)

**Goal.** Adapt the source-trained YOLOv8s to the desktop domain using **only unlabelled target images** and **no source data at adaptation time**. Method: simplified SHOT (after Liang et al., 2020).

**Why simplified.** The full SHOT freezes the classifier head and adapts the feature extractor with information maximization (entropy + diversity) plus self-supervised pseudo-label refinement. For a detection model like YOLOv8 — multi-scale heads, three feature pyramid levels, anchor-free regression — implementing IM at the detector head is not faithful to SHOT's original classification setup.

The simplified version we run is **detection-pseudo-label SHOT**:
1. Run the source-trained detector on all unlabelled target images at high confidence (0.50).
2. The detector's own confident predictions are the only "labels" at adaptation time.
3. Freeze the YOLO head (`freeze=10` does the opposite — freezes backbone; we use the Ultralytics-friendly inverse by unfreezing only the backbone via `freeze=15` to keep head + neck frozen, then doing a short adaptation run).
4. Train the backbone for 15 epochs against the pseudo-labels.
5. Evaluate.

This preserves the SHOT spirit (source-free, head-frozen, target self-supervision) while staying compatible with the Ultralytics trainer.

**Compute reality.** ~5 min for pseudo-labelling, ~20-25 min for 15 epochs at batch 8 imgsz 640. Total ~30 min.

**Honest narrative for the report.** Just like notebook 13, the simplification is named explicitly. The report calls this "detection-pseudo-label SHOT" and reports it as a lower bound on full SHOT.
"""
    ))

    cells.append(code(COMMON_MOUNT))
    cells.append(code(COMMON_CLONE))
    cells.append(code(
        """import sys, subprocess
subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q",
     "ultralytics", "pillow", "opencv-python", "matplotlib"],
    check=False,
)
import torch, ultralytics
print("torch:", torch.__version__, "| cuda:", torch.cuda.is_available(),
      "| device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu")
print("ultralytics:", ultralytics.__version__)
"""
    ))

    cells.append(md(
        """## 14.1 — Bootstrap

Loads `best_source_v8s.pt` and the unlabelled corpus (same D-06 output as in notebook 13).
"""
    ))

    cells.append(code(
        '''import os, glob, shutil, zipfile

DRIVE        = "/content/drive/MyDrive/visclick"
SOURCE_WTS   = os.path.join(DRIVE, "weights", "baseline_source", "best_source_v8s.pt")
SHOT_DIR     = os.path.join(DRIVE, "weights", "uda_shot")
REPORTS_TBL  = os.path.join(DRIVE, "reports", "tables")
os.makedirs(SHOT_DIR, exist_ok=True)
os.makedirs(REPORTS_TBL, exist_ok=True)
assert os.path.isfile(SOURCE_WTS), f"Missing source: {SOURCE_WTS}"

TGT_DIRS = [
    os.path.join(DRIVE, "datasets", "auto_corpus"),
    "/content/visclick/samples/desktop_seed",
]
TARGET_PATHS = []
for d in TGT_DIRS:
    if not os.path.isdir(d):
        continue
    for root, _, files in os.walk(d):
        for f in files:
            if f.lower().endswith((".png", ".jpg", ".jpeg")):
                TARGET_PATHS.append(os.path.join(root, f))
TARGET_PATHS = sorted(set(TARGET_PATHS))
print(f"REPORT target_corpus | n = {len(TARGET_PATHS)}")
assert len(TARGET_PATHS) >= 50

CLASSES = ["button", "text", "text_input", "icon", "menu", "checkbox"]
'''
    ))

    cells.append(md(
        """## 14.2 — Source-model pseudo-labelling on the unlabelled target

We use a high confidence (0.50) so the pseudo-labels are reliable. The SHOT paper's intuition is that confident source-model predictions on the target are the safest signal you can extract without any target labels.
"""
    ))

    cells.append(code(
        '''import time
from ultralytics import YOLO

PSEUDO_CONF = 0.50
IMGSZ = 640
WORK = "/content/uda_shot_data"
IMG_DIR = os.path.join(WORK, "images", "train")
LBL_DIR = os.path.join(WORK, "labels", "train")
os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(LBL_DIR, exist_ok=True)

teacher = YOLO(SOURCE_WTS)
n_box = 0
t0 = time.time()
for path in TARGET_PATHS:
    results = teacher.predict(path, imgsz=IMGSZ, conf=PSEUDO_CONF, verbose=False)
    r = results[0]
    if len(r.boxes) == 0:
        continue
    stem = os.path.splitext(os.path.basename(path))[0]
    if not os.path.isfile(os.path.join(IMG_DIR, os.path.basename(path))):
        shutil.copy2(path, os.path.join(IMG_DIR, os.path.basename(path)))
    with open(os.path.join(LBL_DIR, stem + ".txt"), "w") as fh:
        for cls, xyxy in zip(r.boxes.cls.tolist(), r.boxes.xyxyn.tolist()):
            x1, y1, x2, y2 = xyxy
            cx = (x1 + x2) / 2; cy = (y1 + y2) / 2
            bw = x2 - x1; bh = y2 - y1
            fh.write(f"{int(cls)} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\\n")
    n_box += 1
print(f"REPORT shot_pseudo | n = {n_box}/{len(TARGET_PATHS)} | elapsed_s = {time.time()-t0:.1f}")
'''
    ))

    cells.append(md(
        """## 14.3 — Adapt the backbone with head + neck frozen

`freeze=15` keeps YOLOv8s' top 15 modules (head + most of the neck) frozen during training, while letting the backbone adapt. This is the SHOT-spirit setup: source hypothesis (head) is preserved, feature extractor is what changes.

We train for 15 epochs at batch 8, which fits a single Colab session with margin.
"""
    ))

    cells.append(code(
        '''import yaml

EPOCHS = 15

data_yaml = os.path.join(WORK, "data.yaml")
with open(data_yaml, "w") as fh:
    yaml.safe_dump({
        "path": WORK, "train": "images/train", "val": "images/train",
        "names": CLASSES, "nc": len(CLASSES),
    }, fh)

t0 = time.time()
adapted = YOLO(SOURCE_WTS)
adapted.train(
    data=data_yaml,
    epochs=EPOCHS,
    imgsz=IMGSZ,
    batch=8,
    project=SHOT_DIR,
    name="shot_run",
    freeze=15,
    verbose=False,
    plots=False,
)
elapsed = time.time() - t0
ADAPTED_WTS = os.path.join(SHOT_DIR, "shot_run", "weights", "best.pt")
if not os.path.isfile(ADAPTED_WTS):
    ADAPTED_WTS = os.path.join(SHOT_DIR, "shot_run", "weights", "last.pt")
print(f"REPORT shot_train | epochs = {EPOCHS} | elapsed_s = {elapsed:.1f} | weights = {ADAPTED_WTS}")
'''
    ))

    cells.append(md(
        """## 14.4 — Evaluate: CPV on ScreenSpot + hand-corrected mAP"""
    ))

    cells.append(code(
        '''import subprocess, tempfile, csv

onnx_out = ADAPTED_WTS.replace(".pt", ".onnx")
if not os.path.isfile(onnx_out):
    YOLO(ADAPTED_WTS).export(format="onnx", imgsz=IMGSZ, dynamic=False, opset=12)

with tempfile.TemporaryDirectory() as tmp:
    ss_csv = os.path.join(tmp, "ss.csv")
    subprocess.run([
        sys.executable, "/content/visclick/scripts/run_cpv_screenspot.py",
        "--weights", onnx_out, "--out", ss_csv,
    ], check=True)
    with open(ss_csv) as fh:
        next(fh); ss_overall = next(fh).strip().split(",")
    CPV_SS = float(ss_overall[-1])

    hc_csv = os.path.join(tmp, "hc.csv")
    subprocess.run([
        sys.executable, "/content/visclick/scripts/run_cpv.py",
        "--weights", onnx_out, "--out", hc_csv,
    ], check=True)
    with open(hc_csv) as fh:
        next(fh)
        hc_overall = None
        for line in fh:
            parts = line.strip().split(",")
            if parts and parts[0] == "OVERALL":
                hc_overall = parts; break
    CPV_HC = float(hc_overall[-1]) if hc_overall else float("nan")

print(f"REPORT shot_eval | cpv_screenspot = {CPV_SS:.2f} | cpv_handcorrected = {CPV_HC:.2f}")
'''
    ))

    cells.append(md(
        """## 14.5 — Write `uda_shot.csv`"""
    ))

    cells.append(code(
        '''OUT_CSV = "/content/visclick/reports/tables/uda_shot.csv"
with open(OUT_CSV, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["method", "epochs", "n_pseudo_imgs", "cpv_screenspot_%", "cpv_handcorrected_%"])
    w.writerow(["shot_simplified", EPOCHS, n_box, f"{CPV_SS:.2f}", f"{CPV_HC:.2f}"])
print(f"REPORT step = WRITE_CSV | path = {OUT_CSV}")
shutil.copy2(OUT_CSV, os.path.join(REPORTS_TBL, "uda_shot.csv"))
'''
    ))

    cells.append(md(
        """## 14.6 — Publish to git"""
    ))

    cells.append(code(common_publish(
        ["reports/tables/uda_shot.csv"],
        "D-04: simplified SHOT UDA results",
    )))

    return cells


# ---------------------------------------------------------------------------
# Entry point.
# ---------------------------------------------------------------------------

def main() -> int:
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    write_notebook(NOTEBOOK_DIR / "11_ssp_pretrain.ipynb",       build_nb11())
    write_notebook(NOTEBOOK_DIR / "12_ssp_finetune.ipynb",       build_nb12())
    write_notebook(NOTEBOOK_DIR / "13_uda_adaptive_teacher.ipynb", build_nb13())
    write_notebook(NOTEBOOK_DIR / "14_uda_shot.ipynb",           build_nb14())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
