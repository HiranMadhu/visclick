# Figures 1-16 — what to use and where it comes from

For each figure already cited in `Final_Report_v2*.md`, this document gives you:

1. **Status** — `READY` (I produced it), `FETCH` (you download / screenshot it), or `MIXED` (I produced one option, you can also use a real image).
2. **Use this file** — the path to drop into Word.
3. **Where to insert** — which `[FIGURE N: ...]` placeholder block to replace and in which markdown file.
4. **Caption** — the exact caption to leave under the image after deleting the placeholder.

I rendered every SVG to PNG at 150 DPI. Word imports either format; PNG is the safest. Files are in `docs/figures/`.

---

## Quick map

| # | Status | File to use | In which markdown |
|---:|---|---|---|
| 1  | FETCH (you screenshot) | n/a — see Section 1 below | `Final_Report_v2.md` |
| 2  | READY | `docs/figures/figure_02_positioning_grid.png` | `Final_Report_v2.md` |
| 3  | READY | `docs/figures/figure_03_solution_overview.png` | `Final_Report_v2.md` |
| 4  | FETCH (paper image) | n/a — see Section 4 below | `Final_Report_v2.md` |
| 5  | READY | `docs/figures/figure_05_classical_baselines_grid.png` | `Final_Report_v2.md` |
| 6  | READY | `docs/figures/figure_06_modular_vs_e2e.png` | `Final_Report_v2.md` |
| 7  | READY | `docs/figures/figure_07_use_case_diagram.png` | `Final_Report_v2.md` |
| 8  | READY | `docs/figures/figure_08_gantt.png` | `Final_Report_v2.md` |
| 9  | READY | `docs/figures/figure_09_block_diagram.png` | `Final_Report_v2.md` |
| 10 | READY | `docs/figures/figure_10_process_flowchart.png` | `Final_Report_v2.md` |
| 11 | MIXED | `docs/figures/figure_11_gui_wireframe.png` (or your real `proto_2_captured.png`) | `Final_Report_v2.md` |
| 12 | READY | `docs/figures/figure_12_repo_tree.png` | `Final_Report_v2.md` |
| 13 | READY | `docs/figures/figure_13_source_backbone.png` | `Final_Report_v2_part2.md` |
| 14 | READY | `docs/figures/figure_14_sample_efficiency.png` | `Final_Report_v2_part2.md` |
| 15 | READY | `docs/figures/figure_15_all_methods_screenspot.png` | `Final_Report_v2_part2.md` |
| 16 | READY | `docs/figures/figure_16_screenspot_by_slice.png` | `Final_Report_v2_part2.md` |

13 of 16 done. Two require external screenshots (Figures 1, 4) and you'll see why below.

---

## Per-figure detail

### Figure 1 — FETCH (mobile-to-desktop shift)
**Why fetch?** Three real screenshots that have to be from real apps; cannot be drawn.
**How to make it.**
- Panel A (mobile): `https://github.com/google-research-datasets/clay` shows annotated CLAY screens — pick any clean portrait one and screenshot it.
- Panel B (classic Win32): open Windows File Explorer → screenshot.
- Panel C (modern Win11 WinUI 3): in Notepad, File → Save As → screenshot the dialog. Or Settings → Bluetooth & Devices → screenshot.
- Stitch the three side-by-side in PowerPoint, paint.net, or Word's "Insert → Picture" with three columns. Save as `reports/figures/ch1_domain_shift_examples.png`.

**Insert location.** In `docs/Final_Report_v2.md`, replace the existing block on lines **31-33** (the one that begins `[FIGURE 1: Examples of the mobile-to-desktop shift.`).

**Final caption to leave under the image.**
> Figure 1: Three axes of the mobile-to-desktop shift. Left, a mobile portrait UI from CLAY. Centre, a classic landscape desktop with a packed toolbar. Right, a modern Win11 WinUI 3 dialog with flat, theme-dependent controls.

---

### Figure 2 — READY (positioning grid)
**File.** `docs/figures/figure_02_positioning_grid.png`

**Insert location.** `Final_Report_v2.md`, replace the placeholder block on lines **68-70**.

**Caption.**
> Figure 2: Where the proposed framework sits relative to existing GUI automation approaches. Classical image-based and accessibility-tree tools sit in the lightweight-but-brittle corner; large vision-language models sit in the heavyweight-but-tolerant corner; this project targets the middle.

---

### Figure 3 — READY (solution overview)
**File.** `docs/figures/figure_03_solution_overview.png`

**Insert location.** `Final_Report_v2.md`, replace the placeholder block on lines **152-154**.

**Caption.**
> Figure 3: End-to-end shape of the proposed solution. A mobile-pretrained detector is adapted to desktop using one of three methods and then wrapped inside the IVGocr-style instruction-to-action pipeline that constitutes the deliverable prototype.

---

### Figure 4 — FETCH (RICO vs CLAY)
**Why fetch?** Real labelled screens from the CLAY paper.
**How to make it.**
- The CLAY paper itself: Li et al. (2022a) "Learning to Denoise Raw Mobile UI Layouts for Improving Datasets at Scale", **Figure 5** (the side-by-side example). Paper PDF: `https://research.google/pubs/learning-to-denoise-raw-mobile-ui-layouts-for-improving-datasets-at-scale/`. Open the PDF, screenshot Figure 5, save as `reports/figures/ch2_rico_vs_clay.png`.
- Alternatively, the CLAY GitHub README at `https://github.com/google-research-datasets/clay` has matched-pair examples you can screenshot.
- Cite as "Reproduced from Li et al. (2022a), Figure 5" in the caption.

**Insert location.** `Final_Report_v2.md`, replace the placeholder block on lines **219-221**.

**Caption.**
> Figure 4: Raw RICO labels on the left, CLAY's denoised labels on the right, same screen. CLAY removes invisible-container nodes, fixes class mis-assignments, and reduces overlapping-box duplicates. Source: Li et al. (2022a).

---

### Figure 5 — READY (classical baselines grid)
**File.** `docs/figures/figure_05_classical_baselines_grid.png`

**Insert location.** `Final_Report_v2.md`, replace the placeholder block on lines **245-247**.

**Caption.**
> Figure 5: Per-task verdicts for the three classical baselines across the 15 evaluation tasks. Each baseline's failure cluster is distinct, which is what motivates the project's combined vision + OCR approach.

**Note.** I produced this from the actual `baseline_per_task.csv`, so the verdicts are the canonical evidence (not illustrative).

---

### Figure 6 — READY (modular vs end-to-end)
**File.** `docs/figures/figure_06_modular_vs_e2e.png`

**Insert location.** `Final_Report_v2.md`, replace the placeholder block on lines **289-291**.

**Caption.**
> Figure 6: Two architectural families for instruction-to-action GUI agents. This project belongs to the modular family on the left, in deliberate contrast to the end-to-end LVLM family on the right.

---

### Figure 7 — READY (UML use case diagram)
**File.** `docs/figures/figure_07_use_case_diagram.png`

**Insert location.** `Final_Report_v2.md`, replace the placeholder block on lines **404-406**.

**Caption.**
> Figure 7: Use case diagram for the VisClick prototype. UC-01 to UC-04 are user-facing; UC-05 and UC-06 are run during evaluation. Each use case maps to one or more functional requirements in Section 3.7.

---

### Figure 8 — READY (Gantt chart)
**File.** `docs/figures/figure_08_gantt.png`

**Insert location.** `Final_Report_v2.md`, replace the placeholder block on lines **543-545**.

**Caption.**
> Figure 8: Twelve-month project plan over the four operational phases. Phase boundaries are deliberately drawn with overlap; in practice each phase's documentation continued while the next phase's experiments began.

---

### Figure 9 — READY (block diagram)
**File.** `docs/figures/figure_09_block_diagram.png` (this is the polished version of the earlier `svg_01_visclick_layered_architecture.svg`)

**Insert location.** `Final_Report_v2.md`, replace the placeholder block on lines **642-644**.

**Caption.**
> Figure 9: Block diagram of VisClick. The capture, detect, OCR, match and act components are each a Python module under `src/visclick/`. Logging components live in `scripts/run_baselines.py`.

---

### Figure 10 — READY (process flow chart)
**File.** `docs/figures/figure_10_process_flowchart.png`

**Insert location.** `Final_Report_v2.md`, replace the placeholder block on lines **668-670**.

**Caption.**
> Figure 10: Per-instruction flow chart. The decision diamond at the matcher determines whether the detector's top candidate is accepted (Yes), whether the full-image OCR fallback is invoked (No, retry), or whether the system refuses to click (No, refuse).

---

### Figure 11 — MIXED (GUI wireframe)
**Two options.**
- (a) Use my wireframe: `docs/figures/figure_11_gui_wireframe.png`. This is fine if you don't have a clean Tk screenshot.
- (b) Use the real screenshot: `reports/figures/proto_2_captured.png` exists already. Annotate it with arrows in PowerPoint or Word and label the six numbered elements. More credible in a viva but more work.

**Insert location.** `Final_Report_v2.md`, replace the placeholder block on lines **710-712**.

**Caption.**
> Figure 11: GUI wireframe. (1) Monitor dropdown. (2) Instruction text box. (3) Run / Stop buttons. (4) Live status line. (5) Last-overlay thumbnail. (6) Verbose log toggle.

---

### Figure 12 — READY (repository tree)
**File.** `docs/figures/figure_12_repo_tree.png`

**Insert location.** `Final_Report_v2.md`, replace the placeholder block on lines **729-731**.

**Caption.**
> Figure 12: Repository directory tree. Top-level directories group the artefact's responsibilities: source code, dependency packaging, training data, model weights, evaluation scripts, notebooks, tests, reports, and documentation. Every path quoted elsewhere in this report is a node in this tree.

---

### Figure 13 — READY (source backbone three-panel)
**File.** `docs/figures/figure_13_source_backbone.png`

**Insert location.** `Final_Report_v2_part2.md`, replace the placeholder block on lines **407-409**.

**Caption.**
> Figure 13: Three-panel comparison of YOLOv8s and DETR-R50 on the unified-bundle val split. Left, mAP@0.5; centre, mAP@0.5:0.95; right, training wall-clock cost on a single Colab T4. Under the project's compute budget, YOLOv8s is the strict engineering win.

**Source data.** Both bars are taken directly from `reports/tables/source_domain_results.csv` and `reports/tables/source_domain_results_detr.csv`.

---

### Figure 14 — READY (sample-efficiency dual-axis curve)
**File.** `docs/figures/figure_14_sample_efficiency.png`

**Insert location.** `Final_Report_v2_part2.md`, replace the placeholder block on lines **440-442**.

**Caption.**
> Figure 14: Sample-efficiency curve. Hand-corrected mAP@0.5 (orange) rises monotonically from 0.012 at k = 0 to 0.271 at k = 8. ScreenSpot CPV (blue) peaks at 68.26 % at k = 1 then collapses to 10.48 % at k = 4 and recovers partially to 25.15 % at k = 8. The two protocols disagree about which checkpoint is best; the deployed model is k = 1.

**Source data.** All five points come straight from `reports/tables/sample_efficiency.csv`.

---

### Figure 15 — READY (all-method bar chart)
**File.** `docs/figures/figure_15_all_methods_screenspot.png`

**Insert location.** `Final_Report_v2_part2.md`, replace the placeholder block on lines **500-502**.

**Caption.**
> Figure 15: ScreenSpot desktop CPV across eleven configurations. Two clusters: a high cluster (60-69 %) comprising zero-shot, k = 1 head FT, AT short, and AT full; and a low cluster (below 50 %) containing every other adaptation method.

**Source data.** Drawn from `cpv_screenspot_desktop*.csv` and `cpv_summary_uda_*.csv`.

---

### Figure 16 — READY (CPV by slice and method)
**File.** `docs/figures/figure_16_screenspot_by_slice.png`

**Insert location.** `Final_Report_v2_part2.md`, replace the placeholder block on lines **542-544**.

**Caption.**
> Figure 16: ScreenSpot desktop CPV by slice (overall, macOS, Windows, text, icon) and method (k = 1 head FT, AT short, AT full, SHOT freeze=10). The text slice is the strongest across every method (60-86 %); the icon slice is the dominant failure mode for every method (17-49 %).

**Source data.** Drawn from `cpv_screenspot_desktop*.csv` per-method files.

---

## Replacement procedure (per figure)

1. Open the markdown file.
2. Find the existing `[FIGURE N: ...]` placeholder block (3 lines, between `[FIGURE` and the closing `]`).
3. Replace it with: a Word figure containing the image + the caption directly below.

**For the markdown source itself** (so the markdown stays clean before you paste into Word): replace the three-line placeholder block with this single line, then re-paste the whole chapter into Word and insert images at each marker.

```
[Figure N — see docs/figures/figure_NN_*.png]
```

That keeps the markdown short and Word-paste friendly.

---

## Bonus figure produced — `figure_99_protocol_disagreement_optional.svg/.png`

I had the SVG ready for the protocol disagreement chart (1.40 % vs 57.49 %). It's not currently a numbered figure in the report. If you want it as a new Figure 17 inside Section 7.3.3 (just before "PROTOCOL DISAGREEMENT" subsection in `Final_Report_v2_part2.md`), say the word and I'll insert a placeholder + bump the numbering.

---

## What I cannot create — only Figures 1 and 4

Both need real-world UI screenshots that have to come from outside this codebase. The instructions in Sections 1 and 4 above are concrete. Estimated time: 5-10 minutes each.
