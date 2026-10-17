"""FastAPI server: leaf-image upload -> CNN prediction -> JSON.

Run with:  python main.py   (serves http://localhost:8000)
"""

import io
from pathlib import Path

import numpy as np
import uvicorn
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from model import CLASS_NAMES, plant_model
from second_opinion import compare, second_opinion
from species_id import species_identifier
from i18n import LANGS, UI, EVIDENCE, HEADLINES, NOTES, REASONS, localize_result, tr

app = FastAPI(title="Nexus Plant Doctor API", version="1.0")


def pretty_crop(class_name: str) -> str:
    """'Corn_(maize)___Common_rust_' -> 'Corn'."""
    crop = class_name.split("___", 1)[0]
    pretty = crop.replace("(maize)", "").replace("_(including_sour)", "")
    pretty = pretty.replace(",_bell", "").replace("(", " ").replace(")", "")
    # Replace underscores first, then strip: "Corn_" -> "Corn" (not "Corn ").
    return pretty.replace("_", " ").strip()


def covered_crops() -> list[str]:
    """The 14 crop species the CNN was trained on, human-formatted."""
    crops = {pretty_crop(name) for name in CLASS_NAMES}
    return sorted(crops)


def build_identification(stats: dict, best: dict, trust: dict, data: bytes) -> dict:
    """Decide WHAT the leaf is - and whether we can honestly claim to know.

    Both experts are asked on every image, and a disagreement is surfaced
    rather than silently resolved:

    * crop CNN passes, species expert has no coherent counter-claim -> crop ID.
      (The CNN is asked first: its verdict is backed by the 1,900-image
      reference bank; and its own false accept - a wheat field read as corn -
      cannot be caught by the species model, which has no wheat class either.)
    * crop CNN passes, species expert has a credible counter-claim -> either
      the species name wins (both species models agree AND the species expert
      stands behind its answer) or, if not, CONFLICT: we refuse to name the
      plant at all. This is what stops a Pelargonium leaf being reported as
      "Pepper, 100%" and a dead-nettle as "Tomato".
    * crop CNN declines -> the species expert answers on its own, under its
      normal (weaker) bar.

    Order also hides the species expert's one observed solo false positive: it
    called an actual corn leaf "Bocoa prouacensis", but its top-5 were not
    genus-coherent, so it never reaches the conflict stage for corn.
    """
    species = species_identifier.identify(data) if species_identifier.available else None
    crop_claim = pretty_crop(best["class"])

    # Can the species expert credibly challenge the crop model's claim?
    #  - its top-5 candidates are all one genus (coherent), OR
    #  - both species models agree on the genus, with >=0.8 confidence and the
    #    answer holding across >=70% of the photo's crops (corroborated).
    sig = species.get("signals", {}) if species else {}
    coherent = bool(sig.get("coherence"))
    corroborated = bool(
        sig.get("agree")
        and species
        and species.get("confidence", 0) >= 0.8
        and sig.get("stable_fraction", 0) >= 0.7
    )
    challenge = bool(species) and (coherent or corroborated)

    if not stats["uncertain"]:
        if challenge:
            species_evidence_keys = list(species.get("evidence_keys", [])) + [
                {
                    "key": "evidence.crop_claim",
                    "params": {
                        "crop": crop_claim,
                        "sim": stats["centroid_similarity"],
                    },
                }
            ]
            if sig.get("agree") and species["status"] == "identified":
                # both species models agree AND the species expert is willing
                # to stand behind its answer -> trust it over a crop CNN that
                # has never seen this plant
                return {
                    "status": "identified",
                    "name": species["name"],
                    "method": "plantnet_species",
                    "confidence": species["confidence"],
                    "evidence": species["evidence"]
                    + [
                        tr(
                            "en",
                            EVIDENCE,
                            "evidence.crop_claim",
                            crop=crop_claim,
                            sim=stats["centroid_similarity"],
                        )
                    ],
                    "evidence_keys": species_evidence_keys,
                    "reasons": [],
                    "note": tr(
                        "en",
                        NOTES,
                        "note.species_override",
                        crop=crop_claim,
                    ),
                    "note_key": "note.species_override",
                    "note_params": {"crop": crop_claim},
                    "alternatives": species.get("alternatives", []),
                }
            # two experts, two answers - refuse to name it
            return {
                "status": "not_identified",
                "name": None,
                "method": None,
                "confidence": None,
                "evidence": [],
                "evidence_keys": [],
                "reasons": ["experts_disagree"],
                "conflict": {
                    "crop_model": crop_claim,
                    "species_model": species.get("best_guess"),
                },
                "best_guess": species.get("best_guess"),
                "note": tr("en", NOTES, "note.conflict"),
                "note_key": "note.conflict",
                "note_params": {},
            }

        evidence_keys = [
            {
                "key": "evidence.corpus_match",
                "params": {"sim": stats["centroid_similarity"]},
            },
            {
                "key": "evidence.peak_conf",
                "params": {"conf": f"{stats['confidence']:.0%}"},
            },
            {
                "key": "evidence.texture",
                "params": {"rough": stats["texture_roughness"]},
            },
        ]
        if trust.get("level") == "high":
            evidence_keys.append(
                {"key": "evidence.second_agrees", "params": {}}
            )
        evidence = [
            tr("en", EVIDENCE, e["key"], **e["params"]) for e in evidence_keys
        ]
        return {
            "status": "identified",
            "name": crop_claim,
            "method": "crop_disease_cnn",
            "confidence": stats["confidence"],
            "evidence": evidence,
            "evidence_keys": evidence_keys,
            "reasons": [],
            "note": tr("en", NOTES, "note.crops", n=len(covered_crops())),
            "note_key": "note.crops",
            "note_params": {"n": len(covered_crops())},
        }

    # Crop CNN declined: the species expert answers on its own.
    if species and species["status"] == "identified":
        return {
            "status": "identified",
            "name": species["name"],
            "method": "plantnet_species",
            "confidence": species["confidence"],
            "evidence": species["evidence"],
            "evidence_keys": species.get("evidence_keys", []),
            "reasons": [],
            "note": tr("en", NOTES, "note.species"),
            "note_key": "note.species",
            "note_params": {},
            "alternatives": species["alternatives"],
        }

    reasons = list(dict.fromkeys(stats["reasons"] + (species["reasons"] if species else [])))
    return {
        "status": "not_identified",
        "name": None,
        "method": None,
        "confidence": None,
        "evidence": [],
        "evidence_keys": [],
        "reasons": reasons or ["no_signal"],
        "best_guess": (
            species.get("best_guess") if species else best["class"]
        ),
        "note": tr("en", NOTES, "note.not_identified"),
        "note_key": "note.not_identified",
        "note_params": {},
    }

# The SPA is served from this same origin in production, and Vite proxies
# /api -> :8000 in dev, so cross-origin access is never needed. An earlier
# wildcard ("*") + credentials allowed ANY website to read responses from
# this server - which mattered because of the file-serving bug fixed below.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

MAX_BYTES = 8 * 1024 * 1024  # 8 MB upload cap
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model_loaded": plant_model.available,
        "model_file": plant_model.model_path.name if plant_model.model_path else None,
        "classes": len(CLASS_NAMES),
        "second_opinion": second_opinion.available,
        "species_model": species_identifier.available,
        "species_classes": (
            len(species_identifier.index_to_name) if species_identifier.available else 0
        ),
        "covered_crops": covered_crops(),
        "languages": LANGS,
    }


@app.get("/i18n")
def i18n(lang: str = "en") -> dict:
    """UI string bundle for the SPA (one source of truth for translations)."""
    if lang not in LANGS:
        lang = "en"
    return {
        "lang": lang,
        "languages": LANGS,
        "ui": {key: (entry.get(lang) or entry["en"]) for key, entry in UI.items()},
        "reasons": {key: tr(lang, REASONS, key) for key in REASONS},
    }


@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    lang: str = Query("en", description="UI language: en | kn"),
) -> dict:
    if lang not in LANGS:
        lang = "en"
    if not plant_model.available:
        raise HTTPException(status_code=503, detail=plant_model.error)

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image larger than 8 MB")

    # Validate that it really is a decodable image before hitting the model.
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="File is not a valid image") from exc

    try:
        predictions, stats = plant_model.predict(data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

    second = second_opinion.predict(data) if second_opinion.available else None
    best = predictions[0]
    trust = compare(best, second)
    identification = build_identification(stats, best, trust, data)

    # Honest verdicts, driven by what we could prove about the photo.
    headline_key = None
    headline_params: dict = {}
    if identification["status"] == "not_identified":
        status = "not_identified"
        headline_key = "headline.not_identified"
    elif identification["method"] == "plantnet_species":
        status = "identified_only"
        headline_key = "headline.identified_only"
        headline_params = {"name": identification["name"].rstrip(".")}
    elif trust["level"] == "low":
        status = "disputed"
        headline_key = "headline.disputed"
    else:
        status = "diagnosed"

    response = {
        "status": status,
        "headline": tr("en", HEADLINES, headline_key, **headline_params) if headline_key else None,
        "headline_key": headline_key,
        "headline_params": headline_params,
        "identification": identification,
        "class": best["class"],
        "plant": pretty_crop(best["class"]),
        "disease": best["disease"],
        "confidence": best["confidence"],
        "healthy": best["healthy"],
        "advice": best["advice"],
        "advice_key": best["advice_key"],
        # Display rows get the cleaned crop name; the raw dicts stay untouched
        # for logs/tests.
        "top_k": [{**row, "plant": pretty_crop(row["class"])} for row in predictions],
        "uncertainty": stats,
        "second_model": second,
        "trust": trust,
        "covered_crops": covered_crops(),
        "mock": False,
    }
    if lang != "en":
        localize_result(response, lang)
    return response


# --- Serve the built React frontend (production mode) ------------------------
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/{path:path}", include_in_schema=False)
    async def serve_frontend(path: str = ""):
        # Resolve and CONFINE to dist/: without this check a request like
        # /..%2f..%2fbackend%2fmain.py served any file on disk (and CORS "*"
        # let any webpage read it). Escapes fall through to index.html.
        try:
            candidate = (FRONTEND_DIST / path).resolve()
            candidate.relative_to(FRONTEND_DIST.resolve())
        except (ValueError, OSError):
            candidate = None
        if path and candidate is not None and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
