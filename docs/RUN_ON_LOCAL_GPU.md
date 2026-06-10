# Running SSP pretraining (D-02) on a local GPU box

This document is a step-by-step runbook for executing `scripts/run_ssp_local.py`
on `us01odc-sc4-1-gpu064` (or any Linux + NVIDIA GPU machine). It bypasses
Colab/Drive entirely.

## 0. SSH in and sanity-check

```bash
ssh us01odc-sc4-1-gpu064
hostname
nvidia-smi -L                  # confirm GPU(s) visible
python3 --version              # need 3.10 or newer
which git
df -h ~                        # need ~20 GB free for env + data + checkpoints
```

If `nvidia-smi -L` returns nothing the box has no usable GPU; bail and try
a different host.

## 1. Locate the inputs (don't assume)

Two things need to be on this machine's filesystem before training:

1. **The Zenodo unified bundle** — ~9k images organised as
   `unified/{train,val,test}/images/*.{png,jpg}`. This is what
   `04_assemble_source.ipynb` consumed.
2. **Source training metadata** — `source_train_bundles/{train,val,test}.tar.gz`
   produced by `04_assemble_source.ipynb`. These are tiny (1-2 MB each).
3. **Source-trained YOLOv8s weights** —
   `weights/baseline_source/best_source_v8s.pt`. Produced by
   `05_train_source.ipynb`.
4. **(Optional) 50 desktop seeds** — `samples/desktop_seed/*.png`. These
   ship with the repo.

Check shared filesystems before copying anything:

```bash
# Common shared mount points; adjust to your site:
ls /proj/visclick 2>/dev/null
ls /shared/datasets/visclick 2>/dev/null
ls /scratch/$USER/visclick 2>/dev/null
find /remote -maxdepth 5 -name "unified" -type d 2>/dev/null | head -5
find /remote -maxdepth 5 -name "source_train_bundles" -type d 2>/dev/null | head -5
```

If you find the bundle on a shared FS, skip Step 2. Otherwise rsync from
wherever you have it (Windows desktop, another Linux box, or Google Drive
via `rclone`).

## 2. Stage data into a working dir (if not already shared)

Pick a path with at least 15 GB free:

```bash
export VISCLICK_DATA=/scratch/$USER/visclick_data    # or wherever
mkdir -p "$VISCLICK_DATA"
```

### 2a. From Google Drive via `rclone`

If your unified bundle is on Drive (the Colab setup), set up `rclone`
once on this box (see `https://rclone.org/drive/`), then:

```bash
# Replace `gdrive` with whatever you named the remote in rclone config.
rclone copy gdrive:visclick/data/unified                 "$VISCLICK_DATA/unified"               --progress --transfers 8
rclone copy gdrive:visclick/data/source_train_bundles    "$VISCLICK_DATA/source_train_bundles"  --progress
rclone copy gdrive:visclick/weights/baseline_source      "$VISCLICK_DATA/weights/baseline_source" --progress
```

Note: the `unified/` directory is large (~5-10 GB). Expect 10-30 min on a
reasonable link.

### 2b. From another Linux box you control

```bash
rsync -avh --info=progress2 \
    other-host:/path/to/visclick/data/unified                "$VISCLICK_DATA/"
rsync -avh \
    other-host:/path/to/visclick/data/source_train_bundles   "$VISCLICK_DATA/"
rsync -avh \
    other-host:/path/to/visclick/weights/baseline_source     "$VISCLICK_DATA/weights/"
```

### 2c. Verify the layout

```bash
tree -L 3 "$VISCLICK_DATA"   # should look like:
# $VISCLICK_DATA/
#   unified/
#     train/images/*.png  (a lot)
#     val/images/*.png
#     test/images/*.png
#   source_train_bundles/
#     train.tar.gz
#     val.tar.gz
#     test.tar.gz
#   weights/baseline_source/best_source_v8s.pt
```

Quick file counts:

```bash
for sp in train val test; do
    echo -n "$sp images: "
    find "$VISCLICK_DATA/unified/$sp/images" -maxdepth 1 -type f 2>/dev/null | wc -l
done
```

You want ~6000 / 1600 / 2000 (train / val / test) for the standard
unified bundle. Anything else and notebook 04 wasn't run in standard config.

## 3. Clone visclick and pull latest

```bash
mkdir -p ~/code && cd ~/code
git clone https://github.com/HiranMadhu/visclick.git
cd visclick
git pull --rebase origin main
git rev-parse --short HEAD          # should be 6de93e1 or newer
```

If you already have a checkout, just `git pull --rebase` inside it.

## 4. Create a Python env

We need PyTorch with CUDA, ultralytics, and a couple of small deps. The
simplest setup is a venv:

```bash
cd ~/code/visclick
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip

# PyTorch with CUDA 12.1 wheels. Pick the right index for your driver:
#   - CUDA 12.1 driver -> cu121
#   - CUDA 11.8 driver -> cu118
# Check `nvidia-smi` top-right for the runtime CUDA version.
pip install torch==2.3.* torchvision==0.18.* --index-url https://download.pytorch.org/whl/cu121

# VisClick deps
pip install ultralytics pillow opencv-python matplotlib pi-heif
```

Sanity-check CUDA wiring:

```bash
python - <<'PY'
import torch
print("torch:", torch.__version__, "cuda:", torch.cuda.is_available(),
      "device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu")
PY
```

Expected: `cuda: True` and a real GPU name. If `cuda: False`, the wheel
doesn't match the driver — reinstall with the right `--index-url`.

## 5. Run training

```bash
cd ~/code/visclick
source .venv/bin/activate
export VISCLICK_DATA=/scratch/$USER/visclick_data    # same value as in step 2

# Smoke test first: cap corpus, single epoch.
python scripts/run_ssp_local.py --epochs 1 --max-corpus 200

# Real run: 10 epochs, full corpus, resume if interrupted.
python scripts/run_ssp_local.py
```

Optional flags:

- `--force-fresh` — discard prior checkpoint and start from epoch 0.
- `--epochs N` — override the default 10.
- `--batch N` — default 64; drop to 32 if you hit OOM.
- `--img-size N` — default 224; 160 if you want a faster CPU/old-GPU run.
- `--workers N` — DataLoader workers, default 4.
- `--max-corpus N` — cap corpus for smoke tests.

### What you'll see

```
data_root  = /scratch/.../visclick_data
epochs     = 10
batch      = 64
img_size   = 224
device     = cuda (NVIDIA A100 ...)

--- corpus ---
  train: 7720 paths
  val:   1463 paths
  test:    50 paths
REPORT corpus | size = 9283 | head = [...]
REPORT loader | batch = 64 | steps_per_epoch = 145

--- backbone ---
REPORT backbone | modules = 10 | feat = (1, 512, 7, 7) | channels = 512
REPORT simsiam | params = 12,xxx,xxx

--- training 10 epoch(s) ---
epoch 01/10 | loss = -0.4321 | lr = 0.01250 |  62.4s
epoch 02/10 | loss = -0.5198 | lr = 0.01218 |  61.8s
...
epoch 10/10 | loss = -0.7912 | lr = 0.00000 |  61.5s

REPORT backbone_out | path = .../weights/ssp/backbone_simsiam.pt | size_mb = 21.4
REPORT step = SSP_TRAIN | status = done
```

Expect ~10-25 minutes total on a modern NVIDIA GPU.

## 6. Get the outputs back

Three files land in `$VISCLICK_DATA/weights/ssp/`:

| File | Purpose | Size |
|---|---|---|
| `backbone_simsiam.pt` | SSP-adapted backbone state dict (input to nb 12) | ~20 MB |
| `ssp_ckpt.pt` | Full resume checkpoint | ~50 MB |
| `ssp_loss_log.csv` | Per-epoch loss curve (used in report Figure) | < 1 KB |

Copy the loss log into the repo so it gets committed:

```bash
mkdir -p ~/code/visclick/reports/tables
cp "$VISCLICK_DATA/weights/ssp/ssp_loss_log.csv" \
   ~/code/visclick/reports/tables/ssp_loss_log.csv

cd ~/code/visclick
git add reports/tables/ssp_loss_log.csv
git commit -m "D-02: SimSiam SSP pretrain loss log (gpu064 run)"
git push https://HiranMadhu:<YOUR_TOKEN>@github.com/HiranMadhu/visclick.git main
```

The adapted backbone weights (`backbone_simsiam.pt`) are too large for git
but you'll need them for D-02 step 2 (`12_ssp_finetune.ipynb`). Push them
to your Drive (so the Colab notebook can find them) or transfer to
whichever machine runs notebook 12:

```bash
rclone copy "$VISCLICK_DATA/weights/ssp/backbone_simsiam.pt" \
            gdrive:visclick/weights/ssp/
```

## 7. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `cuda: False` in step 4 | Wrong wheel for your driver | Reinstall torch with correct `--index-url` |
| `Corpus too small (50)` | `unified/` not staged or wrong path | Re-check step 2c, ensure `$VISCLICK_DATA/unified/<split>/images/` has files |
| `Source weights missing` | `best_source_v8s.pt` not staged | Copy `weights/baseline_source/best_source_v8s.pt` from Drive |
| OOM during training | GPU memory too small for batch 64 | `--batch 32 --workers 2` |
| Hangs at "starting epoch 1" | DataLoader stuck on slow shared FS | `--workers 0` to read in-process |
| `pi-heif` AutoUpdate noise | Ultralytics 8.3+ pre-flight | Already installed in step 4; ignore |

## 8. Next experiments on the same machine

Once SSP is done you can keep using this box for D-03 / D-04 (UDA). The
two UDA notebooks (`13_uda_adaptive_teacher.ipynb`, `14_uda_shot.ipynb`)
still need to be converted to standalone scripts the way notebook 11 was;
ping me when you're ready and I'll write `run_uda_adaptive_teacher_local.py`
and `run_uda_shot_local.py` using the same pattern.
