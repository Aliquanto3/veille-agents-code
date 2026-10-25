"""Banc de rejeu : rejoue une story BMAD de référence dans un dossier jetable sans historique,
avec une session headless `claude -p`, puis mesure coût, tokens, tours, durée et réussite aux tests cachés.

Sous-commandes (toutes via `uv run --no-project python -I banc.py ...`) :
  reference STORY...        valide les tests cachés (commit final = tout passe ; base = échec) et fixe `total_ref`
  run STORY COND MODELE REP [--advisor opus]   une exécution
  lot PLAN.json [--max 2]   exécute un plan (liste d'objets run) avec au plus 2 sessions claude à la fois
  Tableaux : `python rapport.py t3|t6` (sans -I) ; plans dans plans/*.json ; données dans donnees/runs.jsonl.
  Option --consigne / champ "consigne" : ajoute la phrase de consulter le conseiller (bras b' de T6).

Isolation : `git archive <base> | tar -x`, `git init`, un commit ; aucun historique ; tests cachés retirés ;
`.claude/` du dépôt retiré ; CLAUDE.md = celui de la condition ; `~/.claude/CLAUDE.md` exclu par
`claudeMdExcludes` et réglages utilisateur exclus par `--setting-sources project,local`.
"""

import argparse
import concurrent.futures as cf
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

ICI = Path(__file__).resolve().parent
CORPUS = ICI / "corpus"
DONNEES = ICI / "donnees"
RUNS_JSONL = DONNEES / "runs.jsonl"
SCRATCH = Path(
    r"C:\Users\UTILIS~1\AppData\Local\Temp\claude\C--Users-Utilisateur-Documents-GitHub"
    r"\791fed94-a8b0-414e-8a6c-8fe967283749\scratchpad\rejeu"
)
DEPOT = Path(r"C:\Users\Utilisateur\Documents\GitHub\usine-migration-jira-demo")
CLAUDE = shutil.which("claude") or "claude"
UV = shutil.which("uv") or "uv"
MODELES = {"s": "claude-sonnet-5-5", "o": "claude-opus-5-5", "h": "claude-haiku-5-5"}
TIMEOUT_S = 25 * 60
BUDGET_USD = "15"
CONSIGNE_CONSEILLER = (
    "Tu disposes d'un conseiller (outil advisor) : consulte-le avant de commencer à coder, puis avant de déclarer la story terminée.\n\n"
)
PROMPT = "Implémente la story suivante, avec ses tests ; lance les tests ciblés avant de finir.\n\n"
OUTILS = "Read,Edit,Write,Glob,Grep,Bash"
AUTORISES = [
    "Read", "Edit", "Write", "Glob", "Grep",
    "Bash(uv run *)", "Bash(uv sync*)", "Bash(python -m pytest*)", "Bash(git status*)",
    "Bash(git diff*)", "Bash(git add*)", "Bash(git commit*)",
]  # fmt: skip
REGLAGES = {"claudeMdExcludes": ["**/Utilisateur/.claude/CLAUDE.md"]}
VERROU_ECRITURE = threading.Lock()
GIT_ID = ["-c", "user.name=banc", "-c", "user.email=banc@local", "-c", "core.longpaths=true"]


# ---------------------------------------------------------------- utilitaires
def effacer(chemin: Path) -> None:
    def _rw(fonction, p, _exc):  # type: ignore[no-untyped-def]
        os.chmod(p, stat.S_IWRITE)
        fonction(p)

    if chemin.exists():
        shutil.rmtree(chemin, onerror=_rw)


def lancer(cmd: list[str], cwd: Path, timeout: int, env: dict | None = None, entree: str | None = None):
    """Exécute une commande ; tue l'arbre de processus au dépassement. Rend (code, sortie, expire)."""
    p = subprocess.Popen(
        cmd, cwd=cwd, env=env, stdin=subprocess.PIPE if entree is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
    )  # fmt: skip
    try:
        sortie, erreur = p.communicate(entree, timeout=timeout)
        return p.returncode, sortie, erreur, False
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
        sortie, erreur = p.communicate()
        return -9, sortie or "", erreur or "", True


def env_enfant() -> dict:
    env = {
        k: v for k, v in os.environ.items()
        if not re.search(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", k, re.I)
    }  # fmt: skip
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def charger_meta(story: str) -> dict:
    return json.loads((CORPUS / story / "meta.json").read_text(encoding="utf-8"))


def dossier_run(story: str, cond: str, modele: str, advisor: str | None, rep: int, consigne: bool = False) -> tuple[str, Path]:
    rid = f"{story}-{cond}{modele}{'v' if advisor else ''}{'c' if consigne else ''}{rep}"
    return rid, Path(os.path.realpath(SCRATCH)) / rid


# ---------------------------------------------------------------- préparation
def preparer(story: str, commit: str, cible: Path, claude_md: Path | None, retirer_caches: bool) -> str:
    """Dossier jetable sans historique. Rend le sha du commit initial."""
    meta = charger_meta(story)
    effacer(cible)
    cible.mkdir(parents=True)
    arch = subprocess.Popen(["git", "-C", str(DEPOT), "archive", commit], stdout=subprocess.PIPE)
    subprocess.run(["tar", "-x", "-C", str(cible)], stdin=arch.stdout, check=True)
    arch.wait()
    effacer(cible / ".claude")
    for nom in ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md"):
        (cible / nom).unlink(missing_ok=True)
    if retirer_caches:
        for chemin in meta["tests_caches"]:
            (cible / chemin).unlink(missing_ok=True)
    if claude_md is not None:
        shutil.copyfile(claude_md, cible / "CLAUDE.md")
    subprocess.run(["git", "init", "-q"], cwd=cible, check=True)
    subprocess.run(["git", *GIT_ID, "add", "-A"], cwd=cible, check=True, capture_output=True)
    subprocess.run(["git", *GIT_ID, "commit", "-qm", "etat initial"], cwd=cible, check=True)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cible, capture_output=True, text=True).stdout.strip()
    r = subprocess.run([UV, "sync", "--frozen"], cwd=cible, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("uv sync a échoué : " + r.stderr[-500:])
    return sha


SONDE = """
import importlib, json, sys
res = []
for module, nom in json.loads(sys.argv[1]):
    try:
        m = importlib.import_module(module)
    except Exception:
        res.append([module, nom, "module"])
        continue
    if hasattr(m, nom):
        continue
    try:
        importlib.import_module(module + "." + nom)
    except Exception:
        res.append([module, nom, "nom"])
    else:
        continue
print(json.dumps(res))
"""


def noms_importes(fichiers: list[Path]) -> list[tuple[str, str]]:
    import ast

    vus: list[tuple[str, str]] = []
    for f in fichiers:
        if f.suffix != ".py":
            continue
        arbre = ast.parse(f.read_text(encoding="utf-8"))
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.ImportFrom) and noeud.module and noeud.module.split(".")[0] == "usine":
                vus += [(noeud.module, a.name) for a in noeud.names]
    return sorted(set(vus))


def interface_attendue(story: str, base: Path) -> str:
    """Noms `usine.*` importés par les tests cachés et absents à la base (liste imposée à l'agent)."""
    meta = charger_meta(story)
    fichiers = [CORPUS / story / "cache" / c for c in meta["tests_caches"]]
    paires = noms_importes(fichiers)
    sonde = base / "_sonde.py"
    sonde.write_text(SONDE, encoding="utf-8")
    code, sortie, erreur, _ = lancer(
        [UV, "run", "--no-sync", "python", "_sonde.py", json.dumps(paires)], base, 120, env=env_enfant()
    )
    sonde.unlink(missing_ok=True)
    manquants = json.loads(sortie.strip().splitlines()[-1])
    modules: dict[str, list[str]] = {}
    nouveaux: set[str] = set()
    for module, nom, genre in manquants:
        if genre == "module":
            nouveaux.add(module)
        modules.setdefault(module, []).append(nom)
    lignes = []
    for module, noms in sorted(modules.items()):
        noms = [n for n in noms if f"{module}.{n}" not in nouveaux]
        if not noms:
            continue
        etat = "nouveau module" if module in nouveaux else "module existant, noms à ajouter"
        lignes.append(f"- `{module}` ({etat}) : " + ", ".join(f"`{n}`" for n in sorted(noms)))
    return (
        "## Interface attendue par les tests d'acceptation\n\n"
        "Les tests d'acceptation de la story importent les noms suivants, qui doivent exister aux "
        "chemins indiqués (leur comportement est celui de la spécification ci-dessus) :\n\n"
        + "\n".join(lignes) + "\n"
    )


def copier_caches(story: str, cible: Path) -> list[str]:
    meta = charger_meta(story)
    for chemin in meta["tests_caches"]:
        src = CORPUS / story / "cache" / chemin
        (cible / chemin).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, cible / chemin)
    return meta["tests_caches"]


# ---------------------------------------------------------------- mesures
def compter_pytest(texte: str) -> dict:
    def n(mot: str) -> int:
        m = re.search(rf"(\d+) {mot}", texte)
        return int(m.group(1)) if m else 0

    return {
        "passed": n("passed"), "failed": n("failed"), "errors": n("errors?"), "skipped": n("skipped"),
        "collection_error": "error collecting" in texte.lower() or "ERROR collecting" in texte,
    }  # fmt: skip


def pytest(cible: Path, args: list[str], timeout: int = 900) -> dict:
    cmd = [UV, "run", "--no-sync", "pytest", "-q", "--tb=line", "-p", "no:cacheprovider", *args]
    t0 = time.time()
    code, sortie, erreur, expire = lancer(cmd, cible, timeout, env=env_enfant())
    res = compter_pytest(sortie)
    res.update({"code": code, "expire": expire, "duree_s": round(time.time() - t0, 1), "fin": sortie[-1500:]})
    return res


def metriques_transcription(chemin: Path | None) -> dict:
    """Appels, tokens par type et par modèle, outils appelés, contexte, depuis la transcription."""
    if chemin is None or not chemin.exists():
        return {}
    vus: dict[str, dict] = {}
    outils: dict[str, int] = {}
    blocs_vus: set = set()
    ordre: list[str] = []
    with chemin.open(encoding="utf-8") as f:
        for ligne in f:
            if '"type":"assistant"' not in ligne and '"type": "assistant"' not in ligne:
                continue
            try:
                o = json.loads(ligne)
            except ValueError:
                continue
            m = o.get("message") or {}
            mid = m.get("id") or o.get("uuid")
            u = m.get("usage") or {}
            if mid not in vus:
                ordre.append(mid)
            vus[mid] = {"model": m.get("model"), "usage": u, "content": []}
            for bloc in m.get("content") or []:
                if isinstance(bloc, dict) and bloc.get("type") in ("tool_use", "server_tool_use"):
                    ident = bloc.get("id") or id(bloc)
                    if ident not in blocs_vus:
                        blocs_vus.add(ident)
                        outils[bloc.get("name", "?")] = outils.get(bloc.get("name", "?"), 0) + 1
    par_modele: dict[str, dict] = {}
    ctx: list[int] = []
    for mid in ordre:
        e = vus[mid]
        u = e["usage"]
        d = par_modele.setdefault(
            e["model"] or "?", {"appels": 0, "input": 0, "cache_creation": 0, "cache_read": 0, "output": 0}
        )
        d["appels"] += 1
        d["input"] += u.get("input_tokens", 0) or 0
        d["cache_creation"] += u.get("cache_creation_input_tokens", 0) or 0
        d["cache_read"] += u.get("cache_read_input_tokens", 0) or 0
        d["output"] += u.get("output_tokens", 0) or 0
        ctx.append(
            (u.get("input_tokens", 0) or 0)
            + (u.get("cache_creation_input_tokens", 0) or 0)
            + (u.get("cache_read_input_tokens", 0) or 0)
        )
    return {
        "appels": len(ordre), "par_modele": par_modele, "outils": outils,
        "ctx_premier": ctx[0] if ctx else 0, "ctx_max": max(ctx) if ctx else 0,
    }  # fmt: skip


def trouver_transcription(session_id: str) -> Path | None:
    racine = Path.home() / ".claude" / "projects"
    for p in racine.glob(f"*/{session_id}.jsonl"):
        return p
    return None


# ---------------------------------------------------------------- exécution
def executer(story: str, cond: str, modele: str, rep: int, advisor: str | None = None, effort: str = "medium", consigne: bool = False) -> dict:
    meta = charger_meta(story)
    rid, cible = dossier_run(story, cond, modele, advisor, rep, consigne)
    claude_md = ICI / "claude_md" / ("actuel.md" if cond == "a" else "minimal.md")
    sha0 = preparer(story, meta["base"], cible, claude_md, retirer_caches=True)
    spec = (CORPUS / story / "spec.md").read_text(encoding="utf-8")
    spec += "\n" + (CORPUS / story / "interface.md").read_text(encoding="utf-8")
    session = str(uuid.uuid4())
    cmd = [
        CLAUDE, "-p", "--model", MODELES[modele], "--effort", effort, "--output-format", "json",
        "--permission-mode", "acceptEdits", "--allowedTools", *AUTORISES,
        "--tools", OUTILS, "--setting-sources", "project,local",
        "--settings", json.dumps(REGLAGES), "--session-id", session, "--max-budget-usd", BUDGET_USD,
    ]  # fmt: skip
    if advisor:
        cmd += ["--advisor", MODELES[advisor]]
    debut = datetime.now().astimezone()
    t0 = time.time()
    code, sortie, erreur, expire = lancer(cmd, cible, TIMEOUT_S, env=env_enfant(), entree=PROMPT + (CONSIGNE_CONSEILLER if consigne else "") + spec)
    duree = round(time.time() - t0, 1)
    (DONNEES / "brut").mkdir(parents=True, exist_ok=True)
    (DONNEES / "brut" / f"{rid}.json").write_text(sortie or "", encoding="utf-8")
    brut: dict = {}
    try:
        brut = json.loads(sortie)
    except ValueError:
        pass
    transcription = trouver_transcription(session)
    enreg: dict = {
        "id": rid, "story": story, "cond": cond, "modele": MODELES[modele],
        "advisor": MODELES[advisor] if advisor else None, "consigne": consigne, "rep": rep, "effort": effort,
        "debut": debut.isoformat(timespec="seconds"), "duree_mur_s": duree, "code": code, "expire": expire,
        "session_id": session, "base": meta["base"],
        "cout_usd": brut.get("total_cost_usd"), "tours": brut.get("num_turns"),
        "duree_ms": brut.get("duration_ms"), "duree_api_ms": brut.get("duration_api_ms"),
        "is_error": brut.get("is_error"), "subtype": brut.get("subtype"),
        "usage": brut.get("usage"), "modelUsage": brut.get("modelUsage"),
        "refus_permission": len(brut.get("permission_denials") or []),
        "resultat_debut": (brut.get("result") or "")[:400], "stderr_fin": erreur[-300:],
        "transcription": metriques_transcription(transcription),
    }  # fmt: skip
    # Mesures sur l'arbre de l'agent, avant d'y copier les tests cachés.
    subprocess.run(["git", *GIT_ID, "add", "-A"], cwd=cible, capture_output=True)
    num = subprocess.run(
        ["git", "diff", "--cached", "--numstat", sha0], cwd=cible, capture_output=True, text=True
    ).stdout.splitlines()
    ajoutes = supprimes = 0
    fichiers: list[str] = []
    for ligne in num:
        a, s, chemin = ligne.split("\t", 2)
        fichiers.append(chemin)
        ajoutes += int(a) if a.isdigit() else 0
        supprimes += int(s) if s.isdigit() else 0
    enreg["diff"] = {
        "fichiers": len(fichiers), "ajoutes": ajoutes, "supprimes": supprimes,
        "tests_ecrits": sum(1 for f in fichiers if f.startswith("tests/")),
        "src_ecrits": sum(1 for f in fichiers if f.startswith("src/")),
        "commits": int(subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=cible, capture_output=True, text=True).stdout.strip() or 1) - 1,
    }  # fmt: skip
    patch = subprocess.run(["git", "diff", "--cached", sha0], cwd=cible, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    (DONNEES / "patches").mkdir(parents=True, exist_ok=True)
    (DONNEES / "patches" / f"{rid}.diff").write_text(patch, encoding="utf-8", newline="\n")
    ruff = lancer([UV, "run", "--no-sync", "ruff", "check", "."], cible, 300, env=env_enfant())
    fmt = lancer([UV, "run", "--no-sync", "ruff", "format", "--check", "."], cible, 300, env=env_enfant())
    m = re.search(r"Found (\d+) error", ruff[1] + ruff[2])
    enreg["ruff_erreurs"] = int(m.group(1)) if m else (0 if ruff[0] == 0 else -1)
    m = re.search(r"(\d+) files? would be reformatted", fmt[1] + fmt[2])
    enreg["ruff_format_fichiers"] = int(m.group(1)) if m else (0 if fmt[0] == 0 else -1)
    # Tests cachés puis suite existante.
    caches = copier_caches(story, cible)
    cache_res = pytest(cible, caches, 600)
    enreg["cache"] = cache_res
    total = meta.get("total_ref")
    enreg["total_ref"] = total
    enreg["taux_cache"] = round(cache_res["passed"] / total, 4) if total else None
    suite = pytest(cible, ["--ignore=" + c for c in caches], 900)
    enreg["suite"] = suite
    with VERROU_ECRITURE:
        DONNEES.mkdir(parents=True, exist_ok=True)
        with RUNS_JSONL.open("a", encoding="utf-8") as f:
            f.write(json.dumps(enreg, ensure_ascii=False) + "\n")
    # La transcription est copiée hors du profil pour les mesures ultérieures.
    if transcription:
        (SCRATCH / "_transcriptions").mkdir(exist_ok=True)
        shutil.copyfile(transcription, SCRATCH / "_transcriptions" / f"{rid}.jsonl")
    return enreg


def deja_faits() -> set[str]:
    if not RUNS_JSONL.exists():
        return set()
    return {json.loads(ligne)["id"] for ligne in RUNS_JSONL.read_text(encoding="utf-8").splitlines() if ligne}


def resume(e: dict) -> str:
    return (
        f"{e['id']}: cout={e['cout_usd']} tours={e['tours']} mur={e['duree_mur_s']}s "
        f"cache={e['cache']['passed']}/{e['total_ref']} suite_ko={e['suite']['failed'] + e['suite']['errors']} "
        f"ruff={e['ruff_erreurs']} expire={e['expire']}"
    )


def lot(plan: Path, maximum: int) -> None:
    taches = json.loads(plan.read_text(encoding="utf-8"))
    faits = deja_faits()
    a_faire = []
    for t in taches:
        rid, _ = dossier_run(t["story"], t["cond"], t["modele"], t.get("advisor"), t["rep"], t.get("consigne", False))
        if rid not in faits:
            a_faire.append(t)
    print(f"{len(a_faire)} exécutions à faire sur {len(taches)}", flush=True)

    def une(t: dict) -> str:
        try:
            return resume(executer(t["story"], t["cond"], t["modele"], t["rep"], t.get("advisor"), consigne=t.get("consigne", False)))
        except Exception as exc:  # noqa: BLE001
            return f"{t}: ECHEC BANC {exc!r}"

    with cf.ThreadPoolExecutor(max_workers=maximum) as pool:
        for r in pool.map(une, a_faire):
            print(datetime.now().strftime("%H:%M:%S"), r, flush=True)


def reference(stories: list[str]) -> None:
    for story in stories:
        meta = charger_meta(story)
        cible = SCRATCH / f"ref-{story}"
        preparer(story, meta["commit"], cible, None, retirer_caches=False)
        res = pytest(cible, meta["tests_caches"], 600)
        # même dossier, avec le code de la base mais les tests cachés : doit échouer
        base = SCRATCH / f"base-{story}"
        preparer(story, meta["base"], base, None, retirer_caches=True)
        copier_caches(story, base)
        res_base = pytest(base, meta["tests_caches"], 600)
        (CORPUS / story / "interface.md").write_text(interface_attendue(story, base), encoding="utf-8", newline="\n")
        ok = res["failed"] == 0 and res["errors"] == 0 and res["passed"] > 0
        meta["total_ref"] = res["passed"] + res["failed"] + res["errors"] if ok else None
        meta["base_passed"] = res_base["passed"]
        (CORPUS / story / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        print(story, "référence", res["passed"], "ok" if ok else "ECHEC", "| base :", res_base["passed"], "passés,",
              res_base["failed"], "échecs,", res_base["errors"], "erreurs", flush=True)
        if not ok:
            print(res["fin"])


def main() -> int:
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("reference")
    r.add_argument("stories", nargs="+")
    u = sp.add_parser("run")
    u.add_argument("story")
    u.add_argument("cond", choices=["a", "b"])
    u.add_argument("modele", choices=list(MODELES))
    u.add_argument("rep", type=int)
    u.add_argument("--advisor", choices=list(MODELES))
    u.add_argument("--effort", default="medium")
    u.add_argument("--consigne", action="store_true", help="ajoute la consigne de consulter le conseiller")
    lt = sp.add_parser("lot")
    lt.add_argument("plan", type=Path)
    lt.add_argument("--max", type=int, default=2)
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    if a.cmd == "reference":
        reference(a.stories)
    elif a.cmd == "run":
        print(resume(executer(a.story, a.cond, a.modele, a.rep, a.advisor, a.effort, a.consigne)))
    else:
        lot(a.plan, a.max)
    return 0


if __name__ == "__main__":
    sys.exit(main())
