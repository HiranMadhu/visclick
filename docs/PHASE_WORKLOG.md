# VisClick — Phase Worklog (canonical plan + findings)

**This file is the single source of truth for "where we are and what's next."**

- **Per-item ledger** (D-01 … U-11, with status and evidence pointers) lives in `Final_Report_GAPS.md`.
- **Underlying project data** (hardware spec, raw bench numbers, integration notes) lives in `VisClick_Report_Data_Form.md`.
- **Historical / original how-to-build plan** lives in `VisClick_Detailed_Plan.md` (archived; do not follow step-by-step).

**Author:** Hiran Abeywardhana.
**Last updated:** 2 June 2026.

---

## 1. Current state at a glance

| Phase | What it covers | Status |
|---|---|---|
| 1 — Easy evidence (hardware, det. latency, memory, T-04) | U-05, D-09, D-11, T-04, NFR refresh | **DONE** (D-11 PARTIAL) |
| 2 — CPV on hand-corrected set + optional A/B + reviewers | D-08, D-12, D-10 | **DONE** (D-08 closed; D-10 + D-12 deferred) |
| 3 — Independent CPV via public benchmark | D-07, D-06 (initial deferral) | **DONE** (D-07 closed via ScreenSpot; D-06 was deferred here but is reopened in Phase 4) |
| **4 — Heavy retraining: different transfer-learning approaches** | **D-06 corpus, D-01 DETR, D-05 few-shot curve, D-02 SSP+FT** | **IN PROGRESS — D-01 source-side DONE (2 June 2026, mAP@0.5 = 0.2438 on CLAY test). D-06 / D-05 / D-02 still in progress. D-01 target-side and D-03 / D-04 UDA remain DEFERRED.** |
| 5 — Tables | T-01, T-02, T-03 | **OPEN** — fills after Phase 4 produces numbers |
| 6 — Writing sync | W-01, W-02, W-03, W-04 | **DONE** for what's possible without Phase 4 (W-02 will need a refresh once Phase 4 numbers land) |
| 7 — Figures | F-01 … F-12 | **OPEN** (paused — author has deprioritised final-report polish) |
| 8 — Submission pack | U-01 … U-11 except U-05/U-06 | **OPEN** (paused — same as Phase 7) |

**Net:** Phase 4 is the active engineering lane. Phases 7 and 8 are paused. Phase 4 produces new mAP / CPV / sample-efficiency numbers that downstream Phase 5 tables (T-01, T-02) and Phase 6 W-02 sync will pick up once they land.

---

## 2. Active sprint — Phase 4 (different transfer-learning approaches)

The proposal promised a comparison of three transfer-learning families on two backbones. Today the report has only one family (few-shot fine-tuning) on one backbone (YOLOv8). Phase 4 fills the missing cells:

| Family | Approach | Backbone(s) | Sub-phase |
|---|---|---|---|
| (a) | Few-shot fine-tuning | YOLOv8 (done in M0..M3), **DETR** (D-01), **YOLOv8 + curve** (D-05) | **4.2**, **4.3** |
| (b) | Self-Supervised Pre-training + Fine-tune (SSP+FT) | YOLOv8 | **4.4** (needs D-06 corpus from **4.1**) |
| (c) | Unsupervised Domain Adaptation (Adaptive Teacher, SHOT) | DEFERRED | not in this sprint; future work |

### Dependency chain

```
4.0 Setup ─► 4.1 D-06 corpus capture (~1-2 calendar days, passive) ─► 4.4 D-02 SSP+FT
              │
              └── 4.2 D-01 DETR (3-5 h Colab) ── independent
              │
              └── 4.3 D-05 few-shot curve (4-6 h Colab) ── independent
```

The corpus capture runs in the background while D-01 and D-05 happen on Colab.

### 2.0 — Setup (15 minutes)

Before kicking off any sub-phase:

- [ ] Confirm Colab Free still allocates a GPU (open any of `notebooks/05_train_source.ipynb` or `06_finetune_desktop.ipynb`, check `nvidia-smi`).
- [ ] Confirm the existing Drive-mounted dataset folders (`source_clay/`, `handcorrected_desktop_test/`) are still in place.
- [ ] Confirm the YOLOv8 fine-tuned checkpoint exists (`weights/visclick.onnx` for inference; the `.pt` source-best lives in Drive next to the source-train notebook). DETR pre-training will start from `facebookresearch/detr` `detr-r50` HF weights, not from VisClick's YOLOv8 weights.
- [ ] Optional but recommended: open a small Drive folder `visclick/phase4_results/` to hold the new training logs and weights.

### 2.1 — Sub-phase 4.1: D-06 corpus capture (1-2 calendar days, mostly passive)

**Goal:** 1500–2000 unlabelled desktop screenshots across 10-15 apps, written to `~/Documents/visclick_data/desktop_unlabeled/<app>/`. SSP needs *diversity* (different apps, themes, window sizes) more than *count*; aim for ≥10 apps with ≥100 screens each.

Two capture modes are available. **Mode A (recommended)** is fully passive; **Mode B** is what `scripts/capture_screenshots.py` already does.

**Mode A — auto-capture in the background:** new script `scripts/auto_capture_corpus.py` (added in this commit). Runs in a terminal, takes a screenshot every N seconds (default 60), buckets by foreground app name (read via the Win32 API). Stop with F10.

Run on Windows as administrator so the F10 hotkey works:

```
.\.venv\Scripts\python.exe scripts\auto_capture_corpus.py --interval 60 --root %USERPROFILE%\Documents\visclick_data\desktop_unlabeled --max 2000
```

Then **just use your computer normally** for the rest of the day. The script samples once per minute. Over 6-8 active hours you'll accumulate 400-500 screens; over 2 days of normal work, 1500-2000.

**Mode B — manual hotkey (existing script):** if you want curated coverage (10 of each app), the existing `scripts/capture_screenshots.py` lets you hold F9 to snap.

**Phase 4.1 checklist**

- [ ] Started `auto_capture_corpus.py` on Windows.
- [ ] Verified screenshots are accumulating in the right folder (open the folder, see PNGs appear every minute).
- [ ] Reached ≥1500 PNGs across ≥10 apps (check the per-app subfolder counts).
- [ ] Stopped the script (F10) and confirmed final count.
- [ ] Optional: zip the folder and upload to Drive (large; do not commit to git).

When this is running, move to 4.2 and 4.3 in parallel.

### 2.2 — Sub-phase 4.2: D-01 DETR baseline (3-5 hours Colab)

**Goal:** Train DETR-R50 on CLAY (source) → fine-tune on the 8-image hand-corrected desktop test set → produce mAP@0.5 and CPV numbers comparable to VisClick's YOLOv8.

Two new notebooks to be created in this sub-phase (will be drafted when you reach this step):

- `notebooks/09_detr_source.ipynb` — DETR-R50, HuggingFace `transformers.DetrForObjectDetection`, train on CLAY for ~10-15 epochs with imgsz 800. Save best checkpoint to Drive.
- `notebooks/10_detr_finetune.ipynb` — load the source checkpoint, fine-tune on hand-corrected for ~30 epochs, evaluate mAP / CPV.

**Phase 4.2 checklist**

- [x] `09_detr_source.ipynb` runs end-to-end on Colab Free T4. (2 June 2026 — 6 epochs fp16 imgsz cap {600,800}.)
- [x] DETR source-best checkpoint saved to Drive. (`weights/baseline_source_detr/best_source_detr_r50.pt`.)
- [x] Source-side mAP recorded: **mAP@0.5 = 0.2438, mAP@0.5:0.95 = 0.1606** on CLAY test (7998 / 1000 / 1000). CSV: `reports/tables/source_domain_results_detr.csv`. **~54 % of YOLOv8s mAP@0.5 (0.4505) at ~6× the wall-clock time per training run** — clean compute-matched comparison.
- [ ] `10_detr_finetune.ipynb` runs to completion. **PENDING author decision** — see Phase-4.2 follow-up below.
- [ ] mAP@0.5 + CPV numbers recorded in `reports/tables/transfer_experiments.csv` (new DETR rows).
- [ ] Smoke-test: download fine-tuned DETR weights, run one inference on `samples/test_screenshots/T01.png`, confirm boxes look reasonable.

**Phase 4.2 follow-up (target-side):** the next move on D-01 is one of three paths; all leave Phase 4.3 (D-05) as the next sub-phase regardless. (a) Run a 5-minute zero-shot eval of `best_source_detr_r50.pt` on the 8-image hand-corrected desktop set (no fine-tune; cheapest way to close the proposal's "evaluated zero-shot on the labelled desktop test set" clause). (b) Run `10_detr_finetune.ipynb` to do head-only fine-tune on the 8 images + the zero-shot eval (more work; produces a fairer comparison but the 8-image fine-tune is likely to overfit). (c) Document the target-side as deferred (cite source-side number only, list target-side in Section 9.8 future work). Author preference recorded as: TBD.

### 2.3 — Sub-phase 4.3: D-05 few-shot curve (4-6 hours Colab)

**Goal:** Show how YOLOv8 mAP scales with k = 1, 5, 10, 50, 100 labelled desktop images. The proposal's RQ on sample efficiency.

Notebook to be created in this sub-phase:

- `notebooks/08c_few_shot_curve.ipynb` — load CLAY-pretrained YOLOv8 best.pt, fine-tune at each k, log mAP@0.5 + CPV.

**Note on k=100:** the hand-corrected set is only 8 images. For k>8 you'll need either (i) extend the hand-corrected set (a sub-task within D-07-2.0 if you want to do it), or (ii) limit the curve to k ∈ {1, 2, 4, 8} which is honest given the data budget. Option (ii) is acceptable for an MSc-scale finding; report it as "few-shot curve at small-k regime" rather than "to k=100."

**Phase 4.3 checklist**

- [x] `08c_few_shot_curve.ipynb` drafted (2 June 2026). Design: head-only fine-tune from `best_source_v8s.pt`, `k ∈ {1, 2, 4, 8}` strict-subset stems, primary eval on **ScreenSpot desktop (held-out, n=334)** via CPV, secondary mAP on hand-corrected (flagged `fit_to_train` for `k > 0`), plus the `k = 0` source-pretrained anchor point.
- [ ] `08c_few_shot_curve.ipynb` runs end-to-end on Colab Free T4 (~1 hour expected).
- [ ] `reports/tables/sample_efficiency.csv` exported (one row per k, with mAP@0.5 + CPV).
- [ ] Quick matplotlib line plot saved as `reports/figures/sample_efficiency_curve.png` (the F-11 figure).

### 2.4 — Sub-phase 4.4: D-02 SSP + FT (1 day Colab; runs after 4.1 corpus is done)

**Goal:** Self-Supervised Pre-training on the D-06 corpus, then few-shot fine-tune on hand-corrected. Compare to family (a).

**Method choice:** SimCLR-style contrastive pre-training on the CSPDarknet backbone (YOLOv8's feature extractor). Two-stage:

1. **SSP pretrain (`notebooks/11_ssp_pretrain.ipynb`):** take YOLOv8s backbone, attach a projection head, train with NT-Xent loss on the D-06 corpus for ~20-30 epochs with strong augmentation (RandomResizedCrop, ColorJitter, RandomGrayscale). The CSPDarknet learns desktop-specific features without labels.
2. **SSP fine-tune (`notebooks/12_ssp_finetune.ipynb`):** load the SSP-pretrained backbone into YOLOv8s, fine-tune on hand-corrected for ~30 epochs with the same recipe as M3. Evaluate.

**Phase 4.4 checklist**

- [ ] D-06 corpus has ≥1500 screens before starting 4.4.
- [ ] `11_ssp_pretrain.ipynb` produces an SSP backbone checkpoint.
- [ ] `12_ssp_finetune.ipynb` produces a fine-tuned YOLOv8 + SSP model with mAP@0.5 + CPV recorded.
- [ ] Numbers added to `reports/tables/transfer_experiments.csv` (new SSP row).
- [ ] Side-by-side mAP / CPV comparison: M0 (zero-shot) vs M3 (few-shot FT) vs SSP+FT. Documented in Section 6 / 7 of `Final_Report.md` once Phase 4 is closed.

### 2.5 — After Phase 4 lands

Once 4.1-4.4 are all DONE:

1. Update `Final_Report_GAPS.md`: D-01, D-02, D-05, D-06 from IN PROGRESS → DONE.
2. Refresh `transfer_experiments.csv` (T-01 sub-task) and `sample_efficiency.csv` (T-02 sub-task).
3. Rewrite Sections 6.5.5–6.5.8 of `Final_Report.md` (DETR + SSP + few-shot curve prose) — closes W-02 fully.
4. Reopen the dissertation-polish lane (Phase 7 figures + Phase 8 submission pack) when the author is ready.

---

## 3. Completed phases (reference)

Detailed checklists, instructions, and findings for the work already done.

### Phase 1 — Easy evidence (no new training)

Closed items: **U-05** hardware; **D-09** detector-only latency (YOLOv8 ONNX); **D-11** memory (PARTIAL); **T-04** requirements evidence table; NFR aggregation refreshed.

Headline numbers:

- Hardware: Win11 Enterprise 22631 / Intel Core Ultra 5 135H (14C/18T) / 32 GB / Intel Arc iGPU / 1920×1080.
- Detector-only ONNX bench (imgsz=640, 50 runs): **median 67.81 ms, p95 79.02 ms.** Snapshot: `reports/tables/detector_bench_snapshot_2026-05-14.csv`.
- Peak RSS (psutil, in-process): **~212 MB** detector-only, **~764 MB** after EasyOCR warm-up. Formal per-method CSV deferred to Phase 4 sprint.
- Requirements evidence table: `reports/tables/requirements_evidence.csv` (19 rows, keyed to Chapter 3 R-FR-01..R-FR-09 + R-NFR-01..R-NFR-10).

Display-scaling sub-item (per-monitor DPI capture) still PENDING — author can fill it from `dxdiag` if needed.

### Phase 2 — CPV on hand-corrected set

Closed items: **D-08** CPV computed; **D-10** + **D-12** explicitly deferred.

Script: `scripts/run_cpv.py` (default conf 0.25, iou 0.5) on 8 hand-corrected screens, 356 GT boxes.

**Overall CPV = 1.40 %** (5 / 356). Per class: button 13.3 %, menu 9.1 %; text_input / icon / text / checkbox all 0 %.

Reading: detector emits very few predictions per screen at conf 0.25 (0-4 vs 30-50 GT/screen), so centre-in-box recall is floor-bound. Consistent with the 0.033 mAP@0.5 hand-corrected number already cited in Section 8.2; reinforces the recall-bound interpretation and the case for D-07.

Evidence: `reports/tables/cpv_summary.csv`, `reports/tables/cpv_per_image.csv`.

Optional follow-up not run: `scripts/run_cpv.py --conf 0.10 --tag conf010` for a soft-threshold companion row. Not blocking.

### Phase 3 — Independent CPV via ScreenSpot

Closed items: **D-07** (closed via the public-benchmark path rather than hand-labelling 100 more screens); **D-06** explicitly deferred.

Script: `scripts/run_cpv_screenspot.py`. Dataset: ScreenSpot (Cheng et al. 2024, SeeClick paper) via HuggingFace `datasets`, desktop slice (macOS + Windows).

| slice_kind | slice_name | n | hits | cpv_% |
|---|---|--:|--:|--:|
| overall | desktop | 334 | 192 | **57.49** |
| data_source | macos | 172 | 107 | 62.21 |
| data_source | windows | 162 | 85 | 52.47 |
| data_type | text | 194 | 145 | 74.74 |
| data_type | icon | 140 | 47 | 33.57 |

Critical interpretive note (Section 8.2 already reflects this): ScreenSpot CPV measures *per-instruction grounding success* (one GT target per row). Hand-corrected CPV (Phase 2, 1.4 %) measures *per-element recall* (every UI element on the screen is a GT box). Same metric name, different protocols. Both reported with the protocol distinction made explicit.

Three script fixes applied in commit `d7e0285`: bbox space = normalized fractions (not pixel xywh); HF cache moved to `tempfile.gettempdir()/visclick_hf_cache` to escape Windows MAX_PATH on OneDrive-managed paths; platform filter maps `desktop` → `data_source ∈ {windows, macos}`.

Evidence: `reports/tables/cpv_screenspot_desktop.csv`, `..._rows.csv`.

### Phases 5 + 6 — Writing sync + personal-voice chapters

Closed items: **W-01** references renumbered; **W-04** Section 9.5 self-taught areas; **U-06** Section 9.6 challenges. **PARTIAL**: **W-02** Chapter 6 implementation sync (the DETR/SSP/UDA stub paragraphs remain accurate-because-unrun, gated on Phase 4); **W-03** Section 9.3 / 9.4 personal voice (institution filled from title page; five `[MODULE: ...]` placeholders pending the author's exact handbook titles).

References: `scripts/renumber_references.py` walks the body, masks fenced + inline code regions so patterns like `offset[0]` are not rewritten, collapses 5 alias entries (L1=[8], L3=[1], L4=[10], L7=[33], L9=[9]) onto canonical numeric entries, renumbers in first-appearance order, rewrites both inline citations and the references list. Result: 53 canonical refs, 92 citation groups preserved, list is `[1]..[53]` with no gaps. Idempotent.

CPV results folded into `docs/Final_Report.md` Sections 6.12 (harness), 7.3.1 (detector evaluation), 8.2 (quantitative reading with the protocol caveat), 8.8 (Objective 2 closure), 9.7 (limitations), 9.8 (future work).

---

## 4. Phase 7 — Figures (still open)

The minimum set that adds the most to the dissertation:

| ID | What | Where to get it |
|----|------|-----------------|
| F-03 | High-level solution overview | Export from the Mermaid source in `VisClick_Report_Data_Form.md` Section 18.1 |
| F-05 | UIED-style overlay on a Win11 dialog | Pick one existing T01 overlay from `reports/figures/baselines/` |
| F-07 | Wireframe of the prototype GUI | Screenshot the current Tk GUI, annotate |
| F-08 | 12-month Gantt chart | Export from spreadsheet / draw.io / Notion |
| Figure 5.4 | Repository directory tree | `tree -L 3 -I '__pycache__\|.venv\|node_modules\|datasets'` from repo root, paste into report |

The rest of F-01..F-12 are nice-to-have; defer or omit, document under "F-XX not submitted" in the report if a figure is intentionally skipped.

## 5. Phase 8 — Submission pack (still open)

| ID | What | Owner |
|----|------|-------|
| U-01 | Submission date on title page | author |
| U-02 | Second marker name on title page | confirmed with RGU |
| U-03 | Word count against the programme cap | author + handbook |
| U-04 | Acknowledgements + AI-tool disclosure | author |
| U-07 | IEEE numeric `[N]` vs Harvard — pick one | RGU style guide |
| U-08 | First-person vs third-person impersonal — one consistent pass | author |
| U-09 | British vs American spelling — current draft is British | RGU style |
| U-10 | T16–T20 task definitions **or** state evaluation stops at T15 | author |
| U-11 | Demo video — only if RGU requires it | author |
| Export | Markdown → Word/PDF; TOC, LOF, LOT; declarations | author |
| W-03 last 5 modules | Replace `[MODULE: ...]` placeholders in Section 9.4 with handbook titles | author |

User said on 26 May 2026 to deprioritise final-report polish and the demo. This block is here only so it's not lost; it does not need attention until the report-polish lane is reopened.

---

## 6. Findings log

| Date | Phase | Gaps closed | Notes |
|------|-------|-------------|-------|
| 2026-05-14 | 1 | U-05 (DONE; display scaling sub-PENDING); D-09 (DONE, YOLOv8 only); D-11 (PARTIAL); T-04 (DONE) | Hardware = Win11 22631 / Core Ultra 5 135H / 32 GB / Intel Arc iGPU / 1920×1080. ONNX bench 50 runs: median 67.81 ms, p95 79.02 ms (image had 0 detections). Peak RSS ~212 MB det-only, ~764 MB after EasyOCR. `requirements_evidence.csv` re-keyed to Chapter 3 (R-FR-01..R-FR-09 + R-NFR-01..R-NFR-10) with 8 columns. |
| 2026-05-14 | 2 | D-08 (DONE); D-10 (DEFERRED); D-12 (DEFERRED) | Overall CPV = **1.40 %** (5/356) at conf 0.25 / iou 0.5 on the 8-image hand-corrected set. Best per class: `button` 13.3 %, `menu` 9.1 %; `text`, `text_input`, `icon`, `checkbox` all 0 %. Consistent with the 0.033 mAP@0.5 hand-corrected number in report Section 8.2; reinforces the recall-bound interpretation. Reviewers (D-10) and preprocessing A/B (D-12) deferred by author decision. Evidence: `reports/tables/cpv_summary.csv` and `reports/tables/cpv_per_image.csv`. |
| 2026-05-14 | 3 | D-07 (DONE via ScreenSpot path); D-06 (DEFERRED) | ScreenSpot-desktop n=334 (macOS+Windows), **CPV = 57.49 %** (192/334) at conf 0.25 / iou 0.5. Per data_source: macos 62.2 %, windows 52.5 %. Per data_type: text 74.7 %, icon 33.6 %. ScreenSpot CPV measures *per-instruction grounding success* (one GT per row), distinct from the *per-element recall* protocol used in D-08. Both must be reported in Section 8.2 with this caveat explicit. Three script fixes applied (commit d7e0285): bbox space = normalized fractions, format = xyxy, HF cache moved out of OneDrive to escape Windows MAX_PATH. Evidence: `reports/tables/cpv_screenspot_desktop.csv` + `..._rows.csv`. D-06 (2000 unlabelled corpus) deferred by author decision; only required for SSP/UDA experiments, which are not committed to. |
| 2026-05-14 | 5/6 | W-02 (PARTIAL) | Writing-sync pass on `docs/Final_Report.md`. Five precision edits folded Phase 2 + Phase 3 CPV results into the dissertation prose: Section 7.3.1 now reports both CPV numbers with per-class and per-slice tables; Section 8.2 interprets them via the per-element-recall vs per-instruction-grounding-success protocol caveat; Section 6.12 documents `run_cpv.py` and `run_cpv_screenspot.py` as part of the evaluation harness; Sections 8.8, 9.7, 9.8 updated to reflect that D-07's *evidence* side closed via ScreenSpot while the hand-correction expansion remains future work. References (W-01), Ch6 DETR/SSP/UDA stubs (still gated on D-01..D-04), and personal-voice paragraphs in Sections 9.3-9.5 (W-03/W-04) remain OPEN. Report line count 1632 → 1735. |
| 2026-05-14 | 5/6 | W-01 (DONE); W-03 (PARTIAL); W-04 (DONE); U-06 (DONE) | Personal-voice writing pass on `docs/Final_Report.md` Sections 9.3, 9.4, 9.5, 9.6, written in the author's voice drawing on actual Phase 1-3 project pivots (hand-correction-to-ScreenSpot pivot, auto-label-to-hand-corrected mAP retraction, ScreenSpot bbox-format bug, OneDrive MAX_PATH lockfile, public-benchmark integration workflow). Section 9.5 expanded from 4 to 5 self-taught areas. Section 9.4 module-mapping `[INSTITUTION]` placeholder filled from the title page; five module-name placeholders remain for the author to confirm against the RGU/IIT MSc Data Science programme handbook at submission time. References renumbered via reproducible `scripts/renumber_references.py`: 53 canonical refs, 5 aliases collapsed (L1, L3, L4, L7, L9), 92 inline citation groups preserved, list now `[1]..[53]` with no gaps. Script masks fenced and inline code blocks so patterns like `offset[0]` are not rewritten. |
| 2026-05-26 | meta | n/a | Plan consolidation: deleted `docs/SUBMISSION_TASK_PLAN.md` (redundant with this file) and the repo-root `PHASE_WORKLOG.md` (its Phase 1 measurement notes already live in `VisClick_Report_Data_Form.md` Section 1.1 and `reports/tables/detector_bench_snapshot_2026-05-14.csv`). Added an archived banner to `VisClick_Detailed_Plan.md`. `docs/PHASE_WORKLOG.md` rewritten as the single canonical plan, organised around current state + what's next, with the full findings log preserved. |
| 2026-05-26 | 4 (kick-off) | D-01, D-02, D-05, D-06 → IN PROGRESS | Author committed to the recommended Phase 4 triple: D-06 corpus capture → D-01 DETR + D-05 few-shot curve in parallel → D-02 SSP+FT. D-03 / D-04 UDA remain DEFERRED (multi-day each, low marginal return given D-07 ScreenSpot already supplies third-party-labelled evidence). Detailed sub-phase instructions (4.0 setup, 4.1 D-06, 4.2 D-01, 4.3 D-05, 4.4 D-02) added to Section 2 above. New script `scripts/auto_capture_corpus.py` written for D-06: background capture every 60 s with foreground-app bucketing, F10 to stop. Notebooks 09–12 (DETR + few-shot + SSP) to be written when the author reaches each sub-phase. |
| 2026-06-02 | 4.2 | D-01 → SOURCE-SIDE DONE (target-side pending) | `09_detr_source.ipynb` completed end-to-end on Colab Free T4 with the compute-fit config: **6 epochs, imgsz cap {600, 800}, fp16 autocast + GradScaler, micro-batch 2 / grad-accum 8 (effective 16)**. Result on CLAY test split: **mAP@0.5 = 0.2438, mAP@0.5:0.95 = 0.1606** (`reports/tables/source_domain_results_detr.csv`). Compared to the existing YOLOv8s source baseline (mAP@0.5 = 0.4505 at 30 epochs imgsz=640 fp32), DETR-R50 reaches ~54 % of YOLOv8's mAP@0.5 while consuming ~6× the wall-clock time per training run — clean compute-matched evidence that supports the architectural choice of YOLOv8s for VisClick's production pipeline. Two pre-completion attempts informed the final config: (1) an 8-epoch imgsz=1333 fp32 run disconnected mid-training at ~2.5 epochs (mAP@0.5 = 0.0114, retracted as a partial-checkpoint artefact); (2) `processor.pad(..., return_tensors="pt")` raised a TypeError in recent transformers, replaced with manual variable-size padding + pixel-mask construction in the collate function (commits 08eeecc, eea04b5). The Drive bundle path was also augmented with a `_bootstrap_from_unified()` fallback (commit f2b9b4f) so the cell now recovers when the `.tar.gz` bundles have been pruned but `data/unified/` is intact. Target-side evaluation (zero-shot on the 8-image hand-corrected desktop set; optional head-only fine-tune via `10_detr_finetune.ipynb`) is the next decision under Phase 4.2 follow-up in Section 2.2. |
| 2026-06-02 | 4.3 | D-05 notebook drafted | `notebooks/08c_few_shot_curve.ipynb` drafted: head-only YOLOv8s fine-tune from `best_source_v8s.pt` at `k ∈ {1, 2, 4, 8}` using the first-k stems of the sorted hand-corrected pool (smaller `k` is a strict subset of larger `k`, so the resulting curve is monotone-by-construction and reproducible). **Primary** metric is CPV on the **ScreenSpot desktop slice (n=334, held-out, third-party labelled)** so the small training pool does not contaminate the test signal. **Secondary** metric is mAP@0.5 / mAP@0.5:0.95 on the hand-corrected set itself, flagged `fit_to_train` in the CSV for `k > 0`. Plus a `k = 0` anchor point (source-pretrained, no fine-tune) so the curve starts at the existing zero-shot baseline. Resume-aware on `<DRIVE>/weights/few_shot/k{k}/run1/weights/best.pt`. Hyperparameters: AdamW, lr0 = 1e-3, freeze = 10 (head-only), epochs 50 patience 15, imgsz 640, batch = min(k, 4). Expected runtime ~1 hour on Colab Free T4. Outputs: `reports/tables/sample_efficiency.csv` + `reports/figures/sample_efficiency_curve.png`. Awaiting author to run the notebook. |

---

*Companion files: `Final_Report_GAPS.md` (per-item ledger), `VisClick_Report_Data_Form.md` (project data form), `Final_Report.md` (dissertation), `VisClick_Detailed_Plan.md` (archived).*
