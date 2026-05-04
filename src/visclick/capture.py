"""Screenshot capture (primary monitor) via mss + Windows DPI awareness."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Tuple

import mss
import numpy as np
from PIL import Image


def set_dpi_awareness() -> None:
    """Make the process per-monitor DPI aware on Windows.

    Without this call, on a 125%/150%-scaled display ``mss`` reports virtual
    (logical) pixels but ``pyautogui.click(x, y)`` expects physical pixels —
    so detected boxes and clicks disagree by 20–30%. Calling this once at
    process start makes both libs see the same pixel grid.
    No-op on non-Windows.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def primary_monitor() -> dict:
    """Return mss monitor[1] dict (primary screen, excludes virtual-screen origin)."""
    with mss.mss() as sct:
        return dict(sct.monitors[1])


def grab(monitor_index: int = 1) -> np.ndarray:
    """Return the chosen monitor as RGB uint8, shape (H, W, 3).

    monitor_index = 0 → all monitors stitched
    monitor_index = 1 → primary (default)
    monitor_index ≥ 2 → secondary screens
    """
    with mss.mss() as sct:
        m = sct.monitors[monitor_index]
        bgra = np.array(sct.grab(m))
    return bgra[:, :, :3][:, :, ::-1].copy()


def save_screenshot(path: str | Path, monitor_index: int = 1) -> Tuple[int, int, str]:
    """Capture and save a screenshot. Returns (width, height, abs_path)."""
    img = grab(monitor_index)
    h, w = img.shape[:2]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img).save(path)
    return w, h, str(path.resolve())
