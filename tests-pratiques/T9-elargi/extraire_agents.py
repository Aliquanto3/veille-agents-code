"""T9 elargi : extrait des transcriptions Claude Code le detail des agents ``dev-story`` (appels, cout, story, debut).

Un seul processus, sequentiel, en flux (reutilise ``lire_fichier`` et ``cout_appel`` de ``T1/analyse.py``, donc le meme
comptage d'appels « propres » et le meme dedoublonnage par ``message.id`` : une reponse recopiee par une reprise n'est
comptee qu'une fois, dans la transcription qui a demarre en premier).

Racines de transcriptions : ``~/.claude/projects`` (toujours, sauf ``--sans-racine-locale``) plus chaque
``--transcriptions <dossier>`` (repetable : transcriptions rapatriees d'autres PC, meme structure de dossiers
``<racine>/<projet>/<session>/subagents/agent-*.jsonl`` et ``.meta.json`` voisin). Plus aucune limite de date.
Sont ecartes : les dossiers dont le nom contient ``scratchpad`` (tests de la veille eux-memes) et tout agent dont le
depot (element du ``cwd`` de la transcription portant le nom d'un depot, ce qui couvre sous-dossiers et worktrees ``.claude``) n'est pas dans la
liste des depots publics ``--depots``. Les agents sans appel propre (copie d'une transcription deja lue) sont ignores ; ceux dont le dernier appel date de moins
de ``--minutes-en-cours`` sont marques ``en_cours`` (``construire_donnees.py`` ecarte leur story : comptage incomplet).

Option ``--avant-kit`` : ajoute les agents ``general-purpose`` de developpement d'avant le kit (usine-migration-jira-demo et
service-public-slm-fine-tuning, description « Implement story X.Y », « Reprise story X.Y », etc.), avec ``ere`` = ``avant-kit`` ;
les ``dev-story`` ont ``ere`` = ``kit``.

Sortie (HORS du depot de veille) : ``<travail>/agents.json``, liste de {depot, session, agent, story, appels, cout, debut, ere}.
Aucun contenu de transcription n'est conserve.

Usage : uv run --no-project python -I extraire_agents.py --travail <dossier hors depot> [--transcriptions <racine> ...]
(les scripts propres au dossier se lancent sans -I si ils importent un module voisin ; celui-ci n'en importe aucun).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path, PurePosixPath, PureWindowsPath

ICI = Path(__file__).resolve().parent
T1 = ICI.parent / "T1" / "analyse.py"
RACINE_LOCALE = Path.home() / ".claude" / "projects"
DEPOTS_PUBLICS = ["usine-migration-jira-demo", "wavestack", "wavedevsecops", "wavelocalai", "wavelibrarian",
                  "service-public-slm-fine-tuning", "agent-cost-kit"]
STORY = re.compile(r"(?<![\w.])(\d+\.\d+[a-z]?)(?![\w.])")
# Avant le 2026-10-13 (kit non installe), ces deux depots developpaient les stories sous ``bmad-build-auto`` avec des agents
# ``general-purpose`` ; seule la description (``*.meta.json``) les distingue. Classement verifie sur un echantillon de premiers
# messages : « Implement (la) story X.Y », « Implementation story X.Y », « Re-implement », « Finir Story X.Y » et « Story X.Y
# correctifs » codent eux-memes (Edit/Write, pas d'Agent) ; « Reprise story » et « Resume story » reprennent la meme story
# (orchestrateurs partiels, gardes comme demande). Exclus : « Story X.Y ... » (orchestrateur qui lance « Implement »), les
# relecteurs (« Follow-up review story X.Y » en est un : revue de suivi, pas une reprise de developpement), « Edge Case », etc.
DEPOTS_AVANT_KIT = ("usine-migration-jira-demo", "service-public-slm-fine-tuning")
DEV_AVANT_KIT = re.compile(
    r"^\s*(?:Implement(?:ation)?|Impl[ée]ment(?:er|ation)|Re-implement|Reprise|Resume|Finir)\b|^\s*Story\s+\d+\.\d+[a-z]?\s+correctifs\s*$",
    re.IGNORECASE)

spec = importlib.util.spec_from_file_location("t1_analyse", T1)
t1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t1)  # type: ignore[union-attr]


def noms_du_chemin(cwd: str | None) -> list[str]:
    """Elements du chemin du cwd (Windows ou POSIX), du plus profond au plus haut."""
    if not cwd:
        return []
    p = PureWindowsPath(cwd) if "\\" in cwd or re.match(r"^[A-Za-z]:", cwd) else PurePosixPath(cwd)
    return list(reversed(p.parts))


def main() -> int:
    for flux in (sys.stdout, sys.stderr):
        flux.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--travail", type=Path, required=True, help="dossier de travail HORS du depot de veille")
    ap.add_argument("--transcriptions", type=Path, action="append", default=[], help="racine de transcriptions supplementaire (repetable)")
    ap.add_argument("--sans-racine-locale", action="store_true")
    ap.add_argument("--depots", nargs="+", default=DEPOTS_PUBLICS)
    ap.add_argument("--types", nargs="+", default=["dev-story"], help="types d'agent retenus (defaut dev-story ; avant le 2026-10-13 les stories de "
                    "usine-migration-jira-demo et service-public-slm-fine-tuning passaient par des agents general-purpose : piste a part, non testee)")
    ap.add_argument("--avant-kit", action="store_true", help="ajoute les agents general-purpose de developpement d'avant le kit (usine et service-public "
                    "seulement), avec ere = avant-kit ; les dev-story ont ere = kit")
    ap.add_argument("--minutes-en-cours", type=int, default=30, help="un agent dont le dernier appel date de moins de N minutes est marque en_cours")
    o = ap.parse_args()
    maintenant = time.time()

    racines = ([] if o.sans_racine_locale else [RACINE_LOCALE]) + list(o.transcriptions)
    autorises = {d.lower(): d for d in o.depots}
    fichiers = []
    ecartes = Counter()
    for racine in racines:
        if not racine.is_dir():
            print(f"racine introuvable, ignoree : {racine}", file=sys.stderr)
            continue
        for d in sorted(racine.iterdir()):
            if not d.is_dir():
                continue
            if "scratchpad" in d.name:
                ecartes["dossier_scratchpad"] += 1
                continue
            for f in d.glob("*/subagents/agent-*.jsonl"):
                try:
                    meta = json.loads(f.with_suffix(".meta.json").read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                type_agent = str(meta.get("agentType", "")).split(":")[-1]
                ere = "kit"
                if type_agent not in o.types:
                    if not (o.avant_kit and type_agent == "general-purpose" and DEV_AVANT_KIT.match(str(meta.get("description", "")))):
                        continue
                    ere = "avant-kit"
                fichiers.append((d.name, f.parent.parent.name, f.stem[len("agent-"):], f, meta, ere))
    debut = []
    for x in fichiers:
        t = t1.premiere_ts(x[3], 0.0)
        debut.append((t if t is not None else 1e18, x))
    debut.sort(key=lambda z: (z[0], str(z[1][3])))
    fichiers = [z[1] for z in debut]

    deja_ids: set[str] = set()
    agents = []
    t0 = time.time()
    for dossier, session, ident, chemin, meta, ere in fichiers:
        r = t1.lire_fichier(chemin, deja_ids, set(), 0.0)
        if r is None:
            continue
        deja_ids |= r["ids"]
        propres = [a for a in r["appels"] if a["propre"]]
        if not propres:
            ecartes["sans_appel_propre"] += 1
            continue
        noms = noms_du_chemin(r["cwd"])
        # depot = element le plus profond du chemin qui porte le nom d'un depot de la liste (couvre sous-dossiers et worktrees)
        depot = next((autorises[n.lower()] for n in noms if n.lower() in autorises), None)
        if depot is None:
            ecartes["depot_hors_liste:" + (noms[0] if noms else "?")] += 1
            continue
        if ere == "avant-kit" and depot not in DEPOTS_AVANT_KIT:
            ecartes["avant_kit_hors_usine_et_service_public"] += 1
            continue
        cout = sum(sum(t1.cout_appel(a["modele"], a["entree"], a["e5"], a["e1h"], a["lu"], a["sortie"], a["geo"]).values()) for a in propres)
        m = STORY.search(str(meta.get("description", "")))
        agents.append({"depot": depot, "session": session, "agent": ident, "story": m.group(1) if m else None,
                       "appels": len(propres), "cout": round(cout, 5), "debut": propres[0]["ts"], "fin": propres[-1]["ts"],
                       "en_cours": maintenant - propres[-1]["t"] < o.minutes_en_cours * 60, "fam": propres[0]["fam"], "ere": ere})
    o.travail.mkdir(parents=True, exist_ok=True)
    (o.travail / "agents.json").write_text(json.dumps(agents, ensure_ascii=False), encoding="utf-8")
    par_depot = Counter(a["depot"] if a["ere"] == "kit" else a["depot"] + "/avant-kit" for a in agents)
    print(json.dumps({"racines": [str(r) for r in racines], "agents_dev_story_lus": len(fichiers), "agents_retenus": len(agents),
                      "avec_numero_de_story": sum(1 for a in agents if a["story"]), "en_cours": sum(1 for a in agents if a["en_cours"]), "par_depot": dict(par_depot),
                      "ecartes": dict(ecartes), "duree_s": round(time.time() - t0)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
