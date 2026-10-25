"""Tableaux Markdown de T3 et de T6 depuis `donnees/runs.jsonl` (voir agreger.py pour les définitions).

Usage :
  uv run --no-project python -I rapport.py t3
  uv run --no-project python -I rapport.py t6 --cond a      # condition retenue en T3
"""

import argparse
import statistics as st
import sys
from collections import defaultdict

import agreger as ag


def sel(groupe: str, cond: str | None = None):  # type: ignore[no-untyped-def]
    return lambda r: r["groupe"] == groupe and (cond is None or r["cond"] == cond)


def ligne_apparie(titre: str, runs: list[dict], a, b) -> str:  # type: ignore[no-untyped-def]
    e = ag.ecarts_apparies(runs, a, b)
    rel = []
    ra = {(r["story"], r["rep"]): r for r in runs if a(r)}
    rb = {(r["story"], r["rep"]): r for r in runs if b(r)}
    for k in sorted(set(ra) & set(rb)):
        rel.append((rb[k]["cout_usd"] - ra[k]["cout_usd"]) / ra[k]["cout_usd"])
    lo, hi = ag.bootstrap_ic(rel)
    return (
        f"| {titre} | {e['couples']} | {ag.f(e['delta_cout_agrege'] * 100, 1)} % | {ag.f(e['delta_cout_relatif_moyen'] * 100, 1)} % "
        f"[{ag.f(lo * 100, 0)} ; {ag.f(hi * 100, 0)}] | {ag.f(e['delta_cout_relatif_median'] * 100, 1)} % | "
        f"{e['moins_cher_dans']}/{e['couples']} | {ag.f(e['delta_taux_moyen'] * 100, 1)} pt (+{e['meilleur_taux_dans']} / -{e['pire_taux_dans']}) |"
    )


ENTETE_APPARIE = (
    "| Comparaison (B contre A) | Couples | Écart de coût agrégé | Écart relatif moyen [IC 95 % bootstrap] | Médian | B moins cher | Écart de taux moyen |\n"
    "|---|---|---|---|---|---|---|"
)


def cv_cellules(runs: list[dict], s) -> str:  # type: ignore[no-untyped-def]
    cell = defaultdict(list)
    for r in runs:
        if s(r):
            cell[r["story"]].append(r["cout_usd"])
    cvs = [ag.sd(v) / ag.moy(v) for v in cell.values() if len(v) > 1]
    return ag.f(ag.moy(cvs) * 100, 0) + " %"


def contexte(runs: list[dict], s) -> str:  # type: ignore[no-untyped-def]
    xs = [r["transcription"].get("ctx_premier", 0) for r in runs if s(r)]
    return ag.f(ag.moy(xs) / 1000, 1) + " k"


def par_run(runs: list[dict], groupes: list[str]) -> str:
    lignes = [
        "| Run | Coût | Tours | Durée (s) | Tests cachés | Suite KO | ruff (erreurs / fichiers à reformater) | Refus de permission |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in sorted(runs, key=lambda r: (r["story"], r["groupe"], r["cond"], r["rep"])):
        if r["groupe"] in groupes:
            lignes.append(
                f"| {r['id']} | {ag.f(r['cout_usd'], 3)} $ | {r['tours']} | {ag.f(r['duree_mur_s'], 0)} | "
                f"{r['cache']['passed']}/{r['total_ref']} | {r['suite_ko']} | {r['ruff_erreurs']} / {r['ruff_format_fichiers']} | {r['refus_permission']} |"
            )
    return "\n".join(lignes)


def t3(runs: list[dict]) -> None:
    runs = [r for r in runs if r["groupe"] == "Sonnet"]
    print("### Global par condition\n")
    print(ag.tableau_global(runs, [("(a) CLAUDE.md actuel", sel("Sonnet", "a")), ("(b) CLAUDE.md minimal", sel("Sonnet", "b"))], "Condition"))
    print("\n### Par story (moyenne ; entre parenthèses, coût et % de réussite de chaque répétition)\n")
    print(ag.tableau_story(runs, [("(a)", sel("Sonnet", "a")), ("(b)", sel("Sonnet", "b"))]))
    print("\n### Comparaison appariée\n")
    print(ENTETE_APPARIE)
    print(ligne_apparie("(b) minimal contre (a) actuel", runs, sel("Sonnet", "a"), sel("Sonnet", "b")))
    print("\n### Variance et contexte\n")
    print(f"- Coefficient de variation du coût entre répétitions d'une même cellule (moyenne sur les stories) : (a) {cv_cellules(runs, sel('Sonnet', 'a'))}, (b) {cv_cellules(runs, sel('Sonnet', 'b'))}.")
    print(f"- Contexte du premier appel de l'API : (a) {contexte(runs, sel('Sonnet', 'a'))}, (b) {contexte(runs, sel('Sonnet', 'b'))}.")
    for cond in ("a", "b"):
        g = [r for r in runs if r["cond"] == cond]
        tests = ag.moy([r["diff"]["tests_ecrits"] for r in g])
        print(f"- ({cond}) refus de permission moyens : {ag.f(ag.moy([r['refus_permission'] for r in g]), 1)} ; lignes ajoutées : {ag.f(ag.moy([r['diff']['ajoutes'] for r in g]), 0)} ; fichiers de tests écrits : {ag.f(tests, 1)}.")
    print("\n### Détail par run\n")
    print(par_run(runs, ["Sonnet"]))


def t6(runs: list[dict], cond: str) -> None:
    runs = [r for r in runs if r["cond"] == cond]
    SO, SOC = "Sonnet+Opus", "Sonnet+Opus (consigne)"
    gs = ["Sonnet", SO, SOC, "Opus"]
    print("### Global par bras (condition CLAUDE.md :", cond, ")\n")
    print(ag.tableau_global(runs, [("(a) Sonnet seul, 5 répétitions", sel("Sonnet")), ("(a) Sonnet seul, répétitions 1 à 3 (appariées)", lambda x: x["groupe"] == "Sonnet" and x["rep"] <= 3), ("(b) Sonnet + conseiller Opus, prompt du protocole", sel(SO)), ("(b') Sonnet + conseiller Opus, consigne de consulter", sel(SOC)), ("(c) Opus seul", sel("Opus"))], "Bras"))
    print("\n### Par story\n")
    print(ag.tableau_story(runs, [("(a) Sonnet", sel("Sonnet")), ("(b) Sonnet+Opus", sel(SO)), ("(b') avec consigne", sel(SOC)), ("(c) Opus", sel("Opus"))]))
    print("\n### Comparaisons appariées (même story, même répétition)\n")
    print(ENTETE_APPARIE)
    print(ligne_apparie("(b) conseiller (prompt du protocole) contre (c) Opus seul", runs, sel("Opus"), sel(SO)))
    print(ligne_apparie("(b) conseiller (prompt du protocole) contre (a) Sonnet seul", runs, sel("Sonnet"), sel(SO)))
    print(ligne_apparie("(b') conseiller avec consigne contre (c) Opus seul", runs, sel("Opus"), sel(SOC)))
    print(ligne_apparie("(b') conseiller avec consigne contre (a) Sonnet seul", runs, sel("Sonnet"), sel(SOC)))
    print(ligne_apparie("(c) Opus seul contre (a) Sonnet seul", runs, sel("Sonnet"), sel("Opus")))
    print("\n### Conseiller\n")
    for nom, b in (("(b) prompt du protocole", [r for r in runs if r["groupe"] == SO]), ("(b') avec consigne", [r for r in runs if r["groupe"] == SOC])):
        if not b:
            continue
        part = [r["cout_conseiller"] / r["cout_usd"] for r in b]
        appels = [r["appels_conseiller"] for r in b]
        print(f"- {nom} : part du coût due au conseiller {ag.f(ag.moy(part) * 100, 0)} % en moyenne (min {ag.f(min(part) * 100, 0)} %, max {ag.f(max(part) * 100, 0)} %) ; coût moyen du conseiller {ag.f(ag.moy([r['cout_conseiller'] for r in b]), 3)} $ ; appels par run : moyenne {ag.f(ag.moy(appels), 1)} (min {min(appels)}, max {max(appels)}) ; runs sans aucun appel : {sum(1 for x in appels if x == 0)}/{len(b)}.")
    print(f"- Coefficient de variation du coût (moyenne sur les stories) : (a) {cv_cellules(runs, sel('Sonnet'))}, (b) {cv_cellules(runs, sel(SO))}, (b') {cv_cellules(runs, sel(SOC))}, (c) {cv_cellules(runs, sel('Opus'))}.")
    print("\n### Détail par run\n")
    print(par_run(runs, gs))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["t3", "t6"])
    p.add_argument("--cond", default="a")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    runs = ag.charger()
    t3(runs) if a.mode == "t3" else t6(runs, a.cond)
    return 0


if __name__ == "__main__":
    sys.exit(main())
