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

---

# CHAPTER 03 – REQUIREMENT ANALYSIS

## 3.1 CHAPTER OVERVIEW

This chapter sets out the requirements the system was built against. It begins with a stakeholder analysis using the Onion model. Requirements without stakeholders are arbitrary. The stakeholder analysis is then converted into a set of stakeholder viewpoints, each of which contributes some requirements. The methodologies used to gather requirements come next, together with the methodology for obtaining the datasets the system is trained on. UML use case diagrams formalise the system's interactions with its users, and the use cases are then written out in long form. The chapter ends with the explicit list of functional requirements (R-FR-01 to R-FR-09) and non-functional requirements (R-NFR-01 to R-NFR-10) the rest of the dissertation is evaluated against. Each requirement carries a unique identifier, a description, a target value where measurable, and a pointer to the testing chapter that validates it.

A reader who is not interested in the requirements rationale can skip to Section 3.7 and Section 3.8 and read the requirement lists directly.

## 3.2 STAKEHOLDER ANALYSIS

Stakeholder analysis identifies the people and organisations who are affected by the system, or who affect the system. The motivation is to spot conflicting interests early and to capture requirements from each perspective before the design hardens around any single one. This section uses the Onion model, where stakeholders are placed in concentric rings according to their distance from the technical core.

### 3.2.1 THE ONION MODEL

The Onion model for this project has six rings.

The **innermost ring** is the system itself: the VisClick prototype. The ONNX detector, the EasyOCR layer, the rapidfuzz matcher, the Tk GUI, and the PyAutoGUI action layer.

The **second ring** is the **operational users**. Two distinct groups sit here. The first is the author, who runs the bot for evaluation and treats it as a research artefact. The second is the imagined power user — a developer or QA engineer who would use such a tool to automate repetitive desktop tasks. The two groups have meaningfully different requirements. The researcher wants observability above all else: overlay images, structured CSVs, verifiable verdicts. The power user wants reliability (zero crashes, predictable refusal-on-uncertainty) and convenience (a GUI rather than a CLI). The system addresses both by shipping a CLI for the researcher and a Tk GUI for the power user, layered over a common core.

The **third ring** is the **academic operational stakeholders**: the project supervisor (Pumudu Fernando) and the second marker. Their concerns are different again. They want a reproducible artefact, an honest evaluation, an academic novelty argument, and a dissertation properly structured against the RGU programme handbook.

The **fourth ring** is the **functional layer of downstream beneficiaries**. Three sub-groups belong here. QA and test-automation engineers who might adapt the project's code for production purposes. Accessibility users who could in principle benefit from a text-driven click bot when traditional input devices are not usable. And the research community — authors of any of the literature reviewed in Chapter 2 who might cite or extend this work, and future students inheriting the codebase.

The **fifth ring** is the **containing organisations**. Robert Gordon University is the degree-awarding body and the source of the dissertation's ethical-review framework, style guide, and assessment criteria. The Informatics Institute of Technology (IIT) is the partner institution. The author's employer is mentioned only because professional context informs some of the architectural choices. An automation tool that is interpretable and locally-deployable is more aligned with corporate compliance concerns than one that calls out to a cloud LLM.

The **outermost ring** is the **wider environment**. Microsoft is the platform owner — Windows 11 OS, the UI Automation framework, Notepad, File Explorer. Their decisions about which control libraries to ship and how to expose them through the accessibility tree have material effects on every measurement in Chapter 7. Google Colab is the compute provider for all training. Their Free-tier T4 quota is the binding budget constraint that shapes the data and experimental design. GitHub hosts the public artefact. The open-source community supplies the underlying libraries (Ultralytics for YOLOv8, JaidedAI for EasyOCR, the pywinauto and PyAutoGUI maintainers). Dataset providers sit here too — Deka et al. (2017) for RICO, Li et al. (2022a) for CLAY — as do the bad-actor groups whose existence motivates the social-impact discussion in Section 8.10.

### 3.2.2 STAKEHOLDER VIEWPOINTS

Each ring produces requirements. And the requirements sometimes conflict. The five viewpoints below capture the conflicts that mattered during design.

**The researcher's viewpoint** prioritises observability and reproducibility. Every prediction must be inspectable. Every result must be regeneratable from a script that can be re-run. This pushes the design towards verbose CSV logging, per-attempt overlay images, and CLI flags that fix randomness and dump intermediate state.

**The power user's viewpoint** prioritises a tight loop of action and feedback. Speed matters. Clarity of error messages matters. Refusal on uncertainty matters more than maximum coverage. This viewpoint produced R-FR-06 (refusal on low confidence), one of the harder-fought design decisions of the project.

**The academic stakeholder's viewpoint** prioritises an honest, defensible evaluation. This viewpoint is the reason the report explicitly cites both the inflated mAP figure (0.7176, against pseudo-labels) and the corrected one (0.0330, against hand-corrected ground truth). It is also the reason the negative test case T15 is kept in the headline TSR denominator rather than removed.

**The accessibility-user viewpoint** prioritises permission and refusal semantics over raw speed. A bot that confidently clicks the wrong thing is worse, for this group, than one that takes an extra second to be sure. This viewpoint reinforces R-FR-06 and motivates the human-in-the-loop verdict prompt in the evaluation harness.

**The platform-and-OS viewpoint** prioritises portability, or more precisely makes the project acknowledge its lack of portability. Windows 11 only. Multi-monitor support. DPI-scaling-aware coordinate handling. These constraints are captured in R-NFR-09 (compatibility) and discussed at length in Section 9.7.

Where the viewpoints conflict, the design rule is consistent: prefer the more conservative behaviour. When in doubt about whether to click, do not click; this is R-FR-06. When in doubt about which monitor to use, ask; this is the `--monitor` flag. When in doubt about whether a result should go into the CSV, log it with a `notes` field.

## 3.3 REQUIREMENT GATHERING TECHNIQUES

Four requirement-gathering techniques were used during the project, each in proportion to its cost-effectiveness on a single-developer MSc project.

**Literature review.** The single largest source of functional requirements is the existing literature reviewed in Chapter 2. The IVGocr architecture of Dardouri et al. (2024a) directly contributed R-FR-01 to R-FR-05 (capture, instruction, detection, matching, action). The published failure modes of classical baselines — UIED's argument that neither pure deep learning nor pure CV suffices on its own (Chen et al., 2020), Apple's published in-distribution-to-out-of-distribution drop (Zhang et al., 2021) — directly contributed R-FR-06 (refusal on uncertainty). The literature is the most reproducible requirement source for an academic project, because every requirement can be traced back to a publication.

**Self-as-stakeholder analysis.** The author is one of the operational users. Several requirements were derived from running early versions of the bot during the prototype phase. Multi-monitor coordinate confusion produced R-FR-07. Silent Tesseract failure produced part of R-NFR-04 (reliability). The difficulty of switching OCR engines from the CLI produced part of R-NFR-05 (usability). Self-as-stakeholder is a recognised method in agile and lean software engineering, though it is more often used in industrial projects than in dissertation work.

**Stakeholder interviews.** A short interview was conducted with the project supervisor early in the proposal phase to clarify the academic-stakeholder viewpoint described in Section 3.2.2. No formal transcript was kept, but the interview output is reflected in the proposal's research questions and is therefore the source of all four RQ-grounded requirements implicitly.

**Field observation of analogous systems.** The author used SikuliX, `pywinauto` and PyAutoGUI for short experimental sessions during the first month of the project. The observed failure modes from these sessions (template captures aging out, UIA `Name`s that do not match the visible labels, coordinate scripts that broke when DPI changed) were converted into the explicit failure-mode list in Section 8.4, and into the comparison baselines in Chapter 7. This is, in effect, the requirement-gathering technique that justifies the lightweight stance. The requirements *not* met by existing tools are the most concrete justification for the new tool.

A fifth technique that the reference report at IIT/RGU uses but this project does not is **stakeholder questionnaires**. Questionnaires are sensible for projects with non-overlapping target users. For a developer-tooling artefact at MSc scale with the author as the primary user, the cost of designing and distributing a questionnaire would have exceeded the benefit.

## 3.4 METHODOLOGY FOR OBTAINING DATASETS

The data-engineering side follows a three-tier methodology dictated by the data-availability constraints reviewed in Section 2.2.

**Tier 1: public source-domain corpora.** Three publicly available datasets are used as the source domain: RICO (Deka et al., 2017), CLAY (Li et al., 2022a), and VINS. Acquisition is straightforward — a download from the respective project pages and a checksum check — but the cleaning and class-collapse work is non-trivial and is documented in Chapter 6. The combined corpus is the 6-class "Zenodo unified bundle" of approximately 9,646 screens used in the source-training notebook.

**Tier 2: captured target-domain unlabelled corpus.** The proposal commits to roughly 2,000 unlabelled desktop screenshots captured from 10 to 15 applications. The capture methodology is implemented in `scripts/auto_capture_corpus.py` and uses `mss` for the screen grab plus the foreground-window title for the per-image filename. The script is parameterised so the eventual corpus covers the in-the-wild variability the bot encounters. As of submission this corpus is in active accumulation.

**Tier 3: hand-curated target-domain labelled corpus.** A small set of hand-corrected screens with 356 ground-truth boxes serves as the gold-standard test pool. Annotation methodology follows the CVAT shape-and-label convention used in the wider literature: rectangular bounding boxes only, no rotated boxes, no segmentation masks. Class labels are restricted to the 6-class taxonomy `{button, text, text_input, icon, menu, checkbox}`. Annotators (in practice, the author alone) follow a written guideline document that mirrors the conventions used in the CLAY release notes.

A practical note about scale. The hand-corrected pool is small by deliberate choice, not by oversight. Building a 100-image labelled set at a single-developer MSc cadence is hard. Building one with high-quality boundaries on dense Windows 11 toolbars is harder. The project's response is layered: a small hand-corrected pool for fine-grained per-element recall, supplemented by the ScreenSpot benchmark (Cheng et al., 2024) for held-out per-instruction grounding. Both protocols are reported side by side in Chapter 7 so the reader can see the limitation directly rather than inferring it.

The three tiers feed three different experimental purposes. Tier 1 is the source-domain training set. Tier 2 is the unlabelled target corpus needed for SSP+FT and UDA. Tier 3 is the labelled target test set used for evaluating every adaptation method, and is also the training source for the few-shot fine-tuning experiment.

## 3.5 USE CASE DIAGRAMS (UML)

The system supports six use cases, four of which are user-facing and two of which are internal to evaluation.

[FIGURE 7: UML use case diagram for VisClick.
Source: `reports/figures/ch3_use_cases.png` (to be produced; one actor "User", six use cases UC-01 to UC-06 with `<<include>>` relationships where appropriate).
Caption: Use case diagram for the VisClick prototype. UC-01 to UC-04 are user-facing; UC-05 and UC-06 are run during evaluation. Each use case maps to one or more functional requirements in Section 3.7.]

The six use cases:

- **UC-01: Click a labelled element.** The user provides a text instruction; the system captures the screen, detects elements, matches the instruction, and clicks the chosen element.
- **UC-02: Refuse a click on low confidence.** The user provides an instruction for which no high-confidence target exists; the system reports a structured failure rather than clicking.
- **UC-03: Select a specific monitor.** The user selects which monitor the bot should operate on, via either the CLI flag or the GUI dropdown.
- **UC-04: Inspect a prediction overlay.** The user opens the saved overlay PNG for any past click to verify what the bot did.
- **UC-05: Run a baseline evaluation.** The evaluator runs `scripts/run_baselines.py` to evaluate one or more methods across the canonical task suite.
- **UC-06: Generate result tables and figures.** The evaluator runs the analysis scripts to regenerate the report's tables and figures from the per-attempt CSV.

## 3.6 USE CASE DESCRIPTIONS

Each of the four user-facing use cases is described below at a more practical level than the UML. UC-05 and UC-06 are evaluation tooling and are documented in Chapter 6 rather than here.

**UC-01: Click a labelled element.**

- *Primary actor:* End user (developer or power user).
- *Pre-condition:* The bot is launched, the model weights are loaded, and the target monitor is selected.
- *Main success flow:* (1) User types an instruction such as "click Save" into the GUI. (2) User presses Run or hits Enter. (3) The system pauses 3 seconds, allowing the user to switch focus to the target window. (4) The system captures the configured monitor. (5) The detector emits N candidate boxes. (6) The OCR layer reads the text on each box. (7) The matcher selects the best-fitting box above the similarity threshold. (8) The action layer moves the cursor to the box centre and clicks. (9) The system saves the overlay PNG and writes the CSV row.
- *Alternative flow:* If no candidate exceeds the similarity threshold, the system follows UC-02 instead of clicking.
- *Post-condition:* The targeted element has received a single left-click. The action has been logged.

**UC-02: Refuse a click on low confidence.**

- *Primary actor:* End user.
- *Pre-condition:* As UC-01.
- *Main success flow:* (1) User types an instruction. (2) System captures and detects as in UC-01. (3) Matcher computes the best-fitting box, but its similarity score is below the threshold (`min_text_similarity = 60` in the current build). (4) System emits a structured `FAIL: cannot find <target>` message. (5) System still saves the overlay PNG (with no click marker) and writes a CSV row with verdict `refused`.
- *Post-condition:* No click was issued. The decision is logged.

**UC-03: Select a specific monitor.**

- *Primary actor:* End user on a multi-monitor setup.
- *Pre-condition:* The system has detected more than one monitor at start-up.
- *Main success flow:* The user selects the target monitor from the GUI's dropdown (or passes `--monitor <id>` to the CLI). The system queries `mss.monitors` for the selected index, recovers the `(left, top)` offset, and uses that offset throughout the subsequent capture-detect-match-click flow.
- *Post-condition:* All subsequent clicks issued by the bot land on the chosen monitor regardless of where the GUI window itself is sitting.

**UC-04: Inspect a prediction overlay.**

- *Primary actor:* Researcher or end user reviewing past behaviour.
- *Pre-condition:* The bot has previously processed at least one instruction.
- *Main success flow:* The user opens the saved overlay PNG. The overlay shows the detected boxes coloured by class, the chosen box highlighted, the click point marked with a crosshair, and (when relevant) the OCR text overlaid above each box. The user can confirm or refute the bot's decision visually.
- *Post-condition:* No state change. The use case is purely diagnostic.

## 3.7 FUNCTIONAL REQUIREMENTS

The functional requirements R-FR-01 to R-FR-09 are listed in Table 2. Each requirement carries a unique identifier, a description, a priority, the use cases it serves, and the section of the testing chapter that validates it. The pass-rate column reports the headline empirical result already measured against the requirement; the exact computation is in Chapter 7.

**Table 2: Functional requirements.**

| ID | Requirement | Description | Priority | Use cases | Test section | Status |
|----|-------------|-------------|----------|-----------|--------------|--------|
| R-FR-01 | Screen Capture | The system shall capture a screenshot of the user-selected monitor at native resolution, in the virtual-desktop coordinate space. | Essential | UC-01, UC-03 | Section 7.3.1 | FULL: 15/15 on T01-T15 |
| R-FR-02 | Text Instruction Input | The system shall accept a free-form text instruction via CLI flag or GUI text box. | Essential | UC-01, UC-02 | Section 7.3.1 | FULL: 15/15 |
| R-FR-03 | Element Detection | The system shall detect candidate UI elements of types `{button, text, text_input, icon, menu, checkbox}` on the captured screenshot. | Essential | UC-01 | Section 7.2 | FULL: 15/15 emit ≥1 detection |
| R-FR-04 | Instruction-to-Element Matching | The system shall match the user instruction to one detected element using fuzzy OCR text similarity, with a class-aware bonus, and shall fall back to full-image OCR when no per-box candidate exceeds the threshold. | Essential | UC-01 | Section 7.3.1, Section 8.2 | FULL: 11/14 PASS on positives |
| R-FR-05 | Action Execution | The system shall move the mouse cursor to the centre of the chosen element and execute a single left-click. | Essential | UC-01 | Section 7.3.1 | FULL: 11/14 verdict |
| R-FR-06 | Refusal on Low Confidence | The system shall refuse to click when no candidate exceeds the similarity threshold, and shall emit a structured failure message. | Essential | UC-02 | Section 7.3.1 | PARTIAL: 0/1 on T15; planned threshold fix |
| R-FR-07 | Multi-Monitor Support | The system shall operate correctly across virtual-desktop coordinate spaces on multi-monitor setups, with an explicit monitor selector. | Important | UC-03 | live demo log | FULL: verified on 3440×1440 + 1920×1080 stacked layout |
| R-FR-08 | Visual Feedback | The system shall render an annotated overlay PNG of every prediction (detected boxes, chosen element, click marker, OCR text) for human verification. | Important | UC-04 | Section 7.3.1 | FULL: 60/60 overlays |
| R-FR-09 | Per-Attempt Logging | The system shall log per-attempt fields (instruction, capture path, predicted xy, verdict, latency, method, is_negative, notes) to a CSV file for evaluation. | Important | UC-05 | `reports/tables/baseline_results.csv` | FULL: 60/60 rows |

The classification "Essential" vs "Important" follows the MoSCoW convention. An Essential requirement must be met for the system to be considered fit for purpose. An Important requirement is needed for the system to be considered fit for evaluation, but is not on the critical functional path.

## 3.8 NON-FUNCTIONAL REQUIREMENTS

The non-functional requirements are quantitative wherever possible. Each row in Table 3 records the target value, the measured value, the source of the measurement, and a status.

**Table 3: Non-functional requirements.**

| ID | NFR | Target | Measured | Source | Status |
|----|-----|--------|---------|--------|--------|
| R-NFR-01 | Accuracy (TSR) | ≥ 50 % on T01-T15 | 73.3 % | `baseline_summary.csv` row `visclick` | FULL |
| R-NFR-02 | Latency | p95 ≤ 15 s per click attempt | 14.8 s p95 / 8.05 s median | `nfr_performance.csv` row `visclick` | FULL (just) |
| R-NFR-03 | Memory footprint | Peak RSS ≤ 2 GB during a 15-task run | PARTIAL | gap D-11 | PARTIAL |
| R-NFR-04 | Reliability | Zero crashes during 60-attempt evaluation | 0 crashes | run log 6-7 May 2026 | FULL |
| R-NFR-05 | Usability | Single-window Tk dialog; keyboard shortcuts for Pass/Fail/Skip | implemented in `scripts/run_baselines.py::_verdict_dialog_tk` | source review | FULL (single-reviewer) |
| R-NFR-06 | Maintainability | Object-oriented modular package (`visclick.{capture, detect, ocr, match, act, bot, gui}`) built around 8 substantive classes (`Capture`, `Detector`, `OCREngine`, `Matcher`, `Actor`, `Bot`, `BotResult`, `VisClickApp`) plus 2 PyTorch subclasses in the training script; composition-over-inheritance; every module PEP-8 clean | 8 pipeline / GUI classes + 2 training subclasses, ~1,850 LoC total, `ruff check` clean, class diagram in Figure 12A | source review + Figure 12A | FULL |
| R-NFR-07 | Extensibility | Two extension seams. (i) New baseline methods plug in by implementing `predict(image_rgb, instruction) -> BaselineResult`. (ii) Any of the five pipeline collaborators can be replaced by dependency injection through `Bot.__init__(capture=, detector=, ocr=, matcher=, actor=)` without touching the orchestrator body. | 4 baseline adapters + injectable-collaborator constructor | `scripts/baseline_*.py`; `src/visclick/bot.py::Bot.__init__` | FULL |
| R-NFR-08 | Security & Privacy | No off-machine I/O during inference; no telemetry; no credentials handled | verified by `rg 'requests|urllib|http' src/visclick/` | source review | FULL |
| R-NFR-09 | Compatibility | Windows 11 supported; multi-monitor verified | Windows 11 + 3440×1440 + 1920×1080 PASS | live demo | PARTIAL (Windows-only by design) |
| R-NFR-10 | Scalability | Pipeline complexity scales linearly in #candidates per screenshot | per-box OCR is O(N); ceiling ≈ 300 boxes/screenshot | analytical | PARTIAL |

The classification of each NFR as Essential, Important, or Optional follows the same MoSCoW convention used for FRs. Accuracy, latency, reliability, security, and compatibility are Essential. The rest are Important or Optional. None of the NFRs are marked Failed. The PARTIAL items (R-NFR-03, R-NFR-09, R-NFR-10) are timeline matters or scope-deliberate choices, not fundamental capability gaps.

## 3.9 CHAPTER SUMMARY

The requirements above are the contract the rest of the dissertation is evaluated against. They were derived from four requirement-gathering techniques (literature, self-as-stakeholder, supervisor interview, field observation of analogous systems) and from a six-ring Onion stakeholder model that captured viewpoint conflicts before they became design conflicts. Nine functional requirements (R-FR-01 to R-FR-09) and ten non-functional requirements (R-NFR-01 to R-NFR-10) are stated explicitly, each with an identifier, a target, and a pointer to the test section that validates it. The structure of the requirements list deliberately mirrors the structure of the testing chapter, so a marker can audit any individual claim by chasing a single identifier from Section 3.7 or Section 3.8 down into Chapter 7.

The next chapter, Chapter 4, describes the project management approach: the research methodology, the software methodology, the risk register, and the four-phase project plan.

---

# CHAPTER 04 – PROJECT MANAGEMENT

## 4.1 CHAPTER OVERVIEW

This chapter explains how the project was run. It begins with the research methodology — the philosophical and procedural framework that determined the kind of evidence the project chased. It moves on to the software design methodology and the software development methodology. Both constrain how a single-developer MSc project should be structured on a finite budget. The project management methodology is described next. The risk register is then made explicit. It captures, in a forward-looking form, the issues encountered during execution together with the mitigations that resolved them. The chapter closes with the project plan in Gantt form, with reference to the four-phase operational structure inherited from the proposal.

A reader interested only in the empirical findings can skip Chapter 4 and pick up at Chapter 5 (Design). The contents here are required by the RGU MSc dissertation rubric, and they perform a real function: they tell a marker which research-philosophical commitments the rest of the dissertation expects to be evaluated against.

## 4.2 RESEARCH METHODOLOGY

The project is in the design-science research (DSR) tradition (Hevner et al., 2004). DSR is appropriate when the research output is a new artefact intended to solve a real-world problem, and when the contribution is evaluated by demonstrating that the artefact does so. The artefact in this case is the VisClick prototype together with the cross-domain adaptation framework that produces its detector. The output is evaluated by measuring the prototype's performance against three quantitative metrics (mAP, CPV, TSR), and against the three classical baselines that constitute the practical comparison set.

A purely positivist methodology was considered and rejected. A positivist framing would treat the project as a hypothesis test — for example, "training on CLAY transfers well to Windows 11" as a falsifiable hypothesis — and would seek a single binary answer. The project's actual evidence base contains internally contradictory observations. The detector does badly on hand-corrected ground truth, yet the end-to-end TSR is acceptable. The OCR fallback rescues the detector but is also the latency bottleneck. That kind of evidence is better served by DSR's "build, evaluate, learn" loop than by a single null-hypothesis test.

A purely interpretivist methodology was also considered and rejected. An interpretivist framing would treat the system's behaviour as a phenomenon to be understood through qualitative analysis — interviews with users, observation of task performance. The project does have a small qualitative-evaluation slot, but the primary evidence is quantitative. The qualitative layer is supplementary rather than central.

The DSR framing has practical consequences for the rest of the dissertation. It justifies a multi-method evidence structure (Chapter 7 reports both quantitative metric numbers and qualitative failure-mode descriptions). It justifies an iterative narrative in which an early result (the 22-fold mAP collapse from auto-label evaluation to hand-corrected ground truth) directly motivates a later methodological change (hand-correcting more test data). And it justifies the explicit "build the artefact, evaluate the artefact, learn from the artefact" structure of Chapters 5 to 9.

## 4.3 SOFTWARE DESIGN METHODOLOGY

The system was designed against three principles, each carrying through from the literature reviewed in Chapter 2.

**Modularity.** The system is decomposed into seven Python packages under `src/visclick/` (`capture`, `detect`, `ocr`, `match`, `act`, `bot`, `gui`). Each package has a single responsibility and a small public surface, so any one component can be replaced without touching the others. This is the architectural choice that made it possible to plug in three classical baselines and the VisClick full pipeline as four interchangeable `predict()` implementations in the same evaluation harness. Modularity is also what allows the dissertation to make the comparison chart in Section 7.4 a fair one. The four methods share the screenshot capture, the verdict-collection harness, and the per-attempt logging schema. Only the perception-and-grounding code differs.

**Reproducibility.** Every numerical claim in the report is regeneratable from a script in the public repository, against a result table on disk, with a commit hash documented in the data form. The supporting convention is that every notebook cell which produces a report number prints a marker line identifying the report section it serves. The same principle drives the explicit version-control of the desktop screenshot corpus and the ONNX detector weights inside the repository, rather than only on cloud storage.

**Refusal on uncertainty.** A click bot that issues a confident wrong click is worse than one that issues an honest failure. This principle is captured in R-FR-06. It is the architectural reason the matcher has a `min_text_similarity` threshold rather than always returning the highest-scoring candidate.

A separate architectural pattern worth flagging is the **pre-flight probe**. The OCR layer exposes an `ocr_status()` function that runs at start-up and prints a tick or cross for each backend (EasyOCR, Tesseract, falling back to a pure-Python OCR). The detector layer exposes an equivalent `detect_status()` for ONNX model loading. The first time any of these probes fails, a `_warn_once()` helper prints the underlying error, the configured path, and three concrete fixes. This pattern was introduced after a silent Tesseract failure during the live demo and has been propagated to every external dependency in the stack. It is one of the strongest practical lessons of the project and is recorded as such in Section 9.3.

## 4.4 SOFTWARE DEVELOPMENT METHODOLOGY

The development process is best described as an agile/waterfall hybrid. The four-phase project plan from the proposal is essentially a waterfall structure: data engineering, then modelling, then prototype, then evaluation. Inside each phase, the actual day-to-day work was iterative. The observation log records the cycles of "try, hit a wall, document the wall, fix the wall, move on" that drove progress through each phase.

The agile elements are concrete. Continuous integration is provided by Git, with commits at a granularity that maps individual problems to individual fixes (the commit log includes entries such as `fix(make_prototype): load tasks from T01_T20.json tasks array`). Backlog management is provided by the Phase L checklist in `docs/PHASE_WORKLOG.md`. The dissertation and the working code consult it in lock-step. Retrospective is performed at the end of each phase: the observation log in the data form serves as the retrospective output, with each O-numbered entry describing what happened and what it taught the project.

The waterfall elements are equally concrete. Phase ordering was preserved. Data engineering really did precede model training, model training really did precede the prototype, and the prototype really did precede the evaluation. No phase was started before the prior phase's deliverable existed. This is more rigid than a pure agile project would be, but it is appropriate for a research project where each phase's output is a measurement that the next phase's design depends on.

The choice of an agile/waterfall hybrid over pure agile or pure waterfall was made for one reason. A single-developer MSc project does not have the team structure that justifies a pure agile process — no scrum, no stand-ups, no separate product-owner role. But it also cannot afford the inflexibility of pure waterfall. A single mid-project disconnect, like the auto-label evaluation crisis, requires the freedom to re-scope upstream phases without throwing out the whole plan. The hybrid is what allowed the auto-label evaluation crisis to be turned into a controlled re-evaluation rather than into a project failure.

## 4.5 PROJECT MANAGEMENT METHODOLOGY

Project tracking used two artefacts. The first is a static Gantt chart at the level of the four phases (Figure 8). The second is the rolling Phase L checklist in `docs/PHASE_WORKLOG.md`, which is more granular and is updated continuously.

[FIGURE 8: Project Gantt chart over the 12 months of the MSc.
Source: `reports/figures/ch4_gantt.png` (to be produced; suggested format is Phase 1 over Months 1-3, Phase 2 over Months 4-7, Phase 3 over Months 8-9, Phase 4 over Months 10-12, with overlaps at phase boundaries to indicate continuous work).
Caption: Twelve-month project plan over the four operational phases. Phase boundaries are deliberately drawn with overlap; in practice each phase's documentation continued while the next phase's experiments began.]

The two artefacts have different update cadences. The Gantt is updated at most monthly and is treated as a contract between the author and the supervisor. The Phase L checklist is updated continuously and is treated as the working memory of the project. Every commit to the repository typically toggles at least one `[ ]` to `[x]`.

Time accounting was kept informally. The detailed plan recorded an original time budget of approximately 120 hours over twelve weeks (the proposal's reference cadence). The actual time spent is significantly higher and is not formally logged. For a future-work entry, an honest answer to "how long did this dissertation take" would be in the region of 200 to 250 hours.

## 4.6 RISK MITIGATION PLAN

The risk register is a forward-looking transformation of the observation log. Each risk has a probability, an impact, a mitigation, and a status. Table 4 mirrors the data form's Section 17 but is reproduced here for completeness.

**Table 4: Risk register.**

| ID | Risk | Source | Prob | Impact | Mitigation | Status |
|----|------|--------|:----:|:------:|------------|--------|
| RR-01 | Pseudo-label evaluation overstates accuracy | observation log | High | High | Hand-correct test images; report both auto-label and hand-corrected mAP | Mitigated |
| RR-02 | Source-domain training distribution does not generalise to Win11 native | observation log | High (confirmed) | High | OCR text-grounding fallback; recall-ceiling acknowledged; Phase 4 planned | Mitigated |
| RR-03 | Silent dependency failure (Tesseract not on PATH) | live demo | Med | High | Startup probe `ocr.ocr_status()`; `_warn_once()` helper | Mitigated |
| RR-04 | Multi-monitor virtual-desktop coordinate confusion | observation log | High | High | `(left, top)` offset propagated through `act.click_box`; `--monitor` flag | Mitigated |
| RR-05 | Confident wrong action on negative case | observation log | Med | High | `min_text_similarity` threshold; planned raise from 60 to 75 | Open |
| RR-06 | OCR latency dominates total wall-clock | NFR profile | Certain | Med | Detector-first short-circuit (skip OCR on confident classes) | Open |
| RR-07 | Colab Free disconnect mid-training | training log | Med | Med | `last.pt` per-epoch; resume-from-disconnect built in | Mitigated |
| RR-08 | Drive FUSE I/O instability on directories with 10k+ files | observation log | High | Med | Retry + shell `find` fallback; cached listings | Mitigated |
| RR-09 | Drive FUSE `stat` cache lags `readdir` cache | observation log | Med | High | Set-of-stems via `find` retry; never `os.path.isfile()` on Drive | Mitigated |
| RR-10 | Auto-labeller class collapse (menu/checkbox ≈ 0) | observation log | Med | Med | Hand-correct ground truth; class top-up | Open |
| RR-11 | Licence / IP concerns on dataset use | design review | Low | High | All datasets public; AGPL inherited from Ultralytics; documented in Section 8.10 | Mitigated |
| RR-12 | Personal-data leakage from desktop seed screenshots | design review | Low | High | All seed PNGs manually reviewed before commit | Mitigated |
| RR-13 | Bot misuse for click-fraud or automated account creation | LEPSI review | Low (research scope) | Med | Human-in-the-loop verdict step; no headless service mode shipped | Monitored |
| RR-14 | Labelled-data budget falls below the proposal's nominal target | small-data triage | High (confirmed) | High | Layered response: auto-labelled seed → hand-corrected ground truth → ScreenSpot import for per-instruction grounding → passive unlabelled accumulation. Each tier is reported alongside its protocol caveat so the dissertation's claims stay calibrated to the data actually held. | Mitigated |

Three observations about the register are worth pulling out for prose.

First, **the highest-impact risks are all data-quality risks**, not modelling or deployment risks. RR-01, RR-02, RR-10 and RR-14 between them account for the project's biggest empirical findings: the auto-label vs hand-correct mAP gap, the recall-bounded source-domain backbone, the icon class-distribution skew, and the small-data triage that determined which mAP and CPV protocols the dissertation could report. Each is a reminder that the modelling chain is no stronger than its weakest data link.

Second, **most of the Open risks have costed mitigations**. RR-05 (refusal threshold), RR-06 (OCR latency), and RR-10 (class top-up) all have a documented work item that would move them from Open to Mitigated. Whether those work items are completed before submission is a separate triage call.

Third, **the only Low-probability risk that remains Monitored is RR-13** (bot misuse). The probability is low because the project ships an interactive verdict step by default and no headless service mode. The risk is kept on the register because the *category* — vision-driven UI automation can be misused at the systemic level — does not disappear merely because this particular prototype mitigates it. The social-impact discussion in Section 8.10 takes the category seriously.

## 4.7 PROJECT PLAN

The project plan is the four-phase structure inherited from the proposal. The Gantt-equivalent rendering is in Figure 8 above; the text below makes each phase's scope and deliverable explicit.

**Phase 1: Data engineering and baseline establishment (Months 1-3, completed).** Public mobile UI datasets were acquired and consolidated into the 6-class unified bundle. A baseline detector was trained on the unified bundle. A small desktop seed set was captured and auto-labelled. The hand-corrected test pool was assembled. The transfer-learning ablations were run on Colab Free, and the headline desktop fine-tune was selected. Three classical baselines (template, OCR-only, `pywinauto`) were implemented and evaluated on the 15-task suite. **Deliverable D1 (baseline performance report) is the content of Section 7.2 of this dissertation.**

**Phase 2: Model adaptation experiments (Months 4-7, partially completed).** The DETR backbone source-side is done; the DETR target-side is pending. The few-shot sample-efficiency curve is done. SSP+FT and the two UDA experiments (Adaptive Teacher and SHOT) are the outstanding pieces. These are listed as gaps D-01 to D-04 in `docs/Final_Report_GAPS.md`. **Deliverable D2 (ablation study and model-comparison report) is partially complete; the completed sub-experiments are reported in Section 7.2 and Section 7.3.**

**Phase 3: Prototype integration (Months 8-9, completed).** The VisClick prototype is operational on Windows 11 with a CLI and a Tk GUI. The IVGocr architecture is implemented end-to-end. The interactive evaluation harness supports the four-method comparison and the verdict-collection dialog. **Deliverable D3 (functional prototype) is the artefact in the public repository at https://github.com/HiranMadhu/visclick.**

**Phase 4: Evaluation and thesis composition (Months 10-12, ongoing).** The 15-task evaluation is complete. TSR, latency, and failure-mode analysis are reported in Chapter 7. The qualitative third-party evaluation and the memory profiling are outstanding. **Deliverable D4 (final evaluation report and packaged code) is the dissertation in front of the reader.**

The phase boundaries on the Gantt are deliberately drawn with overlap. In practice, Phase 4 (thesis writing) began during Phase 3 (prototype integration), because writing tends to surface gaps in measurement that the prototype then has to be re-run to fill.

## 4.8 CHAPTER SUMMARY

The project follows a design-science research methodology, with a modular, reproducible, refusal-on-uncertainty software design, executed under an agile/waterfall hybrid development process. The risk register captures fourteen risks distilled from the observation log: most are mitigated, three are open with costed plans, and one is monitored. The project plan is the four-phase structure inherited from the proposal. Phase 1 and Phase 3 are complete, Phase 2 is partially complete with the outstanding work listed in `docs/Final_Report_GAPS.md`, and Phase 4 is ongoing.

The next chapter, Chapter 5, presents the design: the high-level architecture, the block diagram and flow chart of the runtime, the research design, and the wireframes for the prototype GUI.

---

# CHAPTER 05 – DESIGN

## 5.1 CHAPTER OVERVIEW

This chapter is the design half of the build-then-evaluate loop. It begins with the research design, which lays out the experimental matrix the rest of the dissertation populates. It moves on to the system architecture, presented as a block diagram in Section 5.3 and as a per-instruction flow chart in Section 5.4. The module-level design is presented next: which Python package contains which logical responsibility, and how the modules connect. The GUI side is covered in Section 5.6 with wireframes. The storage design (file layout, CSV schemas, ONNX weights) is in Section 5.7. The chapter closes with the algorithm design for the two non-trivial components: the fuzzy text-plus-class matcher in `visclick.match`, and the refusal rule that implements R-FR-06.

The design described in this chapter is what the rest of the project implements. Chapter 6 walks through the code in the order this chapter lays out. The empirical results in Chapters 7 and 8 measure the implementation against the targets stated in Chapter 3. A reader who only wants the operational picture can read Section 5.3 and Section 5.4 and skip the rest.

## 5.2 RESEARCH DESIGN

The research design is an experimental matrix that crosses three axes. The first axis is **architectural family**: YOLOv8s and DETR-R50. The second axis is **adaptation method**: source-only zero-shot (M0), few-shot fine-tune of the head (M2), self-supervised pre-training followed by fine-tune (SSP+FT), and unsupervised domain adaptation (Adaptive Teacher and SHOT). The third axis is **labelled-target budget**: a small range of `k` values for the methods that use any labelled target data.

A fully populated matrix would contain 2 × 5 × 5 = 50 cells. But many of those cells degenerate — zero-shot does not depend on `k`, UDA does not depend on `k` in the same way. The reduced matrix the project actually executes is shown in Table 5. The cells marked DONE are reported in Chapter 7. The remaining cells are listed in gaps D-01 to D-05 of `docs/Final_Report_GAPS.md` and would close the matrix to its full proposal-committed shape.

**Table 5: Experimental matrix.**

| Backbone | Method | k | Status |
|----------|--------|----:|--------|
| YOLOv8s | M0 zero-shot (CLAY → desktop) | n/a | DONE |
| YOLOv8s | M1 COCO direct (control) | n/a | DONE |
| YOLOv8s | M2 head fine-tune | 50 | DONE (headline detector) |
| YOLOv8s | M3 frozen layers 22 | 50 | DONE (ablation) |
| DETR-R50 | source-domain training | n/a | DONE (D-01 source-side, 2 June 2026) |
| DETR-R50 | M0 zero-shot on target | n/a | PENDING (D-01 target-side) |
| DETR-R50 | M2 head fine-tune | 50 | PENDING (D-01 target-side) |
| YOLOv8s | M2 few-shot curve | 1, 2, 4, 8 | DONE (D-05, 3 June 2026) |
| YOLOv8s | SSP + M2 | small-k | PENDING (D-02) |
| YOLOv8s | UDA Adaptive Teacher | n/a | PENDING (D-03) |
| YOLOv8s | UDA SHOT | n/a | PENDING (D-04) |

The end-to-end TSR evaluation is run only against the single headline detector (YOLOv8s M2 fine-tune) rather than against every cell. The rationale is twofold. First, the prototype's downstream behaviour depends on detection plus OCR plus matching plus action, so a fair end-to-end comparison across detectors would require re-running the full 15-task suite for each adaptation cell — roughly an hour of human verdict-collection per cell, which scales poorly. Second, RQ4 (end-to-end practicality) is about whether *one* viable adapter can be turned into a working bot, not about which of several adapters does so best end-to-end. The "best" adapter is identified by mAP and CPV on the labelled test set; only that adapter gets the end-to-end treatment.

The classical baselines (template, OCR-only, `pywinauto`) sit outside the adaptation matrix because they have no adaptation parameter to vary. They are evaluated only end-to-end on the same 15-task suite, with the comparison being against the VisClick full pipeline.

## 5.3 SYSTEM ARCHITECTURE

The system architecture is captured in two diagrams. Figure 9 is the static block diagram: boxes are logical components, arrows are data dependencies. Figure 10 is the dynamic flow chart, tracing a single instruction from text input to clicked element.

[FIGURE 9: Block diagram of the VisClick system.
Source: `reports/figures/ch5_block_diagram.png` (to be produced; regenerate from the Mermaid source in `docs/VisClick_Report_Data_Form.md` Section 18.1 via mermaid-cli).
Caption: Block diagram of VisClick. The capture, detect, OCR, match and act components are each a Python module under `src/visclick/`. Logging components live in `scripts/run_baselines.py`.]

The architecture has six logical layers. Each layer is realised as exactly one Python module under `src/visclick/`, with one small exception (logging is handled at the script level rather than as a dedicated module).

**Layer 1: User input.** Either a text instruction from the GUI (`visclick.gui`) or a `--target` argument from the CLI (`visclick.__main__`).

**Layer 2: Screen capture.** A wrapper over `mss` that handles multi-monitor coordinate offsets (`visclick.capture`). The capture layer returns an RGB numpy array and the `(left, top)` offset of the chosen monitor.

**Layer 3: Detection.** An ONNX wrapper that loads the trained YOLOv8s weights and emits a list of `(class_id, confidence, xyxy)` tuples (`visclick.detect`). The wrapper supports both an `onnxruntime` backend (the default, CPU only) and an Ultralytics `model.predict()` backend (used during training and during ablations).

**Layer 4: OCR.** A two-mode OCR layer (`visclick.ocr`). The per-box mode runs EasyOCR on each detected bounding box and returns the most confident text string. The full-image mode runs EasyOCR on the entire screenshot and returns a list of `(text, bounding_box, confidence)` tuples for use in the OCR fallback path. The module exposes the `ocr_status()` probe described in Section 4.3.

**Layer 5: Matching.** A fuzzy matcher built on `rapidfuzz` (`visclick.match`). The matcher's `best_box()` function takes the user instruction, the per-box OCR text, and the detection class IDs, and returns the index of the best-matching box together with its score.

**Layer 6: Action.** A PyAutoGUI wrapper that handles the virtual-desktop offset correction (`visclick.act`). The wrapper exposes `click_box(box, offset=(left, top))` and `move_to_box(...)`.

Above the six layers sits the orchestrator `visclick.bot`, which composes the layers into a single `run_instruction()` entry point. The orchestrator is what both the CLI and the GUI invoke. It is also what the evaluation harness's VisClick baseline calls.

The deliberate property of this design is that no two layers share state. The capture layer hands an image to the detect layer. The detect layer hands a box list to the OCR layer. The OCR layer hands text to the matcher, and so on. This is what makes each layer independently testable. It is also what made the four-baseline comparison possible without duplicating code.

## 5.4 PROCESS FLOW

The flow chart in Figure 10 makes the runtime behaviour explicit. The single decision point worth pulling out for discussion is the OCR-fallback decision at the matcher.

[FIGURE 10: Process flow chart for a single click instruction.
Source: `reports/figures/ch5_flowchart.png` (to be produced; regenerate from the Mermaid source in `docs/VisClick_Report_Data_Form.md` Section 18.2).
Caption: Per-instruction flow chart. The decision diamond at the matcher determines whether the detector's top candidate is accepted (Yes), whether the full-image OCR fallback is invoked (No, retry), or whether the system refuses to click (No, refuse).]

The flow has six stages. **Capture** acquires the screenshot from the chosen monitor. **Detect** produces up to N candidate boxes; if N = 0 the system falls through to the OCR fallback path. **Per-box OCR** annotates each box with its text. **Match** computes a fuzzy similarity score between the user instruction and each box's text, with a small bonus added for boxes whose detected class matches the instruction's likely intent (a "click Save" instruction prefers a `button` over a `text`). **Decision** compares the top score against `min_text_similarity` (currently 60 on a 0-100 scale). If the score clears the threshold, the system proceeds to **Action**. If it does not, the system enters the **fallback** branch, runs full-image OCR, and re-matches the instruction against every recognised text region. If the fallback also fails to clear the threshold, the system **refuses**.

The fallback is the architectural compromise that pays for the source-domain detector's limited recall on Windows 11 native dialogs. Without the fallback, the bot would refuse on roughly half the test tasks because the detector simply does not see the target box. With the fallback, the bot recovers the visible-text-but-no-box cases at the cost of a roughly 6-second latency penalty. The cost-benefit is recorded in Section 7.3.2 and is one of the two design trade-offs that Chapter 8 returns to.

## 5.5 MODULE DESIGN

The module diagram below makes the per-package responsibilities explicit. Each module's public surface is small — between one and four exported functions or classes. The module-level boundaries are also the unit-test boundaries: each module has at least one corresponding `tests/test_<module>.py` file.

```text
src/visclick/
  __init__.py          # package re-exports
  __main__.py          # CLI entry point: python -m visclick.bot ...
  capture.py           # mss wrapper; multi-monitor offset
  detect.py            # ONNX YOLOv8s wrapper; Ultralytics fallback
  ocr.py               # EasyOCR per-box + full-image; status probe
  match.py             # rapidfuzz best_box; class-aware bonus
  act.py               # PyAutoGUI click_box; offset correction
  bot.py               # orchestrator: run_instruction()
  gui.py               # Tk GUI; monitor selector; verdict logging
  utils.py             # logging helpers; _warn_once
scripts/
  run_baselines.py        # 4-method evaluation harness
  analyse_baselines.py    # TSR computation, p50/p95 latency
  baseline_visclick.py    # VisClick BaselineResult adapter
  baseline_template.py    # cv2.matchTemplate adapter
  baseline_ocr_only.py    # OCR-only adapter
  baseline_pywinauto.py   # accessibility-tree adapter
  auto_capture_corpus.py  # corpus expansion
  make_prototype_figures.py # report figure generation
  run_nfr.py              # NFR latency + memory profiling
```

The module dependency graph is intentionally a directed acyclic graph: `bot` depends on `capture, detect, ocr, match, act`; the five depended-on modules are mutually independent; `gui` depends on `bot`. The acyclic property is what lets the four baselines reuse `capture` and `act` without dragging in the detector. A circular dependency would have collapsed this composition.

### 5.5.1 CLASS DIAGRAM

The module view above answers "what files exist and how do they depend on each other". The class view in Figure 12A answers a different question: "which objects hold state, and what are the collaboration contracts between them". The two views are complementary and both are needed because the system is deliberately object-oriented at the pipeline seam and procedural at the leaf-utility level.

[FIGURE 12A: Class diagram of the VisClick package.
Source: `docs/figures/figure_12A_class_diagram.png` (produced from `docs/figures/figure_12A_class_diagram.svg`; UML class diagram with composition, inheritance and dependency edges).
Caption: Class diagram. The orchestrator `Bot` composes five pipeline classes — `Capture`, `Detector`, `OCREngine`, `Matcher`, `Actor` — and returns a `BotResult` value object; the `VisClickApp` Tk GUI subclass consumes `Bot`; two training-side subclasses (`TwoViewDataset`, `SimSiam`) extend the corresponding PyTorch base classes.]

Eight substantive classes are shown. Six of them realise the pipeline: `Capture` encapsulates the mss / DPI plumbing, `Detector` encapsulates the ONNX session and post-processing, `OCREngine` encapsulates the cached EasyOCR reader plus the one-shot Tesseract diagnostic, `Matcher` encapsulates the scoring policy (class bonus, verb vocabulary, class vocabulary) and the refusal rule, `Actor` encapsulates the PyAutoGUI configuration and click primitives, and `Bot` is the composer that receives instances of the five and drives one `run_instruction` call end-to-end. The GUI (`VisClickApp`) is a `tkinter.Tk` subclass and consumes a `Bot` instance. The training script contributes two more subclasses — `TwoViewDataset` extends `torch.utils.data.Dataset` for the SimSiam SSP two-view augmentation, and `SimSiam` extends `torch.nn.Module`. Composition dominates over inheritance: `Bot` does not inherit from any of the five collaborators, it *owns* them, which is what allows tests to swap any collaborator for a stub without touching the others. The design consciously follows the "prefer composition over inheritance" principle from the Gang-of-Four literature, and every collaborator is injectable through `Bot.__init__` for exactly that reason.

A design decision worth surfacing. Alongside the classes, each pipeline module still exposes its public operations as module-level functions (for example `visclick.capture.grab`, `visclick.match.best_box`). These are one-line delegates to a module-scope default instance of the corresponding class. The pattern is deliberate. It keeps existing scripts, notebooks and the four baseline adapters (which were written before the refactor) working without modification, and it gives callers a choice between the classical stateless-function style and the injectable object-oriented style. Neither style is claimed as superior; the class-based style is used inside the orchestrator and inside `baseline_visclick.py`, and the function-based style is used inside the notebooks. Both styles resolve to the same instance data.

## 5.6 GUI WIREFRAMES

The prototype ships a single-window Tk dialog. The wireframe in Figure 11 captures the layout. There are deliberately few controls. The goal is to make the bot's behaviour obvious to a first-time user, not to put every parameter on the surface.

[FIGURE 11: Wireframe of the VisClick GUI.
Source: `reports/figures/ch5_gui_wireframe.png` (to be produced; hand-drawn rectangles or a screenshot of the actual Tk window with annotations overlaid; the existing screenshot `reports/figures/proto_2_captured.png` can be used with arrow annotations).
Caption: GUI wireframe. (1) Monitor dropdown. (2) Instruction text box. (3) Run / Stop buttons. (4) Live status line. (5) Last-overlay thumbnail. (6) Verbose log toggle.]

The six elements:

1. **Monitor dropdown** (`gui.MonitorSelector`). Populated at start-up from `mss.monitors`. Selection sets the `--monitor` index for every subsequent run. Defaults to the primary monitor.
2. **Instruction text box** (single line, `tk.Entry`). The user types a free-form instruction. Enter triggers Run.
3. **Run / Stop buttons.** Run kicks off the orchestrator. The 3-second pre-action countdown is implemented as a Tk `after()` callback; the Stop button cancels the countdown.
4. **Status line.** Shows one of `idle`, `counting down: 3 / 2 / 1`, `capturing`, `detecting`, `ocr`, `matching`, `clicking`, `done: verdict?`, `FAIL: cannot find target`.
5. **Last-overlay thumbnail.** A 320×180 thumbnail of the most recent `overlay.png`. Clicking the thumbnail opens the full-resolution PNG in the system viewer. This is the diagnostic affordance that supports UC-04.
6. **Verbose log toggle.** A check box that, when on, prints the per-stage timings to stdout. Off by default to avoid noise.

The wireframe is deliberately small. Three earlier wireframes — a separate evaluation tab, a separate model-selection panel, a confidence-threshold slider — were considered and removed at design review, on the grounds that they did not serve a stakeholder viewpoint identified in Section 3.2.2.

## 5.7 REPOSITORY LAYOUT AND DATA STORAGE DESIGN

The project does not use a database. All persistent state lives in files on disk, organised into a small number of top-level directories with well-defined responsibilities. The repository layout is presented once, in Figure 12, and every other chapter that names a file does so as a leaf inside this tree. A reader without the source-code repository in front of them can use Figure 12 together with the role descriptions below to follow every artefact reference in the report.

[FIGURE 12: Repository directory tree.
Source: `reports/figures/ch5_repo_tree.png` (to be produced; a single-panel directory tree exported from the actual repository at submission time using `tree -L 3 --dirsfirst`, or a hand-drawn equivalent in draw.io).
Caption: Repository directory tree. Top-level directories group the artefact's responsibilities: source code, dependency packaging, training data, model weights, evaluation scripts, notebooks, tests, reports, and documentation. Every path quoted elsewhere in this report is a node in this tree.]

The plain-text rendering of the same tree, for readers viewing the dissertation as plain text:

```text
visclick/                                # project root
  src/visclick/                          # the runnable Python package
    capture.py  detect.py  ocr.py
    match.py    act.py     bot.py     gui.py
  scripts/                               # evaluation and utility scripts
    run_baselines.py        # 4-method evaluation harness
    analyse_baselines.py    # TSR + latency summary
    baseline_visclick.py    # full-pipeline adapter
    baseline_template.py    # cv2.matchTemplate adapter
    baseline_ocr_only.py    # OCR-only adapter
    baseline_pywinauto.py   # accessibility-tree adapter
    auto_capture_corpus.py  # corpus expansion
    make_prototype_figures.py
    run_nfr.py              # NFR latency and memory profile
  notebooks/                             # 01..14 training + ablations
  tests/                                 # pytest suites for each module
  weights/                               # trained ONNX + .pt checkpoints
  configs/                               # YOLO/dataset YAMLs
  datasets/                              # training and test data
    source_zenodo_unified/{images,labels}/{train,val}
    desktop_seed/{images,labels}
    handcorrected_desktop_test/{images,labels}
  samples/                               # seed images and templates
  tasks/                                 # canonical T01..T15 task definitions
  reports/                               # everything the dissertation cites
    tables/                              # result CSVs
    figures/                             # result PNGs
    references/                          # literature PDFs cited
  docs/                                  # this report + plan + style guide
    Final_Report.md
    Final_Report_v2.md
    Final_Report_GAPS.md
    REPORT_STYLE_GUIDE.md
    PHASE_WORKLOG.md
    VisClick_Report_Data_Form.md
  runs/                                  # transient Ultralytics output
                                         # (regeneratable, not committed)
```

The top-level directories and their roles:

**The runnable package (`src/visclick/`).** Seven modules implementing the six-layer architecture from Section 5.3, plus a Tk GUI module. This is what `pip install -e .` installs and what `import visclick` resolves to.

**The evaluation scripts (`scripts/`).** A dozen Python entry points for jobs that are not part of the importable package: the evaluation harness, four per-method adapters, the NFR profiler, the figure regenerator, the corpus-expansion script.

**The notebooks (`notebooks/`).** Numbered Jupyter notebooks containing the training, fine-tuning and ablation experiments. Notebook 01 acquires and unifies the source-domain corpora. Notebook 05 trains the source-domain YOLOv8s detector. Notebook 08 runs the Phase 1.B transfer-learning ablations. Notebook 08c runs the few-shot sample-efficiency curve (D-05). Notebooks 09 and 10 are the DETR pair (source and fine-tune). Notebooks 11 to 14 are reserved for the pending adaptation experiments.

**The tests (`tests/`).** One pytest file per module under `src/visclick/`. Test command is `pytest -q tests/`.

**The trained weights (`weights/`).** The deployed ONNX detector at the canonical name `weights/visclick.onnx`, plus the per-ablation Ultralytics checkpoints. The deployed file is approximately 45 MB.

**The configs (`configs/`).** YAML configuration files for the YOLO/Ultralytics training pipeline plus the unified 6-class taxonomy file.

**The datasets (`datasets/`).** The training and test data, laid out in the YOLO/Ultralytics directory convention so the training command consumes the layout without modification. Three sub-trees: the unified source-domain bundle, the desktop seed, and the hand-corrected desktop test set.

**The task definitions (`tasks/`).** A single JSON file `T01_T20.json` listing the 15 canonical evaluation tasks plus 5 reserved slots. Each task carries the natural-language instruction together with per-method hints.

**The reports artefacts (`reports/`).** Everything the dissertation cites. Two principal sub-directories: a CSVs directory (the evidence file for every quantitative claim) and a PNGs directory (the figures). One additional sub-directory holds the PDF copies of the literature references.

**The documentation (`docs/`).** This dissertation, the gaps tracker, the style guide, the phase worklog, and the data form. The first five are submission and operational artefacts; the data form is the working memory of the project.

**The transient output (`runs/`).** Per-experiment Ultralytics training output. This directory is not version-controlled because the contents are deterministic outputs of the notebooks; only the relevant final weights are promoted into the trained-weights directory.

The principal data schema for the evaluation evidence is the per-attempt CSV that the harness writes after every task. The schema is stable across all 60 attempts collected so far and across the four method adapters. It is reproduced below for completeness:

```text
columns: task_id, method, instruction, capture_path, predicted_xy,
         verdict, latency_seconds, is_negative, notes
verdict in {pass, fail, skip, refused}
method  in {template, ocr_only, pywinauto, visclick}
```

Every per-attempt row is the smallest unit of evaluation evidence in the dissertation. The 60 rows currently on disk are what every percentage figure in Chapter 7 is computed from.

## 5.8 ALGORITHM DESIGN

Two algorithms in the system are non-trivial enough to warrant a dedicated design statement. The fuzzy matcher in `visclick.match`, and the refusal rule in the orchestrator.

### 5.8.1 THE MATCHER

The matcher's job is to pick which of the N detected boxes the user is asking the bot to click. The input is the user instruction (a short string), the list of per-box OCR texts, and the list of detection class IDs. The output is the index of the chosen box plus a confidence score on a 0-100 scale.

The matcher scores each box by combining two signals. The **text-similarity signal** is `rapidfuzz.fuzz.WRatio(instruction, box_text)`, which is a normalised mix of partial-string, token-set, and token-sort scores. WRatio is preferred over a single ratio metric because it is robust to word-order variation. "Click Save button" and "click the Save button" both score near 100 against an OCR string `Save`. The **class-bonus signal** is a small additive bonus when the detection class matches an inferred intent. The intent inference is a tiny rule table: instruction contains "type" or "enter" → prefers `text_input`; instruction contains "select" → prefers `menu` or `checkbox`; everything else prefers `button`. The bonus is set to +10 on a 0-100 scale. That is enough to break ties between two same-text boxes of different classes but not enough to override a strong text mismatch.

The final score is `min(100, text_similarity + class_bonus)`. The chosen box is the one with the highest final score, ties broken by detection confidence (higher first).

The Python implementation:

```python
def best_box(instruction: str,
             box_texts: list[str],
             box_classes: list[str]) -> tuple[int, float]:
    intent_class = _infer_intent(instruction)
    scores = []
    for text, cls in zip(box_texts, box_classes):
        ts = rapidfuzz.fuzz.WRatio(instruction.lower(), (text or "").lower())
        bonus = 10 if cls == intent_class else 0
        scores.append(min(100, ts + bonus))
    best_idx = max(range(len(scores)), key=scores.__getitem__)
    return best_idx, scores[best_idx]
```

The threshold for accepting the chosen box is `min_text_similarity = 60` in the current build. This threshold was selected empirically. The 15-task suite was run at thresholds of 40, 50, 60, 75 and 85, and the lowest threshold at which the negative test case (T15) was refused while the 14 positive tasks were still accepted was chosen. A higher threshold of 75 is being considered as part of risk RR-05; the change is contingent on widening the negative-case set beyond a single task.

### 5.8.2 THE REFUSAL RULE

The refusal rule is the orchestrator-level decision that determines whether a click is issued. It has three branches.

The **first branch** is the no-candidates branch. If the detector emits zero boxes, the orchestrator skips the per-box OCR stage entirely and goes directly to the OCR fallback. The fallback may itself find no candidates, in which case the system refuses.

The **second branch** is the low-confidence branch. If the matcher's chosen box has a score below `min_text_similarity` after per-box OCR, the orchestrator goes to the OCR fallback. If the fallback also returns a low-confidence result, the system refuses.

The **third branch** is the high-confidence branch. If the matcher's chosen box has a score at or above the threshold, the orchestrator proceeds directly to action. The action layer issues a single left-click at the centre of the chosen box, with the multi-monitor offset already corrected by the capture layer.

In all three branches the system writes a CSV row to `baseline_results.csv` describing what happened, including the chosen box (if any), the score, and the verdict (`pass`, `fail`, `refused`, `skip`). The CSV is what the analysis pipeline consumes in Section 7.3 and Section 8.2.

## 5.9 CHAPTER SUMMARY

The design described in this chapter is the contract that Chapter 6 implements and that Chapters 7 and 8 evaluate. The system has six logical layers (capture, detect, OCR, match, act, bot) each realised as one Python module, plus a thin GUI and an evaluation harness. The architecture is deliberately acyclic, which is what made the four-baseline comparison possible inside a shared harness. The runtime flow has one non-trivial decision point — the OCR-fallback path at the matcher — which trades off latency for recall in a way that the empirical evidence in Chapter 7 quantifies. Data is stored as files on disk in a layout that supports both YOLOv8/Ultralytics training conventions and per-attempt CSV evaluation logs. Two algorithms (the rapidfuzz-plus-class-bonus matcher and the three-branch refusal rule) are made explicit because they encode the project's twin commitments: fuzzy human-text tolerance and refusal-on-uncertainty.

The next chapter walks through the implementation of every element of this design.
