"""Statistiques complémentaires du volet 1 (par classe, par story, coûts, jetons). Sortie Markdown sur stdout."""
import json, statistics, collections
from agreger import *

res = json.loads((ICI / "donnees" / "volet1_resume.json").read_text(encoding="utf-8"))
runs = {(r["run"] if r["temoin"] else r["id"]): r for r in lire_jsonl(ICI / "donnees" / "verif_runs.jsonl") if r["temoin"] or r["id"] in DEFAUTS}
v = res["versions"]
INDEP = {"d04": ["T2"], "d09": ["T2"], "d11": ["T2"], "e06": ["T2"], "e07": ["T2"]}  # FAIL non ciblés jugés indépendants du défaut (classés à la main)
def classe(i): return DEFAUTS[i]["classe"]
par_classe = collections.defaultdict(lambda: [0, 0])
par_story = collections.defaultdict(lambda: [0, 0])
for i, x in v.items():
    if x["temoin"] or not x.get("principal"): continue
    par_classe[classe(i)][1] += 1; par_classe[classe(i)][0] += x["detecte_agent"]
    par_story[x["story"]][1] += 1; par_story[x["story"]][0] += x["detecte_agent"]
print("Par classe :"); [print(f"- {k} : {a}/{b}") for k, (a, b) in sorted(par_classe.items())]
print("Par story :"); [print(f"- {k} : {a}/{b}") for k, (a, b) in sorted(par_story.items())]
couts = [x["cout"] for x in v.values() if x["cout"] is not None]
print("coût : min %.3f médiane %.3f moyenne %.3f max %.3f total %.2f n=%d" % (min(couts), statistics.median(couts), statistics.mean(couts), max(couts), sum(couts), len(couts)))
durs = [x["duree_s"] for x in v.values()]
print("durée : min %.0f médiane %.0f moyenne %.0f max %.0f" % (min(durs), statistics.median(durs), statistics.mean(durs), max(durs)))
tours = [x["tours"] for x in v.values()]; app = [x["appels_outils"] for x in v.values()]
print("tours moyen %.1f, appels d'outils moyen %.1f" % (statistics.mean(tours), statistics.mean(app)))
u = [runs[k]["usage"] for k in v if runs.get(k) and runs[k].get("usage")]
for champ in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"):
    print(champ, round(statistics.mean(x.get(champ, 0) for x in u)))
tem = [x["cout"] for x in v.values() if x["temoin"]]; dfc = [x["cout"] for x in v.values() if not x["temoin"]]
print("coût témoins %.3f (n=%d), défauts %.3f (n=%d)" % (statistics.mean(tem), len(tem), statistics.mean(dfc), len(dfc)))
outils = collections.Counter()
for k in v:
    for n, c in (runs[k].get("outils") or {}).items(): outils[n.replace("mcp__playwright__", "")] += c
print("outils :", dict(outils.most_common()))
fp_indep = [i for i in INDEP if i in v]
print("FAIL non ciblés indépendants du défaut :", fp_indep, "sur", sum(1 for x in v.values() if not x["temoin"]), "versions défectueuses")
