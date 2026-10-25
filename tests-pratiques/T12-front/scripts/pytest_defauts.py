"""Vérifie que les tests pytest du dépôt (tests/unit/ui + tests/depot) passent avec chaque défaut semé et sur le témoin.
Usage : uv run --no-project python pytest_defauts.py [ID...]   (ID = d01..d16 ou t713..t716)"""
import json, sys, time
from commun import *
import semer

SORTIE = ICI / "donnees" / "pytest_defauts_lot3.jsonl"
SORTIE.parent.mkdir(exist_ok=True)

def lancer_pytest(sid):
    cible = semer.arbre(sid)
    t0 = time.time()
    r = subprocess.run([UV, "run", "--no-sync", "pytest", "-q", "--tb=line", "-p", "no:cacheprovider", "tests/unit/ui"],
                       cwd=cible, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env_enfant(), timeout=900)
    return {"code": r.returncode, "duree_s": round(time.time() - t0, 1), "fin": r.stdout[-400:]}

def un(ident):
    if ident.startswith("t"):
        sid = "s" + ident[1:]
    else:
        sid = semer.DEFAUTS[ident]["story"]; semer.appliquer(ident)
    try:
        res = lancer_pytest(sid)
    finally:
        semer.retirer(sid)
    res.update({"id": ident, "story": sid})
    with SORTIE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(res, ensure_ascii=False) + "\n")
    print(ident, res["code"], res["duree_s"], res["fin"].strip().splitlines()[-1] if res["fin"].strip() else "", flush=True)

if __name__ == "__main__":
    ids = sys.argv[1:] or [f"t{n}" for n in (713, 714, 715, 716)] + list(semer.DEFAUTS)
    for i in ids:
        un(i)
