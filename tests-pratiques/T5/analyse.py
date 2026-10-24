"""T5 : agrege les mesures par modele et par passe (constats, tests, classes, cout, latence) vers analyse.json.

Entrees : reponses/ (passe r1 officielle, 4 modeles), reponses_run2/ (r2, repetition luna et sol), execution.json (tests sur l'etat
fusionne), execution_tete.json (memes tests sur la tete de main), classification.json (classement manuel des Important),
exploratoire_v0.json (premiere passe abandonnee, hors tableaux).
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from executer_tests import DOSSIERS, charger_constats, cle_test

ICI = Path(__file__).parent
MODELES = ["openai/gpt-6-luna", "xiaomi/mimo-v2.6-pro", "openai/gpt-6.1-sol", "moonshotai/kimi-k3.1-pro"]
ECHEC = ("echoue_assertion", "echoue_exception")


def lire(nom: str) -> dict:
    f = ICI / nom
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def main() -> None:
    execution, tete, classif = lire("execution.json"), lire("execution_tete.json"), lire("classification.json")
    constats = charger_constats()
    sortie: dict = {}
    for dossier, run in DOSSIERS:
        reponses = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((ICI / dossier).glob("*.json"))] if (ICI / dossier).exists() else []
        for m in MODELES:
            rs = [r for r in reponses if r["modele"] == m]
            if not rs:
                continue
            cs = [c for c in constats if c["modele"] == m and c["run"] == run]
            imp = [c for c in cs if c.get("severite") == "Important"]
            classes = Counter(classif.get(cle_test(c), {}).get("classe", "non_classe") for c in imp)
            etats = Counter(execution.get(cle_test(c), {}).get("etat", "sans_test" if not c.get("test") else "non_execute") for c in imp)
            vides = [r["story"] for r in rs if not r["contenu"].strip()]
            tronques = [r["story"] for r in rs if r["finish_reason"] == "length" and r["contenu"].strip()]
            retrouves = sorted({f"{c['story']}:{classif[cle_test(c)]['defaut']}" for c in imp if classif.get(cle_test(c), {}).get("defaut")})
            sortie[f"{m}|{run}"] = {
                "reponses": len(rs), "reponses_vides": len(vides), "reponses_tronquees_salvees": len(tronques),
                "stories_vides": sorted(vides), "stories_tronquees": sorted(tronques),
                "cout_usd": round(sum(r["cout_usd"] for r in rs), 3),
                "latence_totale_s": round(sum(r["latence_s"] for r in rs)), "latence_moyenne_s": round(sum(r["latence_s"] for r in rs) / len(rs)),
                "jetons_entree": sum(r["usage"].get("prompt_tokens", 0) for r in rs), "jetons_sortie": sum(r["usage"].get("completion_tokens", 0) for r in rs),
                "reprises_effort_bas": sum(1 for r in rs if len(r.get("tentatives", [])) > 1),
                "important": len(imp), "nit": sum(1 for c in cs if c.get("severite") == "Nit"),
                "classes": dict(classes), "tests": dict(etats),
                "porte_validee": sum(1 for c in imp if execution.get(cle_test(c), {}).get("etat") in ECHEC),
                "corriges_plus_tard_sur_main": [cle_test(c) for c in imp if tete.get(cle_test(c), {}).get("etat") == "passe"],
                "defauts_connus_retrouves": retrouves,
                "stories_avec_important": sorted({c["story"] for c in imp}),
            }
    exp = lire("exploratoire_v0.json")
    sortie["exploratoire_v0"] = exp
    (ICI / "analyse.json").write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in sortie.items():
        if k != "exploratoire_v0":
            print(k, json.dumps(v, ensure_ascii=False))


if __name__ == "__main__":
    main()
