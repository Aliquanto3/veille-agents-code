"""T5 : construit le jeu de donnees (diff, spec, verite terrain) depuis le depot public de reference.

Depot : usine-migration-jira-demo (public). Sortie : jeu/<id>/{diff.patch,spec.md,chaine.md} et jeu/jeu.json.
Seuls diff.patch et spec.md sont envoyes aux modeles ; chaine.md (revue d'origine) et la verite terrain ne le sont jamais.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO = Path.home() / "Documents" / "GitHub" / "usine-migration-jira-demo"
SORTIE = Path(__file__).with_name("jeu")
LIMITE_DIFF = 60_000
LIMITE_SPEC = 14_000
SPEC_DIR = "_bmad-output/implementation-artifacts"
SECTIONS_SPEC = ("Intent", "Boundaries & Constraints", "I/O & Edge-Case Matrix", "Code Map", "Tasks & Acceptance", "Design Notes")

# Verite terrain : defauts decouverts apres la fusion (source : retro Epic 0, revue de 7.17-b, constats reportes) ou
# deja notes par la chaine mais non corriges a la fusion (categorie "connu_chaine").
STORIES = [
    dict(
        id="S1-E0-7", titre="Story 0.7, passerelle LLM minimale", commits=["674dd68", "e34200a"], etat="e34200a",
        spec="spec-0-7-passerelle-llm-minimale.md",
        defauts=[dict(id="D1", categorie="manque_chaine",
                      resume="Grammaire des jetons de pseudonymisation dupliquee entre adaptateurs/pseudonymisation et ia/passerelle.py ; la doublure de test ne reconnait pas les jetons prefixes et la suite de contrat ne couvre pas ce cas",
                      source="retrospective Epic 0 (2026-10-12), constat 8",
                      mots=["grammaire", "dupliqu", "prefix", "préfix", "regex"])],
    ),
    dict(
        id="S2-E0-8", titre="Story 0.8, UI minimale", commits=["05ee86f", "4171da2"], etat="4171da2",
        spec="spec-0-8-ui-minimale.md",
        defauts=[dict(id="D1", categorie="manque_chaine",
                      resume="construire_rapport instancie Secrets(...) sans traduire la ValidationError pydantic : un USINE_MODE_REPLI illisible leve une erreur brute (la CLI ne capte que UsineErreur) ; seul mode_repli() a ete corrige",
                      source="retrospective Epic 0, constat 13 (verifie dans le source)",
                      mots=["ValidationError", "Secrets", "USINE_MODE_REPLI", "construire_rapport"]),
                  dict(id="D2", categorie="manque_chaine",
                      resume="USINE_RACINE lu par os.environ dans ui/app.py, hors usine.config.Secrets, contre AD-19",
                      source="retrospective Epic 0, constat 14 (verifie dans le source)",
                      mots=["USINE_RACINE", "os.environ", "AD-19"]),
                  dict(id="D3", categorie="manque_chaine",
                      resume="lancement.lancer_chaine lance Popen sans nouveau groupe de processus ni detachement : la Chaine partage la console, Ctrl+C ou la fermeture du terminal l'arrete aussi (decouvert par la revue de 7.17-b, documente seulement)",
                      source="spec 7.17-b, Revue, second avis 2 (le code vient de la Story 0.8, lancement.py)",
                      mots=["Popen", "creationflags", "start_new_session", "console", "Ctrl+C", "détach", "detach", "groupe"])],
    ),
    dict(
        id="S3-6-10", titre="Story 6.10, classification tolerante, prechauffage, balayage SM-7", commits=["22d7079", "3ac720e"], etat="3ac720e",
        spec="spec-6-10-recette-palier-2.md",
        defauts=[dict(id="D1", categorie="connu_chaine",
                      resume="Le cout majore d'un appel LLM en echec est impute au plafond mais absent des traces et de cout_llm_eur ; SM-7 ne voit pas ces appels (reporte par la revue, corrige en 6.10-b)",
                      source="spec 6.10-b, Problem (1) et (2)", mots=["échec", "echec", "trace", "cout_llm_eur", "SM-7"]),
                  dict(id="D2", categorie="connu_chaine",
                      resume="Le prechauffage redemande a chaque relance une Anomalie qui echoue toujours (echecs non mis en cache, passage_id neuf par tranche) ; relances non bornees",
                      source="spec 6.10-b, Problem (3)", mots=["préchauffage", "prechauffage", "relance", "tranche"])],
    ),
    dict(
        id="S4-7-7", titre="Story 7.7, explication sourcee a l'ecran et apercu de pseudonymisation", commits=["adba54b"], etat="adba54b",
        spec="spec-7-7-explication-sourcee-et-comparaison-des-paliers.md",
        defauts=[dict(id="D1", categorie="connu_chaine",
                      resume="Une ImportError/OSError a la construction du moteur Presidio ou au chargement du modele spaCy plante l'ecran Pseudonymisation (erreur hors UsineErreur non interceptee) ; note par la revue, corrige apres coup (7.7-a)",
                      source="spec 7.7 Auto Run Result + commit 4056a97", mots=["ImportError", "OSError", "Presidio", "spaCy", "apercu", "aperçu"])],
    ),
    dict(
        id="S5-7-10", titre="Story 7.10, suite d'evaluation de l'agent", commits=["56f0de6"], etat="56f0de6",
        spec="spec-7-10-suite-d-evaluation-de-l-agent.md",
        defauts=[dict(id="D1", categorie="connu_chaine",
                      resume="En mode --reel, une erreur reseau non UsineErreur remonte en trace Python au lieu du code de sortie 1 ; rejetee low par la revue, corrigee apres coup (7.10-a)",
                      source="spec 7.10 Review Triage Log + commit 5ca440d", mots=["réseau", "reseau", "--reel", "UsineErreur", "exit", "code de sortie"])],
    ),
    dict(
        id="S6-7-15", titre="Story 7.15, lancement de la Chaine et bouton de mode", commits=["d58ce6c", "c86b2f7"], etat="c86b2f7",
        spec="spec-7-15-lancement-de-la-chaine-et-bouton-de-mode.md",
        defauts=[],  # temoin : aucun defaut connu manque ; toute alerte Important est a classer "rien de verifiable" sauf preuve
    ),
    dict(
        id="S7-7-16", titre="Story 7.16, Agent, Avant/apres, Pseudonymisation et Outillage", commits=["5545523", "cf54141"], etat="cf54141",
        spec="spec-7-16-agent-avant-apres-pseudonymisation-et-outillage.md",
        defauts=[dict(id="D1", categorie="manque_chaine",
                      resume="Le badge 'hors perimetre' de l'Agent compare la reponse du LLM a SANS_REPONSE par egalite stricte (apres strip) : casse, ponctuation finale, guillemets ou espaces differents font perdre le badge (corrige en 7.17-b)",
                      source="spec 7.17-b, Problem (2) ; commit 40e44ad", mots=["SANS_REPONSE", "hors_perimetre", "hors périmètre", "texte_hors_perimetre", "égalité", "egalite", "strip"])],
    ),
]

SECTION = re.compile(r"^## (.+?)\s*$", re.M)


def git(*args: str) -> str:
    r = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
    return r.stdout


def categorie(chemin: str) -> int:
    if chemin.startswith(("_bmad-output/", "_bmad/")) or "/resultats/" in chemin or chemin.endswith((".lock", ".jsonl")):
        return 9
    py = chemin.endswith(".py")
    if py and chemin.startswith(("src/", "evals/", "outils/", "evaluation/")):
        return 0
    if py and chemin.startswith("tests/"):
        return 1
    return 2


def par_fichier(texte: str) -> dict[str, list[str]]:
    sortie: dict[str, list[str]] = {}
    for bloc in re.split(r"(?m)^(?=diff --git )", texte):
        m = re.match(r"diff --git a/(\S+) b/(\S+)", bloc) if bloc.strip() else None
        if m:
            sortie.setdefault(m.group(2), []).append(bloc)
    return sortie


def diff_net(commits: list[str], nom: str) -> str | None:
    """Diff net des commits de la story appliques seuls sur le parent du premier (worktree jetable, cherry-pick -n).

    Evite les hunks contradictoires entre le commit de la story et son commit de correctifs de revue, et les
    modifications d'autres stories intercalees. None si un cherry-pick entre en conflit."""
    wt = Path(__file__).with_name("worktrees") / f"_net_{nom}"
    wt.parent.mkdir(exist_ok=True)
    if wt.exists():
        git("worktree", "remove", "--force", str(wt))
    base = git("rev-parse", f"{commits[0]}^").strip()
    git("worktree", "add", "--detach", str(wt), base)
    try:
        for c in commits:
            r = subprocess.run(["git", "-C", str(wt), "cherry-pick", "-n", c], capture_output=True, text=True)
            if r.returncode:
                return None
        return subprocess.run(["git", "-C", str(wt), "diff", "--cached", "--no-color", "-U1"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    finally:
        git("worktree", "remove", "--force", str(wt))
        git("worktree", "prune")


def patchs(commits: list[str], nom: str = "x") -> tuple[dict[str, str], str]:
    """Patch par fichier : net si possible, sinon concatene sur les commits de la story (dans l'ordre)."""
    net = diff_net(commits, nom) if len(commits) > 1 else None
    if net:
        return {f: "".join(b) for f, b in par_fichier(net).items()}, "net"
    cumul: dict[str, list[str]] = {}
    for c in commits:
        for f, b in par_fichier(git("show", "--format=", "--no-color", "-U1", c)).items():
            cumul.setdefault(f, []).extend(b)
    return {f: "".join(b) for f, b in cumul.items()}, ("simple" if len(commits) == 1 else "concatene")


def construire_diff(commits: list[str], nom: str = "x") -> tuple[str, list[str], list[str], str]:
    p, mode = patchs(commits, nom)
    ordre = sorted(p, key=lambda f: (categorie(f), len(p[f]), f))
    sortie, inclus, omis, taille = [], [], [], 0
    for f in ordre:
        if categorie(f) == 9:
            omis.append(f + " (exclu)")
            continue
        bloc = p[f]
        if taille >= LIMITE_DIFF:
            omis.append(f)
            continue
        if taille + len(bloc) > LIMITE_DIFF:
            bloc = bloc[: LIMITE_DIFF - taille] + "\n[... diff tronque a 60 000 caracteres ...]\n"
            inclus.append(f + " (tronque)")
        else:
            inclus.append(f)
        sortie.append(bloc)
        taille += len(bloc)
    return "".join(sortie), inclus, omis, mode


def extraire_sections(texte: str, noms: tuple[str, ...], inverse: bool = False) -> str:
    morceaux = []
    reperes = list(SECTION.finditer(texte))
    for i, m in enumerate(reperes):
        fin = reperes[i + 1].start() if i + 1 < len(reperes) else len(texte)
        garde = m.group(1).strip() in noms
        if garde != inverse:
            morceaux.append(texte[m.start():fin])
    return "".join(morceaux)


def main() -> None:
    SORTIE.mkdir(exist_ok=True)
    meta = []
    for s in STORIES:
        d = SORTIE / s["id"]
        d.mkdir(exist_ok=True)
        diff, inclus, omis, mode = construire_diff(s["commits"], s["id"])
        (d / "diff.patch").write_text(diff, encoding="utf-8", newline="\n")
        spec_complete = git("show", f"{s['etat']}:{SPEC_DIR}/{s['spec']}")
        spec = extraire_sections(spec_complete, SECTIONS_SPEC)[:LIMITE_SPEC]
        (d / "spec.md").write_text(spec, encoding="utf-8", newline="\n")
        chaine = extraire_sections(spec_complete, SECTIONS_SPEC, inverse=True)
        (d / "chaine.md").write_text(chaine, encoding="utf-8", newline="\n")
        meta.append({**s, "diff_caracteres": len(diff), "spec_caracteres": len(spec), "fichiers_inclus": inclus, "fichiers_omis": omis, "mode_diff": mode})
        print(s["id"], mode, len(diff), len(spec), "omis:", len(omis))
    (SORTIE / "jeu.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
