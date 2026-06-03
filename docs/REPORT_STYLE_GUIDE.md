# VisClick — Final Report Style Guide

**Purpose.** A single source of truth for the writing, formatting, and reference rules used in `Final_Report_v2.md` and the eventual Word/PDF submission. Whenever a question comes up about "how do we do X in the report?", check here first.

**Last updated:** 3 June 2026.

---

## 1. Template alignment

The submission follows the convention used by the 2026 MSc Big Data Analytics cohort at IIT/RGU (Anushka Siriweera, supervisor Pumudu Fernando — reference PDF at `gui_temp/2425489.pdf`). The bare `MSc_Project_Report_Template.docx` is the institutional minimum; the reference report is the de facto programme convention and is what we follow.

### 1.1 Chapter count and order

Nine chapters, not six. The bare template's six-chapter outline is generic; the BDA cohort uses nine.

1. Introduction
2. Literature Review
3. Requirement Analysis
4. Project Management
5. Design
6. Implementation
7. Testing
8. Evaluation
9. Conclusion

Every chapter starts with `N.1 CHAPTER OVERVIEW` and ends with `N.x CHAPTER SUMMARY`.

### 1.2 Heading format

- Chapter heading: `CHAPTER 01 – INTRODUCTION` (en-dash, all caps, zero-padded number).
- Section heading: `1.2 PROJECT BACKGROUND` (all caps).
- Sub-section heading: `1.9.1 DATA AND PREPROCESSING PIPELINE` (all caps).
- In markdown source we use `# CHAPTER ...`, `## 1.x ...`, `### 1.x.y ...` so Word's Heading 1 / 2 / 3 styles map cleanly on paste.

### 1.3 Figure and table numbering

Sequential across the whole document, **not** chapter-prefixed.

- Figures: `Figure 1`, `Figure 2`, ..., `Figure N`. Caption appears **below** the figure.
- Tables: `Table 1`, `Table 2`, ..., `Table N`. Caption appears **above** the table.
- Markdown placeholders use the form:
  ```
  [FIGURE N: short title.
  Source: relative path to PNG (or "to be produced").
  Caption: full caption sentence(s).]
  ```

### 1.4 Front matter (Word, not markdown)

Front matter is added in Word, not in `Final_Report_v2.md`. Required pages in order:

1. Consent page (RGU template)
2. Title page (Project title, full name, "MSc Big Data Analytics", IIT Sri Lanka, RGU Aberdeen, supervisor, second marker, month/year)
3. Declaration page (signed)
4. SPER form (Student Project Ethical Review)
5. Abstract (one page) + Keywords
6. Acknowledgements (optional, brief)
7. Table of Contents (auto-generated in Word from Heading 1/2/3 styles)
8. List of Figures
9. List of Tables

### 1.5 Body text formatting (Word)

- Font: Times New Roman, 11 pt.
- Line spacing: 1.5 throughout the main text.
- Paper: A4. Margins: 3 cm left, 2.5 cm top/bottom/right (adjust if binding requires wider left).
- Alignment: Justified body text; headings left-aligned.
- Use Word's built-in Heading 1 / 2 / 3 styles for automatic TOC.

### 1.6 Page budget

**Hard limit: 100 pages of body chapters.** This excludes front matter (title, declaration, abstract, TOC, lists of figures and tables), references, and appendices. Only the nine numbered chapters count.

Per-page word counts at the institutional formatting (Times New Roman 11 pt, 1.5 line spacing, A4) vary by content density:

| Page content | Typical words/page |
|---|---:|
| Pure prose | 350-400 |
| Bullet lists and structured prose | 280-340 |
| Tables and code blocks | 200-260 |

Mixed chapters (the realistic case) average around **340 words/page**.

Per-chapter budget. These are targets, not floors. Coming in under budget is fine and welcome; overrunning has to be paid for by another chapter or by cutting figures.

| Chapter | Target pages | Target words | Style notes |
|---|---:|---:|---|
| Ch 1 INTRODUCTION | 9-10 | ~3,000 | Mixed prose and figures |
| Ch 2 LITERATURE REVIEW | 10-12 | ~3,500 | Heavy citations and one table |
| Ch 3 REQUIREMENT ANALYSIS | 9-11 | ~3,200 | Two large requirement tables |
| Ch 4 PROJECT MANAGEMENT | 7-9 | ~2,400 | Risk register dominates |
| Ch 5 DESIGN | 10-12 | ~3,300 | Four figures, one code block |
| Ch 6 IMPLEMENTATION | 18-20 | ~4,500-5,000 | Heavy code blocks; biggest overrun risk |
| Ch 7 TESTING | 13-15 | ~3,500-4,000 | All result tables and figures land here |
| Ch 8 EVALUATION | 11-13 | ~3,500-4,000 | Discussion of RQs, NFRs, ethics |
| Ch 9 CONCLUSION | 6-8 | ~2,000-2,500 | Lightweight prose; reflection and future work |
| **Total** | **93-100** | **~28,900-31,900** | At submission formatting |

Tracker. Updated as each chapter is drafted.

| As of | Chapters drafted | Words to date | Est. pages | Headroom (against 100) |
|---|---|---:|---:|---:|
| 3 June 2026 | Ch 1, 2 | 6,500 | ~19 | 81 |
| 3 June 2026 | Ch 1-5 | 15,400 | ~46-49 | 51-54 |

### 1.7 Discipline rules to stay in budget

These rules apply to every remaining chapter, especially Ch 6 where the overrun risk is highest.

- **No re-explanation of design decisions.** Once a decision is justified in Ch 3 (requirements), Ch 4 (project management), or Ch 5 (design), later chapters only point to the implementation or measurement, not the rationale.
- **One representative code block per module in Ch 6.** Pick the most informative function. Do not copy whole files. Reader has the repository link.
- **Tables are summaries, not data dumps.** A per-attempt CSV with 60 rows becomes a 4-row summary table in the report. The raw CSV lives in `reports/tables/`.
- **Figures only if they add information that prose cannot.** Two figures showing the same thing is one figure too many.
- **Cut "Chapter Overview" paragraphs to 1-2 short paragraphs.** They are signposting, not content.
- **Strict 9.x cap on sub-sections.** Heading level 3 only where the structure benefits the reader, never to pad the TOC.

---

## 2. Citation and reference rules

### 2.1 Style

Harvard "Cite Them Right" (RGU library standard).

- In-text: `(Author, Year)` for parenthetical, `Author (Year)` for narrative.
- One author: `(Carion et al., 2020)` if ≥3 authors; `(Liang and Hu, 2020)` if 2; `(Sweigart, 2024)` if 1.
- Two papers by the same author in the same year are disambiguated with `a`, `b`: `(Li et al., 2022a)` for CLAY, `(Li et al., 2022b)` for Adaptive Teacher.

### 2.2 Reference-list format

```
Surname, Initial. (Year) Title in sentence case. Italicised Journal, vol(iss), pp. start–end. Available from: https://doi.org/...
```

- Listed alphabetically by first author surname.
- For ≥3 authors: `Surname, X. et al. (Year)`.
- For 2 authors: `Surname, X. and Surname, Y. (Year)`.
- DOIs: `Available from: https://doi.org/...` (preferred over `Available at:`).
- Web pages: `Available from: URL [Accessed DD Month YYYY].`

### 2.3 Reference budget

**Target: 30 to 40 unique sources.** Anushka's report has ~25. We will run slightly higher because the project covers more sub-topics (data, two detectors, three adaptation methods, evaluation, ethics). Hard ceiling: 50.

Rules to stay in budget:

- One anchor reference per claim. Do not stack `[7, 22]` for the same thing.
- Use survey papers to cover broad areas (one transfer-learning survey, one SSP survey, one SSOD survey if needed).
- Drop "completeness" citations — works mentioned only to demonstrate awareness, never used as method or evidence.
- Tool documentation refs (SikuliX, PyAutoGUI, pywinauto, Ultralytics, Tesseract, EasyOCR, rapidfuzz, mss, ONNX Runtime) count toward the budget but are cheap; keep one per tool.
- Drop placeholder/stub entries with `Co-authors` or `arXiv:2503.xxxxx` style filler unless the work genuinely needs them.

### 2.4 Cumulative reference status

| As of | Chapters drafted | Unique references | Headroom (against 40) |
|---|---|---|---|
| 3 June 2026 | Ch 1, Ch 2 | ~18 | 22 |
| 3 June 2026 | Ch 1, Ch 2, Ch 3, Ch 4, Ch 5 | ~19 (added Hevner et al., 2004 for DSR) | 21 |

Updated as each chapter is added.

---

## 3. Voice and style

The goal is prose that reads as a thoughtful student wrote it, supported by AI drafting. Two principles run through every chapter.

**(a) Variable sentence length and rhythm.** AI prose is unnaturally uniform — sentences cluster around 18-22 words. Real writing mixes 4-word punches with 30-word complex sentences. Match the reference report's rhythm.

**(b) Direct, declarative voice.** Drop AI smoothing connectives. Replace "Moreover, ..." and "Furthermore, ..." with the next sentence starting cleanly. Use "And" and "But" at sentence starts where the rhythm calls for it; both are accepted in modern academic prose.

### 3.1 Specific moves that are encouraged

- **Sentence fragments** where they land hard for emphasis.
  > *"A small set of clicks and keystrokes, directed at coloured rectangles on a screen."*
- **"And" / "But" sentence-starts** when the rhythm calls for it.
  > *"And critically, there is no RICO-equivalent for desktops."*
- **Mixed paragraph length.** Some 2-sentence paragraphs, some 6-sentence paragraphs. Avoid uniformity.
- **Hedges in student voice.** "I think", "my reading", "I am not sure why, but ..." where natural.
- **Concrete moments** that only the author could have written. "During the second day of running the auto-capture script, GIMP's title-bar text changed because of an autosave indicator and the corpus stopped clustering by app."
- **Slightly loose parallelism.** Three bullets where the first two start with verbs and the third starts with a noun. AI prose is parallel to a fault.
- **Em-dashes** for asides. `—` (not `--`, not `-`).
- **Italics for emphasis** on a single word, sparingly. `*can*` not `**bold**` for emphasis.
- **First-person where natural.** "I observed", "we evaluated", "the author tested". The reference report uses third person for the body and first person only in the Declaration. Default to third person but allow first person in Chapter 9 (Conclusion) for reflection.

### 3.2 AI-tells to avoid

The following words and phrases show up disproportionately in LLM output. Replace them with plainer alternatives.

| Avoid | Prefer |
|---|---|
| delve | look at, examine, explore |
| navigate | move through, work through, deal with |
| comprehensive | full, complete, thorough |
| leverage | use, draw on |
| facilitate | help, allow, support |
| intricate | detailed, complex |
| myriad | many, a lot of |
| tapestry | (just delete the metaphor) |
| robust (in non-statistical sense) | reliable, stable, well-tested |
| underscores | shows, makes clear, emphasises |
| embarked on | started, began |
| in essence | (delete) |
| it is worth noting that | (delete; just state the thing) |
| Moreover, ... | (delete; let the next sentence stand) |
| Furthermore, ... | (delete; use "And" if a connective is needed) |
| In conclusion, ... | (delete from chapter summaries; use the section heading instead) |
| dominant way / paramount / pivotal | important, central |

### 3.3 What we do NOT do

These are non-negotiable.

- **No deliberate typos, misspellings, or grammar errors.** Inserting "teh" or a wrong tense to fool a detector is academic misconduct and is also detected as a second-order signal.
- **No paraphrasing tools or "humanizers".** These are detectable and treated by RGU/IIT as the same offence category.
- **No fabricated citations.** Every reference points to a real source.
- **No undeclared AI use at submission time.** Declare AI-assisted drafting in the Declaration page; see §4.

### 3.4 Why this works

Modern AI detectors (Turnitin AI, GPTZero, etc.) measure perplexity and burstiness at the sentence level. Variable sentence length and rhythm directly move both metrics in the direction of human writing. Concrete first-person details and topic-specific hedges add information that an LLM trained on general text cannot easily produce. Surface tricks (typos, find-and-replace synonym swaps) do not move these metrics and add a second-order error signature of their own.

---

## 4. AI use declaration

The Declaration page should contain a sentence acknowledging AI-assisted drafting. Confirm exact wording with your supervisor; the standard draft is:

> "AI tools (large language models, including OpenAI ChatGPT and Anthropic Claude) were used for drafting prose, restructuring chapters, and producing the initial reference list, under my direction and review. All research questions, experiments, technical decisions, results, and analysis are my own work. All AI-generated text was edited and verified by me before inclusion."

With this declaration in place, the AI-detection result becomes a non-issue at submission. The reviewer's question shifts from "did they use AI" to "is the work theirs to defend at viva".

---

## 5. Chapter writing workflow

The pragmatic split, given that Phase 4 experiments are still running:

| Phase | Action | Depends on experiments? |
|---|---|---|
| A | Write Ch 1, Ch 2 | No (done as of 3 June 2026) |
| B | Write Ch 3, Ch 4, Ch 5, Ch 6 | No |
| C | **Pause.** Run remaining Phase 4 experiments (D-01 target-side, D-02, D-03, D-04) | — |
| D | Write Ch 7, Ch 8 with real numbers | Yes |
| E | Write Ch 9 (Conclusion) | Some |
| F | Rebuild Harvard reference list, alphabetised | — |
| G | Author's second-pass rewrite in own voice in Word | — |
| H | Front matter (title page, consent, declaration, SPER) in Word | — |
| I | Pandoc or manual MD-to-DOCX conversion | — |
| J | Final formatting in Word (TOC, lists of figures/tables, page numbers, Turnitin check) | — |
| K | Submit | — |

### 5.1 Per-chapter sub-section conventions

Match the reference report's section depth.

- Section heading depth 2 only for `N.1`, `N.2`, ..., `N.last`.
- Section heading depth 3 (e.g. `1.8.1`, `1.8.2`) only inside `OPERATIONAL OBJECTIVES`, `PROPOSED SOLUTION`, and similar mid-chapter sub-decompositions.
- Every chapter ends with `N.x CHAPTER SUMMARY` that points the reader to the next chapter in the final paragraph.

### 5.2 Placeholder convention

Where a number, table cell, figure, or citation depends on an experiment not yet run, use one of these explicit placeholders:

- `[NUMBER]` — single metric value pending
- `[TABLE]` — a table-shaped result pending
- `[FIGURE N: short title. Source: path. Caption: ...]` — a figure pending
- `[CITATION: short description]` — a reference whose canonical entry is not yet known

Placeholders make second-pass review easy: a single `grep -nE '\[NUMBER\]|\[TABLE\]|\[FIGURE|\[CITATION'` finds every gap.

---

## 6. Tracking documents

The following docs work together. Do not duplicate state across them.

- `docs/PHASE_WORKLOG.md` — ordered phases (1-8), current state, findings log, "what's next" notes. **The canonical plan.**
- `docs/Final_Report_GAPS.md` — per-ID ledger of every gap (D-01...D-12, T-01..T-04, W-01..W-04, F-01..F-12, U-01..U-08). **The status table.**
- `docs/REPORT_STYLE_GUIDE.md` — this file. **The style and convention rulebook.**
- `docs/Final_Report.md` — v1 draft, IEEE-numeric citations, polished AI voice. Retained for reference but not the submission source.
- `docs/Final_Report_v2.md` — v2 draft, Harvard citations, natural-informality voice, ALL-CAPS section headings. **The submission source.**

When a rule in this file is updated, log the change date in §0 and the affected chapters get a re-pass.
