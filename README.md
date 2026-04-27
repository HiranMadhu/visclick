# VisClick

Vision-based GUI element detection and click automation for desktop applications using transfer learning (YOLOv8, mobile/web UI pre-training, Windows desktop fine-tune).

- **Code & notebooks:** this repository  
- **Datasets & trained weights:** Google Drive (see project plan)  
- **Runtime:** Google Colab (GPU) for training; Windows for the click-bot demo  

Full methodology: `VisClick_Detailed_Plan.md` in the project docs (sibling folder if you use the monorepo layout).

## Run the notebooks in Colab (no local install required)

| Notebook | Open in Colab |
|----------|---------------|
| 00 — Data acquisition | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HiranMadhu/visclick/blob/main/notebooks/00_data_acquisition.ipynb) |
| 01 — EDA | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HiranMadhu/visclick/blob/main/notebooks/01_data_eda.ipynb) |
| 02 — Train source | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HiranMadhu/visclick/blob/main/notebooks/02_train_source.ipynb) |
| 03 — Fine-tune desktop | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HiranMadhu/visclick/blob/main/notebooks/03_finetune_desktop.ipynb) |
| 04 — Transfer experiments | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HiranMadhu/visclick/blob/main/notebooks/04_experiments_transfer.ipynb) |
| 05 — Eval & ablations | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HiranMadhu/visclick/blob/main/notebooks/05_eval_and_ablations.ipynb) |

## Local setup (Windows, click-bot)

```bash
python -m venv .venv
.venv\Scripts\activate   # or source .venv/bin/activate on Linux
pip install -r requirements.txt
# Install Tesseract OCR for pytesseract (see https://github.com/UB-Mannheim/tesseract/wiki)
python -m visclick.bot --instruction "click Save" --dry-run
```

## Layout

| Path | Purpose |
|------|---------|
| `src/visclick/` | Library: capture, detect, OCR, match, act, bot |
| `notebooks/` | Colab notebooks (00–05) |
| `configs/` | YOLO `data.yaml` and `classes.txt` (paths point at Drive after you mount) |
| `scripts/` | CLI helpers: capture, CVAT export, eval suite |
| `tests/` | Unit tests |
| `reports/figures` , `reports/tables` | Figures and CSVs for the project report (git-tracked) |

## Push to personal GitHub (when your PC defaults to a company account)

This clone is configured so HTTPS uses the **HiranMadhu** username:

- `credential.https://github.com.username=HiranMadhu`
- `remote.origin.url=https://HiranMadhu@github.com/HiranMadhu/visclick.git`

**Option A — one-shot push with a personal PAT** (does not store the token in Git config):

1. Create a token: [GitHub → Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens) (enable **repo**).
2. In a terminal (bash / Git Bash / WSL):

```bash
export GH_TOKEN=ghp_your_token_here
bash scripts/push_personal.sh
```

**Option B — Windows Credential Manager:** remove any saved `github.com` entry, then `git push`; when prompted, sign in with the **personal** account (or paste the PAT as the password).

**Option C — SSH second key:** add a key to your personal GitHub, then `git remote set-url origin git@github.com-personal:HiranMadhu/visclick.git` with a `~/.ssh/config` host alias (see GitHub docs for multiple accounts).

## License

See repository settings on GitHub; default is all-rights reserved unless a `LICENSE` file is added.
