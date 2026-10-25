"""Volet 1 : sous-agent de verification (claude -p Sonnet, Playwright MCP) sur une version d'une story.

Usage : uv run --no-project python verifier.py ID [ID...]
  ID = d01..d16 (defaut seme) ou t713..t716 (temoin sans defaut)
Un seul serveur d'application et un seul navigateur a la fois ; le serveur est demarre par le banc
(commande du depot : `uv run usine ui --port 8765`, avec USINE_MODE_REPLI=1 sauf s715), arrete apres.
"""
import json, sys, time
from commun import *
import semer
from verite_run import verite

RUNS = ICI / "donnees" / "verif"
RUNS.mkdir(parents=True, exist_ok=True)
MODELE = "claude-sonnet-5-5"

PROMPT = """Tu es le sous-agent de vérification d'une story front. Tu vérifies, dans un vrai navigateur, que l'application respecte les critères d'acceptation de la story ci-dessous. Tu ne modifies rien et tu n'as pas accès au code source : tu ne te fies qu'à ce que montre le navigateur.

L'application est déjà démarrée à l'adresse {base}/ (commande du dépôt : `{commande}`). {mode_phrase}
Ton seul outil est le serveur MCP Playwright (outils `browser_*`). N'ouvre que cette application. Au plus 40 appels d'outil au total.

## Story à vérifier

{fiche}

## Contrôles transverses (à faire sur chaque écran que tu visites pour les critères)
- T1 : navigation au clavier. Tab parcourt les éléments interactifs dans un ordre logique, le focus est visible, Entrée ou Espace active les boutons et les liens.
- T2 : mise en page à 390 px de large (`browser_resize` 390 x 844, puis capture d'écran) : pas de défilement horizontal de la page, pas de contenu coupé ou superposé. Remets ensuite la fenêtre à 1280 x 800.
- T3 : aucun message d'erreur affiché sans texte, aucun lien mort (un lien suivi aboutit à une page qui se charge).

## Méthode
Préfère `browser_snapshot` (arbre d'accessibilité) aux captures ; utilise `browser_take_screenshot` pour T2 et pour un doute visuel. Parcours chaque critère C1... dans l'ordre, puis les contrôles T1 à T3 sur un ou deux écrans de la story. Ne devine pas : si tu ne peux pas observer un point dans le navigateur, mets NA.

## Rendu
Réponds uniquement par un objet JSON sur une seule ligne (sans autre texte) :
{{"criteres":[{{"id":"C1","verdict":"PASS|FAIL|NA","preuve":"ce que tu as observé : texte exact, état, URL, statut HTTP"}}, ...],"transverses":[{{"id":"T1","verdict":"PASS|FAIL|NA","preuve":"..."}},{{"id":"T2",...}},{{"id":"T3",...}}],"synthese":"une phrase"}}
Un critère dont une partie échoue est FAIL ; précise laquelle dans la preuve."""


def phrase_mode(sid):
    if sid == "s715":
        return "Elle a été lancée en Mode réel (sans la variable `USINE_MODE_REPLI`)."
    return "Elle a été lancée en Mode repli (`USINE_MODE_REPLI=1`)."


def commande(sid):
    pre = "USINE_CLE_PSEUDO=<cle de test> " + ("" if sid == "s715" else "USINE_MODE_REPLI=1 ")
    return f"{pre}uv run usine ui --port {PORT}"


def lancer_claude(rid, sid, prompt):
    wd = SCRATCH / "verif" / rid
    effacer(wd); wd.mkdir(parents=True)
    mcp = {"mcpServers": {"playwright": {"command": "node", "args": [
        str(MCP_CLI), "--headless", "--isolated", "--executable-path", str(CHROMIUM),
        "--output-dir", str(wd / ".mcp-out")]}}}
    (wd / "mcp.json").write_text(json.dumps(mcp), encoding="utf-8")
    cmd = [CLAUDE, "-p", "--model", MODELE, "--effort", "medium", "--setting-sources", "project,local", "--no-chrome",
           "--tools", "Read", "--permission-mode", "acceptEdits", "--permission-prompts", "none",
           "--max-budget-usd", "2", "--output-format", "stream-json", "--verbose", "--no-session-persistence",
           "--strict-mcp-config", "--mcp-config", str(wd / "mcp.json"),
           "--allowedTools", "Read,mcp__playwright",
           "--settings", json.dumps({"claudeMdExcludes": ["**/Utilisateur/.claude/CLAUDE.md"]})]
    out = open(wd / "flux.jsonl", "wb"); err = open(wd / "stderr.txt", "wb")
    t0 = time.time()
    p = subprocess.Popen(cmd, cwd=wd, env=env_enfant(), stdin=subprocess.PIPE, stdout=out, stderr=err)
    try:
        p.communicate(prompt.encode("utf-8"), timeout=1200); statut = "ok" if p.returncode == 0 else f"rc={p.returncode}"
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True); statut = "timeout"
    out.close(); err.close()
    return wd, statut, round(time.time() - t0, 1)


def resume_flux(chemin):
    r = {"outils": {}, "refus": 0, "result": ""}
    for ligne in chemin.read_text(encoding="utf-8", errors="replace").splitlines():
        try: ev = json.loads(ligne)
        except Exception: continue
        t = ev.get("type")
        if t == "assistant":
            for b in ev.get("message", {}).get("content", []):
                if b.get("type") == "tool_use":
                    r["outils"][b["name"]] = r["outils"].get(b["name"], 0) + 1
        elif t == "result":
            r.update({"cout_usd": ev.get("total_cost_usd"), "tours": ev.get("num_turns"), "duree_ms": ev.get("duration_ms"),
                      "is_error": ev.get("is_error"), "subtype": ev.get("subtype"), "usage": ev.get("usage"),
                      "refus": len(ev.get("permission_denials") or []), "result": ev.get("result") or ""})
    return r


def un(ident):
    temoin = ident.startswith("t")
    sid = "s" + ident[1:] if temoin else semer.DEFAUTS[ident]["story"]
    rid = ident + "-" + time.strftime("%H%M%S")
    arbre = semer.arbre(sid)
    if not temoin:
        semer.appliquer(ident)
    # oracle scripté + axe-core sur la même version (serveur propre à l'oracle, arrêté ensuite)
    oracle, axe = verite(arbre, sid, "reel" if sid == "s715" else "repli", PORT)
    env = env_enfant()
    env["USINE_CLE_PSEUDO"] = "cle-de-test-t12-pseudo"
    if sid != "s715":
        env["USINE_MODE_REPLI"] = "1"
    else:
        env.pop("USINE_MODE_REPLI", None)
    srv_log = open(SCRATCH / f"serveur-{rid}.log", "wb")
    srv = subprocess.Popen([UV, "run", "--no-sync", "usine", "ui", "--port", str(PORT)], cwd=arbre, env=env, stdout=srv_log, stderr=subprocess.STDOUT)
    try:
        assert attendre(f"http://127.0.0.1:{PORT}/api/cadre"), "serveur indisponible"
        fiche = (ICI / "fiches" / f"{sid}.md").read_text(encoding="utf-8")
        prompt = PROMPT.format(base=f"http://127.0.0.1:{PORT}", commande=commande(sid), mode_phrase=phrase_mode(sid), fiche=fiche)
        wd, statut, duree = lancer_claude(rid, sid, prompt)
    finally:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(srv.pid)], capture_output=True)
        srv_log.close()
        time.sleep(1)
        semer.retirer(sid)
        subprocess.run(["git", "clean", "-fdq", "-e", ".venv"], cwd=arbre, capture_output=True)
    meta = resume_flux(wd / "flux.jsonl")
    meta.update({"id": ident, "run": rid, "story": sid, "temoin": temoin, "statut": statut, "duree_mur_s": duree,
                 "cibles": [] if temoin else semer.DEFAUTS[ident]["cibles"],
                 "oracle": oracle, "axe": axe})
    # sortie brute conservee dans le depot (anonymisee ensuite)
    dest = RUNS / rid; dest.mkdir(exist_ok=True)
    shutil.copyfile(wd / "flux.jsonl", dest / "flux.jsonl")
    (dest / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    with (RUNS.parent / "verif_runs.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(meta, ensure_ascii=False) + "\n")
    print(ident, statut, meta.get("cout_usd"), duree, meta.get("tours"), sum(meta["outils"].values()), flush=True)


if __name__ == "__main__":
    for i in sys.argv[1:]:
        un(i)
