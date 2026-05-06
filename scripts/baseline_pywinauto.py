"""Phase 1.C.3 — Windows accessibility-tree baseline.

Idea: Windows exposes a (mostly) machine-readable description of every
control through the UI Automation (UIA) API. ``pywinauto`` wraps that
API in Python. If we ask for a control by ``Name='Save'`` and
``ControlType='Button'``, the OS hands us its on-screen rectangle and
we click its centre — *no detector, no OCR, no screenshot*.

EXPECTED OUTCOME for the dissertation:
- Works on **native Win32** dialogs (Notepad's Save As, the classic
  File Explorer ribbon, system Settings) — they expose a complete UIA
  tree.
- Works partially on **Chrome / Edge** — the renderer exposes the
  page's ARIA roles but UIA names of toolbar controls are inconsistent
  across versions.
- Fails on **VS Code, Teams, Slack, Discord, Spotify, anything Electron**.
  Electron exposes a degenerate tree of ``Pane / Document / Group``
  with no useful Names. UIA returns ``ElementNotFound``.
- Cannot find positional descriptions like "first list item" or
  "click word hello" — UIA needs a Name string.

This script demonstrates *"if accessibility worked, ML would be
unnecessary — but it doesn't"*, which is the dissertation's
justification for using a vision-based approach.

NOTE: ``pywinauto`` is **Windows-only** and is not in the project's
default dependencies. Install with ``pip install pywinauto`` (or
``pip install '.[windows]'`` once we add the optional extra). On
non-Windows the script exits with a clear "skip" message instead of
crashing the runner.

USAGE:
    py -3 scripts/baseline_pywinauto.py \\
        --instruction "click Save" \\
        --target-uia-name Save \\
        --target-uia-role Button
"""
from __future__ import annotations

import sys
from typing import Optional

from baseline_common import (
    BaselineResult,
    autopick_monitor,
    baseline_argparser,
    load_image,
    maybe_click,
    print_result,
    time_call,
)


def _can_run() -> Optional[str]:
    if sys.platform != "win32":
        return f"pywinauto is Windows-only; this is sys.platform={sys.platform!r}"
    try:
        import pywinauto  # noqa: F401
    except Exception as e:
        return f"pywinauto import failed: {e!r}. Try: pip install pywinauto"
    return None


def _find(name: str, role: str):
    """Walk the UIA tree of every top-level window and return the first
    descendant whose ``Name`` matches and (optionally) ``ControlType`` matches.

    Returns the wrapper or ``None``.
    """
    from pywinauto import Desktop
    desktop = Desktop(backend="uia")
    try:
        windows = desktop.windows()
    except Exception:
        windows = []

    for w in windows:
        try:
            if not w.is_visible():
                continue
        except Exception:
            continue
        try:
            kw = {"name": name}
            if role:
                kw["control_type"] = role
            elem = w.descendants(**kw)
            if elem:
                return elem[0]
        except Exception:
            continue
    return None


def predict(_image_rgb,
            instruction: str,
            *,
            target_uia_name: str = "",
            target_uia_role: str = "",
            offset: tuple[int, int] = (0, 0),
            **_: object) -> BaselineResult:
    r = BaselineResult(method="pywinauto")

    why_skip = _can_run()
    if why_skip:
        r.notes = why_skip
        return r

    if not target_uia_name:
        r.notes = ("no target_uia_name supplied; pywinauto cannot guess a UIA "
                   "Name from a free-text instruction.")
        return r

    elem, ms = time_call(_find, target_uia_name, target_uia_role)
    r.elapsed_ms = ms

    if elem is None:
        role_label = f" ({target_uia_role})" if target_uia_role else ""
        r.notes = (f"UIA element Name='{target_uia_name}'{role_label} not found "
                   f"in any visible top-level window")
        return r

    try:
        rect = elem.rectangle()
        x1, y1, x2, y2 = int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)
    except Exception as e:
        r.notes = f"found UIA element but rectangle() failed: {e!r}"
        return r

    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    r.found = True
    r.confidence = 1.0
    r.bbox = (x1, y1, x2, y2)
    r.xy = (int(cx + offset[0]), int(cy + offset[1]))
    try:
        ctype = elem.element_info.control_type
    except Exception:
        ctype = "?"
    r.notes = (f"UIA hit Name='{target_uia_name}' ControlType={ctype} "
               f"at virtual-desktop ({cx},{cy})")
    return r


def main(argv: Optional[list[str]] = None) -> int:
    p = baseline_argparser("pywinauto")
    args = p.parse_args(argv)

    monitor = autopick_monitor(args.monitor)
    img, offset = load_image(args.image, monitor)

    r = predict(img, args.instruction,
                target_uia_name=args.target_uia_name,
                target_uia_role=args.target_uia_role,
                offset=offset)
    print_result(r)

    if r.found:
        maybe_click(r, args.dry_run)
    return 0 if r.found else 1


if __name__ == "__main__":
    sys.exit(main())
