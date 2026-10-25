"""T10 : description des 5 stories et des chemins (disque virtuel T: sur le scratchpad, chemins courts)."""
from __future__ import annotations

import os
from pathlib import Path

ICI = Path(__file__).parent
BRUTS = ICI / "resultats-bruts"
RACINE_T = Path("T:/")          # `subst T:` sur le dossier jetable t10 du scratchpad
GITHUB = Path(os.environ.get("T10_GITHUB", Path.home() / "Documents" / "GitHub"))
DEPOTS = {"wd": GITHUB / "wavedevsecops", "us": GITHUB / "usine-migration-jira-demo"}
UI = "src/usine/ui"
UT = "tests/unit/ui"
WD = "src/wavedevsecops"

STORIES = {
    "wd-5-9": dict(court="wd59", depot="wd", commit="66cefe8", spec="_bmad-output/implementation-artifacts/5-9-*.md",
                   sources=[f"{WD}/web/blockers.py", f"{WD}/scenarios/model.py", f"{WD}/scenarios/loader.py"],
                   tests=["tests/test_blockers.py"], dossier_tests="tests"),
    "wd-8-4": dict(court="wd84", depot="wd", commit="e5247df", spec="_bmad-output/implementation-artifacts/8-4-*.md",
                   sources=[f"{WD}/ci/findings.py", f"{WD}/scenarios/ops/replace_in_file.py",
                            f"{WD}/toolrun/__init__.py", f"{WD}/ci/__init__.py"],
                   tests=["tests/test_quality_gate.py"], dossier_tests="tests"),
    "us-7-14": dict(court="u14", depot="us", commit="23c1fd3", spec="_bmad-output/implementation-artifacts/spec-7-14-*.md",
                    sources=[f"{UI}/carte.py", f"{UI}/detail.py", f"{UI}/vues.py", f"{UI}/serveur.py", f"{UI}/cli.py", f"{UI}/liens.py"],
                    tests=[f"{UT}/test_vues_ecrans.py", f"{UT}/test_serveur.py", "tests/contrat/consultation/test_contrat.py"],
                    dossier_tests=UT),
    "us-7-15": dict(court="u15", depot="us", commit="c86b2f7", spec="_bmad-output/implementation-artifacts/spec-7-15-*.md",
                    sources=[f"{UI}/chaine.py", f"{UI}/vues.py", f"{UI}/serveur.py", f"{UI}/app.py", f"{UI}/textes.py"],
                    tests=[f"{UT}/test_chaine.py", f"{UT}/test_serveur.py", f"{UT}/test_vues_ecrans.py", f"{UT}/test_cli.py"],
                    dossier_tests=UT),
    "us-7-16": dict(court="u16", depot="us", commit="cf54141", spec="_bmad-output/implementation-artifacts/spec-7-16-*.md",
                    sources=[f"{UI}/ecrans.py", f"{UI}/outillage.py", f"{UI}/pseudonymisation.py", f"{UI}/vues.py", f"{UI}/serveur.py", f"{UI}/cli.py"],
                    tests=[f"{UT}/test_ecrans_web.py", f"{UT}/test_vues_ecrans.py", f"{UT}/test_serveur.py", f"{UT}/test_chaine.py"],
                    dossier_tests=UT),
}

SPARSE = {
    "wd": ["/pyproject.toml", "/uv.lock", "/.python-version", "/tools.toml", "/LICENSE", "/NOTICE", "/src/", "/tests/",
           "/scripts/", "/content/", "/.github/", "/docs/*.md"],
    "us": ["/pyproject.toml", "/uv.lock", "/.python-version", "/README.md", "/SPEC-*.md", "/src/", "/tests/", "/config/",
           "/demo/", "/donnees/", "/evals/", "/evaluation/", "/gabarits/", "/outils/", "/docs/*.md"],
}


def arbre(story: str, bras: str, essai: int) -> Path:
    return RACINE_T / "s" / f"{STORIES[story]['court']}-{bras}{essai}"


def venv(story: str, bras: str) -> Path:
    return RACINE_T / "v" / f"{STORIES[story]['depot']}-{bras}"


def env_pour(story: str, bras: str, essai: int) -> dict:
    """Environnement d'un processus de test ou d'agent : venv du bras en tete du PATH, PYTHONPATH sur l'arbre."""
    a = arbre(story, bras, essai)
    e = dict(os.environ)
    for k in list(e):
        if k.upper().endswith(("API_KEY", "_TOKEN", "SECRET")):
            e.pop(k)
    e.pop("VIRTUAL_ENV", None)
    e["PYTHONPATH"] = os.pathsep.join([str(a / "src"), str(a)])
    e["PATH"] = str(venv(story, bras) / "Scripts") + os.pathsep + e["PATH"]
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    e["PYTHONUTF8"] = "1"
    return e


def python(story: str, bras: str) -> str:
    return str(venv(story, bras) / "Scripts" / "python.exe")
