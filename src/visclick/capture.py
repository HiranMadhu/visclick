"""Screenshot capture (primary monitor) via mss."""

import mss
import numpy as np


def grab() -> np.ndarray:
    """Return full primary monitor as RGB uint8, shape (H, W, 3)."""
    with mss.mss() as sct:
        m = sct.monitors[1]
        img = np.array(sct.grab(m))[:, :, :3][:, :, ::-1]
    return img
