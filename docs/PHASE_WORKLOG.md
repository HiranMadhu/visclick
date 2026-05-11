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

**You are on:** Phase 1 — not started

**Last updated by:** (you / assistant + date)

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

- [ ] Step 1.1 U-05 hardware captured
- [ ] Step 1.2 D-09 detector bench numbers recorded
- [ ] Step 1.3 D-11 peak memory recorded (at least VisClick)
- [ ] Step 1.4 T-04 requirements_evidence.csv created
- [ ] Step 1.5 run_nfr.py run if needed

**Gaps this phase can close (after review):** U-05 (hardware captured), D-09, D-11, T-04. **D-08** is Phase 2 (notebook).

### Your notes for Phase 1

```
(paste here when done)
```

---

## Phase 2 — CPV, optional preprocessing A/B, reviewers

**Goal:** **D-08**, optional **D-12**, optional **D-10**.

| Step | Gap | What you do | You should get |
|-----|-----|-------------|----------------|
| 2.1 | **D-08** | In Colab or local: open `08_phase1B_ablations.ipynb` (or your eval notebook). For each predicted box vs GT box on the hand-corrected set, mark CPV = 1 if **predicted centre falls inside GT box**, else 0. Report **CPV rate** (%) and keep **mAP@0.5** alongside. | Numbers in **Your notes** + optional `reports/tables/cpv_summary.csv`. |
| 2.2 | **D-12** (optional) | Only if time: add bilateral/CLAHE before detect; re-run T01–T15 for VisClick only; compare TSR to current. | Delta TSR in **Your notes**. |
| 2.3 | **D-10** (optional) | Ask **2 colleagues** to run **3–5 tasks** each (or watch you). They send **3–5 sentences** feedback. | Paste anonymised quotes in **Your notes**; later use for report Section 8.3 and **F-12**. |

**Phase 2 checklist**

- [ ] D-08 CPV computed
- [ ] D-12 skipped or done (note which)
- [ ] D-10 skipped or done (note which)

### Your notes for Phase 2

```
(paste here when done)
```

---

## Phase 3 — More data (labels + unlabelled)

**Goal:** **D-07**, optional **D-06**.

| Step | Gap | What you do |
|-----|-----|-------------|
| 3.1 | **D-07** | Annotate **more desktop screens** in CVAT/Roboflow (target: move toward **100**; any increase above **8** helps). Export YOLO labels into `datasets/handcorrected_desktop_test/` (or new folder) and update eval YAML if paths change. |
| 3.2 | **D-06** | Only if you will run **SSP or UDA**: extend `capture_screenshots.py` usage toward **~2000** unlabelled PNGs; else **skip** and write *deferred* in Section 9.8 of the report later. |

**Phase 3 checklist**

- [ ] D-07: N new images annotated (write N below)
- [ ] D-06: done or explicitly deferred

### Your notes for Phase 3

```
N new labelled images = 
D-06 status = 
```

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

| Date | Phase | Gaps marked DONE | Notes |
|------|-------|------------------|-------|
|  |  |  |  |

*(Add a new row after each "Phase N complete" message.)*

---

*Owner: Hiran Abeywardhana. Companion to `SUBMISSION_TASK_PLAN.md` and `Final_Report_GAPS.md`.*
