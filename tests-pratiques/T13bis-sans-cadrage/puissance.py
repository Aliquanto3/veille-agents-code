"""T13 bis : analyse de puissance faite avant les runs, à partir des seules données de T13.

Usage : uv run --no-project python -I puissance.py > donnees/puissance.md
Lit `../T13-story-legere/donnees/runs.jsonl` et `cadrages.jsonl`. Estime :
  - l'écart type des écarts appariés D − A par story (une répétition) ;
  - le bruit entre deux répétitions d'un même bras sur la même story (l51, bras A et B) ;
puis simule le plan de T13 bis (10 stories de T13 à deux répétitions, N nouvelles à une répétition), avec le bootstrap
apparié par story de l'analyse, pour donner la puissance de la non-infériorité selon la marge.
"""

import json
import math
import random
import statistics as st
import sys
from pathlib import Path

T13 = Path(__file__).resolve().parent.parent / "T13-story-legere" / "donnees"
random.seed(1313)


def charger(nom: str) -> list[dict]:
    return [json.loads(l) for l in (T13 / nom).read_text(encoding="utf-8").splitlines() if l]


runs = charger("runs.jsonl")
cads = {c["id"]: c for c in charger("cadrages.jsonl")}


def taux_moyen(story: str, arm: str) -> float:
    xs = [r["taux_cache"] * 100 for r in runs if r["story"] == story and r["arm"] == arm]
    return sum(xs) / len(xs)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    stories = sorted({r["story"] for r in runs if r["arm"] == "D"})
    ecarts = [taux_moyen(s, "D") - taux_moyen(s, "A") for s in stories]
    m, sd = st.mean(ecarts), st.stdev(ecarts)
    # bruit entre répétitions : l51, bras A et B (seule story rejouée)
    paires = []
    for arm in "AB":
        xs = [r["taux_cache"] * 100 for r in runs if r["story"] == "l51" and r["arm"] == arm]
        paires.append(xs)
    var_run = st.mean([(x[0] - x[1]) ** 2 / 2 for x in paires])
    cout_a = st.mean([(r["cout_usd"] or 0) + (cads[r["id"]]["cout_usd"] or 0) for r in runs if r["arm"] == "A"])
    cout_d = st.mean([r["cout_usd"] or 0 for r in runs if r["arm"] == "D"])
    print("# T13 bis : analyse de puissance (avant les runs)\n")
    print("## Variance observée en T13\n")
    print("| Story | D − A (points) |\n|---|---|")
    for s, e in zip(stories, ecarts):
        print(f"| {s} | {e:+.1f} |")
    print(f"\nMoyenne {m:+.1f} points, écart type {sd:.1f} points (10 stories, une répétition ; l51 : A moyenné sur 2).")
    print(f"Bruit entre deux runs du même bras (l51, A : {paires[0][0]:.1f} et {paires[0][1]:.1f} ; B : {paires[1][0]:.1f} et {paires[1][1]:.1f}) : "
          f"variance par run {var_run:.0f}, écart type {math.sqrt(var_run):.1f} points.")
    print(f"Si tout l'écart venait du bruit des runs, la variance d'un écart D − A à une répétition serait 2 × {var_run:.0f} = {2 * var_run:.0f}, "
          f"au-dessus de la variance observée ({sd ** 2:.0f}) : le bruit des runs explique tout l'écart observé, l'effet propre à chaque story n'est pas mesurable.")
    print(f"\nCoût moyen T13 : A (cadrage + dév.) {cout_a:.2f} $, D {cout_d:.2f} $.\n")

    v1 = sd**2
    print("## Puissance simulée du plan T13 bis\n")
    print("Modèle : écart par story ~ normal, de variance V1 × (f / r + 1 − f), V1 = variance observée à une répétition, r = répétitions, "
          "f = part du bruit des runs (1 : tout est bruit, comme l'indique l51 ; 0,5 : moitié). 2 000 simulations, bootstrap apparié percentile de 2 000 tirages, "
          "IC 95 % bilatéral ; « non-infériorité » si la borne basse de D − A dépasse −marge.\n")
    print("| Nouvelles stories N | f | Vrai écart | Demi-largeur IC | Marge 3 | Marge 5 | Marge 8 | Marge 10 |")
    print("|---|---|---|---|---|---|---|---|")
    for n_new in (8, 10, 12):
        for f in (1.0, 0.5):
            for vrai in (0.0, -2.7):
                variances = [v1 * (f / 2 + 1 - f)] * 10 + [v1] * n_new
                bornes, largeurs = [], []
                for _ in range(2000):
                    xs = [random.gauss(vrai, math.sqrt(v)) for v in variances]
                    n = len(xs)
                    boots = sorted(sum(random.choice(xs) for _ in range(n)) / n for _ in range(2000))
                    bas, haut = boots[50], boots[1949]
                    bornes.append(bas)
                    largeurs.append((haut - bas) / 2)
                puiss = [sum(1 for b in bornes if b > -d) / len(bornes) for d in (3, 5, 8, 10)]
                print(f"| {n_new} | {f:.1f} | {vrai:+.1f} | {st.mean(largeurs):.1f} | " + " | ".join(f"{p * 100:.0f} %" for p in puiss) + " |")
    print("\n## Budget\n")
    for n_new in (8, 9, 10, 12):
        lot1 = 9 * cout_a + 10 * cout_d
        lot2 = n_new * (cout_a + cout_d)
        dc = (10 + n_new) * cout_d
        print(f"- N = {n_new} : seconde répétition des 10 stories de T13 {lot1:.1f} $ ; nouvelles stories A + D {lot2:.1f} $ ; "
              f"D-court sur les {10 + n_new} stories {dc:.1f} $ ; total {lot1 + lot2 + dc:.1f} $ (sans D-court {lot1 + lot2:.1f} $).")


if __name__ == "__main__":
    main()
