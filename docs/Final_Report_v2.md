# VISCLICK – FINAL REPORT (V2, REFERENCE-STYLE DRAFT)

> **How to use this file.** This file restyles the existing `Final_Report.md` to match the convention used by the 2026 MSc Big Data Analytics cohort at IIT/RGU (see `gui_temp/2425489.pdf`). The structural changes from v1 are: ALL CAPS chapter and section headings, sequential figure and table numbering across the whole document (no chapter prefix), Harvard "Cite Them Right" citations in place of IEEE numeric, and slightly tighter declarative paragraphs. Content is preserved from v1 wherever practical. Front-matter (title page, consent, declaration, SPER) is intentionally omitted — the author will paste those separately. Figure placeholders use the pattern `[FIGURE N: title. Source: path. Caption: …]` so they can be replaced with the final images at submission time.
>
> **Reference budget.** Target ~30-40 references for the final list (the reference report has ~25). Citations are added sparingly: one anchor reference per claim, no stacking, no placeholder/stub entries. Most consolidation happens in Chapter 2.
>
> **Chapter 7 (Testing) is paused.** When the v2 draft reaches Chapter 6, work stops and waits for the user's notebook results (D-01 DETR, D-05 few-shot curve, YOLOv8 source, ScreenSpot CPV, prototype TSR) before Chapter 7 is written.

---

# CHAPTER 01 – INTRODUCTION

## 1.1 CHAPTER OVERVIEW

This chapter sets the outline of the project. A detailed discussion on the background, the problem and the proposed solution is presented. The chapter also defines the aim, the research questions, the research gap, and the research objectives that the rest of the report addresses. The operational objectives section gives a quick view of how the work was broken down into phases. The chapter closes with the scope statement and a short summary.

## 1.2 PROJECT BACKGROUND

Graphical user interfaces are the dominant way humans interact with software. Whether a user is filing a tax return on a web form, editing code in Visual Studio Code, processing an image in GIMP, or simply renaming a file in Windows File Explorer, the underlying mechanics are the same. A small set of clicks and keystrokes is directed at coloured rectangles on a screen. Because this is such a universal mode of interaction, automating it has been an active area of research and engineering for decades. The motivations range from the mundane, such as repetitive data entry and regression testing, to the more ambitious, such as accessibility tools that let users with motor impairment drive an application by voice, and autonomous agents that complete multi-step tasks on a user's behalf.

The available tooling for GUI automation falls broadly into two camps. The older camp is image-based automation. SikuliX, for example, lets a user record a small bitmap of a button and asks the operating system to find that bitmap on screen using OpenCV template matching (SikuliX, 2024). PyAutoGUI extends the same idea by exposing a Python interface to mouse and keyboard, but at heart it is still working in pixel coordinates (Sweigart, 2024). Tools of this kind are simple to use but brittle. The bitmap of a button is not the button. It is a photograph of the button taken on one particular machine, with one particular theme, at one particular DPI scaling, on one particular operating system build. Change any of those and the photograph stops matching. The same brittleness is described in AskUI's recent review of visual automation tools, which characterises SikuliX-style approaches as "image-recognition first" and notes that the recognition only generalises as far as the captured image library does (AskUI, 2024).

The second camp is accessibility-tree automation. Classic Windows applications expose a tree of named controls through the UI Automation framework, and Python libraries such as `pywinauto` walk that tree to find a *Save* button by its semantic name rather than by its appearance (pywinauto Contributors, 2024). When the approach works, it is fast and stable. The problem is that it has stopped working reliably on a meaningful fraction of the modern Windows application mix. Electron applications such as Visual Studio Code, Slack and Microsoft Teams expose only a degenerate accessibility tree because the entire interface is a Chromium DOM. Modern Windows 11 applications that use WinUI 3 or XAML islands frequently expose their controls under localised internal names rather than the visible labels a user sees. Web pages inside any browser are served through ARIA, which uses different conventions again. The empirical consequence, demonstrated in Chapter 7 of this report, is that `pywinauto` can still drive classic Windows applications reliably but fails on the modern WinUI 3 application surface that ships with Windows 11 by default.

Sitting outside both camps is a newer strand of work that uses computer vision and machine learning to detect UI elements directly from a screenshot, without any privileged access to the application's internal tree. Object-detection models such as YOLOv8 (Ultralytics, 2024) and DETR (Carion et al., 2020) are trained on annotated images of UIs and learn to predict bounding boxes labelled with classes such as `button`, `text`, `icon` and so on. Mobile UIs are well resourced in this respect because of the RICO dataset (Deka et al., 2017) and its denoised successor CLAY (Li et al., 2022a), which between them provide tens of thousands of labelled mobile screens. Recent work on YOLOv5-MGC reports mean average precision (mAP) figures in the high 80s and low 90s on mobile UIs (Cheng et al., 2022).

Desktops are a different story. Desktop UIs differ from mobile UIs along several axes at once. They are landscape rather than portrait. They are multi-window rather than single-window. They contain dense toolbars and ribbon menus that produce what Chen et al. (2020) describe as a "packed scene", where elements sit close enough together that a standard detector struggles to put a clean bounding box around each one. They draw on decades of stylistic variance (Win32, WPF, Material Design, custom themes, dark mode, high-contrast accessibility skins) that has no real parallel in the much more harmonised design languages of Android and iOS. And, critically, there is no RICO-equivalent dataset for desktops. The most recent attempts to build one, such as DeskVision (Wang et al., 2025) and GenGUI (Patel et al., 2025), are themselves dated 2024 and 2025, which indicates how recent the recognition of this gap is, and even those datasets are an order of magnitude smaller than RICO.

The practical consequence is that a detector trained to high accuracy on mobile UIs typically does not, on its own, do well on desktop screenshots. There is a domain shift between the two domains. Quantifying that shift, and developing data-efficient strategies for closing it, is the problem this project takes on.

[FIGURE 1: Examples of the mobile-to-desktop shift.
Source: `reports/figures/ch1_domain_shift_examples.png` (to be produced; suggested layout is a three-panel composite stitching a mobile portrait screen from CLAY, a classic Win32 desktop screen from Windows File Explorer, and a modern Win11 WinUI 3 Save-As dialog).
Caption: Three axes of the mobile-to-desktop shift. Left, a mobile portrait UI from CLAY. Centre, a classic landscape desktop with a packed toolbar. Right, a modern Win11 WinUI 3 dialog with flat, theme-dependent controls.]

## 1.3 PROBLEM STATEMENT

The practical problem this project addresses can be stated in one sentence. A practitioner who wants to build a vision-based UI automation tool for the modern Windows desktop today has no off-the-shelf option that is at the same time accurate, lightweight enough to run on a typical workstation, and tolerant of the variability that real desktop UIs exhibit in the wild.

The classical image-based tools, such as SikuliX (SikuliX, 2024) and PyAutoGUI (Sweigart, 2024), are lightweight but not tolerant of variability. Their bitmap matching collapses the moment the theme, DPI or font shifts. The accessibility-tree tools, such as `pywinauto`, are tolerant of theme and DPI by construction but not accurate on the modern Windows application mix. The empirical work in Chapter 7 shows `pywinauto` succeeding on only one out of fifteen task instances on a representative Windows 11 workload, and even that one success is a negative case where the correct outcome is for the bot to do nothing. At the other extreme, heavyweight large vision–language models such as SeeClick (Cheng et al., 2024) are accurate and tolerant of variability across domains, but they are not lightweight by any reasonable definition. They require multi-GPU inference setups and large memory budgets that are unrealistic for most practical deployments and are out of reach for an MSc-scale project.

The gap therefore sits in the middle of the spectrum. Can a lightweight object-detection model, trained on the relatively well-resourced mobile UI domain and adapted to the data-scarce desktop domain with a minimal labelled budget, deliver a detector that is "accurate enough" for use inside a practical automation pipeline? And, given that this is fundamentally a transfer-learning question, which adaptation strategy gives the best return on the labelled data budget? These are the questions the project sets out to answer.

A secondary, more practical, problem is that even an accurate detector is not, by itself, an automation system. A user does not want to be told "there are forty-seven elements on your screen". A user wants to say "click Save", and have the system do the right thing. That requires a grounding step in which a natural-language instruction is matched to one of the detected elements. The IVGocr framework of Dardouri et al. (2024a) provides a sensible scaffolding for this kind of pipeline, and this project adopts it. The novelty in the prototype is therefore not the pipeline architecture but the cross-domain-adapted detector that sits inside it.

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

The literature reviewed in Chapter 2 establishes that the gap addressed in this project is not a lack of state-of-the-art models. The mobile UI domain has highly optimised detectors of its own, such as YOLOv5-MGC (Cheng et al., 2022). The desktop target domain has a clear application pipeline in the IVGocr framework of Dardouri et al. (2024a). Heavyweight large vision–language models such as SeeClick (Cheng et al., 2024) are capable of bridging the domain gap, but they do so at a computational cost that puts them out of reach for the kind of practical, on-machine deployment this project cares about.

The gap is therefore in the combination. There is no published, lightweight, data-efficient method that takes a state-of-the-art mobile detector, adapts it to the desktop domain using the kind of small labelled data budget that an individual or a small team can realistically produce, and demonstrates that the resulting model is usable inside a complete automation pipeline rather than only on a static benchmark. This combination is what the dissertation contributes.

The gap is sharpened by the data side as well. The mobile UI domain has RICO (Deka et al., 2017) and CLAY (Li et al., 2022a) providing tens of thousands of labelled screens, while the desktop domain has only a handful of small, recently-published datasets (Wang et al., 2025; Patel et al., 2025). The data-scarce nature of the target domain is what mandates the use of domain adaptation in the first place. Training a high-capacity desktop-only model from scratch is not feasible at MSc scale; a model has to be trained somewhere else and then moved across.

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

The proposed solution has three interlocking components. The technical depth on each lives in Chapter 5 (Design) and Chapter 6 (Implementation); this section gives the high-level shape only.

### 1.9.1 DATA AND PREPROCESSING PIPELINE

The source mobile corpus is the CLAY dataset of Li et al. (2022a), a denoised subset of RICO (Deka et al., 2017). Using CLAY rather than raw RICO matters because RICO is known to contain significant layout noise; CLAY is a deep-learning pipeline that automatically cleans and corrects those raw layouts, and the resulting corpus is a much better starting point for transfer learning. The CLAY annotation schema is mapped onto the five-class desktop schema using a deterministic mapping table documented in Chapter 6.

The target unlabelled desktop corpus is collected by a Python script that drives `pywinauto` to enumerate the visible top-level windows of a curated set of 10 to 15 applications, captures each window with `mss`, and saves the resulting screenshot to disk. The script is parameterised by resolution, theme and DPI scaling so that the corpus covers the in-the-wild variability the deployed prototype will eventually encounter.

The target labelled desktop corpus is curated by hand from the unlabelled corpus and annotated in CVAT against the five-class schema. This corpus serves as the gold-standard test set against which all adaptation methods are evaluated and is also the source of the few-shot training subsets used in the sample-efficiency experiment.

### 1.9.2 ADAPTATION METHODOLOGIES

All adaptation methods are applied to both a YOLOv8 backbone and a DETR-R50 backbone, so that the cross-architecture comparison in RQ3 is a controlled one.

The baseline is established by running the mobile-trained detector zero-shot on the labelled target corpus. The resulting low mAP is the "problem" that the three adaptation methods then try to close.

The first adaptation method is few-shot supervised fine-tuning. The CLAY-trained backbone is frozen and only the final detection head is re-trained on the labelled desktop images, sweeping over a small range of training budgets to produce a data-efficiency curve. This is the simplest of the three methods and serves as the floor against which the other two are compared.

The second adaptation method is self-supervised pre-training followed by fine-tuning. A generative inpainting task (Anaya-Isaza et al., 2024) is used on the unlabelled desktop corpus. Random patches are masked out and the model is trained to predict them. The intuition is that, to inpaint a missing patch of a Windows toolbar, the model must implicitly learn the structural grammar of desktop UIs (toolbars are horizontal, icons sit in rows, dialog buttons cluster bottom-right, and so on). The self-supervised backbone is then handed to the few-shot procedure to measure whether unsupervised pre-training improves the final mAP.

The third adaptation method is unsupervised domain adaptation (UDA). Two state-of-the-art UDA frameworks are implemented and compared. The first is the Cross-Domain Adaptive Teacher of Li et al. (2022b), which is a teacher-student setup where a stable Exponential Moving Average teacher generates pseudo-labels on weakly augmented target images and a student is then trained on a mixed batch of labelled source data and strongly augmented pseudo-labelled target data. The second is SHOT (Liang et al., 2020), which freezes the source-trained classification head (the "source hypothesis") and adapts only the feature extractor on the unlabelled target images using self-supervision. The goal of SHOT is to align the new target features to the frozen source hypothesis rather than to retrain the head itself.

### 1.9.3 PROTOTYPE INTEGRATION AND EVALUATION

The prototype, named VisClick, is a direct implementation of the IVGocr architecture of Dardouri et al. (2024a). The novelty is the replacement of their standard YOLOv8 detector with the cross-domain-adapted detector from the previous component.

The runtime flow is as follows.

1. The user supplies a free-form text instruction, for example "click Save".
2. A screenshot of the user-selected monitor is taken with `mss`, in the virtual-desktop coordinate space.
3. The adapted detector runs on the screenshot and returns a set of candidate bounding boxes, each with a class label and a confidence score.
4. Tesseract or EasyOCR is run on each detected bounding box, rather than the whole image, to recover the visible text on the element. A full-image OCR pass is kept in reserve as a fallback for cases where the detector misses the target element entirely.
5. A fuzzy-string-matching function (`rapidfuzz`) computes the similarity between the user's instruction and the OCR text of each detected element. The element with the highest score above a configured similarity threshold is selected.
6. PyAutoGUI moves the cursor to the centre of the selected box and issues a single left click. When no candidate exceeds the threshold, the prototype refuses to click and reports a structured failure message. This refusal-on-uncertainty behaviour is a deliberate design choice, motivated by the observation that a confident wrong click is worse, in an automation tool, than an honest refusal.

The detection metric used for component-level evaluation is mAP at IoU 0.5, with the Central Point Validation (CPV) metric of Dardouri et al. (2024b) used for grounding quality. The end-to-end bot metric is Task Success Rate (TSR), defined as a binary pass or fail on each of the standardised tasks.

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

This chapter has set up the problem, the aim, the four research questions, the research gap and the four-phase work plan that the rest of the report follows. The picture, in one paragraph, is the following. GUI automation on the modern desktop is in an awkward place. Classical image-based tools are too brittle. Classical accessibility-tree tools have fallen out of step with the modern Windows application mix. The heavyweight large vision–language models that can do the job are too big to run anywhere most people would actually want to. Sitting in the middle, where there is a clear opportunity, is the idea of a cross-domain-adapted lightweight detector trained on the relatively well-resourced mobile UI domain and then carried across to the data-scarce desktop domain. The project investigates how far that idea can be pushed using three adaptation methods (few-shot fine-tuning, self-supervised pre-training plus fine-tuning, and unsupervised domain adaptation) on two backbone architectures (YOLOv8 and DETR), and integrates the best of those into a working prototype that closes the loop from a typed instruction to a click on the real Windows desktop.

The rest of the report is organised as follows. **Chapter 2** is the literature review. It walks through the datasets, the model architectures and the adaptation methodologies in enough depth to support the architectural choices made later, and it ends with the explicit research-gap statement that motivates the rest of the work. **Chapter 3** lays out the requirement analysis, including a stakeholder analysis using the Onion model, the functional requirements and the non-functional requirements with quantitative targets. **Chapter 4** covers the project management approach: the research methodology, the software development methodology, the risk register, and the project plan. **Chapter 5** covers the design, including a high-level architecture, a research design, a block diagram, a flow chart, and the wireframes for the prototype user interface. **Chapter 6** is the implementation chapter, which describes how the data pipeline, the three adaptation methods, and the prototype were actually built. **Chapter 7** is the testing chapter, which reports the model-level and prototype-level test results in tabular form. **Chapter 8** is the evaluation chapter, which interprets those results against the research questions and the requirements and includes a discussion of legal, ethical, professional and social impact. **Chapter 9** concludes with the limitations, the things the author would do differently in retrospect, and the directions for future work.
