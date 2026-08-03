# VisClick - MSc Project Code Submission (CMM799)

**Student:** Hiran Abeywardhana  
**RGU ID:** 2425488 | **IIT ID:** 20241504  
**Project:** Cross-Domain Machine Learning Framework for Scalable GUI Element Detection and Adaptation in Desktop Environments

This zip contains source code for the VisClick prototype and the ML experiment scripts. Third-party Python libraries are **not** included; install them with `pip` as below.

**GitHub (full history):** https://github.com/HiranMadhu/visclick

---

## 1. What is in this zip

| Part | Folders | Purpose |
|------|---------|---------|
| **Prototype (Windows bot)** | `src/visclick/`, `tasks/`, `scripts/run_baselines.py`, `scripts/baseline_*.py` | Live GUI automation on Windows 11 |
| **ML / experiments** | `notebooks/`, `configs/`, `scripts/run_*.py`, `reports/tables/` | Training, adaptation, evaluation (Colab or Linux GPU) |

| Included data (small) | Location |
|-----------------------|----------|
| Deployed detector (ONNX) | `weights/visclick.onnx` |
| Hand-corrected test set (8 screens) | `datasets/handcorrected_desktop_test/` |
| Desktop seed images (50) | `samples/desktop_seed/` |
| Evaluation task list | `tasks/T01_T20.json` |
| Result CSVs | `reports/tables/` |

Large datasets and extra model checkpoints are **not** in this zip (see Section 4).

---

## 2. Run the prototype (markers - start here)

**Requirements:** Windows 11, Python 3.11 or 3.12, 64-bit.

```bat
cd VisClick_CMM799_Code_Submission
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[windows]"
python -m visclick
```

1. Open a target window (e.g. Notepad, File Explorer).
2. In the VisClick window, type an instruction such as `click Save`.
3. Press **Run**. A short countdown runs, then the tool captures the screen, finds a UI element, and clicks it.

**Headless CLI (optional):**

```bat
python -m visclick.bot --instruction "click Save" --countdown 3
```

**Four-method evaluation (15 tasks, offline screenshots):**

```bat
py -3 scripts\run_baselines.py --auto
```

Results append to `reports\tables\baseline_results.csv`.

**Weights:** `weights/visclick.onnx` is included (~43 MB). No separate download needed for the demo.

---

## 3. Reproduce ML experiments (optional)

1. Upload large data to Google Drive or use the RGU OneDrive bundle (Section 4).
2. Open notebooks from `notebooks/` in Google Colab (GPU runtime), or run `scripts/run_uda_at_local.py` / `scripts/run_uda_shot_local.py` on a Linux machine with CUDA.
3. Use `configs/` and `python scripts/patch_colab_configs.py` when paths point to Drive.

Notebooks `01` through `14` follow the project phases: data pull, source training, desktop fine-tune, ONNX export, few-shot curve, SSP, UDA.

---

## 4. Large data (not in zip - RGU OneDrive)

Files over the Moodle zip limit are uploaded separately. See `ONEDRIVE_LARGE_DATA_README.txt` in this zip for the folder list.

**OneDrive link (request access from student):**  
[PASTE YOUR RGU ONEDRIVE SHARE LINK HERE BEFORE SUBMISSION]

Typical contents on OneDrive:

- YOLOv8 source checkpoint (`best_source_v8s.pt`)
- UDA / SSP training weights (optional)
- Unified mobile UI bundle or instructions to download RICO / CLAY / Zenodo record 19195885

Public datasets (download yourself):

| Dataset | URL |
|---------|-----|
| RICO | https://interactionmining.org/rico |
| CLAY (denoised RICO) | Li et al. (2022a) - see paper / project page |
| Zenodo unified bundle | https://zenodo.org/records/19195885 |
| ScreenSpot (eval only) | Cheng et al. (2024) - HuggingFace `datasets` |

---

## 5. Third-party software and libraries

Install via `pip install -e ".[windows]"` (see `pyproject.toml`). No vendor code is copied into this zip.

| Component | URL |
|-----------|-----|
| Python | https://www.python.org/ |
| Ultralytics (YOLOv8) | https://github.com/ultralytics/ultralytics |
| ONNX Runtime | https://onnxruntime.ai/ |
| OpenCV (`opencv-python`) | https://opencv.org/ |
| NumPy | https://numpy.org/ |
| Pillow | https://python-pillow.org/ |
| EasyOCR | https://github.com/JaidedAI/EasyOCR |
| PyAutoGUI | https://pyautogui.readthedocs.io/ |
| mss (screen capture) | https://github.com/BoboTiG/python-mss |
| rapidfuzz | https://github.com/maxbachmann/RapidFuzz |
| psutil | https://github.com/giampaolo/psutil |
| pywinauto (Windows baseline) | https://pywinauto.readthedocs.io/ |
| Tesseract OCR (optional, faster than EasyOCR) | https://github.com/UB-Mannheim/tesseract/wiki |
| Google Colab (training) | https://colab.research.google.com/ |
| HuggingFace `datasets` (ScreenSpot) | https://huggingface.co/docs/datasets |

**Licences:** Ultralytics YOLOv8 is AGPL-3.0; other pip dependencies use their respective open-source licences listed on PyPI.

---

## 6. Unit tests

```bat
pip install -e ".[dev]"
pytest -q tests
```

---

## 7. Contact

Hiran Abeywardhana - for OneDrive access or run issues during marking.
