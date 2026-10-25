r"""Lance les tests ciblés d'une story sur son arbre (T:\src\<id>) avec le venv du dépôt (T:\v\<depot>), PYTHONPATH sur l'arbre.
usage : lancer_tests.py <id> [--timeout 300]  -> code 0 si verts ; affiche la dernière ligne et la durée."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

T = Path("T:/")


def env_pour(depot: str, arbre: Path) -> dict:
    e = dict(os.environ)
    pp = [str(arbre / "src"), str(arbre)]
    e["PYTHONPATH"] = os.pathsep.join(pp)
    for k in list(e):
        if k.upper().endswith(("API_KEY", "_TOKEN", "SECRET")) or k in ("OPENROUTER_API_KEY",):
            e.pop(k)  # aucun secret dans l'environnement des tests
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    return e


def commande(sid: str) -> tuple[list[str], Path, dict]:
    meta = json.loads((T / "jeu" / sid / "meta.json").read_text(encoding="utf-8"))
    arbre = T / "src" / sid
    py = T / "v" / meta["depot"] / ".venv" / "Scripts" / "python.exe"
    tests = [t for t in meta["tests"] if (arbre / t).exists()]
    fd = T / "jeu" / sid / "deselect.json"
    des = json.loads(fd.read_text(encoding="utf-8")) if fd.exists() else {"ignore": [], "deselect": []}
    extra = [f"--ignore={i}" for i in des["ignore"]] + [f"--deselect={d}" for d in des["deselect"]]
    tests = [t for t in tests if t not in des["ignore"]]
    cmd = [str(py), "-m", "pytest", "-q", "--tb=short", "-x", "-p", "no:cacheprovider", *extra, *tests]
    return cmd, arbre, env_pour(meta["depot"], arbre)


def controle(sid: str) -> None:
    """Premier passage sans -x : les tests deja rouges dans cet environnement (paquet non installe, GUI, GGUF) sont ecartes."""
    cmd, arbre, env = commande(sid)
    base = [c for c in cmd if c not in ("-x",) and not c.startswith(("--ignore=", "--deselect="))]
    base = [c for c in base if not (c.endswith(".py") and "tests" in c)]
    meta = json.loads((T / "jeu" / sid / "meta.json").read_text(encoding="utf-8"))
    tests = [t for t in meta["tests"] if (arbre / t).exists()]
    p = subprocess.run([*base, "--continue-on-collection-errors", "-rfE", "--tb=no", *tests], cwd=arbre, env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=900)
    ign, des = [], []
    for ligne in p.stdout.splitlines():
        if ligne.startswith("ERROR ") and " - " in ligne or ligne.startswith("ERROR "):
            chemin = ligne.split()[1].replace("\\", "/")
            if "::" not in chemin and chemin.endswith(".py"):
                ign.append(chemin)
            else:
                des.append(chemin)
        elif ligne.startswith("FAILED "):
            des.append(ligne.split()[1].replace("\\", "/"))
    (T / "jeu" / sid / "deselect.json").write_text(json.dumps({"ignore": ign, "deselect": des}, indent=1), encoding="utf-8")
    print(sid, "ecartes : fichiers", ign, "tests", len(des), "|", (p.stdout.strip().splitlines() or [""])[-1][:120])


if __name__ == "__main__":
    sid = sys.argv[1]
    if "--controle" in sys.argv:
        sys.exit(controle(sid))
    timeout = int(sys.argv[sys.argv.index("--timeout") + 1]) if "--timeout" in sys.argv else 300
    cmd, arbre, env = commande(sid)
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=arbre, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        out = p.stdout.strip().splitlines()
        print(sid, "rc", p.returncode, f"{time.time() - t0:.0f}s", out[-1] if out else p.stderr[-300:])
        if p.returncode:
            print("\n".join(out[-25:]))
    except subprocess.TimeoutExpired:
        print(sid, "TIMEOUT", timeout)
