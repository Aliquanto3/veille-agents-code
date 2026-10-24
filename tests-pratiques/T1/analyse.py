"""T1 : analyse des transcriptions locales de Claude Code (questions 1 a 4 et 6), un seul passage en flux.

Un seul processus, sequentiel, ligne par ligne : aucun gros fichier n'est charge en memoire. Seules les
lignes utiles sont decodees (assistant, user, attachment, api-request, api-request-shape) ; les blobs
``api-request-blob`` (les plus volumineux) sont ignores sans etre analyses.

La logique de ``agent-cost-kit/scripts/mesurer_couts.py`` est reutilisee, pas recopiee : prix
(``prix``, ``ECRITURE``, ``GEO_US_FACTEUR``), familles de modeles, lecture des horodatages, sortie
reestimee a ``CARACTERES_PAR_TOKEN``. Dedoublonnage par ``message.id`` : chaque reponse n'est comptee qu'une
fois, dans la transcription qui a demarre en premier ; les reponses recopiees par une reprise restent le
« precedent » pour les pauses. Idem pour les resultats d'outils (``tool_use_id``).

Usage :
    uv run --no-project python -I analyse.py --out agregats.json [--jours 45] [--detail-dir <dossier hors depot>]

Confidentialite : ``agregats.json`` ne contient que des nombres et des noms d'outils ou d'agents ; les noms de
projets sont ramenes a une liste blanche (depots publics) ou « autre ». Le detail par agent
(``--detail-dir``) est a garder hors du depot.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

KIT = Path.home() / "Documents" / "GitHub" / "agent-cost-kit" / "scripts" / "mesurer_couts.py"
RACINE = Path.home() / ".claude" / "projects"
PUBLICS = ["agent-cost-kit", "wavestack", "wavedevsecops", "wavelocalai", "slm-quality-bench",
           "usine-migration-jira-demo", "veille-agents-code", "WaveEval", "claude-code-mods"]
PREFIXE_DOSSIER = "C--Users-Utilisateur-Documents-GitHub-"
CAR_PAR_TOKEN_ENTREE = 3.5  # regle de la veille pour les resultats d'outils (l'entree n'est pas la sortie, 2,2)
TOKENS_IMAGE = 1500  # approximation d'une image dans un tool_result
SEUILS_PAUSE = [300, 900, 1800, 3600]  # secondes
# fichiers d'etat d'un run autonome ou de nuit, dans _bmad-output/implementation-artifacts du depot
MOTIFS_RUN_AUTONOME = ["*run-autonome*.md", "etat-run*.md", "etat-nuit*.md", "rapport-de-nuit*.md", "journal-decisions-nuit*.md"]
GROUPES_OUTILS = {"Bash": "Shell", "PowerShell": "Shell"}

spec = importlib.util.spec_from_file_location("mesurer_couts", KIT)
mc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc)  # type: ignore[union-attr]


def projet_public(dossier: str) -> str:
    nom = dossier[len(PREFIXE_DOSSIER):] if dossier.startswith(PREFIXE_DOSSIER) else dossier
    return nom if nom in PUBLICS else "autre"


def instant_s(texte: str) -> float:
    return mc.instant(texte).timestamp()


def prix_eff(modele: str, ctx: int, geo) -> tuple[float, float, float]:
    """(entree, sortie, lecture) en $/Mtok avec le multiplicateur de long contexte et de zone, comme ``couts``."""
    t = mc.prix(modele)
    p_e, p_s, p_l = t["entree"], t["sortie"], t["lecture"]
    long = t.get("long_contexte")
    if long and ctx > long["seuil_tokens"]:
        p_e, p_s, p_l = (p * long["facteur"] for p in (p_e, p_s, p_l))
    if geo == "us" and t.get("geo_us", True):
        p_e, p_s, p_l = (p * mc.GEO_US_FACTEUR for p in (p_e, p_s, p_l))
    return p_e, p_s, p_l


def cout_appel(modele: str, entree: int, e5: int, e1h: int, lu: int, sortie: int, geo) -> dict[str, float]:
    p_e, p_s, p_l = prix_eff(modele, entree + e5 + e1h + lu, geo)
    return {
        "entree": entree * p_e / 1e6,
        "ecriture": (e5 * mc.ECRITURE["5m"] + e1h * mc.ECRITURE["1h"]) * p_e / 1e6,
        "lecture": lu * p_l / 1e6,
        "sortie": sortie * p_s / 1e6,
    }


CATEGORIES_COMMANDE = [
    ("tests_lint", re.compile(r"\b(pytest|vitest|jest|mocha|cargo test|go test|npm (?:run )?test|ruff|mypy|pyright|eslint|tsc|playwright test|dotnet test|node --test)\b")),
    ("gh", re.compile(r"\bgh\b")),
    ("git", re.compile(r"\bgit\b")),
    ("python", re.compile(r"\b(python|uv run|uv sync|uv pip|pip)\b")),
    ("recherche", re.compile(r"\b(grep|rg|find|Select-String|findstr)\b")),
    ("lecture_fichier", re.compile(r"\b(cat|head|tail|sed|awk|Get-Content|type|more)\b")),
    ("liste", re.compile(r"\b(ls|dir|tree|Get-ChildItem|Test-Path|Get-Item|wc|stat)\b")),
]
PREMIER_MOT = {
    "git": "git", "gh": "gh", "grep": "recherche", "rg": "recherche", "find": "recherche", "Select-String": "recherche", "findstr": "recherche",
    "cat": "lecture_fichier", "head": "lecture_fichier", "tail": "lecture_fichier", "sed": "lecture_fichier", "awk": "lecture_fichier",
    "Get-Content": "lecture_fichier", "type": "lecture_fichier", "more": "lecture_fichier",
    "ls": "liste", "dir": "liste", "tree": "liste", "Get-ChildItem": "liste", "Test-Path": "liste", "wc": "liste", "stat": "liste",
    "sleep": "attente", "Start-Sleep": "attente", "timeout": "attente",
}
PREFIXE_COMMANDE = re.compile(r"^\s*(?:cd [^&;|]+(?:&&|;)|Set-Location [^&;|]+(?:&&|;)|export \S+=\S*(?:&&|;)|\$env:\S+\s*=\s*\S+;)\s*")


def categorie_commande(cmd: str) -> str:
    """Categorie grossiere d'une commande Shell (premier mot, sinon motifs) ; seul le nom de la categorie est conserve."""
    cmd = cmd.strip()
    while True:
        court = PREFIXE_COMMANDE.sub("", cmd, count=1)
        if court == cmd:
            break
        cmd = court
    mots = re.split(r"[\s|;&]+", cmd, maxsplit=1)
    premier = mots[0] if mots else ""
    if premier in PREMIER_MOT:
        return PREMIER_MOT[premier]
    for nom, motif in CATEGORIES_COMMANDE[:4]:
        if motif.search(cmd):
            return nom
    for nom, motif in CATEGORIES_COMMANDE[4:]:
        if motif.search(cmd):
            return nom
    return "autre"


def texte_resultat(contenu) -> tuple[int, int]:
    """(caracteres de texte, nombre d'images) d'un tool_result."""
    if isinstance(contenu, str):
        return len(contenu), 0
    car = img = 0
    for b in contenu or []:
        if not isinstance(b, dict):
            continue
        t = b.get("type")
        if t == "text":
            car += len(b.get("text", ""))
        elif t == "image":
            img += 1
        else:
            car += len(json.dumps(b, ensure_ascii=False))
    return car, img


def texte_utilisateur(contenu) -> int:
    if isinstance(contenu, str):
        return len(contenu)
    return sum(len(b.get("text", "")) for b in contenu or [] if isinstance(b, dict) and b.get("type") == "text")


def premiere_ts(chemin: Path, limite: float) -> float | None:
    motif = re.compile(r'"timestamp":"([^"]+)"')
    with open(chemin, encoding="utf-8", errors="replace") as f:
        for i, ligne in enumerate(f):
            m = motif.search(ligne[:4000]) if not ligne.startswith('{"type":"api-request-blob"') else None
            if m:
                return instant_s(m.group(1))
            if i > 200:
                break
    return None


def lire_fichier(chemin: Path, deja_ids: set, deja_tu: set, coupure: float) -> dict | None:
    """Un passage en flux sur une transcription ; retourne un resume compact (pas de contenu)."""
    appels: dict[str, dict] = {}
    ordre: list[str] = []
    noms_outil: dict[str, str] = {}
    cat_commande: dict[str, str] = {}
    appels_outil: Counter = Counter()
    resultats: list[tuple] = []  # (outil, caracteres, images, appels_avant, categorie de commande)
    formes: dict[str, dict] = {}
    req_par_forme: Counter = Counter()
    pre = {"att": Counter(), "user": 0, "meta": 0}
    avant_premier = True
    cwd = None
    tu_fichier: set[str] = set()
    ignores = Counter()
    with open(chemin, encoding="utf-8", errors="replace") as f:
        for ligne in f:
            if ligne.startswith('{"type":"api-request-shape"'):
                try:
                    e = json.loads(ligne)
                except ValueError:
                    continue
                ts = instant_s(e["timestamp"]) if e.get("timestamp") else 0
                if ts and ts < coupure:
                    continue
                forme = e.get("shape") or {}
                outils = []
                for o in forme.get("tools") or []:
                    outils.append((o.get("name") or o.get("type") or "?", len(json.dumps(o, ensure_ascii=False)), bool(o.get("defer_loading"))))
                formes[e.get("shapeHash", "")] = {
                    "systeme": sum(len(s.get("text", "")) for s in forme.get("system") or [] if isinstance(s, dict)),
                    "outils": outils,
                }
                continue
            if ligne.startswith('{"type":"api-request",'):
                try:
                    e = json.loads(ligne)
                except ValueError:
                    continue
                ts = instant_s(e["timestamp"]) if e.get("timestamp") else 0
                if ts and ts < coupure:
                    continue
                req_par_forme[e.get("shapeHash", "")] += 1
                continue
            if not ligne.startswith('{"parentUuid"'):
                ignores[ligne[:20]] += 1
                continue
            try:
                e = json.loads(ligne)
            except ValueError:
                continue
            ts_txt = e.get("timestamp") or ""
            if cwd is None and e.get("cwd"):
                cwd = e["cwd"]
            typ = e.get("type")
            message = e.get("message") or {}
            if typ == "attachment":
                if avant_premier:
                    a = e.get("attachment") or {}
                    pre["att"][a.get("type", "?")] += len(json.dumps(a, ensure_ascii=False))
                continue
            if typ == "assistant" and message.get("id"):
                if not ts_txt or instant_s(ts_txt) < coupure:
                    continue
                fam = mc.famille(str(message.get("model", "")))
                if fam is None:
                    continue
                avant_premier = False
                mid = message["id"]
                a = appels.get(mid)
                if a is None:
                    a = appels[mid] = {"fam": fam, "modele": str(message.get("model", "")), "ts": ts_txt, "car": 0, "u": {}, "outils": []}
                    ordre.append(mid)
                for b in message.get("content") or []:
                    if not isinstance(b, dict):
                        continue
                    t = b.get("type")
                    if t == "text":
                        a["car"] += len(b.get("text", ""))
                    elif t == "thinking":
                        a["car"] += len(b.get("thinking", ""))
                    elif t == "tool_use":
                        a["car"] += len(json.dumps(b.get("input"), ensure_ascii=False))
                        if b.get("id") and b["id"] not in noms_outil:
                            noms_outil[b["id"]] = b.get("name", "?")
                            if b.get("name") in ("Bash", "PowerShell"):
                                cat_commande[b["id"]] = categorie_commande(str((b.get("input") or {}).get("command", "")))
                            a["outils"].append(b.get("name", "?"))
                usage = message.get("usage") or {}
                if usage and int(usage.get("output_tokens") or 0) >= int(a["u"].get("output_tokens") or 0):
                    a["u"] = usage
                continue
            if typ == "user":
                if ts_txt and instant_s(ts_txt) < coupure:
                    continue
                contenu = message.get("content")
                if avant_premier:
                    n = texte_utilisateur(contenu)
                    pre["meta" if e.get("isMeta") else "user"] += n
                if isinstance(contenu, list):
                    for b in contenu:
                        if isinstance(b, dict) and b.get("type") == "tool_result":
                            tid = b.get("tool_use_id", "")
                            if tid in deja_tu:
                                continue
                            car, img = texte_resultat(b.get("content"))
                            resultats.append((noms_outil.get(tid, "inconnu"), car, img, len(ordre), cat_commande.get(tid)))
    tu_fichier = set(noms_outil)
    if not ordre:
        return None
    liste = []
    for mid in ordre:
        a = appels[mid]
        u = a["u"]
        ecrit = int(u.get("cache_creation_input_tokens") or 0)
        e1h = int((u.get("cache_creation") or {}).get("ephemeral_1h_input_tokens") or 0)
        decl = int(u.get("output_tokens") or 0)
        liste.append({
            "id": mid, "fam": a["fam"], "modele": a["modele"], "geo": u.get("inference_geo"),
            "t": instant_s(a["ts"]), "ts": a["ts"],
            "entree": int(u.get("input_tokens") or 0), "e5": ecrit - e1h, "e1h": e1h,
            "lu": int(u.get("cache_read_input_tokens") or 0),
            "sortie": max(decl, int(a["car"] / mc.CARACTERES_PAR_TOKEN)),
            "propre": mid not in deja_ids, "outils": a["outils"],
        })
    liste.sort(key=lambda a: a["t"])
    return {
        "appels": liste, "resultats": resultats, "formes": formes, "req_par_forme": req_par_forme,
        "pre": pre, "cwd": cwd, "ids": set(ordre), "tu": tu_fichier, "ignores": ignores,
        "n_total": len(ordre),
    }


def quartiles(v: list[float]) -> dict:
    if not v:
        return {"n": 0}
    s = sorted(v)
    q = statistics.quantiles(s, n=4, method="inclusive") if len(s) >= 2 else [s[0]] * 3
    return {"n": len(s), "q1": round(q[0]), "mediane": round(q[1]), "q3": round(q[2]), "min": round(s[0]), "max": round(s[-1])}


def racine_depot(cwd: str | None) -> Path | None:
    if not cwd:
        return None
    p = Path(cwd)
    parts = list(p.parts)
    if ".claude" in parts:
        p = Path(*parts[: parts.index(".claude")])
    for cand in [p, *p.parents]:
        try:
            if (cand / ".git").exists() or (cand / "_bmad-output").exists():
                return cand
        except OSError:
            return None
        if cand.parent == cand:
            break
    return None


def simuler_q6(agents: list[dict], sessions: Counter) -> dict:
    """Critere d'arret : couper un agent dev-story a ``k`` x la mediane de ses appels (``k`` = 1,5 ; 2 ; 3)."""

    def un_jeu(lot: list[dict]) -> dict:
        if not lot:
            return {"n": 0}
        mediane = statistics.median(a["appels"] for a in lot)
        total = sum(a["cout"] for a in lot)
        sortie = {"n_agents": len(lot), "appels": quartiles([a["appels"] for a in lot]), "cout_total_usd": round(total, 2),
                  "cout_agent_usd_mediane": round(statistics.median(a["cout"] for a in lot), 2), "mediane_appels": mediane, "coupures": {}}
        for k in (1.5, 2, 3):
            plafond = int(k * mediane)
            coupes = [a for a in lot if a["appels"] > plafond]
            eco = sum(sum(a["cout_appels"][plafond:]) for a in coupes)
            sortie["coupures"][str(k)] = {
                "plafond_appels": plafond, "agents_coupes": len(coupes), "part_coupes": round(len(coupes) / len(lot), 3),
                "economie_usd": round(eco, 2), "part_cout": round(eco / total, 3) if total else 0,
                "appels_economises": sum(a["appels"] - plafond for a in coupes),
            }
        return sortie

    res = {
        "tous": un_jeu(agents),
        "repos_run_autonome": un_jeu([a for a in agents if a["run_autonome"]]),
        "sonnet_seul": un_jeu([a for a in agents if a["fam"] == "sonnet"]),
        "sonnet_repos_run_autonome": un_jeu([a for a in agents if a["fam"] == "sonnet" and a["run_autonome"]]),
        "sessions_3_stories_ou_plus": un_jeu([a for a in agents if sessions[(a["dossier"], a["session"])] >= 3]),
    }
    # par story (agents reprises regroupes) quand le numero est lisible dans la description
    par_story: dict = defaultdict(lambda: {"appels": 0, "cout": 0.0, "cout_appels": [], "agents": 0, "run_autonome": False})
    for a in agents:
        cle = (a["dossier"], a["story"]) if a["story"] else (a["dossier"], a["agent"])
        s = par_story[cle]
        s["appels"] += a["appels"]
        s["cout"] += a["cout"]
        s["cout_appels"] += a["cout_appels"]
        s["agents"] += 1
        s["run_autonome"] |= a["run_autonome"]
    res["par_story_tous"] = un_jeu([dict(v, dossier="", session="") for v in par_story.values()])
    res["stories_a_plusieurs_agents"] = sum(1 for v in par_story.values() if v["agents"] > 1)
    # plafond a 2 x la mediane de son propre depot (>= 5 agents), sinon de l'ensemble
    mediane_globale = statistics.median(a["appels"] for a in agents)
    par_depot: dict = defaultdict(list)
    for a in agents:
        par_depot[a["dossier"]].append(a)
    total = eco = coupes = evites = 0
    for lot in par_depot.values():
        m = statistics.median(a["appels"] for a in lot) if len(lot) >= 5 else mediane_globale
        plafond = int(2 * m)
        for a in lot:
            total += a["cout"]
            if a["appels"] > plafond:
                coupes += 1
                eco += sum(a["cout_appels"][plafond:])
                evites += a["appels"] - plafond
    res["mediane_par_depot_x2"] = {"n_depots": len(par_depot), "agents_coupes": coupes, "part_coupes": round(coupes / len(agents), 3),
                                   "economie_usd": round(eco, 2), "part_cout": round(eco / total, 3), "appels_economises": evites}
    res["par_depot_mediane_appels"] = {str(i): {"n": len(l), "mediane": statistics.median(a["appels"] for a in l)}
                                       for i, l in enumerate(sorted(par_depot.values(), key=len, reverse=True))}
    res["par_modele"] = dict(Counter(a["fam"] for a in agents))
    return res


def main() -> int:
    for flux in (sys.stdout, sys.stderr):
        flux.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).with_name("agregats.json"))
    ap.add_argument("--jours", type=int, default=45)
    ap.add_argument("--detail-dir", type=Path, help="detail par agent (hors depot)")
    ap.add_argument("--limite-fichiers", type=int, default=0, help="debug : n premiers fichiers")
    o = ap.parse_args()

    maintenant = datetime.now(timezone.utc)
    coupure = (maintenant - timedelta(days=o.jours)).timestamp()
    fichiers = []
    for d in sorted(RACINE.iterdir()):
        if not d.is_dir():
            continue
        for f in d.glob("*.jsonl"):
            fichiers.append((d.name, f.stem, "MAIN", f))
        for f in d.glob("*/subagents/agent-*.jsonl"):
            fichiers.append((d.name, f.parent.parent.name, f.stem[len("agent-"):], f))
    fichiers = [x for x in fichiers if x[3].stat().st_mtime >= coupure]
    debut = []
    for x in fichiers:
        t = premiere_ts(x[3], coupure)
        debut.append((t if t is not None else 1e18, x))
    debut.sort(key=lambda z: (z[0], z[1][2] != "MAIN", str(z[1][3])))
    fichiers = [z[1] for z in debut]
    if o.limite_fichiers:
        fichiers = fichiers[: o.limite_fichiers]

    deja_ids: set[str] = set()
    deja_tu: set[str] = set()
    t0 = time.time()

    # accumulateurs
    q1 = defaultdict(list)  # (genre, mois|tous, type) -> [(entree+ecriture, ctx_total)]
    q1_pre = defaultdict(lambda: defaultdict(list))  # genre -> composant -> [tokens estimes]
    q1_ex = Counter()
    q1_formes = defaultdict(lambda: defaultdict(list))
    q1_types = defaultdict(lambda: defaultdict(list))
    q2_present = defaultdict(lambda: Counter())  # outil -> compteurs
    q2_taille: dict[str, int] = {}
    q2_expo = defaultdict(float)  # outil -> cout $ equivalent de sa definition (chargee)
    q2_expo_tok = defaultdict(float)
    q2_ecr = defaultdict(float)
    cout_couvert = 0.0
    cout_par_type = defaultdict(Counter)
    q4_type = defaultdict(Counter)
    appels_outil = defaultdict(Counter)  # genre -> outil -> n
    q3 = defaultdict(lambda: defaultdict(lambda: Counter()))  # genre -> groupe -> compteurs
    q3_cmd = defaultdict(Counter)
    d_tokens = defaultdict(Counter)  # genre -> entree/ecrit/lu/sortie owned
    q4 = defaultdict(lambda: defaultdict(float))
    q6_agents = []
    couts_total = defaultdict(float)
    n_fichiers = Counter()
    depots: dict[str, Path | None] = {}
    inconnus_forme = 0
    total_requetes = 0
    ignores_tot = Counter()
    sessions_devstory = Counter()

    for dossier, session, ident, chemin in fichiers:
        meta = {}
        if ident != "MAIN":
            mp = chemin.with_suffix(".meta.json")
            try:
                meta = json.loads(mp.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                meta = {}
        genre = "principale" if ident == "MAIN" else "sous-agent"
        type_agent = "MAIN" if ident == "MAIN" else str(meta.get("agentType", "?"))
        r = lire_fichier(chemin, deja_ids, deja_tu, coupure)
        if r is None:
            continue
        n_fichiers[genre] += 1
        ignores_tot.update(r["ignores"])
        appels = r["appels"]
        propres = [a for a in appels if a["propre"]]
        projet = projet_public(dossier)
        # ---- Q1 : premier appel (la premiere reponse du fichier doit etre propre : session neuve)
        premier = appels[0]
        if premier["propre"]:
            mois = premier["ts"][:7]
            ctx_u = premier["entree"] + premier["e5"] + premier["e1h"]
            ctx_t = ctx_u + premier["lu"]
            sem = datetime.fromisoformat(premier["ts"].replace("Z", "+00:00")).isocalendar()
            for cle in ((genre, "tous", "tous"), (genre, mois, "tous"), (genre, f"S{sem[0]}-{sem[1]:02d}", "tous"), (genre, "tous", type_agent), (genre, "tous", "fam:" + premier["fam"])):
                q1[cle].append((ctx_u, ctx_t))
            # composition estimee (caracteres -> tokens, 3,5)
            if r["formes"]:
                forme0 = next(iter(r["formes"].values()))
                charges = [o_ for o_ in forme0["outils"] if not o_[2]]
                q1_formes[genre]["systeme"].append(forme0["systeme"] / CAR_PAR_TOKEN_ENTREE)
                q1_formes[genre]["outils_charges"].append(sum(o_[1] for o_ in charges) / CAR_PAR_TOKEN_ENTREE)
                q1_formes[genre]["n_outils_charges"].append(len(charges))
                q1_formes[genre]["n_outils_differes"].append(len(forme0["outils"]) - len(charges))
                q1_formes[genre]["ctx_utile"].append(ctx_u)
                cp = q1_types[type_agent]
                cp["outils_charges"].append(sum(o_[1] for o_ in charges) / CAR_PAR_TOKEN_ENTREE)
                cp["n_outils_charges"].append(len(charges))
                cp["ctx_total"].append(ctx_t)
                pre = r["pre"]
                q1_formes[genre]["prompt_initial"].append(pre["user"] / CAR_PAR_TOKEN_ENTREE)
                q1_formes[genre]["rappels_meta"].append(pre["meta"] / CAR_PAR_TOKEN_ENTREE)
                for t_att, n in pre["att"].items():
                    q1_pre[genre][t_att].append(n / CAR_PAR_TOKEN_ENTREE)
                q1_formes[genre]["attachments_total"].append(sum(pre["att"].values()) / CAR_PAR_TOKEN_ENTREE)
        else:
            q1_ex[genre] += 1
        # ---- couts et denominateurs
        tarif_fichier = mc.prix(premier["modele"])
        for a in propres:
            c = cout_appel(a["modele"], a["entree"], a["e5"], a["e1h"], a["lu"], a["sortie"], a["geo"])
            a["cout"] = c
            for k, v in c.items():
                couts_total[(genre, k)] += v
            d_tokens[genre]["entree"] += a["entree"]
            d_tokens[genre]["ecrit"] += a["e5"] + a["e1h"]
            d_tokens[genre]["lu"] += a["lu"]
            d_tokens[genre]["sortie"] += a["sortie"]
            d_tokens[genre]["appels"] += 1
            for nom in a["outils"]:
                appels_outil[genre][nom] += 1
        ct = cout_par_type[type_agent.split(":")[-1]]
        ct["agents"] += 1
        ct["appels"] += len(propres)
        ct["cout"] += sum(sum(a["cout"].values()) for a in propres)
        if r["formes"]:
            cout_couvert += sum(sum(a["cout"].values()) for a in propres)
        # ---- Q2 : outils presents (definitions) et exposition
        presents: dict[str, tuple[int, bool]] = {}
        expo_requetes: Counter = Counter()
        for h, forme in r["formes"].items():
            n_req = r["req_par_forme"].get(h, 0)
            for nom, taille, diff in forme["outils"]:
                p = presents.get(nom)
                if p is None or (p[1] and not diff):
                    presents[nom] = (taille, diff)
                if not diff:
                    expo_requetes[nom] += n_req
                    q2_taille[nom] = max(q2_taille.get(nom, 0), taille)
                    tok = taille / CAR_PAR_TOKEN_ENTREE
                    q2_expo_tok[nom] += tok * n_req
                    q2_expo[nom] += tok * n_req * tarif_fichier["lecture"] / 1e6
                    q2_ecr[nom] += tok * mc.ECRITURE["5m"] * tarif_fichier["entree"] / 1e6
        if r["formes"]:
            n_fichiers[genre + ":avec_definitions_outils"] += 1
        total_requetes += sum(r["req_par_forme"].values())
        inconnus_forme += sum(n for h, n in r["req_par_forme"].items() if h not in r["formes"])
        appeles = {nom for a in propres for nom in a["outils"]}
        for nom, (taille, diff) in presents.items():
            c = q2_present[nom]
            c[f"{genre}:fichiers_presents"] += 1
            if not diff:
                c[f"{genre}:fichiers_charges"] += 1
            if nom in appeles:
                c[f"{genre}:fichiers_appeles"] += 1
        for nom in appeles - set(presents):
            q2_present[nom][f"{genre}:appele_sans_definition"] += 1
        # ---- Q3 : resultats d'outils
        total_appels_fichier = r["n_total"]
        for nom, car, img, avant, cat in r["resultats"]:
            g = GROUPES_OUTILS.get(nom, nom if not nom.startswith("mcp__") else "MCP")
            restant = max(0, total_appels_fichier - avant)
            tok = car / CAR_PAR_TOKEN_ENTREE + img * TOKENS_IMAGE
            c = q3[genre][g]
            c["n"] += 1
            c["car"] += car
            c["img"] += img
            c["tok_reads"] += tok * restant
            c["cout"] += tok * (mc.ECRITURE["5m"] * tarif_fichier["entree"] + restant * tarif_fichier["lecture"]) / 1e6
            c["nul"] += 1 if car == 0 and img == 0 else 0
            c["gros_10k"] += 1 if tok > 10_000 else 0
            if cat:
                cc = q3_cmd[cat]
                cc["n"] += 1
                cc["car"] += car
                cc["cout"] += tok * (mc.ECRITURE["5m"] * tarif_fichier["entree"] + restant * tarif_fichier["lecture"]) / 1e6
        # ---- Q4 : pauses (le precedent peut etre une reponse recopiee)
        seuil_genre = 3600 if genre == "principale" else 300
        prec = None
        for a in appels:
            ecrit = a["e5"] + a["e1h"]
            ctx = a["entree"] + ecrit + a["lu"]
            if a["propre"]:
                c = a["cout"]
                q4[genre]["ecrit_tok"] += ecrit
                q4[genre]["ecrit_cout"] += c["ecriture"]
                q4[genre]["appels"] += 1
                if prec is None:
                    q4[genre]["ecrit_tok_premier"] += ecrit
                    q4[genre]["ecrit_cout_premier"] += c["ecriture"]
                else:
                    pause = a["t"] - prec["t"]
                    nouveau = max(0, ctx - prec["ctx"])
                    reecrit = max(0, ecrit - nouveau)
                    ttl = "1h" if a["e1h"] > a["e5"] else "5m"
                    q4[genre][f"ttl_{ttl}_ecrit_tok"] += ecrit
                    p_e, _, p_l = prix_eff(a["modele"], ctx, a["geo"])
                    if 300 < pause <= 3600 and a["e5"] > a["e1h"]:
                        # TTL 1 h : la pause n'expirerait pas, la reecriture deviendrait une lecture
                        q4[genre]["ctf1h_gain_pause_5m_a_1h"] += reecrit * (mc.ECRITURE["5m"] * p_e - p_l) / 1e6
                        q4_type[type_agent.split(":")[-1]]["gain"] += reecrit * (mc.ECRITURE["5m"] * p_e - p_l) / 1e6
                    # cout d'ecriture proportionnel
                    prix_ecr = c["ecriture"] / ecrit if ecrit else 0
                    for s in SEUILS_PAUSE:
                        if pause > s:
                            q4[genre][f"s{s}_appels"] += 1
                            q4[genre][f"s{s}_ecrit_tok"] += ecrit
                            q4[genre][f"s{s}_ecrit_cout"] += c["ecriture"]
                            q4[genre][f"s{s}_reecrit_tok"] += reecrit
                            q4[genre][f"s{s}_reecrit_cout"] += reecrit * prix_ecr
                    if ecrit > 20_000 and pause > mc.TTL_S[ttl]:
                        q4[genre]["exp_ttl_propre_appels"] += 1
                        q4[genre]["exp_ttl_propre_reecrit_cout"] += reecrit * prix_ecr
                p_e0, _, _ = prix_eff(a["modele"], ctx, a["geo"])
                q4_type[type_agent.split(":")[-1]]["surcout"] += a["e5"] * (mc.ECRITURE["1h"] - mc.ECRITURE["5m"]) * p_e0 / 1e6
                q4_type[type_agent.split(":")[-1]]["pause_5m_appels"] += 1 if (prec is not None and a["t"] - prec["t"] > 300) else 0
                q4_type[type_agent.split(":")[-1]]["appels"] += 1
                q4[genre]["ctf1h_surcout_toutes_ecritures_5m"] += a["e5"] * (mc.ECRITURE["1h"] - mc.ECRITURE["5m"]) * p_e0 / 1e6
                q4[genre]["ecrit_cout_5m"] += a["e5"] * mc.ECRITURE["5m"] * p_e0 / 1e6
                q4[genre]["ecrit_cout_1h"] += a["e1h"] * mc.ECRITURE["1h"] * p_e0 / 1e6
            prec = {"t": a["t"], "ctx": ctx + a["sortie"]}
        # ---- Q6 : agents dev-story
        if type_agent.split(":")[-1] == "dev-story":
            racine = None
            if dossier not in depots:
                depots[dossier] = racine_depot(r["cwd"])
            racine = depots[dossier]
            run_auto = bool(racine) and any(
                any((racine / "_bmad-output" / "implementation-artifacts").glob(motif)) for motif in MOTIFS_RUN_AUTONOME
            )
            m = re.search(r"\d+\.\d+", str(meta.get("description", "")))
            sessions_devstory[(dossier, session)] += 1
            q6_agents.append({
                "projet": projet, "dossier": dossier, "session": session, "agent": ident, "story": m.group(0) if m else None,
                "run_autonome": run_auto, "fam": propres[0]["fam"] if propres else appels[0]["fam"],
                "appels": len(propres), "cout": sum(sum(a["cout"].values()) for a in propres),
                "cout_appels": [round(sum(a["cout"].values()), 5) for a in propres],
                "debut": appels[0]["ts"][:10],
            })
        deja_ids |= r["ids"]
        deja_tu |= r["tu"]

    duree = time.time() - t0

    # ---- mise en forme
    res: dict = {
        "genere_le": maintenant.strftime("%Y-%m-%d"), "jours": o.jours, "coupure_utc": datetime.fromtimestamp(coupure, timezone.utc).strftime("%Y-%m-%d"),
        "fichiers": dict(n_fichiers), "duree_s": round(duree), "requetes_api": total_requetes, "requetes_forme_inconnue": inconnus_forme,
        "ignores_top": ignores_tot.most_common(8),
        "premiers_appels_exclus_reprise": dict(q1_ex),
    }
    res["tokens"] = {g: dict(c) for g, c in d_tokens.items()}
    res["cout_equiv_api_usd"] = {f"{g}:{k}": round(v, 2) for (g, k), v in couts_total.items()}
    res["q1"] = {"|".join(k): {"entree_ecriture": quartiles([x[0] for x in v]), "ctx_total": quartiles([x[1] for x in v])} for k, v in sorted(q1.items())}
    res["q1_composition_estimee_tokens_mediane"] = {
        g: {k: round(statistics.median(v)) for k, v in comp.items() if v} for g, comp in q1_formes.items()
    }
    res["q1_outils_par_type_agent"] = {
        t: {"n": len(c["ctx_total"]), "outils_charges_tokens_mediane": round(statistics.median(c["outils_charges"])),
            "n_outils_charges_mediane": statistics.median(c["n_outils_charges"]), "ctx_total_mediane": round(statistics.median(c["ctx_total"]))}
        for t, c in q1_types.items() if len(c["ctx_total"]) >= 3
    }
    res["q1_attachments_avant_premier_appel_mediane"] = {
        g: {k: {"mediane": round(statistics.median(v)), "n": len(v)} for k, v in comp.items()} for g, comp in q1_pre.items()
    }
    # Q2
    outils = {}
    for nom in set(q2_present) | set(appels_outil["principale"]) | set(appels_outil["sous-agent"]):
        c = q2_present.get(nom, Counter())
        outils[nom] = {
            "taille_def_tokens_est": round(q2_taille.get(nom, 0) / CAR_PAR_TOKEN_ENTREE),
            "principale_charge": c["principale:fichiers_charges"], "principale_presente": c["principale:fichiers_presents"],
            "principale_appelee": c["principale:fichiers_appeles"], "principale_appels": appels_outil["principale"][nom],
            "sous_agent_charge": c["sous-agent:fichiers_charges"], "sous_agent_present": c["sous-agent:fichiers_presents"],
            "sous_agent_appele": c["sous-agent:fichiers_appeles"], "sous_agent_appels": appels_outil["sous-agent"][nom],
            "tokens_lus_def_Mtok": round(q2_expo_tok[nom] / 1e6, 2), "cout_lecture_def_usd": round(q2_expo[nom], 2), "cout_ecriture_unique_def_usd": round(q2_ecr[nom], 2),
        }
    res["q2_outils"] = dict(sorted(outils.items(), key=lambda kv: -kv[1]["taille_def_tokens_est"]))
    # Q3
    q3r = {}
    for g, groupes in q3.items():
        q3r[g] = {}
        for nom, c in groupes.items():
            q3r[g][nom] = {k: (round(v) if k != "cout" else round(v, 2)) for k, v in c.items()}
    res["q3"] = q3r
    res["q3_shell_par_commande"] = {c: {k_: (round(v, 2) if k_ == "cout" else round(v)) for k_, v in cc.items()} for c, cc in q3_cmd.items()}
    res["cout_par_type_agent"] = {t: {"agents": c["agents"], "appels": c["appels"], "cout_usd": round(c["cout"], 2), "cout_median_agent_approx_usd": round(c["cout"] / c["agents"], 2)}
                                  for t, c in sorted(cout_par_type.items(), key=lambda kv: -kv[1]["cout"]) if c["agents"] >= 5}
    res["q4_ctf1h_par_type"] = {t: {"gain_usd": round(c["gain"], 2), "surcout_usd": round(c["surcout"], 2), "solde_usd": round(c["gain"] - c["surcout"], 2),
                                    "appels": c["appels"], "appels_apres_pause_5m": c["pause_5m_appels"]}
                                for t, c in sorted(q4_type.items(), key=lambda kv: -kv[1]["surcout"]) if c["appels"] >= 200 and t != "MAIN"}
    res["cout_fichiers_avec_definitions_usd"] = round(cout_couvert, 2)
    res["q4"] = {g: {k: (round(v, 4) if "cout" in k else round(v)) for k, v in c.items()} for g, c in q4.items()}
    # Q6 : resume ici, simulation dans le rapport
    res["q6"] = simuler_q6(q6_agents, sessions_devstory)
    o.out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    if o.detail_dir:
        o.detail_dir.mkdir(parents=True, exist_ok=True)
        (o.detail_dir / "q6_agents.json").write_text(json.dumps(q6_agents, ensure_ascii=False), encoding="utf-8")
    print(f"termine en {duree:.0f} s, {sum(n_fichiers.values())} fichiers -> {o.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
