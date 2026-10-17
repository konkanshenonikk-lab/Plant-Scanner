"""Plant disease CNN inference engine.

Runs the trained 38-class Keras model on the PyTorch backend, because this
machine has Python 3.14 (TensorFlow does not ship wheels for 3.14) while
PyTorch 2.13 + CUDA is already installed.
"""

import os

# Must be set BEFORE keras is imported anywhere.
os.environ.setdefault("KERAS_BACKEND", "torch")

import warnings

warnings.filterwarnings("ignore")

from pathlib import Path

import keras
import numpy as np
import torch
from PIL import Image

# --- Configuration ------------------------------------------------------------

IMAGE_SIZE = 150  # the model was trained on 150x150 RGB leaves

BASE_DIR = Path(__file__).resolve().parent
MODEL_CANDIDATES = [
    BASE_DIR.parent / "best_model.keras",
    BASE_DIR.parent / "my_cnn_model.h5",
    BASE_DIR / "best_model.keras",
]

# PlantVillage class order the model was trained with (index -> class name).
CLASS_NAMES = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot",
    "Peach___healthy",
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
]

# Optional agronomic advice returned alongside the prediction.
TREATMENTS = {
    "Apple_scab": "Remove infected leaves; apply a fungicide (myclobutanil or captan) at bud scale and post-harvest. Improve air flow by pruning.",
    "Black_rot": "Prune out mummified fruit and cankers, remove fallen debris, and apply copper or a strobilurin fungicide during bloom.",
    "Cedar_apple_rust": "Remove nearby juniper hosts if possible; spray with mancozeb or myclobutanil from green tip to petal fall.",
    "Powdery_mildew": "Apply sulfur or potassium bicarbonate sprays; avoid overhead watering and ensure good ventilation.",
    "Cercospora_leaf_spot": "Use resistant hybrids, rotate crops, and apply foliar fungicides (azoxystrobin, pyraclostrobin) at first symptom.",
    "Common_rust": "Usually tolerable; if severe, spray a triazole/strobilurin fungicide and plant rust-resistant varieties next season.",
    "Northern_Leaf_Blight": "Rotate crops, use resistant hybrids, and apply foliar fungicide when lesions reach 0.5 inch on 50% of plants.",
    "Esca": "Prune carefully in dry weather, avoid summer pruning wounds, and protect wounds with paste. No reliable cure once advanced.",
    "Haunglongbing": "No cure — remove infected trees, control Asian citrus psyllid with insecticides, and use certified disease-free seedlings.",
    "Bacterial_spot": "Apply copper-based bactericides, use certified seed, rotate crops, and avoid working with wet foliage.",
    "Early_blight": "Remove lower infected leaves, mulch to prevent soil splash, rotate 2-3 years, and apply chlorothalonil or mancozeb.",
    "Late_blight": "Act fast: destroy infected plants, apply metalaxyl-mancozeb or copper, and use resistant varieties. Keep foliage dry.",
    "Leaf_Mold": "Reduce humidity, improve spacing/ventilation, remove affected leaves, and apply chlorothalonil or copper sprays.",
    "Septoria_leaf_spot": "Stake and mulch plants, remove lower leaves, rotate 3+ years, and spray chlorothalonil every 7-10 days.",
    "Spider_mites": "Insecticidal soap, neem oil, or abamectin; increase humidity and release predatory mites for biological control.",
    "Target_Spot": "Rotate crops, remove plant debris, avoid overhead irrigation, and apply azoxystrobin or boscalid.",
    "Yellow_Leaf_Curl_Virus": "No cure — remove and destroy infected plants, control whitefly vectors with yellow sticky traps and imidacloprid, use reflective mulch.",
    "mosaic_virus": "No cure — remove infected plants, control aphids/whiteflies, wash hands and tools between plants, use virus-free seed.",
    "Leaf_scorch": "Remove and destroy infected plants, irrigate to avoid drought stress, acidify soil, and avoid overhead watering.",
    "Leaf_blight": "Remove fallen leaves, apply copper or mancozeb sprays, and ensure good air circulation.",
}


# --- Inference engine ---------------------------------------------------------


class PlantDiseaseModel:
    """Loads the CNN once at startup and serves single-image predictions."""

    def __init__(self) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.model_path: Path | None = None
        self.error: str | None = None
        self.feature_model = None
        self.ref_embeddings = None
        self._load()

    def _load(self) -> None:
        for path in MODEL_CANDIDATES:
            if not path.exists():
                continue
            try:
                # compile=False skips torch.compile, which needs Triton
                # (not installed) and is pointless for single-image inference.
                self.model = keras.saving.load_model(path, compile=False)
                self.model.to(self.device)
                self.model.eval()
                self.model_path = path
                print(f"[model] loaded {path.name} on {self.device.type}")
                self._load_feature_tools()
                return
            except Exception as exc:  # noqa: BLE001 - try the next candidate
                self.error = str(exc)
                print(f"[model] failed to load {path}: {exc}")
        if self.error is None:
            self.error = "No model file found (best_model.keras / my_cnn_model.h5)"

    def _load_feature_tools(self) -> None:
        """Feature extractor + OOD reference bank (built once, offline)."""
        import keras as _keras

        # Layer 13 is the 512-d penultimate representation (see model summary).
        self.feature_model = _keras.Model(
            self.model.inputs[0], self.model.layers[13].output
        )
        self.feature_model.eval()
        bank = BASE_DIR / "reference_bank.npz"
        if bank.exists():
            data = np.load(bank, allow_pickle=True)
            self.ref_embeddings = torch.from_numpy(data["embeddings"].astype(np.float32))
            self.ref_labels = torch.from_numpy(data["class_idx"].astype(np.int64))
            # Per-class mean embedding (normalised) for centroid scoring.
            centroids = []
            for cls in range(data["class_idx"].max() + 1):
                centre = data["embeddings"][data["class_idx"] == cls].astype(np.float32).mean(0)
                norm = np.linalg.norm(centre)
                centroids.append(centre / norm if norm > 0 else centre)
            self.ref_centroids = torch.from_numpy(np.stack(centroids))
            print(
                f"[model] reference bank: {self.ref_embeddings.shape[0]} samples, "
                f"{self.ref_centroids.shape[0]} class centroids"
            )
        else:
            self.ref_labels = None
            self.ref_centroids = None
            print("[model] no reference_bank.npz - OOD gate disabled")

    @property
    def available(self) -> bool:
        return self.model is not None

    def _preprocess(self, image_bytes: bytes) -> torch.Tensor:
        image = Image.open(__import__("io").BytesIO(image_bytes)).convert("RGB")
        image = image.resize((IMAGE_SIZE, IMAGE_SIZE))
        array = np.asarray(image, dtype=np.float32) / 255.0  # normalize 0..1
        array = np.expand_dims(array, 0)  # add batch dimension -> (1,150,150,3)
        return torch.from_numpy(array).to(self.device)

    # Abstention thresholds (calibrated with calibrate_gate.py + texture_stats.py).
    MIN_CONFIDENCE = 0.60          # softmax peak below this -> guessing
    MAX_NORMALISED_ENTROPY = 0.45  # flat distribution -> guessing
    MIN_CENTROID_SIMILARITY = 0.42 # feature distance to the predicted class
                                   # centroid; junk images score far lower
                                   # (good leaves: 0.44-0.97, junk: 0.27-0.53)
    MIN_TEXTURE_ROUGHNESS = 8.0    # mean |pixel neighbour delta| at 256x256.
                                   # Real leaves: 13.9-26.7. Synthetic flats and
                                   # UI screenshots: 0.1-7.4.

    @staticmethod
    def _texture_roughness(image_bytes: bytes) -> float:
        """Local texture strength - flat synthetic images score near zero."""
        import io

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((256, 256))
        grey = np.asarray(image, dtype=np.float32).mean(axis=2)
        dx = np.abs(np.diff(grey, axis=0)).mean()
        dy = np.abs(np.diff(grey, axis=1)).mean()
        return float(dx + dy)

    def _ood_similarity(self, feats: torch.Tensor) -> float | None:
        """Max cosine similarity of the input to the 1,900 training samples."""
        if self.ref_embeddings is None:
            return None
        normed = feats / feats.norm(dim=-1, keepdim=True).clamp_min(1e-12)
        sims = normed @ self.ref_embeddings.to(self.device).T
        return float(sims.max())

    @torch.inference_mode()
    def predict(
        self, image_bytes: bytes, top_k: int = 3
    ) -> tuple[list[dict], dict]:
        """Returns (top-k predictions, confidence statistics)."""
        if self.model is None:
            raise RuntimeError(self.error or "model unavailable")

        tensor = self._preprocess(image_bytes)
        # Direct forward pass (keras .predict() would try to torch.compile).
        probs = self.model(tensor, training=False).detach().cpu().numpy()[0]

        # Uncertainty: peak confidence plus entropy normalised to 0..1.
        eps = 1e-12
        entropy = float(-(probs * np.log(probs + eps)).sum())
        norm_entropy = entropy / float(np.log(len(probs)))
        confidence = float(probs.max())

        # Feature-space check: does this image look like anything the model
        # was trained on? Softmax alone is overconfident on foreign images.
        feats = self.feature_model(tensor, training=False)
        similarity = self._ood_similarity(feats)
        roughness = self._texture_roughness(image_bytes)

        # Second OOD score: similarity to the centroid of the predicted class.
        centroid_similarity = None
        if self.ref_centroids is not None:
            normed = feats / feats.norm(dim=-1, keepdim=True).clamp_min(1e-12)
            pred_idx = int(probs.argmax())
            centre = self.ref_centroids[pred_idx].to(self.device)
            centroid_similarity = float((normed * centre).sum())

        reasons = []
        if confidence < self.MIN_CONFIDENCE:
            reasons.append("low_confidence")
        if norm_entropy > self.MAX_NORMALISED_ENTROPY:
            reasons.append("high_entropy")
        if (
            centroid_similarity is not None
            and centroid_similarity < self.MIN_CENTROID_SIMILARITY
        ):
            reasons.append("unlike_training_data")
        if roughness < self.MIN_TEXTURE_ROUGHNESS:
            reasons.append("no_leaf_texture")

        stats = {
            "confidence": round(confidence, 4),
            "normalised_entropy": round(norm_entropy, 4),
            "reference_similarity": round(similarity, 4) if similarity is not None else None,
            "centroid_similarity": (
                round(centroid_similarity, 4) if centroid_similarity is not None else None
            ),
            "texture_roughness": round(roughness, 3),
            "reasons": reasons,
            "uncertain": bool(reasons),
        }

        order = probs.argsort()[::-1][:top_k]
        results = []
        for idx in order:
            class_name = CLASS_NAMES[int(idx)]
            plant, disease = class_name.split("___", 1)
            results.append(
                {
                    "class": class_name,
                    "plant": plant,
                    "disease": disease.replace("_", " ").strip(),
                    "confidence": round(float(probs[int(idx)]), 4),
                    "healthy": disease.strip().lower() == "healthy",
                    "advice": _advice_for(disease),
                    # Stable key so i18n.py can swap the advice text per language.
                    "advice_key": _advice_key_for(disease),
                }
            )
        return results, stats


def _advice_key_for(disease: str) -> str:
    """TREATMENTS key for a disease label ('healthy'/'default' when no match)."""
    if disease.strip().lower() == "healthy":
        return "healthy"
    for key in TREATMENTS:
        if key.lower() in disease.lower():
            return key
    return "default"


def _advice_for(disease: str) -> str | None:
    if disease.strip().lower() == "healthy":
        return "No disease detected. Keep monitoring the crop and maintain normal field hygiene."
    for key, text in TREATMENTS.items():
        if key.lower() in disease.lower():
            return text
    return "Isolate affected plants, remove severely infected foliage, and consult a local agronomist for region-specific control."


# Process-wide singleton so the model is loaded only once at server start.
plant_model = PlantDiseaseModel()
