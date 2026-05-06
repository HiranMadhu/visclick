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
import baseline_visclick as B_VC

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
    ("visclick",  B_VC),
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
            r = bc.BaselineResult(
                method=name,
                found=False,
                notes=f"skipped via --skip-{name}",
            )
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
        "visclick":  ( 60, 220,  90),
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
    """Fallback: hand the PNG to the OS's default image viewer (non-blocking)."""
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


_METHOD_COLOURS_HEX = {
    "template":  "#ff6464",
    "ocr_only":  "#3cc8ff",
    "pywinauto": "#ffc800",
    "visclick":  "#3cdc5a",
}


def _verdict_dialog_tk(overlay_path: Path,
                       task: Dict[str, Any],
                       to_judge: List[Tuple[str, bc.BaselineResult]]
                       ) -> Dict[str, str]:
    """Modal Tk window: shows the overlay image + a Pass/Fail/Skip row per
    method that needs a human verdict. Blocks until the user hits "Next →".
    Returns ``{method: "pass"|"fail"|"skip"}``.

    One window at a time, brought to the foreground; closes when the user
    advances. This replaces ``os.startfile()`` which was non-blocking and
    let multiple system image-viewer windows pile up.
    """
    import tkinter as tk
    from PIL import Image as _PILImage, ImageTk

    img = _PILImage.open(overlay_path)
    iw, ih = img.size
    max_w, max_h = 1500, 760
    scale = min(max_w / iw, max_h / ih, 1.0)
    if scale < 1.0:
        img = img.resize((int(iw * scale), int(ih * scale)), _PILImage.LANCZOS)

    choices: Dict[str, Optional[str]] = {m: None for m, _ in to_judge}

    root = tk.Tk()
    root.title(f"{task['id']} — {task['instruction']!r}")
    try:
        root.attributes("-topmost", True)
    except tk.TclError:
        pass
    root.lift()
    root.focus_force()

    photo = ImageTk.PhotoImage(img)
    canvas_lbl = tk.Label(root, image=photo, bd=2, relief=tk.SUNKEN)
    canvas_lbl.image = photo  # keep reference
    canvas_lbl.pack(padx=8, pady=(8, 4))

    header = tk.Label(
        root,
        text=f"{task['id']}: {task['instruction']!r}   (app={task['app']})",
        font=("Arial", 13, "bold"),
    )
    header.pack(pady=(0, 4))

    grid = tk.Frame(root)
    grid.pack(pady=4)

    btn_refs: Dict[str, Dict[str, tk.Button]] = {}

    def _refresh_next_state() -> None:
        next_btn.configure(
            state=("normal" if all(c is not None for c in choices.values()) else "disabled")
        )

    def _mark(method: str, verdict: str) -> None:
        choices[method] = verdict
        for v, b in btn_refs[method].items():
            b.configure(
                bg=("#88ee88" if v == verdict else "SystemButtonFace"),
                relief=(tk.SUNKEN if v == verdict else tk.RAISED),
            )
        _refresh_next_state()

    for i, (m, r) in enumerate(to_judge):
        swatch = tk.Label(
            grid, bg=_METHOD_COLOURS_HEX.get(m, "#cccccc"),
            width=2, height=1, relief=tk.RAISED,
        )
        swatch.grid(row=i, column=0, padx=(2, 6), pady=2)
        tk.Label(grid, text=m, width=12, anchor="w",
                 font=("Arial", 11, "bold")).grid(row=i, column=1, sticky="w")
        info_text = f"xy={r.xy}" if r.xy else "(not found)"
        tk.Label(grid, text=info_text, width=22, anchor="w",
                 font=("Consolas", 10)).grid(row=i, column=2, sticky="w")
        btn_refs[m] = {}
        for col, (label, v) in enumerate(
            [("Pass", "pass"), ("Fail", "fail"), ("Skip", "skip")], start=3
        ):
            b = tk.Button(grid, text=label, width=8,
                          command=lambda m=m, v=v: _mark(m, v))
            b.grid(row=i, column=col, padx=2, pady=1)
            btn_refs[m][v] = b

    def _next() -> None:
        if all(c is not None for c in choices.values()):
            root.destroy()

    next_btn = tk.Button(
        root, text="Next →", width=22, font=("Arial", 11, "bold"),
        command=_next, state="disabled",
    )
    next_btn.pack(pady=(8, 12))

    # Keyboard shortcuts: y/n/s mark all methods at once (handy when there's
    # only one method to judge, e.g. --only-method visclick); Enter advances
    # once everything is decided.
    def _mark_all(verdict: str) -> None:
        for m in choices:
            _mark(m, verdict)
    root.bind("<y>", lambda e: _mark_all("pass"))
    root.bind("<n>", lambda e: _mark_all("fail"))
    root.bind("<s>", lambda e: _mark_all("skip"))
    root.bind("<Return>", lambda e: _next())
    root.bind("<Escape>", lambda e: _mark_all("skip"))

    # If user closes the window early, treat any unset methods as 'skip'.
    def _on_close() -> None:
        for m, v in choices.items():
            if v is None:
                choices[m] = "skip"
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", _on_close)

    root.mainloop()
    return {m: (v or "skip") for m, v in choices.items()}


def ask_verdicts(task: Dict[str, Any],
                 results: Dict[str, bc.BaselineResult],
                 overlay: Path,
                 gui: bool = True,
                 auto_pass_negative: bool = True) -> None:
    """Mutates each result.verdict to 'pass' / 'fail' / 'skip'.

    Pass-1: assign deterministic verdicts (skipped methods, negative tasks,
    not-found predictions).  Pass-2: ask the human about the remaining
    methods that need eyeballs. With ``gui=True`` (default) the human pass
    uses a single modal Tk window per task — one image visible at a time,
    Pass/Fail/Skip buttons, blocking until "Next →" is clicked. With
    ``gui=False`` it falls back to the legacy os.startfile + stdin flow.
    """
    print(f"    overlay saved: {overlay}")

    to_judge: List[Tuple[str, bc.BaselineResult]] = []
    for name, r in results.items():
        if r.notes.startswith("skipped via --skip-"):
            r.verdict = "skip"
            continue
        if task["is_negative"]:
            r.verdict = "pass" if not r.found else "fail"
            continue
        if not r.found:
            r.verdict = "fail"
            continue
        to_judge.append((name, r))

    if not to_judge:
        print(f"    (no method needs a human verdict for {task['id']})")
        return

    if gui:
        try:
            choices = _verdict_dialog_tk(overlay, task, to_judge)
            for name, r in to_judge:
                r.verdict = choices.get(name, "skip")
            for name, r in to_judge:
                print(f"    [{name}] predicted {r.xy} → {r.verdict}")
            return
        except Exception as e:
            print(f"    (GUI verdict dialog failed: {e!r}; falling back to terminal)")

    _open_overlay(overlay)
    for name, r in to_judge:
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


def append_csv(rows: List[Dict[str, Any]], csv_path: Path,
               replace_tasks: Optional[List[str]] = None) -> None:
    """Append ``rows`` to ``csv_path``. If ``replace_tasks`` is provided,
    drop any pre-existing rows whose ``task`` is in that list before writing
    (so re-running a task overwrites instead of duplicating)."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    existing: List[Dict[str, str]] = []
    if csv_path.exists():
        with csv_path.open(newline="") as f:
            reader = csv.DictReader(f)
            existing = [r for r in reader]
        if replace_tasks:
            keep = {t.upper() for t in replace_tasks}
            n_before = len(existing)
            existing = [r for r in existing if r.get("task", "").upper() not in keep]
            n_dropped = n_before - len(existing)
            if n_dropped:
                print(f"  (dropped {n_dropped} existing row(s) for "
                      f"task(s) {sorted(keep)})")

    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for row in existing:
            w.writerow({k: row.get(k, "") for k in CSV_FIELDS})
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
    p.add_argument("--skip-visclick", action="store_true")
    p.add_argument("--only-method", default="",
                   help="comma-separated subset of methods to run (others are "
                        "marked as skip). Use to re-run a single method against "
                        "saved screenshots, e.g. --only-method visclick --auto.")
    p.add_argument("--no-gui", action="store_true",
                   help="skip the modal Tk dialog and use the legacy "
                        "os.startfile + stdin verdict flow (for headless / "
                        "broken-tkinter setups).")
    p.add_argument("--csv", type=Path, default=CSV_PATH,
                   help=f"output CSV (default: {CSV_PATH.relative_to(REPO)}).")
    args = p.parse_args(argv)

    method_names = [n for n, _ in METHODS]
    skip = []
    if args.only_method.strip():
        wanted = {n.strip() for n in args.only_method.split(",") if n.strip()}
        unknown = wanted - set(method_names)
        if unknown:
            print(f"ERROR: unknown method(s) in --only-method: {sorted(unknown)} "
                  f"(known: {method_names})", file=sys.stderr)
            return 2
        skip.extend(n for n in method_names if n not in wanted)
    for n in method_names:
        if getattr(args, f"skip_{n}", False):
            if n not in skip:
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
        ask_verdicts(task, results, overlay, gui=not args.no_gui)

        for name, r in results.items():
            row = r.to_csv_row()
            row["task"] = task["id"]
            row["instruction"] = task["instruction"]
            row["is_negative"] = task["is_negative"]
            all_rows.append(row)

    ran_task_ids = [t["id"] for t in tasks if t["app"] != "TBD"]
    append_csv(all_rows, args.csv, replace_tasks=ran_task_ids)
    summarise(args.csv)
    print(f"\nWrote {len(all_rows)} row(s) to {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
