"""T10b : mutants hors liste montrée a l'agent C : survivants de T4 sur les lignes cibles, hors variante montree et hors equivalents identite/egalite.
Sert a mesurer si les tests ecrits generalisent (variantes de la meme ligne non montrees). Sortie : resultats-bruts/T10b/holdout.json"""
from __future__ import annotations

import json
from pathlib import Path

from cibles import STORIES, T4, priorite

ICI = Path(__file__).parent
cibles = json.loads((ICI / "cibles.json").read_text(encoding="utf-8"))
sortie = {}
for story in STORIES:
    d = json.loads((T4 / f"{story}.json").read_text(encoding="utf-8"))
    lignes = {(c["module"], c["ligne"]): c for c in cibles[story]["cibles"]}
    hold = []
    for m in d["modules"]:
        for s in m["survivors"]:
            c = lignes.get((m["module"], s["line"]))
            if not c:
                continue
            diff = s["diff"].split("\n")
            moins = [l[1:] for l in diff if l.startswith("-")]
            plus = [l[1:] for l in diff if l.startswith("+")]
            if moins == c["moins"] and plus == c["plus"]:
                continue   # variante montree
            if priorite(s["operator"]) == 9:
                continue   # equivalent identite/egalite
            hold.append({"id": f"{story}:{m['module'].split('/')[-1]}:{s['line']}:{len(hold)}", "cible": c["id"], "module": m["module"],
                         "ligne": s["line"], "operateur": s["operator"], "moins": moins, "plus": plus})
    sortie[story] = hold
    print(story, len(hold))
print("total", sum(len(v) for v in sortie.values()))
(ICI / "resultats-bruts" / "T10b" / "holdout.json").write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
