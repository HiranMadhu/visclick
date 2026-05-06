"""Shared utilities for the Phase 1.C classical baselines.

Each baseline (template / OCR-only / pywinauto) implements the same
``predict(image_rgb, instruction, **task) -> BaselineResult`` API, so the
runner can call all three on the same captured screenshot and produce a
side-by-side comparison.

A *result* always contains:
- ``found``: did the baseline pick anything at all?
- ``xy``: the absolute screen coordinate it would click (already includes
  monitor offset, so it is directly usable by ``pyautogui.click``).
- ``confidence``: method-specific score in 0..1 — for template matching,
  this is ``cv2.matchTemplate`` correlation; for OCR, it is the fuzzy
  similarity / 100; for pywinauto, it is 1.0 on hit, 0.0 on miss.
- ``elapsed_ms``: wall-clock time of just the predict call.
- ``notes``: short free-text describing why it matched (or why it did not).

The runner judges *correctness* separately. A baseline returning
``found=False`` is the right answer for tasks with ``is_negative=True``
(graceful refusal).
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


# ---------- result type ----------

@dataclass
class BaselineResult:
    method: str
    found: bool
    xy: Optional[Tuple[int, int]] = None
    confidence: float = 0.0
    elapsed_ms: float = 0.0
    notes: str = ""
    bbox: Optional[Tuple[int, int, int, int]] = None
    # for the runner to attach the user's verdict (kept here so it serialises
    # together with the rest of the result):
    verdict: Optional[str] = None  # "pass" | "fail" | "skip"

    def to_csv_row(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.xy is not None:
            d["xy"] = f"{self.xy[0]},{self.xy[1]}"
        if self.bbox is not None:
            x1, y1, x2, y2 = self.bbox
            d["bbox"] = f"{x1},{y1},{x2},{y2}"
        return d


# ---------- screenshot helpers ----------

def add_repo_to_path() -> Path:
    """Make ``import visclick.*`` work even when scripts/ is run directly."""
    here = Path(__file__).resolve().parent.parent
    src = here / "src"
    if src.is_dir() and str(src) not in sys.path:
        sys.path.insert(0, str(src))
    return here


def load_image(image_path: Optional[str], monitor: int = 1
               ) -> Tuple[np.ndarray, Tuple[int, int]]:
    """Return (RGB image, (left, top) virtual-desktop offset).

    If ``image_path`` is given, load from disk and assume offset (0, 0)
    (offline reproduction). Otherwise capture the requested monitor live.
    """
    if image_path:
        from PIL import Image
        img = np.array(Image.open(image_path).convert("RGB"))
        return img, (0, 0)

    add_repo_to_path()
    from visclick.capture import grab, set_dpi_awareness
    set_dpi_awareness()
    img, left, top = grab(monitor)
    return img, (int(left), int(top))


# ---------- instruction parsing ----------

def parse_target_words(instruction: str) -> List[str]:
    """Extract the keyword(s) from a natural-language instruction.

    "click Save"           -> ["save"]
    "open File menu"       -> ["file"]   (drops the verb "open" and the noun "menu")
    "toggle Use system proxy" -> ["use", "system", "proxy"]
    """
    if not instruction:
        return []
    drop = {
        "click", "tap", "press", "hit", "open", "close", "toggle", "the",
        "a", "an", "this", "that", "on", "in", "at", "menu", "button",
        "icon", "checkbox", "tab", "field", "box", "bar",
    }
    words = [w.strip(".,;:!?\"'()") for w in instruction.split()]
    keep = [w for w in words if w and w.lower() not in drop]
    return [w.lower() for w in keep]


# ---------- CLI scaffolding shared by every baseline ----------

def baseline_argparser(method: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=f"baseline_{method}",
        description=f"Phase 1.C — {method} baseline. Predicts (x, y) for a "
                    f"natural-language instruction without using the YOLO "
                    f"detector.")
    p.add_argument("--instruction", required=True,
                   help="natural-language instruction, e.g. 'click Save'.")
    p.add_argument("--image", default=None,
                   help="optional path to a saved screenshot (PNG). If omitted, "
                        "captures monitor --monitor live.")
    p.add_argument("--monitor", type=int, default=None,
                   help="mss monitor index (1..N). Default: pyautogui's primary.")
    p.add_argument("--target-text", default="",
                   help="OCR keyword override (defaults to parsed from instruction).")
    p.add_argument("--target-template", default="",
                   help="template-baseline reference filename in samples/templates/.")
    p.add_argument("--target-uia-name", default="",
                   help="pywinauto baseline UIA Name override.")
    p.add_argument("--target-uia-role", default="",
                   help="pywinauto baseline UIA control type override.")
    p.add_argument("--dry-run", action="store_true", default=True,
                   help="default: do NOT actually click. Pass --click to click.")
    p.add_argument("--click", action="store_false", dest="dry_run",
                   help="actually move mouse and click after predicting.")
    return p


def autopick_monitor(monitor: Optional[int]) -> int:
    if monitor is not None:
        return monitor
    add_repo_to_path()
    try:
        from visclick.capture import find_pyautogui_primary
        return int(find_pyautogui_primary())
    except Exception:
        return 1


def maybe_click(result: BaselineResult, dry_run: bool) -> None:
    if not result.found or result.xy is None or dry_run:
        return
    add_repo_to_path()
    from visclick.act import click_xy
    x, y = result.xy
    click_xy(float(x), float(y))
    result.notes += f" [clicked @ ({x},{y})]"


def time_call(fn, *args, **kwargs) -> Tuple[Any, float]:
    t0 = time.perf_counter()
    out = fn(*args, **kwargs)
    return out, (time.perf_counter() - t0) * 1000.0


def print_result(r: BaselineResult) -> None:
    state = "FOUND" if r.found else "MISS "
    xy = f"@({r.xy[0]:>5d},{r.xy[1]:>5d})" if r.xy else "@(-----,-----)"
    print(f"  {state} {r.method:14s} {xy} conf={r.confidence:.3f} "
          f"in {r.elapsed_ms:.1f} ms  {r.notes}")
