"""T10 : verifie que les 75 mutants s'appliquent et se compilent (interpreteur de la story)."""
import json, subprocess, tempfile, os
from jeu import *
from mutation import muter
c = json.load(open("cibles.json", encoding="utf-8"))
bad = 0
for s, v in c.items():
    a = arbre(s, "A", 0)
    for t in v["cibles"]:
        p = a / t["module"]
        try:
            n = muter(p.read_bytes(), t["ligne"], t["moins"], t["plus"])
            assert n != p.read_bytes()
            with tempfile.NamedTemporaryFile("wb", suffix=".py", delete=False) as f:
                f.write(n)
            r = subprocess.run([python(s, "A"), "-c", "import sys;compile(open(sys.argv[1],encoding='utf-8').read(),'x','exec')", f.name], capture_output=True, text=True)
            os.unlink(f.name)
            assert r.returncode == 0, r.stderr[-200:]
        except Exception as e:
            bad += 1; print("ECHEC", t["id"], repr(e)[:200])
print("echecs", bad)
