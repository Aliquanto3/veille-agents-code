"""Tableau Markdown des défauts semés (sortie stdout)."""
import json
from agreger import *

res = json.loads((ICI / "donnees" / "volet1_resume.json").read_text(encoding="utf-8"))
v = res["versions"]
SCREEN = {"s713": "7.13", "s714": "7.14", "s715": "7.15", "s716": "7.16"}
print("| Id | Story | Classe | Défaut semé | pytest | Oracle scripté | Sous-agent | FAIL de l'agent | Coût ($) |")
print("|---|---|---|---|---|---|---|---|---|")
for i, d in DEFAUTS.items():
    x = v.get(i)
    if not x: continue
    pyt = "échoue" if x["pytest_voit"] else "passe"
    orc = "KO " + ",".join(k.split("_")[0] for k in x["ko_oracle"]) if x["ko_oracle"] else "aucun KO"
    det = "détecté" if x["detecte_agent"] else "manqué"
    print(f"| {i} | {SCREEN[d['story']]} | {d['classe']} | {d['description']} | {pyt} | {orc} | {det} | {','.join(x['fails_agent']) or '-'} | {x['cout']:.3f} |")
