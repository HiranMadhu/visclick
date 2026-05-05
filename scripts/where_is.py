"""Live cursor position printer — manual coordinate finder.

Run this in a terminal, hover the cursor over a target (e.g. the Save
button you want the bot to click), and read the (x, y) value off the
screen. Then feed those numbers back into VisClick:

  GUI:  type ``xy 1234 567`` in the instruction box and press Run.
  CLI:  python -m visclick.bot --xy 1234,567 --countdown 5

Why this script: pyautogui's coordinate system is the *virtual desktop*
(top-left of the Windows primary monitor is (0, 0)), which on a
multi-monitor setup is not what your eyes intuitively report. Reading
the cursor off this script is the most reliable way to get a coord
the bot will click on.

Usage:
  python scripts/where_is.py                  # print updates while moving
  python scripts/where_is.py --hold 5         # sample every 0.1 s for 5 s
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pyautogui  # noqa: E402

from visclick.capture import (  # noqa: E402
    find_pyautogui_primary,
    list_monitors,
    set_dpi_awareness,
)


def _which_monitor(x: int, y: int, mons: list[dict]) -> int:
    for m in mons:
        if m["index"] == 0:
            continue
        if (m["left"] <= x < m["left"] + m["width"]
                and m["top"] <= y < m["top"] + m["height"]):
            return m["index"]
    return -1


def main() -> int:
    ap = argparse.ArgumentParser(description="Live cursor position printer")
    ap.add_argument("--hold", type=float, default=0.0,
                    help="If > 0, sample for this many seconds and exit "
                         "(useful with task scheduler).")
    ap.add_argument("--interval", type=float, default=0.1,
                    help="Sampling interval in seconds (default 0.1).")
    args = ap.parse_args()

    set_dpi_awareness()
    mons = list_monitors()
    primary = find_pyautogui_primary()
    pa_w, pa_h = pyautogui.size()

    print(f"pyautogui primary: {pa_w} x {pa_h} (the (0, 0) origin lives here)")
    print(f"pyautogui-primary mss index: {primary}")
    print("Monitors:")
    for m in mons:
        if m["index"] == 0:
            print(f"  [virtual] {m['width']}x{m['height']} @({m['left']},{m['top']})")
        else:
            print(f"  [{m['index']}] {m['width']}x{m['height']} "
                  f"@({m['left']},{m['top']})"
                  f"{'  <- pyautogui primary' if m['index'] == primary else ''}")
    print()
    print("Hover the cursor over your target. Ctrl+C to stop.")
    print()

    start = time.time()
    last = None
    try:
        while True:
            try:
                pos = pyautogui.position()
            except Exception:
                time.sleep(args.interval); continue
            if (pos.x, pos.y) != last:
                mon = _which_monitor(pos.x, pos.y, mons)
                mon_str = f"monitor {mon}" if mon > 0 else "off-screen"
                local = ""
                if mon > 0:
                    m = mons[mon]
                    local = f"  monitor-local=({pos.x - m['left']:>5d},{pos.y - m['top']:>5d})"
                print(f"\rcursor: virtual=({pos.x:>5d},{pos.y:>5d})  "
                      f"{mon_str:>9s}{local}",
                      end="", flush=True)
                last = (pos.x, pos.y)
            if args.hold > 0 and (time.time() - start) >= args.hold:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    print()
    if last is not None:
        print(f"final cursor: virtual=({last[0]}, {last[1]})")
        print(f"feed into bot: python -m visclick.bot --xy {last[0]},{last[1]} --countdown 5")
        print(f"feed into GUI: type 'xy {last[0]} {last[1]}' into the instruction box")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
