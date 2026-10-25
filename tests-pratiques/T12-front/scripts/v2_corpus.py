"""Volet 2 : corpus de rejeu (spec, tests cachés) pour 7.15 et 7.14, avec le code du banc de rejeu."""
import json, sys
sys.path.insert(0, str(Path := __import__("pathlib").Path(__file__).resolve().parents[2] / "banc-rejeu"))
import extraire_corpus as ec
from commun import *

STORIES_V2 = [
    {"id": "v715", "story": "7.15", "titre": "Lancement de la Chaîne et bouton de mode", "commit": "d58ce6c",
     "spec": "_bmad-output/implementation-artifacts/spec-7-15-lancement-de-la-chaine-et-bouton-de-mode.md"},
    {"id": "v714", "story": "7.14", "titre": "Carte météo, détail d'une Entité et livrables", "commit": "9eb4728",
     "spec": "_bmad-output/implementation-artifacts/spec-7-14-carte-meteo-detail-d-une-entite-et-livrables.md"},
]
if __name__ == "__main__":
    sortie = ICI / "corpus-v2"
    for e in STORIES_V2:
        m = ec.construire(DEPOT, e, sortie)
        print(m["id"], m["base"][:7], m["tests_caches"])
