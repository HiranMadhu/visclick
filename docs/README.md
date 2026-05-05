# `docs/` — VisClick design and dissertation source documents

This folder is the canonical, version-controlled home of the two long-form documents that drive the project:

| File | What it is | When to read it |
|------|------------|-----------------|
| `VisClick_Detailed_Plan.md` | The full multi-phase implementation and research plan: what to build, what to read, how to evaluate. ~75 KB. | Before starting a new phase / before a session where you want to know "what comes next". |
| `VisClick_Report_Data_Form.md` | The structured data form for the dissertation. Contains every metric, table, finding, integration headache, and architecture diagram in the form the final report needs. ~80 KB. | While running experiments (to record results) and while writing the report (to fill prose around the recorded numbers). |

## Sections worth knowing about (in `VisClick_Report_Data_Form.md`)

- **§0.3** — data-pipeline issues and workarounds (F1–F11).
- **§4.x** — per-model experimental results.
- **§8.2** — prototype-side integration headaches (P1–P11) hit during the 5 May 2026 Windows live demo.
- **§8.4** — known limitations of the prototype's element coverage (text-labeled vs icon-only clickables), with literature-table cross-refs.
- **§8.5** — runtime architecture diagram (Mermaid + ASCII) of the bot's data-flow.
- **§8.6** — live-demo chronology with the concrete failure → fix → commit chain.
- **§13** — free-form observations O1–O16, the discussion-chapter raw material.

## Why these are inside the repo

Earlier the working copies lived at `<workspace>/gui_temp/VisClick_*.md`, which was outside `visclick/`. Mirroring them into `visclick/docs/` makes them:

- **Versioned with the code** — every commit that introduces a code change can document its rationale in the same commit.
- **Discoverable to anyone who clones the repo** — no need to dig through Drive or local copies to find the design rationale.
- **Reproducible from the artefact** — the dissertation reviewer / examiner can read the plan, run the notebooks, and run the prototype from a single `git clone`.

## Update workflow

The user's working copies in `gui_temp/` are the source of truth during active sessions. After substantive edits — every few commits — copy the latest version into `visclick/docs/` so the repo stays in sync. Concretely:

```bash
cp gui_temp/VisClick_Report_Data_Form.md visclick/docs/VisClick_Report_Data_Form.md
cp gui_temp/VisClick_Detailed_Plan.md    visclick/docs/VisClick_Detailed_Plan.md
git -C visclick add docs/
git -C visclick commit -m "docs: sync plan + report"
git -C visclick push
```

## Related artefacts elsewhere in the repo

- `reports/literature_table.csv` — the 10-paper annotated literature review referenced from §8.4 and §C.1.5 of the plan.
- `reports/figures/` — EDA charts and overlay PNGs that the report cites.
- `reports/tables/` — per-class metric CSVs (e.g. `source_per_class.csv`).
- `notebooks/01..07_*.ipynb` — every numeric result in the report comes from one of these.
