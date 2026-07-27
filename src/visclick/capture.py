"""Screenshot capture (multi-monitor) via mss + Windows DPI awareness.

Multi-monitor reality on Windows:
- ``mss.monitors[0]`` is the **virtual screen** (bounding box of all monitors).
- ``mss.monitors[1..N]`` are individual physical monitors. The order is
  whatever Win32 ``EnumDisplayMonitors`` returns, which is **not guaranteed
  to put Windows' "primary display" first**.
- ``pyautogui.size()`` returns only the Windows primary monitor's size.
- ``pyautogui.click(x, y)`` operates in **virtual screen coordinates**, where
  the Windows primary monitor's top-left is (0, 0). Other monitors live at
  positive or negative offsets depending on Display Settings arrangement.

Implications:
- A screenshot of ``mss.monitors[2]`` shows pixels in the range (0..W, 0..H)
  *of that monitor's framebuffer*. Detection boxes from that screenshot are
  in monitor-local coordinates. To click them, you must add the monitor's
  ``(left, top)`` virtual-desktop offset before passing to pyautogui.
- ``grab()`` returns ``(img, left, top)`` so callers always have the offset.
"""
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


def list_monitors() -> list[dict]:
    """Return the list of monitors as mss reports them.

    Each entry is a dict with keys ``index, top, left, width, height``.
    Index 0 is the virtual screen; 1..N are individual monitors.
    """
    out: list[dict] = []
    with mss.mss() as sct:
        for i, m in enumerate(sct.monitors):
            out.append({
                "index": i,
                "top": int(m["top"]),
                "left": int(m["left"]),
                "width": int(m["width"]),
                "height": int(m["height"]),
            })
    return out


def primary_monitor() -> dict:
    """Return mss monitor[1] dict (first physical screen as mss enumerates)."""
    with mss.mss() as sct:
        return dict(sct.monitors[1])


def find_pyautogui_primary() -> int:
    """Return the mss monitor index whose size matches pyautogui's primary.

    pyautogui.size() reports only the Windows primary monitor — that is the
    monitor where (0, 0) lives in pyautogui's coordinate system. Capturing
    that same monitor with mss is the simplest setup: no offset needed for
    clicks. Returns 1 if no match (then mss[1] *is* effectively primary).
    """
    try:
        import pyautogui
        pa_w, pa_h = pyautogui.size()
    except Exception:
        return 1
    pa_w, pa_h = int(pa_w), int(pa_h)
    with mss.mss() as sct:
        for i, m in enumerate(sct.monitors):
            if i == 0:
                continue
            if int(m["width"]) == pa_w and int(m["height"]) == pa_h \
               and int(m["top"]) == 0 and int(m["left"]) == 0:
                return i
    return 1


def grab(monitor_index: int = 1) -> Tuple[np.ndarray, int, int]:
    """Capture a monitor. Return ``(img_rgb, left, top)``.

    monitor_index=0 → all monitors stitched (virtual screen)
    monitor_index=1 → mss's first monitor
    monitor_index≥2 → other monitors (run ``test_screen.py --list-monitors``)
    """
    with mss.mss() as sct:
        if monitor_index < 0 or monitor_index >= len(sct.monitors):
            raise IndexError(
                f"monitor_index={monitor_index} out of range; "
                f"have {len(sct.monitors)} monitors (incl. virtual at 0)."
            )
        m = sct.monitors[monitor_index]
        bgra = np.array(sct.grab(m))
        left = int(m["left"])
        top = int(m["top"])
    img = bgra[:, :, :3][:, :, ::-1].copy()
    return img, left, top


def save_screenshot(
    path: str | Path, monitor_index: int = 1
) -> Tuple[int, int, int, int, str]:
    """Capture and save a screenshot. Return ``(width, height, left, top, abs_path)``.

    ``left, top`` are the captured monitor's offset on the virtual desktop
    — needed by callers that want to click at coordinates derived from this
    screenshot.
    """
    img, left, top = grab(monitor_index)
    h, w = img.shape[:2]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img).save(path)
    return w, h, left, top, str(path.resolve())
