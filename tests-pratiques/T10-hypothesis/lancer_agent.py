"""T10 : lance un agent `claude -p` (Sonnet, effort medium) sur le worktree d'une (story, bras, essai).
usage : lancer_agent.py <story> <A|B> <essai>
Ecrit resultats-bruts/agent-<story>-<bras><essai>.json (sortie JSON de claude + git status) et copie les tests crees."""
from __future__ import annotations

import glob
import json
import shutil
import subprocess
import sys
import time

from jeu import BRUTS, STORIES, arbre, env_pour
from preparer import preparer

MAX_TURNS = "40"
MAX_BUDGET = "3"
DELAI_S = 1800

CONSIGNE = ("Renforce les tests de cette story : ajoute des tests pytest qui vérifient précisément le comportement attendu "
            "(valeurs exactes, bornes, branches d'erreur). Ne modifie pas le code source.")
CONSIGNE_C = ("Ces mutations du code ne font échouer aucun test existant. Pour chacune qui change un comportement observable, "
              "ajoute un test qui échoue sur le code muté et passe sur le code actuel. Si une mutation est équivalente "
              "(aucun comportement observable ne change), dis-le sans écrire de test. Ne modifie pas le code source.")
FIN_C = (" Termine par la liste des fichiers créés, puis, pour chaque mutation Mn, une ligne : le test qui la tue, "
         "ou « équivalente » avec la raison en une phrase.")
HYPOTHESIS = (" Utilise Hypothesis (tests de propriétés) là où une propriété générale existe ; "
              "garde des exemples ciblés pour le reste.")




def liste_survivants(story: str) -> list[str]:
    """T10b : survivants cibles de la story, un diff d'une ligne chacun (cibles.json de T10)."""
    import json
    from pathlib import Path
    cibles = json.loads((Path(__import__("os").environ.get("T10_CIBLES", Path(__file__).parent / "cibles.json"))).read_text(encoding="utf-8"))[story]["cibles"]
    out = ["Mutations survivantes (fichier:ligne, fonction, diff) :"]
    for i, c in enumerate(cibles, 1):
        out.append(f"M{i} `{c['module']}:{c['ligne']}` (`{c['fonction']}`)")
        out += [f"  - {m.strip()}" for m in c["moins"] if m.strip()]
        out += [f"  + {m.strip()}" for m in c["plus"] if m.strip()]
    if any("CosmicRayTestingException" in "".join(c["plus"]) for c in cibles):
        out.append("(`CosmicRayTestingException` : classe d'exception jamais levée, donc l'`except` concerné n'attrape plus rien.)")
    return out


def construire_prompt(story: str, bras: str, essai: int) -> str:
    m = STORIES[story]
    a = arbre(story, bras, essai)
    spec = sorted(glob.glob(str(a / m["spec"])))
    spec_rel = spec[0].replace("\\", "/").split(a.as_posix().replace("\\", "/") + "/")[-1] if spec else "(introuvable)"
    p = [
        "Tu travailles dans un dépôt Python (le dossier courant). Voici la story à renforcer.",
        f"Spec de la story : `{spec_rel}` (à lire d'abord).",
        "Fichiers source modifiés par la story :",
        *[f"- `{s}`" for s in m["sources"]],
        "Tests existants de la story :",
        *[f"- `{t}`" for t in m["tests"]],
        "",
        CONSIGNE + (HYPOTHESIS if bras == "B" else ""),
        *(["", *liste_survivants(story), "", CONSIGNE_C] if bras == "C" else []),
        "",
        f"Écris les nouveaux tests dans de nouveaux fichiers `{m['dossier_tests']}/test_renf_*.py` ; ne modifie ni le code source ni les tests existants. "
        "Lance les tests avec `python -m pytest -q --tb=short <fichiers>` (l'environnement est prêt, rien à installer). "
        "Tous tes tests doivent passer." + (FIN_C if bras == "C" else " Termine par la liste des fichiers créés."),
    ]
    return "\n".join(p)


def main():
    story, bras, essai = sys.argv[1], sys.argv[2], int(sys.argv[3])
    a = preparer(story, bras, essai)
    texte = construire_prompt(story, bras, essai)
    env = env_pour(story, bras, essai)
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    cmd = ["claude", "-p", "--model", "sonnet", "--effort", "medium",
           "--tools", "Read,Edit,Write,Grep,Glob,Bash",
           "--allowedTools", "Read", "Edit", "Write", "Grep", "Glob",
           "Bash(python -m pytest:*)", "Bash(pytest:*)", "Bash(git status:*)",
           "--permission-mode", "acceptEdits", "--setting-sources", "project,local",
           "--disable-slash-commands", "--strict-mcp-config", "--no-session-persistence",
           "--max-turns", MAX_TURNS, "--max-budget-usd", MAX_BUDGET, "--output-format", "json"]
    t = time.time()
    try:
        p = subprocess.run(cmd, input=texte, cwd=a, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=DELAI_S)
        brut, err, rc = p.stdout, p.stderr, p.returncode
    except subprocess.TimeoutExpired as e:
        brut, err, rc = (e.stdout or ""), "timeout", -1
    duree = round(time.time() - t, 1)
    try:
        sortie = json.loads(brut)
    except json.JSONDecodeError:
        sortie = {"brut": brut[-2000:]}
    st = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=a, capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
    modifies = [l[3:] for l in st if not l.startswith("??")]
    crees = [l[3:] for l in st if l.startswith("??")]
    out = {"story": story, "bras": bras, "essai": essai, "prompt": texte, "rc": rc, "stderr": err[-500:],
           "duree_mur_s": duree, "modifies_suivis": modifies, "crees": crees, "sortie": sortie}
    nom = f"{story}-{bras}{essai}"
    (BRUTS / f"agent-{nom}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    dest = BRUTS / "tests-produits" / nom
    for c in crees:
        if c.endswith(".py") and ".hypothesis" not in c:
            d = dest / c
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(a / c, d)
    r = sortie
    print(nom, "rc", rc, "cout", r.get("total_cost_usd"), "tours", r.get("num_turns"), "api_ms", r.get("duration_ms"),
          "mur_s", duree, "modifies", modifies, "crees", [c for c in crees if c.endswith('.py')])


if __name__ == "__main__":
    main()
