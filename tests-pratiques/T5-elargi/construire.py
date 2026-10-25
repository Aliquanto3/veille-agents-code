r"""T5 elargi, etape 1 : construit pour chaque story retenue l'arbre fusionne (sans historique), le diff Python et la spec.

Sortie (sur le lecteur T: = scratchpad\t5e, chemins courts) :
  T:\src\<id>\   arbre du depot au commit fusionne (sans .git, sans _bmad-output, sans binaires)
  T:\jeu\<id>\diff_orig.patch, spec.md, meta.json
Le depot d'origine n'est jamais modifie (git archive, git diff : lecture seule).
"""
from __future__ import annotations

import fnmatch
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

from stories import CANDIDATES, G

T = Path("T:/")
SELECTION = {
    "wavedevsecops": ["wd59", "wd86", "wd96", "wd58", "wd81"],
    "wavestack": ["ws-granite", "ws-minicpm", "ws-v2s7", "ws-v2s2", "ws-v2s6"],
    "wavelocalai": ["wl93", "wl94", "wl95", "wl91", "wl27"],
    "usine-migration-jira-demo": ["us611", "us612", "us613", "us713", "us711"],
}
RESERVE = ["wd85", "wd56", "ws-v2s4", "ws-v1s4", "wl83", "us78"]
EXCLUS = [":(exclude)_bmad-output", ":(exclude)_bmad", ":(exclude).claude"] + [
    f":(exclude,glob)**/*.{e}" for e in ("png", "gif", "jpg", "mp4", "webm", "woff2", "woff", "pdf", "parquet", "zip", "ico", "xlsx", "pptx")]
# titres de section ecartes de la spec : ce qui est ecrit apres le developpement ou issu de la revue
SECTIONS_ECARTEES = re.compile(r"(revue|review|dev agent|change log|verification|auto run|journal|^tests?\b|e2e|implementation notes|dev notes|completion|file list)", re.I)
LIMITE_SPEC = 14_000


def git(repo: str, *a: str, binaire: bool = False):
    p = subprocess.run(["git", "-C", f"{G}/{repo}", "-c", "core.quotepath=false", *a], capture_output=True)
    if p.returncode:
        sys.exit(f"git {a} : {p.stderr[-300:]!r}")
    return p.stdout if binaire else p.stdout.decode("utf-8", "replace")


def decouper_spec(texte: str) -> str:
    morceaux = re.split(r"(?m)^(?=## )", texte)
    gardes = [morceaux[0]]
    for m in morceaux[1:]:
        titre = m.splitlines()[0].lstrip("# ").strip()
        if SECTIONS_ECARTEES.search(titre):
            continue
        gardes.append(m)
    return "".join(gardes)[:LIMITE_SPEC]


def construire(sid: str) -> dict:
    repo, base, post, motif = CANDIDATES[sid]
    base_sha = git(repo, "rev-parse", base).strip()
    post_sha = git(repo, "rev-parse", post).strip()
    fichiers = git(repo, "diff", "--name-only", base_sha, post_sha).splitlines()
    py = [f for f in fichiers if f.endswith(".py") and not f.startswith(("_bmad", "docs/", "content/", "data/", "demo/"))]
    diff = git(repo, "diff", "-U1", base_sha, post_sha, "--", *py)
    d0 = git(repo, "diff", "-U0", base_sha, post_sha, "--", *py)
    ajoutees: dict[str, list[int]] = {}
    courant = None
    for ligne in d0.splitlines():
        m = re.match(r"^\+\+\+ b/(.*)$", ligne)
        if m:
            courant = m.group(1)
            continue
        m = re.match(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", ligne)
        if m and courant:
            debut, n = int(m.group(1)), int(m.group(2) or 1)
            ajoutees.setdefault(courant, []).extend(range(debut, debut + n))
    tests = [f for f in py if "tests/" in f and Path(f).name.startswith("test_")]
    src = [f for f in py if "tests/" not in f]
    sortie = T / "jeu" / sid
    sortie.mkdir(parents=True, exist_ok=True)
    (sortie / "diff_orig.patch").write_text(diff, encoding="utf-8")
    # spec
    tous = git(repo, "ls-tree", "-r", "--name-only", post_sha).splitlines()
    specs = [f for f in tous if f.startswith("_bmad-output") and f.endswith(".md")
             and fnmatch.fnmatch(Path(f).stem, motif)]
    spec_txt = ""
    if specs:
        brut = git(repo, "show", f"{post_sha}:{specs[0]}")
        spec_txt = decouper_spec(brut)
    (sortie / "spec.md").write_text(spec_txt, encoding="utf-8")
    # arbre fusionne
    arbre = T / "src" / sid
    if arbre.exists():
        shutil.rmtree(arbre, ignore_errors=True)
    arbre.mkdir(parents=True)
    tar = git(repo, "archive", "--format=tar", post_sha, "--", ".", *EXCLUS, binaire=True)
    with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
        for membre in tf:
            try:
                tf.extract(membre, arbre, filter="data")
            except Exception as exc:  # chemins trop longs ou liens
                print("  ignore", membre.name[:80], type(exc).__name__)
    meta = dict(id=sid, depot=repo, base=base_sha[:10], post=post_sha[:10], diff_caracteres=len(diff), spec_caracteres=len(spec_txt),
                spec_source=specs[0] if specs else None, src=src, tests=tests, lignes_ajoutees={k: sorted(set(v)) for k, v in ajoutees.items()})
    (sortie / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return meta


if __name__ == "__main__":
    ids = sys.argv[1:] or [s for v in SELECTION.values() for s in v]
    for sid in ids:
        m = construire(sid)
        print(sid, m["depot"], "diff", m["diff_caracteres"], "spec", m["spec_caracteres"], "src", len(m["src"]), "tests", len(m["tests"]), flush=True)
