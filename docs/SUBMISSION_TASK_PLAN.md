# VisClick: submission task plan

**Purpose:** day-to-day checklist. Detailed gap rows and evidence pointers: `Final_Report_GAPS.md`.

**Author priority (locked):** **D → T → W → F → U**

1. **D (DATA)** first: experiments and measurements.
2. **T (TABLE)** second: consolidate CSVs and requirement tables.
3. **W (WRITING)** third: references, Chapter 6 sync, personal Chapter 9.
4. **F (FIGURE)** fourth: diagrams and screenshots (many depend on D).
5. **U (USER)** last: RGU front matter, style, title page, export to PDF.

**Last updated:** 11 May 2026.

---

## 1. What is already done (do not redo)

| Area | Status |
|------|--------|
| Dissertation draft (`docs/Final_Report.md`) | Chapters 1–9 + References, ~36k words |
| Formal scaffolding (`docs/VisClick_Report_Data_Form.md`) | Stakeholders, FR/NFR, risks, diagrams, LEPSI scaffold |
| Core code + harness | `src/visclick/`, four-method baselines, T01–T15 tasks |
| Quantitative evidence | Baseline TSR, NFR latency, transfer tables, hand-corrected mAP story |
| Gaps tracker | `docs/Final_Report_GAPS.md` (43 line items, ordered D–T–W–F–U) |

---

## 2. What is still missing (by bucket)

| Bucket | Count | When you work it |
|--------|------:|------------------|
| **D** | 12 | **Now** (Track 1) |
| **T** | 4 | After the D items each row needs |
| **W** | 4 | After major D/T stable; **W-01** just before final PDF |
| **F** | 12 | After D/T (or skip purely decorative ones) |
| **U** | 11 | **Last** (Track 5) |

---

## 3. Track 1: DATA (D) — do first

Use `[ ]` / `[x]`; match IDs in `Final_Report_GAPS.md`.

**Foundation (unblocks D-05, D-02–D-04):**

- [ ] **D-07** Hand-correct labelled desktop set toward 100 images (minimum: extend beyond 8).
- [ ] **D-06** Unlabelled desktop capture toward ~2k *if* you run SSP/UDA; else document deferral in report Section 9.8.

**Heavy experiments (triage with supervisor):**

- [ ] **D-01** DETR source + fine-tune; feeds **T-01**, **W-02**.
- [ ] **D-05** Few-shot curve ($k = 1,5,10,50,100$); feeds **T-02**, **F-11**.
- [ ] **D-02** SSP + fine-tune (needs **D-06**); feeds **T-02**.
- [ ] **D-03** Adaptive Teacher; feeds **T-03**, **W-02**.
- [ ] **D-04** SHOT; feeds **T-03**, **W-02**.

**Lighter / parallel (good ROI without full Phase 2):**

- [ ] **D-08** CPV metric beside mAP.
- [ ] **D-09** Detector-only inference timing.
- [ ] **D-10** 2 reviewers on T01–T15; feeds Section 8.3 and **F-12**.
- [ ] **D-11** Peak RSS → `nfr_memory.csv`; closes R-NFR-03.
- [ ] **D-12** Preprocessing A/B on TSR.

**Suggested order:** **D-07** early; then **D-08, D-09, D-11, D-12** in parallel with whatever heavy D you choose; **D-06** before **D-02–D-04**; **D-01** before claiming DETR in **T-01**.

---

## 4. Track 2: TABLE (T) — after D

- [ ] **T-04** Master FR/NFR evidence table (can start anytime; uses existing CSVs).
- [ ] **T-01** Extend transfer / model comparison table (YOLO complete; add DETR after **D-01**).
- [ ] **T-02** Sample-efficiency table (after **D-05** ± **D-02**).
- [ ] **T-03** UDA comparison table (after **D-03** and **D-04**).

Paste or link final numbers into `Final_Report.md` where chapters already point to those tables.

---

## 5. Track 3: WRITING (W) — after D/T settle

- [ ] **W-02** Chapter 6: align implementation prose with whatever D experiments you actually ran.
- [ ] **W-03** Chapter 9.3–9.4: personal learning outcomes + relevant modules.
- [ ] **W-04** Chapter 9.5: self-taught areas (tighten placeholders).
- [ ] **W-01** Renumber references = **first appearance order** in full dissertation (**do this last among W**, right before final export).

---

## 6. Track 4: FIGURE (F) — defer

Do **after** the numbers and tables you want to illustrate exist.

Minimum set if time is short: **F-03**, **F-05**, **F-08**, **F-07**, repository tree (**Figure 5.4** in report). Full list: `Final_Report_GAPS.md` (F-01–F-12).

- [ ] **F-10** after detector eval refresh (**D** / notebook).
- [ ] **F-11** after **T-02** / **D-05**.
- [ ] **F-12** after **D-10**.

---

## 7. Track 5: USER (U) — last

Do **after** figures embedded and text frozen except final proofread.

- [ ] **U-07** RGU reference style (IEEE vs Harvard).
- [ ] **U-08** Voice (I vs impersonal) — one consistent pass.
- [ ] **U-09** British vs American spelling.
- [ ] **U-03** Word count vs programme cap.
- [ ] **U-01** Submission date on title page.
- [ ] **U-02** Second marker name.
- [ ] **U-04** Acknowledgements + AI disclosure per rules.
- [ ] **U-05** Hardware spec in data form; align Chapter 7 latency text.
- [ ] **U-06** Reflection Section 9.6 (YOLO vs DETR effort).
- [ ] **U-10** Define T16–T20 **or** state explicitly evaluation ends at T15.
- [ ] **U-11** Demo video only if required.
- [ ] Export `Final_Report.md` → faculty Word/LaTeX; TOC, LOF, LOT; final PDF + declarations.

---

## 8. If you run out of time

1. Finish **D** items your supervisor marks as mandatory; document the rest under Section 9.7–9.8.
2. **T-04** + partial **T-01** still strengthen the report without every experiment.
3. **W-01** + **U-*** are required for submission hygiene; do not skip **U** entirely, only **defer** it to the end as planned.

---

## 9. Gap ID quick map

| Track | IDs |
|-------|-----|
| 1 D | D-01 … D-12 |
| 2 T | T-01 … T-04 |
| 3 W | W-01 … W-04 |
| 4 F | F-01 … F-12 |
| 5 U | U-01 … U-11 |

---

*Owner: Hiran Abeywardhana. Keep this file in sync when you mark items DONE in `Final_Report_GAPS.md`.*
