"""Compare l'export OpenTelemetry (JSON normalisé) à la reconstitution depuis la transcription
(agents.csv de mesurer_couts.py + usage lu directement dans les .jsonl).

Usage : uv run --no-project python comparer.py <otel.json> <dossier_session> <agents.csv> [--cumulatif]
  <dossier_session> = ~/.claude/projects/<projet>/<session>  (le .jsonl est à côté du dossier)
--cumulatif : métriques de l'exporteur console (cumulées) ; sinon OTLP delta (à additionner).
"""
import csv
import glob
import json
import os
import sys
from collections import defaultdict

otel_path, sess, csv_path = sys.argv[1:4]
cumul = "--cumulatif" in sys.argv
otel = json.load(open(otel_path, encoding="utf-8"))
KEYS = ["input", "output", "ecriture", "lecture"]


def vide():
    return {"cout": 0.0, "input": 0, "output": 0, "ecriture": 0, "lecture": 0, "n": 0}


# 1. OTel, événements api_request (par agent)
ev = defaultdict(vide)
for e in otel["events"]:
    if e["name"] != "claude_code.api_request":
        continue
    a = e["attrs"]
    k = (a.get("agent_id") or "MAIN")[-8:] if a.get("agent_id") else "MAIN"
    d = ev[k]
    d["cout"] += float(a["cost_usd"]); d["n"] += 1
    d["input"] += int(a["input_tokens"]); d["output"] += int(a["output_tokens"])
    d["ecriture"] += int(a["cache_creation_tokens"]); d["lecture"] += int(a["cache_read_tokens"])

# 2. OTel, métriques (par query_source / agent.name)
met = defaultdict(vide)
TYPES = {"input": "input", "output": "output", "cacheCreation": "ecriture", "cacheRead": "lecture"}
acc = defaultdict(lambda: defaultdict(float))
for m in otel["metrics"]:
    a = m["attrs"]
    grp = "MAIN" if a.get("query_source") == "main" else a.get("agent.name", "?")
    champ = "cout" if m["name"] == "claude_code.cost.usage" else (TYPES.get(a.get("type")) if m["name"] == "claude_code.token.usage" else None)
    if not champ:
        continue
    if cumul:
        acc[grp][champ] = max(acc[grp][champ], m["value"])
    else:
        acc[grp][champ] += m["value"]
for g, d in acc.items():
    met[g].update(d)

# 3. Transcription : usage dédoublonné par message.id
def lire(path):
    d, vus = vide(), set()
    for l in open(path, encoding="utf-8"):
        o = json.loads(l)
        m = o.get("message") or {}
        if o.get("type") != "assistant" or m.get("id") in vus:
            continue
        vus.add(m.get("id")); u = m["usage"]
        d["input"] += u.get("input_tokens", 0); d["output"] += u.get("output_tokens", 0)
        d["ecriture"] += u.get("cache_creation_input_tokens", 0); d["lecture"] += u.get("cache_read_input_tokens", 0)
        d["n"] += 1
    return d

tr = {"MAIN": lire(sess + ".jsonl")}
for f in glob.glob(os.path.join(sess, "subagents", "agent-*.jsonl")):
    tr[os.path.basename(f)[:-6][-8:]] = lire(f)
for r in csv.DictReader(open(csv_path, encoding="utf-8")):
    k = "MAIN" if r["agent"] == "MAIN" else r["agent"]
    tr[k]["cout"] = float(r["cout_usd"])
    tr[k]["lu_csv"] = int(r["lu"]); tr[k]["sortie_estimee"] = int(r["sortie_estimee"])


def pct(a, b):
    return "0.00%" if a == b else f"{(a - b) / b * 100:+.2f}%" if b else "n/a"


print(f"{'agent':9}{'grandeur':10}{'OTel evts':>12}{'OTel metr.':>12}{'transcr.':>12}{'ecart evts':>12}{'ecart metr.':>12}")
tot = {"e": 0, "m": 0, "t": 0}
sub = {"e": 0, "m": 0, "t": 0}
# métriques indexées par type d'agent : relier MAIN et le sous-agent (un seul ici)
met_sub = [g for g in met if g != "MAIN"]
for k in tr:
    mg = met["MAIN"] if k == "MAIN" else (met[met_sub[0]] if met_sub else vide())
    for c in ["cout"] + KEYS:
        e, m, t = ev[k][c], mg[c], tr[k][c]
        f = (lambda x: f"{x:.5f}") if c == "cout" else (lambda x: f"{int(x)}")
        print(f"{k:9}{c:10}{f(e):>12}{f(m):>12}{f(t):>12}{pct(e, t):>12}{pct(m, t):>12}")
    tot["e"] += ev[k]["cout"]; tot["m"] += mg["cout"]; tot["t"] += tr[k]["cout"]
print(f"{'TOTAL':9}{'cout':10}{tot['e']:>12.5f}{tot['m']:>12.5f}{tot['t']:>12.5f}{pct(tot['e'], tot['t']):>12}{pct(tot['m'], tot['t']):>12}")
print("appels :", {k: (ev[k]["n"], tr[k]["n"]) for k in tr}, "(OTel, transcription)")
