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
| 7 | done | `07_export_onnx.ipynb` — export `best_desktop_v8s.pt` → `.onnx` |
| 8 | done | Windows prototype: capture → detect → OCR → match → click |
| 9 | done | Phase 1.A — hand-corrected 8-image desktop test set (`08_phase1A_handlabel.ipynb`) |
| 10 | done | Phase 1.B — ML ablations M0/M1/M2/M3 on hand-corrected GT (`08_phase1B_ablations.ipynb`); see `reports/tables/transfer_experiments.csv` |
| **11** | **current** | Phase 1.C — classical baselines: `scripts/baseline_template.py`, `scripts/baseline_ocr_only.py`, `scripts/baseline_pywinauto.py`, runner `scripts/run_baselines.py` |

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
# OCR: EasyOCR is included in pip install -e . (default engine).
#      Tesseract is OPTIONAL — install only if you want the ~5 ms/box speed boost
#      from https://github.com/UB-Mannheim/tesseract/wiki  (default install path
#      is auto-detected; otherwise set TESSERACT_CMD env var).
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

### Phase 1.C — classical baselines (Windows)

Compare VisClick against three non-ML approaches on the same `T01..T20` task list (`tasks/T01_T20.json`):

```bash
pip install ".[windows]"      # adds pywinauto for the accessibility-tree baseline

py -3 scripts/run_baselines.py                # interactive — captures screenshots and asks per-task verdicts
py -3 scripts/run_baselines.py --auto          # offline — re-uses existing samples/test_screenshots/<id>.png
py -3 scripts/run_baselines.py --only T01,T02  # subset
py -3 scripts/run_baselines.py --skip-pywinauto  # skip if pywinauto unavailable
```

Each task captures one screenshot, runs **template / ocr_only / pywinauto** on it, saves an annotated overlay to `reports/figures/baselines/<id>.png`, and appends rows to `reports/tables/baseline_results.csv`. Per-baseline overlays let you confirm visually whether the predicted (x, y) lands on the correct control. To make the template baseline work you need to capture reference PNGs once — see `samples/templates/README.md`.

Each baseline can also be invoked standalone:

```bash
py -3 scripts/baseline_ocr_only.py   --instruction "click Save" --image samples/test_screenshots/T01.png
py -3 scripts/baseline_template.py   --instruction "click Save" --target-template Save.png --image samples/test_screenshots/T01.png
py -3 scripts/baseline_pywinauto.py  --instruction "click Save" --target-uia-name Save --target-uia-role Button
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
| `scripts/` | data utilities (`capture_screenshots.py`, `annotate_export_to_yolo.py`, `run_eval.py`); Phase-1.C baselines (`baseline_template.py`, `baseline_ocr_only.py`, `baseline_pywinauto.py`, `run_baselines.py`); reproducibility (`sync_reports_to_repo.py`, `sync_handcorrected_zip_to_drive.py`) |
| `tasks/` | `T01_T20.json` — canonical evaluation task list shared between VisClick and the classical baselines |
| `samples/` | `desktop_seed/` (50 raw screenshots used to fine-tune); `templates/` (Phase-1.C reference PNGs, see its README); `test_screenshots/` (per-task captures saved by `run_baselines.py`) |
| `tests/` | Unit tests |
| `reports/` | `literature_table.csv` + `figures/`, `tables/` for the report |

## Push to personal GitHub

See `scripts/push_personal.sh` and Git credential notes from your earlier setup.

## License

Add a `LICENSE` when you are ready; default is all-rights reserved.
