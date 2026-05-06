"""Phase 1.C runner — drive every classical baseline on the T01..T20 task set.

For each task in ``tasks/T01_T20.json``:
  1. Print task description; wait for user to switch to the target app.
  2. Capture the active monitor, save it under
     ``samples/test_screenshots/<id>.png`` (so reproductions can use
     ``--image`` instead of capturing live).
  3. Call each baseline's ``predict()`` on the captured image.
  4. Save an annotated overlay PNG showing every baseline's pick.
  5. Ask the user (per baseline) whether the prediction is correct.
  6. Append a row per task per method to
     ``reports/tables/baseline_results.csv``.

The runner does **not** click anything: this phase is about predictions,
not actions. Phase 2 will replay the same task list with actual clicks
once the comparison has been made.

Usage on Windows::

    py -3 scripts/run_baselines.py                   # interactive
    py -3 scripts/run_baselines.py --auto            # use saved screenshots
    py -3 scripts/run_baselines.py --skip-pywinauto  # skip if pywinauto unavailable

Subset::

    py -3 scripts/run_baselines.py --only T01,T02,T15
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

import baseline_common as bc
import baseline_template as B_TPL
import baseline_ocr_only as B_OCR
import baseline_pywinauto as B_PWA

REPO = Path(__file__).resolve().parent.parent
TASKS_JSON = REPO / "tasks" / "T01_T20.json"
SHOT_DIR = REPO / "samples" / "test_screenshots"
TABLES_DIR = REPO / "reports" / "tables"
FIG_DIR = REPO / "reports" / "figures" / "baselines"
CSV_PATH = TABLES_DIR / "baseline_results.csv"

METHODS: List[Tuple[str, Any]] = [
    ("template",  B_TPL),
    ("ocr_only",  B_OCR),
    ("pywinauto", B_PWA),
]

CSV_FIELDS = [
    "task", "method", "found", "verdict", "xy", "bbox",
    "confidence", "elapsed_ms", "instruction", "is_negative", "notes",
]


# ---------- helpers ----------

def load_tasks(only: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    spec = json.loads(TASKS_JSON.read_text())
    tasks = spec["tasks"]
    if only:
        wanted = {t.strip().upper() for t in only}
        tasks = [t for t in tasks if t["id"].upper() in wanted]
    return tasks


def capture_for_task(task: Dict[str, Any], monitor: int,
                     auto: bool) -> Tuple[np.ndarray, Tuple[int, int], Path]:
    """Either re-load saved screenshot (auto mode) or capture live."""
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    shot = SHOT_DIR / f"{task['id']}.png"

    if auto and shot.is_file():
        img = np.array(Image.open(shot).convert("RGB"))
        return img, (0, 0), shot

    print(f"\n>>> {task['id']}  app={task['app']}  setup={task['setup']}")
    print(f"    instruction: {task['instruction']!r}")
    print(f"    is_negative: {task['is_negative']}")
    if task["is_negative"]:
        print("    (negative case: SUCCESS == every baseline returns 'not found')")
    input("    Place the target window on the screen and press Enter when ready… ")
    for s in range(3, 0, -1):
        print(f"    capturing in {s}...", end="\r", flush=True)
        time.sleep(1.0)
    print()

    img, offset = bc.load_image(None, monitor)
    Image.fromarray(img).save(shot)
    print(f"    captured {img.shape[1]}x{img.shape[0]} → {shot.name}")
    return img, offset, shot


def run_methods(image_rgb: np.ndarray,
                offset: Tuple[int, int],
                task: Dict[str, Any],
                skip: List[str]) -> Dict[str, bc.BaselineResult]:
    out: Dict[str, bc.BaselineResult] = {}
    for name, mod in METHODS:
        if name in skip:
            r = bc.BaselineResult(method=name, notes="skipped via --skip-" + name)
            out[name] = r
            continue
        r = mod.predict(
            image_rgb,
            task["instruction"],
            target_text=task.get("target_text", ""),
            target_template=task.get("target_template", ""),
            target_uia_name=task.get("target_uia_name", ""),
            target_uia_role=task.get("target_uia_role", ""),
            offset=offset,
        )
        out[name] = r
        bc.print_result(r)
    return out


def save_overlay(image_rgb: np.ndarray,
                 task: Dict[str, Any],
                 results: Dict[str, bc.BaselineResult]) -> Path:
    """Draw every method's bbox + xy on a single overlay PNG."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    img = image_rgb.copy()
    colours = {
        "template":  (255,  60,  60),
        "ocr_only":  ( 60, 200, 255),
        "pywinauto": (255, 200,   0),
    }
    for name, r in results.items():
        c = colours.get(name, (200, 200, 200))
        if r.bbox:
            x1, y1, x2, y2 = r.bbox
            cv2.rectangle(img, (x1, y1), (x2, y2), c, 3)
        if r.xy:
            x, y = r.xy
            cv2.circle(img, (int(x), int(y)), 12, c, 2)
            cv2.line(img, (int(x) - 18, int(y)), (int(x) + 18, int(y)), c, 2)
            cv2.line(img, (int(x), int(y) - 18), (int(x), int(y) + 18), c, 2)
        label = f"{name}: {'HIT' if r.found else 'MISS'}"
        y_lbl = 30 + 30 * list(colours.keys()).index(name)
        cv2.putText(img, label, (10, y_lbl), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, c, 2, cv2.LINE_AA)
    out = FIG_DIR / f"{task['id']}.png"
    Image.fromarray(img).save(out)
    return out


def _open_overlay(p: Path) -> None:
    try:
        if sys.platform == "win32":
            import os as _os
            _os.startfile(str(p))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            import subprocess as _sp
            _sp.Popen(["open", str(p)])
        else:
            import subprocess as _sp
            _sp.Popen(["xdg-open", str(p)])
    except Exception as e:
        print(f"    (could not auto-open {p.name}: {e})")


def ask_verdicts(task: Dict[str, Any],
                 results: Dict[str, bc.BaselineResult],
                 overlay: Path,
                 auto_pass_negative: bool = True) -> None:
    """Mutates each result.verdict to 'pass' / 'fail' / 'skip'."""
    print(f"    overlay saved: {overlay}")
    if any(r.found for r in results.values()) and not task["is_negative"]:
        _open_overlay(overlay)
    for name, r in results.items():
        if task["is_negative"]:
            if not r.found:
                r.verdict = "pass"
                continue
            r.verdict = "fail"
            continue

        if not r.found:
            r.verdict = "fail"
            continue

        prompt = (f"    [{name}] predicted {r.xy}. "
                  f"open {overlay.name} and check the {name} marker. "
                  f"Is it on the correct element? [y/N/s(kip)] ")
        while True:
            ans = input(prompt).strip().lower()
            if ans in {"y", "yes"}:
                r.verdict = "pass"; break
            if ans in {"", "n", "no"}:
                r.verdict = "fail"; break
            if ans in {"s", "skip"}:
                r.verdict = "skip"; break


def append_csv(rows: List[Dict[str, Any]], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not csv_path.exists()
    with csv_path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new_file:
            w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in CSV_FIELDS})


def summarise(csv_path: Path) -> None:
    """Print a TSR per method from the latest run only (filters by run_id if
    we ever add one; for now read all rows and aggregate)."""
    rows = list(csv.DictReader(csv_path.open()))
    if not rows:
        return
    by_method: Dict[str, List[str]] = {}
    for r in rows:
        by_method.setdefault(r["method"], []).append(r["verdict"])

    print("\n=== Phase 1.C running TSR (across all tasks recorded so far) ===")
    print(f"{'method':14s} {'tasks':>6s} {'pass':>6s} {'fail':>6s} {'skip':>6s} {'TSR':>7s}")
    for m, verdicts in by_method.items():
        n = len(verdicts)
        p = verdicts.count("pass")
        f = verdicts.count("fail")
        s = verdicts.count("skip")
        denom = n - s
        tsr = (p / denom) if denom else 0.0
        print(f"{m:14s} {n:>6d} {p:>6d} {f:>6d} {s:>6d} {tsr:>6.1%}")


# ---------- main ----------

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--monitor", type=int, default=None,
                   help="mss monitor index (default: pyautogui's primary).")
    p.add_argument("--only", default="",
                   help="comma-separated list of task ids to run, e.g. 'T01,T02'.")
    p.add_argument("--auto", action="store_true",
                   help="reuse existing samples/test_screenshots/<id>.png "
                        "instead of capturing live (offline reproducibility).")
    p.add_argument("--skip-template", action="store_true")
    p.add_argument("--skip-ocr_only", action="store_true")
    p.add_argument("--skip-pywinauto", action="store_true")
    p.add_argument("--csv", type=Path, default=CSV_PATH,
                   help=f"output CSV (default: {CSV_PATH.relative_to(REPO)}).")
    args = p.parse_args(argv)

    skip = []
    for n in ("template", "ocr_only", "pywinauto"):
        if getattr(args, f"skip_{n}"):
            skip.append(n)

    only = [t for t in args.only.split(",") if t.strip()] or None
    tasks = load_tasks(only)
    if not tasks:
        print("no tasks selected", file=sys.stderr); return 2
    print(f"Phase 1.C — running {len(tasks)} task(s); skip={skip or 'none'}")

    monitor = bc.autopick_monitor(args.monitor)
    print(f"monitor={monitor}; output csv={args.csv.relative_to(REPO)}")

    all_rows: List[Dict[str, Any]] = []
    for task in tasks:
        if task["app"] == "TBD":
            print(f"\n>>> {task['id']}  (TBD — skipping; fill the JSON to run it)")
            continue

        img, offset, _shot = capture_for_task(task, monitor, args.auto)
        results = run_methods(img, offset, task, skip)
        overlay = save_overlay(img, task, results)
        ask_verdicts(task, results, overlay)

        for name, r in results.items():
            row = r.to_csv_row()
            row["task"] = task["id"]
            row["instruction"] = task["instruction"]
            row["is_negative"] = task["is_negative"]
            all_rows.append(row)

    append_csv(all_rows, args.csv)
    summarise(args.csv)
    print(f"\nWrote {len(all_rows)} row(s) to {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
