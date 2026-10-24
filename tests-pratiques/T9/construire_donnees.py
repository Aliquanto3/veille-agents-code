"""T9 : construit le jeu de stories etiquetees (specs pre-developpement + etiquette de derapage).

Entrees
- ``q6_agents.json`` : detail par agent ``dev-story`` produit par ``T1/analyse.py --detail-dir <dossier hors depot>``
  (appels propres, cout, numero de story lu dans la description, date de debut). Contient aussi des depots
  non publics : ils sont ecartes ici.
- Depots publics sous ``~/Documents/GitHub`` : ``_bmad-output/planning-artifacts/epics.md`` (spec de chaque story)
  et ``_bmad-output/implementation-artifacts`` (revue, pour l'etiquette secondaire).

Sorties
- ``--out-textes`` (hors depot !) : ``textes.json`` {cle: texte de spec}. Les specs ne sont jamais ecrites dans le depot de veille.
- ``--out-csv`` : ``etiquettes.csv`` (cle, depot, appels, etiquettes, caracteristiques numeriques ; aucun texte).

Anti-fuite : la spec est la section « Story X.Y » de ``epics.md`` telle qu'elle etait au dernier commit de ce
fichier anterieur au debut du developpement de la story (minuit UTC du jour du premier agent ``dev-story``). Une
story absente de cette version est ecartee (specification ecrite apres coup). Les sections remplies pendant ou
apres le developpement (Livre, Revue, Dev Agent Record, File List, Change Log, cases cochees) sont retirees.

Usage : uv run --no-project python construire_donnees.py --agents <q6_agents.json> --out-textes <hors depot>/textes.json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

GH = Path.home() / "Documents" / "GitHub"
PREFIXE = "C--Users-Utilisateur-Documents-GitHub-"
DEPOTS = {"wavedevsecops", "wavelocalai", "usine-migration-jira-demo", "wavestack", "slm-quality-bench", "agent-cost-kit", "WaveEval"}
EPICS = "_bmad-output/planning-artifacts/epics.md"
ARTEFACTS = "_bmad-output/implementation-artifacts"

ENTETE_STORY = re.compile(r"^#{3,4} Story (\d+\.\d+[a-z]?)\b")
FIN_SECTION = re.compile(r"^(#{1,4} (Story|Epic) \d|#{1,2} )")
# sections ou marqueurs remplis pendant ou apres le developpement
POST_DEV = re.compile(r"^#{1,4}\s*(Livr[ée]|Revue|Review|Dev Agent Record|File List|Change Log|Completion Notes|Reports?|Spec Change Log|Auto Run Result)\b", re.IGNORECASE)
CASE_COCHEE = re.compile(r"^\s*[-*] \[[xX]\]")
CHEMIN = re.compile(r"`([^`\s]*(?:/|\.(?:py|js|ts|tsx|yaml|yml|json|toml|md|css|html|sql|xlsx|pptx))[^`\s]*)`")


def depot_de(dossier: str) -> str | None:
    nom = dossier[len(PREFIXE):] if dossier.startswith(PREFIXE) else dossier
    return nom if nom in DEPOTS else None  # worktrees `usine-lanes-t1-*` : rejeux experimentaux, ecartes


def git(depot: str, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(GH / depot), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout


def versions_epics(depot: str) -> list[tuple[datetime, str]]:
    out = git(depot, "log", "--format=%H %cI", "--", EPICS)
    v = []
    for ligne in out.splitlines():
        h, d = ligne.split(" ", 1)
        v.append((datetime.fromisoformat(d.strip()).astimezone(timezone.utc), h))
    return sorted(v)


def section(texte: str, cle: str) -> str | None:
    lignes = texte.splitlines()
    debut = None
    for i, l in enumerate(lignes):
        m = ENTETE_STORY.match(l)
        if m and m.group(1) == cle:
            debut = i
            break
    if debut is None:
        return None
    fin = len(lignes)
    for j in range(debut + 1, len(lignes)):
        if FIN_SECTION.match(lignes[j]):
            fin = j
            break
    return "\n".join(lignes[debut:fin]).strip()


def nettoyer(texte: str) -> tuple[str, int]:
    """Retire les sous-sections post-developpement et les cases cochees ; retourne (texte, lignes retirees)."""
    sortie, retire, saute = [], 0, False
    for l in texte.splitlines():
        if re.match(r"^#{1,6}\s", l):
            saute = bool(POST_DEV.match(l))
        if saute or CASE_COCHEE.match(l):
            retire += 1
            continue
        sortie.append(l)
    return "\n".join(sortie).strip(), retire


def caracteristiques(t: str) -> dict:
    lignes = t.splitlines()
    given = sum(1 for l in lignes if re.match(r"^\**\s*(Given|[ÉE]tant donn[ée]e?s?)\b", l.strip(), re.IGNORECASE))
    clauses = sum(1 for l in lignes if re.match(r"^\**\s*(Then|And|When|Alors|Et|Quand)\b", l.strip(), re.IGNORECASE))
    chemins = {c.strip(".,;:") for c in CHEMIN.findall(t)}
    return {
        "n_car": len(t), "n_mots": len(t.split()), "n_criteres": given, "n_clauses": clauses,
        "n_fichiers": len(chemins), "n_codes": len(re.findall(r"`[^`]+`", t)),
        "n_ad": len(set(re.findall(r"\bAD-\d+\b", t))), "n_exigences": len(set(re.findall(r"\b(?:FR|NFR|AR|UX-DR)-?\d+\b", t))),
    }


# ---------- etiquette secondaire : la revue a trouve au moins un defaut medium ou high (non rejete) ----------
PUCE_REV = re.compile(r"^\s*[-*]\s*\**\s*(high|medium|haute?|moyen(?:ne)?)\b", re.IGNORECASE)
REJET = re.compile(r"rejet|[ée]cart|non\s+retenu|refus[ée]|faux", re.IGNORECASE)
TRIAGE_USINE = re.compile(r"^\s*[-*]\s*`\[(high|medium)\]`\s*`\[(patch|defer|bad_spec|intent_gap|decision|reject)\]", re.IGNORECASE)


def fichiers_story(depot: str, cle: str) -> list[Path]:
    d = GH / depot / ARTEFACTS
    if not d.is_dir():
        return []
    a, b = cle.split(".")
    if depot == "wavedevsecops":
        motif = re.compile(rf"^{a}-{b}-.*\.md$")
    elif depot == "wavelocalai":
        motif = re.compile(rf"^story-{a}-{b}[a-z]?\.md$")
    else:
        motif = re.compile(rf"^spec-{a}-{b}-.*\.md$")
    return [f for f in sorted(d.glob("*.md")) if motif.match(f.name)]


def defaut_revue(depot: str, cle: str) -> int | None:
    """1 si la revue consigne un defaut medium ou high non rejete, 0 si elle n'en consigne pas, None si aucune revue lisible."""
    fichiers = fichiers_story(depot, cle)
    if not fichiers:
        return None
    revue_vue, trouve = False, False
    for f in fichiers:
        texte = f.read_text(encoding="utf-8", errors="replace")
        if re.search(r"^## (Revue|Review)", texte, re.MULTILINE):
            revue_vue = True
        for l in texte.splitlines():
            m = TRIAGE_USINE.match(l)
            if m:
                revue_vue = True
                if m.group(2).lower() in ("patch", "defer", "bad_spec", "intent_gap", "decision"):
                    trouve = True
                continue
            if PUCE_REV.match(l) and not REJET.search(l[:200]):
                trouve = True
    if not revue_vue:
        return None
    return int(trouve)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agents", type=Path, required=True)
    ap.add_argument("--out-textes", type=Path, required=True, help="HORS du depot de veille")
    ap.add_argument("--out-csv", type=Path, default=Path(__file__).with_name("etiquettes.csv"))
    ap.add_argument("--facteur", type=float, default=2.0)
    o = ap.parse_args()

    agents = json.loads(o.agents.read_text(encoding="utf-8"))
    bilan = {"agents_total": len(agents)}
    stories: dict[tuple[str, str], dict] = {}
    for a in agents:
        depot = depot_de(a["dossier"])
        if depot is None or not a["story"]:
            continue
        s = stories.setdefault((depot, a["story"]), {"appels": 0, "agents": 0, "cout": 0.0, "debut": a["debut"], "appels_agent": []})
        s["appels"] += a["appels"]
        s["agents"] += 1
        s["cout"] += a["cout"]
        s["debut"] = min(s["debut"], a["debut"])
        s["appels_agent"].append(a["appels"])
    bilan["stories_publiques_avec_numero"] = len(stories)

    # mediane et seuil par depot (mediane des appels par story, reprises regroupees)
    par_depot = defaultdict(list)
    for (depot, _), s in stories.items():
        par_depot[depot].append(s["appels"])
    mediane = {d: statistics.median(v) for d, v in par_depot.items()}
    # variante agent par agent (critere de T1) : mediane des appels par agent du depot
    med_agent = {}
    tmp = defaultdict(list)
    for (depot, _), s in stories.items():
        tmp[depot] += s["appels_agent"]
    for d, v in tmp.items():
        med_agent[d] = statistics.median(v)

    epics_versions = {d: versions_epics(d) for d in {k[0] for k in stories}}
    cache_texte: dict[str, str] = {}

    def contenu_epics(depot: str, h: str) -> str:
        cle = f"{depot}@{h}"
        if cle not in cache_texte:
            cache_texte[cle] = git(depot, "show", f"{h}:{EPICS}")
        return cache_texte[cle]

    textes, lignes_csv = {}, []
    ecartes = defaultdict(int)
    retires_total = 0
    for (depot, cle), s in sorted(stories.items()):
        debut = datetime.fromisoformat(s["debut"]).replace(tzinfo=timezone.utc)
        candidats = [h for (d, h) in epics_versions[depot] if d <= debut]
        source = "avant"
        if not candidats:
            candidats = [h for (d, h) in epics_versions[depot] if d <= debut + timedelta(days=1)]
            source = "jour"
        if not candidats:
            ecartes["epics_absent_au_debut"] += 1
            continue
        sec = section(contenu_epics(depot, candidats[-1]), cle)
        if sec is None:
            ecartes["story_absente_de_epics"] += 1
            continue
        sec, retire = nettoyer(sec)
        retires_total += retire
        if len(sec) < 200:
            ecartes["spec_trop_courte"] += 1
            continue
        k = f"{depot}/{cle}"
        textes[k] = sec
        car = caracteristiques(sec)
        lignes_csv.append({
            "cle": k, "depot": depot, "story": cle, "debut": s["debut"], "source_epics": source,
            "appels": s["appels"], "agents": s["agents"], "cout_usd": round(s["cout"], 3),
            "mediane_depot": mediane[depot], "derapage": int(s["appels"] > o.facteur * mediane[depot]),
            "derapage_par_agent": int(max(s["appels_agent"]) > o.facteur * med_agent[depot]),
            "defaut_revue": defaut_revue(depot, cle), **car,
        })
    bilan["ecartes"] = dict(ecartes)
    bilan["stories_etiquetees"] = len(lignes_csv)
    bilan["lignes_post_dev_retirees"] = retires_total
    if not lignes_csv:
        print(json.dumps(bilan, ensure_ascii=False))
        return 1
    o.out_textes.parent.mkdir(parents=True, exist_ok=True)
    o.out_textes.write_text(json.dumps(textes, ensure_ascii=False), encoding="utf-8")
    with open(o.out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes_csv[0]))
        w.writeheader()
        w.writerows(lignes_csv)
    n = len(lignes_csv)
    bilan["taux_derapage"] = round(sum(r["derapage"] for r in lignes_csv) / n, 3)
    bilan["par_depot"] = {d: {"n": sum(1 for r in lignes_csv if r["depot"] == d), "mediane_appels": mediane[d],
                              "derapages": sum(r["derapage"] for r in lignes_csv if r["depot"] == d)} for d in sorted({r["depot"] for r in lignes_csv})}
    rev = [r["defaut_revue"] for r in lignes_csv if r["defaut_revue"] is not None]
    bilan["defaut_revue"] = {"n_lisible": len(rev), "taux": round(sum(rev) / len(rev), 3) if rev else None}
    print(json.dumps(bilan, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
