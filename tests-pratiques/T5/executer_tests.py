"""T5 : execute, un par un, les tests proposes par les modeles pour leurs constats Important.

Les tests sont du code NON FIABLE. Garde-fous :
- filtre statique (reseau, sous-processus, suppression de fichiers, ctypes, eval/exec, ecriture hors tmp_path) : un test refuse n'est pas execute ;
- worktree jetable du depot a l'etat fusionne (git worktree add --detach), un par story, supprime en fin de run ;
- environnement minimal : aucun secret transmis (ni la cle OpenRouter, ni JIRA_*, ni cles LLM) ;
- pytest -q --tb=line -x sur le seul fichier de test, delai 60 s, jamais la suite complete.

Usage : uv run --no-project python executer_tests.py --lister            (affiche les tests, filtre statique compris)
        uv run --no-project python executer_tests.py --executer           (execute ceux que le filtre accepte)
        uv run --no-project python executer_tests.py --nettoyer           (supprime les worktrees)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).parent
REPO = Path.home() / "Documents" / "GitHub" / "usine-migration-jira-demo"
PYTHON = REPO / ".venv" / "Scripts" / "python.exe"
WORKTREES = ICI / "worktrees"
EXTRAIT = ICI / "tests_extraits"
RESULTATS = ICI / "execution.json"
DELAI = 60

INTERDITS = [
    (r"\b(import|from)\s+(socket|requests|urllib|http|httpx|aiohttp|ftplib|smtplib|telnetlib|websockets?)\b", "reseau"),
    (r"\b(import|from)\s+(subprocess|multiprocessing|pty|ctypes|winreg)\b", "sous-processus ou systeme"),
    (r"\bos\.(system|popen|spawn\w*|exec\w*|startfile|remove|unlink|rmdir|removedirs|rename|replace|kill)\b", "systeme ou suppression"),
    (r"\bshutil\.(rmtree|move|copytree)\b", "suppression de fichiers"),
    (r"\.(unlink|rmdir)\s*\(", "suppression de fichiers"),
    (r"\bPopen\s*\(|\bsubprocess\b", "sous-processus"),
    (r"\b(eval|exec|compile|__import__)\s*\(", "execution dynamique"),
    (r"\bimportlib\.(import_module|util)\b.*\b(http|socket)\b", "reseau"),
]
ENV_SURS = ("SystemRoot", "SYSTEMROOT", "PATH", "PATHEXT", "TEMP", "TMP", "COMSPEC", "WINDIR", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE")


def extraire_json(texte: str) -> dict | None:
    t = texte.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try:
        return json.loads(t)
    except ValueError:
        i, j = t.find("{"), t.rfind("}")
        if i >= 0 and j > i:
            try:
                return json.loads(t[i : j + 1])
            except ValueError:
                pass
    # sortie tronquee (finish_reason length) : on recupere les constats complets deja ecrits
    k = t.find("[")
    if k < 0:
        return None
    dec, pos, constats = json.JSONDecoder(), k + 1, []
    while pos < len(t):
        suivant = t.find("{", pos)
        if suivant < 0:
            break
        try:
            obj, pos = dec.raw_decode(t, suivant)
        except ValueError:
            break
        if isinstance(obj, dict):
            constats.append(obj)
    return {"constats": constats, "_tronque": True} if constats else None


DOSSIERS = [("reponses", "r1"), ("reponses_run2", "r2")]


def charger_constats() -> list[dict]:
    """Constats de toutes les passes (r1 : passe officielle ; r2 : repetition luna et sol)."""
    constats = []
    for dossier, run in DOSSIERS:
        for f in sorted((ICI / dossier).glob("*.json")) if (ICI / dossier).exists() else []:
            r = json.loads(f.read_text(encoding="utf-8"))
            d = extraire_json(r["contenu"])
            if d is None or not isinstance(d.get("constats"), list):
                constats.append({"modele": r["modele"], "story": r["story"], "run": run, "id": "PARSE", "severite": "ERREUR_FORMAT"})
                continue
            for k, c in enumerate(d["constats"]):
                if not isinstance(c, dict):
                    continue
                constats.append({
                    "modele": r["modele"], "story": r["story"], "run": run, "id": str(c.get("id") or f"C{k+1}"),
                    "fichier": c.get("fichier"), "ligne": c.get("ligne"), "severite": c.get("severite"),
                    "description": c.get("description"), "test": c.get("test_pytest"), "tronque": bool(d.get("_tronque")),
                })
    return constats


def filtre_statique(source: str) -> str | None:
    for motif, raison in INTERDITS:
        if re.search(motif, source):
            return raison
    for m in re.finditer(r"\bopen\s*\(([^)]*)\)", source):
        args = m.group(1)
        if re.search(r"""['"][^'"]*[wax+][^'"]*['"]\s*[,)]?""", args.split(",", 1)[-1] if "," in args else "") and "tmp_path" not in args:
            return "ecriture hors tmp_path"
    return None


def cle_test(c: dict) -> str:
    base = f"{c['modele'].replace('/', '__')}__{c['story']}__{c['id']}"
    return base if c.get("run", "r1") == "r1" else f"{base}__{c['run']}"


def git(*args: str, cwd: Path = REPO) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")


def worktree_pour(story: dict) -> Path:
    chemin = WORKTREES / story["id"]
    if not chemin.exists():
        WORKTREES.mkdir(exist_ok=True)
        r = git("worktree", "add", "--detach", str(chemin), story["etat"])
        if r.returncode:
            raise SystemExit(r.stderr)
    return chemin


def executer(c: dict, wt: Path, source: str) -> dict:
    nom = "test_t5_" + re.sub(r"\W", "_", cle_test(c)) + ".py"
    cible = wt / "tests" / "unit" / nom
    cible.write_text(source, encoding="utf-8", newline="\n")
    env = {k: v for k, v in os.environ.items() if k in ENV_SURS}
    env.update({"PYTHONPATH": f"{wt / 'src'}{os.pathsep}{wt}", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "NO_COLOR": "1", "COLUMNS": "200"})
    try:
        r = subprocess.run(
            [str(PYTHON), "-m", "pytest", "-q", "--tb=line", "-x", "-p", "no:cacheprovider", str(cible)],
            cwd=wt, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=DELAI,
        )
        sortie = (r.stdout + "\n" + r.stderr).strip()
        rc = r.returncode
    except subprocess.TimeoutExpired as exc:
        sortie, rc = f"TIMEOUT {DELAI}s {exc.stdout or ''}", 124
    finally:
        cible.unlink(missing_ok=True)
    return {"rc": rc, "sortie": sortie[-1500:], "etat": classer(rc, sortie)}


def classer(rc: int, sortie: str) -> str:
    if rc == 124:
        return "delai"
    if rc == 0:
        return "passe"
    if rc == 1:
        # echec d'un test : assertion (demonstration du defaut) ou erreur de l'API inventee
        ligne = next((l for l in sortie.splitlines() if re.search(r"\.py:\d+: ", l)), "")
        if re.search(r"AssertionError|Failed:", ligne) or "assert " in ligne:
            return "echoue_assertion"
        return "echoue_exception"
    return "ne_s_execute_pas"  # rc 2 : erreur de collecte ; 3, 4 : usage ; 5 : aucun test


def rejouer_sur_tete() -> None:
    """Rejoue les tests Important deja executes sur la tete de main : un test qui passe la montre un defaut corrige apres coup."""
    sortie = ICI / "execution_tete.json"
    deja = json.loads(sortie.read_text(encoding="utf-8")) if sortie.exists() else {}
    execution = json.loads(RESULTATS.read_text(encoding="utf-8"))
    tete = git("rev-parse", "HEAD").stdout.strip()
    wt = worktree_pour({"id": "TETE", "etat": tete})
    for c in charger_constats():
        k = cle_test(c)
        if c.get("severite") != "Important" or k in deja or execution.get(k, {}).get("etat") not in ("echoue_assertion", "echoue_exception"):
            continue
        res = executer(c, wt, c["test"])
        res["tete"] = tete
        deja[k] = res
        print(k, res["etat"], flush=True)
        sortie.write_text(json.dumps(deja, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--lister", action="store_true")
    g.add_argument("--executer", action="store_true")
    g.add_argument("--nettoyer", action="store_true")
    g.add_argument("--tete", action="store_true", help="rejoue les tests sur la tete de main (defauts corriges plus tard ?)")
    o = ap.parse_args()
    if o.tete:
        rejouer_sur_tete()
        return
    if o.nettoyer:
        for w in WORKTREES.glob("*") if WORKTREES.exists() else []:
            print(git("worktree", "remove", "--force", str(w)).stderr.strip() or f"supprime {w.name}")
        git("worktree", "prune")
        return
    stories = {s["id"]: s for s in json.loads((ICI / "jeu" / "jeu.json").read_text(encoding="utf-8"))}
    constats = [c for c in charger_constats() if c.get("severite") == "Important"]
    EXTRAIT.mkdir(exist_ok=True)
    resultats = json.loads(RESULTATS.read_text(encoding="utf-8")) if RESULTATS.exists() else {}
    for c in constats:
        k = cle_test(c)
        src = c.get("test")
        if not isinstance(src, str) or not src.strip():
            res = {"etat": "sans_test"}
        else:
            (EXTRAIT / f"{k}.py").write_text(src, encoding="utf-8", newline="\n")
            refus = filtre_statique(src)
            if refus:
                res = {"etat": "refuse", "raison": refus}
            elif o.executer:
                if k in resultats and resultats[k].get("etat") not in (None,):
                    continue
                res = executer(c, worktree_pour(stories[c["story"]]), src)
            else:
                res = {"etat": "a_executer"}
        if o.lister:
            print(f"{k}: {res['etat']} {res.get('raison', '')}")
        else:
            resultats[k] = res
            print(f"{k}: {res['etat']}", flush=True)
            RESULTATS.write_text(json.dumps(resultats, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
