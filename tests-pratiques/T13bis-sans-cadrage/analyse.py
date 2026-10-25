"""Analyse T13 bis : D (sans cadrage) contre A (cadrage BMAD complet), et D-court (Dc), selon le protocole figé.

Usage : uv run --no-project python -I analyse.py > donnees/analyse.md   (écrit aussi donnees/agregats.json)
Données : runs A et D de T13 (répétition 1, et l51-A2), lus sans modification dans `../T13-story-legere/donnees/`,
plus les runs de T13 bis (`donnees/runs.jsonl`, `donnees/cadrages.jsonl`). Unité du bootstrap : la story (taux et coûts
moyennés sur ses répétitions). 5 000 rééchantillonnages, graine 13. Écarts de taux en points (X − A), coûts en ratio agrégé.
"""

import json
import random
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
T13 = ICI.parent / "T13-story-legere" / "donnees"
MARGE, MARGE_SECONDAIRE = 10.0, 5.0
SEUIL_BREVE = 1200


def charger(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l] if p.exists() else []


runs_t13 = [r for r in charger(T13 / "runs.jsonl") if r["arm"] in ("A", "D")]
for r in runs_t13:
    r["source"] = "T13"
runs_bis = charger(ICI / "donnees" / "runs.jsonl")
for r in runs_bis:
    r["source"] = "T13bis"
devs = runs_t13 + runs_bis
cad = {c["id"]: c for c in charger(T13 / "cadrages.jsonl") + charger(ICI / "donnees" / "cadrages.jsonl")}


def richesse(story: str) -> str:
    return "brève" if len((ICI / "corpus" / story / "epics.md").read_text(encoding="utf-8")) < SEUIL_BREVE else "détaillée"


def moy(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def cout_total(d: dict) -> float:
    c = cad.get(d["id"])
    return (d["cout_usd"] or 0) + ((c["cout_usd"] or 0) if c else 0)


def taux(d: dict) -> float:
    return d["taux_cache"] if d.get("taux_cache") is not None else 0.0


def ic(valeurs: list, stat, n: int = 5000, graine: int = 13) -> tuple[float, float]:
    rng = random.Random(graine)
    if len(valeurs) < 2:
        return float("nan"), float("nan")
    res = sorted(stat([rng.choice(valeurs) for _ in valeurs]) for _ in range(n))
    return res[int(0.025 * n)], res[int(0.975 * n) - 1]


def par_story(arm: str, filtre=lambda d: True) -> dict[str, dict]:
    out = {}
    for s in sorted({d["story"] for d in devs if d["arm"] == arm and filtre(d)}):
        ds = [d for d in devs if d["arm"] == arm and d["story"] == s and filtre(d)]
        out[s] = {"n": len(ds), "dev": moy([d["cout_usd"] for d in ds]), "total": moy([cout_total(d) for d in ds]), "taux": moy([taux(d) for d in ds])}
    return out


def comparer(a: str, b: str, filtre=lambda d: True, stories: set[str] | None = None) -> dict:
    ia, ib = par_story(a, filtre), par_story(b, filtre)
    cles = [k for k in sorted(ia) if k in ib and (stories is None or k in stories)]
    if not cles:
        return {}
    paires = [(ia[k], ib[k]) for k in cles]
    idx = list(range(len(paires)))
    agrege = lambda ii: sum(paires[i][1]["total"] for i in ii) / sum(paires[i][0]["total"] for i in ii) - 1  # noqa: E731
    dt = lambda ii: moy([(paires[i][1]["taux"] - paires[i][0]["taux"]) * 100 for i in ii])  # noqa: E731
    ecarts = [(y["taux"] - x["taux"]) * 100 for x, y in paires]
    return {
        "paires": len(paires), "stories": cles,
        "cout_agrege": agrege(idx), "cout_agrege_ic": ic(idx, agrege),
        "dev_seul_agrege": sum(y["dev"] for _, y in paires) / sum(x["dev"] for x, _ in paires) - 1,
        "taux_a": moy([x["taux"] * 100 for x, _ in paires]), "taux_b": moy([y["taux"] * 100 for _, y in paires]),
        "taux_ecart_pts": dt(idx), "taux_ecart_ic": ic(idx, dt),
        "meilleur": sum(1 for e in ecarts if e > 0.01), "egal": sum(1 for e in ecarts if abs(e) <= 0.01), "pire": sum(1 for e in ecarts if e < -0.01),
    }  # fmt: skip


def ligne_bras(arm: str, filtre=lambda d: True) -> dict:
    ds = [d for d in devs if d["arm"] == arm and filtre(d)]
    cs = [cad[d["id"]] for d in ds if d["id"] in cad]
    return {
        "n": len(ds), "stories": len({d["story"] for d in ds}),
        "cadrage_usd": moy([c["cout_usd"] for c in cs]) if cs else 0.0, "cadrage_tours": moy([c["tours"] for c in cs]) if cs else 0.0,
        "dev_usd": moy([d["cout_usd"] for d in ds]), "dev_tours": moy([d["tours"] for d in ds]), "dev_s": moy([d["duree_mur_s"] for d in ds]),
        "total_usd": moy([cout_total(d) for d in ds]), "taux": moy([taux(d) for d in ds]) * 100,
        "complets": sum(1 for d in ds if taux(d) >= 0.999),
        "ruff_propre": sum(1 for d in ds if d["ruff_erreurs"] == 0 and d["ruff_format_fichiers"] == 0),
        "ruff_mesures": sum(1 for d in ds if d["ruff_erreurs"] >= 0),
        "hors_perimetre": sum(1 for d in ds if d["diff"]["hors_perimetre"]),
        "erreurs": sum(1 for d in ds if d.get("is_error") or d.get("expire")),
    }  # fmt: skip


def fmt_cmp(c: dict) -> str:
    if not c:
        return "pas de paire"
    return (f"{c['paires']} stories | coût {c['cout_agrege'] * 100:+.1f} % [{c['cout_agrege_ic'][0] * 100:+.1f} ; {c['cout_agrege_ic'][1] * 100:+.1f}] "
            f"(dév. seul {c['dev_seul_agrege'] * 100:+.1f} %) | taux {c['taux_a']:.1f} % contre {c['taux_b']:.1f} % : "
            f"**{c['taux_ecart_pts']:+.1f} points** [{c['taux_ecart_ic'][0]:+.1f} ; {c['taux_ecart_ic'][1]:+.1f}] | mieux/égal/moins bien {c['meilleur']}/{c['egal']}/{c['pire']}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    nouveaux = lambda d: d["source"] == "T13bis"  # noqa: E731
    toutes = sorted({d["story"] for d in devs})
    strates = {s: richesse(s) for s in toutes}
    sortie = {
        "bras": {a: ligne_bras(a) for a in ("A", "D", "Dc")},
        "D_vs_A": comparer("A", "D"),
        "D_vs_A_nouveaux_runs": comparer("A", "D", nouveaux),
        "D_vs_A_stories_T13": comparer("A", "D", stories={s for s in toutes if s in {d["story"] for d in runs_t13}}),
        "D_vs_A_stories_nouvelles": comparer("A", "D", stories={s for s in toutes if s not in {d["story"] for d in runs_t13}}),
        "D_vs_A_sans_u57": comparer("A", "D", stories={s for s in toutes if s not in ("u57", "l13")}),
        "Dc_vs_D": comparer("D", "Dc"), "Dc_vs_A": comparer("A", "Dc"),
        "strates": {r: {"D_vs_A": comparer("A", "D", stories={s for s, v in strates.items() if v == r}),
                        "Dc_vs_D": comparer("D", "Dc", stories={s for s, v in strates.items() if v == r}),
                        "D_vs_A_nouveaux_runs": comparer("A", "D", nouveaux, stories={s for s, v in strates.items() if v == r})} for r in ("détaillée", "brève")},
        "richesse": strates,
    }  # fmt: skip
    # répétabilité : écart rep 2 − rep 1 du même bras, stories de T13
    rep = {}
    for arm in ("A", "D"):
        ecarts = []
        for s in toutes:
            xs = {d["rep"]: taux(d) * 100 for d in devs if d["arm"] == arm and d["story"] == s}
            if 1 in xs and 2 in xs:
                ecarts.append(xs[2] - xs[1])
        rep[arm] = {"n": len(ecarts), "ecart_abs_moyen": moy([abs(e) for e in ecarts]), "var_run": moy([e * e / 2 for e in ecarts])}
    sortie["repetabilite"] = rep
    # par story
    tab = {}
    for s in toutes:
        tab[s] = {}
        for a in ("A", "D", "Dc"):
            ds = sorted([d for d in devs if d["story"] == s and d["arm"] == a], key=lambda d: d["rep"])
            if ds:
                tab[s][a] = {"taux": [round(taux(d) * 100) for d in ds], "total": moy([cout_total(d) for d in ds]),
                             "cadrage": moy([cad[d["id"]]["cout_usd"] for d in ds if d["id"] in cad] or [0])}  # fmt: skip
    sortie["par_story"] = tab
    (ICI / "donnees" / "agregats.json").write_text(json.dumps(sortie, indent=1, ensure_ascii=False), encoding="utf-8")

    f = lambda x, n=2: f"{x:.{n}f}"  # noqa: E731
    print("## Par bras (toutes les exécutions, T13 répétition 1 comprise)\n")
    print("| Bras | runs | stories | cadrage $ | tours | dév. $ | tours | s | total $ | tests cachés | 100 % | ruff propre | hors périmètre | erreurs |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for a, nom in (("A", "A cadrage BMAD"), ("D", "D sans cadrage"), ("Dc", "D-court")):
        b = sortie["bras"][a]
        if b["n"]:
            print(f"| {nom} | {b['n']} | {b['stories']} | {f(b['cadrage_usd'])} | {f(b['cadrage_tours'], 1)} | {f(b['dev_usd'])} | {f(b['dev_tours'], 1)} | {f(b['dev_s'], 0)} | "
                  f"{f(b['total_usd'])} | {f(b['taux'], 1)} % | {b['complets']}/{b['n']} | {b['ruff_propre']}/{b['ruff_mesures']} | {b['hors_perimetre']}/{b['n']} | {b['erreurs']} |")
    print("\n## Comparaisons appariées (IC 95 % bootstrap par story)\n")
    for cle, nom in (("D_vs_A", "D − A, toutes les données (critère principal)"), ("D_vs_A_nouveaux_runs", "D − A, runs de T13 bis seulement (robustesse)"),
                     ("D_vs_A_sans_u57", "D − A, sans u57 ni l13 (défaut de banc, sensibilité)"),
                     ("D_vs_A_stories_T13", "D − A, 10 stories de T13 (2 répétitions)"), ("D_vs_A_stories_nouvelles", "D − A, nouvelles stories"),
                     ("Dc_vs_D", "D-court − D"), ("Dc_vs_A", "D-court − A")):
        print(f"- {nom} : {fmt_cmp(sortie[cle])}")
    print("\n## Par strate de richesse de l'entrée\n")
    for r, v in sortie["strates"].items():
        print(f"- {r} ({sum(1 for x in strates.values() if x == r)} stories) : D − A : {fmt_cmp(v['D_vs_A'])} ; D − A sur les runs de T13 bis seuls (confirmatoire) : {fmt_cmp(v['D_vs_A_nouveaux_runs'])} ; D-court − D : {fmt_cmp(v['Dc_vs_D'])}")
    print("\n## Répétabilité (stories à 2 répétitions)\n")
    for a, v in rep.items():
        print(f"- {a} : {v['n']} stories, écart absolu moyen entre répétitions {f(v['ecart_abs_moyen'], 1)} points, variance par run {f(v['var_run'], 0)}")
    print("\n## Par story (taux des tests cachés par répétition ; coût total moyen, dont cadrage)\n")
    print("| Story | Richesse | A | D | D-court |\n|---|---|---|---|---|")
    for s, v in tab.items():
        cell = lambda a: (" / ".join(f"{t} %" for t in v[a]["taux"]) + f" ; {f(v[a]['total'])} $" + (f" ({f(v[a]['cadrage'])})" if a == "A" else "")) if a in v else "-"  # noqa: E731
        print(f"| {s} | {strates[s]} | {cell('A')} | {cell('D')} | {cell('Dc')} |")
    c = sortie["D_vs_A"]
    if c:
        bas = c["taux_ecart_ic"][0]
        print(f"\n## Critère\n\nBorne basse de D − A : {bas:+.1f} points. Marge principale −{MARGE:.0f} : {'tenue' if bas > -MARGE else 'non tenue'} ; "
              f"marge secondaire −{MARGE_SECONDAIRE:.0f} : {'tenue' if bas > -MARGE_SECONDAIRE else 'non tenue'}. "
              f"Coût de D sous A d'au moins 50 % : {'oui' if c['cout_agrege'] <= -0.5 else 'non'} ({c['cout_agrege'] * 100:+.1f} %).")


if __name__ == "__main__":
    main()
