r"""T5 elargi : applique la localisation de la grille (grille.md, conditions 1) et prepare la lecture a l'aveugle (condition 2).

usage : juger.py candidats  -> ecrit T:\candidats.json (constats localises, ordre melange, identifiant masque) et affiche le texte a lire
        juger.py appliquer  -> lit jugements.json (T5-elargi\jugements.json : {"c012": [1|0, "note"]}) et ecrit T:\detections.json
La graine du melange est fixe. Le relecteur n'apparait pas dans le texte a lire.
"""
from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

T = Path("T:/")
ICI = Path(__file__).resolve().parent
FENETRE = 5
SUF = os.environ.get("T5E_SUF", "")


def verites() -> dict:
    out = {}
    for d in sorted((T / "sem").iterdir()):
        v = json.loads((d / "verite.json").read_text(encoding="utf-8"))
        out[d.name] = v
    return out


def localise(c: dict, v: dict) -> bool:
    if v.get("temoin"):
        return False
    a0, b0 = v["ligne"] - FENETRE, v["ligne"] + FENETRE
    cible = v["fichier"]
    for f, a, b in c["refs"]:
        if (f == cible or cible.endswith("/" + f) or f.endswith("/" + cible) or cible.rsplit("/", 1)[-1] == f.rsplit("/", 1)[-1] and f == f.rsplit("/", 1)[-1]) and a <= b0 and b >= a0:
            return True
    return False


def candidats() -> None:
    V = verites()
    constats = json.loads((T / f"constats{SUF}.json").read_text(encoding="utf-8"))
    cand = [c for c in constats if localise(c, V[c["story"]])]
    rng = random.Random(20261024)
    rng.shuffle(cand)
    for i, c in enumerate(cand):
        c["cid"] = f"c{i:03d}"
    (T / f"candidats{SUF}.json").write_text(json.dumps(cand, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(cand), "candidats localises sur", len({c["story"] for c in cand}), "stories")
    for c in cand:
        v = V[c["story"]]
        print(f"\n=== {c['cid']} | story {c['story']} | defaut seme : {v['fichier']}:{v['ligne']} | `{v['ancien']}` devient `{v['nouveau']}` | nature : {v['nature']} ({v.get('explication', '')})")
        print(c["description"][:1200])


def appliquer() -> None:
    cand = {c["cid"]: c for c in json.loads((T / f"candidats{SUF}.json").read_text(encoding="utf-8"))}
    jug = json.loads((ICI / f"jugements{SUF}.json").read_text(encoding="utf-8"))
    manquants = [k for k in cand if k not in jug]
    if manquants:
        sys.exit(f"jugements manquants : {manquants}")
    det = []
    for k, c in cand.items():
        c = dict(c)
        c["detecte"] = bool(jug[k][0])
        c["note"] = jug[k][1]
        det.append(c)
    (T / f"detections{SUF}.json").write_text(json.dumps(det, ensure_ascii=False, indent=1), encoding="utf-8")
    print(sum(c["detecte"] for c in det), "detections sur", len(det), "candidats")


if __name__ == "__main__":
    {"candidats": candidats, "appliquer": appliquer}[sys.argv[1]]()
