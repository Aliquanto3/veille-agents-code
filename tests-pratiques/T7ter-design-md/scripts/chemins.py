"""Chemins communs. Le répertoire de travail est dans le scratchpad (chemin long, jamais le nom court 8.3 :
`claude -p` refuse les écritures sous un chemin court)."""
import os
from pathlib import Path

DEPOT = Path(__file__).resolve().parent.parent          # tests-pratiques/T7ter-design-md
if "T7TER_TRAVAIL" not in os.environ:
    raise SystemExit("Définir T7TER_TRAVAIL : dossier de travail (dans le scratchpad, chemin long) contenant arms/, base1/, base2/, "
                     "vendor-skills/, outils/ et mesures_rendus/")
TRAVAIL = Path(os.environ["T7TER_TRAVAIL"])
ARMS = TRAVAIL / "arms"
MESURES = TRAVAIL / "mesures_rendus"
OUTILS = TRAVAIL / "outils"
SKILL_SRC = TRAVAIL / "vendor-skills" / "skills" / "frontend-design"
SKILL_SHA = "dbd4588f9e1033efb41dad4bef2f7947c8993d44"
BASES = {1: TRAVAIL / "base1", 2: TRAVAIL / "base2"}
TACHES = {1: DEPOT / "tache-ecran1.md", 2: DEPOT / "tache-ecran2.md"}
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BRAS = ["b2", "b5"]
ECRANS = (1, 2)
ESSAIS = (1, 2, 3)


def nom(bras, ecran, essai):
    return f"{bras}_e{ecran}_r{essai}"
