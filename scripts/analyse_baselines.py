"""Phase 1.D — load reports/tables/baseline_results.csv and produce:

1. ``reports/tables/baseline_summary.csv`` — one row per method:
   ``method, n_tasks, pass, fail, skip, TSR, latency_p50_ms, n_template_skips, lines_of_code, dependencies``.
2. ``reports/tables/baseline_per_task.csv`` — pivoted matrix of verdicts:
   ``task, instruction, is_negative, template, ocr_only, pywinauto``.
3. ``reports/figures/method_comparison_tsr.png`` — bar chart of TSR for the
   three Phase-1.C baselines (and a placeholder for VisClick's TSR which
   will be filled in once Phase 2 produces it).

Usage::

    python scripts/analyse_baselines.py
    python scripts/analyse_baselines.py --visclick-tsr 0.85    # add a 4th bar

The script is idempotent: re-running it overwrites the summary CSV and the
PNG without touching ``baseline_results.csv``. It does **not** push to git.
"""
from __future__ import annotations

import argparse
import csv
import statistics
import sys
from pathlib import Path
from typing import Dict, List

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "reports" / "tables" / "baseline_results.csv"
SUMMARY = REPO / "reports" / "tables" / "baseline_summary.csv"
PIVOT = REPO / "reports" / "tables" / "baseline_per_task.csv"
FIG = REPO / "reports" / "figures" / "method_comparison_tsr.png"

# Static facts we want in the summary so the dissertation can quote LoC and deps.
LOC = {
    "template":  157,
    "ocr_only":  121,
    "pywinauto": 164,
}
DEPS = {
    "template":  "opencv-python (already a VisClick dep)",
    "ocr_only":  "easyocr + rapidfuzz (already VisClick deps)",
    "pywinauto": "pywinauto>=0.6.8 (Windows-only optional extra)",
}


def load_rows() -> List[Dict[str, str]]:
    if not RESULTS.is_file():
        print(f"ERROR: {RESULTS} not found. Run scripts/run_baselines.py first.",
              file=sys.stderr)
        sys.exit(2)
    with RESULTS.open(newline="") as f:
        return list(csv.DictReader(f))


def per_method_summary(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_method: Dict[str, List[Dict[str, str]]] = {}
    for r in rows:
        by_method.setdefault(r["method"], []).append(r)

    out = []
    for method, items in by_method.items():
        passes = sum(1 for r in items if r["verdict"] == "pass")
        fails  = sum(1 for r in items if r["verdict"] == "fail")
        skips  = sum(1 for r in items if r["verdict"] == "skip")
        n      = len(items)
        denom  = n - skips
        tsr    = (passes / denom) if denom else 0.0

        latencies = []
        for r in items:
            try:
                v = float(r.get("elapsed_ms", "0") or "0")
                if v > 0:
                    latencies.append(v)
            except ValueError:
                pass
        p50 = statistics.median(latencies) if latencies else 0.0

        n_template_skips = sum(
            1 for r in items
            if r["verdict"] == "fail" and "no target_template supplied" in r.get("notes", "")
        )

        out.append({
            "method": method,
            "n_tasks": n,
            "pass": passes,
            "fail": fails,
            "skip": skips,
            "TSR": f"{tsr:.4f}",
            "latency_p50_ms": f"{p50:.1f}",
            "n_template_skips_or_unsupplied": n_template_skips,
            "lines_of_code": LOC.get(method, "?"),
            "dependencies": DEPS.get(method, "?"),
        })
    return out


def per_task_pivot(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_task: Dict[str, Dict[str, str]] = {}
    for r in rows:
        d = by_task.setdefault(r["task"], {
            "task": r["task"],
            "instruction": r["instruction"],
            "is_negative": r["is_negative"],
        })
        d[r["method"]] = r["verdict"]
    return sorted(by_task.values(), key=lambda d: d["task"])


def write_csv(path: Path, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})
    print(f"  wrote {path.relative_to(REPO)}  ({len(rows)} rows)")


def make_chart(summary: List[Dict[str, str]], visclick_tsr: float | None) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  (matplotlib not installed; skipping bar chart)")
        return

    methods = [r["method"] for r in summary]
    tsr = [float(r["TSR"]) * 100 for r in summary]
    if visclick_tsr is not None:
        methods.append("VisClick (full)")
        tsr.append(visclick_tsr * 100)

    colours = {
        "template":  "#cc4444",
        "ocr_only":  "#3a8fbf",
        "pywinauto": "#d9a000",
        "VisClick (full)": "#3aa05e",
    }
    bar_colours = [colours.get(m, "#888888") for m in methods]

    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    bars = ax.bar(methods, tsr, color=bar_colours, edgecolor="black", linewidth=0.6)
    for b, v in zip(bars, tsr):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}%",
                ha="center", va="bottom", fontsize=10)
    ax.set_ylabel("Task Success Rate (TSR), %")
    ax.set_title("Phase 1.C / 1.D — Method comparison on T01–T15"
                 + (" (VisClick = Phase 2 placeholder)" if visclick_tsr is not None else ""))
    ax.set_ylim(0, 110)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, linestyle=":", linewidth=0.5)
    fig.tight_layout()
    FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG, dpi=150)
    print(f"  wrote {FIG.relative_to(REPO)}")


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--visclick-tsr", type=float, default=None,
                   help="Phase 2 TSR for VisClick full pipeline (0..1) to include "
                        "as a 4th bar. Omit to plot the three baselines only.")
    args = p.parse_args(argv)

    rows = load_rows()
    print(f"Loaded {len(rows)} rows from {RESULTS.relative_to(REPO)}")

    summary = per_method_summary(rows)
    write_csv(SUMMARY, summary, [
        "method", "n_tasks", "pass", "fail", "skip", "TSR",
        "latency_p50_ms", "n_template_skips_or_unsupplied",
        "lines_of_code", "dependencies",
    ])

    pivot = per_task_pivot(rows)
    write_csv(PIVOT, pivot, [
        "task", "instruction", "is_negative", "template", "ocr_only", "pywinauto",
    ])

    print("\n=== Per-method TSR ===")
    print(f"{'method':14s} {'n':>3s} {'pass':>4s} {'fail':>4s} {'skip':>4s} {'TSR':>7s} {'p50_ms':>9s}")
    for r in summary:
        print(f"{r['method']:14s} {r['n_tasks']:>3} {r['pass']:>4} {r['fail']:>4} "
              f"{r['skip']:>4} {float(r['TSR']):>6.1%} {float(r['latency_p50_ms']):>9.1f}")

    make_chart(summary, args.visclick_tsr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
