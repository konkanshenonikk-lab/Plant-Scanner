"""Offline translations for the app's fixed vocabulary (English <-> Kannada).

Every string the app can emit comes from a closed set: 14 crop names, 21
distinct disease names, 21 treatment texts, evidence/note/headline phrases and
trust verdicts. So instead of calling a paid translation API (and leaking
farmer photos to a third party), we ship a curated dictionary. Lookup is a dict
hit with an English fallback, so a missing key degrades to English rather than
breaking the response.

    tr("kn", "diseases", "Common rust")          -> "ಸಾಮಾನ್ಯ ತುಕ್ಕು ರೋಗ"
    tr("kn", "evidence", "evidence.texture", rough=12.3) -> formatted phrase

Lang codes: "en" (default), "kn" (Kannada).
"""

LANGS = {"en": "English", "kn": "ಕನ್ನಡ"}

# --- Plant vocabulary ---------------------------------------------------------

CROPS = {
    "Apple": "ಸೇಬು",
    "Blueberry": "ಬ್ಲೂಬೆರಿ",
    "Cherry": "ಚೆರಿ",
    "Corn": "ಮೆಕ್ಕೆಜೋಳ",
    "Grape": "ದ್ರಾಕ್ಷಿ",
    "Orange": "ಕಿತ್ತಳೆ",
    "Peach": "ಪೀಚು",
    "Pepper": "ಮೆಣಸಿನಕಾಯಿ",
    "Potato": "ಆಲೂಗಡ್ಡೆ",
    "Raspberry": "ರಾಸ್ಪ್‌ಬೆರಿ",
    "Soybean": "ಸೋಯಾಬೀನು",
    "Squash": "ಸ್ಕ್ವಾಶ್",
    "Strawberry": "ಸ್ಟ್ರಾಬೆರಿ",
    "Tomato": "ಟೊಮ್ಯಾಟೊ",
}

# Keyed by the *English display* string (model.py: disease.replace("_", " ")).
DISEASES = {
    "healthy": "ಆರೋಗ್ಯಕರ",
    "Apple scab": "ಸೇಬು ಸ್ಕ್ಯಾಬ್ ರೋಗ",
    "Black rot": "ಕಪ್ಪು ಕೊಳೆತ",
    "Cedar apple rust": "ಸಿಡಾರ್ ಆಪಲ್ ತುಕ್ಕು ರೋಗ",
    "Powdery mildew": "ಬೂಳು ಮಿಲ್ಡ್ಯೂ ರೋಗ",
    "Cercospora leaf spot Gray leaf spot": "ಸರ್ಕೋಸ್ಪೋರಾ ಎಲೆ ಚುಕ್ಕೆ / ಬೂದು ಎಲೆ ಚುಕ್ಕೆ ರೋಗ",
    "Common rust": "ಸಾಮಾನ್ಯ ತುಕ್ಕು ರೋಗ",
    "Northern Leaf Blight": "ಉತ್ತರ ಎಲೆ ಬ್ಲೈಟ್ ರೋಗ",
    "Esca (Black Measles)": "ಎಸ್ಕಾ ರೋಗ (ಕಪ್ಪು ಜ್ವರ)",
    "Leaf blight (Isariopsis Leaf Spot)": "ಎಲೆ ಬ್ಲೈಟ್ (ಇಸಾರಿಯೋಪ್ಸಿಸ್ ಎಲೆ ಚುಕ್ಕೆ)",
    "Haunglongbing (Citrus greening)": "ಹುವಾಂಗ್‌ಲಾಂಗ್‌ಬಿಂಗ್ (ಸಿಟ್ರಸ್ ಹಸಿರೀಕರಣ ರೋಗ)",
    "Bacterial spot": "ಬ್ಯಾಕ್ಟೀರಿಯಾ ಚುಕ್ಕೆ ರೋಗ",
    "Early blight": "ಆರಂಭಿಕ ಬ್ಲೈಟ್ ರೋಗ",
    "Late blight": "ತಡ ಬ್ಲೈಟ್ ರೋಗ",
    "Leaf Mold": "ಎಲೆ ಮಾಲ್ಡ್ ರೋಗ",
    "Septoria leaf spot": "ಸೆಪ್ಟೋರಿಯಾ ಎಲೆ ಚುಕ್ಕೆ ರೋಗ",
    "Spider mites Two-spotted spider mite": "ಸ್ಪೈಡರ್ ಮೈಟ್ (ಎರಡು ಚುಕ್ಕೆಯ ಸಣ್ಣ ಸೊಳ್ಳೆ)",
    "Target Spot": "ಗುರಿ ಚುಕ್ಕೆ ರೋಗ",
    "Tomato Yellow Leaf Curl Virus": "ಟೊಮ್ಯಾಟೊ ಹಳದಿ ಎಲೆ ಬಾಗುವಿಕೆ ವೈರಸ್",
    "Tomato mosaic virus": "ಟೊಮ್ಯಾಟೊ ಮೊಸೈಕ್ ವೈರಸ್",
    "Leaf scorch": "ಎಲೆ ಸುಟ್ಟಿಕೆ ರೋಗ",
    # Short forms the PlantDoc second-opinion model emits (see LABEL_MAP).
    "mosaic virus": "ಟೊಮ್ಯಾಟೊ ಮೊಸೈಕ್ ವೈರಸ್",
    "Yellow Leaf Curl Virus": "ಹಳದಿ ಎಲೆ ಬಾಗುವಿಕೆ ವೈರಸ್",
    "Spider mites": "ಸ್ಪೈಡರ್ ಮೈಟ್ (ಎರಡು ಚುಕ್ಕೆಯ ಸಣ್ಣ ಸೊಳ್ಳೆ)",
    "Blight": "ಎಲೆ ಬ್ಲೈಟ್ ರೋಗ",
    "Leaf Spot": "ಎಲೆ ಚುಕ್ಕೆ ರೋಗ",
}

# Keyed by model.py's TREATMENTS keys, plus "healthy" and "default".
ADVICE = {
    "healthy": "ಯಾವುದೇ ರೋಗ ಪತ್ತೆಯಾಗಿಲ್ಲ. ಬೆಳೆಯ ನಿಯಮಿತ ನಿಗಾ ಮುಂದುವರಿಸಿ ಮತ್ತು ಸಾಮಾನ್ಯ ಹೊಲದ ಸ್ವಚ್ಛತೆ ಕಾಪಾಡಿ.",
    "default": (
        "ಪೀಡಿತ ಸಸ್ಯಗಳನ್ನು ಪ್ರತ್ಯೇಕಿಸಿ, ತೀವ್ರ ರೋಗಗ್ರಸ್ತ ಎಲೆಗಳನ್ನು ತೆಗೆದುಹಾಕಿ, ಪ್ರದೇಶಕ್ಕೆ ಅನುಗುಣವಾದ ನಿಯಂತ್ರಣಕ್ಕಾಗಿ "
        "ಸ್ಥಳೀಯ ಕೃಷಿ ತಜ್ಞರನ್ನು ಸಂಪರ್ಕಿಸಿ."
    ),
    "Apple_scab": (
        "ರೋಗಗ್ರಸ್ತ ಎಲೆಗಳನ್ನು ತೆಗೆದುಹಾಕಿ; ಕೊಂಬೆ ಕಾಲದಲ್ಲಿ ಮತ್ತು ಕೊಯ್ಲಿನ ನಂತರ ಶಿಲೀಂಧ್ರನಾಶಕ "
        "(ಮೈಕ್ಲೋಬ್ಯುಟನಿಲ್ ಅಥವಾ ಕ್ಯಾಪ್ಟನ್) ಸಿಂಪಡಿಸಿ. ಕತ್ತರಿಸುವಿಕೆಯಿಂದ ಗಾಳಿ ಸಂಚಾರ ಸುಧಾರಿಸಿ."
    ),
    "Black_rot": (
        "ಒಣಗಿದ ಹಣ್ಣುಗಳು ಮತ್ತು ಕ್ಯಾಂಕರ್‌ಗಳನ್ನು ಕತ್ತರಿಸಿ, ಬಿದ್ದ ತ್ಯಾಜ್ಯವನ್ನು ತೆಗೆದುಹಾಕಿ, ಹೂವಿನ ಋತುವಿನಲ್ಲಿ "
        "ತಾಮ್ರ ಅಥವಾ ಸ್ಟ್ರೋಬಿಲ್ಯುರಿನ್ ಶಿಲೀಂಧ್ರನಾಶಕ ಸಿಂಪಡಿಸಿ."
    ),
    "Cedar_apple_rust": (
        "ಸಾಧ್ಯವಾದರೆ ಹತ್ತಿರದ ಜೂನಿಪರ್ ಸಸ್ಯಗಳನ್ನು ತೆಗೆದುಹಾಕಿ; ಹಸಿರು ತುದಿಯಿಂದ ಹೂವು ಉದುರುವವರೆಗೆ "
        "ಮ್ಯಾಂಕೋಜೆಬ್ ಅಥವಾ ಮೈಕ್ಲೋಬ್ಯುಟನಿಲ್ ಸಿಂಪಡಿಸಿ."
    ),
    "Powdery_mildew": (
        "ಸಲ್ಫರ್ ಅಥವಾ ಪೊಟ್ಯಾಸಿಯಂ ಬೈಕಾರ್ಬೊನೇಟ್ ಸಿಂಪಡಣೆ ಮಾಡಿ; ಮೇಲ್ಭಾಗದಿಂದ ನೀರು ಹಾಕುವುದನ್ನು ತಪ್ಪಿಸಿ ಮತ್ತು "
        "ಉತ್ತಮ ಗಾಳಿಚಲನೆ ಖಚಿತಪಡಿಸಿ."
    ),
    "Cercospora_leaf_spot": (
        "ರೋಗನಿರೋಧಕ ತಳಿಗಳನ್ನು ಬಳಸಿ, ಬೆಳೆ ಬದಲಾವಣೆ ಮಾಡಿ, ಮೊದಲ ಲಕ್ಷಣ ಕಂಡಾಗ ಎಲೆಮೇಲಿನ ಶಿಲೀಂಧ್ರನಾಶಕ "
        "(ಅಜೋಕ್ಸಿಸ್ಟ್ರೋಬಿನ್, ಪೈರಾಕ್ಲೋಸ್ಟ್ರೋಬಿನ್) ಸಿಂಪಡಿಸಿ."
    ),
    "Common_rust": (
        "ಸಾಮಾನ್ಯವಾಗಿ ಸಹಿಸಬಹುದು; ತೀವ್ರವಾದರೆ ಟ್ರೈಯಾಜೊಲ್/ಸ್ಟ್ರೋಬಿಲ್ಯುರಿನ್ ಶಿಲೀಂಧ್ರನಾಶಕ ಸಿಂಪಡಿಸಿ ಮತ್ತು ಮುಂದಿನ "
        "ಋತುವಿನಲ್ಲಿ ತುಕ್ಕು ನಿರೋಧಕ ತಳಿಗಳನ್ನು ಬಿತ್ತನೆ ಮಾಡಿ."
    ),
    "Northern_Leaf_Blight": (
        "ಬೆಳೆ ಬದಲಾವಣೆ ಮಾಡಿ, ರೋಗನಿರೋಧಕ ತಳಿಗಳನ್ನು ಬಳಸಿ, 50% ಸಸ್ಯಗಳಲ್ಲಿ ಗಾಯಗಳು ಅರ್ಧ ಇಂಚು ತಲುಪಿದಾಗ "
        "ಎಲೆಮೇಲಿನ ಶಿಲೀಂಧ್ರನಾಶಕ ಸಿಂಪಡಿಸಿ."
    ),
    "Esca": (
        "ಒಣ ಹವೆಯಲ್ಲಿ ಎಚ್ಚರಿಕೆಯಿಂದ ಕತ್ತರಿಸಿ, ಬೇಸಿಗೆಯ ಕತ್ತರಿಸುವಿಕೆಯ ಗಾಯಗಳನ್ನು ತಪ್ಪಿಸಿ, ಗಾಯಗಳಿಗೆ ಪೇಸ್ಟ್ "
        "ಹಚ್ಚಿ. ರೋಗ ಮುಂದುವರಿದ ನಂತರ ನಂಬಿಕೆಯ ಚಿಕಿತ್ಸೆ ಇಲ್ಲ."
    ),
    "Haunglongbing": (
        "ಚಿಕಿತ್ಸೆ ಇಲ್ಲ — ರೋಗಗ್ರಸ್ತ ಮರಗಳನ್ನು ತೆಗೆದುಹಾಕಿ, ಕೀಟನಾಶಕಗಳಿಂದ ಸಿಟ್ರಸ್ ಸಸ್ಯಹಾನಿಕಾರಕ ನೊಣಗಳನ್ನು "
        "ನಿಯಂತ್ರಿಸಿ, ಪ್ರಮಾಣಿತ ರೋಗಮುಕ್ತ ಸಸಿಗಳನ್ನು ಬಳಸಿ."
    ),
    "Bacterial_spot": (
        "ತಾಮ್ರ ಆಧಾರಿತ ಬ್ಯಾಕ್ಟೀರಿಯಾನಾಶಕ ಸಿಂಪಡಿಸಿ, ಪ್ರಮಾಣಿತ ಬೀಜ ಬಳಸಿ, ಬೆಳೆ ಬದಲಾವಣೆ ಮಾಡಿ, ಒದ್ದೆಯಾದ "
        "ಎಲೆಗಳೊಂದಿಗೆ ಕೆಲಸ ಮಾಡುವುದನ್ನು ತಪ್ಪಿಸಿ."
    ),
    "Early_blight": (
        "ಕೆಳಗಿನ ರೋಗಗ್ರಸ್ತ ಎಲೆಗಳನ್ನು ತೆಗೆದುಹಾಕಿ, ಮಣ್ಣು ಚೆಲ್ಲುವುದನ್ನು ತಡೆಯಲು ಮಲ್ಚಿಂಗ್ ಮಾಡಿ, 2-3 ವರ್ಷ "
        "ಬೆಳೆ ಬದಲಾವಣೆ ಮಾಡಿ, ಕ್ಲೋರೊಥಲೋನಿಲ್ ಅಥವಾ ಮ್ಯಾಂಕೋಜೆಬ್ ಸಿಂಪಡಿಸಿ."
    ),
    "Late_blight": (
        "ಬೇಗ ಕ್ರಮ ತೆಗೆದುಕೊಳ್ಳಿ: ರೋಗಗ್ರಸ್ತ ಸಸ್ಯಗಳನ್ನು ನಾಶಮಾಡಿ, ಮೆಟಾಲಾಕ್ಸಿಲ್-ಮ್ಯಾಂಕೋಜೆಬ್ ಅಥವಾ ತಾಮ್ರ "
        "ಸಿಂಪಡಿಸಿ, ರೋಗನಿರೋಧಕ ತಳಿಗಳನ್ನು ಬಳಸಿ. ಎಲೆಗಳನ್ನು ಒಣಗಿಸಿಡಿ."
    ),
    "Leaf_Mold": (
        "ಆರ್ದ್ರತೆ ಕಡಿಮೆ ಮಾಡಿ, ಅಂತರ ಮತ್ತು ಗಾಳಿಚಲನೆ ಸುಧಾರಿಸಿ, ಪೀಡಿತ ಎಲೆಗಳನ್ನು ತೆಗೆದುಹಾಕಿ, ಕ್ಲೋರೊಥಲೋನಿಲ್ "
        "ಅಥವಾ ತಾಮ್ರ ಸಿಂಪಡಿಸಿ."
    ),
    "Septoria_leaf_spot": (
        "ಸಸ್ಯಗಳಿಗೆ ಬೆಂಬಲ ಕಟ್ಟಿ ಮಲ್ಚಿಂಗ್ ಮಾಡಿ, ಕೆಳಗಿನ ಎಲೆಗಳನ್ನು ತೆಗೆದುಹಾಕಿ, 3+ ವರ್ಷ ಬೆಳೆ ಬದಲಾವಣೆ ಮಾಡಿ, "
        "7-10 ದಿನಗಳಿಗೊಮ್ಮೆ ಕ್ಲೋರೊಥಲೋನಿಲ್ ಸಿಂಪಡಿಸಿ."
    ),
    "Spider_mites": (
        "ಕೀಟನಾಶಕ ಸೋಪ್, ನೀಮ್ ಎಣ್ಣೆ ಅಥವಾ ಅಬಮೆಕ್ಟಿನ್; ಆರ್ದ್ರತೆ ಹೆಚ್ಚಿಸಿ ಮತ್ತು ಜೈವಿಕ ನಿಯಂತ್ರಣಕ್ಕಾಗಿ ಬೇಟೆಯಾಡುವ "
        "ಸೊಳ್ಳೆಗಳನ್ನು ಬಿಡುಗಡೆ ಮಾಡಿ."
    ),
    "Target_Spot": (
        "ಬೆಳೆ ಬದಲಾವಣೆ ಮಾಡಿ, ಸಸ್ಯ ತ್ಯಾಜ್ಯವನ್ನು ತೆಗೆದುಹಾಕಿ, ಮೇಲ್ಭಾಗದ ನೀರಾವರಿ ತಪ್ಪಿಸಿ, ಅಜೋಕ್ಸಿಸ್ಟ್ರೋಬಿನ್ "
        "ಅಥವಾ ಬಾಸ್ಕಲಿಡ್ ಸಿಂಪಡಿಸಿ."
    ),
    "Yellow_Leaf_Curl_Virus": (
        "ಚಿಕಿತ್ಸೆ ಇಲ್ಲ — ರೋಗಗ್ರಸ್ತ ಸಸ್ಯಗಳನ್ನು ತೆಗೆದು ನಾಶಮಾಡಿ, ಹಳದಿ ಸ್ಟಿಕಿ ಬಲೆ ಮತ್ತು ಇಮಿಡಾಕ್ಲೋಪ್ರಿಡ್‌ನಿಂದ "
        "ಬಿಳಿಏಡಿ ನಿಯಂತ್ರಿಸಿ, ಪ್ರತಿಫಲಿಸುವ ಮಲ್ಚ್ ಬಳಸಿ."
    ),
    "mosaic_virus": (
        "ಚಿಕಿತ್ಸೆ ಇಲ್ಲ — ರೋಗಗ್ರಸ್ತ ಸಸ್ಯಗಳನ್ನು ತೆಗೆದುಹಾಕಿ, ಹೇಮಿ/ಬಿಳಿಏಡಿ ನಿಯಂತ್ರಿಸಿ, ಸಸ್ಯಗಳ ನಡುವೆ ಕೈ ಮತ್ತು "
        "ಉಪಕರಣಗಳನ್ನು ತೊಳೆಯಿರಿ, ವೈರಸ್‌ಮುಕ್ತ ಬೀಜ ಬಳಸಿ."
    ),
    "Leaf_scorch": (
        "ರೋಗಗ್ರಸ್ತ ಸಸ್ಯಗಳನ್ನು ತೆಗೆದು ನಾಶಮಾಡಿ, ಬರ ಒತ್ತಡ ತಪ್ಪಿಸಲು ನೀರಾವರಿ ಮಾಡಿ, ಮಣ್ಣನ್ನು ಆಮ್ಲೀಯಗೊಳಿಸಿ, "
        "ಮೇಲ್ಭಾಗದ ನೀರುಹಾಕುವಿಕೆ ತಪ್ಪಿಸಿ."
    ),
    "Leaf_blight": (
        "ಬಿದ್ದ ಎಲೆಗಳನ್ನು ತೆಗೆದುಹಾಕಿ, ತಾಮ್ರ ಅಥವಾ ಮ್ಯಾಂಕೋಜೆಬ್ ಸಿಂಪಡಿಸಿ, ಉತ್ತಮ ಗಾಳಿ ಸಂಚಾರ ಖಚಿತಪಡಿಸಿ."
    ),
}

# --- Abstention / identification reasons -------------------------------------

REASONS = {
    "low_confidence": {
        "en": "low model confidence",
        "kn": "ಮಾಡೆಲ್ ವಿಶ್ವಾಸಾರ್ಹತೆ ಕಡಿಮೆ",
    },
    "high_entropy": {
        "en": "spread-out probabilities",
        "kn": "ಸಮಾನವಾಗಿ ಹರಡಿದ ಸಂಭಾವ್ಯತೆಗಳು",
    },
    "unlike_training_data": {
        "en": "unlike any training photo",
        "kn": "ತರಬೇತಿ ಚಿತ್ರಗಳಿಗಿಂತ ಭಿನ್ನ",
    },
    "no_leaf_texture": {
        "en": "no leaf texture (flat/synthetic)",
        "kn": "ಎಲೆಯ ವಿನ್ಯಾಸವಿಲ್ಲ (ಸಮತಲ/ಕೃತ್ರಿಮ)",
    },
    "close_call": {
        "en": "top candidates too close to call",
        "kn": "ಅತ್ಯಂತ ಹತ್ತಿರದ ಆಯ್ಕೆಗಳು",
    },
    "inconsistent": {
        "en": "the photo answers differently when cropped",
        "kn": "ಫೋಟೋವನ್ನು ಕತ್ತರಿಸಿದಾಗ ಉತ್ತರ ಬದಲಾಗುತ್ತದೆ",
    },
    "experts_disagree": {
        "en": "the two models name different plants",
        "kn": "ಎರಡು ಮಾಡೆಲ್‌ಗಳು ಬೇರೆ ಸಸ್ಯಗಳನ್ನು ಹೇಳುತ್ತವೆ",
    },
    "model_unavailable": {
        "en": "identification model unavailable",
        "kn": "ಗುರುತಿಸುವ ಮಾಡೆಲ್ ಲಭ್ಯವಿಲ್ಲ",
    },
    "no_signal": {
        "en": "no reliable signal in this image",
        "kn": "ಚಿತ್ರದಲ್ಲಿ ವಿಶ್ವಾಸಾರ್ಹ ಸುಳಿವಿಲ್ಲ",
    },
}

# --- Phrases emitted by the backend ------------------------------------------
# Each entry: key -> {"en": ..., "kn": ...}; params via str.format().

EVIDENCE = {
    "evidence.corpus_match": {
        "en": "matches the training corpus (feature similarity {sim} vs 0.42 required)",
        "kn": "ತರಬೇತಿ ದತ್ತಸಂಚಯಕ್ಕೆ ಹೊಂದಿಕೆಯಾಗುತ್ತದೆ (ವೈಶಿಷ್ಟ್ಯ ಸಾಮ್ಯತೆ {sim}, ಬೇಕಾದದ್ದು 0.42)",
    },
    "evidence.peak_conf": {
        "en": "peak confidence {conf}",
        "kn": "ಗರಿಷ್ಠ ವಿಶ್ವಾಸಾರ್ಹತೆ {conf}",
    },
    "evidence.texture": {
        "en": "real leaf texture (score {rough})",
        "kn": "ನೈಜ ಎಲೆಯ ವಿನ್ಯಾಸ (ಅಂಕ {rough})",
    },
    "evidence.second_agrees": {
        "en": "an independent second model reaches the same diagnosis",
        "kn": "ಸ್ವತಂತ್ರ ಎರಡನೇ ಮಾಡೆಲ್ ಅದೇ ರೋಗನಿರ್ಣಯಕ್ಕೆ ಬರುತ್ತದೆ",
    },
    "evidence.crop_claim": {
        "en": "the crop model instead claimed {crop} (feature similarity {sim})",
        "kn": "ಬದಲಾಗಿ ಬೆಳೆ ಮಾಡೆಲ್ {crop} ಎಂದು ಹೇಳಿತು (ವೈಶಿಷ್ಟ್ಯ ಸಾಮ್ಯತೆ {sim})",
    },
    "evidence.top5_genus": {
        "en": "top-5 candidates are all the same genus",
        "kn": "ಅಗ್ರ 5 ಆಯ್ಕೆಗಳೆಲ್ಲವೂ ಒಂದೇ ವರ್ಗಕ್ಕೆ ಸೇರಿವೆ",
    },
    "evidence.tta_stable": {
        "en": "same answer from all 7 crops of the photo ({pct})",
        "kn": "ಫೋಟೋದ 7 ಭಾಗಗಳಿಂದಲೂ ಒಂದೇ ಉತ್ತರ ({pct})",
    },
    "evidence.mnet_agrees": {
        "en": "independent MobileNet model agrees on the genus",
        "kn": "ಸ್ವತಂತ್ರ MobileNet ಮಾಡೆಲ್ ವರ್ಗದ ಬಗ್ಗೆ ಏಕಮತ",
    },
    "evidence.mnet_lone": {
        "en": "second model differs - identification rests on ResNet18 alone",
        "kn": "ಎರಡನೇ ಮಾಡೆಲ್ ಭಿನ್ನವಾಗಿದೆ - ಗುರುತಿಸುವಿಕೆ ರೆಸ್‌ನೆಟ್18 ಅವಲಂಬಿತ",
    },
}

NOTES = {
    "note.crops": {
        "en": "One of the {n} crops this app diagnoses.",
        "kn": "ಈ ಆ್ಯಪ್ ರೋಗನಿರ್ಣಯ ಮಾಡುವ {n} ಬೆಳೆಗಳಲ್ಲಿ ಒಂದು.",
    },
    "note.species": {
        "en": (
            "Named by the species model, but this plant is not one of the 14 crops "
            "the disease model covers - so no treatment advice."
        ),
        "kn": (
            "ಪ್ರಭೇದ ಮಾಡೆಲ್ ಹೆಸರಿಸಿದೆ, ಆದರೆ ಈ ಸಸ್ಯ ರೋಗ ಮಾಡೆಲ್ ವ್ಯಾಪ್ತಿಯ 14 ಬೆಳೆಗಳಲ್ಲಿ ಒಂದಲ್ಲ - "
            "ಆದ್ದರಿಂದ ಚಿಕಿತ್ಸಾ ಸಲಹೆ ಇಲ್ಲ."
        ),
    },
    "note.species_override": {
        "en": (
            "Identified by the species model; the crop model disagreed (said {crop}), "
            "so this is outside the 14 crops and no treatment advice is given."
        ),
        "kn": (
            "ಪ್ರಭೇದ ಮಾಡೆಲ್ ಗುರುತಿಸಿದೆ; ಬೆಳೆ ಮಾಡೆಲ್ ಏಕಮತವಾಗಿಲ್ಲ ({crop} ಎಂದಿತು), ಆದ್ದರಿಂದ ಇದು 14 "
            "ಬೆಳೆಗಳ ಹೊರಗಿದೆ ಮತ್ತು ಚಿಕಿತ್ಸಾ ಸಲಹೆ ಇಲ್ಲ."
        ),
    },
    "note.conflict": {
        "en": (
            "The two models name different plants for this photo, so there is no "
            "answer we can stand behind."
        ),
        "kn": (
            "ಈ ಫೋಟೋಗೆ ಎರಡು ಮಾಡೆಲ್‌ಗಳು ಬೇರೆ ಸಸ್ಯಗಳ ಹೆಸರನ್ನು ಹೇಳುತ್ತವೆ, ಆದ್ದರಿಂದ ನಮಗೆ ಒಪ್ಪಿಕೊಳ್ಳಲು "
            "ಯಾವುದೇ ಉತ್ತರವಿಲ್ಲ."
        ),
    },
    "note.not_identified": {
        "en": (
            "Not identified. Retake the photo with one leaf filling the frame, "
            "daylight, and a plain background."
        ),
        "kn": (
            "ಗುರುತಿಸಲಾಗಿಲ್ಲ. ಒಂದೇ ಎಲೆ ಚೌಕಟ್ಟನ್ನು ತುಂಬುವಂತೆ, ಹಗಲ ಬೆಳಕಿನಲ್ಲಿ, ಸರಳ ಹಿನ್ನೆಲೆಯೊಂದಿಗೆ "
            "ಮತ್ತೆ ಫೋಟೊ ತೆಗೆಯಿರಿ."
        ),
    },
}

HEADLINES = {
    "headline.not_identified": {
        "en": (
            "We could not confidently identify this leaf, so every guess below "
            "should be treated as unreliable."
        ),
        "kn": (
            "ನಮಗೆ ಈ ಎಲೆಯನ್ನು ವಿಶ್ವಾಸಾರ್ಹವಾಗಿ ಗುರುತಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ, ಆದ್ದರಿಂದ ಕೆಳಗಿನ ಪ್ರತಿಯೊಂದು "
            "ಊಹೆಯನ್ನೂ ವಿಶ್ವಾಸಾರ್ಹವಲ್ಲ ಎಂದು ಪರಿಗಣಿಸಬೇಕು."
        ),
    },
    "headline.identified_only": {
        "en": (
            "Identified as {name}. This species is outside the 14 crops the disease "
            "model covers, so there is no diagnosis or treatment advice for it."
        ),
        "kn": (
            "{name} ಎಂದು ಗುರುತಿಸಲಾಗಿದೆ. ಈ ಪ್ರಭೇದ ರೋಗ ಮಾಡೆಲ್ ವ್ಯಾಪ್ತಿಯ 14 ಬೆಳೆಗಳ ಹೊರಗಿದೆ, "
            "ಆದ್ದರಿಂದ ಅದಕ್ಕೆ ರೋಗನಿರ್ಣಯ ಅಥವಾ ಚಿಕಿತ್ಸಾ ಸಲಹೆ ಇಲ್ಲ."
        ),
    },
    "headline.disputed": {
        "en": (
            "The two models disagree about this leaf, so confidence is limited. "
            "Consider a close-up of a single leaf and its underside."
        ),
        "kn": (
            "ಈ ಎಲೆಯ ಬಗ್ಗೆ ಎರಡು ಮಾಡೆಲ್‌ಗಳು ಏಕಮತವಾಗಿಲ್ಲ, ಆದ್ದರಿಂದ ವಿಶ್ವಾಸಾರ್ಹತೆ ಮಿತವಾಗಿದೆ. "
            "ಒಂದೇ ಎಲೆಯ ಹತ್ತಿರದ ಚಿತ್ರ ಮತ್ತು ಅದರ ಕೆಳಭಾಗ ತೆಗೆಯಿರಿ."
        ),
    },
}

# Trust verdicts (second_opinion.py emits label_key/note_key + params).
TRUST = {
    "trust.single.label": {"en": "Single model", "kn": "ಒಂದೇ ಮಾಡೆಲ್"},
    "trust.single.note": {
        "en": "Second-opinion model unavailable; verdict comes from the CNN alone.",
        "kn": "ದ್ವಿತೀಯ ಅಭಿಪ್ರಾಯ ಮಾಡೆಲ್ ಲಭ್ಯವಿಲ್ಲ; ತೀರ್ಪು ಸಿಎನ್‌ಎನ್‌ನಿಂದ ಮಾತ್ರ.",
    },
    "trust.weak.label": {
        "en": "CNN verdict (second opinion too unsure)",
        "kn": "ಸಿಎನ್‌ಎನ್ ತೀರ್ಪು (ದ್ವಿತೀಯ ಅಭಿಪ್ರಾಯ ಅಸ್ಪಷ್ಟ)",
    },
    "trust.weak.note": {
        "en": (
            "The independent PlantDoc model was only {conf} confident, too weak "
            "to confirm or contradict the CNN - so its guess is set aside."
        ),
        "kn": (
            "ಸ್ವತಂತ್ರ PlantDoc ಮಾಡೆಲ್ {conf} ಮಾತ್ರ ವಿಶ್ವಾಸಾರ್ಹವಾಗಿತ್ತು, ಸಿಎನ್‌ಎನ್ ದೃಢೀಕರಿಸಲು/ಖಂಡಿಸಲು "
            "ಅದು ದುರ್ಬಲವಾಗಿತ್ತು - ಆದ್ದರಿಂದ ಅದರ ಊಹೆಯನ್ನು ಕಡೆಗಣಿಸಲಾಗಿದೆ."
        ),
    },
    "trust.high.label": {"en": "Both models agree", "kn": "ಎರಡು ಮಾಡೆಲ್‌ಗಳೂ ಏಕಮತ"},
    "trust.high.note": {
        "en": "The CNN and an independent PlantDoc ViT reach the same diagnosis.",
        "kn": "ಸಿಎನ್‌ಎನ್ ಮತ್ತು ಸ್ವತಂತ್ರ PlantDoc ViT ಅದೇ ರೋಗನಿರ್ಣಯಕ್ಕೆ ಬರುತ್ತವೆ.",
    },
    "trust.high_medium.note": {
        "en": (
            "Both models reach the same diagnosis, though the PlantDoc model was "
            "only {conf} confident - treat as likely rather than certain."
        ),
        "kn": (
            "ಎರಡು ಮಾಡೆಲ್‌ಗಳೂ ಅದೇ ರೋಗನಿರ್ಣಯಕ್ಕೆ ಬರುತ್ತವೆ, ಆದರೆ PlantDoc ಮಾಡೆಲ್ {conf} ಮಾತ್ರ "
            "ವಿಶ್ವಾಸಾರ್ಹವಾಗಿತ್ತು - ಖಚಿತವಲ್ಲ, ಸಂಭವನೀಯ ಎಂದು ಪರಿಗಣಿಸಿ."
        ),
    },
    "trust.medium.label": {
        "en": "Crops match, severity differs",
        "kn": "ಬೆಳೆ ಹೊಂದಿಕೆಯಾಗುತ್ತದೆ, ತೀವ್ರತೆ ಭಿನ್ನ",
    },
    "trust.medium.note": {
        "en": (
            "Both models agree on the crop but differ on the exact condition - "
            "treat as a strong hint, not a certainty."
        ),
        "kn": (
            "ಎರಡು ಮಾಡೆಲ್‌ಗಳೂ ಬೆಳೆಯ ಬಗ್ಗೆ ಏಕಮತವಾಗಿವೆ ಆದರೆ ನಿಖರ ಸ್ಥಿತಿಯಲ್ಲಿ ಭಿನ್ನ - ಇದು ಬಲವಾದ "
            "ಸುಳಿವು, ಖಚಿತತೆಯಲ್ಲ."
        ),
    },
    "trust.low.label": {"en": "Models disagree", "kn": "ಮಾಡೆಲ್‌ಗಳು ಏಕಮತವಾಗಿಲ್ಲ"},
    "trust.low.note": {
        "en": (
            "The two models name different crops ({crop1} vs {crop2}). This photo "
            "may sit outside the 14 species we cover - verify with a local agronomist."
        ),
        "kn": (
            "ಎರಡು ಮಾಡೆಲ್‌ಗಳು ಬೇರೆ ಬೆಳೆಗಳ ಹೆಸರನ್ನು ಹೇಳುತ್ತವೆ ({crop1} ಮತ್ತು {crop2}). ಈ ಫೋಟೊ "
            "ನಮ್ಮ ವ್ಯಾಪ್ತಿಯ 14 ಪ್ರಭೇದಗಳ ಹೊರಗೆ ಇರಬಹುದು - ಸ್ಥಳೀಯ ಕೃಷಿ ತಜ್ಞರೊಂದಿಗೆ ದೃಢೀಕರಿಸಿ."
        ),
    },
}

# --- Frontend UI strings ------------------------------------------------------
# Served by GET /i18n so the SPA has one source of truth.

UI = {
    "tagline": {"en": "CNN crop-disease detection", "kn": "ಸಿಎನ್‌ಎನ್ ಬೆಳೆ ರೋಗ ಪತ್ತೆ"},
    "badge_online": {"en": "● model online", "kn": "● ಮಾಡೆಲ್ ಆನ್‌ಲೈನ್"},
    "badge_offline": {"en": "● backend offline", "kn": "● ಬ್ಯಾಕ್‌ಎಂಡ್ ಆಫ್‌ಲೈನ್"},
    "lang_label": {"en": "Language", "kn": "ಭಾಷೆ"},
    "pill": {
        "en": "38 disease classes · 14 crop species",
        "kn": "38 ರೋಗ ವರ್ಗಗಳು · 14 ಬೆಳೆ ಪ್ರಭೇದಗಳು",
    },
    "hero_title_a": {"en": "Diagnose crop disease from a", "kn": "ಬೆಳೆ ರೋಗವನ್ನು ಪತ್ತೆಹಚ್ಚಿ -"},
    "hero_title_em": {"en": "single leaf photo", "kn": "ಒಂದೇ ಎಲೆಯ ಫೋಟೋದಿಂದ"},
    "hero_body": {
        "en": (
            "Upload a picture or snap one with your camera. A convolutional neural "
            "network returns the most likely condition, its confidence, and "
            "field-level treatment advice."
        ),
        "kn": (
            "ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ ಅಥವಾ ಕ್ಯಾಮೆರಾದಿಂದ ತೆಗೆದುಕೊಳ್ಳಿ. ಸಂಪೂರ್ಣ ನರಜ್ಞಾನ ಜಾಲವು "
            "(CNN) ಸಾಧ್ಯವಾದ ರೋಗ, ಅದರ ವಿಶ್ವಾಸಾರ್ಹತೆ ಮತ್ತು ಹೊಲದ ಮಟ್ಟದ ಚಿಕಿತ್ಸಾ ಸಲಹೆಯನ್ನು ನೀಡುತ್ತದೆ."
        ),
    },
    "drop_title": {"en": "Drop a leaf photo here", "kn": "ಇಲ್ಲಿ ಎಲೆಯ ಫೋಟೋವನ್ನು ಬಿಡಿ"},
    "drop_sub": {
        "en": "or click to browse · JPG / PNG · max 8 MB",
        "kn": "ಅಥವಾ ಕ್ಲಿಕ್ ಮಾಡಿ ಆಯ್ಕೆ ಮಾಡಿ · JPG/PNG · ಗರಿಷ್ಠ 8 MB",
    },
    "btn_analyze": {"en": "Analyze leaf", "kn": "ಎಲೆಯನ್ನು ವಿಶ್ಲೇಷಿಸಿ"},
    "btn_analyzing": {"en": "Analyzing…", "kn": "ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ…"},
    "btn_camera": {"en": "📷 Take photo", "kn": "📷 ಫೋಟೊ ತೆಗೆಯಿರಿ"},
    "alt_selected_leaf": {"en": "Selected leaf", "kn": "ಆಯ್ಕೆ ಮಾಡಿದ ಎಲೆ"},
    "samples_title": {"en": "Or try a sample leaf", "kn": "ಅಥವಾ ಮಾದರಿ ಎಲೆಯನ್ನು ಪ್ರಯತ್ನಿಸಿ"},
    "sample_corn": {"en": "Corn rust", "kn": "ಮೆಕ್ಕೆಜೋಳ ತುಕ್ಕು"},
    "sample_potato": {"en": "Potato early blight", "kn": "ಆಲೂಗಡ್ಡೆ ಆರಂಭಿಕ ಬ್ಲೈಟ್"},
    "sample_tomato": {"en": "Tomato bacterial spot", "kn": "ಟೊಮ್ಯಾಟೊ ಬ್ಯಾಕ್ಟೀರಿಯಾ ಚುಕ್ಕೆ"},
    "loading": {"en": "Analyzing leaf tissue…", "kn": "ಎಲೆಯ ಅಂಗಾಂಶವನ್ನು ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ…"},
    "empty": {"en": "The diagnosis will appear here.", "kn": "ರೋಗನಿರ್ಣಯ ಇಲ್ಲಿ ಕಾಣಿಸುತ್ತದೆ."},
    "err_image": {
        "en": "Please choose an image file (JPG or PNG).",
        "kn": "ದಯವಿಟ್ಟು ಚಿತ್ರ ಕಡತವನ್ನು ಆಯ್ಕೆ ಮಾಡಿ (JPG ಅಥವಾ PNG).",
    },
    "footer": {
        "en": "Keras 3 · PyTorch (CUDA) · FastAPI · React + Vite — built from scratch",
        "kn": "ಕೆರಸ್ 3 · ಪೈಟಾರ್ಚ್ (CUDA) · ಫಾಸ್ಟ್‌ಎಪಿಐ · ರಿಯಾಕ್ಟ್ + ವೈಟ್ — ಮೊದಲನೆಯದರಿಂದ ನಿರ್ಮಿಸಲಾಗಿದೆ",
    },
    # Result panel
    "status_not_identified": {"en": "❓ Not identified", "kn": "❓ ಗುರುತಿಸಲಾಗಿಲ್ಲ"},
    "status_identified_only": {
        "en": "🌱 Identified (no diagnosis)",
        "kn": "🌱 ಗುರುತಿಸಲಾಗಿದೆ (ರೋಗನಿರ್ಣಯ ಇಲ್ಲ)",
    },
    "status_disputed": {"en": "⚠ Conflicting signals", "kn": "⚠ ವಿರೋಧಾಭಾಸದ ಸೂಚನೆಗಳು"},
    "status_healthy": {"en": "✅ Healthy", "kn": "✅ ಆರೋಗ್ಯಕರ"},
    "status_disease": {"en": "🦠 Disease detected", "kn": "🦠 ರೋಗ ಪತ್ತೆಯಾಗಿದೆ"},
    "ident_yes": {"en": "Leaf identified:", "kn": "ಎಲೆ ಗುರುತಿಸಲಾಗಿದೆ:"},
    "ident_no": {"en": "Not identified", "kn": "ಗುರುತಿಸಲಾಗಿಲ್ಲ"},
    "ident_no_body": {
        "en": "Neither model could prove what plant this is, so no name is given rather than a wrong one.",
        "kn": (
            "ಎರಡೂ ಮಾಡೆಲ್‌ಗಳು ಯಾವ ಸಸ್ಯವೆಂದು ಸಾಬೀತುಪಡಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ, ಆದ್ದರಿಂದ ತಪ್ಪಾದ "
            "ಹೆಸರಿನ ಬದಲು ಯಾವುದೇ ಹೆಸರನ್ನು ನೀಡಲಾಗುತ್ತಿಲ್ಲ."
        ),
    },
    "ident_why": {"en": "Why:", "kn": "ಕಾರಣ:"},
    "ident_guess": {
        "en": "Closest guess (unreliable):",
        "kn": "ಹತ್ತಿರದ ಊಹೆ (ವಿಶ್ವಾಸಾರ್ಹವಲ್ಲ):",
    },
    "tip_1": {
        "en": "Fill the frame with a single leaf, in daylight",
        "kn": "ಹಗಲ ಬೆಳಕಿನಲ್ಲಿ ಒಂದೇ ಎಲೆಯಿಂದ ಚೌಕಟ್ಟನ್ನು ತುಂಬಿರಿ",
    },
    "tip_2": {"en": "Use a plain background and avoid shadows", "kn": "ಸರಳ ಹಿನ್ನೆಲೆ ಬಳಸಿ, ನೆರಳು ತಪ್ಪಿಸಿ"},
    "tip_3": {
        "en": "Include the leaf edge and underside if spots are only on the back",
        "kn": "ಚುಕ್ಕೆಗಳು ಕೇವಲ ಹಿಂಭಾಗದಲ್ಲಿದ್ದರೆ ಎಲೆಯ ಅಂಚು ಮತ್ತು ಕೆಳಭಾಗ ಸೇರಿಸಿ",
    },
    "conflict_crop": {"en": "Crop model", "kn": "ಬೆಳೆ ಮಾಡೆಲ್"},
    "conflict_species": {"en": "Species model", "kn": "ಪ್ರಭೇದ ಮಾಡೆಲ್"},
    "conflict_says": {"en": "says", "kn": "ಹೇಳುವುದು"},
    "gauge_confidence": {"en": "confidence", "kn": "ವಿಶ್ವಾಸಾರ್ಹತೆ"},
    "second_line": {
        "en": "Independent PlantDoc ViT says:",
        "kn": "ಸ್ವತಂತ್ರ PlantDoc ViT ಹೇಳುವುದು:",
    },
    "advice_title": {"en": "💡 Recommended action", "kn": "💡 ಶಿಫಾರಸು ಮಾಡಿದ ಕ್ರಮ"},
    "covered_title": {
        "en": "Crops this model is trained on",
        "kn": "ಈ ಮಾಡೆಲ್ ತರಬೇತಿ ಪಡೆದ ಬೆಳೆಗಳು",
    },
    "disclaimer": {
        "en": "AI-generated diagnosis — confirm with a local agronomist before applying chemicals.",
        "kn": (
            "ಎಐ-ಜನಿತ ರೋಗನಿರ್ಣಯ — ರಾಸಾಯನಿಕಗಳನ್ನು ಬಳಸುವ ಮೊದಲು ಸ್ಥಳೀಯ ಕೃಷಿ ತಜ್ಞರೊಂದಿಗೆ "
            "ದೃಢೀಕರಿಸಿ."
        ),
    },
    # Camera modal
    "cam_title": {"en": "📷 Leaf camera", "kn": "📷 ಎಲೆ ಕ್ಯಾಮೆರಾ"},
    "cam_cancel": {"en": "Cancel", "kn": "ರದ್ದುಗೊಳಿಸಿ"},
    "cam_capture": {"en": "📸 Capture leaf", "kn": "📸 ಎಲೆ ಸೆರೆಹಿಡಿಯಿರಿ"},
    "cam_starting": {"en": "Starting camera…", "kn": "ಕ್ಯಾಮೆರಾ ಆರಂಭವಾಗುತ್ತಿದೆ…"},
    "cam_no_api": {
        "en": 'This browser has no camera API — use "Analyze leaf" to pick a file instead.',
        "kn": "ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಕ್ಯಾಮೆರಾ API ಇಲ್ಲ — ಬದಲಿಗೆ \"ಎಲೆಯನ್ನು ವಿಶ್ಲೇಷಿಸಿ\" ಮೂಲಕ ಕಡತ ಆಯ್ಕೆ ಮಾಡಿ.",
    },
    "cam_denied": {
        "en": "Camera permission denied. Allow camera access in your browser and try again.",
        "kn": (
            "ಕ್ಯಾಮೆರಾ ಅನುಮತಿ ನಿರಾಕರಿಸಲಾಗಿದೆ. ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಕ್ಯಾಮೆರಾ ಪ್ರವೇಶವನ್ನು ಅನುಮತಿಸಿ ಮತ್ತೆ "
            "ಪ್ರಯತ್ನಿಸಿ."
        ),
    },
    "cam_none": {
        "en": "No camera found on this device — upload a photo instead.",
        "kn": "ಈ ಸಾಧನದಲ್ಲಿ ಯಾವುದೇ ಕ್ಯಾಮೆರಾ ಕಂಡುಬಂದಿಲ್ಲ — ಬದಲಿಗೆ ಫೋಟೊ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
    },
    "cam_failed": {
        "en": "Could not open the camera ({err}). Upload a photo instead.",
        "kn": "ಕ್ಯಾಮೆರಾ ತೆರೆಯಲಾಗಲಿಲ್ಲ ({err}). ಬದಲಿಗೆ ಫೋಟೊ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
    },
}


# --- Lookup helpers -----------------------------------------------------------


def tr(lang: str, table: dict, key: str, /, **params) -> str:
    """Render `key` from `table` in `lang`, falling back to English/Kannada."""
    if lang not in LANGS:
        lang = "en"
    entry = table.get(key)
    if entry is None:
        return key  # unknown key: show it rather than crash
    text = entry.get(lang) or entry.get("en") or key
    try:
        return text.format(**params) if params else text
    except (KeyError, IndexError):  # param mismatch: show the template
        return text


def _crop_key(name: str) -> str:
    """Normalize a raw class prefix to a display crop: 'Corn_(maize)' -> 'Corn'."""
    pretty = (
        name.strip()
        .replace("(maize)", "")
        .replace("_(including_sour)", "")
        .replace(",_bell", "")
        .replace("(", " ")
        .replace(")", "")
        .replace("_", " ")
    )
    return " ".join(pretty.split())


def crop_name(lang: str, english: str) -> str:
    if lang != "kn":
        return english
    key = _crop_key(english)
    return CROPS.get(key, english)


def disease_name(lang: str, english: str) -> str:
    if lang != "kn":
        return english
    return DISEASES.get(english.strip(), english)


def advice_text(lang: str, key: str, english: str) -> str:
    if lang != "kn":
        return english
    return ADVICE.get(key, english)


def reason_text(lang: str, key: str) -> str:
    return tr(lang, REASONS, key)


def localize_result(result: dict, lang: str) -> dict:
    """Rewrite a /predict response into `lang` (in place, returns it).

    Only human-readable fields are touched; keys, statuses, confidences and
    Latin species names stay as they are (scientific names are never
    translated).
    """
    if lang == "en":
        return result

    # Headline: built from headline_key + params by main.py.
    if result.get("headline_key"):
        result["headline"] = tr(
            lang, HEADLINES, result.pop("headline_key"), **result.pop("headline_params", {})
        )

    ident = result.get("identification") or {}
    if ident:
        if ident.get("method") == "crop_disease_cnn" and ident.get("name"):
            ident["name"] = crop_name(lang, ident["name"])
        ident["evidence"] = [
            tr(lang, EVIDENCE, e["key"], **e.get("params", {}))
            for e in ident.get("evidence_keys", [])
        ] or ident.get("evidence", [])
        if ident.get("note_key"):
            ident["note"] = tr(
                lang, NOTES, ident.pop("note_key"), **ident.pop("note_params", {})
            )
        conflict = ident.get("conflict")
        if conflict:
            conflict["crop_model"] = crop_name(lang, conflict.get("crop_model", ""))
        # alternatives are Latin species names - never translated.

    # Trust verdict.
    trust = result.get("trust")
    if trust:
        if trust.get("label_key"):
            trust["label"] = tr(lang, TRUST, trust.pop("label_key"))
        if trust.get("note_key"):
            params = trust.pop("note_params", {})
            # crop1/crop2 arrive as raw class prefixes: 'Corn_(maize)' -> 'Corn'
            params = {
                k: (crop_name(lang, v) if k.startswith("crop") else v)
                for k, v in params.items()
            }
            trust["note"] = tr(lang, TRUST, trust.pop("note_key"), **params)

    # Prediction rows (best + top_k + second opinion).
    def fix_row(row: dict | None) -> None:
        if not row:
            return
        # 'plant' for CNN rows, 'crop' for the PlantDoc second opinion.
        if row.get("plant"):
            row["plant"] = crop_name(lang, row["plant"])
        if row.get("crop"):
            row["crop"] = crop_name(lang, row["crop"])
        if row.get("disease"):
            row["disease"] = disease_name(lang, row["disease"])
        if row.get("advice_key"):
            row["advice"] = advice_text(lang, row["advice_key"], row.get("advice", ""))

    fix_row(result)
    for row in result.get("top_k", []):
        fix_row(row)
    fix_row(result.get("second_model"))

    result["covered_crops"] = [crop_name(lang, c) for c in result.get("covered_crops", [])]
    result["lang"] = lang
    return result
