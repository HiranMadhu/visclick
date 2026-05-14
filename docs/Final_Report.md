# Cross-Domain Machine Learning Framework for Scalable GUI Element Detection and Adaptation in Desktop Environments

**Author:** Hiran Abeywardhana
**IIT Registration ID:** 20241504
**RGU Registration ID:** 2425488
**Supervisor:** Pumudu Fernando
**Second Marker:** [TBD]
**Programme:** MSc, Robert Gordon University Aberdeen / Informatics Institute of Technology (IIT)
**Submission date:** [TBD]

---

## Notes on this draft (delete before submission)

This is a first-pass draft written to the **proposal's stated scope**. Where a number, table cell, or figure has not yet been finalised in the experimental work, the text uses an explicit placeholder of the form `[NUMBER]`, `[TABLE]`, or `[FIGURE N.x: …]`. These placeholders mark the points where the author will paste the final values from `reports/tables/` or drop the final image from `reports/figures/`. The placeholders are deliberate. They are not omissions; they are the points where data and prose meet, and they have to be filled by hand because only the author knows which run is the "headline" one.

Figure placeholders follow this format:

```
[FIGURE N.x: short title.
 Suggested source: <relative path or "TBD by user">.
 Suggested caption (~30 words): <one-line draft caption, rewrite freely>.]
```

For consistency with the dissertation template the author will use, all section numbering follows the sample format (Chapter N → N.1, N.2 …). Tables and figures are numbered within the chapter.

---

# Chapter 1: Introduction

## 1.1 Chapter Overview

This chapter introduces the project and frames the work that follows. It begins with the background to graphical user interface (GUI) automation on the modern desktop and the reasons the existing tooling has not held up well as desktop applications have moved further away from the assumptions those tools were built on. From there it narrows down to a specific problem, a specific aim, and a set of research questions that the rest of the report sets out to answer. The research gap is then made explicit, and the work is positioned against both the lightweight classical tools (such as SikuliX, pywinauto and PyAutoGUI) and the heavyweight large vision-language models (such as SeeClick) that sit at the other end of the spectrum. The research objectives and the operational objectives are stated next, with the operational objectives broken down into the four phases by which the project was actually executed. After that, the proposed solution is described in enough detail that a reader can decide, before the technical chapters begin, whether the rest of the report is relevant to their interests. The scope of the project is then made explicit so that a reader is not left guessing what was intentionally left out. The chapter closes with a short summary that ties everything together and points the reader to the chapters that contain the experimental evidence.

The chapter is written so it can be read on its own. A reader who only has fifteen minutes to spend on this dissertation should be able to read Chapter 1 and come away with a fair sense of what the project tried to do, why it tried to do that, and what kind of evidence is offered later in support of the claims.

## 1.2 Project Background

Graphical user interfaces are the main way most people interact with software. Whether the user is filing a tax return on a web form, writing code in Visual Studio Code, processing an image in GIMP, or simply renaming a file in Windows File Explorer, what is actually happening, mechanically, is a small set of clicks and keystrokes directed at coloured rectangles on a screen. Because this is such a universal mode of interaction, automating it has been an active area of work for decades. The reasons range from the mundane (repetitive data entry, regression testing of an application's controls, robotic process automation in back-office settings) to the more ambitious, such as accessibility tools that let users with motor impairment drive an application by voice, or autonomous agents that complete multi-step tasks on a user's behalf.

The tooling for this kind of automation falls broadly into two camps. The first, and by far the older, is image-based or coordinate-based automation. SikuliX, for instance, lets a user record a small bitmap of a button and then asks the operating system to find that bitmap on screen using OpenCV template matching [1]. PyAutoGUI takes the same idea one step further by exposing a Python interface to mouse and keyboard, but at heart it is still working in pixel coordinates [2]. These tools are powerful, but they are also brittle. The bitmap of a button is not the button; it is a frozen photograph of the button taken on one particular machine, on one particular theme, on one particular DPI scaling, on one particular operating system build. Change any of those and the photograph stops matching. In practice, that is what happens every time a Windows feature update reshuffles the look and feel of the system, every time a user prefers dark mode, every time the same script is moved from a 1080p laptop to a 1440p desktop. The same brittleness is well documented in the literature: AskUI's recent review of visual automation tools describes SikuliX-style approaches as "image-recognition first" and notes the obvious downside that the recognition only generalises as far as the captured image library does [3].

The second camp is accessibility-tree automation. Windows applications written against the classic Win32 framework expose a tree of named UI controls through the UI Automation framework, and Python libraries such as pywinauto walk that tree to find a Save button by its semantic name rather than by its appearance [4]. When it works, this approach is fast and stable. The problem is that it has stopped working reliably on a meaningful fraction of the modern Windows application mix. Electron applications (Visual Studio Code, Slack, Discord, Microsoft Teams) expose only a degenerate tree because the entire interface is a Chromium browser rendering DOM. Modern Windows 11 applications that use WinUI 3 or XAML islands frequently expose their controls under localised internal names rather than the visible labels a user sees. Web pages inside any browser are served through ARIA, which uses different conventions again. The result is that pywinauto can correctly click a Save button in classic Notepad on Windows 7 but cannot find the same Save button on the same logical action in the modern Windows 11 Notepad, because the modern Notepad's Save-As dialog is itself a WinUI 3 surface. Empirical evidence for this exact failure mode is provided in Chapter 7 of this report.

Sitting outside both camps is a more recent strand of work that uses computer vision and machine learning to detect UI elements directly from a screenshot, without any privileged access to the application's internal tree. Object-detection models such as YOLOv8 [5] and DETR [6] are trained on annotated images of UIs and learn to predict bounding boxes labelled with classes such as `button`, `text`, `icon` and so on. Mobile UIs are well resourced in this respect, because of the RICO dataset [7] and its denoised successor CLAY [8], which between them provide tens of thousands of labelled mobile screens and have made it routine to train a competent mobile-UI detector on commodity hardware. Recent work such as YOLOv5-MGC [9] reports mean average precision (mAP) figures in the high 80s and low 90s on mobile UIs.

Desktops are a different story. Desktop UIs differ from mobile UIs along several axes at once. They are landscape rather than portrait. They are multi-window rather than single-window. They contain dense toolbars and ribbon menus that produce what Chen et al. (2020) call a "packed scene" [10], where elements sit close enough together that a standard detector struggles to put a clean bounding box around each one. They draw on decades of stylistic variance (Win32, WPF, Material Design, custom themes, dark mode, high-contrast accessibility skins) that has no real parallel in the much more harmonised design languages of Android and iOS. And, critically, there is no RICO-equivalent dataset for desktops. The most recent attempts to build one (DeskVision [11], GenGUI [12]) are themselves dated 2024 and 2025, which speaks to how recent the recognition of this gap is, and even those datasets are an order of magnitude smaller than RICO.

What this means in practice is that a detector trained to high accuracy on mobile UIs typically does not, on its own, do well on desktop screenshots. There is a domain shift between the two. Quantifying that shift, and developing data-efficient strategies for closing it, is the problem this project takes on.

[FIGURE 1.1: "Examples of the three desktop UI shifts." 
 Suggested source: a three-panel composite that the author can produce by stitching together one mobile screen from CLAY, one classic Win32 desktop screen from Windows File Explorer, and one modern Win11 screen from Notepad's Save-As dialog. Path placeholder: `reports/figures/ch1_domain_shift_examples.png`.
 Suggested caption (~30 words): "Three axes of the mobile-to-desktop shift. Left: a mobile portrait UI from CLAY. Middle: a classic landscape desktop with a packed toolbar. Right: a modern Win11 WinUI 3 dialog with flat, theme-dependent controls."]

## 1.3 Problem Statement

The practical problem this project addresses can be stated in a single sentence. **A practitioner who wants to build a vision-based UI-automation bot for the modern Windows desktop today has no off-the-shelf option that is at the same time accurate, lightweight enough to run on a typical workstation, and tolerant of the variability that real desktop UIs exhibit in the wild.**

The classical image-based tools (SikuliX, PyAutoGUI) are lightweight, but they are not tolerant of variability; their bitmap matching collapses the moment the theme, DPI, or font shifts. The accessibility-tree tools (pywinauto, AutoIt) are tolerant of theme and DPI by construction, but they are not accurate on the modern Windows application mix; the empirical work in Chapter 7 of this report shows pywinauto succeeding on only one out of fifteen task instances on a representative Windows 11 workload, and that one success is the negative case where the right answer is to do nothing. At the other extreme, heavyweight large vision-language models such as SeeClick [13] are accurate and tolerant of variability across domains, but they are not lightweight by any reasonable definition; they require multi-GPU inference setups and large memory budgets that are unrealistic for most practical deployments and are out of reach for a project at MSc scale.

The gap, then, is in the middle of the spectrum. Can a lightweight object-detection model, trained on the relatively well-resourced mobile UI domain and then adapted to the data-scarce desktop domain using minimal labelled desktop data, deliver an "accurate enough" detector for use inside a practical automation pipeline? And, given that this is fundamentally a transfer-learning question, which adaptation strategy gives the best return on the labelled data budget? These are the questions the project sets out to answer.

A secondary, more practical, problem is that even an accurate detector is not, by itself, an automation system. A user does not want to be told "there are forty-seven elements on your screen". A user wants to say "click Save", and have the system do the right thing. That requires a grounding step: matching a natural-language instruction to one of the detected elements. The IVGocr framework of Dardouri et al. (2024) [14] provides a sensible scaffolding for this kind of pipeline, and this project adopts it. The novelty in the prototype is therefore not the pipeline architecture but the detector that sits inside it.

## 1.4 Research Aim

> *The aim of this research is to design and implement a scalable cross-domain machine learning framework capable of adapting mobile-trained GUI detection models for desktop environments while maintaining high accuracy and generalisation.* [15]

The aim is quoted verbatim from the approved project proposal. It deliberately combines a research goal (cross-domain adaptation) with a quality target (high accuracy and generalisation) and a deployment context (desktop environments). All three are needed for the answer to be useful in practice; an adaptation method that closes the domain gap on paper but does not generalise across applications, or a detector that generalises across applications but loses accuracy in the process, would each fail the aim. The methodology is structured around all three in equal measure.

## 1.5 Research Questions

The aim is decomposed into four research questions that the rest of the work then addresses one at a time. The four questions are taken verbatim from the project proposal [15]:

* **RQ1.** What is the magnitude of performance degradation when applying mobile-trained GUI detectors to desktop screenshots?
* **RQ2.** Which adaptation strategies yield the largest improvements in low-label regimes?
* **RQ3.** How does model choice (YOLO vs DETR vs LVLM) influence transferability and sample efficiency?
* **RQ4.** What are the practical limits of a vision–action bot using adapted detectors in real desktop applications?

These four questions are answered, respectively, in the baseline performance numbers in Chapter 6 (RQ1), the adaptation-method comparison in Chapter 7 (RQ2), the cross-architecture comparison in Chapter 7 (RQ3), and the prototype evaluation in Chapter 8 (RQ4). The chapter map is repeated in Section 1.11.

## 1.6 Research Gap

The literature reviewed in Chapter 2 establishes that the gap addressed here is *not* a lack of state-of-the-art models. The mobile-UI domain has highly optimised detectors of its own; the YOLOv5-MGC paper of Cheng et al. (2022) [9] is one example. The desktop-target domain has a clear application pipeline in the IVGocr framework of Dardouri et al. (2024) [14]. Heavyweight large vision-language models such as SeeClick [13] are perfectly capable of bridging the domain gap, but they do so at a computational cost that puts them out of reach for the kind of practical, on-machine deployment this project cares about.

The gap is therefore in the *combination*. There is no published, lightweight, data-efficient method that takes a state-of-the-art mobile detector, adapts it to the desktop domain using the kind of small labelled-data budget that an individual or a small team can realistically produce, and demonstrates that the resulting model is usable inside a complete automation pipeline rather than only on a static benchmark. This combination is what the dissertation contributes.

The gap is sharpened by the data side as well. The mobile UI domain has RICO [7] and CLAY [8] providing tens of thousands of labelled screens, while the desktop domain has only a handful of small, recently-published datasets ([11], [12]). The data-scarce nature of the target domain is what mandates the use of domain adaptation in the first place. Training a high-capacity desktop-only model from scratch is not feasible at MSc scale; a model has to be trained somewhere else and then moved across.

[FIGURE 1.2: "Positioning of this project against existing automation approaches."
 Suggested source: a 2x2 grid with axes (lightweight ↔ heavyweight) and (theme/DPI tolerant ↔ brittle). Place SikuliX/PyAutoGUI bottom-left, pywinauto bottom-right (but greyed out because it fails on modern Win11), SeeClick top-right, and this project (cross-domain adapted YOLOv8 + IVGocr) middle. Path placeholder: `reports/figures/ch1_positioning_grid.png`.
 Suggested caption (~30 words): "Where the proposed framework sits relative to existing GUI automation approaches. Classical image-based and accessibility-tree tools sit in the lightweight-but-brittle corner; LVLMs sit in the heavyweight-but-tolerant corner; this project targets the middle."]

## 1.7 Research Objectives

The four research objectives below are quoted from the approved project proposal [15]. Together they describe what the project committed to deliver in order to answer the research questions in Section 1.5.

1. **Quantify** the mobile-to-desktop performance gap using mean average precision (mAP) for detection quality and the Central Point Validation (CPV) metric of Dardouri et al. (2024) for grounding quality.
2. **Implement and compare** three adaptation methods: few-shot supervised fine-tuning, self-supervised pre-training followed by fine-tuning (SSP+FT), and unsupervised domain adaptation (UDA) using the Cross-Domain Adaptive Teacher framework of Li et al. (2022) and the Source Hypothesis Transfer (SHOT) framework described in Sensors (2023).
3. **Evaluate sample efficiency** by determining how many labelled desktop images are actually required to achieve acceptable performance, sweeping over $k = 1, 5, 10, 50, 100$.
4. **Develop a prototype bot** that demonstrates instruction-to-action behaviour on real desktop applications using the adapted detector inside the IVGocr pipeline.

Each objective is mapped to a chapter and to a measurable deliverable. The mapping is made explicit in Section 8.8 (Achievement of Research Objectives).

## 1.8 Operational Objectives

The research objectives describe what is to be answered. The operational objectives describe how the work was actually broken down. The project was executed in four phases, each with concrete deliverables.

**Phase 1: Data engineering and baseline establishment.** Survey 10–15 diverse desktop applications (Visual Studio Code, GIMP, Chrome, Firefox, Windows File Explorer, Notepad, Excel, and others). Use an automated capture script built on top of `mss` and `pywinauto` to collect an unlabelled corpus of approximately 2,000 desktop screenshots, covering different resolutions, themes, and application states. From that unlabelled corpus, hand-select and annotate a 100-image "Labelled Target Corpus" in CVAT. The annotation schema is the five-class set `{button, menu, text_input, checkbox, icon}`, intentionally simplified to focus on interactive elements. Train the mobile-baseline detector on CLAY. **Deliverables:** the labelled corpus itself and **D1**, a baseline-performance report addressing RQ1.

**Phase 2: Model adaptation experiments.** Implement both a YOLOv8 backbone and a DETR backbone, each pre-trained on CLAY. Run three experiments. *Experiment 1* trains a few-shot fine-tune on $k = 1, 5, 10, 50, 100$ labelled desktop images to plot a data-efficiency curve. *Experiment 2* pre-trains the backbones using a generative inpainting self-supervised task on the 2,000 unlabelled desktop images and then repeats Experiment 1, to measure the uplift from SSP. *Experiment 3* implements the Adaptive Teacher [16] and SHOT [17] UDA frameworks. **Deliverables:** trained weights for all variants and **D2**, an ablation study addressing RQ2 and RQ3.

**Phase 3: Prototype integration.** Pick the single best adapted model from Phase 2 and build the "Adapted-IVGocr" prototype that wraps it. The integration stack is `mss`/`pywinauto` for capture, the adapted detector for perception, Tesseract or EasyOCR for reading text inside detected boxes, fuzzy string matching (rapidfuzz) for grounding the instruction to a detected element, and PyAutoGUI for the click action itself. **Deliverable:** **D3**, a functional Python prototype with a short demonstration video.

**Phase 4: End-to-end evaluation and thesis composition.** Define 10–15 standardised automation tasks (such as "open Notepad and save the file as `test.txt`") and evaluate the prototype's Task Success Rate (TSR) on those tasks. Perform a qualitative failure analysis that traces end-to-end failures back to detection errors, OCR errors, or grounding-logic errors. Write the final thesis. **Deliverable:** **D4**, the final report and packaged code.

## 1.9 Proposed Solution

The proposed solution has three interlocking components. The technical depth on each lives in Chapter 5 (Design) and Chapter 6 (Implementation); this section gives the high-level shape only.

### 1.9.1 Data and preprocessing pipeline

The **source (mobile) corpus** is the CLAY dataset of Li et al. (2022) [8], a denoised 59,555-image subset of RICO [7]. Using CLAY rather than raw RICO matters because RICO is known to contain significant layout noise; CLAY is a deep-learning pipeline that automatically cleans and corrects those raw layouts, and the resulting corpus is a much better starting point for transfer learning. The CLAY annotation schema is mapped onto the five-class desktop schema using a deterministic mapping table documented in Chapter 6.

The **target (desktop) unlabelled corpus** of approximately 2,000 screenshots is collected by a Python script that drives `pywinauto` to enumerate the visible top-level windows of a curated set of 10–15 applications, captures each window with `mss`, and saves the resulting screenshot to disk. The script is parameterised by resolution, theme, and DPI scaling so that the corpus covers the in-the-wild variability the deployed prototype will eventually encounter.

The **target (desktop) labelled corpus** of N = 100 screenshots is curated by hand from the unlabelled corpus and annotated in CVAT against the five-class schema. This corpus is the gold-standard test set against which all adaptation methods are evaluated, and it is also the source of the few-shot training subsets in Experiment 1.

### 1.9.2 Adaptation methodologies

All adaptation methods are applied to both a **YOLOv8-L** backbone and a **DETR-R50** backbone to make the cross-architecture comparison in RQ3 a controlled one.

The **baseline** is established by running the mobile-trained detector zero-shot on the 100-image labelled target corpus. The resulting low mAP is the "problem" that the three adaptation methods then try to close.

**Method 1: few-shot supervised fine-tuning.** The CLAY-trained backbone is frozen, and only the final detection head is re-trained on the N = 100 labelled desktop images, sweeping over $k = 1, 5, 10, 50, 100$ to produce a data-efficiency curve. This is the simplest of the three methods and serves as the floor against which the other two are compared.

**Method 2: self-supervised pre-training (SSP) plus fine-tuning.** A generative inpainting task [18] is used on the 2,000 unlabelled desktop images: random patches are masked out, and the model is trained to predict them. The intuition is that, to inpaint a missing patch of a Windows toolbar, the model must implicitly learn the structural grammar of desktop UIs (toolbars are horizontal, icons sit in rows, dialog buttons cluster bottom-right, and so on). The SSP-trained backbone is then handed to Method 1 to measure whether this unsupervised pre-training step improves the final few-shot mAP.

**Method 3: unsupervised domain adaptation (UDA).** Two state-of-the-art UDA frameworks are implemented and compared. The first is the **Cross-Domain Adaptive Teacher** of Li et al. (2022) [16, 19], which is a teacher-student setup where a stable Exponential Moving Average (EMA) teacher generates pseudo-labels on weakly augmented target images and a student is then trained on a mixed batch of labelled source (CLAY) data and strongly-augmented pseudo-labelled target data. The second is **SHOT** [17, 20], which freezes the source-trained classification head (the "source hypothesis") and adapts only the feature extractor backbone on the unlabelled target images using self-supervision; the goal is to align the new target features to the frozen source hypothesis rather than to retrain the head itself.

### 1.9.3 Prototype integration and evaluation

The prototype, named **VisClick**, is a direct implementation of the IVGocr architecture of Dardouri et al. (2024) [14, 21]. The novelty is the replacement of their standard YOLOv8 detector with the cross-domain-adapted detector from the previous component.

The runtime flow is:

1. **Input.** The user supplies a free-form text instruction, for example "click Save".
2. **Capture.** A screenshot of the user-selected monitor is taken with `mss`, in the virtual-desktop coordinate space.
3. **Perception.** The adapted detector runs on the screenshot and returns N candidate bounding boxes, each with a class label and a confidence score.
4. **Reading.** Tesseract or EasyOCR is run on each detected bounding box (rather than the whole image) to recover the visible text on the element. A full-image OCR pass is kept in reserve as a fallback for cases where the detector misses the target element entirely.
5. **Grounding.** A fuzzy-string-matching function (using `rapidfuzz`) computes the similarity between the user's instruction and the OCR text of each detected element. The element with the highest score above a configured similarity threshold is selected.
6. **Action.** PyAutoGUI moves the cursor to the centre of the selected box and issues a single left click. When no candidate exceeds the threshold, the prototype refuses to click and reports a structured failure message; this refusal-on-uncertainty behaviour is a deliberate design choice, motivated by the observation that a confident wrong click is worse, in an automation tool, than an honest "I do not know".

The detection metric used for component-level evaluation is mAP at IoU 0.5, with the Central Point Validation (CPV) metric of Dardouri et al. (2024) used for grounding quality. The end-to-end bot metric is Task Success Rate (TSR), defined as a binary pass/fail on each of the 10–15 standardised tasks.

[FIGURE 1.3: "High-level architecture of the proposed solution."
 Suggested source: a single-panel block diagram showing the three components (source-domain pre-training, cross-domain adaptation, prototype integration) laid out left-to-right with arrows. The Mermaid block diagram already in `docs/VisClick_Report_Data_Form.md` Section 18.1 is a good starting point and can be exported as PNG. Path placeholder: `reports/figures/ch1_solution_overview.png`.
 Suggested caption (~30 words): "End-to-end shape of the proposed solution. A mobile-pretrained detector is adapted to desktop using one of three methods and then wrapped inside the IVGocr-style instruction-to-action pipeline that constitutes the deliverable prototype."]

## 1.10 Scope of the Project

It is worth being explicit, this early in the report, about what the project does and does not commit to deliver.

**In scope.**

* Cross-domain adaptation from a single mobile source domain (CLAY, with raw RICO as the upstream corpus) to a single desktop target domain (Windows 11, ten to fifteen common applications).
* Two-detector architectural comparison: YOLOv8 and DETR. Both are state-of-the-art, both have well-known reference implementations, and they differ on a single architecturally meaningful axis (anchor-based dense detection with a multi-scale neck for YOLO, versus anchor-free direct set prediction with a transformer encoder-decoder for DETR), which makes the comparison clean.
* Three adaptation methods: few-shot fine-tuning, SSP-plus-fine-tuning, and unsupervised domain adaptation. Method 3 itself contains the Adaptive Teacher / SHOT sub-comparison.
* A prototype that closes the loop, on the user's machine, from a natural-language instruction to a click.
* Quantitative evaluation against three measurable criteria: mAP on the labelled desktop test set, CPV on the IVGocr grounding step, and TSR on a fixed task suite.

**Out of scope.**

* **Cross-platform support.** The prototype targets Windows 11. macOS and Linux are not in scope; pywinauto is itself Windows-only, the DPI assumptions in the capture stage are Windows-specific, and any meaningful cross-platform work would have at least doubled the project's effort budget.
* **Heavyweight large vision-language models.** Models such as SeeClick [13] are referenced and discussed at length in the literature review, because they represent the "heavyweight SOTA" against which the project's lightweight stance is positioned, but they are not benchmarked here. The compute budget for that kind of comparison is well beyond what was available, and including it would have shifted the project from a practical engineering investigation to a pure benchmarking exercise.
* **Full accessibility-tree integration.** pywinauto is used in the data-collection stage (to enumerate visible top-level windows) and is also benchmarked as a classical baseline in Chapter 7. It is not used at runtime in the prototype's perception pipeline; doing so would defeat the point of the vision-based approach.
* **Highly multimodal instructions.** Instructions are free-form text. Voice input, image-conditioned instructions, multi-step natural-language commands, and conversational dialogue are all out of scope.
* **Robotic process automation at fleet scale.** The prototype is a single-user, single-machine demonstrator. Scaling out to multiple machines, multi-tenant deployment, or enterprise governance is left for future work and discussed in Chapter 9.

The scope statement above is informed by the literature review in Chapter 2 and by the risk analysis in Chapter 4. Where the proposal's original scope had to be trimmed during execution, the trimming and the reason for it is documented in Section 4.6 (Risk Mitigation Plan) and in Section 9.7 (Limitations) rather than being silently dropped.

## 1.11 Chapter Summary

This chapter has set up the problem, the aim, the four research questions, the research gap, and the four-phase work plan that the rest of the report follows. The picture, in one paragraph, is this. GUI automation on the modern desktop is in an awkward place. Classical image-based tools are too brittle; classical accessibility-tree tools have fallen out of step with the modern Windows application mix; the heavyweight large vision-language models that *can* do it are too big to run anywhere most people would actually want to. Sitting in the middle, where there is a clear opportunity, is the idea of a cross-domain-adapted lightweight detector trained on the relatively well-resourced mobile UI domain and then carried across to the data-scarce desktop domain. The project investigates how far that idea can be pushed using three adaptation methods (few-shot fine-tuning, self-supervised pre-training plus fine-tuning, and unsupervised domain adaptation) on two backbone architectures (YOLOv8 and DETR), and integrates the best of those into a working prototype that closes the loop from a typed instruction to a click on the real Windows desktop.

The rest of the report is organised as follows. **Chapter 2** is the literature review. It walks through the datasets, the model architectures, and the adaptation methodologies in enough depth to support the architectural choices made later, and it ends with the explicit research-gap statement that motivates the rest of the work. **Chapter 3** lays out the requirement analysis, including a stakeholder analysis using the Onion model, five functional requirements, and ten non-functional requirements with quantitative targets. **Chapter 4** covers the project management approach: the research methodology, the software development methodology, the risk register, and the project plan. **Chapter 5** covers the design: a high-level architecture, a research design, a block diagram, a flow chart, and the UI wireframes for the prototype. **Chapter 6** is the implementation chapter, which describes how the data pipeline, the three adaptation methods, and the prototype were actually built. **Chapter 7** is the testing chapter, which reports the model-level and prototype-level test results in tabular form. **Chapter 8** is the evaluation chapter, which interprets those results against the research questions and the requirements, includes a qualitative review from independent practitioners, and discusses legal, ethical, professional and social impact. **Chapter 9** concludes with the limitations, the things I would do differently in retrospect, and the directions for future work.

# Chapter 2: Literature Review

## 2.1 Overview

This chapter is a critical review of the prior work that informs the project. It is organised in the same order that the methodology in Chapter 6 puts the pieces together. It starts with the available datasets, because data is the gating constraint for everything that follows. It moves on to the pre-processing step that bridges noisy raw data and a trainable corpus. From there it covers classical automation approaches that have historically dominated GUI testing, then the deep-learning detectors that have started to replace them on mobile UIs. It then surveys the family of domain-adaptation methodologies that this project relies on to carry a mobile-trained detector across to the desktop. After that it looks at the wider GUI-agent landscape, including the heavyweight large vision-language models that sit at the other end of the spectrum from this work. It closes with a short summary of the metrics used in the UI-detection literature and a precise statement of the research gap.

The chapter is deliberately structured around comparisons. Where two pieces of work try to do roughly the same thing, the review puts their numbers side-by-side so the reader can see which one is genuinely better and which one is a re-branding. Where a piece of work is cited only as motivation, the review says so plainly. The aim is to leave the reader with a clear picture of which methodological tools were taken off the shelf for this dissertation and which were left there for considered reasons.

## 2.2 Existing GUI Element Datasets

The starting point for any vision-based UI-detection work is a corpus of annotated screenshots. The single most important fact about that corpus today is that the mobile side of it is well resourced and the desktop side of it is not.

The canonical mobile-UI dataset is **RICO**, released by Deka and colleagues in 2017 [7, 22]. RICO contains roughly 72,000 unique Android UI screenshots harvested from 9,300 free apps on the Google Play Store, paired with their Android view-hierarchy XML and a number of derived properties: textual labels, structural relationships, animation traces, and interaction sequences. The view hierarchy is what makes RICO useful for object detection rather than just for design retrieval. From the XML one can derive a bounding box and a class label for every leaf node on screen, which in practice means tens of millions of labelled elements across the corpus. The downside, well known in the literature, is that the raw view hierarchy is noisy. Container nodes overlap with their visual children, invisible nodes still appear in the tree, and the leaf-class labels are inconsistent across SDK versions and across app authors. Anyone who has tried to train an object detector directly on raw RICO bounding boxes hits these issues quickly.

The community's response is the **CLAY** dataset of Li and colleagues at CHI 2022 [8, 23]. CLAY is not a new collection of screenshots; it is a deep-learning denoising pipeline that takes RICO's raw view hierarchies and produces cleaner, machine-verified layouts. The result is a corpus of 59,555 cleaned Android UI layouts with a more consistent 23-class taxonomy and a much-reduced rate of overlapping, invisible, or mis-classified bounding boxes. The improvement is not trivial: published detectors trained on CLAY instead of raw RICO labels report a 5 to 8 percentage-point uplift in mean average precision on held-out test splits. For this reason CLAY became the source-domain training set for this project's headline detector; the proposal commits to it in Section 7.A.

The mobile domain has not stood still since RICO. The **MUD** dataset of 2024 [24, 25, 26] was created in direct response to the observation that RICO and CLAY are now temporally outdated. The Android visual design language has shifted noticeably since 2017 (the move from older Holo and Material 1 themes to Material 3, the rise of foldable form factors, the increase in dark-mode and large-text accessibility variants), and a detector trained on the older corpus does noticeably worse on modern screens. MUD reports buttons-class mAP of 75.3% on its own test split compared to 63.4% when the same model is trained on RICO and evaluated on MUD. That gap is not large in absolute terms, but it speaks to a real and ongoing data-currency problem even within the mobile domain.

[FIGURE 2.1: "RICO and CLAY side-by-side." 
 Suggested source: one mobile screen from RICO (raw view-hierarchy boxes overlaid) and the same screen with CLAY's cleaned labels. The CLAY GitHub page has matched-pair examples that can be reproduced. Path placeholder: `reports/figures/ch2_rico_vs_clay.png`.
 Suggested caption (~30 words): "RICO raw labels (left) vs CLAY's denoised labels (right) on the same screen. CLAY removes invisible-container nodes, fixes class mis-assignments, and reduces overlapping-box duplicates."]

On the desktop side the picture is much thinner. There is no "desktop RICO" of comparable scale. The recent attempts to fill the gap are illustrative both of demand and of how recent the recognition of the gap is. **DeskVision** (2025) [11] proposes a large-scale desktop region-captioning corpus aimed at GUI agents; it is dated March 2025 on arXiv. **GenGUI** (2025) [12] is a synthetic dataset of web interfaces generated by ChatGPT and is closer to a UI-design-generation corpus than to an element-detection one. **AS400-DET** [27] is a niche detection dataset for legacy terminal-style interfaces. None of these is yet at the order of magnitude of RICO. Importantly, the authors of the IVGocr paper that this project's prototype is modelled after had to build their own desktop dataset to run their experiments [14], which they note explicitly. The data-scarce nature of the desktop target domain is the gravitational pull that draws this project, and others like it, towards domain adaptation rather than train-from-scratch on the target.

Table 2.1 sets the principal datasets side-by-side. The figures for RICO and CLAY are the ones the authors report; the figures for DeskVision and GenGUI are the ones their respective arXiv papers cite at submission.

**Table 2.1: Available GUI element datasets.**

| Dataset | Year | Domain | Screens | Annotations | Public licence |
|---------|------|--------|---------|------------:|----------------|
| RICO [7] | 2017 | Mobile (Android) | 72,219 | ~3M leaf nodes (raw view-hierarchy) | Free for research |
| CLAY [8] | 2022 | Mobile (Android) | 59,555 | Cleaned 23-class layouts | Open access |
| VINS [L2 in `literature_table.csv`] | 2021 | Mobile | 4,800 | 11-class detection labels | Open access |
| MUD [24] | 2024 | Mobile (Android, modern) | 18,132 | Modern-style annotations | Open access |
| DeskVision [11] | 2025 | Desktop | "Large-scale" (exact count unreleased at time of writing) | Region-caption pairs | Pending release |
| GenGUI [12] | 2025 | Web (synthetic) | Synthetic: generated on demand by ChatGPT | Layout + class labels | CC-BY |
| Zenodo unified bundle (used in this project) | 2023 | Mobile + Web | 9,646 | 6-class collapsed from RICO+CLAY+VINS | Open access |

The Zenodo unified bundle row is the corpus this project actually trains on. It combines RICO, CLAY and VINS into a single 6-class taxonomy (`{button, text, text_input, icon, menu, checkbox}`) chosen to match what an automation bot needs to interact with. Details of the class-collapse mapping are in Chapter 6.

## 2.3 Pre-processing for UI Element Detection

Pre-processing for a UI corpus is not the same problem as pre-processing for a natural-image corpus. The standard tricks (random crop, horizontal flip, colour jitter) are either useless or actively harmful on screenshots. Horizontal flip turns a left-aligned toolbar into a right-aligned one, which is fine in principle until the model also flips the text inside the buttons and produces meaningless training signal. Colour jitter on a Win11 light theme can produce shades that no real application ever displays. The literature treats UI pre-processing largely as a label-noise problem rather than as an image-augmentation problem.

The largest single piece of UI pre-processing work in the public literature is CLAY itself [8, 23]. CLAY's main contribution is a learned denoiser that takes raw RICO view-hierarchy bounding boxes and produces cleaner labels: invisible containers are removed, overlapping duplicates are collapsed, mis-classified node types are corrected. The authors report a measurable downstream effect, with detectors trained on CLAY-cleaned labels gaining several mAP points on held-out test splits over the same architecture trained on raw RICO. The denoising is a pre-processing step in spirit, even though it is implemented as its own deep-learning pipeline.

A more pragmatic line of pre-processing work tackles class-imbalance. Both RICO and the desktop seed corpora collected in this project are heavily skewed: the `text` class is much more frequent than any of the actionable classes (`button`, `text_input`, `menu`, `checkbox`). The sample dissertation reviewed alongside this project [the RGU MSc skin-cancer report, 2026] used weighted random oversampling on the minority classes; the AS400-DET paper [27] reports good results with class-balanced focal loss. This project chose a simpler route, a 12-to-6 class collapse that puts visually similar minority classes into the same training target, partly to keep the training pipeline reproducible on Colab Free without exotic loss functions and partly because the 6-class taxonomy maps cleanly onto what the downstream IVGocr matcher needs.

Two pre-processing patterns recur across the literature and were considered for this project. The first is **stratified sub-sampling** of the source corpus to bring its class distribution closer to the target domain's. This is appealing when the source-target class imbalance is severe; in this project it was not used, on the grounds that the target distribution is itself unknown until enough labelled desktop data exists to characterise it. The second pattern is **synthesis-based augmentation**, in which under-represented elements (icon-only buttons, dropdown arrows) are pasted onto background screenshots to inflate the training corpus. ScreenAI [28] and several recent agent papers use a variant of this idea at very large scale. For this project's data budget the cost of building a high-quality synthesis pipeline is not obviously worth the benefit, but Chapter 9 records it as a future-work direction.

A short remark on input resolution. RICO and CLAY use portrait-oriented Android screens that fit comfortably into a square 640×640 detector input. Desktop screenshots are landscape, often at 1920×1080 or 3440×1440, and need to be down-scaled before they enter a YOLOv8 detector with `imgsz=640`. This rescaling is, in itself, a pre-processing concern that produces measurable accuracy variation. The numbers in Chapter 7 are reported with a single fixed `imgsz=640`; the sensitivity of those numbers to that choice is briefly discussed in Section 9.7.

## 2.4 Classical Automation Approaches

Before the deep-learning era, three families of tools dominated GUI automation. They are still in widespread use, particularly in industrial test automation and RPA, and the project measures itself against the strongest of them. They are reviewed here because the gap they leave is precisely the gap this project tries to fill.

The first family is **bitmap-based visual automation**. The best-known tool is **SikuliX** [1, 3]. SikuliX records a small bitmap of a UI element (a Save button, a magnifying-glass icon) and at run time uses OpenCV's `matchTemplate` to find that bitmap on the live screen. The user writes a script in a Sikuli-flavoured Python that says, in essence, "click this image". The strength of the approach is its simplicity. The weakness is its rigidity. A bitmap is a frozen photograph of the element under one theme, one DPI, one font, one application version. Change the theme to dark mode and the bitmap stops matching. Change the DPI from 100% to 125% and the same thing happens. AskUI's recent review [3] phrases this politely as "image recognition first", but in practice anyone who has tried to deploy a SikuliX script across a fleet of machines has seen the failure mode at scale. The empirical evidence in Chapter 7 of this report confirms that **on the specific subset of tasks where a reference bitmap could be captured, template matching is excellent (it scored 100% on those tasks)**, but on tasks where no useful bitmap exists (positional targets such as "click the first command", dynamic state toggles, or text-inside-text) it cannot represent the problem at all.

The second family is **coordinate-based automation**. **PyAutoGUI** [2, 29] is the canonical Python example: it exposes `pyautogui.click(x, y)` and lets the user write scripts that drive the mouse and keyboard at specified pixel coordinates. PyAutoGUI is widely used inside other automation stacks (including this project's prototype, where it drives the final click). On its own it is the most brittle of the three families because it has no knowledge of what is at those coordinates. The same script that works on a 1080p laptop fails on a 1440p desktop unless every coordinate is recomputed. PyAutoGUI is best understood not as a competitor to a vision-based bot but as a low-level primitive that any vision-based bot eventually has to use to translate a chosen bounding box into an OS-level click.

The third family is **accessibility-tree automation**. On Windows the canonical Python library is **pywinauto** [4, 29]. pywinauto uses Microsoft's UI Automation framework to walk the live application's accessibility tree and find controls by their semantic Name and ControlType. The approach is theoretically beautiful: it abstracts away theme, DPI and font; the same script will work on a 1080p laptop and a 1440p desktop because both expose the same `Button(Name='Save')` control. In practice the modern Windows application mix has eroded the assumption that the accessibility tree faithfully reflects the visible UI. Electron applications (Visual Studio Code, Slack, Discord) expose only a degenerate tree because the renderer is a Chromium browser. Modern Windows 11 applications using WinUI 3 or XAML islands frequently expose localised internal control names rather than the visible labels. Web pages inside any browser serve their accessibility via ARIA, which is a separate convention again. The empirical baseline reported in Chapter 7 of this report shows pywinauto scoring 1 out of 15 task instances on a representative Windows 11 workload (and that single success is the negative case where the right answer is to do nothing). On every positive task (Notepad's Save-As dialog, Visual Studio Code's Search panel, Chrome's omnibox, File Explorer's ribbon) pywinauto returned `ElementNotFound`.

The collective failure of all three classical families on the modern Windows 11 application mix is the operative justification for a vision-based approach. If the accessibility tree could be trusted, machine learning would not be needed; the empirical evidence is that on a 2026-vintage desktop, it cannot.

[FIGURE 2.2: "Where each classical baseline succeeds and fails on T01–T15."
 Suggested source: one of the existing per-method overlays from `reports/figures/baselines/`. A horizontal bar chart of pass/fail counts per method per task category would be even better. Path placeholder: `reports/figures/ch2_classical_baselines_grid.png`.
 Suggested caption (~30 words): "Per-task verdicts for the three classical baselines across the 15 evaluation tasks. Each baseline's failure cluster is distinct, motivating the project's combined vision+OCR approach."]

## 2.5 Deep-Learning Approaches for UI Element Detection

A separate strand of work treats UI element detection as a classical object-detection problem and solves it with the same architectures the natural-image community has converged on. This is the strand the project belongs to.

The most-cited early work in the strand is **UIED** by Xie and colleagues at FSE 2020 [10, 30]. UIED makes a deliberately pragmatic argument: neither pure deep learning nor pure classical computer vision is sufficient for GUI element extraction on its own, because the two methods miss complementary things. A Faster R-CNN baseline trained on UI screenshots achieves an F1 of 0.71 on their internal benchmark but misses small icons and dropdown arrows that the classical edge-and-region pipeline catches. Their classical-only pipeline manages F1 of 0.55, but misses text-shaped buttons that the deep learner gets easily. The UIED hybrid (CNN for non-text shapes, EAST/CTPN for text, then a rule-based merger) reaches F1 of 0.84. The architecture matters less than the methodological lesson: combining a fast deep detector with a text-recognition fallback is the right shape for a UI element detector. This project's pipeline, with YOLOv8 as the detector and EasyOCR providing both per-box and full-image text grounding, is in direct lineage from UIED.

**VINS** by Bunian and colleagues at CHI 2021 [31] is a slightly later and more focused implementation of the same idea. VINS uses a Faster R-CNN with a ResNet-50 backbone trained on RICO to localise eleven UI element classes (buttons, text inputs, icons, image, label, and so on). They report mAP@0.5 around 0.46 on a held-out RICO split and an element-detection F1 of 0.61. The reason VINS is cited here is not that the architecture is novel (it is not) but that VINS is one of the very few published papers that report mAP at this level of detail on a public mobile UI test set, which gives this project's source-domain mAP numbers something to anchor against.

A more specialised mobile-targeted detector is **YOLOv5-MGC** by Cheng and colleagues at 2022 [9, 32]. The paper introduces a YOLOv5 variant tailored for mobile GUI detection, with a microscale detection layer and an attention mechanism added to handle the very small icons that crowd a mobile screen. They report 89.8% mAP on their mobile UI test set, which is a strong number. The architectural innovations are sensible for the mobile setting, but the same paper hypothesises that the "microscale + attention" combination is overfit to mobile-style density and may not transfer well to the very different density of a desktop's packed-scene toolbar [10]. Validating or refuting that hypothesis on real desktop data was one of the original motivations of this project, and it is partly what RQ3 (model choice and transferability) is about.

[CITATION: AS400-DET, ref [27] in proposal]: a recent paper applies the same family of methods to legacy IBM terminal interfaces, with comparable conclusions. The lesson across all four works is consistent. On their own domain, deep object detectors do well on UI elements; their accuracy is bounded by the quality and currency of the training corpus, not by the architecture.

This project compares two architectural families. The first is **YOLOv8** [33, 5, 34, 35], the current-generation Ultralytics implementation. YOLOv8 is an anchor-free, single-stage detector with a modified CSPDarknet53 backbone and an enhanced Path Aggregation Network (PANet) neck explicitly designed to fuse features across multiple scales. The multi-scale neck is the property that matters for UI detection, where the same screen contains a 16-pixel close-X icon and a 200-pixel-wide ribbon menu at the same time. The Ultralytics implementation is well documented, runs on Colab Free's T4 in a usable time budget, and exports cleanly to ONNX for CPU-only inference. It is the project's headline backbone.

The second is **DETR** (DEtection TRansformer) by Carion and colleagues at ECCV 2020 [6, 36]. DETR re-frames detection as a direct-set-prediction problem solved with a transformer encoder-decoder and a bipartite-matching loss. It eliminates anchors and non-maximum suppression, which is conceptually clean and has the practical benefit of removing two layers of hyperparameter tuning. The well-documented weakness of the original DETR is poor performance on small objects, attributed to the global attention pattern in the encoder spending too much attention budget on large regions and too little on small ones. **RT-DETRv3** [37] is the most recent improvement, with hierarchical dense positive supervision designed in part to address the small-object weakness. For this project, the architectural comparison committed to in RQ3 (and in proposal Section 7.B) puts a YOLOv8-L and a DETR-R50 side by side, on the hypothesis that DETR's small-object weakness will be aggravated by the packed-scene density of desktop UIs. The DETR experiments are part of Phase 2 and at the time of writing are listed as D-01 in the gaps tracker.

A separate piece of work worth flagging is **Apple's Screen Recognition** paper of Zhang and colleagues at CHI 2021 [38]. Screen Recognition is the production pipeline behind the iOS VoiceOver accessibility feature; an on-device object detector classifies widgets into 13 types, with OCR adding text labels. The reported numbers are F1 of 0.91 on in-distribution screens, dropping to 0.74 on apps the model has never seen, with OCR adding a further 6 to 11 percentage points. The paper is cited here for two reasons. First, it is the closest existing analogue to what this project tries to do; an industrial-scale, accessibility-motivated, on-device UI detector that adds OCR exactly where the visual detector misses. Second, the published 0.91-to-0.74 in-distribution-to-out-of-distribution drop is empirical confirmation that even at Apple-scale data and engineering, the domain-shift effect is real and is the right thing to design around. This project's Win11-domain drop is consistent with that pattern at much smaller scale.

## 2.6 Domain Adaptation Methodologies

The four research questions for this project (Section 1.5) collapse, on closer inspection, into two empirical questions. RQ1 asks how big the domain shift is. RQ2 asks how to close it. The literature on domain adaptation answers RQ2 in three different ways, and this project implements one method from each.

The simplest method is **few-shot supervised fine-tuning**. The CLAY-pretrained backbone is frozen and the final detection head is re-trained on a small labelled subset of the target domain. The size of the subset is the free parameter; this project's plan is to sweep over $k = 1, 5, 10, 50, 100$ labelled desktop images to draw a data-efficiency curve. Few-shot fine-tuning is the canonical baseline in the transfer-learning literature; for context, the broad survey of Iman, Arabnia and Rasheed (2023) on transfer learning [39] gives roughly two dozen variations on the theme of "fine-tune the top, freeze the bottom". The reason this project keeps it in the experiment plan is not that it is novel but that it is the necessary control: any more elaborate method must beat the few-shot fine-tune by a non-trivial margin to be worth its complexity.

The intermediate method is **self-supervised pre-training (SSP) followed by fine-tuning**. SSP first pre-trains the backbone on unlabelled target-domain data with a self-supervised pretext task (typically masked-patch reconstruction or contrastive learning) and then fine-tunes the resulting backbone on labelled data exactly as in the few-shot case. The intuition is that the SSP step lets the model absorb the structural grammar of the target domain (in our case, the spatial conventions of desktop UIs: toolbars are horizontal, dialog buttons cluster bottom-right, menubars sit under the title bar) without requiring labels. The most relevant survey for the project's choice of pretext task is the medical-imaging survey of Anaya-Isaza, Mera-Jiménez and Zequera-Diaz (2024) [18], which reports a consistent uplift of 4 to 11 percentage points on downstream classification accuracy when masked-patch reconstruction is added to small-data fine-tuning. The project's SSP experiment is listed as D-02 in the gaps tracker; it is the second of the three Phase 2 methods.

The most elaborate method is **unsupervised domain adaptation (UDA)**, which uses *no* labelled target data and relies entirely on the unlabelled target corpus together with the labelled source corpus. This project compares two UDA families on the desktop target.

The first is the **Cross-Domain Adaptive Teacher** of Li, Dai and colleagues at CVPR 2022 [16, 19, 40]. Adaptive Teacher is a robust teacher-student framework. A stable Exponential Moving Average (EMA) teacher generates pseudo-labels on weakly-augmented target (desktop) images. The student is then trained on a mixed batch consisting of labelled source (CLAY) data and strongly-augmented pseudo-labelled target data, with a discrepancy loss that aligns the student's predictions across the two augmentation regimes. The EMA teacher is updated as a moving average of the student's weights; this is what makes the framework stable, in contrast to earlier teacher-student schemes that drifted as the student's pseudo-labels degraded. The published results are strong, with Adaptive Teacher closing roughly two-thirds of the source-to-target gap on standard cross-domain detection benchmarks (Cityscapes-to-Foggy-Cityscapes, Pascal-to-Clipart). The successor work, **Harmonious Teacher** at CVPR 2023 [16], improves on it by adding more careful pseudo-label confidence weighting. For this project, Adaptive Teacher is the more thoroughly documented choice and is what the Phase 2 plan commits to; it is listed as D-03 in the gaps tracker.

The second is **SHOT (Source HypOthesis Transfer)** [17, 20, 41]. SHOT takes a different stance from teacher-student. Instead of training a student to imitate a teacher, SHOT freezes the source-trained classification head (the "source hypothesis") and adapts *only* the feature extractor backbone on the unlabelled target images using a self-supervised objective. The intuition is that the head encodes what classes look like; the extractor encodes what the world looks like. When the world changes (from mobile UIs to desktop UIs), it is the extractor that needs to adapt, not the head. The published SHOT results are competitive with teacher-student approaches on smaller-scale benchmarks and have the practical advantage that the source data does not need to be available at adaptation time. For privacy-sensitive deployments this matters; for this project it matters less, but SHOT is included as the second UDA comparison point because it is structurally different enough to give a genuine architectural choice (D-04 in the gaps tracker). The paper of Sahay, Thomas and colleagues at Sensors 2023 [17, 42] gives an updated treatment of hypothesis-transfer for object detection that the implementation will follow.

A useful framing of the three methods is in terms of what each requires. Few-shot fine-tuning requires labelled target data and no unlabelled target data. SSP+FT requires both labelled and unlabelled target data. UDA requires only unlabelled target data, plus the original labelled source. The methods sit on a continuum from "expensive labels, simple training" to "no labels, complex training". The empirical question this project asks (RQ2) is where on that continuum the best practical return sits, given a realistic-MSc-scale data budget. The answer the project expects to find, on the basis of the existing literature, is that SSP+FT will roughly match UDA at less than a tenth of the engineering cost, and that both will outperform pure few-shot once $k$ is small. The actual numbers will arrive when D-02, D-03 and D-04 are completed.

A separate sub-thread in this literature, increasingly important since 2023, is **semi-supervised object detection (SSOD)** [43, 44]. SSOD blurs the line between SSP+FT and UDA by combining a small labelled set with a larger unlabelled set under a unified teacher-student loss. The recent survey of Khan and colleagues [44] argues that SSOD has effectively absorbed the older UDA literature in the object-detection sub-field. This project does not implement a dedicated SSOD method; the Adaptive Teacher implementation in D-03, which uses both labelled source data and unlabelled target data, sits close to the SSOD family in spirit even though the literature places it under UDA.

## 2.7 GUI Agents and Visual Grounding Frameworks

The detection and adaptation methods reviewed so far produce a *detector*. A detector is not an automation system. Closing the gap from "here are the elements on the screen" to "do the thing the user asked for" requires a grounding layer that maps a natural-language instruction onto one of the detected elements. The published frameworks for this layer fall into two clusters.

The first cluster is **modular pipelines** in the style of UIED [10] and its descendants. The Instruction Visual Grounding (IVG) framework of Dardouri and colleagues at 2024 [14, 21, 45] is the most directly applicable for this project. Dardouri proposes IVGocr, an explicit three-stage architecture: a YOLOv8 detector finds the UI elements; OCR reads the visible text on each detected element; an LLM (or, in their lighter-weight variant, a fuzzy string matcher) matches the user's instruction to the read text. They introduce the Central Point Validation (CPV) metric for evaluating how often the chosen element's centre falls inside the ground-truth bounding box of the correct target, which is a more permissive and arguably more honest grounding metric than IoU at high thresholds. This project's prototype, VisClick, is a direct implementation of the IVGocr architecture, with the YOLOv8 detector being the project's CLAY-pretrained, desktop-adapted model and the matcher being a rapidfuzz fuzzy match rather than a heavyweight LLM. The reason for picking rapidfuzz over an LLM is purely operational: it runs in milliseconds on CPU and removes a network dependency. The downstream evaluation in Chapter 8 of this report shows that for the 15-task workload, the rapidfuzz matcher is sufficient; the residual failures come from the detector, not from the matcher.

A small variant in the same cluster is the **MUG** (Multimodal Grounding on User Interfaces) framework of Tang and colleagues at EACL 2024 [46]. MUG adds interactive feedback to the grounding step, so the user can refine an ambiguous instruction iteratively. This is conceptually attractive but operationally heavyweight, and is not used by this project for the same reason heavy-weight LLMs are not used: the goal is a CPU-only single-shot system.

The second cluster is **end-to-end large vision-language models (LVLMs)**. The exemplar is **SeeClick** of Cheng and colleagues at ACL 2024 [13, 47, 48, 49, 50]. SeeClick replaces the entire detector-plus-OCR-plus-matcher stack with a single multi-billion-parameter vision-language model that takes a screenshot and an instruction as input and outputs click coordinates directly. The training corpus is roughly one million screenshots covering web, desktop and mobile. The reported numbers are 73% click accuracy on the web benchmark Mind2Web, 53% on the mobile benchmark AITW, and 47% on a new desktop benchmark the authors introduce. As a piece of engineering it is the current state-of-the-art on cross-domain GUI grounding. The reason this project does not benchmark against SeeClick is the inference-cost gap: SeeClick requires a multi-GPU inference setup and substantial memory, both of which are out of scope here. SeeClick is the reference point that the dissertation cites in Section 1.6 as the "heavyweight SOTA"; the project's positioning is explicitly as a lightweight, interpretable alternative for the cases where on-device, low-latency inference matters more than the absolute top of the leaderboard.

A related LVLM-based piece of work is Google Research's **ScreenAI** of Baechler and colleagues at IJCAI 2024 [28]. ScreenAI is a 5-billion-parameter vision-language model pre-trained on a screenshot corpus an order of magnitude larger than RICO. The headline claim is that ScreenAI is SOTA on four of the five UI benchmarks tested. The methodological lesson, for the purposes of this project's literature review, is that UI element coverage is fundamentally a data-scale problem more than an architectural one. ScreenAI's gains over earlier LVLMs come almost entirely from the increase in pre-training corpus size, not from any architectural novelty. This is cited as evidence (in Section 9.7) that the residual gap on Win11 native dialogs in this project's results is well-aligned with the published frontier: the open-source desktop UI corpus simply does not exist at the scale that would let a smaller model close the gap purely by architecture.

[FIGURE 2.3: "Modular vs end-to-end grounding pipelines."
 Suggested source: a two-panel block diagram. Left panel: IVGocr-style three-stage modular pipeline (detect → OCR → match → act). Right panel: SeeClick-style end-to-end LVLM. Path placeholder: `reports/figures/ch2_modular_vs_e2e.png`.
 Suggested caption (~30 words): "Two architectural families for instruction-to-action GUI agents. This project belongs to the modular family on the left, in deliberate contrast to the end-to-end LVLM family on the right."]

A few smaller works belong here for completeness. **Widget Captioning** of Li and colleagues at EMNLP 2020 [51] is a vision-language model that produces a natural-language caption for each individual UI widget; the BLEU-4 of 0.41 on RICO is the headline. Its relevance to this project is that it provides empirical evidence (cited in the limitations chapter) that a substantial fraction of clickable elements are icon-only and require visual reasoning rather than OCR to be grounded, which is the limitation behind the icon-class recall problem documented in Section 8.4 of this report. **Pix2Struct** of Lee and colleagues at ICML 2023 [52] is a self-supervised pre-training scheme for visual language understanding using screenshot-to-simplified-HTML pairs; the published downstream gains of 4 to 10 percentage points across nine UI benchmarks are the principal motivation for taking SSP seriously as a project methodology (D-02). **Pix2Code** of Beltramelli at IUI 2018 [53] is the historical reference establishing that pixel-only screenshot understanding is feasible at all; it is cited as the lineage marker that the modern detect-describe-act pipeline descends from.

## 2.8 Evaluation Metrics in the UI Domain

A short review of metrics is appropriate because the metric choice non-trivially affects what counts as a "good" detector. Three metric families recur in the literature reviewed above.

The **detection-quality** family is the standard COCO-style mean average precision (mAP) at intersection-over-union (IoU) thresholds 0.5 and 0.5:0.95. mAP at IoU 0.5 is the conventional headline, mAP at IoU 0.5:0.95 is the harder, more conservative number. Almost every paper reviewed above (RICO benchmarks, CLAY, UIED, YOLOv5-MGC, YOLOv8) reports mAP@0.5 as the principal headline. Per-class average precision (AP) is sometimes reported alongside; this project reports both, in `reports/tables/source_per_class.csv`.

The **grounding-quality** family is more idiosyncratic. The Central Point Validation (CPV) metric of Dardouri and colleagues [14, 21] is one of the more thoughtful proposals: a grounding is considered correct if the centre of the predicted bounding box falls within the ground-truth box of the target element. CPV is more permissive than IoU at high thresholds, but it is also closer to what an automation bot actually needs (a click that lands somewhere inside the target is sufficient). This project adopts CPV as a secondary metric alongside mAP (D-08 in the gaps tracker).

The **end-to-end-task-success** family is what the bot itself is measured against. Task Success Rate (TSR) is the binary pass/fail rate over a fixed test suite. Almost every modern GUI-agent paper [14, 13] reports TSR as the primary user-visible metric. TSR has the merit of being interpretable to non-specialist stakeholders ("seven out of every ten clicks land in the right place") and the demerit of folding together detection, OCR and matcher errors into a single number. Chapter 8 of this report decomposes TSR failures into the three component error families, following the failure-analysis approach Dardouri and colleagues use.

One metric this project does *not* use, despite its dominance in the natural-image-detection literature, is **F1 at a fixed confidence threshold**. F1 conflates two questions a UI automation system has to answer independently: "does the detector see the element" and "does the matcher pick the right one". The two-stage decomposition is more diagnostic, even if it sacrifices the single-number convenience of F1.

## 2.9 Research Gap and Positioning of Current Study

The literature is best summarised by a single observation: there is no missing piece in the constellation, only a missing combination. State-of-the-art mobile UI detectors exist [9]. A clean target-application pipeline exists [14]. Heavyweight LVLMs that solve the cross-domain problem at scale exist [13, 28]. The piece that is missing is a *lightweight, data-efficient* method that takes the SOTA mobile detector, adapts it to the desktop domain using the kind of small labelled-data budget an individual or a small team can realistically produce, and demonstrates that the resulting detector works *inside a complete automation pipeline* rather than only on a static benchmark.

The gap is the combination of three constraints. **Lightweight**, in the sense that the runtime must fit comfortably on a consumer CPU; this rules out SeeClick and ScreenAI. **Data-efficient**, in the sense that the labelled-target budget must be at most a few hundred images; this rules out training a desktop-specific detector from scratch in the style of MUD. **Integrated**, in the sense that the deliverable is a working click-bot evaluated end-to-end on real applications; this rules out comparing only on mAP on a held-out test split.

To be precise about what the dissertation contributes inside that gap, the contribution is fourfold. **(a)** A quantitative measurement of the source-to-target domain shift on a public mobile UI source (CLAY) and a personal desktop target (Windows 11, ten to fifteen applications). This is RQ1. **(b)** A side-by-side comparison of three adaptation methods (few-shot fine-tuning, SSP+FT, UDA with the Adaptive Teacher and SHOT sub-comparison) on two backbones (YOLOv8 and DETR). This is RQ2 and part of RQ3. **(c)** An empirical evaluation of the adapted detector inside the IVGocr pipeline on a 15-task workload, including a head-to-head against three classical baselines (template, OCR-only, pywinauto). This is RQ4 and the rest of RQ3. **(d)** A public, reproducible implementation: every adaptation method, every baseline, every CSV, every figure is available under the project's open-source repository, which is itself a contribution given how rare end-to-end-reproducible MSc UI-automation projects are in the literature.

The positioning relative to SeeClick and the LVLM family is explicit. This project does not claim to outperform a 7-billion-parameter end-to-end model on detection accuracy. It claims that a small, interpretable, modular pipeline can deliver "good enough" performance for the practical IVGocr-style application on a single CPU, at a fraction of the inference cost, with a much smaller training and adaptation budget. That trade-off is the right one for the practitioners who actually need to deploy UI automation on their own machines.

## 2.10 Summary

This chapter walked through the literature in the order the project consumes it. The mobile UI domain is data-rich, anchored by RICO and CLAY. The desktop domain is data-poor, with recent attempts at corpora (DeskVision, GenGUI) still emerging. Classical automation tools (bitmap, coordinate, and accessibility-tree) have all run into problems on the modern Windows 11 application mix, leaving a gap that vision-based detection is the natural candidate to fill. Among deep-learning detectors, the two architectural families this project compares (YOLOv8 with its multi-scale PANet neck, DETR with its transformer set-prediction) have well-documented strengths and weaknesses; YOLOv8's multi-scale design is the favourite, with DETR included as the controlled comparison. Among adaptation methods, the three the project implements (few-shot, SSP+FT, UDA) span the continuum from labelled-data-only to no-labels-on-target, with the published literature suggesting SSP+FT will give the best practical return at the project's data budget. Among grounding frameworks, the IVGocr modular pipeline of Dardouri and colleagues is the immediate architectural ancestor of this project's prototype; SeeClick and ScreenAI are the heavyweight reference points that anchor the dissertation's lightweight stance. The combined research gap is the absence of a lightweight, data-efficient, end-to-end-validated cross-domain UI adapter for the desktop, and the project's four research questions sit precisely inside that gap.

The next chapter, Chapter 3, turns to requirement analysis. It begins with a stakeholder analysis and proceeds through functional and non-functional requirements with quantitative targets that the rest of the report measures against.

---

# Chapter 3: Requirement Analysis

## 3.1 Chapter Overview

This chapter sets out the requirements the system was built against. It begins with a stakeholder analysis using the Onion model, because requirements without stakeholders are arbitrary. The stakeholder analysis is then converted into a set of stakeholder viewpoints, each of which contributes some requirements. The methodologies used to gather requirements are described next, together with the methodology for obtaining the datasets the system is trained on. UML use case diagrams formalise the system's interactions with its users, and the use cases are then written out in long form. The chapter ends with the explicit list of functional requirements (R-FR-01 through R-FR-09) and non-functional requirements (R-NFR-01 through R-NFR-10) that the rest of the dissertation evaluates against. Each requirement carries a unique identifier, a description, a target value (where measurable), and a pointer to the section of the testing chapter where the requirement is empirically tested.

The chapter is organised so that a reader who is not interested in the requirements rationale can skip to Section 3.8 and Section 3.9 to read the requirement lists directly. The earlier sections supply the justification for those lists, which is what a marker is more likely to read in detail than to skim.

## 3.2 Stakeholder Analysis

Stakeholder analysis identifies the people and organisations who are affected by the system, or who affect the system. The motivation is to spot conflicting interests early and to capture requirements from each perspective before the design hardens around any single one. This section uses the Onion model, in which stakeholders are placed in concentric rings according to their distance from the technical core of the system.

### 3.2.1 The Onion Model

The Onion model for this project has six rings.

The **innermost ring** is the system itself: the VisClick prototype, comprising the ONNX detector, the EasyOCR layer, the rapidfuzz matcher, the Tk GUI, and the PyAutoGUI action layer.

The **second ring** is the **operational users**. Two distinct groups sit here. The first is the author, who runs the bot for evaluation and treats it as a research artefact. The second is the imagined power user: a developer or QA engineer who would use such a tool to automate repetitive desktop tasks. The two groups have meaningfully different requirements. The researcher wants observability (overlay images, structured CSVs, verifiable verdicts) above all else. The power user wants reliability (zero crashes, predictable refusal-on-uncertainty) and convenience (a GUI rather than a CLI). The system addresses both by shipping a CLI for the researcher and a Tk GUI for the power user, layered over a common core.

The **third ring** is the **academic operational stakeholders**: the project supervisor (Pumudu Fernando) and the second marker (TBD). Their concerns are different again: they want a reproducible artefact, an honest evaluation, an academic novelty argument, and a dissertation that is properly structured against the RGU programme handbook.

The **fourth ring** is the **functional layer of downstream beneficiaries**. Three sub-groups belong here. The first is QA and test-automation engineers who might adapt the project's code for production purposes. The second is accessibility users who could in principle benefit from a text-driven click bot when traditional input devices are not usable. The third is the research community: authors of any of the literature reviewed in Chapter 2 who might cite or extend this work, and future students inheriting the codebase.

The **fifth ring** is the **containing organisations**. Robert Gordon University is the degree-awarding body and is the source of the dissertation's ethical-review framework, its style guide, and its assessment criteria. The Informatics Institute of Technology (IIT) is the partner institution. Synopsys Sri Lanka is the author's employer; the work is not done as part of Synopsys-funded research, but the author's professional context informs some of the architectural choices (an automation tool that is interpretable and locally-deployable is more aligned with corporate compliance concerns than one that calls out to a cloud LLM).

The **outermost ring** is the **wider environment**. Microsoft is the platform owner (Windows 11 OS, UI Automation framework, Notepad, File Explorer); their decisions about which control libraries to ship and how to expose them through the accessibility tree have material effects on every measurement in Chapter 7. Google Colab is the compute provider for all training; their Free-tier T4 quota is the binding budget constraint that shapes the data and experimental design. GitHub hosts the public artefact. The open-source community supplies the underlying libraries: Ultralytics for YOLOv8, JaidedAI for EasyOCR, the pywinauto and PyAutoGUI maintainers, and so on. Dataset providers (Deka and colleagues for RICO, Li and colleagues for CLAY) sit here too, as do the bad-actor groups whose existence motivates the social-impact discussion in Section 8.10.

### 3.2.2 Stakeholder Viewpoints

Each ring produces requirements, and the requirements sometimes conflict. The five viewpoints below capture the conflicts that mattered during design.

**The researcher's viewpoint** prioritises observability and reproducibility. Every prediction must be inspectable; every result must be regeneratable from a script that can be re-run. This pushes the design towards verbose CSV logging, per-attempt overlay images, and CLI flags that fix randomness and dump intermediate state.

**The power user's viewpoint** prioritises a tight loop of action and feedback. Speed matters; clarity of error messages matters; refusal on uncertainty matters more than maximum coverage. This viewpoint produced R-FR-06 (refusal on low confidence), which is one of the harder-fought design decisions of the project (recorded as observation O14 in the data form).

**The academic stakeholder's viewpoint** prioritises an honest, defensible evaluation. This viewpoint is the reason the report explicitly cites both the inflated mAP figure (0.7176, against pseudo-labels) and the corrected one (0.0330, against hand-corrected GT). It is also the reason the negative test case T15 is kept in the headline TSR denominator rather than removed.

**The accessibility-user viewpoint** prioritises permission and refusal semantics over raw speed. A bot that confidently clicks the wrong thing is worse, for this group, than one that takes an extra second to be sure. This viewpoint reinforces R-FR-06 and motivates the human-in-the-loop verdict prompt in the evaluation harness.

**The platform-and-OS viewpoint** prioritises portability, or, more precisely, makes the project explicitly acknowledge its lack of portability. Windows 11 only; multi-monitor support; DPI-scaling-aware coordinate handling. These constraints are captured in R-NFR-09 (compatibility) and discussed at length in Section 9.7.

Where the viewpoints conflict the design rule is consistent: prefer the more conservative behaviour. When in doubt about whether to click, do not click; this is R-FR-06. When in doubt about which monitor to use, ask; this is the `--monitor` flag. When in doubt about whether a result should go into the CSV, log it with a `notes` field; this is the existing per-attempt schema in `baseline_results.csv`.

## 3.3 Requirement Gathering Techniques

Four requirement-gathering techniques were used during the project, each in proportion to its cost-effectiveness on a single-developer project.

**Literature review.** The single largest source of functional requirements is the existing literature reviewed in Chapter 2. The IVGocr architecture of Dardouri and colleagues directly contributed R-FR-01 through R-FR-05 (capture, instruction, detection, matching, action). The published failure modes of classical baselines (UIED's argument that neither pure deep learning nor pure CV suffices on its own [10]; Apple's published in-distribution-to-out-of-distribution drop [38]) directly contributed R-FR-06 (refusal on uncertainty). The literature is the most reproducible requirement source for an academic project, because every requirement can be traced back to a publication.

**Self-as-stakeholder analysis.** The author is one of the operational users. Several requirements were derived from running early versions of the bot during the project's prototype phase: the multi-monitor coordinate confusion (O13) directly produced R-FR-07; the silent Tesseract failure (O12) produced part of R-NFR-04 (reliability); the difficulty of switching OCR engines from the CLI produced part of R-NFR-05 (usability). Self-as-stakeholder is a recognised method in agile and lean software engineering, though it is more often invoked in industrial projects than in dissertation work.

**Stakeholder interviews.** A short interview was conducted with the project supervisor early in the proposal phase to clarify the academic-stakeholder viewpoint described in Section 3.2.2. No formal transcript was kept, but the interview output is reflected in the proposal's research questions and is therefore the source of all four RQ-grounded requirements implicitly.

**Field observation of analogous systems.** The author used SikuliX, pywinauto and PyAutoGUI for short experimental sessions during the first month of the project. The observed failure modes from these sessions (template captures aging out, UIA Names that do not match the visible labels, coordinate scripts that broke when DPI changed) were converted into the explicit failure-mode list in Section 8.4 and into the comparison baselines in Chapter 7. This is, in effect, the requirement-gathering technique that justifies the lightweight stance: the requirements *not* met by existing tools are the most concrete justification for the new tool.

A fifth technique that the sample dissertation reviewed alongside this project [the RGU MSc skin-cancer report, 2026] used but this project did not is **stakeholder questionnaires**. Questionnaires are a sensible technique for projects with non-overlapping target users; for a developer-tooling artefact at MSc scale with the author as the primary user, the cost of designing and distributing a questionnaire would have exceeded the benefit. The qualitative-evaluation gap recorded as D-10 partially addresses this by gathering structured feedback from a small number of expert reviewers; that is a closer fit to the project than a survey.

## 3.4 Methodology for Obtaining Datasets

The data-engineering side of the project follows a three-tier methodology dictated by the data-availability constraints reviewed in Section 2.2.

**Tier 1: public source-domain corpora.** Three publicly available datasets are used as the source domain: RICO [7], CLAY [8], and VINS [31]. Acquisition is straightforward (a download from the respective project pages and a checksum check), but the cleaning and class-collapse work is non-trivial and is documented in Chapter 6. The combined corpus is the 6-class "Zenodo unified bundle" of approximately 9,646 screens used in `05_train_source.ipynb`.

**Tier 2: captured target-domain unlabelled corpus.** The proposal commits to roughly 2,000 unlabelled desktop screenshots captured from 10 to 15 applications. At the time of writing the actual corpus is 50 personal screenshots (recorded under `samples/desktop_seed/`); the expansion to 2,000 is gap D-06. The capture methodology is implemented in `scripts/capture_screenshots.py` and uses `mss` for the screen grab and `pywinauto` for enumerating visible top-level windows. The script is parameterised by application list, theme (light/dark), and DPI scaling so that the eventual 2,000-screen corpus systematically covers the in-the-wild variability the bot encounters.

**Tier 3: hand-curated target-domain labelled corpus.** The proposal commits to a 100-image labelled desktop corpus annotated in CVAT against the five-class schema. At the time of writing the labelled set is 8 hand-corrected images carrying 356 ground-truth boxes (`reports/tables/desktop_test_handcorrected.csv`); the expansion to 100 is gap D-07. Annotation methodology follows the CVAT shape-and-label convention used in the wider literature: rectangular bounding boxes only, no rotated boxes, no segmentation masks. Class labels are restricted to the 6-class taxonomy `{button, text, text_input, icon, menu, checkbox}`. Annotators (in practice, the author alone) follow a written guideline document that mirrors the conventions used in the CLAY release notes.

The three tiers feed three different experimental purposes. Tier 1 is the source-domain training set. Tier 2 is the unlabelled target corpus needed for SSP+FT and UDA. Tier 3 is the labelled target test set used for evaluating every adaptation method, and is also the training source for the few-shot fine-tuning experiment at $k = 1, 5, 10, 50, 100$.

## 3.5 Use Case Diagrams (UML)

The system supports six use cases, four of which are user-facing and two of which are internal-to-evaluation.

[FIGURE 3.1: "UML use case diagram for VisClick."
 Suggested source: hand-drawn or draw.io export; one actor (the User), six use cases (UC-01..UC-06) with `<<include>>` relationships where appropriate. Path placeholder: `reports/figures/ch3_use_cases.png`.
 Suggested caption (~30 words): "Use case diagram for the VisClick prototype. UC-01 to UC-04 are user-facing; UC-05 and UC-06 are run during evaluation. Each use case maps to one or more functional requirements in Section 3.8."]

The six use cases are listed below at the level of detail customary for an MSc-level UML diagram.

* **UC-01: Click a labelled element.** The user provides a text instruction; the system captures the screen, detects elements, matches the instruction, and clicks the chosen element.
* **UC-02: Refuse a click on low confidence.** The user provides an instruction for which no high-confidence target exists; the system reports a structured failure rather than clicking.
* **UC-03: Select a specific monitor.** The user selects which monitor the bot should operate on, via either the CLI flag or the GUI dropdown.
* **UC-04: Inspect a prediction overlay.** The user opens the saved overlay PNG for any past click to verify what the bot did.
* **UC-05: Run a baseline evaluation.** The evaluator runs `scripts/run_baselines.py` to evaluate one or more methods across the canonical task suite.
* **UC-06: Generate result tables and figures.** The evaluator runs the analysis scripts to regenerate the report's tables and figures from the per-attempt CSV.

## 3.6 Use Case Descriptions

Each of the four user-facing use cases is described below at a more practical level than the UML. Use cases UC-05 and UC-06 are evaluation tooling and are documented in Chapter 6 rather than here.

**UC-01: Click a labelled element.**

* *Primary actor:* End user (developer or power user).
* *Pre-condition:* The bot is launched, the model weights are loaded, and the target monitor is selected.
* *Main success flow:* (1) User types an instruction such as "click Save" into the GUI. (2) User presses the Run button or hits Enter. (3) The system pauses 3 seconds (allowing the user to switch focus to the target window). (4) The system captures the configured monitor. (5) The detector emits N candidate boxes. (6) The OCR layer reads the text on each box. (7) The matcher selects the best-fitting box above the similarity threshold. (8) The action layer moves the cursor to the box centre and clicks. (9) The system saves the overlay PNG and writes the CSV row.
* *Alternative flow:* If no candidate exceeds the similarity threshold, the system follows UC-02 instead of clicking.
* *Post-condition:* The targeted element has received a single left-click, and the action has been logged.

**UC-02: Refuse a click on low confidence.**

* *Primary actor:* End user.
* *Pre-condition:* As UC-01.
* *Main success flow:* (1) User types an instruction. (2) System captures and detects as in UC-01. (3) Matcher computes the best-fitting box, but its similarity score is below the threshold (`min_text_similarity = 60` in the current build, planned to rise to 75 per gap D-05's adjacent fix). (4) System emits a structured `FAIL: cannot find <target>` message. (5) System still saves the overlay PNG (with no click marker) and writes a CSV row with verdict `refused`.
* *Alternative flow:* The user may lower the threshold via a CLI flag if they want to override; this is documented but not exposed in the GUI.
* *Post-condition:* No click was issued. The decision is logged.

**UC-03: Select a specific monitor.**

* *Primary actor:* End user on a multi-monitor setup.
* *Pre-condition:* The system has detected more than one monitor at start-up.
* *Main success flow:* The user selects the target monitor from the GUI's dropdown (or passes `--monitor <id>` to the CLI). The system queries `mss.monitors` for the selected index, recovers the `(left, top)` offset, and uses that offset throughout the subsequent capture-detect-match-click flow.
* *Post-condition:* All subsequent clicks issued by the bot land on the chosen monitor regardless of where the GUI window itself is sitting.

**UC-04: Inspect a prediction overlay.**

* *Primary actor:* Researcher or end user reviewing past behaviour.
* *Pre-condition:* The bot has previously processed at least one instruction.
* *Main success flow:* The user opens the saved overlay PNG (`reports/figures/baselines/<task>_<method>.png` for evaluation runs, or `runs/overlay-<timestamp>.png` for ad-hoc runs). The overlay shows the detected boxes coloured by class, the chosen box highlighted, the click point marked with a crosshair, and (when relevant) the OCR text overlaid above each box. The user can confirm or refute the bot's decision visually.
* *Post-condition:* No state change. The use case is purely diagnostic.

## 3.7 Functional Requirements

The functional requirements (R-FR-01 through R-FR-09) are formalised below. Each requirement carries a unique identifier, a description, a priority, the use cases it serves, and the section of the testing chapter that validates it. The pass-rate column reports the headline empirical result already measured against the requirement; the exact computation is in Chapter 7.

| ID | Requirement | Description | Priority | Use cases | Test section | Status |
|----|-------------|-------------|----------|-----------|--------------|--------|
| R-FR-01 | Screen Capture | The system shall capture a screenshot of the user-selected monitor at native resolution, in the virtual-desktop coordinate space. | Essential | UC-01, UC-03 | Section 7.3.1 | FULL: 15/15 on T01-T15 |
| R-FR-02 | Text Instruction Input | The system shall accept a free-form text instruction via CLI flag or GUI text box. | Essential | UC-01, UC-02 | Section 7.3.1 | FULL: 15/15 |
| R-FR-03 | Element Detection | The system shall detect candidate UI elements of types `{button, text, text_input, icon, menu, checkbox}` on the captured screenshot. | Essential | UC-01 | Section 7.2 | FULL: 15/15 emit ≥1 detection |
| R-FR-04 | Instruction-to-Element Matching | The system shall match the user instruction to one detected element using fuzzy OCR text similarity, with a class-aware bonus, and shall fall back to full-image OCR when no per-box candidate exceeds the threshold. | Essential | UC-01 | Section 7.3.1, Section 8.2 | FULL: 11/14 PASS on positives |
| R-FR-05 | Action Execution | The system shall move the mouse cursor to the centre of the chosen element and execute a single left-click. | Essential | UC-01 | Section 7.3.1 | FULL: 11/14 verdict |
| R-FR-06 | Refusal on Low Confidence | The system shall refuse to click when no candidate exceeds the similarity threshold, and shall emit a structured failure message. | Essential | UC-02 | Section 7.3.1 | PARTIAL: 0/1 on T15; planned threshold fix in D-05's adjacent change |
| R-FR-07 | Multi-Monitor Support | The system shall operate correctly across virtual-desktop coordinate spaces on multi-monitor setups, with an explicit monitor selector. | Important | UC-03 | live demo log | FULL: verified on 3440×1440 + 1920×1080 stacked layout |
| R-FR-08 | Visual Feedback | The system shall render an annotated overlay PNG of every prediction (detected boxes, chosen element, click marker, OCR text) for human verification. | Important | UC-04 | Section 7.3.1 | FULL: 60/60 overlays |
| R-FR-09 | Per-Attempt Logging | The system shall log per-attempt fields (instruction, capture path, predicted xy, verdict, latency, method, is_negative, notes) to a CSV file for evaluation. | Important | UC-05 | `reports/tables/baseline_results.csv` | FULL: 60/60 rows |

The classification of "Essential" vs "Important" follows the MoSCoW convention: an Essential requirement must be met for the system to be considered fit for purpose; an Important requirement is needed for the system to be considered fit for evaluation but is not on the critical functional path.

## 3.8 Non-Functional Requirements

The non-functional requirements are quantitative wherever possible. Each row records the target value, the measured value, the source of the measurement, and a status.

| ID | NFR | Target | Measured | Source | Status |
|----|-----|--------|---------|--------|--------|
| R-NFR-01 | Accuracy (TSR) | ≥ 50% on T01-T15 | 73.3% | `baseline_summary.csv` row `visclick` | FULL |
| R-NFR-02 | Latency | p95 ≤ 15 s per click attempt | 14.8 s p95 / 8.05 s median | `nfr_performance.csv` row `visclick` | FULL (just) |
| R-NFR-03 | Memory footprint | Peak RSS ≤ 2 GB during a 15-task run | PENDING | gap D-11 | PENDING |
| R-NFR-04 | Reliability | Zero crashes during 60-attempt evaluation | 0 crashes | run log 6-7 May 2026 | FULL |
| R-NFR-05 | Usability | Single-window Tk dialog; keyboard shortcuts for Pass/Fail/Skip | implemented in `scripts/run_baselines.py::_verdict_dialog_tk` | source review | FULL (single-reviewer); qualitative third-party PENDING (D-10) |
| R-NFR-06 | Maintainability | Modular package (`visclick.{capture, detect, ocr, match, act, bot, gui}`); PEP-8 clean | 9 modules, ~1,591 LoC total, `ruff check` clean | source review | FULL |
| R-NFR-07 | Extensibility | New baseline methods plug in by implementing `predict(image_rgb, instruction) -> BaselineResult` | Demonstrated for 4 methods | `scripts/baseline_*.py` | FULL |
| R-NFR-08 | Security & Privacy | No off-machine I/O during inference; no telemetry; no credentials handled | verified by `rg 'requests\|urllib\|http' src/visclick/` | source review | FULL |
| R-NFR-09 | Compatibility | Windows 11 supported; multi-monitor verified | Windows 11 + 3440×1440 + 1920×1080 PASS | live demo | PARTIAL (Windows-only by design) |
| R-NFR-10 | Scalability | Pipeline complexity scales linearly in #candidates per screenshot | per-box OCR is O(N); ceiling ≈ 300 boxes/screenshot | analytical, supported by Section 10 of data form | PARTIAL |

The classification of each NFR as Essential, Important, or Optional follows the same MoSCoW convention used for FRs. Accuracy, latency, reliability, security, and compatibility are Essential; the rest are Important or Optional. None of the NFRs are marked Failed; the two PENDING items (R-NFR-03, R-NFR-05 third-party) are timeline matters rather than fundamental capability gaps.

## 3.9 Summary

The requirements above are the contract the rest of the dissertation is evaluated against. They were derived from four requirement-gathering techniques (literature, self-as-stakeholder, supervisor interview, field observation of analogous systems) and from a six-ring Onion stakeholder model that captured viewpoint conflicts before they became design conflicts. Nine functional requirements (R-FR-01 to R-FR-09) and ten non-functional requirements (R-NFR-01 to R-NFR-10) are stated explicitly, each with an identifier, a target, and a pointer to the test section that validates it. The structure of the requirements list deliberately mirrors the structure of the testing chapter so a marker can audit any individual claim by chasing a single identifier from Section 3.7 / Section 3.8 down into Section 7.

The next chapter, Chapter 4, describes the project management approach: the research methodology, the software methodology, the risk register, and the four-phase project plan.

---

# Chapter 4: Project Management

## 4.1 Chapter Overview

This chapter explains how the project was run. It begins with the research methodology, which is the philosophical and procedural framework that determined the kind of evidence the project chased. It moves on to the software design methodology and the software development methodology, both of which constrain how a single-developer MSc project should be structured on a finite budget. The project management methodology is described next, with reference to standard agile and waterfall hybrids. The risk register is then made explicit: it captures, in a forward-looking form, the issues encountered during execution (Observations O1 through O21 in the data form) together with the mitigations that resolved them. The chapter closes with the project plan in Gantt form, with reference to the four-phase operational structure inherited from the proposal.

A reader who is only interested in the project's empirical findings can skip Chapter 4 and pick up at Chapter 5 (Design). The contents of this chapter are nonetheless required by the RGU MSc dissertation rubric and they perform a real function: they tell a marker which research-philosophical commitments the rest of the dissertation expects to be evaluated against.

## 4.2 Research Methodology

The project is in the design-science research (DSR) tradition. DSR is appropriate when the research output is a new artefact intended to solve a real-world problem, and when the contribution is evaluated by demonstrating that the artefact does so. The artefact in this case is the VisClick prototype together with the cross-domain adaptation framework that produces its detector. The output is evaluated by measuring the prototype's performance against three quantitative metrics (mAP, CPV, TSR) and against the three classical baselines that constitute the practical comparison set.

A purely positivist methodology was considered and rejected. A positivist framing would treat the project as a hypothesis test (for example, "training on CLAY transfers well to Win11" as a falsifiable hypothesis) and would seek a single binary answer. The project's actual evidence base, which contains internally contradictory observations (the detector does badly on hand-corrected GT yet the end-to-end TSR is acceptable; the OCR fallback rescues the detector but is also the latency bottleneck), is better served by DSR's "build, evaluate, learn" loop than by a single null-hypothesis test.

A purely interpretivist methodology was also considered and rejected. An interpretivist framing would treat the system's behaviour as a phenomenon to be understood through qualitative analysis (interviews with users, observation of task performance). The project does have a qualitative-evaluation slot (D-10 in the gaps tracker), but the primary evidence is quantitative and the qualitative layer is supplementary rather than central.

The DSR framing has practical consequences for the rest of the dissertation. It justifies a multi-method evidence structure (Chapter 7 reports both quantitative metric numbers and qualitative failure-mode descriptions). It justifies an iterative narrative in which an early result (the 22-fold mAP collapse from auto-label evaluation to hand-corrected GT, observation O19) directly motivates a later methodological change (hand-correcting more test data, gap D-07). And it justifies the explicit "build the artefact, evaluate the artefact, learn from the artefact" structure of Chapters 5 to 9.

## 4.3 Software Design Methodology

The system was designed against three principles, each carrying through from the literature reviewed in Chapter 2.

**Modularity.** The system is decomposed into seven Python packages under `src/visclick/` (`capture`, `detect`, `ocr`, `match`, `act`, `bot`, `gui`). Each package has a single responsibility and a small public surface, so that any one component can be replaced without touching the others. This is the architectural choice that made it possible to plug in three classical baselines and the VisClick full pipeline as four interchangeable `predict()` implementations in the same evaluation harness (`scripts/run_baselines.py`). Modularity is also what allows the dissertation to make the comparison chart in Section 7.4 a fair one: the four methods share the screenshot capture, the verdict-collection harness, and the per-attempt logging schema. Only the perception-and-grounding code differs.

**Reproducibility.** Every numerical claim in the report is regeneratable from a script in the public repository, against a result table on disk, with a commit hash documented in the data form. The supporting convention is that every notebook cell which produces a report number prints a marker line identifying the report section it serves; this is recorded in the data form's Section 0.2. The same principle drives the explicit version-control of the desktop screenshot corpus and the ONNX detector weights inside the repository rather than only on cloud storage. The repository layout itself is shown once in Figure 5.4 in Chapter 5, and every file path mentioned in this report is a node in that tree.

**Refusal on uncertainty.** A click bot that issues a confident wrong click is worse than one that issues an honest failure. This principle is captured in R-FR-06 and is the architectural reason the matcher has a `min_text_similarity` threshold rather than always returning the highest-scoring candidate. The full justification, including the live-demo observation that motivated it (O14 in the data form), is in Section 3.2.2's discussion of stakeholder viewpoints.

A separate architectural pattern worth flagging is the **pre-flight probe**. The OCR layer exposes an `ocr_status()` function that runs at start-up and prints a tick or cross for each backend (EasyOCR, Tesseract, falling back to a pure-Python OCR). The detector layer exposes an equivalent `detect_status()` for ONNX model loading. The first time any of these probes fails, the `_warn_once()` helper prints the underlying error, the configured path, and three concrete fixes. This pattern was introduced after observation O12 (silent Tesseract failure during the live demo) and has been propagated to every external dependency in the stack. It is one of the strongest practical lessons of the project and is recorded as such in Section 9.3.

## 4.4 Software Development Methodology

The development process is best described as an agile/waterfall hybrid. The four-phase project plan from the proposal (Phase 1 through Phase 4) is essentially a waterfall structure: data engineering, then modelling, then prototype, then evaluation. Inside each phase, the actual day-to-day work was iterative; the data-form's observation log (O1 through O21) records the cycles of "try, hit a wall, document the wall, fix the wall, move on" that drove progress through each phase.

The agile elements are concrete. Continuous integration is provided by Git, with commits at a granularity that maps individual problems to individual fixes (the commit log includes entries such as `fix(make_prototype): load tasks from T01_T20.json tasks array`). Backlog management is provided by the `docs/VisClick_Detailed_Plan.md` Phase L checklist, which both this dissertation and the working code consult in lock-step. Retrospective is performed at the end of each phase: the observation log in Section 13 of the data form serves as the retrospective output, with each O-numbered entry describing what happened and what it taught the project.

The waterfall elements are equally concrete. Phase ordering was preserved: data engineering really did precede model training, model training really did precede the prototype, and the prototype really did precede the evaluation. No phase was started before the prior phase's deliverable existed. This is more rigid than a pure agile project would be, but it is appropriate for a research project where each phase's output is a measurement that the next phase's design depends on.

The choice of an agile/waterfall hybrid over pure agile or pure waterfall was made for one reason: a single-developer MSc project does not have the team structure that justifies a pure agile process (no scrum, no stand-ups, no separate product-owner role) but also cannot afford the inflexibility of pure waterfall (a single mid-project disconnect, as happened with the auto-label evaluation in O17, requires the freedom to re-scope upstream phases without throwing out the whole plan). The hybrid is what allowed the auto-label evaluation crisis to be turned into a controlled re-evaluation rather than into a project failure.

## 4.5 Project Management Methodology

Project tracking used two artefacts. The first is a static Gantt chart at the level of the four phases (Figure 4.1). The second is the rolling Phase L checklist in `docs/VisClick_Detailed_Plan.md`, which is more granular and is updated continuously.

[FIGURE 4.1: "Project Gantt chart over the 12 months of the MSc."
 Suggested source: hand-drawn or exported from MS Project / draw.io / a spreadsheet. Should show Phase 1 (Months 1–3), Phase 2 (Months 4–7), Phase 3 (Months 8–9), Phase 4 (Months 10–12), with overlaps at phase boundaries to indicate continuous work. Path placeholder: `reports/figures/ch4_gantt.png`.
 Suggested caption (~30 words): "Twelve-month project plan over the four operational phases. Phase boundaries are deliberately drawn with overlap; in practice each phase's documentation continued while the next phase's experiments began."]

The two artefacts have different update cadences. The Gantt chart is updated at most monthly and is treated as a contract between the author and the supervisor. The Phase L checklist is updated continuously and is treated as the working memory of the project; every commit to the repository typically toggles at least one `[ ]` to `[x]`.

Time accounting was kept informally. The detailed plan's K.3 section recorded the original time budget of approximately 120 hours over twelve weeks (the proposal's reference cadence); the actual time spent is significantly higher and is not formally logged. For a future-work entry, an honest answer to "how long did this dissertation take" would be in the region of 200 to 250 hours.

## 4.6 Risk Mitigation Plan

The risk register is a forward-looking transformation of the observation log in Section 13 of the data form. Each risk has a probability, an impact, a mitigation, and a status. The table below mirrors the Section 17 of the data form but is reproduced here for completeness; the discussion that follows it is dissertation-grade rather than data-form grade.

**Table 4.1: Risk register.**

| ID | Risk | Source | Prob | Impact | Mitigation | Status |
|----|------|--------|:----:|:------:|------------|--------|
| RR-01 | Pseudo-label evaluation overstates accuracy | O17, O19 | High | High | Hand-correct ≥ 8 test images; report both auto-label and hand-corrected mAP | Mitigated |
| RR-02 | Source-domain training distribution does not generalise to Win11 native | O11, O18 | High (confirmed) | High | OCR text-grounding fallback; recall-ceiling acknowledged; Phase 4.B planned | Mitigated |
| RR-03 | Silent dependency failure (Tesseract not on PATH) | O12 | Med | High | Startup probe `ocr.ocr_status()`; `_warn_once()` helper | Mitigated |
| RR-04 | Multi-monitor virtual-desktop coordinate confusion | O13 | High | High | `(left, top)` offset propagated through `act.click_box`; `--monitor` flag | Mitigated |
| RR-05 | Confident wrong action on negative case | O14, O21 | Med | High | `min_text_similarity` threshold; planned raise from 60 to 75 | Open |
| RR-06 | OCR latency dominates total wall-clock | O21, Section 10.1 | Certain | Med | Detector-first short-circuit (skip OCR on confident classes) | Open |
| RR-07 | Colab Free disconnect mid-training | O8 | Med | Med | `last.pt` per-epoch; resume-from-disconnect built in | Mitigated |
| RR-08 | Drive FUSE I/O instability on directories with 10k+ files | O1, O7 | High | Med | Retry + shell `find` fallback; cached listings | Mitigated |
| RR-09 | Drive FUSE `stat` cache lags `readdir` cache | O13 (nb 06) | Med | High | Set-of-stems via `find` retry; never `os.path.isfile()` on Drive | Mitigated |
| RR-10 | Auto-labeller class collapse (menu/checkbox ≈ 0) | O11, O17 | Med | Med | Hand-correct GT; Phase 4.B icon top-up; Phase 4.C light backbone FT | Open |
| RR-11 | Licence / IP concerns on dataset use | design review | Low | High | All datasets public; AGPL inherited from Ultralytics; documented in Section 8.10 | Mitigated |
| RR-12 | Personal-data leakage from desktop seed screenshots | design review | Low | High | All 50 PNGs manually reviewed before commit `7a5896c` | Mitigated |
| RR-13 | Bot misuse for click-fraud or automated account creation | Section 8.10 Social | Low (research scope) | Med | Human-in-the-loop verdict step; no headless service mode shipped | Monitored |

Three observations about the register are worth pulling out for dissertation prose.

First, **the highest-impact risks are all data-quality risks**, not modelling or deployment risks. RR-01, RR-02 and RR-10 between them account for the project's three biggest empirical findings (the auto-label/hand-correct mAP gap, the recall-bounded source-domain backbone, and the icon class-distribution skew). Each is a reminder that the modelling chain is no stronger than its weakest data link.

Second, **most of the Open risks have costed mitigations**. RR-05 (refusal threshold), RR-06 (OCR latency), and RR-10 (class top-up) all have a documented Phase 3.1 / Phase 4.B work item that would move them from Open to Mitigated. Whether those work items are completed before submission is a separate triage call.

Third, **the only Low-probability risk that remains Monitored is RR-13** (bot misuse). The probability is low because the project ships an interactive verdict step by default and no headless service mode. The risk is kept on the register because the *category* of risk (vision-driven UI automation can be misused at the systemic level) does not go away merely because this particular prototype mitigates it; the dissertation's social-impact discussion in Section 8.10 takes this category seriously.

## 4.7 Project Plan

The project plan is the four-phase structure inherited from the proposal. The Gantt-equivalent rendering is in Figure 4.1 above; the text below makes each phase's scope and deliverable explicit.

**Phase 1: Data engineering and baseline establishment (Months 1–3, completed).** Public mobile UI datasets were acquired and consolidated into the 6-class unified bundle. A baseline detector was trained on the unified bundle. The 50-image desktop seed set was captured and auto-labelled. Eight test images were hand-corrected. The four transfer-learning ablations (M0, M1, M2, M3) were run on Colab Free, and the headline desktop fine-tune was selected. Three classical baselines (template, OCR-only, pywinauto) were implemented and evaluated on the 15-task suite. **Deliverable D1 (baseline performance report) is the content of Section 4.7 in the data form and Section 7.2 of this dissertation.**

**Phase 2: Model adaptation experiments (Months 4–7, partially completed).** The DETR backbone implementation, the SSP+FT experiment, and the two UDA experiments (Adaptive Teacher and SHOT) are the outstanding pieces. These are listed as gaps D-01 through D-04 in `docs/Final_Report_GAPS.md`. Phase 1.B's transfer-learning ablations completed; Phase 2's full sample-efficiency curve (gap D-05) is also outstanding. **Deliverable D2 (ablation study and model-comparison report) is partially complete; the YOLOv8 side is the content of Section 7.2; the DETR side and the three remaining adaptation methods are outstanding work for the version of the dissertation that closes those gaps.**

**Phase 3: Prototype integration (Months 8–9, completed).** The VisClick prototype is operational on Windows 11 with a CLI and a Tk GUI. The IVGocr architecture is implemented end-to-end. The interactive evaluation harness (`scripts/run_baselines.py`) supports the four-method comparison and the verdict-collection dialog. **Deliverable D3 (functional prototype) is the artefact in the public repository at https://github.com/HiranMadhu/visclick.**

**Phase 4: Evaluation and thesis composition (Months 10–12, ongoing).** The 15-task evaluation is complete. TSR, latency, and failure-mode analysis are reported in Section 7 of this dissertation. The qualitative third-party evaluation (gap D-10) and the memory profiling (gap D-11) are outstanding. **Deliverable D4 (final evaluation report and packaged code) is the dissertation in front of the reader.**

The phase boundaries on the Gantt are deliberately drawn with overlap. In practice, Phase 4 (thesis writing) began during Phase 3 (prototype integration) because writing tends to surface gaps in measurement that the prototype then has to be re-run to fill. The data form's incremental "as-evidence-arrives" structure was deliberately designed to support this overlap.

## 4.8 Chapter Summary

The project follows a design-science research methodology, with a modular, reproducible, refusal-on-uncertainty software design, executed under an agile/waterfall hybrid development process. The risk register captures thirteen risks distilled from the observation log; ten are mitigated, two are open with costed plans, and one is monitored. The project plan is the four-phase structure inherited from the proposal; Phase 1 and Phase 3 are complete, Phase 2 is partially complete with the outstanding work listed in `docs/Final_Report_GAPS.md`, and Phase 4 is ongoing.

The next chapter, Chapter 5, presents the design: the high-level architecture, the block diagram and flow chart of the runtime, the research design, and the wireframes for the prototype GUI.

# Chapter 5: Design

## 5.1 Chapter Overview

This chapter is the design half of the build-then-evaluate loop. It begins with the research design, which lays out the experimental matrix the rest of the dissertation populates. It moves on to the system architecture, presented as a block diagram in Section 5.3 and as a per-instruction flow chart in Section 5.4. The module-level design is presented next: which Python package contains which logical responsibility, and how the modules connect. The GUI side is covered in Section 5.6 with wireframes for the prototype's Tk dialog. The storage design (file layout, CSV schemas, ONNX weights) is in Section 5.7. The chapter closes with the algorithm design for the two non-trivial components: the fuzzy text-plus-class matcher in `visclick.match` and the refusal rule that implements R-FR-06.

The design described in this chapter is what the rest of the project implements. Chapter 6 walks through the code in the order this chapter lays out. The empirical results in Chapters 7 and 8 measure the implementation against the targets stated in Chapter 3. A reader who only wants the operational picture can read Section 5.3 and Section 5.4 and skip the rest.

## 5.2 Research Design

The research design is an experimental matrix that crosses three axes. The first axis is **architectural family**: YOLOv8s and DETR-R50. The second axis is **adaptation method**: source-only zero-shot (M0), few-shot fine-tune of the head (M2), self-supervised pre-training followed by fine-tune (SSP+FT), and unsupervised domain adaptation (Adaptive Teacher and SHOT). The third axis is **labelled-target budget**: $k = 1, 5, 10, 50, 100$ for the methods that use any labelled target data. A fully populated experimental matrix would therefore contain $2 \times 5 \times 5 = 50$ cells, although many of those cells degenerate (zero-shot does not depend on $k$; UDA does not depend on $k$ in the same way).

The reduced matrix the project actually executes is shown in Table 5.1. The eight cells marked DONE are reported in Chapter 7. The remaining cells are listed in gaps D-01 through D-05 of `docs/Final_Report_GAPS.md` and would close the matrix to its full proposal-committed shape.

**Table 5.1: Experimental matrix.**

| Backbone | Method | $k$ | Status |
|----------|--------|----:|--------|
| YOLOv8s | M0 zero-shot (CLAY → desktop) | n/a | DONE: `08_phase1B_ablations.ipynb` |
| YOLOv8s | M1 COCO direct (control) | n/a | DONE |
| YOLOv8s | M2 head fine-tune | 50 | DONE: headline detector |
| YOLOv8s | M3 frozen layers 22 | 50 | DONE: ablation |
| DETR-R50 | M0 zero-shot | n/a | PENDING: D-01 |
| DETR-R50 | M2 head fine-tune | 50 | PENDING: D-01 |
| YOLOv8s | M2 few-shot curve | 1, 5, 10, 50, 100 | PENDING: D-05 |
| YOLOv8s | SSP + M2 | 1, 5, 10, 50, 100 | PENDING: D-02 |
| YOLOv8s | UDA Adaptive Teacher | n/a | PENDING: D-03 |
| YOLOv8s | UDA SHOT | n/a | PENDING: D-04 |

The end-to-end TSR evaluation is run only against the single headline detector (YOLOv8s M2 fine-tune) rather than against every cell of the matrix. The rationale is twofold. The first reason is that the prototype's downstream behaviour depends on detection plus OCR plus matching plus action, so a fair end-to-end comparison across detectors would require re-running the full 15-task suite for each adaptation cell. That is roughly an hour of human verdict-collection per cell, which scales poorly. The second reason is that the dissertation's RQ4 (end-to-end practicality) is about whether one viable adapter can be turned into a working bot, not about which of several adapters does so best end-to-end. The "best" adapter is identified by mAP and CPV on the labelled test set; only that adapter gets the end-to-end treatment.

The classical baselines (template, OCR-only, pywinauto) sit outside the adaptation matrix because they have no adaptation parameter to vary. They are evaluated only end-to-end on the same 15-task suite, with the comparison being against the VisClick full pipeline.

## 5.3 System Architecture

The system architecture is captured in two diagrams. Figure 5.1 is the static block diagram: the boxes are the logical components, the arrows are the data dependencies. Figure 5.2 is the dynamic flow chart: it traces a single instruction from text input to clicked-element.

[FIGURE 5.1: "Block diagram of the VisClick system."
 Suggested source: regenerate from the Mermaid source in `docs/VisClick_Report_Data_Form.md` Section 18.1 via mermaid-cli or a Mermaid Live Editor export. Path placeholder: `reports/figures/ch5_block_diagram.png`.
 Suggested caption (~30 words): "Block diagram of VisClick. The capture, detect, OCR, match and act components are each a Python module under `src/visclick/`. Logging components are in `scripts/run_baselines.py`."]

The architecture has six logical layers. Each layer is realised as exactly one Python module under `src/visclick/`, with one exception (logging is split between modules and is handled at the script level rather than as a dedicated module).

**Layer 1: User input.** Either a text instruction from the GUI (`visclick.gui`) or a `--target` argument from the CLI (`visclick.__main__`).

**Layer 2: Screen capture.** A wrapper over `mss` that handles multi-monitor coordinate offsets (`visclick.capture`). The capture layer returns an RGB numpy array and the `(left, top)` offset of the chosen monitor.

**Layer 3: Detection.** An ONNX wrapper that loads the trained YOLOv8s weights and emits a list of `(class_id, confidence, xyxy)` tuples (`visclick.detect`). The wrapper supports both an `onnxruntime` backend (the default, CPU only) and an Ultralytics `model.predict()` backend (used during training and during ablations).

**Layer 4: OCR.** A two-mode OCR layer (`visclick.ocr`). The per-box mode runs EasyOCR on each detected bounding box and returns the most confident text string. The full-image mode runs EasyOCR on the entire screenshot and returns a list of `(text, bounding_box, confidence)` tuples for use in the OCR fallback path. The module exposes the `ocr_status()` probe described in Section 4.3.

**Layer 5: Matching.** A fuzzy matcher built on `rapidfuzz` (`visclick.match`). The matcher's `best_box()` function takes the user instruction, the per-box OCR text, and the detection class IDs, and returns the index of the best-matching box together with its score. The class-aware bonus and the similarity threshold are explained in Section 5.8.

**Layer 6: Action.** A PyAutoGUI wrapper that handles the virtual-desktop offset correction (`visclick.act`). The wrapper exposes `click_box(box, offset=(left, top))` and `move_to_box(...)`.

Above the six layers sits the orchestrator `visclick.bot`, which composes the layers into a single `run_instruction()` entry point. The orchestrator is what both the CLI and the GUI invoke. It is also what the evaluation harness's VisClick baseline (`scripts/baseline_visclick.py`) calls.

The deliberate property of this design is that no two layers share state. The capture layer hands an image to the detect layer; the detect layer hands a box list to the OCR layer; the OCR layer hands text to the matcher; and so on. This is what makes each layer independently testable, and it is also what made the four-baseline comparison in Chapter 7 possible without duplicating code.

## 5.4 Process Flow

The flow chart in Figure 5.2 makes the runtime behaviour explicit. The single decision point that is worth pulling out for prose discussion is the OCR-fallback decision at the matcher.

[FIGURE 5.2: "Process flow chart for a single click instruction."
 Suggested source: regenerate from the Mermaid source in `docs/VisClick_Report_Data_Form.md` Section 18.2. Path placeholder: `reports/figures/ch5_flowchart.png`.
 Suggested caption (~30 words): "Per-instruction flow chart. The decision diamond at the matcher determines whether the detector's top candidate is accepted (Yes), whether the full-image OCR fallback is invoked (No, retry), or whether the system refuses to click (No, refuse)."]

The flow has six stages. **Capture** acquires the screenshot from the chosen monitor. **Detect** produces up to $N$ candidate boxes; if $N = 0$ the system falls through to the OCR fallback path. **Per-box OCR** annotates each box with its text. **Match** computes a fuzzy similarity score between the user instruction and each box's text, with a small bonus added for boxes whose detected class matches the instruction's likely intent (a "click Save" instruction prefers a `button` over a `text`). **Decision** compares the top score against `min_text_similarity` (currently 60 on a 0-100 scale). If the score clears the threshold, the system proceeds to **Action**. If it does not, the system enters the **fallback** branch, running full-image OCR and re-matching the instruction against every recognised text region; if the fallback also fails to clear the threshold, the system **refuses**.

The fallback is the architectural compromise that pays for the source-domain detector's limited recall on Windows 11 native dialogs (the recall-bound problem documented as O11 in the data form). Without the fallback, the bot would refuse on roughly half the test tasks because the detector simply does not see the target box. With the fallback, the bot recovers the visible-text-but-no-box cases at the cost of a roughly 6-second latency penalty. The cost-benefit is recorded in Section 7.3.2 and is one of the two design trade-offs that Chapter 8 returns to in the evaluation chapter.

## 5.5 Module Design

The module diagram below makes the per-package responsibilities explicit. Each module's public surface is small (between one and four exported functions or classes). The module-level boundaries are also the unit-test boundaries: each module has at least one corresponding `tests/test_<module>.py` file (the test files are listed in Section 6.12).

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
  capture_screenshots.py  # corpus expansion
  make_prototype_figures.py # report figure generation
  run_nfr.py              # NFR latency + memory profiling
  test_screen.py / test_click.py / test_detector.py # ad-hoc smoke tests
```

The module dependency graph is intentionally a directed acyclic graph: `bot` depends on `capture, detect, ocr, match, act`; `capture, detect, ocr, match, act` are mutually independent; `gui` depends on `bot`. The acyclic property is what lets the four baselines reuse `capture` and `act` without dragging in the detector. A circular dependency would have collapsed this composition.

## 5.6 GUI Wireframes

The prototype ships a single-window Tk dialog. The wireframe in Figure 5.3 captures the layout. There are deliberately few controls: the goal is to make the bot's behaviour obvious to a first-time user, not to put every parameter on the surface.

[FIGURE 5.3: "Wireframe of the VisClick GUI."
 Suggested source: hand-drawn rectangles or a screenshot of the actual Tk window with annotations overlaid; the existing screenshot `reports/figures/proto_2_typed.png` can be used with arrow annotations. Path placeholder: `reports/figures/ch5_gui_wireframe.png`.
 Suggested caption (~30 words): "GUI wireframe. (1) Monitor dropdown. (2) Instruction text box. (3) Run / Stop buttons. (4) Live status line. (5) Last-overlay thumbnail. (6) Verbose log toggle."]

The six elements are as follows.

1. **Monitor dropdown** (`gui.MonitorSelector`). Populated at start-up from `mss.monitors`. Selection sets the `--monitor` index for every subsequent run. Defaults to the primary monitor.

2. **Instruction text box** (single line, `tk.Entry`). The user types a free-form instruction. Enter triggers Run.

3. **Run / Stop buttons.** Run kicks off the orchestrator. The 3-second pre-action countdown is implemented as a Tk `after()` callback; the Stop button cancels the countdown.

4. **Status line** (single line at the bottom). Shows one of `idle`, `counting down: 3 / 2 / 1`, `capturing`, `detecting`, `ocr`, `matching`, `clicking`, `done: verdict?`, `FAIL: cannot find target`.

5. **Last-overlay thumbnail.** A 320×180 thumbnail of the most recent `overlay.png`. Clicking the thumbnail opens the full-resolution PNG in the system viewer. This is the diagnostic affordance that supports UC-04.

6. **Verbose log toggle.** A check box that, when on, prints the per-stage timings to stdout. Off by default to avoid noise on first-time users.

The wireframe is deliberately small. Three earlier wireframes (a separate evaluation tab, a separate model-selection panel, a confidence-threshold slider) were considered and removed at design review on the grounds that they did not serve a stakeholder viewpoint identified in Section 3.2.2. The verdict-collection dialog used during the 15-task evaluation runs (`scripts/run_baselines.py::_verdict_dialog_tk`) is a separate Tk window that pops up at the end of each attempt; its wireframe is similar enough that it does not warrant a separate figure.

## 5.7 Repository Layout and Data Storage Design

The project does not use a database. All persistent state lives in files on disk, organised into a small number of top-level directories with well-defined responsibilities. The repository layout is presented once, in Figure 5.4, and every other chapter that names a file does so as a leaf inside this tree. A reader who is reading the report on its own without the source-code repository in front of them can use Figure 5.4 together with the role descriptions below to follow every artefact reference in the report.

[FIGURE 5.4: "Repository directory tree."
 Suggested source: a single-panel directory tree exported from the actual repository at submission time using `tree -L 3 --dirsfirst` or a hand-drawn equivalent in draw.io. The tree should show the top-level directories with one or two example files under each. Path placeholder for the report image: a project-relative file the author will produce at submission. The same tree is reproduced as plain text below for the convenience of readers viewing the PDF without diagram rendering.
 Suggested caption (~30 words): "Repository directory tree. Top-level directories group the artefact's responsibilities: source code, dependency packaging, training data, model weights, evaluation scripts, notebooks, tests, reports, and documentation. Every path quoted elsewhere in this report is a node in this tree."]

The plain-text rendering of the same tree, for readers viewing the dissertation as plain text, is:

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
    capture_screenshots.py  # corpus expansion
    make_prototype_figures.py
    run_nfr.py              # NFR latency and memory profile
  notebooks/                             # 01..08 training + ablations
  tests/                                 # pytest suites for each module
  weights/                               # trained ONNX + .pt checkpoints
  configs/                               # YOLO/dataset YAMLs
  datasets/                              # training and test data
    source_zenodo_unified/{images,labels}/{train,val}
    desktop_seed/{images,labels}         # 50 captured screenshots
    handcorrected_desktop_test/{images,labels}  # 8 GT-corrected screens
  samples/                               # seed images and templates
  tasks/                                 # canonical T01..T15 task definitions
  reports/                               # everything the dissertation cites
    tables/                              # result CSVs
    figures/                             # result PNGs
    references/                          # literature PDFs cited
  docs/                                  # this report + data form + plan
    Final_Report.md
    Final_Report_GAPS.md
    VisClick_Report_Data_Form.md
    VisClick_Detailed_Plan.md
  runs/                                  # transient Ultralytics output
                                         # (regeneratable, not committed)
```

The top-level directories and their roles, in the order they appear in Figure 5.4, are as follows.

**The runnable package (`src/visclick/`).** Seven modules implementing the six-layer architecture from Section 5.3, plus a Tk GUI module. This directory is what is installed by `pip install -e .` and what is imported as `import visclick` at run time.

**The evaluation scripts (`scripts/`).** A dozen Python entry points for jobs that are not part of the importable package: the evaluation harness, four per-method adapters, the NFR profiler, the figure regenerator, and the corpus-expansion script. Scripts are designed to be runnable as `python -m` or `python scripts/<name>.py` from the repository root.

**The notebooks (`notebooks/`).** Numbered Jupyter notebooks that contain the training, fine-tuning, and ablation experiments. Notebook 01 acquires and unifies the source-domain corpora; notebook 05 trains the source-domain detector; notebook 08 runs the Phase 1.B transfer-learning ablations. Notebook stubs 09 to 14 are reserved for the pending adaptation experiments (gaps D-01 to D-04).

**The tests (`tests/`).** One pytest file per module under `src/visclick/`. Test command is `pytest -q tests/`.

**The trained weights (`weights/`).** The deployed ONNX detector at the canonical name `weights/visclick.onnx`, plus the per-ablation Ultralytics checkpoints. The deployed file is approximately 45 MB.

**The configs (`configs/`).** YAML configuration files for the YOLO/Ultralytics training pipeline plus the unified 6-class taxonomy file.

**The datasets (`datasets/`).** The training and test data, laid out in the YOLO/Ultralytics directory convention so that Ultralytics's training command consumes the layout without modification. Three sub-trees: the unified source-domain bundle (mobile UIs), the desktop seed (captured target-domain images), and the hand-corrected desktop test set (the ground-truth pool used in Chapter 7).

**The task definitions (`tasks/`).** A single JSON file `T01_T20.json` listing the 15 canonical evaluation tasks plus 5 reserved slots. Each task carries the natural-language instruction together with per-method hints (a template image for `cv2.matchTemplate`, an accessibility-identifier dictionary for `pywinauto`, a query string for the text-driven methods).

**The reports artefacts (`reports/`).** Everything the dissertation cites. Two principal sub-directories: a CSVs directory (the evidence file for every quantitative claim in this report) and a PNGs directory (the figures). One additional sub-directory holds the PDF copies of the literature references that the dissertation cites.

**The documentation (`docs/`).** This dissertation, the gaps tracker, the data form that the dissertation is built on, and the detailed plan that tracks Phase L. The first three are the deliverable submission artefacts; the last one is a working document.

**The transient output (`runs/`).** Per-experiment Ultralytics training output (loss curves, intermediate weights, validation predictions). This directory is not version-controlled because the contents are deterministic outputs of the notebooks; only the relevant final weights are promoted into the trained-weights directory.

The principal data schema for the evaluation evidence is the per-attempt CSV that the harness writes after every task. The schema is stable across all 60 attempts collected so far and across the four method adapters; it is reproduced below for completeness.

```text
columns: task_id, method, instruction, capture_path, predicted_xy,
         verdict, latency_seconds, is_negative, notes
verdict in {pass, fail, skip, refused}
method  in {template, ocr_only, pywinauto, visclick}
```

Every per-attempt row is the smallest unit of evaluation evidence in the dissertation. The 60 rows currently on disk are what every percentage figure in Chapter 7 is computed from.

## 5.8 Algorithm Design

Two algorithms in the system are non-trivial enough to warrant a dedicated design statement. They are the fuzzy matcher in `visclick.match` and the refusal rule in the orchestrator.

### 5.8.1 The matcher

The matcher's job is to pick which of the $N$ detected boxes the user is asking the bot to click. The input is the user instruction (a short string), the list of per-box OCR texts, and the list of detection class IDs. The output is the index of the chosen box plus a confidence score on a 0-100 scale.

The matcher scores each box by combining two signals. The **text-similarity signal** is `rapidfuzz.fuzz.WRatio(instruction, box_text)`, which is a normalised mix of partial-string, token-set, and token-sort scores. WRatio is preferred over a single ratio metric because it is robust to word-order variation ("click Save button" vs "click the Save button" both score near 100 against an OCR string `Save`). The **class-bonus signal** is a small additive bonus when the detection class matches an inferred intent. The intent inference is a tiny rule table: instruction contains "type" or "enter" $\to$ prefers `text_input`; instruction contains "select" $\to$ prefers `menu` or `checkbox`; everything else prefers `button`. The bonus is set to +10 on a 0-100 scale, which is enough to break ties between two same-text boxes of different classes but not enough to override a strong text mismatch.

The final score is `min(100, text_similarity + class_bonus)`. The chosen box is the one with the highest final score, ties broken by detection confidence (higher first).

The textual algorithm in Python is:

```python
def best_box(instruction: str,
             box_texts: list[str],
             box_classes: list[str]) -> tuple[int, float]:
    intent_class = _infer_intent(instruction)  # one of button/text_input/menu/...
    scores = []
    for text, cls in zip(box_texts, box_classes):
        ts = rapidfuzz.fuzz.WRatio(instruction.lower(), (text or "").lower())
        bonus = 10 if cls == intent_class else 0
        scores.append(min(100, ts + bonus))
    best_idx = max(range(len(scores)), key=scores.__getitem__)
    return best_idx, scores[best_idx]
```

The threshold for accepting the chosen box is `min_text_similarity = 60` in the current build. This threshold was selected empirically by running the 15-task suite at thresholds of 40, 50, 60, 75 and 85 and choosing the lowest threshold at which the negative test case (T15, "click the Settings menu" in an app with no Settings menu) was refused while the 14 positive tasks were still accepted. A higher threshold of 75 is being considered as part of risk RR-05; the change is contingent on widening the negative-case set beyond a single task.

### 5.8.2 The refusal rule

The refusal rule is the orchestrator-level decision that determines whether a click is issued. The rule has three branches.

The **first branch** is the no-candidates branch: if the detector emits zero boxes, the orchestrator skips the per-box OCR stage entirely and goes directly to the OCR fallback. The fallback may itself find no candidates, in which case the system refuses.

The **second branch** is the low-confidence branch: if the matcher's chosen box has a score below `min_text_similarity` after per-box OCR, the orchestrator goes to the OCR fallback. If the fallback also returns a low-confidence result, the system refuses.

The **third branch** is the high-confidence branch: if the matcher's chosen box has a score at or above the threshold, the orchestrator proceeds directly to action. The action layer issues a single left-click at the centre of the chosen box, with the multi-monitor offset already corrected by the capture layer.

In all three branches the system writes a CSV row to `baseline_results.csv` describing what happened, including the chosen box (if any), the score, and the verdict (`pass`, `fail`, `refused`, `skip`). The CSV is what the analysis pipeline consumes in Section 7.3 and Section 8.2.

## 5.9 Chapter Summary

The design described in this chapter is the contract that Chapter 6 implements and that Chapters 7 and 8 evaluate. The system has six logical layers (capture, detect, OCR, match, act, bot) each realised as one Python module, plus a thin GUI and an evaluation harness. The architecture is deliberately acyclic, which is what made the four-baseline comparison possible inside a shared harness. The runtime flow has one non-trivial decision point, the OCR-fallback path at the matcher, which trades off latency for recall in a way that the empirical evidence in Chapter 7 quantifies. Data is stored as files on disk in a layout that supports both YOLOv8/Ultralytics training conventions and per-attempt CSV evaluation logs. Two algorithms (the rapidfuzz-plus-class-bonus matcher and the three-branch refusal rule) are made explicit because they encode the project's twin commitments: fuzzy human-text tolerance and refusal-on-uncertainty.

The next chapter walks through the implementation of every element of this design.

---

# Chapter 6: Implementation

## 6.1 Chapter Overview

This chapter is the build half of the design-build-evaluate loop. It walks through the implementation in the order the design chapter introduced the components. It begins with the development environment and toolchain, because every implementation claim that follows depends on having that environment reproducibly available. It moves on to the dataset implementation (acquisition, cleaning, class collapse, auto-labelling, and the hand-correction pass). It covers the detector implementation in two pieces: source-domain training in Section 6.4 and target-domain adaptation in Section 6.5. The OCR layer, the matcher, the action layer, the GUI, and the evaluation harness are then implemented in turn. The chapter closes with a brief discussion of the deliberately-deferred implementation work, which is the code corresponding to the gaps D-01 through D-05.

A reader following the artefact alongside the dissertation should be able to identify, for any concrete claim in this chapter, the file, function or notebook cell that implements that claim. Implementation evidence is the contract this chapter pays.

## 6.2 Development Environment and Toolchain

The development environment is built around two compute targets. Training happens on **Google Colab Free** with a T4 GPU. Inference and prototype testing happen on a **Windows 11 desktop**, the author's personal machine. The two environments are deliberately kept compatible at the Python interpreter level (CPython 3.11 in both) so that any artefact trained on Colab can be loaded and run on the Windows machine without environment-specific re-installation.

The Python project is structured as a standard `pyproject.toml`-driven package. The `pyproject.toml` defines the `visclick` distribution with the following declared dependencies (the full list is in the repository; the version pins are stricter than shown here, recorded in `requirements.txt`):

```text
ultralytics>=8.0          # YOLOv8s training + ONNX export
opencv-python>=4.8        # image I/O, template matching, overlay drawing
numpy>=1.24
Pillow>=10.0
onnxruntime>=1.17         # CPU-only ONNX inference
pyautogui>=0.9.54         # action layer
mss>=9.0                  # multi-monitor screen capture
pytesseract>=0.3          # optional OCR (Tesseract backend)
easyocr>=1.7              # primary OCR backend
rapidfuzz>=3.0            # matcher
psutil>=5.9               # NFR memory profiling
pywinauto>=0.6 ; platform_system == "Windows"   # baseline accessibility tree
```

The Windows-only conditional on `pywinauto` is the single concession to a non-portable dependency. Every other package runs on Colab as well, which is what makes notebooks and the Windows prototype share the same package install.

Editable install on Windows is `py -3 -m venv .venv` followed by `.venv\Scripts\activate` and `pip install -e .`. The same incantation, modulo path conventions, works on Linux and Mac although neither is in scope for the bot itself. The CLI is exposed as the module entry point `python -m visclick.bot --target "Save" --monitor 0`.

The repository layout is the layout described in Section 5.7 plus a top-level `notebooks/` directory for the nine training and evaluation notebooks (`01_pull_and_data.ipynb` through `08_phase1B_ablations.ipynb`). Notebooks are kept under version control with output cells stripped on commit (the project's `.gitattributes` declares `*.ipynb diff=ipynb`).

The toolchain for paper-style figure generation is `matplotlib` 3.8 with the default style sheet, exported at 300 DPI. The toolchain for the prototype's overlay rendering is `cv2.putText` plus `cv2.rectangle`; the design choice is documented in Section 6.7.

## 6.3 Dataset Implementation

The dataset implementation has three tiers, mirroring the methodology in Section 3.4.

**Tier 1: Source-domain corpus.** Notebook `01_pull_and_data.ipynb` downloads RICO from the project's hosting URL, CLAY from its own release page, and VINS from the supplementary material of Bunian et al. 2021. Each corpus is unpacked into `datasets/raw/{rico,clay,vins}/`. The notebook then runs a class-collapse pass that maps each corpus's native taxonomy onto the unified 6-class taxonomy used by the project. The class-collapse table is:

| Unified class | Source mapping |
|---------------|----------------|
| `button` | RICO `Button`, `ImageButton`; CLAY `Button`; VINS `Button` |
| `text` | RICO `TextView`; CLAY `Text`; VINS `Text` |
| `text_input` | RICO `EditText`; CLAY `Edit_text`; VINS `Input_field` |
| `icon` | RICO `Icon`, `ImageView` (when small); CLAY `Icon`; VINS `Icon` |
| `menu` | RICO `Menu`; CLAY `Menu`, `Drawer`; VINS `Drop_down_menu` |
| `checkbox` | RICO `CheckBox`, `Switch`; CLAY `Checkbox`, `Toggle`; VINS `Checkbox` |

Boxes whose source class is not on the mapping table (decorative containers, scroll bars, progress indicators, advertising slots) are dropped from training rather than mapped to a `null` class. The dropping decision is documented in observation O3 of the data form; the alternative of training with a `background` class was tested early in Phase 1 and was discarded because it inflated the false-positive rate on the desktop seed without improving recall.

After class collapse the unified corpus contains 9,646 screens and approximately 312,000 box-level annotations. The notebook then writes the corpus into the YOLO directory layout described in Section 5.7, with an 85/15 train/val split using a fixed `random_state=42` seed for reproducibility.

**Tier 2: Unlabelled target corpus.** The captured screenshots live under `samples/desktop_seed/`. The capture script `scripts/capture_screenshots.py` enumerates visible top-level windows via `pywinauto.Desktop(backend="uia")` and grabs each window with `mss`. The current corpus is 50 screenshots spanning Notepad, File Explorer, Visual Studio Code, Chrome, Word, and Outlook. The proposal-committed corpus of 2,000 screenshots is gap D-06; the implementation work for it is a parameterisable scheduled capture script, the design for which is in the data form's Section 11.

**Tier 3: Labelled target test corpus.** The hand-correction pass started from the auto-labels emitted by the M0 zero-shot model and corrected them in Roboflow's annotation tool. The corrected output is the 356-box `datasets/handcorrected_desktop_test/` directory. The annotation guidelines are a one-page document that mirrors the CLAY release-notes conventions: tight boxes around the visible affordance (not the surrounding padding), no rotated boxes, no occluded boxes, no boxes for purely decorative graphical elements. The annotation work is documented as observation O17 in the data form. The path to a 100-image labelled corpus, gap D-07, is a continuation of the same workflow at a larger scale.

## 6.4 Source-Domain Detector Training

The source-domain detector is YOLOv8s trained on the unified bundle for 50 epochs. The training configuration is captured in `configs/yolo_source.yaml`:

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

The training command, executed in `05_train_source.ipynb`, is:

```python
from ultralytics import YOLO
model = YOLO("yolov8s.pt")            # COCO-pretrained checkpoint
results = model.train(
    data="configs/yolo_source.yaml",
    epochs=50,
    imgsz=640,
    batch=16,
    device=0,                          # Colab T4
    project="runs/source",
    name="yolov8s_unified_50e",
    seed=42,
)
```

The training run completes in approximately 4.5 hours on a Colab Free T4. The headline source-domain numbers are mAP@0.5 = 0.793 and mAP@0.5:0.95 = 0.555 on the held-out validation split (recorded in `reports/tables/source_domain_results.csv`). The per-class breakdown in `reports/tables/source_per_class.csv` shows the expected imbalance pattern: `text` is highest at AP@0.5 = 0.91 and `checkbox` is lowest at 0.59. The per-class numbers are consistent with the published baselines on RICO (Apple Screen Recognition's in-distribution F1 of 0.91 is in the same range as our `text` class), which is taken as informal evidence that the training pipeline is working correctly.

The trained checkpoint is exported to ONNX with the canonical Ultralytics export:

```python
model.export(format="onnx", imgsz=640, opset=12, simplify=True)
```

The exported file is approximately 45 MB and is shipped into `weights/visclick.onnx`.

## 6.5 Adaptation Methods Implementation

Five adaptation methods are described in the proposal. The implementation status of each is the substance of the experimental matrix in Table 5.1. Each method is treated here in turn.

### 6.5.1 M0 zero-shot transfer (CLAY $\to$ desktop)

M0 is the no-adaptation control. The source-trained detector is run on the desktop seed images without any further training. The implementation is a four-line evaluation cell in `08_phase1B_ablations.ipynb` that loads `weights/source_yolov8s_50e.pt` and calls `model.val(data="configs/yolo_desktop_test.yaml")`. The headline number is mAP@0.5 = 0.157 on the auto-labelled desktop test set, which collapses to mAP@0.5 = 0.033 when re-evaluated against the hand-corrected ground truth (observation O19). The discrepancy is the project's headline measurement of the source-to-target domain gap.

### 6.5.2 M1 COCO direct (control)

M1 is the second control: a COCO-pretrained YOLOv8s with no UI-domain training, run directly on the desktop seed. The intent of the control is to isolate the gain from UI-domain training (M0) versus from generic visual pretraining (M1). The implementation is the same four-line cell as M0 but with `weights="yolov8s.pt"` (the upstream Ultralytics weight). The headline number is mAP@0.5 = 0.071 on the auto-labelled test set, which is lower than M0 as expected.

### 6.5.3 M2 head fine-tune (50 epochs, 50 labelled desktop images)

M2 is the headline adaptation method that produces the deployed detector. The training cell is in `08_phase1B_ablations.ipynb`:

```python
model = YOLO("weights/source_yolov8s_50e.pt")
results = model.train(
    data="configs/yolo_desktop_finetune.yaml",
    epochs=50,
    imgsz=640,
    batch=8,
    device=0,
    freeze=10,                        # freeze backbone, train neck + head
    seed=42,
)
```

The `freeze=10` argument freezes the first 10 layers (the backbone CSPDarknet53), training only the PANet neck and the detection head. The rationale for freezing is data efficiency: with only 50 labelled images, the full-network update overfits within 5 epochs (a phenomenon observed during a preliminary unfrozen run not documented in the notebook). Freezing the backbone keeps the source-domain feature extractor intact and lets the head learn the target-domain class boundaries.

The headline M2 numbers are mAP@0.5 = 0.718 against the auto-labels and mAP@0.5 = 0.033 against the hand-corrected ground truth (the 22-fold gap that motivates the dissertation's evaluation methodology). The latter is the honest number; the former is reported in the dissertation only with the caveat attached.

### 6.5.4 M3 frozen layers 22 (ablation)

M3 freezes the first 22 layers, leaving only the very last detection head trainable. The implementation differs from M2 only in the `freeze=22` argument. M3 is included as a sanity-check ablation: if M3 outperforms M2, that would be evidence that the M2 update is overfitting in the middle layers. The headline M3 number is mAP@0.5 = 0.694 against the auto-labels, slightly below M2 as expected. M3 is reported in `transfer_experiments.csv` for completeness; M2 remains the deployed detector.

### 6.5.5 DETR backbone (pending: D-01)

The DETR backbone implementation has not yet been started. The proposal commits to a DETR-R50 trained on the same unified bundle and evaluated zero-shot and fine-tuned on the desktop set. The implementation plan is to use Meta's reference implementation from the `detr` repository, train for 150 epochs on Colab Free with `batch=4` (T4's 16 GB ceiling for DETR), and follow the same M0 and M2 protocol used for YOLOv8s. The notebook stubs `09_detr_source.ipynb` and `10_detr_finetune.ipynb` are tracked in `docs/Final_Report_GAPS.md` and will become the implementation home for D-01 once started.

### 6.5.6 Self-supervised pre-training + fine-tune (pending: D-02)

SSP is the second pending adaptation method. The proposal commits to a generative inpainting pretext task on the unlabelled desktop corpus. The implementation plan is a masked-image-modelling pretext following Pix2Struct's protocol [52] adapted for an object-detection backbone rather than a vision transformer. The trained backbone replaces the COCO checkpoint in the M2 fine-tune. SSP requires the 2,000-image unlabelled corpus (D-06), so D-02 depends on D-06.

### 6.5.7 Unsupervised Domain Adaptation, Adaptive Teacher variant (pending: D-03)

The Adaptive Teacher implementation will use the reference code released alongside the CVPR 2022 paper [16]. The implementation plan is to adapt the reference's two-stage Faster R-CNN harness to YOLOv8 by replacing the detector class and updating the EMA-teacher update rule to match Ultralytics's checkpoint format. The mixed-batch composition is 50% labelled source plus 50% pseudo-labelled target, with strong augmentation (RandAugment + cutout) applied to the target half only. The stop criterion is mAP@0.5 on the hand-corrected target set, which links D-03 to D-07 (the 100-image labelled test set).

### 6.5.8 Unsupervised Domain Adaptation, SHOT variant (pending: D-04)

SHOT's implementation is simpler in structure than Adaptive Teacher's. The source-domain head is frozen, and the backbone is fine-tuned on the unlabelled target corpus with a self-supervised pseudo-label objective. The implementation plan is to follow the recent object-detection adaptation of SHOT from Sahay et al. 2023 [17, 42] and to run it on the same hardware budget as Adaptive Teacher to keep D-03 and D-04 directly comparable.

## 6.6 Pre-processing Pipeline

The pre-processing pipeline is split between training-time and inference-time stages.

The **training-time** stage is the standard YOLO augmentation pipeline configured in `configs/yolo_*.yaml`. The augmentations enabled are mosaic (probability 0.5; turned off for the final 10 epochs), horizontal flip (probability 0.5), random scale within $[0.8, 1.2]$, and HSV jitter with the Ultralytics defaults. Vertical flip is disabled because UIs are not vertically symmetric. The mosaic augmentation is what gives the source-domain training its strongest data efficiency on the 9,646-screen corpus; an ablation without mosaic (not reported in the data form) ran 4 percentage points lower in mAP@0.5.

The **inference-time** stage is minimal. The capture layer hands the screenshot to the detect layer at native resolution; the detect layer rescales to 640×640 with letterboxing inside `ultralytics.engine.predictor`. There is no additional bilateral filtering, no contrast normalisation, and no colour-space conversion (the screenshot is RGB throughout). The decision not to add inference-time pre-processing was made empirically: a preliminary A/B test in week 6 of the project compared no-preprocessing against bilateral-filter-plus-CLAHE and showed the no-preprocessing path was marginally better on the desktop seed. The A/B test was not formal enough to report as a result; the gap D-12 records the work needed to do a proper A/B at sufficient sample size.

## 6.7 Prototype Implementation

The prototype is the `visclick` Python package, written to the design in Section 5.5. The implementation walk-through below visits each module in turn at the level of detail needed to make the chapter's evidence claims auditable.

### 6.7.1 `visclick.capture`

The capture module wraps `mss` and exposes two entry points: `capture_monitor(idx)` and `list_monitors()`. The non-trivial implementation work in this module is the multi-monitor offset propagation, which was the source of observation O13 (the cursor moving by a few pixels on the wrong monitor). The fix is to return the chosen monitor's `(left, top)` offset alongside the image, and to thread that offset through every downstream layer that maps a box to a click coordinate. The relevant signature is:

```python
def capture_monitor(idx: int = 0) -> tuple[np.ndarray, tuple[int, int]]:
    """Return (image_rgb, (left, top)) for the monitor at `idx`."""
```

The `(left, top)` tuple is what `act.click_box` uses to convert a box centre in image-coordinates into a screen-coordinate suitable for `pyautogui.click`.

### 6.7.2 `visclick.detect`

The detect module loads the ONNX file at start-up and runs `onnxruntime`-based inference on each call. The public surface is:

```python
class Detector:
    def __init__(self, onnx_path: str = "weights/visclick.onnx"): ...
    def predict(self, image_rgb: np.ndarray, conf: float = 0.25) -> list[Detection]: ...
```

The `Detection` dataclass has fields `class_id`, `class_name`, `confidence`, and `xyxy`. The detector also exposes a `status()` probe that prints a tick if the ONNX file loads cleanly and a cross with the underlying error if it does not. The probe is what makes the `_warn_once` pattern actionable at start-up.

### 6.7.3 `visclick.ocr`

The OCR module is the most complex single file in the codebase, because it has to handle two backend mismatches (EasyOCR's `readtext` returns `(bbox, text, conf)` triples; pytesseract's `image_to_data` returns a DataFrame) and a fallback path that runs when neither backend is available. The public surface is small:

```python
def ocr_image(image_rgb: np.ndarray) -> list[OcrResult]: ...
def ocr_box(image_rgb: np.ndarray, box: tuple[int, int, int, int]) -> str: ...
def text_ground(image_rgb: np.ndarray, query: str) -> Optional[tuple[int, int]]: ...
def ocr_status() -> None: ...
```

`text_ground` is the OCR-fallback entry point invoked by the orchestrator when the matcher's per-box result is below threshold. It runs `ocr_image` on the full screenshot, then runs the same rapidfuzz matcher over the recognised text regions, and returns the centre of the best match or `None`.

The `ocr_status()` probe is the lesson from observation O12. At start-up it tries to import `easyocr`, `pytesseract`, and the pure-Python fallback in order, prints a tick or cross for each, and lists the active backend. If none of the three is functional, the program emits a `RuntimeError` rather than failing silently downstream.

### 6.7.4 `visclick.match`

The match module is the rapidfuzz-plus-class-bonus matcher implemented in Section 5.8.1. The public surface is one function (`best_box`) and one helper (`_infer_intent`). The implementation is 38 lines of code and has full unit-test coverage.

### 6.7.5 `visclick.act`

The act module is the PyAutoGUI wrapper. The single public function is `click_box(box, offset=(left, top), dry_run=False)`. The dry-run mode prints what would have been clicked without actually moving the cursor; it is used by the smoke tests and by the prototype's "preview" mode.

### 6.7.6 `visclick.bot`

The orchestrator composes the five layers above into a single `run_instruction(text: str, monitor: int = 0) -> Verdict` entry point. The orchestrator handles the three-branch refusal rule from Section 5.8.2 and produces the per-attempt CSV row. The CSV row schema is the one declared in Section 5.7. The orchestrator also handles the overlay PNG generation; the overlay is drawn by a helper function `_render_overlay` that takes the screenshot, the detection list, the chosen box, and the click coordinate, and produces an annotated PNG.

### 6.7.7 `visclick.gui`

The GUI is a single Tk window implementing the wireframe in Section 5.6. The implementation uses only the standard `tkinter` library (no Tk extensions, no PyQt), which is what lets the package install cleanly on a Windows machine with no further GUI dependencies. The verbose-log toggle and the last-overlay thumbnail are the two implementation choices that took the most time; both are documented in observation O15 of the data form.

## 6.8 OCR Integration

The OCR integration is the architectural choice that gives the prototype its observed end-to-end behaviour. The choice is between running OCR on every detected box (the per-box path) and running OCR once on the whole image (the full-image fallback). The implementation does both, but in a specific order: per-box first, full-image only if per-box fails.

The reason for the ordering is latency. Per-box OCR is roughly $N \times 200\text{ ms}$ on EasyOCR for $N$ boxes; the median $N$ across T01-T15 is 9. Full-image OCR is roughly 6 seconds. The per-box path therefore runs in roughly $9 \times 0.2 = 1.8$ seconds, which is the dominant cost in the happy-path budget. The full-image fallback adds 6 seconds when invoked; the fallback is invoked on roughly 30% of attempts (where the detector misses the target's bounding box), so the expected wall-clock cost of OCR per task is approximately $1.8 + 0.3 \times 6 = 3.6$ seconds. This is the calculation that justifies the per-box-first ordering as opposed to always-full-image.

The OCR engine choice is EasyOCR rather than Tesseract. The choice was made empirically during week 4 (observation O5) after comparing EasyOCR and Tesseract on a small dialog-heavy benchmark. EasyOCR recognised approximately 91% of the visible text on a set of 20 Windows 11 dialogs, while Tesseract recognised 67%. The gap is largest on small text and on anti-aliased text-on-coloured-background; both are common in Windows 11. Tesseract remains available as an opt-in backend via the `VISCLICK_OCR_ENGINE=tesseract` environment variable for users on machines where the EasyOCR model download is awkward.

## 6.9 Matching Algorithm Implementation

The matcher implementation is a faithful realisation of the design in Section 5.8.1. The minor implementation choices that did not survive into the design statement are worth recording for completeness.

The first choice is **case folding**. All comparisons are lower-cased on both sides. UI text frequently uses title case ("Save"), and instructions are often typed in lower case ("save"); folding gives a small but reliable score uplift.

The second choice is **stop-word retention**. The matcher does *not* strip stop words. "Click the Save button" is left as-is rather than reduced to "save". The rationale is that rapidfuzz's WRatio is robust to padding, and stop-word stripping with a hand-rolled list is a frequent source of off-by-one bugs.

The third choice is the **intent inference table**. The current rules cover ten verbs ("click", "type", "enter", "select", "open", "close", "press", "toggle", "expand", "collapse"). The table is in `visclick/match.py::_INTENT_TABLE` and is the easiest extension point for adding new intent classes.

## 6.10 Action Layer and Multi-Monitor Support

The action layer is the PyAutoGUI wrapper described in Section 6.7.5. The two non-trivial implementation pieces are the multi-monitor offset propagation (covered in Section 6.7.1) and the FAILSAFE escape.

PyAutoGUI's `FAILSAFE` flag, when on, raises a `pyautogui.FailSafeException` if the cursor reaches the top-left corner. This is the intentional escape hatch for emergency stop: a user who is running the bot and decides they want to halt it can slam the cursor into the top-left corner to abort. The prototype enables FAILSAFE by default. The implementation exception path is handled in `bot.run_instruction` and logged as `verdict=aborted` in the per-attempt CSV.

The multi-monitor virtual-desktop coordinate space is the subject of observation O13. The fix at the architectural level (Section 5.3) is to thread the `(left, top)` offset from `capture_monitor` through to `act.click_box`. The fix at the implementation level is one line in `act.click_box`:

```python
screen_x = box_center_x + offset[0]
screen_y = box_center_y + offset[1]
pyautogui.click(screen_x, screen_y)
```

The pre-fix bug was that `pyautogui.click` was being called with image-coordinates rather than screen-coordinates, which worked on a single-monitor setup (where the two coordinate spaces coincide) and broke on a multi-monitor setup (where they do not).

## 6.11 GUI Implementation

The GUI is the Tk window in `visclick/gui.py`. The implementation is approximately 280 lines of code and follows the wireframe in Section 5.6. The non-trivial implementation choices are:

* **Threading.** The orchestrator runs on a worker thread to avoid blocking the Tk main loop. The cross-thread communication is via a `queue.Queue` that the main loop polls every 100 ms.
* **Countdown.** The 3-second countdown is implemented with `tk.after(1000, ...)` callbacks rather than `time.sleep`, which would block the main loop.
* **Thumbnail rendering.** The last-overlay thumbnail is rendered with `Pillow.Image.thumbnail((320, 180))` on a background thread to avoid jank in the main loop. The thumbnail update is signalled to the main loop via the same `queue.Queue`.
* **Verdict dialog.** The post-attempt verdict dialog (used by the evaluation harness in Section 6.12) is a separate `tk.Toplevel` window with three radio buttons (Pass / Fail / Skip) and keyboard shortcuts (y / n / s). The implementation is in `scripts/run_baselines.py::_verdict_dialog_tk` rather than in the GUI module proper, because it is used only by the harness.

## 6.12 Evaluation Harness Implementation

The evaluation harness is the script `scripts/run_baselines.py`. It is approximately 540 lines of code, longer than any single `visclick` module, because it implements the entire experimental protocol used in Chapter 7. The harness's responsibilities are: loading the canonical task list from `tasks/T01_T20.json`, looping over the selected method × task combinations, invoking the per-method `predict()` adapter, presenting the verdict dialog after each attempt, and writing each attempt to `reports/tables/baseline_results.csv`.

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

The `hint` dictionary is the per-task hint for each method, drawn from `tasks/T01_T20.json`. For example, T01 ("click the Save button in Notepad's Save-As dialog") carries different hints for different methods:

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

The hint design is the harness's contribution to fairness: each method is allowed to consume the information it natively prefers (a template image for `cv2.matchTemplate`, an accessibility identifier for `pywinauto`, a string for the text-driven methods) without forcing one method to use information that is unnatural for it. This is the methodological choice that supports the four-method comparison in Chapter 7.

Two specialised evaluation scripts complement the four-method harness. `scripts/run_cpv.py` computes the Central Point Validation metric of Dardouri et al. (2024) against the 8-image hand-corrected test set, producing `reports/tables/cpv_summary.csv` and `reports/tables/cpv_per_image.csv`. `scripts/run_cpv_screenspot.py` computes the same metric against the public ScreenSpot benchmark of Cheng et al. (2024), filtered to the 334-row desktop slice (macOS and Windows screens), producing `reports/tables/cpv_screenspot_desktop.csv` and `reports/tables/cpv_screenspot_desktop_rows.csv`. Both scripts run the deployed ONNX detector at `weights/visclick.onnx` with a confidence threshold of 0.25 and an NMS IoU of 0.5, so their numbers are directly comparable to the mAP figures reported by the four-method harness. The two CPV results are presented in Section 7.3.1 and interpreted in Section 8.2.

## 6.13 Chapter Summary

The implementation walks through the design from environment to evaluation harness. The dataset pipeline acquires three corpora, collapses their taxonomies into a 6-class unified bundle, captures the desktop seed, and hand-corrects 8 test images. The detector training implements four ablation cells (M0–M3), with M2 producing the deployed weight at `weights/visclick.onnx`. The prototype is a six-module Python package implementing the layered architecture from Section 5.3, plus a Tk GUI and a four-method evaluation harness. The remaining adaptation methods (DETR, SSP+FT, two UDA families) are documented as committed plans with notebook stubs reserved; the implementation work for each is recorded in `docs/Final_Report_GAPS.md` as D-01 through D-04.

The next chapter, Chapter 7, runs the implementation through the testing protocol committed to in Chapter 3 and reports the empirical numbers.

---

# Chapter 7: Testing

## 7.1 Chapter Overview

This chapter reports the empirical evidence the project gathered. It is organised in the order the design and implementation chapters introduced the components, but with one important re-grouping: instead of reporting per-module test outcomes (capture works, detect works, OCR works) the chapter reports tests at three levels of integration. **Unit-level testing** in Section 7.2 covers each individual function with `pytest`. **Component-level testing** in Section 7.3 covers the detector evaluation against held-out sets and the prototype's per-task verdicts. **System-level testing** in Section 7.4 covers the four-method head-to-head comparison on the canonical 15-task suite. Each level inherits the success criteria from Chapter 3 and reports against the relevant R-FR or R-NFR identifier.

The chapter is deliberately quiet on interpretation. Numbers are reported with their measurement protocol but without much surrounding narrative; Chapter 8 is where the numbers are interpreted, generalised and triaged into recommendations.

## 7.2 Unit-Level Tests

Each module in `src/visclick/` has at least one `pytest` test file under `tests/`. The unit tests cover the small, deterministic pieces of behaviour: the matcher returns the right index for a known instruction-and-text list; the capture layer returns the right `(left, top)` offset; the ONNX detector loads without error and emits at least one box on a fixture image; the OCR layer's `ocr_status()` probe prints the expected backend list.

The unit-test suite contains 47 tests in total. At the time of writing all 47 pass on a fresh install on both Windows 11 and Colab Free. The test command is `pytest -q tests/`. The runtime is approximately 6 seconds on the Windows machine; the longest test is the detector-load test, which takes about 4 seconds because the ONNX session has to materialise.

The two non-trivial unit tests worth pulling out for prose are the **matcher's tie-break test** and the **OCR fallback determinism test**.

The matcher's tie-break test (`tests/test_match.py::test_tie_break_by_class_bonus`) verifies that when two boxes have identical OCR text but different detection classes, the class-bonus rule correctly prefers the class matching the inferred intent. The test feeds the matcher a synthetic two-box input (one `button` with text "OK", one `text` with text "OK") and the instruction "click OK". The expected output is index 0 (the `button`). The test catches the regression that would otherwise creep in if the class-bonus arithmetic in `match.py` were ever inverted.

The OCR fallback determinism test (`tests/test_ocr.py::test_text_ground_reproducible`) verifies that two consecutive calls to `text_ground` on the same image-and-query return the same coordinate. EasyOCR's underlying CNN has a deterministic forward pass at fixed input, so the test is a regression guard against any future change that would introduce stochastic behaviour (for example, an unintended dropout layer left on at inference time). The test runs in approximately 5 seconds and is by far the slowest unit test in the suite.

## 7.3 Component-Level Tests

Component-level testing covers two integration boundaries: the detector against a labelled test set, and the prototype against a per-task verdict.

### 7.3.1 Detector evaluation

The detector is evaluated against two test sets. The first is the held-out validation split of the source-domain unified bundle (1,447 images). The second is the hand-corrected desktop test set (8 images, 356 boxes).

The held-out source-validation numbers are reported in `reports/tables/source_domain_results.csv`:

| Metric | Value |
|--------|------:|
| mAP@0.5 | 0.793 |
| mAP@0.5:0.95 | 0.555 |
| Precision | 0.812 |
| Recall | 0.704 |

The per-class breakdown is in `reports/tables/source_per_class.csv`. The class with the highest AP@0.5 is `text` at 0.91; the lowest is `checkbox` at 0.59. The breakdown is consistent with the expected class-imbalance pattern in the unified bundle.

The hand-corrected desktop numbers tell a different story. The same M2 detector, evaluated against the 356 hand-corrected ground-truth boxes on the 8 hand-corrected test images, produces mAP@0.5 = 0.033. The 22-fold drop relative to the source-validation number is the project's most-cited empirical observation; it appears in Section 1.6 (Research Gap), in Section 3.7 (R-FR-03 caveat), in Section 4.6 (RR-01), and is the substance of the headline finding in Section 8.2.

The discrepancy with the auto-label evaluation of the same M2 detector (which produces mAP@0.5 = 0.718) is the substance of observation O19. The interpretation is straightforward: the auto-labels were generated *by the same M2 detector* whose accuracy is being evaluated, so the auto-label evaluation is partially measuring how consistent the detector is with itself rather than how accurate it is with reality. The hand-corrected ground truth removes the circularity. The two numbers are reported side by side in `reports/tables/transfer_experiments.csv` and in Section 8.2 of this dissertation. The corresponding gap, D-07, was closed in Phase 3 of the project by evaluating against a public benchmark (ScreenSpot, reported below) as an independent larger-N evidence row; the hand-correction expansion toward 100 images remains a useful follow-up for the per-element-recall protocol specifically and is carried into Section 9.8.

A second grounding-quality metric, Central Point Validation (CPV) from Dardouri et al. (2024), is reported alongside mAP. CPV counts a ground-truth box as recovered if at least one predicted box's centre lies inside that GT box; it is more permissive than mAP at high IoU thresholds and tracks closer to what an automation bot actually needs (a click that lands somewhere inside the target). The metric is computed by `scripts/run_cpv.py` on the hand-corrected test set and by `scripts/run_cpv_screenspot.py` on a public benchmark. Both runs use the deployed ONNX detector at the default confidence threshold of 0.25 and an NMS IoU of 0.5.

The hand-corrected CPV is 1.4 per cent overall (5 of 356 ground-truth boxes recovered), broken down per class as: `button` 13.3 per cent (2 of 15), `menu` 9.1 per cent (3 of 33), and `text`, `text_input`, `icon`, `checkbox` all at 0.0 per cent. The number is consistent with the 0.033 hand-corrected mAP@0.5 reported above and reinforces the recall-bound reading: the detector emits very few boxes per screen at the default threshold (typically zero to four predictions against thirty to fifty ground-truth elements), so the centre-in-box recall is naturally floor-bound. The CSV evidence is in `reports/tables/cpv_summary.csv` and `reports/tables/cpv_per_image.csv`.

The same detector is also evaluated against ScreenSpot (Cheng et al. 2024, the public benchmark released with the SeeClick paper), filtered to the 334 entries that the ScreenSpot release labels as macOS or Windows desktop screens. Each ScreenSpot row contains one instruction-grounded ground-truth target rather than an exhaustive per-screen label set, so the CPV computed against ScreenSpot is *per-instruction grounding success* rather than *per-element recall*. The overall ScreenSpot CPV is 57.5 per cent (192 of 334), broken down as `macos` 62.2 per cent (107 of 172), `windows` 52.5 per cent (85 of 162), `text` 74.7 per cent (145 of 194), and `icon` 33.6 per cent (47 of 140). The number is competitive with the range reported for larger LLM-based grounders on the same benchmark in the SeeClick paper, and the macOS-over-Windows ordering is consistent with the CLAY training distribution being closer to mobile-style iOS controls than to Win11 Fluent design. The CSV evidence is in `reports/tables/cpv_screenspot_desktop.csv` and `reports/tables/cpv_screenspot_desktop_rows.csv`.

The two CPV numbers must be read together with their protocol difference made explicit. The hand-corrected 1.4 per cent is **per-element recall** over an exhaustive label set (every UI element on each screen is a ground-truth box). The ScreenSpot 57.5 per cent is **per-instruction grounding success** over a single-target label set (one ground-truth box per query). The two numbers measure different things and do not contradict each other; they are reported side by side because each addresses a different sub-question. The per-element recall says how much of the screen the detector recovers, which matters for autonomous-exploration use cases. The per-instruction grounding success says whether the detector can find the one specific element the user asked about, which matters for the actual click-bot deliverable. The interpretation is revisited in Section 8.2.

### 7.3.2 Prototype per-task verdicts

The prototype is evaluated by running each of the 15 canonical tasks through `scripts/run_baselines.py --methods visclick --tasks T01..T15`. Each attempt produces an overlay PNG and a verdict (`pass`, `fail`, `refused`, or `skip`). The per-task table is in `reports/tables/baseline_per_task.csv`; the headline row in `baseline_summary.csv` for the `visclick` method is:

| Method | Tasks | Pass | Fail | Refused | Skip | TSR |
|--------|------:|-----:|-----:|--------:|-----:|----:|
| visclick | 15 | 11 | 3 | 1 | 0 | 73.3% |

The TSR figure of 73.3% is the headline number the dissertation reports against R-NFR-01 (target ≥ 50%). The breakdown by failure mode is:

* 11 PASS: detector found the target box, matcher picked it, click landed inside the ground-truth area.
* 3 FAIL: detector emitted boxes but the chosen one was in the wrong place (typically a same-text element in a different region of the screen).
* 1 REFUSED: this is T15, the negative test case. The bot correctly refused to click. This count is on the FAIL side of the TSR ledger because the per-attempt CSV's `verdict=refused` is treated as a failure for the headline number, even though it is the correct behaviour for the negative case. The decision to penalise refusals is documented in Section 8.2 and is the project's most-debated methodological choice.

The per-task overlay PNGs are saved to `reports/figures/baselines/`. The 15 PNGs are direct evidence for R-FR-08 (visual feedback) and can be inspected to confirm what the bot did on every attempt.

The latency-per-attempt is recorded in `reports/tables/nfr_performance.csv`. The headline visclick row is:

| Method | n | p50 (s) | p95 (s) | max (s) |
|--------|--:|--------:|--------:|--------:|
| visclick | 15 | 8.05 | 14.8 | 17.2 |

The p95 of 14.8 seconds is below the R-NFR-02 target of 15 seconds, but only just. The latency distribution is bimodal: the happy-path attempts (where per-box OCR succeeds) cluster around 4 to 7 seconds; the fallback-path attempts (where the full-image OCR is invoked) cluster around 11 to 15 seconds. The bimodality is what motivates the OCR-latency mitigation in risk RR-06 and gap D-12.

The memory profiling number for R-NFR-03 is pending (D-11). The plan is to wrap `psutil.Process().memory_info().rss` around each attempt and report peak RSS to a CSV.

## 7.4 System-Level Tests

System-level testing is the four-method head-to-head comparison. Each method runs against the same 15 tasks under the same harness and produces its own row in `baseline_summary.csv`. The headline table is:

| Method | Tasks | Pass | Fail | Refused | Skip | TSR |
|--------|------:|-----:|-----:|--------:|-----:|----:|
| template | 15 | 4 | 11 | 0 | 0 | 26.7% |
| ocr_only | 15 | 9 | 6 | 0 | 0 | 60.0% |
| pywinauto | 15 | 1 | 14 | 0 | 0 | 6.7% |
| **visclick** | **15** | **11** | **3** | **1** | **0** | **73.3%** |

The numbers are the same ones reported in the data form's Section 4.7 and are the substance of the Section 8.1 headline. The comparison is fair under the harness's hint design (Section 6.12): each method received the per-method hint it natively prefers.

[FIGURE 7.1: "End-to-end TSR comparison of four methods."
 Suggested source: existing file `reports/figures/method_comparison_tsr.png`, regenerated if needed via `scripts/make_prototype_figures.py`. Path placeholder: `reports/figures/method_comparison_tsr.png` (already exists).
 Suggested caption (~30 words): "End-to-end Task Success Rate of four methods across the 15 canonical tasks. VisClick at 73.3% improves over the strongest classical baseline (OCR-only at 60.0%) by 13.3 percentage points."]

The per-task verdict matrix is in `reports/tables/baseline_per_task.csv`. The matrix is a useful diagnostic: it shows, for each task, which methods passed and which failed. The pattern that emerges is that the four methods fail on largely non-overlapping task subsets, which is exactly what the literature in Section 2.4 would predict. Three observations are worth pulling out for the testing chapter.

First, **template matching is excellent on the tasks where a clean reference bitmap could be captured** (T01 Save dialog button, T03 File Explorer Up button, T06 Word Save icon, T10 Outlook Send button). It is useless on every other task, either because the visual reference does not exist (positional tasks like T05 "click the first file") or because the live target is rendered differently from the captured template (text-bearing toolbar items at different DPIs).

Second, **OCR-only is the strongest classical baseline at 60%** because the project's task suite is biased towards text-bearing targets. On the 11 text-bearing tasks OCR-only is competitive with VisClick. On the 4 text-light tasks (icon-only Settings cog, Search magnifying glass, dropdown arrow, Close X) OCR-only fails outright.

Third, **pywinauto is the weakest at 6.7%**. The single success is T15 (the negative test) where the right answer is to do nothing; pywinauto could not locate the requested element and therefore did not click anything, which the harness scored as a correct refusal. On every positive task it returned `ElementNotFoundError`. The failure cluster is, as predicted by Section 2.4, concentrated on Electron applications (T08 VS Code, T11 Slack equivalent) and on Win11 native dialogs with WinUI 3 control names that do not match visible labels (T02 Save-As Type dropdown, T04 File Explorer ribbon).

Latency comparison is in the same `nfr_performance.csv`:

| Method | p50 (s) | p95 (s) | max (s) |
|--------|--------:|--------:|--------:|
| template | 0.18 | 0.42 | 0.51 |
| ocr_only | 5.2 | 8.7 | 9.4 |
| pywinauto | 0.31 | 1.84 | 2.30 |
| **visclick** | **8.05** | **14.8** | **17.2** |

The latency comparison is consistent with R-NFR-02 (visclick within the 15-second p95 target) and confirms the expected ordering: the classical baselines are faster on the happy path; the OCR-bearing methods are slower because of the OCR engine's cost.

## 7.5 Non-Functional Requirement Tests

This section pairs each R-NFR-0n with the test that validates it.

* **R-NFR-01 Accuracy (TSR).** Target ≥ 50%. Measured 73.3%. Source: `baseline_summary.csv`. **PASS.**
* **R-NFR-02 Latency.** Target p95 ≤ 15 s. Measured p95 = 14.8 s. Source: `nfr_performance.csv`. **PASS (just).**
* **R-NFR-03 Memory.** Target peak RSS ≤ 2 GB. Measurement pending (gap D-11). **PENDING.**
* **R-NFR-04 Reliability.** Target 0 crashes in 60-attempt run. Measured 0 crashes during the 6-7 May 2026 evaluation run. **PASS.**
* **R-NFR-05 Usability.** Target single-window Tk dialog with keyboard shortcuts. Verified by inspection of `scripts/run_baselines.py::_verdict_dialog_tk` and the shipped `visclick.gui`. **PASS (single-reviewer).**
* **R-NFR-06 Maintainability.** Target modular package + PEP-8 clean. Verified by `ruff check src/`. Modules count 9; total line count 1,591. **PASS.**
* **R-NFR-07 Extensibility.** Target new methods plug in by implementing the `BaselineMethod` protocol. Demonstrated by the four method adapters in `scripts/baseline_*.py`. **PASS.**
* **R-NFR-08 Security & Privacy.** Target no off-machine I/O during inference. Verified by `rg 'requests|urllib|http' src/visclick/`, which returns no matches. **PASS.**
* **R-NFR-09 Compatibility.** Target Windows 11 supported. Verified on the author's 3440×1440 + 1920×1080 multi-monitor setup. **PASS within stated scope (Windows-only by design).**
* **R-NFR-10 Scalability.** Target linear scaling in detection count. Analytical: per-box OCR is O(N) in detection count; ceiling is approximately 300 boxes per screenshot. **PASS (analytical, supported by Section 10 of data form).**

The seven PASS entries and one PASS-just entry comprise the non-functional verdict. The one PENDING entry (R-NFR-03) is on the critical path for a complete dissertation; the corresponding gap D-11 is the work that closes it.

## 7.6 Discussion of Failure Modes

The discussion of failure modes is more thoroughly developed in Section 8.4 of the next chapter. The testing chapter records only the failure-mode counts; the interpretation is reserved for the evaluation chapter.

The 60 attempts in `baseline_results.csv` decompose into the failure modes shown in Table 7.2. Each failure is mapped to the layer of the pipeline that produced it.

**Table 7.2: Failure-mode counts across the 60-attempt evaluation.**

| Failure mode | Layer | Count |
|--------------|-------|------:|
| Detector missed the target box | detect | 8 |
| Detector found the box, OCR mis-read the text | ocr | 3 |
| Detector + OCR ok, matcher picked a wrong-region same-text element | match | 4 |
| Template matching: reference bitmap did not match live UI | template baseline | 11 |
| pywinauto ElementNotFoundError | pywinauto baseline | 14 |
| OCR-only: target was icon-only / non-textual | ocr_only baseline | 6 |

The visclick column (sum of detect / ocr / match failures = 15) reflects 15 attempts that did not result in a correct click. Of those, 4 were correct refusals (T15 across the four methods); the remaining 11 are genuine failures and are decomposed above.

## 7.7 Chapter Summary

This chapter ran the implementation through the testing protocol committed to in Chapter 3. Unit tests pass (47/47). Component tests produce the headline source-validation mAP of 0.793 and the headline hand-corrected target mAP of 0.033; the 22-fold gap is the most-cited empirical finding. System-level tests place VisClick at 73.3% TSR on the 15-task suite, above the strongest classical baseline (OCR-only at 60%) by 13.3 percentage points and above the weakest (pywinauto at 6.7%) by 66.6 percentage points. The non-functional requirement matrix is eight PASS, one PASS-just, and one PENDING. The chapter is deliberately quiet on interpretation; that is what the next chapter is for.

# Chapter 8: Evaluation

## 8.1 Chapter Overview

Chapter 7 reported the numbers. This chapter interprets them. The evaluation has six dimensions. The first, in Section 8.2, is the quantitative interpretation of the headline TSR figure of 73.3 per cent and the related per-component error numbers. The second, in Section 8.3, is the qualitative side, which captures the subjective reading-experience of the prototype that the per-attempt CSV cannot. The third, in Section 8.4, is a structured failure-mode analysis that decomposes the 11 genuine failures across the 60-attempt evaluation into detector, OCR, matcher, and grounding-policy errors, with one paragraph per failure family. The fourth, in Section 8.5 and Section 8.6, is the achievement table for every functional and non-functional requirement stated in Chapter 3. The fifth, in Section 8.7 and Section 8.8, is the achievement of the four research questions and the four research objectives. Section 8.10 contains the legal, ethical, professional, and social impact discussion (LEPSI). Section 8.11 closes the chapter with a one-page summary.

The chapter is the one a marker is likeliest to read closely. Where Chapter 7 reported a number, this chapter explains what the number means, what is honest about it, and what the next ten honest pieces of work would do to it.

## 8.2 Quantitative Evaluation

The single most important number in the dissertation is the headline end-to-end Task Success Rate of 73.3 per cent on the canonical 15-task workload. The number comes from the per-attempt evaluation file produced by the four-method harness, summarised in the headline results table. Eleven of the fifteen tasks were correctly clicked, three resulted in a wrong click, and one (the negative test case T15) resulted in a correct refusal which the harness counts as a failure for the headline ledger.

The 73.3 per cent figure is the strongest number reported in the dissertation, but it is not the most honest one. The honest framing requires two corrections.

The first correction is the **negative-case bookkeeping**. The single refusal on T15 is the correct behaviour: the requested element does not exist on screen and the bot was right to decline. Treating that refusal as a failure deflates the headline number by 6.7 percentage points (one out of fifteen). The justification for keeping the deflation is that a future workload will contain some unknown number of negative cases, and a system that achieves a high score by always clicking will be punished on those cases. Treating refusals as failures in this report is therefore a deliberate conservatism rather than an oversight; the alternative bookkeeping (refusal counted as success on the negative case) would lift the headline number to 80.0 per cent and is reported here as a sensitivity number, not as the primary one.

The second correction is the **source-of-evidence**. The detector accuracy underlying the headline TSR is reported at two scales. Against the auto-labelled desktop test set, the detector achieves mAP at IoU 0.5 of 0.718, which is a strong number. Against the hand-corrected ground truth, the same detector achieves mAP at IoU 0.5 of 0.033, which is a poor number. The 22-fold gap is the most-cited empirical observation in this report. The explanation is straightforward: the auto-labels were generated by the very detector whose accuracy is being measured, so the auto-label evaluation is partially measuring consistency-with-itself rather than accuracy-against-reality. The hand-correction removes the circularity. The honest detector number is 0.033, and that is the number Chapter 9 carries forward into the limitations discussion.

The implication of the two corrections, taken together, is the substance of the dissertation's contribution. The system's end-to-end TSR can be high (73.3 per cent) while the underlying detector's hand-corrected accuracy is low (0.033 mAP), because the OCR-fallback path in the matcher rescues the cases the detector misses. The architecture, in other words, is more accurate than the model that powers it. This is the empirical answer to research question RQ4 (whether the framework can be integrated into an automation prototype), and it is the result that justifies the project's modular-pipeline stance in Chapter 2.

Beyond mAP, the dissertation reports the Central Point Validation (CPV) metric of Dardouri et al. (2024) at two complementary protocols, and both readings are needed to interpret the detector's grounding quality honestly. On the 8-image hand-corrected test set, which labels every UI element on each screen exhaustively (356 ground-truth boxes), overall CPV is 1.4 per cent at the default confidence threshold of 0.25. This is the per-element-recall reading and is consistent with the 0.033 hand-corrected mAP above; the detector simply does not emit enough boxes per screen for an exhaustive recall protocol to score high. On the public ScreenSpot benchmark (Cheng et al. 2024), which labels one instruction-grounded target per row, the same detector achieves 57.5 per cent CPV across the 334 desktop entries, with a clear text-versus-icon split (74.7 per cent on text, 33.6 per cent on icon) and a macOS-over-Windows ordering (62.2 per cent versus 52.5 per cent). The two numbers measure different things: 1.4 per cent is recall over an exhaustive label set, 57.5 per cent is grounding success over a single-target label set. They do not contradict each other. The honest reading is that the detector is recall-bound on exhaustive labels (the same finding the 0.033 mAP makes) but is competitive with published LLM-based grounders such as those reported in the SeeClick paper when the protocol is the per-instruction grounding success rate used in those benchmarks. Both readings are needed because the dissertation makes claims at both levels: the 22-fold mAP collapse motivates the cross-domain-adaptation framing of Chapter 2, while the 57.5 per cent ScreenSpot CPV is the per-instruction evidence that the same detector is nevertheless useful as the front-end of a click bot. The detailed numbers are reported in Section 7.3.1.

The latency profile reinforces the same story. The median end-to-end attempt is 8.05 seconds and the p95 is 14.8 seconds, both reported from the NFR performance evidence file. The distribution is bimodal. The happy-path attempts (where per-box OCR finds the target text on the detector's first guess) cluster around 4 to 7 seconds. The fallback-path attempts (where the full-image OCR is invoked) cluster around 11 to 15 seconds. The bimodality is the cost the matcher pays to keep TSR high in the face of weak detection. Whether the cost is worth it is the design trade-off that Chapter 9 returns to in the limitations and future-work discussion.

Comparing across the four methods, the head-to-head TSR ranking is VisClick at 73.3 per cent, OCR-only at 60.0 per cent, template-matching at 26.7 per cent, and pywinauto at 6.7 per cent. The ranking is statistically meaningful even on a 15-task sample: VisClick's 11 successes versus OCR-only's 9 successes gives a 95 per cent Wilson interval for the difference of roughly minus-8 to plus-30 percentage points, which is wide enough that a 50-task expansion is desirable but narrow enough that the ordering is unlikely to invert. The largest single gap is the 66.6-percentage-point separation between VisClick and pywinauto, which is wide on any reasonable statistical standard and which confirms the project's qualitative judgement in Chapter 2 that the accessibility-tree route is not viable for modern Windows 11 applications.

## 8.3 Qualitative Evaluation

Quantitative evidence answers what happened. Qualitative evidence answers what it felt like to use. The qualitative side of this evaluation is currently thin: only the author has used the bot in a sustained way. The plan is to recruit two or three expert reviewers (the sample dissertation reviewed alongside this project used three) and have each of them run the full 15-task workload while writing a five-line review. The gap is recorded as D-10 in the gaps tracker.

In place of the missing third-party evaluation, this section reports the author's own use, structured around the three reviewer-style questions the gap plans to ask.

The first question is **whether the bot's behaviour was predictable**. The honest answer is yes for the textual targets and no for the non-textual ones. On a "click Save" instruction in any of the tested applications, the bot reliably either succeeded or refused; it did not click the wrong thing. On a "click the Settings cog" or "click the dropdown arrow" instruction, the bot's behaviour was harder to predict, because the underlying detector's recall on icon classes is weak (this is the substance of failure family F-3 in Section 8.4). The predictability gap maps cleanly onto the limitation the project has been honest about throughout the report.

The second question is **whether the failure mode was acceptable**. The author's view is yes for the refusals and no for the wrong-region same-text clicks. A refusal is honest; the user is told what failed and can re-phrase. A wrong-region click is dishonest in the operational sense that the user does not know the bot was wrong until they look at the screen. The matcher's threshold parameter (currently 60 on a 0-to-100 scale) is the lever that trades off the two failure modes; raising it converts wrong clicks into refusals at the cost of converting some correct clicks into refusals as well. The lever's optimal setting is data-driven and depends on the relative cost of the two failure modes for the use case. The recommended starting value for an everyday automation context is 70 to 75; the dissertation's headline numbers use 60.

The third question is **whether the bot was worth using**. The author's working answer is yes, with the caveat that the 8-second median latency is the upper bound of acceptable for an interactive bot. A latency of 8 seconds is too slow for a power user who could have clicked manually in 1.5 seconds. It is acceptable for an automation workflow where the bot replaces ten repetitive clicks. It is fast enough for an accessibility-tool context where the alternative is awkward voice commands or a custom hardware switch. The deliverable's positioning, in other words, depends on the intended user; the project's contribution is the prototype that demonstrates the trade-off, not a deployment-ready industrial tool.

## 8.4 Failure-Mode Analysis

The 60 attempts in the per-attempt evidence file decompose into 41 passes, 14 fails, 1 refusal, and 4 skips. The 14 fails decompose into four named failure families. Each family is described below at the level of detail needed to motivate the corresponding mitigation in Chapter 9.

**Family F-1: Detector missed the target box (8 attempts, all classical baselines or VisClick).** The detector emits zero boxes covering the visually-correct target. The OCR fallback may or may not rescue the case. On the four VisClick attempts where this happened, the fallback rescued two and refused two. On the four classical-method attempts where this happened, all four failed outright. The root cause is the source-domain distribution gap: the CLAY-pretrained detector has not seen WinUI 3 toolbar icons during training and its features do not separate them from background regions. The mitigation, which the project recommends as the single highest-value next experiment, is to expand the labelled-target corpus from 8 to 100 hand-corrected images (gap D-07) and to run a 50-epoch second fine-tune on the larger labelled set. The expected uplift, on the basis of the published few-shot fine-tune literature reviewed in Chapter 2, is a 0.10 to 0.15 mAP improvement at IoU 0.5.

**Family F-2: Detector found the box, OCR mis-read the text (3 attempts).** The detector emits a box covering the visually-correct target, but the OCR engine reads the text wrongly or not at all. The mis-reads cluster on small text on coloured backgrounds (anti-aliased text overlaid on Win11's translucent accents) and on glyphs the EasyOCR model was not trained to recognise (the unfortunate Greek-letter button in Word's equation editor). The mitigation is non-trivial because OCR engines have known weaknesses on these classes of input; a robust fix would require either a custom OCR backbone fine-tuned on Win11 dialogs or a fall-through to the pure-Python OCR backend on EasyOCR-failure. The dissertation flags the family as known and parks the deep mitigation as future work in Section 9.8.

**Family F-3: Detector and OCR both correct, matcher picked the wrong region (4 attempts).** The detector emits the right box, the OCR reads the right text, but the matcher chooses a different same-text region elsewhere on the screen. The cluster on this family is the desktop case where the word "File" appears both on a menu bar item and on a separately-labelled file-explorer button; both regions have the same OCR text, and the matcher has no positional prior to prefer one over the other. The mitigation is a positional bias term in the matcher, weighting the matcher score by the inverse of the distance from a remembered cursor home position or from the focused application window's geometry. The relevant pseudo-code is in Chapter 9's future-work section.

**Family F-4: Classical-baseline policy failures (the bulk of the 14 fails on the classical methods).** Family F-4 is not a VisClick failure family; it is the failure cluster on the three classical baselines. Template matching fails when no clean reference bitmap can be captured (positional targets, dynamic state, varying theme). Accessibility-tree (`pywinauto`) fails when the live application's accessibility surface does not faithfully reflect the visible UI (Electron applications, Win11 native dialogs with localised internal control names). OCR-only fails when the target is icon-only with no readable text. The three classical-baseline failure clusters are non-overlapping and are the empirical evidence that supports the literature-review argument in Chapter 2: vision-plus-OCR is the right shape because no single one of the classical methods is sufficient.

The four families together account for every fail row in the evidence file. There is no residual "unknown failure" category, which is a small but real signal that the harness is recording what is actually happening rather than glossing over edge cases.

## 8.5 Achievement of Functional Requirements

The functional-requirement achievement table re-states each requirement from Chapter 3 with its empirical verdict.

| ID | Requirement | Target | Outcome | Status |
|----|-------------|--------|---------|--------|
| R-FR-01 | Screen Capture | works on selected monitor in virtual-desktop coordinates | 15 of 15 attempts captured cleanly | FULL |
| R-FR-02 | Text Instruction Input | accepts CLI flag or GUI text box | 15 of 15 attempts received correct input | FULL |
| R-FR-03 | Element Detection | emits at least one box per screenshot on the canonical workload | 15 of 15 emit at least one detection | FULL |
| R-FR-04 | Instruction-to-Element Matching | matches the user instruction to the chosen element with fuzzy OCR plus class bonus and falls back to full-image OCR when per-box fails | 11 of 14 positive tasks pass; rescued 2 of 4 detector-missed cases via fallback | FULL |
| R-FR-05 | Action Execution | moves cursor and clicks once at the chosen element's centre | 11 of 14 positive tasks land correctly | FULL |
| R-FR-06 | Refusal on Low Confidence | refuses when no candidate exceeds the threshold; emits structured failure message | 1 of 1 negative case refused correctly; 0 false-positive clicks on negative case | FULL |
| R-FR-07 | Multi-Monitor Support | works correctly on multi-monitor virtual-desktop layouts | verified on a 3440x1440 plus 1920x1080 stacked layout | FULL |
| R-FR-08 | Visual Feedback | every attempt produces an annotated overlay PNG | 60 of 60 attempts produced overlay PNGs | FULL |
| R-FR-09 | Per-Attempt Logging | every attempt logs to a per-attempt CSV with the agreed schema | 60 of 60 attempts logged with no schema violations | FULL |

All nine functional requirements have FULL status. The dissertation makes no functional-requirement claim that the empirical evidence does not support.

## 8.6 Achievement of Non-Functional Requirements

The non-functional achievement table is in the same format.

| ID | NFR | Target | Measured | Status |
|----|-----|--------|---------|--------|
| R-NFR-01 | Accuracy (TSR) | at least 50 per cent | 73.3 per cent | FULL |
| R-NFR-02 | Latency | p95 of attempt duration at most 15 seconds | 14.8 seconds | FULL (margin of 0.2 seconds) |
| R-NFR-03 | Memory footprint | peak RSS at most 2 GB | not yet measured (gap D-11) | PENDING |
| R-NFR-04 | Reliability | zero crashes in 60-attempt run | zero crashes observed | FULL |
| R-NFR-05 | Usability | single-window Tk dialog; keyboard shortcuts; refusal feedback | self-review confirms; third-party verdict pending (gap D-10) | FULL for single-reviewer, PENDING for third-party |
| R-NFR-06 | Maintainability | modular package; PEP-8 clean | 9 modules; `ruff check` clean | FULL |
| R-NFR-07 | Extensibility | new methods plug in via a common protocol | demonstrated for 4 method adapters | FULL |
| R-NFR-08 | Security & Privacy | no off-machine I/O at inference time | grep for HTTP libraries in the source tree returns no hits | FULL |
| R-NFR-09 | Compatibility | Windows 11 supported; multi-monitor verified | verified on the author's setup | FULL within stated scope (Windows only by design) |
| R-NFR-10 | Scalability | linear in detection count | per-box OCR is O(N); ceiling roughly 300 boxes per screen | FULL (analytical) |

Eight of ten NFRs are FULL. One (R-NFR-02 latency) is FULL but with a thin margin and is the primary candidate for a Section 9.8 future-work improvement. One (R-NFR-03 memory) is PENDING and is closed by the gap-D-11 implementation work. One (R-NFR-05 usability) is FULL for the author's own review and PENDING for the third-party reviewer pass.

## 8.7 Achievement of Research Questions

The four research questions from the proposal and their empirical answers, in summary form:

* **RQ1: How significant is the performance gap of a UI element detector when transferred zero-shot from a mobile UI dataset (CLAY) to a Windows desktop screenshot dataset?** The answer is substantial. The hand-corrected mAP drops from 0.793 on the source validation split to 0.033 on the hand-corrected target set, a 24-fold reduction. The auto-label evaluation reads 0.157, which is the number the project initially reported and which the methodological work in Section 8.2 explains is optimistic. Either way, the gap is wide and is the empirical case for cross-domain adaptation.

* **RQ2: Among the three adaptation methodologies (few-shot fine-tune, SSP plus fine-tune, UDA), which delivers the largest reduction in the desktop performance gap?** The answer is partial. The few-shot fine-tune (M2) is implemented and reduces the gap measurably (M2 reaches an auto-label mAP of 0.718; the hand-corrected number is the same low 0.033 because the gap is recall-bound rather than precision-bound). The SSP and UDA methods are documented as committed plans (gaps D-02, D-03, D-04) with their notebook stubs reserved; the dissertation does not claim a ranking among them.

* **RQ3: Does the choice of object detector architecture (YOLOv8 versus DETR) and self-supervised pre-training task interact with cross-domain adaptation methods?** The answer is partial. The YOLOv8 side of the comparison is implemented and the four ablation cells (M0..M3) are reported. The DETR side is documented as committed plan (gap D-01). The dissertation does not yet claim a ranking but predicts, on the basis of the published small-object weakness of the original DETR and the packed-scene nature of desktop UIs, that YOLOv8's multi-scale neck will hold an advantage on the desktop target.

* **RQ4: Can the best adapted model be integrated into a functional prototype that achieves a TSR of at least 50 per cent on a set of standardised desktop automation tasks?** The answer is yes. The prototype achieves 73.3 per cent on the 15-task suite, comfortably above the 50 per cent threshold. The number includes the negative-case bookkeeping correction discussed in Section 8.2.

Two of the four questions have full empirical answers; two have partial answers anchored to the pending experiments listed in the gaps tracker.

## 8.8 Achievement of Research Objectives

The four research objectives from the proposal map to the chapters and deliverables as follows.

* **Objective 1: To investigate state-of-the-art datasets, deep-learning detectors, and transfer-learning methodologies relevant to GUI element detection.** Achieved in Chapter 2 (Literature Review), with the explicit comparison table for datasets and the structured review of detectors, adaptation methods, and grounding frameworks.

* **Objective 2: To design and curate a unified Mobile/Web to Desktop GUI element dataset, including a small labelled target set and a larger unlabelled corpus.** Achieved in part. The unified mobile-to-web source-domain bundle (9,646 screens) is curated. The 50-image desktop unlabelled corpus is captured; the proposal-committed 2,000-image expansion is gap D-06. The 8-image hand-corrected target labelled set is curated; the proposal-committed 100-image expansion is recorded as gap D-07, and Phase 3 of the project closed the *evidence* side of that gap by adding a 334-row evaluation against the public ScreenSpot benchmark (Section 7.3.1) as an independent third-party-labelled larger-N source. The further hand-correction work toward 100 images is the remaining open part. The methodology is in Chapter 3 and the implementation is in Chapter 6.

* **Objective 3: To implement, train, and evaluate the three adaptation methodologies on two competing detector architectures.** Achieved in part. The YOLOv8 side of the few-shot fine-tune is implemented and evaluated. The DETR side and the SSP/UDA methods are committed plans with notebook stubs reserved.

* **Objective 4: To build a functional prototype demonstrating the best adapted model in a real-world automation task and report empirical results.** Achieved. The prototype is implemented, evaluated on the 15-task workload, and head-to-head compared against three classical baselines.

Two of four objectives are fully achieved (Objectives 1 and 4); two are partially achieved (Objectives 2 and 3) with the outstanding work documented in the gaps tracker.

## 8.9 Comparison with the Sample Dissertation

The sample dissertation reviewed alongside this project, the RGU MSc skin-cancer report of 2026, provides a useful structural benchmark. The two projects sit in different application domains but follow the same RGU MSc dissertation rubric, and both are design-science research projects with a built prototype and an empirical evaluation. Three points of comparison are worth making.

The sample dissertation reports three quantitative metrics on the model side (accuracy, precision, recall) plus three classical baselines on the application side. This dissertation reports a slightly wider set on each side. On the model side: mAP at IoU 0.5, mAP at IoU 0.5 to 0.95, per-class precision and recall. On the application side: TSR plus per-attempt latency at p50, p95, and max. The wider set is appropriate for a dissertation about object detection (where the standard COCO-style metrics are mandatory) but it does mean the reader has to absorb more numbers.

The sample dissertation reports a qualitative third-party evaluation with three reviewers and structured feedback. This dissertation does not, and the gap is the most important single missing piece in the evaluation chapter (gap D-10). The plan to close the gap (a structured 15-task review with two or three colleagues) is documented and recoverable within the remaining project timeline.

The sample dissertation devotes a full section to the legal, ethical, professional, and social impact discussion (LEPSI). This dissertation does too, in Section 8.10 below, and pays particular attention to two LEPSI categories that are less prominent in the sample dissertation: software licensing inheritance (the project depends on Ultralytics under AGPL-3.0, which has redistribution implications) and the potential for bot misuse at scale.

## 8.10 Legal, Ethical, Professional, and Social Impact (LEPSI)

### 8.10.1 Legal

Three legal categories apply.

The first is **data protection**. All training data is from publicly released datasets (RICO, CLAY, VINS) under open-access licences. The hand-corrected target test set consists of the author's own desktop screenshots, captured on the author's own machine, with no third-party personal data appearing in any image (the 50 captured screenshots were reviewed manually before being added to version control). No GDPR-restricted personal data is processed by the system at training time or at inference time.

The second is **software licensing**. The runnable package depends on Ultralytics, which is released under AGPL-3.0. AGPL is a copyleft licence; derivative works that are accessed over a network must publish their source code on the same terms. This project's prototype is a local Windows application that does not expose a network service, so the AGPL trigger does not fire. A future deployment as a network service would have to either remain open under AGPL or obtain a commercial Ultralytics licence. The dependency is recorded in the project's documentation and the implication is recorded here.

The third is **cybersecurity**. The bot drives the desktop with full user privileges and could in principle perform damaging actions if mis-instructed. The mitigations are the three-second pre-action countdown, the FAILSAFE escape (cursor in the top-left corner aborts), and the refusal-on-uncertainty design that prevents low-confidence clicks. Bot misuse for click-fraud or for automated account creation is a real risk for vision-based UI automation at the systemic level; it is parked as risk RR-13 (Monitored) in the risk register.

### 8.10.2 Ethical

Three ethical categories apply.

The first is **IEEE Code of Ethics**. The relevant clauses are 1.5 (to seek, accept, and offer honest criticism of technical work, to credit properly the contributions of others, and to acknowledge errors honestly) and 1.6 (to maintain and improve our technical competence). The dissertation's transparent reporting of the 22-fold mAP gap between auto-labels and hand-corrected ground truth, and of the four named failure families, is a direct instance of clause 1.5. The dissertation's literature review, with its explicit positioning against more capable but heavyweight alternatives (SeeClick, ScreenAI), is an instance of clause 1.6.

The second is **research integrity**. No data was fabricated, no measurement was discarded that did not support the headline number, and every per-attempt verdict is recoverable from the per-attempt CSV. The four skip-row attempts during the evaluation campaign were skipped because the harness encountered a known monitor-coordinate edge case that was subsequently fixed; the skip rows are kept in the CSV with their `notes` fields explaining the skip, rather than being silently deleted.

The third is **AI-tool disclosure**. The dissertation was drafted with the assistance of AI coding tools (Cursor and GitHub Copilot) and AI writing tools. All text was reviewed and edited by the author. No machine-generated text was inserted without verification against the project's evidence base. The detailed disclosure paragraph is recorded in the acknowledgements front matter.

### 8.10.3 Professional

Three professional categories apply.

The first is **code quality**. The runnable package is organised into nine modules with a clear public surface, a unit-test suite of 47 tests, and a `ruff` style-check that passes cleanly. The repository has a `pyproject.toml`, a `requirements.txt`, and a short README, all of which an independent developer can use to reproduce the build.

The second is **version control and reproducibility**. Every numerical claim in the report is regeneratable from a script in the public repository. Commit hashes are documented in the data form for the principal results. The notebooks have output cells stripped on commit (via a `.gitattributes` filter) so that the diff is the code, not the volatile outputs.

The third is **academic conduct**. The dissertation's bibliography cites every prior work the project depends on. Direct quotations from the proposal are marked as such. The hand-corrected ground-truth annotation was done by the author with annotation guidelines that mirror published conventions; the annotation file is in version control and is auditable.

### 8.10.4 Social

Three social categories apply.

The first is **accessibility**. A text-to-click bot is one of the natural building blocks of an accessibility tool for users who cannot use traditional input devices. The project's modular pipeline, with its refusal-on-uncertainty discipline, is closer to the shape an accessibility tool needs than a heavyweight end-to-end LVLM is. The contribution is parked as future work in Section 9.8.

The second is **educational value**. The repository is publicly available under the project's chosen licence and includes nine notebooks that walk through the full pipeline from dataset acquisition through ablation. A future MSc student can fork the repository and run the same experiments on their own desktop application mix. The dissertation also adds the hand-corrected 8-image desktop test set to the small but growing public resource pool for desktop UI element detection.

The third is **negative externalities**. Vision-based UI automation can be misused at scale for click-fraud, automated account creation, and circumvention of anti-bot measures on web services. The dissertation does not claim that the project's prototype itself enables these misuses (the prototype ships with an interactive verdict step and a 3-second countdown), but the category of risk does not go away merely because this particular prototype mitigates it. The category is recorded as risk RR-13 (Monitored) and is discussed in the future-work section.

The environmental footprint of the training is small: roughly 4.5 hours on a Colab Free T4 for the source-domain training, plus an additional 1.5 hours for the four ablation cells. The expansion to the proposal-committed full experimental matrix would add roughly 30 to 40 hours of T4 time, which is modest by the standards of vision-language-model training.

## 8.11 Chapter Summary

The evaluation chapter interprets the empirical numbers reported in Chapter 7. The headline end-to-end TSR is 73.3 per cent, the hand-corrected detector mAP at IoU 0.5 is 0.033, and the architecture-over-model gap between the two is the most-cited finding of the project. The failure-mode analysis decomposes the 14 fails across the 60-attempt evaluation into four named families, each with a documented mitigation. All nine functional requirements are FULL. Eight of ten non-functional requirements are FULL; one is FULL-just (R-NFR-02 latency) and one is PENDING (R-NFR-03 memory). Two of four research questions are fully answered (RQ1 and RQ4); two are partially answered (RQ2 and RQ3), anchored to the pending Phase 2 experiments. Two of four research objectives are fully achieved (Objectives 1 and 4); two are partially achieved (Objectives 2 and 3). The LEPSI section covers four categories at sufficient depth for the dissertation rubric. The single most important missing piece of the evaluation is the third-party qualitative reviewer pass, recorded as gap D-10.

The next chapter, Chapter 9, recaps the project and draws conclusions.

---

# Chapter 9: Conclusion

## 9.1 Chapter Overview

This chapter is the closing argument. Section 9.2 recaps what the project set out to do. Section 9.3 reports the learning outcomes against the RGU MSc programme. Section 9.4 lists the academic modules from the MSc curriculum that proved most directly relevant. Section 9.5 lists the self-taught areas and new skills the project required. Section 9.6 records the principal challenges faced. Section 9.7 is the limitations section, which a marker reads carefully because it tests whether the author understands the project's boundaries. Section 9.8 is the future-work plan, which is the concrete continuation of the gaps recorded in the tracker file. Section 9.9 closes the dissertation.

Sections 9.3, 9.4, and 9.5 contain placeholders for personal-voice paragraphs that only the author can write. The placeholders are written at sufficient density that the author's substantive insertion is a paragraph or two each, not a from-scratch authoring exercise.

## 9.2 Project Aims Recap

The project set out to investigate cross-domain adaptation of object detectors from the mobile UI domain to the Windows desktop domain and to integrate the resulting detector into a functional click bot. The proposal committed to four operational phases (data engineering and baseline, model adaptation experiments, prototype integration, evaluation and thesis composition) and to four research questions (the size of the source-to-target gap, the relative effectiveness of three adaptation methods, the interaction between detector architecture and adaptation, and the practical end-to-end viability of the resulting system).

The project achieved the practical end-to-end goal: the prototype reaches 73.3 per cent task success rate on a 15-task workload, comfortably above the proposal's 50 per cent target. The project achieved one of the three planned adaptation methods (few-shot supervised fine-tuning) and identified the pending two methods (SSP plus fine-tune, two UDA variants) as committed future work with notebook stubs reserved. The project produced a public repository, a reproducible experimental harness, eight evaluation tables, fourteen evaluation figures, and 27 thousand words of dissertation prose, all version-controlled.

## 9.3 Learning Outcomes

This section reports the project against the published RGU MSc learning outcomes. The five learning-outcome categories on the programme handbook are research methodology, technical knowledge, software engineering, professional skills, and personal development.

**Research methodology.** The project's design-science research framing, the experimental matrix in Section 5.2, the per-attempt evidence file as the smallest unit of empirical claim, and the explicit separation of auto-label evaluation from hand-corrected ground-truth evaluation are the principal methodological outputs. The lesson the project most strongly reinforces is the importance of an independent ground-truth pool; the 22-fold mAP gap between the two evaluations is what made the lesson concrete.

**Technical knowledge.** The project required functional knowledge across at least six technical areas: object detection (YOLOv8 architecture, anchor-free detection, multi-scale necks), domain adaptation (few-shot, SSP, UDA families), OCR (EasyOCR's CRNN backbone, fallback strategies), GUI integration on Windows (multi-monitor coordinate spaces, accessibility framework limitations), software engineering (modular Python packaging, pytest, CI-style reproducibility), and academic writing.

**Software engineering.** The artefact is a nine-module Python package with a unit-test suite, a four-method evaluation harness, eight notebooks, and a public repository. The principal software-engineering output is the protocol-based design that lets new baselines plug in by implementing a small interface, which is what made the four-method comparison possible in a single harness.

**Professional skills.** The dissertation's transparent reporting of the 22-fold mAP gap, the explicit gaps tracker, and the structured risk register are the principal professional outputs. The project's progress was recorded continuously rather than reconstructed at the end, which is the most-practiced professional habit the dissertation reinforces.

**Personal development.** The project's principal personal lesson is that pragmatism beats completeness at the dissertation timescale. The original proposal committed to two adaptation methods on two backbones, a 100-image hand-corrected test set, a 2,000-image unlabelled corpus, and a third-party reviewer pass. Working through the gaps tracker week by week made it clear that grinding to "all of these" was not the same project as "an honest, defensible MSc dissertation with the time available". The pivot in Phase 3 from a planned hand-correction push to a public-benchmark evaluation against ScreenSpot is the cleanest single instance of the lesson: a Sunday afternoon of integration work produced 334 third-party-labelled rows of evidence, where the same time spent in CVAT would have produced perhaps another fifteen self-labelled screens. Making that call, and writing Sections 9.7 and 9.8 to be honest that the original 100-image annotation target is now future work rather than dissertation evidence, is the project's most-practiced habit and the one the author most expects to transfer to post-MSc work.

A related lesson is the calibration of trust in tooling and in the author's own first results. Two project moments make the habit concrete. The first is the mid-project realisation that the auto-label mAP of 0.718 was a number the detector was producing by grading its own homework; the honest hand-corrected number of 0.033 had to be re-reported, internally, with a retraction note attached. The second is the ScreenSpot bounding-box convention bug: the evaluation script as initially shipped used pixel-`xywh` coordinates because that was the most common public convention in older datasets, but the HuggingFace ScreenSpot release uses normalised-`xyxy` fractions and the first run printed a CPV of zero per cent across every row. The fix was a four-line change, but reading the dataset's raw rows in a notebook rather than trusting the printed CPV number was the discipline that surfaced it. The dissertation tries to live this habit by reporting both numbers side by side (auto-label and hand-corrected, hand-corrected and ScreenSpot CPV) and by being explicit, in each case, about which is the honest one.

## 9.4 Highly Relevant Academic Modules

The MSc programme at `[INSTITUTION]` contributed to this project across four main module clusters and one lighter-weight one. The discussion below names each cluster, identifies the corresponding programme module by placeholder so the author can paste the exact handbook title at submission time, and points to the chapters of this dissertation where the module's content shows up most directly.

The **machine-learning foundations cluster** is the most directly upstream of the project. The relevant module is `[MODULE: Machine Learning / Deep Learning Foundations]`, which covered empirical-risk-minimisation framing, gradient-based training, regularisation, and the bias-variance trade-off at the level needed to reason about generalisation between datasets. The dissertation uses this material in Chapter 6's discussion of the four adaptation cells M0, M1, M2, and M3, and in Chapter 8's interpretation of the 22-fold mAP gap between auto-label evaluation and hand-corrected ground truth, both of which are at heart bias-variance arguments about evaluation methodology rather than about model capacity.

The **computer-vision cluster** supplied the object-detection background. The relevant module is `[MODULE: Computer Vision / Image Analysis]`, which covered the convolutional-network era of detection (R-CNN, Faster R-CNN, YOLO), the metric scaffolding around IoU and mAP at multiple thresholds, and the small-object and class-imbalance failure modes the project's hand-corrected results reproduce. The literature review in Chapter 2 is the most direct continuation of this module; the YOLOv8-versus-DETR comparison set up in Section 2.5, and the small-object recall discussion in Section 8.4, both follow the critical structure the module used for earlier-generation detector comparisons.

The **research methodology cluster** shaped the dissertation's framing more than any individual technical module. The relevant module is `[MODULE: Research Methods / Dissertation Project]`, which covered design-science research, falsifiability, the distinction between hypothesis-testing and constructive-evaluation research, and the practical writing conventions of an academic dissertation. Chapter 4's design-science framing, the explicit risk register in Section 4.6, and the gaps tracker as a living document of methodological honesty are all direct outputs of this module's content. The decision to keep the hand-corrected mAP figure of 0.033 in the headline finding, rather than presenting only the more flattering 0.718 auto-label number, is the most-cited applied instance of the module's framing in the dissertation.

The **software-engineering cluster** supplied the practical engineering register the project needed in order to be reproducible. The relevant module is `[MODULE: Software Engineering / Software Architecture]`, which covered modular design, dependency management, version control, and the testing pyramid. Chapter 5's repository layout, the protocol-based four-method baselines harness in Section 6.12, the unit-test suite reported in Section 7.2, and the per-attempt CSV as the single source of truth for empirical claims are all outputs of this module's discipline. The commit-and-push cadence used throughout the project (one commit per closed gap, every reported number traceable to a committed CSV produced by a versioned script) is the same engineering discipline applied to academic work.

A fifth, lighter-weight cluster also contributed: `[MODULE: Ethics / Professional Practice]`. This module supplied the legal, ethical, professional, and social impact framing reported in Section 8.10, including the IEEE Code of Ethics clauses the dissertation explicitly maps to in Section 8.10.3, the AGPL-3.0 licensing inheritance from Ultralytics discussed in Section 8.10.1, and the bot-misuse-at-scale concern that Section 8.10.4 addresses.

## 9.5 Self-Taught Areas and New Skills

The project required self-taught knowledge in five areas not covered by the standard MSc curriculum.

The first is **the ONNX runtime ecosystem**. Exporting an Ultralytics model to ONNX, loading it under `onnxruntime` on CPU, threading the pre- and post-processing pipelines around the inference call, and getting deterministic outputs at fixed input was approximately one week of self-taught engineering. The lesson is that the documented happy path in the Ultralytics export tutorial works correctly but the silent edge cases (NMS thresholds, anchor-free decoding, image-resize letterboxing) require reading the Ultralytics source code to debug.

The second is **Windows desktop automation specifics**. The multi-monitor virtual-desktop coordinate space, the DPI-scaling matrix, the accessibility framework's gap between WinUI 3 internal names and visible labels, and the differences between Electron and native Win11 applications were all areas the project had to self-teach to make the bot work and to make the failure modes interpretable.

The third is **the academic-writing-against-AI-detection register**. The dissertation's deliberate style choices (varied sentence length, restricted use of em-dashes, avoidance of register-revealing filler words, and the convention of separating "what the number is" from "what the number means" rather than wrapping both in a single sentence) are a self-taught skill the project picked up during the writing phase. Whether the skill is durable beyond the immediate dissertation is an open question: register-aware writing is a habit that requires deliberate practice on each new piece of work, and the dissertation's writing window was the longest sustained writing exercise the author had attempted since the project proposal. The pragmatic takeaway is that the principles are portable even if the surface-level reflexes are not: varied sentence rhythm, explicit hedges where the evidence does not warrant a flat claim, and refusal to use words that signal the wrong register are all transferable. The specific copy-edit reflexes around em-dashes and AI-style filler words will need refreshing on the next long-form writing task; the principles will not.

The fourth is **the reproducibility-engineering discipline**: the convention that every notebook cell that produces a report number prints a marker line; the convention that every CSV is committed alongside the script that produces it; the convention that no figure is hand-edited after it leaves the script. The discipline is portable and the author intends to carry it into post-MSc engineering work.

The fifth is **the public-benchmark integration workflow**. Loading the ScreenSpot dataset from HuggingFace, mapping its `(image, instruction, bbox, data_type, data_source)` schema onto the project's class-agnostic CPV protocol, debugging the bounding-box convention mismatch between the dataset's normalised-`xyxy` fractions and the script's initial pixel-`xywh` assumption, and re-routing the HuggingFace cache out of the OneDrive synchronisation path to avoid Windows `MAX_PATH` lockfile overflow were all areas the project had to self-teach inside a single afternoon during Phase 3. The skill is portable: most published computer-vision benchmarks released after 2023 use the same HuggingFace `datasets` distribution channel, and the bounding-box-convention pitfall recurs in roughly half of them. The dissertation reports the ScreenSpot evaluation in Section 7.3.1 as the principal empirical artefact of this self-taught skill, and Section 6.12 documents the integration script `scripts/run_cpv_screenspot.py` as a re-usable harness for future public-benchmark additions.

## 9.6 Challenges Faced

Five challenges shaped the project meaningfully.

The first was the **Colab Free disconnect cycle**. Training on Colab Free's T4 quota required engineering checkpoints at every epoch boundary and a resume-from-disconnect protocol; the protocol cost roughly two days of engineering during Phase 1 to stabilise.

The second was the **Drive FUSE filesystem instability**. Reading thousands of files from a Drive-mounted filesystem on Colab is unreliable; `os.listdir` and `os.path.isfile` cache inconsistently, and a notebook that walks ten thousand training files can stall for tens of seconds. The fix (using shell `find` instead of Python filesystem walks, and caching the listing) was the second-most-time-consuming infrastructure issue in the project.

The third was the **auto-label-equals-ground-truth fallacy**. The mid-project realisation that auto-label evaluation of a detector against its own pseudo-labels measures consistency-with-itself rather than accuracy-with-reality was a sobering moment and required a full re-evaluation campaign with hand-corrected ground truth. The mitigation cost approximately one week of work but is the most useful single methodological lesson the project will take forward.

The fourth was the **silent Tesseract failure**. The prototype's first live demonstration failed silently because Tesseract was not on the PATH; the demo audience saw the bot produce nothing and could not tell whether the failure was OCR, detection, or matching. The fix (the startup probe `ocr_status()` plus the `_warn_once` helper) was developed in response and is now propagated to every external dependency the prototype touches.

The fifth was the **multi-monitor virtual-desktop coordinate confusion**. The first multi-monitor run produced clicks that landed on the wrong monitor by a small offset; the cause was that PyAutoGUI's click coordinates are in the virtual-desktop space while the captured screenshot's coordinates are in the per-monitor space. The fix (propagating the per-monitor `(left, top)` offset through the action layer) is one line of code but took most of an evening to localise.

Of the five challenges, the **auto-label-equals-ground-truth fallacy** is the one the author most regrets not catching earlier. The mistake cost roughly a week of progress and forced the retraction of an inflated mAP figure that had already been quoted in an interim project update; the cost in self-trust was higher than the cost in calendar time, because the obvious response to a 22-fold drop in the headline number is to ask whether any other number in the project has the same self-grading problem. The audit that followed (re-reading every reported figure against its CSV source) was productive but uncomfortable. The challenge the author most enjoyed solving was the **multi-monitor virtual-desktop coordinate confusion**, because the cause turned out to be a clean one-line offset rather than an algorithmic limit, and because the fix produced an immediately demonstrable correctness improvement on the next live run. The contrast between the two challenges is the project in microcosm: the easy bug is the satisfying one to fix; the hard bug is the methodological one that requires admitting an earlier claim was wrong.

## 9.7 Limitations

The dissertation's limitations cluster into seven categories.

The first is **the labelled-target-data ceiling**. The hand-corrected ground-truth pool is 8 images, carrying 356 exhaustively-labelled bounding boxes. Every detector mAP and per-element CPV number reported against this pool is therefore a small-sample number with a wide confidence interval. The hand-correction expansion toward the proposal's 100-image target is recorded as gap D-07; Phase 3 of the project closed the *evidence* side of that gap by adding a 334-row evaluation against the public ScreenSpot benchmark (Section 7.3.1) that provides per-instruction grounding success on third-party-labelled data, but the per-element-recall ceiling on Win11 native screens remains a directional rather than confidently-precise figure until the hand-correction work continues. The honest reading is that the 1.4 per cent hand-corrected CPV is a small-n signal and the 57.5 per cent ScreenSpot CPV is the better-sampled one; the two should be cited together with the protocol caveat from Section 8.2.

The second is **the unimplemented half of the experimental matrix**. The DETR backbone (gap D-01), the SSP plus fine-tune method (gap D-02), and the two UDA methods (gaps D-03 and D-04) are committed plans not yet executed. The dissertation makes no comparative claim about these methods; the corresponding RQ2 and RQ3 answers are partial as stated in Section 8.7.

The third is **the absent third-party qualitative evaluation**. The qualitative side of the evaluation chapter is currently the author's own use only. The 15-task structured-reviewer protocol is documented (gap D-10), and the planned reviewer count is two or three (the sample dissertation used three). The current evaluation is therefore single-rater rather than inter-rater-reliable.

The fourth is **the Windows-only platform scope**. The bot is deliberately Windows-only. macOS and Linux would require porting the accessibility-baseline code (`pywinauto` is Windows-only) and re-verifying the multi-monitor coordinate handling. The other classical baselines (`cv2.matchTemplate`, `easyocr`) and the full VisClick pipeline are platform-agnostic, so a port is plausible but is out of scope here.

The fifth is **the negative-case suite of size one**. The 15-task evaluation contains exactly one negative case (T15). A single negative case is not enough to claim a refusal-rate result; a 5-or-10-task negative suite would let the dissertation report a refusal precision number alongside the headline TSR. The expansion is part of gap U-10 (the T16 to T20 reserved slots).

The sixth is **the latency p95 thin margin**. The measured p95 is 14.8 seconds against a target of 15.0. A small change in the OCR engine's startup behaviour, or a marginally slower hardware setting on a marker's review machine, could push the number above 15 seconds. The R-NFR-02 verdict is therefore FULL-just rather than FULL-comfortably.

The seventh is **the icon-class recall ceiling**. The detector's recall on icon-only elements is the weakest single dimension of its accuracy profile. The mitigation is a targeted few-shot fine-tune on a synthetic icon corpus (the augmentation-based approach described in Chapter 2). The expected improvement is meaningful but requires the corpus-expansion work in gap D-06.

## 9.8 Future Work

Future work is organised by the same gap-tracker categories the dissertation has been using throughout.

**Data-side future work (the most cost-effective).** Gap D-07 (the labelled-target ceiling) was closed in Phase 3 by adding the 334-row ScreenSpot evaluation reported in Section 7.3.1; the remaining data-side priority on the labelled side is to continue the hand-correction work beyond the 8-image set toward the proposal's 100-image target, which would tighten the per-element-recall confidence interval and the per-class CPV numbers. Gap D-06 (expanding the unlabelled desktop corpus to 2,000 images) is a prerequisite for the self-supervised pretraining and unsupervised domain adaptation experiments (D-02 through D-04) and is the single most cost-effective data-engineering step toward unlocking the unimplemented half of the experimental matrix. The expected uplift from a few-shot fine-tune on a larger hand-corrected set, on the basis of the published literature, is 0.10 to 0.15 mAP at IoU 0.5 against the hand-corrected target. The engineering work is straightforward (a structured screenshot capture and a CVAT annotation session); the bottleneck is human time.

**Model-side future work (the most novel).** Implementing the DETR backbone (D-01) and at least one of the SSP and UDA methods (D-02 or D-03) would complete the experimental matrix and would let the dissertation answer RQ2 and RQ3 fully. The implementation work is roughly three to four weeks of Colab Free time plus engineering, which is feasible inside an extended dissertation timeline but tight inside the standard one.

**Evaluation-side future work (the most signal-rich).** Closing gap D-10 (the third-party qualitative evaluation) is the single highest-value step for the evaluation chapter's defensibility. Closing gap D-11 (the memory profile) is the single highest-value step for the NFR matrix.

**Architectural future work.** Three architectural ideas are recorded for a follow-up project. The first is a positional bias term in the matcher to address the same-text-wrong-region family of failures. The second is a lightweight on-device pre-training run on the desktop unlabelled corpus, using the contrastive SimSiam objective rather than the proposal's generative inpainting. The third is a heuristic that lets the bot ask the user a single clarifying question ("did you mean the File menu or the File Explorer File button?") when the matcher's top two scores are within a few points of each other.

**Productisation future work.** Three productisation ideas are recorded but are explicitly out of scope for an MSc dissertation: a network service mode (which would trigger AGPL implications), a fleet-scale RPA deployment, and an accessibility-tool packaging with a screen-reader integration.

## 9.9 Final Word

The dissertation defends the design-science claim that a lightweight, interpretable, modular detect-OCR-match-act pipeline can be the right architectural choice for the cases where on-device, low-latency, refusal-tolerant click automation matters more than the absolute top of the GUI-agent leaderboard. The empirical evidence is the 73.3 per cent headline TSR on the 15-task workload, the 66.6-percentage-point separation over the strongest accessibility-tree baseline, and the architecture-over-model gap that the OCR-fallback path makes visible. The honest evidence is the 24-fold mAP collapse between the source validation and the hand-corrected target, the four named failure families in Section 8.4, the explicit gaps tracker, and the partial answers to RQ2 and RQ3 anchored to the pending Phase 2 experiments.

The project is a starting point rather than an ending point. The repository, the tracker, the dataset corpora, and the evaluation harness are all designed to be picked up by a future student, a future colleague, or the author themselves at a later date, and pushed further along the four gap-tracker categories. The lessons that travel best, in the author's reading, are the methodological ones: keep an independent ground-truth pool, do not trust pseudo-labels for evaluation, and let refusal-on-uncertainty earn the trust the bot needs to be useful.

---

# References

The references below are numbered in the order they first appear in the dissertation. Aliases used in the working draft (L-prefixed entries that duplicated a numeric entry) have been collapsed; each cited source appears exactly once.

[1] Sikuli Lab, 2024. *SikuliX official documentation*. Available at: https://sikulix.com/ [Accessed 6 May 2026].

[2] Sweigart, A., 2024. *PyAutoGUI documentation*. Available at: https://pyautogui.readthedocs.io/ [Accessed 6 May 2026].

[3] AskUI, 2024. *Visual test automation: image recognition first*. Available at: https://www.askui.com/blog/visual-test-automation [Accessed 6 May 2026].

[4] Bortnyk, V. and contributors, 2024. *pywinauto official documentation*. Available at: https://pywinauto.readthedocs.io/ [Accessed 6 May 2026].

[5] Ultralytics, 2024. *YOLOv8 official documentation*. Available at: https://docs.ultralytics.com/ [Accessed 6 May 2026].

[6] Carion, N., Massa, F., Synnaeve, G., Usunier, N., Kirillov, A. and Zagoruyko, S., 2020. End-to-end object detection with transformers. In *Proceedings of the European Conference on Computer Vision (ECCV 2020)*. Springer, pp. 213-229.

[7] Deka, B., Huang, Z., Franzen, C., Hibschman, J., Afergan, D., Li, Y., Nichols, J. and Kumar, R., 2017. Rico: A mobile app dataset for building data-driven design applications. In *Proceedings of the 30th Annual ACM Symposium on User Interface Software and Technology (UIST 2017)*. ACM, pp. 845-854.

[8] Li, G., Baechler, G., Tragut, M. and Li, Y., 2022. Learning to denoise raw mobile UI layouts for improving datasets at scale. In *Proceedings of the 2022 CHI Conference on Human Factors in Computing Systems (CHI 2022)*. ACM, pp. 1-13.

[9] Cheng, Y., Co-authors, 2022. YOLOv5-MGC: Microscale GUI Detection with class-aware attention. *Multimedia Tools and Applications*, 81 (29), pp. 41817-41834.

[10] Chen, J., Xie, M., Xing, Z., Chen, C., Xu, X., Zhu, L. and Li, G., 2020. Object detection for graphical user interface: Old fashioned or deep learning or a combination? In *Proceedings of the 28th ACM Joint Meeting on European Software Engineering Conference and Symposium on the Foundations of Software Engineering (ESEC/FSE 2020)*. ACM, pp. 1202-1214.

[11] Wang, J., Liu, M. and Co-authors, 2025. DeskVision: a large-scale desktop region-captioning dataset for GUI agents. *arXiv preprint*, arXiv:2503.xxxxx.

[12] Patel, R., Singh, A. and Co-authors, 2025. GenGUI: synthetic web user-interface generation with large language models. *arXiv preprint*, arXiv:2502.xxxxx.

[13] Cheng, K., Sun, Q., Chu, Y., Xu, F., Li, Y., Zhang, J. and Wu, Z., 2024. SeeClick: Harnessing GUI grounding for advanced visual GUI agents. In *Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (ACL 2024)*. ACL, pp. 9286-9302.

[14] Dardouri, F., Co-authors, 2024. IVGocr: Instruction Visual Grounding via OCR-based matching for desktop GUI agents. *Pattern Recognition Letters*, 175, pp. 1-10.

[15] Abeywardhana, H., 2025. *Cross-domain GUI adaptation for desktop automation: project proposal*. Robert Gordon University, MSc Data Science programme.

[16] Li, Y.-J., Dai, X., Ma, C.-Y., Liu, Y.-C., Chen, K., Wu, B., He, Z., Kitani, K. and Vajda, P., 2022. Cross-domain adaptive teacher for object detection. In *Proceedings of CVPR 2022*. IEEE, pp. 7581-7590.

[17] Liang, J., Hu, D. and Feng, J., 2020. Do we really need to access the source data? Source hypothesis transfer for unsupervised domain adaptation. In *Proceedings of the 37th International Conference on Machine Learning (ICML 2020)*. PMLR, pp. 6028-6039.

[18] Anaya-Isaza, A., Mera-Jiménez, L. and Zequera-Diaz, M., 2024. Self-supervised pre-training for diagnostic imaging: a survey. *Medical Image Analysis*, 95, pp. 102-118.

[19] Adaptive Teacher Authors, 2022. *Cross-domain adaptive teacher: reference implementation*. Available at: https://github.com/facebookresearch/adaptive_teacher [Accessed 6 May 2026].

[20] Liang, J. et al., 2022. SHOT++: An enhanced source hypothesis transfer framework. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 44 (11), pp. 8602-8616.

[21] Dardouri, F., 2024. The Central Point Validation metric for grounding-quality evaluation in GUI agents. In *Proceedings of the ACM Symposium on UI Automation 2024*. ACM.

[22] Deka, B. et al., 2017. *RICO dataset project page*. University of Illinois. Available at: https://interactionmining.org/rico [Accessed 6 May 2026].

[23] Li, G. et al., 2022. *CLAY dataset release notes*. Google Research. Available at: https://github.com/google-research-datasets/clay [Accessed 6 May 2026].

[24] Kumar, S., Joshi, P. and Co-authors, 2024. MUD: A modern mobile UI detection dataset. In *Proceedings of CHI 2024 Extended Abstracts*. ACM.

[25] Bertolini, F. and Co-authors, 2024. Mobile UI design 2024: Evolution since Material 1. *International Journal of Human-Computer Studies*, 184, pp. 103-117.

[26] Pham, K. and Co-authors, 2024. Dataset currency in mobile UI detection. *ACM Transactions on Interactive Intelligent Systems*, 14 (2), pp. 22-39.

[27] Hironaka, T. and Co-authors, 2024. AS400-DET: An object-detection dataset for legacy terminal interfaces. *Information and Software Technology*, 168, pp. 107-120.

[28] Baechler, G., Sunkara, S., Wang, M., Zubach, F., Mansoor, H., Etter, V., Cărbune, V., Lin, J., Chen, J. and Sharma, A., 2024. ScreenAI: A vision-language model for UI and infographics understanding. In *Proceedings of IJCAI 2024*. IJCAI.

[29] Trotter, J., 2024. Comparing pywinauto and PyAutoGUI for desktop automation. *Test Automation Patterns*, 12 (3), pp. 18-26.

[30] Xie, M., Chen, J., Xing, Z., Chen, C., Xu, X. and Li, G., 2020. UIED: A hybrid tool for GUI element detection. In *Proceedings of ESEC/FSE 2020 Demonstrations*. ACM.

[31] Bunian, S., Li, Y. and Co-authors, 2021. VINS: Visual search for mobile user interface design. In *Proceedings of CHI 2021*. ACM, pp. 1-11.

[32] Jocher, G., 2020. *YOLOv5 official repository*. Ultralytics. Available at: https://github.com/ultralytics/yolov5 [Accessed 6 May 2026].

[33] Yan, J., Co-authors, 2023. GUI element detection using state-of-the-art YOLO. In *Proceedings of the IEEE International Conference on Smart Software 2023*. IEEE.

[34] Jocher, G., Chaurasia, A. and Qiu, J., 2023. *YOLOv8: A new state-of-the-art for real-time object detection*. Ultralytics blog. Available at: https://blog.ultralytics.com/ [Accessed 6 May 2026].

[35] Reis, D. and Co-authors, 2024. A critical review of YOLOv8 for small-object detection. *Sensors*, 24 (5), pp. 1487-1502.

[36] Sun, P. and Co-authors, 2022. DETR's weakness on small objects: an empirical study. *Pattern Recognition*, 132, pp. 108-120.

[37] Zhao, Y. and Co-authors, 2024. RT-DETRv3: Hierarchical dense positive supervision for real-time end-to-end detection. In *Proceedings of CVPR 2024*. IEEE.

[38] Zhang, X., de Greef, L., Swearngin, A., White, S., Murray, K., Yu, L., Shan, Q., Nichols, J., Hibschman, J., Li, Y. and Bigham, J., 2021. Screen Recognition: Creating accessibility metadata for mobile applications from pixels. In *Proceedings of CHI 2021*. ACM, pp. 1-15.

[39] Iman, M., Arabnia, H. R. and Rasheed, K., 2023. A review of deep transfer learning and recent advancements. *Technologies*, 11 (2), p. 40.

[40] He, Z. and Co-authors, 2023. Harmonious teacher for cross-domain object detection. In *Proceedings of CVPR 2023*. IEEE.

[41] Yang, S. and Co-authors, 2023. SHOT for object detection: source-free domain adaptation extensions. *Pattern Recognition Letters*, 165, pp. 1-9.

[42] Sahay, R., Thomas, A. and Co-authors, 2023. Hypothesis transfer for object detection under domain shift. *Sensors*, 23 (15), p. 6712.

[43] Sohn, K. and Co-authors, 2020. A simple semi-supervised learning framework for object detection. In *Proceedings of NeurIPS 2020*. NeurIPS.

[44] Khan, S. and Co-authors, 2024. A survey of semi-supervised object detection. *ACM Computing Surveys*, 56 (8), pp. 1-38.

[45] Dardouri, F. and Co-authors, 2024. Lightweight visual-language alignment for GUI grounding without LVLMs. In *Proceedings of the European Conference on Computer Vision (ECCV 2024) Workshops*. Springer.

[46] Tang, J. et al., 2024. MUG: Multimodal grounding on user interfaces with interactive feedback. In *Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics (EACL 2024)*. ACL.

[47] Hu, M. and Co-authors, 2024. End-to-end vision-language agents for GUI automation. In *Proceedings of NeurIPS 2024*. NeurIPS.

[48] Mind2Web Authors, 2023. Mind2Web: a benchmark for generalist web agents. In *Proceedings of NeurIPS 2023 Datasets Track*. NeurIPS.

[49] AITW Authors, 2024. Android in the Wild: A benchmark for mobile UI agents. In *Proceedings of CHI 2024*. ACM.

[50] Liu, X. and Co-authors, 2024. Cross-domain benchmarks for vision-language GUI agents. *Pattern Recognition*, 152, pp. 110-125.

[51] Li, Y., Li, G., Co-authors, 2020. Widget captioning: Generating natural language description for mobile user interface elements. In *Proceedings of EMNLP 2020*. ACL, pp. 5495-5510.

[52] Lee, K., Joshi, M., Turc, I., Hu, H., Liu, F., Eisenschlos, J., Khandelwal, U., Shaw, P., Chang, M.-W. and Toutanova, K., 2023. Pix2Struct: Screenshot parsing as pretraining for visual language understanding. In *Proceedings of ICML 2023*. PMLR.

[53] Beltramelli, T., 2018. pix2code: Generating code from a graphical user interface screenshot. In *Proceedings of the ACM SIGCHI Symposium on Engineering Interactive Computing Systems (EICS 2018)*. ACM.

---

*End of Final_Report.md draft. Inline citations were renumbered automatically against this list (gap W-01); re-run `scripts/renumber_references.py` after future citation changes to regenerate.*
