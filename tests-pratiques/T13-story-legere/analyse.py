"""Analyse T13 : tableaux par bras, coût par étape, comparaison appariée A contre B (bootstrap), critère de décision.

Usage : uv run --no-project python -I analyse.py   (écrit donnees/agregats.json, imprime les tableaux en markdown)
"""

import json
import random
from pathlib import Path

ICI = Path(__file__).resolve().parent
D = ICI / "donnees"
random.seed(13)


def charger(nom: str) -> list[dict]:
    p = D / nom
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l] if p.exists() else []


devs = charger("runs.jsonl")
cads = charger("cadrages.jsonl")
cad = {c["id"]: c for c in cads}


def moy(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def cout_total(d: dict) -> float:
    c = cad.get(d["id"])
    return (d["cout_usd"] or 0) + ((c["cout_usd"] or 0) if c else 0)


def tours_total(d: dict) -> int:
    c = cad.get(d["id"])
    return (d["tours"] or 0) + ((c["tours"] or 0) if c else 0)


def duree_totale(d: dict) -> float:
    c = cad.get(d["id"])
    return d["duree_mur_s"] + (c["duree_mur_s"] if c else 0)


def taux(d: dict) -> float:
    return d["taux_cache"] if d.get("taux_cache") is not None else 0.0


def ic(valeurs: list[float], stat, n: int = 5000) -> tuple[float, float]:
    if len(valeurs) < 2:
        return float("nan"), float("nan")
    res = sorted(stat([random.choice(valeurs) for _ in valeurs]) for _ in range(n))
    return res[int(0.025 * n)], res[int(0.975 * n)]


def ligne_bras(arm: str) -> dict:
    ds = [d for d in devs if d["arm"] == arm]
    cs = [cad[d["id"]] for d in ds if d["id"] in cad]
    return {
        "n": len(ds),
        "cadrage_usd": moy([c["cout_usd"] for c in cs]) if cs else 0.0,
        "cadrage_tours": moy([c["tours"] for c in cs]) if cs else 0.0,
        "cadrage_s": moy([c["duree_mur_s"] for c in cs]) if cs else 0.0,
        "cadrage_chars": moy([c["spec_chars"] for c in cs]) if cs else 0.0,
        "dev_usd": moy([d["cout_usd"] for d in ds]),
        "dev_tours": moy([d["tours"] for d in ds]),
        "dev_s": moy([d["duree_mur_s"] for d in ds]),
        "total_usd": moy([cout_total(d) for d in ds]),
        "total_tours": moy([tours_total(d) for d in ds]),
        "total_s": moy([duree_totale(d) for d in ds]),
        "taux": moy([taux(d) for d in ds]),
        "complets": sum(1 for d in ds if taux(d) >= 0.999),
        "ruff_propre": sum(1 for d in ds if d["ruff_erreurs"] == 0 and d["ruff_format_fichiers"] == 0),
        "ruff_mesures": sum(1 for d in ds if d["ruff_erreurs"] >= 0),
        "hors_perimetre": sum(1 for d in ds if d["diff"]["hors_perimetre"]),
        "spec_chars_dev": moy([d["spec_chars"] for d in ds]),
    }


def par_story_moyenne(arm: str) -> dict[str, dict]:
    """Une ligne par story : coûts et taux moyennés sur les répétitions (unité du bootstrap : la story)."""
    out = {}
    for s in sorted({d["story"] for d in devs if d["arm"] == arm}):
        ds = [d for d in devs if d["arm"] == arm and d["story"] == s]
        out[s] = {"cout_usd": moy([d["cout_usd"] for d in ds]), "total": moy([cout_total(d) for d in ds]), "taux": moy([taux(d) for d in ds])}
    return out


def appariement(a: str, b: str) -> list[tuple[dict, dict]]:
    ia, ib = par_story_moyenne(a), par_story_moyenne(b)
    return [(ia[k], ib[k]) for k in sorted(ia) if k in ib]


def comparer(a: str, b: str) -> dict:
    paires = appariement(a, b)
    if not paires:
        return {}
    ca = [x["total"] for x, _ in paires]
    cb = [y["total"] for _, y in paires]
    idx = list(range(len(paires)))
    agrege = lambda ii: sum(cb[i] for i in ii) / sum(ca[i] for i in ii) - 1  # noqa: E731
    rel = lambda ii: moy([cb[i] / ca[i] - 1 for i in ii])  # noqa: E731
    dt = lambda ii: moy([(paires[i][1]["taux"] - paires[i][0]["taux"]) * 100 for i in ii])  # noqa: E731
    dev_a = [x["cout_usd"] for x, _ in paires]
    dev_b = [y["cout_usd"] for _, y in paires]
    return {
        "paires": len(paires),
        "cout_agrege": agrege(idx), "cout_agrege_ic": ic(idx, agrege),
        "cout_relatif_moyen": rel(idx), "cout_relatif_ic": ic(idx, rel),
        "dev_seul_agrege": sum(dev_b) / sum(dev_a) - 1,
        "taux_ecart_pts": dt(idx), "taux_ecart_ic": ic(idx, dt),
        "b_moins_cher": sum(1 for i in idx if cb[i] < ca[i]),
    }


def main() -> None:
    import sys

    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    sortie = {"bras": {a: ligne_bras(a) for a in "ABCD"}, **{f"{a}_vs_{b}": comparer(a, b) for a, b in (("A", "B"), ("A", "D"), ("B", "D"), ("A", "C"), ("B", "C"), ("D", "C"))}}
    # par story
    stories = sorted({d["story"] for d in devs})
    par_story = {}
    for s in stories:
        par_story[s] = {}
        for a in "ABCD":
            ds = [d for d in devs if d["story"] == s and d["arm"] == a]
            if ds:
                par_story[s][a] = {
                    "n": len(ds), "total_usd": moy([cout_total(d) for d in ds]), "cadrage_usd": moy([cad[d["id"]]["cout_usd"] for d in ds if d["id"] in cad] or [0]),
                    "taux": moy([taux(d) for d in ds]),
                }
    sortie["par_story"] = par_story
    (D / "agregats.json").write_text(json.dumps(sortie, indent=1, ensure_ascii=False), encoding="utf-8")

    f = lambda x, n=2: f"{x:.{n}f}"  # noqa: E731
    print("| Bras | n | cadrage $ | tours | s | car. | dev $ | tours | s | total $ | tours | s | taux caches | 100 % | ruff propre | hors périmètre |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for a, nom in (("A", "A BMAD complet"), ("B", "B voie légère"), ("D", "D sans cadrage (hors protocole)"), ("C", "C spec d'origine")):
        b = sortie["bras"][a]
        if not b["n"]:
            continue
        print(
            f"| {nom} | {b['n']} | {f(b['cadrage_usd'])} | {f(b['cadrage_tours'], 1)} | {f(b['cadrage_s'], 0)} | {f(b['cadrage_chars'], 0)} | {f(b['dev_usd'])} | {f(b['dev_tours'], 1)} | "
            f"{f(b['dev_s'], 0)} | {f(b['total_usd'])} | {f(b['total_tours'], 1)} | {f(b['total_s'], 0)} | {f(b['taux'] * 100, 1)} % | {b['complets']}/{b['n']} | {b['ruff_propre']}/{b['ruff_mesures']} | {b['hors_perimetre']}/{b['n']} |"
        )
    for cle in ("A_vs_B", "A_vs_D", "B_vs_D", "A_vs_C", "B_vs_C", "D_vs_C"):
        c = sortie[cle]
        if c:
            print(f"\n{cle} ({c['paires']} paires) : coût total agrégé {c['cout_agrege'] * 100:+.1f} % [{c['cout_agrege_ic'][0] * 100:+.1f} ; {c['cout_agrege_ic'][1] * 100:+.1f}], "
                  f"relatif moyen {c['cout_relatif_moyen'] * 100:+.1f} % [{c['cout_relatif_ic'][0] * 100:+.1f} ; {c['cout_relatif_ic'][1] * 100:+.1f}], dev seul {c['dev_seul_agrege'] * 100:+.1f} %, "
                  f"taux {c['taux_ecart_pts']:+.1f} pt [{c['taux_ecart_ic'][0]:+.1f} ; {c['taux_ecart_ic'][1]:+.1f}], moins cher {c['b_moins_cher']}/{c['paires']}")
    print("\n| Story | A total $ (cadrage) | taux A | B total $ (cadrage) | taux B | D $ | taux D | C $ | taux C |")
    print("|---|---|---|---|---|---|---|---|---|")
    for s, v in par_story.items():
        cell = lambda a: (f"{f(v[a]['total_usd'])} ({f(v[a]['cadrage_usd'])})", f"{f(v[a]['taux'] * 100, 0)} %") if a in v else ("-", "-")  # noqa: E731
        print(f"| {s} | {cell('A')[0]} | {cell('A')[1]} | {cell('B')[0]} | {cell('B')[1]} | {cell('D')[0].split(' ')[0]} | {cell('D')[1]} | {cell('C')[0].split(' ')[0]} | {cell('C')[1]} |")


if __name__ == "__main__":
    main()
