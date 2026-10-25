"""T10b (extension) : cibles.json + une variante par ligne retiree (equivalents supposes et artefacts), comme un rapport brut dedoublonne.
Sortie : resultats-bruts/T10b/ext/cibles-ext.json (stories passees en argument)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from cibles import T4, priorite

ICI = Path(__file__).parent
base = json.loads((ICI / "cibles.json").read_text(encoding="utf-8"))
sortie = {}
for story in sys.argv[1:]:
    d = json.loads((T4 / f"{story}.json").read_text(encoding="utf-8"))
    ordre = {m["module"]: i for i, m in enumerate(d["modules"])}
    retires = {(r["module"], r["ligne"]): r["motif"] for r in base[story]["retraits"]}
    ajouts = []
    for m in d["modules"]:
        par_ligne: dict[int, list] = {}
        for s in m["survivors"]:
            par_ligne.setdefault(s["line"], []).append(s)
        for ligne, xs in par_ligne.items():
            if (m["module"], ligne) not in retires:
                continue
            ch = min(xs, key=lambda x: priorite(x["operator"]))
            diff = ch["diff"].split("\n")
            ajouts.append({"id": f"{story}:{m['module'].split('/')[-1]}:{ligne}", "module": m["module"], "ligne": ligne,
                           "operateur": ch["operator"], "fonction": ch["function"], "variantes_ligne": len(xs),
                           "moins": [l[1:] for l in diff if l.startswith("-")], "plus": [l[1:] for l in diff if l.startswith("+")],
                           "retire_motif": retires[(m["module"], ligne)]})
    toutes = base[story]["cibles"] + ajouts
    toutes.sort(key=lambda c: (ordre[c["module"]], c["ligne"]))
    sortie[story] = {"cibles": toutes, "ajouts": [a["id"] for a in ajouts]}
    print(story, len(base[story]["cibles"]), "+", len(ajouts), "=", len(toutes))
out = ICI / "resultats-bruts" / "T10b" / "ext"
out.mkdir(exist_ok=True)
(out / "cibles-ext.json").write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
