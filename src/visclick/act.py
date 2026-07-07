"""Send OS-level mouse events (PyAutoGUI). Click is a single OS call;
the surrounding work is DPI handling, multi-monitor offset, and a small
dwell so the OS has time to register a hover before the click.

Multi-monitor: pyautogui's coordinate system is the **virtual desktop**
(top-left of the Windows primary monitor is (0, 0)). If you took a
screenshot of monitor N at offset ``(left, top)``, every detection box
from that screenshot is in monitor-local coords. Pass ``offset=(left, top)``
to ``click_box`` so the actual click hits the right pixel.

Object-oriented layout:
- ``Actor`` encapsulates the pyautogui configuration (FAILSAFE, PAUSE)
  and the click methods. State kept per-instance so a test harness can
  spawn an Actor with FAILSAFE off without leaking that into the global
  module.
- ``screen_size``, ``click_xy``, ``click_box`` remain as module-level
  delegates so every existing caller keeps working.
"""
from __future__ import annotations

import time
from typing import Tuple

import pyautogui


class Actor:
    """Facade over the click / move primitives."""

    def __init__(self, failsafe: bool = True, pause: float = 0.05) -> None:
        pyautogui.FAILSAFE = failsafe
        pyautogui.PAUSE = pause
        self.failsafe = failsafe
        self.pause = pause

    def screen_size(self) -> Tuple[int, int]:
        """Return pyautogui's view of the screen as (width, height).

        Note: on a multi-monitor setup, this reports only the **Windows
        primary** monitor. ``visclick.capture.list_monitors()`` shows all
        of them.
        """
        w, h = pyautogui.size()
        return int(w), int(h)

    def click_xy(self, x: float, y: float, dwell: float = 0.2, button: str = "left") -> None:
        """Move-then-click in pyautogui's virtual-desktop coordinates."""
        pyautogui.moveTo(float(x), float(y), duration=max(0.0, float(dwell)))
        if dwell > 0:
            time.sleep(0.05)
        pyautogui.click(button=button)

    def click_box(
        self,
        xyxy: Tuple[float, float, float, float],
        offset: Tuple[int, int] = (0, 0),
        dwell: float = 0.2,
        button: str = "left",
    ) -> Tuple[float, float]:
        """Click the centre of ``xyxy`` (monitor-local) plus ``offset``
        (monitor's virtual-desktop top-left). Returns the absolute (x, y)
        actually clicked.
        """
        x1, y1, x2, y2 = xyxy
        cx = (x1 + x2) / 2 + float(offset[0])
        cy = (y1 + y2) / 2 + float(offset[1])
        self.click_xy(cx, cy, dwell=dwell, button=button)
        return cx, cy


_default = Actor()


def screen_size() -> Tuple[int, int]:
    return _default.screen_size()


def click_xy(x: float, y: float, dwell: float = 0.2, button: str = "left") -> None:
    _default.click_xy(x, y, dwell=dwell, button=button)


def click_box(
    xyxy: Tuple[float, float, float, float],
    offset: Tuple[int, int] = (0, 0),
    dwell: float = 0.2,
    button: str = "left",
) -> Tuple[float, float]:
    return _default.click_box(xyxy, offset=offset, dwell=dwell, button=button)
