"""Second-opinion model: a ViT fine-tuned on the PlantDoc dataset.

PlantDoc contains real *field* photographs (unlike PlantVillage's segmented
studio leaves), so it is a genuinely independent check on the main CNN.
It covers 13 crop species - the same family as the main model - which makes
crop-level agreement a meaningful trust signal.
"""

import warnings

warnings.filterwarnings("ignore")

from pathlib import Path

import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

MODEL_ID = "asafe51/plantdoc-disease-classifier"

# PlantDoc label -> (crop, disease) normalised to the main model's vocabulary.
LABEL_MAP = {
    "Apple Scab Leaf": ("Apple", "Apple scab"),
    "Apple leaf": ("Apple", "healthy"),
    "Apple rust leaf": ("Apple", "Cedar apple rust"),
    "Bell_pepper leaf": ("Pepper,_bell", "healthy"),
    "Bell_pepper leaf spot": ("Pepper,_bell", "Bacterial spot"),
    "Blueberry leaf": ("Blueberry", "healthy"),
    "Cherry leaf": ("Cherry_(including_sour)", "healthy"),
    "Corn Gray leaf spot": ("Corn_(maize)", "Cercospora leaf spot Gray leaf spot"),
    "Corn leaf blight": ("Corn_(maize)", "Northern Leaf Blight"),
    "Corn rust leaf": ("Corn_(maize)", "Common rust"),
    "Peach leaf": ("Peach", "healthy"),
    "Potato leaf early blight": ("Potato", "Early blight"),
    "Potato leaf late blight": ("Potato", "Late blight"),
    "Raspberry leaf": ("Raspberry", "healthy"),
    "Soyabean leaf": ("Soybean", "healthy"),
    "Squash Powdery mildew leaf": ("Squash", "Powdery mildew"),
    "Strawberry leaf": ("Strawberry", "healthy"),
    "Tomato Early blight leaf": ("Tomato", "Early blight"),
    "Tomato Septoria leaf spot": ("Tomato", "Septoria leaf spot"),
    "Tomato leaf": ("Tomato", "healthy"),
    "Tomato leaf bacterial spot": ("Tomato", "Bacterial spot"),
    "Tomato leaf late blight": ("Tomato", "Late blight"),
    "Tomato leaf mosaic virus": ("Tomato", "mosaic virus"),
    "Tomato leaf yellow virus": ("Tomato", "Yellow Leaf Curl Virus"),
    "Tomato mold leaf": ("Tomato", "Leaf Mold"),
    "Tomato two spotted spider mites leaf": ("Tomato", "Spider mites"),
    "grape leaf": ("Grape", "healthy"),
    "grape leaf black rot": ("Grape", "Black rot"),
}


class SecondOpinionModel:
    """PlantDoc ViT. Falls back to unavailable if download/load fails."""

    def __init__(self) -> None:
        self.model = None
        self.processor = None
        self.error: str | None = None
        try:
            self.processor = AutoImageProcessor.from_pretrained(MODEL_ID)
            self.model = AutoModelForImageClassification.from_pretrained(MODEL_ID)
            self.model.eval()
            print(f"[second-opinion] loaded {MODEL_ID} ({self.model.config.num_labels} classes)")
        except Exception as exc:  # noqa: BLE001
            self.error = str(exc)
            print(f"[second-opinion] unavailable: {exc}")

    @property
    def available(self) -> bool:
        return self.model is not None

    @torch.inference_mode()
    def predict(self, image_bytes: bytes) -> dict | None:
        if self.model is None:
            return None
        import io

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt")
        logits = self.model(**inputs).logits[0]
        probs = torch.softmax(logits, dim=-1).numpy()
        idx = int(probs.argmax())
        label = self.model.config.id2label[idx]
        crop, disease = LABEL_MAP.get(label, (None, None))
        return {
            "label": label,
            "crop": crop,
            "disease": disease,
            "confidence": round(float(probs[idx]), 4),
        }


second_opinion = SecondOpinionModel()

# Confidence bands for weighing the second opinion's vote.
WEAK_OPINION = 0.30      # below this it is set aside entirely
MODERATE_OPINION = 0.50  # below this, agreement only earns a medium verdict


def compare(main_pred: dict, second_pred: dict | None) -> dict:
    """Combine both models into a single trust verdict for the UI.

    The second model only gets a vote when it is confident enough - otherwise
    a 19% shrug would wrongly veto a solid 69% CNN diagnosis.

    Each verdict carries `label_key`/`note_key` (+ `note_params`) so i18n.py
    can render the same verdict in any language; the English `label`/`note`
    are filled in as a default.
    """
    if second_pred is None:
        return {
            "level": "single",
            "label_key": "trust.single.label",
            "note_key": "trust.single.note",
            "label": "Single model",
            "note": "Second-opinion model unavailable; verdict comes from the CNN alone.",
            "agree_crop": None,
            "agree_disease": None,
        }

    c = second_pred["confidence"]
    weak = c < WEAK_OPINION  # 0.30 - too unsure to confirm or contradict

    if weak:
        return {
            "level": "single",
            "label_key": "trust.weak.label",
            "note_key": "trust.weak.note",
            "note_params": {"conf": f"{c:.0%}"},
            "label": "CNN verdict (second opinion too unsure)",
            "note": (
                f"The independent PlantDoc model was only {c:.0%} confident, too weak "
                "to confirm or contradict the CNN - so its guess is set aside."
            ),
            "agree_crop": second_pred["crop"] == main_pred["plant"],
            "agree_disease": None,
        }

    agree_crop = second_pred["crop"] == main_pred["plant"]
    # Disease-level agreement ignores formatting differences (underscores, case).
    def norm(s: str) -> str:
        return "".join(ch for ch in s.lower() if ch.isalnum())

    agree_disease = agree_crop and norm(second_pred["disease"] or "") == norm(
        main_pred["disease"] or ""
    )

    if agree_disease:
        verdict = {
            "level": "high",
            "label_key": "trust.high.label",
            "note_key": "trust.high.note",
            "label": "Both models agree",
            "note": "The CNN and an independent PlantDoc ViT reach the same diagnosis.",
            "agree_crop": True,
            "agree_disease": True,
        }
        if c < MODERATE_OPINION:  # agreement from a hesitant model is only medium
            verdict["level"] = "medium"
            verdict["note_key"] = "trust.high_medium.note"
            verdict["note_params"] = {"conf": f"{c:.0%}"}
            verdict["note"] = (
                "Both models reach the same diagnosis, though the PlantDoc model was "
                f"only {c:.0%} confident - treat as likely rather than certain."
            )
        return verdict

    if agree_crop:
        return {
            "level": "medium",
            "label_key": "trust.medium.label",
            "note_key": "trust.medium.note",
            "label": "Crops match, severity differs",
            "note": "Both models agree on the crop but differ on the exact condition - treat as a strong hint, not a certainty.",
            "agree_crop": True,
            "agree_disease": False,
        }

    return {
        "level": "low",
        "label_key": "trust.low.label",
        "note_key": "trust.low.note",
        "note_params": {"crop1": main_pred["plant"], "crop2": second_pred["crop"]},
        "label": "Models disagree",
        "note": (
            f"The two models name different crops ({main_pred['plant']} vs "
            f"{second_pred['crop']}). This photo may sit outside the 14 species we "
            "cover - verify with a local agronomist."
        ),
        "agree_crop": False,
        "agree_disease": False,
    }
