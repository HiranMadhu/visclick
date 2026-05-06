"""Phase 1.C.1 — SikuliX-style template-matching baseline.

Idea: instead of training an object detector, capture a reference PNG of
each control (Save button, Cancel button, Search icon, Chrome's omnibox,
…) and at run time slide that template across the live screenshot using
``cv2.matchTemplate``. If the best correlation score exceeds a threshold,
click the centre of the best match.

This is *exactly* what SikuliX [report literature L15] does, distilled
into a few lines of OpenCV. It is an extremely strong baseline whenever
the live screenshot is pixel-identical to the captured template (same
theme, same DPI, same monitor scale). It collapses to zero recall the
moment the UI changes — different theme, different scale, anti-aliasing,
or a new app version.

USAGE:
    py -3 scripts/baseline_template.py \\
        --instruction "click Save" \\
        --target-template Save.png \\
        --image samples/test_screenshots/T01.png

Run on the LIVE screen instead by omitting --image (after a 5 s grace
period to switch focus).

Reference templates live in ``samples/templates/<filename>``. Capture
them once with Win+Shift+S and crop tightly around the control (fewer
pixels = faster, but TOO few pixels means the template is no longer
distinctive). 24x24 minimum, ~120x40 typical for a button.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from baseline_common import (
    BaselineResult,
    baseline_argparser,
    load_image,
    maybe_click,
    print_result,
    time_call,
    autopick_monitor,
)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "samples" / "templates"
DEFAULT_THRESHOLD = 0.7  # cv2.matchTemplate TM_CCOEFF_NORMED correlation


def _do_match(image_rgb: np.ndarray,
              template_rgb: np.ndarray,
              threshold: float = DEFAULT_THRESHOLD) -> Optional[dict]:
    """Run TM_CCOEFF_NORMED at three scales (1.0, 0.85, 1.15) and pick the
    best across all scales. Returns ``None`` if best score < threshold.
    """
    img_g = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    tpl_g = cv2.cvtColor(template_rgb, cv2.COLOR_RGB2GRAY)

    best = None
    for scale in (1.0, 0.85, 1.15):
        if scale != 1.0:
            new_w = max(8, int(tpl_g.shape[1] * scale))
            new_h = max(8, int(tpl_g.shape[0] * scale))
            scaled = cv2.resize(tpl_g, (new_w, new_h),
                                interpolation=cv2.INTER_AREA)
        else:
            scaled = tpl_g

        if scaled.shape[0] > img_g.shape[0] or scaled.shape[1] > img_g.shape[1]:
            continue

        result = cv2.matchTemplate(img_g, scaled, cv2.TM_CCOEFF_NORMED)
        _min_v, max_v, _min_l, max_l = cv2.minMaxLoc(result)
        if best is None or max_v > best["score"]:
            best = {
                "score": float(max_v),
                "loc":   (int(max_l[0]), int(max_l[1])),
                "shape": (int(scaled.shape[0]), int(scaled.shape[1])),
                "scale": scale,
            }

    if best is None or best["score"] < threshold:
        return best  # may still be useful for debugging
    return best


def predict(image_rgb: np.ndarray,
            instruction: str,
            *,
            target_template: str = "",
            offset: tuple[int, int] = (0, 0),
            templates_dir: Optional[Path] = None,
            threshold: float = DEFAULT_THRESHOLD,
            **_: object) -> BaselineResult:
    r = BaselineResult(method="template")
    if not target_template:
        r.notes = "no target_template supplied; skipping"
        return r

    tpl_path = (templates_dir or TEMPLATES_DIR) / target_template
    if not tpl_path.is_file():
        r.notes = f"template not found at {tpl_path}"
        return r

    tpl_rgb = cv2.cvtColor(cv2.imread(str(tpl_path)), cv2.COLOR_BGR2RGB)

    out, ms = time_call(_do_match, image_rgb, tpl_rgb, threshold)
    r.elapsed_ms = ms
    if out is None:
        r.notes = "no match candidates (template larger than image at all scales?)"
        return r

    score = out["score"]
    if score < threshold:
        r.notes = (f"best score {score:.3f} below threshold {threshold:.2f} "
                   f"using template '{target_template}'")
        return r

    h, w = out["shape"]
    x, y = out["loc"]
    cx_local = x + w // 2
    cy_local = y + h // 2
    r.found = True
    r.confidence = score
    r.bbox = (int(x), int(y), int(x + w), int(y + h))
    r.xy = (int(cx_local + offset[0]), int(cy_local + offset[1]))
    r.notes = f"matched '{target_template}' at scale={out['scale']:.2f}"
    return r


def main(argv: Optional[list[str]] = None) -> int:
    p = baseline_argparser("template")
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                   help=f"min cv2.matchTemplate score (default {DEFAULT_THRESHOLD}).")
    args = p.parse_args(argv)

    monitor = autopick_monitor(args.monitor)
    img, offset = load_image(args.image, monitor)

    r = predict(img, args.instruction,
                target_template=args.target_template,
                offset=offset,
                threshold=args.threshold)
    print_result(r)

    if r.found:
        maybe_click(r, args.dry_run)

    return 0 if (r.found or "is_negative" in args.instruction.lower()) else 1


if __name__ == "__main__":
    sys.exit(main())
