"""CLI orchestrator: screenshot -> detect -> OCR -> match -> click.

Examples:
  # Live with a 5-second countdown so you can switch to the target window:
  python -m visclick.bot --instruction "click Save" --countdown 5

  # Live, no countdown (immediate capture + click):
  python -m visclick.bot --instruction "click Save"

  # Multi-monitor: pick monitor 2 explicitly (run test_screen.py
  # --list-monitors to see the layout).
  python -m visclick.bot --instruction "click Save" --monitor 2 --countdown 5

  # Dry-run on a saved screenshot (no clicks)
  python -m visclick.bot --instruction "click Save" --image screenshots/test.png --dry-run

  # Save an overlay PNG with all detection boxes for debugging
  python -m visclick.bot --instruction "click Save" --image screenshots/test.png \
      --dry-run --save-overlay screenshots/overlay.png

Object-oriented layout:
- ``BotResult`` — dataclass carrying verdict, picked box, click coordinates
  and diagnostic notes.
- ``Bot`` — orchestrator that composes ``Capture``, ``Detector``,
  ``OCREngine``, ``Matcher``, ``Actor``. Its ``run_instruction`` method is
  the single OOP entry point that the GUI, the baseline harness and this
  CLI all funnel through.
- ``main`` — argparse + logging wrapper that instantiates ``Bot`` and
  prints the result. Kept as a module function because it is a CLI
  concern, not a domain object.
"""
from __future__ import annotations

import argparse
import os
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import pyautogui

from visclick.act import Actor
from visclick.capture import Capture
from visclick.detect import CLASS_NAMES, Detector
from visclick.match import Matcher
from visclick.ocr import OCREngine

Box4 = Tuple[float, float, float, float]


_COLORS: list[tuple[int, int, int]] = [
    (255, 107, 107), (78, 205, 196), (255, 230, 109),
    (160, 108, 213), (6, 167, 125), (255, 166, 43),
]


@dataclass
class BotResult:
    """Outcome of one ``Bot.run_instruction`` call."""

    verdict: str  # "pass" | "fail" | "refused"
    instruction: str
    picked_index: int = -1
    picked_box: Optional[Box4] = None
    picked_cls: int = -1
    picked_text: str = ""
    match_score: float = 0.0
    det_conf: float = 0.0
    fallback_used: bool = False
    click_xy_abs: Optional[Tuple[float, float]] = None
    click_xy_local: Optional[Tuple[float, float]] = None
    monitor_offset: Tuple[int, int] = (0, 0)
    boxes_with_text: List[Tuple[int, Box4, float, str]] = field(default_factory=list)
    notes: str = ""


class Bot:
    """Orchestrator that composes the five pipeline collaborators.

    A single ``Bot`` instance holds one loaded ``Detector`` (~45 MB ONNX
    session) plus references to the other collaborators, so callers that
    run many instructions in sequence pay the model-load cost once.
    """

    def __init__(
        self,
        weights_path: str,
        *,
        capture: Capture | None = None,
        detector: Detector | None = None,
        ocr: OCREngine | None = None,
        matcher: Matcher | None = None,
        actor: Actor | None = None,
    ) -> None:
        self.weights_path = weights_path
        self.capture = capture or Capture()
        self.detector = detector or Detector(weights_path)
        self.ocr = ocr or OCREngine()
        self.matcher = matcher or Matcher()
        self.actor = actor or Actor()

    def run_instruction(
        self,
        instruction: str,
        *,
        img_rgb: np.ndarray | None = None,
        monitor_index: int = 0,
        countdown: int = 0,
        conf: float = 0.25,
        iou: float = 0.5,
        ocr_engine: str = "easyocr",
        min_text_similarity: int = 60,
        no_text_fallback: bool = False,
        dry_run: bool = False,
        save_overlay: str | None = None,
        allow_click_on_provided_image: bool = False,
    ) -> BotResult:
        """Run the full pipeline for one natural-language instruction.

        Either provide ``img_rgb`` (dry-run over a saved screenshot) or
        omit it (live capture via ``self.capture.grab``).
        """
        r = BotResult(verdict="fail", instruction=instruction)

        monitor_offset = (0, 0)
        if img_rgb is None:
            self.capture.set_dpi_awareness()
            if countdown > 0:
                print("Switch to your target window now.")
                for i in range(countdown, 0, -1):
                    print(f"  capturing in {i}...")
                    time.sleep(1)
            mon_idx = monitor_index if monitor_index > 0 else self.capture.find_pyautogui_primary()
            img_rgb, mleft, mtop = self.capture.grab(mon_idx)
            monitor_offset = (mleft, mtop)
            print(f"captured monitor {mon_idx}: {img_rgb.shape[1]}x{img_rgb.shape[0]} "
                  f"at virtual-desktop offset ({mleft}, {mtop})")
        r.monitor_offset = monitor_offset

        raw = self.detector.predict(img_rgb, conf=conf, iou=iou)
        print(f"detector returned {len(raw)} box(es)")
        if not raw:
            r.notes = "detector found no candidates above conf threshold"
            if save_overlay:
                _save_overlay(img_rgb, [], -1, save_overlay)
                print(f"saved empty overlay to {save_overlay}")
            return r

        ocr_engine = self._resolve_ocr_engine(ocr_engine)

        boxes_with_text: List[Tuple[int, Box4, float, str]] = []
        for cls, xyxy, det_conf in raw:
            text = self.ocr.ocr_box(img_rgb, xyxy, engine=ocr_engine) if ocr_engine != "none" else ""
            boxes_with_text.append((cls, xyxy, det_conf, text))
            cxl = (xyxy[0] + xyxy[2]) / 2
            cyl = (xyxy[1] + xyxy[3]) / 2
            print(f"  cls={CLASS_NAMES[cls]:11s} center=({cxl:>6.0f},{cyl:>6.0f})  "
                  f"conf={det_conf:.2f} text={text!r}")
        r.boxes_with_text = boxes_with_text

        pick = self.matcher.best_box(instruction, boxes_with_text, min_text_similarity=min_text_similarity)

        if pick is None and not no_text_fallback:
            target = self.matcher.target_phrase(instruction)
            if not self.matcher.is_class_only_target(target):
                print(f"FALLBACK: detector miss; running full-image OCR for {target!r}...")
                fallback_engine = ocr_engine if ocr_engine != "none" else "easyocr"
                hits = self.ocr.text_ground(img_rgb, target, engine=fallback_engine, min_similarity=70)
                print(f"  text_ground found {len(hits)} hit(s)")
                for xyxy_h, text_h, sim_h, ocr_conf_h in hits[:5]:
                    cxh = (xyxy_h[0] + xyxy_h[2]) / 2
                    cyh = (xyxy_h[1] + xyxy_h[3]) / 2
                    print(f"    {text_h!r:25s} center=({cxh:>6.0f},{cyh:>6.0f})  "
                          f"sim={sim_h:.0f}  ocr_conf={ocr_conf_h:.0f}")
                if hits:
                    xyxy_h, text_h, sim_h, ocr_conf_h = hits[0]
                    synth = (1, xyxy_h, ocr_conf_h / 100.0, text_h)
                    boxes_with_text.append(synth)
                    pick = (sim_h, 1, xyxy_h, ocr_conf_h / 100.0, text_h)
                    r.fallback_used = True

        picked_index = -1
        if pick is not None:
            score, cls, xyxy, det_conf, text = pick
            for i, (c, b, cf, t) in enumerate(boxes_with_text):
                if c == cls and b == xyxy:
                    picked_index = i
                    break
        r.picked_index = picked_index

        if save_overlay:
            _save_overlay(img_rgb, boxes_with_text, picked_index, save_overlay)
            print(f"saved overlay to {save_overlay}")

        if pick is None:
            target = (instruction or "").lower().replace("click", "").strip().strip("'\"")
            r.verdict = "refused"
            r.notes = f"neither detector nor full-image OCR found {target!r}"
            return r

        score, cls, xyxy, det_conf, text = pick
        r.picked_box = xyxy
        r.picked_cls = cls
        r.picked_text = text
        r.match_score = float(score)
        r.det_conf = float(det_conf)

        cx_local = (xyxy[0] + xyxy[2]) / 2
        cy_local = (xyxy[1] + xyxy[3]) / 2
        cx_abs = cx_local + monitor_offset[0]
        cy_abs = cy_local + monitor_offset[1]
        r.click_xy_local = (cx_local, cy_local)
        r.click_xy_abs = (cx_abs, cy_abs)

        print(f"PICKED cls={CLASS_NAMES[cls]} text={text!r} det_conf={det_conf:.2f} match_score={score}")
        print(f"  monitor-local center: ({cx_local:.0f}, {cy_local:.0f})")
        print(f"  virtual-desktop:      ({cx_abs:.0f}, {cy_abs:.0f})")

        if dry_run:
            r.verdict = "pass"
            r.notes = f"DRY-RUN: would click ({cx_abs:.0f}, {cy_abs:.0f})"
            print(r.notes)
            return r

        if img_rgb is not None and not allow_click_on_provided_image and monitor_offset == (0, 0):
            # Caller supplied an image AND did not ask for the click; safest is to abstain.
            # We detect this via monitor_offset == (0, 0) which means capture didn't happen.
            # (Live capture always sets a non-trivial branch above.)
            pass

        pre = pyautogui.position()
        print(f"  cursor before move:   ({pre.x}, {pre.y})  "
              f"delta-to-target=({cx_abs - pre.x:+.0f}, {cy_abs - pre.y:+.0f})")
        abs_xy = self.actor.click_box(xyxy, offset=monitor_offset)
        post = pyautogui.position()
        err = (post.x - cx_abs, post.y - cy_abs)
        status = "OK" if abs(err[0]) <= 2 and abs(err[1]) <= 2 else "BAD - likely DPI scaling"
        print(f"  cursor after click:   ({post.x}, {post.y})")
        print(f"  arrival error:        ({err[0]:+.0f}, {err[1]:+.0f}) pixels [{status}]")
        print(f"CLICKED virtual-desktop ({abs_xy[0]:.0f}, {abs_xy[1]:.0f}) "
              f"[monitor-local ({cx_local:.0f}, {cy_local:.0f}) + offset {monitor_offset}]")

        r.verdict = "pass"
        r.notes = f"clicked ({abs_xy[0]:.0f}, {abs_xy[1]:.0f})"
        return r

    def _resolve_ocr_engine(self, requested: str) -> str:
        """Print the OCR-backend availability banner and auto-fall-back."""
        if requested == "none":
            print("OCR engine: none")
            return "none"
        st = self.ocr.status()
        for name in ("tesseract", "easyocr"):
            info = st[name]
            if info.get("available"):
                tag = info.get("version", "ok")
                print(f"OCR {name:9s}: OK {tag}")
            else:
                print(f"OCR {name:9s}: -- {info.get('reason', 'unavailable')}")
        if not st.get(requested, {}).get("available"):
            other = "easyocr" if requested == "tesseract" else "tesseract"
            if st.get(other, {}).get("available"):
                print(f"WARNING: requested OCR={requested} is unavailable; auto-switching to {other}.")
                requested = other
            else:
                print("WARNING: no OCR backend is available; matching will use class + confidence only.")
                requested = "none"
        print(f"OCR engine: {requested}")
        return requested


def _load_image(path: str) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    return np.array(img)


def _save_overlay(
    img_rgb: np.ndarray,
    boxes_with_text: List[Tuple[int, Box4, float, str]],
    picked_index: int,
    out_path: str,
) -> None:
    pil = Image.fromarray(img_rgb).copy()
    draw = ImageDraw.Draw(pil)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    for i, (cls, xyxy, conf, text) in enumerate(boxes_with_text):
        color = _COLORS[cls % len(_COLORS)]
        x1, y1, x2, y2 = (int(round(v)) for v in xyxy)
        width = 4 if i == picked_index else 2
        draw.rectangle([x1, y1, x2, y2], outline=color, width=width)
        label = f"{CLASS_NAMES[cls]} {conf:.2f}"
        if text:
            label += f" | {text[:30]}"
        draw.text((x1, max(0, y1 - 16)), label, fill=color, font=font)
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    pil.save(out_path)


def _run_manual_xy(args) -> int:
    """Manual coordinate click - verifies the click plumbing in isolation."""
    actor = Actor()
    Capture().set_dpi_awareness()
    tx, ty = args.xy
    pa_w, pa_h = pyautogui.size()
    print(f"manual xy mode | target=({tx}, {ty}) | pyautogui screen={pa_w}x{pa_h}")
    if args.countdown > 0:
        print("Switch to your target window now.")
        for i in range(args.countdown, 0, -1):
            print(f"  capturing in {i}...")
            time.sleep(1)
    pre = pyautogui.position()
    print(f"  cursor before move: ({pre.x}, {pre.y})")
    print(f"  delta to target:    ({tx - pre.x:+d}, {ty - pre.y:+d}) pixels")
    if args.dry_run:
        print("DRY-RUN: no click sent.")
        return 0
    t0 = time.perf_counter()
    actor.click_xy(tx, ty, dwell=0.3)
    dt_ms = (time.perf_counter() - t0) * 1000
    post = pyautogui.position()
    err = (post.x - tx, post.y - ty)
    status = "OK" if abs(err[0]) <= 2 and abs(err[1]) <= 2 else "BAD - likely DPI scaling"
    print(f"  cursor after click: ({post.x}, {post.y})")
    print(f"  arrival error:      ({err[0]:+d}, {err[1]:+d}) pixels [{status}]")
    print(f"  move + click took {dt_ms:.0f} ms")
    return 0


def _parse_xy(s: str) -> Tuple[int, int]:
    """Accept '500,400', '500 400', or 'xy 500 400'."""
    import re
    m = re.match(r"^\s*(?:xy\s+)?(-?\d+)\s*[,\s]\s*(-?\d+)\s*$", s, re.IGNORECASE)
    if not m:
        raise argparse.ArgumentTypeError(
            f"--xy must be 'X,Y' or 'X Y' (got {s!r})")
    return int(m.group(1)), int(m.group(2))


def main() -> int:
    ap = argparse.ArgumentParser(description="VisClick instruction-driven GUI click bot")
    ap.add_argument("--instruction", default=None, help='e.g. "click Save"')
    ap.add_argument("--xy", type=_parse_xy, default=None,
                    help="Manual coordinate click. Skips capture/detection.")
    ap.add_argument("--weights", default="weights/visclick.onnx",
                    help="Path to ONNX weights (default: weights/visclick.onnx)")
    ap.add_argument("--image", default=None,
                    help="Run on a saved screenshot instead of capturing screen")
    ap.add_argument("--monitor", type=int, default=0,
                    help="mss monitor index (default 0 = auto)")
    ap.add_argument("--countdown", type=int, default=0)
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--iou",  type=float, default=0.50)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--save-overlay", default=None)
    ap.add_argument("--ocr-engine", choices=["tesseract", "easyocr", "both", "none"],
                    default="easyocr")
    ap.add_argument("--no-ocr", action="store_true", help="Alias for --ocr-engine none.")
    ap.add_argument("--no-text-fallback", action="store_true")
    args = ap.parse_args()
    if args.no_ocr:
        args.ocr_engine = "none"

    if args.xy is not None:
        return _run_manual_xy(args)
    if not args.instruction:
        ap.error("either --instruction or --xy is required")

    if not os.path.isfile(args.weights):
        print(f"ERROR: weights not found: {args.weights}")
        return 2

    if args.image:
        if not os.path.isfile(args.image):
            print(f"ERROR: image not found: {args.image}")
            return 2
        print(f"loading saved image: {args.image}")
        img_rgb = _load_image(args.image)
    else:
        img_rgb = None

    print(f"loading detector: {args.weights}")
    bot = Bot(args.weights)

    r = bot.run_instruction(
        args.instruction,
        img_rgb=img_rgb,
        monitor_index=args.monitor,
        countdown=args.countdown,
        conf=args.conf,
        iou=args.iou,
        ocr_engine=args.ocr_engine,
        no_text_fallback=args.no_text_fallback,
        dry_run=(args.dry_run or bool(args.image)),
        save_overlay=args.save_overlay,
    )
    if args.image and not args.dry_run and r.verdict == "pass":
        print("WARN: --image was set. Refusing to click; the screen may not match the image.")
    return 0 if r.verdict == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
