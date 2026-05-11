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

---

*End of Chapter 1. Next chapter to be written: Chapter 2 — Literature Review.*
