"""Somme des coûts déjà engagés (cadrages, développements, pilote)."""
import json
from pathlib import Path
ICI = Path(__file__).resolve().parent
tot = {}
for nom in ("cadrages.jsonl", "runs.jsonl", "pilote/cadrages-pilote.jsonl"):
    p = ICI / "donnees" / nom
    if p.exists():
        for l in p.read_text(encoding="utf-8").splitlines():
            if l:
                r = json.loads(l)
                tot[nom] = tot.get(nom, 0) + (r.get("cout_usd") or 0)
print({k: round(v, 2) for k, v in tot.items()}, "total", round(sum(tot.values()), 2))
