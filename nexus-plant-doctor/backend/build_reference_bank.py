"""Build the OOD reference bank.

Downloads a 50-images-per-class PlantVillage subset (the same source corpus
the CNN was trained on) and stores the CNN's 512-d penultimate-layer features
for every image. At inference time an input's maximum cosine similarity to
this bank tells us whether the photo resembles anything the model was ever
trained on - softmax confidence cannot do that.

Run once:  python build_reference_bank.py
"""

import io
import os
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("KERAS_BACKEND", "torch")

import numpy as np
import pandas as pd
import torch
from PIL import Image
from huggingface_hub import hf_hub_download

from model import IMAGE_SIZE, plant_model, CLASS_NAMES

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reference_bank.npz")
BATCH = 64


def main() -> None:
    if plant_model.model is None:
        raise SystemExit("CNN failed to load - cannot build reference bank")

    # Penultimate features: the 512-d vector just before the classifier head.
    feature_model = keras.Model(
        plant_model.model.inputs[0], plant_model.model.layers[13].output
    )
    feature_model.eval()

    path = hf_hub_download(
        "geraldmc/plantvillage-tiny",
        "data/train-00000-of-00001.parquet",
        repo_type="dataset",
    )
    df = pd.read_parquet(path)
    print(f"reference images: {len(df)}")

    embeddings, labels = [], []
    for start in range(0, len(df), BATCH):
        chunk = df.iloc[start : start + BATCH]
        batch = []
        for cell in chunk["image"]:
            raw = cell["bytes"] if isinstance(cell, dict) else cell
            img = Image.open(io.BytesIO(raw)).convert("RGB").resize((IMAGE_SIZE, IMAGE_SIZE))
            batch.append(np.asarray(img, dtype=np.float32) / 255.0)
        x = torch.from_numpy(np.stack(batch)).to(plant_model.device)
        with torch.inference_mode():
            feats = feature_model(x, training=False).detach().cpu().numpy()
        embeddings.append(feats)
        labels.extend(chunk["class_idx"].tolist())
        if start % 640 == 0:
            print(f"  {start}/{len(df)}")

    emb = np.concatenate(embeddings).astype(np.float16)
    # L2-normalise so a dot product equals cosine similarity at inference.
    emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)
    np.savez_compressed(
        OUT_PATH,
        embeddings=emb,
        class_idx=np.asarray(labels, dtype=np.int32),
        class_names=np.asarray(CLASS_NAMES, dtype=object),
    )
    print(f"saved {emb.shape} -> {OUT_PATH}")
    print(f"disk: {os.path.getsize(OUT_PATH)/1e6:.1f} MB")


import keras  # noqa: E402  (imported late so model.py sets KERAS_BACKEND first)

if __name__ == "__main__":
    main()
