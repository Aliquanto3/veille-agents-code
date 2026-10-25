"""Construit le corpus du banc de rejeu depuis un dépôt BMAD public.

Pour chaque story de `stories.json` : commit de base (parent du commit de la story),
spec (story de `epics.md` à la base + contrat d'intention, plan et notes de conception de la spec,
sans frontmatter, revue, journal de triage ni résultat de run) et tests cachés (fichiers de
`tests/` AJOUTÉS par le commit de la story, dans leur version finale).

Usage : uv run --no-project python -I extraire_corpus.py [--depot CHEMIN]
Sortie : corpus/<id>/{meta.json, spec.md, cache/<chemin des tests>}
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
DEPOT_DEFAUT = Path(r"C:\Users\Utilisateur\Documents\GitHub\usine-migration-jira-demo")
SECTIONS_GARDEES = ("Code Map", "Tasks & Acceptance", "Design Notes")


def git(depot: Path, *args: str, binaire: bool = False) -> str | bytes:
    r = subprocess.run(["git", "-C", str(depot), *args], capture_output=True, check=True)
    return r.stdout if binaire else r.stdout.decode("utf-8")


def section_epics(texte: str, titre: str) -> str:
    """Section `### Story X.Y ...` d'epics.md jusqu'au titre suivant de même niveau ou supérieur."""
    lignes = texte.splitlines()
    debut = next(i for i, ligne in enumerate(lignes) if re.match(rf"###\s+{re.escape(titre)}\b", ligne))
    fin = len(lignes)
    for i in range(debut + 1, len(lignes)):
        if re.match(r"#{1,3}\s", lignes[i]):
            fin = i
            break
    return "\n".join(lignes[debut:fin]).strip()


def spec_pre_dev(texte: str) -> str:
    """Garde le contrat d'intention, le plan (Code Map, Tasks) et les Design Notes."""
    texte = re.sub(r"\A---\n.*?\n---\n", "", texte, count=1, flags=re.S)
    morceaux: list[str] = []
    contrat = re.search(r"<intent-contract>(.*?)</intent-contract>", texte, flags=re.S)
    if contrat:
        morceaux.append(contrat.group(1).strip())
    for titre in SECTIONS_GARDEES:
        m = re.search(rf"^## {re.escape(titre)}\n(.*?)(?=^## |\Z)", texte, flags=re.S | re.M)
        if m:
            morceaux.append(f"## {titre}\n{m.group(1).strip()}")
    return "\n\n".join(morceaux)


def construire(depot: Path, entree: dict, sortie: Path) -> dict:
    commit = str(git(depot, "rev-parse", entree["commit"])).strip()
    base = str(git(depot, "rev-parse", commit + "^")).strip()
    dossier = sortie / entree["id"]
    (dossier / "cache").mkdir(parents=True, exist_ok=True)
    epics = str(git(depot, "show", f"{base}:_bmad-output/planning-artifacts/epics.md"))
    story = section_epics(epics, f"Story {entree['story']}")
    spec = spec_pre_dev(str(git(depot, "show", f"{commit}:{entree['spec']}")))
    note = f"\n{entree['note']}\n" if entree.get("note") else ""
    (dossier / "spec.md").write_text(
        f"# Story {entree['story']}\n\n## Énoncé (epics.md)\n\n{story}\n\n## Spécification d'implémentation\n{note}\n{spec}\n",
        encoding="utf-8",
        newline="\n",
    )
    cache = []
    for ligne in str(git(depot, "diff-tree", "--no-commit-id", "--name-status", "-r", commit)).splitlines():
        statut, chemin = ligne.split("\t", 1)
        if statut == "A" and chemin.startswith("tests/"):
            octets = git(depot, "show", f"{commit}:{chemin}", binaire=True)
            cible = dossier / "cache" / chemin
            cible.parent.mkdir(parents=True, exist_ok=True)
            cible.write_bytes(octets)  # type: ignore[arg-type]
            cache.append(chemin)
    meta = {
        "id": entree["id"],
        "story": entree["story"],
        "titre": entree.get("titre", ""),
        "commit": commit,
        "base": base,
        "tests_caches": cache,
        "depot": str(depot),
    }
    (dossier / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--depot", type=Path, default=DEPOT_DEFAUT)
    p.add_argument("--stories", type=Path, default=ICI / "stories.json")
    p.add_argument("--sortie", type=Path, default=ICI / "corpus")
    a = p.parse_args()
    for entree in json.loads(a.stories.read_text(encoding="utf-8")):
        meta = construire(a.depot, entree, a.sortie)
        print(meta["id"], meta["base"][:7], len(meta["tests_caches"]), "fichiers de tests cachés")
    return 0


if __name__ == "__main__":
    sys.exit(main())
