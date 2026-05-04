"""Manual click test — verifies the click layer in isolation.

Usage:
    python scripts/test_click.py 500 400
    python scripts/test_click.py 500 400 --button right --dwell 0.5
    python scripts/test_click.py --no-click 500 400   # just move, do not click
    python scripts/test_click.py --grid              # click 9 grid points (no GUI hit)

What this script proves (when it works):
1. PyAutoGUI is installed and not blocked by Windows accessibility settings.
2. The mouse can be programmatically moved to (x, y).
3. A click event reaches the OS at the right pixel after Windows DPI scaling.

If a click misses by ~20–30%, it is almost always Windows display scaling.
``visclick.capture.set_dpi_awareness()`` is called at the top of this script
to align mss / pyautogui pixel grids; no further action needed for 125%/150%
display zoom.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Make ``visclick`` importable when running from a fresh clone before ``pip install -e .``
_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from visclick.act import click_xy, screen_size  # noqa: E402
from visclick.capture import set_dpi_awareness  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Manual click test")
    ap.add_argument("x", type=int, nargs="?", default=None)
    ap.add_argument("y", type=int, nargs="?", default=None)
    ap.add_argument("--button", choices=["left", "right", "middle"], default="left")
    ap.add_argument("--dwell", type=float, default=0.3, help="Move duration before click")
    ap.add_argument("--no-click", action="store_true", help="Move only, do not click")
    ap.add_argument("--grid", action="store_true",
                    help="Move to 9 grid points across the screen (no click). "
                         "Useful to visually confirm coords match what you expect.")
    args = ap.parse_args()

    set_dpi_awareness()
    sw, sh = screen_size()
    print(f"pyautogui screen size: {sw} x {sh}")

    if args.grid:
        for fy in (0.10, 0.50, 0.90):
            for fx in (0.10, 0.50, 0.90):
                x, y = int(sw * fx), int(sh * fy)
                print(f"  hover ({x:>5d}, {y:>5d})")
                click_xy(x, y, dwell=0.4) if False else None  # never click in grid mode
                import pyautogui
                pyautogui.moveTo(x, y, duration=0.4)
                time.sleep(0.2)
        print("grid pass complete (no click).")
        return 0

    if args.x is None or args.y is None:
        ap.error("provide x y, or --grid, or --help")

    print(f"target: ({args.x}, {args.y})  button={args.button}  dwell={args.dwell}s  "
          f"click={'yes' if not args.no_click else 'no'}")
    print("BEGINS IN 3 SECONDS — switch to the target window now.")
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    if args.no_click:
        import pyautogui
        pyautogui.moveTo(args.x, args.y, duration=args.dwell)
        print(f"moved to ({args.x}, {args.y}); no click sent.")
    else:
        click_xy(args.x, args.y, dwell=args.dwell, button=args.button)
        print(f"clicked ({args.x}, {args.y}) with {args.button} button.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
