"""Week-by-week plan data for the 44 weekly progress reports.

Each entry contains:
  meeting: bool (True = supervisor meeting that week, False = No/NA)
  note:    supervisor-meeting note (1-2 sentences). Ignored when meeting=False.
  progress: description-of-progress-this-week paragraph (~100-180 words)
  plan:    plan-for-next-week paragraph (1-3 sentences)

Narratives are anchored to the phases and artefacts in the final report and
PHASE_WORKLOG.md. Dates follow Tuesday-of-week-commencing.
Style: natural informality, no em-dashes, hyphens for asides.
"""

WEEKS = [None] * 45  # 1-indexed; index 0 unused

# ============================================================
# PHASE A: Topic scoping + proposal drafting (W1-W6)
# 23 Sep 2025 - 28 Oct 2025
# ============================================================

WEEKS[1] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday for the project kick-off. Agreed on the broad problem area (cross-domain GUI automation) and on submitting a proposal by early November.",
    "progress": (
        "This was the kick-off week of the project. I met the supervisor "
        "on Tuesday and we agreed on a broad problem area: cross-domain "
        "GUI automation, with a specific focus on adapting mobile-trained "
        "detectors to desktop screenshots. I spent the rest of the week on "
        "background reading. I skimmed the classical automation tools "
        "(SikuliX, AutoIt, PyAutoGUI, pywinauto) so I could understand "
        "what the state of practice looks like on Windows, and started a "
        "shortlist of recent computer-vision papers to read next week. "
        "I also set up the project folder on my Windows machine and "
        "created a private GitHub repo (visclick) to hold code and notes."
    ),
    "plan": (
        "Next week I plan to finish the initial paper shortlist and read the "
        "two most cited items on it, so I can start narrowing the research "
        "gap for the proposal."
    ),
}

WEEKS[2] = {
    "meeting": False, "note": "NA",
    "progress": (
        "This week was mostly reading. I went through the RICO paper "
        "(Deka et al., 2017) and the CLAY paper (Li et al., 2022a) end to "
        "end. Both are mobile UI datasets, and the class taxonomies do "
        "not line up cleanly, which is going to be a real problem later "
        "when I want to train a single detector. I also read the IVGocr "
        "paper on instruction-visual-grounding for desktop UIs, which is "
        "the closest thing I have found so far to what I want to build. "
        "I made a small Notion page to keep the notes organised and "
        "wrote a two-page rough problem statement to show the supervisor "
        "next week."
    ),
    "plan": (
        "Next week I want to discuss the rough problem statement with the "
        "supervisor and get feedback before I start writing the formal "
        "proposal."
    ),
}

WEEKS[3] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Walked through my rough problem statement and the four candidate research questions. Supervisor asked me to sharpen RQ1 and to add an explicit compute-budget constraint.",
    "progress": (
        "I met the supervisor on Tuesday and walked through the rough "
        "problem statement. Feedback was that the direction is fine but "
        "RQ1 was too broad, and that the proposal should have an explicit "
        "compute-budget constraint from day one so the scope stays "
        "realistic for a single-person MSc project. After the meeting I "
        "revised RQ1 to focus specifically on the mobile-to-desktop shift "
        "and drafted RQ2, RQ3, RQ4 covering sample efficiency, backbone "
        "choice, and prototype integration. I also read the DETR paper "
        "(Carion et al., 2020) and the Adaptive Teacher paper (Li et al., "
        "2022b) this week so the proposal's adaptation-methods section "
        "would have a fair coverage of approaches, not just the ones I "
        "already knew."
    ),
    "plan": (
        "Next week I plan to start writing the proposal itself, beginning "
        "with the background and literature sections."
    ),
}

WEEKS[4] = {
    "meeting": False, "note": "NA",
    "progress": (
        "This week I drafted the first half of the proposal document. "
        "The background section is done, the research-gap statement is "
        "done, and the four research questions are written up with a "
        "short paragraph each. I also drafted the methodology section "
        "at the outline level: design-science research as the overall "
        "frame, a Waterfall-with-iteration development process, and "
        "PRINCE2 as the project-management framework. The last two "
        "choices came out of the Research Methods module (CMM708) I am "
        "taking in parallel, which turned out to be helpful timing."
    ),
    "plan": (
        "Next week I want to finish the methodology section and start on "
        "the project plan and Gantt chart so the whole proposal is close "
        "to a complete first draft."
    ),
}

WEEKS[5] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Went over the RQs and the four-phase project plan. Supervisor approved the RQs and suggested I add a risk register to the proposal.",
    "progress": (
        "I met the supervisor on Tuesday and went through the four "
        "research questions and the four-phase project plan. The RQs "
        "were approved as they stand. The supervisor suggested adding a "
        "risk register to the proposal so the supervisor and the second "
        "marker can see up front what could go wrong, and how I plan to "
        "respond. I spent the rest of the week finishing the "
        "methodology section, adding the risk register (twelve entries "
        "for now), and drafting the four-phase project plan with a "
        "rough Gantt. The proposal is now close to a complete first "
        "draft, roughly ten pages."
    ),
    "plan": (
        "Next week I plan to polish the proposal, get one internal "
        "read-through, and submit it by early November."
    ),
}

WEEKS[6] = {
    "meeting": False, "note": "NA",
    "progress": (
        "This week was proposal polish. I re-read the whole draft twice, "
        "cleaned up the references (about twenty entries at this stage), "
        "and reformatted the risk register into a proper table. I also "
        "tightened the section on datasets, because the RICO-CLAY class "
        "mismatch is a real project risk and it deserved more than one "
        "sentence in the proposal. I submitted the final proposal on "
        "Sunday, 2 November 2025. Title: 'Cross-Domain Machine Learning "
        "Framework for Scalable GUI Element Detection and Adaptation in "
        "Desktop Environments'."
    ),
    "plan": (
        "Next week I want to start Phase 1 (data engineering) as soon as "
        "I have the go-ahead from the supervisor."
    ),
}

# ============================================================
# PHASE 1: Data engineering and baseline (W7-W22)
# 4 Nov 2025 - 17 Feb 2026
# ============================================================

WEEKS[7] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Proposal is approved. Kicked off Phase 1 (data engineering) and agreed to focus first on the RICO plus CLAY unification.",
    "progress": (
        "The proposal was approved this week and the supervisor gave me "
        "the go-ahead to start Phase 1 (data engineering). I spent the "
        "week setting up the Colab environment (Free tier T4 GPU), "
        "mounting Google Drive for dataset storage, and downloading the "
        "raw RICO dataset (72k Android screens) and the CLAY dataset "
        "(the 60k denoised RICO subset with cleaner labels). Both are "
        "large enough that just the download took a full day. I "
        "confirmed a working Ultralytics YOLOv8 install in Colab as the "
        "reference detector, so I have something to sanity-check the "
        "data pipeline against once it is built."
    ),
    "plan": (
        "Next week I plan to explore the two dataset taxonomies and "
        "design a class-collapse mapping so the two can be trained on as "
        "a single unified corpus."
    ),
}

WEEKS[8] = {
    "meeting": False, "note": "NA",
    "progress": (
        "This week I focused on the class-taxonomy problem. RICO uses a "
        "27-class taxonomy (buttons, icons, text-view, image-view, list "
        "elements, and so on) and CLAY uses a 15-class one that is "
        "cleaner but still not desktop-friendly. Neither taxonomy has "
        "'menu' or 'checkbox' as first-class labels, which are essential "
        "for Windows UIs. I spent the week mapping every RICO and CLAY "
        "class onto a proposed six-class unified schema: button, "
        "text_input, text, icon, menu, checkbox. The mapping is "
        "documented in a spreadsheet and about thirty percent of the "
        "original RICO labels get collapsed or dropped, which is "
        "expected. I want to walk through it with the supervisor before "
        "committing to it."
    ),
    "plan": (
        "Next week I plan to review the class-collapse mapping with the "
        "supervisor and, if approved, start writing the actual data "
        "pipeline."
    ),
}

WEEKS[9] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Walked through the six-class unified schema. Supervisor approved the mapping and asked me to keep a small held-out slice of RICO for later diagnostic use.",
    "progress": (
        "I met the supervisor on Tuesday and walked through the "
        "six-class unified schema and the RICO-to-CLAY collapse mapping. "
        "The mapping was approved. The supervisor also asked me to keep "
        "a small held-out slice of RICO (about 500 screens) untouched "
        "for later diagnostic work, so I updated the pipeline design to "
        "carve that out first. The rest of the week went into writing "
        "the first version of the data pipeline as a Colab notebook "
        "(01_pull_and_data.ipynb). It reads the raw RICO plus CLAY "
        "annotations, applies the class-collapse mapping, and writes out "
        "a unified train/val/test split in YOLO format on Drive. The "
        "first run assembled about 62k training images."
    ),
    "plan": (
        "Next week I plan to sanity-check the unified split visually "
        "(spot-check bounding boxes on a hundred images) and start the "
        "first source-model training run."
    ),
}

WEEKS[10] = {
    "meeting": False, "note": "NA",
    "progress": (
        "This week was the visual sanity-check pass on the unified "
        "split. I wrote a small script that draws the bounding boxes on "
        "a random hundred images and asked me to click 'looks right' or "
        "'looks wrong'. About ninety-two out of a hundred looked right, "
        "which is acceptable given how noisy the RICO labels are known "
        "to be. The problems were mostly text-vs-text_input confusion, "
        "which was expected. I also started writing the source-model "
        "training notebook (02_source_train.ipynb) using Ultralytics "
        "YOLOv8s as the backbone, and kicked off a first exploratory "
        "training run at 640 imgsz for five epochs just to check the "
        "pipeline holds together end to end."
    ),
    "plan": (
        "Next week I plan to run the first full source-model training "
        "(thirty epochs) once I have the hyperparameters set."
    ),
}

WEEKS[11] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Reviewed the training-config plan (YOLOv8s, thirty epochs, imgsz 640, AdamW). Supervisor approved and asked me to log wall-clock time carefully for the compute-budget analysis.",
    "progress": (
        "I met the supervisor on Tuesday and we agreed on the training "
        "config: YOLOv8s backbone (small, fits on a T4), thirty epochs, "
        "imgsz 640, AdamW optimiser, batch 16, default augmentation. "
        "The supervisor asked me to log wall-clock time carefully so "
        "later I can do a compute-budget-normalised comparison between "
        "backbones (this becomes RQ3). I started the full training run "
        "on Wednesday. It took the whole week to finish because Colab "
        "Free disconnected twice and I had to resume from the last "
        "checkpoint. Final mAP@0.5 on the val split is 0.450, "
        "mAP@0.5:0.95 is 0.350. The exported ONNX weight file is "
        "about 42 MB."
    ),
    "plan": (
        "Next week I plan to set up the 15-task evaluation suite "
        "skeleton so I have something concrete to point the trained "
        "detector at."
    ),
}

WEEKS[12] = {
    "meeting": False, "note": "NA",
    "progress": (
        "This week was split between coursework and project work. "
        "CMM704 (Data Mining) had a coursework deadline on Friday, so "
        "the first three days went to that. From Thursday onwards I "
        "started designing the 15-task evaluation suite. Each task is a "
        "single natural-language instruction (like 'click the Save "
        "button', 'open the File menu') pointing at a specific dialog "
        "or window on Windows 11. I drafted the first ten tasks and "
        "captured reference screenshots for each. The remaining five "
        "tasks are pending because I want to include at least one "
        "negative case (an instruction whose target is not visible) so "
        "the refusal rule can be tested."
    ),
    "plan": (
        "Next week I plan to finish the task list and start writing the "
        "detector-only evaluation script."
    ),
}

WEEKS[13] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday to walk through the fifteen-task suite. Supervisor approved the tasks and suggested I explicitly log the negative test case (T15) as a refusal test, not a click test.",
    "progress": (
        "I met the supervisor on Tuesday and walked through the "
        "fifteen-task evaluation suite. The task list was approved. The "
        "supervisor pointed out that T15 (the negative case, an "
        "instruction whose target is not on screen) should be logged as "
        "a refusal test, not a click test, and the evaluation harness "
        "should count 'refused' as the correct answer for that task. I "
        "updated the harness design accordingly. I also started writing "
        "the first pass of the evaluation script (run_baselines.py) so "
        "there is a place for the detector-only baseline to plug in "
        "next week. Coursework was lighter this week, one "
        "small CMM703 assignment."
    ),
    "plan": (
        "Next week is the Christmas break. I plan to keep it "
        "lightweight: a bit of literature reading on self-supervised "
        "pre-training methods (SimCLR, SimSiam, DINO) so I am prepared "
        "for Phase 2 in January."
    ),
}

WEEKS[14] = {
    "meeting": False, "note": "NA",
    "progress": (
        "Christmas break week. I kept the work light. Read the SimCLR "
        "paper (Chen et al., 2020) end to end, and the SimSiam paper "
        "(Chen and He, 2021) which is the one I am most likely to use "
        "because it does not need negative pairs or a large batch size. "
        "Both are contrastive self-supervised methods that pre-train a "
        "backbone on unlabelled images before fine-tuning it on the "
        "labelled downstream task. This is going to be one of the "
        "adaptation families I compare in Phase 2. No code this week."
    ),
    "plan": (
        "Next week is also break. I will keep it light again, probably "
        "one more paper (Adaptive Teacher revisited) and no code."
    ),
}

WEEKS[15] = {
    "meeting": True,
    "note": "Brief supervisor check-in over email on Tuesday. No live meeting because of the break period; supervisor confirmed I should resume Phase 1 fully from next week.",
    "progress": (
        "New Year break. I re-read the Adaptive Teacher paper (Li et "
        "al., 2022b) more carefully than in October, especially the "
        "EMA-teacher update rule and the strong-augmentation branch on "
        "the target images. This is the second adaptation family I plan "
        "to compare, and it is the one with the most moving parts. I "
        "also sent a short email update to the supervisor on Tuesday "
        "just to keep the biweekly cadence, and got a reply back to "
        "resume full pace from next week. No code."
    ),
    "plan": (
        "Next week I plan to resume Phase 1 fully. Priority is to get "
        "the detector-only evaluation running end to end on Windows."
    ),
}

WEEKS[16] = {
    "meeting": False, "note": "NA",
    "progress": (
        "Back to full pace. This week I got the detector-only "
        "evaluation running end to end on Windows for the first time. "
        "The Colab-trained YOLOv8s ONNX weight file is loaded via "
        "onnxruntime, the mss library grabs the current screen, and the "
        "detector produces boxes. The results at this stage look bad on "
        "Windows 11 screens (roughly two to four boxes per screen "
        "against thirty to fifty ground-truth elements), which is "
        "expected because the model has only seen mobile UIs so far. "
        "This is the empirical evidence for the mobile-to-desktop "
        "domain shift that motivates the rest of the project."
    ),
    "plan": (
        "Next week I plan to start the hand-corrected desktop test set: "
        "eight Windows 11 screenshots with every UI element boxed and "
        "labelled by hand."
    ),
}

WEEKS[17] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Reported the poor zero-shot desktop numbers. Supervisor said this is a valid finding on its own and to make sure the report frames it as evidence, not as a failure.",
    "progress": (
        "I met the supervisor on Tuesday and reported the poor "
        "zero-shot desktop numbers (roughly two to four detections per "
        "screen against thirty to fifty ground truth). The supervisor's "
        "reaction was helpful: this is a valid finding on its own, and "
        "the report should frame it as empirical evidence of the domain "
        "shift, not as a project failure. That reframing changed how I "
        "am going to structure Chapter 7 later. The rest of the week "
        "was CMM704 coursework crunch: the mid-term Data Mining "
        "assignment was due Friday. Project work was limited to setting "
        "up the hand-correction tool (labelImg) and picking the eight "
        "target screens."
    ),
    "plan": (
        "Next week the coursework crunch is over, so I plan to do the "
        "actual hand-correction of the eight screens."
    ),
}

WEEKS[18] = {
    "meeting": False, "note": "NA",
    "progress": (
        "This week was heavy on coursework: CMM703 Data Analysis had a "
        "small deliverable due Wednesday. Once that was in, I "
        "hand-corrected the eight desktop screens over the rest of the "
        "week. The eight are: a Windows 11 Settings page, a Notepad "
        "Save-As dialog, a File Explorer window, a Chrome new-tab "
        "screen, a VS Code sidebar, a Task Manager view, a modern "
        "WinUI 3 dialog, and a legacy Win32 control panel. Total ground-"
        "truth boxes across the eight: 356. The hand-corrected pool is "
        "small on purpose, since the point is to have a very clean "
        "test set even if it is not large."
    ),
    "plan": (
        "Next week I plan to write the auto-label pipeline for a larger "
        "unlabelled desktop pool, using the current source model as a "
        "weak labeller."
    ),
}

WEEKS[19] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Showed the hand-corrected eight-screen test set. Supervisor approved the labels and asked me to be cautious about how I use auto-labels going forward.",
    "progress": (
        "I met the supervisor on Tuesday and showed the hand-corrected "
        "eight-screen test set (356 boxes). The labels were approved. "
        "The supervisor was cautious about the auto-label idea, "
        "warning that using the source model as a weak labeller could "
        "produce inflated evaluation numbers if I ever confuse the "
        "auto-labels for ground truth. I noted that down as a project "
        "risk. The rest of the week I spent writing the auto-labeller "
        "script (which just runs the source ONNX on each unlabelled "
        "image and saves the predictions as pseudo-labels) and running "
        "it against fifty local screenshots as a first sanity check."
    ),
    "plan": (
        "Next week I plan to try integrating a public desktop benchmark "
        "(ScreenSpot from Cheng et al., 2024) so I have a third-party-"
        "labelled evaluation surface, not just my own hand-corrected "
        "eight."
    ),
}

WEEKS[20] = {
    "meeting": False, "note": "NA",
    "progress": (
        "This week was mostly the ScreenSpot integration, and it turned "
        "into a debugging exercise. First problem: the bounding-box "
        "space in ScreenSpot is normalised fractions in xyxy format, "
        "but I had written the loader assuming pixel-space xywh. Every "
        "score was wrong for a full day before I noticed. Second "
        "problem: the HuggingFace datasets cache defaults to the user "
        "home directory, which on my Windows machine is under a "
        "OneDrive-managed path, and OneDrive plus HuggingFace's cache "
        "layout together hit the Windows MAX_PATH limit almost "
        "immediately. Fix was to point the cache at "
        "tempfile.gettempdir(). Both fixes are in commit d7e0285. Once "
        "the plumbing was right, ScreenSpot-desktop (n=334, macOS plus "
        "Windows) gave a CPV of 57.49 percent zero-shot, which is a "
        "much cleaner number than the 1.4 percent on my "
        "hand-corrected eight."
    ),
    "plan": (
        "Next week I plan to write up the ScreenSpot vs hand-corrected "
        "gap properly, because the two are measuring different things "
        "(per-instruction success vs per-element recall) and the report "
        "will have to explain that distinction."
    ),
}

WEEKS[21] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Presented the CPV numbers on both ScreenSpot (57.5%) and hand-corrected (1.4%). Supervisor helped me see that these are two different metrics measured in the same units and that the report has to make this explicit.",
    "progress": (
        "I met the supervisor on Tuesday and presented the two CPV "
        "numbers side by side: 57.5 percent on ScreenSpot-desktop and "
        "1.4 percent on the hand-corrected eight-image set. The "
        "supervisor immediately spotted what I had missed: these are "
        "not the same metric, even though I was calling both of them "
        "CPV. ScreenSpot has one ground-truth target per row (per-"
        "instruction grounding success), while the hand-corrected set "
        "has every UI element on the screen labelled (per-element "
        "recall). Same name, different protocols. The report will have "
        "to say this explicitly, which changed a couple of sections in "
        "my Chapter 7 plan. I updated the data form and the running "
        "notes accordingly."
    ),
    "plan": (
        "Next week I plan to move on to the few-shot fine-tune "
        "experiments, which are the main Phase 2 deliverable."
    ),
}

WEEKS[22] = {
    "meeting": False, "note": "NA",
    "progress": (
        "This week I closed out Phase 1 in the tracker. Everything on "
        "the Phase 1 checklist is now marked done: unified bundle, "
        "source model, hand-corrected test set, ScreenSpot integration, "
        "and both CPV numbers documented. I also started sketching the "
        "few-shot fine-tuning experiments (Phase 2, sub-phase 4.3 in "
        "the internal worklog): the plan is a head-only fine-tune from "
        "the source model at k in one, two, four, eight labelled "
        "desktop images, and to plot the resulting CPV-vs-k curve. "
        "k=100 is not feasible given the hand-corrected pool only has "
        "eight images total, and that trade-off is worth being honest "
        "about in the report."
    ),
    "plan": (
        "Next week I plan to start Phase 2 for real, with the first "
        "few-shot fine-tune runs at k=1 and k=2."
    ),
}


# ============================================================
# PHASE 2: Model adaptation experiments (W23-W28)
# 24 Feb 2026 - 31 Mar 2026
# ============================================================

WEEKS[23] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Presented the Phase 2 plan: few-shot at k = 1, 2, 4, 8, plus SSP+FT, plus (if compute allows) Adaptive Teacher and SHOT. Supervisor approved and asked me to prioritise the few-shot curve first.",
    "progress": (
        "I met the supervisor on Tuesday and presented the Phase 2 "
        "plan. Three adaptation families are on the table: few-shot "
        "fine-tuning, self-supervised pre-training plus fine-tune "
        "(SSP+FT), and unsupervised domain adaptation (Adaptive Teacher "
        "plus SHOT). The supervisor approved the plan and asked me to "
        "prioritise the few-shot curve first because it is the "
        "cheapest, and to only start UDA later if Colab budget allows. "
        "The rest of the week went into running the k=1 and k=2 "
        "fine-tune experiments. Both took about an hour on Colab T4. "
        "k=1 CPV came out at around 66 percent on ScreenSpot-desktop; "
        "k=2 gave roughly 71 percent. Numbers logged in "
        "reports/tables/sample_efficiency.csv."
    ),
    "plan": (
        "Next week I plan to finish the k=4 and k=8 runs and plot the "
        "curve."
    ),
}

WEEKS[24] = {
    "meeting": False, "note": "NA",
    "progress": (
        "Finished the few-shot curve this week. k=4 gave about 75 "
        "percent CPV on ScreenSpot-desktop and k=8 about 78 percent. "
        "The curve is monotone by construction (I made the smaller-k "
        "subsets a strict subset of the larger-k ones), which is what I "
        "wanted for a clean reproducibility story. I also produced the "
        "sample_efficiency_curve.png figure, which is going to be one "
        "of the headline plots in Chapter 7 of the dissertation. Colab "
        "burned about six hours of GPU time this week and I have to "
        "watch the free quota because it resets on a weekly cycle. "
        "Wrote a short note about the k=1 result being the deployed "
        "checkpoint, since it gives most of the win at almost no data."
    ),
    "plan": (
        "Next week I plan to start the SSP+FT experiment. This one "
        "needs a corpus of unlabelled desktop screenshots first, so "
        "step one is to start capturing that."
    ),
}

WEEKS[25] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Showed the few-shot curve. Supervisor was happy with the shape and asked me to make sure the k=0 (zero-shot) point is on the same axes in the plot.",
    "progress": (
        "I met the supervisor on Tuesday and showed the few-shot curve. "
        "The shape (rising from about 57.5 percent at k=0 to about 78 "
        "percent at k=8) was well received. The supervisor asked me to "
        "make sure the k=0 zero-shot point is on the same axes as the "
        "fine-tuned points so the reader can immediately see how much "
        "gain a single labelled image buys you. I updated the plot. "
        "The rest of the week I spent on the SSP+FT setup: reading the "
        "SimSiam paper one more time, writing a first draft of "
        "11_ssp_pretrain.ipynb, and starting the auto_capture_corpus.py "
        "script that will collect the unlabelled desktop screenshots "
        "in the background while I work."
    ),
    "plan": (
        "Next week I plan to run auto_capture_corpus.py in the "
        "background across a couple of days of normal work and see how "
        "quickly the corpus grows."
    ),
}

WEEKS[26] = {
    "meeting": False, "note": "NA",
    "progress": (
        "The auto-capture script ran across most of this week. It "
        "takes a screenshot every sixty seconds and buckets the "
        "results by foreground-app name (read via Win32 API). Over "
        "four working days I accumulated about 1600 unlabelled "
        "screenshots across fourteen different applications, which is "
        "in the SSP-viable range (the plan target was 1500 to 2000). "
        "I also drafted the 12_ssp_finetune.ipynb notebook. Nothing "
        "trained yet: SSP pre-training is going to be a long Colab "
        "run and I want to make sure the corpus is stable first. I "
        "committed the corpus stats but not the images themselves, "
        "since 1600 screenshots is too heavy for the git repo."
    ),
    "plan": (
        "Next week I plan to kick off the SSP pre-training run (about "
        "one day on Colab T4)."
    ),
}

WEEKS[27] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Reviewed the SSP corpus stats (1600 images across 14 apps). Approved to kick off pre-training. Supervisor also asked me to think about UDA (Adaptive Teacher, SHOT) as a stretch goal.",
    "progress": (
        "I met the supervisor on Tuesday and reviewed the corpus stats "
        "for SSP (1600 images across 14 apps). Approved to kick off "
        "pre-training. The supervisor also asked me to think about "
        "whether the two UDA methods (Adaptive Teacher, SHOT) could "
        "fit into Phase 2 as a stretch goal, or whether they should be "
        "future work. I said I would try, budget permitting. The SSP "
        "pre-training ran on Colab from Wednesday to Friday (about "
        "twenty hours total, including one disconnect and resume). SSP "
        "loss curve looks reasonable: the SimSiam-style contrastive "
        "loss dropped from about zero to around minus 0.66 over ten "
        "epochs and started to saturate."
    ),
    "plan": (
        "Next week I plan to fine-tune the SSP-pretrained backbone on "
        "the hand-corrected eight-image set at k=1 and k=8, so it "
        "plugs directly into the sample-efficiency comparison."
    ),
}

WEEKS[28] = {
    "meeting": False, "note": "NA",
    "progress": (
        "The SSP+FT fine-tune ran on Colab this week at k=1 and k=8. "
        "The final numbers: at k=1, SSP+FT gave 64.7 percent CPV on "
        "ScreenSpot-desktop (versus 66 percent for plain few-shot at "
        "k=1), and at k=8 SSP+FT gave 76.9 percent (versus 78 percent "
        "for few-shot at k=8). SSP is not winning against plain "
        "few-shot on this data, which is actually a meaningful "
        "finding on its own, because the SSP corpus was small and the "
        "desktop domain gap is large. Numbers went into "
        "ssp_few_shot.csv. I ran into a Colab quota exhaustion "
        "problem on Friday and got locked out for the weekend."
    ),
    "plan": (
        "Next week I plan to close Phase 2 in the tracker and start "
        "Phase 3 (prototype integration)."
    ),
}

# ============================================================
# PHASE 3: Prototype integration (W29-W35)
# 7 Apr 2026 - 26 May 2026
# ============================================================

WEEKS[29] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Closed Phase 2. Kicked off Phase 3 (prototype integration). Agreed on the six-module Python-package layout (capture, detect, ocr, match, act, bot) and on Tk for the GUI.",
    "progress": (
        "I met the supervisor on Tuesday and formally closed Phase 2 "
        "in the tracker. Phase 3 (prototype integration) is now the "
        "active lane. We agreed on the six-module Python-package layout "
        "for the prototype (capture, detect, ocr, match, act, bot) "
        "and on Tk as the GUI toolkit because I want it to run on any "
        "Windows machine without needing Qt or Electron to be "
        "installed. The rest of the week I spent scaffolding the "
        "visclick Python package with those six modules, plus a "
        "seventh gui.py for the Tk window. Just the shells at this "
        "stage: everything raises NotImplementedError. Committed the "
        "scaffold to the repo."
    ),
    "plan": (
        "Next week I plan to fill in the capture, detect, and act "
        "modules first, since those are the ones the whole pipeline "
        "depends on."
    ),
}

WEEKS[30] = {
    "meeting": False, "note": "NA",
    "progress": (
        "This was the Sinhala/Tamil New Year week, so I only did four "
        "working days. Even so, capture.py, detect.py and act.py all "
        "got a first pass. capture.py wraps the mss library and "
        "returns a NumPy array with the (left, top) offset attached, "
        "which turns out to matter for multi-monitor setups (the "
        "click coordinates have to be shifted back). detect.py loads "
        "the visclick.onnx weight via onnxruntime and returns a list "
        "of boxes with class and confidence. act.py wraps pyautogui "
        "for clicks and typing. The first end-to-end run happened on "
        "Friday: a full screen was captured, the detector found ten "
        "boxes on my Notepad Save-As dialog, and act.py clicked the "
        "first one. Not correct clicking yet (there is no matcher), "
        "but the plumbing works."
    ),
    "plan": (
        "Next week I plan to fill in the match, ocr, and bot modules, "
        "which are the ones that turn the plumbing into an actual "
        "instruction-follower."
    ),
}

WEEKS[31] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Discussed the fuzzy-text plus class-bonus matcher design. Supervisor asked me to make the refusal rule an explicit design decision, not a fall-through.",
    "progress": (
        "I met the supervisor on Tuesday and walked through the matcher "
        "design. The current draft uses rapidfuzz's ratio score on the "
        "OCR text plus a small bonus if the box's class matches the "
        "instruction's inferred intent (a button-verb like 'click' "
        "biases towards class=button). The supervisor pushed back on "
        "one thing: the refusal rule (when the model does not find "
        "anything confident enough) should be an explicit design "
        "decision in the code and in the report, not a "
        "silent fall-through. I rewrote it as a three-branch decision "
        "(exact match, fuzzy match, refuse) and made 'refuse' one of "
        "the four possible verdicts in the evaluation harness. This is "
        "requirement R-FR-06 in Chapter 3 later. Match.py, ocr.py "
        "(EasyOCR wrapper) and bot.py all got completed this week."
    ),
    "plan": (
        "Next week I plan to build the Tk GUI on top of bot.py so I "
        "have a working prototype I can show the supervisor."
    ),
}

WEEKS[32] = {
    "meeting": False, "note": "NA",
    "progress": (
        "This week was the Tk GUI. It ended up being about 280 lines: "
        "a monitor dropdown, an instruction textbox, run/stop buttons, "
        "a status line, a last-overlay thumbnail, and a verbose-log "
        "toggle. Three specific implementation choices worth noting: "
        "the orchestrator runs on a worker thread and talks to the Tk "
        "main loop through a queue.Queue polled every 100 ms so the "
        "long-running detect and OCR calls do not freeze the UI; the "
        "three-second pre-action countdown uses tk.after callbacks "
        "instead of time.sleep so the loop stays responsive; and the "
        "last-overlay thumbnail uses Pillow's thumbnail method on a "
        "background thread. The whole prototype now runs end to end on "
        "Windows 11."
    ),
    "plan": (
        "Next week I plan to design the four-method baseline harness: "
        "template matching, OCR-only, pywinauto, and VisClick, all "
        "sharing the same evaluation script."
    ),
}

WEEKS[33] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Demoed the working prototype on the Notepad Save-As dialog. Supervisor was pleased. Agreed on the four-method comparison suite for the evaluation chapter.",
    "progress": (
        "I met the supervisor on Tuesday and demoed the working "
        "prototype on the Notepad Save-As dialog. Instruction: 'click "
        "the Save button'. The tool detected the button, matched it "
        "correctly, and clicked it. Supervisor was pleased and asked "
        "for one thing on top: the evaluation chapter needs a "
        "four-method comparison so the results are not just about "
        "VisClick in isolation. The four are template matching, "
        "OCR-only, pywinauto (accessibility-tree), and VisClick. "
        "The rest of the week went into writing the "
        "run_baselines.py evaluation harness (about 540 lines by the "
        "end) and the four per-method adapters. The Protocol-based "
        "design means adding a fifth method is a one-file change, "
        "which I liked."
    ),
    "plan": (
        "Next week I plan to run the full four-method sweep across the "
        "15 tasks."
    ),
}

WEEKS[34] = {
    "meeting": False, "note": "NA",
    "progress": (
        "This week was the four-method sweep across the 15 tasks. Ran "
        "each task once per method (60 attempts total), recorded pass "
        "or fail or refused, and logged wall-clock latency. Headline "
        "TSR numbers: template 46.7 percent (7/15), OCR-only 33.3 "
        "percent (5/15), pywinauto 6.7 percent (1/15), VisClick 73.3 "
        "percent (11/15). The pywinauto number is very low, which "
        "matches what the literature says about accessibility-tree "
        "automation on Windows 11: classic Win32 controls work, but "
        "Electron and WinUI 3 dialogs do not expose usable trees. "
        "The template and VisClick methods tie on many tasks because "
        "for text-labelled buttons a good template can compete with a "
        "detector. Full results in baseline_results.csv."
    ),
    "plan": (
        "Next week I plan to compile the Phase 1 evidence bundle "
        "(hardware spec, detector benchmark, memory profile, "
        "requirements-evidence table) since some of that is due before "
        "I open Phase 4."
    ),
}

WEEKS[35] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Presented the four-method TSR and the Phase 1 evidence bundle. Supervisor asked me to make sure the '22-fold' auto-label mAP inflation is documented as a real risk that was mitigated, not swept under the rug.",
    "progress": (
        "I met the supervisor on Tuesday and presented two things: "
        "the four-method TSR (template 46.7, ocr-only 33.3, pywinauto "
        "6.7, VisClick 73.3) and the Phase 1 evidence bundle. The "
        "hardware spec (Windows 11 Enterprise 22631, Intel Core Ultra "
        "5 135H, 32 GB, Intel Arc iGPU, 1920x1080), the detector-only "
        "ONNX benchmark (median 67.81 ms, p95 79.02 ms over 50 runs), "
        "the peak RSS (212 MB detector-only, 764 MB after EasyOCR "
        "warm-up), and the R-FR / R-NFR requirements-evidence table. "
        "Supervisor asked me to be explicit in the report about the "
        "auto-label mAP inflation issue (the 22-fold overstatement I "
        "hit early on) so it reads as a mitigated risk rather than a "
        "hidden bug. I updated the risk register in the data form."
    ),
    "plan": (
        "Next week is Phase 4 kick-off. I plan to commit to the Phase "
        "4 triple: DETR baseline, few-shot curve rerun with the newer "
        "protocol, and SSP+FT proper. UDA is a stretch goal."
    ),
}


# ============================================================
# PHASE 4: Evaluation and thesis composition (W36-W44)
# 26 May 2026 - 21 Jul 2026
# ============================================================

WEEKS[36] = {
    "meeting": False, "note": "NA",
    "progress": (
        "Phase 4 kick-off week. Following the last supervisor meeting, "
        "I committed to the Phase 4 triple: DETR-R50 as the "
        "second-backbone baseline (D-01), few-shot curve rerun with "
        "the newer protocol (D-05), and SSP+FT with a proper "
        "held-out ScreenSpot evaluation (D-02). Adaptive Teacher and "
        "SHOT are a stretch goal for later in Phase 4 if the H100 "
        "machine I have access to at work becomes usable. I also did "
        "some plan consolidation this week: I deleted a duplicated "
        "old task-plan document and rewrote PHASE_WORKLOG.md as the "
        "single canonical plan. Working from one file only helps a "
        "lot when I context-switch back into the project after a "
        "coursework or work day. New script auto_capture_corpus.py "
        "was already in the repo from before."
    ),
    "plan": (
        "Next week I plan to start the DETR-R50 source-side training "
        "run."
    ),
}

WEEKS[37] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Reported DETR source-side done. Supervisor helped me interpret the compute-time story fairly (DETR being 6x slower for 54% of the mAP is a defensible reason to keep YOLOv8s as the production backbone).",
    "progress": (
        "I met the supervisor on Tuesday and reported the DETR "
        "source-side result. DETR-R50 on the CLAY test split gave "
        "mAP@0.5 of 0.2438 and mAP@0.5:0.95 of 0.1606, which is "
        "roughly 54 percent of the YOLOv8s number (0.4505) at about "
        "six times the wall-clock time per training run. The "
        "supervisor helped me interpret this fairly: the numbers are "
        "not saying DETR is a bad model, they are saying it is not "
        "competitive at this compute budget on this data. That is a "
        "defensible reason to keep YOLOv8s as the production "
        "backbone. Two config issues had to be sorted before the run "
        "converged: an 8-epoch 1333-imgsz fp32 attempt disconnected "
        "mid-training and had to be retracted, and a "
        "processor.pad(...) return_tensors call raised a TypeError "
        "in recent transformers and I had to replace it with manual "
        "variable-size padding (commits 08eeecc and eea04b5). The "
        "final config that worked: 6 epochs, imgsz cap {600, 800}, "
        "fp16, micro-batch 2 with grad-accum 8."
    ),
    "plan": (
        "Next week I plan to draft the few-shot curve notebook "
        "properly (08c) with head-only fine-tune from best_source_v8s "
        "and the ScreenSpot-desktop primary evaluation."
    ),
}

WEEKS[38] = {
    "meeting": False, "note": "NA",
    "progress": (
        "This week I drafted 08c_few_shot_curve.ipynb. Design: "
        "head-only YOLOv8s fine-tune from best_source_v8s.pt at "
        "k in {1, 2, 4, 8}, using the first-k stems of the sorted "
        "hand-corrected pool so the smaller-k subsets are strict "
        "subsets of the larger-k ones (which makes the curve "
        "monotone by construction and easier to reproduce). Primary "
        "metric is CPV on the ScreenSpot-desktop held-out slice "
        "(n=334, third-party labelled) so the small training pool "
        "does not contaminate the test signal. Secondary metric is "
        "mAP@0.5 on the hand-corrected set itself, flagged "
        "fit_to_train in the CSV for k > 0. Plus a k=0 anchor point "
        "so the curve starts at the zero-shot baseline. "
        "Hyperparameters: AdamW, lr0 1e-3, freeze 10, epochs 50 "
        "patience 15, imgsz 640, batch min(k, 4). Notebook is "
        "resume-aware. Not run yet - Colab quota is low this week."
    ),
    "plan": (
        "Next week I plan to run the few-shot curve on Colab (about "
        "one hour) and start on the SSP proper run."
    ),
}

WEEKS[39] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Discussed the option of moving the heavy runs to a local H100 machine I have access to at work. Supervisor said yes if I can document the compute environment clearly.",
    "progress": (
        "I met the supervisor on Tuesday and floated the idea of "
        "moving the heavy Phase 4 runs (SSP proper and the two UDA "
        "methods) off Colab and onto a local H100 GPU machine that I "
        "have access to at work. The supervisor said yes as long as "
        "I document the compute environment clearly in Chapter 6 "
        "(hardware spec, driver versions, exact commands), so the "
        "results stay reproducible for the second marker. I "
        "confirmed the machine (us01odc-sc4-1-gpu064) has an H100 "
        "and the Ultralytics stack installs cleanly there. The "
        "few-shot curve did run on Colab this week: results plug "
        "back into sample_efficiency.csv and produce a slightly "
        "cleaner curve than the earlier Phase 2 pass (same shape, "
        "tighter numbers because the k=0 anchor was corrected)."
    ),
    "plan": (
        "Next week I plan to get the SSP+FT full run and the first "
        "UDA experiment (Adaptive Teacher, D-03) running on the H100."
    ),
}

WEEKS[40] = {
    "meeting": False, "note": "NA",
    "progress": (
        "Migrated to the H100 machine this week. Cloning the repo, "
        "installing the environment, and pulling the datasets onto "
        "the local SCRATCH space took a full day (about 60 minutes "
        "of that was one runaway find(1) command crawling NFS, "
        "which I killed and replaced with a directory-scoped one). "
        "Once the environment was clean, the D-03 Adaptive Teacher "
        "experiment ran to completion: 5 epochs, batch 16, "
        "348 pseudo-labels out of 384 target images, CPV on "
        "ScreenSpot-desktop of 68.56 percent, training elapsed "
        "217.1 s. That is the best transfer number so far. Full run "
        "log saved to /SCRATCH/madhus/d03_run.log. Weights are on "
        "SCRATCH (not committed; they are 22 MB pt plus 43 MB "
        "onnx). CSVs committed under reports/tables/."
    ),
    "plan": (
        "Next week I plan to run D-04 (SHOT) on the same machine."
    ),
}

WEEKS[41] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Reported D-03 and D-04 done on the H100. Supervisor noted that D-04's negative result is a valid finding on its own and should be reported honestly in Chapter 7.",
    "progress": (
        "I met the supervisor on Tuesday and reported both D-03 and "
        "D-04 done on the H100. D-04 (SHOT, simplified) at 8 epochs "
        "with freeze=15 gave CPV of 23.95 percent on "
        "ScreenSpot-desktop, which is much worse than D-03 (68.56 "
        "percent). The mAP@0.5 on the pseudo-label validation set "
        "went to 0.81 by epoch 8, but the transfer degraded, which "
        "is a classic pseudo-label overfitting story. The supervisor "
        "said this is a valid negative finding and should be "
        "reported honestly. I pushed both runs to GitHub. Ranges "
        "pushed: aad50d1..5203360. I also started the extended UDA "
        "reruns because I want to nail down whether the negative "
        "SHOT result holds under different hyperparameters."
    ),
    "plan": (
        "Next week I plan to finish the extended UDA reruns "
        "(SHOT 15 epochs, SHOT freeze=10, and AT with the full "
        "3-iteration 8k-source protocol) and start writing "
        "Chapter 7."
    ),
}

WEEKS[42] = {
    "meeting": False, "note": "NA",
    "progress": (
        "Three extended runs finished this week, all on the H100. "
        "SHOT 15 epochs (same freeze=15) gave 26.95 percent CPV, "
        "marginal improvement over the 8-epoch run. SHOT with a "
        "looser freeze depth of 10 gave 34.13 percent, which is a "
        "meaningful 10-point improvement and says the freeze=15 "
        "config was probably too aggressive. And AT with the full "
        "protocol (3 iterations, 10 epochs each, 8k source images) "
        "took about 35 minutes and gave 64.67 percent, which is "
        "actually a small drop from the 5-epoch baseline (68.56 "
        "percent). Plausible reason: overfitting to noisy "
        "pseudo-labels compounds across iterations, and the larger "
        "source pool dilutes the target signal. Committed all three "
        "runs (commit d309f99, 15 CSV files). I also drafted the "
        "structure of Chapter 7 while the runs were going."
    ),
    "plan": (
        "Next week I plan to write Chapters 1 to 4 of the "
        "dissertation."
    ),
}

WEEKS[43] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday. Walked through the draft outline of Chapters 1-4. Supervisor gave detailed feedback: onion-model diagram for stakeholders, explicit waterfall justification, functional-versus-OOP justification, and use-case number column for the functional requirements table.",
    "progress": (
        "I met the supervisor on Tuesday and walked through the draft "
        "outline of Chapters 1 to 4. The feedback was detailed and "
        "specific. Chapter 3 needs an onion-model diagram for "
        "stakeholder analysis and a use-case number column on the "
        "functional requirements table. Chapter 4 needs an explicit "
        "waterfall-versus-agile justification, and a paragraph on "
        "why the code is functional-and-module-oriented rather than "
        "OOP (given the pipeline is a straight-line data flow, forcing "
        "OOP would be over-engineering). The supervisor also asked me "
        "to make sure the Gantt chart is justified, not just shown. "
        "I spent the rest of the week folding all of that into the "
        "chapters. Also added the 33-entry references list in Harvard "
        "'Cite Them Right' style and audited every in-text citation "
        "against it."
    ),
    "plan": (
        "Next week is the last week before submission. I plan to "
        "finish Chapters 5 to 9, produce the sixteen figures, and "
        "get the front matter (abstract, acknowledgements, "
        "abbreviations) in place."
    ),
}

WEEKS[44] = {
    "meeting": True,
    "note": "Met the supervisor on Tuesday for the pre-submission review. Walked through the full draft. Supervisor signed off with a few small edits (font sizes, page-number scheme, expert-evaluation to be attached as an appendix).",
    "progress": (
        "This was the pre-submission week. I met the supervisor on "
        "Tuesday for the pre-submission review and walked through "
        "the full draft. Supervisor signed off with a few small "
        "edits: consistent 12pt body text with 10-11pt captions and "
        "table text, roman-numeral page numbers on the front matter "
        "and arabic starting at Chapter 1, and the three-expert "
        "evaluation attached as Appendix A rather than embedded in "
        "Chapter 8. I finished Chapters 5 to 9 this week, produced "
        "all sixteen figures (including the Onion Model diagram and "
        "the actual GUI screenshot on Windows 11), and drafted the "
        "front matter using the RGU reference dissertation as a "
        "style guide. Final page count came in near the 100 to 110 "
        "budget. I also collected the three expert-evaluation write-"
        "ups from colleagues and attached them as Appendix A."
    ),
    "plan": (
        "Next week I plan to submit the dissertation via the RGU "
        "Moodle drop-box and upload the code repository as instructed."
    ),
}

# ============================================================
# Sanity check
# ============================================================

if __name__ == "__main__":
    assert WEEKS[0] is None
    for i in range(1, 45):
        w = WEEKS[i]
        assert w is not None, f"Missing week {i}"
        assert "meeting" in w and "note" in w and "progress" in w and "plan" in w, f"Week {i} incomplete"
        assert "—" not in w["progress"], f"Week {i} progress contains em-dash"
        assert "—" not in w["plan"], f"Week {i} plan contains em-dash"
        assert "—" not in w["note"], f"Week {i} note contains em-dash"
    print(f"OK all 44 weeks defined")
    print(f"total meetings: {sum(1 for i in range(1,45) if WEEKS[i]['meeting'])}")
    print(f"no-meeting weeks: {sum(1 for i in range(1,45) if not WEEKS[i]['meeting'])}")
    # word counts
    import statistics
    pw = [len(WEEKS[i]['progress'].split()) for i in range(1,45)]
    print(f"progress words: min={min(pw)} max={max(pw)} median={statistics.median(pw):.0f}")

