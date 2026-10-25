"""Passe complémentaire à `../banc-rejeu/anonymiser.py` : chemins à quatre barres (JSON échappé deux fois), dossiers
`pytest-of-<nom>` et fragments de chemin tronqués. Ne touche que le nom de compte dans un contexte de chemin.

Usage : uv run --no-project python -I anonymiser_complement.py FICHIER_OU_GLOB...
"""

import glob
import re
import sys
from pathlib import Path

SEP = r"(?:\\{1,8}|/)"
MOTIFS = [
    (re.compile(rf"(?:C:)?{SEP}Users{SEP}(?:Utilisateur|UTILIS~1)", re.I), "<user>"),
    (re.compile(r"pytest-of-(?:Utilisateur|UTILIS~1)"), "pytest-of-user"),
    (re.compile(r"C--Users-(?:Utilisateur|UTILIS-1)|(?<![\w-])(?:Utilisateur|UTILIS-1)(?=-Documents-GitHub)"), "C--Users-user"),
    (re.compile(rf"(rs{SEP}|{SEP})(?:Utilisateur|UTILIS~1)(?={SEP})"), r"\1user"),
]


def anonymiser(chemin: Path) -> int:
    texte = chemin.read_text(encoding="utf-8")
    nouveau, total = texte, 0
    for motif, remplacement in MOTIFS:
        nouveau, n = motif.subn(remplacement, nouveau)
        total += n
    if total:
        chemin.write_text(nouveau, encoding="utf-8", newline="")
    return total


if __name__ == "__main__":
    for motif in sys.argv[1:]:
        for f in sorted(glob.glob(motif)):
            n = anonymiser(Path(f))
            if n:
                print(f, n)
