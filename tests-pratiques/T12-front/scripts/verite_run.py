"""Pilote de l'oracle scripté : uv run --no-project python verite_run.py ARBRE STORY MODE  -> JSON sur stdout."""
import json, sys
from commun import *

def verite(arbre, story, mode, port=8765):
    env = env_enfant()
    env["T12_CHROMIUM"] = str(CHROMIUM); env["T12_UV"] = UV; env["T12_AXE"] = str(T7 / "mesures" / "node" / "node_modules" / "axe-core" / "axe.min.js")
    r = subprocess.run([UV, "run", "--project", str(T7 / "mesures"), "python", str(Path(__file__).parent / "verite.py"), str(arbre), story, mode, str(port)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=600)
    try:
        d = json.loads(r.stdout.strip().splitlines()[-1])
        return d["checks"], d.get("axe", {})
    except Exception:
        return {"erreur_oracle": [False, (r.stdout + r.stderr)[-400:]]}, {}

if __name__ == "__main__":
    arbre, story, mode = sys.argv[1:4]
    res, axe = verite(arbre, story, mode)
    print('axe', {k: v for k, v in axe.items() if v})
    for k, (ok, det) in res.items():
        print(story, k, "OK" if ok else "KO", det[:170])
