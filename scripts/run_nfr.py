"""Phase 2.3 — Latency Non-Functional Requirement (§10.1 of the report).

Aggregates the per-(task, method) wall-time measurements that
``run_baselines.py`` already records in ``reports/tables/baseline_results.csv``
and produces:

1. ``reports/tables/nfr_performance.csv`` — per-method latency statistics
   (n, mean, std, median, p90, p95, max) across the 15 evaluated tasks.
2. ``reports/figures/nfr_latency_box.png`` — box plot of per-method
   latency distributions (skipped silently if matplotlib missing).

We deliberately reuse the elapsed_ms numbers from the orchestrator runs
rather than firing up a separate timing harness:
  - they were measured **on the user's actual Windows desktop**, so the
    laptop/CPU/IO mix is the right one for the dissertation;
  - they cover **the same workload** the TSR table cites (T01..T15), so
    latency and accuracy are directly comparable;
  - the alternative (a 20-rep loop with --auto) would still need the
    same predict() entry points and would just inflate the same numbers.

If you want tighter variance bounds later, re-run::

    py -3 scripts/run_baselines.py --auto --only-method visclick --no-gui

multiple times and union the CSV rows; this script keeps the median
honest because it filters out elapsed_ms == 0 rows (rows skipped by
``--skip-X`` or no-template-supplied paths).

CLI::

    py -3 scripts/run_nfr.py
    py -3 scripts/run_nfr.py --csv reports/tables/baseline_results.csv \
                             --out reports/tables/nfr_performance.csv
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
OUT_CSV = REPO / "reports" / "tables" / "nfr_performance.csv"
OUT_PNG = REPO / "reports" / "figures" / "nfr_latency_box.png"

METHOD_ORDER = ["pywinauto", "ocr_only", "template", "visclick"]


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    sv = sorted(values)
    if pct <= 0:
        return sv[0]
    if pct >= 100:
        return sv[-1]
    k = (len(sv) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sv) - 1)
    if f == c:
        return sv[f]
    return sv[f] + (sv[c] - sv[f]) * (k - f)


def aggregate(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Group elapsed_ms by method and compute summary stats."""
    by_method: Dict[str, List[float]] = {}
    for r in rows:
        try:
            v = float(r.get("elapsed_ms", "0") or "0")
        except ValueError:
            continue
        if v <= 0:
            continue
        by_method.setdefault(r["method"], []).append(v)

    ordered = [m for m in METHOD_ORDER if m in by_method]
    ordered += [m for m in by_method if m not in ordered]

    out = []
    for m in ordered:
        v = by_method[m]
        out.append({
            "method": m,
            "n": len(v),
            "mean_ms": f"{statistics.fmean(v):.1f}",
            "std_ms": f"{statistics.pstdev(v):.1f}" if len(v) > 1 else "0.0",
            "min_ms": f"{min(v):.1f}",
            "median_ms": f"{statistics.median(v):.1f}",
            "p90_ms": f"{_percentile(v, 90):.1f}",
            "p95_ms": f"{_percentile(v, 95):.1f}",
            "max_ms": f"{max(v):.1f}",
        })
    return out, by_method


def write_csv(stats: List[Dict[str, str]], path: Path) -> None:
    fields = ["method", "n", "mean_ms", "std_ms", "min_ms",
              "median_ms", "p90_ms", "p95_ms", "max_ms"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for s in stats:
            w.writerow(s)
    print(f"  wrote {path.relative_to(REPO)}  ({len(stats)} rows)")


def make_chart(by_method: Dict[str, List[float]], path: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  (matplotlib not installed; skipping latency box plot)")
        return

    methods = [m for m in METHOD_ORDER if m in by_method]
    methods += [m for m in by_method if m not in methods]
    data = [by_method[m] for m in methods]

    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    bp = ax.boxplot(data, labels=methods, showmeans=True, patch_artist=True,
                    whis=(5, 95))

    colours = {
        "template":  "#cc4444",
        "ocr_only":  "#3a8fbf",
        "pywinauto": "#d9a000",
        "visclick":  "#3aa05e",
    }
    for patch, m in zip(bp["boxes"], methods):
        patch.set_facecolor(colours.get(m, "#888888"))
        patch.set_alpha(0.7)

    ax.set_yscale("log")
    ax.set_ylabel("Latency per task (ms, log scale)")
    ax.set_title("Phase 2.3 — Per-task wall-time latency on T01..T15"
                 " (n=15 per method)")
    ax.yaxis.grid(True, which="both", linestyle=":", linewidth=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    print(f"  wrote {path.relative_to(REPO)}")


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--csv", type=Path, default=RESULTS,
                   help=f"input baseline_results.csv (default: "
                        f"{RESULTS.relative_to(REPO)})")
    p.add_argument("--out", type=Path, default=OUT_CSV,
                   help=f"output nfr_performance.csv (default: "
                        f"{OUT_CSV.relative_to(REPO)})")
    p.add_argument("--png", type=Path, default=OUT_PNG,
                   help=f"output latency box plot (default: "
                        f"{OUT_PNG.relative_to(REPO)})")
    args = p.parse_args(argv)

    if not args.csv.is_file():
        print(f"ERROR: {args.csv} not found. Run scripts/run_baselines.py first.",
              file=sys.stderr)
        return 2

    try:
        f = args.csv.open(newline="")
    except OSError as e:
        print(f"ERROR: cannot open {args.csv}: {e}", file=sys.stderr)
        return 2
    with f:
        try:
            rows = list(csv.DictReader(f))
        except UnicodeDecodeError:
            f.close()
            with args.csv.open(newline="", encoding="cp1252") as f2:
                rows = list(csv.DictReader(f2))

    print(f"Loaded {len(rows)} rows from {args.csv.relative_to(REPO)}")
    stats, by_method = aggregate(rows)
    write_csv(stats, args.out)

    print("\n=== Per-method latency (ms) ===")
    print(f"{'method':12s} {'n':>3s} {'mean':>8s} {'std':>8s} "
          f"{'median':>8s} {'p90':>8s} {'p95':>8s} {'max':>8s}")
    for s in stats:
        print(f"{s['method']:12s} {int(s['n']):>3d} {float(s['mean_ms']):>8.1f} "
              f"{float(s['std_ms']):>8.1f} {float(s['median_ms']):>8.1f} "
              f"{float(s['p90_ms']):>8.1f} {float(s['p95_ms']):>8.1f} "
              f"{float(s['max_ms']):>8.1f}")

    make_chart(by_method, args.png)
    return 0


if __name__ == "__main__":
    sys.exit(main())
