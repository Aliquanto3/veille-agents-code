"""Volet B : parcours de 7 étapes joué par `claude -p` (Sonnet) avec un seul outil navigateur.

Usage : python lancer_parcours.py <outil>_r<rep> [...]    outil in {playwright-cli, playwright-mcp, agent-browser}
"""
import json, os, re, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lancer_claude import lancer, T7

REF = T7 / "parcours" / "ref_app"
RUNS = T7 / "parcours" / "runs"
NAV = T7 / "tools" / "navigateurs"
CHROMIUM = T7 / "tools" / "browsers" / "chromium-1248" / "chrome-win64" / "chrome.exe"
PORT = 8870
BASE = f"http://127.0.0.1:{PORT}"

PARCOURS = """Tu vérifies, comme le ferait un agent qui contrôle son propre travail, l'écran « Demandes d'achat » d'une application web déjà lancée à l'adresse {base}/demandes.
{outil_phrase}
Tu n'as aucun autre moyen d'accéder à la page. Tu ne modifies aucun fichier et tu ne cherches pas le code source : tu ne te fies qu'à ce que montre le navigateur. N'utilise que cette application (aucun autre site).

Joue ce parcours en 7 étapes, dans l'ordre :
1. Ouvrir la page `/demandes` et vérifier que le tableau contient 6 demandes.
2. Remplir le formulaire avec une erreur : Demandeur « Test Parcours », Service « Finance », Montant « -50 », Motif « Achat de test pour le parcours », puis cliquer sur « Enregistrer la demande ».
3. Constater le message d'erreur affiché pour le montant (recopier son texte exact) et vérifier que la saisie est conservée.
4. Corriger le montant en « 150,75 ».
5. Valider à nouveau le formulaire et constater le message de confirmation (recopier son texte exact).
6. Filtrer le tableau sur le service « Finance » avec la liste « Filtrer par service ».
7. Vérifier le résultat : lire le compteur affiché et compter les lignes visibles du tableau, puis dire si « Test Parcours » figure parmi elles.

Quand tu as fini, ferme le navigateur, puis réponds uniquement par un objet JSON sur une seule ligne, sans autre texte :
{{"etapes":[{{"n":1,"ok":true,"constat":"..."}}, ... jusqu'à n=7],"erreur_montant":"<texte exact>","confirmation":"<texte exact>","compteur":"<texte exact du compteur>","lignes_finance":<nombre de lignes visibles>,"test_parcours_visible":true}}
"""

OUTILS = {
    "playwright-cli": {
        "phrase": "Ton seul outil pour piloter le navigateur est la CLI `playwright-cli` (commandes shell via Bash ; la skill `playwright-cli` est installée dans le projet).",
        "tools": "Bash,Read,Skill",
        "allowed": ["Bash(playwright-cli *)", "Read", "Skill"],
    },
    "agent-browser": {
        "phrase": "Ton seul outil pour piloter le navigateur est la CLI `agent-browser` (commandes shell via Bash ; la skill `agent-browser` est installée dans le projet).",
        "tools": "Bash,Read,Skill",
        "allowed": ["Bash(agent-browser *)", "Read", "Skill"],
    },
    "playwright-mcp": {
        "phrase": "Ton seul outil pour piloter le navigateur est le serveur MCP Playwright (outils `browser_*`).",
        "tools": "Read",
        "allowed": ["Read", "mcp__playwright"],
    },
}


def preparer(outil, nom):
    d = RUNS / nom
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    extra, env_extra = [], {}
    bin_dirs = []
    if outil == "playwright-cli":
        sk = NAV / "playwright-cli" / "node_modules" / "@playwright" / "cli" / "skills" / "playwright-cli"
        shutil.copytree(sk, d / ".claude" / "skills" / "playwright-cli")
        (d / ".playwright").mkdir()
        cfg = {"browser": {"browserName": "chromium", "launchOptions": {"executablePath": str(CHROMIUM), "headless": True}}}
        (d / ".playwright" / "cli.config.json").write_text(json.dumps(cfg), encoding="utf-8")
        bin_dirs.append(NAV / "playwright-cli" / "node_modules" / ".bin")
    elif outil == "agent-browser":
        sk = NAV / "agent-browser" / "node_modules" / "agent-browser" / "skills" / "agent-browser"
        shutil.copytree(sk, d / ".claude" / "skills" / "agent-browser")
        bin_dirs.append(NAV / "agent-browser" / "node_modules" / ".bin")
        env_extra["AGENT_BROWSER_EXECUTABLE_PATH"] = str(CHROMIUM)
    else:
        mcp = {"mcpServers": {"playwright": {"command": "node", "args": [
            str(NAV / "playwright-mcp" / "node_modules" / "@playwright" / "mcp" / "cli.js"),
            "--headless", "--isolated", "--executable-path", str(CHROMIUM), "--output-dir", str(d / ".mcp-out")]}}}
        (d / "mcp.json").write_text(json.dumps(mcp), encoding="utf-8")
        extra += ["--mcp-config", str(d / "mcp.json")]
    env_extra["PATH"] = os.pathsep.join([str(p) for p in bin_dirs] + [os.environ["PATH"]])
    env_extra["NO_UPDATE_NOTIFIER"] = "1"
    return d, extra, env_extra


def attendre(url, t=60):
    t0 = time.time()
    while time.time() - t0 < t:
        try:
            urllib.request.urlopen(url, timeout=2).read()
            return True
        except Exception:
            time.sleep(0.5)
    return False


def nettoyer():
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(Path(__file__).parent / "nettoyer.ps1")], capture_output=True)


def verifier(meta, d):
    """Scores le parcours : JSON final + état du serveur."""
    res = {}
    txt = meta.get("resultat_fin", "")
    # le résultat complet est dans le flux : on relit le dernier évènement result
    full = ""
    for ligne in (d / "_claude.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            ev = json.loads(ligne)
        except Exception:
            continue
        if ev.get("type") == "result":
            full = ev.get("result") or ""
    m = re.search(r"\{.*\}", full, re.S)
    rep = None
    if m:
        try:
            rep = json.loads(m.group(0))
        except Exception:
            rep = None
    res["json_ok"] = rep is not None
    if rep:
        norm = lambda s: re.sub(r"\s+", " ", (s or "").replace(" ", " ").replace(" ", " ")).strip()
        res["erreur_montant_ok"] = norm(rep.get("erreur_montant")) == "Le montant doit être un nombre supérieur à 0 et au plus 50 000 €."
        res["confirmation_ok"] = norm(rep.get("confirmation")).rstrip(".") == "Demande enregistrée"
        res["compteur_ok"] = norm(rep.get("compteur")) == "2 demandes affichées"
        res["lignes_ok"] = rep.get("lignes_finance") == 2
        res["visible_ok"] = rep.get("test_parcours_visible") is True
        et = rep.get("etapes") or []
        res["etapes_ok"] = len(et) == 7 and all(e.get("ok") is True for e in et)
    return res, full


def etat_serveur():
    html = urllib.request.urlopen(BASE + "/demandes", timeout=5).read().decode("utf-8")
    lignes = len(re.findall(r"<tr[ >]", html)) - 1
    return {"lignes_serveur": lignes, "test_parcours_occurrences": html.count("Test Parcours"), "montant_150_75": ("150,75" in html)}


def un_run(nom):
    outil, serie = nom.rsplit("_", 1)   # serie : r<n> = liste d'autorisations stricte ; e<n> = liste élargie (export, sed, grep...)
    d, extra, env_extra = preparer(outil, nom)
    cfg = dict(OUTILS[outil])
    if serie.startswith("e") and outil != "playwright-mcp":
        cfg["allowed"] = cfg["allowed"] + ["Bash(export *)", "Bash(sed *)", "Bash(grep *)", "Bash(head *)", "Bash(tail *)", "Bash(echo *)", "Bash(wc *)"]
    prompt = PARCOURS.format(base=BASE, outil_phrase=cfg["phrase"])
    (d / "_prompt.txt").write_text(prompt, encoding="utf-8")
    nettoyer()
    srv = subprocess.Popen(["uv", "run", "--project", str(REF), "uvicorn", "app.main:app", "--port", str(PORT), "--log-level", "warning"],
                           cwd=REF, stdout=open(d / "serveur.log", "wb"), stderr=subprocess.STDOUT)
    try:
        assert attendre(BASE + "/demandes"), "serveur indisponible"
        meta = lancer(d, prompt, tools=cfg["tools"], allowed=cfg["allowed"], extra=extra, env_extra=env_extra, budget=3.0, timeout=1200, effort="medium")
        score, full = verifier(meta, d)
        score.update(etat_serveur())
        score["serveur_ok"] = score["lignes_serveur"] == 7 and score["test_parcours_occurrences"] == 1 and score["montant_150_75"]
        score["reussite"] = all(score.get(k) is True for k in ("json_ok", "erreur_montant_ok", "confirmation_ok", "compteur_ok", "lignes_ok", "visible_ok", "etapes_ok", "serveur_ok"))
        meta["score"] = score
        meta["reponse"] = full[:1500]
        (d / "_claude.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        print(nom, meta.get("statut"), meta.get("cout_usd"), meta.get("duree_s"), "reussite=", score["reussite"], flush=True)
    finally:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(srv.pid)], capture_output=True)
        nettoyer()


if __name__ == "__main__":
    for n in sys.argv[1:]:
        un_run(n)
