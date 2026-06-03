# VISCLICK – FINAL REPORT (V2, REFERENCE-STYLE DRAFT)

> **How to use this file.** This file restyles the existing `Final_Report.md` to match the convention used by the 2026 MSc Big Data Analytics cohort at IIT/RGU (see `gui_temp/2425489.pdf`). The structural changes from v1 are: ALL CAPS chapter and section headings, sequential figure and table numbering across the whole document (no chapter prefix), Harvard "Cite Them Right" citations in place of IEEE numeric, and slightly tighter declarative paragraphs. Content is preserved from v1 wherever practical. Front-matter (title page, consent, declaration, SPER) is intentionally omitted — the author will paste those separately. Figure placeholders use the pattern `[FIGURE N: title. Source: path. Caption: …]` so they can be replaced with the final images at submission time.
>
> **Reference budget.** Target ~30-40 references for the final list (the reference report has ~25). Citations are added sparingly: one anchor reference per claim, no stacking, no placeholder/stub entries. Most consolidation happens in Chapter 2.
>
> **Chapter 7 (Testing) is paused.** When the v2 draft reaches Chapter 6, work stops and waits for the user's notebook results (D-01 DETR, D-05 few-shot curve, YOLOv8 source, ScreenSpot CPV, prototype TSR) before Chapter 7 is written.

---

# CHAPTER 01 – INTRODUCTION

## 1.1 CHAPTER OVERVIEW

This chapter sets out what the project is about. It starts with the background and the problem, then states the aim, the four research questions, the research gap and the research objectives. The operational objectives section breaks the work into the four phases by which it was actually executed. The chapter ends with the scope statement — both what is in and what was deliberately left out — and a short summary.

## 1.2 PROJECT BACKGROUND

Graphical user interfaces are how most people interact with software. Whether you are filing a tax return on a web form, editing code in VS Code, processing an image in GIMP, or just renaming a file in File Explorer, the underlying mechanics are the same. A small set of clicks and keystrokes, directed at coloured rectangles on a screen. Automating that has been an active area of work for decades. The motivations range from the mundane (repetitive data entry, regression testing of an application's controls, RPA in back-office settings) to the more ambitious. Accessibility tools that let users with motor impairment drive an application by voice. Autonomous agents that complete multi-step tasks on a user's behalf.

The available tooling falls into two camps. The older camp is image-based automation. SikuliX lets a user record a small bitmap of a button and asks the OS to find that bitmap on screen using OpenCV template matching (SikuliX, 2024). PyAutoGUI extends the same idea by exposing a Python interface to mouse and keyboard, but at heart it is still working in pixel coordinates (Sweigart, 2024). Tools of this kind are simple to use, but brittle. The bitmap of a button is not the button. It is a photograph of the button, taken on one machine, under one theme, at one DPI, on one OS build. Change any of those and the photograph stops matching. AskUI's review puts this politely as "image recognition first" (AskUI, 2024); in practice anyone who has tried to deploy a SikuliX script across a fleet has seen the failure mode at scale.

The second camp is accessibility-tree automation. Classic Windows applications expose a tree of named controls through the UI Automation framework, and Python libraries such as `pywinauto` walk that tree to find a *Save* button by its semantic name rather than its appearance (pywinauto Contributors, 2024). When it works, it is fast and stable. But it has stopped working reliably on a sizeable chunk of the modern Windows application mix. Electron apps (VS Code, Slack, Discord, Teams) expose only a degenerate tree because the renderer is a Chromium browser. Modern Windows 11 apps that use WinUI 3 or XAML islands often expose their controls under localised internal names rather than the visible labels. Web pages inside any browser are served through ARIA, which is a separate convention again. The empirical consequence, shown in Chapter 7, is that `pywinauto` can still drive classic Windows applications, but it fails on the modern WinUI 3 surface that ships with Windows 11 by default.

Sitting outside both camps is a newer strand of work. It uses computer vision and machine learning to detect UI elements directly from a screenshot, without any privileged access to the application's internal tree. Object-detection models such as YOLOv8 (Ultralytics, 2024) and DETR (Carion et al., 2020) are trained on annotated images of UIs and learn to predict bounding boxes labelled with classes such as `button`, `text`, `icon`, and so on. Mobile UIs are well resourced in this respect, thanks to RICO (Deka et al., 2017) and its denoised successor CLAY (Li et al., 2022a), which between them provide tens of thousands of labelled mobile screens. Recent work on YOLOv5-MGC reports mean average precision in the high 80s and low 90s on mobile UIs (Cheng et al., 2022).

Desktops are a different story. Desktop UIs differ from mobile UIs along several axes at once. They are landscape, not portrait. They are multi-window, not single-window. They contain dense toolbars and ribbon menus that produce what Chen et al. (2020) call a "packed scene", where elements sit close enough together that a standard detector struggles to put a clean bounding box around each one. They draw on decades of stylistic variance — Win32, WPF, Material Design, custom themes, dark mode, high-contrast accessibility skins — that has no real parallel in the more harmonised design languages of Android and iOS. And critically, there is no RICO-equivalent for desktops. The most recent attempts to build one (Wang et al., 2025; Patel et al., 2025) are themselves dated 2024 and 2025, which tells you how new the recognition of this gap is. Even those are an order of magnitude smaller than RICO.

What this means in practice is that a detector trained to high accuracy on mobile UIs typically does not, on its own, do well on desktop screenshots. There is a domain shift between the two. Quantifying that shift, and finding data-efficient ways to close it, is the problem this project takes on.

[FIGURE 1: Examples of the mobile-to-desktop shift.
Source: `reports/figures/ch1_domain_shift_examples.png` (to be produced; suggested layout is a three-panel composite stitching a mobile portrait screen from CLAY, a classic Win32 desktop screen from Windows File Explorer, and a modern Win11 WinUI 3 Save-As dialog).
Caption: Three axes of the mobile-to-desktop shift. Left, a mobile portrait UI from CLAY. Centre, a classic landscape desktop with a packed toolbar. Right, a modern Win11 WinUI 3 dialog with flat, theme-dependent controls.]

## 1.3 PROBLEM STATEMENT

The practical problem can be stated in one sentence. A practitioner who wants to build a vision-based UI automation tool for the modern Windows desktop has no off-the-shelf option today that is accurate, lightweight enough to run on a typical workstation, and tolerant of the variability that real desktop UIs show in the wild — all at once.

The classical image-based tools (SikuliX, PyAutoGUI) are lightweight, but not tolerant of variability. Their bitmap matching collapses the moment the theme, DPI or font shifts. The accessibility-tree tools (`pywinauto`) are tolerant of theme and DPI by construction, but not accurate on the modern Windows application mix. The empirical work in Chapter 7 shows `pywinauto` succeeding on only one out of fifteen task instances on a Windows 11 workload, and even that one success is a negative case where the right outcome is for the bot to do nothing. At the other extreme, heavyweight large vision–language models such as SeeClick (Cheng et al., 2024) are accurate and tolerant of variability across domains. But they are not lightweight by any reasonable definition. They need multi-GPU inference setups and large memory budgets that are unrealistic for most practical deployments and well out of reach for an MSc-scale project.

The gap therefore sits in the middle of the spectrum. Can a lightweight object-detection model — trained on the relatively well-resourced mobile UI domain and adapted to the data-scarce desktop domain with a minimal labelled budget — deliver a detector that is "accurate enough" for use inside a practical automation pipeline? And given that this is fundamentally a transfer-learning question, which adaptation strategy gives the best return on the labelled-data budget? Those are the questions the project sets out to answer.

A secondary, more practical, problem is that even an accurate detector is not, by itself, an automation system. A user does not want to be told "there are forty-seven elements on your screen". A user wants to say "click Save", and have the system do the right thing. That requires a grounding step — matching a natural-language instruction to one of the detected elements. The IVGocr framework of Dardouri et al. (2024a) provides a sensible scaffolding for this kind of pipeline, and this project adopts it. So the novelty in the prototype is not the pipeline architecture. It is the cross-domain-adapted detector that sits inside it.

## 1.4 RESEARCH AIM

The aim of the research is to design, develop and evaluate a scalable cross-domain machine learning framework capable of adapting mobile-trained GUI detection models for desktop environments while maintaining high accuracy and generalisation.

## 1.5 RESEARCH QUESTIONS

The aim is decomposed into four research questions that the rest of the work addresses one at a time.

- **RQ1.** What is the magnitude of performance degradation when applying mobile-trained GUI detectors to desktop screenshots?
- **RQ2.** Which adaptation strategies yield the largest improvements in low-label regimes?
- **RQ3.** How does model choice (YOLO vs DETR vs LVLM) influence transferability and sample efficiency?
- **RQ4.** What are the practical limits of a vision-and-action bot using adapted detectors in real desktop applications?

These four questions are answered, respectively, in the baseline performance numbers in Chapter 6 (RQ1), the adaptation method comparison in Chapter 7 (RQ2), the cross-architecture comparison in Chapter 7 (RQ3), and the prototype evaluation in Chapter 8 (RQ4). The chapter map is repeated in Section 1.11.

## 1.6 RESEARCH GAP

The literature reviewed in Chapter 2 makes one thing clear. The gap this project addresses is not a lack of state-of-the-art models. The mobile UI domain has highly optimised detectors of its own (Cheng et al., 2022). The desktop target domain has a clear application pipeline in the IVGocr framework (Dardouri et al., 2024a). Heavyweight large vision–language models such as SeeClick (Cheng et al., 2024) are capable of bridging the domain gap. They just do it at a computational cost that puts them out of reach for the kind of practical, on-machine deployment this project cares about.

The gap is in the *combination*. There is no published, lightweight, data-efficient method that takes a state-of-the-art mobile detector, adapts it to the desktop domain using the small labelled-data budget that an individual or a small team can realistically produce, and shows that the resulting model is usable inside a complete automation pipeline — not just on a static benchmark. That combination is what the dissertation contributes.

The data side sharpens the gap further. Mobile has RICO (Deka et al., 2017) and CLAY (Li et al., 2022a) providing tens of thousands of labelled screens. Desktop has only a handful of small, recently published datasets (Wang et al., 2025; Patel et al., 2025). The data-scarce target is what mandates domain adaptation in the first place. Training a high-capacity desktop-only model from scratch is not feasible at MSc scale. A model has to be trained somewhere else and then moved across.

[FIGURE 2: Positioning of this project against existing automation approaches.
Source: `reports/figures/ch1_positioning_grid.png` (to be produced; suggested layout is a 2-by-2 grid with axes "lightweight ↔ heavyweight" and "theme and DPI tolerant ↔ brittle", with SikuliX and PyAutoGUI in the bottom-left, `pywinauto` in the bottom-right but greyed out because it fails on modern Win11, SeeClick in the top-right, and this project in the middle).
Caption: Where the proposed framework sits relative to existing GUI automation approaches. Classical image-based and accessibility-tree tools sit in the lightweight-but-brittle corner; large vision–language models sit in the heavyweight-but-tolerant corner; this project targets the middle.]

## 1.7 RESEARCH OBJECTIVES

The main research objectives are as follows.

- To quantify the mobile-to-desktop performance gap using mean average precision (mAP) for detection quality and the Central Point Validation (CPV) metric of Dardouri et al. (2024b) for grounding quality.
- To implement and compare three adaptation methods: few-shot supervised fine-tuning, self-supervised pre-training followed by fine-tuning (SSP+FT), and unsupervised domain adaptation (UDA) using the Cross-Domain Adaptive Teacher framework of Li et al. (2022b) and the Source Hypothesis Transfer (SHOT) framework of Liang et al. (2020).
- To evaluate sample efficiency by determining how many labelled desktop images are actually required to achieve acceptable performance, sweeping over a small range of training budgets.
- To develop a prototype bot that demonstrates instruction-to-action behaviour on real desktop applications using the adapted detector inside the IVGocr pipeline.

Each objective is mapped to a chapter and to a measurable deliverable. The mapping is made explicit in Section 8.8 (Achievement of Research Objectives).

## 1.8 OPERATIONAL OBJECTIVES

The research objectives describe what is to be answered. The operational objectives describe how the work was actually broken down. The project was executed in four phases.

### 1.8.1 DATA ENGINEERING AND BASELINE ESTABLISHMENT

- Survey 10 to 15 diverse desktop applications, including Visual Studio Code, GIMP, Chrome, Firefox, Windows File Explorer, Notepad and Excel.
- Use an automated capture script built on top of `mss` and `pywinauto` to collect a small unlabelled corpus of desktop screenshots, covering different resolutions, themes and application states.
- Hand-select and annotate a small "Labelled Target Corpus" in CVAT against a five-class schema of `{button, menu, text_input, checkbox, icon}`.
- Train the mobile-baseline detector on CLAY.

### 1.8.2 MODEL ADAPTATION EXPERIMENTS

- Implement both a YOLOv8 backbone and a DETR backbone, each pre-trained on CLAY.
- Run the few-shot fine-tuning experiment on a small number of labelled desktop images to plot a data-efficiency curve.
- Pre-train the backbones using a generative inpainting self-supervised task on the unlabelled desktop corpus and repeat the few-shot experiment to measure the uplift from self-supervised pre-training.
- Implement the Cross-Domain Adaptive Teacher (Li et al., 2022b) and SHOT (Liang et al., 2020) UDA frameworks.

### 1.8.3 PROTOTYPE INTEGRATION

- Select the single best adapted model from the previous phase.
- Build the "Adapted-IVGocr" prototype that wraps it, using `mss` and `pywinauto` for capture, the adapted detector for perception, Tesseract or EasyOCR for reading text inside detected boxes, fuzzy string matching (`rapidfuzz`) for grounding the instruction to a detected element, and PyAutoGUI for the click action.

### 1.8.4 END-TO-END EVALUATION AND THESIS COMPOSITION

- Define 10 to 15 standardised automation tasks such as "open Notepad and save the file as `test.txt`".
- Evaluate the prototype's Task Success Rate (TSR) on those tasks.
- Perform a qualitative failure analysis that traces end-to-end failures back to detection errors, OCR errors, or grounding-logic errors.
- Write the final thesis and package the code.

## 1.9 PROPOSED SOLUTION

The solution has three interlocking components. The technical depth lives in Chapter 5 (Design) and Chapter 6 (Implementation); this section gives only the high-level shape.

### 1.9.1 DATA AND PREPROCESSING PIPELINE

The source mobile corpus is CLAY (Li et al., 2022a), a denoised subset of RICO (Deka et al., 2017). Using CLAY rather than raw RICO matters because RICO contains significant layout noise. CLAY is a deep-learning pipeline that automatically cleans and corrects those raw layouts, and the resulting corpus is a much better starting point for transfer learning. The CLAY annotation schema is mapped onto the five-class desktop schema using a deterministic table documented in Chapter 6.

The target unlabelled desktop corpus is collected by a Python script. The script drives `pywinauto` to enumerate the visible top-level windows of a curated set of 10 to 15 applications, captures each window with `mss`, and saves the screenshot to disk. The script is parameterised by resolution, theme and DPI scaling so the corpus covers the in-the-wild variability the deployed prototype will eventually meet.

The target labelled desktop corpus is hand-curated from the unlabelled pool and annotated in CVAT against the five-class schema. It serves two roles. It is the gold-standard test set against which all adaptation methods are evaluated. And it is the source of the few-shot training subsets used in the sample-efficiency experiment.

### 1.9.2 ADAPTATION METHODOLOGIES

All adaptation methods are applied to both a YOLOv8 backbone and a DETR-R50 backbone, so the cross-architecture comparison in RQ3 is a controlled one.

The baseline is the mobile-trained detector run zero-shot on the labelled target corpus. The resulting low mAP is the "problem" the three adaptation methods then try to close.

The first adaptation method is few-shot supervised fine-tuning. The CLAY-trained backbone is frozen and only the final detection head is re-trained on the labelled desktop images, sweeping over a small range of `k` to produce a data-efficiency curve. This is the simplest of the three methods. It serves as the floor against which the other two are compared.

The second method is self-supervised pre-training (SSP) followed by fine-tuning. A generative inpainting task (Anaya-Isaza et al., 2024) is used on the unlabelled desktop corpus. Random patches are masked out and the model is trained to predict them. The intuition: to inpaint a missing patch of a Windows toolbar, the model has to implicitly learn the structural grammar of desktop UIs — toolbars are horizontal, icons sit in rows, dialog buttons cluster bottom-right. The SSP backbone is then handed to the few-shot procedure to measure whether unsupervised pre-training improves the final mAP.

The third method is unsupervised domain adaptation (UDA). Two UDA frameworks are implemented and compared. The first is the Cross-Domain Adaptive Teacher of Li et al. (2022b). It is a teacher-student setup where a stable Exponential Moving Average teacher generates pseudo-labels on weakly augmented target images, and a student is trained on a mixed batch of labelled source data and strongly augmented pseudo-labelled target data. The second is SHOT (Liang et al., 2020). SHOT freezes the source-trained classification head (the "source hypothesis") and adapts only the feature extractor on the unlabelled target images using self-supervision. The goal is to align the new target features to the frozen source hypothesis, rather than retrain the head itself.

### 1.9.3 PROTOTYPE INTEGRATION AND EVALUATION

The prototype, VisClick, is a direct implementation of the IVGocr architecture (Dardouri et al., 2024a). The novelty is the replacement of their standard YOLOv8 detector with the cross-domain-adapted detector from the previous component.

The runtime flow:

1. The user supplies a free-form text instruction, for example "click Save".
2. A screenshot of the user-selected monitor is taken with `mss`, in the virtual-desktop coordinate space.
3. The adapted detector runs on the screenshot and returns a set of candidate bounding boxes, each with a class label and a confidence score.
4. Tesseract or EasyOCR is run on each detected bounding box (rather than on the whole image) to recover the visible text. A full-image OCR pass is kept in reserve as a fallback, for cases where the detector misses the target entirely.
5. A fuzzy string matcher (`rapidfuzz`) computes the similarity between the user's instruction and the OCR text of each detected element. The element with the highest score above a similarity threshold is selected.
6. PyAutoGUI moves the cursor to the centre of the selected box and issues a single left click. When no candidate clears the threshold, the prototype refuses to click and reports a structured failure message. This refusal-on-uncertainty behaviour is a deliberate design choice. A confident wrong click, in an automation tool, is worse than an honest refusal.

The detection metric used for component-level evaluation is mAP at IoU 0.5, with the Central Point Validation (CPV) metric of Dardouri et al. (2024b) used for grounding quality. The end-to-end bot metric is Task Success Rate (TSR), a binary pass or fail on each of the standardised tasks.

[FIGURE 3: High-level architecture of the proposed solution.
Source: `reports/figures/ch1_solution_overview.png` (to be produced; suggested source is the Mermaid block diagram already in `docs/VisClick_Report_Data_Form.md` Section 18.1, exported as a PNG).
Caption: End-to-end shape of the proposed solution. A mobile-pretrained detector is adapted to desktop using one of three methods and then wrapped inside the IVGocr-style instruction-to-action pipeline that constitutes the deliverable prototype.]

## 1.10 SCOPE OF THE PROJECT

The scope of the project is as follows.

**In scope.**

- Cross-domain adaptation from a single mobile source domain (CLAY, with raw RICO as the upstream corpus) to a single desktop target domain (Windows 11 with 10 to 15 common applications).
- Two-detector architectural comparison between YOLOv8 and DETR. Both are state-of-the-art, both have well-known reference implementations, and they differ on a single architecturally meaningful axis (anchor-based dense detection with a multi-scale neck for YOLO, against anchor-free direct set prediction with a transformer encoder–decoder for DETR), which makes the comparison clean.
- Three adaptation methods: few-shot fine-tuning, self-supervised pre-training followed by fine-tuning, and unsupervised domain adaptation. The third method itself contains the Adaptive Teacher and SHOT sub-comparison.
- A prototype that closes the loop, on the user's machine, from a natural-language instruction to a click.
- Quantitative evaluation against three measurable criteria: mAP on the labelled desktop test set, CPV on the IVGocr grounding step, and TSR on a fixed task suite.

**Out of scope.**

- Cross-platform support. The prototype targets Windows 11. macOS and Linux are not in scope. `pywinauto` is itself Windows-only, the DPI assumptions in the capture stage are Windows-specific, and any meaningful cross-platform work would have at least doubled the project's effort budget.
- Heavyweight large vision–language models. Models such as SeeClick (Cheng et al., 2024) are referenced and discussed in the literature review because they represent the "heavyweight state of the art" against which the project's lightweight stance is positioned, but they are not benchmarked here. The compute budget for that kind of comparison is well beyond what was available, and including it would have shifted the project from a practical engineering investigation to a pure benchmarking exercise.
- Full accessibility-tree integration at runtime. `pywinauto` is used in the data-collection stage and is also benchmarked as a classical baseline in Chapter 7, but it is not used at runtime in the prototype's perception pipeline. Using it at runtime would defeat the point of the vision-based approach.
- Highly multimodal instructions. Instructions are free-form text. Voice input, image-conditioned instructions, multi-step natural-language commands and conversational dialogue are all out of scope.
- Robotic process automation at fleet scale. The prototype is a single-user, single-machine demonstrator. Scaling out to multiple machines, multi-tenant deployment, or enterprise governance is left for future work and discussed in Chapter 9.

## 1.11 CHAPTER SUMMARY

This chapter has set up the problem, the aim, the four research questions, the research gap, and the four-phase work plan the rest of the report follows. The picture in one paragraph is this. GUI automation on the modern desktop is in an awkward place. Classical image-based tools are too brittle. Classical accessibility-tree tools have fallen out of step with the modern Windows application mix. The heavyweight large vision–language models that *can* do the job are too big to run anywhere most people would actually want to. Sitting in the middle, where there is a clear opportunity, is the idea of a cross-domain-adapted lightweight detector — trained on the relatively well-resourced mobile UI domain and then carried across to the data-scarce desktop domain. The project investigates how far that idea can be pushed, using three adaptation methods (few-shot fine-tuning, SSP+FT, and UDA) on two backbones (YOLOv8 and DETR), and integrates the best of those into a working prototype that closes the loop from a typed instruction to a click on the real Windows desktop.

The rest of the report is organised as follows. **Chapter 2** is the literature review. It walks through the datasets, the model architectures and the adaptation methodologies in enough depth to support the architectural choices made later, and it ends with the explicit research-gap statement that motivates the rest of the work. **Chapter 3** lays out the requirement analysis, including a stakeholder analysis using the Onion model, the functional requirements and the non-functional requirements with quantitative targets. **Chapter 4** covers the project management approach: the research methodology, the software development methodology, the risk register, and the project plan. **Chapter 5** covers the design, including a high-level architecture, a research design, a block diagram, a flow chart, and the wireframes for the prototype user interface. **Chapter 6** is the implementation chapter, which describes how the data pipeline, the three adaptation methods, and the prototype were actually built. **Chapter 7** is the testing chapter, which reports the model-level and prototype-level test results in tabular form. **Chapter 8** is the evaluation chapter, which interprets those results against the research questions and the requirements and includes a discussion of legal, ethical, professional and social impact. **Chapter 9** concludes with the limitations, the things the author would do differently in retrospect, and the directions for future work.

---

# CHAPTER 02 – LITERATURE REVIEW

## 2.1 CHAPTER OVERVIEW

This chapter reviews the prior work that the rest of the project rests on. The ordering follows the same shape as the methodology in Chapter 6. Data first, because data is what gates everything else. Then the pre-processing step that turns noisy raw data into something a model can actually train on. Then the classical automation tools that have held the GUI testing space for decades, and the deep-learning detectors that have started to displace them on mobile UIs. After that, the family of domain-adaptation methods this project uses to carry a mobile-trained detector across to the desktop. The chapter then looks at the wider GUI-agent landscape, including the heavyweight vision–language models that sit at the other end of the spectrum from the present work, and ends with a short discussion of metrics and an explicit statement of the research gap.

Where two pieces of work try to do roughly the same thing, I put their numbers side by side so the difference is visible. Where a paper is cited only as motivation rather than as a method we use, I say so. The aim is to leave the reader with a clean picture of what was taken off the shelf and what was left there for a reason.

## 2.2 EXISTING GUI ELEMENT DATASETS

The starting point for any vision-based UI work is a corpus of annotated screenshots. The most important fact about that corpus today is that the mobile side is well resourced and the desktop side is not.

The canonical mobile UI dataset is **RICO**, released by Deka et al. (2017). RICO contains around 72,000 unique Android screens from 9,300 free apps on the Google Play Store, paired with each screen's Android view-hierarchy XML and several derived properties (text labels, structural relationships, animation traces, interaction sequences). The view hierarchy is what makes RICO useful for object detection. From the XML one can derive a bounding box and a class label for every leaf node, which in practice means tens of millions of labelled elements across the corpus. The well-known downside is that the raw view hierarchy is noisy. Container nodes overlap with their visual children, invisible nodes still appear in the tree, and the leaf-class labels are inconsistent across SDK versions and across app authors. Anyone who has tried to train a detector directly on raw RICO boxes hits these issues quickly.

The community's answer is **CLAY** by Li et al. (2022a). CLAY is not a new corpus of screenshots. It is a deep-learning denoising pipeline that takes RICO's raw view-hierarchies and produces cleaner, machine-verified layouts. The result is 59,555 cleaned Android UI screens with a more consistent 23-class taxonomy and a much-reduced rate of overlapping, invisible, or mis-classified boxes. The improvement is not small. Detectors trained on CLAY-cleaned labels gain 5 to 8 mAP points over the same architecture trained on raw RICO. For this reason CLAY is the source-domain training set for this project's headline detector.

The mobile domain has not stood still since RICO. The **MUD** dataset of Kumar et al. (2024) was put together in response to the observation that RICO and CLAY are now temporally outdated. Android's visual design has shifted noticeably since 2017 — the move from Holo and Material 1 themes to Material 3, the rise of foldable form factors, the increase in dark-mode and large-text accessibility variants — and a detector trained on the older corpus does worse on modern screens. MUD reports a button-class mAP of 75.3 % on its own test split compared to 63.4 % when the same model is trained on RICO and evaluated on MUD. That gap is not enormous, but it speaks to a real data-currency problem even within the mobile domain.

On the desktop side the picture is much thinner. There is no "desktop RICO" of comparable scale. The recent attempts to fill the gap are themselves telling, both of demand and of how new the recognition of the gap is. **DeskVision** (Wang et al., 2025) proposes a large-scale desktop region-captioning corpus aimed at GUI agents and is dated March 2025 on arXiv. **GenGUI** (Patel et al., 2025) is a synthetic dataset of web interfaces generated by ChatGPT, closer to a UI-design-generation corpus than to an element-detection one. Neither is yet at the order of magnitude of RICO. The authors of the IVGocr paper this project's prototype is modelled after had to build their own desktop dataset to run their experiments (Dardouri et al., 2024a), and they note this explicitly in the paper. The data-scarce nature of the desktop target is the gravitational pull that draws this project, and others like it, toward domain adaptation rather than train-from-scratch on the target.

Table 1 sets the principal datasets side by side. The figures for RICO and CLAY are the ones the authors report; the figures for DeskVision and GenGUI are from their respective arXiv submissions.

**Table 1: Available GUI element datasets.**

| Dataset | Year | Domain | Screens | Annotations | Public licence |
|---------|------|--------|--------:|-------------|----------------|
| RICO | 2017 | Mobile (Android) | 72,219 | ~3M leaf nodes (raw view-hierarchy) | Free for research |
| CLAY | 2022 | Mobile (Android) | 59,555 | Cleaned 23-class layouts | Open access |
| MUD | 2024 | Mobile (Android, modern) | 18,132 | Modern-style annotations | Open access |
| DeskVision | 2025 | Desktop | "Large-scale" (count not yet released) | Region-caption pairs | Pending release |
| GenGUI | 2025 | Web (synthetic) | Generated on demand | Layout + class labels | CC-BY |
| Zenodo unified bundle (this project) | 2023 | Mobile + Web | 9,646 | 6-class collapsed from RICO + CLAY + VINS | Open access |

The last row, the Zenodo unified bundle, is what this project actually trains on. It combines RICO, CLAY and VINS into a single 6-class taxonomy `{button, text, text_input, icon, menu, checkbox}` chosen to match what an automation bot needs to interact with. The class-collapse mapping is documented in Chapter 6.

[FIGURE 4: RICO and CLAY side by side.
Source: `reports/figures/ch2_rico_vs_clay.png` (to be produced; suggested layout is one mobile screen from RICO with raw view-hierarchy boxes overlaid, beside the same screen with CLAY's cleaned labels — the CLAY GitHub page has matched-pair examples that can be reproduced).
Caption: Raw RICO labels on the left, CLAY's denoised labels on the right, same screen. CLAY removes invisible-container nodes, fixes class mis-assignments, and reduces overlapping-box duplicates.]

## 2.3 PRE-PROCESSING FOR UI ELEMENT DETECTION

Pre-processing for a UI corpus is not the same problem as pre-processing for natural images. The standard tricks (random crop, horizontal flip, colour jitter) are either useless or actively harmful on screenshots. Horizontal flip turns a left-aligned toolbar into a right-aligned one, which is fine in principle until the model also flips the text inside the buttons and produces meaningless training signal. Colour jitter on a Win11 light theme can produce shades that no real application ever displays. The literature treats UI pre-processing more as a label-noise problem than as an image-augmentation problem.

The largest single piece of UI pre-processing work in the public literature is CLAY itself (Li et al., 2022a). Its main contribution is a learned denoiser that takes raw RICO view-hierarchy boxes and produces cleaner labels. Invisible containers are removed, overlapping duplicates are collapsed, mis-classified node types are corrected. Detectors trained on CLAY-cleaned labels gain several mAP points on held-out splits over the same architecture trained on raw RICO. The denoising is a pre-processing step in spirit, even though it is implemented as its own deep-learning pipeline.

A more pragmatic line of pre-processing work tackles class imbalance. Both RICO and the desktop seed corpus collected in this project are heavily skewed: the `text` class is much more frequent than any of the actionable classes (`button`, `text_input`, `menu`, `checkbox`). The standard responses are weighted random oversampling, or a class-balanced focal loss. This project chose a simpler route, a 12-to-6 class collapse that puts visually similar minority classes into the same training target. Two reasons. First, to keep the training pipeline reproducible on Colab Free without exotic loss functions. Second, the 6-class taxonomy maps cleanly onto what the downstream IVGocr matcher needs.

A short remark on input resolution. RICO and CLAY use portrait-oriented Android screens that fit comfortably into a 640 × 640 detector input. Desktop screenshots are landscape, often 1920 × 1080 or 3440 × 1440, and need to be down-scaled before they enter a YOLOv8 detector with `imgsz = 640`. This rescaling is itself a pre-processing concern that produces measurable accuracy variation. The numbers in Chapter 7 are reported with a single fixed `imgsz = 640`; the sensitivity of those numbers to that choice is discussed in Section 9.7.

## 2.4 CLASSICAL AUTOMATION APPROACHES

Before the deep-learning era, three families of tools dominated GUI automation. They are still in widespread use, particularly in industrial test automation and RPA, and this project benchmarks itself against the strongest of them.

The first family is **bitmap-based visual automation**. The best-known tool is **SikuliX** (SikuliX, 2024). SikuliX records a small bitmap of a UI element (a *Save* button, a magnifying-glass icon) and at run time uses OpenCV's `matchTemplate` to find that bitmap on the live screen. The user writes a script in a Sikuli-flavoured Python that says, in effect, "click this image". The strength of the approach is its simplicity. The weakness is its rigidity. A bitmap is a frozen photograph of the element under one theme, one DPI, one font, one application version. Change the theme to dark mode and the bitmap stops matching. Change the DPI from 100 % to 125 % and the same thing happens. AskUI's recent review (AskUI, 2024) phrases this politely as "image recognition first", but the practical effect at deployment scale is that scripts decay quickly. The empirical evidence in Chapter 7 of this report confirms that on the specific subset of tasks where a reference bitmap could be captured, template matching is excellent — it scored 100 % on those tasks — but on tasks where no useful bitmap exists (positional targets such as "click the first command", dynamic state toggles, text-inside-text) it cannot represent the problem at all.

The second family is **coordinate-based automation**. The canonical Python example is **PyAutoGUI** (Sweigart, 2024), which exposes `pyautogui.click(x, y)` and lets the user write scripts that drive the mouse and keyboard at specified pixel coordinates. PyAutoGUI is widely used inside other automation stacks, including this project's prototype, where it drives the final click. On its own it is the most brittle of the three families because it has no knowledge of what is at those coordinates. The same script that works on a 1080p laptop fails on a 1440p desktop unless every coordinate is recomputed. PyAutoGUI is best understood not as a competitor to a vision-based bot but as the low-level primitive that any vision-based bot eventually has to use to translate a chosen bounding box into an OS-level click.

The third family is **accessibility-tree automation**. On Windows the canonical Python library is **pywinauto** (pywinauto Contributors, 2024). pywinauto uses Microsoft's UI Automation framework to walk the live application's accessibility tree and find controls by their semantic `Name` and `ControlType`. The approach is theoretically beautiful. It abstracts away theme, DPI and font: the same script should work on a 1080p laptop and a 1440p desktop because both expose the same `Button(Name='Save')` control. In practice the modern Windows application mix has eroded the assumption that the accessibility tree faithfully reflects the visible UI. Electron applications such as Visual Studio Code, Slack and Discord expose only a degenerate tree because the renderer is a Chromium browser. Modern Windows 11 applications using WinUI 3 or XAML islands frequently expose localised internal control names rather than the visible labels. Web pages inside any browser serve their accessibility tree via ARIA, which is a separate convention again. The empirical baseline reported in Chapter 7 of this report shows pywinauto scoring 1 out of 15 task instances on a representative Windows 11 workload — and that single success is the negative case where the right answer is for the bot to do nothing. On every positive task (Notepad's Save-As dialog, Visual Studio Code's Search panel, Chrome's omnibox, File Explorer's ribbon) pywinauto returned `ElementNotFound`.

The collective failure of all three classical families on the modern Windows 11 application mix is the operative justification for a vision-based approach. If the accessibility tree could be trusted, machine learning would not be needed. On a 2026-vintage desktop, the evidence is that it cannot.

[FIGURE 5: Where each classical baseline succeeds and fails on the 15-task workload.
Source: `reports/figures/ch2_classical_baselines_grid.png` (to be produced; suggested format is a horizontal bar chart of pass/fail counts per method per task category, or one of the existing per-method overlays from `reports/figures/baselines/`).
Caption: Per-task verdicts for the three classical baselines across the 15 evaluation tasks. Each baseline's failure cluster is distinct, which is what motivates the project's combined vision + OCR approach.]

## 2.5 DEEP-LEARNING APPROACHES FOR UI ELEMENT DETECTION

A separate strand of work treats UI element detection as a classical object-detection problem and solves it with the same architectures the natural-image community has converged on. This is the strand this project belongs to.

The most-cited early work in the strand is **UIED** by Chen et al. (2020). UIED makes a deliberately pragmatic argument. Neither pure deep learning nor pure classical computer vision is sufficient for GUI element extraction on its own, because the two methods miss complementary things. A Faster R-CNN baseline trained on UI screenshots reaches an F1 of 0.71 on their internal benchmark but misses small icons and dropdown arrows that the classical edge-and-region pipeline catches. Their classical-only pipeline manages F1 of 0.55, but misses text-shaped buttons that the deep learner gets easily. The UIED hybrid (a CNN for non-text shapes, an EAST/CTPN-style text detector for text, then a rule-based merger) reaches F1 of 0.84. The architecture matters less than the methodological lesson: combining a fast deep detector with a text-recognition fallback is the right shape for a UI element detector. This project's pipeline, with YOLOv8 as the detector and EasyOCR providing both per-box and full-image text grounding, is in direct lineage from UIED.

A more specialised mobile-targeted detector is **YOLOv5-MGC** by Cheng et al. (2022). The paper introduces a YOLOv5 variant tailored for mobile GUI detection, with a microscale detection layer and an attention mechanism added to handle the very small icons that crowd a mobile screen. They report 89.8 % mAP on their mobile UI test set, which is a strong number. The architectural innovations are sensible for mobile UIs, but the paper itself hypothesises that the "microscale + attention" combination may be overfit to mobile-style density and may not transfer well to the very different density of a desktop's packed-scene toolbar. Validating or refuting that hypothesis on real desktop data was one of the original motivations of this project, and is what RQ3 is about.

This project compares two architectural families. The first is **YOLOv8** (Ultralytics, 2024), the current-generation Ultralytics implementation. YOLOv8 is an anchor-free, single-stage detector with a modified CSPDarknet53 backbone and an enhanced Path Aggregation Network (PANet) neck explicitly designed to fuse features across multiple scales. The multi-scale neck is the property that matters for UI detection, where the same screen contains a 16-pixel close-X icon and a 200-pixel ribbon menu at the same time. The Ultralytics implementation is well documented, runs on Colab Free's T4 in a usable time budget, and exports cleanly to ONNX for CPU-only inference. It is the project's headline backbone.

The second is **DETR** (DEtection TRansformer) by Carion et al. (2020). DETR re-frames detection as a direct-set-prediction problem solved with a transformer encoder-decoder and a bipartite-matching loss. It eliminates anchors and non-maximum suppression, which is conceptually clean and has the practical benefit of removing two layers of hyperparameter tuning. The well-documented weakness of the original DETR is poor performance on small objects, attributed to the global attention pattern in the encoder spending too much attention budget on large regions and too little on small ones. For this project, the architectural comparison committed to in RQ3 puts a YOLOv8 backbone and a DETR-R50 backbone side by side, on the hypothesis that DETR's small-object weakness will be aggravated by the packed-scene density of desktop UIs. The DETR experiments are part of Phase 2 and are tracked as D-01.

A separate piece of work worth flagging is **Apple's Screen Recognition** of Zhang et al. (2021). Screen Recognition is the production pipeline behind the iOS VoiceOver accessibility feature. An on-device object detector classifies widgets into 13 types, with OCR adding text labels. The reported numbers are F1 of 0.91 on in-distribution screens, dropping to 0.74 on apps the model has never seen, with OCR adding a further 6 to 11 points on top. The paper is cited here for two reasons. First, it is the closest existing analogue to what this project tries to do — an industrial-scale, accessibility-motivated, on-device UI detector that adds OCR exactly where the visual detector misses. Second, the 0.91 to 0.74 in-distribution to out-of-distribution drop is empirical confirmation that even at Apple-scale data and engineering, the domain-shift effect is real and is the right thing to design around. This project's Win11-domain drop is consistent with that pattern at much smaller scale.

## 2.6 DOMAIN ADAPTATION METHODOLOGIES

The four research questions for this project collapse, on closer inspection, into two empirical questions. RQ1 asks how big the domain shift is. RQ2 asks how to close it. The literature answers RQ2 in three different ways, and this project implements one method from each.

The simplest method is **few-shot supervised fine-tuning**. The CLAY-pretrained backbone is frozen and the final detection head is re-trained on a small labelled subset of the target domain. The size of the subset is the free parameter; this project's plan is to sweep over a small range of `k` values to draw a data-efficiency curve. Few-shot fine-tuning is the canonical baseline in the transfer-learning literature. The broad survey of Iman et al. (2023) gives roughly two dozen variations on the theme of "fine-tune the top, freeze the bottom". The reason the project keeps it in the experiment plan is not novelty. It is the necessary control. Any more elaborate method must beat the few-shot fine-tune by a non-trivial margin to be worth its complexity.

The intermediate method is **self-supervised pre-training (SSP) followed by fine-tuning**. SSP first pre-trains the backbone on unlabelled target-domain data with a self-supervised pretext task — typically masked-patch reconstruction or contrastive learning — and then fine-tunes the resulting backbone on labelled data exactly as in the few-shot case. The intuition is that the SSP step lets the model absorb the structural grammar of the target domain (toolbars are horizontal, dialog buttons cluster bottom-right, menubars sit under the title bar) without requiring labels. The medical-imaging survey of Anaya-Isaza et al. (2024) reports a consistent uplift of 4 to 11 points on downstream classification accuracy when masked-patch reconstruction is added to small-data fine-tuning. The SSP experiment is tracked as D-02.

The most elaborate method is **unsupervised domain adaptation (UDA)**, which uses *no* labelled target data and relies entirely on the unlabelled target corpus together with the labelled source corpus. This project compares two UDA families on the desktop target.

The first is the **Cross-Domain Adaptive Teacher** of Li et al. (2022b). Adaptive Teacher is a robust teacher-student framework. A stable Exponential Moving Average (EMA) teacher generates pseudo-labels on weakly-augmented target images. The student is then trained on a mixed batch of labelled source data and strongly-augmented pseudo-labelled target data, with a discrepancy loss that aligns the student's predictions across the two augmentation regimes. The EMA teacher is updated as a moving average of the student's weights. This is what makes the framework stable, in contrast to earlier teacher-student schemes that drifted as the student's pseudo-labels degraded. The published results are strong, with Adaptive Teacher closing roughly two-thirds of the source-to-target gap on standard cross-domain detection benchmarks. Tracked as D-03.

The second is **SHOT (Source HypOthesis Transfer)** of Liang et al. (2020). SHOT takes a different stance from teacher-student. Instead of training a student to imitate a teacher, SHOT freezes the source-trained classification head (the "source hypothesis") and adapts *only* the feature extractor backbone on the unlabelled target images using a self-supervised objective. The intuition is that the head encodes what classes look like, while the extractor encodes what the world looks like. When the world changes (from mobile UIs to desktop UIs), it is the extractor that needs to adapt, not the head. The published SHOT results are competitive with teacher-student approaches on smaller benchmarks and have the practical advantage that the source data does not need to be available at adaptation time. For privacy-sensitive deployments this matters; for this project it matters less, but SHOT is included as the second UDA comparison point because it is structurally different enough to give a genuine architectural choice. Tracked as D-04.

A useful framing of the three methods is in terms of what each requires. Few-shot fine-tuning requires labelled target data and no unlabelled target data. SSP+FT requires both labelled and unlabelled target data. UDA requires only unlabelled target data, plus the original labelled source. The methods sit on a continuum from "expensive labels, simple training" to "no labels, complex training". The empirical question (RQ2) is where on that continuum the best practical return sits, given a realistic MSc-scale data budget. The published literature suggests SSP+FT will roughly match UDA at a fraction of the engineering cost, and that both will outperform pure few-shot once the labelled budget is small. The actual numbers will arrive when D-02, D-03 and D-04 are completed.

## 2.7 GUI AGENTS AND VISUAL GROUNDING FRAMEWORKS

The detection and adaptation methods reviewed so far produce a *detector*. A detector is not an automation system. Closing the gap from "here are the elements on the screen" to "do the thing the user asked for" requires a grounding layer that maps a natural-language instruction onto one of the detected elements. The published frameworks for this layer fall into two clusters.

The first cluster is **modular pipelines** in the style of UIED and its descendants. The Instruction Visual Grounding framework of Dardouri et al. (2024a) is the most directly applicable for this project. They propose IVGocr, an explicit three-stage architecture: a YOLOv8 detector finds the UI elements; OCR reads the visible text on each detected element; an LLM, or in their lighter-weight variant a fuzzy string matcher, matches the user's instruction to the read text. They also introduce the Central Point Validation (CPV) metric for evaluating how often the chosen element's centre falls inside the ground-truth bounding box of the correct target (Dardouri et al., 2024b). CPV is more permissive than IoU at high thresholds, and arguably more honest as a grounding metric. This project's prototype, VisClick, is a direct implementation of the IVGocr architecture. The YOLOv8 detector is the project's CLAY-pretrained, desktop-adapted model. The matcher is a rapidfuzz fuzzy match rather than a heavyweight LLM. The reason for picking rapidfuzz over an LLM is operational. It runs in milliseconds on CPU and removes a network dependency. The downstream evaluation in Chapter 8 shows that for the 15-task workload, the rapidfuzz matcher is sufficient. The residual failures come from the detector, not from the matcher.

The second cluster is **end-to-end large vision–language models** (LVLMs). The exemplar is **SeeClick** of Cheng et al. (2024). SeeClick replaces the entire detector-plus-OCR-plus-matcher stack with a single multi-billion-parameter vision–language model that takes a screenshot and an instruction as input and outputs click coordinates directly. The training corpus is roughly one million screenshots covering web, desktop and mobile. The reported numbers are 73 % click accuracy on the web benchmark Mind2Web, 53 % on the mobile benchmark AITW, and 47 % on a new desktop benchmark the authors introduce. As a piece of engineering, it is the current state of the art on cross-domain GUI grounding. This project does not benchmark against SeeClick because the inference-cost gap is too large. SeeClick needs a multi-GPU inference setup and substantial memory, both of which are out of scope here. SeeClick is the reference point that Section 1.6 cites as the "heavyweight SOTA", and the project's positioning is explicitly as a lightweight, interpretable alternative for the cases where on-device, low-latency inference matters more than the absolute top of the leaderboard.

A related LVLM piece of work is Google Research's **ScreenAI** of Baechler et al. (2024). ScreenAI is a 5-billion-parameter vision–language model pre-trained on a screenshot corpus an order of magnitude larger than RICO. The headline claim is state-of-the-art on four of the five UI benchmarks tested. The methodological lesson, for the purposes of this review, is that UI element coverage is fundamentally a data-scale problem more than an architectural one. ScreenAI's gains over earlier LVLMs come almost entirely from the increase in pre-training corpus size, not from any architectural novelty. This is cited later, in Section 9.7, as evidence that the residual gap on Win11 native dialogs in this project's results is well aligned with the published frontier. The open-source desktop UI corpus does not yet exist at the scale that would let a smaller model close the gap purely by architecture.

[FIGURE 6: Modular versus end-to-end grounding pipelines.
Source: `reports/figures/ch2_modular_vs_e2e.png` (to be produced; suggested layout is a two-panel block diagram, with the IVGocr-style three-stage modular pipeline on the left and the SeeClick-style end-to-end LVLM on the right).
Caption: Two architectural families for instruction-to-action GUI agents. This project belongs to the modular family on the left, in deliberate contrast to the end-to-end LVLM family on the right.]

## 2.8 EVALUATION METRICS IN THE UI DOMAIN

A short review of metrics is appropriate, because the metric choice non-trivially affects what counts as a "good" detector. Three metric families recur in the literature reviewed above.

The **detection-quality** family is the standard COCO-style mean average precision (mAP) at intersection-over-union (IoU) thresholds 0.5 and 0.5:0.95. mAP at IoU 0.5 is the conventional headline, mAP at IoU 0.5:0.95 is the harder, more conservative number. Almost every paper reviewed above reports mAP@0.5 as the principal headline, with per-class average precision sometimes reported alongside. This project reports both, in `reports/tables/source_per_class.csv`.

The **grounding-quality** family is more idiosyncratic. The CPV metric of Dardouri et al. (2024b) is one of the more thoughtful proposals. A grounding is considered correct if the centre of the predicted bounding box falls within the ground-truth box of the target element. CPV is more permissive than IoU at high thresholds, but it is also closer to what an automation bot actually needs. A click that lands somewhere inside the target is sufficient. This project adopts CPV as a secondary metric alongside mAP.

The **end-to-end task-success** family is what the bot itself is measured against. Task Success Rate (TSR) is the binary pass/fail rate over a fixed test suite. Almost every modern GUI-agent paper reports TSR as the primary user-visible metric. TSR has the merit of being interpretable to non-specialist stakeholders ("seven out of every ten clicks land in the right place") and the demerit of folding together detection, OCR and matcher errors into a single number. Chapter 8 decomposes TSR failures into the three component error families, following the failure-analysis approach Dardouri et al. (2024a) use.

One metric this project does *not* use, despite its dominance in the natural-image-detection literature, is **F1 at a fixed confidence threshold**. F1 conflates two questions a UI automation system has to answer independently. Does the detector see the element? Does the matcher pick the right one? Keeping these two stages separate is more diagnostic, even if it sacrifices the single-number convenience of F1.

## 2.9 RESEARCH GAP AND POSITIONING OF CURRENT STUDY

The literature is best summarised by a single observation. There is no missing piece in the constellation, only a missing combination. State-of-the-art mobile UI detectors exist (Cheng et al., 2022). A clean target-application pipeline exists (Dardouri et al., 2024a). Heavyweight LVLMs that solve the cross-domain problem at scale exist (Cheng et al., 2024; Baechler et al., 2024). The piece that is missing is a *lightweight, data-efficient* method that takes the SOTA mobile detector, adapts it to the desktop domain using the small labelled-data budget an individual or a small team can realistically produce, and demonstrates that the resulting detector works *inside a complete automation pipeline* rather than only on a static benchmark.

The gap is the combination of three constraints. **Lightweight**, in the sense that the runtime must fit comfortably on a consumer CPU; this rules out SeeClick and ScreenAI. **Data-efficient**, in the sense that the labelled-target budget must be at most a few hundred images; this rules out training a desktop-specific detector from scratch in the style of MUD. **Integrated**, in the sense that the deliverable is a working click-bot evaluated end-to-end on real applications; this rules out comparing only on mAP on a held-out test split.

To be precise about what the dissertation contributes inside that gap, the contribution is fourfold.

- A quantitative measurement of the source-to-target domain shift on a public mobile UI source (CLAY) and a personal desktop target (Windows 11, ten to fifteen applications). This is RQ1.
- A side-by-side comparison of three adaptation methods (few-shot fine-tuning, SSP+FT, UDA with an Adaptive Teacher and SHOT sub-comparison) on two backbones (YOLOv8 and DETR). This is RQ2 and part of RQ3.
- An empirical evaluation of the adapted detector inside the IVGocr pipeline on a 15-task workload, including a head-to-head against three classical baselines (template, OCR-only, `pywinauto`). This is RQ4 and the rest of RQ3.
- A public, reproducible implementation. Every adaptation method, every baseline, every CSV, every figure is available under the project's open-source repository. This is itself a contribution given how rare end-to-end-reproducible MSc UI-automation projects are in the literature.

The positioning relative to SeeClick and the LVLM family is explicit. This project does not claim to outperform a 7-billion-parameter end-to-end model on detection accuracy. It claims that a small, interpretable, modular pipeline can deliver "good enough" performance for the practical IVGocr-style application on a single CPU, at a fraction of the inference cost, with a much smaller training and adaptation budget. That trade-off is the right one for practitioners who actually need to deploy UI automation on their own machines.

## 2.10 CHAPTER SUMMARY

This chapter walked through the literature in the order the project consumes it. The mobile UI domain is data-rich, anchored by RICO and CLAY. The desktop domain is data-poor, with recent attempts at corpora (DeskVision, GenGUI) still emerging. Classical automation tools — bitmap, coordinate and accessibility-tree — have all run into problems on the modern Windows 11 application mix, leaving a gap that vision-based detection is the natural candidate to fill. Among deep-learning detectors, the two architectural families this project compares (YOLOv8 with its multi-scale PANet neck, DETR with its transformer set-prediction) have well-documented strengths and weaknesses. YOLOv8's multi-scale design is the favourite, with DETR included as a controlled comparison. Among adaptation methods, the three this project implements (few-shot, SSP+FT, UDA) span the continuum from labelled-only-on-target to no-labels-on-target. The published literature suggests SSP+FT will give the best practical return at the project's data budget. Among grounding frameworks, the IVGocr modular pipeline of Dardouri et al. (2024a) is the immediate architectural ancestor of this project's prototype; SeeClick and ScreenAI are the heavyweight reference points that anchor the dissertation's lightweight stance. The combined research gap is the absence of a lightweight, data-efficient, end-to-end-validated cross-domain UI adapter for the desktop, and the project's four research questions sit precisely inside that gap.

The next chapter, Chapter 3, turns to requirement analysis. It begins with a stakeholder analysis and proceeds through functional and non-functional requirements with quantitative targets that the rest of the report measures against.
