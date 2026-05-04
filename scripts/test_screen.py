"""Screenshot test — verifies the capture layer in isolation.

Usage:
    python scripts/test_screen.py
    python scripts/test_screen.py --out screenshots/foo.png --monitor 2

What this proves (when it works):
1. mss is installed and can read the framebuffer.
2. The captured image dimensions match what pyautogui reports for the screen
   (after DPI awareness is set). A mismatch here means clicks will land in the
   wrong place — see the printed warning.
3. PIL can save the screenshot as PNG.

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
from visclick.capture import primary_monitor, save_screenshot, set_dpi_awareness  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Screenshot test")
    ap.add_argument("--out", default="screenshots/test_screen.png")
    ap.add_argument("--monitor", type=int, default=1,
                    help="mss monitor index (0=all stitched, 1=primary, 2+=secondary)")
    args = ap.parse_args()

    set_dpi_awareness()

    info = primary_monitor()
    print(f"primary monitor (mss): top={info['top']} left={info['left']}  "
          f"width={info['width']} height={info['height']}")

    pa_w, pa_h = screen_size()
    print(f"screen size (pyautogui): {pa_w} x {pa_h}")

    w, h, abs_path = save_screenshot(args.out, monitor_index=args.monitor)
    print(f"saved: {abs_path}  ({w} x {h})")

    if w == pa_w and h == pa_h:
        print("OK: mss and pyautogui agree on screen dimensions — clicks will land correctly.")
    else:
        print("WARNING: mss says {0}x{1} but pyautogui says {2}x{3}.".format(w, h, pa_w, pa_h))
        print("This is usually Windows display scaling. Either:")
        print("  1. Set Display scaling to 100% in Windows Settings (recommended), or")
        print("  2. Confirm visclick.capture.set_dpi_awareness() ran (it is called above).")
        print("  3. If the difference is exactly 1.25x or 1.5x, your DPI awareness call "
              "is being silently rejected — try running this script as Administrator.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
