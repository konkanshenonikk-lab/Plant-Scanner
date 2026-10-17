"""Mapping + quality verification using ONLY species present in the label set.

For each label-set species we fetch a Commons photo by exact name and check
whether ResNet18 top-1 names it (species or at least genus), and whether the
two-model acceptance rule says "identified".

This is the test that matters: if the index->name mapping were a permutation,
these would come back as confident names of unrelated species.

Run:  python verify_mapping.py
"""

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
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TMP = os.environ.get("TEMP", ".")

# Species that (a) live in the label set and (b) photograph well on Commons.
CANDIDATES = [
    "Nymphaea alba", "Papaver rhoeas", "Cirsium vulgare", "Lamium album",
    "Hypericum perforatum", "Mercurialis annua", "Pelargonium zonale",
    "Tradescantia pallida", "Lactuca serriola", "Lupinus polyphyllus",
    "Anemone nemorosa", "Sedum album", "Alocasia macrorrhizos", "Aloe vera",
]


def commons_images(sp: str, limit: int = 2) -> list[str]:
    api = (
        "https://commons.wikimedia.org/w/api.php?action=query&generator=search"
        "&gsrsearch=" + sp.replace(" ", "%20") + "%20leaf"
        f"&gsrnamespace=6&gsrlimit={limit}&prop=imageinfo&iiprop=url&iiurlwidth=700&format=json"
    )
    out = subprocess.run(["curl.exe", "-s", api], capture_output=True, text=True, timeout=60).stdout
    urls = []
    try:
        pages = json.loads(out)["query"]["pages"]
        for page in pages.values():
            urls.append(page["imageinfo"][0]["thumburl"])
    except Exception:  # noqa: BLE001
        pass
    return urls


def genus(n: str) -> str:
    return n.split()[0].lower()


def main() -> None:
    names = json.loads(SPECIES_JSON.read_text(encoding="utf-8"))
    index_to_name = [tidy(names[k]) for k in sorted(names, key=int)]
    binomials = {" ".join(n.split()[:2]).lower(): n for n in index_to_name}

    resnet = models.resnet18(weights=None, num_classes=NUM_CLASSES)
    resnet.load_state_dict(torch.load(
        hf_hub_download("cpoisson/plantnet300k-resnet18", "plantnet_resnet18.pth"),
        map_location="cpu", weights_only=True))
    resnet = resnet.to(DEVICE).eval()

    mobilenet = models.mobilenet_v3_small(weights=None, num_classes=NUM_CLASSES)
    mobilenet.load_state_dict(torch.load(
        hf_hub_download("cpoisson/plantnet300k-mobilenetv3-small", "plantnet_mobilenetv3.pth"),
        map_location="cpu", weights_only=True))
    mobilenet = mobilenet.to(DEVICE).eval()

    answerable = [s for s in CANDIDATES if s.lower() in binomials]
    print(f"in label set: {len(answerable)}/{len(CANDIDATES)} -> {answerable}\n")

    def predict(model, path):
        img = Image.open(path).convert("RGB")
        x = TRANSFORM(img).unsqueeze(0).to(DEVICE)
        with torch.inference_mode():
            return torch.softmax(model(x), dim=1)[0].cpu()

    n_species = n_genus = n_wrong = n_acc = n_acc_wrong = 0
    print(f"{'truth':24s} {'resnet top1':38s} {'mobilenet':34s} {'agr coh c    m    verdict'}")
    for i, sp in enumerate(answerable):
        for j, url in enumerate(commons_images(sp)):
            dest = os.path.join(TMP, f"vm_{i}_{j}.jpg")
            subprocess.run(["curl.exe", "-sL", "-o", dest, url], timeout=60)
            if not os.path.exists(dest) or os.path.getsize(dest) < 5000:
                continue
            rp, mp = predict(resnet, dest), predict(mobilenet, dest)
            ri, mi = int(rp.argmax()), int(mp.argmax())
            r_name, m_name = index_to_name[ri], index_to_name[mi]
            top5 = rp.topk(5).indices.tolist()
            coherence = len({index_to_name[k].split()[0] for k in top5}) == 1
            agree = genus(r_name) == genus(m_name)
            conf = float(rp[ri])
            margin = float(rp[ri] - rp[rp.argsort(descending=True)[1]])

            accept = agree and coherence and conf >= 0.6 and margin >= 0.4
            if " ".join(r_name.split()[:2]).lower() == sp.lower():
                grade = "species"; n_species += 1
            elif genus(r_name) == genus(sp):
                grade = "genus"; n_genus += 1
            else:
                grade = "WRONG"; n_wrong += 1
            if accept:
                n_acc += 1
                if grade == "WRONG":
                    n_acc_wrong += 1

            print(f"{sp:24s} {r_name[:38]:38s} {m_name[:34]:34s} "
                  f"{'Y' if agree else '.':3s} {'Y' if coherence else '.':3s} "
                  f"{conf:.2f} {margin:.2f} "
                  f"{'ACCEPT ' if accept else 'reject '}{grade}")

    total = n_species + n_genus + n_wrong
    print(f"\nraw model: species={n_species} genus={n_genus} wrong={n_wrong} "
          f"(top-1 accuracy {n_species}/{total} = {n_species/max(total,1):.0%})")
    print(f"accept rule: accepted={n_acc} accepted-but-wrong={n_acc_wrong} "
          f"precision={1 - n_acc_wrong/max(n_acc,1):.0%} "
          f"recall(species)={n_acc and min(n_acc, n_species)/max(n_species,1):.0%}")


if __name__ == "__main__":
    main()
