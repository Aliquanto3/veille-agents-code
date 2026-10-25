"""T10 : agrege les eval-*.json et agent-*.json en tableaux (stdout, et resume.json)."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ICI = Path(__file__).parent
BR = ICI / "resultats-bruts"
CIBLES = json.loads((ICI / "cibles.json").read_text(encoding="utf-8"))
ORDRE = ["wd-5-9", "wd-8-4", "us-7-14", "us-7-15", "us-7-16"]


def charger():
    runs = []
    for f in sorted(BR.glob("eval-*.json")):
        e = json.loads(f.read_text(encoding="utf-8"))
        ag = json.loads((BR / f"agent-{e['story']}-{e['bras']}{e['essai']}.json").read_text(encoding="utf-8"))
        s = ag["sortie"]
        e["cout"] = s.get("total_cost_usd")
        e["tours"] = s.get("num_turns")
        e["duree_s"] = round((s.get("duration_ms") or 0) / 1000, 1)
        e["duree_mur_s"] = ag["duree_mur_s"]
        e["terminal"] = s.get("terminal_reason") or s.get("subtype")
        runs.append(e)
    return runs


def main():
    runs = charger()
    par = defaultdict(list)
    for r in runs:
        par[(r["story"], r["bras"])].append(r)
    lignes = []
    tot = {"A": defaultdict(float), "B": defaultdict(float)}
    for s in ORDRE:
        n = len(CIBLES[s]["cibles"])
        for b in "AB":
            for r in par.get((s, b), []):
                valide = "rejet" not in r and r.get("rejeu_possible")
                tues = r.get("tues") if valide else None
                lignes.append((s, b, r["essai"], tues, n, r.get("tues_avec_second_tirage"), r["cout"], r["tours"], r["duree_s"],
                               r.get("nb_tests_nouveaux"), len(r.get("tests_faux", [])), len(r.get("tests_instables", [])),
                               r.get("secondes_nouveaux_tests"), r.get("nb_given"), r.get("rejet")))
                if valide:
                    t = tot[b]
                    t["tues"] += tues; t["cibles"] += n; t["cout"] += r["cout"] or 0; t["runs"] += 1
                    t["faux"] += len(r["tests_faux"]); t["instables"] += len(r["tests_instables"]); t["tests"] += r["nb_tests_nouveaux"]
                    t["sec"] += r["secondes_nouveaux_tests"]; t["tours"] += r["tours"] or 0; t["duree"] += r["duree_s"]
    print("story bras essai tues/cibles (2e tirage) cout tours duree_s nb_tests faux instables sec_tests nb_given rejet")
    for l in lignes:
        print(*l)
    for b in "AB":
        t = tot[b]
        if t["cibles"]:
            print(b, f"tues {int(t['tues'])}/{int(t['cibles'])} = {100*t['tues']/t['cibles']:.1f} %", f"cout moyen {t['cout']/t['runs']:.2f}",
                  f"runs {int(t['runs'])}", "faux", int(t["faux"]), "instables", int(t["instables"]))
    # par cible : tuee par A seul / B seul
    kill = defaultdict(lambda: {"A": [], "B": []})
    for r in runs:
        for x in r.get("rejeu", []):
            kill[x["id"]][r["bras"]].append(x["etat"].startswith("tue"))
    seul = {"A": [], "B": []}
    for cid, d in kill.items():
        if d["A"] and d["B"]:
            a, b = sum(d["A"]) / len(d["A"]), sum(d["B"]) / len(d["B"])
            if a == 1 and b == 0:
                seul["A"].append(cid)
            if b == 1 and a == 0:
                seul["B"].append(cid)
    print("tuees par A seul", len(seul["A"]), seul["A"])
    print("tuees par B seul", len(seul["B"]), seul["B"])
    (ICI / "resultats-bruts" / "resume.json").write_text(json.dumps({"lignes": lignes, "seul": seul}, ensure_ascii=False, indent=1, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()


def markdown():
    runs = charger()
    par = defaultdict(list)
    for r in runs:
        par[(r["story"], r["bras"])].append(r)
    out = ["| Story | Bras | Tués / cibles (essai 1, essai 2) | Taux moyen | Coût moyen ($) | Tours | Durée agent (s) | Nouveaux tests | Dont Hypothesis (`@given`) | Temps des nouveaux tests (s) | Tests faux | Instables |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    moy = lambda xs: sum(xs) / len(xs)
    glob_ = {"A": defaultdict(list), "B": defaultdict(list)}
    for s in ORDRE:
        n = len(CIBLES[s]["cibles"])
        for b in "AB":
            rs = sorted(par[(s, b)], key=lambda r: r["essai"])
            tues = [r["tues"] for r in rs]
            out.append(f"| {s} | {b} | {', '.join(f'{t}/{n}' for t in tues)} | {100*moy(tues)/n:.0f} % | {moy([r['cout'] for r in rs]):.2f} | "
                       f"{moy([r['tours'] for r in rs]):.0f} | {moy([r['duree_s'] for r in rs]):.0f} | {moy([r['nb_tests_nouveaux'] for r in rs]):.0f} | "
                       f"{moy([r['nb_given'] for r in rs]):.1f} | {moy([r['secondes_nouveaux_tests'] for r in rs]):.1f} | "
                       f"{sum(len(r['tests_faux']) for r in rs)} | {sum(len(r['tests_instables']) for r in rs)} |")
            g = glob_[b]
            for r in rs:
                g["taux"].append(r["tues"] / n); g["cout"].append(r["cout"]); g["tours"].append(r["tours"]); g["duree"].append(r["duree_s"])
                g["sec"].append(r["secondes_nouveaux_tests"]); g["tests"].append(r["nb_tests_nouveaux"]); g["tues"].append(r["tues"]); g["n"].append(n)
    out.append("")
    for b in "AB":
        g = glob_[b]
        out.append(f"- Bras {b} : {sum(g['tues'])}/{sum(g['n'])} cibles tuées en cumulé ({100*sum(g['tues'])/sum(g['n']):.1f} %) ; taux moyen par exécution {100*moy(g['taux']):.1f} % "
                   f"(min {100*min(g['taux']):.0f} %, max {100*max(g['taux']):.0f} %) ; coût moyen {moy(g['cout']):.3f} $ ; tours {moy(g['tours']):.1f} ; "
                   f"durée agent {moy(g['duree']):.0f} s ; nouveaux tests {moy(g['tests']):.0f} ; temps des nouveaux tests {moy(g['sec']):.1f} s ; coût total {sum(g['cout']):.2f} $")
    print("\n".join(out))


if __name__ == "__main__" and len(__import__("sys").argv) > 1 and __import__("sys").argv[1] == "md":
    markdown()
