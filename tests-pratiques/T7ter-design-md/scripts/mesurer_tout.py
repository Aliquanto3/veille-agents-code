"""Mesure, un rendu à la fois (un seul navigateur), tous les bras terminés qui n'ont pas encore de mesures.json.

Usage (depuis le projet de mesure) : uv run --offline --frozen python mesurer_tout.py [rendu ...]
"""
import json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from chemins import ARMS, BRAS, ECRANS, ESSAIS, MESURES, nom
import mesure_page


def main(noms):
    cibles = noms or [nom(b, e, r) for e in ECRANS for r in ESSAIS for b in BRAS]
    port = 8810
    for n in cibles:
        d = ARMS / n
        if not (d / "_claude.meta.json").exists():
            print("pas fini", n); continue
        if (MESURES / n / "mesures.json").exists():
            print("déjà mesuré", n); continue
        ecran = json.loads((d / "_arm.json").read_text(encoding="utf-8"))["ecran"]
        o = mesure_page.main(n, ecran, port, MESURES / n)
        port += 1
        c = (o.get("conformite") or {}).get("score")
        print(n, "fonc", (o.get("fonctionnel") or {}).get("_reussis"), "/", (o.get("fonctionnel") or {}).get("_total"),
              "axe", (o.get("axe") or {}).get("noeuds_total"), "detect", (o.get("impeccable_detect") or {}).get("n"), "conf", c, flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
