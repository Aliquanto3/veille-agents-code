"""Extraction de texte seule d'un PDF non fiable (aucune exécution de son contenu).
Usage : uv run --with pypdf python -I extraire_x4.py <pdf> <sortie.txt>"""
import sys
from pypdf import PdfReader
r = PdfReader(sys.argv[1])
with open(sys.argv[2], "w", encoding="utf-8") as f:
    for i, p in enumerate(r.pages, 1):
        f.write(f"\n=== PAGE {i} ===\n")
        f.write(p.extract_text() or "")
print(len(r.pages), "pages")
