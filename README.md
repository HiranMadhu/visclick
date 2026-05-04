# VisClick

Vision-based GUI element detection and click automation for desktop applications using transfer learning (YOLOv8, mobile/web pre-training, Windows desktop fine-tune).

- **This repo** = code, configs, one Colab notebook at a time (phased; see below).
- **Google Drive** `visclick` = datasets and trained weights (large files — not in git).
- **Colab** = GPU; **Windows** = click-bot demo.

**Master plan (all phases):** use `VisClick_Detailed_Plan.md` in your project `gui_temp/` folder next to this repo (or open a local copy). We execute **one phase per step** in Colab, not everything at once.

## Where you are (checklist)

| Step | Status | What |
|------|--------|------|
| 0 | done | GitHub repo, Drive folder `visclick`, Colab GPU |
| 1 | done | `01_pull_and_data.ipynb` — CLAY + UI-Vision |
| 2 | done | `02_rico_zenodo_vins.ipynb` — RICO, Zenodo unified, VINS |
| 3 | done | `03_eda.ipynb` — EDA |
| 4 | done | `04_assemble_source.ipynb` — `source_train` assembly |
| 5 | done | `05_train_source.ipynb` — YOLOv8s source training |
| 6 | done | `06_finetune_desktop.ipynb` — desktop fine-tune (auto-labelled, head-only) |
| **7** | **current** | `07_export_onnx.ipynb` — export `best_desktop_v8s.pt` → `.onnx` |
| 8 | later | Windows prototype: capture → detect → OCR → match → click |

## Colab notebooks (run in order; each starts fresh: mount + `git pull`)

| Step | Open in Colab |
|------|---------------|
| 1 — CLAY + UI-Vision | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HiranMadhu/visclick/blob/main/notebooks/01_pull_and_data.ipynb) |
| 2 — RICO, Zenodo unified, VINS | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HiranMadhu/visclick/blob/main/notebooks/02_rico_zenodo_vins.ipynb) |
| 3 — EDA | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HiranMadhu/visclick/blob/main/notebooks/03_eda.ipynb) |
| 4 — assemble source_train | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HiranMadhu/visclick/blob/main/notebooks/04_assemble_source.ipynb) |
| 5 — train source YOLOv8s | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HiranMadhu/visclick/blob/main/notebooks/05_train_source.ipynb) |
| 6 — desktop fine-tune | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HiranMadhu/visclick/blob/main/notebooks/06_finetune_desktop.ipynb) |
| 7 — export ONNX | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HiranMadhu/visclick/blob/main/notebooks/07_export_onnx.ipynb) |

**Outputs for the project report:** each notebook includes **`REPORT ...` lines** (and a final digest). Copy those into **`VisClick_Report_Data_Form.md` §0** in `gui_temp/`, or paste the block in chat to have it filled in.

**01** does: mount → clone / pull → subfolders → **CLAY** + **UI-Vision** → **C.2.1 RICO** (`wget -c` optional for official `unique_uis.tar.gz`, then `tar` extract; or upload that archive / legacy zip) → REPORT cell.

**02** does: same bootstrap → **RICO** only if not already extracted in 01 → **Zenodo** (`train.zip` / `val.zip` / `test.zip` from record 19195885) → **VINS** clone → full REPORT. Drive holds the data; a new Colab session is fine.

**Config helper (later, when training):** `python scripts/patch_colab_configs.py` with `VISCLICK_DRIVE=/content/drive/MyDrive/visclick` fills `configs/yolo_*_colab.yaml` from the templates in `configs/`.

## Local setup (Windows, click-bot)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
# Tesseract: install from https://github.com/UB-Mannheim/tesseract/wiki  (default path is fine)
git pull   # picks up weights/visclick.onnx committed by notebook 07
```

### Daily use — the GUI

```bash
python -m visclick
```

Opens a window with: instruction text box, countdown spinbox, monitor selector, dry-run toggle, weights browser, and a log panel. Workflow: type the instruction (e.g. `click Save`) → press **Run** → countdown → window minimises → screenshot taken → element clicked → window restores with the result in the log.

### Headless / scripting — the CLI

```bash
# 5-second countdown (give yourself time to switch windows):
python -m visclick.bot --instruction "click Save" --countdown 5
# Immediate (when you're already on the target window):
python -m visclick.bot --instruction "click Save"
# Dry-run on a saved screenshot (no click), with overlay output:
python -m visclick.bot --instruction "click Save" --image screenshots/test.png \
    --dry-run --save-overlay screenshots/overlay.png
```

### One-time verification on a new machine (skip if the GUI already works)

Three diagnostic scripts isolate each pipeline layer so a failure points at one place. You only need them if something feels off — the GUI/CLI run end-to-end on its own.

```bash
python scripts/test_screen.py                  # capture: prints res, monitor layout
python scripts/test_screen.py --list-monitors  # multi-monitor: see indices
python scripts/test_click.py 500 400 --no-click  # click plumbing: move-only
python scripts/test_detector.py screenshots/test_screen.png --bench 50  # ONNX: latency
```

The `test_detector.py --bench 50` rows feed §4.1 / §10.1 of the dissertation report.

## Layout

| Path | Purpose |
|------|---------|
| `src/visclick/` | Library: capture, detect, OCR, match, act, bot |
| `notebooks/` | `01_pull_and_data.ipynb`, `02_rico_zenodo_vins.ipynb` (more phases as we go) |
| `configs/` | YOLO templates (`<DRIVE>` placeholders); use `patch_colab_configs.py` in Colab |
| `scripts/` | `patch_colab_configs.py`, `capture_screenshots.py` (Windows), `annotate_export_to_yolo.py`, `run_eval.py` |
| `tests/` | Unit tests |
| `reports/` | `literature_table.csv` + `figures/`, `tables/` for the report |

## Push to personal GitHub

See `scripts/push_personal.sh` and Git credential notes from your earlier setup.

## License

Add a `LICENSE` when you are ready; default is all-rights reserved.
