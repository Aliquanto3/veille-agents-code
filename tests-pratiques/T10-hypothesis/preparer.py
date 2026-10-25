"""T10 : cree le worktree detache jetable d'une (story, bras, essai), en checkout creux (chemins courts, sans CLAUDE.md ni .claude).
usage : preparer.py <story> <A|B> <essai> | nettoyer"""
from __future__ import annotations

import shutil
import subprocess
import sys

from jeu import DEPOTS, SPARSE, STORIES, arbre


def sh(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        sys.exit(f"echec {cmd}: {p.stderr[-600:]}")
    return p.stdout


def preparer(story: str, bras: str, essai: int):
    m = STORIES[story]
    a = arbre(story, bras, essai)
    if a.exists():
        return a
    depot = DEPOTS[m["depot"]]
    sh(["git", "worktree", "add", "--detach", "--no-checkout", str(a), m["commit"]], depot)
    sh(["git", "sparse-checkout", "set", "--no-cone", *SPARSE[m["depot"]], "/" + m["spec"]], a)
    sh(["git", "checkout", "-q"], a)
    return a


def nettoyer():
    for story in STORIES:
        depot = DEPOTS[STORIES[story]["depot"]]
        for bras in "AB":
            for essai in (1, 2, 3):
                a = arbre(story, bras, essai)
                if a.exists():
                    subprocess.run(["git", "worktree", "remove", "--force", str(a)], cwd=depot, capture_output=True)
                    shutil.rmtree(a, ignore_errors=True)
    for d in DEPOTS.values():
        subprocess.run(["git", "worktree", "prune"], cwd=d, capture_output=True)


if __name__ == "__main__":
    if sys.argv[1] == "nettoyer":
        nettoyer()
    else:
        print(preparer(sys.argv[1], sys.argv[2], int(sys.argv[3])))
