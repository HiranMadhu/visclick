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
| 1 | done (you) | `01_pull_and_data.ipynb` — CLAY + UI-Vision |
| **2** | **current** | `02_rico_zenodo_vins.ipynb` — RICO, Zenodo unified, VINS |
| 3 | later | EDA + `source_train` assembly (C.4, C.5), then source training (Part D) |
| … | later | Desktop fine-tune, experiments, eval (plan G–I) |

## Colab notebooks (run in order; each starts fresh: mount + `git pull`)

| Step | Open in Colab |
|------|---------------|
| 1 — CLAY + UI-Vision | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HiranMadhu/visclick/blob/main/notebooks/01_pull_and_data.ipynb) |
| 2 — RICO, Zenodo unified, VINS | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HiranMadhu/visclick/blob/main/notebooks/02_rico_zenodo_vins.ipynb) |

**Outputs for the project report:** each notebook includes **`REPORT ...` lines** (and a final digest). Copy those into **`VisClick_Report_Data_Form.md` §0** in `gui_temp/`, or paste the block in chat to have it filled in.

**01** does: mount → clone / pull → subfolders → **CLAY** + **UI-Vision** → optional REPORT cell.

**02** does: same bootstrap → **RICO** (if you uploaded the zip) → **Zenodo** download + unzip → **VINS** clone → full REPORT. You do not need to keep the Colab session from 01; Drive holds the data.

**Config helper (later, when training):** `python scripts/patch_colab_configs.py` with `VISCLICK_DRIVE=/content/drive/MyDrive/visclick` fills `configs/yolo_*_colab.yaml` from the templates in `configs/`.

## Local setup (Windows, click-bot)

```bash
python -m venv .venv
.venv\Scripts\activate   # or source .venv/bin/activate on Linux
pip install -e .
# Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
python -m visclick.bot --instruction "click Save" --dry-run
```

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
