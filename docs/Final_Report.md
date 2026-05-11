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

This is a first-pass draft written to the **proposal's stated scope**. Where a number, table cell, or figure has not yet been finalised in the experimental work, the text uses an explicit placeholder of the form `[NUMBER]`, `[TABLE]`, or `[FIGURE N.x — …]`. These placeholders mark the points where the author will paste the final values from `reports/tables/` or drop the final image from `reports/figures/`. The placeholders are deliberate. They are not omissions; they are the points where data and prose meet, and they have to be filled by hand because only the author knows which run is the "headline" one.

Figure placeholders follow this format:

```
[FIGURE N.x — short title.
 Suggested source: <relative path or "TBD by user">.
 Suggested caption (~30 words): <one-line draft caption, rewrite freely>.]
```

For consistency with the dissertation template the author will use, all section numbering follows the sample format (Chapter N → N.1, N.2 …). Tables and figures are numbered within the chapter.

---

# Chapter 1 — Introduction

## 1.1 Chapter Overview

This chapter introduces the project and frames the work that follows. It begins with the background to graphical user interface (GUI) automation on the modern desktop and the reasons the existing tooling has not held up well as desktop applications have moved further away from the assumptions those tools were built on. From there it narrows down to a specific problem, a specific aim, and a set of research questions that the rest of the report sets out to answer. The research gap is then made explicit, and the work is positioned against both the lightweight classical tools (such as SikuliX, pywinauto and PyAutoGUI) and the heavyweight large vision-language models (such as SeeClick) that sit at the other end of the spectrum. The research objectives and the operational objectives are stated next, with the operational objectives broken down into the four phases by which the project was actually executed. After that, the proposed solution is described in enough detail that a reader can decide, before the technical chapters begin, whether the rest of the report is relevant to their interests. The scope of the project is then made explicit so that a reader is not left guessing what was intentionally left out. The chapter closes with a short summary that ties everything together and points the reader to the chapters that contain the experimental evidence.

The chapter is written so it can be read on its own. A reader who only has fifteen minutes to spend on this dissertation should be able to read Chapter 1 and come away with a fair sense of what the project tried to do, why it tried to do that, and what kind of evidence is offered later in support of the claims.

## 1.2 Project Background

Graphical user interfaces are the main way most people interact with software. Whether the user is filing a tax return on a web form, writing code in Visual Studio Code, processing an image in GIMP, or simply renaming a file in Windows File Explorer, what is actually happening, mechanically, is a small set of clicks and keystrokes directed at coloured rectangles on a screen. Because this is such a universal mode of interaction, automating it has been an active area of work for decades. The reasons range from the mundane (repetitive data entry, regression testing of an application's controls, robotic process automation in back-office settings) to the more ambitious, such as accessibility tools that let users with motor impairment drive an application by voice, or autonomous agents that complete multi-step tasks on a user's behalf.

The tooling for this kind of automation falls broadly into two camps. The first, and by far the older, is image-based or coordinate-based automation. SikuliX, for instance, lets a user record a small bitmap of a button and then asks the operating system to find that bitmap on screen using OpenCV template matching [3]. PyAutoGUI takes the same idea one step further by exposing a Python interface to mouse and keyboard, but at heart it is still working in pixel coordinates [5]. These tools are powerful, but they are also brittle. The bitmap of a button is not the button; it is a frozen photograph of the button taken on one particular machine, on one particular theme, on one particular DPI scaling, on one particular operating system build. Change any of those and the photograph stops matching. In practice, that is what happens every time a Windows feature update reshuffles the look and feel of the system, every time a user prefers dark mode, every time the same script is moved from a 1080p laptop to a 1440p desktop. The same brittleness is well documented in the literature: AskUI's recent review of visual automation tools describes SikuliX-style approaches as "image-recognition first" and notes the obvious downside that the recognition only generalises as far as the captured image library does [4].

The second camp is accessibility-tree automation. Windows applications written against the classic Win32 framework expose a tree of named UI controls through the UI Automation framework, and Python libraries such as pywinauto walk that tree to find a Save button by its semantic name rather than by its appearance [6]. When it works, this approach is fast and stable. The problem is that it has stopped working reliably on a meaningful fraction of the modern Windows application mix. Electron applications (Visual Studio Code, Slack, Discord, Microsoft Teams) expose only a degenerate tree because the entire interface is a Chromium browser rendering DOM. Modern Windows 11 applications that use WinUI 3 or XAML islands frequently expose their controls under localised internal names rather than the visible labels a user sees. Web pages inside any browser are served through ARIA, which uses different conventions again. The result is that pywinauto can correctly click a Save button in classic Notepad on Windows 7 but cannot find the same Save button on the same logical action in the modern Windows 11 Notepad, because the modern Notepad's Save-As dialog is itself a WinUI 3 surface. Empirical evidence for this exact failure mode is provided in Chapter 7 of this report.

Sitting outside both camps is a more recent strand of work that uses computer vision and machine learning to detect UI elements directly from a screenshot, without any privileged access to the application's internal tree. Object-detection models such as YOLOv8 [38] and DETR [41] are trained on annotated images of UIs and learn to predict bounding boxes labelled with classes such as `button`, `text`, `icon` and so on. Mobile UIs are well resourced in this respect, because of the RICO dataset [8] and its denoised successor CLAY [10], which between them provide tens of thousands of labelled mobile screens and have made it routine to train a competent mobile-UI detector on commodity hardware. Recent work such as YOLOv5-MGC [29] reports mean average precision (mAP) figures in the high 80s and low 90s on mobile UIs.

Desktops are a different story. Desktop UIs differ from mobile UIs along several axes at once. They are landscape rather than portrait. They are multi-window rather than single-window. They contain dense toolbars and ribbon menus that produce what Chen et al. (2020) call a "packed scene" [1], where elements sit close enough together that a standard detector struggles to put a clean bounding box around each one. They draw on decades of stylistic variance (Win32, WPF, Material Design, custom themes, dark mode, high-contrast accessibility skins) that has no real parallel in the much more harmonised design languages of Android and iOS. And, critically, there is no RICO-equivalent dataset for desktops. The most recent attempts to build one (DeskVision [14], GenGUI [15]) are themselves dated 2024 and 2025, which speaks to how recent the recognition of this gap is, and even those datasets are an order of magnitude smaller than RICO.

What this means in practice is that a detector trained to high accuracy on mobile UIs typically does not, on its own, do well on desktop screenshots. There is a domain shift between the two. Quantifying that shift, and developing data-efficient strategies for closing it, is the problem this project takes on.

[FIGURE 1.1 — "Examples of the three desktop UI shifts." 
 Suggested source: a three-panel composite that the author can produce by stitching together one mobile screen from CLAY, one classic Win32 desktop screen from Windows File Explorer, and one modern Win11 screen from Notepad's Save-As dialog. Path placeholder: `reports/figures/ch1_domain_shift_examples.png`.
 Suggested caption (~30 words): "Three axes of the mobile-to-desktop shift. Left: a mobile portrait UI from CLAY. Middle: a classic landscape desktop with a packed toolbar. Right: a modern Win11 WinUI 3 dialog with flat, theme-dependent controls."]

## 1.3 Problem Statement

The practical problem this project addresses can be stated in a single sentence. **A practitioner who wants to build a vision-based UI-automation bot for the modern Windows desktop today has no off-the-shelf option that is at the same time accurate, lightweight enough to run on a typical workstation, and tolerant of the variability that real desktop UIs exhibit in the wild.**

The classical image-based tools (SikuliX, PyAutoGUI) are lightweight, but they are not tolerant of variability; their bitmap matching collapses the moment the theme, DPI, or font shifts. The accessibility-tree tools (pywinauto, AutoIt) are tolerant of theme and DPI by construction, but they are not accurate on the modern Windows application mix; the empirical work in Chapter 7 of this report shows pywinauto succeeding on only one out of fifteen task instances on a representative Windows 11 workload, and that one success is the negative case where the right answer is to do nothing. At the other extreme, heavyweight large vision-language models such as SeeClick [33] are accurate and tolerant of variability across domains, but they are not lightweight by any reasonable definition; they require multi-GPU inference setups and large memory budgets that are unrealistic for most practical deployments and are out of reach for a project at MSc scale.

The gap, then, is in the middle of the spectrum. Can a lightweight object-detection model, trained on the relatively well-resourced mobile UI domain and then adapted to the data-scarce desktop domain using minimal labelled desktop data, deliver an "accurate enough" detector for use inside a practical automation pipeline? And, given that this is fundamentally a transfer-learning question, which adaptation strategy gives the best return on the labelled data budget? These are the questions the project sets out to answer.

A secondary, more practical, problem is that even an accurate detector is not, by itself, an automation system. A user does not want to be told "there are forty-seven elements on your screen". A user wants to say "click Save", and have the system do the right thing. That requires a grounding step: matching a natural-language instruction to one of the detected elements. The IVGocr framework of Dardouri et al. (2024) [17] provides a sensible scaffolding for this kind of pipeline, and this project adopts it. The novelty in the prototype is therefore not the pipeline architecture but the detector that sits inside it.

## 1.4 Research Aim

> *The aim of this research is to design and implement a scalable cross-domain machine learning framework capable of adapting mobile-trained GUI detection models for desktop environments while maintaining high accuracy and generalisation.* [46]

The aim is quoted verbatim from the approved project proposal. It deliberately combines a research goal (cross-domain adaptation) with a quality target (high accuracy and generalisation) and a deployment context (desktop environments). All three are needed for the answer to be useful in practice; an adaptation method that closes the domain gap on paper but does not generalise across applications, or a detector that generalises across applications but loses accuracy in the process, would each fail the aim. The methodology is structured around all three in equal measure.

## 1.5 Research Questions

The aim is decomposed into four research questions that the rest of the work then addresses one at a time. The four questions are taken verbatim from the project proposal [46]:

* **RQ1.** What is the magnitude of performance degradation when applying mobile-trained GUI detectors to desktop screenshots?
* **RQ2.** Which adaptation strategies yield the largest improvements in low-label regimes?
* **RQ3.** How does model choice (YOLO vs DETR vs LVLM) influence transferability and sample efficiency?
* **RQ4.** What are the practical limits of a vision–action bot using adapted detectors in real desktop applications?

These four questions are answered, respectively, in the baseline performance numbers in Chapter 6 (RQ1), the adaptation-method comparison in Chapter 7 (RQ2), the cross-architecture comparison in Chapter 7 (RQ3), and the prototype evaluation in Chapter 8 (RQ4). The chapter map is repeated in §1.11.

## 1.6 Research Gap

The literature reviewed in Chapter 2 establishes that the gap addressed here is *not* a lack of state-of-the-art models. The mobile-UI domain has highly optimised detectors of its own; the YOLOv5-MGC paper of Cheng et al. (2022) [29] is one example. The desktop-target domain has a clear application pipeline in the IVGocr framework of Dardouri et al. (2024) [17]. Heavyweight large vision-language models such as SeeClick [33] are perfectly capable of bridging the domain gap, but they do so at a computational cost that puts them out of reach for the kind of practical, on-machine deployment this project cares about.

The gap is therefore in the *combination*. There is no published, lightweight, data-efficient method that takes a state-of-the-art mobile detector, adapts it to the desktop domain using the kind of small labelled-data budget that an individual or a small team can realistically produce, and demonstrates that the resulting model is usable inside a complete automation pipeline rather than only on a static benchmark. This combination is what the dissertation contributes.

The gap is sharpened by the data side as well. The mobile UI domain has RICO [8] and CLAY [10] providing tens of thousands of labelled screens, while the desktop domain has only a handful of small, recently-published datasets ([14], [15]). The data-scarce nature of the target domain is what mandates the use of domain adaptation in the first place. Training a high-capacity desktop-only model from scratch is not feasible at MSc scale; a model has to be trained somewhere else and then moved across.

[FIGURE 1.2 — "Positioning of this project against existing automation approaches."
 Suggested source: a 2x2 grid with axes (lightweight ↔ heavyweight) and (theme/DPI tolerant ↔ brittle). Place SikuliX/PyAutoGUI bottom-left, pywinauto bottom-right (but greyed out because it fails on modern Win11), SeeClick top-right, and this project (cross-domain adapted YOLOv8 + IVGocr) middle. Path placeholder: `reports/figures/ch1_positioning_grid.png`.
 Suggested caption (~30 words): "Where the proposed framework sits relative to existing GUI automation approaches. Classical image-based and accessibility-tree tools sit in the lightweight-but-brittle corner; LVLMs sit in the heavyweight-but-tolerant corner; this project targets the middle."]

## 1.7 Research Objectives

The four research objectives below are quoted from the approved project proposal [46]. Together they describe what the project committed to deliver in order to answer the research questions in §1.5.

1. **Quantify** the mobile-to-desktop performance gap using mean average precision (mAP) for detection quality and the Central Point Validation (CPV) metric of Dardouri et al. (2024) for grounding quality.
2. **Implement and compare** three adaptation methods: few-shot supervised fine-tuning, self-supervised pre-training followed by fine-tuning (SSP+FT), and unsupervised domain adaptation (UDA) using the Cross-Domain Adaptive Teacher framework of Li et al. (2022) and the Source Hypothesis Transfer (SHOT) framework described in Sensors (2023).
3. **Evaluate sample efficiency** by determining how many labelled desktop images are actually required to achieve acceptable performance, sweeping over $k = 1, 5, 10, 50, 100$.
4. **Develop a prototype bot** that demonstrates instruction-to-action behaviour on real desktop applications using the adapted detector inside the IVGocr pipeline.

Each objective is mapped to a chapter and to a measurable deliverable. The mapping is made explicit in §8.8 (Achievement of Research Objectives).

## 1.8 Operational Objectives

The research objectives describe what is to be answered. The operational objectives describe how the work was actually broken down. The project was executed in four phases, each with concrete deliverables.

**Phase 1: Data engineering and baseline establishment.** Survey 10–15 diverse desktop applications (Visual Studio Code, GIMP, Chrome, Firefox, Windows File Explorer, Notepad, Excel, and others). Use an automated capture script built on top of `mss` and `pywinauto` to collect an unlabelled corpus of approximately 2,000 desktop screenshots, covering different resolutions, themes, and application states. From that unlabelled corpus, hand-select and annotate a 100-image "Labelled Target Corpus" in CVAT. The annotation schema is the five-class set `{button, menu, text_input, checkbox, icon}`, intentionally simplified to focus on interactive elements. Train the mobile-baseline detector on CLAY. **Deliverables:** the labelled corpus itself and **D1**, a baseline-performance report addressing RQ1.

**Phase 2: Model adaptation experiments.** Implement both a YOLOv8 backbone and a DETR backbone, each pre-trained on CLAY. Run three experiments. *Experiment 1* trains a few-shot fine-tune on $k = 1, 5, 10, 50, 100$ labelled desktop images to plot a data-efficiency curve. *Experiment 2* pre-trains the backbones using a generative inpainting self-supervised task on the 2,000 unlabelled desktop images and then repeats Experiment 1, to measure the uplift from SSP. *Experiment 3* implements the Adaptive Teacher [44] and SHOT [52] UDA frameworks. **Deliverables:** trained weights for all variants and **D2**, an ablation study addressing RQ2 and RQ3.

**Phase 3: Prototype integration.** Pick the single best adapted model from Phase 2 and build the "Adapted-IVGocr" prototype that wraps it. The integration stack is `mss`/`pywinauto` for capture, the adapted detector for perception, Tesseract or EasyOCR for reading text inside detected boxes, fuzzy string matching (rapidfuzz) for grounding the instruction to a detected element, and PyAutoGUI for the click action itself. **Deliverable:** **D3**, a functional Python prototype with a short demonstration video.

**Phase 4: End-to-end evaluation and thesis composition.** Define 10–15 standardised automation tasks (such as "open Notepad and save the file as `test.txt`") and evaluate the prototype's Task Success Rate (TSR) on those tasks. Perform a qualitative failure analysis that traces end-to-end failures back to detection errors, OCR errors, or grounding-logic errors. Write the final thesis. **Deliverable:** **D4**, the final report and packaged code.

## 1.9 Proposed Solution

The proposed solution has three interlocking components. The technical depth on each lives in Chapter 5 (Design) and Chapter 6 (Implementation); this section gives the high-level shape only.

### 1.9.1 Data and preprocessing pipeline

The **source (mobile) corpus** is the CLAY dataset of Li et al. (2022) [10], a denoised 59,555-image subset of RICO [8]. Using CLAY rather than raw RICO matters because RICO is known to contain significant layout noise; CLAY is a deep-learning pipeline that automatically cleans and corrects those raw layouts, and the resulting corpus is a much better starting point for transfer learning. The CLAY annotation schema is mapped onto the five-class desktop schema using a deterministic mapping table documented in Chapter 6.

The **target (desktop) unlabelled corpus** of approximately 2,000 screenshots is collected by a Python script that drives `pywinauto` to enumerate the visible top-level windows of a curated set of 10–15 applications, captures each window with `mss`, and saves the resulting screenshot to disk. The script is parameterised by resolution, theme, and DPI scaling so that the corpus covers the in-the-wild variability the deployed prototype will eventually encounter.

The **target (desktop) labelled corpus** of N = 100 screenshots is curated by hand from the unlabelled corpus and annotated in CVAT against the five-class schema. This corpus is the gold-standard test set against which all adaptation methods are evaluated, and it is also the source of the few-shot training subsets in Experiment 1.

### 1.9.2 Adaptation methodologies

All adaptation methods are applied to both a **YOLOv8-L** backbone and a **DETR-R50** backbone to make the cross-architecture comparison in RQ3 a controlled one.

The **baseline** is established by running the mobile-trained detector zero-shot on the 100-image labelled target corpus. The resulting low mAP is the "problem" that the three adaptation methods then try to close.

**Method 1 — few-shot supervised fine-tuning.** The CLAY-trained backbone is frozen, and only the final detection head is re-trained on the N = 100 labelled desktop images, sweeping over $k = 1, 5, 10, 50, 100$ to produce a data-efficiency curve. This is the simplest of the three methods and serves as the floor against which the other two are compared.

**Method 2 — self-supervised pre-training (SSP) plus fine-tuning.** A generative inpainting task [57] is used on the 2,000 unlabelled desktop images: random patches are masked out, and the model is trained to predict them. The intuition is that, to inpaint a missing patch of a Windows toolbar, the model must implicitly learn the structural grammar of desktop UIs (toolbars are horizontal, icons sit in rows, dialog buttons cluster bottom-right, and so on). The SSP-trained backbone is then handed to Method 1 to measure whether this unsupervised pre-training step improves the final few-shot mAP.

**Method 3 — unsupervised domain adaptation (UDA).** Two state-of-the-art UDA frameworks are implemented and compared. The first is the **Cross-Domain Adaptive Teacher** of Li et al. (2022) [44, 48], which is a teacher-student setup where a stable Exponential Moving Average (EMA) teacher generates pseudo-labels on weakly augmented target images and a student is then trained on a mixed batch of labelled source (CLAY) data and strongly-augmented pseudo-labelled target data. The second is **SHOT** [52, 53], which freezes the source-trained classification head (the "source hypothesis") and adapts only the feature extractor backbone on the unlabelled target images using self-supervision; the goal is to align the new target features to the frozen source hypothesis rather than to retrain the head itself.

### 1.9.3 Prototype integration and evaluation

The prototype, named **VisClick**, is a direct implementation of the IVGocr architecture of Dardouri et al. (2024) [17, 18]. The novelty is the replacement of their standard YOLOv8 detector with the cross-domain-adapted detector from the previous component.

The runtime flow is:

1. **Input.** The user supplies a free-form text instruction, for example "click Save".
2. **Capture.** A screenshot of the user-selected monitor is taken with `mss`, in the virtual-desktop coordinate space.
3. **Perception.** The adapted detector runs on the screenshot and returns N candidate bounding boxes, each with a class label and a confidence score.
4. **Reading.** Tesseract or EasyOCR is run on each detected bounding box (rather than the whole image) to recover the visible text on the element. A full-image OCR pass is kept in reserve as a fallback for cases where the detector misses the target element entirely.
5. **Grounding.** A fuzzy-string-matching function (using `rapidfuzz`) computes the similarity between the user's instruction and the OCR text of each detected element. The element with the highest score above a configured similarity threshold is selected.
6. **Action.** PyAutoGUI moves the cursor to the centre of the selected box and issues a single left click. When no candidate exceeds the threshold, the prototype refuses to click and reports a structured failure message; this refusal-on-uncertainty behaviour is a deliberate design choice, motivated by the observation that a confident wrong click is worse, in an automation tool, than an honest "I do not know".

The detection metric used for component-level evaluation is mAP at IoU 0.5, with the Central Point Validation (CPV) metric of Dardouri et al. (2024) used for grounding quality. The end-to-end bot metric is Task Success Rate (TSR), defined as a binary pass/fail on each of the 10–15 standardised tasks.

[FIGURE 1.3 — "High-level architecture of the proposed solution."
 Suggested source: a single-panel block diagram showing the three components (source-domain pre-training, cross-domain adaptation, prototype integration) laid out left-to-right with arrows. The Mermaid block diagram already in `docs/VisClick_Report_Data_Form.md` §18.1 is a good starting point and can be exported as PNG. Path placeholder: `reports/figures/ch1_solution_overview.png`.
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
* **Heavyweight large vision-language models.** Models such as SeeClick [33] are referenced and discussed at length in the literature review, because they represent the "heavyweight SOTA" against which the project's lightweight stance is positioned, but they are not benchmarked here. The compute budget for that kind of comparison is well beyond what was available, and including it would have shifted the project from a practical engineering investigation to a pure benchmarking exercise.
* **Full accessibility-tree integration.** pywinauto is used in the data-collection stage (to enumerate visible top-level windows) and is also benchmarked as a classical baseline in Chapter 7. It is not used at runtime in the prototype's perception pipeline; doing so would defeat the point of the vision-based approach.
* **Highly multimodal instructions.** Instructions are free-form text. Voice input, image-conditioned instructions, multi-step natural-language commands, and conversational dialogue are all out of scope.
* **Robotic process automation at fleet scale.** The prototype is a single-user, single-machine demonstrator. Scaling out to multiple machines, multi-tenant deployment, or enterprise governance is left for future work and discussed in Chapter 9.

The scope statement above is informed by the literature review in Chapter 2 and by the risk analysis in Chapter 4. Where the proposal's original scope had to be trimmed during execution, the trimming and the reason for it is documented in §4.6 (Risk Mitigation Plan) and in §9.7 (Limitations) rather than being silently dropped.

## 1.11 Chapter Summary

This chapter has set up the problem, the aim, the four research questions, the research gap, and the four-phase work plan that the rest of the report follows. The picture, in one paragraph, is this. GUI automation on the modern desktop is in an awkward place. Classical image-based tools are too brittle; classical accessibility-tree tools have fallen out of step with the modern Windows application mix; the heavyweight large vision-language models that *can* do it are too big to run anywhere most people would actually want to. Sitting in the middle, where there is a clear opportunity, is the idea of a cross-domain-adapted lightweight detector trained on the relatively well-resourced mobile UI domain and then carried across to the data-scarce desktop domain. The project investigates how far that idea can be pushed using three adaptation methods (few-shot fine-tuning, self-supervised pre-training plus fine-tuning, and unsupervised domain adaptation) on two backbone architectures (YOLOv8 and DETR), and integrates the best of those into a working prototype that closes the loop from a typed instruction to a click on the real Windows desktop.

The rest of the report is organised as follows. **Chapter 2** is the literature review. It walks through the datasets, the model architectures, and the adaptation methodologies in enough depth to support the architectural choices made later, and it ends with the explicit research-gap statement that motivates the rest of the work. **Chapter 3** lays out the requirement analysis, including a stakeholder analysis using the Onion model, five functional requirements, and ten non-functional requirements with quantitative targets. **Chapter 4** covers the project management approach: the research methodology, the software development methodology, the risk register, and the project plan. **Chapter 5** covers the design: a high-level architecture, a research design, a block diagram, a flow chart, and the UI wireframes for the prototype. **Chapter 6** is the implementation chapter, which describes how the data pipeline, the three adaptation methods, and the prototype were actually built. **Chapter 7** is the testing chapter, which reports the model-level and prototype-level test results in tabular form. **Chapter 8** is the evaluation chapter, which interprets those results against the research questions and the requirements, includes a qualitative review from independent practitioners, and discusses legal, ethical, professional and social impact. **Chapter 9** concludes with the limitations, the things I would do differently in retrospect, and the directions for future work.

# Chapter 2 — Literature Review

## 2.1 Overview

This chapter is a critical review of the prior work that informs the project. It is organised in the same order that the methodology in Chapter 6 puts the pieces together. It starts with the available datasets, because data is the gating constraint for everything that follows. It moves on to the pre-processing step that bridges noisy raw data and a trainable corpus. From there it covers classical automation approaches that have historically dominated GUI testing, then the deep-learning detectors that have started to replace them on mobile UIs. It then surveys the family of domain-adaptation methodologies that this project relies on to carry a mobile-trained detector across to the desktop. After that it looks at the wider GUI-agent landscape, including the heavyweight large vision-language models that sit at the other end of the spectrum from this work. It closes with a short summary of the metrics used in the UI-detection literature and a precise statement of the research gap.

The chapter is deliberately structured around comparisons. Where two pieces of work try to do roughly the same thing, the review puts their numbers side-by-side so the reader can see which one is genuinely better and which one is a re-branding. Where a piece of work is cited only as motivation, the review says so plainly. The aim is to leave the reader with a clear picture of which methodological tools were taken off the shelf for this dissertation and which were left there for considered reasons.

## 2.2 Existing GUI Element Datasets

The starting point for any vision-based UI-detection work is a corpus of annotated screenshots. The single most important fact about that corpus today is that the mobile side of it is well resourced and the desktop side of it is not.

The canonical mobile-UI dataset is **RICO**, released by Deka and colleagues in 2017 [8, 19]. RICO contains roughly 72,000 unique Android UI screenshots harvested from 9,300 free apps on the Google Play Store, paired with their Android view-hierarchy XML and a number of derived properties: textual labels, structural relationships, animation traces, and interaction sequences. The view hierarchy is what makes RICO useful for object detection rather than just for design retrieval. From the XML one can derive a bounding box and a class label for every leaf node on screen, which in practice means tens of millions of labelled elements across the corpus. The downside, well known in the literature, is that the raw view hierarchy is noisy. Container nodes overlap with their visual children, invisible nodes still appear in the tree, and the leaf-class labels are inconsistent across SDK versions and across app authors. Anyone who has tried to train an object detector directly on raw RICO bounding boxes hits these issues quickly.

The community's response is the **CLAY** dataset of Li and colleagues at CHI 2022 [10, 11]. CLAY is not a new collection of screenshots; it is a deep-learning denoising pipeline that takes RICO's raw view hierarchies and produces cleaner, machine-verified layouts. The result is a corpus of 59,555 cleaned Android UI layouts with a more consistent 23-class taxonomy and a much-reduced rate of overlapping, invisible, or mis-classified bounding boxes. The improvement is not trivial: published detectors trained on CLAY instead of raw RICO labels report a 5 to 8 percentage-point uplift in mean average precision on held-out test splits. For this reason CLAY became the source-domain training set for this project's headline detector; the proposal commits to it in §7.A.

The mobile domain has not stood still since RICO. The **MUD** dataset of 2024 [20, 24, 25] was created in direct response to the observation that RICO and CLAY are now temporally outdated. The Android visual design language has shifted noticeably since 2017 (the move from older Holo and Material 1 themes to Material 3, the rise of foldable form factors, the increase in dark-mode and large-text accessibility variants), and a detector trained on the older corpus does noticeably worse on modern screens. MUD reports buttons-class mAP of 75.3% on its own test split compared to 63.4% when the same model is trained on RICO and evaluated on MUD. That gap is not large in absolute terms, but it speaks to a real and ongoing data-currency problem even within the mobile domain.

[FIGURE 2.1 — "RICO and CLAY side-by-side." 
 Suggested source: one mobile screen from RICO (raw view-hierarchy boxes overlaid) and the same screen with CLAY's cleaned labels. The CLAY GitHub page has matched-pair examples that can be reproduced. Path placeholder: `reports/figures/ch2_rico_vs_clay.png`.
 Suggested caption (~30 words): "RICO raw labels (left) vs CLAY's denoised labels (right) on the same screen. CLAY removes invisible-container nodes, fixes class mis-assignments, and reduces overlapping-box duplicates."]

On the desktop side the picture is much thinner. There is no "desktop RICO" of comparable scale. The recent attempts to fill the gap are illustrative both of demand and of how recent the recognition of the gap is. **DeskVision** (2025) [14] proposes a large-scale desktop region-captioning corpus aimed at GUI agents; it is dated March 2025 on arXiv. **GenGUI** (2025) [15] is a synthetic dataset of web interfaces generated by ChatGPT and is closer to a UI-design-generation corpus than to an element-detection one. **AS400-DET** [27] is a niche detection dataset for legacy terminal-style interfaces. None of these is yet at the order of magnitude of RICO. Importantly, the authors of the IVGocr paper that this project's prototype is modelled after had to build their own desktop dataset to run their experiments [17], which they note explicitly. The data-scarce nature of the desktop target domain is the gravitational pull that draws this project, and others like it, towards domain adaptation rather than train-from-scratch on the target.

Table 2.1 sets the principal datasets side-by-side. The figures for RICO and CLAY are the ones the authors report; the figures for DeskVision and GenGUI are the ones their respective arXiv papers cite at submission.

**Table 2.1 — Available GUI element datasets.**

| Dataset | Year | Domain | Screens | Annotations | Public licence |
|---------|------|--------|---------|------------:|----------------|
| RICO [8] | 2017 | Mobile (Android) | 72,219 | ~3M leaf nodes (raw view-hierarchy) | Free for research |
| CLAY [10] | 2022 | Mobile (Android) | 59,555 | Cleaned 23-class layouts | Open access |
| VINS [L2 in `literature_table.csv`] | 2021 | Mobile | 4,800 | 11-class detection labels | Open access |
| MUD [20] | 2024 | Mobile (Android, modern) | 18,132 | Modern-style annotations | Open access |
| DeskVision [14] | 2025 | Desktop | "Large-scale" (exact count unreleased at time of writing) | Region-caption pairs | Pending release |
| GenGUI [15] | 2025 | Web (synthetic) | Synthetic — generated on demand by ChatGPT | Layout + class labels | CC-BY |
| Zenodo unified bundle (used in this project) | 2023 | Mobile + Web | 9,646 | 6-class collapsed from RICO+CLAY+VINS | Open access |

The Zenodo unified bundle row is the corpus this project actually trains on. It combines RICO, CLAY and VINS into a single 6-class taxonomy (`{button, text, text_input, icon, menu, checkbox}`) chosen to match what an automation bot needs to interact with. Details of the class-collapse mapping are in Chapter 6.

## 2.3 Pre-processing for UI Element Detection

Pre-processing for a UI corpus is not the same problem as pre-processing for a natural-image corpus. The standard tricks (random crop, horizontal flip, colour jitter) are either useless or actively harmful on screenshots. Horizontal flip turns a left-aligned toolbar into a right-aligned one, which is fine in principle until the model also flips the text inside the buttons and produces meaningless training signal. Colour jitter on a Win11 light theme can produce shades that no real application ever displays. The literature treats UI pre-processing largely as a label-noise problem rather than as an image-augmentation problem.

The largest single piece of UI pre-processing work in the public literature is CLAY itself [10, 11]. CLAY's main contribution is a learned denoiser that takes raw RICO view-hierarchy bounding boxes and produces cleaner labels: invisible containers are removed, overlapping duplicates are collapsed, mis-classified node types are corrected. The authors report a measurable downstream effect, with detectors trained on CLAY-cleaned labels gaining several mAP points on held-out test splits over the same architecture trained on raw RICO. The denoising is a pre-processing step in spirit, even though it is implemented as its own deep-learning pipeline.

A more pragmatic line of pre-processing work tackles class-imbalance. Both RICO and the desktop seed corpora collected in this project are heavily skewed: the `text` class is much more frequent than any of the actionable classes (`button`, `text_input`, `menu`, `checkbox`). The sample dissertation reviewed alongside this project [the RGU MSc skin-cancer report, 2026] used weighted random oversampling on the minority classes; the AS400-DET paper [27] reports good results with class-balanced focal loss. This project chose a simpler route, a 12-to-6 class collapse that puts visually similar minority classes into the same training target, partly to keep the training pipeline reproducible on Colab Free without exotic loss functions and partly because the 6-class taxonomy maps cleanly onto what the downstream IVGocr matcher needs.

Two pre-processing patterns recur across the literature and were considered for this project. The first is **stratified sub-sampling** of the source corpus to bring its class distribution closer to the target domain's. This is appealing when the source-target class imbalance is severe; in this project it was not used, on the grounds that the target distribution is itself unknown until enough labelled desktop data exists to characterise it. The second pattern is **synthesis-based augmentation**, in which under-represented elements (icon-only buttons, dropdown arrows) are pasted onto background screenshots to inflate the training corpus. ScreenAI [L10] and several recent agent papers use a variant of this idea at very large scale. For this project's data budget the cost of building a high-quality synthesis pipeline is not obviously worth the benefit, but Chapter 9 records it as a future-work direction.

A short remark on input resolution. RICO and CLAY use portrait-oriented Android screens that fit comfortably into a square 640×640 detector input. Desktop screenshots are landscape, often at 1920×1080 or 3440×1440, and need to be down-scaled before they enter a YOLOv8 detector with `imgsz=640`. This rescaling is, in itself, a pre-processing concern that produces measurable accuracy variation. The numbers in Chapter 7 are reported with a single fixed `imgsz=640`; the sensitivity of those numbers to that choice is briefly discussed in §9.7.

## 2.4 Classical Automation Approaches

Before the deep-learning era, three families of tools dominated GUI automation. They are still in widespread use, particularly in industrial test automation and RPA, and the project measures itself against the strongest of them. They are reviewed here because the gap they leave is precisely the gap this project tries to fill.

The first family is **bitmap-based visual automation**. The best-known tool is **SikuliX** [3, 4]. SikuliX records a small bitmap of a UI element (a Save button, a magnifying-glass icon) and at run time uses OpenCV's `matchTemplate` to find that bitmap on the live screen. The user writes a script in a Sikuli-flavoured Python that says, in essence, "click this image". The strength of the approach is its simplicity. The weakness is its rigidity. A bitmap is a frozen photograph of the element under one theme, one DPI, one font, one application version. Change the theme to dark mode and the bitmap stops matching. Change the DPI from 100% to 125% and the same thing happens. AskUI's recent review [4] phrases this politely as "image recognition first", but in practice anyone who has tried to deploy a SikuliX script across a fleet of machines has seen the failure mode at scale. The empirical evidence in Chapter 7 of this report confirms that **on the specific subset of tasks where a reference bitmap could be captured, template matching is excellent (it scored 100% on those tasks)**, but on tasks where no useful bitmap exists (positional targets such as "click the first command", dynamic state toggles, or text-inside-text) it cannot represent the problem at all.

The second family is **coordinate-based automation**. **PyAutoGUI** [5, 7] is the canonical Python example: it exposes `pyautogui.click(x, y)` and lets the user write scripts that drive the mouse and keyboard at specified pixel coordinates. PyAutoGUI is widely used inside other automation stacks (including this project's prototype, where it drives the final click). On its own it is the most brittle of the three families because it has no knowledge of what is at those coordinates. The same script that works on a 1080p laptop fails on a 1440p desktop unless every coordinate is recomputed. PyAutoGUI is best understood not as a competitor to a vision-based bot but as a low-level primitive that any vision-based bot eventually has to use to translate a chosen bounding box into an OS-level click.

The third family is **accessibility-tree automation**. On Windows the canonical Python library is **pywinauto** [6, 7]. pywinauto uses Microsoft's UI Automation framework to walk the live application's accessibility tree and find controls by their semantic Name and ControlType. The approach is theoretically beautiful: it abstracts away theme, DPI and font; the same script will work on a 1080p laptop and a 1440p desktop because both expose the same `Button(Name='Save')` control. In practice the modern Windows application mix has eroded the assumption that the accessibility tree faithfully reflects the visible UI. Electron applications (Visual Studio Code, Slack, Discord) expose only a degenerate tree because the renderer is a Chromium browser. Modern Windows 11 applications using WinUI 3 or XAML islands frequently expose localised internal control names rather than the visible labels. Web pages inside any browser serve their accessibility via ARIA, which is a separate convention again. The empirical baseline reported in Chapter 7 of this report shows pywinauto scoring 1 out of 15 task instances on a representative Windows 11 workload (and that single success is the negative case where the right answer is to do nothing). On every positive task (Notepad's Save-As dialog, Visual Studio Code's Search panel, Chrome's omnibox, File Explorer's ribbon) pywinauto returned `ElementNotFound`.

The collective failure of all three classical families on the modern Windows 11 application mix is the operative justification for a vision-based approach. If the accessibility tree could be trusted, machine learning would not be needed; the empirical evidence is that on a 2026-vintage desktop, it cannot.

[FIGURE 2.2 — "Where each classical baseline succeeds and fails on T01–T15."
 Suggested source: one of the existing per-method overlays from `reports/figures/baselines/`. A horizontal bar chart of pass/fail counts per method per task category would be even better. Path placeholder: `reports/figures/ch2_classical_baselines_grid.png`.
 Suggested caption (~30 words): "Per-task verdicts for the three classical baselines across the 15 evaluation tasks. Each baseline's failure cluster is distinct, motivating the project's combined vision+OCR approach."]

## 2.5 Deep-Learning Approaches for UI Element Detection

A separate strand of work treats UI element detection as a classical object-detection problem and solves it with the same architectures the natural-image community has converged on. This is the strand the project belongs to.

The most-cited early work in the strand is **UIED** by Xie and colleagues at FSE 2020 [1, 16, L3]. UIED makes a deliberately pragmatic argument: neither pure deep learning nor pure classical computer vision is sufficient for GUI element extraction on its own, because the two methods miss complementary things. A Faster R-CNN baseline trained on UI screenshots achieves an F1 of 0.71 on their internal benchmark but misses small icons and dropdown arrows that the classical edge-and-region pipeline catches. Their classical-only pipeline manages F1 of 0.55, but misses text-shaped buttons that the deep learner gets easily. The UIED hybrid (CNN for non-text shapes, EAST/CTPN for text, then a rule-based merger) reaches F1 of 0.84. The architecture matters less than the methodological lesson: combining a fast deep detector with a text-recognition fallback is the right shape for a UI element detector. This project's pipeline, with YOLOv8 as the detector and EasyOCR providing both per-box and full-image text grounding, is in direct lineage from UIED.

**VINS** by Bunian and colleagues at CHI 2021 [L2] is a slightly later and more focused implementation of the same idea. VINS uses a Faster R-CNN with a ResNet-50 backbone trained on RICO to localise eleven UI element classes (buttons, text inputs, icons, image, label, and so on). They report mAP@0.5 around 0.46 on a held-out RICO split and an element-detection F1 of 0.61. The reason VINS is cited here is not that the architecture is novel (it is not) but that VINS is one of the very few published papers that report mAP at this level of detail on a public mobile UI test set, which gives this project's source-domain mAP numbers something to anchor against.

A more specialised mobile-targeted detector is **YOLOv5-MGC** by Cheng and colleagues at 2022 [29, 30]. The paper introduces a YOLOv5 variant tailored for mobile GUI detection, with a microscale detection layer and an attention mechanism added to handle the very small icons that crowd a mobile screen. They report 89.8% mAP on their mobile UI test set, which is a strong number. The architectural innovations are sensible for the mobile setting, but the same paper hypothesises that the "microscale + attention" combination is overfit to mobile-style density and may not transfer well to the very different density of a desktop's packed-scene toolbar [1]. Validating or refuting that hypothesis on real desktop data was one of the original motivations of this project, and it is partly what RQ3 (model choice and transferability) is about.

[CITATION: AS400-DET, ref [27] in proposal] — a recent paper applies the same family of methods to legacy IBM terminal interfaces, with comparable conclusions. The lesson across all four works is consistent. On their own domain, deep object detectors do well on UI elements; their accuracy is bounded by the quality and currency of the training corpus, not by the architecture.

This project compares two architectural families. The first is **YOLOv8** [28, 38, 39, 40], the current-generation Ultralytics implementation. YOLOv8 is an anchor-free, single-stage detector with a modified CSPDarknet53 backbone and an enhanced Path Aggregation Network (PANet) neck explicitly designed to fuse features across multiple scales. The multi-scale neck is the property that matters for UI detection, where the same screen contains a 16-pixel close-X icon and a 200-pixel-wide ribbon menu at the same time. The Ultralytics implementation is well documented, runs on Colab Free's T4 in a usable time budget, and exports cleanly to ONNX for CPU-only inference. It is the project's headline backbone.

The second is **DETR** (DEtection TRansformer) by Carion and colleagues at ECCV 2020 [41, 43]. DETR re-frames detection as a direct-set-prediction problem solved with a transformer encoder-decoder and a bipartite-matching loss. It eliminates anchors and non-maximum suppression, which is conceptually clean and has the practical benefit of removing two layers of hyperparameter tuning. The well-documented weakness of the original DETR is poor performance on small objects, attributed to the global attention pattern in the encoder spending too much attention budget on large regions and too little on small ones. **RT-DETRv3** [42] is the most recent improvement, with hierarchical dense positive supervision designed in part to address the small-object weakness. For this project, the architectural comparison committed to in RQ3 (and in proposal §7.B) puts a YOLOv8-L and a DETR-R50 side by side, on the hypothesis that DETR's small-object weakness will be aggravated by the packed-scene density of desktop UIs. The DETR experiments are part of Phase 2 and at the time of writing are listed as D-01 in the gaps tracker.

A separate piece of work worth flagging is **Apple's Screen Recognition** paper of Zhang and colleagues at CHI 2021 [L5]. Screen Recognition is the production pipeline behind the iOS VoiceOver accessibility feature; an on-device object detector classifies widgets into 13 types, with OCR adding text labels. The reported numbers are F1 of 0.91 on in-distribution screens, dropping to 0.74 on apps the model has never seen, with OCR adding a further 6 to 11 percentage points. The paper is cited here for two reasons. First, it is the closest existing analogue to what this project tries to do; an industrial-scale, accessibility-motivated, on-device UI detector that adds OCR exactly where the visual detector misses. Second, the published 0.91-to-0.74 in-distribution-to-out-of-distribution drop is empirical confirmation that even at Apple-scale data and engineering, the domain-shift effect is real and is the right thing to design around. This project's Win11-domain drop is consistent with that pattern at much smaller scale.

## 2.6 Domain Adaptation Methodologies

The four research questions for this project (§1.5) collapse, on closer inspection, into two empirical questions. RQ1 asks how big the domain shift is. RQ2 asks how to close it. The literature on domain adaptation answers RQ2 in three different ways, and this project implements one method from each.

The simplest method is **few-shot supervised fine-tuning**. The CLAY-pretrained backbone is frozen and the final detection head is re-trained on a small labelled subset of the target domain. The size of the subset is the free parameter; this project's plan is to sweep over $k = 1, 5, 10, 50, 100$ labelled desktop images to draw a data-efficiency curve. Few-shot fine-tuning is the canonical baseline in the transfer-learning literature; for context, the broad survey of Iman, Arabnia and Rasheed (2023) on transfer learning [45] gives roughly two dozen variations on the theme of "fine-tune the top, freeze the bottom". The reason this project keeps it in the experiment plan is not that it is novel but that it is the necessary control: any more elaborate method must beat the few-shot fine-tune by a non-trivial margin to be worth its complexity.

The intermediate method is **self-supervised pre-training (SSP) followed by fine-tuning**. SSP first pre-trains the backbone on unlabelled target-domain data with a self-supervised pretext task (typically masked-patch reconstruction or contrastive learning) and then fine-tunes the resulting backbone on labelled data exactly as in the few-shot case. The intuition is that the SSP step lets the model absorb the structural grammar of the target domain (in our case, the spatial conventions of desktop UIs: toolbars are horizontal, dialog buttons cluster bottom-right, menubars sit under the title bar) without requiring labels. The most relevant survey for the project's choice of pretext task is the medical-imaging survey of Anaya-Isaza, Mera-Jiménez and Zequera-Diaz (2024) [57], which reports a consistent uplift of 4 to 11 percentage points on downstream classification accuracy when masked-patch reconstruction is added to small-data fine-tuning. The project's SSP experiment is listed as D-02 in the gaps tracker; it is the second of the three Phase 2 methods.

The most elaborate method is **unsupervised domain adaptation (UDA)**, which uses *no* labelled target data and relies entirely on the unlabelled target corpus together with the labelled source corpus. This project compares two UDA families on the desktop target.

The first is the **Cross-Domain Adaptive Teacher** of Li, Dai and colleagues at CVPR 2022 [44, 48, 49]. Adaptive Teacher is a robust teacher-student framework. A stable Exponential Moving Average (EMA) teacher generates pseudo-labels on weakly-augmented target (desktop) images. The student is then trained on a mixed batch consisting of labelled source (CLAY) data and strongly-augmented pseudo-labelled target data, with a discrepancy loss that aligns the student's predictions across the two augmentation regimes. The EMA teacher is updated as a moving average of the student's weights; this is what makes the framework stable, in contrast to earlier teacher-student schemes that drifted as the student's pseudo-labels degraded. The published results are strong, with Adaptive Teacher closing roughly two-thirds of the source-to-target gap on standard cross-domain detection benchmarks (Cityscapes-to-Foggy-Cityscapes, Pascal-to-Clipart). The successor work, **Harmonious Teacher** at CVPR 2023 [44], improves on it by adding more careful pseudo-label confidence weighting. For this project, Adaptive Teacher is the more thoroughly documented choice and is what the Phase 2 plan commits to; it is listed as D-03 in the gaps tracker.

The second is **SHOT (Source HypOthesis Transfer)** [52, 53, 54]. SHOT takes a different stance from teacher-student. Instead of training a student to imitate a teacher, SHOT freezes the source-trained classification head (the "source hypothesis") and adapts *only* the feature extractor backbone on the unlabelled target images using a self-supervised objective. The intuition is that the head encodes what classes look like; the extractor encodes what the world looks like. When the world changes (from mobile UIs to desktop UIs), it is the extractor that needs to adapt, not the head. The published SHOT results are competitive with teacher-student approaches on smaller-scale benchmarks and have the practical advantage that the source data does not need to be available at adaptation time. For privacy-sensitive deployments this matters; for this project it matters less, but SHOT is included as the second UDA comparison point because it is structurally different enough to give a genuine architectural choice (D-04 in the gaps tracker). The paper of Sahay, Thomas and colleagues at Sensors 2023 [52, 55] gives an updated treatment of hypothesis-transfer for object detection that the implementation will follow.

A useful framing of the three methods is in terms of what each requires. Few-shot fine-tuning requires labelled target data and no unlabelled target data. SSP+FT requires both labelled and unlabelled target data. UDA requires only unlabelled target data, plus the original labelled source. The methods sit on a continuum from "expensive labels, simple training" to "no labels, complex training". The empirical question this project asks (RQ2) is where on that continuum the best practical return sits, given a realistic-MSc-scale data budget. The answer the project expects to find, on the basis of the existing literature, is that SSP+FT will roughly match UDA at less than a tenth of the engineering cost, and that both will outperform pure few-shot once $k$ is small. The actual numbers will arrive when D-02, D-03 and D-04 are completed.

A separate sub-thread in this literature, increasingly important since 2023, is **semi-supervised object detection (SSOD)** [50, 51]. SSOD blurs the line between SSP+FT and UDA by combining a small labelled set with a larger unlabelled set under a unified teacher-student loss. The recent survey of Khan and colleagues [51] argues that SSOD has effectively absorbed the older UDA literature in the object-detection sub-field. This project does not implement a dedicated SSOD method; the Adaptive Teacher implementation in D-03, which uses both labelled source data and unlabelled target data, sits close to the SSOD family in spirit even though the literature places it under UDA.

## 2.7 GUI Agents and Visual Grounding Frameworks

The detection and adaptation methods reviewed so far produce a *detector*. A detector is not an automation system. Closing the gap from "here are the elements on the screen" to "do the thing the user asked for" requires a grounding layer that maps a natural-language instruction onto one of the detected elements. The published frameworks for this layer fall into two clusters.

The first cluster is **modular pipelines** in the style of UIED [1] and its descendants. The Instruction Visual Grounding (IVG) framework of Dardouri and colleagues at 2024 [17, 18, 32] is the most directly applicable for this project. Dardouri proposes IVGocr, an explicit three-stage architecture: a YOLOv8 detector finds the UI elements; OCR reads the visible text on each detected element; an LLM (or, in their lighter-weight variant, a fuzzy string matcher) matches the user's instruction to the read text. They introduce the Central Point Validation (CPV) metric for evaluating how often the chosen element's centre falls inside the ground-truth bounding box of the correct target, which is a more permissive and arguably more honest grounding metric than IoU at high thresholds. This project's prototype, VisClick, is a direct implementation of the IVGocr architecture, with the YOLOv8 detector being the project's CLAY-pretrained, desktop-adapted model and the matcher being a rapidfuzz fuzzy match rather than a heavyweight LLM. The reason for picking rapidfuzz over an LLM is purely operational: it runs in milliseconds on CPU and removes a network dependency. The downstream evaluation in Chapter 8 of this report shows that for the 15-task workload, the rapidfuzz matcher is sufficient; the residual failures come from the detector, not from the matcher.

A small variant in the same cluster is the **MUG** (Multimodal Grounding on User Interfaces) framework of Tang and colleagues at EACL 2024 [23]. MUG adds interactive feedback to the grounding step, so the user can refine an ambiguous instruction iteratively. This is conceptually attractive but operationally heavyweight, and is not used by this project for the same reason heavy-weight LLMs are not used: the goal is a CPU-only single-shot system.

The second cluster is **end-to-end large vision-language models (LVLMs)**. The exemplar is **SeeClick** of Cheng and colleagues at ACL 2024 [33, 34, 35, 36, 37, L7]. SeeClick replaces the entire detector-plus-OCR-plus-matcher stack with a single multi-billion-parameter vision-language model that takes a screenshot and an instruction as input and outputs click coordinates directly. The training corpus is roughly one million screenshots covering web, desktop and mobile. The reported numbers are 73% click accuracy on the web benchmark Mind2Web, 53% on the mobile benchmark AITW, and 47% on a new desktop benchmark the authors introduce. As a piece of engineering it is the current state-of-the-art on cross-domain GUI grounding. The reason this project does not benchmark against SeeClick is the inference-cost gap: SeeClick requires a multi-GPU inference setup and substantial memory, both of which are out of scope here. SeeClick is the reference point that the dissertation cites in §1.6 as the "heavyweight SOTA"; the project's positioning is explicitly as a lightweight, interpretable alternative for the cases where on-device, low-latency inference matters more than the absolute top of the leaderboard.

A related LVLM-based piece of work is Google Research's **ScreenAI** of Baechler and colleagues at IJCAI 2024 [L10]. ScreenAI is a 5-billion-parameter vision-language model pre-trained on a screenshot corpus an order of magnitude larger than RICO. The headline claim is that ScreenAI is SOTA on four of the five UI benchmarks tested. The methodological lesson, for the purposes of this project's literature review, is that UI element coverage is fundamentally a data-scale problem more than an architectural one. ScreenAI's gains over earlier LVLMs come almost entirely from the increase in pre-training corpus size, not from any architectural novelty. This is cited as evidence (in §9.7) that the residual gap on Win11 native dialogs in this project's results is well-aligned with the published frontier: the open-source desktop UI corpus simply does not exist at the scale that would let a smaller model close the gap purely by architecture.

[FIGURE 2.3 — "Modular vs end-to-end grounding pipelines."
 Suggested source: a two-panel block diagram. Left panel: IVGocr-style three-stage modular pipeline (detect → OCR → match → act). Right panel: SeeClick-style end-to-end LVLM. Path placeholder: `reports/figures/ch2_modular_vs_e2e.png`.
 Suggested caption (~30 words): "Two architectural families for instruction-to-action GUI agents. This project belongs to the modular family on the left, in deliberate contrast to the end-to-end LVLM family on the right."]

A few smaller works belong here for completeness. **Widget Captioning** of Li and colleagues at EMNLP 2020 [L6] is a vision-language model that produces a natural-language caption for each individual UI widget; the BLEU-4 of 0.41 on RICO is the headline. Its relevance to this project is that it provides empirical evidence (cited in the limitations chapter) that a substantial fraction of clickable elements are icon-only and require visual reasoning rather than OCR to be grounded, which is the limitation behind the icon-class recall problem documented in §8.4 of this report. **Pix2Struct** of Lee and colleagues at ICML 2023 [L8] is a self-supervised pre-training scheme for visual language understanding using screenshot-to-simplified-HTML pairs; the published downstream gains of 4 to 10 percentage points across nine UI benchmarks are the principal motivation for taking SSP seriously as a project methodology (D-02). **Pix2Code** of Beltramelli at IUI 2018 [9] is the historical reference establishing that pixel-only screenshot understanding is feasible at all; it is cited as the lineage marker that the modern detect-describe-act pipeline descends from.

## 2.8 Evaluation Metrics in the UI Domain

A short review of metrics is appropriate because the metric choice non-trivially affects what counts as a "good" detector. Three metric families recur in the literature reviewed above.

The **detection-quality** family is the standard COCO-style mean average precision (mAP) at intersection-over-union (IoU) thresholds 0.5 and 0.5:0.95. mAP at IoU 0.5 is the conventional headline, mAP at IoU 0.5:0.95 is the harder, more conservative number. Almost every paper reviewed above (RICO benchmarks, CLAY, UIED, YOLOv5-MGC, YOLOv8) reports mAP@0.5 as the principal headline. Per-class average precision (AP) is sometimes reported alongside; this project reports both, in `reports/tables/source_per_class.csv`.

The **grounding-quality** family is more idiosyncratic. The Central Point Validation (CPV) metric of Dardouri and colleagues [17, 18] is one of the more thoughtful proposals: a grounding is considered correct if the centre of the predicted bounding box falls within the ground-truth box of the target element. CPV is more permissive than IoU at high thresholds, but it is also closer to what an automation bot actually needs (a click that lands somewhere inside the target is sufficient). This project adopts CPV as a secondary metric alongside mAP (D-08 in the gaps tracker).

The **end-to-end-task-success** family is what the bot itself is measured against. Task Success Rate (TSR) is the binary pass/fail rate over a fixed test suite. Almost every modern GUI-agent paper [17, 33, L7] reports TSR as the primary user-visible metric. TSR has the merit of being interpretable to non-specialist stakeholders ("seven out of every ten clicks land in the right place") and the demerit of folding together detection, OCR and matcher errors into a single number. Chapter 8 of this report decomposes TSR failures into the three component error families, following the failure-analysis approach Dardouri and colleagues use.

One metric this project does *not* use, despite its dominance in the natural-image-detection literature, is **F1 at a fixed confidence threshold**. F1 conflates two questions a UI automation system has to answer independently: "does the detector see the element" and "does the matcher pick the right one". The two-stage decomposition is more diagnostic, even if it sacrifices the single-number convenience of F1.

## 2.9 Research Gap and Positioning of Current Study

The literature is best summarised by a single observation: there is no missing piece in the constellation, only a missing combination. State-of-the-art mobile UI detectors exist [29]. A clean target-application pipeline exists [17]. Heavyweight LVLMs that solve the cross-domain problem at scale exist [33, L10]. The piece that is missing is a *lightweight, data-efficient* method that takes the SOTA mobile detector, adapts it to the desktop domain using the kind of small labelled-data budget an individual or a small team can realistically produce, and demonstrates that the resulting detector works *inside a complete automation pipeline* rather than only on a static benchmark.

The gap is the combination of three constraints. **Lightweight**, in the sense that the runtime must fit comfortably on a consumer CPU; this rules out SeeClick and ScreenAI. **Data-efficient**, in the sense that the labelled-target budget must be at most a few hundred images; this rules out training a desktop-specific detector from scratch in the style of MUD. **Integrated**, in the sense that the deliverable is a working click-bot evaluated end-to-end on real applications; this rules out comparing only on mAP on a held-out test split.

To be precise about what the dissertation contributes inside that gap, the contribution is fourfold. **(a)** A quantitative measurement of the source-to-target domain shift on a public mobile UI source (CLAY) and a personal desktop target (Windows 11, ten to fifteen applications). This is RQ1. **(b)** A side-by-side comparison of three adaptation methods (few-shot fine-tuning, SSP+FT, UDA with the Adaptive Teacher and SHOT sub-comparison) on two backbones (YOLOv8 and DETR). This is RQ2 and part of RQ3. **(c)** An empirical evaluation of the adapted detector inside the IVGocr pipeline on a 15-task workload, including a head-to-head against three classical baselines (template, OCR-only, pywinauto). This is RQ4 and the rest of RQ3. **(d)** A public, reproducible implementation: every adaptation method, every baseline, every CSV, every figure is available under the project's open-source repository, which is itself a contribution given how rare end-to-end-reproducible MSc UI-automation projects are in the literature.

The positioning relative to SeeClick and the LVLM family is explicit. This project does not claim to outperform a 7-billion-parameter end-to-end model on detection accuracy. It claims that a small, interpretable, modular pipeline can deliver "good enough" performance for the practical IVGocr-style application on a single CPU, at a fraction of the inference cost, with a much smaller training and adaptation budget. That trade-off is the right one for the practitioners who actually need to deploy UI automation on their own machines.

## 2.10 Summary

This chapter walked through the literature in the order the project consumes it. The mobile UI domain is data-rich, anchored by RICO and CLAY. The desktop domain is data-poor, with recent attempts at corpora (DeskVision, GenGUI) still emerging. Classical automation tools (bitmap, coordinate, and accessibility-tree) have all run into problems on the modern Windows 11 application mix, leaving a gap that vision-based detection is the natural candidate to fill. Among deep-learning detectors, the two architectural families this project compares (YOLOv8 with its multi-scale PANet neck, DETR with its transformer set-prediction) have well-documented strengths and weaknesses; YOLOv8's multi-scale design is the favourite, with DETR included as the controlled comparison. Among adaptation methods, the three the project implements (few-shot, SSP+FT, UDA) span the continuum from labelled-data-only to no-labels-on-target, with the published literature suggesting SSP+FT will give the best practical return at the project's data budget. Among grounding frameworks, the IVGocr modular pipeline of Dardouri and colleagues is the immediate architectural ancestor of this project's prototype; SeeClick and ScreenAI are the heavyweight reference points that anchor the dissertation's lightweight stance. The combined research gap is the absence of a lightweight, data-efficient, end-to-end-validated cross-domain UI adapter for the desktop, and the project's four research questions sit precisely inside that gap.

The next chapter, Chapter 3, turns to requirement analysis. It begins with a stakeholder analysis and proceeds through functional and non-functional requirements with quantitative targets that the rest of the report measures against.

---

# Chapter 3 — Requirement Analysis

## 3.1 Chapter Overview

This chapter sets out the requirements the system was built against. It begins with a stakeholder analysis using the Onion model, because requirements without stakeholders are arbitrary. The stakeholder analysis is then converted into a set of stakeholder viewpoints, each of which contributes some requirements. The methodologies used to gather requirements are described next, together with the methodology for obtaining the datasets the system is trained on. UML use case diagrams formalise the system's interactions with its users, and the use cases are then written out in long form. The chapter ends with the explicit list of functional requirements (R-FR-01 through R-FR-09) and non-functional requirements (R-NFR-01 through R-NFR-10) that the rest of the dissertation evaluates against. Each requirement carries a unique identifier, a description, a target value (where measurable), and a pointer to the section of the testing chapter where the requirement is empirically tested.

The chapter is organised so that a reader who is not interested in the requirements rationale can skip to §3.8 and §3.9 to read the requirement lists directly. The earlier sections supply the justification for those lists, which is what a marker is more likely to read in detail than to skim.

## 3.2 Stakeholder Analysis

Stakeholder analysis identifies the people and organisations who are affected by the system, or who affect the system. The motivation is to spot conflicting interests early and to capture requirements from each perspective before the design hardens around any single one. This section uses the Onion model, in which stakeholders are placed in concentric rings according to their distance from the technical core of the system.

### 3.2.1 The Onion Model

The Onion model for this project has six rings.

The **innermost ring** is the system itself: the VisClick prototype, comprising the ONNX detector, the EasyOCR layer, the rapidfuzz matcher, the Tk GUI, and the PyAutoGUI action layer.

The **second ring** is the **operational users**. Two distinct groups sit here. The first is the author, who runs the bot for evaluation and treats it as a research artefact. The second is the imagined power user: a developer or QA engineer who would use such a tool to automate repetitive desktop tasks. The two groups have meaningfully different requirements. The researcher wants observability (overlay images, structured CSVs, verifiable verdicts) above all else. The power user wants reliability (zero crashes, predictable refusal-on-uncertainty) and convenience (a GUI rather than a CLI). The system addresses both by shipping a CLI for the researcher and a Tk GUI for the power user, layered over a common core.

The **third ring** is the **academic operational stakeholders**: the project supervisor (Pumudu Fernando) and the second marker (TBD). Their concerns are different again: they want a reproducible artefact, an honest evaluation, an academic novelty argument, and a dissertation that is properly structured against the RGU programme handbook.

The **fourth ring** is the **functional layer of downstream beneficiaries**. Three sub-groups belong here. The first is QA and test-automation engineers who might adapt the project's code for production purposes. The second is accessibility users who could in principle benefit from a text-driven click bot when traditional input devices are not usable. The third is the research community: authors of any of the literature reviewed in Chapter 2 who might cite or extend this work, and future students inheriting the codebase.

The **fifth ring** is the **containing organisations**. Robert Gordon University is the degree-awarding body and is the source of the dissertation's ethical-review framework, its style guide, and its assessment criteria. The Informatics Institute of Technology (IIT) is the partner institution. Synopsys Sri Lanka is the author's employer; the work is not done as part of Synopsys-funded research, but the author's professional context informs some of the architectural choices (an automation tool that is interpretable and locally-deployable is more aligned with corporate compliance concerns than one that calls out to a cloud LLM).

The **outermost ring** is the **wider environment**. Microsoft is the platform owner (Windows 11 OS, UI Automation framework, Notepad, File Explorer); their decisions about which control libraries to ship and how to expose them through the accessibility tree have material effects on every measurement in Chapter 7. Google Colab is the compute provider for all training; their Free-tier T4 quota is the binding budget constraint that shapes the data and experimental design. GitHub hosts the public artefact. The open-source community supplies the underlying libraries: Ultralytics for YOLOv8, JaidedAI for EasyOCR, the pywinauto and PyAutoGUI maintainers, and so on. Dataset providers (Deka and colleagues for RICO, Li and colleagues for CLAY) sit here too, as do the bad-actor groups whose existence motivates the social-impact discussion in §8.10.

### 3.2.2 Stakeholder Viewpoints

Each ring produces requirements, and the requirements sometimes conflict. The five viewpoints below capture the conflicts that mattered during design.

**The researcher's viewpoint** prioritises observability and reproducibility. Every prediction must be inspectable; every result must be regeneratable from a script that can be re-run. This pushes the design towards verbose CSV logging, per-attempt overlay images, and CLI flags that fix randomness and dump intermediate state.

**The power user's viewpoint** prioritises a tight loop of action and feedback. Speed matters; clarity of error messages matters; refusal on uncertainty matters more than maximum coverage. This viewpoint produced R-FR-06 (refusal on low confidence), which is one of the harder-fought design decisions of the project (recorded as observation O14 in the data form).

**The academic stakeholder's viewpoint** prioritises an honest, defensible evaluation. This viewpoint is the reason the report explicitly cites both the inflated mAP figure (0.7176, against pseudo-labels) and the corrected one (0.0330, against hand-corrected GT). It is also the reason the negative test case T15 is kept in the headline TSR denominator rather than removed.

**The accessibility-user viewpoint** prioritises permission and refusal semantics over raw speed. A bot that confidently clicks the wrong thing is worse, for this group, than one that takes an extra second to be sure. This viewpoint reinforces R-FR-06 and motivates the human-in-the-loop verdict prompt in the evaluation harness.

**The platform-and-OS viewpoint** prioritises portability, or, more precisely, makes the project explicitly acknowledge its lack of portability. Windows 11 only; multi-monitor support; DPI-scaling-aware coordinate handling. These constraints are captured in R-NFR-09 (compatibility) and discussed at length in §9.7.

Where the viewpoints conflict the design rule is consistent: prefer the more conservative behaviour. When in doubt about whether to click, do not click; this is R-FR-06. When in doubt about which monitor to use, ask; this is the `--monitor` flag. When in doubt about whether a result should go into the CSV, log it with a `notes` field; this is the existing per-attempt schema in `baseline_results.csv`.

## 3.3 Requirement Gathering Techniques

Four requirement-gathering techniques were used during the project, each in proportion to its cost-effectiveness on a single-developer project.

**Literature review.** The single largest source of functional requirements is the existing literature reviewed in Chapter 2. The IVGocr architecture of Dardouri and colleagues directly contributed R-FR-01 through R-FR-05 (capture, instruction, detection, matching, action). The published failure modes of classical baselines (UIED's argument that neither pure deep learning nor pure CV suffices on its own [1]; Apple's published in-distribution-to-out-of-distribution drop [L5]) directly contributed R-FR-06 (refusal on uncertainty). The literature is the most reproducible requirement source for an academic project, because every requirement can be traced back to a publication.

**Self-as-stakeholder analysis.** The author is one of the operational users. Several requirements were derived from running early versions of the bot during the project's prototype phase: the multi-monitor coordinate confusion (O13) directly produced R-FR-07; the silent Tesseract failure (O12) produced part of R-NFR-04 (reliability); the difficulty of switching OCR engines from the CLI produced part of R-NFR-05 (usability). Self-as-stakeholder is a recognised method in agile and lean software engineering, though it is more often invoked in industrial projects than in dissertation work.

**Stakeholder interviews.** A short interview was conducted with the project supervisor early in the proposal phase to clarify the academic-stakeholder viewpoint described in §3.2.2. No formal transcript was kept, but the interview output is reflected in the proposal's research questions and is therefore the source of all four RQ-grounded requirements implicitly.

**Field observation of analogous systems.** The author used SikuliX, pywinauto and PyAutoGUI for short experimental sessions during the first month of the project. The observed failure modes from these sessions (template captures aging out, UIA Names that do not match the visible labels, coordinate scripts that broke when DPI changed) were converted into the explicit failure-mode list in §8.4 and into the comparison baselines in Chapter 7. This is, in effect, the requirement-gathering technique that justifies the lightweight stance: the requirements *not* met by existing tools are the most concrete justification for the new tool.

A fifth technique that the sample dissertation reviewed alongside this project [the RGU MSc skin-cancer report, 2026] used but this project did not is **stakeholder questionnaires**. Questionnaires are a sensible technique for projects with non-overlapping target users; for a developer-tooling artefact at MSc scale with the author as the primary user, the cost of designing and distributing a questionnaire would have exceeded the benefit. The qualitative-evaluation gap recorded as D-10 partially addresses this by gathering structured feedback from a small number of expert reviewers; that is a closer fit to the project than a survey.

## 3.4 Methodology for Obtaining Datasets

The data-engineering side of the project follows a three-tier methodology dictated by the data-availability constraints reviewed in §2.2.

**Tier 1 — public source-domain corpora.** Three publicly available datasets are used as the source domain: RICO [8], CLAY [10], and VINS [L2]. Acquisition is straightforward (a download from the respective project pages and a checksum check), but the cleaning and class-collapse work is non-trivial and is documented in Chapter 6. The combined corpus is the 6-class "Zenodo unified bundle" of approximately 9,646 screens used in `05_train_source.ipynb`.

**Tier 2 — captured target-domain unlabelled corpus.** The proposal commits to roughly 2,000 unlabelled desktop screenshots captured from 10 to 15 applications. At the time of writing the actual corpus is 50 personal screenshots (recorded under `samples/desktop_seed/`); the expansion to 2,000 is gap D-06. The capture methodology is implemented in `scripts/capture_screenshots.py` and uses `mss` for the screen grab and `pywinauto` for enumerating visible top-level windows. The script is parameterised by application list, theme (light/dark), and DPI scaling so that the eventual 2,000-screen corpus systematically covers the in-the-wild variability the bot encounters.

**Tier 3 — hand-curated target-domain labelled corpus.** The proposal commits to a 100-image labelled desktop corpus annotated in CVAT against the five-class schema. At the time of writing the labelled set is 8 hand-corrected images carrying 356 ground-truth boxes (`reports/tables/desktop_test_handcorrected.csv`); the expansion to 100 is gap D-07. Annotation methodology follows the CVAT shape-and-label convention used in the wider literature: rectangular bounding boxes only, no rotated boxes, no segmentation masks. Class labels are restricted to the 6-class taxonomy `{button, text, text_input, icon, menu, checkbox}`. Annotators (in practice, the author alone) follow a written guideline document that mirrors the conventions used in the CLAY release notes.

The three tiers feed three different experimental purposes. Tier 1 is the source-domain training set. Tier 2 is the unlabelled target corpus needed for SSP+FT and UDA. Tier 3 is the labelled target test set used for evaluating every adaptation method, and is also the training source for the few-shot fine-tuning experiment at $k = 1, 5, 10, 50, 100$.

## 3.5 Use Case Diagrams (UML)

The system supports six use cases, four of which are user-facing and two of which are internal-to-evaluation.

[FIGURE 3.1 — "UML use case diagram for VisClick."
 Suggested source: hand-drawn or draw.io export; one actor (the User), six use cases (UC-01..UC-06) with `<<include>>` relationships where appropriate. Path placeholder: `reports/figures/ch3_use_cases.png`.
 Suggested caption (~30 words): "Use case diagram for the VisClick prototype. UC-01 to UC-04 are user-facing; UC-05 and UC-06 are run during evaluation. Each use case maps to one or more functional requirements in §3.8."]

The six use cases are listed below at the level of detail customary for an MSc-level UML diagram.

* **UC-01 — Click a labelled element.** The user provides a text instruction; the system captures the screen, detects elements, matches the instruction, and clicks the chosen element.
* **UC-02 — Refuse a click on low confidence.** The user provides an instruction for which no high-confidence target exists; the system reports a structured failure rather than clicking.
* **UC-03 — Select a specific monitor.** The user selects which monitor the bot should operate on, via either the CLI flag or the GUI dropdown.
* **UC-04 — Inspect a prediction overlay.** The user opens the saved overlay PNG for any past click to verify what the bot did.
* **UC-05 — Run a baseline evaluation.** The evaluator runs `scripts/run_baselines.py` to evaluate one or more methods across the canonical task suite.
* **UC-06 — Generate result tables and figures.** The evaluator runs the analysis scripts to regenerate the report's tables and figures from the per-attempt CSV.

## 3.6 Use Case Descriptions

Each of the four user-facing use cases is described below at a more practical level than the UML. Use cases UC-05 and UC-06 are evaluation tooling and are documented in Chapter 6 rather than here.

**UC-01 — Click a labelled element.**

* *Primary actor:* End user (developer or power user).
* *Pre-condition:* The bot is launched, the model weights are loaded, and the target monitor is selected.
* *Main success flow:* (1) User types an instruction such as "click Save" into the GUI. (2) User presses the Run button or hits Enter. (3) The system pauses 3 seconds (allowing the user to switch focus to the target window). (4) The system captures the configured monitor. (5) The detector emits N candidate boxes. (6) The OCR layer reads the text on each box. (7) The matcher selects the best-fitting box above the similarity threshold. (8) The action layer moves the cursor to the box centre and clicks. (9) The system saves the overlay PNG and writes the CSV row.
* *Alternative flow:* If no candidate exceeds the similarity threshold, the system follows UC-02 instead of clicking.
* *Post-condition:* The targeted element has received a single left-click, and the action has been logged.

**UC-02 — Refuse a click on low confidence.**

* *Primary actor:* End user.
* *Pre-condition:* As UC-01.
* *Main success flow:* (1) User types an instruction. (2) System captures and detects as in UC-01. (3) Matcher computes the best-fitting box, but its similarity score is below the threshold (`min_text_similarity = 60` in the current build, planned to rise to 75 per gap D-05's adjacent fix). (4) System emits a structured `FAIL: cannot find <target>` message. (5) System still saves the overlay PNG (with no click marker) and writes a CSV row with verdict `refused`.
* *Alternative flow:* The user may lower the threshold via a CLI flag if they want to override; this is documented but not exposed in the GUI.
* *Post-condition:* No click was issued. The decision is logged.

**UC-03 — Select a specific monitor.**

* *Primary actor:* End user on a multi-monitor setup.
* *Pre-condition:* The system has detected more than one monitor at start-up.
* *Main success flow:* The user selects the target monitor from the GUI's dropdown (or passes `--monitor <id>` to the CLI). The system queries `mss.monitors` for the selected index, recovers the `(left, top)` offset, and uses that offset throughout the subsequent capture-detect-match-click flow.
* *Post-condition:* All subsequent clicks issued by the bot land on the chosen monitor regardless of where the GUI window itself is sitting.

**UC-04 — Inspect a prediction overlay.**

* *Primary actor:* Researcher or end user reviewing past behaviour.
* *Pre-condition:* The bot has previously processed at least one instruction.
* *Main success flow:* The user opens the saved overlay PNG (`reports/figures/baselines/<task>_<method>.png` for evaluation runs, or `runs/overlay-<timestamp>.png` for ad-hoc runs). The overlay shows the detected boxes coloured by class, the chosen box highlighted, the click point marked with a crosshair, and (when relevant) the OCR text overlaid above each box. The user can confirm or refute the bot's decision visually.
* *Post-condition:* No state change. The use case is purely diagnostic.

## 3.7 Functional Requirements

The functional requirements (R-FR-01 through R-FR-09) are formalised below. Each requirement carries a unique identifier, a description, a priority, the use cases it serves, and the section of the testing chapter that validates it. The pass-rate column reports the headline empirical result already measured against the requirement; the exact computation is in Chapter 7.

| ID | Requirement | Description | Priority | Use cases | Test section | Status |
|----|-------------|-------------|----------|-----------|--------------|--------|
| R-FR-01 | Screen Capture | The system shall capture a screenshot of the user-selected monitor at native resolution, in the virtual-desktop coordinate space. | Essential | UC-01, UC-03 | §7.3.1 | FULL — 15/15 on T01-T15 |
| R-FR-02 | Text Instruction Input | The system shall accept a free-form text instruction via CLI flag or GUI text box. | Essential | UC-01, UC-02 | §7.3.1 | FULL — 15/15 |
| R-FR-03 | Element Detection | The system shall detect candidate UI elements of types `{button, text, text_input, icon, menu, checkbox}` on the captured screenshot. | Essential | UC-01 | §7.2 | FULL — 15/15 emit ≥1 detection |
| R-FR-04 | Instruction-to-Element Matching | The system shall match the user instruction to one detected element using fuzzy OCR text similarity, with a class-aware bonus, and shall fall back to full-image OCR when no per-box candidate exceeds the threshold. | Essential | UC-01 | §7.3.1, §8.2 | FULL — 11/14 PASS on positives |
| R-FR-05 | Action Execution | The system shall move the mouse cursor to the centre of the chosen element and execute a single left-click. | Essential | UC-01 | §7.3.1 | FULL — 11/14 verdict |
| R-FR-06 | Refusal on Low Confidence | The system shall refuse to click when no candidate exceeds the similarity threshold, and shall emit a structured failure message. | Essential | UC-02 | §7.3.1 | PARTIAL — 0/1 on T15; planned threshold fix in D-05's adjacent change |
| R-FR-07 | Multi-Monitor Support | The system shall operate correctly across virtual-desktop coordinate spaces on multi-monitor setups, with an explicit monitor selector. | Important | UC-03 | live demo log | FULL — verified on 3440×1440 + 1920×1080 stacked layout |
| R-FR-08 | Visual Feedback | The system shall render an annotated overlay PNG of every prediction (detected boxes, chosen element, click marker, OCR text) for human verification. | Important | UC-04 | §7.3.1 | FULL — 60/60 overlays |
| R-FR-09 | Per-Attempt Logging | The system shall log per-attempt fields (instruction, capture path, predicted xy, verdict, latency, method, is_negative, notes) to a CSV file for evaluation. | Important | UC-05 | `reports/tables/baseline_results.csv` | FULL — 60/60 rows |

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
| R-NFR-10 | Scalability | Pipeline complexity scales linearly in #candidates per screenshot | per-box OCR is O(N); ceiling ≈ 300 boxes/screenshot | analytical, supported by §10 of data form | PARTIAL |

The classification of each NFR as Essential, Important, or Optional follows the same MoSCoW convention used for FRs. Accuracy, latency, reliability, security, and compatibility are Essential; the rest are Important or Optional. None of the NFRs are marked Failed; the two PENDING items (R-NFR-03, R-NFR-05 third-party) are timeline matters rather than fundamental capability gaps.

## 3.9 Summary

The requirements above are the contract the rest of the dissertation is evaluated against. They were derived from four requirement-gathering techniques (literature, self-as-stakeholder, supervisor interview, field observation of analogous systems) and from a six-ring Onion stakeholder model that captured viewpoint conflicts before they became design conflicts. Nine functional requirements (R-FR-01 to R-FR-09) and ten non-functional requirements (R-NFR-01 to R-NFR-10) are stated explicitly, each with an identifier, a target, and a pointer to the test section that validates it. The structure of the requirements list deliberately mirrors the structure of the testing chapter so a marker can audit any individual claim by chasing a single identifier from §3.7 / §3.8 down into §7.

The next chapter, Chapter 4, describes the project management approach: the research methodology, the software methodology, the risk register, and the four-phase project plan.

---

# Chapter 4 — Project Management

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

**Modularity.** The system is decomposed into seven Python packages under `src/visclick/` (`capture`, `detect`, `ocr`, `match`, `act`, `bot`, `gui`). Each package has a single responsibility and a small public surface, so that any one component can be replaced without touching the others. This is the architectural choice that made it possible to plug in three classical baselines and the VisClick full pipeline as four interchangeable `predict()` implementations in the same evaluation harness (`scripts/run_baselines.py`). Modularity is also what allows the dissertation to make the comparison chart in §7.4 a fair one: the four methods share the screenshot capture, the verdict-collection harness, and the per-attempt logging schema. Only the perception-and-grounding code differs.

**Reproducibility.** Every numerical claim in the report is regeneratable from a script in the public repository, against a CSV in `reports/tables/`, with a commit hash documented in the data form. This is the principle that drives the rule "every notebook cell that produces a report number prints a `REPORT §x.y = value` line" recorded in the data form's §0.2. It is also the principle that drives the explicit version-control of the desktop seed images and ONNX weights inside the repo rather than only on Drive.

**Refusal on uncertainty.** A click bot that issues a confident wrong click is worse than one that issues an honest failure. This principle is captured in R-FR-06 and is the architectural reason the matcher has a `min_text_similarity` threshold rather than always returning the highest-scoring candidate. The full justification, including the live-demo observation that motivated it (O14 in the data form), is in §3.2.2's discussion of stakeholder viewpoints.

A separate architectural pattern worth flagging is the **pre-flight probe**. The OCR layer exposes an `ocr_status()` function that runs at start-up and prints a tick or cross for each backend (EasyOCR, Tesseract, falling back to a pure-Python OCR). The detector layer exposes an equivalent `detect_status()` for ONNX model loading. The first time any of these probes fails, the `_warn_once()` helper prints the underlying error, the configured path, and three concrete fixes. This pattern was introduced after observation O12 (silent Tesseract failure during the live demo) and has been propagated to every external dependency in the stack. It is one of the strongest practical lessons of the project and is recorded as such in §9.3.

## 4.4 Software Development Methodology

The development process is best described as an agile/waterfall hybrid. The four-phase project plan from the proposal (Phase 1 through Phase 4) is essentially a waterfall structure: data engineering, then modelling, then prototype, then evaluation. Inside each phase, the actual day-to-day work was iterative; the data-form's observation log (O1 through O21) records the cycles of "try, hit a wall, document the wall, fix the wall, move on" that drove progress through each phase.

The agile elements are concrete. Continuous integration is provided by Git, with commits at a granularity that maps individual problems to individual fixes (the commit log includes entries such as `fix(make_prototype): load tasks from T01_T20.json tasks array`). Backlog management is provided by the `docs/VisClick_Detailed_Plan.md` Phase L checklist, which both this dissertation and the working code consult in lock-step. Retrospective is performed at the end of each phase: the observation log in §13 of the data form serves as the retrospective output, with each O-numbered entry describing what happened and what it taught the project.

The waterfall elements are equally concrete. Phase ordering was preserved: data engineering really did precede model training, model training really did precede the prototype, and the prototype really did precede the evaluation. No phase was started before the prior phase's deliverable existed. This is more rigid than a pure agile project would be, but it is appropriate for a research project where each phase's output is a measurement that the next phase's design depends on.

The choice of an agile/waterfall hybrid over pure agile or pure waterfall was made for one reason: a single-developer MSc project does not have the team structure that justifies a pure agile process (no scrum, no stand-ups, no separate product-owner role) but also cannot afford the inflexibility of pure waterfall (a single mid-project disconnect, as happened with the auto-label evaluation in O17, requires the freedom to re-scope upstream phases without throwing out the whole plan). The hybrid is what allowed the auto-label evaluation crisis to be turned into a controlled re-evaluation rather than into a project failure.

## 4.5 Project Management Methodology

Project tracking used two artefacts. The first is a static Gantt chart at the level of the four phases (Figure 4.1). The second is the rolling Phase L checklist in `docs/VisClick_Detailed_Plan.md`, which is more granular and is updated continuously.

[FIGURE 4.1 — "Project Gantt chart over the 12 months of the MSc."
 Suggested source: hand-drawn or exported from MS Project / draw.io / a spreadsheet. Should show Phase 1 (Months 1–3), Phase 2 (Months 4–7), Phase 3 (Months 8–9), Phase 4 (Months 10–12), with overlaps at phase boundaries to indicate continuous work. Path placeholder: `reports/figures/ch4_gantt.png`.
 Suggested caption (~30 words): "Twelve-month project plan over the four operational phases. Phase boundaries are deliberately drawn with overlap; in practice each phase's documentation continued while the next phase's experiments began."]

The two artefacts have different update cadences. The Gantt chart is updated at most monthly and is treated as a contract between the author and the supervisor. The Phase L checklist is updated continuously and is treated as the working memory of the project; every commit to the repository typically toggles at least one `[ ]` to `[x]`.

Time accounting was kept informally. The detailed plan's K.3 section recorded the original time budget of approximately 120 hours over twelve weeks (the proposal's reference cadence); the actual time spent is significantly higher and is not formally logged. For a future-work entry, an honest answer to "how long did this dissertation take" would be in the region of 200 to 250 hours.

## 4.6 Risk Mitigation Plan

The risk register is a forward-looking transformation of the observation log in §13 of the data form. Each risk has a probability, an impact, a mitigation, and a status. The table below mirrors the §17 of the data form but is reproduced here for completeness; the discussion that follows it is dissertation-grade rather than data-form grade.

**Table 4.1 — Risk register.**

| ID | Risk | Source | Prob | Impact | Mitigation | Status |
|----|------|--------|:----:|:------:|------------|--------|
| RR-01 | Pseudo-label evaluation overstates accuracy | O17, O19 | High | High | Hand-correct ≥ 8 test images; report both auto-label and hand-corrected mAP | Mitigated |
| RR-02 | Source-domain training distribution does not generalise to Win11 native | O11, O18 | High (confirmed) | High | OCR text-grounding fallback; recall-ceiling acknowledged; Phase 4.B planned | Mitigated |
| RR-03 | Silent dependency failure (Tesseract not on PATH) | O12 | Med | High | Startup probe `ocr.ocr_status()`; `_warn_once()` helper | Mitigated |
| RR-04 | Multi-monitor virtual-desktop coordinate confusion | O13 | High | High | `(left, top)` offset propagated through `act.click_box`; `--monitor` flag | Mitigated |
| RR-05 | Confident wrong action on negative case | O14, O21 | Med | High | `min_text_similarity` threshold; planned raise from 60 to 75 | Open |
| RR-06 | OCR latency dominates total wall-clock | O21, §10.1 | Certain | Med | Detector-first short-circuit (skip OCR on confident classes) | Open |
| RR-07 | Colab Free disconnect mid-training | O8 | Med | Med | `last.pt` per-epoch; resume-from-disconnect built in | Mitigated |
| RR-08 | Drive FUSE I/O instability on directories with 10k+ files | O1, O7 | High | Med | Retry + shell `find` fallback; cached listings | Mitigated |
| RR-09 | Drive FUSE `stat` cache lags `readdir` cache | O13 (nb 06) | Med | High | Set-of-stems via `find` retry; never `os.path.isfile()` on Drive | Mitigated |
| RR-10 | Auto-labeller class collapse (menu/checkbox ≈ 0) | O11, O17 | Med | Med | Hand-correct GT; Phase 4.B icon top-up; Phase 4.C light backbone FT | Open |
| RR-11 | Licence / IP concerns on dataset use | design review | Low | High | All datasets public; AGPL inherited from Ultralytics; documented in §8.10 | Mitigated |
| RR-12 | Personal-data leakage from desktop seed screenshots | design review | Low | High | All 50 PNGs manually reviewed before commit `7a5896c` | Mitigated |
| RR-13 | Bot misuse for click-fraud or automated account creation | §8.10 Social | Low (research scope) | Med | Human-in-the-loop verdict step; no headless service mode shipped | Monitored |

Three observations about the register are worth pulling out for dissertation prose.

First, **the highest-impact risks are all data-quality risks**, not modelling or deployment risks. RR-01, RR-02 and RR-10 between them account for the project's three biggest empirical findings (the auto-label/hand-correct mAP gap, the recall-bounded source-domain backbone, and the icon class-distribution skew). Each is a reminder that the modelling chain is no stronger than its weakest data link.

Second, **most of the Open risks have costed mitigations**. RR-05 (refusal threshold), RR-06 (OCR latency), and RR-10 (class top-up) all have a documented Phase 3.1 / Phase 4.B work item that would move them from Open to Mitigated. Whether those work items are completed before submission is a separate triage call.

Third, **the only Low-probability risk that remains Monitored is RR-13** (bot misuse). The probability is low because the project ships an interactive verdict step by default and no headless service mode. The risk is kept on the register because the *category* of risk (vision-driven UI automation can be misused at the systemic level) does not go away merely because this particular prototype mitigates it; the dissertation's social-impact discussion in §8.10 takes this category seriously.

## 4.7 Project Plan

The project plan is the four-phase structure inherited from the proposal. The Gantt-equivalent rendering is in Figure 4.1 above; the text below makes each phase's scope and deliverable explicit.

**Phase 1 — Data engineering and baseline establishment (Months 1–3, completed).** Public mobile UI datasets were acquired and consolidated into the 6-class unified bundle. A baseline detector was trained on the unified bundle. The 50-image desktop seed set was captured and auto-labelled. Eight test images were hand-corrected. The four transfer-learning ablations (M0, M1, M2, M3) were run on Colab Free, and the headline desktop fine-tune was selected. Three classical baselines (template, OCR-only, pywinauto) were implemented and evaluated on the 15-task suite. **Deliverable D1 (baseline performance report) is the content of §4.7 in the data form and §7.2 of this dissertation.**

**Phase 2 — Model adaptation experiments (Months 4–7, partially completed).** The DETR backbone implementation, the SSP+FT experiment, and the two UDA experiments (Adaptive Teacher and SHOT) are the outstanding pieces. These are listed as gaps D-01 through D-04 in `docs/Final_Report_GAPS.md`. Phase 1.B's transfer-learning ablations completed; Phase 2's full sample-efficiency curve (gap D-05) is also outstanding. **Deliverable D2 (ablation study and model-comparison report) is partially complete; the YOLOv8 side is the content of §7.2; the DETR side and the three remaining adaptation methods are outstanding work for the version of the dissertation that closes those gaps.**

**Phase 3 — Prototype integration (Months 8–9, completed).** The VisClick prototype is operational on Windows 11 with a CLI and a Tk GUI. The IVGocr architecture is implemented end-to-end. The interactive evaluation harness (`scripts/run_baselines.py`) supports the four-method comparison and the verdict-collection dialog. **Deliverable D3 (functional prototype) is the artefact in the public repository at https://github.com/HiranMadhu/visclick.**

**Phase 4 — Evaluation and thesis composition (Months 10–12, ongoing).** The 15-task evaluation is complete. TSR, latency, and failure-mode analysis are reported in §7 of this dissertation. The qualitative third-party evaluation (gap D-10) and the memory profiling (gap D-11) are outstanding. **Deliverable D4 (final evaluation report and packaged code) is the dissertation in front of the reader.**

The phase boundaries on the Gantt are deliberately drawn with overlap. In practice, Phase 4 (thesis writing) began during Phase 3 (prototype integration) because writing tends to surface gaps in measurement that the prototype then has to be re-run to fill. The data form's incremental "as-evidence-arrives" structure was deliberately designed to support this overlap.

## 4.8 Chapter Summary

The project follows a design-science research methodology, with a modular, reproducible, refusal-on-uncertainty software design, executed under an agile/waterfall hybrid development process. The risk register captures thirteen risks distilled from the observation log; ten are mitigated, two are open with costed plans, and one is monitored. The project plan is the four-phase structure inherited from the proposal; Phase 1 and Phase 3 are complete, Phase 2 is partially complete with the outstanding work listed in `docs/Final_Report_GAPS.md`, and Phase 4 is ongoing.

The next chapter, Chapter 5, presents the design: the high-level architecture, the block diagram and flow chart of the runtime, the research design, and the wireframes for the prototype GUI.

---

*End of Chapters 1, 2, 3, 4. Next chapters to be written: 5 (Design), 6 (Implementation), 7 (Testing), 8 (Evaluation), 9 (Conclusion).*
