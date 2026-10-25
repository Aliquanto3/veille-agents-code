r"""T5 elargi, etape 3 : seme 1 defaut par story (survivant cosmic-ray tire au sort, ou mutant ecrit a la main) et produit
  T:\rev\<id>\            arbre seme, copie vue par les relecteurs Claude (sans _bmad, sans docs, sans fichiers de mutation)
  T:\sem\<id>\diff.patch  diff envoye a tous les relecteurs (diff Python de la story, ligne semee modifiee)
  T:\sem\<id>\verite.json verite terrain, jamais montree aux relecteurs
usage : semer.py <id> [--indice N]        tirage au sort (graine fixe) parmi les survivants admissibles, ou l'indice donne
        semer.py <id> --lister            liste les survivants admissibles
        semer.py <id> --manuel fichier ligne "ancien" "nouveau" nature description
        semer.py <id> --temoin            copie sans defaut, diff d'origine
"""
from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import sys
from pathlib import Path

T = Path("T:/")
GRAINE = 20261024
EXCLUS_COPIE = ("_bmad", "_bmad-output", ".claude", ".venv", "__pycache__", ".pytest_cache", ".git", "docs", "node_modules", "CLAUDE.md", "AGENTS.md")
NATURE = {
    "AddNot": ("condition inversee", "une condition est niee"),
    "ReplaceComparisonOperator_Eq_NotEq": ("condition inversee", "== devient !="),
    "ReplaceComparisonOperator_NotEq_Eq": ("condition inversee", "!= devient =="),
    "ReplaceUnaryOperator_Delete_Not": ("condition inversee", "un 'not' est supprime"),
    "ReplaceOrWithAnd": ("condition modifiee", "'or' devient 'and'"),
    "ReplaceAndWithOr": ("condition modifiee", "'and' devient 'or'"),
    "ReplaceContinueWithBreak": ("branche modifiee", "'continue' devient 'break'"),
    "NumberReplacer": ("borne ou valeur changee", "une constante numerique est decalee"),
}


# classes de defauts realistes retenues (consigne : condition inversee, borne decalee, branche supprimee, valeur par defaut, exception avalee)
OPERATEURS_REALISTES = re.compile(
    r"^(AddNot|ReplaceUnaryOperator_Delete_Not|ReplaceOrWithAnd|ReplaceAndWithOr|ReplaceContinueWithBreak|ReplaceBreakWithContinue|"
    r"ReplaceTrueWithFalse|ReplaceFalseWithTrue|ZeroIterationForLoop|NumberReplacer|ReplaceBinaryOperator_(Add_Sub|Sub_Add)|"
    r"ReplaceComparisonOperator_(Eq|NotEq|Lt|LtE|Gt|GtE)_(Eq|NotEq|Lt|LtE|Gt|GtE))$")


def nature_de(op: str) -> tuple[str, str]:
    cle = op.split("/")[-1]
    if cle in NATURE:
        return NATURE[cle]
    if re.search(r"ReplaceComparisonOperator_\w+_(Lt|LtE|Gt|GtE)$", cle) or re.search(r"ReplaceComparisonOperator_(Lt|LtE|Gt|GtE)_\w+", cle):
        return "borne decalee", "un operateur de comparaison d'ordre est change (< <= > >=)"
    if cle.startswith("ReplaceComparisonOperator"):
        return "condition modifiee", "un operateur de comparaison est change"
    if cle.startswith("ReplaceBinaryOperator"):
        return "calcul modifie", "un operateur arithmetique est change"
    if cle in ("ReplaceFalseWithTrue", "ReplaceTrueWithFalse"):
        return "valeur par defaut ou de retour changee", "un booleen litteral est inverse"
    if cle == "ZeroIterationForLoop":
        return "branche supprimee", "le corps d'une boucle n'est plus execute"
    if cle.startswith("ReplaceTrueFalse"):
        return "valeur par defaut changee", "True et False echanges"
    return "autre", cle


def lignes_diff(d: dict) -> tuple[list[str], list[str]]:
    moins = [l[1:] for l in d["diff"].splitlines() if l.startswith("-") and not l.startswith("---")]
    plus = [l[1:] for l in d["diff"].splitlines() if l.startswith("+") and not l.startswith("+++")]
    return moins, plus


def normaliser(ancien: str, nouveau: str) -> str:
    """cosmic-ray laisse des espaces parasites ('= 2', 'if  x') qui trahiraient la mutation : on les retire."""
    p = 0
    while p < min(len(ancien), len(nouveau)) and ancien[p] == nouveau[p]:
        p += 1
    s = 0
    while s < min(len(ancien), len(nouveau)) - p and ancien[len(ancien) - 1 - s] == nouveau[len(nouveau) - 1 - s]:
        s += 1
    ins = nouveau[p:len(nouveau) - s]
    rem = ancien[p:len(ancien) - s]
    if ins.startswith(" ") and not rem.startswith(" "):
        nouveau = nouveau[:p] + ins.lstrip(" ") + nouveau[len(nouveau) - s:]
    if "  " not in ancien.strip():
        nouveau = re.sub(r"(?<=\S)  +(?=\S)", " ", nouveau)
    return nouveau


def admissibles(surv: list[dict], arbre: Path) -> list[dict]:
    out, vus = [], set()
    for s in surv:
        moins, plus = lignes_diff(s)
        if len(moins) != 1 or len(plus) != 1:
            continue
        cle = s["operateur"].split("/")[-1]
        if not OPERATEURS_REALISTES.match(cle) or "CosmicRay" in plus[0]:
            continue
        if (s["module"], s["ligne"]) in vus:
            continue
        vus.add((s["module"], s["ligne"]))
        lignes = (arbre / s["module"]).read_text(encoding="utf-8").splitlines()
        if lignes[s["ligne"] - 1].strip() != moins[0].strip():
            continue
        out.append(s)
    return out


def copier_arbre(sid: str) -> Path:
    arbre = T / "src" / sid
    cible = T / "rev" / sid
    if cible.exists():
        shutil.rmtree(cible, ignore_errors=True)
    shutil.copytree(arbre, cible, ignore=lambda d, noms: [n for n in noms if n in EXCLUS_COPIE or n.startswith("cr-") or n.endswith((".sqlite", ".pyc"))])
    return cible


def ecrire_defaut(sid: str, module: str, ligne: int, ancien: str, nouveau: str, meta: dict) -> None:
    arbre = T / "src" / sid
    source = (arbre / module).read_text(encoding="utf-8").split("\n")
    assert source[ligne - 1].strip().rstrip("\r") == ancien.strip(), (source[ligne - 1], ancien)
    indent = source[ligne - 1][: len(source[ligne - 1]) - len(source[ligne - 1].lstrip())]
    source[ligne - 1] = indent + nouveau.strip()
    cible = copier_arbre(sid)
    (cible / module).write_text("\n".join(source), encoding="utf-8")
    diff = (T / "jeu" / sid / "diff_orig.patch").read_text(encoding="utf-8").split("\n")
    out, fichier, nl, fait = [], None, 0, False
    for l in diff:
        m = re.match(r"^\+\+\+ b/(.*)$", l)
        if m:
            fichier = m.group(1)
        h = re.match(r"^@@ -\S+ \+(\d+)", l)
        if h:
            nl = int(h.group(1))
            out.append(l)
            continue
        if fichier == module and l.startswith("+") and not l.startswith("+++"):
            if nl == ligne:
                assert l[1:].strip() == ancien.strip(), (l, ancien)
                l = "+" + indent + nouveau.strip()
                fait = True
            nl += 1
        elif fichier == module and l.startswith(" "):
            nl += 1
        out.append(l)
    assert fait, "ligne semee absente du diff"
    sem = T / "sem" / sid
    sem.mkdir(parents=True, exist_ok=True)
    (sem / "diff.patch").write_text("\n".join(out), encoding="utf-8")
    verite = dict(id=sid, fichier=module, ligne=ligne, ancien=ancien.strip(), nouveau=nouveau.strip(), **meta)
    (sem / "verite.json").write_text(json.dumps(verite, ensure_ascii=False, indent=1), encoding="utf-8")
    print(sid, module, ligne, "|", ancien.strip(), "=>", nouveau.strip(), "|", meta.get("nature"))


def temoin(sid: str) -> None:
    copier_arbre(sid)
    sem = T / "sem" / sid
    sem.mkdir(parents=True, exist_ok=True)
    shutil.copy(T / "jeu" / sid / "diff_orig.patch", sem / "diff.patch")
    (sem / "verite.json").write_text(json.dumps({"id": sid, "temoin": True}, indent=1), encoding="utf-8")
    print(sid, "temoin")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("sid")
    ap.add_argument("--indice", type=int, default=None)
    ap.add_argument("--temoin", action="store_true")
    ap.add_argument("--lister", action="store_true")
    ap.add_argument("--manuel", nargs=6, metavar=("FICHIER", "LIGNE", "ANCIEN", "NOUVEAU", "NATURE", "DESCRIPTION"))
    a = ap.parse_args()
    if a.temoin:
        return temoin(a.sid)
    if a.manuel:
        f, ln, anc, nouv, nat, desc = a.manuel
        return ecrire_defaut(a.sid, f, int(ln), anc, nouv, dict(nature=nat, explication=desc, origine="mutant manuel"))
    surv = json.loads((T / "mut" / a.sid / "survivants.json").read_text(encoding="utf-8")).get("survivants", [])
    adm = admissibles(surv, T / "src" / a.sid)
    adm.sort(key=lambda s: (s["module"], s["ligne"], s["operateur"]))
    if a.lister:
        for i, s in enumerate(adm):
            print(i, s["module"].split("/")[-1], s["ligne"], s["operateur"].split("/")[-1], [l[1:].strip() for l in s["diff"].splitlines() if l[:1] in "+-" and not l.startswith(("---", "+++"))])
        return
    if not adm:
        sys.exit(f"{a.sid} : aucun survivant admissible (survivants bruts : {len(surv)}), semer a la main")
    i = a.indice if a.indice is not None else random.Random(f"{GRAINE}-{a.sid}").randrange(len(adm))
    s = adm[i]
    moins, plus = lignes_diff(s)
    nouveau = normaliser(moins[0], plus[0])
    nat, expl = nature_de(s["operateur"])
    ecrire_defaut(a.sid, s["module"], s["ligne"], moins[0], nouveau, dict(
        nature=nat, explication=expl, operateur=s["operateur"], fonction=s["fonction"], origine="survivant cosmic-ray",
        survivants_admissibles=len(adm), indice=i))


if __name__ == "__main__":
    main()
