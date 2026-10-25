"""Constantes et utilitaires communs de T12 (verification navigateur d'une story front)."""
import os, re, shutil, stat, subprocess, time, json, urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
RACINE_TESTS = ICI.parent
SCRATCH = Path(r"C:\Users\Utilisateur\AppData\Local\Temp\claude\C--Users-Utilisateur-Documents-GitHub\791fed94-a8b0-414e-8a6c-8fe967283749\scratchpad\t12")
T7 = SCRATCH.parent / "t7"
CHROMIUM = T7 / "tools" / "browsers" / "chromium-1248" / "chrome-win64" / "chrome.exe"
MCP_CLI = T7 / "tools" / "navigateurs" / "playwright-mcp" / "node_modules" / "@playwright" / "mcp" / "cli.js"
DEPOT = Path(r"C:\Users\Utilisateur\Documents\GitHub\usine-migration-jira-demo")
UV = shutil.which("uv") or "uv"
CLAUDE = shutil.which("claude") or "claude"
GIT_ID = ["-c", "user.name=banc", "-c", "user.email=banc@local", "-c", "core.longpaths=true"]

# Stories : id -> commit fusionne (apres la revue) et port
STORIES = {
    "s713": {"story": "7.13", "commit": "bc8ab21", "titre": "Socle web FastAPI et cadre commun"},
    "s714": {"story": "7.14", "commit": "23c1fd3", "titre": "Carte meteo, detail d'une Entite et livrables"},
    "s715": {"story": "7.15", "commit": "c86b2f7", "titre": "Lancement de la Chaine et bouton de mode"},
    "s716": {"story": "7.16", "commit": "cf54141", "titre": "Agent, Avant / apres, Pseudonymisation et Outillage"},
}
PORT = 8765


def effacer(chemin: Path) -> None:
    def _rw(f, p, _e):
        os.chmod(p, stat.S_IWRITE); f(p)
    if chemin.exists():
        shutil.rmtree(chemin, onerror=_rw)


def env_enfant() -> dict:
    env = {k: v for k, v in os.environ.items() if not re.search(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", k, re.I)}
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["NO_UPDATE_NOTIFIER"] = "1"
    return env


def attendre(url, t=60):
    t0 = time.time()
    while time.time() - t0 < t:
        try:
            urllib.request.urlopen(url, timeout=2).read()
            return True
        except Exception:
            time.sleep(0.5)
    return False
