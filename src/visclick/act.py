"""Send OS-level mouse events (PyAutoGUI). Click is a single OS call;
the surrounding work is DPI handling and a small dwell so the OS has time
to register a hover before the click.
"""
from __future__ import annotations

import time
from typing import Tuple

import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


def screen_size() -> Tuple[int, int]:
    """Return pyautogui's view of the screen as (width, height)."""
    w, h = pyautogui.size()
    return int(w), int(h)


def click_xy(x: float, y: float, dwell: float = 0.2, button: str = "left") -> None:
    """Move-then-click with a small dwell. Coordinates are in pyautogui logical pixels.

    On 125%/150% scaled Windows displays, call ``visclick.capture.set_dpi_awareness()``
    once at process start so the screenshot dimensions and these coordinates line up.
    """
    pyautogui.moveTo(float(x), float(y), duration=max(0.0, float(dwell)))
    if dwell > 0:
        time.sleep(0.05)
    pyautogui.click(button=button)


def click_box(xyxy: Tuple[float, float, float, float], dwell: float = 0.2) -> None:
    x1, y1, x2, y2 = xyxy
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    click_xy(cx, cy, dwell=dwell)
