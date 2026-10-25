"""Extrait chaque story fusionnee dans un dossier jetable (git archive, sans historique) et installe l'environnement."""
import subprocess, sys
from commun import *

def preparer(sid, cible=None):
    s = STORIES[sid]
    cible = cible or (SCRATCH / "stories" / sid)
    effacer(cible); cible.mkdir(parents=True)
    arch = subprocess.Popen(["git", "-C", str(DEPOT), "archive", s["commit"]], stdout=subprocess.PIPE)
    subprocess.run(["tar", "-x", "-C", str(cible)], stdin=arch.stdout, check=True)
    arch.wait()
    effacer(cible / ".claude"); effacer(cible / "_bmad-output"); effacer(cible / "_bmad")
    for n in ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md"):
        (cible / n).unlink(missing_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=cible, check=True)
    subprocess.run(["git", *GIT_ID, "add", "-A"], cwd=cible, check=True, capture_output=True)
    subprocess.run(["git", *GIT_ID, "commit", "-qm", "etat fusionne"], cwd=cible, check=True)
    r = subprocess.run([UV, "sync", "--frozen"], cwd=cible, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-500:]
    return cible

if __name__ == "__main__":
    for sid in sys.argv[1:] or STORIES:
        print(sid, preparer(sid), flush=True)
