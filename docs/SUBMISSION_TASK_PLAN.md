# VisClick: submission task plan

**Purpose:** turn the draft dissertation and code into a marker-ready submission. This file is the day-to-day checklist. Detailed gap IDs and evidence pointers live in `Final_Report_GAPS.md`.

**Last updated:** 11 May 2026.

---

## 1. What is already done (do not redo)

| Area | Status |
|------|--------|
| Dissertation draft (`docs/Final_Report.md`) | Chapters 1–9 + References, ~36k words |
| Formal scaffolding (`docs/VisClick_Report_Data_Form.md`) | Stakeholders, FR/NFR, risks, diagrams, LEPSI scaffold |
| Core code + harness | `src/visclick/`, four-method baselines, T01–T15 tasks |
| Quantitative evidence | Baseline TSR, NFR latency, transfer tables, hand-corrected mAP story |
| Gaps tracker | `docs/Final_Report_GAPS.md` (43 line items) |

---

## 2. What is still missing (summary by type)

| Type | Count | Typical effort |
|------|------:|----------------|
| **DATA** (new runs, metrics) | 12 | Hours to weeks each |
| **FIGURE** (PNG exports, composites) | 12 | Minutes to hours each |
| **TABLE** (consolidate CSVs) | 4 | ~30 min to hours |
| **WRITING** (citations, personal voice) | 4 | 1–2 sessions |
| **USER** (RGU/front matter, style, hardware) | 11 | Half-day + approvals |

**Cross-cutting:** Many TABLE and FIGURE items depend on DATA items (for example T-02 needs D-05). The plan below orders work so dependencies are respected.

---

## 3. Phased task plan (what to do in order)

Use the checkboxes as you complete work. Change `[ ]` to `[x]` and optionally commit with message `docs: SUBMISSION_TASK_PLAN progress`.

### Phase 0: Admin and house style (before binding)

These are mostly USER and WRITING items. No new experiments.

- [ ] **U-07** Confirm reference style with RGU Handbook: IEEE `[1]` vs Harvard `(Author, Year)`.
- [ ] **U-08** Pick voice: first-person vs impersonal; then edit Chapters 1–9 consistently.
- [ ] **U-09** Confirm British vs American spelling; run a pass if required.
- [ ] **W-01** Renumber references so bibliography order matches **first appearance** in the dissertation (gap tracker calls this out).
- [ ] **U-03** Check word count vs programme limit; trim or flag overflow sections.
- [ ] **U-01** Fill submission date on title page.
- [ ] **U-02** Fill second marker name when RGU confirms it.
- [ ] **U-04** Write Acknowledgements (supervisor, second marker, family, AI-tool disclosure per programme rules).
- [ ] **U-05** Paste hardware spec (`dxdiag` / `systeminfo`) into data form Section 1.1; align latency claims in Chapter 7.
- [ ] Export `Final_Report.md` to your faculty template (Word / LaTeX / PDF) and fix headings, page breaks, and figure placement there.

### Phase 1: Minimum viable figures (high visual impact, low dependency)

Pick a subset if time is tight. Suggested minimum set for a strong first impression:

- [ ] **F-03** Solution overview block diagram (export from Mermaid in data form Section 18.1).
- [ ] **F-05** One Win11 overlay from existing baseline figures (UIED-style).
- [ ] **F-08** Gantt or timeline for the four project phases.
- [ ] **F-07** GUI wireframe or annotated screenshot of real Tk window.
- [ ] **Figure 5.4** Repository tree PNG (as promised in Chapter 5: `tree -L 3` or draw.io).

Optional but valuable:

- [ ] **F-01** Domain shift three-panel composite.
- [ ] **F-02** Positioning 2×2 grid.
- [ ] **F-04** RICO vs CLAY pair.
- [ ] **F-06** UML use case diagram.
- [ ] **F-09** CVAT/Roboflow screenshot.
- [ ] **F-10** Confusion matrix from notebook.
- [ ] **F-11** After D-05 only: sample-efficiency curve.
- [ ] **F-12** After D-10 only: reviewer feedback redacted screenshots.

### Phase 2: Evaluation defensibility (no new models)

Strengthens Chapter 7–8 without DETR/UDA.

- [ ] **D-11** Peak RSS per method during T01–T15; write `nfr_memory.csv`; close R-NFR-03 in prose.
- [ ] **D-08** Add CPV alongside mAP in evaluation notebook; one paragraph + optional table in report.
- [ ] **D-09** Optional: separate detector-only timing vs full pipeline in `run_nfr` or a small script.
- [ ] **D-10** Two reviewers run T01–T15; collect short written feedback; update Section 8.3 + **F-12**.
- [ ] **T-04** Export one master CSV (or Word table) mapping every R-FR / R-NFR to evidence file + verdict.
- [ ] **T-01** (partial) Refresh transfer table with **only YOLO** rows if DETR slips; leave DETR rows blank or "Not run" per programme rules.

### Phase 3: Data and labels (largest accuracy gain for time)

- [ ] **D-07** Expand hand-corrected desktop test set toward 100 images (or as many as you can before deadline).
- [ ] **D-06** If pursuing SSP/UDA: grow unlabelled desktop capture toward 2,000 screens; else **document deferral** in Section 9.8.
- [ ] **D-05** Few-shot curve $k \in \{1,5,10,50,100\}$ once D-07 gives enough labels **or** honestly scope to available $k$.
- [ ] **U-10** Fill **T16–T20** in task JSON **or** state in report that evaluation stops at T15 (align with programme expectations).

### Phase 4: Proposal-stretch experiments (optional; triage before starting)

Complete only if time remains after Phase 0–3. Each unlocks new report prose (**W-02**) and tables **T-01–T-03**.

- [ ] **D-01** DETR source + fine-tune notebooks; extend transfer CSV; update RQ3 answer.
- [ ] **D-02** SSP pretrain + fine-tune (needs **D-06** corpus).
- [ ] **D-03** Adaptive Teacher UDA.
- [ ] **D-04** SHOT UDA.
- [ ] **D-12** Preprocessing A/B on T01–T15.

### Phase 5: Final polish

- [ ] **W-03** Personal paragraphs: Learning outcomes (Section 9.3) and relevant modules (Section 9.4).
- [ ] **W-04** Personal paragraph: Self-taught areas refinement (Section 9.5).
- [ ] **U-06** Short reflection in Section 9.6 (YOLO vs DETR difficulty), even if DETR was not run ("did not complete DETR; YOLO consumed X hours…").
- [ ] **U-11** Record demo video if programme or supervisor expects multimedia evidence; otherwise note "not submitted" in appendices.
- [ ] Spell-check, consistency pass on acronyms (TSR, mAP, CPV, IVGocr).
- [ ] Final PDF: table of contents, list of figures, list of tables, plagiarism/AI declaration per RGU.

---

## 4. Triage rule (so you do not drown)

1. **Phase 0** and **Phase 1** are usually enough for a **defensible** MSc submission **if** the written argument and existing numbers are honest (including partial RQ2/RQ3).
2. **Phase 2** turns "good draft" into "hard to argue with" on evaluation.
3. **Phase 3** improves science more than **Phase 4** for equal hours, if the story is detector + OCR + refusal.
4. **Phase 4** is for programmes that **require** every proposal experiment: confirm with supervisor before committing weeks.

If you defer Phase 4, add one explicit paragraph in Section 9.7 Limitations and Section 9.8 Future work stating which proposal items were not completed and why (time, compute, data).

---

## 5. Link to gap IDs

| Phase | Main gap IDs |
|-------|----------------|
| 0 | U-01–U-09, W-01 |
| 1 | F-01–F-09, Figure 5.4 tree |
| 2 | D-08, D-09, D-10, D-11, T-01 (partial), T-04, F-10, F-12 |
| 3 | D-05, D-06, D-07, U-10 |
| 4 | D-01–D-04, D-12, T-01–T-03, W-02, F-11 |
| 5 | W-03, W-04, U-06, U-11 |

---

*Owner: Hiran Abeywardhana. Sync this file when you close items in `Final_Report_GAPS.md`.*
