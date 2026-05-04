"""Tkinter front-end for VisClick.

Workflow:
1. User types an instruction (e.g. "click Save") in the text box.
2. User presses Run. A countdown starts (default 5s).
3. The GUI window minimises so it doesn't appear in the screenshot.
4. After the countdown, the screen is captured, the model runs, and the
   matched element is clicked.
5. The GUI window restores and the result is shown in the log.

Run: ``python -m visclick.gui``  (or ``python -m visclick`` after install)
"""
from __future__ import annotations

import os
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Optional

import numpy as np
from PIL import Image

from visclick.act import click_box
from visclick.capture import find_pyautogui_primary, grab, list_monitors, set_dpi_awareness
from visclick.detect import CLASS_NAMES, Detector
from visclick.match import best_box
from visclick.ocr import ocr_box

_DEFAULT_WEIGHTS = "weights/visclick.onnx"


class VisClickApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("VisClick")
        root.geometry("520x520")
        root.minsize(460, 480)

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

        ttk.Label(frm, text="Countdown (s)").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.countdown_var = tk.IntVar(value=5)
        self.countdown_spin = ttk.Spinbox(frm, from_=0, to=30, width=5,
                                          textvariable=self.countdown_var)
        self.countdown_spin.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        ttk.Label(frm, text="Monitor").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.monitor_var = tk.StringVar()
        self.monitor_combo = ttk.Combobox(frm, textvariable=self.monitor_var,
                                          state="readonly", width=44)
        self.monitor_combo.grid(row=2, column=1, columnspan=2, sticky="ew",
                                padx=(8, 0), pady=(8, 0))
        self._populate_monitors()

        self.dry_run_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Dry run (don't actually click)",
                        variable=self.dry_run_var).grid(row=3, column=0, columnspan=2,
                                                         sticky="w", pady=(8, 0))

        ttk.Label(frm, text="Weights").grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.weights_var = tk.StringVar(value=_DEFAULT_WEIGHTS)
        ttk.Entry(frm, textvariable=self.weights_var).grid(
            row=4, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        ttk.Button(frm, text="…", width=3, command=self.on_browse_weights).grid(
            row=4, column=2, sticky="w", padx=(4, 0), pady=(8, 0))

        self.run_btn = ttk.Button(frm, text="Run", command=self.on_run)
        self.run_btn.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(14, 4))

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(frm, textvariable=self.status_var, anchor="w",
                  foreground="#444").grid(row=6, column=0, columnspan=3, sticky="ew")

        ttk.Label(frm, text="Log").grid(row=7, column=0, sticky="w", pady=(8, 0))
        log_frame = ttk.Frame(frm)
        log_frame.grid(row=8, column=0, columnspan=3, sticky="nsew", pady=(2, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        frm.rowconfigure(8, weight=1)
        self.log = tk.Text(log_frame, height=12, wrap="word", state="disabled",
                           font=("Consolas", 9))
        self.log.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.log["yscrollcommand"] = sb.set

        self._log("VisClick GUI started. Type an instruction and press Run.")
        self._log(f"Default weights: {self.weights_var.get()}")

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

    def on_run(self) -> None:
        if self._busy:
            return
        instruction = self.instruction_var.get().strip()
        if not instruction:
            self._log("ERROR: instruction is empty")
            return
        weights = self.weights_var.get().strip()
        if not os.path.isfile(weights):
            self._log(f"ERROR: weights not found: {weights}")
            return

        self._set_busy(True)
        countdown = int(self.countdown_var.get())
        mon_idx = self._selected_monitor_index()
        dry_run = bool(self.dry_run_var.get())

        self._log("")
        self._log(f"Run: instruction={instruction!r}  countdown={countdown}s  "
                  f"monitor={mon_idx or 'auto'}  dry_run={dry_run}")
        self._set_status("Switch to your target window…")
        self._countdown_step(countdown, instruction, weights, mon_idx, dry_run)

    def _countdown_step(self, remaining: int, instruction: str, weights: str,
                         mon_idx: int, dry_run: bool) -> None:
        if remaining > 0:
            self._set_status(f"Capturing in {remaining}…")
            self._log(f"  capturing in {remaining}...")
            self.root.after(1000, self._countdown_step, remaining - 1,
                            instruction, weights, mon_idx, dry_run)
            return
        self.root.iconify()
        self.root.after(250, self._do_pipeline, instruction, weights, mon_idx, dry_run)

    def _do_pipeline(self, instruction: str, weights: str, mon_idx: int, dry_run: bool) -> None:
        try:
            t0 = time.perf_counter()
            actual_mon = mon_idx if mon_idx > 0 else find_pyautogui_primary()
            img, left, top = grab(actual_mon)
            t_grab = time.perf_counter()
            self._log(f"captured monitor {actual_mon}: "
                      f"{img.shape[1]}x{img.shape[0]} @({left},{top})  "
                      f"({(t_grab - t0)*1000:.0f} ms)")

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

            pick = best_box(instruction, boxes_with_text)
            if pick is None:
                self._log("FAIL: no candidates after matching")
                self._set_status("No match.")
                return
            score, cls, xyxy, cf, txt = pick
            cx_local = (xyxy[0] + xyxy[2]) / 2
            cy_local = (xyxy[1] + xyxy[3]) / 2
            cx_abs, cy_abs = cx_local + left, cy_local + top
            self._log(f"PICKED cls={CLASS_NAMES[cls]} text={txt!r} "
                      f"det_conf={cf:.2f} match_score={score:.0f}")
            self._log(f"  monitor-local center: ({cx_local:.0f}, {cy_local:.0f})")
            self._log(f"  virtual-desktop:      ({cx_abs:.0f}, {cy_abs:.0f})")

            if dry_run:
                self._log("DRY-RUN: no click sent.")
                self._set_status(f"Picked {CLASS_NAMES[cls]} {txt!r} (dry-run).")
            else:
                ax, ay = click_box(xyxy, offset=(left, top))
                t_click = time.perf_counter()
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


def main() -> int:
    root = tk.Tk()
    VisClickApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
