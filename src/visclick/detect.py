"""ONNX YOLOv8 inference (Ultralytics export, fixed batch=1, imgsz=640).

The exported model output has shape (1, 4 + nc, 8400) where:
  - 4 = box [cx, cy, w, h] in letterboxed pixel space.
  - nc = number of classes (6 for VisClick).
  - 8400 = anchor-free predictions across the 3 detection heads.

Postprocess flow (matches Ultralytics' ``Detect`` head):
  1. Transpose to (8400, 4+nc).
  2. Per-row argmax over class scores → (cls_id, cls_conf).
  3. Filter rows where cls_conf < ``conf``.
  4. Convert xywh → xyxy (still in letterboxed space).
  5. Class-agnostic NMS via cv2.dnn.NMSBoxes.
  6. Map xyxy back to original image space using the letterbox scale + pad.
"""
from __future__ import annotations

from typing import List, Tuple

import cv2
import numpy as np
import onnxruntime as ort

Box4 = Tuple[float, float, float, float]


CLASS_NAMES: tuple[str, ...] = (
    "button", "text", "text_input", "icon", "menu", "checkbox",
)


def letterbox(
    img: np.ndarray, new_shape: int = 640, color: tuple[int, int, int] = (114, 114, 114)
) -> tuple[np.ndarray, float, tuple[int, int]]:
    """Resize + pad to a square ``new_shape`` keeping aspect ratio."""
    h, w = img.shape[:2]
    r = min(new_shape / h, new_shape / w)
    new_w, new_h = int(round(w * r)), int(round(h * r))
    dw, dh = (new_shape - new_w) / 2, (new_shape - new_h) / 2
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    padded = cv2.copyMakeBorder(resized, top, bottom, left, right,
                                cv2.BORDER_CONSTANT, value=color)
    return padded, r, (left, top)


class Detector:
    def __init__(self, onnx_path: str, imgsz: int = 640, providers: list[str] | None = None) -> None:
        if providers is None:
            providers = ["CPUExecutionProvider"]
        self.sess = ort.InferenceSession(onnx_path, providers=providers)
        self.input_name = self.sess.get_inputs()[0].name
        self.output_name = self.sess.get_outputs()[0].name
        self.imgsz = imgsz
        self.providers = providers

    def predict(
        self,
        img_rgb: np.ndarray,
        conf: float = 0.25,
        iou: float = 0.5,
    ) -> List[Tuple[int, Box4, float]]:
        """Run inference on an HxWx3 RGB uint8 image. Return list of (cls_id, xyxy, conf)."""
        if img_rgb.ndim != 3 or img_rgb.shape[2] != 3:
            raise ValueError(f"expected HxWx3 RGB image, got shape {img_rgb.shape}")
        h0, w0 = img_rgb.shape[:2]

        lb, scale, (pad_x, pad_y) = letterbox(img_rgb, self.imgsz)
        x = lb.transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        out = self.sess.run([self.output_name], {self.input_name: x})[0]
        return self._postprocess(out, w0, h0, scale, pad_x, pad_y, conf, iou)

    def _postprocess(
        self,
        out: np.ndarray,
        w0: int,
        h0: int,
        scale: float,
        pad_x: int,
        pad_y: int,
        conf: float,
        iou: float,
    ) -> List[Tuple[int, Box4, float]]:
        pred = out[0].T
        nc = pred.shape[1] - 4
        if nc <= 0:
            return []
        boxes_xywh = pred[:, :4]
        scores = pred[:, 4:4 + nc]
        cls_id = scores.argmax(axis=1)
        cls_conf = scores.max(axis=1)

        keep = cls_conf >= conf
        if not keep.any():
            return []
        boxes_xywh = boxes_xywh[keep]
        cls_id = cls_id[keep]
        cls_conf = cls_conf[keep]

        cx, cy, w, h = boxes_xywh.T
        x1 = cx - w / 2; y1 = cy - h / 2
        x2 = cx + w / 2; y2 = cy + h / 2
        boxes_xyxy_lb = np.stack([x1, y1, x2, y2], axis=1)

        nms_input = [[float(b[0]), float(b[1]), float(b[2] - b[0]), float(b[3] - b[1])]
                     for b in boxes_xyxy_lb]
        idx = cv2.dnn.NMSBoxes(nms_input, cls_conf.tolist(), conf, iou)
        if isinstance(idx, tuple) or len(idx) == 0:
            return []
        idx = np.array(idx).flatten()
        boxes_xyxy_lb = boxes_xyxy_lb[idx]
        cls_id = cls_id[idx]
        cls_conf = cls_conf[idx]

        x1 = (boxes_xyxy_lb[:, 0] - pad_x) / scale
        y1 = (boxes_xyxy_lb[:, 1] - pad_y) / scale
        x2 = (boxes_xyxy_lb[:, 2] - pad_x) / scale
        y2 = (boxes_xyxy_lb[:, 3] - pad_y) / scale
        x1 = np.clip(x1, 0, w0 - 1); y1 = np.clip(y1, 0, h0 - 1)
        x2 = np.clip(x2, 0, w0 - 1); y2 = np.clip(y2, 0, h0 - 1)

        results: List[Tuple[int, Box4, float]] = []
        for i in range(len(idx)):
            results.append((
                int(cls_id[i]),
                (float(x1[i]), float(y1[i]), float(x2[i]), float(y2[i])),
                float(cls_conf[i]),
            ))
        return results
