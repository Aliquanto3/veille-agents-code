"""T13 bis : peut-on sauter le cadrage BMAD pour une petite story ? Banc de T13 réutilisé tel quel, par import.

`../T13-story-legere/t13.py` n'est pas modifié : ce module l'importe et redirige ses chemins (corpus, données, dossier
jetable) vers T13 bis. Les consignes de cadrage (`prompts/`) et les CLAUDE.md minimaux (`claude_md/`) sont lus dans le
dossier de T13. Ajouts : l'extraction sans spec d'origine (le bras C n'est pas joué), le bras `Dc` (D-court : entrée
de epics.md réduite à son titre et à sa phrase « As a / I want / So that ») et un garde-fou de budget.

Sous-commandes (via `uv run --no-project python -I t13bis.py ...`) :
  copier ID...          reprend corpus/<id>/ de T13 (meta, tests cachés, entrée, interface) et écrit epics_court.md
  extraire ID...        construit corpus/<id>/ pour une nouvelle story de stories13bis.json
  reference ID...       valide les tests cachés (commit = tout passe ; base = échec), écrit interface.md
  lot PLAN.json [--max 2] [--plafond 40]   exécute un plan ; s'arrête avant de dépasser le plafond de coût
  cout                  coût engagé par T13 bis
"""

import argparse
import concurrent.futures as cf
import json
import re
import shutil
import sys
import threading
from datetime import datetime
from pathlib import Path

BIS = Path(__file__).resolve().parent
T13 = BIS.parent / "T13-story-legere"
sys.path.insert(0, str(T13))
import t13  # noqa: E402

t13.CORPUS = BIS / "corpus"
t13.DONNEES = BIS / "donnees"
t13.RUNS = t13.DONNEES / "runs.jsonl"
t13.CADRAGES = t13.DONNEES / "cadrages.jsonl"
t13.SCRATCH = Path(
    r"C:\Users\Utilisateur\AppData\Local\Temp\claude\C--Users-Utilisateur-Documents-GitHub"
    r"\791fed94-a8b0-414e-8a6c-8fe967283749\scratchpad\t13bis\run"
)
# Réservation de coût par tâche avant lancement (moyennes de T13 arrondies au-dessus, cadrage A le plus cher : 1,91 $).
RESERVE = {"A": 2.6, "D": 0.7, "Dc": 0.7}
LOCK_BUDGET = threading.Lock()
EN_COURS: dict[str, float] = {}
SAUTEES: set[str] = set()


# ------------------------------------------------------------------ entrées
def entree_courte(entree: str) -> str:
    """Titre de la story et sa phrase « As a / I want / So that » (ou « En tant que »), sans exigences ni critères."""
    lignes = entree.strip().splitlines()
    garde = [lignes[0]]
    phrase: list[str] = []
    for l in lignes[1:]:
        if l.startswith("**") or re.match(r"^\s*[-*]\s", l):
            if phrase:
                break
            continue
        if not l.strip():
            if phrase:
                break
            continue
        phrase.append(l)
    if not phrase or not re.match(r"(?i)^(as an?|en tant qu)", phrase[0].strip()):
        raise RuntimeError("phrase « As a » introuvable : " + lignes[0])
    return "\n".join(garde + [""] + phrase) + "\n"


def ecrire_court(story: str) -> None:
    d = t13.CORPUS / story
    (d / "epics_court.md").write_text(entree_courte((d / "epics.md").read_text(encoding="utf-8")), encoding="utf-8", newline="\n")


SEUIL_BREVE = 1200  # caractères de l'entrée epics.md, fixé avant les runs (protocole, section 4)


def richesse(story: str) -> str:
    """« détaillée » ou « brève » (entrée à critères Given/When/Then de moins de 1 200 caractères) ; « courte » sans critères."""
    texte = (t13.CORPUS / story / "epics.md").read_text(encoding="utf-8")
    if not re.search(r"\*\*Given\*\*|\bGiven\b|Étant donné", texte):
        return "courte"
    return "brève" if len(texte) < SEUIL_BREVE else "détaillée"


def copier(stories: list[str]) -> None:
    for story in stories:
        src, dst = T13 / "corpus" / story, t13.CORPUS / story
        t13.banc.effacer(dst)
        dst.mkdir(parents=True)
        shutil.copytree(src / "cache", dst / "cache")
        for nom in ("meta.json", "epics.md", "interface.md"):
            shutil.copyfile(src / nom, dst / nom)
        ecrire_court(story)
        print(story, "copiée de T13,", richesse(story))


def extraire(entree: dict) -> None:
    """Comme t13.extraire, sans spec d'origine (pas de bras C en T13 bis)."""
    story = entree["id"]
    meta = {k: entree[k] for k in ("id", "repo", "pkg", "label")}
    meta["commit"] = t13.git(entree, "rev-parse", entree["commit"]).strip()
    meta["base"] = t13.git(entree, "rev-parse", meta["commit"] + "^").strip()
    statuts = [l.split("\t") for l in t13.git(meta, "-c", "core.quotepath=false", "diff-tree", "--no-commit-id", "--name-status", "-r", meta["commit"]).splitlines()]
    meta["fichiers_commit"] = [s[-1] for s in statuts]
    caches = [s[1] for s in statuts if s[0] == "A" and re.match(r"^tests?/", s[1]) and "__pycache__" not in s[1]]
    meta["tests_caches"] = caches
    meta["tests_executes"] = [c for c in caches if re.search(r"(^|/)test_[^/]*\.py$", c)]
    meta["tests_appui"] = [
        s[1] for s in statuts
        if s[0] == "M" and re.match(r"^tests?/", s[1]) and s[1].endswith(".py") and not re.search(r"(^|/)test_[^/]*\.py$", s[1])
    ]  # fmt: skip
    meta["src_modifies"] = [s[1] for s in statuts if not re.match(r"^(tests?/|_bmad|docs/)", s[1]) and not s[1].endswith(".md")]
    meta["c_disponible"] = False
    dossier = t13.CORPUS / story
    t13.banc.effacer(dossier)
    (dossier / "cache").mkdir(parents=True)
    for c in caches + meta["tests_appui"]:
        cible = dossier / "cache" / c
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_bytes(t13.git(meta, "show", f"{meta['commit']}:{c}", binaire=True))
    ep = "_bmad-output/planning-artifacts/epics.md"
    (dossier / "epics.md").write_text(t13.section_epics(t13.git(meta, "show", f"{meta['base']}:{ep}"), entree["label"]), encoding="utf-8", newline="\n")
    (dossier / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    ecrire_court(story)
    print(story, richesse(story), "| tests cachés :", caches, "| appui :", meta["tests_appui"], "| src :", meta["src_modifies"])


# ------------------------------------------------------------------ bras Dc
_spec_pour_dev_t13 = t13.spec_pour_dev


def spec_pour_dev(story: str, arm: str, rep: int) -> tuple[str, str]:
    if arm != "Dc":
        return _spec_pour_dev_t13(story, arm, rep)
    meta = t13.meta_de(story)
    court = (t13.CORPUS / story / "epics_court.md").read_text(encoding="utf-8")
    return f"{court}\n---\n\n\n{(t13.CORPUS / story / 'interface.md').read_text(encoding='utf-8')}", meta["label"]


t13.spec_pour_dev = spec_pour_dev


# ------------------------------------------------------------------ coût et lots
def cout_engage() -> float:
    tot = 0.0
    for p in (t13.RUNS, t13.CADRAGES):
        if p.exists():
            tot += sum((json.loads(l).get("cout_usd") or 0) for l in p.read_text(encoding="utf-8").splitlines() if l)
    return tot


def une_tache(t: dict, plafond: float) -> list[str]:
    cle = f"{t['story']}-{t['arm']}{t['rep']}"
    if cle in t13.faits(t13.RUNS):
        return []
    with LOCK_BUDGET:
        engage = cout_engage()
        if t["arm"] == "D" and t["story"] in SAUTEES:  # A sautée faute de budget : D seule ne sert pas l'appariement
            return [f"{cle}: SAUTÉE (A de la même story sautée)"]
        if engage + sum(EN_COURS.values()) + RESERVE[t["arm"]] > plafond:
            if t["arm"] == "A":
                SAUTEES.add(t["story"])
            return [f"{cle}: SAUTÉE (budget : engagé {engage:.2f} $, en cours {sum(EN_COURS.values()):.2f} $, plafond {plafond} $)"]
        EN_COURS[cle] = RESERVE[t["arm"]]
    try:
        return t13.une_tache(t)
    finally:
        with LOCK_BUDGET:
            EN_COURS.pop(cle, None)


def lot(plan: Path, maximum: int, plafond: float) -> None:
    taches = json.loads(plan.read_text(encoding="utf-8"))
    print(f"{len(taches)} tâches, engagé {cout_engage():.2f} $", flush=True)
    with cf.ThreadPoolExecutor(max_workers=maximum) as pool:
        for r in pool.map(lambda t: une_tache(t, plafond), taches):
            for ligne in r:
                print(datetime.now().strftime("%H:%M:%S"), ligne, flush=True)
    print(f"fin du lot, engagé {cout_engage():.2f} $", flush=True)


def main() -> int:
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    for nom in ("copier", "extraire", "reference"):
        sp.add_parser(nom).add_argument("ids", nargs="+")
    lt = sp.add_parser("lot")
    lt.add_argument("plan", type=Path)
    lt.add_argument("--max", type=int, default=2)
    lt.add_argument("--plafond", type=float, default=45.0)
    sp.add_parser("cout")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    if a.cmd == "copier":
        copier(a.ids)
    elif a.cmd == "extraire":
        for e in json.loads((BIS / "stories13bis.json").read_text(encoding="utf-8")):
            if e["id"] in a.ids or a.ids == ["tout"]:
                extraire(e)
    elif a.cmd == "reference":
        t13.reference(a.ids)
    elif a.cmd == "cout":
        print(f"engagé T13 bis : {cout_engage():.2f} $")
    else:
        lot(a.plan, min(a.max, 2), a.plafond)
    return 0


if __name__ == "__main__":
    sys.exit(main())
