"""T13 bis : repère les commits de petites stories utilisables (mêmes critères que T13, section 3).

Usage : uv run --no-project python -I candidats.py > donnees/candidats.md
Lecture seule sur les dépôts d'origine (git log, git show). Critères : le sujet du commit cite un numéro de story X.Y
présent dans `epics.md` à la base ; le commit ajoute au moins un fichier `tests/**/test_*.py` ; au plus 3 fichiers source
modifiés (hors tests, docs, `_bmad*`, `.md`), dont aucun fichier de front (js, ts, html, css) ; au plus 200 lignes de
source modifiées (ajouts plus suppressions). Richesse de l'entrée : « riche » si elle porte des critères Given/When/Then.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

GITHUB = Path(r"C:\Users\Utilisateur\Documents\GitHub")
DEPOTS = ["wavelibrarian", "usine-migration-jira-demo", "wavelocalai", "service-public-slm-fine-tuning", "wavedevsecops"]
EPICS = "_bmad-output/planning-artifacts/epics.md"
DEJA_T13 = {"00b07955", "5f083236", "0febaeba", "97734e64", "558b621f", "8900082d", "347310df", "2229b27c", "fe4f03d3", "ab1fcfec", "8113003d", "d3cb062f"}
MAX_SRC, MAX_LIGNES = int(sys.argv[1]) if len(sys.argv) > 1 else 3, int(sys.argv[2]) if len(sys.argv) > 2 else 200
FRONT = (".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".vue", ".svelte")


def git(repo: str, *args: str) -> str:
    r = subprocess.run(["git", "-c", "core.quotepath=false", "-C", str(GITHUB / repo), *args], capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def entree_epics(texte: str, label: str) -> str | None:
    lignes = texte.splitlines()
    debut = next((i for i, l in enumerate(lignes) if re.match(rf"^###\s+Story\s+{re.escape(label)}\s*[:\s]", l)), None)
    if debut is None:
        return None
    fin = next((i for i in range(debut + 1, len(lignes)) if re.match(r"^#{1,3}\s", lignes[i])), len(lignes))
    return "\n".join(lignes[debut:fin]).strip()


def richesse(entree: str) -> str:
    return "riche" if re.search(r"\*\*Given\*\*|\bGiven\b|\bÉtant donné\b", entree) else "courte"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    sortie = []
    for repo in DEPOTS:
        cache_epics: dict[str, str] = {}
        for ligne in git(repo, "log", "--no-merges", "--format=%H%x09%s").splitlines():
            sha, sujet = ligne.split("\t", 1)
            if sha[:8] in DEJA_T13:
                continue
            if re.match(r"(?i)^(fix|docs?|chore|merge|test|refactor|revue)\b", sujet) or re.search(r"(?i)\brevue\b", sujet):
                continue
            labels = re.findall(r"(?<![\d.v])(\d{1,2})\.(\d{1,2})(?![\d.])", sujet)
            if not labels:
                continue
            num = git(repo, "show", "--numstat", "--format=", sha).splitlines()
            ajoutes_tests, src, lignes_src = [], [], 0
            statuts = dict((s.split("\t")[-1], s.split("\t")[0]) for s in git(repo, "show", "--name-status", "--format=", sha).splitlines() if s)
            for n in num:
                a, d, chemin = n.split("\t", 2)
                if re.match(r"^tests?/", chemin):
                    if statuts.get(chemin) == "A" and re.search(r"(^|/)test_[^/]*\.py$", chemin):
                        ajoutes_tests.append(chemin)
                    continue
                if re.match(r"^(_bmad|docs/|\.claude|\.github)", chemin) or chemin.endswith((".md", ".lock", ".txt", ".yaml", ".yml")):
                    continue
                src.append(chemin)
                lignes_src += (int(a) if a.isdigit() else 0) + (int(d) if d.isdigit() else 0)
            if not ajoutes_tests or not src or len(src) > MAX_SRC or lignes_src > MAX_LIGNES or any(s.endswith(FRONT) for s in src):
                continue
            base = git(repo, "rev-parse", sha + "^").strip()
            if base not in cache_epics:
                cache_epics[base] = git(repo, "show", f"{base}:{EPICS}")
            for maj, mineur in labels:
                label = f"{maj}.{mineur}"
                ent = entree_epics(cache_epics[base], label)
                if ent:
                    sortie.append({
                        "repo": repo, "commit": sha[:8], "label": label, "sujet": sujet[:90], "tests": ajoutes_tests,
                        "src": src, "lignes_src": lignes_src, "richesse": richesse(ent), "entree_chars": len(ent),
                    })  # fmt: skip
                    break
    print("| Dépôt | Commit | Story | Richesse | Car. entrée | Src (lignes) | Tests ajoutés | Sujet |")
    print("|---|---|---|---|---|---|---|---|")
    for c in sortie:
        print(f"| {c['repo']} | `{c['commit']}` | {c['label']} | {c['richesse']} | {c['entree_chars']} | {', '.join(Path(s).name for s in c['src'])} ({c['lignes_src']}) | {len(c['tests'])} | {c['sujet']} |")
    Path(__file__).resolve().parent.joinpath("donnees", "candidats.json").write_text(json.dumps(sortie, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
