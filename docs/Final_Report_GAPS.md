# Final Report: Gaps and Outstanding Work

**Status:** living checklist. Whenever the report's prose introduces a placeholder of the form `[NUMBER]`, `[TABLE]`, `[FIGURE N.x]`, or `[CITATION]` that depends on work not yet finished, the matching entry below records what needs to be done to fill it. The author works through this list to bring the report from "first draft" to "submission-ready".

**Action plan:** use **`PHASE_WORKLOG.md`** for ordered phases (1–8), plain-English steps, and a **findings log**. Use `SUBMISSION_TASK_PLAN.md` for gap-ID checklists. Both follow the **author priority order** below.

**Author priority order (current plan).** Work in this sequence unless the supervisor says otherwise.

1. **D (DATA) first:** run experiments and measurements; produce CSVs and numbers the report can cite.
2. **T (TABLE) second:** consolidate results into submission tables and extend `transfer_experiments` (and related files) once the D items they depend on exist.
3. **W (WRITING) third:** renumber references (**W-01**); refresh Chapter 6 prose for new methods (**W-02**); personal Chapter 9 paragraphs (**W-03**, **W-04**) when the story is stable.
4. **F (FIGURE) fourth:** export diagrams, composites, and screenshots; several figures depend on D outputs (for example **F-10**, **F-11**, **F-12**).
5. **U (USER) last:** title page, RGU style, acknowledgements, hardware spec, Word/PDF export, and binding tasks.

**Conventions.** Each row has a unique `ID`, a short `Gap` description, a chapter/section pointer, a `Source` indicating where the data or content needs to come from, and a `Status` field (`OPEN`, `IN PROGRESS`, `DONE`). Items group into five categories: DATA gaps (experiments not yet run), WRITING gaps (sections needing expansion), FIGURE gaps, TABLE gaps, and USER-OWED gaps (information only the author can provide).

Section headings in this file follow that same order: **D, then T, then W, then F, then U.**

---

## DATA gaps (priority: first)

**Do these before** investing in final tables, figures, and submission admin.

| ID | Gap | Chapter | Source | Status |
|----|-----|---------|--------|--------|
| D-01 | DETR-R50 backbone trained on CLAY and evaluated zero-shot on the labelled desktop test set. Proposal Section 7.B requires both YOLOv8 and DETR for RQ3. Currently only YOLOv8 numbers exist. | Ch6, Ch7, Ch8 | new Colab notebook `09_detr_source.ipynb` + `10_detr_finetune.ipynb` | OPEN |
| D-02 | SSP (self-supervised pre-training) experiment: train both backbones with the generative inpainting task on the ~2,000 unlabelled corpus, then fine-tune. Phase 2 Experiment 2 in proposal. | Ch6, Ch7, Ch8 | new notebooks `11_ssp_pretrain.ipynb` + `12_ssp_finetune.ipynb` | OPEN |
| D-03 | Unsupervised Domain Adaptation experiment 1: Cross-Domain Adaptive Teacher (Li et al. 2022). Implement teacher-student loop with EMA teacher, weak/strong augmentation, mixed batches. | Ch6, Ch7, Ch8 | new notebook `13_uda_adaptive_teacher.ipynb` | OPEN |
| D-04 | Unsupervised Domain Adaptation experiment 2: SHOT (Source Hypothesis Transfer). Freeze source classifier head, adapt only feature extractor on unlabelled target data with self-supervision. | Ch6, Ch7, Ch8 | new notebook `14_uda_shot.ipynb` | OPEN |
| D-05 | Few-shot data-efficiency curve: train at $k = 1, 5, 10, 50, 100$ labelled desktop images. Phase 2 Experiment 1 in proposal. Currently only one labelled-data budget (the 8-image hand-corrected test set) exists. | Ch6, Ch7, Ch8 | extension of `08_phase1B_ablations.ipynb` | OPEN |
| D-06 | Unlabelled desktop corpus expansion from 50 (current) to ~2000 screenshots as the proposal specifies. Required for D-02, D-03, D-04. | Ch6 | `scripts/capture_screenshots.py` extended to walk 10-15 apps and capture systematically | OPEN |
| D-07 | Labelled desktop corpus expansion from 8 (current hand-corrected test) to 100 (proposal target). Required for D-05 to be meaningful. | Ch6 | CVAT or Roboflow annotation session | OPEN |
| D-08 | CPV (Central Point Validation) metric reported alongside mAP@0.5. Currently only mAP is computed. CPV is from Dardouri et al. 2024 and is committed to in proposal Section 7.C. | Ch7 | add a CPV computation step to `08_phase1B_ablations.ipynb` Section 6 | **DONE** — Phase 2, 14 May 2026. Computed via `scripts/run_cpv.py` (default conf 0.25) on the 8-image hand-corrected set. Outputs: `reports/tables/cpv_summary.csv` and `reports/tables/cpv_per_image.csv`. **Overall CPV = 1.40 %** (5 / 356 GT boxes). Per class: `button` 13.3 % (2/15), `menu` 9.1 % (3/33), `text_input` 0 % (0/189), `icon` 0 % (0/89), `text` 0 % (0/20), `checkbox` 0 % (0/10). Consistent with the 0.033 mAP@0.5 hand-corrected number already cited in report Section 8.2; reinforces the recall-bound finding and the case for D-07. Optional: a softer-threshold companion run can be added with `--conf 0.10 --tag conf010` for a precision-vs-recall sensitivity row. |
| D-09 | Inference-speed measurement on the same hardware for all backbones (YOLOv8, DETR, classical baselines). Currently only end-to-end wall-clock latency in `nfr_performance.csv`; pure detector inference is bundled with OCR. | Ch7, Ch8 | `scripts/run_nfr.py` extended to time `Detector.predict()` only, separately from OCR | **DONE (YOLOv8 only)** — Phase 1, 14 May 2026. 50-run ONNX bench: median 67.81 ms, p95 79.02 ms (`reports/tables/detector_bench_snapshot_2026-05-14.csv`). DETR row still pending D-01; bench used matplotlib `logo2.png` (n_detections=0) so re-run on a real desktop screenshot is a nice-to-have. |
| D-10 | Qualitative third-party evaluation. Sample dissertation Table 19 gives 3 expert reviewers. We have zero. | Ch8 Section 8.3 | 1-2 colleagues run the bot on T01-T15, write 5-line review each. Either by email or short video call notes. | **DEFERRED** — Phase 2, 14 May 2026. Author decision: skip third-party reviewer pass for this submission. Report Sections 8.3 / 9.7 already state the qualitative side is single-rater; will be flagged explicitly as a limitation. F-12 figure also deferred consequently. |
| D-11 | Memory profiling during a full T01-T15 run, peak RSS reported per method. R-NFR-03 PENDING in Section 16 of data form. | Ch7 Section 7.3.2 | `psutil`-based wrapper around `run_baselines.py`, write per-method peak memory to `nfr_memory.csv` | **PARTIAL** — Phase 1, 14 May 2026. psutil RSS in-process: ~212 MB detector-only, ~764 MB with EasyOCR (`PHASE_WORKLOG.md`). Formal per-method `nfr_memory.csv` over the full T01-T15 still PENDING. |
| D-12 | Preprocessing impact A/B test: run T01-T15 with bilateral filter / contrast normalisation enabled vs disabled, report ΔTSR. | Ch6 Section 6.6, Ch7 Section 7.2.3 | new script `scripts/run_preprocessing_ab.py` | **DEFERRED** — Phase 2, 14 May 2026. Author decision: skip; report Section 9.7 already lists preprocessing tuning as future work. |

**Suggested D sequence (dependencies):** **D-07** and/or **D-06** enlarge data where needed; then **D-05**, **D-01**, **D-02–D-04** as you choose. In parallel, lighter D items: **D-08**, **D-09**, **D-10**, **D-11**, **D-12**.

---

## TABLE gaps (priority: second)

Fill after the D runs that feed each row.

| ID | Gap | Chapter | Source | Status |
|----|-----|---------|--------|--------|
| T-01 | Table 4.1: full per-model results across YOLOv8 and DETR, both zero-shot and fine-tuned. Currently only YOLOv8 rows are filled (M0..M3). DETR rows pending D-01. | Ch4 Section 4.1, Ch6, Ch7 | `reports/tables/transfer_experiments.csv` extended | OPEN |
| T-02 | Table 7.x: sample-efficiency table: mAP@0.5 vs $k$ labelled images, both with and without SSP. | Ch7 | new CSV `reports/tables/sample_efficiency.csv` from D-05 + D-02 | OPEN |
| T-03 | Table 7.y: UDA comparison: Adaptive Teacher vs SHOT, both backbones. | Ch7 | new CSV `reports/tables/uda_comparison.csv` from D-03 + D-04 | OPEN |
| T-04 | Table 8.x: full requirement-evaluation table: every R-FR-01..R-FR-09 and R-NFR-01..R-NFR-10 with measured value. Today the per-method pass rate is in `baseline_per_task.csv`; the FR/NFR mapping table needs to be exported as its own CSV for citation. | Ch3 Section 3.8, Ch3 Section 3.9, Ch8 Section 8.4, Section 8.5 | hand-built table; ~30 min | **DONE** — Phase 1, 14 May 2026. `reports/tables/requirements_evidence.csv` (19 rows: R-FR-01..R-FR-09 + R-NFR-01..R-NFR-10) keyed to Chapter 3, with columns req_id, req_name, target, evidence_type, evidence_file, measured, summary_verdict, notes. |

---

## WRITING gaps (priority: third)

| ID | Gap | Chapter | Source | Status |
|----|-----|---------|--------|--------|
| W-01 | References list at end of report. Currently inline `[N]` citations use the proposal's numbering. Need a single sequential list ordered by first appearance in dissertation. | end of report | mechanical pass once all chapters written | OPEN |
| W-02 | Chapter 6 (Implementation) sections covering DETR backbone implementation, SSP pretraining objective, and UDA framework code paths. These exist as plans in the proposal but are not yet implemented; corresponding prose must follow the code. | Ch6 | depends on D-01..D-04 | OPEN |
| W-03 | Chapter 9 Section 9.3 "Learning Outcomes" and Section 9.4 "Highly Relevant Academic Modules" need personal-voice reflections that only the author can provide (which modules from the MSc curriculum mapped to which parts of the work, what surprised the author during execution, etc.). | Ch9 | author-owned | OPEN |
| W-04 | Chapter 9 Section 9.5 "Self-Taught Areas and New Skills": same as W-03, author-owned. | Ch9 | author-owned | OPEN |

---

## FIGURE gaps (priority: fourth; defer)

**Skip until** the D and T work you plan to cite is largely done (many figures depend on notebook output or reviewer quotes).

| ID | Gap | Chapter | Source | Status |
|----|-----|---------|--------|--------|
| F-01 | Figure 1.1: three-panel domain-shift example (mobile / classic desktop / Win11 native). | Ch1 Section 1.2 | composite to be made by the author; suggested file `reports/figures/ch1_domain_shift_examples.png` | OPEN |
| F-02 | Figure 1.2: positioning 2x2 grid (lightweight↔heavyweight × tolerant↔brittle). | Ch1 Section 1.6 | hand-drawn or matplotlib; suggested file `reports/figures/ch1_positioning_grid.png` | OPEN |
| F-03 | Figure 1.3: high-level solution overview (Mermaid export from data-form Section 18.1). | Ch1 Section 1.9 | export `reports/figures/ch1_solution_overview.png` from existing Mermaid source | OPEN |
| F-04 | Figure 2.x: RICO sample screen and CLAY-cleaned counterpart, side-by-side. | Ch2 Section 2.2 | author screenshots from RICO/CLAY downloads | OPEN |
| F-05 | Figure 2.y: UIED-style overlay on a Win11 dialog. | Ch2 Section 2.4 | one of the existing T01 overlays from `reports/figures/baselines/` | OPEN |
| F-06 | Figure 5.x: UML use case diagram (UC-01..UC-06). | Ch3 Section 3.6 | hand-drawn, draw.io, or mermaid `usecaseDiagram` | OPEN |
| F-07 | Figure 5.y: Wireframe(s) for the prototype GUI. | Ch5 Section 5.6 | hand-drawn or screenshot of current Tk GUI annotated | OPEN |
| F-08 | Figure 4.x: Gantt chart for the 12-month project plan. | Ch4 Section 4.7 | export from MS Project / draw.io / Notion / spreadsheet | OPEN |
| F-09 | Figure 6.x: annotation guidelines screenshot (CVAT or Roboflow). | Ch6 Section 6.3 | screenshot of the actual annotation tool with labels visible | OPEN |
| F-10 | Figure 7.x: confusion matrix for the headline detector. | Ch7 Section 7.2 | regenerate from `08_phase1B_ablations.ipynb` and save as PNG | OPEN |
| F-11 | Figure 7.y: sample-efficiency curve (depends on D-05). | Ch7 Section 7.2 | matplotlib plot from `sample_efficiency.csv` (T-02) | OPEN |
| F-12 | Figure 8.x: qualitative evaluation evidence (screenshots of feedback). | Ch8 Section 8.3 | depends on D-10; could be quoted email screenshots, redacted as needed | OPEN |

---

## USER-OWED gaps (priority: last)

**Do last:** RGU front matter, style decisions that affect the whole PDF, and hardware acknowledgement for timing claims.

| ID | Gap | Chapter | Source | Status |
|----|-----|---------|--------|--------|
| U-01 | Submission Date (TBD on title page). | title page | author | OPEN |
| U-02 | Second Marker name (TBD on title page). | title page | confirmed by RGU | OPEN |
| U-03 | Word count check against RGU MSc requirement (typically 15-20k for a 60-credit project; the dissertation template has a specific limit). | end of report | RGU programme handbook | OPEN |
| U-04 | Acknowledgements paragraph (supervisor, second marker, family, AI-tool disclosure). | front matter | author | OPEN |
| U-05 | Final hardware spec for the Windows test machine: fill Section 1.1 of the data form before quoting any latency number in Ch7. | Ch7, data form Section 1.1 | author's `dxdiag` or `systeminfo` output | **DONE** — Phase 1, 14 May 2026. `docs/VisClick_Report_Data_Form.md` Section 1.1 populated (Win11 22631 / Ultra 5 135H / 32 GB / Intel Arc iGPU / 1920×1080). Display **scaling** still PENDING. |
| U-06 | Reflection on whether YOLOv8 or DETR was harder to set up / debug / get running on Colab Free T4. Needed for Section 9.2 Challenges Faced. | Ch9 Section 9.2 | author memory | OPEN |
| U-07 | Whether to keep IEEE numeric `[N]` or switch to Harvard `(Author Year)` for the final reference style. | all chapters | RGU dissertation style guide | OPEN |
| U-08 | Whether to write in first-person ("I designed...") or third-person impersonal ("the project designed..."). The sample dissertation uses third-person; this draft uses light first-person. | all chapters | author preference | OPEN |
| U-09 | Whether to keep British or American spelling. Current draft is British. | all chapters | RGU style guide; programme is at RGU Aberdeen so British is the default | OPEN |
| U-10 | Annotations for T16-T20 in `tasks/T01_T20.json`. Five tasks are currently "TBD". The Phase 2 evaluation only runs T01-T15 today; if T16-T20 are needed the author must define them. | Ch6 Section 6.7, Ch7 Section 7.3 | author defines five more representative tasks | OPEN |
| U-11 | Demo video (~5 minute, 6-8 task storyboard, refusal case). Plan Section L.3. | Ch8 Section 8.x, Ch9 Section 9.x | author records | OPEN |

---

## Notes on style and process

* **Filling a gap.** When an item is resolved, change `Status` to `DONE` and add the commit hash / file path that closes it.
* **Reading the report top-to-bottom right now.** A reader will hit several `[NUMBER]` / `[FIGURE]` placeholders. This is expected for a first draft. The reader should treat the prose as the contract; the placeholders are the line items still outstanding.
* **Not every gap will be closed before submission.** Some items (D-01 through D-05, for example) are large enough that finishing all of them adds another month of work. The author makes a final triage call about which to close before submission and which to defer into the "future work" of Section 9.8. The gaps tracker is the place to record that decision.

---

*Tracker created 11 May 2026. Owner: Hiran Abeywardhana.*
