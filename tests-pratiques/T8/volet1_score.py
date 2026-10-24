"""Note les réponses d'un fichier jsonl selon la grille de questions_lookup.py."""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from questions_lookup import Q

def noter(q, rep):
    ok = all(re.search(p, rep, re.I | re.S) for p in q["req"]) and not any(re.search(p, rep, re.I | re.S) for p in q["nok"])
    return int(ok)

if __name__ == "__main__":
    lignes = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
    par = {r["id"]: r for r in lignes}
    s = [noter(q, par[q["id"]]["answer"]) for q in Q if q["id"] in par]
    print(sys.argv[1], "auto:", sum(s), "/", len(s), "ids ratés:", [q["id"] for q, v in zip(Q, s) if not v])
