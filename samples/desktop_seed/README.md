# Desktop seed screenshots

50 personal screenshots used to fine-tune the source-baseline YOLOv8s into the
desktop domain (§E of `VisClick_Detailed_Plan.md`). 48 PNG + 2 JPG, ~16 MB.

Content: VS Code (light/dark themes, Explorer, Extensions panel, Problems pane),
Microsoft Excel (full ribbon — Formulas/Insert/Home tabs), and Google Chrome.

These are tracked in git intentionally (the project's `data/` is `.gitignore`d for
large generated datasets like RICO and the Zenodo unified bundle). At ~16 MB they
are small enough to version, and pinning them is essential for the desktop
fine-tune to be reproducible from a fresh clone.

## How they are consumed

`notebooks/06_finetune_desktop.ipynb` (cell 6.1) reads from
`<DRIVE>/data/desktop/raw/`. If that folder is empty on a fresh Colab session,
the notebook **auto-seeds it by copying these 50 files from the cloned repo**.
You can also drop additional desktop screenshots into Drive at the same path
and they will be auto-labelled and folded into the dataset on the next run.

## Labels

Labels are **not** committed — they are auto-generated at notebook runtime by
the source-baseline teacher (`best_source_v8s.pt`) and persisted to
`<DRIVE>/data/desktop/labels/` and the Drive bundles.

If you hand-correct any label files in Roboflow, drop the corrected `.txt`s
into `samples/desktop_seed_labels/` (create the folder) and we can later make
the notebook prefer those over the pseudo-labels.
