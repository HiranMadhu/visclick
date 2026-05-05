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
import subprocess
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import List, Optional, Tuple

import numpy as np
import pyautogui
from PIL import Image, ImageDraw, ImageFont

from visclick.act import click_box, click_xy
from visclick.capture import find_pyautogui_primary, grab, list_monitors, set_dpi_awareness
from visclick.detect import CLASS_NAMES, Detector
from visclick.match import _is_class_only_target, _target_phrase, best_box
from visclick.ocr import ocr_box, ocr_status, text_ground

_DEFAULT_WEIGHTS = "weights/visclick.onnx"
_OVERLAY_PATH = "screenshots/last_overlay.png"

_COLORS = [
    (255, 107, 107), (78, 205, 196), (255, 230, 109),
    (160, 108, 213), (6, 167, 125), (255, 166, 43),
]


def _save_overlay(
    img_rgb: np.ndarray,
    boxes_with_text: List[Tuple[int, Tuple[float, float, float, float], float, str]],
    picked_xyxy: Optional[Tuple[float, float, float, float]],
    out_path: str,
) -> str:
    pil = Image.fromarray(img_rgb).copy()
    draw = ImageDraw.Draw(pil)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except OSError:
            font = ImageFont.load_default()
    for cls, xyxy, conf, text in boxes_with_text:
        color = _COLORS[cls % len(_COLORS)]
        x1, y1, x2, y2 = (int(round(v)) for v in xyxy)
        is_picked = picked_xyxy is not None and tuple(xyxy) == tuple(picked_xyxy)
        draw.rectangle([x1, y1, x2, y2], outline=color, width=4 if is_picked else 2)
        label = f"{CLASS_NAMES[cls]} {conf:.2f}"
        if text:
            label += f" | {text[:30]}"
        draw.text((x1, max(0, y1 - 16)), label, fill=color, font=font)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    pil.save(out_path)
    return str(Path(out_path).resolve())


def _open_in_default_viewer(path: str) -> None:
    """Open the given file with the OS's default app (Windows: image viewer)."""
    try:
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass

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

        ttk.Label(frm, text="OCR").grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.ocr_var = tk.StringVar(value="easyocr")
        ttk.Combobox(
            frm, textvariable=self.ocr_var, state="readonly", width=14,
            values=["tesseract", "easyocr", "both", "none"],
        ).grid(row=4, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        ttk.Label(frm, text="Conf threshold").grid(row=4, column=1, sticky="e", padx=(0, 80), pady=(8, 0))
        self.conf_var = tk.DoubleVar(value=0.25)
        ttk.Spinbox(frm, from_=0.05, to=0.90, increment=0.05, width=5,
                    textvariable=self.conf_var, format="%.2f").grid(
            row=4, column=2, sticky="w", pady=(8, 0))

        self.dry_run_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Dry run (don't actually click)",
                        variable=self.dry_run_var).grid(row=5, column=0, columnspan=2,
                                                         sticky="w", pady=(8, 0))
        self.show_overlay_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm, text="Open overlay PNG after run",
                        variable=self.show_overlay_var).grid(row=5, column=1, columnspan=2,
                                                              sticky="e", pady=(8, 0))

        ttk.Label(frm, text="Weights").grid(row=6, column=0, sticky="w", pady=(8, 0))
        self.weights_var = tk.StringVar(value=_DEFAULT_WEIGHTS)
        ttk.Entry(frm, textvariable=self.weights_var).grid(
            row=6, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        ttk.Button(frm, text="…", width=3, command=self.on_browse_weights).grid(
            row=6, column=2, sticky="w", padx=(4, 0), pady=(8, 0))

        btn_row = ttk.Frame(frm)
        btn_row.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(14, 4))
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)
        self.run_btn = ttk.Button(btn_row, text="Run", command=self.on_run)
        self.run_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.pick_btn = ttk.Button(btn_row, text="Pick Coordinates (5 s)",
                                   command=self.on_pick)
        self.pick_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(frm, textvariable=self.status_var, anchor="w",
                  foreground="#444").grid(row=8, column=0, columnspan=3, sticky="ew")

        ttk.Label(frm, text="Log").grid(row=9, column=0, sticky="w", pady=(8, 0))
        log_frame = ttk.Frame(frm)
        log_frame.grid(row=10, column=0, columnspan=3, sticky="nsew", pady=(2, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        frm.rowconfigure(10, weight=1)
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
        st = ocr_status()
        for name in ("easyocr", "tesseract"):
            info = st[name]
            mark = "✓" if info.get("available") else "✗"
            detail = info.get("version") or info.get("reason") or ""
            self._log(f"OCR {name:9s}: {mark} {detail}")
        if not st["easyocr"].get("available") and not st["tesseract"].get("available"):
            self._log("WARNING: no OCR backend available. "
                      "`pip install easyocr` is the simplest fix.")
        self._log("After each Run, an overlay PNG with all detected boxes is saved")
        self._log(f"  to {_OVERLAY_PATH} and opened automatically.")

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

        ocr_engine = self.ocr_var.get() or "easyocr"
        if ocr_engine != "none":
            st = ocr_status()
            if not st[ocr_engine].get("available"):
                other = "easyocr" if ocr_engine == "tesseract" else "tesseract"
                if st[other].get("available"):
                    self._log(f"WARNING: OCR={ocr_engine} unavailable "
                              f"({st[ocr_engine].get('reason', '')}); "
                              f"auto-switching to {other}.")
                    ocr_engine = other
                    self.ocr_var.set(other)
                else:
                    self._log("WARNING: no OCR backend available; matching by "
                              "class+conf only.")
                    ocr_engine = "none"
                    self.ocr_var.set("none")
        try:
            conf = float(self.conf_var.get())
        except (tk.TclError, ValueError):
            conf = 0.25
        show_overlay = bool(self.show_overlay_var.get())
        self._log(f"DETECT mode: instruction={instruction!r}  countdown={countdown}s  "
                  f"monitor={mon_idx or 'auto'}  ocr={ocr_engine}  conf={conf:.2f}  "
                  f"dry_run={dry_run}")
        self._set_status("Switch to your target window…")
        self._countdown_then(countdown, lambda: self._do_pipeline(
            instruction, weights, mon_idx, dry_run, ocr_engine, conf, show_overlay))

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

    def _do_pipeline(self, instruction: str, weights: str, mon_idx: int,
                     dry_run: bool, ocr_engine: str = "tesseract",
                     conf: float = 0.25, show_overlay: bool = True) -> None:
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

            raw = self._detector.predict(img, conf=conf, iou=0.5)
            t_det = time.perf_counter()
            self._log(f"detector: {len(raw)} boxes (conf>={conf:.2f}) in {(t_det - t_load)*1000:.0f} ms")

            if not raw:
                self._log("FAIL: detector found no candidates")
                if show_overlay:
                    p = _save_overlay(img, [], None, _OVERLAY_PATH)
                    self._log(f"overlay saved: {p}")
                    _open_in_default_viewer(p)
                self._set_status("No candidates found.")
                return

            boxes_with_text = []
            for cls, xyxy, cf in raw:
                txt = ocr_box(img, xyxy, engine=ocr_engine)
                boxes_with_text.append((cls, xyxy, cf, txt))
            t_ocr = time.perf_counter()
            self._log(f"OCR ({ocr_engine}): {(t_ocr - t_det)*1000:.0f} ms")
            self._log("all candidates (monitor-local centers):")
            for cls, xyxy, cf, txt in boxes_with_text[:12]:
                cxl = (xyxy[0] + xyxy[2]) / 2
                cyl = (xyxy[1] + xyxy[3]) / 2
                self._log(f"  {CLASS_NAMES[cls]:11s} ({cxl:>6.0f}, {cyl:>6.0f})  "
                          f"conf={cf:.2f}  text={txt!r}")

            pick = best_box(instruction, boxes_with_text)

            if pick is None:
                target = _target_phrase(instruction)
                if target and not _is_class_only_target(target):
                    self._log(f"FALLBACK: detector miss; running full-image OCR for {target!r}…")
                    eng = ocr_engine if ocr_engine != "none" else "easyocr"
                    hits = text_ground(img, target, engine=eng, min_similarity=70)
                    self._log(f"  text_ground found {len(hits)} hit(s)")
                    for xyxy_h, text_h, sim_h, ocr_conf_h in hits[:5]:
                        cxh = (xyxy_h[0] + xyxy_h[2]) / 2
                        cyh = (xyxy_h[1] + xyxy_h[3]) / 2
                        self._log(f"    {text_h!r:25s} center=({cxh:>6.0f},{cyh:>6.0f})  "
                                  f"sim={sim_h:.0f}  ocr_conf={ocr_conf_h:.0f}")
                    if hits:
                        xyxy_h, text_h, sim_h, ocr_conf_h = hits[0]
                        boxes_with_text.append((1, xyxy_h, ocr_conf_h / 100.0, text_h))
                        pick = (sim_h, 1, xyxy_h, ocr_conf_h / 100.0, text_h)

            if pick is None:
                target = instruction.lower().replace("click", "").strip().strip("'\"")
                self._log(f"FAIL: neither detector nor full-image OCR found {target!r}.")
                self._log("  Possible causes:")
                self._log(f"  - the model didn't detect that element on this UI")
                self._log(f"    (try lowering the Conf threshold and re-running)")
                self._log(f"  - OCR couldn't read the text (try OCR=easyocr)")
                self._log(f"  - that text isn't on screen at all")
                self._log("  Workaround: hover the target, press 'Pick Coordinates (5 s)',")
                self._log("              then Run with the auto-filled 'xy …' instruction.")
                if show_overlay:
                    p = _save_overlay(img, boxes_with_text, None, _OVERLAY_PATH)
                    self._log(f"overlay saved: {p}")
                    _open_in_default_viewer(p)
                self._set_status(f"No box matches {target!r}.")
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

            if show_overlay:
                p = _save_overlay(img, boxes_with_text, xyxy, _OVERLAY_PATH)
                self._log(f"overlay saved: {p}")
                _open_in_default_viewer(p)

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
