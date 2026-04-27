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
| **1** | **← you are here** | Open the notebook below: **pull** + first data downloads (Part C.2) |
| 2 | later | RICO, Zenodo, VINS, EDA, `source_train` assembly (plan C.2, C.4, C.5) |
| 3 | later | Source-domain training (plan Part D) — *new notebook when you finish step 1–2* |
| … | later | Desktop fine-tune, experiments, eval (plan G–I) |

## Colab — only notebook for now

| Step 1: pull repo + start data (Part C) | Open in Colab |
|----------------------------------------|---------------|
| `notebooks/01_pull_and_data.ipynb` | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HiranMadhu/visclick/blob/main/notebooks/01_pull_and_data.ipynb) |

**What it does (in order):** mount Drive → **clone or `git pull`** `main` into `/content/visclick` → create Drive subfolders → install `huggingface_hub` → **CLAY** + **UI-Vision** downloads. Stops there. Next phases stay in the written plan until you add the next notebook.

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
| `notebooks/` | `01_pull_and_data.ipynb` only, until the next phase is added |
| `configs/` | YOLO templates (`<DRIVE>` placeholders); use `patch_colab_configs.py` in Colab |
| `scripts/` | `patch_colab_configs.py`, `capture_screenshots.py` (Windows), `annotate_export_to_yolo.py`, `run_eval.py` |
| `tests/` | Unit tests |
| `reports/` | `literature_table.csv` + `figures/`, `tables/` for the report |

## Push to personal GitHub

See `scripts/push_personal.sh` and Git credential notes from your earlier setup.

## License

Add a `LICENSE` when you are ready; default is all-rights reserved.
