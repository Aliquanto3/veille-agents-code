"""T1, question 5 : part des constats du second avis que le reviewer a retenus, rejetes ou juges faux.

Ou la revue est consignee : dans les fichiers de story ``_bmad-output/implementation-artifacts/*.md`` du
depot, sous forme de puces « severite, second avis N : constat. Corrige / Rejete / Reporte ... », ecrites par
le reviewer (Opus) apres lecture de la liste du second avis (Haiku). Le journal ``run-autonome.md`` donne le
nombre de constats declares a l'etape ``second-avis``.

Methode : lecture ligne par ligne des .md (petits fichiers) de chaque depot ayant un dossier
``implementation-artifacts`` hors ``.claude/worktrees`` ; une puce est un constat du second avis si elle
commence par une severite (high, medium, low) et contient « second avis ». Le verdict est le premier mot-cle
trouve apres « second avis N » (corrige, rejete, reporte...). Les lignes identiques d'un depot a l'autre
(clones, worktrees) ne comptent qu'une fois. Aucun texte n'est recopie : seuls des comptes sortent.

Usage : uv run --no-project python -I q5_second_avis.py --out q5.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

RACINE_DEPOTS = Path.home() / "Documents" / "GitHub"
RACINE_TRANSCRIPTIONS = Path.home() / ".claude" / "projects"
PUBLICS = ["agent-cost-kit", "wavestack", "wavedevsecops", "wavelocalai", "slm-quality-bench",
           "usine-migration-jira-demo", "veille-agents-code", "WaveEval", "claude-code-mods"]

PUCE = re.compile(r"^\s*(?:[-*]|\d+\.)\s*\**\s*(high|medium|low|haute?|moyen(?:ne)?|faible)\b", re.IGNORECASE)
CONSTAT = re.compile(r"second[- ]avis\s*(?:n°\s*)?\d*", re.IGNORECASE)
VERDICTS = [
    ("partiel", re.compile(r"corrig\w*\s+en\s+partie|partiellement\s+corrig", re.IGNORECASE)),
    ("corrige", re.compile(r"corrig|trait[ée]|r[ée]solu|ajout[ée]|fait\b", re.IGNORECASE)),
    ("rejete", re.compile(r"rejet|[ée]cart|non\s+retenu|refus[ée]", re.IGNORECASE)),
    ("reporte", re.compile(r"report|diff[ée]r|[àa]\s+reprendre|non\s+corrig", re.IGNORECASE)),
    ("requalifie", re.compile(r"requalifi", re.IGNORECASE)),
]
MOTIFS_REJET = [
    ("faux", re.compile(r"faux positif|constat (?:faux|inexact)|[àa] tort|sans objet|n'existe pas|inexact|jamais un|ne se produit pas|impossible", re.IGNORECASE)),
    ("deja_regle", re.compile(r"d[ée]j[àa]|ant[ée]rieur|sur (?:master|main)|apr[èe]s rebase|base en retard|lu sur une base", re.IGNORECASE)),
    ("voulu", re.compile(r"d[ée]cision|voulu|comportement|exig[ée]|impos[ée]|\bAD-\d|contrat|spec\b|crit[èe]re|choix|natif|attendu|par conception", re.IGNORECASE)),
]
FAUX = re.compile(r"faux positif|constat (?:faux|inexact)|[àa] tort|sans objet|d[ée]j[àa] (?:r[ée]gl[ée]|corrig[ée]|trait[ée])|n'existe pas|inexact", re.IGNORECASE)
JOURNAL = re.compile(r"^- \d{4}-\d\d-\d\d(?: \d\d:\d\d)? · ([^·]+) · second-avis · (.*?)(?: · \S*)?$")
SEVERITE = {"high": "high", "haut": "high", "haute": "high", "medium": "medium", "moyen": "medium", "moyenne": "medium", "low": "low", "faible": "low"}


def label(nom: str) -> str:
    return nom if nom in PUBLICS else "autre"


def classer(reste: str) -> str:
    premier, meilleure = None, 10**9
    for nom, motif in VERDICTS:
        m = motif.search(reste[:260])
        if m and m.start() < meilleure:
            premier, meilleure = nom, m.start()
    return premier or "indetermine"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).with_name("q5.json"))
    o = ap.parse_args()

    vus: set[str] = set()
    par_depot: dict = defaultdict(lambda: {"stories": set(), "constats": Counter(), "journal_declares": 0, "journal_lignes": 0, "fichiers": 0})
    autres_idx = {}
    for depot in sorted(RACINE_DEPOTS.iterdir(), key=lambda d: (d.name not in PUBLICS, d.name)):  # depots publics d abord : un clone ne leur vole pas leurs lignes
        dossier = depot / "_bmad-output" / "implementation-artifacts"
        if not dossier.is_dir():
            continue
        nom = label(depot.name)
        if nom == "autre":
            autres_idx.setdefault("autre", 0)
            autres_idx["autre"] += 1
        d = par_depot[nom]
        for f in sorted(dossier.glob("*.md")):
            d["fichiers"] += 1
            with open(f, encoding="utf-8", errors="replace") as fh:
                for ligne in fh:
                    jm = JOURNAL.match(ligne.strip())
                    if jm:
                        resultat = jm.group(2)
                        if re.search(r"lanc[ée]|liste [àa] transmettre", resultat) and not re.search(r"\d+ (high|medium|low)", resultat):
                            continue
                        cle = "J" + hashlib.sha1(ligne.strip().encode("utf-8")).hexdigest()
                        if cle in vus:
                            continue
                        vus.add(cle)
                        d["journal_lignes"] += 1
                        d["journal_declares"] += sum(int(n) for n, _ in re.findall(r"(\d+) (high|medium|low)", resultat))
                        continue
                    m = PUCE.match(ligne)
                    if not m:
                        continue
                    c = CONSTAT.search(ligne)
                    if not c:
                        continue
                    cle = hashlib.sha1(ligne.strip().encode("utf-8")).hexdigest()
                    if cle in vus:
                        continue
                    vus.add(cle)
                    verdict = classer(ligne[c.end():])
                    sev = SEVERITE[m.group(1).lower()]
                    d["stories"].add(f.name)
                    d["constats"][f"{sev}|{verdict}"] += 1
                    if verdict == "rejete":
                        motif = next((n for n, mo in MOTIFS_REJET if mo.search(ligne[c.end():])), "autre")
                        d["constats"][f"rejet_motif|{motif}"] += 1

    # agents second-avis et reviewer lances (transcriptions des 45 derniers jours, meta.json seulement)
    import time
    coupure = time.time() - 45 * 86400
    agents = Counter()
    for meta in RACINE_TRANSCRIPTIONS.glob("*/*/subagents/*.meta.json"):
        if meta.stat().st_mtime < coupure:
            continue
        try:
            t = json.loads(meta.read_text(encoding="utf-8")).get("agentType", "")
        except (OSError, ValueError):
            continue
        if t.split(":")[-1] in ("second-avis", "reviewer", "dev-story"):
            agents[t.split(":")[-1]] += 1

    total = Counter()
    sortie = {"depots": {}, "agents_lances_45j": dict(agents)}
    for nom, d in par_depot.items():
        sortie["depots"][nom] = {
            "fichiers_story_et_journal": d["fichiers"], "stories_avec_constats": len(d["stories"]),
            "constats": dict(sorted(d["constats"].items())), "journal_lignes_resultat": d["journal_lignes"],
            "journal_constats_declares": d["journal_declares"],
        }
        total.update(d["constats"])
    sortie["total_constats"] = dict(sorted(total.items()))
    sortie["total_stories"] = sum(len(d["stories"]) for d in par_depot.values())
    verdicts = Counter()
    sev = Counter()
    for k, v in total.items():
        if "|" in k and not k.startswith("rejet_motif"):
            s, vd = k.split("|")
            verdicts[vd] += v
            sev[s] += v
    sortie["motifs_rejet"] = {k.split("|")[1]: v for k, v in total.items() if k.startswith("rejet_motif")}
    sortie["par_verdict"] = dict(verdicts)
    sortie["par_severite"] = dict(sev)
    sortie["note_depots_autres"] = autres_idx.get("autre", 0)
    o.out.write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: sortie[k] for k in ("total_stories", "par_verdict", "par_severite", "agents_lances_45j")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
