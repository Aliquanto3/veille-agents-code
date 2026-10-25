"""T10 : construit la liste des survivants cibles (dedoublonnes par ligne) depuis les JSON de T4.

Sortie : cibles.json = {story: {"cibles": [...], "retraits": [...]}}.
Une cible par ligne : on garde la variante la plus parlante (inversion, constante, exception, saut),
les variantes de comparaison redondantes sont ecartees. Les lignes dont toutes les variantes sont
equivalentes (identite contre egalite sur chaines ou enums, borne atteinte par construction) sont retirees.
"""
from __future__ import annotations

import json
from pathlib import Path

ICI = Path(__file__).parent
T4 = ICI.parent / "T4" / "resultats-bruts"
STORIES = ["wd-5-9", "wd-8-4", "us-7-14", "us-7-15", "us-7-16"]

# (story, fichier, ligne) -> motif de retrait (mutant equivalent ou artefact)
RETRAITS = {
    ("wd-5-9", "loader.py", 254): "signature : `*,` devenu `/,` (marqueur d'arguments nommes, artefact d'operateur)",
    ("wd-8-4", "findings.py", 364): "`line == previous + 1` -> `<=` : equivalent, les lignes sont triees et uniques (`sorted(set(lines))`)",
    ("us-7-14", "carte.py", 339): "`is` -> `==` sur un StrEnum : equivalent",
    ("us-7-14", "detail.py", 455): "`is not Couleur.rouge` -> `<` : equivalent, `rouge` est la plus grande valeur de la chaine (StrEnum)",
    ("us-7-14", "detail.py", 486): "`is Couleur.rouge` -> `==` ou `>=` : equivalents (StrEnum, `rouge` maximum)",
    ("us-7-14", "detail.py", 504): "`is StatutControle.rejete` -> `==` ou `>=` : equivalents (StrEnum, `rejete` maximum)",
    ("us-7-14", "detail.py", 538): "`palier == 1` -> `<= 1` : equivalent, palier vaut 1 ou 2",
    ("us-7-14", "detail.py", 555): "`palier == 2` -> `>= 2` : equivalent, palier vaut 1 ou 2",
    ("us-7-14", "detail.py", 556): "`palier == 1` -> `<= 1` : equivalent, palier vaut 1 ou 2",
    ("us-7-14", "detail.py", 607): "`palier == 2` -> `>= 2` : equivalent, palier vaut 1 ou 2",
    ("us-7-14", "detail.py", 608): "`palier_demande == 1` -> `<= 1` : equivalent sur le domaine {1, 2}",
    ("us-7-14", "detail.py", 615): "`palier == 1` -> `<= 1` : equivalent, palier vaut 1 ou 2",
    ("us-7-14", "serveur.py", 122): "`else 2` -> `else 3` : equivalent, `vue_detail` traite 3 comme 2 (`palier_demande == 1 else 2`)",
    ("us-7-14", "serveur.py", 145): "`nom == 'rapport_xlsx'` -> `>=` : equivalent sur les deux noms valides ('rapport_pptx' < 'rapport_xlsx')",
    ("us-7-15", "chaine.py", 193): "`==` -> `is` sur une chaine : equivalent (chaines internees)",
    ("us-7-15", "chaine.py", 254): "`statut == 'terminee'` -> `is` ou `>=` : equivalents (chaine internee, valeur maximale)",
    ("us-7-15", "chaine.py", 256): "`==` -> `is` sur une chaine : equivalent",
    ("us-7-15", "chaine.py", 258): "`statut == 'attente'` -> `is` ou `<=` : equivalents (valeur minimale)",
    ("us-7-15", "serveur.py", 150): "`mode == 'repli'` -> `>=` ou `is` : equivalents sur {'repli', 'reel'}",
    ("us-7-16", "ecrans.py", 142): "`is StatutControle.rejete` -> `==` ou `>=` : equivalents (StrEnum, `rejete` maximum)",
    ("us-7-16", "ecrans.py", 285): "`carte is manuel` -> `==` : equivalent, les deux cartes ont des contenus differents",
}

# variante imposee (suffixe de l'operateur) quand la regle de priorite ne convient pas
VARIANTE = {
    ("us-7-16", "outillage.py", 89): ("Eq_LtE", 'jeton.type <= "heading_open"'),  # `heading_close` <= `heading_open` : le cas utile ; `tag <= "h1"` serait equivalent
    ("us-7-15", "chaine.py", 271): ("Is_LtE", ""),    # `is` -> `==` serait equivalent
}

EQUIV_OPS = {"Eq_Is", "Is_Eq", "IsNot_NotEq", "NotEq_IsNot"}


def priorite(op: str) -> int:
    nom = op.split("/")[-1].replace("ReplaceComparisonOperator_", "")
    if nom in EQUIV_OPS:
        return 9
    if nom.startswith(("Eq_Is", "Is_IsNot", "IsNot_Is")):
        return 1
    if "_" in nom and nom.split("_")[0] in ("Eq", "NotEq", "Lt", "Gt", "LtE", "GtE", "Is", "IsNot") \
            and nom.split("_")[1] in ("Eq", "NotEq", "Lt", "Gt", "LtE", "GtE", "Is", "IsNot"):
        return 2 if nom.endswith(("GtE", "LtE")) else 1
    return 0


def construire() -> dict:
    sortie = {}
    for story in STORIES:
        d = json.loads((T4 / f"{story}.json").read_text(encoding="utf-8"))
        cibles, retraits = [], []
        for m in d["modules"]:
            fichier = m["module"].split("/")[-1]
            par_ligne: dict[int, list] = {}
            for s in m["survivors"]:
                par_ligne.setdefault(s["line"], []).append(s)
            for ligne, xs in par_ligne.items():
                cle = (story, fichier, ligne)
                if cle in RETRAITS:
                    retraits.append({"module": m["module"], "ligne": ligne, "variantes": len(xs),
                                     "motif": RETRAITS[cle]})
                    continue
                if cle in VARIANTE:
                    suf, sub = VARIANTE[cle]
                    choisi = next(x for x in xs if x["operator"].endswith(suf) and sub in x["diff"])
                else:
                    choisi = min(xs, key=lambda x: priorite(x["operator"]))
                    if priorite(choisi["operator"]) == 9:
                        retraits.append({"module": m["module"], "ligne": ligne, "variantes": len(xs),
                                         "motif": "toutes les variantes sont des equivalents identite/egalite"})
                        continue
                diff = choisi["diff"].split("\n")
                cibles.append({
                    "id": f"{story}:{fichier}:{ligne}",
                    "module": m["module"], "ligne": ligne, "operateur": choisi["operator"],
                    "fonction": choisi["function"], "variantes_ligne": len(xs),
                    "moins": [l[1:] for l in diff if l.startswith("-")],
                    "plus": [l[1:] for l in diff if l.startswith("+")],
                })
        sortie[story] = {"cibles": cibles, "retraits": retraits,
                         "survivants_t4": sum(m["survived"] for m in d["modules"]),
                         "lignes_t4": sum(len({s["line"] for s in m["survivors"]}) for m in d["modules"])}
    return sortie


if __name__ == "__main__":
    res = construire()
    (ICI / "cibles.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    tot = 0
    for s, v in res.items():
        tot += len(v["cibles"])
        print(s, "survivants", v["survivants_t4"], "lignes", v["lignes_t4"], "cibles", len(v["cibles"]), "retraits", len(v["retraits"]))
    print("total cibles", tot)
