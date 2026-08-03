VisClick - Large data bundle for RGU OneDrive
Student: Hiran Abeywardhana (RGU 2425488)

Upload this folder to RGU OneDrive and share a link with "people with link can view"
(or grant access to markers). Paste that link into SUBMISSION_README.md Section 4
before you submit the code zip to Moodle.

Suggested folder name on OneDrive:
  VisClick_LargeData_2425488

Suggested contents (upload what you have):

  weights/
    best_source_v8s.pt          - YOLOv8s source-trained checkpoint (~22 MB)
    uda_at/ ...                 - Adaptive Teacher runs (optional)
    uda_shot/ ...               - SHOT runs (optional)
    ssp_few_shot/ ...           - SSP+FT runs (optional)

  data/ (optional - very large)
    unified/                    - Zenodo unified mobile bundle (if not re-downloadable)
    desktop_unlabeled/          - ~1600 unlabelled desktop screenshots (if kept locally)

  README.txt                    - copy of this file

If a file is missing, markers can still run the Windows prototype using only
weights/visclick.onnx inside the Moodle code zip.

Public download alternatives (no OneDrive needed for these):

  RICO:     https://interactionmining.org/rico
  Zenodo:   https://zenodo.org/records/19195885
  ScreenSpot: loaded at runtime via HuggingFace datasets in scripts/run_cpv_screenspot.py

OneDrive share link (fill in before submission):
  [PASTE LINK HERE]
