"""Calibrate the OOD gate: print confidence + reference similarity per image.

Run with:  python calibrate_gate.py [extra image paths...]
"""

import io
import os
import sys
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("KERAS_BACKEND", "torch")

import numpy as np
from PIL import Image

from model import plant_model

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(ROOT, "frontend", "public", "samples")


def score(path: str) -> None:
    with open(path, "rb") as fh:
        data = fh.read()
    preds, stats = plant_model.predict(data)
    verdict = "ACCEPT " if not stats["uncertain"] else "REJECT "
    cent = stats.get("centroid_similarity")
    print(
        f"{verdict}sim={stats['reference_similarity']!s:6s} "
        f"cent={('%.3f' % cent) if cent is not None else 'n/a  ':5s} "
        f"rough={stats['texture_roughness']:5.1f} "
        f"conf={stats['confidence']:.2f} H={stats['normalised_entropy']:.2f} "
        f"{preds[0]['class']:46s} {stats['reasons']}  <- {os.path.basename(path)}"
    )


def make_flat(path: str) -> None:
    img = Image.new("RGB", (480, 360), "#3b5998")
    Image.fromarray(
        np.linspace(0, 255, 360 * 480 * 3, dtype=np.uint8).reshape(360, 480, 3)
    ).save(path)


def make_noise(path: str) -> None:
    rng = np.random.default_rng(0)
    Image.fromarray(rng.integers(0, 255, (360, 480, 3), dtype=np.uint8)).save(path)


if __name__ == "__main__":
    tmp = os.environ.get("TEMP", ".")
    flat = os.path.join(tmp, "calib_flat.png")
    noise = os.path.join(tmp, "calib_noise.png")
    make_flat(flat)
    make_noise(noise)

    print("--- known-good leaves (PlantVillage, covered crops) ---")
    for name in sorted(os.listdir(SAMPLES)):
        score(os.path.join(SAMPLES, name))

    print("--- known-bad inputs (not leaf photos) ---")
    score(flat)
    score(noise)
    for path in sys.argv[1:]:
        score(path)
