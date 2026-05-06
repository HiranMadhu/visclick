# VisClick — Detailed Step-Level Implementation & Report Plan

**Companion to:** `VisClick_3_Month_Plan.md` (the *scope* doc).
**This doc:** the *how*. Step-by-step instructions, dataset links, command lines, and where each output ends up in the final MSc project report.
**Compute:** Google Colab Free (T4 GPU).
**Demo / capture OS:** Windows.
**Demo apps:** VS Code, File Explorer, Chrome, Notepad.
**Final goals:** (1) a working **click-bot** prototype; (2) a finished MSc-style **PROJECT REPORT** in the same shape as the example RGU report.

> If anything in this doc and the scope doc disagree, the scope doc wins for *what*. This doc owns *how* and *with which links/commands*.

---

## Table of contents

- [0. Reading order and conventions](#0-reading-order-and-conventions)
- [Part A — The project frame](#part-a--the-project-frame)
- [Part B — Phase 0: Environment setup (Week 0)](#part-b--phase-0-environment-setup-week-0)
- [Part C — Phase 1: Literature & dataset acquisition (Weeks 1–2)](#part-c--phase-1-literature--dataset-acquisition-weeks-12)
- [Part D — Phase 2: Source-domain training (Weeks 3–4)](#part-d--phase-2-source-domain-training-weeks-34)
- [Part E — Phase 3: Target-domain screenshot capture (Week 5)](#part-e--phase-3-target-domain-screenshot-capture-week-5)
- [Part F — Phase 4: Annotation in CVAT (Weeks 5–6)](#part-f--phase-4-annotation-in-cvat-weeks-56)
- [Part G — Phase 5: Transfer-learning experiments (Week 7)](#part-g--phase-5-transfer-learning-experiments-week-7)
- [Part H — Phase 6: End-to-end click-bot prototype (Week 8)](#part-h--phase-6-end-to-end-click-bot-prototype-week-8)
- [Part I — Phase 7: Evaluation, ablations, and SILC readiness (Weeks 9–12)](#part-i--phase-7-evaluation-ablations-and-silc-readiness-weeks-912)
- [Part J — Producing the MSc project report](#part-j--producing-the-msc-project-report)
- [Part K — Appendices (cheat-sheet, troubleshooting, costs)](#part-k--appendices-cheat-sheet-troubleshooting-costs)

---

## 0. Reading order and conventions

- Read **Part A** for the frame. Then do **Part B** end-to-end before any Colab work.
- Code blocks marked `bash` run in Windows PowerShell (or WSL where noted), `colab` run inside a Colab cell, `python` are runnable scripts.
- Anywhere you see `<DRIVE>` replace with your own Google Drive path, e.g. `/content/drive/MyDrive/visclick`.
- Anywhere you see `<REPO>` it is the local clone of the project repo.
- Anywhere you see `[CITE]` it is something to cite verbatim in the report later.
- Every numbered task corresponds to a row you will check off in your Kanban board.
- Anywhere you see a quote-block starting with **`→ RECORD for VisClick_Report_Data_Form.md §X.Y:`** that is the *only* moment in this plan where I need a number / file from your hand. Capture it the moment it is produced, and drop it into the matching section of the form. Everything else (literature prose, requirements wording, LEPSI, conclusion, RQ answers, qualitative paragraphs) I will write for you from the form's contents.

---

## Part A — The project frame

This restates only what is needed to act on this doc. Full version lives in the scope doc.

| Field | Value |
|-------|-------|
| Working title | VisClick — Vision-Based GUI Element Detection and Click Automation for Desktop Applications using Transfer Learning |
| Aim | Build a lightweight AI that detects GUI elements in desktop screenshots using transfer learning from mobile/web UI data, then performs instruction-driven click automation, and report measurable accuracy. |
| Source domain (train) | Mobile UI: **RICO / CLAY**, Web UI: **WebUI**, plus unified **RICO+WebUI** YOLO bundle |
| Target domain (eval + demo) | Windows desktop UI: VS Code, File Explorer, Chrome, Notepad. Optional external benchmark: **UI-Vision** (ServiceNow, ICML 2025) |
| Detector family | Ultralytics YOLOv8 (n / s) |
| Compute | Google Colab Free (T4 GPU) |
| OCR | Tesseract first, EasyOCR fallback |
| Click | PyAutoGUI on Windows |
| Final outputs | (1) trained `.pt` and `.onnx` weights; (2) `bot.py` working on real Windows desktop; (3) report (this doc maps to its 9 chapters); (4) ≤60s demo video |

---

## Part B — Phase 0: Environment setup (Week 0)

**Outcome of this week:** every tool installed, every account ready, every folder structure agreed, repo bootstrapped, Colab confirmed working with GPU. **No model work yet.**

### B.0 — Hosting strategy: what lives where

Three platforms, each used for what it does well. Do **not** try to put everything in one place.

| Platform | Holds | Why this and not the others |
|----------|-------|-----------------------------|
| **GitHub** | Code, notebooks (`.ipynb`), configs (`*.yaml`), scripts, `README.md`, `requirements.txt` / `pyproject.toml` — text only, ≤ a few MB | Diffs, PRs, history, public link for the SILC poster and the supervisor. Atrocious for binaries > 100 MB. |
| **Google Drive** | Datasets (RICO, CLAY, WebUI, VINS, UI-Vision), trained `.pt` / `.onnx` weights, generated figures during training, big intermediate artefacts | 15 GB free, mounts inside Colab in two lines. No version history needed for these. |
| **Google Colab** | Compute runtime only — no persistent storage | Free T4 GPU. At runtime it *pulls code from GitHub* and *mounts Drive for data*. |

GitHub and Colab are first-class friends — Colab knows how to open and save notebooks straight to/from GitHub. Drive is mounted as a folder. So, the right setup order is **GitHub first** (so the repo URL exists), **Colab+Drive second** (referencing the repo we just made).

### B.1 GitHub repo bootstrap (Sessions S0a)

Do this **first**, before Colab. Once the repo URL exists, every Colab notebook just clones it.

1. Create / sign in to a GitHub account. Create a **private** repo called `visclick`. Stay private during development; flip it public around SILC submission so the poster URL works.
2. On your Windows machine, install Git for Windows: <https://git-scm.com/download/win>.
3. Clone the (still-empty) repo locally:

```bash
cd %USERPROFILE%\Documents
git clone https://github.com/<your-user>/visclick.git
cd visclick
```

4. Create the repo skeleton:

```
visclick/                          # <REPO>
  README.md
  .gitignore                       # ignore data/, weights/, *.zip, .ipynb_checkpoints
  requirements.txt                 # or pyproject.toml
  src/
    visclick/
      __init__.py
      capture.py                   # screenshots
      detect.py                    # YOLO inference
      ocr.py                       # Tesseract / EasyOCR
      match.py                     # instruction → element
      act.py                       # PyAutoGUI click
      bot.py                       # orchestrator
      utils.py
  notebooks/
    00_data_acquisition.ipynb
    01_data_eda.ipynb
    02_train_source.ipynb
    03_finetune_desktop.ipynb
    04_experiments_transfer.ipynb
    05_eval_and_ablations.ipynb
  configs/
    yolo_source.yaml
    yolo_desktop_finetune.yaml
    classes.txt
  scripts/
    capture_screenshots.py
    annotate_export_to_yolo.py
    run_eval.py
  tests/
    test_match.py
    test_pipeline.py
  reports/
    figures/
    tables/
```

5. `.gitignore` — keep all binary / large content out of GitHub. Those go to Drive.

```
__pycache__/
*.pyc
.ipynb_checkpoints/
data/
weights/
*.zip
*.tar.gz
*.7z
*.onnx
*.pt
.env
```

6. `README.md` — paste this stub. The Colab badges are what make any notebook clickable from GitHub straight into Colab:

````markdown
# VisClick

Vision-based GUI element detection and click automation for desktop applications using transfer learning.

## Run the notebooks in Colab (no local install required)

| Notebook | Open in Colab |
|----------|---------------|
| 00 — Data acquisition | [![Open](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<your-user>/visclick/blob/main/notebooks/00_data_acquisition.ipynb) |
| 01 — EDA              | [![Open](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<your-user>/visclick/blob/main/notebooks/01_data_eda.ipynb) |
| 02 — Train source     | [![Open](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<your-user>/visclick/blob/main/notebooks/02_train_source.ipynb) |
| 03 — Fine-tune desktop| [![Open](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<your-user>/visclick/blob/main/notebooks/03_finetune_desktop.ipynb) |
| 04 — Transfer experiments | [![Open](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<your-user>/visclick/blob/main/notebooks/04_experiments_transfer.ipynb) |
| 05 — Eval & ablations | [![Open](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<your-user>/visclick/blob/main/notebooks/05_eval_and_ablations.ipynb) |
````

> Replace `<your-user>` with your GitHub handle. The badge URLs follow the fixed pattern `colab.research.google.com/github/<user>/<repo>/blob/<branch>/<path>.ipynb` — nothing else needs to be configured on the GitHub side.

7. First commit:

```bash
git add .
git commit -m "bootstrap: project skeleton"
git push -u origin main
```

### B.2 Google + Colab + Drive (Sessions S0b)

GitHub holds the code. Drive holds the data. Colab is the runtime that pulls from both.

1. Sign in to Google with the account you will use for the whole project. Use one account; do not switch.
2. Open Google Drive → create a folder called `visclick`. This is `<DRIVE>` from now on. Sub-folders (data + weights + videos only — code is on GitHub):

```
<DRIVE>/visclick/
  data/
    raw/                  # untouched downloaded archives
    rico/                 # extracted RICO
    clay/                 # extracted CLAY labels
    webui/                # extracted WebUI subset
    vins/                 # extracted VINS
    ui_vision/            # ServiceNow UI-Vision desktop benchmark
    desktop_unlabeled/    # screenshots you will capture in Phase 3
    desktop_labeled/      # CVAT exports in Phase 4
    desktop_test/         # held-out screenshots, never seen during training
  weights/
    baseline_source/
    finetuned_desktop/
    experiments/
  videos/                 # screen recordings for demo
```

> Note: no `notebooks/`, `src/`, `configs/`, `scripts/`, `tests/`, or `reports/` in Drive. Those live in the GitHub repo and only appear inside Colab as `/content/visclick/...` after the clone in step 5.

3. Open Google Colab: <https://colab.research.google.com/> and sign in with the same Google account.
4. Top menu → **Runtime → Change runtime type → Hardware accelerator: GPU → Save**. On Colab Free this gives you a T4 most of the time.
5. The **first cell of every Colab notebook** does three things in order: mount Drive, clone the GitHub repo (or pull the latest), `cd` into it. Paste this template:

```colab
# 1) Mount Drive (data + weights live here)
from google.colab import drive
drive.mount('/content/drive')

# 2) Clone-or-pull the GitHub repo (code + notebooks + configs live here)
import os
REPO = "https://github.com/<your-user>/visclick.git"
if not os.path.isdir('/content/visclick'):
    !git clone {REPO} /content/visclick
else:
    !cd /content/visclick && git pull --rebase
%cd /content/visclick

# 3) Confirm GPU
import torch, subprocess
print("torch:", torch.__version__,
      "cuda:", torch.cuda.is_available(),
      "device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU only")
print(subprocess.check_output(["nvidia-smi"]).decode())
```

If all three sections run cleanly, **you are ready**. From now on every training command can read code/configs from `/content/visclick/...` and read/write data from `/content/drive/MyDrive/visclick/...`.

> **→ RECORD for `VisClick_Report_Data_Form.md` §1.2:** the **GPU name** printed by `nvidia-smi` (e.g. "Tesla T4 16 GB"), and from time to time how many Colab GPU-hours you have burned.

### B.2.1 Two-way Colab ↔ GitHub workflow (cheat-sheet)

You will edit notebooks **inside Colab** and want changes saved back to GitHub. Three options, ranked easiest first:

1. **One-click open** — anyone (you, supervisor, marker) clicks the README badge for a notebook and Colab opens that exact file from `main` of GitHub. No local clone needed.

2. **Open from inside Colab** — File → Open notebook → **GitHub** tab → search for `visclick` → pick a notebook. Same as the badge but without leaving Colab.

3. **Save changes back** — when a notebook has been edited in Colab: File → Save a copy in GitHub → choose `visclick` repo, `main` branch (or a new branch), commit message → "OK". This pushes the modified `.ipynb` straight to GitHub. The first time it asks Colab to authorise GitHub — click through once, never again.

> Tip: keep training-result cells *not cleared* before saving back. The committed `.ipynb` then contains the metrics inline, which makes Chapter 6 of the report easy to write.

For source-code files (`.py`) Colab cannot push directly. The clean pattern is: edit `.py` files locally on Windows in your editor (VS Code, etc.), `git push`, then in Colab the next `git pull --rebase` brings the change in. Notebooks change in Colab; `.py` changes locally.

### B.3 Windows local environment (Sessions S0c)

**Why local at all when training is in Colab?** The click-bot runs *on the desktop the user is touching*, so the demo and screenshot capture have to be local. Training stays in Colab.

1. Install **Python 3.10+ (64-bit)** for Windows: <https://www.python.org/downloads/windows/>. During install tick "Add Python to PATH".
2. Confirm:

```bash
python --version
pip --version
```

3. Create a virtual environment for the bot:

```bash
cd %USERPROFILE%\Documents\visclick
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
```

4. Install bot-side dependencies (CPU only is fine; inference is fast):

```bash
pip install ultralytics opencv-python pillow numpy pyautogui mss pytesseract easyocr fuzzywuzzy[speedup] python-Levenshtein onnxruntime
```

> **→ RECORD for `VisClick_Report_Data_Form.md` §1.3:** run `pip freeze > reports/pip_freeze.txt` once everything is installed, and copy the exact versions of `ultralytics`, `torch`, `opencv-python`, `pyautogui`, `mss`, `pytesseract`, `easyocr`, `onnxruntime`, `rapidfuzz`, `numpy` into the form's library-versions table.

5. Install **Tesseract** (for `pytesseract`): <https://github.com/UB-Mannheim/tesseract/wiki>. Take the latest 64-bit installer; tick "Add to PATH" if available, otherwise note the install path (default `C:\Program Files\Tesseract-OCR\tesseract.exe`) — `ocr.py` will reference it.
6. Install a recording tool for the demo video. Free options:
   - **OBS Studio**: <https://obsproject.com/>
   - **ShareX**: <https://getsharex.com/>
7. Sanity check that screenshots and clicks actually work — run this two-line probe (do **not** point at anything important; it just moves the cursor 10 px):

```python
import pyautogui
pyautogui.screenshot("probe.png")
print("saved probe.png")
pyautogui.moveRel(10, 0, duration=0.2)
```

> **→ RECORD for `VisClick_Report_Data_Form.md` §1.1:** open Windows Settings → System → About and copy: device name, processor (full string), installed RAM, OS version. Also note display resolution and DPI scaling (Settings → Display). One-time only.

### B.4 Annotation tool — CVAT (Sessions S0d)

You have two options. Pick one and stick with it.

**Option 1 — CVAT cloud (easiest).** Go to <https://app.cvat.ai/> → sign up free. Best for one-person, ~50–100 image annotation. No install.

**Option 2 — CVAT self-hosted.** Use only if you do not want screenshots leaving your machine. Requires Docker Desktop. Repo: <https://github.com/cvat-ai/cvat>. Install guide: <https://docs.cvat.ai/docs/administration/basics/installation/>.

For Phase 4 we will use **Option 1** unless your screenshots contain anything you cannot upload.

### B.5 Reference manager (Sessions S0e)

For the final report you need 25–40 references. Set this up now so you do not lose any link.

- Install **Zotero** (free): <https://www.zotero.org/download/>.
- Install the Zotero Connector browser extension.
- Create a collection called `VisClick`.
- Every paper / dataset / tool you use later in this doc gets a Zotero entry the *first time you read it*. Future you will thank present you.

### B.6 Definition of done — Phase 0

- [ ] GitHub repo `visclick` exists with the skeleton committed and pushed (per §B.1) and Colab badges in `README.md`.
- [ ] Drive folder structure exists exactly as in §B.2 (data, weights, videos only — no code).
- [ ] First-cell template in §B.2 step 5 mounts Drive, clones GitHub, and prints a Tesla T4 from `nvidia-smi`. `torch.cuda.is_available()` is `True`.
- [ ] At least one notebook has been opened *via* its GitHub Colab badge and saved back via "Save a copy in GitHub" (proves the round-trip works).
- [ ] Local Windows venv installed; PyAutoGUI screenshot works; Tesseract found.
- [ ] CVAT account created or self-hosted CVAT reachable on `localhost:8080`.
- [ ] Zotero `VisClick` collection exists and has the example RGU report PDF added.

---

## Part C — Phase 1: Literature & dataset acquisition (Weeks 1–2)

**Outcome of this phase:** all datasets downloaded, a written literature review draft, and a class schema agreed.

### C.1 Reading list and what to extract

Open each of these and create a Zotero entry. For every paper, record three things in a single sheet (`reports/literature_table.csv`): *what they did*, *what numbers they got*, *what is missing that VisClick adds*.

#### C.1.1 Datasets and benchmarks (must-read)

| # | Title | Year | Why read | Link |
|---|-------|------|----------|------|
| L1 | RICO: A Mobile App Dataset for Building Data-Driven Design Applications (Deka et al., UIST 2017) | 2017 | The grandparent of all UI corpora | Project: <https://interactionmining.org/rico> · Paper: <https://dl.acm.org/doi/10.1145/3126594.3126651> |
| L2 | CLAY: Learning to Denoise Raw Mobile UI Layouts (Li et al., CHI 2022) | 2022 | Cleaned RICO labels; the source data we will train on | Paper: <https://arxiv.org/abs/2201.04100> · Code: <https://github.com/google-research-datasets/clay> |
| L3 | VINS: Visual Search for Mobile UI Design (Bunian et al., CHI 2021) | 2021 | Concrete mAP baseline (76.39%) on a small UI element set | Paper: <https://arxiv.org/abs/2102.05216> · Code/data: <https://github.com/sbunian/VINS> |
| L4 | WebUI: A Dataset for Enhancing Visual UI Understanding with Web Semantics (Wu et al., CHI 2023) | 2023 | Web UI screenshots, useful as a *bridge* domain between mobile and desktop | Project: <https://uimodeling.github.io/> · Paper: <https://huggingface.co/papers/2301.13280> |
| L5 | UI-Vision: A Desktop-centric GUI Benchmark (Nayak et al., ICML 2025) | 2025 | The first real desktop UI benchmark — 83 apps, 6 categories. Use as **external test set** for the report | Paper: <https://arxiv.org/abs/2503.15661> · Site: <https://uivision.github.io/> · GitHub: <https://github.com/uivision/UI-Vision> · HF dataset: <https://huggingface.co/datasets/ServiceNow/ui-vision> |
| L6 | Unified RICO + WebUI YOLO bundle (Zenodo, 2026) | 2026 | Pre-merged 12-class YOLO-format dataset, saves you weeks of schema unification | <https://zenodo.org/records/19195885> |

#### C.1.2 Detection / transfer-learning techniques (must-read)

| # | Topic | Why read | Link |
|---|-------|----------|------|
| L7 | YOLOv8 docs (Ultralytics) | Train / freeze / export commands you will copy | <https://docs.ultralytics.com/> · <https://docs.ultralytics.com/guides/finetuning-guide/> |
| L8 | "GUI Element Detection Using SOTA YOLO Deep Learning Models" | Direct prior art on YOLO for GUIs | <https://arxiv.org/abs/2408.03507> |
| L9 | Comparison of YOLOv5 vs YOLOv8 on Mobile UI Detection | Justifies picking YOLOv8 over older versions | <https://www.researchgate.net/publication/372873844> |
| L10 | DINOv2: Learning Robust Visual Features Without Supervision (Oquab et al., 2023/24) | Modern vision foundation model used as a labeller in 2025 work | Paper: <https://arxiv.org/abs/2304.07193> · Code: <https://github.com/facebookresearch/dinov2> |
| L11 | DINO Teacher (CVPR 2025) — UDA for object detection with foundation labels | A 2025 alternative to plain Mean Teacher; cite as "tried, trade-off found" | <https://openaccess.thecvf.com/content/CVPR2025/html/Lavoie_Large_Self-Supervised_Models_Bridge_the_Gap_in_Domain_Adaptive_Object_CVPR_2025_paper.html> |
| L12 | ALDI (Align and Distill) framework — unified UDA for detection | Cite as the modern benchmarking framework | <https://arxiv.org/abs/2403.12029> |
| L13 | Structural Consistency Learning for UDA Object Detection (NN 2025) | Alternative feature-alignment technique | <https://www.sciencedirect.com/science/article/pii/S0893608025006471> |
| L14 | YOLOv8 fine-tuning on small datasets — Ultralytics community | Best practices for the 50–100 image regime | <https://github.com/ultralytics/ultralytics/issues/6201> |

#### C.1.3 GUI automation / classical baselines

| # | Tool | Why mention | Link |
|---|------|-------------|------|
| L15 | SikuliX (image-template clicking) | Classical baseline VisClick must beat conceptually | <http://sikulix.com/> |
| L16 | pywinauto (Windows accessibility-tree automation) | Classical baseline; needs the app to expose accessibility | <https://pywinauto.readthedocs.io/> |
| L17 | PyAutoGUI | The actual library you will use to *send* clicks | <https://pyautogui.readthedocs.io/> |
| L18 | mss (faster screenshots than PIL) | Cite if you switch capture for performance | <https://github.com/BoboTiG/python-mss> |

#### C.1.5 UI element diversity (added after the 5 May 2026 prototype review)

When the prototype was first run on a Windows 11 Save-As dialog the YOLO detector missed the Save button entirely (see §8.4 of the Report Data Form). The papers below were added to the literature table to (a) explain why this happens, (b) justify the OCR-based text-grounding fallback that fixes the specific case, and (c) establish that closing the residual gap on icon-only clickables is an open problem in the field — not a defect of this thesis. Full annotations live in `reports/literature_table.csv`.

| # | Title | Why it matters for VisClick |
|---|-------|------------------------------|
| L3 (lit. table) | UIED — Object Detection for GUI: Old Fashioned or DL or Combination? (Xie et al., FSE 2020) | Explicitly proves pure deep learning misses fine icons / dropdown arrows on dense UIs and proposes the OCR + detector hybrid VisClick now uses. |
| L5 | Apple Screen Recognition (Zhang et al., CHI 2021) | Production system that hits the same out-of-distribution drop (F1 0.91 → 0.74 on unseen apps) and uses an OCR fallback for the same reason. |
| L6 | Widget Captioning (Li et al., EMNLP 2020) | Establishes that icon-only clickables (close X / settings cog / dropdown arrows) require visual / spatial reasoning beyond what the 6-class detector provides. |
| L7 | SeeClick (Cheng et al., ACL 2024) | The modern VLM-grounding alternative; cited as the deliberate path *not* taken (interpretability + CPU latency reasons). |
| L8 | Pix2Struct (Lee et al., ICML 2023) | Shows web-scale screenshot pretraining matters; cited as broader trend. |
| L10 | ScreenAI (Baechler et al., IJCAI 2024) | Demonstrates the residual icon-coverage gap is fundamentally a data-scale problem at the open-source frontier. |

#### C.1.4 Existing accuracy numbers worth quoting in the report

These are concrete numbers you can cite in the **Literature Review** and in the **Control Study** of the report. Put them in `reports/literature_table.csv` exactly as written.

| Source | Domain | Detector | Reported metric | Value |
|--------|--------|----------|-----------------|-------|
| Bunian et al. 2021 (VINS) [L3] | Mobile UI | Custom | mAP | **76.39%** |
| Salehi et al. 2024 [L8] | Mobile / generic UI | YOLOv8 family | mAP@.5 (varies by version) | up to ~84% on subsets |
| Roboflow YOLOv8s on web GUI (web search, 2026) | Web UI (~1000 imgs) | YOLOv8s | mAP@.5:.95 | **0.232** (precision 0.454, recall 0.425) |
| YOLOv8s vs YOLOv5s on mobile UI [L9] | Mobile UI | YOLOv8s | Δ mAP vs YOLOv5s | +3.32% |
| UI-Vision (ServiceNow) [L5] | **Desktop**, 83 apps | Multiple agent baselines | element grounding accuracy | reports show even SOTA agents struggle, especially on dense apps — *use as motivation* |

> **Use of these numbers in the report:** Chapter 2 (Literature Review) cites these to establish that even on cleaner / larger datasets, GUI element detection mAP is far from saturated — and that specifically on *desktop*, performance is still an open problem [L5].

### C.2 Dataset acquisition (Sessions S1–S2)

Run all of these from a Colab notebook (`notebooks/00_data_acquisition.ipynb`) so the downloads land directly in Google Drive.

#### C.2.1 RICO

```colab
%cd <DRIVE>/data/raw
# RICO is hosted at interactionmining.org. Browse to https://interactionmining.org/rico
# and click 'UI Screenshots and View Hierarchies'. Once you have the direct mirror URL
# you can: !wget -O rico_unique_uis.zip <URL>
# As of 2026 there is no single stable curl-able link; using the browser is fine.
# After download, move the zip into <DRIVE>/data/raw/rico_unique_uis.zip then:
!unzip -q rico_unique_uis.zip -d ../rico
```

The extracted tree usually contains **`rico/combined/`** (screenshots + JSON per UI). Point label joins and path logic at that folder, not only `rico/` root.

If browser-download into Drive is annoying, install the [Drive desktop app](https://www.google.com/drive/download/) and drop the zip into the synced folder.

#### C.2.2 CLAY (denoised RICO)

```colab
%cd <DRIVE>/data/raw
!git clone https://github.com/google-research-datasets/clay.git
# CLAY ships labels (clay_labels.csv, label_map.txt, split_*.txt). Images come from RICO.
# We will join CLAY labels onto RICO image filenames.
%cd <DRIVE>/data
!cp -r raw/clay/* clay/
```

The class list is in `<DRIVE>/data/clay/label_map.txt`. Open it and pick the subset that maps to VisClick classes (see §C.3).

#### C.2.3 WebUI (optional bridge domain)

```colab
%cd <DRIVE>/data/raw
# Project page: https://uimodeling.github.io/
# WebUI is large (~400k pages). Use the Web-7k split for our purposes.
# Follow the instructions on the project page to fetch Web-7k tarball,
# then place at <DRIVE>/data/raw/webui_7k.tar.gz
!tar -xzf webui_7k.tar.gz -C ../webui
```

#### C.2.4 VINS

```colab
%cd <DRIVE>/data/raw
!git clone https://github.com/sbunian/VINS.git vins_repo
# Follow VINS README for the actual image archive (one-time external download).
# Place archive then:
%cd <DRIVE>/data
# unzip into vins/ once obtained
```

#### C.2.5 UI-Vision (the **desktop** benchmark — most valuable test set)

```colab
%cd <DRIVE>/data
!pip install -q huggingface_hub
!huggingface-cli download ServiceNow/ui-vision --repo-type dataset --local-dir ./ui_vision
# Or, plain git:
# !git lfs install
# !git clone https://huggingface.co/datasets/ServiceNow/ui-vision
```

This is **781 MB**, **MIT licensed**, **83 applications**, with bounding boxes and action trajectories. We will use it as an *external generalisation test set* in Phase 7. **This is the single strongest dataset for our project's report.**

#### C.2.6 Unified RICO + WebUI YOLO bundle (saves time on schema merge)

```colab
%cd <DRIVE>/data/raw
# Zenodo bundle: 105,130 images, 12 unified classes, YOLO format
# The deposit ships as three zips (not dataset.zip): train, val, test
!wget -c -O train.zip "https://zenodo.org/records/19195885/files/train.zip?download=1"
!wget -c -O val.zip   "https://zenodo.org/records/19195885/files/val.zip?download=1"
!wget -c -O test.zip  "https://zenodo.org/records/19195885/files/test.zip?download=1"
!unzip -q train.zip -d ../unified
!unzip -q val.zip   -d ../unified
!unzip -q test.zip  -d ../unified
```

File names and links: <https://zenodo.org/records/19195885> (API lists `train.zip` ~5.5 GB, `val.zip` ~6.7 GB, `test.zip` ~0.7 GB as of 2026).

### C.3 Class schema (Sessions S3)

VisClick classes are intentionally **small** to keep annotation feasible. We map all source datasets to this same 6-class schema:

```
configs/classes.txt
0  button
1  text
2  text_input
3  icon
4  menu
5  checkbox
```

Mapping table (use `scripts/map_labels.py` to apply it):

| Source dataset | Source label | VisClick class |
|----------------|--------------|----------------|
| CLAY | BUTTON, RADIO_BUTTON_GROUP, TOGGLE_SWITCH | button |
| CLAY | TEXT, LABEL | text |
| CLAY | INPUT, EDIT_TEXT | text_input |
| CLAY | ICON, IMAGE_BUTTON | icon |
| CLAY | LIST_ITEM, MENU_ITEM, NAV_DRAWER | menu |
| CLAY | CHECKBOX, CHECKED_TEXTVIEW | checkbox |
| Unified RICO+WebUI | Button, Text, Image, Icon, Input, Link, Checkbox, Toggle, Toolbar, Navigation, Modal, Tab | button (Button, Toggle, Tab), text (Text, Link), text_input (Input), icon (Image, Icon), menu (Toolbar, Navigation, Modal), checkbox (Checkbox) |
| WebUI | (similar to RICO, use the unified bundle in §C.2.6 instead of raw WebUI labels) |  |
| UI-Vision | annotation taxonomy | match by name where possible; otherwise leave for §C.5 |

> **Why 6 classes and not 12?** With ~50 desktop labelled images, 12 classes will starve some classes of examples. 6 classes keeps every class learnable and is enough to demonstrate the click-bot.

> **What clickables does this 6-class schema cover, and what does it deliberately NOT cover?** Real-world UIs contain many shapes of clickable element: text-labeled buttons (Save / Cancel / OK), icon-only buttons (close X, settings cog, minimise), dropdown arrows (▼), toggle switches, sliders, hyperlinked text inside paragraphs, image buttons (folder thumbnails), tabs, and breadcrumb chevrons. The 6-class schema covers the first kind reliably and the others partially:
> - **`button` / `text` / `text_input` / `menu` / `checkbox`** — strong coverage when training data has examples (RICO / Zenodo are well-represented for these).
> - **`icon`** — under-represented in the source data, so recall drops on Windows native dialogs. Documented in §8.4 of the Report Data Form.
> - **Toggle / slider** — not represented in the schema at all. Out of scope for the prototype; the bot's `xy` and *Pick Coordinates* fallbacks cover them in daily use.
>
> This is not a bug, it is a deliberate scope decision aligned with the literature: UIED [L3] reports that pure deep learning misses fine icons / dropdown arrows on dense desktops and proposes the same OCR + detector hybrid VisClick uses; Apple's Screen Recognition [L5] reports the same out-of-distribution drop on unseen apps and uses an OCR fallback for the same reason; ScreenAI [L10] shows that closing the gap on icon-only clickables fundamentally requires a screenshot corpus an order of magnitude larger than RICO, which does not exist in the open-source space. Citations live in `reports/literature_table.csv` (rows L3, L5, L6, L10).
>
> **Mitigation already in the prototype:** when YOLO misses a text-labeled element (e.g. the Save button on a flat Windows 11 dialog), the bot runs full-image Tesseract OCR via `ocr.text_ground()` and clicks the matching word's bounding box. This recovers Save / Cancel / OK / Apply / any text-labeled button regardless of whether the detector drew a box on it. Implementation: `src/visclick/ocr.py::text_ground`, wired into both the CLI (`bot.py`) and the GUI (`gui.py`).

### C.4 EDA on each dataset (Session S4)

For every dataset write a short EDA section in `notebooks/01_data_eda.ipynb`:

1. Sample size (number of images and instances per class).
2. Class balance bar chart.
3. Image resolution distribution (histogram).
4. 9 random samples with bounding boxes drawn (use `cv2.rectangle`).
5. Note any obvious quality issues.

These figures go straight into **Chapter 6 — Implementation** of the report.

> **→ RECORD for `VisClick_Report_Data_Form.md` §3.2:** save each chart as `reports/figures/eda_<dataset>_classes.png` and `reports/figures/eda_<dataset>_resolutions.png`. Just paste the file paths into the form. I'll write the prose around them.

### C.5 Source-domain training set assembly (Session S5)

To keep Colab Free training under control we assemble a **smaller, well-mixed source set** rather than throwing all 105k images at training:

| Source | Images sampled | Purpose |
|--------|---------------|---------|
| Unified RICO+WebUI | 8,000 (random, stratified by class) | Main training set — broadest coverage |
| CLAY | 2,000 (clean labels) | Bias the detector toward semantic correctness |
| VINS | All ~4,800 | Better balance for `icon`, `text_input`, `checkbox` |
| **Total** | **~14,800** | |

Save the assembled YOLO-format dataset under `<DRIVE>/data/source_train/` with `images/`, `labels/`, and a `data.yaml`:

```yaml
# configs/yolo_source.yaml
path: <DRIVE>/data/source_train
train: images/train
val:   images/val
test:  images/test

nc: 6
names: [button, text, text_input, icon, menu, checkbox]
```

> **→ RECORD for `VisClick_Report_Data_Form.md` §2.1:** after the assembly script has run, write a tiny one-liner that prints **per-class instance counts** in the assembled set (e.g. `button=3214, text=4012, ...`). Paste the six numbers into §2.1 of the form.

### C.6 Definition of done — Phase 1

- [ ] All 6 datasets in §C.2 are downloaded and unzipped under `<DRIVE>/data/`.
- [ ] `reports/literature_table.csv` has at least 18 entries (one per ref [L1]–[L18]).
- [ ] `configs/classes.txt` and the source `data.yaml` exist.
- [ ] `notebooks/01_data_eda.ipynb` produces 4 figures per dataset, saved into `reports/figures/eda/`.
- [ ] First draft of **Chapter 2 — Literature Review** exists, even if rough.

---

## Part D — Phase 2: Source-domain training (Weeks 3–4)

**Outcome:** a `baseline_source.pt` checkpoint that detects the 6 VisClick classes well on mobile/web UIs.

### D.1 Notebook stub — `notebooks/02_train_source.ipynb`

The notebook always starts with the **standard first cell from §B.2 step 5** (mount Drive, clone GitHub, GPU check). After that, the training cell uses code/configs from the GitHub clone and reads/writes data + weights to Drive.

```colab
# After the standard first cell from §B.2 step 5 has run, you are at /content/visclick.

# Constants — Drive paths for data and weights
DRIVE = "/content/drive/MyDrive/visclick"

# Install Ultralytics fresh in the runtime
!pip install -q ultralytics==8.* opencv-python

# Train YOLOv8s on the source set (~14,800 images, 6 classes)
from ultralytics import YOLO
model = YOLO("yolov8s.pt")  # COCO-pretrained starting point
results = model.train(
    data="configs/yolo_source.yaml",          # from the GitHub clone (cwd)
    epochs=30,                                # T4 + 15k images: ~30 epochs in ~6h split across sessions
    imgsz=640,
    batch=16,
    workers=2,
    optimizer="AdamW",
    lr0=0.001,
    cos_lr=True,
    patience=10,
    project=f"{DRIVE}/weights/baseline_source",  # results survive runtime restarts
    name="run1",
    seed=0,
    save=True,
    plots=True,
)
```

The dataset paths inside `configs/yolo_source.yaml` should already point at `<DRIVE>/data/source_train/...` (see §C.5), so no path edit is needed in the yaml.

> **Why YOLOv8s, not n or m?** Free Colab T4 has ~16 GB; YOLOv8s at 640 fits comfortably with batch 16 and converges fast. YOLOv8m would also fit but takes ~1.7× longer. We will *also* train a YOLOv8n later for the latency comparison (see §G.1, Method M0).

### D.2 Saving and checkpointing across sessions (important on Colab Free)

Colab Free disconnects after ~12 hours of activity (or much sooner if idle). Train in two halves. Because `project=` points at Drive, the `last.pt` checkpoint is already persisted between sessions.

```colab
DRIVE = "/content/drive/MyDrive/visclick"
model = YOLO(f"{DRIVE}/weights/baseline_source/run1/weights/last.pt")
model.train(
    data="configs/yolo_source.yaml",
    epochs=30,
    resume=True,
)
```

Once happy with a run, give the best weights a stable name in Drive so later notebooks can reference it without knowing the run number:

```colab
!cp {DRIVE}/weights/baseline_source/run1/weights/best.pt {DRIVE}/weights/baseline_source/best_source_v8s.pt
```

### D.3 Sanity-check predictions

```colab
DRIVE = "/content/drive/MyDrive/visclick"
m = YOLO(f"{DRIVE}/weights/baseline_source/best_source_v8s.pt")
res = m.predict(source="data/source_train/images/test", save=True, conf=0.25)
# Inspect the saved annotated images under runs/predict/...
```

### D.4 Recording the result for the report

For Chapter 6 / Chapter 7 of the report you need:

1. Training curves (loss + mAP) → `reports/figures/source_train_curves.png` (Ultralytics auto-saves these).
2. Final source-domain metrics table → `reports/tables/source_domain_results.csv` with mAP@.5, mAP@.5:.95, precision, recall.
3. 6 example predictions (one per class) on the source test split → `reports/figures/source_predictions/`.

> **→ RECORD for `VisClick_Report_Data_Form.md` §4 (row "Source baseline"):** the four numbers from `model.val()` (mAP@.5, mAP@.5:.95, precision, recall), the wall-clock training time, plus `reports/figures/source_train_curves.png`. Treat the source-domain detector as one of the model rows, even though it does not become the headline.

### D.5 Definition of done — Phase 2

- [ ] `<DRIVE>/weights/baseline_source/best_source_v8s.pt` exists in Drive.
- [ ] mAP@.5 reported on the source test split (target: ≥0.55; that is realistic given the unified bundle).
- [ ] At least 6 example predictions saved.
- [ ] First draft of **Chapter 6.5 — Source-domain training** in the report.

---

## Part E — Phase 3: Target-domain screenshot capture (Week 5)

**Outcome:** ≥120 desktop screenshots from the four target apps, organised and ready for annotation.

### E.1 Capture protocol

We need *variety* much more than *volume*. Aim for these counts:

| App | Screenshots | What to vary |
|-----|------------|--------------|
| **VS Code** | 40 | Light vs Dark theme, Explorer / Source Control / Search panels open, Command Palette visible, dialogs (Save As, Open File), context menus |
| **File Explorer** | 30 | Different folders, Details / Tiles / List view, properties dialog, ribbon vs no ribbon, error dialogs |
| **Chrome** | 30 | New tab, settings page, downloaded items, bookmarks bar shown/hidden, in-page form |
| **Notepad** | 20 | Empty, with text, Find dialog, Save dialog, About dialog |
| **Total** | **120** | |

> Of these 120 we will hold out **~30 (split balanced across apps) as the desktop test set**. They never enter training or annotation tuning.

> **→ RECORD for `VisClick_Report_Data_Form.md` §2.2:** at end-of-capture run a `dir /s /b *.png | wc -l` per app folder; write the four counts into §2.2 of the form.

### E.2 Capture script — `scripts/capture_screenshots.py`

```python
# Run on Windows. Captures the active monitor every time you press F9.
# Press F10 to quit.
# Saves to <REPO>/../data/desktop_unlabeled/<app>/<UTC-timestamp>.png
import os, datetime, time, keyboard, mss

APP_KEY_TO_NAME = {"1":"vscode", "2":"file_explorer", "3":"chrome", "4":"notepad"}
out_root = os.path.expanduser(r"~\Documents\visclick_data\desktop_unlabeled")

def capture(app):
    folder = os.path.join(out_root, app); os.makedirs(folder, exist_ok=True)
    name = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ.png")
    with mss.mss() as sct:
        sct.shot(mon=-1, output=os.path.join(folder, name))
    return os.path.join(folder, name)

print("Press 1/2/3/4 to choose app, then F9 to capture, F10 to quit.")
app = "vscode"
while True:
    if keyboard.is_pressed("f10"): break
    for k,v in APP_KEY_TO_NAME.items():
        if keyboard.is_pressed(k): app = v; print("active:", app); time.sleep(0.4)
    if keyboard.is_pressed("f9"):
        path = capture(app); print("saved", path); time.sleep(0.4)
    time.sleep(0.05)
```

Install once:

```bash
pip install keyboard mss
```

Run as **administrator** so the global `F9` hotkey works:

```bash
python scripts/capture_screenshots.py
```

### E.3 Naming and folder hygiene

After a session, rsync (or just copy) the local capture folder up to `<DRIVE>/data/desktop_unlabeled/`. Do **not** rename files — the timestamp is your audit trail.

### E.4 Privacy / IP review (LEPSI prep)

For each screenshot, before uploading:

- Close any window with sensitive information (chats, email).
- Avoid screenshots showing internal company tooling (this is why we deliberately picked VS Code / Explorer / Chrome / Notepad).
- Note in `reports/screenshot_provenance.csv` the app name and the date — Chapter 9.5 of the report (LEPSI) will cite it.

### E.5 Definition of done — Phase 3

- [ ] At least 120 screenshots in `<DRIVE>/data/desktop_unlabeled/` distributed roughly per the table above.
- [ ] 30 of them moved into `<DRIVE>/data/desktop_test/` (selected *before* annotation begins to keep them blind).
- [ ] `reports/screenshot_provenance.csv` filled in.

---

## Part F — Phase 4: Annotation in CVAT (Weeks 5–6)

**Outcome:** ~90 labelled training screenshots and ~30 labelled test screenshots in YOLO format, ready for fine-tuning.

### F.1 Set up CVAT project

1. <https://app.cvat.ai/> → New Project → Name: `VisClick Desktop`.
2. Labels → add the 6 classes from `configs/classes.txt` (`button`, `text`, `text_input`, `icon`, `menu`, `checkbox`). Use distinct colours.
3. Create two tasks: `desktop_train` and `desktop_test`.
4. Upload screenshots into the matching task.

### F.2 Annotation playbook (decide once, follow always)

| Class | Includes | Excludes |
|-------|----------|----------|
| `button` | Anything clickable that *visually* looks like a button (filled, outlined, raised). Tabs in a tab-bar are buttons. | Plain links inside text |
| `text` | Static labels, headings, body text (only if it is a label of something interactive or part of the UI chrome). | Big paragraphs of document content (e.g. inside a Notepad note) |
| `text_input` | Editable input fields (search bar, address bar, file-name field). | Read-only text |
| `icon` | Small graphic affordances (cogs, magnifier, checkbox-of-a-todo-list inside content). | Application logos in the title bar (skip) |
| `menu` | Top-bar menu rows ("File", "Edit"), context-menu items, sidebar navigation rows. | Single buttons that happen to be in a row |
| `checkbox` | Real checkboxes. | Toggle switches (those go to `button`, the schema is small on purpose) |

Tightness: the bounding box should hug the visible widget; do not include adjacent shadow.

Do a **calibration pass**: annotate the first 10 images, then re-open them after a 10-minute break and check consistency. If you would re-draw any box differently, update the playbook before continuing.

### F.3 Export to YOLO

CVAT → task → Actions → **Export task dataset** → format: `YOLO 1.1`. Download zip, extract into `<DRIVE>/data/desktop_labeled/` (train task) and `<DRIVE>/data/desktop_test/labels/` (test task).

### F.4 Build the desktop fine-tune `data.yaml`

```yaml
# configs/yolo_desktop_finetune.yaml
path: <DRIVE>/data/desktop_labeled
train: images/train
val:   images/val
test:  images/test

nc: 6
names: [button, text, text_input, icon, menu, checkbox]
```

Use a 75/15/10 split of the 90 train images, keep the 30 test images untouched.

> **→ RECORD for `VisClick_Report_Data_Form.md` §2.3:** after the YOLO-format export, run a 5-line script that walks the `labels/train`, `labels/val`, `labels/test` folders and tallies instances per class. Drop the resulting 6×3 numbers (6 classes × 3 splits) into §2.3 of the form. The same script can also tally per-app counts; paste those into §2.2.

### F.5 Definition of done — Phase 4

- [ ] ~90 desktop training screenshots fully labelled with the 6 VisClick classes.
- [ ] ~30 desktop test screenshots fully labelled (held out).
- [ ] YOLO-format export succeeded; `data.yaml` validated by `ultralytics check`.
- [ ] First draft of **Chapter 6.3 — Dataset preprocessing** of the report (covers the annotation playbook in §F.2).

---

## Part G — Phase 5: Transfer-learning experiments (Week 7)

**Outcome:** a comparison table of multiple transfer-learning strategies on the desktop test set. Each experiment is a row in the **control study** of the report.

### G.0 Why run several methods, even ones we expect to be worse?

Running and *honestly reporting* multiple methods is the heart of an MSc research chapter. The example RGU report does the same thing (it compared MobileNetV3 / EfficientNetB0 / DenseNet121, and explicitly tested *with* and *without* preprocessing). The point is **not** that everything wins — it is that the experiments answer your research questions.

### G.1 Methods to run

For every method we report on the **same desktop test set** (the 30 held-out screenshots). All experiments live in `notebooks/04_experiments_transfer.ipynb` and write a row into `reports/tables/transfer_experiments.csv`. Each notebook starts with the standard first cell from §B.2 step 5 (mount Drive, clone GitHub) and uses `DRIVE = "/content/drive/MyDrive/visclick"` for any path that should survive runtime disconnect.

| ID | Method | One-line description | Expected verdict |
|----|--------|----------------------|------------------|
| **M0** | YOLOv8n trained-from-scratch on desktop only | No transfer at all | Worst (control / floor) |
| **M1** | YOLOv8s COCO-pretrained, fine-tune on desktop only | "Standard" off-the-shelf transfer | Mid |
| **M2** | YOLOv8s **source (RICO/CLAY/VINS) pre-trained**, **head-only** fine-tune on desktop | Cheap, fast | Mid |
| **M3** | YOLOv8s source pre-trained, **light full fine-tune** (low LR, freeze=10) | Our main candidate | **Best of practical methods** |
| **M4** | YOLOv8s source pre-trained, **full fine-tune** (no freezing) | Slightly slower; risk of overfitting on 90 images | Comparable to M3, sometimes worse |
| **M5** | M3 + **screenshot preprocessing** (theme normalization, contrast/CLAHE on dense regions, fixed-size letterbox) | Direct ablation of preprocessing | Improvement over M3 if preprocessing matters |
| **M6** | M3 + **pseudo-labelling** on extra unlabelled desktop screenshots (Mean-Teacher-lite) | UDA stretch goal | Modest extra improvement |
| **M7** | **DINOv2 + linear-probe detection head** as an alternative architecture | Cite [L10] [L11]; compare *foundation-model* style transfer to YOLO-style transfer | Likely lower mAP, slower training, but interesting for the report |
| **M8** | **Heavy data augmentation only** (mosaic, mixup, hsv, flips) on top of M0 | Augmentation-without-transfer ablation | Better than M0, worse than M3 |

> **Per the user's request**: M0, M7, M8 are explicitly included so the report can say *"we tried these other methods, here are the numbers, here is why we did not pick them as the headline approach"*.

### G.2 Recipes (copy-pasteable)

#### M1 — Standard COCO-pretrained → desktop

```colab
DRIVE = "/content/drive/MyDrive/visclick"
from ultralytics import YOLO
m = YOLO("yolov8s.pt")
m.train(data="configs/yolo_desktop_finetune.yaml",
        epochs=80, imgsz=640, batch=8,
        optimizer="AdamW", lr0=1e-3, patience=15,
        project=f"{DRIVE}/weights/experiments", name="M1")
```

#### M2 — Source pre-trained, **head-only**

```colab
DRIVE = "/content/drive/MyDrive/visclick"
m = YOLO(f"{DRIVE}/weights/baseline_source/best_source_v8s.pt")
m.train(data="configs/yolo_desktop_finetune.yaml",
        epochs=80, imgsz=640, batch=8,
        optimizer="AdamW", lr0=1e-3, freeze=22,   # freeze backbone+neck, train head
        patience=15,
        project=f"{DRIVE}/weights/experiments", name="M2")
```

#### M3 — Source pre-trained, **light full fine-tune**

```colab
DRIVE = "/content/drive/MyDrive/visclick"
m = YOLO(f"{DRIVE}/weights/baseline_source/best_source_v8s.pt")
m.train(data="configs/yolo_desktop_finetune.yaml",
        epochs=120, imgsz=640, batch=8,
        optimizer="AdamW", lr0=5e-4, cos_lr=True,
        freeze=10,            # keep first 10 backbone layers frozen
        warmup_epochs=3,
        patience=20,
        project=f"{DRIVE}/weights/experiments", name="M3")
```

#### M4 — Source pre-trained, **full fine-tune**

Same as M3 but `freeze=None` (or omit) and `lr0=3e-4`.

#### M5 — M3 + screenshot preprocessing

Add a Ultralytics pre-processing hook in `src/visclick/preprocess.py`:

```python
import cv2, numpy as np
def vc_preprocess(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    L = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(L)
    return cv2.cvtColor(cv2.merge([L,A,B]), cv2.COLOR_LAB2BGR)
```

Run a one-time pass over `data/desktop_labeled/images/` and write the processed set to `data/desktop_labeled_preproc/`. Then run M3 with `data=` pointing at the preprocessed yaml.

> **→ RECORD for `VisClick_Report_Data_Form.md` §3.1:** while preprocessing, save **3 representative before/after pairs** (e.g. one VS Code dark, one File Explorer light, one Notepad small-text) to `reports/figures/prep_<id>_before.png` / `_after.png`. Paste the six file paths into §3.1.

#### M6 — Pseudo-labelling (UDA-lite)

```python
# 1) take ~200 unlabelled extra desktop screenshots (Phase 3 leftovers)
# 2) run M3 on them, keep boxes with conf > 0.5 as pseudo-labels
# 3) merge with the 90 hand-labelled images and retrain M3 from M3's own checkpoint
```

Cite [L11] [L12] for the technique; explicitly say in the report: *"a single-round Mean-Teacher-lite, not the full DINO Teacher pipeline of Lavoie et al. 2025, due to compute constraints"*.

#### M7 — DINOv2 + linear-probe detection

This one is research-y; expect it to take a session to get running.

```colab
!pip install -q git+https://github.com/facebookresearch/dinov2
# Use a DINOv2-S backbone, freeze it, train a small detection head (e.g. a YOLO-style head).
# Reference: [L10]. Report mAP, training time, memory.
```

Keep it short. Even a partial result is a great report-paragraph: *"we explored DINOv2 as the backbone in line with 2024–25 trends; in our small-data regime it underperformed YOLOv8 fine-tuning by N%, at K× the training cost — therefore not selected"*.

#### M8 — Augmentation-only (no transfer)

Same as M0 but with `mosaic=1.0, mixup=0.2, hsv_h=0.015, hsv_s=0.7, hsv_v=0.4, flipud=0.5, fliplr=0.5` in train args.

### G.3 Result table to fill (`reports/tables/transfer_experiments.csv`)

| ID | Description | Train time (h) | mAP@.5 desktop | mAP@.5:.95 desktop | Latency ms (T4) | Latency ms (Win CPU, ONNX) |
|----|-------------|---------------|----------------|--------------------|------------------|----------------------------|
| M0 | scratch | … | … | … | … | … |
| M1 | COCO→desktop | … | … | … | … | … |
| M2 | source→desktop (head only) | … | … | … | … | … |
| M3 | source→desktop (light full) | … | … | … | … | … |
| M4 | source→desktop (full) | … | … | … | … | … |
| M5 | M3 + preprocessing | … | … | … | … | … |
| M6 | M3 + pseudo-labels | … | … | … | … | … |
| M7 | DINOv2 + linear head | … | … | … | … | … |
| M8 | M0 + heavy aug | … | … | … | … | … |

The **headline** model for the bot is whichever wins in mAP@.5 *and* fits into Windows-CPU latency (typically M3 or M5).

> **→ RECORD for `VisClick_Report_Data_Form.md` §4 (one row per method run):** for every model M0..M8 that you actually train, capture the seven numbers in the table above (train time, mAP@.5, mAP@.5:.95, T4 latency ms, Win-CPU ONNX latency ms, plus precision and recall from `model.val()`), the **hyperparameters used** (lr, batch, epochs, freeze depth — already in your `m.train(...)` call, just copy them), and the auto-saved training curve at `weights/experiments/M*/results.png`. Skipped methods: write `SKIPPED` in §4 and I will explain it in the report. Also pick which row is the headline and tell me in §5 of the form.

> **→ RECORD for `VisClick_Report_Data_Form.md` §6 (preprocessing ablation):** if you run both M3 and M5, just confirm the two mAP rows from §4 — I will derive the delta and write the paragraph.

### G.4 Export the headline model to ONNX for the bot

```colab
DRIVE = "/content/drive/MyDrive/visclick"
m = YOLO(f"{DRIVE}/weights/experiments/M3/weights/best.pt")
m.export(format="onnx", opset=12, simplify=True)
# saves best.onnx in the same folder
```

Then copy the `.onnx` from Drive down to your Windows machine (Drive desktop app, or download via the browser) and place it at `<REPO>\weights\visclick.onnx` so the bot in §H finds it. The `.onnx` should not be committed to GitHub (it is in the `.gitignore` of §B.1) — share via a tagged GitHub release or a Drive link.

> **→ RECORD for `VisClick_Report_Data_Form.md` §4 (model-size column) and §12:** `dir weights\visclick.onnx` for the file size in MB. Also note the `.pt` size for the headline run. These two numbers go into the `Model size (MB)` column of §4 and the artefact list in §12.

### G.5 Definition of done — Phase 5

- [ ] At least M0, M1, M3, M5 are trained and reported (M2/M4/M6/M7/M8 are nice-to-have for the discussion).
- [ ] `reports/tables/transfer_experiments.csv` is populated.
- [ ] Headline model exported to ONNX and copied locally.
- [ ] First draft of **Chapter 6.5 / 6.6 — Model design and training** of the report.
- [ ] First draft of **Chapter 8.2 — Quantitative evaluation** with the M-table as the centrepiece.

---

## Part H — Phase 6: End-to-end click-bot prototype (Week 8)

**Outcome:** running `python -m visclick.bot --instruction "click Save"` performs the click on a real Windows desktop.

### H.1 `capture.py` — screenshot the active monitor

```python
import mss, numpy as np
def grab():
    with mss.mss() as sct:
        m = sct.monitors[1]                        # primary monitor
        img = np.array(sct.grab(m))[:, :, :3][:, :, ::-1]  # BGRA -> RGB
    return img
```

### H.2 `detect.py` — load ONNX model, return boxes

```python
import onnxruntime as ort, numpy as np, cv2
class Detector:
    def __init__(self, onnx_path):
        self.sess = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
        self.input_name = self.sess.get_inputs()[0].name
    def predict(self, img_rgb, conf=0.3, iou=0.5):
        h, w = img_rgb.shape[:2]
        x = cv2.resize(img_rgb, (640, 640))
        x = x.transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        out = self.sess.run(None, {self.input_name: x})[0]
        # ultralytics ONNX export shape: (1, 84, 8400) for 80 classes; ours is (1, 10, 8400)
        # 10 = 4 box + 6 classes
        boxes = self.postprocess(out, w, h, conf, iou)
        return boxes  # list of (cls, xyxy, conf)
```

> **Tip:** Ultralytics also ships `model = YOLO("visclick.onnx")` which gives you a 1-line `model.predict(...)`; it runs onnxruntime under the hood. Use that for speed of development; only hand-code the postprocess if you need tight control.

### H.3 `ocr.py` — text per box

```python
import pytesseract, cv2, easyocr
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
_reader = None
def ocr_box(img_rgb, xyxy):
    x1,y1,x2,y2 = [int(v) for v in xyxy]
    crop = img_rgb[y1:y2, x1:x2]
    txt = pytesseract.image_to_string(crop, config="--psm 7").strip()
    if not txt:                                      # fallback for icons / small text
        global _reader
        _reader = _reader or easyocr.Reader(["en"], gpu=False)
        out = _reader.readtext(crop)
        txt = " ".join([o[1] for o in out])
    return txt
```

### H.4 `match.py` — instruction → best box

```python
from rapidfuzz import fuzz
def best_box(instruction, boxes_with_text, prefer_classes=None):
    target = instruction.lower().split()[-1]            # "click Save" -> "save"
    scored = []
    for cls, xyxy, conf, text in boxes_with_text:
        s = fuzz.partial_ratio(target, (text or "").lower())
        if prefer_classes and cls in prefer_classes:
            s += 10
        scored.append((s, cls, xyxy, conf, text))
    scored.sort(reverse=True, key=lambda t: t[0])
    return scored[0] if scored else None
```

For instructions like "*click the Save button*", parse the verb (`click`), the object (`Save`), and an optional class hint (`button`). A 50-line rule-based parser is enough for v1.

### H.5 `act.py` — actually click

```python
import pyautogui, time
pyautogui.FAILSAFE = True   # move mouse to a corner to abort
def click_xy(x, y, dwell=0.2):
    pyautogui.moveTo(x, y, duration=dwell)
    pyautogui.click()
def click_box(xyxy):
    x1,y1,x2,y2 = xyxy
    click_xy(int((x1+x2)/2), int((y1+y2)/2))
```

### H.6 `bot.py` — orchestrator

```python
import argparse
from visclick.capture import grab
from visclick.detect import Detector
from visclick.ocr import ocr_box
from visclick.match import best_box
from visclick.act import click_box

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instruction", required=True)
    ap.add_argument("--weights", default="weights/visclick.onnx")
    ap.add_argument("--dry-run", action="store_true", help="don't actually click")
    args = ap.parse_args()

    img = grab()
    det = Detector(args.weights)
    boxes = det.predict(img)
    boxes_with_text = [(cls, xyxy, conf, ocr_box(img, xyxy)) for cls, xyxy, conf in boxes]
    pick = best_box(args.instruction, boxes_with_text)
    if not pick:
        print("FAIL: no candidates"); return
    s, cls, xyxy, conf, text = pick
    print(f"PICKED cls={cls} text={text!r} conf={conf:.2f} score={s}")
    if not args.dry_run:
        click_box(xyxy)
```

### H.7 First-success checklist

Run the bot from the repo root:

```bash
python -m visclick.bot --instruction "click Save" --dry-run
```

Iterate until the printed pick is the correct widget on Notepad's Save dialog, **then** drop `--dry-run`. A "first end-to-end click" is a milestone worth screenshotting and putting in **Chapter 6.7 — Prototype** of the report.

> **→ RECORD for `VisClick_Report_Data_Form.md` §8 (prototype screenshots):** save **6 PNGs** under `reports/figures/proto_*.png` — startup, instruction entered, detection overlay, chosen element highlighted, after click, and one failure case. Paste the file paths into §8. Also write a 1-line note for any "this didn't work and I had to fix it" moment (e.g. ONNX shape mismatch, DPI scaling click offset, Tesseract path) into §8 — I will turn each line into a paragraph in Chapter 6.7.

### H.8 Definition of done — Phase 6

- [ ] `python -m visclick.bot --instruction "click Save"` works on a Notepad save dialog.
- [ ] Same call works on the Open dialog of File Explorer.
- [ ] Same call works on a "Save As" of VS Code.
- [ ] At least 5 instructions on Chrome's settings page (toggles, search box, "About Chrome" button) succeed.
- [ ] Demo-ready screenshots saved in `reports/figures/prototype/`.

---

## Part I — Phase 7: Evaluation, ablations, and SILC readiness (Weeks 9–12)

This is what becomes **Chapter 7 — Testing** and **Chapter 8 — Evaluation** in the report.

### I.1 Model testing (mirrors §8.1 of the scope doc)

For each headline model (M3 and M5):

| Test | Output → file |
|------|---------------|
| Per-class precision / recall / F1 on desktop test set | `reports/tables/desktop_classification_report.csv` |
| Confusion matrix on desktop test set | `reports/figures/desktop_confusion_matrix.png` |
| mAP@.5 and mAP@.5:.95 on desktop test set | `reports/tables/desktop_map.csv` |
| Same metrics on **UI-Vision** subset | `reports/tables/uivision_external.csv` ← *external generalisation evidence* |
| Latency: T4 (Colab) and Windows-CPU (ONNX) | `reports/tables/latency.csv` |
| **Preprocessing ablation** (M3 vs M5) | `reports/tables/preprocessing_ablation.csv` |

Generate them with `notebooks/05_eval_and_ablations.ipynb`. Use Ultralytics' built-in `model.val()` plus a small custom script for the UI-Vision split.

> **→ RECORD for `VisClick_Report_Data_Form.md`:**
> - §4 (per-class block of the headline model): `desktop_classification_report.csv` and `desktop_confusion_matrix.png` paths.
> - §6: the `preprocessing_ablation.csv` numbers (M3 vs M5 mAP).
> - §7: `uivision_external.csv` mAP@.5 if you run UI-Vision external generalisation. If skipped, write `SKIPPED` and I will note it as a limitation.

### I.2 Prototype testing — functional (FR-01 .. FR-06)

Define a fixed task suite with **15 instructions** in `tests/task_suite.yaml`, e.g.:

```yaml
- id: T01
  app: Notepad
  setup: open Notepad with text "hello"; choose Save As menu
  instruction: "click Save"
  expected_class: button
  expected_text: "Save"
- id: T02
  app: VS Code
  setup: dark theme, untitled file
  instruction: "click File menu"
- id: T03
  app: Chrome
  setup: settings → Privacy and security
  instruction: "click Clear browsing data"
# ... up to T15
```

`scripts/run_eval.py` iterates the suite, calls the bot, asks the human to confirm pass/fail (or compares the predicted box against a hand-marked ground-truth box), then writes:

| TC | FR | App | Instruction | Expected | Actual | Pass/Fail |
|----|----|-----|-------------|----------|--------|-----------|
| T01 | FR-04, FR-05 | Notepad | click Save | Save button | Save button | Pass |
| ... | | | | | | |

This table goes straight into Chapter 7.3.1 of the report.

The **Task Success Rate (TSR)** is the headline number: `passes / total`. Target ≥ 70%.

> **→ RECORD for `VisClick_Report_Data_Form.md` §9:** save the populated table (TC / FR / app / instruction / expected / actual / pass-fail) as `reports/tables/functional_tests.csv` and **also paste the rows directly into §9 of the form** so you do not have to send a separate file. I will compute TSR and the per-FR breakdown automatically.

### I.3 Prototype testing — non-functional (NFR-01 .. NFR-09)

Each NFR gets one Table 14-style entry like the example report:

```
Test ID:                   NFT-02
Unit:                      Performance
Non-Functional Req:        NFR-02
Description:               Inference + click latency under target
Expected Result:           latency_per_frame_ms < 200, mem < 2 GB
Actual Result:             ... measured ...
Status:                    Pass / Partial / Fail
```

Tools:

- Latency: time `bot.py` end-to-end over 20 instructions; write `reports/tables/nfr_performance.csv`.
- Memory: `psutil.Process().memory_info().rss` sampled every 0.5 s during a 5-minute soak; plot to `reports/figures/nfr_memory.png`.
- Reliability: 30-minute random-instruction soak; confirm 0 crashes; log to `reports/logs/soak.log`.
- Security: assert no `*.png` files left in temp after a run; cite in report.

> **→ RECORD for `VisClick_Report_Data_Form.md` §10:**
> - 20 latency values (just paste the column from `nfr_performance.csv`).
> - peak memory MB (read max value from psutil log).
> - soak duration in minutes + crash count.
> - count of `*.png` files left in the temp folder after a clean run (target = 0).
> - paths to `nfr_memory.png` and `soak.log`.

### I.4 Control study (mirrors §8.4 of the scope doc)

Final comparison table for the report — `reports/tables/control_study.csv`:

| Study | Domain | # imgs (target) | Detector | mAP@.5 | Notes |
|-------|--------|-----------------|----------|--------|-------|
| Bunian et al. 2021 (VINS) [L3] | Mobile | 4,800 | custom | **76.39%** | Mobile, no domain transfer |
| Salehi et al. 2024 [L8] | Mobile / generic | varies | YOLOv8s/m | up to ~84% | Larger, more uniform dataset |
| Roboflow YOLOv8s on web GUI (2026) | Web (~1k) | 1,000 | YOLOv8s | mAP@.5:.95 = 0.232 | Small dataset, similar regime to ours |
| UI-Vision agent baselines [L5] | **Desktop** | varies | various agents | low element grounding accuracy | Confirms the gap |
| **VisClick (this work)** | **Desktop**, transfer-learned | 90 | YOLOv8s (M3) | *X.XX* | **Headline result** |

If your number is below VINS that is fine — your dataset is 50× smaller and the domain is harder. The paragraph in Chapter 8 explains exactly that.

> **→ RECORD for `VisClick_Report_Data_Form.md` §11:** just confirm in §11 which model row from §4 is the one to plug into the **VisClick (this work)** row. You do not need to copy the prior-work numbers — they are constants and I keep them in the report.

### I.5 Qualitative evaluation

Ask **three** people for short written feedback after running the demo:

- one software engineer with ML background,
- one tester / QA engineer,
- one general user.

Capture verbatim quotes (with permission) into `reports/qualitative_feedback.md`. Goes into Chapter 8.3.

> **→ RECORD for `VisClick_Report_Data_Form.md`:** *not asked in the form.* If you want this section in the report, send `reports/qualitative_feedback.md` separately when you have it. Otherwise I will write Chapter 8.3 as a self-evaluation against the FRs/NFRs and explicitly state in the LIMITATIONS section of Chapter 9 that no third-party qualitative review was conducted.

### I.6 LEPSI write-up

Already collected through this doc — bring everything into Chapter 8.10 of the report:

- **Legal:** dataset licenses (MIT for UI-Vision; check RICO/CLAY/WebUI per their pages); UK DPA principles, GDPR; commercial-grade software disclaimers (this is a research prototype, not a deployed automation product).
- **Ethical:** no covert automation of others' systems; no PII in screenshots; honest reporting of failure modes (M0/M7/M8 results published even though they lose).
- **Professional:** Git history, tests, reproducible Colab notebooks, signed README.
- **Social:** lowering the QA-automation barrier helps engineers but can be misused; recommend human-in-the-loop for any safety-critical system.

### I.7 Demo video

- Record a continuous 60-second clip with OBS / ShareX of:
  1. Bot running on Notepad → Save (success).
  2. Bot running on Chrome settings → toggle (success).
  3. One *failure* case discussed honestly (icon misread by OCR).
- Save to `videos/demo.mp4`, also extract a thumbnail to `reports/figures/demo_thumb.png` for the SILC poster.

> **→ RECORD for `VisClick_Report_Data_Form.md` §12:** paste the path to `videos/demo.mp4` (or an unlisted YouTube URL if you upload it). Also drop the thumbnail path.

### I.8 Definition of done — Phase 7

- [ ] Every table in §I is populated.
- [ ] TSR computed over ≥10 tasks.
- [ ] UI-Vision external generalisation evaluated.
- [ ] Demo video recorded.
- [ ] Chapters 7 and 8 of the report are first-draft complete.

---

## Part J — Producing the MSc project report

The report follows the **same nine-chapter structure as the example RGU MSc report** so a marker recognises the shape immediately. This section maps every artefact you produced above to the chapter that needs it.

### J.1 Chapter map

| Chapter | What it contains | Where the content comes from |
|---------|------------------|------------------------------|
| **1. Introduction** | Background, problem statement, aim, RQs, gap, objectives, scope, summary | §A and §2 of scope doc |
| **2. Literature Review** | Datasets, prior detectors, transfer learning, mobile/web/desktop GUI work, gap positioning | §C.1 reading list + `reports/literature_table.csv` |
| **3. Requirement Analysis** | Stakeholders (onion), use cases (UC-01..06), functional reqs (FR-01..06), non-functional reqs (NFR-01..09), datasets selection | §3 of scope doc + §C.2 |
| **4. Project Management** | Research methodology (deductive), software design (data-flow), software development (prototype model), Kanban, risk register, Gantt | §6 of scope doc + §10 of scope doc |
| **5. Design** | Three-tier architecture, data-flow diagrams (training + runtime), block diagram, class diagram, flow chart, wireframes | §4 of scope doc — already drawn in the SVGs you have |
| **6. Implementation** | Tools (Python, Ultralytics, Colab), datasets (RICO, CLAY, VINS, WebUI, UI-Vision, Unified bundle), preprocessing, model design, model training (M0..M8), prototype build | §B, §C, §D, §G, §H of this doc |
| **7. Testing** | Model testing (per-class, confusion matrix, mAP, latency); functional test cases T01..T15; non-functional NFT entries | §I.1, §I.2, §I.3 of this doc |
| **8. Evaluation** | Quantitative (control study), qualitative (3 reviewers), achievement of aim/RQs/objectives/FRs/NFRs, LEPSI | §I.4, §I.5, §I.6 of this doc |
| **9. Conclusion** | Challenges, learning outcomes, contributions (research + technical), limitations, future work | Personal reflection + §G results |

### J.2 Suggested chapter sizes (approx, for a ~120-page report like the example)

| Chapter | Pages | Notes |
|---------|-------|-------|
| 1 | 6 | One page per sub-section |
| 2 | 8–10 | Heavy: VINS, RICO/CLAY, WebUI, UI-Vision, YOLO comparisons, UDA techniques |
| 3 | 10 | Onion model + UC + FR + NFR tables |
| 4 | 6 | Methodologies + risk + Gantt |
| 5 | 6 | Diagrams + short text |
| 6 | 25–30 | The thickest chapter; covers all M0..M8 |
| 7 | 12–15 | Test tables + figures |
| 8 | 8–10 | Control study + LEPSI |
| 9 | 4–6 | Reflection + future work |
| Refs + Appendix | 8–12 | Plus a Kanban screenshot in the appendix like the example |

### J.3 Templates to produce while implementing

- `reports/figures/` → at least 30 figures (training curves, confusion matrices, predictions, GUI screenshots).
- `reports/tables/` → at least 12 tables (literature, source-domain results, M-table, FR/NFR evaluation, control study, latency, ablations).
- A Word / LaTeX skeleton mirroring the chapters above — populate as soon as Phase 1 finishes (do not wait for Phase 7).

### J.4 Submission cadence

Write **every chapter as a draft as soon as the underlying phase is done**:

| Chapter | Drafted by end of |
|---------|-------------------|
| 1, 2 | Week 2 |
| 3, 4 | Week 4 |
| 5 | Week 5 |
| 6 | Week 8 |
| 7, 8 | Week 11 |
| 9 + final pass | Week 12 |

This is the same cadence the example report's Gantt chart shows (Sept–Apr in their case, scaled to your 12-week sprint). Late writing is the single biggest reason these projects miss deadlines.

---

## Part L — Post-prototype roadmap (added 5 May 2026 after the first live demo)

After the 5 May 2026 live-demo session (logged in `docs/VisClick_Report_Data_Form.md` §8.6), the project has a working prototype but several dissertation-required entries are still `[FILL]`. This part is the **single source of truth** for everything left to do — every step is a checkbox you can tick (`- [ ]` → `- [x]`) as it is completed, and every commit that closes a step should reference its ID (e.g. `Phase 1.B.2: M1 trained and evaluated`).

### Two design rules for this roadmap

1. **Track per step, commit per step.** Each step below is a checkbox. Each one should produce one or more commits; the commit message should name the step ID (e.g. `Phase 1.A.1: hand-corrected 8 desktop test images`).
2. **"Adopt if better" rule.** Any time a comparison method (Phase 1.C) or alternative approach (Phase 4) **beats the current headline by ≥ 3 pp on TSR or ≥ 5 pp on mAP@.5 with no major regression elsewhere**, the dissertation honestly switches to that as the headline. We are not married to YOLOv8s. The dissertation is stronger if "I tried X, Y, Z, and Y won" than if "I picked one and called it the headline".

### Status overview

- [ ] **Phase 1** — Comparison study + defensible numbers (~3–4 h). MANDATORY.
- [ ] **Phase 2** — Live prototype evidence (~2 h). MANDATORY.
- [ ] **Phase 3** — Demo video (~1 h). MANDATORY.
- [ ] **Phase 4** — Better element coverage for icon-only / dropdown clickables (day-long). OPTIONAL.

---

### L.1 — Phase 1: Comparison study + defensible numbers (~3–4 h, urgent)

The original "Option A" (just ablate M1 / M2) is too narrow. To defend the headline approach in the dissertation, Phase 1 is broadened into a proper **comparison study** that runs ML ablations *and* classical baselines on the **same hand-corrected test set**. After Phase 1 we have a single comparison table that says *"here is what every reasonable alternative scores; here is why we picked this one"*.

#### L.1.A — Test-set hardening (~45 min, **prerequisite for everything else in Phase 1**)

- [x] **1.A.1** Hand-correct the 8 desktop test images in Roboflow. Open `data/desktop_finetune/images/test/`, fix wrong boxes, add missing boxes (especially Save / Cancel / OK / dropdowns the auto-labeler missed), keep the 6-class taxonomy. Export YOLO labels back to `data/desktop_finetune/labels/test/`. ~30 min. **DONE 6 May 2026 → 356 boxes total (button 15 / text 33 / text_input 10 / icon 189 / menu 89 / checkbox 20). Roboflow export at `datasets/handcorrected_desktop_test/visclick3.yolov8.zip`.**
- [x] **1.A.2** Verify exports: count files, check at least one label file by hand, count instances per class in the test split, paste counts into report §4.6c. ~15 min. **DONE 6 May 2026 → counts CSV at `<DRIVE>/reports/tables/desktop_test_handcorrected.csv`; rebuilt `desktop_finetune_bundles/test.tar.gz`; original auto-labels backed up to `test_autolabels.tar.gz`.**

**Deliverable:** a hand-corrected 8-image test split with ~30–40 real-GT boxes across the 6 classes. Every other Phase-1 evaluation runs on this set.

#### L.1.B — ML transfer-learning ablations (~1.5 h on Colab T4)

All four runs use **the same hand-corrected test split** so rows are directly comparable.

- [x] **1.B.1** **M0 — YOLOv8n trained from scratch on the 50 desktop images.** No transfer learning. ~50 epochs, batch=8, `imgsz=640`. **DONE May 6, 2026: mAP@.5 = 0.0000 (collapsed to zero — random init on 50 images detects nothing on the hand-corrected test set; P = R = 0). This is the cleanest empirical proof that transfer is mandatory.**
- [x] **1.B.2** **M1 — YOLOv8s with COCO weights → fine-tuned on desktop.** Standard "off-the-shelf" transfer. `freeze=None`, 30 epochs, AdamW `lr0=0.001`, cos_lr. **DONE May 6, 2026: mAP@.5 = 0.0390, mAP@.5:.95 = 0.0226, P = 0.024, R = 0.233 (highest recall of any contender, lowest precision).**
- [x] **1.B.3** **M2 — YOLOv8s source-pretrained → desktop, head-only `freeze=22`.** Same recipe as M3 but only the head trains. **DONE May 6, 2026: mAP@.5 = 0.0277, mAP@.5:.95 = 0.0160, P = 0.541 (highest precision of any contender), R = 0.047.**
- [x] **1.B.4** **M3 — current headline (already trained).** Re-ran `model.val(split='test')` on hand-corrected test set. **DONE May 6, 2026: mAP@.5 = 0.0330 (collapsed 22× from 0.7176 against auto-labels — see Report §13 O19), P = 0.389, R = 0.047.**
- [x] **1.B.5** Updated report §4.1 with rows for **Src no FT**, **M0**, **M1**, **M2**, **M3** — all on the same hand-corrected test set, identical `model.val()` call. M4/M5/M6/M7/M8 marked `SKIPPED` (Phase 1.B + Phase 1.C is the agreed comparison study; further ML variants would not change the recall ceiling identified in O19). **DONE May 6, 2026.**
- [x] **Adopt-if-better outcome:** no contender beats M3 by ≥ 3 pp mAP@.5 (the spread is < 1.5 pp); **headline stays M3**. The honest headline number is now **mAP@.5 = 0.0319 on hand-corrected GT** (not 0.7176 on auto-labels). See Report §13 O19 for full interpretation; core finding is that the recall ceiling is set by the source-domain backbone, not the head.

**Notebook to author:** `notebooks/08_phase1_ablations.ipynb`. Single cell per method, all writing into `tables/transfer_experiments.csv` and saving `runs/M*/` artefacts to Drive.

**Adopt-if-better trigger:** if M1 ≥ M3 + 3 pp mAP@.5 OR M2 ≥ M3 + 3 pp, the dissertation switches headline to that method. (Unlikely but possible.)

#### L.1.C — Classical / non-ML baselines (~1.5 h, local Windows)

This is the **single most important addition** to the original plan. To defend "we used a deep object-detection approach", we need to demonstrate that simpler approaches are worse on our task. SikuliX [L15] is cited in the literature review precisely so we can compare against its template-matching idea here.

Each baseline runs as a standalone CLI script that takes the **same instruction set** (T01–T20 from §9) and reports a TSR (Task Success Rate). If a baseline beats VisClick in TSR, the dissertation honestly says so.

- [ ] **1.C.1** **`scripts/baseline_template.py` — SikuliX-style template matching.** Capture reference PNGs of common Windows 11 / Chrome / VS Code controls (Save, Cancel, OK, search icon, address bar) into `samples/templates/`. The script does `cv2.matchTemplate(screenshot, template, TM_CCOEFF_NORMED)` for each named template, picks the best match if score > 0.7, clicks. *Expected: very high precision when the template matches exactly (same theme, same DPI), zero recall when the UI changes (dark mode, different scale, anti-aliasing).* ~1 h to write + capture references.
- [ ] **1.C.2** **`scripts/baseline_ocr_only.py` — OCR-only.** No detection model at all. Run EasyOCR (or Tesseract) on the full screenshot, find the word matching the instruction's target via `rapidfuzz.partial_ratio`, click its bounding box centre. *Expected: succeeds on text-labeled buttons (Save, Cancel), fails completely on icon-only clickables (close X, settings cog, dropdown arrow). This is essentially "VisClick without the YOLO step".* ~30 min.
- [ ] **1.C.3** **`scripts/baseline_pywinauto.py` — accessibility-tree.** Uses `pywinauto.Desktop().connect(active_only=True).find_element(name='Save')` to locate controls via the Windows accessibility API. *Expected: works on native Win32 dialogs (Notepad Save As, File Explorer), fails on Chrome / VS Code which have partial accessibility, fails completely on Electron apps that don't expose UIA. Demonstrates "if accessibility worked, we wouldn't need ML — but it doesn't".* ~30 min. **Optional**: skip if Windows accessibility is awkward.

**Each baseline produces:** a CSV row in `tables/baseline_results.csv` with columns: `method`, `T01..T20` (✓/✗), `TSR`, `latency_p50_ms`, `dependencies` (one line), `lines_of_code`.

**Adopt-if-better trigger:** if any baseline TSR > VisClick TSR on the 20 cases, the dissertation switches the headline. (Almost certainly won't happen, but the test must be honest.)

#### L.1.D — Cross-method comparison table + bar chart (~30 min)

- [ ] **1.D.1** Aggregate `tables/transfer_experiments.csv` (ML methods) and `tables/baseline_results.csv` (classical) into a single `tables/method_comparison.csv` with rows: `M0, M1, M2, M3, baseline_template, baseline_ocr_only, baseline_pywinauto, VisClick_full_pipeline`. Columns: `mAP@.5_test`, `TSR_T01_T20`, `latency_p50_ms`, `lines_of_code`, `external_dependencies`.
- [ ] **1.D.2** One-figure summary: bar chart of TSR per method, saved to `figures/method_comparison_tsr.png` and a second bar chart of mAP@.5 saved to `figures/method_comparison_map.png`. Goes into report §4.1 / §6.
- [ ] **1.D.3** Write 1–2 sentences in report §13 (new observation **O17**) explaining why VisClick wins (or, if a baseline won, why we adopted it).

#### L.1.E — Honest skipping (~10 min)

- [ ] **1.E.1** In report §4.1, mark each of M4 / M5 / M6 / M7 / M8 as `SKIPPED` with a one-line reason. Acceptable per detailed-plan §G.0 because the report can say *"we tried these other methods, here are the numbers, here is why we did not pick them as the headline approach"*.

**After Phase 1:** §4.1 has 5 ML rows + 3 classical-baseline rows + 5 honest `SKIPPED` rows = 13 rows total, all eval'd on the same 8-image hand-corrected test set or T01–T20 cases. **Chapter 6 (Implementation) and Chapter 7 (Evaluation) both have a defensible quantitative spine.**

---

### L.2 — Phase 2: Live prototype evidence (~2 h)

Phase 2 only starts once Phase 1.A (test-set hardening) and Phase 1.C (baselines) are done — the same T01–T20 cases drive both.

- [ ] **2.1** Run the 20 functional test cases T01–T20 in report §9 with the **VisClick full pipeline**. For each: launch `python -m visclick`, type instruction, observe pass/fail, paste the predicted element + path to `screenshots/last_overlay.png`. ~1 h.
- [ ] **2.2** Run the same 20 cases with each Phase-1.C baseline (template / ocr-only / pywinauto). Record into `tables/baseline_results.csv`. ~30 min if scripts are working.
- [ ] **2.3** Latency NFR (report §10.1): write `scripts/run_nfr.py` — a CLI loop that runs 20 representative instructions with `--image` so it's deterministic. Dump wall-times to `tables/nfr_performance.csv`. ~30 min.
- [ ] **2.4** Six prototype screenshots for report §8.1 (terminal showing command / captured screen / overlay with all boxes / picked element highlighted / after-click result / honest failure case). Drag them into `figures/`. ~20 min.
- [ ] **2.5** (Optional) Three before/after preprocessing pairs (report §3.1) — only needed if M5 is kept alive in Phase 1. Otherwise mark §3.1 as not applicable. ~15 min.

**After Phase 2:** §8, §9, §10 are populated; both VisClick and the baselines have TSR numbers on the same 20 cases. **Chapter 7 (Evaluation) writes itself.**

---

### L.3 — Phase 3: Demo video (~1 h)

§12 of the data form requires a demo video.

- [ ] **3.1** Storyboard: 6–8 representative tasks. Recommended sequence: (a) open GUI; (b) `click Save` on Notepad Save-As → success; (c) switch to Chrome → `click address bar` → success; (d) switch to VS Code → `click Search` → success or graceful failure with overlay shown; (e) refusal case: `click Save` on a blank desktop → bot prints `FAIL: cannot find 'save'`; (f) manual `xy 1234 567` fallback → success. ~10 min planning.
- [ ] **3.2** Tooling check: OBS Studio (free, full screen capture, no watermark) installed and configured for 1080p / 30 fps; or Windows Game Bar as fallback. ~10 min.
- [ ] **3.3** Single-take recording (run through storyboard once with the GUI). Re-record only on hard errors. ~20 min.
- [ ] **3.4** Light edit: trim head/tail, add 4 title cards (Capture / Detect / Match / Click) at the corresponding moments. Export at 720p–1080p MP4. ~15 min.
- [ ] **3.5** Upload to YouTube unlisted. Paste link into report §12. ~5 min.

---

### L.4 — Phase 4: Better element coverage (optional, day-long)

This is the "dropdowns and icon-only buttons" thread. **Honest framing for the dissertation:** §8.4 already documents this limitation as a deliberate scope decision aligned with UIED [L3], Apple Screen Recognition [L5], and ScreenAI [L10]. So Phase 4 is *not* required to defend the thesis; it is a quality lever.

- [ ] **4.A** **Class-specific conf thresholds.** Add a per-class threshold dict to `detect.py::Detector.predict` (e.g. `icon` at 0.10, `menu` at 0.15, others at 0.25). Re-run §9 functional tests. *Expected: +5–15 pp recall on icon class; some precision drop.* ~15 min.
- [ ] **4.B** **Hand-add icon-only boxes.** In Roboflow, open the existing 50 desktop seeds and ADD bounding boxes for close X, settings cog, dropdown arrows (▼ / `^v`), minimise, app-bar icons, breadcrumb chevrons. Don't touch existing auto-labels. Re-fine-tune for 30 more epochs from `best_desktop_v8s.pt`. ~3–4 h.
- [ ] **4.C** **UI-Vision external test.** [L5 in `reports/literature_table.csv`]. Use it as test-only: `model.val(data=ui_vision_data.yaml)` on the desktop fine-tune. Numbers feed report §7. ~4–5 h. **Strong external-generalisation evidence.**
- [ ] **4.D** **Icon-classifier ensemble** (e.g. UIED-style hybrid). Day+. **Not recommended** unless aiming for distinction.

**Recommended Phase-4 order if pursued:** 4A first (cheap, instantly informs whether 4B is worth doing), then 4B if recall gains in 4A look real, then 4C for external evidence. Skip 4D unless you have a free week.

---

### L.5 — Recommended overall order

```
Today + tomorrow   → Phase 1 (3–4 h, mandatory)
Day after          → Phase 2 (2 h, mandatory)
Same day or next   → Phase 3 (1 h, mandatory)
If time / ambition → Phase 4.A (15 min) + Phase 4.B (half day) + Phase 4.C (half day)
```

Mandatory work (Phases 1–3) = ~6–7 h spread over a few days. Phases 1.C and 4 are the dissertation-quality multipliers — the more of them done well, the stronger the comparative evaluation chapter.

### L.6 — How to use this roadmap with git

- Each Phase-1.x.y / 2.x / 3.x / 4.x checkbox is a unit of work. When it's done, edit this document, change `- [ ]` to `- [x]`, and commit with a message like `Phase 1.A.1: hand-corrected 8 desktop test images`.
- After every couple of completed steps, sync the working copy from `gui_temp/VisClick_Detailed_Plan.md` into `docs/VisClick_Detailed_Plan.md` and push so the GitHub copy reflects current progress.
- The same checkboxes are mirrored in `docs/VisClick_Report_Data_Form.md` §13.1 for at-a-glance status; keep both copies in sync.

---

## Part K — Appendices (cheat-sheet, troubleshooting, costs)

### K.1 Command cheat-sheet

```bash
# Local (Windows)
.venv\Scripts\activate
python -m visclick.bot --instruction "click Save" --dry-run
python scripts/capture_screenshots.py
python scripts/run_eval.py --suite tests/task_suite.yaml

# Colab (after the standard first cell from §B.2 step 5; cwd is /content/visclick, DRIVE=/content/drive/MyDrive/visclick)
!nvidia-smi
yolo detect train data=configs/yolo_source.yaml model=yolov8s.pt epochs=30 imgsz=640 batch=16 project=$DRIVE/weights/baseline_source name=run1
yolo detect val   data=configs/yolo_desktop_finetune.yaml model=$DRIVE/weights/experiments/M3/weights/best.pt
yolo export       model=$DRIVE/weights/experiments/M3/weights/best.pt format=onnx opset=12 simplify=true
```

### K.2 Trouble-shooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Colab disconnects mid-train | Free tier idle / 12h limit | Add `resume=True`; train in 2 halves; save `last.pt` to Drive every epoch |
| Out of memory in YOLOv8 train | Batch too big | Drop `batch` to 8 or 4; use `imgsz=512` |
| ONNX outputs wrong shape | Mismatch in `nc` | Re-export from a checkpoint trained with the right `data.yaml` |
| Tesseract returns empty | Crop too small or low-contrast | Pad crop by 4 px each side; binarise crop with `cv2.adaptiveThreshold` before OCR; fall back to EasyOCR |
| PyAutoGUI clicks the wrong place on a high-DPI monitor | DPI scaling | Set `pyautogui.FAILSAFE=True`; verify with the script in §B.3; if still off, capture and click both in *physical* coordinates using `mss.monitors[1]` |
| F9 hotkey not detected | Need admin | Re-run terminal as Administrator |
| CVAT export missing `.txt` for empty images | Filter setting | Tick "include negatives" in the export dialog |
| Drive runs out of space | Datasets are big | Keep raw zips outside Drive; only the extracted form needed for training |
| Pseudo-labels collapse a class | Confidence threshold too low | Raise to ≥0.5; require ≥3 boxes per class before adding pseudo-labelled image |

### K.3 Costs and time accounting

| Item | Cost | Why |
|------|------|-----|
| Google account / Colab Free | £0 | Used for training |
| GitHub | £0 | Free private repo |
| Google Drive 15 GB | £0 | Should fit datasets if WebUI is kept to the 7k split |
| CVAT cloud | £0 | Free tier; 10 GB |
| Zotero | £0 | Reference manager |
| OBS Studio | £0 | Demo video |
| Tesseract / EasyOCR / PaddleOCR | £0 | OCR |
| Optional Colab Pro upgrade | ~£10/month | Only if you hit T4 quota; not required |

Time budget on 2 days/week × ~5 h × 12 weeks = ~120 h.

| Phase | Hours |
|-------|-------|
| 0 setup | 6 |
| 1 lit + data | 18 |
| 2 source train | 16 |
| 3 capture | 4 |
| 4 annotate | 14 |
| 5 experiments | 22 |
| 6 bot | 16 |
| 7 eval + report | 24 |
| **Total** | **120** |

### K.4 What to do if you fall behind

If you are 2 weeks late at any point, **drop in this order**:

1. M7 (DINOv2 path).
2. M6 (pseudo-labelling).
3. UI-Vision external evaluation (keep desktop test set only).
4. Soak / stress reliability test (note "limited stress testing performed" in NFR-06).

Do **not** drop M3, M5, the M-table, the TSR suite, or the demo video. Those are the report's spine.

### K.5 Final hand-off checklist

Before submission day:

- [ ] All weights in Drive **and** in a tagged Git release.
- [ ] All notebooks re-runnable end-to-end with a fresh runtime.
- [ ] All datasets accessible (link or local zip referenced in README).
- [ ] Report PDF compiled, references checked, page count sane.
- [ ] Demo video uploaded (private YouTube link or attached MP4).
- [ ] Public README explains how to reproduce the headline number in ≤5 commands.

---

*This detailed plan is a sibling of `VisClick_3_Month_Plan.md`. Update it as soon as upstream URLs move or compute environments change. Treat it as living documentation; commit changes to Git so reviewers can see how the plan evolved alongside the work.*
