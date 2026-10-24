"""Exploratoire : rejoue, sur l'etat fusionne et sur la tete de main, les tests Important de la premiere passe (diff concatene,
abandonnee) pour la story S1. Hors tableaux : sert a documenter la variabilite d'une passe a l'autre."""
import json
import sys

import executer_tests as ex

sys.stdout.reconfigure(encoding="utf-8")
stories = {s["id"]: s for s in json.loads((ex.ICI / "jeu" / "jeu.json").read_text(encoding="utf-8"))}
sortie = {}
for f in sorted((ex.ICI / "archive_v0_diff_concatene").glob("*.json")):
    if f.name.startswith("cout") or f.name.endswith(".bak"):
        continue
    r = json.loads(f.read_text(encoding="utf-8"))
    d = ex.extraire_json(r["contenu"])
    if not d:
        continue
    for k, c in enumerate(d["constats"]):
        if c.get("severite") != "Important" or not c.get("test_pytest"):
            continue
        cc = {"modele": r["modele"], "story": r["story"], "id": "v0_" + str(c.get("id") or k)}
        refus = ex.filtre_statique(c["test_pytest"])
        cle = ex.cle_test(cc)
        if refus:
            sortie[cle] = {"etat": "refuse", "raison": refus}
            continue
        (ex.EXTRAIT / f"{cle}.py").write_text(c["test_pytest"], encoding="utf-8")
        res = {"merge": ex.executer(cc, ex.worktree_pour(stories[r["story"]]), c["test_pytest"])["etat"],
               "tete": ex.executer(cc, ex.worktree_pour({"id": "TETE", "etat": ex.git("rev-parse", "HEAD").stdout.strip()}), c["test_pytest"])["etat"],
               "description": c.get("description", "")[:300]}
        sortie[cle] = res
        print(cle, res["merge"], res["tete"], flush=True)
(ex.ICI / "exploratoire_v0.json").write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
