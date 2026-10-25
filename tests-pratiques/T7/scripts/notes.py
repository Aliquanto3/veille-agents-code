"""Croise la note à l'aveugle d'Anaël (export de notation.html) avec correspondance.json, moyennes par bras.

Usage : uv run --no-project python scripts/notes.py [donnees/notes-anael.json]
"""

import json
import statistics as st
import sys
from pathlib import Path

T7 = Path(__file__).resolve().parent.parent
CRITERES = ["lisibilite", "finition", "coherence"]


def main():
    fichier = Path(sys.argv[1]) if len(sys.argv) > 1 else T7 / "donnees" / "notes-anael.json"
    notes = json.loads(fichier.read_text(encoding="utf-8"))
    corr = json.loads((T7 / "correspondance.json").read_text(encoding="utf-8"))
    par = {}
    for lettre, m in corr.items():
        if lettre in notes:
            par.setdefault(m["bras"], []).append((m["repetition"], lettre, notes[lettre]))
    lignes = ["| Bras | " + " | ".join(CRITERES) + " | moyenne | rendus (lettre : moyenne) |",
              "|---|" + "---|" * (len(CRITERES) + 2)]
    resume = {}
    for bras in sorted(par):
        ms = [st.mean(n[c] for _, _, n in par[bras]) for c in CRITERES]
        detail = ", ".join(f"r{r} {l} : {st.mean(n[c] for c in CRITERES):.2f}" for r, l, n in sorted(par[bras]))
        resume[bras] = dict(zip(CRITERES, ms), moyenne=st.mean(ms))
        lignes.append(f"| {bras} | " + " | ".join(f"{m:.2f}" for m in ms) + f" | {st.mean(ms):.2f} | {detail} |")
    (T7 / "donnees" / "notes_resume.json").write_text(json.dumps(resume, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(lignes))


if __name__ == "__main__":
    main()
