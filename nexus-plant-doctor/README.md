# 🌿 Nexus Plant Doctor

Full-stack crop-disease detection: photograph a leaf → CNN diagnosis + confidence + treatment advice.

Built **from scratch** (the reference projects in this folder were only used as a source for the trained weights).

## Stack — languages & tech

| Layer | Language / Tech | Why |
|---|---|---|
| Deep learning | **Python** · Keras 3 on **PyTorch** (CUDA) | TensorFlow has no wheel for Python 3.14, which is what this machine runs; PyTorch 2.13 was already installed |
| REST API | **Python** · FastAPI + Uvicorn | Async, auto docs at `/docs` |
| Web UI | **JavaScript** (React 19) + **HTML/CSS** | Drag-drop upload, camera capture, animated confidence bars |
| Bundler | Vite 7 | Instant dev server, production build to `frontend/dist` |
| Model | `best_model.keras` — 38 classes, 14 crops, ~97% val. accuracy, 150×150 RGB input | Trained on the New Plant Diseases (Augmented) dataset |

## Layout

```
nexus-plant-doctor/
├── backend/
│   ├── model.py          # CNN inference engine (Keras 3 + PyTorch, GPU) + abstention gate
│   ├── second_opinion.py # PlantDoc ViT cross-check + trust verdict
│   ├── species_id.py     # PlantNet species expert (ResNet18 + MobileNet + TTA)
│   ├── main.py           # FastAPI: /predict, /health, serves the built UI
│   └── requirements.txt
├── frontend/
│   ├── src/App.jsx       # main React app
│   ├── src/components/   # ImageUpload, ResultCard, SampleGallery
│   ├── public/samples/   # one-click demo leaves
│   └── dist/             # production build (served by FastAPI)
├── best_model.keras      # trained 38-class CNN weights
└── README.md
```

## Run it

```powershell
# 1. Backend (loads the model on the GPU, serves http://localhost:8000)
cd backend
python main.py

# 2. First time only — build the UI
cd ../frontend
npm install
npm run build
```

Open **http://localhost:8000** — or for live-reload UI development:

```powershell
cd frontend
npm run dev        # http://localhost:5173 (proxies /api → :8000)
```

Double-click `start.bat` to launch everything at once.

## Plant identification: "what is this leaf - and do you actually know?"

Every request now returns an `identification` object with an explicit
**identified / not_identified** verdict. It is decided by two complementary
experts, asked in order:

1. **Crop CNN (14 crops)** — its answer is backed by the 1,900-image reference
   bank and four calibrated signals. Evidence reported: feature similarity,
   peak confidence, texture, second-model agreement.
2. **PlantNet-300K species expert** — runs on **every** image so it can
   challenge the crop model. Two independently trained models (ResNet18 45 MB +
   MobileNetV3-Small 10 MB, same 1,081 species) plus **test-time
   augmentation**: the photo is predicted 7 ways (centre, flip, 4 corners,
   zoom). On its own (when the CNN declines) it claims an answer only when:

   ```
   (top-5 all one genus  OR  same genus from all 7 views)
   AND top-1 confidence >= 0.60
   AND top-1 margin     >= 0.30
   AND leaf texture     >= 8.0
   ```

   Calibrated at **100% precision / 50% recall** over 20 labelled photos
   (`verify_mapping.py`, `tta_species.py`): 4 accepted, 4 correct. All junk
   inputs (dog, noise, gradients, screenshots) and all crop leaves were declined.

**Cross-check (the two experts are both asked, and disagreement is shown):**
when the crop CNN claims a plant, the species expert's claim counts as a
*credible challenge* if its top-5 are all one genus (**coherent**), or if both
species models agree on the genus with ≥0.8 confidence and ≥70% of the photo's
crops agree (**corroborated**). Then:

* challenge **+** both species models agree **+** the species expert stands
  behind its answer → the **species name wins** (no treatment advice);
* challenge otherwise → **CONFLICT**: `not_identified`, showing *Crop model says
  X* vs *Species model says Y*;
* no challenge → the crop CNN's answer stands.

Measured effect: a *Pelargonium* leaf no longer comes back as
"Pepper, 100%" (→ conflict), *Lupinus polyphyllus* beats the CNN's "Grape",
and a dead-nettle beats its "Tomato". Corn/potato/tomato still flow through
the crop path because the species models' top-5 for them are scattered.

Why the elaborate gating: measured top-1 on web photos is only **~30%** (the
published 75.8% is on PlantNet's own field photos) and the errors are
*confident* — a foxglove photo was called *Galega officinalis* at 0.92. The
label set also contains **none** of the 14 crops (and no wheat/rice/maize
either), so the species expert is strictly for non-crop plants. Its solo false
positive — an actual corn leaf named *Bocoa prouacensis* at 0.99 — is held back
by the challenge rule: the two species models name unrelated genera and its
top-5 are scattered, so it never challenges the crop model.

| Verdict | Meaning |
|---|---|
| 🌱 `identified` via `crop_disease_cnn` | One of the 14 crops → full diagnosis + treatment |
| 🌱 `identified` via `plantnet_species` | Named species, not a covered crop → name only, no treatment |
| ❓ `not_identified` | Neither model could prove an answer → reasons + photo tips, guesses struck through |
| ❓ `not_identified` + `conflict` | The two experts name different plants → both claims are shown, neither asserted |

### Identification test scripts

```powershell
cd backend
python test_identification.py   # verdicts on labelled photos, crops and junk
python verify_mapping.py        # index->name mapping check, precision/recall
python tta_species.py           # compare candidate acceptance rules
python calibrate_species.py     # ground-truth species photos + junk scores
```

`backend\test_images\` holds the regression photos used above — three
non-crop leaves (a *Pelargonium* and a *Lupinus* the crop CNN would otherwise
mis-report as Pepper/Grape, a dead-nettle it read as Tomato), two junk inputs
and the wheat field photo. Quick API check:

```powershell
curl.exe -s -X POST http://localhost:8000/predict -F "file=@backend\test_images\pelargonium_leaf.jpg"
```

## Confidence, trust and honest abstention

The 38-class CNN can only recognise the 14 crops it was trained on (PlantVillage).
Two safeguards stop it inventing answers for everything else:

1. **Abstention gate** — four signals must all be sane or the crop claim is
   dropped: the leaf then gets named by the species expert instead, or
   reported `not_identified` with the failing signals listed:

   | Signal | Threshold | Catches |
   |---|---|---|
   | Softmax peak confidence | ≥ 0.60 | vague, off-distribution photos |
   | Normalised entropy | ≤ 0.45 | flat/uniform probability spread |
   | 512-d feature similarity to predicted-class centroid | ≥ 0.42 | images unlike the training corpus |
   | Local texture roughness (256², mean neighbour delta) | ≥ 8.0 | synthetic flats, UI screenshots |

   The reference bank is 1,900 PlantVillage images (50/class) stored by
   `build_reference_bank.py`. Softmax alone is useless for this — a synthetic
   flat canvas scores **100% confidence** for "Cherry powdery mildew"; the
   texture signal (0.1 vs 13.9–26.7 for real leaves) is what rejects it.

   Thresholds were calibrated with `calibrate_gate.py` / `texture_stats.py`:

   | Input | verdict |
   |---|---|
   | corn / potato / tomato leaves | ✅ accept (3/3) |
   | flat gradient, blue canvas, noise, 2× UI screenshot, dog photo | ✅ reject (6/6) |
   | wheat field photo | ❌ **false accept** — diagnosed as Northern Leaf Blight at 96% |

   **Known limitation:** a wheat leaf is never rejected — it is visually a grass
   and the bank contains corn, so it sits inside training-distribution feature
   space (sim 0.91) with healthy texture (11.6). The same applies to a few
   non-crop leaves whose species answer the two models cannot corroborate (one
   *Lupinus* photo still reads as "Corn" because the species models contradict
   themselves on it). No threshold can fix this; only genuine coverage
   (retraining with wheat/rice/etc.) or an external identification API does.
   The gate is honest about *junk* and the cross-check catches the
   *identifiable* non-crops — neither is a substitute for *coverage*.
2. **Second opinion** — an independent ViT fine-tuned on **PlantDoc** (real field
   photos) votes alongside the CNN. Agreement raises a trust badge; a genuine
   disagreement downgrades the verdict to *disputed*. The second model's own
   confidence is weighted: below 30% its guess is set aside entirely (so a 19%
   shrug can't veto a 69% diagnosis), 30–50% caps agreement at *medium*.

| Trust badge | Meaning |
|---|---|
| 🟢 Both models agree | Same crop **and** same condition |
| 🟡 Crops match, severity differs | Same crop, different condition — or the second model was hesitant |
| 🔴 Models disagree | Different crops named — possibly outside coverage |
| ⚪ CNN verdict only | Second model too unsure to weigh |

Verified behaviour: corn-rust → *high*, potato-early-blight → *medium*,
tomato-bacterial → CNN verdict (PlantDoc only 19% sure),
non-plant screenshot → **outside_coverage** at 34%.

## Recalibrating / retraining

```powershell
# rebuild the OOD reference bank (after any model change)
cd backend
python build_reference_bank.py

# print gate scores for the sample leaves + any extra images you pass
python calibrate_gate.py path\to\your\photo.jpg

# texture-only view (flat/synthetic detection)
python texture_stats.py path\to\your\photo.jpg
```

## API

```bash
curl -X POST http://localhost:8000/predict -F "file=@leaf.jpg"
curl -X POST "http://localhost:8000/predict?lang=kn" -F "file=@leaf.jpg"   # ಕನ್ನಡ
curl "http://localhost:8000/i18n?lang=kn"                                  # UI bundle
```

```json
{
  "class": "Tomato___Late_blight",
  "plant": "Tomato",
  "disease": "Late blight",
  "confidence": 0.9567,
  "healthy": false,
  "advice": "...",
  "top_k": [ { "class": "...", "confidence": 0.95 } ]
}
```

## Languages (English ⇄ ಕನ್ನಡ)

The header has an **EN | ಕನ್ನಡ** toggle (choice is remembered in `localStorage`,
and the first visit follows the browser language). Switching re-asks the
backend for the current photo, so the whole verdict - plant and disease names,
treatment advice, identification evidence, trust notes, headlines - changes
language together with the UI.

- One source of truth: `backend/i18n.py` holds every fixed string the app can
  emit (14 crop names, 21 disease names, 22 treatment texts, evidence/note/
  headline/trust phrases, reason chips, UI labels). `GET /i18n?lang=` serves
  the UI half to the SPA; `POST /predict?lang=` translates the result half.
- Offline dictionary, no translation API: the vocabulary is a closed set, so a
  curated dict is instant, free, and keeps farmer photos on this machine. A
  missing key falls back to English instead of breaking the response.
- Latin species names (`Lupinus polyphyllus`) stay untranslated - scientific
  names are language-independent.
- Rendering: Noto Sans Kannada is loaded in `index.html` and listed in the
  font stack, with `Nirmala UI` as an offline Windows fallback.

## The 38 classes

Apple (4) · Blueberry (1) · Cherry (2) · Corn (4) · Grape (4) · Orange (1) · Peach (2) · Pepper (2) · Potato (3) · Raspberry (1) · Soybean (1) · Squash (1) · Strawberry (2) · Tomato (10)

## Next steps

- [ ] Retrain / fine-tune (`Plant-Doctor-main/plant-diseases-detection-cnn-97-acc.ipynb` is the reference notebook)
- [ ] Severity estimation from lesion coverage
- [ ] Offline PWA + field history
