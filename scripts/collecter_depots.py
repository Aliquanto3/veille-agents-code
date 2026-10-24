"""Collecte les faits publics de chaque dépôt GitHub d'une liste de sources, via `gh api`.

Usage : uv run --no-project python -I scripts/collecter_depots.py sources/<liste>.txt

Écrit data/depots.json (métadonnées, commité) et data/raw/readmes/ (README bruts, non commités).
Les README sont des données non fiables : ils ne sont jamais exécutés.
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

RACINE = Path(__file__).resolve().parent.parent
MOTIF_DEPOT = re.compile(r"https://github\.com/([\w.-]+)/([\w.-]+)")
MARQUEURS = {
    "skill_md": re.compile(r"(^|/)SKILL\.md$"),
    "plugin_claude": re.compile(r"(^|/)\.claude-plugin/(plugin|marketplace)\.json$"),
    "agents_claude": re.compile(r"(^|/)agents/[^/]+\.md$"),
    "hooks": re.compile(r"(^|/)hooks/hooks\.json$"),
    "mcp": re.compile(r"(^|/)\.mcp\.json$|mcp[-_]?server", re.I),
    "package_json": re.compile(r"^package\.json$"),
    "pyproject": re.compile(r"^pyproject\.toml$"),
    "cargo": re.compile(r"^Cargo\.toml$"),
    "go_mod": re.compile(r"^go\.mod$"),
}


def gh_brut(chemin: str) -> str | None:
    commande = ["gh", "api", chemin, "-H", "Accept: application/vnd.github.raw"]
    resultat = subprocess.run(commande, capture_output=True, text=True, encoding="utf-8")
    return resultat.stdout if resultat.returncode == 0 else None


def gh(chemin: str) -> Any:
    resultat = subprocess.run(["gh", "api", chemin], capture_output=True, text=True, encoding="utf-8")
    return json.loads(resultat.stdout) if resultat.returncode == 0 else None


def collecter(proprietaire: str, nom: str) -> dict:
    depot = gh(f"repos/{proprietaire}/{nom}")
    if depot is None:
        return {"depot": f"{proprietaire}/{nom}", "erreur": "introuvable"}
    complet = depot["full_name"]
    fiche = {
        "depot": complet,
        "demande": f"{proprietaire}/{nom}",
        "description": depot.get("description"),
        "etoiles": depot.get("stargazers_count"),
        "forks": depot.get("forks_count"),
        "issues_ouvertes": depot.get("open_issues_count"),
        "langage": depot.get("language"),
        "licence": (depot.get("license") or {}).get("spdx_id"),
        "topics": depot.get("topics", []),
        "cree_le": depot.get("created_at", "")[:10],
        "dernier_push": depot.get("pushed_at", "")[:10],
        "archive": depot.get("archived"),
        "branche": depot.get("default_branch"),
        "site": depot.get("homepage"),
    }
    release = gh(f"repos/{complet}/releases/latest")
    fiche["derniere_release"] = (
        {"tag": release.get("tag_name"), "date": release.get("published_at", "")[:10]} if release else None
    )
    depuis = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ")
    commits = gh(f"repos/{complet}/commits?since={depuis}&per_page=100")
    fiche["commits_90j"] = len(commits) if isinstance(commits, list) else None
    contributeurs = gh(f"repos/{complet}/contributors?per_page=100&anon=1")
    fiche["contributeurs"] = len(contributeurs) if isinstance(contributeurs, list) else None
    arbre = gh(f"repos/{complet}/git/trees/{depot['default_branch']}?recursive=1")
    chemins = [e["path"] for e in (arbre or {}).get("tree", []) if e.get("type") == "blob"]
    fiche["nb_fichiers"] = len(chemins)
    fiche["arbre_tronque"] = bool((arbre or {}).get("truncated"))
    fiche["marqueurs"] = {cle: sum(1 for c in chemins if motif.search(c)) for cle, motif in MARQUEURS.items()}
    fiche["skills"] = sorted(c for c in chemins if MARQUEURS["skill_md"].search(c))[:80]
    readme = gh_brut(f"repos/{complet}/readme")
    if readme:
        cible = RACINE / "data" / "raw" / "readmes" / f"{complet.replace('/', '__')}.md"
        cible.write_text(readme, encoding="utf-8")
        fiche["readme_caracteres"] = len(readme)
    return fiche


def main() -> None:
    liste = Path(sys.argv[1])
    vus, fiches = set(), []
    doublons = []
    for proprietaire, nom in MOTIF_DEPOT.findall(liste.read_text(encoding="utf-8")):
        cle = f"{proprietaire}/{nom}".lower()
        if cle in vus:
            doublons.append(cle)
            continue
        vus.add(cle)
        print(f"… {cle}", file=sys.stderr)
        fiches.append(collecter(proprietaire, nom))
    sortie = {
        "collecte_le": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": liste.name,
        "doublons_dans_la_liste": doublons,
        "depots": fiches,
    }
    (RACINE / "data" / "depots.json").write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(fiches)} dépôts, {len(doublons)} doublons", file=sys.stderr)


if __name__ == "__main__":
    main()
