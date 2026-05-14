# Phase worklog (local measurements)

## Phase 1 notes — 14 May 2026

### U-05 — Hardware (`systeminfo` + WMI)

Recorded on SNPS-M8CMYRED1M (Dell Latitude 5450).

- **OS:** Microsoft Windows 11 Enterprise, build 22631.
- **CPU:** Intel(R) Core(TM) Ultra 5 135H — 14 cores, 18 logical processors.
- **RAM:** 32 GB total physical (32,213 MB per `systeminfo`).
- **GPU:** Intel(R) Arc(TM) Graphics (integrated); primary display 1920×1080 per `Win32_VideoController`.

### D-09 — Detector-only speed

Command (repo `visclick/`, venv Python):

`.\.venv\Scripts\python.exe scripts/test_detector.py "<matplotlib sample>\logo2.png" --weights weights/visclick.onnx --bench 50`

- **median_ms:** 67.8  
- **p95_ms:** 79.0  
- Row appended to `tables/detector_latency.csv` (script default path relative to cwd; that folder is gitignored). A copy of this bench row for version control is in `reports/tables/detector_bench_snapshot_2026-05-14.csv`.

### D-11 — Memory (rough)

Method: `psutil.Process().memory_info().rss` sampled during an 80× ONNX `Detector.predict` loop plus three `text_ground(..., engine="easyocr")` calls on the same RGB image (warms EasyOCR / torch path).

- **Peak RSS (approx.):** ~212 MB after detector-only loop; **~764 MB** after EasyOCR-inclusive calls (single process, same session).

Formal `nfr_memory.csv` / soak chart deferred per plan.

### T-04 — Requirements evidence

Draft table: `reports/tables/requirements_evidence.csv`.

### NFR latency refresh

`.\.venv\Scripts\python.exe scripts/run_nfr.py` — regenerated `reports/tables/nfr_performance.csv` and `reports/figures/nfr_latency_box.png` from `baseline_results.csv`.
