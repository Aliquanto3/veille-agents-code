"""Dépouille la note à l'aveugle d'Anaël (export `notes-t7ter.json` de notation.html) : croise avec correspondance.json,
moyennes par bras, écran et critère, écart b5 - b2 avec intervalle de bootstrap apparié, et verdict du critère de décision.

Usage : uv run --no-project python scripts/notes.py [donnees/notes-anael.json [correspondance.json]]

Appariement : (écran, numéro d'essai). Les essais ne sont pas réellement appariés (exécutions indépendantes) ; c'est une
convention de calcul. 6 paires sur les deux écrans, 3 sur l'écran 2 seul : l'intervalle de ce dernier est très large.
"""
import json
import random
import statistics as st
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
CRITERES = ["lisibilite", "finition", "coherence"]


def moy3(n):
    return st.mean(n[c] for c in CRITERES)


def bootstrap(diffs, n=10000, graine=7):
    rng = random.Random(graine)
    ms = sorted(st.mean(rng.choices(diffs, k=len(diffs))) for _ in range(n))
    return ms[int(0.025 * n)], ms[int(0.975 * n) - 1]


def main():
    fichier = Path(sys.argv[1]) if len(sys.argv) > 1 else ICI / "donnees" / "notes-anael.json"
    notes = json.loads(fichier.read_text(encoding="utf-8"))
    corr = json.loads((Path(sys.argv[2]) if len(sys.argv) > 2 else ICI / "correspondance.json").read_text(encoding="utf-8"))
    manquants = [l for l in corr if l not in notes or any(c not in notes[l] for c in CRITERES)]
    if manquants:
        print("Rendus non notés (ou incomplets) :", ", ".join(sorted(manquants)))
    rendus = {}  # (bras, ecran, essai) -> notes
    for l, m in corr.items():
        if l in notes and all(c in notes[l] for c in CRITERES):
            rendus[(m["bras"], m["ecran"], m["essai"])] = dict(notes[l], lettre=l)

    resume = {}
    lignes = ["| Bras | Écran | " + " | ".join(CRITERES) + " | moyenne | rendus (lettre : moyenne) |", "|---|---|" + "---|" * (len(CRITERES) + 2)]
    for bras in ("b2", "b5"):
        for ecran in (1, 2, "tous"):
            L = sorted((k, v) for k, v in rendus.items() if k[0] == bras and (ecran == "tous" or k[1] == ecran))
            if not L:
                continue
            ms = [st.mean(v[c] for _, v in L) for c in CRITERES]
            detail = ", ".join(f"e{k[1]}r{k[2]} {v['lettre']} : {moy3(v):.2f}" for k, v in L)
            resume[f"{bras} écran {ecran}"] = dict(zip(CRITERES, ms), moyenne=st.mean(ms), n=len(L))
            lignes.append(f"| {bras} | {ecran} | " + " | ".join(f"{m:.2f}" for m in ms) + f" | {st.mean(ms):.2f} | {detail} |")
    print("\n".join(lignes))

    def ecart(ecrans):
        paires = [(e, r) for e in ecrans for r in (1, 2, 3) if ("b5", e, r) in rendus and ("b2", e, r) in rendus]
        if not paires:
            return None
        res = {}
        for crit in CRITERES + ["moyenne"]:
            f = (lambda v: moy3(v)) if crit == "moyenne" else (lambda v, c=crit: v[c])
            d = [f(rendus[("b5", e, r)]) - f(rendus[("b2", e, r)]) for e, r in paires]
            lo, hi = bootstrap(d)
            res[crit] = {"ecart": st.mean(d), "ic95": [lo, hi], "min": min(d), "max": max(d), "paires": len(d)}
        return res

    ecarts = {"ecran 1": ecart([1]), "ecran 2": ecart([2]), "deux écrans": ecart([1, 2])}
    print("\nÉcart b5 - b2 (moyenne des paires ; intervalle de bootstrap à 95 % ; min à max)")
    for k, v in ecarts.items():
        if not v:
            continue
        for crit, x in v.items():
            print(f"  {k:12s} {crit:10s} {x['ecart']:+.2f}  [{x['ic95'][0]:+.2f} ; {x['ic95'][1]:+.2f}]  ({x['min']:+.2f} à {x['max']:+.2f}, {x['paires']} paires)")

    # coût et verdict
    verdict = None
    runs_f = ICI / "donnees" / "design_runs.json"
    if runs_f.exists() and ecarts["ecran 2"]:
        runs = json.loads(runs_f.read_text(encoding="utf-8"))
        cout = lambda b, e=None: st.mean(r["cout_usd"] for r in runs if r["bras"] == b and (e is None or r["ecran"] == e))
        surcout = cout("b5") / cout("b2") - 1
        surcout2 = cout("b5", 2) / cout("b2", 2) - 1
        e2 = ecarts["ecran 2"]
        c1 = e2["moyenne"]["ecart"] >= 0.5
        c2 = e2["coherence"]["ecart"] >= 0
        c3 = surcout <= 0.10
        verdict = {"gain_ecran2": e2["moyenne"]["ecart"], "critere1_gain_ge_0_5": c1,
                   "ecart_coherence_ecran2": e2["coherence"]["ecart"], "critere2_coherence_non_inferieure": c2,
                   "surcout_6_essais": surcout, "surcout_ecran2": surcout2, "critere3_surcout_le_10pct": c3,
                   "decision": "garder DESIGN.md" if (c1 and c2 and c3) else "ne pas garder DESIGN.md en l'état"}
        print("\nCritère de décision :", json.dumps(verdict, ensure_ascii=False, indent=1))
    (ICI / "donnees" / "notes_resume.json").write_text(
        json.dumps({"moyennes": resume, "ecarts_b5_moins_b2": ecarts, "verdict": verdict}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
