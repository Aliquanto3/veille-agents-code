"""Remplace les chemins locaux des fichiers bruts par `<user>` avant publication.

Usage : uv run --no-project python -I anonymiser.py FICHIER_OU_GLOB...
Remplace `C:\\Users\\Utilisateur` et `C:\\Users\\UTILIS~1` (barres obliques ou doubles, échappées JSON ou non)
par `<user>`, et le nom de dossier de projet `C--Users-Utilisateur` / `C--Users-UTILIS-1` par `C--Users-user`.
"""

import glob
import re
import sys
from pathlib import Path

MOTIFS = [
    (re.compile(r"(?:C:)?(?:\\\\|\\|/)Users(?:\\\\|\\|/)(?:Utilisateur|UTILIS~1)", re.I), "<user>"),
    (re.compile(r"C--Users-(?:Utilisateur|UTILIS-1)"), "C--Users-user"),
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
            print(f, anonymiser(Path(f)))
