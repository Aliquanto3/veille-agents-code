"""Joue seulement les textes nouveaux : ceux qui ont un `textes/<id>/source.md` mais aucune sortie (ou des
sorties incomplètes). Enchaîne : conditions (A, B, C, D), juge, tics, régénération de notation.html.
Les lettres déjà tirées pour les textes déjà notés sont conservées (correspondance.json).

Prérequis : `uv run python preparer.py` (projets jetables et skills aux SHA épinglés).
Pour un nouveau texte Xn : créer textes/Xn/source.md (et lecteur.txt ; pour une langue autre que le français,
ajouter l'identifiant à LANGUES dans config.py), puis lancer ce script. Un fichier `<!-- TEXTE -->` dans
source.md sépare une éventuelle attribution (non envoyée aux modèles) du texte à réécrire.

Usage : uv run python relancer_nouveaux.py [--seulement X5]
"""
import subprocess, sys
from config import T11, CONDITIONS, ESSAIS


def incomplet(tid):
    return any(not (T11 / "sorties" / tid / f"{c}-{e}.md").exists() for c in CONDITIONS for e in ESSAIS)


def main():
    args = sys.argv[1:]
    if args[:1] == ["--seulement"]:
        nouveaux = args[1:]
    else:
        nouveaux = sorted(d.name for d in (T11 / "textes").iterdir() if (d / "source.md").exists() and incomplet(d.name))
    if not nouveaux:
        print("Aucun texte nouveau."); return
    print("Textes à jouer :", nouveaux)
    py = [sys.executable, "-I"]
    here = T11 / "scripts"
    for script in ("lancer_conditions.py", "juge.py", "mesurer_tics.py", "generer_notation.py"):
        r = subprocess.run([sys.executable, str(here / script), *nouveaux if script != "generer_notation.py" else []], cwd=here)
        if r.returncode:
            sys.exit(r.returncode)


if __name__ == "__main__":
    main()
