import json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from lancer_claude import lancer, T7

ALLOWED = ["Read", "Write", "Edit", "Glob", "Grep", "Skill",
           "Bash(uv run *)", "Bash(node *)", "Bash(*impeccable*)", "Bash(ls *)", "Bash(cat *)"]

def un_bras(nom):
    d = T7 / "arms" / nom
    if (d / "_claude.meta.json").exists():
        print("déjà fait", nom, flush=True); return
    prompt = (d / "_prompt.txt").read_text(encoding="utf-8")
    print("début", nom, flush=True)
    m = lancer(d, prompt, allowed=ALLOWED, budget=6.0, timeout=2700)
    print("fin", nom, m.get("statut"), m.get("cout_usd"), m.get("duree_s"), flush=True)

if __name__ == "__main__":
    noms = sys.argv[1:]
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(un_bras, noms))
