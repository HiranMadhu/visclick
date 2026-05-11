# Final Report — Gaps and Outstanding Work

**Status:** living checklist. Whenever the report's prose introduces a placeholder of the form `[NUMBER]`, `[TABLE]`, `[FIGURE N.x]`, or `[CITATION]` that depends on work not yet finished, the matching entry below records what needs to be done to fill it. The author works through this list to bring the report from "first draft" to "submission-ready".

**Conventions.** Each row has a unique `ID`, a short `Gap` description, a chapter/section pointer, a `Source` indicating where the data or content needs to come from, and a `Status` field (`OPEN`, `IN PROGRESS`, `DONE`). Items group into five categories: DATA gaps (experiments not yet run), WRITING gaps (sections needing expansion), FIGURE gaps, TABLE gaps, and USER-OWED gaps (information only the author can provide).

---

## DATA gaps (experiments not yet run; results still owed)

| ID | Gap | Chapter | Source | Status |
|----|-----|---------|--------|--------|
| D-01 | DETR-R50 backbone trained on CLAY and evaluated zero-shot on the labelled desktop test set. Proposal §7.B requires both YOLOv8 and DETR for RQ3. Currently only YOLOv8 numbers exist. | Ch6, Ch7, Ch8 | new Colab notebook `09_detr_source.ipynb` + `10_detr_finetune.ipynb` | OPEN |
| D-02 | SSP (self-supervised pre-training) experiment: train both backbones with the generative inpainting task on the ~2,000 unlabelled corpus, then fine-tune. Phase 2 Experiment 2 in proposal. | Ch6, Ch7, Ch8 | new notebooks `11_ssp_pretrain.ipynb` + `12_ssp_finetune.ipynb` | OPEN |
| D-03 | Unsupervised Domain Adaptation experiment 1: Cross-Domain Adaptive Teacher (Li et al. 2022). Implement teacher-student loop with EMA teacher, weak/strong augmentation, mixed batches. | Ch6, Ch7, Ch8 | new notebook `13_uda_adaptive_teacher.ipynb` | OPEN |
| D-04 | Unsupervised Domain Adaptation experiment 2: SHOT (Source Hypothesis Transfer). Freeze source classifier head, adapt only feature extractor on unlabelled target data with self-supervision. | Ch6, Ch7, Ch8 | new notebook `14_uda_shot.ipynb` | OPEN |
| D-05 | Few-shot data-efficiency curve: train at $k = 1, 5, 10, 50, 100$ labelled desktop images. Phase 2 Experiment 1 in proposal. Currently only one labelled-data budget (the 8-image hand-corrected test set) exists. | Ch6, Ch7, Ch8 | extension of `08_phase1B_ablations.ipynb` | OPEN |
| D-06 | Unlabelled desktop corpus expansion from 50 (current) to ~2000 screenshots as the proposal specifies. Required for D-02, D-03, D-04. | Ch6 | `scripts/capture_screenshots.py` extended to walk 10-15 apps and capture systematically | OPEN |
| D-07 | Labelled desktop corpus expansion from 8 (current hand-corrected test) to 100 (proposal target). Required for D-05 to be meaningful. | Ch6 | CVAT or Roboflow annotation session | OPEN |
| D-08 | CPV (Central Point Validation) metric reported alongside mAP@0.5. Currently only mAP is computed. CPV is from Dardouri et al. 2024 and is committed to in proposal §7.C. | Ch7 | add a CPV computation step to `08_phase1B_ablations.ipynb` Section 6 | OPEN |
| D-09 | Inference-speed measurement on the same hardware for all backbones (YOLOv8, DETR, classical baselines). Currently only end-to-end wall-clock latency in `nfr_performance.csv`; pure detector inference is bundled with OCR. | Ch7, Ch8 | `scripts/run_nfr.py` extended to time `Detector.predict()` only, separately from OCR | OPEN |
| D-10 | Qualitative third-party evaluation. Sample dissertation Table 19 gives 3 expert reviewers. We have zero. | Ch8 §8.3 | 1-2 colleagues run the bot on T01-T15, write 5-line review each. Either by email or short video call notes. | OPEN |
| D-11 | Memory profiling during a full T01-T15 run, peak RSS reported per method. R-NFR-03 PENDING in §16 of data form. | Ch7 §7.3.2 | `psutil`-based wrapper around `run_baselines.py`, write per-method peak memory to `nfr_memory.csv` | OPEN |
| D-12 | Preprocessing impact A/B test: run T01-T15 with bilateral filter / contrast normalisation enabled vs disabled, report ΔTSR. | Ch6 §6.6, Ch7 §7.2.3 | new script `scripts/run_preprocessing_ab.py` | OPEN |

## TABLE gaps (table shells exist but cells still empty)

| ID | Gap | Chapter | Source | Status |
|----|-----|---------|--------|--------|
| T-01 | Table 4.1 — full per-model results across YOLOv8 and DETR, both zero-shot and fine-tuned. Currently only YOLOv8 rows are filled (M0..M3). DETR rows pending D-01. | Ch4 §4.1, Ch6, Ch7 | `reports/tables/transfer_experiments.csv` extended | OPEN |
| T-02 | Table 7.x — sample-efficiency table: mAP@0.5 vs $k$ labelled images, both with and without SSP. | Ch7 | new CSV `reports/tables/sample_efficiency.csv` from D-05 + D-02 | OPEN |
| T-03 | Table 7.y — UDA comparison: Adaptive Teacher vs SHOT, both backbones. | Ch7 | new CSV `reports/tables/uda_comparison.csv` from D-03 + D-04 | OPEN |
| T-04 | Table 8.x — full requirement-evaluation table: every R-FR-01..R-FR-09 and R-NFR-01..R-NFR-10 with measured value. Today the per-method pass rate is in `baseline_per_task.csv`; the FR/NFR mapping table needs to be exported as its own CSV for citation. | Ch3 §3.8, Ch3 §3.9, Ch8 §8.4, §8.5 | hand-built table; ~30 min | OPEN |

## FIGURE gaps (placeholders waiting for the author's images)

| ID | Gap | Chapter | Source | Status |
|----|-----|---------|--------|--------|
| F-01 | Figure 1.1 — three-panel domain-shift example (mobile / classic desktop / Win11 native). | Ch1 §1.2 | composite to be made by the author; suggested file `reports/figures/ch1_domain_shift_examples.png` | OPEN |
| F-02 | Figure 1.2 — positioning 2x2 grid (lightweight↔heavyweight × tolerant↔brittle). | Ch1 §1.6 | hand-drawn or matplotlib; suggested file `reports/figures/ch1_positioning_grid.png` | OPEN |
| F-03 | Figure 1.3 — high-level solution overview (Mermaid export from data-form §18.1). | Ch1 §1.9 | export `reports/figures/ch1_solution_overview.png` from existing Mermaid source | OPEN |
| F-04 | Figure 2.x — RICO sample screen and CLAY-cleaned counterpart, side-by-side. | Ch2 §2.2 | author screenshots from RICO/CLAY downloads | OPEN |
| F-05 | Figure 2.y — UIED-style overlay on a Win11 dialog. | Ch2 §2.4 | one of the existing T01 overlays from `reports/figures/baselines/` | OPEN |
| F-06 | Figure 5.x — UML use case diagram (UC-01..UC-06). | Ch3 §3.6 | hand-drawn, draw.io, or mermaid `usecaseDiagram` | OPEN |
| F-07 | Figure 5.y — Wireframe(s) for the prototype GUI. | Ch5 §5.6 | hand-drawn or screenshot of current Tk GUI annotated | OPEN |
| F-08 | Figure 4.x — Gantt chart for the 12-month project plan. | Ch4 §4.7 | export from MS Project / draw.io / Notion / spreadsheet | OPEN |
| F-09 | Figure 6.x — annotation guidelines screenshot (CVAT or Roboflow). | Ch6 §6.3 | screenshot of the actual annotation tool with labels visible | OPEN |
| F-10 | Figure 7.x — confusion matrix for the headline detector. | Ch7 §7.2 | regenerate from `08_phase1B_ablations.ipynb` and save as PNG | OPEN |
| F-11 | Figure 7.y — sample-efficiency curve (depends on D-05). | Ch7 §7.2 | matplotlib plot from `sample_efficiency.csv` (T-02) | OPEN |
| F-12 | Figure 8.x — qualitative evaluation evidence (screenshots of feedback). | Ch8 §8.3 | depends on D-10; could be quoted email screenshots, redacted as needed | OPEN |

## WRITING gaps (sections needing content rewrite / expansion)

| ID | Gap | Chapter | Source | Status |
|----|-----|---------|--------|--------|
| W-01 | References list at end of report. Currently inline `[N]` citations use the proposal's numbering. Need a single sequential list ordered by first appearance in dissertation. | end of report | mechanical pass once all chapters written | OPEN |
| W-02 | Chapter 6 (Implementation) sections covering DETR backbone implementation, SSP pretraining objective, and UDA framework code paths. These exist as plans in the proposal but are not yet implemented; corresponding prose must follow the code. | Ch6 | depends on D-01..D-04 | OPEN |
| W-03 | Chapter 9 §9.3 "Learning Outcomes" and §9.4 "Highly Relevant Academic Modules" need personal-voice reflections that only the author can provide (which modules from the MSc curriculum mapped to which parts of the work, what surprised the author during execution, etc.). | Ch9 | author-owned | OPEN |
| W-04 | Chapter 9 §9.5 "Self-Taught Areas and New Skills" — same as W-03, author-owned. | Ch9 | author-owned | OPEN |

## USER-OWED gaps (only the author can supply)

| ID | Gap | Chapter | Source | Status |
|----|-----|---------|--------|--------|
| U-01 | Submission Date (TBD on title page). | title page | author | OPEN |
| U-02 | Second Marker name (TBD on title page). | title page | confirmed by RGU | OPEN |
| U-03 | Word count check against RGU MSc requirement (typically 15-20k for a 60-credit project; the dissertation template has a specific limit). | end of report | RGU programme handbook | OPEN |
| U-04 | Acknowledgements paragraph (supervisor, second marker, family, AI-tool disclosure). | front matter | author | OPEN |
| U-05 | Final hardware spec for the Windows test machine — fill §1.1 of the data form before quoting any latency number in Ch7. | Ch7, data form §1.1 | author's `dxdiag` or `systeminfo` output | OPEN |
| U-06 | Reflection on whether YOLOv8 or DETR was harder to set up / debug / get running on Colab Free T4. Needed for §9.2 Challenges Faced. | Ch9 §9.2 | author memory | OPEN |
| U-07 | Whether to keep IEEE numeric `[N]` or switch to Harvard `(Author Year)` for the final reference style. | all chapters | RGU dissertation style guide | OPEN |
| U-08 | Whether to write in first-person ("I designed...") or third-person impersonal ("the project designed..."). The sample dissertation uses third-person; this draft uses light first-person. | all chapters | author preference | OPEN |
| U-09 | Whether to keep British or American spelling. Current draft is British. | all chapters | RGU style guide; programme is at RGU Aberdeen so British is the default | OPEN |
| U-10 | Annotations for T16-T20 in `tasks/T01_T20.json`. Five tasks are currently "TBD". The Phase 2 evaluation only runs T01-T15 today; if T16-T20 are needed the author must define them. | Ch6 §6.7, Ch7 §7.3 | author defines five more representative tasks | OPEN |
| U-11 | Demo video (~5 minute, 6-8 task storyboard, refusal case). Plan §L.3. | Ch8 §8.x, Ch9 §9.x | author records | OPEN |

---

## Notes on style and process

* **Filling a gap.** When an item is resolved, change `Status` to `DONE` and add the commit hash / file path that closes it.
* **Reading the report top-to-bottom right now.** A reader will hit several `[NUMBER]` / `[FIGURE]` placeholders. This is expected for a first draft. The reader should treat the prose as the contract; the placeholders are the line items still outstanding.
* **Not every gap will be closed before submission.** Some items (D-01 through D-05, for example) are large enough that finishing all of them adds another month of work. The author makes a final triage call about which to close before submission and which to defer into the "future work" of §9.8. The gaps tracker is the place to record that decision.

---

*Tracker created 11 May 2026. Owner: Hiran Abeywardhana.*
