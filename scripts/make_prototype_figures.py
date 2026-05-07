"""Phase 2.4 — emit the six prototype-evidence figures for report §8.1.

The dissertation §8.1 asks for six screenshots that together demonstrate
the end-to-end loop:

  1. proto_1_terminal.png       — terminal showing the user issuing a command
  2. proto_2_captured.png       — raw screenshot the bot grabs (no annotations)
  3. proto_3_overlay_all.png    — same screenshot with EVERY detector box drawn
  4. proto_4_picked.png         — same screenshot with ONLY the matcher's pick highlighted
  5. proto_5_after_click.png    — desktop after the click (the dialog opened, focus changed, etc.)
  6. proto_6_failure.png        — an honest failure case (e.g. T15 or T06)

Of these, **four can be derived programmatically** from artefacts already in
the repo (saved screenshots from Phase 1.C + the ONNX detector + the matcher):

  - #2 = ``samples/test_screenshots/T01.png``
  - #3 = run detector on T01.png, draw ALL boxes coloured by class
  - #4 = run the full VisClick pipeline on T01.png, draw ONLY the picked box
  - #6 = run the full pipeline on T15.png (negative case), show the false-positive

The remaining **two require fresh captures on the user's Windows
machine** — see the printed instructions at the end of this script:

  - #1 (terminal screenshot of `python -m visclick "click Save"`)
  - #5 (desktop after the bot clicks)

Usage::

    py -3 scripts/make_prototype_figures.py
    py -3 scripts/make_prototype_figures.py --task T01 --fail-task T15
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
SHOT_DIR = REPO / "samples" / "test_screenshots"
FIG_DIR = REPO / "reports" / "figures"

CLASS_COLOURS_BGR = {
    "button":      (60, 60, 255),    # red
    "text":        (60, 200, 255),   # cyan
    "text_input":  (255, 200, 0),    # blue-orange
    "icon":        (60, 220, 90),    # green
    "menu":        (200, 60, 200),   # magenta
    "checkbox":    (255, 255, 60),   # yellow
}


def _add_repo_to_path() -> None:
    src = REPO / "src"
    if src.is_dir() and str(src) not in sys.path:
        sys.path.insert(0, str(src))
    sc = REPO / "scripts"
    if sc.is_dir() and str(sc) not in sys.path:
        sys.path.insert(0, str(sc))


def _detector():
    _add_repo_to_path()
    from visclick.detect import Detector
    onnx = REPO / "weights" / "visclick.onnx"
    if not onnx.is_file():
        print(f"ERROR: weights not found at {onnx}", file=sys.stderr)
        sys.exit(2)
    return Detector(str(onnx))


def _draw_box_bgr(img_bgr: np.ndarray,
                  xyxy: Tuple[float, float, float, float],
                  colour: Tuple[int, int, int],
                  label: Optional[str],
                  thickness: int = 3) -> None:
    x1, y1, x2, y2 = (int(v) for v in xyxy)
    cv2.rectangle(img_bgr, (x1, y1), (x2, y2), colour, thickness)
    if label:
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.55
        (tw, th), _ = cv2.getTextSize(label, font, scale, 1)
        cv2.rectangle(img_bgr, (x1, max(0, y1 - th - 6)), (x1 + tw + 6, y1),
                      colour, -1)
        cv2.putText(img_bgr, label, (x1 + 3, y1 - 4), font, scale,
                    (255, 255, 255), 1, cv2.LINE_AA)


def emit_proto_2_captured(task: str) -> Path:
    src = SHOT_DIR / f"{task}.png"
    if not src.is_file():
        print(f"  SKIP proto_2: {src} not found "
              f"(run scripts/run_baselines.py first to capture it)")
        return Path()
    dst = FIG_DIR / "proto_2_captured.png"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    print(f"  proto_2_captured        <- copy of {src.name}")
    return dst


def emit_proto_3_overlay_all(task: str, detector) -> Path:
    _add_repo_to_path()
    from visclick.detect import CLASS_NAMES

    src = SHOT_DIR / f"{task}.png"
    if not src.is_file():
        print(f"  SKIP proto_3: {src} not found")
        return Path()

    img_rgb = np.array(Image.open(src).convert("RGB"))
    boxes = detector.predict(img_rgb, conf=0.15, iou=0.5)
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    for cls, xyxy, conf in boxes:
        cls_name = CLASS_NAMES[cls] if 0 <= cls < len(CLASS_NAMES) else str(cls)
        col = CLASS_COLOURS_BGR.get(cls_name, (200, 200, 200))
        _draw_box_bgr(img_bgr, xyxy, col, f"{cls_name} {conf:.2f}", thickness=2)

    dst = FIG_DIR / "proto_3_overlay_all.png"
    dst.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(dst), img_bgr)
    print(f"  proto_3_overlay_all     <- {len(boxes)} detector boxes drawn")
    return dst


def emit_proto_4_picked(task: str, instruction: str, detector) -> Path:
    """Run the full VisClick pipeline on the saved screenshot and highlight
    only the matcher's chosen box (or the text_ground fallback hit)."""
    import baseline_visclick as bvc

    src = SHOT_DIR / f"{task}.png"
    if not src.is_file():
        print(f"  SKIP proto_4: {src} not found")
        return Path()

    img_rgb = np.array(Image.open(src).convert("RGB"))
    bvc._DETECTOR = detector  # reuse already-loaded detector
    r = bvc.predict(img_rgb, instruction)

    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    if r.found and r.bbox:
        _draw_box_bgr(img_bgr, r.bbox, (60, 220, 90),
                      f"VisClick: {instruction!r}", thickness=4)
        cx, cy = r.xy if r.xy else ((r.bbox[0] + r.bbox[2]) // 2,
                                    (r.bbox[1] + r.bbox[3]) // 2)
        cv2.drawMarker(img_bgr, (int(cx), int(cy)), (60, 220, 90),
                       cv2.MARKER_CROSS, 28, 4)
        print(f"  proto_4_picked          <- highlighted {r.bbox} "
              f"(found via {'fallback' if 'fallback' in r.notes else 'detector'})")
    else:
        print(f"  WARN proto_4: VisClick did not find a target on {task} ({r.notes})")

    dst = FIG_DIR / "proto_4_picked.png"
    cv2.imwrite(str(dst), img_bgr)
    return dst


def emit_proto_6_failure(task: str, instruction: str, detector) -> Path:
    """Negative-case overlay: shows VisClick's wrong pick on a screen where
    the right answer is 'no element'."""
    import baseline_visclick as bvc

    src = SHOT_DIR / f"{task}.png"
    if not src.is_file():
        print(f"  SKIP proto_6: {src} not found")
        return Path()

    img_rgb = np.array(Image.open(src).convert("RGB"))
    bvc._DETECTOR = detector
    r = bvc.predict(img_rgb, instruction)

    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    if r.found and r.bbox:
        _draw_box_bgr(img_bgr, r.bbox, (40, 40, 220),
                      f"FALSE POSITIVE: predicted {instruction!r}", thickness=4)
        cx, cy = r.xy if r.xy else ((r.bbox[0] + r.bbox[2]) // 2,
                                    (r.bbox[1] + r.bbox[3]) // 2)
        cv2.drawMarker(img_bgr, (int(cx), int(cy)), (40, 40, 220),
                       cv2.MARKER_TILTED_CROSS, 32, 4)
        print(f"  proto_6_failure         <- VisClick wrongly clicked "
              f"{r.bbox} for {instruction!r} (negative case)")
    else:
        # The correct answer actually IS 'no element'; show a banner saying so.
        cv2.putText(img_bgr,
                    f"correct refusal: VisClick returned 'no match' for {instruction!r}",
                    (40, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (40, 200, 40), 2,
                    cv2.LINE_AA)
        print(f"  proto_6_failure         <- (negative case correctly refused; "
              f"choose a different failure task to make the figure dramatic)")

    dst = FIG_DIR / "proto_6_failure.png"
    cv2.imwrite(str(dst), img_bgr)
    return dst


def manual_capture_instructions() -> None:
    print()
    print("=" * 72)
    print("MANUAL CAPTURES YOU STILL OWE — please do these on Windows")
    print("=" * 72)
    print()
    print("[#1] proto_1_terminal.png — terminal demonstrating the command")
    print("     1. Open PowerShell.")
    print("     2. Run: cd C:\\...\\Repo\\Bot\\visclick")
    print("     3. Run: .\\.venv\\Scripts\\python.exe -m visclick")
    print("     4. In the GUI, type 'click Save' and press Run (Notepad Save-As open).")
    print("     5. Snipping Tool screenshot the PowerShell + GUI window together.")
    print("     6. Save as reports/figures/proto_1_terminal.png")
    print()
    print("[#5] proto_5_after_click.png — desktop AFTER the bot's click")
    print("     1. Set up Notepad with an unsaved 'Hello World' (so 'Save As'")
    print("        opens a dialog).")
    print("     2. Run: .\\.venv\\Scripts\\python.exe -m visclick")
    print("     3. Issue 'click Save'. Watch the cursor jump and click.")
    print("     4. Immediately Snipping-Tool the resulting Save-As dialog")
    print("        with focus.")
    print("     5. Save as reports/figures/proto_5_after_click.png")
    print()
    print("Both PNGs should be ~1920x1080 or smaller. Commit them with the")
    print("message 'phase2.4: prototype screenshots #1 and #5'.")
    print()


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--task", default="T01",
                   help="task id whose saved screenshot drives proto_2/3/4 "
                        "(default: T01).")
    p.add_argument("--instruction", default=None,
                   help="instruction for proto_4 picked element. "
                        "Default: read from tasks/T01_T20.json for --task.")
    p.add_argument("--fail-task", default="T15",
                   help="task id whose screenshot drives proto_6 (default: "
                        "T15, the negative-case false positive).")
    p.add_argument("--fail-instruction", default=None,
                   help="instruction for proto_6 failure. Default: read from "
                        "tasks/T01_T20.json for --fail-task.")
    args = p.parse_args(argv)

    # Resolve instructions from tasks/T01_T20.json if not provided.
    if args.instruction is None or args.fail_instruction is None:
        import json
        tj = json.loads((REPO / "tasks" / "T01_T20.json").read_text())
        task_list = tj["tasks"] if isinstance(tj, dict) and "tasks" in tj else tj
        by_id = {t["id"]: t for t in task_list}
        if args.instruction is None:
            args.instruction = by_id[args.task]["instruction"]
        if args.fail_instruction is None:
            args.fail_instruction = by_id[args.fail_task]["instruction"]

    print(f"Phase 2.4 — generating prototype figures into "
          f"{FIG_DIR.relative_to(REPO)}")
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n[derived from {args.task} / instruction={args.instruction!r}]")
    emit_proto_2_captured(args.task)
    det = _detector()
    emit_proto_3_overlay_all(args.task, det)
    emit_proto_4_picked(args.task, args.instruction, det)

    print(f"\n[derived from {args.fail_task} / instruction={args.fail_instruction!r}]")
    emit_proto_6_failure(args.fail_task, args.fail_instruction, det)

    manual_capture_instructions()
    return 0


if __name__ == "__main__":
    sys.exit(main())
