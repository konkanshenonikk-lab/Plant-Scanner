"""Plant species identification - the "what plant is this leaf from?" expert.

Two PlantNet-300K models (ResNet18 + MobileNetV3-Small, trained independently
on the same 1,081 species) plus test-time-augmentation (TTA) voting. Label
space is complementary to the crop CNN: mostly European weeds/ornamentals and
houseplants, and it contains NONE of the 14 crop species, so the two experts
never compete - the CNN owns crops, this owns everything else.

Why the elaborate gating: measured top-1 accuracy of these models on web
photos is only ~30% (their advertised 75.8% is on PlantNet's own field photos),
and their errors are confident (foxglove -> Galega officinalis at 0.92). So we
only claim "identified" when the evidence holds together:

    top-5 genus coherence  OR  same genus across 7 TTA views
    AND top-1 confidence   >= 0.60
    AND top-1 margin       >= 0.30

Calibrated on 20 labelled photos (verify_mapping.py / tta_species.py):
4 accepts, all 4 correct (100% precision, 50% recall). When it cannot prove an
answer it says so instead of guessing - which is exactly the behaviour asked
for: "it should tell if the leaf is identified or not".
"""

import io
import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import torch
from PIL import Image
from torchvision import models, transforms

from i18n import EVIDENCE, tr

RESNET_REPO = "cpoisson/plantnet300k-resnet18"
MOBILENET_REPO = "cpoisson/plantnet300k-mobilenetv3-small"
NUM_CLASSES = 1081

WEIGHTS_PATH = Path(
    r"D:\huggingface_cache\hub\models--cpoisson--plantnet300k-resnet18"
    r"\snapshots\d15cde6e60e07c40369f597467e63bb99a8034b9"
)
SPECIES_JSON = WEIGHTS_PATH / "plantnet300K_species_id_2_name.json"

# ---- acceptance thresholds (calibrated: 100% precision / 50% recall) --------
MIN_CONFIDENCE = 0.60
MIN_MARGIN = 0.30
# a leaf-likeness floor shared with the CNN gate: flat/synthetic images fail
MIN_TEXTURE_ROUGHNESS = 8.0

_TENSOR_TRANSFORM = transforms.ToTensor()
_NORMALIZE = transforms.Normalize(
    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
)


def tidy(name: str) -> str:
    """'Lactuca virosa L.' -> 'Lactuca virosa' (drops trailing author abbrev.)."""
    parts = name.replace("\ufffd", "").strip().split()
    if len(parts) > 2 and len(parts[-1]) <= 5 and parts[-1].endswith("."):
        parts = parts[:-1]
    return " ".join(parts)


def genus_of(name: str) -> str:
    return name.split()[0].lower() if name else ""


def texture_roughness(image_bytes: bytes) -> float:
    """Local texture strength; flat synthetic images score near zero.

    Same metric as the CNN gate (model.py) - real leaves measured 13.9-26.7,
    flat/gradient images 0.1-1.0, UI screenshots 4-12.
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((256, 256))
    grey = np.asarray(image, dtype=np.float32).mean(axis=2)
    return float(
        np.abs(np.diff(grey, axis=0)).mean() + np.abs(np.diff(grey, axis=1)).mean()
    )


def _tta_views(img: Image.Image) -> list[torch.Tensor]:
    """7 deterministic views: center, H-flip, 4 corners, gentle zoom."""
    w, h = img.size
    side = min(w, h)
    views = [
        transforms.Compose(
            [transforms.Resize(256), transforms.CenterCrop(224), _TENSOR_TRANSFORM, _NORMALIZE]
        )(img),
        transforms.Compose(
            [transforms.Resize(256), transforms.CenterCrop(224), _TENSOR_TRANSFORM, _NORMALIZE]
        )(ImageOps_hflip(img)),
    ]

    def crop(box):
        return transforms.Compose(
            [transforms.Resize((224, 224)), _TENSOR_TRANSFORM, _NORMALIZE]
        )(img.crop(box))

    half = side // 2
    views += [
        crop((0, 0, half, half)),
        crop((w - half, 0, w, half)),
        crop((0, h - half, half, h)),
        crop((w - half, h - half, w, h)),
    ]
    m = int(side * 0.1)
    views.append(crop((m, m, w - m, h - m)))
    return views


def ImageOps_hflip(img: Image.Image) -> Image.Image:
    from PIL import ImageOps

    return ImageOps.mirror(img)


class SpeciesIdentifier:
    def __init__(self) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.resnet = None
        self.mobilenet = None
        self.index_to_name: list[str] = []
        self.error: str | None = None
        self._load()

    def _load(self) -> None:
        try:
            from huggingface_hub import hf_hub_download

            if not (WEIGHTS_PATH / "plantnet_resnet18.pth").exists():
                raise FileNotFoundError("PlantNet ResNet18 weights missing (D:\\huggingface_cache)")

            names = json.loads(SPECIES_JSON.read_text(encoding="utf-8"))
            # train.py used ImageFolder: class index = folder order; the repo's
            # own demo maps index -> sorted taxon id, which we verified against
            # author-curated images (Nymphaea alba -> "Nymphaea alba", 0.99).
            self.index_to_name = [tidy(names[k]) for k in sorted(names, key=int)]

            self.resnet = models.resnet18(weights=None, num_classes=NUM_CLASSES)
            self.resnet.load_state_dict(
                torch.load(
                    hf_hub_download(RESNET_REPO, "plantnet_resnet18.pth"),
                    map_location="cpu", weights_only=True,
                )
            )
            self.resnet = self.resnet.to(self.device).eval()

            self.mobilenet = models.mobilenet_v3_small(weights=None, num_classes=NUM_CLASSES)
            self.mobilenet.load_state_dict(
                torch.load(
                    hf_hub_download(MOBILENET_REPO, "plantnet_mobilenetv3.pth"),
                    map_location="cpu", weights_only=True,
                )
            )
            self.mobilenet = self.mobilenet.to(self.device).eval()
            print(
                f"[species] PlantNet-300K ready: ResNet18 + MobileNetV3 "
                f"({len(self.index_to_name)} species, TTA gating)"
            )
        except Exception as exc:  # noqa: BLE001
            self.error = str(exc)
            print(f"[species] unavailable: {exc}")

    @property
    def available(self) -> bool:
        return self.resnet is not None

    @torch.inference_mode()
    def identify(self, image_bytes: bytes, top_k: int = 3) -> dict:
        """Identify the species, or honestly report that we could not.

        Returns a dict with:
          status        'identified' | 'not_identified'
          name          latin name (when identified)
          confidence    top-1 probability
          evidence      human-readable reasons supporting the verdict
          reasons       why we refused (when not identified)
          alternatives  top-k guesses regardless of verdict
        """
        if self.resnet is None:
            return {"status": "not_identified", "reasons": ["model_unavailable"],
                    "evidence": [], "alternatives": []}

        roughness = texture_roughness(image_bytes)
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        batch = torch.stack(_tta_views(img)).to(self.device)

        probs_r = torch.softmax(self.resnet(batch), dim=1).cpu().numpy()
        probs_m = torch.softmax(self.mobilenet(batch), dim=1).cpu().numpy()

        base_r, base_m = probs_r[0], probs_m[0]
        order = base_r.argsort()[::-1]
        top_idx = order[:top_k]

        name = self.index_to_name[int(order[0])]
        confidence = float(base_r[order[0]])
        margin = float(base_r[order[0]] - base_r[order[1]]) if len(order) > 1 else confidence
        eps = 1e-12
        entropy = float(-(base_r * np.log(base_r + eps)).sum()) / float(np.log(len(base_r)))

        # signal 1: top-5 all one genus
        top5_genera = {genus_of(self.index_to_name[int(i)]) for i in base_r.argsort()[::-1][:5]}
        coherence = len(top5_genera) == 1

        # signal 2: same genus across all 7 crops/flips of the photo
        view_genera = [genus_of(self.index_to_name[int(p.argmax())]) for p in probs_r]
        stable = len(set(view_genera)) == 1
        stable_fraction = view_genera.count(view_genera[0]) / len(view_genera)

        # signal 3: the independent MobileNet agrees on the genus
        agree = genus_of(self.index_to_name[int(base_m.argmax())]) == genus_of(name)

        reasons = []
        if roughness < MIN_TEXTURE_ROUGHNESS:
            reasons.append("no_leaf_texture")
        if confidence < MIN_CONFIDENCE:
            reasons.append("low_confidence")
        if margin < MIN_MARGIN:
            reasons.append("close_call")
        if not (coherence or stable):
            reasons.append("inconsistent")

        # Evidence is carried as (key, params) so i18n.py can render it in any
        # language; `evidence` keeps the English strings for logs/scripts.
        if reasons:
            status = "not_identified"
            evidence_keys: list[dict] = []
        else:
            status = "identified"
            evidence_keys = []
            if coherence:
                evidence_keys.append({"key": "evidence.top5_genus", "params": {}})
            if stable:
                evidence_keys.append(
                    {
                        "key": "evidence.tta_stable",
                        "params": {"pct": f"{stable_fraction:.0%}"},
                    }
                )
            if agree:
                evidence_keys.append({"key": "evidence.mnet_agrees", "params": {}})
            if not agree:
                evidence_keys.append({"key": "evidence.mnet_lone", "params": {}})

        evidence = [
            tr("en", EVIDENCE, e["key"], **e["params"]) for e in evidence_keys
        ]

        return {
            "status": status,
            "name": name if status == "identified" else None,
            "best_guess": name,
            "confidence": round(confidence, 4),
            "margin": round(margin, 4),
            "entropy": round(entropy, 4),
            "texture_roughness": round(roughness, 3),
            "signals": {
                "coherence": coherence,
                "stable": stable,
                "stable_fraction": round(stable_fraction, 3),
                "agree": agree,
            },
            "evidence": evidence,
            "evidence_keys": evidence_keys,
            "reasons": reasons,
            "alternatives": [
                {"name": self.index_to_name[int(i)], "confidence": round(float(base_r[int(i)]), 4)}
                for i in top_idx
            ],
        }


species_identifier = SpeciesIdentifier()
