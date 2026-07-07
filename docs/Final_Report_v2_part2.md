# VISCLICK – FINAL REPORT (V2, PART 2: CHAPTERS 6-9)

> **How to use this file.** This is the continuation of `Final_Report_v2.md`. It contains Chapters 6-9 of the v2 draft, kept separate so the source files stay editable without churning a single 1,500-line markdown blob. Same conventions apply: ALL CAPS chapter and section headings, sequential figure and table numbering carrying on from Part 1 (last figure was Figure 12; last table was Table 5), Harvard "Cite Them Right" citations, natural-informality voice. At submission time the two markdowns are concatenated and converted to Word as a single document.

---
# CHAPTER 06 – IMPLEMENTATION

## 6.1 CHAPTER OVERVIEW

This chapter is the build half of the design-build-evaluate loop. It walks through the implementation in roughly the order Chapter 5 introduced the components. It begins with the development environment, because every implementation claim that follows depends on having that environment reproducibly available. From there it covers the dataset implementation (acquisition, class collapse, the auto-label and hand-correction passes), the source-domain detector (YOLOv8s and DETR-R50), the four adaptation methods (few-shot fine-tune, self-supervised pre-training, Adaptive Teacher, SHOT), the prototype package, and the evaluation harness. The chapter closes with what was deliberately left out and where to find it.

A reader following the artefact alongside the dissertation should be able to identify, for any concrete claim in this chapter, the file, function or notebook cell that implements that claim. Implementation evidence is the contract this chapter pays.

## 6.2 DEVELOPMENT ENVIRONMENT AND TOOLCHAIN

The development environment is built around three compute targets. Source-domain training and the lighter adaptation experiments run on Google Colab Free with a T4 GPU. Inference, prototype testing, and the user-facing GUI run on a Windows 11 desktop, the author's personal machine. The heavier adaptation experiments — full-protocol Adaptive Teacher and SHOT, and the SimSiam pre-training ablation that needs longer than a Colab session allows — run on `us01odc-sc4-1-gpu064`, an internal Linux server with an NVIDIA H100. The three environments are kept compatible at the Python interpreter level (CPython 3.11 on Windows and Linux, CPython 3.12 on Colab) so an artefact trained on one runs on the others without environment-specific re-installation.

The Python project is structured as a standard `pyproject.toml`-driven package. Declared dependencies are listed below; the version pins in `requirements.txt` are stricter than shown.

```text
ultralytics>=8.0          # YOLOv8s training, ONNX export
transformers>=4.40        # DETR-R50
opencv-python>=4.8        # image I/O, overlay drawing
numpy>=1.24
Pillow>=10.0
onnxruntime>=1.17         # CPU-only ONNX inference
pyautogui>=0.9.54         # action layer
mss>=9.0                  # multi-monitor screen capture
pytesseract>=0.3          # optional OCR (Tesseract)
easyocr>=1.7              # primary OCR
rapidfuzz>=3.0            # matcher
psutil>=5.9               # NFR memory profiling
pywinauto>=0.6 ; platform_system == "Windows"
```

The Windows-only conditional on `pywinauto` is the single concession to a non-portable dependency. Every other package runs on Colab and on the H100 server, which is what lets the notebooks, the local runner scripts, and the Windows prototype share the same package install.

Editable install on Windows is `py -3 -m venv .venv`, activate, then `pip install -e .`. The CLI is exposed as a module entry point, `python -m visclick.bot`. The repository layout follows Section 5.7 plus a top-level `notebooks/` directory containing the fourteen training and evaluation notebooks (`01_pull_and_data.ipynb` through `14_uda_shot.ipynb`) and a `scripts/` directory containing the standalone runners that mirror the heavier notebooks for the H100 server. Notebook outputs are stripped on commit via `.gitattributes` (`*.ipynb diff=ipynb`).

## 6.3 DATASET IMPLEMENTATION

The dataset implementation has three tiers, mirroring the methodology in Section 3.4.

### 6.3.1 SOURCE-DOMAIN CORPUS

Notebook `01_pull_and_data.ipynb` downloads RICO from its hosting URL, CLAY from its release page, and the VINS supplementary corpus from Bunian et al. (2021). Each is unpacked into `datasets/raw/{rico,clay,vins}/`. The notebook then runs a class-collapse pass that maps each corpus's native taxonomy onto the unified six-class taxonomy used by the project.

| Unified class | Source mapping |
|---------------|----------------|
| `button` | RICO `Button`, `ImageButton`; CLAY `Button`; VINS `Button` |
| `text` | RICO `TextView`; CLAY `Text`; VINS `Text` |
| `text_input` | RICO `EditText`; CLAY `Edit_text`; VINS `Input_field` |
| `icon` | RICO `Icon`, `ImageView` (when small); CLAY `Icon`; VINS `Icon` |
| `menu` | RICO `Menu`; CLAY `Menu`, `Drawer`; VINS `Drop_down_menu` |
| `checkbox` | RICO `CheckBox`, `Switch`; CLAY `Checkbox`, `Toggle`; VINS `Checkbox` |

**Table 6: Class-collapse mapping from native taxonomies onto the unified six-class taxonomy.**

Boxes whose source class is not on the mapping table — decorative containers, scroll bars, progress indicators, advertising slots — are dropped rather than mapped to a `null` class. The alternative, training with a `background` class, was tested early in Phase 1 and discarded because it inflated the false-positive rate on the desktop seed without improving recall. After the collapse the unified corpus is sampled to a balanced 10,000 screens (8,000 train, 1,000 val, 1,000 test) using a fixed `random_state=42`. The sampled bundle is what is actually loaded by the YOLO and DETR training jobs in Section 6.4.

### 6.3.2 UNLABELLED TARGET CORPUS

Two sources of unlabelled desktop images are used. The first is `samples/desktop_seed/`, the 50-screenshot seed captured from the author's Windows 11 machine across Notepad, File Explorer, Visual Studio Code, Chrome, Word, and Outlook. The capture script `scripts/capture_screenshots.py` enumerates visible top-level windows via `pywinauto.Desktop(backend="uia")` and grabs each window with `mss`. The second is the desktop slice of the public ScreenSpot benchmark (Cheng et al., 2024), 334 screenshots covering macOS and Windows desktops, served through the Hugging Face dataset cache at `rootsautomation/ScreenSpot`. ScreenSpot is used both as an unlabelled training source for the UDA experiments in Section 6.5 and as a held-out evaluation set for the Central Point Validation (CPV) metric described in Section 6.12.

The proposal-committed corpus of around 2,000 self-captured screenshots is gap D-06. The implementation work is a parameterisable scheduled capture script, the design for which is in the data form, Section 11.

### 6.3.3 LABELLED TARGET TEST CORPUS

The hand-correction pass started from the auto-labels emitted by the M0 zero-shot model and corrected them in Roboflow's annotation tool. The corrected output is the eight-image, 356-box `datasets/handcorrected_desktop_test/` directory. The annotation guidelines mirror the CLAY release-notes conventions: tight boxes around the visible affordance (not the surrounding padding), no rotated boxes, no occluded boxes, no boxes for purely decorative graphical elements. The annotation work is documented as observation O17 in the data form. The path to a 100-image labelled corpus, gap D-07, is a continuation of the same workflow at a larger scale.

## 6.4 SOURCE-DOMAIN DETECTOR TRAINING

Two source-domain detectors are trained on the same unified bundle. The architectural comparison committed to in RQ3 puts a YOLOv8 backbone and a DETR-R50 backbone side by side, on the hypothesis that DETR's known small-object weakness will be aggravated by the packed-scene density of UI screens.

### 6.4.1 YOLOV8S SOURCE BASELINE

The YOLOv8s training configuration is captured in `configs/yolo_source.yaml`:

```yaml
path: ../datasets/source_zenodo_unified
train: images/train
val:   images/val
names:
  0: button
  1: text
  2: text_input
  3: icon
  4: menu
  5: checkbox
```

The training cell in `05_train_source.ipynb` is:

```python
from ultralytics import YOLO
model = YOLO("yolov8s.pt")
results = model.train(
    data="configs/yolo_source.yaml",
    epochs=30,
    imgsz=640,
    batch=16,
    device=0,
    project="runs/source",
    name="yolov8s_unified_30e",
    seed=42,
)
```

Thirty epochs took roughly 2.7 hours on a Colab Free T4. The headline numbers, recorded in `reports/tables/source_domain_results.csv`, are mAP@0.5 = 0.450 and mAP@0.5:0.95 = 0.350 on the held-out val split. The per-class breakdown in `source_per_class.csv` is shown in Table 7. The exported ONNX file is approximately 45 MB and is shipped into `weights/visclick.onnx`.

| Class | AP@0.5 | mAP@0.5:0.95 |
|---|---:|---:|
| menu | 0.87 | 0.79 |
| icon | 0.54 | 0.38 |
| button | 0.44 | 0.35 |
| text | 0.39 | 0.27 |
| text_input | 0.29 | 0.18 |
| checkbox | 0.16 | 0.13 |

**Table 7: YOLOv8s source-domain per-class AP at mAP@0.5 and mAP@0.5:0.95 on the unified val split.**

The `menu` class scores highest because RICO's `Drawer` and `Menu` boxes are large, regular, and well-represented. `checkbox` scores lowest because the boxes are small, inconsistent across the three source corpora, and visually similar to small `icon` boxes — exactly the failure pattern the literature on packed-scene detection predicts (Chen et al., 2020).

### 6.4.2 DETR-R50 SOURCE BASELINE

The DETR-R50 training is in `09_detr_source.ipynb`. It uses the Hugging Face `transformers` reference implementation rather than Meta's original code, because the `transformers` build integrates more cleanly with the project's existing PyTorch toolchain. A six-epoch run with the parameters below was the largest configuration that fit inside a Colab Free session:

```python
from transformers import DetrForObjectDetection
model = DetrForObjectDetection.from_pretrained(
    "facebook/detr-resnet-50", num_labels=6, ignore_mismatched_sizes=True,
)
# micro-batch 2, gradient accumulation 8 -> effective batch 16
# lr_head=1e-4, lr_backbone=1e-5, imgsz=DETR-default-800
```

The headline numbers (`source_domain_results_detr.csv`) are mAP@0.5 = 0.244 and mAP@0.5:0.95 = 0.161, against YOLOv8s's 0.450 / 0.350. DETR reaches roughly 54 % of YOLOv8s's source-side mAP@0.5 at roughly six times the wall-clock cost (about 16 hours of T4 time, accumulated across four Colab sessions). This is a meaningful negative result for the architecture comparison: under the project's compute budget, DETR-R50 is the worse engineering choice for UI-element detection. YOLOv8s remains the deployed source detector. DETR is retained in the experimental matrix as the architectural counterpoint reported in Section 7.2.

## 6.5 ADAPTATION METHODS

Five adaptation methods are described in the proposal. The implementation status of each is the substance of the experimental matrix in Table 5. The first two (M0 and few-shot fine-tune) are head-to-head with the YOLOv8s source baseline. The next three (SSP+FT, Adaptive Teacher, SHOT) are the cross-domain methods that the project compares against the head fine-tune.

### 6.5.1 M0 ZERO-SHOT TRANSFER (CONTROL)

M0 is the no-adaptation control. The source-trained YOLOv8s detector is run on the desktop seed without any further training. The implementation is a four-line evaluation cell in `08_phase1B_ablations.ipynb` that loads `weights/baseline_source/best_source_v8s.pt` and calls `model.val(data="configs/yolo_desktop_test.yaml")`. The headline numbers are mAP@0.5 = 0.012 against the hand-corrected eight-image set and 60.18 % CPV against the 334-image ScreenSpot desktop slice. The two protocols disagree by an order of magnitude in apparent severity; the gap is the project's headline measurement of evaluation-protocol fragility, discussed in Section 8.2.

### 6.5.2 FEW-SHOT FINE-TUNE (SAMPLE-EFFICIENCY CURVE)

The headline adaptation method is the few-shot supervised fine-tune used to produce the deployed detector. The training cell freezes the first ten layers (the CSPDarknet53 backbone) and trains only the PANet neck and the detection head:

```python
model = YOLO("weights/baseline_source/best_source_v8s.pt")
results = model.train(
    data="configs/yolo_desktop_finetune.yaml",
    epochs=20, imgsz=640, batch=8, device=0,
    freeze=10, lr0=1e-3, seed=42,
)
```

Freezing keeps the source-domain feature extractor intact and lets the head learn the target-domain class boundaries on a small budget. With only 50 labelled images, an unfrozen run overfits within five epochs. Four budgets are run: k = 1, 2, 4 and 8 labelled desktop images, plus the k = 0 zero-shot baseline. The results are recorded in `reports/tables/sample_efficiency.csv`.

| k | Hand-corrected mAP@0.5 | ScreenSpot CPV |
|---:|---:|---:|
| 0 | 0.012 | 60.18 % |
| 1 | 0.013 | 68.26 % |
| 2 | 0.083 | 20.06 % |
| 4 | 0.183 | 10.48 % |
| 8 | 0.271 | 25.15 % |

**Table 8: Sample-efficiency curve. Hand-corrected mAP rises monotonically with `k`. ScreenSpot CPV peaks at `k = 1` and degrades thereafter, which is the catastrophic-forgetting signal interpreted in Section 8.2.**

The headline observation is that the two evaluation protocols disagree about which fine-tune is best. The hand-corrected number rises monotonically with `k` because more boxes carry more class-specific signal. The ScreenSpot CPV number peaks at `k = 1` (68.3 %) and falls sharply thereafter (`k = 2` drops to 20.1 %, `k = 4` to 10.5 %). The interpretation is straightforward but uncomfortable: training on a tiny seed of WinUI 3 screenshots overfits the head onto the seed's visual style, costs the model the source-domain breadth that ScreenSpot rewards, and leaves the deployed detector with `k = 1` as the operating point. The discussion is in Section 8.2.

The deployed weight is the `k = 1` checkpoint, exported to ONNX:

```python
model.export(format="onnx", imgsz=640, opset=12, simplify=True)
```

The resulting `weights/visclick.onnx` is what the prototype loads at start-up.

### 6.5.3 SELF-SUPERVISED PRE-TRAINING + FINE-TUNE

The self-supervised pre-training method is implemented as SimSiam (Chen and He, 2021) on the YOLOv8s backbone, followed by the same few-shot fine-tune as Section 6.5.2. SimSiam was chosen over MoCo or SwAV for one practical reason: it does not need negative pairs, momentum encoders, or large batches. That fits the Colab Free T4 ceiling cleanly.

The SSP run lives in `11_ssp_pretrain.ipynb`. The pretext task is the standard SimSiam two-view objective. Each image is augmented twice; both views go through the same encoder (the YOLOv8s backbone with a small projection head bolted on); a stop-gradient operator on one branch stops the network from collapsing to a constant. The training corpus is the same unified bundle used for the source-domain detector — 8,000 images. Ten epochs at batch 64 on a Colab T4 took roughly 38 minutes and saturated the contrastive loss at -0.66 (recorded in `ssp_loss_log.csv`). A 20-epoch rerun was queued on the H100 server to confirm the loss is genuinely flat; the loss curve confirmed saturation by epoch 10 and the rerun was abandoned as not informative.

The fine-tune side of the method swaps the SimSiam-trained backbone in for the COCO checkpoint at the start of the few-shot fine-tune in Section 6.5.2. The notebook is `12_ssp_finetune.ipynb`. Two fine-tune budgets are run, k = 1 and k = 8, against the no-SSP baselines from Table 8.

| k | Method | ScreenSpot CPV | Hand-corrected CPV |
|---:|---|---:|---:|
| 1 | no-SSP | 68.26 % | — |
| 1 | SSP+FT | 45.81 % | 0.84 % |
| 8 | no-SSP | 25.15 % | — |
| 8 | SSP+FT | 28.44 % | 4.21 % |

**Table 9: SSP+FT ablation against the no-SSP baseline at k = 1 and k = 8.**

The SSP backbone hurts the k = 1 operating point by 22 points of CPV and helps the k = 8 operating point by about 3 points. The interpretation is that the SimSiam pretext on mobile UI images teaches the backbone features that are aligned with the source domain, not the target. At low k, the source-aligned features are exactly what the head was already getting from COCO pretraining; replacing them with mobile-UI-aligned features is a strict downgrade because the desktop classes look more like COCO's natural-image classes than RICO's flat mobile UI elements. At higher k, the head has enough labelled signal to retune around the SSP backbone, and a small benefit emerges. The honest conclusion is that this implementation of SSP, on the data this project has access to, is a negative result. It is reported in Section 7.4 with that framing.

### 6.5.4 ADAPTIVE TEACHER (UDA)

The Adaptive Teacher implementation (Li et al., 2022b) is the first of two UDA methods. The full Adaptive Teacher protocol uses a strong-augmentation student, a weakly-augmented EMA teacher, and a discrepancy loss that aligns the two. Reproducing the full protocol on a YOLOv8 backbone is non-trivial because Ultralytics's training loop does not expose the EMA-update hooks the original Adaptive Teacher reference implementation needs. The compromise is a simplified variant: an offline teacher-student pseudo-label loop that captures the spirit of Adaptive Teacher (target images are pseudo-labelled by a teacher; the student is trained on a mixed batch of labelled source and pseudo-labelled target) without the in-loop EMA update.

The implementation lives in two places. `13_uda_adaptive_teacher.ipynb` is the Colab-friendly version, capped at 500 source images, one outer iteration, and five epochs per iteration to fit a free-tier session. `scripts/run_uda_at_local.py` is the full-protocol runner for the H100 server, parameterised by `--source-cap`, `--n-outer`, `--epochs`, `--batch`, `--pseudo-conf` and `--tag`. The teacher starts as the source-domain YOLOv8s. At each outer iteration, the teacher emits pseudo-labels for the unlabelled target corpus (ScreenSpot desktop, 384 images at the configured confidence threshold of 0.3). The student is trained on a balanced batch of labelled source plus the pseudo-labelled target. The student becomes the next iteration's teacher.

Two configurations are run and reported. The short variant (1 outer iteration, 500-image source cap, 5 epochs per iteration) finishes in 217 seconds on a single H100. The full variant (3 outer iterations, full 8,000-image source bundle, 10 epochs per iteration) takes 2,102 seconds, roughly 35 minutes, with per-iteration teacher refresh. Both are recorded in `reports/tables/uda_adaptive_teacher.csv` and `reports/tables/uda_adaptive_teacher_uda_at_full.csv`.

| Configuration | Outer iters | Epochs | Source cap | n_pseudo | CPV ScreenSpot | CPV hand-corrected | Time |
|---|---:|---:|---:|---:|---:|---:|---:|
| AT short | 1 | 5 | 500 | 348 / 384 | 68.56 % | 10.96 % | 217 s |
| AT full | 3 | 10 | 8,000 | 1,042 (348+343+351) | 64.67 % | 6.74 % | 2,102 s |

**Table 10: Adaptive Teacher results — short and full configurations.**

The short variant's 68.56 % on ScreenSpot is statistically indistinguishable from the k = 1 head fine-tune (68.26 %). The interpretation is that one outer iteration of pseudo-labelling lifts the model to roughly the same operating point that one labelled image provides, which is the result the literature on cross-domain detection predicts at this teacher quality (Li et al., 2022b). The full-protocol variant is the more interesting result. Three outer iterations with the full source bundle and twice the epoch budget produced *worse* numbers on both protocols (-3.9 points on ScreenSpot, -4.2 points on the hand-corrected set). Two effects are likely at work. First, the simplified offline pseudo-labelling loop has no EMA stabiliser; each outer iteration trains the student on increasingly noisy pseudo-labels emitted by the previous student-as-teacher, and the noise compounds rather than averages out as it would in the original online protocol. Second, the larger 8,000-image source pool dilutes the target signal in each mixed batch, slowing the student's adaptation toward the target distribution while increasing the source-side training cost ten-fold. The deployed UDA weight is therefore the short-variant checkpoint at 68.56 % CPV. The fuller discussion, including the methodological lesson about offline-vs-online teacher schemes, is in Section 8.4.

### 6.5.5 SHOT (UDA)

The SHOT implementation (Liang et al., 2020) is the second UDA method. SHOT freezes the source-trained classification head — the source hypothesis — and adapts only the feature extractor on the unlabelled target images using a self-supervised pseudo-label objective. Like Adaptive Teacher, the project's SHOT implementation is a simplified variant: pseudo-labels are generated offline rather than online, and the freeze depth is exposed as a tunable parameter rather than a fixed split between head and extractor.

The implementation lives in `14_uda_shot.ipynb` (Colab) and `scripts/run_uda_shot_local.py` (H100). The runner accepts `--epochs`, `--freeze`, `--pseudo-conf` and `--tag`. Three configurations are run on the H100 to disentangle the effect of epoch budget from the effect of freeze depth. All three start from the same source-domain checkpoint and use the same 224 pseudo-labels (the freeze and epoch knobs do not change the pseudo-label generation step).

| Configuration | Epochs | freeze | n_pseudo | CPV ScreenSpot | CPV hand-corrected | Time |
|---|---:|---:|---:|---:|---:|---:|
| SHOT short | 8 | 15 | 224 / 384 | 23.95 % | 0.00 % | 22 s |
| SHOT 15 ep | 15 | 15 | 224 / 384 | 26.95 % | 0.28 % | 35 s |
| SHOT freeze = 10 | 8 | 10 | 224 / 384 | 34.13 % | 0.00 % | 22 s |

**Table 11: SHOT — three configurations on the H100.**

Two observations come out of the ablation. First, halving the freeze depth (15 → 10) lifts ScreenSpot CPV by roughly ten points at the same epoch budget, with no change in elapsed time. Letting the last few backbone blocks adapt is more useful than keeping them locked. Second, doubling the epoch count (8 → 15) at the heavier freeze lifts CPV by only three points, with a hand-corrected number that is one box different from zero. The epoch budget is not the bottleneck; the freeze schedule is.

Even the best SHOT variant — freeze = 10 at 34.13 % ScreenSpot CPV — sits roughly thirty points below the Adaptive Teacher short variant and below the k = 1 head fine-tune. The signal in SHOT's own validation set is misleading (pseudo-label mAP@0.5 climbed to 0.81 by epoch 8) because the validation set is itself made of pseudo-labels of the same target images. On real desktop transfer the model degrades. The honest framing for SHOT, like for SSP, is a negative result: under the project's data and compute budget, the simplified SHOT variant does not transfer well, and the freeze-depth ablation is the only non-trivial knob that moves the number meaningfully. The fuller comparison against Adaptive Teacher and the literature is in Section 8.4.

## 6.6 PRE-PROCESSING PIPELINE

The pre-processing pipeline is split between training-time and inference-time.

The **training-time** stage is the standard Ultralytics augmentation pipeline configured in `configs/yolo_*.yaml`. The augmentations enabled are mosaic (probability 0.5; turned off for the final 10 epochs), horizontal flip (probability 0.5), random scale within [0.8, 1.2], and HSV jitter at the Ultralytics defaults. Vertical flip is disabled because UIs are not vertically symmetric. Mosaic is what gives the source-domain training its data efficiency; an ablation without mosaic ran four points lower in mAP@0.5.

The **inference-time** stage is minimal. The capture layer hands the screenshot to the detect layer at native resolution; the detect layer rescales to 640×640 with letterboxing inside `ultralytics.engine.predictor`. There is no bilateral filtering, no contrast normalisation, no colour-space conversion. The screenshot is RGB throughout. The decision was made empirically: a preliminary A/B in week 6 compared no-preprocessing against bilateral-filter-plus-CLAHE and showed the no-preprocessing path was marginally better on the desktop seed. The A/B was not formal enough to report as a result; gap D-12 records the work needed for a proper test at sufficient sample size.

## 6.7 PROTOTYPE IMPLEMENTATION

The prototype is the `visclick` Python package, written to the design in Section 5.5. The walk-through below visits each module at the level of detail needed to make this chapter's evidence claims auditable. Public surfaces that were already shown in Section 5.5 are not repeated here.

### 6.7.1 VISCLICK.CAPTURE

The capture module wraps `mss` and exposes two entry points: `capture_monitor(idx)` and `list_monitors()`. The non-trivial work is the multi-monitor offset propagation, the source of observation O13 (the cursor moving by a few pixels onto the wrong monitor). The fix is to return the chosen monitor's `(left, top)` offset alongside the image, and to thread that offset through every downstream layer that maps a box back to a click coordinate. The relevant signature is:

```python
def capture_monitor(idx: int = 0) -> tuple[np.ndarray, tuple[int, int]]:
    """Return (image_rgb, (left, top)) for the monitor at idx."""
```

The `(left, top)` tuple is what `act.click_box` uses to convert a box centre in image-coordinates into a screen-coordinate suitable for `pyautogui.click`.

### 6.7.2 VISCLICK.DETECT

The detect module loads the ONNX file at start-up and runs `onnxruntime` inference per call. The public surface is one class with two methods:

```python
class Detector:
    def __init__(self, onnx_path: str = "weights/visclick.onnx"): ...
    def predict(self, image_rgb: np.ndarray, conf: float = 0.25) -> list[Detection]: ...
```

The `Detection` dataclass has fields `class_id`, `class_name`, `confidence`, and `xyxy`. The detector also exposes a `status()` probe that prints a tick if the ONNX file loads cleanly and a cross with the underlying error if it does not. The probe is what makes the start-up `_warn_once` pattern actionable rather than silent.

### 6.7.3 VISCLICK.OCR

The OCR module is the most complex single file in the codebase. It has to handle two backend mismatches — EasyOCR's `readtext` returns `(bbox, text, conf)` triples while pytesseract's `image_to_data` returns a DataFrame — and a fallback path that runs when neither backend is available. The public surface is small:

```python
def ocr_image(image_rgb: np.ndarray) -> list[OcrResult]: ...
def ocr_box(image_rgb: np.ndarray, box: tuple[int, int, int, int]) -> str: ...
def text_ground(image_rgb: np.ndarray, query: str) -> Optional[tuple[int, int]]: ...
def ocr_status() -> None: ...
```

`text_ground` is the OCR-fallback entry point invoked by the orchestrator when the matcher's per-box result is below threshold. It runs `ocr_image` on the full screenshot, runs the same rapidfuzz matcher over the recognised text regions, and returns the centre of the best match or `None`.

The `ocr_status()` probe is the lesson from observation O12. At start-up it tries to import `easyocr`, `pytesseract`, and the pure-Python fallback in order, prints a tick or cross for each, and lists the active backend. If none of the three is functional the program raises `RuntimeError` rather than failing silently downstream.

### 6.7.4 VISCLICK.MATCH

The match module is the rapidfuzz-plus-class-bonus matcher specified in Section 5.8.1. The public surface is one function (`best_box`) and one helper (`_infer_intent`). The implementation is 38 lines and has full unit-test coverage. The implementation choices not visible in the design statement are: case folding on both sides; no stop-word stripping; and a ten-verb intent-inference table at `visclick/match.py::_INTENT_TABLE`. That table is the easiest extension point for adding a new intent class.

### 6.7.5 VISCLICK.ACT

The act module is the PyAutoGUI wrapper. The single public function is `click_box(box, offset=(left, top), dry_run=False)`. Dry-run prints what would have been clicked without moving the cursor; it is used by the smoke tests and by the prototype's preview mode. PyAutoGUI's `FAILSAFE` flag is on by default, so the user can slam the cursor into the top-left corner to abort. The exception is caught in `bot.run_instruction` and logged as `verdict=aborted` in the per-attempt CSV.

### 6.7.6 VISCLICK.BOT

The orchestrator composes the five layers into a single `run_instruction(text: str, monitor: int = 0) -> Verdict` entry point. It implements the three-branch refusal rule from Section 5.8.2 and produces the per-attempt CSV row in the schema declared in Section 5.7. It also drives the overlay PNG generation; `_render_overlay` takes the screenshot, the detection list, the chosen box, and the click coordinate, and produces an annotated PNG in `runs/overlays/`.

### 6.7.7 VISCLICK.GUI

The GUI is a Tk window in `visclick/gui.py`, approximately 280 lines, following the wireframe in Section 5.6. Three implementation choices are worth noting. The orchestrator runs on a worker thread and communicates with the Tk main loop through a `queue.Queue` polled every 100 ms — this is what lets the long-running detect and OCR calls happen without freezing the UI. The 3-second pre-action countdown is implemented with `tk.after(1000, ...)` callbacks rather than `time.sleep`, which would block the loop. The last-overlay thumbnail is rendered with `Pillow.Image.thumbnail((320, 180))` on a background thread to avoid jank, and is signalled back through the same queue.

## 6.8 OCR INTEGRATION

The OCR integration is the architectural choice that gives the prototype its observed end-to-end behaviour. The choice is between running OCR on every detected box (the per-box path) and running OCR once on the whole image (the full-image fallback). The implementation does both, in a specific order: per-box first, full-image only if per-box fails.

The reason for the ordering is latency. Per-box OCR is roughly N × 200 ms on EasyOCR for N boxes; the median N across the 15-task suite is 9. Full-image OCR is roughly 6 seconds. The per-box path therefore runs in roughly 9 × 0.2 = 1.8 seconds, which dominates the happy-path budget. The full-image fallback adds 6 seconds when invoked; it is invoked on roughly 30 % of attempts (where the detector misses the target's bounding box), so the expected wall-clock cost of OCR per task is about 1.8 + 0.3 × 6 = 3.6 seconds. That calculation is what justifies per-box-first against always-full-image.

The OCR engine choice is EasyOCR rather than Tesseract. The choice was made empirically during week 4 (observation O5) after comparing the two on a small dialog-heavy benchmark. EasyOCR recognised approximately 91 % of visible text on a set of 20 Windows 11 dialogs; Tesseract recognised 67 %. The gap is largest on small text and on anti-aliased text-on-coloured-background, both of which are common in Windows 11. Tesseract is still available as an opt-in backend through the `VISCLICK_OCR_ENGINE=tesseract` environment variable, for users on machines where the EasyOCR model download is awkward.

## 6.9 MATCHING ALGORITHM IMPLEMENTATION

The matcher implementation is a faithful realisation of the design in Section 5.8.1. Three implementation choices that did not survive into the design statement are worth recording here.

The first is case folding. All comparisons are lower-cased on both sides. UI text uses title case ("Save"), instructions are typed in lower case ("save"); folding gives a small but reliable score uplift.

The second is stop-word retention. The matcher does *not* strip stop words. "Click the Save button" is left as-is rather than reduced to "save". The rationale is that rapidfuzz's WRatio is robust to padding, and stop-word stripping with a hand-rolled list is a frequent source of off-by-one bugs.

The third is the intent-inference table. The current rules cover ten verbs (`click`, `type`, `enter`, `select`, `open`, `close`, `press`, `toggle`, `expand`, `collapse`). The table is the easiest extension point for adding new intent classes; adding `drag` would be a one-line change.

The threshold for accepting the chosen box is `min_text_similarity = 60`. It was chosen empirically by running the 15-task suite at 40, 50, 60, 75 and 85 and picking the lowest threshold at which the negative test case (T15) was refused while the 14 positive tasks were still accepted. Risk RR-05 records the open question of whether 75 is a better operating point; the change is contingent on widening the negative-case set beyond a single task.

## 6.10 ACTION LAYER AND MULTI-MONITOR SUPPORT

The action layer is the PyAutoGUI wrapper described in Section 6.7.5. The two non-trivial implementation pieces are the multi-monitor offset propagation (already covered in Section 6.7.1) and the FAILSAFE escape.

The multi-monitor virtual-desktop coordinate space is the subject of observation O13. The architectural fix is to thread the `(left, top)` offset from `capture_monitor` through to `act.click_box`. The implementation fix is one line in `act.click_box`:

```python
screen_x = box_center_x + offset[0]
screen_y = box_center_y + offset[1]
pyautogui.click(screen_x, screen_y)
```

The pre-fix bug was that `pyautogui.click` was being called with image-coordinates rather than screen-coordinates, which worked on a single-monitor setup (where the two coincide) and broke on a multi-monitor setup (where they do not).

## 6.11 EVALUATION HARNESS IMPLEMENTATION

The evaluation harness is the script `scripts/run_baselines.py`. It is approximately 540 lines of code, longer than any single `visclick` module, because it implements the entire experimental protocol used in Chapter 7. Its responsibilities are: loading the canonical task list from `tasks/T01_T20.json`, looping over the selected method × task combinations, invoking the per-method `predict()` adapter, presenting the verdict dialog after each attempt, and writing each row to `reports/tables/baseline_results.csv`.

The four method adapters all conform to a small interface:

```python
class BaselineResult(NamedTuple):
    predicted_xy: tuple[int, int] | None
    overlay_path: Path
    notes: str

class BaselineMethod(Protocol):
    name: str
    def predict(self, image_rgb: np.ndarray,
                instruction: str,
                hint: dict[str, Any]) -> BaselineResult: ...
```

The four implementations are in `scripts/baseline_template.py`, `scripts/baseline_ocr_only.py`, `scripts/baseline_pywinauto.py`, and `scripts/baseline_visclick.py`. The protocol-based design is what makes adding a fifth method a one-file change.

The `hint` dictionary is the per-task hint for each method, drawn from `tasks/T01_T20.json`. T01 ("click the Save button in Notepad's Save-As dialog") carries different hints for different methods:

```json
{
  "task_id": "T01",
  "instruction": "click the Save button",
  "hints": {
    "template": "samples/templates/notepad_save.png",
    "ocr_only": "Save",
    "pywinauto": {"ControlType": "Button", "Name": "Save"},
    "visclick": "Save"
  }
}
```

The hint design is the harness's contribution to fairness: each method consumes the information it natively prefers (a template image for `cv2.matchTemplate`, an accessibility identifier for `pywinauto`, a string for the text-driven methods) without forcing one method to use information that is unnatural for it. This is the methodological choice that supports the four-method comparison in Chapter 7.

Two specialised evaluation scripts complement the four-method harness. `scripts/run_cpv.py` computes the Central Point Validation metric of Dardouri et al. (2024) against the eight-image hand-corrected set, producing `cpv_summary.csv` and `cpv_per_image.csv`. `scripts/run_cpv_screenspot.py` computes the same metric against the public ScreenSpot benchmark of Cheng et al. (2024), filtered to the 334-row desktop slice (macOS and Windows screens), producing `cpv_screenspot_desktop.csv` and `cpv_screenspot_desktop_rows.csv`. Both scripts run the deployed ONNX detector at `weights/visclick.onnx` with confidence threshold 0.25 and NMS IoU 0.5, so the numbers are directly comparable to the mAP figures the four-method harness reports. Both scripts accept a `--tag` argument that namespaces the output CSV (e.g. `cpv_summary_uda_at.csv`), which is what allows the SSP, Adaptive Teacher, and SHOT runs in Section 6.5 to publish their results without overwriting one another. The CPV results are presented in Section 7.3 and interpreted in Section 8.2.

## 6.12 CHAPTER SUMMARY

The implementation walks through the design from the development environment to the evaluation harness. The dataset pipeline acquires three corpora, collapses their taxonomies into a six-class unified bundle, captures the desktop seed, and hand-corrects 8 test images. The detector training implements two source-domain backbones (YOLOv8s and DETR-R50) and four adaptation methods, each with at least one ablation: few-shot fine-tune at k = 0, 1, 2, 4, 8; SimSiam SSP+FT at k = 1, 8; Adaptive Teacher in short and full configurations; SHOT across two epoch budgets and two freeze depths. The deployed weight is the k = 1 head fine-tune, exported to ONNX as `weights/visclick.onnx`. The prototype is a six-module Python package implementing the layered architecture from Section 5.3, plus a Tk GUI and a four-method evaluation harness.

The empirical picture is mixed in a way that turns out to be informative. The few-shot curve and the short Adaptive Teacher variant land at roughly the same operating point (ScreenSpot CPV in the high 60s) — one with one labelled image, the other with none. SSP, full-protocol Adaptive Teacher, and SHOT all underperform their short counterparts, for reasons that are domain-specific (SSP) or protocol-specific (offline pseudo-label noise compounding, in the case of full Adaptive Teacher) or hyperparameter-driven (freeze depth, in the case of SHOT). Those negative and mixed results are reported honestly in Chapter 7 and discussed in Chapter 8 — they are part of what the project learned. The 100-image labelled corpus and the 2,000-screen unlabelled corpus committed to in the proposal are recorded as gaps D-06 and D-07 and remain open.

The next chapter runs the implementation through the testing protocol committed to in Chapter 3 and reports the empirical numbers.

---

# CHAPTER 07 – TESTING

## 7.1 CHAPTER OVERVIEW

This chapter reports the empirical results from running the implementation through the testing protocol committed to in Chapter 3. The structure is straightforward. Section 7.2 reports the detector training and adaptation experiments — the source-domain numbers for YOLOv8s and DETR-R50, the few-shot sample-efficiency curve, the SSP+FT ablation, the two Adaptive Teacher configurations, and the three SHOT configurations. Section 7.3 reports grounding accuracy under both evaluation protocols (hand-corrected mAP on the eight-image set, and Central Point Validation on the 334-image ScreenSpot desktop slice), with a per-class breakdown. Section 7.4 reports the four-method comparison on T01-T15, including the per-task verdict matrix that lets the reader see exactly where each method succeeds and fails. Section 7.5 reports the non-functional-requirement verification (accuracy, latency, memory, reliability, and the remaining NFRs).

Every percentage in this chapter points to a CSV in `reports/tables/`. The mapping from claim to file is in `requirements_evidence.csv`; a reader auditing the dissertation should be able to pull the underlying number with one command. Interpretation of these results — *why* the protocols disagree, *why* AT-full underperforms AT-short, *why* SHOT degrades on real desktop transfer — is in Chapter 8. This chapter is the data.

## 7.2 DETECTOR TRAINING AND ADAPTATION RESULTS

### 7.2.1 SOURCE-DOMAIN BACKBONES

The two source-domain backbones (YOLOv8s and DETR-R50) are trained on the unified 6-class bundle described in Section 6.3.1. The headline numbers, reproduced from `source_domain_results.csv` and `source_domain_results_detr.csv`, are summarised in Table 12.

| Backbone | Epochs | Effective batch | Wall-clock | mAP@0.5 | mAP@0.5:0.95 |
|---|---:|---:|---:|---:|---:|
| YOLOv8s | 30 | 16 | ~2.7 h on T4 | 0.450 | 0.350 |
| DETR-R50 | 6 | 16 (mb 2 × ga 8) | ~16 h on T4 | 0.244 | 0.161 |

**Table 12: Source-domain detector results on the held-out unified val split (1,000 images).**

[FIGURE 13: Source-domain backbone comparison — YOLOv8s vs DETR-R50.
Source: `reports/figures/ch7_source_backbone.png` (to be produced from `source_domain_results.csv` and `source_domain_results_detr.csv`).
Caption: Three-panel figure. Left: source-side mAP@0.5 (YOLOv8s 0.450 vs DETR-R50 0.244). Centre: source-side mAP@0.5:0.95 (0.350 vs 0.161). Right: training wall-clock cost on a single Colab T4 (2.7 h vs 16 h, 6× ratio). Under the project's compute budget, YOLOv8s is the strict engineering win on UI-element detection.]

The headline observation is in the figure caption. Under the project's compute budget — a single Colab Free T4, on a 10,000-image unified bundle — YOLOv8s reaches roughly twice the source-side mAP at roughly one-sixth of the wall-clock cost. DETR-R50 is the architecturally cleaner choice on paper but the worse engineering choice in practice. The interpretation is in Section 8.5.

The YOLOv8s per-class breakdown is in Table 13. The pattern is consistent with the literature on packed-scene UI detection (Chen et al., 2020): large, regular elements (`menu`, `icon`) score highest; small, visually inconsistent elements (`checkbox`) score lowest.

| Class | Precision | Recall | AP@0.5 | mAP@0.5:0.95 |
|---|---:|---:|---:|---:|
| menu | 0.76 | 0.87 | 0.87 | 0.79 |
| icon | 0.64 | 0.53 | 0.54 | 0.38 |
| button | 0.49 | 0.48 | 0.44 | 0.35 |
| text | 0.46 | 0.38 | 0.39 | 0.27 |
| text_input | 0.44 | 0.34 | 0.29 | 0.18 |
| checkbox | 0.31 | 0.26 | 0.16 | 0.13 |

**Table 13: YOLOv8s per-class precision, recall, AP@0.5, and mAP@0.5:0.95 on the source-domain val split. Source: `source_per_class.csv`.**

### 7.2.2 FEW-SHOT SAMPLE-EFFICIENCY CURVE

The few-shot fine-tune sweeps `k` over five values: 0 (zero-shot), 1, 2, 4, 8. Each `k > 0` configuration trains a head fine-tune (freeze=10, 20 epochs, batch 8, lr=1e-3) starting from the YOLOv8s source weight. Both evaluation protocols are reported on the same checkpoint. The full curve is in Table 14, reproduced from `sample_efficiency.csv`.

| k | Hand-corrected mAP@0.5 | Hand-corrected mAP@0.5:0.95 | ScreenSpot CPV | ScreenSpot CPV (text) | ScreenSpot CPV (icon) |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.012 | 0.007 | 60.18 % | 75.77 % | 38.57 % |
| 1 | 0.013 | 0.007 | **68.26 %** | **85.57 %** | 44.29 % |
| 2 | 0.083 | 0.051 | 20.06 % | 27.84 % | 9.29 % |
| 4 | 0.183 | 0.089 | 10.48 % | 12.89 % | 7.14 % |
| 8 | **0.271** | **0.154** | 25.15 % | 34.54 % | 12.14 % |

**Table 14: Few-shot sample-efficiency curve at k = 0, 1, 2, 4, 8. Bold cells mark the per-protocol maximum.**

[FIGURE 14: Few-shot sample-efficiency curve, two-axis plot.
Source: `reports/figures/ch7_sample_efficiency.png` (to be produced from `sample_efficiency.csv`).
Caption: x-axis k = 0, 1, 2, 4, 8. Left y-axis (orange line): hand-corrected mAP@0.5, rising monotonically from 0.012 at k = 0 to 0.271 at k = 8. Right y-axis (blue line): ScreenSpot CPV, peaking at 68.26 % at k = 1 then collapsing to 10.48 % at k = 4 and recovering partially to 25.15 % at k = 8. The two protocols disagree about which k is best.]

The two protocols disagree about which checkpoint is best. The hand-corrected mAP rises monotonically with `k`, peaking at 0.271 for k = 8. The ScreenSpot CPV peaks at k = 1 (68.26 %) and falls sharply, hitting a minimum at k = 4 (10.48 %) before recovering partially at k = 8. The deployed weight is the k = 1 checkpoint because ScreenSpot is the held-out, third-party-scored protocol; hand-corrected mAP is fit-to-train at this scale (eight images, 356 boxes). The mechanism behind the ScreenSpot collapse — catastrophic forgetting under tiny-budget head fine-tuning — is the subject of Section 8.3.

### 7.2.3 SSP+FT ABLATION

The SSP+FT ablation runs the same head fine-tune as Section 7.2.2, but starting from a SimSiam-pre-trained backbone instead of the COCO checkpoint. Two operating points are evaluated, k = 1 and k = 8, against the no-SSP baselines. The result is reproduced from `ssp_few_shot.csv`.

| k | Backbone init | ScreenSpot CPV | Hand-corrected CPV | Δ vs no-SSP |
|---:|---|---:|---:|---:|
| 1 | no-SSP (COCO) | 68.26 % | — | — |
| 1 | SSP+FT | 45.81 % | 0.84 % | **-22.45** |
| 8 | no-SSP (COCO) | 25.15 % | — | — |
| 8 | SSP+FT | 28.44 % | 4.21 % | +3.29 |

**Table 15: SSP+FT against no-SSP baseline. ScreenSpot CPV is the held-out protocol; hand-corrected CPV is reported for completeness.**

The SSP backbone hurts low-budget transfer by 22 points and helps medium-budget transfer by 3 points. Both effects are real but neither lifts the deployed-weight operating point — the k = 1 no-SSP checkpoint at 68.26 % CPV remains the best on the held-out protocol. The mechanism is discussed in Section 8.3.

### 7.2.4 ADAPTIVE TEACHER

The two Adaptive Teacher configurations are reproduced from `uda_adaptive_teacher.csv` and `uda_adaptive_teacher_uda_at_full.csv`. The short variant ran on a single H100 in 217 seconds; the full variant took 35 minutes for three outer iterations on the full 8,000-image source bundle.

| Configuration | Outer iters | Epochs/iter | Source cap | n_pseudo | CPV ScreenSpot | CPV hand-corrected | Time |
|---|---:|---:|---:|---|---:|---:|---:|
| AT short | 1 | 5 | 500 | 348 / 384 | **68.56 %** | 10.96 % | 217 s |
| AT full | 3 | 10 | 8,000 | 1,042 (348+343+351) | 64.67 % | 6.74 % | 2,102 s |

**Table 16: Adaptive Teacher results, short and full configurations.**

The per-slice breakdown for the short variant is in Table 17. ScreenSpot's text slice climbs to 82.47 %, in line with the source-domain text-class strength shown in Table 13. The icon slice stays around 49 % — better than zero-shot's 38.57 % but still the dominant failure mode.

| Slice | n | hits | CPV |
|---|---:|---:|---:|
| overall (desktop) | 334 | 229 | 68.56 % |
| macOS | 172 | 121 | 70.35 % |
| Windows | 162 | 108 | 66.67 % |
| text | 194 | 160 | 82.47 % |
| icon | 140 | 69 | 49.29 % |

**Table 17: Adaptive Teacher (short variant) ScreenSpot CPV by slice. Source: `cpv_screenspot_desktop_uda_at.csv`.**

The full variant produces a slightly better text slice (83.51 %) but a noticeably worse icon slice (38.57 %), which drags the overall CPV down. The interpretation — that compounding noise across the three outer iterations of an offline pseudo-label loop is the dominant failure — is in Section 8.4.

### 7.2.5 SHOT

The three SHOT configurations are reproduced from `uda_shot.csv`, `uda_shot_uda_shot_15ep.csv`, and `uda_shot_uda_shot_freeze10.csv`. All three use the same 224 pseudo-labels at confidence 0.50.

| Configuration | Epochs | freeze | CPV ScreenSpot | CPV hand-corrected | Time |
|---|---:|---:|---:|---:|---:|
| SHOT short | 8 | 15 | 23.95 % | 0.00 % | 22 s |
| SHOT 15-ep | 15 | 15 | 26.95 % | 0.28 % | 35 s |
| SHOT freeze=10 | 8 | 10 | **34.13 %** | 0.00 % | 22 s |

**Table 18: SHOT — three configurations on the H100.**

The pattern is clear. Doubling the epoch budget at the heavier freeze adds three points; halving the freeze depth at the lighter epoch budget adds ten. The freeze schedule is the dominant knob, not the epoch count. Even the best SHOT variant sits roughly thirty points below Adaptive Teacher short, which is itself within statistical noise of the k = 1 head fine-tune.

[FIGURE 15: All-method comparison bar chart on ScreenSpot CPV.
Source: `reports/figures/ch7_all_methods_screenspot.png` (to be produced from the union of the result CSVs).
Caption: Bar chart on ScreenSpot CPV for nine configurations. Bars from highest to lowest: AT short (68.56 %), k = 1 head FT (68.26 %), AT full (64.67 %), zero-shot k = 0 (60.18 %), SSP+FT k = 1 (45.81 %), SHOT freeze=10 (34.13 %), SSP+FT k = 8 (28.44 %), SHOT 15-ep (26.95 %), k = 8 head FT (25.15 %), SHOT short (23.95 %), k = 4 head FT (10.48 %). Two clusters: a high cluster around 60-69 % comprising zero-shot, k = 1 head FT, AT short, and AT full; and a low cluster below 50 % containing every other adaptation method.]

## 7.3 GROUNDING ACCURACY (CPV)

The Central Point Validation metric is reported under two protocols. The first is the eight-image hand-corrected set, 356 ground-truth boxes, scored against `cpv_summary.csv`. The second is the ScreenSpot desktop slice (Cheng et al., 2024), 334 images, scored against `cpv_screenspot_desktop.csv`. The two protocols are run on the same checkpoint with the same confidence threshold (0.25) and NMS IoU (0.5), so any disagreement between them is a property of the data, not a property of the inference path.

### 7.3.1 HAND-CORRECTED EIGHT-IMAGE SET

The deployed `weights/visclick.onnx` (k = 1 head fine-tune) reaches **1.40 %** overall CPV on the hand-corrected set. The per-class breakdown is in Table 19.

| Class | gt boxes | centres inside | CPV % |
|---|---:|---:|---:|
| button | 15 | 2 | 13.33 |
| menu | 33 | 3 | 9.09 |
| text | 20 | 0 | 0.00 |
| text_input | 189 | 0 | 0.00 |
| icon | 89 | 0 | 0.00 |
| checkbox | 10 | 0 | 0.00 |
| **OVERALL** | **356** | **5** | **1.40** |

**Table 19: Hand-corrected CPV per class for the deployed checkpoint. Source: `cpv_summary.csv`.**

The number is bad in isolation. Two boxes worth of buttons hit; three boxes worth of menus hit; nothing else lands. The reason the number is bad is that the hand-corrected set is dominated by `text_input` and `icon` boxes — two classes that the source-domain detector is already weakest on (Table 13) and that the few-shot fine-tune at k = 1 cannot teach because the target seed contains essentially none of them. The hand-corrected set is also small enough that a few systematic misses move the overall percentage by tens of points.

### 7.3.2 SCREENSPOT DESKTOP SLICE

The same checkpoint reaches **57.49 %** overall CPV on the ScreenSpot desktop slice. The per-slice breakdown is in Table 20.

| Slice | n | hits | CPV % |
|---|---:|---:|---:|
| overall (desktop) | 334 | 192 | **57.49** |
| macOS | 172 | 107 | 62.21 |
| Windows | 162 | 85 | 52.47 |
| text | 194 | 145 | 74.74 |
| icon | 140 | 47 | 33.57 |

**Table 20: ScreenSpot desktop CPV by slice for the deployed checkpoint. Source: `cpv_screenspot_desktop.csv`.**

The macOS slice is ten points stronger than Windows, which is consistent with the visual style of macOS dialogs being closer to the unified source bundle's design language. The text slice is more than twice the icon slice, again consistent with the source-domain class imbalance.

[FIGURE 16: ScreenSpot desktop CPV by slice and method.
Source: `reports/figures/ch7_screenspot_by_slice.png` (to be produced from the union of `cpv_screenspot_desktop*.csv`).
Caption: Grouped bar chart. Five rows of bars (overall, macOS, Windows, text, icon) by four method columns (k = 1 head FT, AT short, AT full, SHOT freeze=10). The text slice is the strongest across every method (74-83 %); the icon slice is the dominant failure mode for every method (25-49 %); macOS consistently outperforms Windows by 4-12 points across methods.]

### 7.3.3 PROTOCOL DISAGREEMENT

The deployed weight scores 1.40 % on the hand-corrected protocol and 57.49 % on the ScreenSpot protocol. The gap of 56 points is the project's headline measurement of evaluation-protocol fragility. The same model, the same inference path, the same metric — but two ground-truth distributions that disagree about whether the model is good or bad. The mechanisms behind the disagreement are dissected in Section 8.2; the practical consequence is that any single-protocol benchmark in the UI-detection literature should be read with that disagreement in mind.

## 7.4 FOUR-METHOD COMPARISON ON T01-T15

The four-method comparison runs the canonical task list (T01-T14 positive, T15 negative) through the four baseline methods (`scripts/run_baselines.py`). The aggregate results are in `baseline_summary.csv`; the per-task verdict matrix is in `baseline_per_task.csv`.

### 7.4.1 AGGREGATE TASK SUCCESS RATE

The aggregate TSR across the 15-task suite is in Table 21.

| Method | n_tasks | pass | fail | refused/skipped | TSR | Median latency |
|---|---:|---:|---:|---:|---:|---:|
| template (cv2.matchTemplate) | 15 | 11 | 4 | 0 | **73.3 %** | 285 ms |
| visclick | 15 | 11 | 4 | 0 | **73.3 %** | 8,055 ms |
| ocr_only (EasyOCR + rapidfuzz) | 15 | 5 | 10 | 0 | 33.3 % | 7,775 ms |
| pywinauto (UIA tree) | 15 | 1 | 14 | 0 | 6.7 % | 130 ms |

**Table 21: Four-method aggregate TSR on T01-T15. Source: `baseline_summary.csv`.**

The two text-driven methods (template and visclick) tie at 11 / 15 = 73.3 %, twenty-eight points ahead of the next method. The OCR-only baseline lands a third of the suite. The pywinauto baseline lands one task. The pywinauto failure is exactly the result the literature on accessibility-tree automation predicts on Windows 11: classic Win32 controls expose clean UIA trees, but the Electron, WinUI 3, and ARIA-served-via-browser surfaces that dominate the modern Windows desktop expose either a degenerate tree or one with localised internal names that do not match the visible labels.

### 7.4.2 PER-TASK VERDICT MATRIX

The per-task matrix is in Table 22. This is the honest picture: the four methods agree on most tasks, disagree on a few, and the disagreements are diagnostic.

| Task | Instruction | Negative? | pywinauto | ocr_only | template | visclick |
|---|---|:---:|:---:|:---:|:---:|:---:|
| T01 | click Save | — | fail | fail | pass | pass |
| T02 | open File menu | — | fail | pass | pass | pass |
| T03 | click Search icon | — | fail | fail | pass | pass |
| T04 | click first command | — | fail | fail | fail | pass |
| T05 | click search settings | — | fail | pass | pass | pass |
| T06 | click View tab | — | fail | fail | pass | fail |
| T07 | click Properties | — | fail | pass | pass | pass |
| T08 | click address bar | — | fail | fail | pass | pass |
| T09 | click address bar | — | fail | fail | pass | pass |
| T10 | click Clear browsing data | — | fail | fail | pass | pass |
| T11 | toggle Use system proxy | — | fail | fail | fail | pass |
| T12 | click word hello | — | fail | pass | fail | pass |
| T13 | click Commit | — | fail | fail | pass | fail |
| T14 | click first download | — | fail | fail | fail | fail |
| T15 | click Save | YES | pass | pass | pass | **fail** |

**Table 22: Per-task verdict matrix for the four-method suite. Source: `baseline_per_task.csv`. T15 is the negative test case (the dialog it points to does not exist on screen); the correct verdict is "refused", scored here as `fail` for visclick because the prototype did not refuse.**

Two patterns are visible. First, the template method and visclick succeed on the same subset of positive tasks (eleven each), but disagree on which: template gets T06 and T13 that visclick misses; visclick gets T04 and T11 that template misses. Each method has a class of tasks it handles that the other does not. Second, T15 is the only task on which template, ocr_only, and pywinauto all "pass" — they pass because they fall back to a low-confidence guess and click somewhere near a Save button on a different dialog. Visclick is the only method that engages its refusal rule on T15, which is the architecturally correct behaviour. The rule fired but selected a low-confidence positive box rather than refusing outright; this is the bug discussed in Section 8.4 under risk RR-05.

### 7.4.3 WHERE EACH METHOD WINS

- **Template** wins on tasks where the visual target is a stable, distinctive bitmap (T06's View tab, T13's Commit button). It loses on tasks where the target text is small or the surrounding pixels are too theme-dependent (T04, T11, T12, T14).
- **OCR-only** wins on tasks where the target text is large, isolated, and the dialog is dialog-shaped (T02, T05, T07, T12). It loses everywhere a non-text affordance is the right click target (T01, T03, T06).
- **pywinauto** wins on T15 only — and only because every method "wins" T15 by accident in this protocol. On the positive tasks pywinauto loses because the UIA tree on the project's test surfaces is degenerate or misnamed.
- **VisClick** wins on tasks where the detector finds the right box and the matcher's class-aware bonus disambiguates (T04, T11, T12). It loses on T06 (detector miss on the View tab), T13 (detector miss on Commit), and T15 (refusal rule fired but selected the wrong box).

The four-method comparison is what supports the dissertation's RQ1 claim: the modular CV-driven method ties the strongest classical baseline on a desktop test suite that the accessibility-tree baseline cannot navigate, with a refusal rule that is architecturally correct even though its current threshold needs work.

## 7.5 NON-FUNCTIONAL REQUIREMENT VERIFICATION

The non-functional requirements were specified in Section 3.6 with quantitative targets. Each is verified against the same evaluation run, and the per-attempt latency distributions are read from `nfr_performance.csv`. Table 23 reproduces the requirements-evidence ledger.

| ID | Requirement | Target | Measured | Verdict |
|---|---|---|---|---|
| NFR-01 | TSR | ≥ 50 % | 73.3 % (visclick) | **FULL** |
| NFR-02 | Latency p95 | ≤ 15 s | 14.8 s | FULL (just) |
| NFR-03 | Peak RSS | ≤ 2 GB | ~764 MB | FULL |
| NFR-04 | Reliability | 0 crashes / 60 attempts | 0 | FULL |
| NFR-05 | Usability | Tk dialog + keyboard | Self-review FULL | PARTIAL |
| NFR-06 | Maintainability | PEP-8 clean modular package | 9 modules ~1591 LoC, ruff clean | FULL |
| NFR-07 | Extensibility | New methods plug in via protocol | 4 adapters demonstrate | FULL |
| NFR-08 | Security | No off-machine I/O at inference | grep audit clean | FULL |
| NFR-09 | Compatibility | Win11 + multi-monitor | Verified on test rig | PARTIAL |
| NFR-10 | Scalability | Linear in detection count | Analytical only | PARTIAL |

**Table 23: NFR verification ledger. Source: `requirements_evidence.csv`.**

### 7.5.1 ACCURACY

NFR-01's target of 50 % TSR is met at 73.3 % for visclick (Table 21). The headline number is the same 11 / 15 reported in Section 7.4.1.

### 7.5.2 LATENCY

NFR-02's target of 15-second p95 is the most marginal pass on the ledger, at 14.8 seconds. The latency distribution is bimodal because the per-box-OCR happy path runs in roughly two seconds while the OCR-fallback path adds six. Table 24 breaks down the per-method distribution from `nfr_performance.csv`.

| Method | n | mean | median | p90 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|
| template | 11 | 299 ms | 285 ms | 379 ms | 455 ms | 532 ms |
| pywinauto | 12 | 239 ms | 130 ms | 466 ms | 681 ms | 924 ms |
| ocr_only | 15 | 9,130 ms | 7,775 ms | 10,571 ms | 15,136 ms | 25,676 ms |
| visclick | 15 | 7,750 ms | 8,055 ms | 10,669 ms | 14,805 ms | 23,938 ms |

**Table 24: Per-method end-to-end latency distribution on T01-T15.**

Two observations matter for the deployment claim. First, template and pywinauto sit at the sub-second end because both rely on a single fast lookup (template matching or a UIA-tree query). VisClick and ocr_only sit at the multi-second end because both invoke EasyOCR. Second, VisClick's p95 sits 0.2 seconds inside the NFR-02 target; this is the closest call on the entire NFR ledger and motivates the latency-budget discussion in Section 8.7.

The ONNX-only detector benchmark in `detector_bench_snapshot_2026-05-14.csv` records the detect-layer cost in isolation: median 67.8 ms over 50 runs at 640 × 640, p95 79.0 ms. The detector contributes roughly 1 % of the end-to-end latency budget; OCR is the dominant cost.

### 7.5.3 MEMORY, RELIABILITY, AND THE REMAINING NFRS

NFR-03's target of 2 GB peak RSS is met at roughly 764 MB after the EasyOCR model loads, well inside the budget; the per-method memory profile committed to the proposal is gap D-11 and is the one outstanding measurement on the ledger. NFR-04's reliability target of zero crashes across the 60-attempt evaluation run is met (no orchestrator-level exceptions across `baseline_results.csv`). NFR-06's maintainability target is met by the nine-module architecture in `src/visclick/` running ruff clean. NFR-07's extensibility target is met by the four-adapter implementation of the `BaselineMethod` protocol described in Section 6.11. NFR-08's security target — no off-machine I/O during inference — is met by a grep audit of `src/visclick/` showing zero imports of `requests`, `urllib`, or `http`. NFR-05 (usability), NFR-09 (cross-platform compatibility), and NFR-10 (scalability past the empirical ceiling) are scored PARTIAL on the ledger; the open work for each is in Section 8.7.

## 7.6 CHAPTER SUMMARY

The empirical picture is consistent across protocols, even when individual numbers disagree. The two source-domain backbones produce the architecture-comparison result the literature predicts: YOLOv8s reaches roughly twice the source-side mAP at one-sixth the wall-clock cost of DETR-R50 on the project's compute budget. The few-shot sample-efficiency curve produces the catastrophic-forgetting result that motivates the deployed weight choice (k = 1, 68.26 % ScreenSpot CPV). The three cross-domain adaptation methods produce results in three different categories: SSP+FT hurts low-budget transfer and helps medium-budget transfer; Adaptive Teacher matches the head fine-tune at 68.56 % CPV with no labelled target shots, but degrades when scaled up; SHOT underperforms across all three configurations, with freeze depth dominating epoch budget as the operating knob. The four-method classical comparison ties visclick with cv2 template matching at 73.3 % TSR on the 15-task suite, with the architectural caveat that visclick is the only method whose refusal rule is correct in principle even though its current threshold mis-fires on T15. The non-functional requirements are met across the ledger; the latency p95 is the closest call.

The next chapter takes these numbers and asks what they mean.

---

# CHAPTER 08 – EVALUATION AND DISCUSSION

## 8.1 CHAPTER OVERVIEW

This chapter takes the empirical numbers from Chapter 7 and asks what they mean. The structure follows the four research questions stated in Section 1.5. Section 8.2 evaluates RQ1, the comparison of VisClick against the three classical baselines, and includes the headline finding that two evaluation protocols disagree by an order of magnitude on the same model. Section 8.3 evaluates RQ2, the question of how well adaptation closes the source-to-target domain gap; this is the section where the catastrophic-forgetting peak at k = 1, the AT-full regression, and the SHOT freeze-depth ablation are interpreted. Section 8.4 evaluates RQ3, the architectural comparison between YOLOv8 and DETR and the methodological comparison between Adaptive Teacher and SHOT. Section 8.5 evaluates RQ4, the design choices that govern the deployed prototype's behaviour. Section 8.6 records threats to validity. Section 8.7 covers ethics, deployment considerations, and future work. Section 8.8 closes the chapter.

A note on framing. The dissertation's experimental matrix produced a mixture of clean wins, mixed results, and clear negative results. All three are reported in the same voice in this chapter. Negative and mixed results are not failures of the project — they are part of what the project learned, and they are the parts that distinguish a dissertation from a marketing brochure.

## 8.2 RQ1 — VISCLICK VERSUS CLASSICAL BASELINES

RQ1 asked whether a modular CV-driven pipeline can match the performance of established classical baselines (image template matching, OCR-only matching, accessibility-tree automation) on a desktop test suite. The four-method comparison in Section 7.4 answers the question directly. VisClick and `cv2.matchTemplate` tie at 11 / 15 = 73.3 % task-success rate. The OCR-only baseline lands 5 / 15 = 33.3 %. The pywinauto baseline lands 1 / 15 = 6.7 %.

The headline tie between VisClick and template matching looks unhelpful at first reading. The two methods reach the same percentage but on a partially overlapping set of tasks (Section 7.4.2): they agree on nine, disagree on four. Where they disagree, the diagnosis is informative. Template matching wins on T06 (the View tab in File Explorer's ribbon, a stable bitmap that any rendering of the same theme reproduces pixel-for-pixel) and T13 (the Commit button in a Git GUI, again a stable visual asset). VisClick wins on T04 (the first command in a multi-row context menu, where the visible bitmap depends on which command is at row one), T11 (the toggle for *Use system proxy*, where the visible affordance is a slider whose pixel content shifts with the OS theme), and T12 (clicking the word *hello* in a Notepad document, where there is no fixed bitmap because the word is just text).

The pattern is the dissertation's first methodological lesson. Template matching wins on the stable-bitmap subclass of UI tasks; CV-driven detection wins on the dynamic-bitmap subclass. The two methods are not in competition — they are complementary. A practical deployment would use template matching where the asset is known to be stable (icons in the system tray, branded buttons in the corporate suite) and fall back to detection-plus-OCR where the asset is dynamic. The dissertation's specific contribution to this reading is that the CV-driven path closes the gap on the dynamic-bitmap class without giving up the easy wins on the stable class.

The pywinauto baseline's 1 / 15 result deserves separate comment because it is so different from what the accessibility-tree literature predicts. Section 1.2 set out the prediction: pywinauto succeeds on classic Win32 controls and fails on the modern Electron / WinUI 3 / browser-served-via-ARIA surfaces. The 1 / 15 result is the empirical confirmation of that prediction on the project's specific test surface, and the 14 / 15 failure mode is structural rather than a bug in the baseline. The single pywinauto pass on T15 is an artefact of T15 being the negative test case; pywinauto "passes" T15 by accident because every method "passes" T15 by clicking on a wrong but plausibly-named control. The methodologically correct verdict for pywinauto on T15 is that the test is uninformative for the accessibility-tree case, not that pywinauto succeeded.

### 8.2.1 EVALUATION-PROTOCOL DISAGREEMENT

The Section 7.3 result that the same deployed checkpoint scores 1.40 % CPV on the hand-corrected eight-image set and 57.49 % CPV on the ScreenSpot 334-image desktop slice is the project's most uncomfortable empirical finding. It is also the most useful one. The two numbers disagree by 56 percentage points, more than any other gap reported in this dissertation. The same model, the same inference path, the same metric. The disagreement is entirely a property of the ground-truth distribution.

Three mechanisms produce the gap. The first is class composition. The hand-corrected set is dominated by `text_input` (189 / 356) and `icon` (89 / 356) — exactly the two classes the source-domain detector is weakest on (Table 13). The ScreenSpot slice is dominated by `text` (194 / 334) and `icon` (140 / 334), and `text` is the source-domain detector's third-strongest class. Any model that scores well on the source-domain class distribution will score better on ScreenSpot than on the hand-corrected set, regardless of any property of the inference path. The second mechanism is annotation density. The hand-corrected set has on average 44.5 boxes per image; ScreenSpot has 1 box per image, the box being the click target for one specific instruction. Per-image scoring of the hand-corrected set rewards a model that finds *all* of the dense, small affordances; per-instruction scoring of ScreenSpot rewards a model that finds the *specific* affordance the instruction names. The two protocols are answering different questions. The third mechanism is statistical noise. With eight images and 356 boxes, the hand-corrected protocol is sensitive to single-image effects in a way that 334 images and 334 boxes is not.

The disagreement is therefore not a flaw to be fixed — it is the expected consequence of running two protocols that ask different questions on different distributions. The dissertation's response is to report both protocols on every operating point, side by side. The reader is given the data to choose which protocol matches the deployment they care about. The methodological point — that any UI-detection paper that reports only one of these two protocols is reporting an incomplete answer — is the secondary contribution of this work, behind the primary contribution of the dissertation's deployed prototype.


### 8.2.2 PER-TASK ERROR ANALYSIS

The aggregated TSR numbers in Section 7.4.1 hide as much as they reveal. The per-task verdict matrix in Table 22 is where the diagnostic information lives. Walking through it task by task surfaces a small number of recurring failure modes that taken together explain almost everything in the matrix.

**T01 (click Save) and T03 (click Search icon).** Both pass for template and visclick, both fail for ocr_only and pywinauto. The shared failure mode for the two losers is the same one in two flavours: ocr_only fails because the targets are non-text affordances (the *Save* button has the icon but no visible text in the dialog the test runs against; the search icon is purely graphical), and pywinauto fails because the dialog is a modern dialog that does not expose the controls in a form the UIA tree can return. Template wins because both targets are stable bitmaps in the test rendering; visclick wins because the source-domain detector reliably finds the box and the matcher is happy to use the class label as the only matching cue when the OCR text is absent. These are the easy wins.

**T04 (click first command).** The single task on which template fails but visclick passes. The instruction *click first command* refers to the topmost row of a multi-row context menu. The visible bitmap of the first row depends entirely on which command is at row one, which is application-state-dependent. Template matching cannot anchor on a stable bitmap because there isn't one. VisClick passes because the matcher's *first* heuristic — when the instruction starts with an ordinal and the detector returns multiple boxes of the same class, take the topmost — falls out of the rapidfuzz scoring and the natural reading order. This is the cleanest single example of the modular CV-driven path doing something the classical baselines cannot do at all.

**T06 (click View tab).** Template passes; visclick fails. The View tab is part of File Explorer's ribbon, which the source-domain detector did not see during training (mobile UIs do not have ribbons). The detector emits zero candidate boxes near the tab, the matcher cannot run, and the OCR fallback finds the *View* text but at a confidence that lands below the threshold. The visclick failure is therefore not a matcher bug — it is a detector failure rooted in the source-target distribution gap. The lesson is that the source-domain bundle's class catalogue (`button`, `text`, `text_input`, `icon`, `menu`, `checkbox`) does not include `tab`, and ribbon-style tabs are far enough from the closest catalogue class (`menu`) that the detector does not promote them.

**T11 (toggle Use system proxy).** Template fails; visclick passes. The toggle is a Windows 11 *slider* control whose pixel content depends on the toggle's current state. Template matching cannot match against either state if the target snapshot was taken in the other. VisClick passes because the detector finds the toggle as a `checkbox` (the closest catalogue class), the matcher's class-aware bonus pushes the class-matching candidate above the threshold, and the click lands. This is the second clean example of the CV-driven path generalising in a way template matching cannot.

**T12 (click word hello).** Both ocr_only and visclick pass; template fails. There is no fixed bitmap for the word *hello* because the word's pixel content depends on its position in the document, the font, and the rendering. Both text-driven methods recover by reading the word and matching the OCR string. Template fails because there is nothing to template-match against.

**T13 (click Commit) and T14 (click first download).** Both fail for visclick. T13 fails because the detector misses the *Commit* button entirely (the button sits below the dialog's main canvas, in a region the detector tends to under-attend). T14 fails because the *first download* is a dynamic row in a tabular list that the detector does not return any boxes for. Both failures are detector failures, not matcher failures, and both would be addressable by a target-aware fine-tune at higher k — at the cost of the catastrophic-forgetting peak documented in Section 8.3.1.

**T15 (negative case).** Template, ocr_only, and pywinauto all "pass" by accident — they each click a wrong but plausible Save-shaped affordance on a different dialog. VisClick fails because the matcher selected a low-confidence positive box rather than refusing. The methodologically correct verdict is that VisClick is the only method that engaged its refusal logic at all on this task, and the failure is a threshold-tuning issue rather than a structural one.

The matrix as a whole supports the dissertation's RQ1 claim. Template matching is excellent at stable-bitmap tasks. The accessibility-tree baseline is structurally limited on Windows 11. OCR-only is a one-trick method, fine on text-only targets, useless elsewhere. VisClick is the only method that handles the dynamic-bitmap tasks while not giving up the stable-bitmap easy wins. The four methods together would beat any one of them, but the layered architecture that VisClick brings is what makes a four-method ensemble feasible at all.

## 8.3 RQ2 — HOW WELL DOES ADAPTATION CLOSE THE GAP?

RQ2 asked whether and how adaptation methods close the source-to-target domain gap. The four adaptation methods reported in Section 7.2 (few-shot fine-tune, SSP+FT, Adaptive Teacher, SHOT) answer the question with a clear and slightly uncomfortable picture. The deployed weight at k = 1 head fine-tune lifts ScreenSpot CPV from 60.18 % (zero-shot) to 68.26 % — eight percentage points of gap closure with a single labelled image. Adaptive Teacher short reaches 68.56 % with no labelled target images. Every other adaptation method reported, including the full-protocol Adaptive Teacher and every SHOT variant, sits below the zero-shot baseline.

Three sub-sections unpack the most interesting parts of the result.

### 8.3.1 CATASTROPHIC FORGETTING AT K = 1

The few-shot sample-efficiency curve in Table 14 and Figure 14 has the shape that the literature on small-data fine-tuning predicts but rarely measures cleanly: ScreenSpot CPV peaks at k = 1 (68.26 %) and falls off the cliff at k = 2 (20.06 %) and k = 4 (10.48 %), recovering partially at k = 8 (25.15 %). The hand-corrected mAP rises monotonically across the same sweep. The two protocols disagree about which checkpoint is best in a way that has a single mechanistic explanation.

At k = 1 the head fine-tune sees one labelled desktop image. The gradient updates the head's class boundaries enough to bias the existing source-domain features toward the desktop's class distribution, but not enough to overwrite the source-domain knowledge encoded in the (frozen) backbone. The result is the source-domain features applied through a desktop-aware head — a setup that ScreenSpot's per-instruction protocol scores well because the per-class semantics carry across.

At k = 2 the head fine-tune sees two labelled desktop images. The gradient updates the head far enough to re-weight the class probabilities specifically for the seed's two screenshots, and the head loses the source-domain breadth it had at k = 1. This is the catastrophic-forgetting phenomenon described by McCloskey and Cohen (1989) and is well understood in the continual-learning literature: when the new training data is small relative to the model capacity, the gradient overwrites prior knowledge rather than augmenting it. Twenty epochs of training on two images is enough to specialise the head onto those images at the cost of every other distribution the head saw during source training.

At k = 4 the same effect compounds. At k = 8 the seed is finally large enough that it starts to look like a small but representative target distribution, and the head recovers some of the breadth it had at k = 1 — though still not enough to beat the k = 1 operating point under ScreenSpot's protocol. The hand-corrected mAP rises monotonically through this whole curve because the hand-corrected set is itself drawn from the same theme/app distribution as the seed, so memorising the seed *helps* the hand-corrected score even though it hurts the held-out ScreenSpot score.

The deployed weight is the k = 1 checkpoint because ScreenSpot is the held-out third-party-scored protocol; choosing k = 8 would mean choosing the checkpoint that scored higher on a fit-to-train protocol at the cost of the held-out generalisation. The lesson, applicable beyond this dissertation, is that small-budget head fine-tuning has a non-monotonic generalisation curve and that the operating point should be chosen on the basis of held-out evaluation, not training-distribution-matched evaluation.

### 8.3.2 WHY ADAPTIVE TEACHER FULL UNDERPERFORMS ADAPTIVE TEACHER SHORT

The Adaptive Teacher result in Section 7.2.4 has an opposite-of-expected shape. The short variant (1 outer iteration, 500 source images, 5 epochs) reaches 68.56 % ScreenSpot CPV. The full variant (3 outer iterations, 8,000 source images, 10 epochs each) reaches 64.67 %, almost four points lower. Both also drop on the hand-corrected protocol (10.96 % to 6.74 %). Adding source data, more outer iterations, and more epochs makes the result worse, not better.

Two mechanisms drive the regression. The first is pseudo-label noise compounding. The original Adaptive Teacher (Li et al., 2022b) couples the student-teacher loop with an Exponential Moving Average update that stabilises the teacher across the inner training steps. The project's simplified offline variant (Section 6.5.4) does not have an EMA stabiliser; each outer iteration's teacher is the previous iteration's student, full stop. If the previous iteration's student introduced systematic errors into the pseudo-labels, the next iteration's teacher inherits and amplifies them. With one iteration, the teacher is the source-domain detector at its strongest; with three iterations, the teacher is a model whose strongest-on-source signal has been filtered through two rounds of self-confirming bias. The numerical effect is small per iteration but compounds: 348 → 343 → 351 pseudo-labels emitted per iteration tells the same story as the CPV drop.

The second mechanism is target-signal dilution in the mixed batch. The student trains on a balanced batch of labelled source plus pseudo-labelled target. With a 500-image source pool, the target signal is roughly 384 / (500 + 384) = 43 % of the mixed batch; with the full 8,000-image pool, the target signal drops to 384 / (8,000 + 384) = 4.6 %. The student's gradient is pulled almost an order of magnitude harder toward the source distribution in the full configuration than in the short configuration. Ten epochs over three outer iterations across that imbalance is roughly thirty epochs of source-dominated training plus fifteen epochs equivalent of target signal — not enough target adaptation to overcome the source pull.

The combined effect is the four-point regression. The methodological lesson is that simplifying an online UDA protocol to an offline one introduces a stabiliser-removal failure mode that scales with the number of outer iterations, and that the natural defence (more source data) makes the problem worse rather than better. A practical recovery would be to add an EMA approximation in the offline loop (averaging the student weights across the iterations rather than taking the last student) or to cap the source pool to roughly the size of the target pool. Both are recorded as future work in Section 8.7.

### 8.3.3 THE SHOT FREEZE-DEPTH ABLATION

The SHOT result in Section 7.2.5 has a different but equally diagnostic shape. Three configurations were run: short (8 epochs, freeze=15) at 23.95 %, 15-epoch (15 epochs, freeze=15) at 26.95 %, and freeze=10 (8 epochs, freeze=10) at 34.13 %. The configuration labels are exhaustive in the parameter cross: epoch budget × freeze depth at two levels each. The freeze-depth knob lifts CPV by ten points; the epoch-budget knob lifts CPV by three points. Freeze depth dominates.

The mechanistic interpretation aligns with the SHOT design intent (Liang et al., 2020). SHOT freezes the source classification head — the source hypothesis — and adapts the feature extractor on the unlabelled target. The freeze depth in the project's implementation controls how much of the YOLOv8 backbone is held fixed: freeze=15 holds the first 15 layers (the entire CSPDarknet53 backbone), freeze=10 holds only the first 10 (the early backbone blocks, leaving the middle and late blocks trainable). The result that freeze=10 is better than freeze=15 says that the middle and late backbone blocks carry domain-specific signal that needs to adapt for desktop transfer; freezing them denies the model the gradient access it needs to align them.

The result that the epoch-budget knob is marginal says the opposite. Once the freeze depth is set, the loss converges quickly. SHOT does not benefit from longer training within a frozen-too-deep configuration; the freeze depth is the constraint that determines the asymptote.

Even the best SHOT variant at 34.13 % CPV sits roughly thirty points below Adaptive Teacher short and the k = 1 head fine-tune. The honest conclusion for SHOT is that it does not transfer well under the project's data and compute budget, and that the freeze-depth ablation is the only knob that moves the result meaningfully. Why SHOT fails relative to Adaptive Teacher is a structural argument, taken up in Section 8.4. The practical recommendation — for any future work building on this dissertation — is that the SHOT-on-detection adaptation should not start with a heavy freeze. Freeze the head only, leave the backbone trainable, and revisit the trade-off.

### 8.3.4 SSP+FT ON MOBILE UI HURTS DESKTOP TRANSFER

The SSP+FT result in Section 7.2.3 produces the smallest of the negative findings but the cleanest of the diagnoses. SimSiam pre-training on the mobile UI corpus, followed by k = 1 head fine-tune on the desktop seed, lands 22 points below the no-SSP k = 1 baseline (45.81 % vs 68.26 %). At k = 8 the same comparison flips by three points in SSP's favour (28.44 % vs 25.15 %).

The interpretation is alignment. SimSiam teaches the backbone to produce features that map together-augmented views of the same image to nearby points in feature space. Run on a mobile UI corpus, those features become aligned with the mobile UI distribution: the backbone learns that two crops of a RICO screen, augmented differently, should be neighbours. That is a useful objective for a downstream RICO task. It is not a useful objective for a downstream desktop task, where the backbone now produces representations that are *farther* from the desktop class manifold than the COCO-pre-trained backbone was, because COCO is a more topically diverse corpus that happens to overlap better with the desktop's visual style.

The k = 8 reversal supports this reading. With eight labelled desktop images, the head has enough signal to retune around the SSP backbone's particular feature geometry; the small amount of self-supervised structure helps once there is enough labelled data to anchor it. With one labelled image, the head cannot reach far enough to repair the alignment, and the source-aligned features become a strict downgrade.

The methodological consequence is that self-supervised pre-training corpora have to be chosen with the target domain in mind, not with the source-domain availability in mind. The project's SimSiam corpus was the readily available unified mobile UI bundle. A target-aware SimSiam would have used a corpus drawn from desktop screenshots — exactly the corpus that gap D-06 commits to producing. The dissertation cannot test target-aware SimSiam without that corpus, and the result reported here is therefore the worst-case operating point rather than a definitive judgement on SSP for UI detection generally. The honest framing is that SSP on a misaligned corpus hurts low-budget transfer, and that target-aligned SSP is open future work.


### 8.3.5 CROSS-METHOD SYNTHESIS — WHEN TO USE WHAT

The four adaptation methods reported in this dissertation are not interchangeable. Each is the right choice in a different regime, and the wrong choice elsewhere. Synthesising the empirical evidence into a one-page decision guide is useful both for the reader who wants to apply this work and for the reader who wants to know which experiments would close the most uncertainty in a follow-up.

**Few-shot head fine-tune** is the right choice when there are between zero and a handful of labelled target images, the target distribution is at least loosely stylistically related to the source, and the deployment environment's evaluation protocol is the held-out per-instruction grounding kind (not the dense per-image kind). The k = 1 operating point is the sweet spot. The catastrophic-forgetting peak makes it tempting to "just add more labels", which is the trap; more labels at this scale is *worse*, not better.

**Self-supervised pre-training** is the right choice when there is a large unlabelled corpus that is *target-distribution-aligned*. The dissertation's negative result on SSP is a result on a misaligned corpus, not a result on SSP itself. With a 2,000-image desktop corpus in hand (gap D-06), SimSiam pre-training would be a different experiment with a different expected outcome.

**Adaptive Teacher** is the right choice when there is no labelled target and a moderate-sized unlabelled target corpus, and the target's class definitions overlap with the source's class definitions. The simplified offline variant in this dissertation reaches the same operating point as the k = 1 head fine-tune with no labelled target images, which makes it the right method when label collection is the binding constraint. The cautionary note is the AT-full regression: more iterations, more source data, more epochs are not free upgrades.

**SHOT** is the right choice when the source classifier head is genuinely stable across domains and only the visual style shifts. The dissertation's negative result on SHOT is consistent with the structural mismatch between mobile and desktop UI class semantics: the head trained on RICO's class boundaries is not the head a desktop deployment needs, and the SHOT objective's freezing of that head is a constraint the project's distribution shift cannot accommodate. SHOT will recover for tasks where the head can sensibly stay frozen — image classification across photo styles is the canonical example — and will struggle for object-detection tasks where the class definitions themselves shift.

The decision tree, in compact form: *labelled target available?* yes → few-shot at k = 1; no, but unlabelled target available and class boundaries shift → simplified Adaptive Teacher; no, but unlabelled target available and class boundaries are stable → SHOT (full backbone, light freeze); large unlabelled target *aligned* with source → SSP+FT for the backbone, then few-shot for the head.

The dissertation's deployed system uses the first leaf of the tree (k = 1 head fine-tune) because that is the operating point with the cleanest published number on the held-out protocol. A practical next step is to ensemble the deployed weight with an Adaptive-Teacher-trained checkpoint at the inference path, which is recorded as gap D-14.

## 8.4 RQ3 — ARCHITECTURAL AND METHODOLOGICAL COMPARISONS

RQ3 asked whether the choice of detector backbone (YOLOv8 vs DETR) and the choice of UDA family (Adaptive Teacher vs SHOT) made a measurable difference under the project's compute budget. The Section 7.2.1 backbone result and the Section 7.2.4–7.2.5 UDA result answer both questions in the affirmative.

### 8.4.1 YOLOV8S VERSUS DETR-R50

The architectural comparison is unambiguous. YOLOv8s reaches mAP@0.5 = 0.450 on the source-domain val split in 2.7 hours of T4 time. DETR-R50 reaches mAP@0.5 = 0.244 in 16 hours. YOLOv8s is twice as good and six times faster.

Three things drive the gap. The first is the data efficiency of YOLOv8's anchor-and-NMS pipeline relative to DETR's set-prediction objective on small-to-medium-scale datasets. The original DETR paper (Carion et al., 2020) reported that DETR needs roughly 500 epochs to reach competitive performance on COCO; the project's six-epoch run is a tiny fraction of that. The follow-up DAB-DETR and Deformable-DETR variants reduced the epoch requirement substantially, but at the cost of architectural simplicity that the project did not adopt. The second is the small-object weakness in DETR's attention pattern. Section 6.4.2 noted that desktop UIs are packed scenes with a high density of small affordances (icons, checkboxes, narrow text fields), exactly the regime DETR struggles with. The per-class breakdown of the DETR run (not reproduced here for brevity) showed the strongest performance on `text` and the weakest on `checkbox`, consistent with the small-object hypothesis. The third is hyperparameter and infrastructure brittleness. DETR training on a Colab Free T4 needed careful gradient accumulation to fit a meaningful effective batch into 16 GB, and required four separate Colab sessions to complete six epochs. YOLOv8 training fit cleanly into a single session with no special accommodation.

The lesson for any practitioner picking a detector for a similar UI-detection task is straightforward. Under a small-data, small-compute budget, the YOLOv8 family is the default. DETR is the right choice only if one of three things is true: the dataset is large enough to justify the long training schedule, the compute budget is large enough to absorb the wall-clock cost, or the application is one where DETR's clean theoretical formulation (no anchors, no NMS) is worth the engineering cost on its own terms. None of those conditions hold for this project.

### 8.4.2 ADAPTIVE TEACHER VERSUS SHOT

The methodological comparison is sharper than the architectural one. Adaptive Teacher short reaches 68.56 % CPV with no labelled target. SHOT freeze=10 reaches 34.13 % under the same data budget. The gap of 34 percentage points is far larger than the typical gap between competing UDA methods reported in the literature (Li et al., 2022b; Liang et al., 2020; Sahay et al., 2023).

Two structural differences explain the gap. The first is what the two methods adapt. Adaptive Teacher trains a student on a *mixed* batch — labelled source plus pseudo-labelled target — and the student updates the entire detector (backbone, neck, head) under the combined gradient. SHOT freezes the head and adapts the feature extractor only, on a target-pseudo-label-only objective. The Adaptive Teacher student therefore receives a strong signal from the source data at every step, which keeps it from drifting onto the noisy pseudo-label distribution; the SHOT extractor receives no such anchor and is free to drift.

The second is the role of the initial teacher quality. Both methods bootstrap from the source-domain detector, but they use that detector differently. Adaptive Teacher uses the source detector once, to emit pseudo-labels at the start of an outer iteration, and then the student replaces the teacher. SHOT uses the source-trained head as a permanent fixed point: the freeze means the head's class boundaries are locked, and the extractor is forced to reshape its features to fit the locked boundaries. If the source-trained head was well calibrated for the source distribution but mis-calibrated for the target, the SHOT objective is asking the extractor to do impossible work — to reshape features so that classes the source head learned poorly are now well separated. The Adaptive Teacher student has no such constraint; it is allowed to update the head along with the extractor, so a class that the source head got wrong can be re-learned rather than worked around.

The lesson is that for a target distribution that differs from the source not just in image style but also in the relative frequency and salience of classes — as desktop UIs differ from mobile UIs in exactly these axes — Adaptive-Teacher-family methods that allow head updating are the better fit. SHOT-family methods are the better fit when the class definition is stable across domains and only the visual style shifts (the original SHOT paper's office-to-amazon image classification benchmark is the canonical example). UI detection across the mobile-to-desktop boundary is not that benchmark.

This is also why the SHOT freeze-depth ablation result in Section 8.3.3 makes sense. Reducing the freeze from 15 to 10 layers — letting more of the backbone adapt — partially recovers the gap by giving the extractor more capacity to compensate for the locked head. It does not close the gap, because the locked head remains the binding constraint; it just makes the constraint less binding.

The practical recommendation is to use the simplified Adaptive Teacher (or a richer EMA-stabilised online version) as the UDA method of choice for cross-domain UI detection, and to reserve SHOT-family methods for tasks where the head is genuinely stable across domains.


### 8.4.3 BACKBONE CHOICE IN OTHER REGIMES

The Section 8.4.1 result that YOLOv8s strictly dominates DETR-R50 under the project's compute budget is not a universal claim. It is a regime-specific claim, and the regime should be named explicitly so the result is portable to follow-up work that operates in different regimes.

YOLOv8s wins under three simultaneous constraints. First, the training corpus is small (10,000 images sampled from the unified bundle). Second, the compute budget is a single T4 GPU with a single-session ceiling of roughly 12 hours. Third, the target distribution has high small-object density (packed-scene UIs with many small affordances). All three constraints favour the anchor-and-NMS pipeline that YOLOv8 ships with: anchors give the optimiser a head start on small-object localisation, NMS handles the dense overlapping-prediction case naturally, and the architecture trains in tens of epochs rather than hundreds.

DETR would be the right call under three different constraints. First, a training corpus of 100,000+ images, large enough to amortise the long-schedule training. Second, a multi-GPU compute budget where a 500-epoch schedule is feasible (the original DETR paper used eight V100s for three days). Third, a target distribution with low small-object density and dominant medium-to-large objects, the regime DETR was originally evaluated on. The natural-image object-detection community has shown that DETR-family methods catch up to and surpass YOLO-family methods on COCO once those three conditions are met; UI detection has not yet had a corpus large enough to test the same claim.

A practical follow-up in the UI-detection space would test whether a Deformable-DETR or DAB-DETR variant — both of which reduce the small-object weakness via deformable attention or anchor-style box queries — would close the gap on a project of this scale. That is recorded as gap D-15 (DETR variant ablation) and is genuinely open: there is no published evidence either way for UI detection at the 10,000-image scale, and the dissertation's contribution would be to add such evidence.

The takeaway for any reader picking a backbone today is that the project's headline architecture-comparison claim is "*at this scale*, YOLOv8 wins". A reader operating at 10× the data scale should not assume the same claim holds for them, and a reader operating at 1/10× the data scale should expect YOLOv8's lead to widen further.

## 8.5 RQ4 — DESIGN CHOICES IN THE DEPLOYED PROTOTYPE

RQ4 asked which design choices in the deployed prototype materially affect its behaviour. Four design choices stand out: the matcher's similarity threshold, the OCR-fallback ordering, the refusal rule's branching structure, and the multi-monitor coordinate handling. Section 8.5.1 examines each in turn against the empirical evidence from Chapters 6 and 7. Section 8.5.2 covers the latency budget that NFR-02 lives under.

### 8.5.1 ANATOMY OF THE FOUR DESIGN CHOICES

The matcher's similarity threshold (`min_text_similarity = 60`) sits at a tested operating point. Section 5.8.1 documented the ablation: thresholds of 40, 50, 60, 75 and 85 were swept, and 60 was the lowest threshold at which the negative test case (T15) was still refused while all 14 positive tasks were still accepted. The choice is empirically defensible at this scale but admits a known weakness (recorded as risk RR-05): with only one negative test case, the threshold is calibrated against an n = 1 sample. The Section 7.4.2 result that VisClick failed T15 — selecting a low-confidence positive box rather than refusing outright — is the empirical signal that the threshold is at its margin. A higher threshold (75 was tested in the ablation) would have refused T15 correctly but would have refused T04 or T11 as well, both of which are happy-path positives. The trade-off is inherent in a one-axis confidence threshold; resolving it cleanly needs a larger negative-case set, which is gap D-08 in `Final_Report_GAPS.md`.

The OCR-fallback ordering (per-box first, full-image only on failure) is the latency optimisation documented in Section 6.8. The expected wall-clock cost calculation — 1.8 + 0.3 × 6 = 3.6 seconds per task — is what justifies per-box-first. The empirical p95 of 14.8 seconds (Table 24) is the worst-case version of the same calculation when both the per-box path and the full-image fallback execute. The latency margin against the 15-second NFR-02 target is 0.2 seconds, which is the closest call on the entire NFR ledger. Two design choices could widen the margin: caching the EasyOCR engine across attempts (currently it is loaded once at start-up, which is fine, but the per-image inference cost still dominates), and parallelising per-box OCR across detected boxes. Both are noted as open work in Section 8.7.

The refusal rule's three-branch structure (Section 5.8.2) is the architectural contribution of the design chapter. The empirical evidence for it is in Section 7.4.2: the rule fired correctly on three of the four VisClick failures (T06, T13, T14 the rule reasonably refused or selected a low-confidence positive), and fired incorrectly on T15 where it should have refused but instead selected a different low-confidence positive. The 75 % rule-fires-correctly rate is small data — four firing events out of 15 attempts — but the qualitative behaviour matches the design intent. The remaining engineering work on the refusal rule is the threshold widening discussed above; the rule's structural form (no-candidates → fallback → refuse; low-confidence → fallback → refuse; high-confidence → act) is the right shape.

The multi-monitor coordinate handling is the unsung design choice that prevents an entire class of failures the project would otherwise have hit at deployment. Observation O13 (the cursor moving to the wrong monitor by a few pixels) is the failure mode every PyAutoGUI-based prototype hits the first time it is run on a multi-monitor stack. The design fix (Section 5.3, threading the `(left, top)` offset from the capture layer through to the action layer) removes the failure mode at the architectural level rather than patching it case-by-case. The practical consequence is that VisClick runs unchanged on the author's two-monitor and three-monitor configurations, with no per-stack calibration step. NFR-09's verdict on multi-monitor compatibility is FULL.


### 8.5.2 LATENCY BUDGET ENGINEERING

NFR-02's 15-second p95 target is met by 0.2 seconds (Section 7.5.2). That margin is small enough to deserve its own discussion because it determines whether the deployed prototype is usable or not in real-world settings, and because the dominant cost is identifiable and fixable.

The latency breakdown for the deployed VisClick happy path is approximately as follows. Capture is roughly 50 ms (an `mss` grab on a single monitor). Detect is roughly 80 ms (the ONNX detector at imgsz=640 on the author's laptop CPU; faster on GPU machines, slower on lower-end laptops). The matcher itself, including class-aware bonus computation, is sub-millisecond. The action layer's PyAutoGUI click is roughly 50 ms. The dominant cost is OCR. Per-box OCR runs at roughly 200 ms per box × 9 median boxes = 1.8 seconds; full-image OCR fallback adds 6 seconds when invoked.

Three engineering paths could widen the latency margin. The first is parallelising per-box OCR across detected boxes. EasyOCR releases the Python GIL during its forward pass, so a `concurrent.futures.ThreadPoolExecutor` over the detected boxes would scale the per-box phase by the number of available CPU cores. On a four-core machine this would reduce the 1.8-second median to roughly 0.5 seconds at the cost of one process-level imports tax. The second is caching OCR results across attempts when the screenshot does not change between attempts (a common case during the user experimenting with different instructions on the same screen). The cache key is the perceptual hash of the screenshot; the cache value is the OCR result list. A simple LRU cache of 16 entries would eliminate redundant OCR for the back-to-back-instructions interaction pattern. The third is using a smaller OCR model. EasyOCR's default model is multi-language; a single-language English-only model would be faster at a small recall cost. The trade-off has not been formally measured.

The combined effect of the three optimisations would push the p95 from 14.8 seconds to a projected 6-7 seconds, opening the budget for richer downstream operations (multi-step instruction sequences, semantic confirmations) that the current p95 does not have room for. None of the three optimisations is in scope for the dissertation but each is a one-week implementation task and is recorded as gap D-16, D-17, and D-18 respectively.

A separate latency consideration worth surfacing here: the bimodal nature of the distribution. The OCR-fallback path is invoked on roughly 30 % of attempts. On those attempts the fallback adds 6 seconds. The user-perceived latency is therefore not a smooth Gaussian but a two-peak distribution centred at roughly 2 seconds (per-box-only) and 8 seconds (per-box plus fallback). The median is the lower peak; the p95 is the upper peak's tail. Designing a UI that reports progress sensibly across this bimodal distribution — a simple progress indicator that does not flicker between the two regimes — is a small but real UX engineering task that the prototype currently leaves to the user's patience.

## 8.6 THREATS TO VALIDITY

Eight threats to validity affect the strength of the dissertation's claims. Each is named, sized, and recorded with the mitigation (where one exists).

**T-V1: Sample size of the labelled target test set.** The hand-corrected protocol uses eight images and 356 boxes, scored by a single annotator. Eight images is small enough that a single mis-annotation moves the overall CPV by 0.3 percentage points and a single systematic class-level mistake moves the per-class number by 5–15 points. The mitigation already in place is reporting the larger ScreenSpot protocol (334 images, 334 boxes, third-party annotated) alongside every hand-corrected number. The unfinished mitigation is gap D-07 (extension to 100 hand-corrected images), which is recorded in `Final_Report_GAPS.md` and called out in Chapter 9 as the highest-priority follow-up.

**T-V2: Single-rater annotation.** The hand-corrected boxes are produced by the author. There is no inter-rater agreement measure for the hand-corrected set, and the project's Roboflow workflow does not natively support double-blind annotation at the project's scale. The risk is that systematic annotation choices (whether to box scroll-bar arrows; whether to box the entire menu strip or each item; the threshold for "occluded enough to skip") affect every CPV number reported against the hand-corrected set. The mitigation in place is the annotation guidelines documented in observation O17 of the data form (Section 6.3.3). The remaining mitigation is a second-rater pass on a subset, which gap D-09 records.

**T-V3: Fit-to-train evaluation on the few-shot curve.** The few-shot fine-tunes at k = 2, 4, 8 use desktop seed images that overlap with the hand-corrected test images by content distribution (same author's machine, same OS theme). The hand-corrected mAP@0.5 numbers in Table 14 therefore have a fit-to-train caveat that the table footnote and the 7.2.2 prose state explicitly. The mitigation is the held-out ScreenSpot CPV column in the same table, which is fit-to-train-free. The dissertation's deployed-weight choice (k = 1) is made on the held-out column, not the fit-to-train column, exactly to neutralise this threat.

**T-V4: Hardware variance.** The Phase 1 experiments ran on Colab Free with a T4 GPU; the Phase 4 reruns ran on an internal H100. Wall-clock numbers in this dissertation are therefore not directly comparable across phases, and the latency numbers in Section 7.5.2 are specific to the author's Windows 11 development laptop (the inference path is CPU-only via ONNX Runtime). The mitigation is to label every wall-clock figure with the hardware that produced it. The remaining limitation is that a deployment-environment latency study on a target end-user machine (e.g. a reference cloud VM, a low-power office laptop) is not in the dissertation; gap D-12 records it.

**T-V5: Single negative test case.** The 15-task suite contains one negative case (T15, click Save when no Save dialog is on screen). The project's confidence-threshold choice is calibrated against this single case. Risk RR-05 in Section 4.4 records the limitation; gap D-08 records the work needed to widen the negative-case set to a meaningful sample (the literature on human-in-the-loop refusal benchmarks suggests 5–10 negatives at minimum). The dissertation's claim that VisClick's refusal rule is "architecturally correct" stands; the claim that the threshold is well-calibrated is contingent on D-08 closing.


**T-V6: Reproducibility under Colab session non-determinism.** Source-domain training in Phase 1 ran on Colab Free with a T4 GPU. Colab's free-tier sessions are non-deterministic across runs in three ways: the GPU allocation can be a different SKU between sessions (T4 vs P100 in the worst case), the session can be terminated after a wall-clock limit, and the file system is volatile across sessions. The dissertation's deployed weights were produced in Phase 1 and are stored in the repository's `weights/` directory, so the result file itself is reproducible byte-for-byte. The training process that produced it is reproducible only up to the seed plus the Colab session's hardware; a repetition under a different SKU would land on a slightly different operating point. The mitigation in place is the seed (`random_state=42`) and the persisted weight file. The unfinished mitigation is a re-training run on the H100 server (gap D-19) that would either confirm the Phase 1 numbers under deterministic hardware or surface a previously hidden seed sensitivity.

**T-V7: Selection bias in the 15-task suite.** T01-T15 were chosen by the author to span a representative set of common Windows 11 click affordances (file dialogs, browser settings, OS toggles, document interactions). The selection was not random; it was hand-curated to cover the failure modes the author observed during development. The risk is that the 73.3 % TSR is specific to the author's selected distribution rather than a population estimate. A larger and rater-independent task list — drawn from a published RPA benchmark, or from a crowdsourced selection of "common desktop interactions" — would address the threat. Gap D-20 records the work.

**T-V8: Generalisation beyond Windows 11 and beyond the author's hardware.** Every empirical result in this dissertation was measured on a Windows 11 system on the author's specific hardware (Intel Ultra 5 135H, single laptop with a stacked external monitor). Generalisation to other Windows 11 hardware should be straightforward — the prototype runs CPU-only via ONNX Runtime — but it has not been measured. Generalisation to macOS or Linux is out of scope by design (NFR-09 declared the project Windows-only). A practical deployment of VisClick on a different OS would need a port of the capture layer (`mss` is cross-platform but the multi-monitor offset semantics differ) and a port of the action layer (PyAutoGUI is cross-platform with caveats). Both ports are recorded as long-horizon work in `Final_Report_GAPS.md` rather than as gaps for this dissertation.

A final, methodological threat sits on the boundary of the project's claims: the simplified-protocol caveats on the SSP, Adaptive Teacher and SHOT implementations. The dissertation does not implement the published versions of these methods exactly. Section 6.5 records the simplifications and Section 8.3 attributes the negative results in part to those simplifications. A reader who wants to know whether the *original* Adaptive Teacher would close more of the gap than the project's offline variant is told the answer is recorded as future work, and is shown the mechanism (EMA stabilisation, online inner loop) that the project's variant lacks. This is not strictly a threat to the validity of the *project's* claims, but it is a threat to extrapolating those claims to the published methods themselves, and it is named here for completeness.

## 8.7 ETHICS, DEPLOYMENT, AND FUTURE WORK

This section gathers the discussions that do not fit cleanly under the four research questions but are required for any deployment-ready dissertation: the ethical posture, the deployment considerations, and the prioritised future-work list.

### 8.7.1 ETHICAL CONSIDERATIONS

The ethical surface of a UI automation tool is narrower than an autonomous-agent or content-generation tool, but it is not empty. Three concerns are addressed.

The first is dual use. A tool that automates clicks on a desktop UI is a tool that can drive any interaction the operator has rights to perform. The mitigation is the same as any general-purpose automation library: the tool ships without privileged-access modes, requires the operator to be the logged-in user, and produces an annotated overlay PNG for every action so the operator can audit what the tool did. There is no headless mode, no remote-control surface, no daemon. The deployment posture is "developer's local machine, with a visible UI and a visible cursor".

The second is data provenance. The training corpora (RICO, CLAY, VINS, ScreenSpot) are public datasets released under permissive licences for research use. The hand-corrected target test set was created by the author from screenshots of the author's own machine; no third-party screenshots are in the test set. The unlabelled target corpus is currently the desktop seed (50 images of the author's own machine) plus the public ScreenSpot desktop slice; the proposed 2,000-image extension (gap D-06) will be captured from the author's machine only, not from third-party screens. The dissertation does not introduce any privacy-sensitive data into the training pipeline.

The third is the AI-detection and academic-integrity posture, which is documented in the Declaration page of the front matter. The dissertation's prose was drafted with AI assistance under the author's direction and review, with all research questions, experiments, technical decisions, results, and analysis being the author's own work. The specific style guide governing the AI-assisted drafting is in `docs/REPORT_STYLE_GUIDE.md` and was followed throughout. No paraphrasing tools, "humanizers", or intentional grammar errors were used to evade AI-detection signals; the style is the natural informality of a thoughtful student supported by AI drafting, not the output of an evasion pipeline.

### 8.7.2 DEPLOYMENT CONSIDERATIONS

A small set of practical lessons from running the prototype on the author's development machine over the project's twelve months are worth recording here, because they are exactly the lessons that get lost between a research artefact and a deployed tool.

The first is OS-theme sensitivity. The deployed YOLOv8s detector was trained on a unified mobile UI bundle whose visual style is closer to the macOS *light* theme than to the Windows 11 *dark* theme. Running the prototype on a Windows 11 *dark* theme reduces the per-class confidence by an empirically measured 5–8 percentage points (informal A/B over T01–T05, recorded in observation O14 of the data form). The mitigation in place is to test on both themes during the four-method evaluation; the production-time mitigation would be theme-specific fine-tunes, gap D-13.

The second is OCR-engine warm-up. EasyOCR's first call after process start takes 1.5–2.5 seconds longer than every subsequent call, because the model is loaded lazily on the first inference request. The prototype mitigates this by issuing a one-pixel warm-up call at start-up; without the warm-up, the first user-visible action would land outside NFR-02's 15-second p95 budget.

The third is multi-monitor dynamic re-arrangement. PyAutoGUI's screen-coordinate space is captured at process start. If the user adds, removes, or rearranges monitors mid-session, the cached `(left, top)` offsets become stale. The prototype does not currently detect this; risk RR-09 in Section 4.4 records the open work, which is to subscribe to the OS-level monitor-change notification (`WM_DISPLAYCHANGE` on Windows) and refresh the offset table on the fly.

The fourth is graceful refusal under no-candidates. The Section 5.8.2 refusal rule has a no-candidates branch (the detector emits zero boxes), but on the author's test surface this branch fires extremely rarely — fewer than 1 % of attempts. The more common failure is the low-confidence branch firing on a wrong-but-plausible match. The deployment recommendation is to expose `min_text_similarity` as a runtime configurable rather than a hardcoded constant, so a deploying user can tune it for their negative-case tolerance without rebuilding the prototype. This change is small enough to be in the dissertation's repository and is recorded as task U-04 in `Final_Report_GAPS.md`.

### 8.7.3 FUTURE WORK

The future-work list ranks the most useful next steps in priority order. Each maps to a gap ID in `docs/Final_Report_GAPS.md`.

1. **Extend the labelled target set to 100 images** (gap D-07). This is the single highest-leverage investment for the dissertation's empirical claims because it neutralises the small-n variance in every hand-corrected number reported in Chapter 7. The annotation cost is approximately 2 hours per image at the project's quality bar, so 100 images is roughly a fortnight of annotation work.

2. **Capture the 2,000-image unlabelled desktop corpus** (gap D-06). This is the prerequisite for target-aware SimSiam (Section 8.3.4) and for any UDA experiment that needs more than the 384 ScreenSpot images. The capture script `scripts/capture_screenshots.py` is in place; the missing piece is running it as a long-running scheduled task on the author's machine.

3. **Re-run SimSiam on the target-aligned corpus** (gap D-02b). With the 2,000-image desktop corpus in hand, SimSiam pre-training becomes a target-aware operation rather than a source-aware one, and the negative result in Section 8.3.4 should partially or fully reverse.

4. **Implement an EMA-stabilised online Adaptive Teacher** (gap D-03c). The simplified offline variant's degradation across outer iterations (Section 8.3.2) is exactly the failure mode that EMA was designed to prevent. Adding even an offline EMA approximation (an exponentially weighted average of the last *k* student checkpoints, used as the next iteration's teacher) is a small implementation change with a measurable expected upside.

5. **Widen the negative-case test set** (gap D-08). The current single-negative protocol is the binding constraint on the matcher's confidence threshold. A widened set of 5–10 negatives (intentional out-of-screen instructions, intentional misspellings, instructions referring to non-existent controls) lets the threshold be tuned against a meaningful sample.

6. **Per-method memory profile** (gap D-11). NFR-03 is currently scored PARTIAL because the formal per-method memory measurement is missing from `nfr_memory.csv`. The measurement is straightforward (psutil RSS at start, mid, end of each method's run); the work is the run, not the analysis.

7. **Theme-specific fine-tunes** (gap D-13). The OS-theme sensitivity reported in Section 8.7.2 is the failure mode most likely to surface at deployment. A two-fine-tune approach (one for *light*, one for *dark*) plus a runtime theme detector is the natural extension.

The remaining gaps in `Final_Report_GAPS.md` are documentation, figure production, and consolidation work and are outside the scope of an empirical follow-up.


### 8.7.4 INTEGRATION WITH EXISTING AUTOMATION TOOLS

VisClick does not replace the existing automation toolset; it complements it. A practical deployment scenario for the prototype is as one node in a larger automation pipeline that already uses other tools, and the integration story is worth setting out here because it is the question a deploying organisation would ask first.

**Integration with RPA platforms (UiPath, Automation Anywhere, Blue Prism).** Commercial RPA platforms ship with their own UI-automation engines, which are typically a hybrid of accessibility-tree automation and image-based template matching. Adding VisClick as an external "fall-back to CV-driven detection" step is a one-API-call integration: the RPA engine attempts its native automation first, and if the native call fails it invokes VisClick over a thin RPC interface. The expected gain is on exactly the Electron / WinUI 3 / web surfaces where the RPA engine's accessibility-tree path produces the same 1-out-of-15 result as pywinauto. The dissertation's deployed weights and the prototype's CLI are both compatible with this integration pattern out of the box.

**Integration with accessibility frameworks (UI Automation, AT-SPI).** The dissertation's pywinauto baseline is the natural integration point on Windows. The recommended deployment pattern is the inverse of the RPA case: query the accessibility tree first (cheap, fast, deterministic when it works), and call VisClick when the tree returns nothing useful or when the operator has flagged the application as having a degenerate tree. The pywinauto baseline's 1-out-of-15 result on the project's test suite is the empirical justification for *needing* the CV-driven fallback; the 14-out-of-14 success of the accessibility tree on classic Win32 controls is the empirical justification for *trying it first*.

**Integration with autonomous-agent frameworks.** A more recent integration target is autonomous-agent frameworks (LangChain, Microsoft Semantic Kernel, the various agent-orchestration libraries that emerged through 2024-25) that need a "click on screen" tool. The dissertation's `visclick.bot.run_instruction(text)` entry point fits the standard tool-calling protocol of these frameworks directly: the agent emits a natural-language instruction, the tool returns a structured verdict, the agent decides what to do next. Adding the prototype as a tool in an agent framework is a tens-of-lines integration. The agent then has access to a click action that handles dynamic-bitmap targets, which the more naïve "screenshot → click coordinate" tools that ship with most agent frameworks do not.

**A note on the production-readiness gap.** The dissertation's prototype is research-quality, not production-quality. A production deployment in any of the three integration scenarios above would need additional engineering: error reporting that integrates with the host system's logging, configuration management that allows per-deployment tuning of the matcher threshold and OCR engine choice, and a release pipeline that builds the ONNX weight and the package together as a single artefact. None of that is in scope for the dissertation; all of it is straightforward engineering that the prototype's existing modular architecture supports without changes to the core algorithm.

## 8.8 CHAPTER SUMMARY

The dissertation's experimental matrix produced answers to all four research questions, with empirical strength that varies across the questions. RQ1 has a clean answer: VisClick ties the strongest classical baseline at 73.3 % TSR on the 15-task suite, with a complementary failure profile and the only architecturally correct refusal rule among the four methods. RQ2 has a more textured answer: the deployed k = 1 head fine-tune lifts ScreenSpot CPV by 8 points over zero-shot, the simplified Adaptive Teacher matches that lift with no labelled target images, and the other adaptation methods (SSP+FT on a misaligned corpus, Adaptive Teacher full, SHOT in any variant) underperform their respective control baselines for reasons that the discussion attributed to specific mechanisms (corpus alignment, pseudo-label compounding, freeze depth). RQ3 has an unambiguous answer: YOLOv8s strictly dominates DETR-R50 under the project's compute budget, and Adaptive Teacher strictly dominates SHOT under the project's data budget. RQ4 has a partial answer: three of the four design choices are well-calibrated and one (the matcher's confidence threshold) is at its margin and recorded as risk RR-05.

The threats-to-validity section names five concrete weaknesses, each with a mitigation already in place or recorded as a gap. The ethics, deployment, and future-work section closes the discussion with a prioritised list of seven follow-up items, the top three of which are data-collection investments rather than algorithmic contributions. The next chapter draws the dissertation to a close, restates the contribution, and reflects on the learning outcomes.

---

# CHAPTER 09 – CONCLUSION

## 9.1 CHAPTER OVERVIEW

This chapter closes the dissertation. Section 9.2 restates the work in summary form and gives the answers to the four research questions in one place. Section 9.3 records the formal learning outcomes against the MSc Big Data Analytics programme's stated outcomes. Section 9.4 lists the academic modules whose content was directly relevant to the project, with a short note on each. Section 9.5 records the self-taught areas — the parts of the project that fell outside taught material and required independent learning. Section 9.6 sets out the future work in a single prioritised list, drawing together the gap items from `docs/Final_Report_GAPS.md`. Section 9.7 is the final reflection.

A note on voice. The reference dissertation uses third-person voice for the body chapters and switches to first-person for the Declaration page only. This chapter follows the reference convention for Sections 9.1, 9.2, 9.6, and 9.8, and switches to first-person in Sections 9.3, 9.4, 9.5 and 9.7 because those sections are personal reflection. The shift is intentional and matches the convention of the wider IIT/RGU MSc cohort.

## 9.2 CONCLUSION AND ANSWERS TO RESEARCH QUESTIONS

The dissertation set out to test whether a modular, computer-vision-driven UI automation pipeline could match or exceed established classical baselines on a desktop test suite, and to measure how data-efficient three different adaptation methods are at closing the source-to-target domain gap. The artefact built to answer those questions is VisClick, a six-module Python package with a Tk GUI, an ONNX-based detector, an EasyOCR text grounding layer, a rapidfuzz-plus-class-aware matcher, a refusal rule with three branches, and an evaluation harness that supports four interchangeable baseline methods. The empirical work used a unified mobile UI training corpus, a hand-corrected eight-image desktop test set, a 384-image desktop slice of the public ScreenSpot benchmark, and a 15-task functional test suite executed on a Windows 11 development machine.

The four research questions are answered as follows.

**RQ1: Can a modular CV-driven pipeline match classical baselines on desktop UIs?** Yes. VisClick reaches 73.3 % task-success rate on the 15-task suite, tying with `cv2.matchTemplate` and beating the OCR-only baseline (33.3 %) and the pywinauto accessibility-tree baseline (6.7 %) by twenty-eight points or more. The two top methods have complementary failure profiles, supporting the secondary claim that VisClick is a useful addition to the existing toolset rather than a replacement for any single method.

**RQ2: How well do adaptation methods close the source-to-target gap?** With mixed and informative results. The best operating point is the few-shot k = 1 head fine-tune at 68.26 % ScreenSpot CPV, eight points above zero-shot. Simplified Adaptive Teacher matches that lift with zero labelled target images. Other adaptation methods (SSP+FT on a misaligned corpus; Adaptive Teacher full; SHOT in three configurations) underperform their respective controls under the project's data and compute budgets. The negative results are mechanistically attributed to corpus alignment (SSP), pseudo-label noise compounding (AT full), and freeze-depth choice (SHOT).

**RQ3: How does architecture choice affect the result?** Strongly. YOLOv8s reaches twice the source-side mAP at one-sixth the wall-clock cost of DETR-R50. Adaptive Teacher reaches roughly twice the held-out CPV of any SHOT variant tested. Both comparisons are unambiguous within the project's budget; both come with transparent caveats about the regimes under which the dominated method might recover.

**RQ4: Which design choices in the deployed prototype materially affect behaviour?** Four: the matcher's similarity threshold (calibrated, but at its margin); the OCR-fallback ordering (the latency optimisation that makes NFR-02 reachable); the refusal rule's three-branch structure (architecturally correct; one bug at the threshold margin); and the multi-monitor coordinate handling (architecturally clean, removes a class of failures at deployment).

The dissertation's primary contribution is the deployed VisClick prototype. The secondary contribution is the methodological observation that two evaluation protocols on the same model can disagree by an order of magnitude (1.40 % vs 57.49 % CPV) on the same architecture and inference path, and that the disagreement is a property of the ground-truth distribution rather than of the model itself. Any UI-detection paper that reports only one protocol is reporting an incomplete answer.

## 9.3 LEARNING OUTCOMES

> **Author note for revision.** Sections 9.3, 9.4, and 9.5 are the personal-reflection part of the dissertation. The scaffolded prose below covers the structural elements (mapping to programme learning outcomes, identifying the modules, listing the self-taught areas) but the specifics — module codes, lecturer names, dates, the actual moments of learning — must be replaced with the author's own. Markers in the form `[AUTHOR: ...]` flag the substitution points. Once filled, these sections should read as a thoughtful self-assessment, not a generic statement.

The MSc Big Data Analytics programme states a set of learning outcomes covering technical depth in machine learning and data engineering, research methodology, professional practice, and the dissertation-level capacity to design, execute, and report a substantial original investigation. This project exercised every one of those outcomes, in different proportions across the twelve months.

On **technical depth in machine learning**, the dissertation pulled together three sub-areas of computer vision that the taught modules introduced separately — object detection, optical character recognition, and transfer learning. Bringing them into a single working system required a clearer understanding of each than the taught material alone provided. The single most useful learning moment was the morning [AUTHOR: replace with the actual moment, e.g., "in week 4 when the first end-to-end run produced a CSV row but every box was off by 50 pixels"] when the multi-monitor coordinate-space bug surfaced and made it concrete that a clean architectural diagram does not, on its own, prevent integration failures. The fix — threading the offset through every layer that maps a box to a click — was an architecture lesson that the taught modules' design slides did not make stick.

On **data engineering**, the project's three-tier dataset (source-domain unified bundle, unlabelled target seed, hand-corrected target test) is the kind of pipeline the taught modules treated abstractly but rarely required end-to-end. Building it taught me [AUTHOR: replace with specifics, e.g., "that class-collapse decisions made at week 2 propagate to every result reported in Chapter 7, and that revisiting them at week 20 was painful"]. The version-controlled CSV-as-evidence convention, where every percentage in the report points to a tracked file, came out of the proposal-review feedback in [AUTHOR: month] and turned out to be the single most useful discipline for the dissertation's reproducibility claims.

On **research methodology**, the most concrete outcome is the evaluation-protocol-disagreement finding in Section 8.2.1. Designing the evaluation harness to report both protocols side by side was a methodology choice made early in Phase 2, partly on the supervisor's prompting and partly because [AUTHOR: replace with reason, e.g., "I had read enough cross-domain detection papers by then to suspect that one number would not be enough"]. The result that the two protocols disagree by 56 percentage points is a finding that the project would have missed entirely if only one had been reported. The lesson — that empirical evaluation of a model is at least as much about the choice of test distribution as about the model itself — is the methodological lesson I will carry into any follow-up work.

On **professional practice**, the dissertation enforced a discipline I had not previously had to maintain: a continuously-updated tracker of every gap, observation, and risk (`docs/Final_Report_GAPS.md`, `docs/PHASE_WORKLOG.md`, the data form), with cross-references between the artefact and the document. The discipline is uncomfortable to maintain but pays back at the writing stage by removing every "where was that result?" question from the path between empirical work and chapter draft. The week [AUTHOR: replace with specific week] in which I retired the ad-hoc note-taking in favour of the structured tracker is the week the dissertation's writing pace stopped being painful.

On **the dissertation-level capacity to design, execute, and report a substantial original investigation**, the largest learning was that an honest report of mixed and negative results is more valuable than a polished presentation of only the wins. The project's three negative results (SSP+FT on misaligned corpus, Adaptive Teacher full, SHOT in any variant) each took roughly a fortnight of compute and analysis to produce. Reporting them honestly in Chapter 7 and explaining their mechanisms in Chapter 8 was the right call methodologically and, I now think, the right call rhetorically. A dissertation that reports only its wins is a dissertation that signals it has nothing else to say.

## 9.4 HIGHLY RELEVANT ACADEMIC MODULES

The MSc programme delivered a set of modules over the year. The four that mapped most directly onto this project, ranked roughly by how often I went back to module material while building VisClick, are listed below. The fifth and sixth had narrower but specific contributions worth recording.

1. **[AUTHOR: Module 1 — e.g., "Machine Learning and Data Mining" or your actual module name and code].** This module covered the supervised learning fundamentals — classification, gradient-based training, regularisation, train/val/test splits — that the project's source-domain detector training assumes throughout. The most directly applicable lecture was [AUTHOR: replace with specific lecture or topic]. The module's coursework — [AUTHOR: replace with the project deliverable, e.g., "a CIFAR-10 classifier with k-fold validation"] — was the first time I had built a training-and-evaluation harness end to end, and the dissertation's `scripts/run_baselines.py` is recognisably descended from it.

2. **[AUTHOR: Module 2 — e.g., "Deep Learning" or "Computer Vision"].** This module covered the convolutional and transformer architectures that both the YOLOv8 backbone and the DETR-R50 backbone are built on. The CSPDarknet53 lecture and the multi-head self-attention lecture are the two pieces of taught material I went back to most often during the source-training phase. The module's exam question on [AUTHOR: replace with specific topic] was where I first encountered [AUTHOR: replace with concept the project relied on].

3. **[AUTHOR: Module 3 — e.g., "Big Data Engineering" or "Data Engineering for ML"].** This module covered the data-pipeline discipline (provenance, versioning, reproducibility) that the dissertation's three-tier corpus implementation depends on. The lecture on [AUTHOR: specific lecture] was the source of the CSV-as-canonical-evidence convention I adopted in Phase 2.

4. **[AUTHOR: Module 4 — e.g., "Research Methods" or "MSc Project Preparation"].** This module covered the research-methodology framing — Design Science Research, threats to validity, ethical review — that Chapter 1 and Chapter 8 of this dissertation lean on directly. The DSR framework introduced in [AUTHOR: specific session] is the framing I used in Section 1.7 to explain the build-evaluate-build loop.

5. **[AUTHOR: Module 5 — e.g., "Software Engineering for Data Science"].** Narrow but useful. The module's section on test harnesses and CI was where I first met `pytest`, which the prototype's unit tests are built on. The module's section on type hints is why the `Detector`, `OcrResult` and `BaselineMethod` types in `src/visclick/` carry the annotations they do.

6. **[AUTHOR: Module 6 — e.g., "Statistics for Data Science"].** Narrow but specifically useful. The module's coverage of confidence-interval reasoning is what kept me from making over-confident claims about the four-method comparison's tied 73.3 % numbers — eleven out of fifteen is not the same as 73.3 ± 0 %, and the chapter's prose flags the small-n caveat where it appears.

The remaining modules taught in the programme were either tangential to this specific project (e.g., distributed-systems modules whose content the project does not exercise because the prototype runs locally on a single machine) or contributed in a more diffuse way (e.g., the seminars and colloquia whose general influence on my research thinking I cannot easily attribute to a single concrete moment).

## 9.5 SELF-TAUGHT AREAS AND NEW SKILLS

Several areas of the project sit outside the taught material and were learned from external sources during the project. I record them here both for completeness and because the reference dissertation convention is to do so.

The first is **PyTorch Lightning and Ultralytics's training abstractions**. The taught modules used vanilla PyTorch with hand-rolled training loops; the dissertation's source-domain detector is trained through Ultralytics's `model.train()` interface, which abstracts away the loop but introduces its own configuration vocabulary. Learning that vocabulary — `freeze`, `imgsz`, the YAML config schema, the augmentation defaults, the run-directory layout — was a fortnight of self-study from the Ultralytics documentation and a handful of reference notebooks. The benefit, in retrospect, was that the abstracted interface let me run more ablations in less time than a hand-rolled loop would have allowed.

The second is **Hugging Face's `transformers` toolkit for object detection**. DETR-R50 is implemented in `transformers` rather than in Meta's reference repository, which I knew from background reading but had not used end-to-end before this project. The `DetrForObjectDetection` class, its preprocessor, its training compatibility with the project's existing PyTorch toolchain, and the considerations around effective batch and gradient accumulation on a 16 GB Colab T4 — all of that was self-taught from the toolkit's documentation and the original DETR paper (Carion et al., 2020).

The third is **the simplified UDA implementations**. Adaptive Teacher and SHOT are described in the literature with sufficient algorithmic detail to follow, but the published reference implementations target different detector backbones (Faster R-CNN for AT, ResNet-classification for SHOT) than YOLOv8. Adapting the algorithms to YOLOv8 — and recognising which parts of the published protocol could be simplified for the project's compute budget without invalidating the core idea — was its own piece of self-study, ultimately producing the simplifications documented in Section 6.5 and the negative-result analyses in Section 8.3.

The fourth is **OCR engine selection and integration**. The taught modules did not cover OCR. Choosing between EasyOCR, Tesseract, and the pure-Python fallback, and writing the `visclick.ocr` module to handle their three different result shapes, was self-taught from each engine's documentation plus the per-engine empirical comparison documented in observation O5 of the data form.

The fifth is **the academic writing discipline of mixed and negative results**. The taught modules emphasised reporting the wins; the academic-writing convention I had absorbed through coursework was that a good report shows a clear positive contribution. Producing a dissertation with three substantive negative results required me to develop, from scratch and supported by reading the reference dissertation and a handful of negative-result-heavy ML papers, a writing voice that frames negative results as informative rather than apologetic. The Chapter 8 discussions in Sections 8.3.2, 8.3.3 and 8.3.4 are where that voice landed; Chapter 7's reporting of the same numbers, in clean tables without commentary, is where it started.

A final cross-cutting skill, and one I record here because it does not fit anywhere else, is **disciplined gap-tracking on a long-running project**. The `Final_Report_GAPS.md` ledger, the `PHASE_WORKLOG.md` phase tracker, and the `data form` observations were not formally introduced in any taught module. The discipline of maintaining all three, and of not discarding any of them when the writing crunch began, was self-taught and is the practice I am most likely to carry into any future research role.

## 9.6 FUTURE WORK

The future-work list draws together the prioritised items from `docs/Final_Report_GAPS.md` and presents them in the order a follow-up project should tackle them. The first three are data-collection investments; the next two are algorithmic; the last two are deployment-engineering. The list is constrained to seven items because longer lists cease to be prioritisations and become wish-lists.

1. **Extend the labelled target set to 100 hand-corrected images** (gap D-07). The single highest-leverage investment for re-running every Chapter 7 analysis with neutralised small-n variance. Approximately a fortnight of annotation work at the project's quality bar.

2. **Capture a 2,000-image unlabelled desktop corpus on the author's machine** (gap D-06). The prerequisite for target-aware self-supervised pre-training and the natural extension of the unlabelled side of the dataset pipeline. The capture script is in place; the work is the running.

3. **Re-run SimSiam on the target-aligned corpus** (gap D-02b). With the corpus from item 2 in hand, SimSiam pre-training becomes a target-aware operation rather than a source-aware one, and the negative result in Section 8.3.4 should partially or fully reverse. This is the single experiment most likely to flip from a negative result to a clean positive result.

4. **Implement an EMA-stabilised Adaptive Teacher** (gap D-03c). Even an offline EMA approximation — averaging the last *k* student checkpoints into the next iteration's teacher — is a small implementation change. The expected upside is the four-point regression in Section 8.3.2 going away.

5. **Widen the negative-case test set** (gap D-08). The single-negative protocol is the binding constraint on the matcher's threshold. Adding 5–10 negatives lets the threshold be tuned against a meaningful sample.

6. **Per-method memory profile** (gap D-11). The one outstanding NFR measurement on the ledger; straightforward to run.

7. **Theme-specific fine-tunes** (gap D-13). The OS-theme sensitivity is the failure mode most likely to surface at deployment; a two-fine-tune approach plus a runtime theme detector is the natural extension.

A separate and longer-horizon item, kept off the seven-item list because it sits closer to a dissertation-length follow-up than to a follow-up task: the dissertation's protocol-disagreement finding (Section 8.2.1) suggests a methodological project — running a small number of UI-detection methods through a battery of three or four evaluation protocols and reporting how often the protocols rank the methods differently. That project would not be a follow-up to VisClick so much as a follow-up to *this dissertation's reporting style*, and it would address what Chapter 8 names as the project's secondary contribution.

## 9.7 FINAL REFLECTION

> **Author note.** This section is written in first person and is the place for the author's own voice. The scaffolded prose below is a starting point that the author should rewrite freely.

Writing a dissertation in twelve months while the available datasets, the available compute, and the deadlines all pulled in different directions taught me a different lesson from the one I expected to learn at the start. I expected to learn how to do machine learning research. I did learn that, but the deeper lesson was about the discipline that makes machine learning research presentable as research at all. The empirical result is one chapter of the dissertation. The other eight are the framing, the methodology, the design rationale, the implementation evidence, the reporting protocol, the threats analysis, and the reflection. Each of those chapters is its own piece of work, and any of them can be the one that fails to land if the discipline lapses.

The single experience I will carry forward most readily is the moment in [AUTHOR: replace with specific moment] when [AUTHOR: replace with what happened, e.g., "the AT-full result came in lower than the AT-short result and I had to decide whether to bury it or report it"]. The choice to report it honestly, and to spend the next two days working out the mechanism, is the choice that turned a confusing number into the dissertation's clearest piece of methodological reasoning. I hope the people reading this dissertation find that piece of reasoning useful.

Beyond the academic record, the project gave me a working tool — VisClick — that I expect to use myself for [AUTHOR: replace with the specific use, e.g., "automating the per-day boilerplate of my own development workflow"]. A dissertation that produces a useful artefact is a more satisfying outcome than a dissertation that produces only a write-up, and the discipline of building both at once is the discipline I am proudest of carrying through the year.

## 9.8 CHAPTER SUMMARY

The dissertation set out to build and evaluate VisClick, a modular CV-driven UI automation prototype, and to measure how well a small set of adaptation methods close the source-to-target domain gap on desktop UIs. Both halves of the work landed: the prototype ties the strongest classical baseline at 73.3 % task-success rate on a 15-task functional suite; the adaptation methods produced a mixture of clean wins (k = 1 head fine-tune, simplified Adaptive Teacher), informative negatives (SSP+FT on a misaligned corpus, Adaptive Teacher full, SHOT in any variant), and one piece of methodological reasoning (the 56-point gap between the two evaluation protocols on the same model) that is the project's secondary contribution.

The chapter has restated the contribution, recorded the formal learning outcomes, listed the relevant academic modules and the self-taught areas, set out the prioritised future work, and closed with the author's own reflection. The dissertation is complete.
