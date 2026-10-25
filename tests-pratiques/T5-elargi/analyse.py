r"""T5 elargi : agregats (rappel, Wilson, faux positifs, combinaisons, cout, latence) -> analyse.json et tableaux Markdown.

Entrees : T:\sem\<id>\verite.json, T:\constats.json, T:\detections.json (juger.py appliquer),
          T5-elargi\classification_temoins.json ({"relecteur|story|n": "demontre|discutable|faux"}), reponses brutes T:\rep, T:\rep_gpt.
usage : analyse.py [--md]
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

T = Path("T:/")
ICI = Path(__file__).resolve().parent
NOMS = {"haiku": "Haiku 5.5 (second-avis)", "opus": "Opus 5.5 (reviewer)", "openai/gpt-6-luna": "gpt-6-luna", "openai/gpt-6.1-sol": "gpt-6.1-sol"}
ORDRE = ["haiku", "opus", "openai/gpt-6-luna", "openai/gpt-6.1-sol"]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - m) / d, (c + m) / d)


def pct(x: float) -> str:
    return f"{100 * x:.0f} %"


def charger():
    verite = {d.name: json.loads((d / "verite.json").read_text(encoding="utf-8")) for d in sorted((T / "sem").iterdir())}
    constats = json.loads((T / "constats.json").read_text(encoding="utf-8"))
    det = json.loads((T / "detections.json").read_text(encoding="utf-8"))
    return verite, constats, det


def cout_latence() -> dict:
    out = defaultdict(lambda: {"cout": 0.0, "lat": 0.0, "n": 0})
    for a in ("haiku", "opus"):
        for f in (T / "rep" / a).glob("*.json"):
            d = json.loads(f.read_text(encoding="utf-8"))
            o = out[a]
            o["cout"] += d.get("total_cost_usd", 0.0)
            o["lat"] += d.get("_duree_s", 0.0)
            o["n"] += 1
    for f in (T / "rep_gpt").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        o = out[d["modele"]]
        o["cout"] += d.get("cout_usd", 0.0)
        o["lat"] += d.get("latence_s", 0.0)
        o["n"] += 1
    return out


def main() -> None:
    verite, constats, det = charger()
    semees = sorted(s for s, v in verite.items() if not v.get("temoin"))
    temoins = sorted(s for s, v in verite.items() if v.get("temoin"))
    classif_f = ICI / "classification_temoins.json"
    classif = json.loads(classif_f.read_text(encoding="utf-8")) if classif_f.exists() else {}
    res: dict = {"semees": semees, "temoins": temoins, "relecteurs": {}}
    # detections[(relecteur, story)] = (any, important)
    hit = defaultdict(lambda: [False, False])
    for c in det:
        if c["detecte"]:
            h = hit[(c["relecteur"], c["story"])]
            h[0] = True
            h[1] = h[1] or c["important"]
    # constats par (relecteur, story)
    par = defaultdict(list)
    for c in constats:
        par[(c["relecteur"], c["story"])].append(c)
    detecte_ids = {(c["relecteur"], c["story"], c["n"]) for c in det if c["detecte"]}
    n = len(semees)
    for r in ORDRE:
        k_all = sum(hit[(r, s)][0] for s in semees)
        k_imp = sum(hit[(r, s)][1] for s in semees)
        imp_hors = 0
        imp_temoins = 0
        fp_t = {"demontre": 0, "discutable": 0, "faux": 0, "artefact": 0, "non_classe": 0}
        nit_total = 0
        for s in semees:
            for c in par[(r, s)]:
                if c["important"] and (r, s, c["n"]) not in detecte_ids:
                    imp_hors += 1
        for s in temoins:
            for c in par[(r, s)]:
                if c["important"]:
                    imp_temoins += 1
                    fp_t[classif.get(f"{r}|{s}|{c['n']}", "non_classe")] += 1
        imp_par_story = {s: sum(c["important"] for c in par[(r, s)]) for s in semees + temoins}
        tot_imp = sum(imp_par_story.values())
        res["relecteurs"][r] = dict(
            rappel=[k_all, n, wilson(k_all, n)], rappel_important=[k_imp, n, wilson(k_imp, n)],
            important_hors_semis=imp_hors, important_temoins=imp_temoins, classes_temoins=fp_t,
            important_total=tot_imp, constats_total=sum(len(par[(r, s)]) for s in semees + temoins),
            important_par_story_moy=round(tot_imp / (len(semees) + len(temoins)), 2),
        )
    # combinaisons
    def union(rs: list[str], important: bool) -> int:
        return sum(any(hit[(r, s)][1 if important else 0] for r in rs) for s in semees)

    comb = {}
    for nom, rs in {"Haiku seul": ["haiku"], "Opus seul": ["opus"], "chaine (Haiku + Opus)": ["haiku", "opus"],
                    "chaine + luna": ["haiku", "opus", "openai/gpt-6-luna"], "chaine + sol": ["haiku", "opus", "openai/gpt-6.1-sol"],
                    "chaine + luna + sol": ["haiku", "opus", "openai/gpt-6-luna", "openai/gpt-6.1-sol"],
                    "luna + sol": ["openai/gpt-6-luna", "openai/gpt-6.1-sol"]}.items():
        ka, ki = union(rs, False), union(rs, True)
        bruit = sum(res["relecteurs"][r]["important_hors_semis"] + res["relecteurs"][r]["important_temoins"] for r in rs)
        classes = {k: sum(res["relecteurs"][r]["classes_temoins"][k] for r in rs) for k in ("demontre", "discutable", "faux", "artefact", "non_classe")}
        comb[nom] = dict(rappel=[ka, n, wilson(ka, n)], rappel_important=[ki, n, wilson(ki, n)], bruit_important=bruit,
                         important_temoins=sum(res["relecteurs"][r]["important_temoins"] for r in rs), classes_temoins=classes)
    res["combinaisons"] = comb
    # gains par story de chaque critique externe sur la chaine
    gains = {}
    for x in ("openai/gpt-6-luna", "openai/gpt-6.1-sol"):
        g = [s for s in semees if any(hit[(x, s)][0] for _ in [0]) and not any(hit[(r, s)][0] for r in ("haiku", "opus"))]
        gi = [s for s in semees if hit[(x, s)][1] and not any(hit[(r, s)][1] for r in ("haiku", "opus"))]
        gains[x] = {"toutes_severites": g, "important": gi}
    res["gains_sur_chaine"] = gains
    # par origine du defaut et par depot
    strat = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for s in semees:
        v = verite[s]
        for crit, cle in (("origine", v["origine"]), ("depot", s[:2])):
            for r in ORDRE:
                strat[f"{crit}:{cle}"][r][1] += 1
                strat[f"{crit}:{cle}"][r][0] += hit[(r, s)][0]
            strat[f"{crit}:{cle}"]["chaine"][1] += 1
            strat[f"{crit}:{cle}"]["chaine"][0] += any(hit[(r, s)][0] for r in ("haiku", "opus"))
    res["strates"] = {k: dict(v) for k, v in strat.items()}
    # matrice par story
    res["matrice"] = {s: {r: hit[(r, s)] for r in ORDRE} for s in semees}
    res["cout_latence"] = cout_latence()
    (ICI / "analyse.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=list), encoding="utf-8")
    # affichage
    print("semees", n, "temoins", len(temoins))
    for r in ORDRE:
        x = res["relecteurs"][r]
        print(f"{NOMS[r]:28s} rappel {x['rappel'][0]}/{n} = {pct(x['rappel'][0] / n)} IC [{pct(x['rappel'][2][0])} ; {pct(x['rappel'][2][1])}] | important {x['rappel_important'][0]}/{n} | hors semis {x['important_hors_semis']} | temoins {x['important_temoins']} {x['classes_temoins']} | Important/story {x['important_par_story_moy']}")
    for k, x in comb.items():
        print(f"{k:24s} rappel {x['rappel'][0]}/{n} {pct(x['rappel'][0] / n)} [{pct(x['rappel'][2][0])};{pct(x['rappel'][2][1])}] | imp {x['rappel_important'][0]}/{n} | bruit {x['bruit_important']} | temoins {x['important_temoins']} {x['classes_temoins']}")
    print("gains sur la chaine", json.dumps(gains))
    for k, v in res["cout_latence"].items():
        print(k, f"cout {v['cout']:.2f} $ sur {v['n']} reponses, latence moy {v['lat'] / max(v['n'], 1):.0f} s")


if __name__ == "__main__":
    main()
