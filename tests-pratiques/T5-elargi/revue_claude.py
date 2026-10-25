r"""T5 elargi : revue par les relecteurs Claude (Haiku avec second-avis.md, Opus avec reviewer.md), via `claude -p` (abonnement).

usage : revue_claude.py <haiku|opus> [--stories id1,id2] [--jobs 2]
Chaque relecteur travaille dans T:\rev\<id> (arbre seme, sans historique ni .git ni _bmad-output) avec les seuls outils Read, Grep, Glob.
La consigne est celle de l'agent d'agent-cost-kit (corps du fichier, sans l'en-tete), plus un paragraphe d'adaptation (lecture seule).
Le diff et la spec sont dans le message, comme pour les relecteurs GPT. Aucune cle n'est lue ni ecrite.
Sortie : T:\rep\<modele>\<id>.json (reponse brute JSON de `claude -p`, avec cout et duree).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

T = Path("T:/")
AGENTS = Path(r"C:\Users\Utilisateur\Documents\GitHub\agent-cost-kit\agents")
FICHIER = {"haiku": "second-avis.md", "opus": "reviewer.md"}
MODELE = {"haiku": "haiku", "opus": "opus"}

ADAPTATION = """

## Adaptation au banc d'essai (mesure du rappel sur defauts semes)
- Tu es en LECTURE SEULE et tu ne disposes que des outils Read, Grep et Glob : ni Bash, ni git, ni execution de tests, ni modification de fichier. Les consignes ci-dessus qui parlent de rebase, de SHA, de CI, de `git`, d'execution, de correction ou de section `## Revue` sont sans objet : signale, ne corrige pas, n'ecris aucune section de revue. Pour la mesure d'ecart de base, ecris seulement « base : sans objet ».
- Le depot, dans l'etat fusionne de la story, est le repertoire de travail courant. Le diff de la story et sa spec sont dans le message. Il n'existe aucun autre historique : ne cherche rien hors du repertoire courant.
- Rapport final : une ligne par constat, sans limite de longueur de rapport, au format `etiquette | severite | chemin/relatif.py:ligne | mecanisme et preuve par lecture | certain ou probable`, ou etiquette vaut Important, Nit ou Pre-existing et severite high, medium ou low. Le chemin est relatif a la racine du depot courant. Un constat par ligne, jamais deux defauts sur une meme ligne.
- Ne signale que des defauts que tu as verifies par lecture du code ; si tu ne trouves rien d'Important, dis-le en une ligne.
"""


def corps(agent: str) -> str:
    texte = (AGENTS / FICHIER[agent]).read_text(encoding="utf-8")
    m = re.match(r"^---\n.*?\n---\n(.*)$", texte, re.S)
    return (m.group(1) if m else texte).strip()


def message(sid: str) -> str:
    spec = (T / "jeu" / sid / "spec.md").read_text(encoding="utf-8")
    diff = (T / "sem" / sid / "diff.patch").read_text(encoding="utf-8")
    return ("## Spec de la story (sections ecrites avant le developpement)\n\n" + spec
            + "\n\n## Diff fusionne de la story, correctifs de revue compris (le depot du repertoire courant est dans l'etat apres fusion)\n\n```diff\n"
            + diff + "\n```\n\nFais ta revue de cette story.\n")


def lancer(agent: str, sid: str, verrou: threading.Semaphore, dossier: Path, essai_max: int = 2) -> str:
    sortie = dossier / f"{sid}.json"
    if sortie.exists():
        return f"{agent} {sid} : deja fait"
    cwd = T / "rev" / sid
    cmd = ["claude", "-p", "--model", MODELE[agent], "--effort", "medium", "--output-format", "json",
           "--safe-mode", "--restricted", "--tools", "Read,Grep,Glob", "--allowedTools", "Read,Grep,Glob",
           "--strict-mcp-config", "--no-session-persistence", "--permission-mode", "dontAsk",
           "--append-system-prompt", corps(agent) + ADAPTATION]
    env = dict(os.environ)
    for k in list(env):
        if k.upper().endswith(("API_KEY", "_TOKEN", "SECRET")):
            env.pop(k)
    with verrou:
        for essai in range(1, essai_max + 1):
            t0 = time.time()
            try:
                p = subprocess.run(cmd, cwd=cwd, env=env, input=message(sid), capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=1500)
            except subprocess.TimeoutExpired:
                if essai == essai_max:
                    sortie.with_suffix(".erreur.txt").write_text("timeout 1500 s", encoding="utf-8")
                    return f"{agent} {sid} : TIMEOUT"
                continue
            duree = time.time() - t0
            try:
                brut = json.loads(p.stdout)
            except json.JSONDecodeError:
                brut = None
            if brut and not brut.get("is_error") and (brut.get("result") or "").strip():
                brut["_duree_s"] = round(duree, 1)
                sortie.write_text(json.dumps(brut, ensure_ascii=False, indent=1), encoding="utf-8")
                u = brut.get("usage", {})
                return (f"{agent} {sid} : {duree:.0f} s, {brut.get('num_turns')} tours, {brut.get('total_cost_usd')} $ (equivalent API), "
                        f"sortie {len(brut.get('result', ''))} car.")
            if essai == essai_max:
                sortie.with_suffix(".erreur.txt").write_text((p.stdout or "")[-1500:] + "\n--- stderr ---\n" + (p.stderr or "")[-1500:], encoding="utf-8")
                return f"{agent} {sid} : ERREUR (voir .erreur.txt)"
    return f"{agent} {sid} : ?"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("agent", choices=["haiku", "opus"])
    ap.add_argument("--stories", default="")
    ap.add_argument("--jobs", type=int, default=2)
    a = ap.parse_args()
    ids = [s for s in a.stories.split(",") if s] or sorted(d.name for d in (T / "sem").iterdir() if (d / "verite.json").exists())
    dossier = T / "rep" / a.agent
    dossier.mkdir(parents=True, exist_ok=True)
    verrou = threading.Semaphore(a.jobs)
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for r in ex.map(lambda s: lancer(a.agent, s, verrou, dossier), ids):
            print(r, flush=True)


if __name__ == "__main__":
    main()
