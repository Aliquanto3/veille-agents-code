"""Applique / retire un défaut sur l'arbre d'une story. Usage : semer.py appliquer|retirer ID [ID...]"""
import glob, json, subprocess, sys
from commun import *

DEFAUTS = {d["id"]: d for d in json.loads((Path(__file__).parent / "defauts.json").read_text(encoding="utf-8"))}

def arbre(sid): return SCRATCH / os.environ.get("T12_STORIES", "stories") / sid

def appliquer(did):
    d = DEFAUTS[did]; racine = arbre(d["story"])
    for motif, ancien, nouveau, n in d["edits"]:
        fichiers = glob.glob(str(racine / motif))
        total = 0
        for f in fichiers:
            t = Path(f).read_bytes().decode("utf-8")
            t = t.replace("\r\n", "\n")
            k = t.count(ancien)
            if k:
                Path(f).write_bytes(t.replace(ancien, nouveau).encode("utf-8")); total += k
        assert total == n, f"{did}: {motif} attendu {n}, trouvé {total}"

def retirer(sid):
    subprocess.run(["git", *GIT_ID, "checkout", "--", "."], cwd=arbre(sid), check=True, capture_output=True)

if __name__ == "__main__":
    cmd, ids = sys.argv[1], sys.argv[2:]
    for i in ids:
        (appliquer if cmd == "appliquer" else (lambda x: retirer(DEFAUTS[x]["story"])))(i)
        print(cmd, i)
