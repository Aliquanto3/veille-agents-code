"""Chemins et constantes communs de T11. Le scratchpad doit être donné en chemin long (jamais UTILIS~1)."""
import os
from pathlib import Path

T11 = Path(__file__).resolve().parent.parent
SCRATCH = Path(os.environ.get(
    "T11_SCRATCH",
    r"C:\Users\Utilisateur\AppData\Local\Temp\claude\C--Users-Utilisateur-Documents-GitHub"
    r"\791fed94-a8b0-414e-8a6c-8fe967283749\scratchpad\t11"))
VENDOR = SCRATCH / "vendor"
PROJETS = SCRATCH / "projets"   # un projet jetable par condition (A, B, C)
MODELE = "claude-opus-5-5"
EFFORT = "medium"
ESSAIS = (1, 2)
CONDITIONS = ("A", "B", "C", "D")
NOMS = {"A": "sans skill", "B": "humanizer", "C": "clarity", "D": "clarity puis humanizer"}
LANGUES = {"X4": "en"}   # X1 à X3 en français
LECTEURS = {
    "X1": "tes contacts LinkedIn, consultants et développeurs",
    "X2": "un responsable technique qui décide de la configuration de son équipe",
    "X3": "ses contacts LinkedIn, consultants et développeurs",
    "X4": "an engineering lead choosing a coding-agent setup",
}
CONSIGNE = ("Réécris ce texte en français pour le rendre plus clair et plus naturel, pour {lecteur}. "
            "N'invente aucun fait, ne renforce aucune affirmation, garde les chiffres et les renvois. "
            "Rends seulement le texte.")
SKILL_PHRASE = {
    "A": "",
    "B": "Utilise d'abord la skill humanizer (outil Skill). ",
    "C": "Utilise d'abord la skill clarity en mode rewrite (outil Skill). ",
}
TOOLS = "Read,Write,Edit,Glob,Grep,Skill"
CONSIGNE_EN = ("Rewrite this text in English to make it clearer and more natural, for {lecteur}. "
               "Do not invent any fact, do not strengthen any claim, keep the numbers and the references. "
               "Return only the text.")
SKILL_PHRASE_EN = {
    "A": "",
    "B": "First use the humanizer skill (Skill tool). ",
    "C": "First use the clarity skill in rewrite mode (Skill tool). ",
}
MARQUEUR = "<!-- TEXTE -->"


def langue(tid):
    return LANGUES.get(tid, "fr")


def lire_source(tid):
    """Texte à réécrire : tout le fichier, ou la partie après le marqueur (attribution en tête)."""
    t = (T11 / "textes" / tid / "source.md").read_text(encoding="utf-8")
    if MARQUEUR in t:
        t = t.split(MARQUEUR, 1)[1]
    return t.strip() + "\n"
