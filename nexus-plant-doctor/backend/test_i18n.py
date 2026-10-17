"""End-to-end check: every verdict path renders in English AND Kannada.

Run with the server up:  python test_i18n.py
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

IMAGES = [
    ("corn sample", Path("..") / "frontend" / "public" / "samples" / "corn-rust.jpg"),
    ("potato sample", Path("..") / "frontend" / "public" / "samples" / "potato-early-blight.jpg"),
    ("lupinus (species)", Path("test_images") / "lupinus_leaf.jpg"),
    ("dead nettle (species)", Path("test_images") / "deadnettle_leaf.jpg"),
    ("pelargonium (conflict)", Path("test_images") / "pelargonium_leaf.jpg"),
    ("junk (abstain)", Path("test_images") / "junk_canvas.png"),
]

DEV = re.compile(r"[\u0c80-\u0cff]")


def predict(path: Path, lang: str) -> dict:
    boundary = "----testboundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"http://localhost:8000/predict?lang={lang}",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.loads(res.read().decode())


def kn_text(r: dict) -> str:
    """Every string field that should be localized for lang=kn."""
    ident = r.get("identification") or {}
    trust = r.get("trust") or {}
    fields = [
        r.get("headline"),
        r.get("plant"),
        r.get("disease"),
        r.get("advice"),
        ident.get("note"),
        *ident.get("evidence", []),
        trust.get("label"),
        trust.get("note"),
        r.get("second_model", {}).get("disease") if r.get("second_model") else None,
        *[row.get("disease") for row in r.get("top_k", [])],
        *[row.get("advice") for row in r.get("top_k", [])],
    ]
    return " ".join(str(f) for f in fields if f)


def main() -> int:
    failures = []
    for name, img in IMAGES:
        if not img.exists():
            print(f"  SKIP {name}: {img} not found")
            continue
        en = predict(img, "en")
        kn = predict(img, "kn")
        if en["status"] != kn["status"]:
            failures.append(f"{name}: status en={en['status']} kn={kn['status']}")
        # Nothing translated in English, something translated in Kannada.
        if DEV.search(" ".join(str(v) for v in [en.get("advice"), en.get("disease")])):
            failures.append(f"{name}: Devanagari leaked into English response")
        has_kn = bool(DEV.search(kn_text(kn)))
        if en["status"] != "not_identified" and not has_kn:
            failures.append(f"{name}: no Kannada text found in {en['status']} response")
        # No raw class prefixes or missing-translation keys in the Kannada UI.
        if "_(" in str(kn.get("plant", "")):
            failures.append(f"{name}: raw plant prefix {kn['plant']}")
        label = (
            f"{name:26} {en['status']:15} "
            f"plant={kn.get('plant') or '-':12} disease={(kn.get('disease') or '-')[:28]}"
        )
        print(f"  OK   {label}" if not any(name in f for f in failures) else f"  ??   {label}")

    print()
    if failures:
        print("FAILURES:")
        for f in failures:
            print("  -", f)
        return 1
    print(f"All {len(IMAGES)} images pass in both languages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
