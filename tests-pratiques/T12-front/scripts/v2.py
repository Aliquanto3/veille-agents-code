"""Volet 2 : boucle de développement sur le banc de rejeu (Sonnet), conception appariée.

Usage : uv run --no-project python v2.py ref            (valide les tests cachés, écrit interface.md)
        uv run --no-project python v2.py run v715 REP   (une répétition complète)

Une répétition = UNE session de développement (dev-story), évaluée telle quelle (bras A), puis le
sous-agent de vérification (Playwright MCP) parcourt les critères sur ce même arbre, son rapport est
renvoyé à la MÊME session par `--resume` (une passe de correction) et l'arbre corrigé est évalué (bras B).
B contient donc A : les deux bras partagent le développement (apparié, moitié moins cher que deux
développements indépendants, et sans la variance entre deux développements).
Vérité : oracle scripté (verite.py, figé avant les runs) + tests cachés de la story.
"""
import json, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "banc-rejeu"))
import banc
from commun import *
import verifier
from verite_run import verite

banc.CORPUS = ICI / "corpus-v2"
banc.DONNEES = ICI / "donnees" / "v2"
banc.SCRATCH = SCRATCH / "v2"
banc.SCRATCH.mkdir(parents=True, exist_ok=True)
banc.DONNEES.mkdir(parents=True, exist_ok=True)
SORTIE = ICI / "donnees" / "v2_runs.jsonl"
FICHE = {"v715": "s715", "v714": "s714"}  # fiche donnée au vérificateur
ORACLE = {"v715": "s715", "v714": "s714x"}  # oracle scripté (sélecteurs par rôle pour v714)
MODE = {"v715": "reel", "v714": "repli"}


def cmd_claude(session, resume=False):
    c = [banc.CLAUDE, "-p", "--model", banc.MODELES[os.environ.get("V2_MODELE", "s")], "--effort", "medium", "--output-format", "json",
         "--permission-mode", "acceptEdits", "--allowedTools", *banc.AUTORISES, "--tools", banc.OUTILS,
         "--setting-sources", "project,local", "--settings", json.dumps(banc.REGLAGES), "--max-budget-usd", "6"]
    c += ["--resume", session] if resume else ["--session-id", session]
    return c


def session_claude(cible, session, entree, resume=False, etiquette=""):
    t0 = time.time()
    code, sortie, erreur, expire = banc.lancer(cmd_claude(session, resume), cible, banc.TIMEOUT_S, env=banc.env_enfant(), entree=entree)
    brut = {}
    try:
        brut = json.loads(sortie)
    except ValueError:
        pass
    (banc.DONNEES / "brut").mkdir(exist_ok=True)
    (banc.DONNEES / "brut" / f"{etiquette}.json").write_text(sortie or "", encoding="utf-8")
    return {"etiquette": etiquette, "code": code, "expire": expire, "duree_mur_s": round(time.time() - t0, 1),
            "cout_usd": brut.get("total_cost_usd"), "tours": brut.get("num_turns"), "is_error": brut.get("is_error"),
            "subtype": brut.get("subtype"), "refus_permission": len(brut.get("permission_denials") or []),
            "resultat_debut": (brut.get("result") or "")[:300], "usage": brut.get("usage")}


def evaluer(cible, sid, story):
    """Oracle scripté + tests cachés (copiés puis retirés) + ruff."""
    oracle, axe = verite(cible, ORACLE[story], MODE[story], PORT)
    meta = banc.charger_meta(story)
    caches = banc.copier_caches(story, cible)
    res = banc.pytest(cible, caches, 600)
    for c in caches:  # le fichier caché ne doit pas rester pour la passe de correction
        (cible / c).unlink(missing_ok=True)
    ruff = banc.lancer([banc.UV, "run", "--no-sync", "ruff", "check", "."], cible, 300, env=banc.env_enfant())
    total = meta.get("total_ref")
    return {"oracle": oracle, "criteres_tenus": sum(1 for k, (ok, _) in oracle.items() if ok), "criteres_total": len(oracle),
            "caches_passes": res["passed"], "caches_total": total, "caches_fin": res["fin"][-300:], "ruff_ok": ruff[0] == 0}


def rapport_texte(meta_verif):
    """Rapport du vérificateur renvoyé à l'agent : verdicts et preuves des critères en échec (et des NA)."""
    import re
    m = re.search(r"\{.*\}", meta_verif.get("result", ""), re.S)
    try:
        rap = json.loads(m.group(0))
    except Exception:
        return "Rapport illisible : " + meta_verif.get("result", "")[:1500]
    lignes = []
    for it in rap.get("criteres", []) + rap.get("transverses", []):
        if it.get("verdict") != "PASS":
            lignes.append(f"- {it.get('id')} : {it.get('verdict')} : {it.get('preuve')}")
    return "\n".join(lignes) + ("\n\nSynthèse du vérificateur : " + str(rap.get("synthese", "")) if rap.get("synthese") else "") if lignes else \
        "Tous les critères et contrôles transverses sont PASS."


def repetition(story, rep):
    rid = f"{story}-r{rep}" + ("" if os.environ.get("V2_MODELE", "s") == "s" else "-" + os.environ["V2_MODELE"])
    cible = Path(os.path.realpath(banc.SCRATCH)) / rid
    meta = banc.charger_meta(story)
    banc.preparer(story, meta["base"], cible, banc.ICI / "claude_md" / "minimal.md", retirer_caches=True)
    spec = (banc.CORPUS / story / "spec.md").read_text(encoding="utf-8") + "\n" + (banc.CORPUS / story / "interface.md").read_text(encoding="utf-8")
    session = str(uuid.uuid4())
    out = {"id": rid, "story": story, "rep": rep, "session": session, "modele_dev": banc.MODELES[os.environ.get("V2_MODELE", "s")]}
    out["dev"] = session_claude(cible, session, banc.PROMPT + spec, etiquette=rid + "-dev")
    out["A"] = evaluer(cible, rid, story)
    print(rid, "dev", out["dev"]["cout_usd"], "A", out["A"]["criteres_tenus"], "/", out["A"]["criteres_total"], "caches", out["A"]["caches_passes"], flush=True)
    # vérification navigateur sur l'arbre A (serveur démarré par le banc, comme au volet 1)
    sid = FICHE[story]
    env = env_enfant(); env["USINE_CLE_PSEUDO"] = "cle-de-test-t12-pseudo"
    if MODE[story] == "repli": env["USINE_MODE_REPLI"] = "1"
    else: env.pop("USINE_MODE_REPLI", None)
    srv = subprocess.Popen([UV, "run", "--no-sync", "usine", "ui", "--port", str(PORT)], cwd=cible, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    try:
        if not attendre(f"http://127.0.0.1:{PORT}/api/cadre"):
            out["verif"] = {"erreur": "serveur indisponible sur l'arbre de l'agent"}
            rapport = "Le serveur `usine ui` ne démarre pas ou ne répond pas sur /api/cadre."
        else:
            fiche = (ICI / "fiches" / f"{sid}.md").read_text(encoding="utf-8")
            prompt = verifier.PROMPT.format(base=f"http://127.0.0.1:{PORT}", commande=verifier.commande(sid), mode_phrase=verifier.phrase_mode(sid), fiche=fiche)
            wd, statut, duree = verifier.lancer_claude(rid + "-verif", sid, prompt)
            mv = verifier.resume_flux(wd / "flux.jsonl")
            mv.update({"statut": statut, "duree_mur_s": duree})
            shutil.copyfile(wd / "flux.jsonl", banc.DONNEES / "brut" / f"{rid}-verif.flux.jsonl")
            out["verif"] = {k: mv.get(k) for k in ("statut", "cout_usd", "tours", "duree_mur_s", "outils", "refus", "is_error")}
            out["verif"]["rapport"] = mv.get("result", "")[:4000]
            rapport = rapport_texte(mv)
    finally:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(srv.pid)], capture_output=True)
    # une passe de correction dans la même session
    consigne = ("Un sous-agent de vérification a parcouru dans un vrai navigateur (Playwright) les critères d'acceptation de ta story, "
                "sur l'application que tu viens d'écrire. Voici les critères qui ne sont pas PASS, avec ses preuves :\n\n" + rapport +
                "\n\nCorrige ce qui est réellement en défaut par rapport à la spécification (ignore ce qui relève d'une erreur du vérificateur ou de "
                "l'environnement). Relance les tests ciblés avant de finir. Une seule passe.")
    out["correction"] = session_claude(cible, session, consigne, resume=True, etiquette=rid + "-correction")
    out["B"] = evaluer(cible, rid, story)
    out["cout_A"] = out["dev"]["cout_usd"]
    out["cout_B"] = round((out["dev"]["cout_usd"] or 0) + (out["verif"].get("cout_usd") or 0) + (out["correction"]["cout_usd"] or 0), 4)
    with SORTIE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")
    print(rid, "B", out["B"]["criteres_tenus"], "/", out["B"]["criteres_total"], "caches", out["B"]["caches_passes"], "coût A", out["cout_A"], "coût B", out["cout_B"], flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "ref":
        sys.stdout.reconfigure(encoding="utf-8")
        banc.reference(sys.argv[2:])
    else:
        repetition(sys.argv[2], int(sys.argv[3]))
