"""Screenshot test — verifies the capture layer in isolation.

Usage:
    python scripts/test_screen.py
    python scripts/test_screen.py --list-monitors
    python scripts/test_screen.py --out screenshots/foo.png --monitor 2

What this proves (when it works):
1. mss is installed and can read the framebuffer.
2. On a single-monitor setup: captured image dimensions equal pyautogui.size().
3. On a multi-monitor setup: prints all monitors and tells you which one to
   pass with ``--monitor N`` (or to ``visclick.bot --monitor N``) so that
   click coordinates align with the screenshot.

The output directory ``screenshots/`` is created if missing.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from visclick.act import screen_size  # noqa: E402
from visclick.capture import (  # noqa: E402
    find_pyautogui_primary,
    list_monitors,
    save_screenshot,
    set_dpi_awareness,
)


def _print_monitors(mons: list[dict], pa_w: int, pa_h: int, primary_idx: int) -> None:
    print("Monitors (mss):")
    for m in mons:
        i = m["index"]
        if i == 0:
            tag = "virtual-screen (all monitors stitched)"
        elif i == primary_idx:
            tag = "→ MATCHES pyautogui primary; default capture target"
        else:
            tag = "secondary (use --monitor {} to capture)".format(i)
        print(f"  [{i}] {m['width']:>5d} x {m['height']:<5d}  "
              f"at ({m['left']:>+6d}, {m['top']:>+6d})  {tag}")
    print(f"pyautogui primary: {pa_w} x {pa_h}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Screenshot test")
    ap.add_argument("--out", default="screenshots/test_screen.png")
    ap.add_argument("--monitor", type=int, default=None,
                    help="mss monitor index (0=virtual, 1=first, 2+=others). "
                         "Default: auto-pick the monitor whose size matches "
                         "pyautogui's primary.")
    ap.add_argument("--list-monitors", action="store_true",
                    help="Just print the monitor layout and exit.")
    args = ap.parse_args()

    set_dpi_awareness()

    mons = list_monitors()
    pa_w, pa_h = screen_size()
    primary_idx = find_pyautogui_primary()

    if args.list_monitors:
        _print_monitors(mons, pa_w, pa_h, primary_idx)
        return 0

    mon_idx = args.monitor if args.monitor is not None else primary_idx
    if mon_idx < 0 or mon_idx >= len(mons):
        print(f"ERROR: --monitor {mon_idx} is out of range; valid: 0..{len(mons) - 1}")
        _print_monitors(mons, pa_w, pa_h, primary_idx)
        return 2

    _print_monitors(mons, pa_w, pa_h, primary_idx)
    print(f"capturing monitor {mon_idx} → {args.out}")

    w, h, left, top, abs_path = save_screenshot(args.out, monitor_index=mon_idx)
    print(f"saved: {abs_path}  ({w} x {h})  virtual-desktop offset: ({left}, {top})")

    captured_is_pyautogui_primary = (mon_idx == primary_idx and (left, top) == (0, 0))

    if captured_is_pyautogui_primary and (w, h) == (pa_w, pa_h):
        print("OK: captured monitor matches pyautogui primary; clicks need no offset.")
    elif captured_is_pyautogui_primary:
        print("WARNING: captured the pyautogui-primary index but resolution disagrees:")
        print(f"  mss = {w} x {h}, pyautogui = {pa_w} x {pa_h}.")
        print("This is usually Windows display scaling. Either:")
        print("  1. Set Display scaling to 100% for that monitor in Settings (recommended).")
        print("  2. Confirm visclick.capture.set_dpi_awareness() ran (it did, above).")
        print("  3. If (1) and (2) don't help, re-run this script as Administrator.")
    else:
        print("Note: you captured a non-primary monitor.")
        print(f"  Click coordinates from this screenshot need to be offset by "
              f"({left}, {top}) on the virtual desktop.")
        print(f"  visclick.bot does this automatically when you pass "
              f"--monitor {mon_idx}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
