# Phase worklog — VisClick dissertation

**How to use this file**

1. Work **one phase at a time** from top to bottom.
2. For each step, do the action on your machine, then tick `[x]` when it is truly done.
3. Paste **short results** under **Your notes for this phase** (numbers, file paths, one screenshot link, whatever helps).
4. Tell the chat: *"Phase N complete"* + paste your notes. The gaps tracker (`Final_Report_GAPS.md`) can then be updated to **DONE** for the IDs that phase closes.
5. Commit and push the repo when a phase produces new CSVs or images.

**Gap IDs** refer to `docs/Final_Report_GAPS.md`.

---

## Current phase (fill in)

**You are on:** **Phase 5 / 6 — writing sync done (W-02 PARTIAL); next is W-01 (reference renumbering) and W-03/W-04 (author personal voice in Sections 9.3-9.5).** Phases 1, 2, 3 complete; Phase 4 heavy retraining is opt-in and currently deferred.

**Last updated by:** assistant, 14 May 2026.

**Companion file:** `PHASE_WORKLOG.md` at the **repo root** holds your raw local notes per phase (hardware bullets, bench numbers, paths). This `docs/PHASE_WORKLOG.md` keeps the **phase definitions, checklists, and findings log**.

---

## Phase 1 — Evidence that does not need new training

**Goal:** Close easy **D** items and start **T-04**. No Colab training yet.

| Step | Gap | What you do | You should get |
|-----|-----|-------------|----------------|
| 1.1 | **U-05** | On your Windows test PC run `dxdiag` (save report) or in PowerShell: `systeminfo`. Copy **OS, CPU, RAM, GPU (if any)** into a short bullet list. | Paste the same bullets into `VisClick_Report_Data_Form.md` (hardware section) **and** below under **Your notes**. |
| 1.2 | **D-09** (detector-only speed) | From repo root: `py -3 scripts/test_detector.py` on a real screenshot (see script `--help`). Use `--bench 50` on your headline ONNX. Note **median_ms** and **p95_ms** printed as `REPORT bench \| ...`. | Write those two numbers in **Your notes**. Optional: confirm row appended under `tables/detector_latency.csv` if the script does that. |
| 1.3 | **D-11** (memory) | During **one full method run** (e.g. VisClick on 3 tasks), open **Task Manager → Performance → Memory** and note **peak commit / working set** for the Python process, **or** run a small `psutil` snippet if you prefer code. Repeat idea for **ocr_only** if quick. | Table in **Your notes**: method name → peak MB (approx is OK). Save file `reports/tables/nfr_memory.csv` if you make one; else paste numbers only. |
| 1.4 | **T-04** | Create `reports/tables/requirements_evidence.csv` with one row per requirement. **Minimum columns:** `req_id`, `evidence_type`, `summary_verdict`, `notes`. Use Chapter 3 tables plus existing `baseline_per_task.csv`, `nfr_performance.csv`. | New CSV committed; first draft is enough (you can refine later). |
| 1.5 | **Run NFR aggregation** (if not fresh) | `py -3 scripts/run_nfr.py` so `nfr_performance.csv` matches latest `baseline_results.csv`. | Confirm file timestamps / numbers look right. |

**Phase 1 checklist**

- [x] Step 1.1 U-05 hardware captured (display **scaling** still PENDING)
- [x] Step 1.2 D-09 detector bench numbers recorded (50 runs on `logo2.png`, n_detections=0; re-run on a real screenshot is nice-to-have)
- [x] Step 1.3 D-11 peak memory recorded (rough psutil RSS; formal per-method `nfr_memory.csv` PARTIAL)
- [x] Step 1.4 T-04 requirements_evidence.csv created (re-keyed to Chapter 3 R-FR-01..R-FR-09 + R-NFR-01..R-NFR-10)
- [x] Step 1.5 run_nfr.py refreshed

**Gaps closed:** U-05 (DONE, scaling PENDING sub-item), D-09 (DONE, YOLOv8 only), D-11 (PARTIAL), T-04 (DONE).

### Your notes for Phase 1

See repo-root `PHASE_WORKLOG.md` and `docs/VisClick_Report_Data_Form.md` Section 1.1.

Headline numbers:

- Hardware: Win11 Enterprise 22631 / Intel Core Ultra 5 135H (14C/18T) / 32 GB / Intel Arc iGPU / 1920×1080.
- Detector-only (ONNX, imgsz=640, 50 runs): **median 67.81 ms, p95 79.02 ms**. Snapshot: `reports/tables/detector_bench_snapshot_2026-05-14.csv`.
- Peak RSS (psutil, in-process, same session): **~212 MB** detector-only, **~764 MB** after EasyOCR `text_ground` warm-up.
- Requirements evidence: `reports/tables/requirements_evidence.csv` (19 rows, keyed to Chapter 3 wording, with `evidence_file` pointing at the CSV/figure backing each verdict).

---

## Phase 2 — CPV, optional preprocessing A/B, reviewers

**Goal:** **D-08**, optional **D-12**, optional **D-10**.

| Step | Gap | What you do | You should get |
|-----|-----|-------------|----------------|
| 2.1 | **D-08** | In Colab or local: open `08_phase1B_ablations.ipynb` (or your eval notebook). For each predicted box vs GT box on the hand-corrected set, mark CPV = 1 if **predicted centre falls inside GT box**, else 0. Report **CPV rate** (%) and keep **mAP@0.5** alongside. | Numbers in **Your notes** + optional `reports/tables/cpv_summary.csv`. |
| 2.2 | **D-12** (optional) | Only if time: add bilateral/CLAHE before detect; re-run T01–T15 for VisClick only; compare TSR to current. | Delta TSR in **Your notes**. |
| 2.3 | **D-10** (optional) | Ask **2 colleagues** to run **3–5 tasks** each (or watch you). They send **3–5 sentences** feedback. | Paste anonymised quotes in **Your notes**; later use for report Section 8.3 and **F-12**. |

**Phase 2 checklist**

- [x] D-08 CPV computed via `scripts/run_cpv.py` (default conf 0.25)
- [x] D-12 **DEFERRED** (author decision; future work in Section 9.7)
- [x] D-10 **DEFERRED** (author decision; report keeps single-rater qualitative scope)

### Your notes for Phase 2

CPV on hand-corrected test set, ONNX detector at default conf 0.25 / iou 0.50.

**Overall CPV = 1.40 %**  (5 hits / 356 GT boxes)

Per class:

| class | gt | hit | cpv_% |
|-------|---:|---:|------:|
| button | 15 | 2 | 13.33 |
| text | 20 | 0 | 0.00 |
| text_input | 189 | 0 | 0.00 |
| icon | 89 | 0 | 0.00 |
| menu | 33 | 3 | 9.09 |
| checkbox | 10 | 0 | 0.00 |
| OVERALL | 356 | 5 | 1.40 |

Reading: the detector emits very few predictions per image at conf 0.25 (0-4 versus 30-50 GT boxes), so centre-in-box recall is naturally floor-bound. Consistent with the 0.033 mAP@0.5 hand-corrected number already in Section 8.2. The 78 % of GT boxes that are `text_input` + `icon` get zero CPV hits, which is the same recall ceiling the report flags under R-NFR-03 / gap D-07.

CSV evidence:

- `reports/tables/cpv_summary.csv` (per-class + OVERALL)
- `reports/tables/cpv_per_image.csv` (per-image with prediction counts)

Optional follow-up not run yet: `scripts/run_cpv.py --conf 0.10 --tag conf010` to publish a soft-threshold companion row. Worth doing later if the report wants a precision-vs-recall sensitivity sentence; not blocking Phase 3.

---

## Phase 3 — More test data via a public benchmark (ScreenSpot)

**Goal:** Close **D-07** by adding an *independent, third-party-labelled* CPV row from a public benchmark instead of hand-labelling 100 more screens. Skip **D-06** unless SSP/UDA is also planned.

**Rationale:** the 8-image hand-corrected set is fragile (n is too small for stable per-class numbers). Rather than spend a day in CVAT, we evaluate the same ONNX detector against **ScreenSpot's desktop slice** (~280-310 real Windows/macOS screens, labelled by the SeeClick authors, used as a benchmark in other GUI grounding papers). CPV is class-agnostic, so the taxonomy mismatch (their `text|icon` vs our 6 classes) doesn't matter for the headline number. The hand-corrected set stays in the report for the *class-aware* mAP and CPV; ScreenSpot supplies the *out-of-domain, larger-N* row.

| Step | Gap | What you do | You should get |
|-----|-----|-------------|----------------|
| 3.1 | **D-07** | On your Windows machine, inside the project venv: `pip install datasets`. (First-time only; ~30 MB of wheels.) | `datasets` importable from your venv. |
| 3.2 | **D-07** | Smoke test first: `.\.venv\Scripts\python.exe scripts/run_cpv_screenspot.py --limit 20`. This downloads the dataset (~70 MB, cached at `datasets/_hf_cache/`) and processes 20 rows. | A printed `REPORT cpv_screenspot \| platform=desktop overall = X.XX% (..)`. CSVs in `reports/tables/`. |
| 3.3 | **D-07** | Full run: `.\.venv\Scripts\python.exe scripts/run_cpv_screenspot.py`. Should take 1-3 minutes on the iGPU. | `reports/tables/cpv_screenspot_desktop.csv` (overall + per-data-source + per-data-type) and `..._rows.csv`. |
| 3.4 | **D-07** | Paste the printed `REPORT cpv_screenspot ...` line below under **Your notes** plus the per-slice (`data_source`, `data_type`) numbers from the console. | A short results block we can fold into Section 8.2 in Phase 6 (writing sync). |
| 3.5 | **D-06** | Explicit decision: **DEFERRED** unless you commit to a Phase 4 SSP/UDA experiment that consumes the 2000 unlabelled PNGs. | A one-line confirmation below. |

**If HuggingFace is blocked by Synopsys VPN:** tell me and I'll add a fallback path (snapshot-download via `huggingface-cli` on a personal laptop, then copy the cache folder across).

**Phase 3 checklist**

- [x] `pip install datasets` succeeded in the venv
- [x] Smoke test `--limit 20` produced numbers
- [x] Full `run_cpv_screenspot.py` produced `cpv_screenspot_desktop.csv`
- [x] Headline CPV % and per-slice numbers pasted below
- [x] D-06 explicitly deferred

**Script fixes applied during Phase 3** (commit `d7e0285`): ScreenSpot HF rows store bbox as **normalized xyxy fractions** (0..1 of W,H), not pixel xywh as I had defaulted; the script now defaults to `--bbox-space normalized --bbox-format xyxy`. Also moved the HF cache to `tempfile.gettempdir()/visclick_hf_cache` because the original under-OneDrive cache path overflowed Windows MAX_PATH on lockfile names. Filter logic also corrected: `--platform-prefix desktop` now maps to `data_source ∈ {windows, macos}` (HF schema doesn't use a `desktop_` prefix).

### Your notes for Phase 3

ScreenSpot CPV on the ONNX detector at default conf 0.25 / iou 0.50:

| slice_kind | slice_name | n | hits | cpv_% |
|---|---|--:|--:|--:|
| overall | desktop | 334 | 192 | **57.49** |
| data_source | macos | 172 | 107 | 62.21 |
| data_source | windows | 162 | 85 | 52.47 |
| data_type | text | 194 | 145 | 74.74 |
| data_type | icon | 140 | 47 | 33.57 |

D-06 status = **DEFERRED** (Author decision; only needed if Phase 4 SSP/UDA experiments commit to running, which they are not at this point.)

**Interpretation (critical for Section 8.2 prose):** ScreenSpot CPV (57.5 %) is *per-instruction grounding success* — one GT target per row, "did any prediction land in it?" Hand-corrected CPV (1.4 %, from Phase 2 / D-08) is *per-element recall* — every UI element on the screen is a GT box, ~44/screen × 8 screens = 356 GT boxes total. Same metric name, different protocols, different denominators. The 57.5 % puts VisClick's detector in the same ballpark as published LLM grounders on the same benchmark (SeeClick paper reports ~30-50 % on ScreenSpot-desktop). The 1.4 % stays as the recall ceiling on Win11 native screens. Section 8.2 must report both with the protocol distinction made explicit.

CSV evidence:

- `reports/tables/cpv_screenspot_desktop.csv` (overall + per-slice)
- `reports/tables/cpv_screenspot_desktop_rows.csv` (334 per-row hits)
- `reports/tables/cpv_summary.csv` and `cpv_per_image.csv` (from Phase 2, hand-corrected)

---

## Phase 4 — Heavy experiments (agree with supervisor first)

**Goal:** Pick a subset: **D-01** DETR, **D-05** few-shot curve, **D-02 / D-03 / D-04**.

**Rule:** Do **not** start all of these. Mark **which IDs you commit to** in **Your notes**.

**Phase 4 checklist**

- [ ] D-01 DETR: done / skipped
- [ ] D-05 few-shot curve: done / skipped
- [ ] D-02 SSP: done / skipped
- [ ] D-03 Adaptive Teacher: done / skipped
- [ ] D-04 SHOT: done / skipped

### Your notes for Phase 4

```
Chosen experiments: 
Key numbers / new CSV paths: 
```

---

## Phase 5 — Tables (T)

**Goal:** Refresh **`transfer_experiments.csv`** and add **T-01, T-02, T-03** as far as data allows.

| Step | Gap | What you do |
|-----|-----|-------------|
| 5.1 | **T-01** | Add DETR rows only if D-01 done; else keep YOLO-only and write *DETR not run* in notes column. |
| 5.2 | **T-02** | Only if D-05 (and optional D-02) done. |
| 5.3 | **T-03** | Only if D-03 and D-04 done. |
| 5.4 | **Final_Report.md** | Paste final table snippets or reference CSV paths in Chapters 6–8 where you already discuss metrics. |

**Phase 5 checklist**

- [ ] T-01 updated
- [ ] T-02 done or N/A
- [ ] T-03 done or N/A
- [ ] Report prose synced to tables

### Your notes for Phase 5

```
(paste here when done)
```

---

## Phase 6 — Writing (W)

**Goal:** **W-02** (Chapter 6 vs actual code), **W-03 / W-04** (personal Chapter 9), **W-01** last pass on references.

**Phase 6 checklist**

- [ ] W-02 Chapter 6 matches what you built
- [ ] W-03 / W-04 placeholders replaced with your voice
- [ ] W-01 bibliography order = first citation order in dissertation

### Your notes for Phase 6

```
(paste here when done)
```

---

## Phase 7 — Figures (F)

**Goal:** Work through **F-01–F-12** in `Final_Report_GAPS.md`. Minimum practical set: **F-03, F-05, F-08, F-07**, repo tree **Figure 5.4**.

**Phase 7 checklist**

- [ ] Minimum figure set exported into `reports/figures/`
- [ ] Optional figures done or marked *not submitted*

### Your notes for Phase 7

```
(list PNG paths)
```

---

## Phase 8 — Submission pack (U)

**Goal:** All **U-*** except **U-05** if already done in Phase 1.

| Step | IDs | What you do |
|-----|-----|-------------|
| 8.1 | U-07, U-08, U-09 | Confirm style with handbook; one voice/spelling pass. |
| 8.2 | U-01, U-02, U-03, U-04 | Title page, word count, acknowledgements. |
| 8.3 | U-10 | Define T16–T20 **or** state in report evaluation stops at T15. |
| 8.4 | U-11 | Demo video only if required. |
| 8.5 | Export | Word/PDF, TOC, LOF, LOT, declarations. |

**Phase 8 checklist**

- [ ] Style and front matter complete
- [ ] Final PDF ready for upload

### Your notes for Phase 8

```
(paste submission date / any examiner-facing notes)
```

---

## Findings log (running summary)

Append a row when a phase finishes.

| Date | Phase | Gaps marked DONE / PARTIAL | Notes |
|------|-------|----------------------------|-------|
| 2026-05-14 | 1 | U-05 (DONE; display scaling sub-PENDING); D-09 (DONE, YOLOv8 only); D-11 (PARTIAL); T-04 (DONE) | Hardware = Win11 22631 / Core Ultra 5 135H / 32 GB / Intel Arc iGPU / 1920×1080. ONNX bench 50 runs: median 67.81 ms, p95 79.02 ms (image had 0 detections). Peak RSS ~212 MB det-only, ~764 MB after EasyOCR. `requirements_evidence.csv` re-keyed to Chapter 3 (R-FR-01..R-FR-09 + R-NFR-01..R-NFR-10) with 8 columns. |
| 2026-05-14 | 2 | D-08 (DONE); D-10 (DEFERRED); D-12 (DEFERRED) | Overall CPV = **1.40 %** (5/356) at conf 0.25 / iou 0.5 on the 8-image hand-corrected set. Best per class: `button` 13.3 %, `menu` 9.1 %; `text`, `text_input`, `icon`, `checkbox` all 0 %. Consistent with the 0.033 mAP@0.5 hand-corrected number in report Section 8.2; reinforces the recall-bound interpretation. Reviewers (D-10) and preprocessing A/B (D-12) deferred by author decision. Evidence: `reports/tables/cpv_summary.csv` and `reports/tables/cpv_per_image.csv`. |
| 2026-05-14 | 3 | D-07 (DONE via ScreenSpot path); D-06 (DEFERRED) | ScreenSpot-desktop n=334 (macOS+Windows), **CPV = 57.49 %** (192/334) at conf 0.25 / iou 0.5. Per data_source: macos 62.2 %, windows 52.5 %. Per data_type: text 74.7 %, icon 33.6 %. ScreenSpot CPV measures *per-instruction grounding success* (one GT per row), distinct from the *per-element recall* protocol used in D-08. Both must be reported in Section 8.2 with this caveat explicit. Three script fixes applied (commit d7e0285): bbox space = normalized fractions, format = xyxy, HF cache moved out of OneDrive to escape Windows MAX_PATH. Evidence: `reports/tables/cpv_screenspot_desktop.csv` + `..._rows.csv`. D-06 (2000 unlabelled corpus) deferred by author decision; only required for SSP/UDA experiments, which are not committed to. |
| 2026-05-14 | 5/6 | W-02 (PARTIAL) | Writing-sync pass on `docs/Final_Report.md`. Five precision edits folded Phase 2 + Phase 3 CPV results into the dissertation prose: Section 7.3.1 now reports both CPV numbers with per-class and per-slice tables; Section 8.2 interprets them via the per-element-recall vs per-instruction-grounding-success protocol caveat; Section 6.12 documents `run_cpv.py` and `run_cpv_screenspot.py` as part of the evaluation harness; Sections 8.8, 9.7, 9.8 updated to reflect that D-07's *evidence* side closed via ScreenSpot while the hand-correction expansion remains future work. References (W-01), Ch6 DETR/SSP/UDA stubs (still gated on D-01..D-04), and personal-voice paragraphs in Sections 9.3-9.5 (W-03/W-04) remain OPEN. Report line count 1632 → 1735. |

---

*Owner: Hiran Abeywardhana. Companion to `SUBMISSION_TASK_PLAN.md` and `Final_Report_GAPS.md`.*
