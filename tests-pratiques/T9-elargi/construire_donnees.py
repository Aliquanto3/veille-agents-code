"""T9 elargi : construit le jeu de stories etiquetees (spec pre-developpement + etiquettes) a partir de ``agents.json``.

Entrees
- ``<travail>/agents.json`` (``extraire_agents.py``) : agents ``dev-story`` (ere ``kit``) et, avec ``--avant-kit``, agents
  ``general-purpose`` de developpement d'avant le kit (ere ``avant-kit``), avec depot, numero de story, appels, cout, debut.
- Depots publics clones sous ``--racine-depots`` (defaut ``~/Documents/GitHub``) : ``_bmad-output/planning-artifacts/epics.md``
  (spec de chaque story) et ``_bmad-output/implementation-artifacts`` (revue ; spec de repli).

Sorties
- ``<travail>/textes.json`` {cle: texte de spec} : HORS du depot de veille, jamais ecrit dans le depot.
- ``etiquettes.csv`` (a cote du script) : cle, depot, appels, cout, etiquettes, caracteristiques numeriques ; aucun texte.
- ``bilan_donnees.json`` : agregats (nombre de stories, de positifs, d'ecartees, par depot).

Etiquettes (par groupe : les seuils se calculent sur toutes les stories numerotees du groupe, avant ecartement ; le groupe est
``<depot>`` pour l'ere kit et ``<depot>/avant-kit`` pour l'ere d'avant, car les deux processus n'ont pas le meme cout ; une story
presente dans les deux eres garde l'ere de son premier agent et additionne les appels et couts de tous ses agents)
- ``derapage``     : somme des appels propres des agents dev-story de la story > 2 x mediane des sommes par story du groupe ;
- ``cout80``       : cout (USD equivalent API) des agents dev-story de la story > 80e centile du groupe (comparaison stricte) ;
- ``defaut_revue`` : la revue a consigne au moins un constat de severite medium ou high retenu et traite (ni rejete, ni
                     reporte) ; vide si aucune revue lisible ;
- exploratoires ``derapage_par_agent`` (le plus long agent > 2 x mediane par agent du groupe) et ``haut20``
  (appels > 80e centile du groupe).

Anti-fuite : la spec est la section « Story X.Y » de ``epics.md`` au dernier commit anterieur au premier appel de
l'agent (``source_epics = avant``) ; faute de commit anterieur, la version de la fin du jour de demarrage (``jour``).
Repli (``source_spec = fichier``) : le fichier de story au dernier commit anterieur au developpement, sous-sections
post-developpement retirees. Une story sans spec (ou de moins de 200 caracteres) est ecartee.

Usage : uv run --no-project python construire_donnees.py --travail <dossier hors depot>
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

ICI = Path(__file__).resolve().parent
EPICS = "_bmad-output/planning-artifacts/epics.md"
ARTEFACTS = "_bmad-output/implementation-artifacts"

ENTETE_STORY = re.compile(r"^#{3,4} Story (\d+\.\d+[a-z]?)\b")
FIN_SECTION = re.compile(r"^(#{1,4} (Story|Epic) \d|#{1,2} )")
POST_DEV = re.compile(r"^#{1,4}\s*(Livr[ée]|Revue|Review|Dev Agent Record|File List|Change Log|Completion Notes|Reports?|Spec Change Log|Auto Run Result)\b", re.IGNORECASE)
CASE = re.compile(r"^\s*[-*] \[[ xX]\]")
CASE_COCHEE = re.compile(r"^\s*[-*] \[[xX]\]")
CHEMIN = re.compile(r"`([^`\s]*(?:/|\.(?:py|js|ts|tsx|yaml|yml|json|toml|md|css|html|sql|xlsx|pptx))[^`\s]*)`")

PUCE_REV = re.compile(r"^\s*[-*]\s*\**\s*(high|medium|haute?|moyen(?:ne)?)\b", re.IGNORECASE)
REJET = re.compile(r"rejet|[ée]cart|non\s+retenu|refus[ée]|faux", re.IGNORECASE)
REPORTE = re.compile(r"report[ée]|diff[ée]r[ée]|\bdefer|non\s+corrig", re.IGNORECASE)
TRIAGE_USINE = re.compile(r"^\s*[-*]\s*`\[(high|medium)\]`\s*`\[(patch|defer|bad_spec|intent_gap|decision|reject)\]", re.IGNORECASE)


def git(racine: Path, depot: str, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(racine / depot), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout


def versions(racine: Path, depot: str, chemin: str) -> list[tuple[datetime, str]]:
    out = git(racine, depot, "log", "--format=%H %cI", "--", chemin)
    v = []
    for ligne in out.splitlines():
        h, d = ligne.split(" ", 1)
        v.append((datetime.fromisoformat(d.strip()).astimezone(timezone.utc), h))
    return sorted(v)


def section(texte: str, cle: str) -> str | None:
    lignes = texte.splitlines()
    debut = next((i for i, l in enumerate(lignes) if (m := ENTETE_STORY.match(l)) and m.group(1) == cle), None)
    if debut is None:
        return None
    fin = next((j for j in range(debut + 1, len(lignes)) if FIN_SECTION.match(lignes[j])), len(lignes))
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


def caracteristiques(brut: str, propre: str) -> dict:
    """Caracteristiques de structure. Les taches (cases a cocher) sont comptees avant nettoyage (leur nombre, pas leur etat) ;
    les sections d'``epics.md`` n'en ont pas, d'ou ``n_puces`` (elements de liste), mesure de remplacement."""
    lignes = propre.splitlines()
    given = sum(1 for l in lignes if re.match(r"^\W*(Given|[ÉE]tant donn[ée]e?s?)\b", l.strip(), re.IGNORECASE))
    ac = sum(1 for l in lignes if re.match(r"^\W*AC[- ]?\d+\b", l.strip()))
    clauses = sum(1 for l in lignes if re.match(r"^\W*(Then|And|When|Alors|Et|Quand)\b", l.strip(), re.IGNORECASE))
    chemins = {c.strip(".,;:") for c in CHEMIN.findall(propre)}
    return {
        "n_car": len(propre), "n_mots": len(propre.split()), "n_criteres": given + ac, "n_clauses": clauses,
        "n_taches": sum(1 for l in brut.splitlines() if CASE.match(l)),
        "n_puces": sum(1 for l in propre.splitlines() if re.match(r"^\s*(?:[-*]|\d+[.)])\s+\S", l)),
        "n_fichiers": len(chemins), "n_codes": len(re.findall(r"`[^`]+`", propre)),
        "n_ad": len(set(re.findall(r"\bAD-\d+\b", propre))),
    }


def fichiers_story(racine: Path, depot: str, cle: str) -> list[Path]:
    d = racine / depot / ARTEFACTS
    if not d.is_dir():
        return []
    a, b = cle.split(".")
    if depot in ("wavedevsecops", "wavelibrarian"):
        motif = re.compile(rf"^{a}-{b}-.*\.md$")
    elif depot == "wavelocalai":
        motif = re.compile(rf"^story-{a}-{b}\.md$")
    else:
        motif = re.compile(rf"^spec-{a}-{b}-.*\.md$")
    return [f for f in sorted(d.glob("*.md")) if motif.match(f.name)]


def defaut_revue(racine: Path, depot: str, cle: str) -> int | None:
    """1 si la revue consigne un defaut medium ou high retenu et traite, 0 sinon, None si aucune revue lisible."""
    fichiers = fichiers_story(racine, depot, cle)
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
            tete = l[:200]
            if PUCE_REV.match(l) and not REJET.search(tete) and not REPORTE.search(tete):
                trouve = True
    if not revue_vue:
        return None
    return int(trouve)


def centile(valeurs: list[float], p: float) -> float:
    """Centile p (0-100) par interpolation lineaire, comme numpy.percentile."""
    v = sorted(valeurs)
    if len(v) == 1:
        return v[0]
    k = (len(v) - 1) * p / 100
    i = int(k)
    return v[i] + (v[min(i + 1, len(v) - 1)] - v[i]) * (k - i)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--travail", type=Path, required=True, help="dossier hors depot (agents.json en entree, textes.json en sortie)")
    ap.add_argument("--racine-depots", type=Path, default=Path.home() / "Documents" / "GitHub")
    ap.add_argument("--out-csv", type=Path, default=ICI / "etiquettes.csv")
    ap.add_argument("--facteur", type=float, default=2.0)
    o = ap.parse_args()

    agents = json.loads((o.travail / "agents.json").read_text(encoding="utf-8"))
    bilan: dict = {"agents_retenus": len(agents)}
    stories: dict[tuple[str, str], dict] = {}
    en_cours = {(a["depot"], a["story"]) for a in agents if a["story"] and a.get("en_cours")}
    bilan["stories_ecartees_en_cours"] = len(en_cours)
    for a in agents:
        if not a["story"] or (a["depot"], a["story"]) in en_cours:
            continue
        ere = a.get("ere", "kit")
        s = stories.setdefault((a["depot"], a["story"]), {"appels": 0, "agents": 0, "cout": 0.0, "debut": a["debut"], "appels_agent": [], "familles": set(),
                                                          "ere": ere, "eres": set()})
        s["eres"].add(ere)
        if a["debut"] < s["debut"]:  # l'ere est celle du premier agent de la story
            s["ere"] = ere
        s["appels"] += a["appels"]
        s["agents"] += 1
        s["cout"] += a["cout"]
        s["debut"] = min(s["debut"], a["debut"])
        s["appels_agent"].append(a["appels"])
        s["familles"].add(a.get("fam") or "?")
    bilan["stories_avec_numero"] = len(stories)
    avant_kit = any(a.get("ere", "kit") == "avant-kit" for a in agents)

    def groupe_de(depot: str, s: dict) -> str:
        return depot if s["ere"] == "kit" else f"{depot}/avant-kit"

    par_depot = defaultdict(list)
    for (depot, _), s in stories.items():
        par_depot[groupe_de(depot, s)].append(s)
    seuils = {}
    for d, lst in par_depot.items():
        seuils[d] = {
            "mediane_appels": statistics.median(s["appels"] for s in lst),
            "mediane_appels_agent": statistics.median(x for s in lst for x in s["appels_agent"]),
            "p80_cout": centile([s["cout"] for s in lst], 80),
            "p80_appels": centile([s["appels"] for s in lst], 80),
            "n": len(lst),
        }

    cache_versions: dict[tuple[str, str], list] = {}
    cache_texte: dict[str, str] = {}

    def versions_cache(depot: str, chemin: str):
        if (depot, chemin) not in cache_versions:
            cache_versions[(depot, chemin)] = versions(o.racine_depots, depot, chemin)
        return cache_versions[(depot, chemin)]

    def contenu(depot: str, h: str, chemin: str) -> str:
        k = f"{depot}@{h}:{chemin}"
        if k not in cache_texte:
            cache_texte[k] = git(o.racine_depots, depot, "show", f"{h}:{chemin}")
        return cache_texte[k]

    def choisir(vs, debut):
        """(hash, source) : dernier commit strictement avant le debut, sinon fin du jour de demarrage."""
        av = [h for (d, h) in vs if d < debut]
        if av:
            return av[-1], "avant"
        fin_jour = debut.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        jr = [h for (d, h) in vs if d <= fin_jour]
        return (jr[-1], "jour") if jr else (None, None)

    textes, lignes_csv = {}, []
    ecartes = defaultdict(int)
    retires_total = 0
    for (depot, cle), s in sorted(stories.items()):
        debut = datetime.fromisoformat(s["debut"].replace("Z", "+00:00")).astimezone(timezone.utc)
        brut = sec = None
        source_spec = source = None
        h, source = choisir(versions_cache(depot, EPICS), debut)
        if h:
            brut = section(contenu(depot, h, EPICS), cle)
            if brut:
                source_spec = "epics"
        if not brut:  # repli : fichier de story
            for f in fichiers_story(o.racine_depots, depot, cle):
                chemin = f"{ARTEFACTS}/{f.name}"
                h2, src2 = choisir(versions_cache(depot, chemin), debut)
                if h2 and src2 == "avant":
                    brut, source, source_spec = contenu(depot, h2, chemin), src2, "fichier"
                    break
        if not brut:
            ecartes["sans_spec_ante_dev"] += 1
            continue
        sec, retire = nettoyer(brut)
        retires_total += retire
        if len(sec) < 200:
            ecartes["spec_trop_courte"] += 1
            continue
        k = f"{depot}/{cle}"
        textes[k] = sec
        groupe = groupe_de(depot, s)
        t = seuils[groupe]
        lignes_csv.append({
            "cle": k, "depot": depot, "groupe": groupe, "story": cle, "debut": s["debut"], "source_epics": source, "source_spec": source_spec,
            "appels": s["appels"], "agents": s["agents"], "cout_usd": round(s["cout"], 3), "familles": "+".join(sorted(s["familles"])),
            "mediane_depot": t["mediane_appels"], "p80_cout_depot": round(t["p80_cout"], 3),
            "derapage": int(s["appels"] > o.facteur * t["mediane_appels"]),
            "cout80": int(s["cout"] > t["p80_cout"]),
            "derapage_par_agent": int(max(s["appels_agent"]) > o.facteur * t["mediane_appels_agent"]),
            "haut20": int(s["appels"] > t["p80_appels"]),
            "defaut_revue": defaut_revue(o.racine_depots, depot, cle),
            **caracteristiques(brut, sec),
        })
    bilan["ecartes"] = dict(ecartes)
    bilan["stories_etiquetees"] = len(lignes_csv)
    bilan["lignes_post_dev_retirees"] = retires_total
    if not lignes_csv:
        print(json.dumps(bilan, ensure_ascii=False))
        return 1
    o.travail.mkdir(parents=True, exist_ok=True)
    (o.travail / "textes.json").write_text(json.dumps(textes, ensure_ascii=False), encoding="utf-8")
    with open(o.out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes_csv[0]))
        w.writeheader()
        w.writerows(lignes_csv)
    for e in ("derapage", "cout80", "derapage_par_agent", "haut20"):
        bilan[f"positifs_{e}"] = sum(r[e] for r in lignes_csv)
    rev = [r["defaut_revue"] for r in lignes_csv if r["defaut_revue"] is not None]
    bilan["defaut_revue"] = {"n_lisible": len(rev), "positifs": sum(rev)}
    bilan["source_spec"] = {k: sum(1 for r in lignes_csv if r["source_spec"] == k) for k in ("epics", "fichier")}
    bilan["source_epics"] = {k: sum(1 for r in lignes_csv if r["source_epics"] == k) for k in ("avant", "jour")}
    bilan["par_depot"] = {d: {"n": sum(1 for r in lignes_csv if r["groupe"] == d), "stories_numerotees": seuils[d]["n"],
                              "mediane_appels": seuils[d]["mediane_appels"], "p80_cout_usd": round(seuils[d]["p80_cout"], 2),
                              "derapages": sum(r["derapage"] for r in lignes_csv if r["groupe"] == d),
                              "cout80": sum(r["cout80"] for r in lignes_csv if r["groupe"] == d)}
                          for d in sorted({r["groupe"] for r in lignes_csv})}
    if avant_kit:
        etiquetees = {r["cle"] for r in lignes_csv}
        deux = [(d, c) for (d, c), s in stories.items() if len(s["eres"]) > 1]
        bilan["stories_dans_les_deux_eres"] = {"total": len(deux), "etiquetees": sum(1 for d, c in deux if f"{d}/{c}" in etiquetees),
                                               "ere_retenue_avant_kit": sum(1 for d, c in deux if stories[(d, c)]["ere"] == "avant-kit")}
        bilan["par_ere"] = {e: {"stories_numerotees": sum(1 for s in stories.values() if s["ere"] == e),
                                "etiquetees": sum(1 for r in lignes_csv if r["groupe"].endswith("/avant-kit") == (e == "avant-kit")),
                                "derapages": sum(r["derapage"] for r in lignes_csv if r["groupe"].endswith("/avant-kit") == (e == "avant-kit")),
                                "defaut_revue_lisible": sum(1 for r in lignes_csv if r["defaut_revue"] is not None and r["groupe"].endswith("/avant-kit") == (e == "avant-kit")),
                                "source_spec_fichier": sum(1 for r in lignes_csv if r["source_spec"] == "fichier" and r["groupe"].endswith("/avant-kit") == (e == "avant-kit")),
                                "source_epics_jour": sum(1 for r in lignes_csv if r["source_epics"] == "jour" and r["groupe"].endswith("/avant-kit") == (e == "avant-kit"))}
                           for e in ("kit", "avant-kit")}
    (ICI / "bilan_donnees.json").write_text(json.dumps(bilan, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(bilan, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
