"""Statistiques du volet 1 : exactitude (grille automatique + relecture manuelle), latence, tok/s, coût."""
import json, statistics as st, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from questions_lookup import Q
from volet1_score import noter

# Relecture manuelle (1, 0,5 ou 0), question par question, après lecture des 120 réponses.
# Par défaut 1 ; seules les exceptions sont listées. Raisons dans resultats.md.
MANUEL = {
 "A": {"haiku": {}, "qwen3.5_4b": {9: .5}, "nemotron-3-nano_4b": {9: .5, 17: 0}},
 "B": {"haiku": {}, "qwen3.5_4b": {5: 0, 19: 0, 20: .5}, "nemotron-3-nano_4b": {2: 0, 5: .5, 9: 0, 17: .5}},
}
def charge(n, suf):
    return [json.loads(l) for l in open(f"out/{n}{suf}.jsonl", encoding="utf-8")]
def pct(v, p):
    v = sorted(v); return v[min(len(v) - 1, round(p * (len(v) - 1)))]
rows = {}
for var, suf in (("A", ""), ("B", "_full")):
    for n in ("haiku", "qwen3.5_4b", "nemotron-3-nano_4b"):
        r = charge(n, suf)
        auto = sum(noter(q, x["answer"]) for q, x in zip(Q, r))
        man = sum(MANUEL[var][n].get(x["id"], 1) for x in r)
        lat = [x["latency_s"] for x in r]
        d = dict(auto=auto, manuel=man, lat_med=st.median(lat), lat_p95=pct(lat, .95), lat_tot=sum(lat))
        if n == "haiku":
            d.update(api_med=st.median([x["api_ms"] / 1000 for x in r]), cout=sum(x["cost_usd"] for x in r),
                     tok_out=sum(x["out_tokens"] or 0 for x in r), erreurs=sum(bool(x["is_error"]) for x in r),
                     in_tot=sum((x["in_tokens"] or 0) + (x["cache_creation"] or 0) + (x["cache_read"] or 0) for x in r))
        else:
            d.update(tok_s=st.median([x["tok_s"] for x in r]), prompt_tok=st.median([x["prompt_tokens"] for x in r]),
                     out_tok=st.median([x["out_tokens"] for x in r]), prompt_s=st.median([x["prompt_s"] for x in r]))
        rows[(var, n)] = d
for k, d in rows.items():
    print(k, {a: round(b, 3) if isinstance(b, float) else b for a, b in d.items()})
for var in "AB":
    h = rows[(var, "haiku")]["manuel"]
    for n in ("qwen3.5_4b", "nemotron-3-nano_4b"):
        print(var, n, "ratio vs Haiku (manuel):", round(rows[(var, n)]["manuel"] / h * 100, 1), "%")
for n in ("qwen3.5_4b", "nemotron-3-nano_4b"):
    c = (rows[("A", n)]["manuel"] + rows[("B", n)]["manuel"]) / (rows[("A", "haiku")]["manuel"] + rows[("B", "haiku")]["manuel"])
    print("combiné", n, round(c * 100, 1), "%")
