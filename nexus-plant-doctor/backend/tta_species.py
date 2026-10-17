"""Can test-time-augmentation (TTA) stability raise recall without losing precision?

For each already-labelled photo (vm_<i>_<j>.jpg, truth = answerable[i]) we
predict under 7 views (center, H-flip, 4 corner crops, 1 zoom) and measure how
often the predicted GENUS stays the same. Then compare candidate accept rules.

Run:  python tta_species.py
"""

import glob
import json
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("KERAS_BACKEND", "torch")

import torch
from huggingface_hub import hf_hub_download
from PIL import Image
from torchvision import models, transforms

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from species_id import SPECIES_JSON, tidy  # noqa: E402

NUM_CLASSES = 1081
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TMP = os.environ.get("TEMP", ".")
NORMALIZE = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

ANSWERABLE = [
    "Nymphaea alba", "Papaver rhoeas", "Cirsium vulgare", "Lamium album",
    "Hypericum perforatum", "Mercurialis annua", "Pelargonium zonale",
    "Tradescantia pallida", "Lactuca serriola", "Lupinus polyphyllus",
    "Anemone nemorosa", "Sedum album", "Alocasia macrorrhizos",
]


def views(img: Image.Image) -> list[torch.Tensor]:
    """7 deterministic views of the same photo."""
    w, h = img.size
    side = min(w, h)
    out = []
    base = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(), NORMALIZE,
    ])
    out.append(base(img))
    out.append(base(transforms.functional.hflip(img)))

    def crop(box):
        return transforms.Compose([
            transforms.Resize((224, 224)), transforms.ToTensor(), NORMALIZE,
        ])(img.crop(box))

    s = side
    out.append(crop((0, 0, s // 2, s // 2)))
    out.append(crop((w - s // 2, 0, w, s // 2)))
    out.append(crop((0, h - s // 2, s // 2, h)))
    out.append(crop((w - s // 2, h - s // 2, w, h)))
    m = int(side * 0.1)
    out.append(crop((m, m, w - m, h - m)))
    return out


def main() -> None:
    names = json.loads(SPECIES_JSON.read_text(encoding="utf-8"))
    index_to_name = [tidy(names[k]) for k in sorted(names, key=int)]

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

    def genus(n: str) -> str:
        return n.split()[0].lower()

    files = sorted(glob.glob(os.path.join(TMP, "vm_*.jpg")))
    rows = []
    for path in files:
        m = re.match(r"vm_(\d+)_(\d+)\.jpg", os.path.basename(path))
        if not m:
            continue
        truth = ANSWERABLE[int(m.group(1))]

        img = Image.open(path).convert("RGB")
        vs = views(img)
        batch = torch.stack(vs).to(DEVICE)
        with torch.inference_mode():
            rp = torch.softmax(resnet(batch), dim=1).cpu()
            mp = torch.softmax(mobilenet(batch), dim=1).cpu()

        base_rp, base_mp = rp[0], mp[0]
        ri, mi = int(base_rp.argmax()), int(base_mp.argmax())
        r_name, m_name = index_to_name[ri], index_to_name[mi]
        top5 = base_rp.topk(5).indices.tolist()
        coherence = len({index_to_name[k].split()[0] for k in top5}) == 1
        conf = float(base_rp[ri])
        margin = float(base_rp[ri] - base_rp[base_rp.argsort(descending=True)[1]])

        # genus stability across views
        gens = [genus(index_to_name[int(p.argmax())]) for p in rp]
        stable = len(set(gens)) == 1
        stable_frac = gens.count(gens[0]) / len(gens)
        # correct-view vote share (how often views give the truth's genus)
        truth_votes = sum(1 for g in gens if g == genus(truth)) / len(gens)

        agree = genus(r_name) == genus(m_name)
        grade = ("species" if " ".join(r_name.split()[:2]).lower() == truth.lower()
                 else ("genus" if genus(r_name) == genus(truth) else "WRONG"))
        rows.append(dict(truth=truth, r=r_name, grade=grade, conf=conf, margin=margin,
                         coherence=coherence, agree=agree, stable=stable,
                         stable_frac=stable_frac, truth_votes=truth_votes))
        print(f"{truth:24s} {r_name[:34]:34s} {grade:7s} conf={conf:.2f} "
              f"coh={'Y' if coherence else '.'} agr={'Y' if agree else '.'} "
              f"stable={'Y' if stable else '.'} ({stable_frac:.0%}) truthvotes={truth_votes:.0%}")

    good = [r for r in rows if r["grade"] != "WRONG"]
    bad = [r for r in rows if r["grade"] == "WRONG"]
    print(f"\ngood={len(good)} bad={len(bad)}")

    rules = {
        "coherence": lambda r: r["coherence"],
        "stable genus (all views)": lambda r: r["stable"],
        "stable_frac>=0.85": lambda r: r["stable_frac"] >= 0.85,
        "agree + conf>=0.6 + margin>=0.4": lambda r: r["agree"] and r["conf"] >= 0.6 and r["margin"] >= 0.4,
        "coherence + conf>=0.6": lambda r: r["coherence"] and r["conf"] >= 0.6,
        "coherence OR stable": lambda r: r["coherence"] or r["stable"],
        "coherence OR stable_frac>=0.85": lambda r: r["coherence"] or r["stable_frac"] >= 0.85,
        "(coherence OR stable) + conf>=0.6 + margin>=0.3":
            lambda r: (r["coherence"] or r["stable"]) and r["conf"] >= 0.6 and r["margin"] >= 0.3,
    }
    print(f"\n{'rule':42s} {'accept':16s} {'precision':10s} {'recall(good)'}")
    for name, fn in rules.items():
        acc = [r for r in rows if fn(r)]
        wrong_acc = [r for r in acc if r["grade"] == "WRONG"]
        prec = 1 - len(wrong_acc) / max(len(acc), 1)
        rec = len([r for r in acc if r["grade"] != "WRONG"]) / max(len(good), 1)
        print(f"{name:42s} {len(acc):2d}/{len(rows)}        {prec:8.0%}  {rec:8.0%}")


if __name__ == "__main__":
    main()
