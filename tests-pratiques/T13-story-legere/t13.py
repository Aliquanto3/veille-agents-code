"""T13 : story légère (spec courte façon OpenSpec) contre story BMAD complète, sur 10 petites stories.

Étend le banc de rejeu `../banc-rejeu/banc.py` (mêmes réglages d'isolation, même dev-story Sonnet) à plusieurs dépôts
et ajoute l'étape de cadrage (Opus). Sous-commandes (toutes via `uv run --no-project python -I t13.py ...`) :
  extraire ID...        construit corpus/<id>/ (meta, tests cachés, entrée epics.md, spec d'origine nettoyée)
  reference ID...       valide les tests cachés (commit = tout passe ; base = échec), écrit interface.md et total_ref
  cadrer ID ARM REP     une étape de cadrage (ARM = A bmad complet, B voie légère) : écrit donnees/specs/<id>-<ARM><REP>.md
  dev ID ARM REP        une étape de développement (ARM = A, B après cadrage, C spec d'origine)
  lot PLAN.json [--max 2]   exécute un plan ; au plus 2 sessions claude à la fois, une seule suite de tests à la fois
"""

import argparse
import concurrent.futures as cf
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "banc-rejeu"))
import banc  # noqa: E402  (fonctions de mesure et d'isolation partagées avec les autres tests)

CORPUS = ICI / "corpus"
DONNEES = ICI / "donnees"
RUNS = DONNEES / "runs.jsonl"
CADRAGES = DONNEES / "cadrages.jsonl"
GITHUB = Path(r"C:\Users\Utilisateur\Documents\GitHub")
SCRATCH = Path(
    r"C:\Users\Utilisateur\AppData\Local\Temp\claude\C--Users-Utilisateur-Documents-GitHub"
    r"\791fed94-a8b0-414e-8a6c-8fe967283749\scratchpad\t13\run"
)
CLAUDE = banc.CLAUDE
UV = banc.UV
SONNET, OPUS = "claude-sonnet-5-5", "claude-opus-5-5"
GIT_ID = banc.GIT_ID
LOCK_TESTS = threading.Lock()  # une seule suite de tests (ou uv sync) à la fois côté banc
LOCK_ECRITURE = threading.Lock()
PROMPT_DEV = banc.PROMPT
OUTILS_DEV = banc.OUTILS
AUTORISES = banc.AUTORISES
REGLAGES = banc.REGLAGES
OUTILS_CADRAGE = "Read,Glob,Grep"
AUTORISES_CADRAGE = ["Read", "Glob", "Grep"]
SECTIONS_GARDEES = {
    "intent", "boundaries & constraints", "i/o & edge-case matrix", "code map", "tasks & acceptance",
    "design notes", "acceptance", "tâches et critères", "objectif", "critères d'acceptation et preuves",
    "contrat partagé", "fichiers",
}  # fmt: skip


def depot(meta: dict) -> Path:
    return GITHUB / meta["repo"]


def git(meta: dict, *args: str, binaire: bool = False):
    r = subprocess.run(["git", "-C", str(depot(meta)), *args], capture_output=True)
    return r.stdout if binaire else r.stdout.decode("utf-8", errors="replace")


def meta_de(story: str) -> dict:
    return json.loads((CORPUS / story / "meta.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ extraction
def section_epics(texte: str, label: str) -> str:
    lignes = texte.splitlines()
    debut = next((i for i, l in enumerate(lignes) if re.match(rf"^###\s+Story\s+{re.escape(label)}\s*[:\s]", l)), None)
    if debut is None:
        raise RuntimeError(f"story {label} introuvable dans epics.md")
    fin = len(lignes)
    for i in range(debut + 1, len(lignes)):
        if re.match(r"^#{1,3}\s", lignes[i]):
            fin = i
            break
    return "\n".join(lignes[debut:fin]).strip() + "\n"


def nettoyer_spec(texte: str, repo: str) -> str:
    """Garde les sections de conception de la spec d'origine, retire frontmatter et tout ce qu'écrivent dev et revue."""
    texte = re.sub(r"\A---\n.*?\n---\n", "", texte, flags=re.S)
    parties = re.split(r"(?m)^(?=## )", texte)
    gardees = [parties[0].strip()] if parties[0].strip() else []
    for p in parties[1:]:
        titre = p.splitlines()[0][3:].strip().lower()
        if titre in SECTIONS_GARDEES:
            gardees.append(p.strip())
    out = "\n\n".join(gardees) + "\n"
    out = re.sub(r"<!--.*?-->", "", out, flags=re.S)
    if repo == "wavelibrarian":  # les tâches citent les tests écrits ensuite : on retire ces renvois
        out = re.sub(r"\s*:\s*`test_[^`]+`(?:,\s*`test_[^`]+`)*", "", out)
        out = "\n".join(l for l in out.splitlines() if not re.match(r"^\s*-\s*Tests?\s*:", l)) + "\n"
    return out


def extraire(entree: dict) -> None:
    story = entree["id"]
    meta = {k: entree[k] for k in ("id", "repo", "pkg", "label")}
    meta["commit"] = git(entree, "rev-parse", entree["commit"]).strip()
    meta["base"] = git(entree, "rev-parse", meta["commit"] + "^").strip()
    statuts = [l.split("\t") for l in git(meta, "diff-tree", "--no-commit-id", "--name-status", "-r", meta["commit"]).splitlines()]
    meta["fichiers_commit"] = [s[-1] for s in statuts]
    caches = [s[1] for s in statuts if s[0] == "A" and re.match(r"^tests?/", s[1]) and "__pycache__" not in s[1]]
    meta["tests_caches"] = caches
    meta["tests_executes"] = [c for c in caches if re.search(r"(^|/)test_[^/]*\.py$", c)]
    # Fichiers d'appui des tests (conftest, fixtures, aides) modifiés par le commit : remis dans leur version finale à la mesure.
    meta["tests_appui"] = [
        s[1] for s in statuts
        if s[0] == "M" and re.match(r"^tests?/", s[1]) and s[1].endswith(".py") and not re.search(r"(^|/)test_[^/]*\.py$", s[1])
    ]  # fmt: skip
    spec = [s[1] for s in statuts if "implementation-artifacts" in s[1] and entree["spec"] in s[1].split("/")[-1]]
    meta["spec_origine"] = spec[0]
    meta["src_modifies"] = [
        s[1] for s in statuts
        if not re.match(r"^(tests?/|_bmad|docs/)", s[1]) and not s[1].endswith(".md")
    ]  # fmt: skip
    dossier = CORPUS / story
    banc.effacer(dossier)
    (dossier / "cache").mkdir(parents=True)
    for c in caches + meta["tests_appui"]:
        cible = dossier / "cache" / c
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_bytes(git(meta, "show", f"{meta['commit']}:{c}", binaire=True))
    ep = [l for l in git(meta, "ls-tree", "-r", "--name-only", meta["base"]).splitlines() if l.endswith("planning-artifacts/epics.md")][0]
    (dossier / "epics.md").write_text(section_epics(git(meta, "show", f"{meta['base']}:{ep}"), entree["label"]), encoding="utf-8", newline="\n")
    brut = git(meta, "show", f"{meta['commit']}:{spec[0]}")
    (dossier / "spec_brute.md").write_text(brut, encoding="utf-8", newline="\n")
    (dossier / "spec.md").write_text(nettoyer_spec(brut, meta["repo"]), encoding="utf-8", newline="\n")
    meta["c_disponible"] = entree.get("c_disponible", True)
    (dossier / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(story, "tests cachés :", caches, "| src :", meta["src_modifies"])


# ------------------------------------------------------------------ préparation et référence
def preparer(story: str, commit: str, cible: Path, retirer_caches: bool, sync: bool = True) -> str:
    meta = meta_de(story)
    banc.effacer(cible)
    cible.mkdir(parents=True)
    arch = subprocess.Popen(["git", "-C", str(depot(meta)), "archive", commit], stdout=subprocess.PIPE)
    subprocess.run(["tar", "-x", "-C", str(cible)], stdin=arch.stdout, check=True)
    arch.wait()
    banc.effacer(cible / ".claude")
    for nom in ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md"):
        (cible / nom).unlink(missing_ok=True)
    if retirer_caches:
        for chemin in meta["tests_caches"]:
            (cible / chemin).unlink(missing_ok=True)
    claude_md = ICI / "claude_md" / f"{meta['repo']}.md"
    shutil.copyfile(claude_md, cible / "CLAUDE.md")
    subprocess.run(["git", "init", "-q"], cwd=cible, check=True)
    subprocess.run(["git", *GIT_ID, "add", "-A"], cwd=cible, check=True, capture_output=True)
    subprocess.run(["git", *GIT_ID, "commit", "-qm", "etat initial"], cwd=cible, check=True)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cible, capture_output=True, text=True).stdout.strip()
    if sync:
        with LOCK_TESTS:
            r = subprocess.run([UV, "sync", "--frozen"], cwd=cible, capture_output=True, text=True, env=banc.env_enfant())
        if r.returncode != 0:
            raise RuntimeError("uv sync a échoué : " + r.stderr[-500:])
    return sha


def copier_caches(story: str, cible: Path) -> list[str]:
    meta = meta_de(story)
    for chemin in meta["tests_caches"] + meta.get("tests_appui", []):
        (cible / chemin).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(CORPUS / story / "cache" / chemin, cible / chemin)
    return meta["tests_executes"]


def noms_importes(fichiers: list[Path], pkg: str) -> list[tuple[str, str]]:
    import ast

    vus: list[tuple[str, str]] = []
    for f in fichiers:
        if f.suffix != ".py":
            continue
        try:
            arbre = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.ImportFrom) and noeud.module and noeud.module.split(".")[0] == pkg and not noeud.level:
                vus += [(noeud.module, a.name) for a in noeud.names]
    return sorted(set(vus))


def interface_attendue(story: str, base: Path) -> str:
    meta = meta_de(story)
    fichiers = [CORPUS / story / "cache" / c for c in meta["tests_caches"] + meta.get("tests_appui", [])]
    paires = noms_importes(fichiers, meta["pkg"])
    sonde = base / "_sonde.py"
    sonde.write_text(banc.SONDE, encoding="utf-8")
    code, sortie, erreur, _ = banc.lancer([UV, "run", "--no-sync", "python", "_sonde.py", json.dumps(paires)], base, 180, env=banc.env_enfant())
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
    entete = (
        "## Interface attendue par les tests d'acceptation\n\n"
        "Les tests d'acceptation de la story importent les noms suivants, qui doivent exister aux "
        "chemins indiqués (leur comportement est celui de la spécification ci-dessus) :\n\n"
    )
    if not lignes:
        return "## Interface attendue par les tests d'acceptation\n\nLes tests d'acceptation n'importent aucun nom nouveau du paquet : aucune interface imposée.\n"
    return entete + "\n".join(lignes) + "\n"


def pytest(cible: Path, args: list[str], timeout: int = 600) -> dict:
    cmd = [UV, "run", "--no-sync", "pytest", "-q", "--tb=line", "-p", "no:cacheprovider", *args]
    t0 = time.time()
    code, sortie, erreur, expire = banc.lancer(cmd, cible, timeout, env=banc.env_enfant())
    res = banc.compter_pytest(sortie)
    res.update({"code": code, "expire": expire, "duree_s": round(time.time() - t0, 1), "fin": sortie[-1200:]})
    return res


def reference(stories: list[str]) -> None:
    for story in stories:
        meta = meta_de(story)
        ref = SCRATCH / f"ref-{story}"
        preparer(story, meta["commit"], ref, retirer_caches=False)
        with LOCK_TESTS:
            res = pytest(ref, meta["tests_executes"])
        base = SCRATCH / f"base-{story}"
        preparer(story, meta["base"], base, retirer_caches=True)
        copier_caches(story, base)
        with LOCK_TESTS:
            res_base = pytest(base, meta["tests_executes"])
        (CORPUS / story / "interface.md").write_text(interface_attendue(story, base), encoding="utf-8", newline="\n")
        ok = res["failed"] == 0 and res["errors"] == 0 and res["passed"] > 0
        meta["total_ref"] = res["passed"] + res["failed"] + res["errors"] if ok else None
        meta["base_passed"] = res_base["passed"]
        meta["base_failed"] = res_base["failed"] + res_base["errors"]
        meta["duree_ref_s"] = res["duree_s"]
        (CORPUS / story / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        print(story, "référence", res["passed"], "ok" if ok else "ECHEC", f"({res['duree_s']} s)", "| base :", res_base["passed"],
              "passés,", res_base["failed"], "échecs,", res_base["errors"], "erreurs", flush=True)
        if not ok:
            print(res["fin"])
        banc.effacer(ref)
        banc.effacer(base)


def appui(stories: list[str]) -> None:
    """Ajoute les fichiers d'appui des tests (fichiers .py de tests/ modifiés, non test_*) puis refait référence et interface."""
    for story in stories:
        meta = meta_de(story)
        statuts = [l.split("	") for l in git(meta, "diff-tree", "--no-commit-id", "--name-status", "-r", meta["commit"]).splitlines()]
        meta["tests_appui"] = [
            s[1] for s in statuts
            if s[0] == "M" and re.match(r"^tests?/", s[1]) and s[1].endswith(".py") and not re.search(r"(^|/)test_[^/]*\.py$", s[1])
        ]  # fmt: skip
        for c in meta["tests_appui"]:
            cible = CORPUS / story / "cache" / c
            cible.parent.mkdir(parents=True, exist_ok=True)
            cible.write_bytes(git(meta, "show", f"{meta['commit']}:{c}", binaire=True))
        (CORPUS / story / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        print(story, "appui :", meta["tests_appui"], flush=True)
    reference(stories)


# ------------------------------------------------------------------ appels claude
def base_cmd(modele: str, effort: str, outils: str, autorises: list[str], session: str, budget: str) -> list[str]:
    return [
        CLAUDE, "-p", "--model", modele, "--effort", effort, "--output-format", "json",
        "--permission-mode", "acceptEdits", "--allowedTools", *autorises,
        "--tools", outils, "--setting-sources", "project,local",
        "--settings", json.dumps(REGLAGES), "--session-id", session, "--max-budget-usd", budget,
    ]  # fmt: skip


def mesures_appel(brut: dict, transcription: Path | None) -> dict:
    return {
        "cout_usd": brut.get("total_cost_usd"), "tours": brut.get("num_turns"),
        "duree_ms": brut.get("duration_ms"), "duree_api_ms": brut.get("duration_api_ms"),
        "is_error": brut.get("is_error"), "subtype": brut.get("subtype"),
        "usage": brut.get("usage"), "modelUsage": brut.get("modelUsage"),
        "refus_permission": len(brut.get("permission_denials") or []),
        "transcription": banc.metriques_transcription(transcription),
    }  # fmt: skip


def ecrire_jsonl(chemin: Path, enreg: dict) -> None:
    with LOCK_ECRITURE:
        DONNEES.mkdir(parents=True, exist_ok=True)
        with chemin.open("a", encoding="utf-8") as f:
            f.write(json.dumps(enreg, ensure_ascii=False) + "\n")


def faits(chemin: Path) -> set[str]:
    if not chemin.exists():
        return set()
    return {json.loads(l)["id"] for l in chemin.read_text(encoding="utf-8").splitlines() if l}


def copier_transcription(rid: str, transcription: Path | None) -> None:
    if transcription:
        (SCRATCH / "_transcriptions").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(transcription, SCRATCH / "_transcriptions" / f"{rid}.jsonl")


# ------------------------------------------------------------------ cadrage
def prompt_cadrage(story: str, arm: str) -> str:
    meta = meta_de(story)
    entete = (ICI / "prompts" / f"cadrage-{arm}.md").read_text(encoding="utf-8")
    if arm == "A":
        src = ICI / "prompts" / "bmad-build"
        pieces = "\n\n".join(
            f"<!-- {nom} -->\n" + (src / nom).read_text(encoding="utf-8") for nom in ("workflow.md", "step-01-clarify-and-route.md", "step-02-plan.md", "spec-template.md")
        )
        entete = entete.replace("{{METHODE}}", pieces)
    else:
        src = ICI / "prompts" / "openspec"
        pieces = "\n\n".join(
            f"<!-- {nom} -->\n" + (src / nom).read_text(encoding="utf-8") for nom in ("instructions.md", "proposal.md", "spec.md", "tasks.md")
        )
        entete = entete.replace("{{METHODE}}", pieces)
    entree = (
        f"\n\n# Entrée : story {meta['label']}\n\n"
        "## Entrée de la story dans epics.md\n\n" + (CORPUS / story / "epics.md").read_text(encoding="utf-8")
        + "\n" + (CORPUS / story / "interface.md").read_text(encoding="utf-8")
    )
    return entete + entree


def nettoyer_reponse(texte: str) -> str:
    texte = texte.strip()
    m = re.match(r"^```(?:markdown|md)?\n(.*)\n```$", texte, flags=re.S)
    return (m.group(1) if m else texte).strip() + "\n"


def cadrer(story: str, arm: str, rep: int) -> dict:
    rid = f"{story}-{arm}{rep}"
    cible = Path(os.path.realpath(SCRATCH)) / "cad" / rid
    preparer(story, meta_de(story)["base"], cible, retirer_caches=True, sync=False)
    session = str(uuid.uuid4())
    cmd = base_cmd(OPUS, "medium", OUTILS_CADRAGE, AUTORISES_CADRAGE, session, "6")
    debut = datetime.now().astimezone()
    t0 = time.time()
    code, sortie, erreur, expire = banc.lancer(cmd, cible, 20 * 60, env=banc.env_enfant(), entree=prompt_cadrage(story, arm))
    duree = round(time.time() - t0, 1)
    (DONNEES / "brut").mkdir(parents=True, exist_ok=True)
    (DONNEES / "brut" / f"cadrage-{rid}.json").write_text(sortie or "", encoding="utf-8")
    brut: dict = {}
    try:
        brut = json.loads(sortie)
    except ValueError:
        pass
    texte = nettoyer_reponse(brut.get("result") or "")
    (DONNEES / "specs").mkdir(parents=True, exist_ok=True)
    (DONNEES / "specs" / f"{rid}.md").write_text(texte, encoding="utf-8", newline="\n")
    transcription = banc.trouver_transcription(session)
    enreg = {
        "id": rid, "etape": "cadrage", "story": story, "arm": arm, "rep": rep, "modele": OPUS, "effort": "medium",
        "debut": debut.isoformat(timespec="seconds"), "duree_mur_s": duree, "code": code, "expire": expire,
        "session_id": session, "spec_chars": len(texte), "spec_lignes": len(texte.splitlines()),
        "resultat_vide": len(texte.strip()) < 200, "stderr_fin": erreur[-300:],
        **mesures_appel(brut, transcription),
    }  # fmt: skip
    ecrire_jsonl(CADRAGES, enreg)
    copier_transcription("cad-" + rid, transcription)
    banc.effacer(cible)
    return enreg


# ------------------------------------------------------------------ développement
def lint_fichiers(cible: Path, fichiers: list[str]) -> tuple[int, int]:
    py = [f for f in fichiers if f.endswith(".py") and (cible / f).exists()]
    if not py:
        return 0, 0
    r1 = banc.lancer([UV, "run", "--no-sync", "ruff", "check", "--output-format", "concise", *py], cible, 300, env=banc.env_enfant())
    r2 = banc.lancer([UV, "run", "--no-sync", "ruff", "format", "--check", *py], cible, 300, env=banc.env_enfant())
    m1 = re.search(r"Found (\d+) error", r1[1] + r1[2])
    m2 = re.search(r"(\d+) files? would be reformatted", r2[1] + r2[2])
    return (int(m1.group(1)) if m1 else (0 if r1[0] == 0 else -1)), (int(m2.group(1)) if m2 else (0 if r2[0] == 0 else -1))


def spec_pour_dev(story: str, arm: str, rep: int) -> tuple[str, str]:
    meta = meta_de(story)
    if arm == "C":
        spec = (CORPUS / story / "spec.md").read_text(encoding="utf-8")
    elif arm == "D":  # bras ajouté hors protocole : aucune étape de cadrage, entrée de epics.md et interface seulement
        spec = ""
    else:
        spec = (DONNEES / "specs" / f"{story}-{arm}{rep}.md").read_text(encoding="utf-8")
    epics = (CORPUS / story / "epics.md").read_text(encoding="utf-8")
    texte = f"{epics}\n---\n\n{spec}\n{(CORPUS / story / 'interface.md').read_text(encoding='utf-8')}"
    return texte, meta["label"]


def developper(story: str, arm: str, rep: int) -> dict:
    meta = meta_de(story)
    rid = f"{story}-{arm}{rep}"
    cible = Path(os.path.realpath(SCRATCH)) / "dev" / rid
    sha0 = preparer(story, meta["base"], cible, retirer_caches=True)
    texte, _ = spec_pour_dev(story, arm, rep)
    session = str(uuid.uuid4())
    cmd = base_cmd(SONNET, "medium", OUTILS_DEV, AUTORISES, session, "5")
    debut = datetime.now().astimezone()
    t0 = time.time()
    code, sortie, erreur, expire = banc.lancer(cmd, cible, banc.TIMEOUT_S, env=banc.env_enfant(), entree=PROMPT_DEV + texte)
    duree = round(time.time() - t0, 1)
    (DONNEES / "brut").mkdir(parents=True, exist_ok=True)
    (DONNEES / "brut" / f"dev-{rid}.json").write_text(sortie or "", encoding="utf-8")
    brut: dict = {}
    try:
        brut = json.loads(sortie)
    except ValueError:
        pass
    transcription = banc.trouver_transcription(session)
    enreg: dict = {
        "id": rid, "etape": "dev", "story": story, "arm": arm, "rep": rep, "modele": SONNET, "effort": "medium",
        "debut": debut.isoformat(timespec="seconds"), "duree_mur_s": duree, "code": code, "expire": expire,
        "session_id": session, "base": meta["base"], "resultat_debut": (brut.get("result") or "")[:300],
        "stderr_fin": erreur[-300:], "spec_chars": len(texte),
        **mesures_appel(brut, transcription),
    }  # fmt: skip
    subprocess.run(["git", *GIT_ID, "add", "-A"], cwd=cible, capture_output=True)
    num = subprocess.run(["git", "diff", "--cached", "--numstat", sha0], cwd=cible, capture_output=True, text=True).stdout.splitlines()
    fichiers: list[str] = []
    ajoutes = supprimes = 0
    for ligne in num:
        a, s, chemin = ligne.split("\t", 2)
        fichiers.append(chemin)
        ajoutes += int(a) if a.isdigit() else 0
        supprimes += int(s) if s.isdigit() else 0
    perimetre = set(meta["fichiers_commit"])
    hors = [f for f in fichiers if f not in perimetre and not f.startswith("_bmad-output/")]
    enreg["diff"] = {
        "fichiers": len(fichiers), "ajoutes": ajoutes, "supprimes": supprimes, "liste": fichiers,
        "hors_perimetre": hors,
        "src_ecrits": sum(1 for f in fichiers if f in meta["src_modifies"]),
    }  # fmt: skip
    patch = subprocess.run(["git", "diff", "--cached", sha0], cwd=cible, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    (DONNEES / "patches").mkdir(parents=True, exist_ok=True)
    (DONNEES / "patches" / f"{rid}.diff").write_text(patch, encoding="utf-8", newline="\n")
    with LOCK_TESTS:
        enreg["ruff_erreurs"], enreg["ruff_format_fichiers"] = lint_fichiers(cible, [f for f in fichiers if not f.startswith("tests/")] + [f for f in fichiers if f.startswith("tests/")])
        caches = copier_caches(story, cible)
        enreg["cache"] = pytest(cible, caches)
    total = meta.get("total_ref")
    enreg["total_ref"] = total
    enreg["taux_cache"] = round(enreg["cache"]["passed"] / total, 4) if total else None
    ecrire_jsonl(RUNS, enreg)
    copier_transcription("dev-" + rid, transcription)
    banc.effacer(cible)
    return enreg


def reevaluer(ids: list[str]) -> None:
    """Rejoue la mesure des tests cachés sur le patch enregistré d'un run (après ajout des fichiers d'appui)."""
    lignes = [json.loads(l) for l in RUNS.read_text(encoding="utf-8").splitlines() if l]
    for e in lignes:
        if e["id"] not in ids:
            continue
        meta = meta_de(e["story"])
        cible = Path(os.path.realpath(SCRATCH)) / "reeval" / e["id"]
        preparer(e["story"], meta["base"], cible, retirer_caches=True)
        patch = DONNEES / "patches" / f"{e['id']}.diff"
        if patch.stat().st_size:
            r = subprocess.run(["git", "apply", "--whitespace=nowarn", str(patch)], cwd=cible, capture_output=True, text=True)
            if r.returncode:
                print(e["id"], "git apply a échoué", r.stderr[-300:])
                continue
        caches = copier_caches(e["story"], cible)
        with LOCK_TESTS:
            e["cache_avant_reeval"] = e["cache"]["passed"]
            e["cache"] = pytest(cible, caches)
        e["total_ref"] = meta["total_ref"]
        e["taux_cache"] = round(e["cache"]["passed"] / meta["total_ref"], 4)
        e["reeval"] = "fichiers d'appui des tests ajoutés"
        banc.effacer(cible)
        print(e["id"], "->", e["cache"]["passed"], "/", meta["total_ref"], flush=True)
    RUNS.write_text("".join(json.dumps(e, ensure_ascii=False) + chr(10) for e in lignes), encoding="utf-8")


# ------------------------------------------------------------------ lots
def resume(e: dict) -> str:
    base = f"{e['id']} {e['etape']}: cout={e['cout_usd']} tours={e['tours']} mur={e['duree_mur_s']}s"
    if e["etape"] == "dev":
        return base + f" cache={e['cache']['passed']}/{e['total_ref']} ruff={e['ruff_erreurs']}/{e['ruff_format_fichiers']} hors={len(e['diff']['hors_perimetre'])}"
    return base + f" chars={e['spec_chars']} vide={e['resultat_vide']}"


def une_tache(t: dict) -> list[str]:
    sortie = []
    story, arm, rep = t["story"], t["arm"], t["rep"]
    try:
        if arm in ("A", "B") and f"{story}-{arm}{rep}" not in faits(CADRAGES):
            e = cadrer(story, arm, rep)
            sortie.append(resume(e))
            if e["resultat_vide"]:
                return sortie + [f"{story}-{arm}{rep}: cadrage vide, développement sauté"]
        if f"{story}-{arm}{rep}" not in faits(RUNS):
            sortie.append(resume(developper(story, arm, rep)))
    except Exception as exc:  # noqa: BLE001
        sortie.append(f"{t}: ECHEC BANC {exc!r}")
    return sortie


def lot(plan: Path, maximum: int) -> None:
    taches = json.loads(plan.read_text(encoding="utf-8"))
    print(f"{len(taches)} tâches", flush=True)
    with cf.ThreadPoolExecutor(max_workers=maximum) as pool:
        for r in pool.map(une_tache, taches):
            for ligne in r:
                print(datetime.now().strftime("%H:%M:%S"), ligne, flush=True)


def main() -> int:
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    for nom in ("extraire", "reference", "appui", "reeval"):
        s = sp.add_parser(nom)
        s.add_argument("ids", nargs="+")
    for nom in ("cadrer", "dev"):
        s = sp.add_parser(nom)
        s.add_argument("story")
        s.add_argument("arm", choices=["A", "B", "C", "D"])
        s.add_argument("rep", type=int)
    lt = sp.add_parser("lot")
    lt.add_argument("plan", type=Path)
    lt.add_argument("--max", type=int, default=2)
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    if a.cmd == "extraire":
        for e in json.loads((ICI / "stories13.json").read_text(encoding="utf-8")):
            if e["id"] in a.ids or a.ids == ["tout"]:
                extraire(e)
    elif a.cmd == "reference":
        reference(a.ids)
    elif a.cmd == "reeval":
        reevaluer(a.ids)
    elif a.cmd == "appui":
        appui(a.ids)
    elif a.cmd == "cadrer":
        print(resume(cadrer(a.story, a.arm, a.rep)))
    elif a.cmd == "dev":
        print(resume(developper(a.story, a.arm, a.rep)))
    else:
        lot(a.plan, a.max)
    return 0


if __name__ == "__main__":
    sys.exit(main())
