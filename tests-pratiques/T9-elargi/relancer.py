r"""T9 elargi : relance toute la chaine (extraction, etiquettes, scores, analyse) en un seul processus a la fois.

Etapes, dans l'ordre : ``extraire_agents.py`` (transcriptions -> agents.json), ``construire_donnees.py`` (specs, etiquettes,
``etiquettes.csv``), ``scorer.py`` (Jev latest, Jev 1,13, gpt-6-luna deux fois : seules les stories nouvelles sont
demandees, plafond de 4 $ cumule dans ``budget.json``), ``analyse.py`` (``resultats.json``, ``tableaux.md``).
Le texte des specs et le detail par agent restent dans ``--travail`` (HORS du depot de veille). La cle OpenRouter est lue
par ``cle.py`` (variable ``OPENROUTER_API_KEY`` de l'environnement, sinon ``HKCU\Environment``), jamais affichee.

Commande exacte (depuis ce dossier ; ajouter une racine ``--transcriptions`` par PC rapatrie, meme structure de dossiers) :

    uv run --no-project --with numpy --with scikit-learn --with scipy python relancer.py --transcriptions D:\rapatrie\pc2\projects --transcriptions D:\rapatrie\pc3\projects

Options : ``--travail <dossier>`` (defaut ``~/.cache/veille-t9-elargi``), ``--sans-racine-locale`` (ignorer
``~/.claude/projects``), ``--sans-scoring`` (extraction, etiquettes et analyse seulement, sans appel payant),
``--forcer-scores`` (refaire tous les scores), ``--racine-depots`` (clones git, defaut ``~/Documents/GitHub``).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent


def lancer(*args: str) -> None:
    print("==>", Path(args[0]).name, *args[1:], flush=True)
    r = subprocess.run([sys.executable, *args], cwd=ICI)
    if r.returncode != 0:
        raise SystemExit(f"echec : {Path(args[0]).name} (code {r.returncode})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--travail", type=Path, default=Path.home() / ".cache" / "veille-t9-elargi")
    ap.add_argument("--transcriptions", type=Path, action="append", default=[])
    ap.add_argument("--sans-racine-locale", action="store_true")
    ap.add_argument("--racine-depots", type=Path, default=Path.home() / "Documents" / "GitHub")
    ap.add_argument("--sans-scoring", action="store_true")
    ap.add_argument("--forcer-scores", action="store_true")
    o = ap.parse_args()
    o.travail.mkdir(parents=True, exist_ok=True)

    ext = [str(ICI / "extraire_agents.py"), "--travail", str(o.travail)]
    for t in o.transcriptions:
        ext += ["--transcriptions", str(t)]
    if o.sans_racine_locale:
        ext.append("--sans-racine-locale")
    lancer(*ext)
    lancer(str(ICI / "construire_donnees.py"), "--travail", str(o.travail), "--racine-depots", str(o.racine_depots))
    if not o.sans_scoring:
        textes = str(o.travail / "textes.json")
        forcer = ["--forcer"] if o.forcer_scores else []
        lancer(str(ICI / "scorer.py"), "--bras", "jev", "--modele", "~typesafe/jev-latest", "--textes", textes, "--out", str(ICI / "scores_jev_latest.json"), *forcer)
        lancer(str(ICI / "scorer.py"), "--bras", "jev", "--modele", "typesafe/jev-1.13", "--textes", textes, "--out", str(ICI / "scores_jev_1_13.json"), *forcer)
        for r in ("r1", "r2"):
            lancer(str(ICI / "scorer.py"), "--bras", "llm", "--modele", "openai/gpt-6-luna", "--textes", textes,
                   "--out", str(ICI / f"scores_luna_{r}.json"), "--fils", "2", *forcer)
    lancer(str(ICI / "analyse.py"))
    print("termine : resultats.json et tableaux.md mis a jour ; reporter les chiffres dans resultats.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
