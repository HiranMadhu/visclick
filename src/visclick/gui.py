"""Tkinter front-end for VisClick.

Three workflows in one window:

1. Natural-language click:   instruction = "click Save"
                              → screenshot → detect → OCR → match → click
2. Manual coordinate click:  instruction = "xy 1234 567"  (or "1234, 567")
                              → screenshot is skipped; cursor moves to that
                              virtual-desktop coord and clicks. Use this to
                              verify the click plumbing is sound before
                              trusting the model.
3. Coordinate picker:        press "Pick Coordinates (5s)"
                              → window minimises, count-down, position read.
                              Use this to find a known button's coordinates by
                              hovering the cursor over it.

Run: ``python -m visclick.gui``  (or ``python -m visclick`` after install)
"""
from __future__ import annotations

import os
import re
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Optional, Tuple

import numpy as np
import pyautogui
from PIL import Image

from visclick.act import click_box, click_xy
from visclick.capture import find_pyautogui_primary, grab, list_monitors, set_dpi_awareness
from visclick.detect import CLASS_NAMES, Detector
from visclick.match import best_box
from visclick.ocr import ocr_box

_DEFAULT_WEIGHTS = "weights/visclick.onnx"

# Match instructions like "xy 500 400", "1234, 567", "click 100 200", "click xy 50,50".
_MANUAL_RE = re.compile(
    r"^\s*(?:(?:click|xy|goto|move|at)\s+)*(-?\d+)\s*[,\s]\s*(-?\d+)\s*$",
    re.IGNORECASE,
)


def _parse_manual_xy(text: str) -> Optional[Tuple[int, int]]:
    m = _MANUAL_RE.match(text or "")
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


class VisClickApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("VisClick")
        root.geometry("560x620")
        root.minsize(500, 560)

        set_dpi_awareness()

        self._detector: Optional[Detector] = None
        self._detector_path: Optional[str] = None
        self._busy = False

        frm = ttk.Frame(root, padding=12)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="Instruction").grid(row=0, column=0, sticky="w")
        self.instruction_var = tk.StringVar(value="click Save")
        self.instruction_entry = ttk.Entry(frm, textvariable=self.instruction_var)
        self.instruction_entry.grid(row=0, column=1, columnspan=2, sticky="ew", padx=(8, 0))
        self.instruction_entry.bind("<Return>", lambda _e: self.on_run())

        hint = ttk.Label(
            frm,
            text="Tip: type \"xy 1234 567\" to skip detection and click that virtual-desktop coord.",
            foreground="#666",
            font=("Segoe UI", 8),
        )
        hint.grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 0))

        ttk.Label(frm, text="Countdown (s)").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.countdown_var = tk.IntVar(value=5)
        self.countdown_spin = ttk.Spinbox(frm, from_=0, to=30, width=5,
                                          textvariable=self.countdown_var)
        self.countdown_spin.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        ttk.Label(frm, text="Monitor").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.monitor_var = tk.StringVar()
        self.monitor_combo = ttk.Combobox(frm, textvariable=self.monitor_var,
                                          state="readonly", width=44)
        self.monitor_combo.grid(row=3, column=1, columnspan=2, sticky="ew",
                                padx=(8, 0), pady=(8, 0))
        self._populate_monitors()

        self.dry_run_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Dry run (don't actually click)",
                        variable=self.dry_run_var).grid(row=4, column=0, columnspan=2,
                                                         sticky="w", pady=(8, 0))

        ttk.Label(frm, text="Weights").grid(row=5, column=0, sticky="w", pady=(8, 0))
        self.weights_var = tk.StringVar(value=_DEFAULT_WEIGHTS)
        ttk.Entry(frm, textvariable=self.weights_var).grid(
            row=5, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        ttk.Button(frm, text="…", width=3, command=self.on_browse_weights).grid(
            row=5, column=2, sticky="w", padx=(4, 0), pady=(8, 0))

        btn_row = ttk.Frame(frm)
        btn_row.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(14, 4))
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)
        self.run_btn = ttk.Button(btn_row, text="Run", command=self.on_run)
        self.run_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.pick_btn = ttk.Button(btn_row, text="Pick Coordinates (5 s)",
                                   command=self.on_pick)
        self.pick_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(frm, textvariable=self.status_var, anchor="w",
                  foreground="#444").grid(row=7, column=0, columnspan=3, sticky="ew")

        ttk.Label(frm, text="Log").grid(row=8, column=0, sticky="w", pady=(8, 0))
        log_frame = ttk.Frame(frm)
        log_frame.grid(row=9, column=0, columnspan=3, sticky="nsew", pady=(2, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        frm.rowconfigure(9, weight=1)
        self.log = tk.Text(log_frame, height=14, wrap="word", state="disabled",
                           font=("Consolas", 9))
        self.log.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.log["yscrollcommand"] = sb.set

        self._log("VisClick GUI started. Three modes:")
        self._log("  1. Natural language:  click Save")
        self._log("  2. Manual coordinate: xy 1234 567   (or 1234, 567)")
        self._log("  3. Pick a coord:      hover target, press 'Pick Coordinates (5 s)'")
        self._log(f"weights: {self.weights_var.get()}")
        pa_w, pa_h = pyautogui.size()
        self._log(f"pyautogui screen size: {pa_w} x {pa_h}")

    def _populate_monitors(self) -> None:
        primary = find_pyautogui_primary()
        items = ["auto (pyautogui-primary)"]
        for m in list_monitors():
            i = m["index"]
            if i == 0:
                continue
            tag = "  [primary]" if i == primary else ""
            items.append(f"{i}: {m['width']}x{m['height']} @({m['left']},{m['top']}){tag}")
        self.monitor_combo["values"] = items
        self.monitor_combo.current(0)

    def _selected_monitor_index(self) -> int:
        s = self.monitor_var.get()
        if not s or s.startswith("auto"):
            return 0
        try:
            return int(s.split(":", 1)[0])
        except ValueError:
            return 0

    def _log(self, msg: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
        self.root.update_idletasks()

    def _set_status(self, msg: str) -> None:
        self.status_var.set(msg)
        self.root.update_idletasks()

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.run_btn.configure(state=state)
        self.pick_btn.configure(state=state)
        self.instruction_entry.configure(state=state)
        self.countdown_spin.configure(state=state)
        self.monitor_combo.configure(state="disabled" if busy else "readonly")

    def on_browse_weights(self) -> None:
        path = filedialog.askopenfilename(
            title="Select ONNX weights",
            filetypes=[("ONNX models", "*.onnx"), ("All files", "*.*")],
        )
        if path:
            self.weights_var.set(path)

    # ---------- main Run path ----------

    def on_run(self) -> None:
        if self._busy:
            return
        instruction = self.instruction_var.get().strip()
        if not instruction:
            self._log("ERROR: instruction is empty")
            return

        self._set_busy(True)
        countdown = int(self.countdown_var.get())
        mon_idx = self._selected_monitor_index()
        dry_run = bool(self.dry_run_var.get())

        self._log("")
        manual = _parse_manual_xy(instruction)
        if manual is not None:
            self._log(f"MANUAL coord mode: target=({manual[0]}, {manual[1]})  "
                      f"countdown={countdown}s  dry_run={dry_run}")
            self._set_status("Manual click — switch to your target window…")
            self._countdown_then(countdown, lambda: self._do_manual_click(manual, dry_run))
            return

        weights = self.weights_var.get().strip()
        if not os.path.isfile(weights):
            self._log(f"ERROR: weights not found: {weights}")
            self._set_busy(False)
            return

        self._log(f"DETECT mode: instruction={instruction!r}  countdown={countdown}s  "
                  f"monitor={mon_idx or 'auto'}  dry_run={dry_run}")
        self._set_status("Switch to your target window…")
        self._countdown_then(countdown, lambda: self._do_pipeline(
            instruction, weights, mon_idx, dry_run))

    def _countdown_then(self, remaining: int, action) -> None:
        if remaining > 0:
            self._set_status(f"Capturing in {remaining}…")
            self._log(f"  capturing in {remaining}...")
            self.root.after(1000, self._countdown_then, remaining - 1, action)
            return
        self.root.iconify()
        self.root.after(250, action)

    # ---------- manual coord click ----------

    def _do_manual_click(self, target: Tuple[int, int], dry_run: bool) -> None:
        try:
            tx, ty = target
            pre = pyautogui.position()
            self._log(f"cursor before move: ({pre.x}, {pre.y})")
            self._log(f"target:             ({tx}, {ty})")
            self._log(f"delta:              ({tx - pre.x:+d}, {ty - pre.y:+d})  pixels")
            if dry_run:
                self._log("DRY-RUN: no click sent.")
                self._set_status(f"Manual: would click ({tx}, {ty}).")
            else:
                t0 = time.perf_counter()
                click_xy(tx, ty, dwell=0.3)
                dt = (time.perf_counter() - t0) * 1000
                post = pyautogui.position()
                self._log(f"cursor after click: ({post.x}, {post.y})")
                arrival = (post.x - tx, post.y - ty)
                self._log(f"arrival error:      ({arrival[0]:+d}, {arrival[1]:+d})  "
                          f"pixels  ({'OK' if abs(arrival[0]) <= 2 and abs(arrival[1]) <= 2 else 'BAD — DPI?'})")
                self._log(f"move + click took {dt:.0f} ms")
                self._set_status(f"Clicked ({tx}, {ty}).")
        except Exception as e:
            self._log(f"ERROR: {type(e).__name__}: {e}")
            self._set_status("Error — see log.")
        finally:
            self.root.deiconify()
            self.root.lift()
            self._set_busy(False)

    # ---------- detect → pick → click ----------

    def _do_pipeline(self, instruction: str, weights: str, mon_idx: int, dry_run: bool) -> None:
        try:
            t0 = time.perf_counter()
            actual_mon = mon_idx if mon_idx > 0 else find_pyautogui_primary()
            img, left, top = grab(actual_mon)
            t_grab = time.perf_counter()
            self._log(f"captured monitor {actual_mon}: "
                      f"{img.shape[1]}x{img.shape[0]} @({left},{top})  "
                      f"({(t_grab - t0)*1000:.0f} ms)")
            pa_w, pa_h = pyautogui.size()
            self._log(f"pyautogui screen: {pa_w}x{pa_h}  "
                      f"({'matches capture' if (pa_w, pa_h) == (img.shape[1], img.shape[0]) and (left, top) == (0, 0) else 'differs from captured monitor'})")

            if self._detector is None or self._detector_path != weights:
                self._log("loading detector…")
                self._detector = Detector(weights)
                self._detector_path = weights
            t_load = time.perf_counter()

            raw = self._detector.predict(img, conf=0.25, iou=0.5)
            t_det = time.perf_counter()
            self._log(f"detector: {len(raw)} boxes in {(t_det - t_load)*1000:.0f} ms")

            if not raw:
                self._log("FAIL: detector found no candidates")
                self._set_status("No candidates found.")
                return

            boxes_with_text = []
            for cls, xyxy, cf in raw:
                txt = ocr_box(img, xyxy)
                boxes_with_text.append((cls, xyxy, cf, txt))
            t_ocr = time.perf_counter()
            self._log(f"OCR: {(t_ocr - t_det)*1000:.0f} ms")
            self._log("all candidates (monitor-local centers):")
            for cls, xyxy, cf, txt in boxes_with_text[:12]:
                cxl = (xyxy[0] + xyxy[2]) / 2
                cyl = (xyxy[1] + xyxy[3]) / 2
                self._log(f"  {CLASS_NAMES[cls]:11s} ({cxl:>6.0f}, {cyl:>6.0f})  "
                          f"conf={cf:.2f}  text={txt!r}")

            pick = best_box(instruction, boxes_with_text)
            if pick is None:
                self._log("FAIL: no candidates after matching")
                self._set_status("No match.")
                return
            score, cls, xyxy, cf, txt = pick
            cx_local = (xyxy[0] + xyxy[2]) / 2
            cy_local = (xyxy[1] + xyxy[3]) / 2
            cx_abs = cx_local + left
            cy_abs = cy_local + top
            self._log(f"PICKED: {CLASS_NAMES[cls]} text={txt!r} "
                      f"det_conf={cf:.2f} match_score={score:.0f}")
            self._log(f"  monitor-local center: ({cx_local:.0f}, {cy_local:.0f})")
            self._log(f"  virtual-desktop:      ({cx_abs:.0f}, {cy_abs:.0f})")
            pre = pyautogui.position()
            self._log(f"  cursor before move:   ({pre.x}, {pre.y})  "
                      f"delta-to-target=({cx_abs - pre.x:+.0f}, {cy_abs - pre.y:+.0f})")

            if dry_run:
                self._log("DRY-RUN: no click sent.")
                self._set_status(f"Picked {CLASS_NAMES[cls]} {txt!r} (dry-run).")
            else:
                ax, ay = click_box(xyxy, offset=(left, top))
                t_click = time.perf_counter()
                post = pyautogui.position()
                arrival = (post.x - cx_abs, post.y - cy_abs)
                self._log(f"  cursor after click:   ({post.x}, {post.y})")
                self._log(f"  arrival error:        ({arrival[0]:+.0f}, {arrival[1]:+.0f}) "
                          f"pixels  ({'OK' if abs(arrival[0]) <= 2 and abs(arrival[1]) <= 2 else 'BAD — DPI scaling?'})")
                self._log(f"CLICKED ({ax:.0f}, {ay:.0f})  ({(t_click - t_ocr)*1000:.0f} ms)")
                self._set_status(f"Clicked {CLASS_NAMES[cls]} {txt!r}.")

            t_total = time.perf_counter() - t0
            self._log(f"total: {t_total*1000:.0f} ms")
        except Exception as e:
            self._log(f"ERROR: {type(e).__name__}: {e}")
            self._set_status("Error — see log.")
        finally:
            self.root.deiconify()
            self.root.lift()
            self._set_busy(False)

    # ---------- coordinate picker ----------

    def on_pick(self) -> None:
        if self._busy:
            return
        self._set_busy(True)
        self._log("")
        self._log("PICK MODE: hover the cursor over your target. Window minimising in 1 s…")
        self._set_status("Hover the cursor over the target…")
        self.root.after(1000, self._pick_step, 5, [])

    def _pick_step(self, remaining: int, samples: list) -> None:
        if remaining == 5:
            self.root.iconify()
        try:
            pos = pyautogui.position()
            samples.append((pos.x, pos.y))
            self._set_status(f"Sampling cursor — {remaining} s left  "
                              f"(now at {pos.x}, {pos.y})")
        except Exception:
            pass
        if remaining > 0:
            self.root.after(1000, self._pick_step, remaining - 1, samples)
            return
        self.root.deiconify()
        self.root.lift()
        if not samples:
            self._log("PICK: no samples collected.")
            self._set_status("Pick failed.")
            self._set_busy(False)
            return
        last = samples[-1]
        self._log(f"PICK: cursor was at virtual-desktop ({last[0]}, {last[1]}) "
                  f"at the end of the 5-s window.")
        if len(samples) > 1:
            self._log("       trajectory: " + " → ".join(f"({x},{y})" for x, y in samples))
        # Fill the instruction box for one-click reuse
        self.instruction_var.set(f"xy {last[0]} {last[1]}")
        self._set_status(f"Cursor was at ({last[0]}, {last[1]}). "
                          f"Press Run to click there.")
        self._set_busy(False)


def main() -> int:
    root = tk.Tk()
    VisClickApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
