"""Tableau du volet 2 (stdout)."""
import json
from pathlib import Path
ICI = Path(__file__).resolve().parent.parent
rows = [json.loads(l) for l in (ICI / "donnees" / "v2_runs.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
print("| Cellule | Dév. | Dév. : coût A ($) | durée (min) | tours | Critères tenus A | Tests cachés A | Vérificateur ($) | Correction ($) | Critères tenus B | Tests cachés B | Coût B mesuré ($) | Coût B sans correction à vide ($) |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
tot = 0
for r in rows:
    A, B = r["A"], r["B"]
    vf = r["verif"].get("cout_usd") or 0
    tot += r["cout_B"]
    print(f"| {r['id']} | {r.get('modele_dev', 'claude-sonnet-5-5').replace('claude-', '')} | {r['cout_A']:.2f} | {r['dev']['duree_mur_s']/60:.1f} | {r['dev']['tours']} | {A['criteres_tenus']}/{A['criteres_total']} | {A['caches_passes']}/{A['caches_total']} | {vf:.2f} | {r['correction']['cout_usd']:.2f} | {B['criteres_tenus']}/{B['criteres_total']} | {B['caches_passes']}/{B['caches_total']} | {r['cout_B']:.2f} | {r['cout_A'] + vf:.2f} |")
print("\ncoût total du volet 2 : %.2f $" % tot)
