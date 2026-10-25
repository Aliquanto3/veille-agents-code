"""T10b : verifie a la main (par comparaison de sorties) que des cibles declarees equivalentes le sont.
usage (variables T10_RACINE, PYTHONUTF8) : sonde_equiv.py <story> <essai>   (arbre du bras C deja prepare)
Applique chaque mutant declare equivalent, execute une sonde (corpus de documents, ou validateur pydantic) et compare
la signature des sorties a celle du code d'origine. Egalite sur tout le corpus = pas de contre-exemple trouve."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from jeu import arbre, env_pour, python
from mutation import applique

ICI = Path(__file__).parent
CIBLES = json.loads((ICI / "cibles.json").read_text(encoding="utf-8"))

SONDE_US16 = r'''
import hashlib, random, sys
from usine.ui.outillage import rendre_fiche
frag = ["# Titre", "# Second titre", "## Section A", "## Section B", "### sous", "texte \u2705 ok \u26a0\ufe0f attention \u274c ko",
        "`code \u2705`", "**gras \u2705**", "| a | b |\n|---|---|\n| \u2705 | x |\n| \u274c | y |", "- item \u274c\n- autre \u2705", "<b>html</b>",
        "> citation \u26a0", "1. un\n2. deux", "```\nbloc \u2705\n```", "texte *\u00e9mphase* `\u274c` fin", "", "# ", "\u2705", "#"]
rnd = random.Random(7)
h = hashlib.sha256(); n = 0
docs = [""] + [f for f in frag] + [f + "\n\n" + g for f in frag for g in frag]
for _ in range(1500):
    docs.append("\n\n".join(rnd.choice(frag) for _ in range(rnd.randint(1, 9))))
for d in docs:
    try:
        out = rendre_fiche(d)
    except Exception as e:
        out = "EXC " + type(e).__name__
    h.update(out.encode()); h.update(b"\0"); n += 1
print(n, h.hexdigest())
'''

SONDE_WD84 = r'''
import hashlib
from pydantic import ValidationError
from wavedevsecops.scenarios.ops.replace_in_file import Args
h = hashlib.sha256()
cas = [dict(path="a.txt", old="x", new="y"), dict(path="a.txt", old="", new="y"), dict(path="/abs", old="x", new="y"),
       dict(path="../x", old="x", new="y"), dict(path="", old="x", new="y"), dict(path="a\b", old="\n", new=""), dict(path="a", old=" ", new="z"),
       dict(path="a", old=None, new="z"), dict(path="a", old=3, new="z")]
for c in cas:
    try:
        a = Args(op="replace_in_file", **c)
        out = "OK " + repr(a)
    except ValidationError as e:
        out = "VE " + str([(x["loc"], x["type"], x["msg"]) for x in e.errors()])
    h.update(out.encode()); h.update(b"\0"); print(out[:110])
print(h.hexdigest())
'''

CIBLES_A_VERIFIER = {
    "us-7-16": ["outillage.py:55", "outillage.py:72", "outillage.py:87", "outillage.py:89", "outillage.py:92"],
    "wd-8-4": ["replace_in_file.py:27"],
}


def lancer(story, essai, code):
    a = arbre(story, "C", essai)
    f = a / "_sonde_tmp.py"
    f.write_text(code, encoding="utf-8")
    try:
        p = subprocess.run([python(story, "C"), str(f)], cwd=a, env=env_pour(story, "C", essai), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=300)
        return (p.stdout + p.stderr).strip()
    finally:
        f.unlink(missing_ok=True)


def main():
    story, essai = sys.argv[1], int(sys.argv[2])
    a = arbre(story, "C", essai)
    code = SONDE_US16 if story == "us-7-16" else SONDE_WD84
    base = lancer(story, essai, code)
    print("origine :", base.splitlines()[-1][:100])
    res = {"origine": base.splitlines()[-1], "mutants": {}}
    for cid in CIBLES_A_VERIFIER[story]:
        c = next(x for x in CIBLES[story]["cibles"] if x["id"] == f"{story}:{cid}")
        with applique(a / c["module"], c):
            out = lancer(story, essai, code)
        ident = out == base
        res["mutants"][cid] = {"identique": ident, "signature": out.splitlines()[-1][:100]}
        print(cid, "identique" if ident else "DIFFERENT", out.splitlines()[-1][:100])
    (ICI / "resultats-bruts" / "T10b" / f"sonde-{story}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
