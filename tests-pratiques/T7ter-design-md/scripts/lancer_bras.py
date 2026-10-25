"""Lance des bras `claude -p` (2 au plus en parallèle). Usage : lancer_bras.py b2_e1_r1 b5_e1_r1 ..."""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from chemins import ARMS
from lancer_claude import lancer

ALLOWED = ["Read", "Write", "Edit", "Glob", "Grep", "Skill",
           "Bash(uv run *)", "Bash(node *)", "Bash(*impeccable*)", "Bash(ls *)", "Bash(cat *)"]


def un_bras(nom):
    d = ARMS / nom
    if (d / "_claude.meta.json").exists():
        print("déjà fait", nom, flush=True); return
    prompt = (d / "_prompt.txt").read_text(encoding="utf-8")
    print("début", nom, flush=True)
    m = lancer(d, prompt, allowed=ALLOWED, budget=1.5, timeout=2700)
    print("fin", nom, m.get("statut"), m.get("cout_usd"), m.get("duree_s"), flush=True)


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(un_bras, sys.argv[1:]))
