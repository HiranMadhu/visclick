"""Send OS-level mouse events (PyAutoGUI)."""

from __future__ import annotations

import time
from typing import Tuple

import pyautogui

pyautogui.FAILSAFE = True


def click_xy(x: float, y: float, dwell: float = 0.2) -> None:
    pyautogui.moveTo(x, y, duration=dwell)
    pyautogui.click()


def click_box(xyxy: Tuple[float, float, float, float]) -> None:
    x1, y1, x2, y2 = xyxy
    click_xy((x1 + x2) / 2, (y1 + y2) / 2)
