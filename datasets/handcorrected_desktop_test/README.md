# Hand-corrected desktop **test** split (Roboflow YOLOv8 export)

This folder holds the **8-image test-set** labels after manual correction in Roboflow (Phase 1.A).

| File | Contents |
|------|----------|
| `visclick3.yolov8.zip` | Roboflow export: `train/images/` + `train/labels/` (8 PNGs + 8 YOLO `.txt`) + `data.yaml`. Roboflow names the split `train/` even though these are our **test** images — `notebooks/08_phase1A_handlabel.ipynb` Section 4 remaps them into `desktop_finetune/labels/test/`. |

**Size:** ~2.5 MB — small enough to live in git so Colab can `git pull` without hunting Drive.

**Sync to Google Drive** (so notebook `08_phase1A_handlabel.ipynb` cell 9 finds `desktop_test_handcorrected.zip`):

```bash
# From repo root, after git pull:
python scripts/sync_handcorrected_zip_to_drive.py
```

Or set the destination explicitly:

```bash
python scripts/sync_handcorrected_zip_to_drive.py --dest "/content/drive/MyDrive/visclick/data"
```

On Windows with Drive for Desktop, `--dest` might be like:

```text
"C:\Users\<you>\Google Drive\My Drive\visclick\data"
```

See `scripts/sync_handcorrected_zip_to_drive.py --help`.
