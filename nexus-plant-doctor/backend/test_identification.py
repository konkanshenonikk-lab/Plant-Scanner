"""Unit test for the species-identification verdict.

Expect: labelled photos of label-set species may be accepted (and must be
correct when accepted); junk and crop leaves must be NOT identified.

Run:  python test_identification.py
"""

import glob
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("KERAS_BACKEND", "torch")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from species_id import species_identifier  # noqa: E402

TMP = os.environ.get("TEMP", ".")
SAMPLES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "frontend", "public", "samples",
)
ANSWERABLE = [
    "Nymphaea alba", "Papaver rhoeas", "Cirsium vulgare", "Lamium album",
    "Hypericum perforatum", "Mercurialis annua", "Pelargonium zonale",
    "Tradescantia pallida", "Lactuca serriola", "Lupinus polyphyllus",
    "Anemone nemorosa", "Sedum album", "Alocasia macrorrhizos",
]


def genus(n: str) -> str:
    return n.split()[0].lower() if n else ""


def run(path: str, truth: str | None, tag: str) -> None:
    with open(path, "rb") as fh:
        res = species_identifier.identify(fh.read())
    if res["status"] == "identified":
        if truth is None:
            grade = "FALSE-POSITIVE"
        elif genus(res["name"]) == genus(truth):
            grade = "correct" if res["name"].split()[:2] == truth.split()[:2] else "genus-ok"
        else:
            grade = "FALSE-ID"
        detail = f"{res['name']:34s} conf={res['confidence']:.2f} {res['signals']}"
    else:
        grade = "-          "
        detail = f"best={res.get('best_guess', '?'):30s} reasons={res['reasons']}"
    print(f"{tag:9s} {res['status']:14s} {grade:15s} {detail}  <- {os.path.basename(path)}")


if __name__ == "__main__":
    if not species_identifier.available:
        sys.exit(f"unavailable: {species_identifier.error}")

    print("--- labelled photos of label-set species (accepting is allowed) ---")
    for path in sorted(glob.glob(os.path.join(TMP, "vm_*.jpg"))):
        m = re.match(r"vm_(\d+)_\d+\.jpg", os.path.basename(path))
        truth = ANSWERABLE[int(m.group(1))] if m else None
        run(path, truth, "truth")

    print("\n--- crop leaves (CNN's job - species expert should decline) ---")
    for name in sorted(os.listdir(SAMPLES)):
        run(os.path.join(SAMPLES, name), None, "crop")

    print("\n--- junk (must be NOT identified) ---")
    for pattern in ["calib_flat.png", "calib_noise.png", "calib_canvas.png",
                    "calib_dog.jpg", r"opencode-browser-*\0\screenshot.png"]:
        for path in sorted(glob.glob(os.path.join(TMP, pattern))):
            run(path, None, "junk")
