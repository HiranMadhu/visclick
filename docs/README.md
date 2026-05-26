# `docs/` — VisClick dissertation source documents

This folder is the canonical, version-controlled home of every long-form document driving the project. There are now **five live files** and **one archived file**:

| File | Role | When to read it |
|------|------|-----------------|
| `Final_Report.md` | The dissertation itself (Chapters 1-9 + References). | When writing or polishing the report. |
| `PHASE_WORKLOG.md` | **Canonical "where are we / what's next" plan.** Phase 1-8 status, current state at a glance, next-sprint recommendations, full findings log. | At the start of any session, or whenever you ask "what's left?". |
| `Final_Report_GAPS.md` | Per-item ledger of every D / T / W / F / U gap with status + evidence pointers. | When you want to know the state of one specific item (e.g. "is D-08 done?"). |
| `VisClick_Report_Data_Form.md` | Structured project data form: hardware spec, per-model results, prototype integration notes, architecture diagrams, observations. The dissertation's underlying data source. | While running experiments (to record results) and while writing prose around the numbers. |
| `VisClick_Detailed_Plan.md` | **ARCHIVED.** The original multi-phase "how-to-build" plan from early in the project. Superseded by `PHASE_WORKLOG.md`. | Only when you want to understand earlier reasoning; do not follow it step-by-step. |
| `README.md` | This file. | When the folder layout changes. |

## Relationship between the three living planning files

`PHASE_WORKLOG.md` is the **plan** (chronological, phase-by-phase, with checklists and a findings log).
`Final_Report_GAPS.md` is the **ledger** (one row per ID, queryable by ID).
`VisClick_Report_Data_Form.md` is the **data form** (the actual numbers, observations, and diagrams the dissertation cites).

When something gets done, update all three: tick the checklist in `PHASE_WORKLOG.md`, flip the status in `Final_Report_GAPS.md`, paste any new numbers into `VisClick_Report_Data_Form.md`.

## Files that used to be here but are no longer

| File | Removed | Reason |
|------|---------|--------|
| `SUBMISSION_TASK_PLAN.md` | 26 May 2026 | Redundant with `PHASE_WORKLOG.md`. |
| `PHASE_WORKLOG.md` at repo root | 26 May 2026 | Its Phase 1 measurement notes were already mirrored in `VisClick_Report_Data_Form.md` Section 1.1 and `reports/tables/detector_bench_snapshot_2026-05-14.csv`. |

## Related artefacts elsewhere in the repo

- `reports/tables/` — every CSV the report cites (per-class metrics, latency, requirements evidence, CPV summaries).
- `reports/figures/` — PNG figures referenced by the dissertation.
- `reports/references/` — PDFs of cited papers (and the author's own SILC 2026 entry, `13034.pdf`).
- `scripts/` — reproducible scripts: `run_cpv.py`, `run_cpv_screenspot.py`, `renumber_references.py`, `run_nfr.py`, `test_detector.py`.
- `notebooks/01..07_*.ipynb` — the original Colab notebooks; numeric results in the report come from one of these.

## Update workflow

When you edit `docs/Final_Report.md`, `docs/PHASE_WORKLOG.md`, `docs/Final_Report_GAPS.md`, or `docs/VisClick_Report_Data_Form.md`, commit the change with a message that names the IDs it closes (e.g. `Phase 3: D-07 DONE via ScreenSpot path`). One commit per closed gap keeps the history easy to read.
