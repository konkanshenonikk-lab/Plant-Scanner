"""Measure simple texture statistics to separate flat/synthetic images from
real leaf photos. Prints the dominant-colour fraction and greyscale std for
every calibration image.
"""

import glob
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(ROOT, "frontend", "public", "samples")


def stats(path: str) -> tuple[float, float, float]:
    img = Image.open(path).convert("RGB").resize((256, 256))
    a = np.asarray(img).astype(np.int32)

    # Dominant colour bucket (16-level bins) as a fraction of all pixels.
    bins = a // 16
    keys = bins[..., 0] * 289 + bins[..., 1] * 17 + bins[..., 2]
    _, counts = np.unique(keys, return_counts=True)
    dominant = counts.max() / keys.size

    # Greyscale spread = texture.
    grey = a.mean(axis=2)
    std = grey.std()

    # Local roughness: mean absolute difference between neighbouring pixels.
    roughness = float(np.abs(np.diff(grey, axis=0)).mean() + np.abs(np.diff(grey, axis=1)).mean())
    return dominant, std, roughness


def report(path: str) -> None:
    dominant, std, roughness = stats(path)
    print(
        f"dominant={dominant:5.2f}  grey_std={std:5.1f}  rough={roughness:5.2f}  "
        f"<- {os.path.basename(path)}"
    )


if __name__ == "__main__":
    print("--- known-good leaves ---")
    for name in sorted(os.listdir(SAMPLES)):
        report(os.path.join(SAMPLES, name))
    print("--- known-bad ---")
    tmp = os.environ.get("TEMP", ".")
    for pattern in ["calib_flat.png", "calib_noise.png", "calib_wheat.jpg", "calib_dog.jpg",
                    r"opencode-browser-*\0\screenshot.png"]:
        for p in glob.glob(os.path.join(tmp, pattern)):
            report(p)
    for p in sys.argv[1:]:
        report(p)
