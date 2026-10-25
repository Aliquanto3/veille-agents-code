"""T10b : rejoue les mutants hors liste (holdout.json) contre les tests produits par un agent (bras A ou C de T10/T10b).
usage : evaluer_holdout.py <story> <A|C> <essai>  ; arbre de controle = arbre(story, "C", 3) (code de la story, sans test d'agent)."""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

from evaluer import pytest
from jeu import BRUTS, STORIES, arbre
from mutation import applique
from preparer import preparer

ICI = Path(__file__).parent
T10 = ICI / "resultats-bruts"
T10B = T10 / "T10b"


def main():
    story, bras, essai = sys.argv[1], sys.argv[2], int(sys.argv[3])
    a = preparer(story, "C", 3)
    src = (T10 if bras == "A" else T10B) / "tests-produits" / f"{story}-{bras}{essai}"
    fichiers = sorted(p for p in src.rglob("*.py") if ".hypothesis" not in str(p))
    rel = []
    for p in fichiers:
        r = p.relative_to(src)
        (a / r).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, a / r)
        rel.append(r.as_posix())
    hold = json.loads((T10B / "holdout.json").read_text(encoding="utf-8"))[story]
    res = {"story": story, "bras": bras, "essai": essai, "fichiers": rel, "mutants": []}
    try:
        rc, out, dur = pytest(story, "C", 3, ["-q", "--tb=no", *rel], 900)
        res["base"] = {"rc": rc, "fin": (out.strip().splitlines() or [""])[-1][:120], "secondes": dur}
        for h in hold:
            chemin = a / h["module"]
            for pyc in chemin.parent.glob("__pycache__"):
                shutil.rmtree(pyc, ignore_errors=True)
            try:
                with applique(chemin, h):
                    rc, out, dur = pytest(story, "C", 3, ["-x", "--tb=no", *rel], 180)
            except Exception as e:
                res["mutants"].append({"id": h["id"], "etat": "erreur", "detail": repr(e)[:150]})
                continue
            res["mutants"].append({"id": h["id"], "cible": h["cible"], "etat": "survit" if rc in (0, 5) else "tue", "rc": rc, "secondes": dur})
    finally:
        for r in rel:
            (a / r).unlink(missing_ok=True)
    res["tues"] = sum(1 for m in res["mutants"] if m["etat"] == "tue")
    res["erreurs"] = sum(1 for m in res["mutants"] if m["etat"] == "erreur")
    (T10B / f"holdout-{story}-{bras}{essai}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(story, bras, essai, "tues", res["tues"], "/", len(hold), "base", res["base"]["rc"], "erreurs", res["erreurs"])


if __name__ == "__main__":
    main()
