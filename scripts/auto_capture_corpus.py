"""
Background screenshot collector for D-06 (unlabelled desktop corpus).

Captures the active monitor every `--interval` seconds and writes the PNG
under `<root>/<app_bucket>/<timestamp>.png`, where `<app_bucket>` is derived
from the foreground window's process name (e.g. `chrome`, `code`, `notepad`).
The script is meant to be left running in the background while the user
works normally; over a couple of days this accumulates a diverse unlabelled
corpus suitable for self-supervised pre-training (Phase 4.4 / D-02).

Run on Windows as administrator so the F10 stop hotkey works globally.

Example:
    .\\.venv\\Scripts\\python.exe scripts\\auto_capture_corpus.py \
        --interval 60 \
        --root %USERPROFILE%\\Documents\\visclick_data\\desktop_unlabeled \
        --max 2000

Stops on F10, on reaching `--max`, or on Ctrl+C.

See `docs/PHASE_WORKLOG.md` Section 2.1 for context.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import os
import re
import sys
import time
from pathlib import Path

try:
    import mss
except ImportError:  # pragma: no cover - dependency hint only
    raise SystemExit("pip install mss") from None

try:
    import keyboard
except ImportError:  # pragma: no cover
    raise SystemExit("pip install keyboard") from None


_DEFAULT_BUCKET = "unknown"


def _foreground_process_name() -> str:
    """Return a lower-case slug for the foreground window's process, or unknown.

    Windows-only; uses ctypes against user32 + psapi. Returns _DEFAULT_BUCKET on
    any failure so the capture loop never dies because of a transient WinAPI
    error.
    """
    if sys.platform != "win32":
        return _DEFAULT_BUCKET
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)

        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return _DEFAULT_BUCKET

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == 0:
            return _DEFAULT_BUCKET

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not handle:
            return _DEFAULT_BUCKET
        try:
            buf = ctypes.create_unicode_buffer(512)
            length = psapi.GetModuleBaseNameW(handle, None, buf, 512)
            if length == 0:
                return _DEFAULT_BUCKET
            name = buf.value
        finally:
            kernel32.CloseHandle(handle)

        slug = name.lower()
        if slug.endswith(".exe"):
            slug = slug[:-4]
        slug = re.sub(r"[^a-z0-9_-]+", "_", slug).strip("_")
        return slug or _DEFAULT_BUCKET
    except Exception:
        return _DEFAULT_BUCKET


def _capture_once(out_root: Path, monitor: int) -> tuple[Path, str]:
    bucket = _foreground_process_name()
    folder = out_root / bucket
    folder.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = folder / f"{stamp}.png"
    with mss.mss() as sct:
        sct.shot(mon=monitor, output=str(path))
    return path, bucket


def _file_hash(path: Path, block: int = 65_536) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        while True:
            chunk = f.read(block)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _count_existing(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for p in root.rglob("*.png"))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Background unlabelled-corpus capture (D-06).")
    p.add_argument(
        "--root",
        default=os.path.expanduser(r"~\Documents\visclick_data\desktop_unlabeled"),
        help="Output root folder (per-app subfolders created automatically).",
    )
    p.add_argument("--interval", type=int, default=60, help="Seconds between captures (default 60).")
    p.add_argument("--max", type=int, default=2000, help="Stop after this many PNGs in root (default 2000).")
    p.add_argument("--monitor", type=int, default=-1, help="mss monitor index, -1 = all (default -1).")
    p.add_argument(
        "--dedup",
        action="store_true",
        help="Discard the new PNG if its SHA1 matches the immediately previous capture for the same app.",
    )
    p.add_argument(
        "--stop-key",
        default="f10",
        help="Hotkey that ends the loop (default F10; needs admin terminal to grab globally).",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    out_root = Path(args.root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    existing = _count_existing(out_root)
    print(f"[info] root: {out_root}")
    print(f"[info] existing PNGs in root: {existing}")
    print(f"[info] interval: {args.interval}s | max: {args.max} | dedup: {args.dedup}")
    print(f"[info] press {args.stop_key.upper()} to stop (admin terminal required for global hotkey).")
    print("[info] running. minimise this window and use your computer normally.")

    last_hash_per_bucket: dict[str, str] = {}
    captured = 0
    try:
        while True:
            if keyboard.is_pressed(args.stop_key):
                print(f"[stop] {args.stop_key.upper()} pressed.")
                break

            path, bucket = _capture_once(out_root, args.monitor)

            kept = True
            if args.dedup:
                h = _file_hash(path)
                prev = last_hash_per_bucket.get(bucket)
                if prev == h:
                    try:
                        path.unlink()
                    except OSError:
                        pass
                    kept = False
                else:
                    last_hash_per_bucket[bucket] = h

            if kept:
                captured += 1
                total = existing + captured
                print(f"[{captured:4d}] {bucket:>20s}  {path.name}  (total {total})")
                if total >= args.max:
                    print(f"[done] reached --max ({args.max}). stopping.")
                    break

            for _ in range(args.interval * 10):
                if keyboard.is_pressed(args.stop_key):
                    break
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n[stop] ctrl-c.")

    final_total = _count_existing(out_root)
    print(f"[done] session captured: {captured}  |  total in root: {final_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
