"""Validate + calibrate the PlantNet species identifier.

1. Ground-truth check: download known species photos from Wikimedia Commons and
   confirm the model names them correctly (this also proves the output-index ->
   species-name mapping is right, which ImageFolder's alphabetical ordering
   makes non-obvious).
2. Abstention check: run the crop samples and junk inputs through it.

Run:  python calibrate_species.py
"""

import io
import json
import os
import subprocess
import sys
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("KERAS_BACKEND", "torch")

from PIL import Image

from species_id import SPECIES_JSON, species_identifier

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(ROOT, "frontend", "public", "samples")
TMP = os.environ.get("TEMP", ".")

# Species we can easily source ground-truth photos for.
TARGETS = [
    "Taraxacum officinale",
    "Urtica dioica",
    "Plantago lanceolata",
    "Bellis perennis",
]


def commons_image(genus_species: str) -> str | None:
    """Fetch a Commons photo URL for a species."""
    api = (
        "https://commons.wikimedia.org/w/api.php?action=query&generator=search"
        "&gsrsearch=" + genus_species.replace(" ", "%20") + "%20leaf"
        "&gsrnamespace=6&gsrlimit=1&prop=imageinfo&iiprop=url&iiurlwidth=700&format=json"
    )
    out = subprocess.run(
        ["curl.exe", "-s", api], capture_output=True, text=True, timeout=60
    ).stdout
    try:
        pages = json.loads(out)["query"]["pages"]
        page = next(iter(pages.values()))
        return page["imageinfo"][0]["thumburl"]
    except Exception:  # noqa: BLE001
        return None


def fetch(url: str, dest: str) -> bool:
    subprocess.run(["curl.exe", "-sL", "-o", dest, url], timeout=60)
    return os.path.exists(dest) and os.path.getsize(dest) > 5000


def show(tag: str, res: dict | None) -> None:
    if res is None:
        print(f"  {tag}: unavailable")
        return
    alts = ", ".join(f"{a['name']}={a['confidence']:.2f}" for a in res["alternatives"][:3])
    print(
        f"  {tag}: {res['status']:14s} {res['name']:32s} "
        f"conf={res['confidence']:.2f} margin={res['margin']:.2f} "
        f"H={res['entropy']:.2f} {res['reasons']}\n      top3: {alts}"
    )


if __name__ == "__main__":
    if not species_identifier.available:
        sys.exit(f"species model unavailable: {species_identifier.error}")

    print("=== 1. ground-truth species photos (mapping check) ===")
    for i, target in enumerate(TARGETS):
        url = commons_image(target)
        if not url:
            print(f"  {target}: no image found")
            continue
        dest = os.path.join(TMP, f"species_ref_{i}.jpg")
        if not fetch(url, dest):
            print(f"  {target}: download failed")
            continue
        with open(dest, "rb") as fh:
            res = species_identifier.identify(fh.read())
        show(target, res)
        if res and res["name"].split()[:2] != target.split()[:2]:
            print(
                f"      !! expected {target} - got {res['name']} "
                "(index mapping may be wrong)"
            )

    print("=== 2. crop leaves (CNN's territory - expect NOT confident) ===")
    for name in sorted(os.listdir(SAMPLES)):
        with open(os.path.join(SAMPLES, name), "rb") as fh:
            show(name, species_identifier.identify(fh.read()))

    print("=== 3. junk inputs (expect NOT identified) ===")
    for name in ["calib_flat.png", "calib_noise.png", "calib_canvas.png", "calib_dog.jpg"]:
        path = os.path.join(TMP, name)
        if not os.path.exists(path):
            continue
        with open(path, "rb") as fh:
            show(name, species_identifier.identify(fh.read()))
