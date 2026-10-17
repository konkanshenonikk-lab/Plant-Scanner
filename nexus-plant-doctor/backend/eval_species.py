"""Evaluate abstention signals for species identification.

Ground truth: 4 author-curated demo images + 9 Wikimedia species photos we
fetched by name. Junk: dog / noise / flat / canvas / screenshots.

For each image we record:
  - ResNet18 top-1 (name, conf)
  - MobileNetV3 top-1 (independent architecture, same label space)
  - whether the two agree (at species and genus level)
  - genus coherence of the ResNet top-5
  - whether the answer matches ground truth (species / genus)

Goal: find which combination reliably separates CORRECT from CONFIDENT-BUT-WRONG.

Run:  python eval_species.py
"""

import glob
import json
import os
import subprocess
import sys
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("KERAS_BACKEND", "torch")

import torch
from huggingface_hub import hf_hub_download
from PIL import Image
from torchvision import models

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from species_id import SPECIES_JSON, TRANSFORM, tidy  # noqa: E402

NUM_CLASSES = 1081
MOBILENET_REPO = "cpoisson/plantnet300k-mobilenetv3-small"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TMP = os.environ.get("TEMP", ".")
SAMPLES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "frontend", "public", "samples",
)

# ---- ground truth: (file, expected species or genus) -------------------------
GROUND_TRUTH: list[tuple[str, str]] = []

ORDER = ["Taraxacum officinale", "Digitalis purpurea", "Nymphaea alba", "sedum"]


def commons_images(genus_species: str, limit: int = 3) -> list[str]:
    api = (
        "https://commons.wikimedia.org/w/api.php?action=query&generator=search"
        "&gsrsearch=" + genus_species.replace(" ", "%20") + "%20leaf"
        f"&gsrnamespace=6&gsrlimit={limit}&prop=imageinfo&iiprop=url&iiurlwidth=700&format=json"
    )
    out = subprocess.run(
        ["curl.exe", "-s", api], capture_output=True, text=True, timeout=60
    ).stdout
    urls = []
    try:
        pages = json.loads(out)["query"]["pages"]
        for page in pages.values():
            urls.append(page["imageinfo"][0]["thumburl"])
    except Exception:  # noqa: BLE001
        pass
    return urls


def genus(name: str) -> str:
    return name.split()[0].lower() if name else ""


def main() -> None:
    # Author demo images (filename = ground truth)
    demo_truth = {
        "Taraxacum_officinale_02_Fr_web_2015_fullsize.jpg": "Taraxacum officinale",
        "digitalis_purpurea.jpg": "Digitalis purpurea",
        "nymphea_alba.jpg": "Nymphaea alba",
        "sedum.jpg": "Sedum",
    }
    for fn, truth in demo_truth.items():
        p = hf_hub_download("cpoisson/plantnet300k", f"examples/{fn}", repo_type="space")
        GROUND_TRUTH.append((p, truth))

    # Wikimedia photos by species name
    for i, sp in enumerate(["Taraxacum officinale", "Urtica dioica", "Quercus robur"]):
        for j, url in enumerate(commons_images(sp)):
            dest = os.path.join(TMP, f"gt_{i}_{j}.jpg")
            subprocess.run(["curl.exe", "-sL", "-o", dest, url], timeout=60)
            if os.path.exists(dest) and os.path.getsize(dest) > 5000:
                GROUND_TRUTH.append((dest, sp))

    # ---- load both models ----
    names = json.loads(SPECIES_JSON.read_text(encoding="utf-8"))
    index_to_name = [tidy(names[k]) for k in sorted(names, key=int)]

    resnet = models.resnet18(weights=None, num_classes=NUM_CLASSES)
    resnet.load_state_dict(
        torch.load(
            hf_hub_download("cpoisson/plantnet300k-resnet18", "plantnet_resnet18.pth"),
            map_location="cpu", weights_only=True,
        )
    )
    resnet = resnet.to(DEVICE).eval()

    mobilenet = models.mobilenet_v3_small(weights=None, num_classes=NUM_CLASSES)
    mobilenet.load_state_dict(
        torch.load(
            hf_hub_download(MOBILENET_REPO, "plantnet_mobilenetv3.pth"),
            map_location="cpu", weights_only=True,
        )
    )
    mobilenet = mobilenet.to(DEVICE).eval()

    def probs_of(model, path: str) -> torch.Tensor:
        img = Image.open(path).convert("RGB")
        x = TRANSFORM(img).unsqueeze(0).to(DEVICE)
        with torch.inference_mode():
            return torch.softmax(model(x), dim=1)[0].cpu()

    print(f"{'image':28s} {'truth':22s} {'resnet top1':34s} {'mn top1':26s} "
          f"{'agr':4s} {'coh':4s} {'c':4s} {'m':4s} {'ok'}")
    rows = []
    for path, truth in GROUND_TRUTH:
        rp = probs_of(resnet, path)
        mp = probs_of(mobilenet, path)
        ri = int(rp.argmax())
        mi = int(mp.argmax())
        r_name, m_name = index_to_name[ri], index_to_name[mi]

        top5 = rp.topk(5).indices.tolist()
        genera = {index_to_name[i].split()[0] for i in top5}
        coherence = len(genera) == 1

        agree_species = r_name == m_name
        agree_genus = genus(r_name) == genus(m_name)

        conf = float(rp[ri])
        margin = float(rp[ri] - rp[rp.argsort(descending=True)[1]])

        ok_species = r_name.split()[:2] == truth.split()[:2]
        ok_genus = genus(r_name) == genus(truth)
        verdict = "species" if ok_species else ("genus" if ok_genus else "WRONG")

        rows.append(dict(truth=truth, ok=verdict, conf=conf, margin=margin,
                         coherence=coherence, agree_species=agree_species,
                         agree_genus=agree_genus, r=r_name, m=m_name))
        print(
            f"{os.path.basename(path)[:28]:28s} {truth[:22]:22s} {r_name[:34]:34s} "
            f"{m_name[:26]:26s} "
            f"{'Y' if agree_species else ('g' if agree_genus else '.'):4s} "
            f"{'Y' if coherence else '.':4s} {conf:.2f} {margin:.2f} {verdict}"
        )

    # ---- junk (should never be identified) ----
    print("\n--- junk (must be rejected) ---")
    junk = []
    for pattern in ["calib_flat.png", "calib_noise.png", "calib_canvas.png",
                    "calib_dog.jpg", r"opencode-browser-*\0\screenshot.png"]:
        junk += glob.glob(os.path.join(TMP, pattern))
    junk += sorted(glob.glob(os.path.join(SAMPLES, "*.jpg")))
    for path in junk:
        rp = probs_of(resnet, path)
        mp = probs_of(mobilenet, path)
        ri, mi = int(rp.argmax()), int(mp.argmax())
        r_name, m_name = index_to_name[ri], index_to_name[mi]
        top5 = rp.topk(5).indices.tolist()
        coherence = len({index_to_name[i].split()[0] for i in top5}) == 1
        conf = float(rp[ri])
        margin = float(rp[ri] - rp[rp.argsort(descending=True)[1]])
        tag = "CROP(sample)" if path.startswith(SAMPLES) else "junk"
        print(
            f"{tag:12s} {r_name[:34]:34s} {m_name[:26]:26s} "
            f"{'Y' if r_name == m_name else ('g' if genus(r_name) == genus(m_name) else '.'):4s} "
            f"{'Y' if coherence else '.':4s} {conf:.2f} {margin:.2f}  <- {os.path.basename(path)}"
        )

    # ---- signal quality summary ----
    print("\n--- signal quality on ground truth ---")
    correct = [r for r in rows if r["ok"] != "WRONG"]
    wrong = [r for r in rows if r["ok"] == "WRONG"]

    def rate(pred, subset):
        return sum(1 for r in subset if pred(r)) / max(len(subset), 1)

    signals = {
        "agree_species": lambda r: r["agree_species"],
        "agree_genus": lambda r: r["agree_genus"],
        "coherence": lambda r: r["coherence"],
        "conf>=0.6": lambda r: r["conf"] >= 0.6,
        "margin>=0.4": lambda r: r["margin"] >= 0.4,
        "agree_genus AND coherence": lambda r: r["agree_genus"] and r["coherence"],
    }
    for name, fn in signals.items():
        print(f"  {name:30s} pass-rate correct={rate(fn, correct):.0%}  wrong={rate(fn, wrong):.0%}"
              f"   (want: high on correct, LOW on wrong)")


if __name__ == "__main__":
    main()
