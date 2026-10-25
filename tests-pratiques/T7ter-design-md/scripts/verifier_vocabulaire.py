"""Liste les mots (5 lettres et plus, sans accents ni casse) communs à DESIGN.md et à un énoncé.

Usage : uv run --no-project python -I scripts/verifier_vocabulaire.py tache-ecran2.md [tache-T7.md]
"""
import re, sys, unicodedata
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent


def mots(texte):
    t = unicodedata.normalize("NFD", texte.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return set(re.findall(r"[a-z]{5,}", t))


design = mots((ICI / "DESIGN.md").read_text(encoding="utf-8"))
for f in sys.argv[1:]:
    communs = sorted(design & mots(Path(f).read_text(encoding="utf-8")))
    print(f, len(communs), communs)
