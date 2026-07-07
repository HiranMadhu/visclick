# VisClick Report — Image Catalog

> **How to use this catalog.** Each candidate image is listed with: a candidate ID (`I-NN`), the chapter and section it belongs to, what the image should show, where to source it, and a suggested figure caption. Tick the ones you want; we'll renumber them into the report's sequential `Figure N` scheme at the final pass. Status legend: **READY** (file exists in repo); **AUTHORED** (SVG written, drop into Word); **FETCH** (download or screenshot from external source); **DRAW** (you draw it).

## Summary

| Source | Count | Total est. pages added (Word) |
|---|---:|---:|
| A — Already in `reports/figures/` (READY) | 9 candidates | — |
| B — SVG diagrams I wrote in `docs/figures/` (AUTHORED) | 6 candidates | ~3 |
| C — Paper figures you fetch (FETCH) | 5 candidates | ~2.5 |
| D — Author screenshots (DRAW/SCREENSHOT) | 6 candidates | ~3 |
| **Total candidates** | **26** | |

Pick whichever subset gets you to your target page count. ~12 figures total typically adds 5-6 pages.

---

## A. Already in `reports/figures/` — READY to drop in

| ID | Chapter | What | File | Suggested caption |
|---|---|---|---|---|
| **A-01** | Ch 6 §6.5.1 (M0) | Auto-label preview on a desktop screenshot | `reports/figures/desktop_autolabel_preview.png` | Figure: zero-shot M0 detector applied to a Windows 11 desktop screenshot. Many small icons go unboxed; the source-target gap is visible directly. |
| **A-02** | Ch 6 §6.5.2 (head FT) | Training curves for the desktop fine-tune | `reports/figures/desktop_finetune_curves.png` | Figure: training and validation curves for the freeze=10 head fine-tune. Convergence is reached by epoch 15. |
| **A-03** | Ch 7 §7.4.1 (TSR) | Four-method TSR bar chart | `reports/figures/method_comparison_tsr.png` | Figure: aggregate TSR on T01-T15 across the four methods. Template and visclick tie at 73.3%. |
| **A-04** | Ch 7 §7.2 (mAP) | Four-method mAP comparison | `reports/figures/method_comparison_map.png` | Figure: mAP@0.5 on the hand-corrected set across methods. |
| **A-05** | Ch 7 §7.5.2 (latency) | Latency box plot | `reports/figures/nfr_latency_box.png` | Figure: per-method end-to-end latency distribution on T01-T15. Template and pywinauto cluster at sub-second; visclick and ocr_only at multi-second. |
| **A-06** | Ch 6 §6.5.1 (M0 phase 1B) | Phase 1B M0 training curves | `reports/figures/phase1B_M0_curves.png` | Figure: M0 zero-shot reference run. |
| **A-07** | Ch 6 §6.5.1 (M1 phase 1B) | Phase 1B M1 training curves | `reports/figures/phase1B_M1_curves.png` | Figure: M1 COCO-direct control. |
| **A-08** | Ch 6 §6.5.2 (M2 phase 1B) | Phase 1B M2 training curves | `reports/figures/phase1B_M2_curves.png` | Figure: M2 head-only fine-tune curves. |
| **A-09** | Ch 6 §6.5.2 (k-curve) | Sample-efficiency curve | `reports/figures/sample_efficiency_curve.png` | Figure: hand-corrected mAP vs k. Monotonic increase. (See also Figure 14, the dual-axis version showing the ScreenSpot peak at k=1.) |

**Prototype walkthrough sequence — recommend pasting these as a single 6-panel composite.**

| ID | Chapter | What | File | Suggested caption |
|---|---|---|---|---|
| **A-10** | Ch 6 (intro / §6.7) | Step 1: terminal launch | `reports/figures/proto_1_terminal.png` | Figure: VisClick prototype, six-step walkthrough of a single click attempt. (Panel 1: command entered.) |
| **A-11** | Ch 6 §6.7 | Step 2: screen captured | `reports/figures/proto_2_captured.png` | (Panel 2: screenshot captured.) |
| **A-12** | Ch 6 §6.7 | Step 3: all detections overlaid | `reports/figures/proto_3_overlay_all.png` | (Panel 3: all candidate boxes detected.) |
| **A-13** | Ch 6 §6.7 | Step 4: matcher pick | `reports/figures/proto_4_picked.png` | (Panel 4: matcher selects best box.) |
| **A-14** | Ch 6 §6.7 | Step 5: post-click | `reports/figures/proto_5_after_click.png` | (Panel 5: action layer fires; UI changes confirm success.) |
| **A-15** | Ch 7 §7.4.2 | Step 6: failure mode | `reports/figures/proto_6_failure.png` | (Panel 6: failure mode for T13/T14, where the detector misses the target box.) |

Recommendation: A-10 through A-15 work either as a 2×3 composite figure on a single page (saves 2 pages vs separate placements) or as one figure per chapter section. Up to you.

---

## B. SVG diagrams — AUTHORED (drop straight into Word)

I wrote these as SVG files. Word 2016+ imports SVG natively (Insert → Pictures → from file). If your Word doesn't, open the SVG in a browser and screenshot, or use any free SVG-to-PNG converter.

| ID | Chapter | What | File | Suggested caption |
|---|---|---|---|---|
| **B-01** | Ch 5 §5.3 or Ch 6 §6.7 | VisClick six-layer architecture diagram | `docs/figures/svg_01_visclick_layered_architecture.svg` | Figure: VisClick's six-layer modular architecture. Each layer realised as one Python module; orchestrator composes layers and produces the per-attempt CSV. |
| **B-02** | Ch 5 §5.8.2 | Three-branch refusal rule decision flow | `docs/figures/svg_02_refusal_rule_three_branches.svg` | Figure: refusal rule decision flow. Three branches (no candidates, low confidence, high confidence) all terminate at a recorded verdict in `baseline_results.csv`. |
| **B-03** | Ch 6 §6.5.4 / Ch 8 §8.3.2 | Adaptive Teacher: published vs simplified | `docs/figures/svg_03_at_simplified_vs_published.svg` | Figure: Adaptive Teacher in the published EMA-stabilised online form (left) versus the project's simplified offline pseudo-label loop (right). The right-hand variant is what the dissertation runs; the absence of an EMA stabiliser is the failure mode driving the AT-full regression. |
| **B-04** | Ch 8 §8.3.5 | Adaptation method decision tree | `docs/figures/svg_04_adaptation_decision_tree.svg` | Figure: decision tree for picking an adaptation method given data budget and target alignment. Empirical operating points listed at the foot. |
| **B-05** | Ch 8 §8.7.4 | Integration architecture: VisClick alongside RPA, accessibility tree, and agent frameworks | `docs/figures/svg_05_integration_architecture.svg` | Figure: VisClick as a complement to existing automation tools. Three integration patterns (RPA fall-back, accessibility-tree fall-back, agent-framework tool call) all use the same `run_instruction(text) → Verdict` entry point. |
| **B-06** | Ch 7 §7.3.3 / Ch 8 §8.2.1 | Protocol disagreement bar chart (1.40% vs 57.49%) | `docs/figures/svg_06_protocol_disagreement.svg` | Figure: same deployed checkpoint, two protocols, 56-point gap. Hand-corrected per-class on the left; ScreenSpot per-slice on the right. |

---

## C. Paper figures — FETCH from the literature

For each paper figure: download the paper's PDF, screenshot the figure, paste in Word. Always cite the source in the caption (the citations are already in `Final_Report_v2.md`'s Harvard-style references).

| ID | Chapter | What | Source | Suggested caption |
|---|---|---|---|---|
| **C-01** | Ch 2 §2.4 / Ch 6 §6.5.4 | Adaptive Teacher framework | Li et al. (2022b) "Cross-Domain Adaptive Teacher", CVPR 2022, **Figure 1** or **Figure 2**. arXiv: 2111.13216. URL: `https://arxiv.org/pdf/2111.13216` | Figure: published Adaptive Teacher framework. EMA teacher + strong/weak augmentation + discrepancy loss. Source: Li et al. (2022b), Figure 1, reproduced for educational purposes. |
| **C-02** | Ch 2 §2.4 / Ch 6 §6.5.3 | SimSiam architecture | Chen and He (2021) "Exploring Simple Siamese Representation Learning", CVPR 2021, **Figure 1**. arXiv: 2011.10566. URL: `https://arxiv.org/pdf/2011.10566` | Figure: SimSiam pretext task — two augmented views, shared encoder, predictor on one branch, stop-gradient on the other. Source: Chen and He (2021), Figure 1. |
| **C-03** | Ch 2 §2.4 / Ch 6 §6.5.5 | SHOT framework | Liang et al. (2020) "Do We Really Need to Access the Source Data? Source Hypothesis Transfer for Unsupervised Domain Adaptation", ICML 2020, **Figure 1** or **Figure 2**. arXiv: 2002.08546. URL: `https://arxiv.org/pdf/2002.08546` | Figure: SHOT — frozen source classifier head, adaptive feature extractor on unlabelled target. Source: Liang et al. (2020), Figure 1. |
| **C-04** | Ch 6 §6.4.2 | DETR architecture | Carion et al. (2020) "End-to-End Object Detection with Transformers", ECCV 2020, **Figure 2**. arXiv: 2005.12872. URL: `https://arxiv.org/pdf/2005.12872` | Figure: DETR-R50 architecture — CNN backbone, transformer encoder-decoder, set-prediction head with bipartite matching loss. Source: Carion et al. (2020), Figure 2. |
| **C-05** | Ch 6 §6.4.1 | YOLOv8s architecture | Ultralytics docs at `https://docs.ultralytics.com/models/yolov8/` (architecture diagram, sometimes redrawn by RangeKing on GitHub: `https://github.com/ultralytics/ultralytics/issues/189`) | Figure: YOLOv8 architecture — CSPDarknet53 backbone, PANet neck, decoupled detection head. Source: Ultralytics documentation. |

**Attribution note.** All five are commonly reproduced in MSc and PhD dissertations under fair-use / educational-use conventions. Always include the attribution line in the figure caption ("Source: <Author> (Year), Figure N") and add the original paper to the references list.

---

## D. Author screenshots — DRAW or SCREENSHOT yourself

These are the most credible images in a dissertation viva because they are demonstrably yours.

| ID | Chapter | What | How to capture | Suggested caption |
|---|---|---|---|---|
| **D-01** | Ch 1 §1.2 | Classical baseline failure example | Open `pywinauto.inspect` or AccEvent on a modern Windows 11 dialog (Settings → Privacy → Microphone). Screenshot the inspector showing degenerate / empty / localised tree. Side-by-side with a regular OCR-only output on a graphical icon (e.g. the Windows search button) showing it returns nothing. | Figure: failure modes of the classical baselines on a modern Windows 11 surface. Left: pywinauto's UIA tree on a WinUI 3 settings panel — controls present but with localised internal names. Right: OCR-only baseline applied to the Windows search icon — no recognisable text. |
| **D-02** | Ch 6 §6.7.7 / Ch 5 §5.6 | VisClick GUI screenshot | Run the prototype (`python -m visclick.gui`); screenshot the Tk window with the instruction box filled and the last-overlay thumbnail showing. | Figure: VisClick GUI as it appears at run time. Verbose-log panel on the right; last-overlay thumbnail at lower left; instruction text box at top. |
| **D-03** | Ch 6 §6.5.3 / Ch 8 §8.7.2 | OS theme contrast — same UI in light and dark | Take two screenshots of the same Windows 11 dialog (e.g. Settings → System) under light theme and under dark theme. Run VisClick on each; capture the overlay PNG for both. | Figure: OS theme sensitivity. Same dialog, two themes. The detector's confidence drops by 5-8 points on the dark theme (informal A/B, Section 8.7.2). |
| **D-04** | Ch 6 §6.7.1 / Ch 8 §8.5 | Multi-monitor coordinate space visualisation | Run `mss.tools` or take a stitched screenshot showing the virtual-desktop coordinate space with two monitors at different resolutions; annotate the (left, top) offset for the secondary monitor. | Figure: multi-monitor virtual-desktop coordinate space. The secondary monitor's `(left, top)` offset is what gets threaded through `act.click_box` (Section 6.10). |
| **D-05** | Ch 7 §7.4.2 | T01 success overlay | The prototype produces an overlay PNG for every attempt. Find the overlay for T01 in `runs/overlays/` (or wherever the prototype writes them) and grab it. | Figure: VisClick on T01 (click Save). The detector finds the Save button, the matcher's class-bonus disambiguates it from neighbouring buttons, the click lands. |
| **D-06** | Ch 7 §7.4.2 | T15 negative-case behaviour | Same as D-05 but for T15, where VisClick selected a low-confidence positive instead of refusing. | Figure: VisClick on T15 (negative test case). The matcher selected a low-confidence positive box rather than engaging the refusal rule cleanly — the threshold-tuning issue described in risk RR-05. |

---

## Recommended starter pack for a 95+ page body

If you only do one round of figure additions, this set adds the most impact for the least effort:

| ID | Why pick |
|---|---|
| A-01 | Visualises the source-target gap in Ch 6 |
| A-03 | The four-method headline result |
| A-05 | The latency story in Ch 7 |
| A-09 | Sample-efficiency curve (already produced) |
| A-10..A-15 (composite) | Six-panel walkthrough — 1 page in Word, doubles as the prototype's living-architecture figure |
| B-01 | Architecture diagram (alternative or supplement to existing Figure 9) |
| B-03 | Adaptive Teacher published vs simplified — directly explains the AT-full regression |
| B-04 | Decision tree at the end of Section 8.3.5 |
| B-06 | Protocol-disagreement chart for Section 8.2.1 |
| C-01 | Adaptive Teacher framework (cite-and-screenshot from Li et al. 2022b) |
| C-02 | SimSiam (cite-and-screenshot from Chen and He 2021) |
| D-01 | Author screenshot of pywinauto failure mode — adds your-own-work credibility |

That's 12 figures total. Estimated page addition: **~6 pages**. Combined with current totals, body lands at ~88 pages, plus refs ≈ ~92 total. Still 8-18 pages short of 100-110, but most of the high-value material is in.

If you want to push higher, add more from set A (the existing PNGs are essentially free cost) and one or two more author screenshots (D-03, D-04).
