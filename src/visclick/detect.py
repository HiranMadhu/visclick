"""ONNX YOLO inference (Ultralytics export)."""

from __future__ import annotations

from typing import List, Tuple

import cv2
import numpy as np
import onnxruntime as ort


class Detector:
    def __init__(self, onnx_path: str) -> None:
        self.sess = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
        self.input_name = self.sess.get_inputs()[0].name

    def predict(
        self, img_rgb: np.ndarray, conf: float = 0.3, iou: float = 0.5
    ) -> List[Tuple[int, Tuple[float, float, float, float], float]]:
        """
        Return list of (class_id, (x1,y1,x2,y2), conf).
        Postprocess is model-specific; refine when exporting from Ultralytics.
        """
        h, w = img_rgb.shape[:2]
        x = cv2.resize(img_rgb, (640, 640))
        x = x.transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        out = self.sess.run(None, {self.input_name: x})[0]
        return self._postprocess(out, w, h, conf, iou)

    def _postprocess(
        self, out: np.ndarray, w: int, h: int, conf: float, iou: float
    ) -> List[Tuple[int, Tuple[float, float, float, float], float]]:
        # Placeholder: wire to your exported nc+4 layout; avoid crashing import.
        _ = (out, w, h, conf, iou)
        return []
