"""Oracle scripté (vérité) : parcours Playwright écrit par moi depuis les critères d'acceptation des fiches.

Rôles : (1) vérifier que chaque défaut semé est réellement visible dans le navigateur et que les
versions témoins passent ; (2) vérité du volet 2 (critères tenus), avec des sélecteurs par rôle et
par texte du cahier des charges plutôt que par identifiant d'implémentation.

Usage : uv run --project <t7/mesures> python verite.py ARBRE STORY MODE [PORT]
  ARBRE = dossier de l'application ; STORY = s713..s716 ; MODE = repli|reel
Sortie : JSON {"checks": {nom: [ok, détail]}}. Le serveur est démarré puis arrêté par ce script.
"""
import json, os, re, subprocess, sys, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

CHROMIUM = Path(os.environ["T12_CHROMIUM"])
UV = "uv"
PORT = int(sys.argv[4]) if len(sys.argv) > 4 else 8765
BASE = f"http://127.0.0.1:{PORT}"
TO = 6000


def verif(res, nom, fonction):
    try:
        ok, detail = fonction()
        res[nom] = [bool(ok), detail]
    except Exception as exc:  # noqa: BLE001
        res[nom] = [False, f"exception : {str(exc).splitlines()[0][:200]}"]


def largeur_ok(pg, url, largeur=390):
    pg.set_viewport_size({"width": largeur, "height": 844})
    pg.goto(BASE + url); pg.wait_for_timeout(1200)
    sw = pg.evaluate("document.documentElement.scrollWidth")
    pg.set_viewport_size({"width": 1280, "height": 800})
    return sw <= largeur + 1, f"scrollWidth={sw}"


# ---------------------------------------------------------------- 7.13
def s713(b):
    res = {}
    pg = b.new_page()
    ecrans = {"/": "Carte météo", "/entites/ENT-A": "Détail d'une Entité", "/chaine": "Lancement de la Chaîne", "/agent": "Agent",
              "/avant-apres": "Avant / après", "/pseudonymisation": "Pseudonymisation", "/outillage": "Ce qu'il faut pour le faire en vrai"}
    ext = []
    pg.on("request", lambda r: ext.append(r.url) if not r.url.startswith(BASE) and not r.url.startswith("data:") else None)

    def c1():
        mal = []
        for u, nom in ecrans.items():
            pg.goto(BASE + u); pg.wait_for_timeout(300)
            if pg.title() != f"{nom} · Usine de migration" or pg.locator("h1").count() != 1:
                mal.append(u)
        return not mal, f"écarts : {mal}"
    verif(res, "C1_titres_h1", c1)

    def c2():
        mal = []
        for u in ecrans:
            pg.goto(BASE + u); pg.wait_for_timeout(500)
            lancer = pg.locator("header a", has_text="Lancer la Chaîne").count()
            if (u == "/chaine") != (lancer == 0): mal.append(("bouton", u))
            if pg.locator("nav [aria-current=page]").count() != 1: mal.append(("aria-current", u))
            if not pg.get_by_text(re.compile(r"Passage publié")).first.is_visible(): mal.append(("passage", u))
            if not pg.get_by_text(re.compile(r"^Mode (repli|réel)$")).first.is_visible(): mal.append(("mode", u))
        return not mal, f"écarts : {mal}"
    verif(res, "C2_cadre", c2)

    def c3():
        mal = []
        for u in ("/", "/chaine", "/agent"):
            pg.goto(BASE + u); pg.wait_for_timeout(500)
            if pg.locator("#pastille-mode").inner_text().strip() != "Mode repli": mal.append(("pastille", u))
            if not pg.get_by_text(re.compile(r"Mode repli : la démo lit")).first.is_visible(): mal.append(("bandeau", u))
        return not mal, f"écarts : {mal}"
    verif(res, "C3_repli", c3)

    def c4():
        pg.goto(BASE + "/"); pg.wait_for_timeout(400)
        pg.keyboard.press("Tab")
        lien = pg.evaluate("document.activeElement.className + '|' + document.activeElement.textContent")
        box = pg.evaluate("(()=>{const r=document.activeElement.getBoundingClientRect();return [r.top,r.bottom]})()")
        visible = box[0] >= 0
        pg.keyboard.press("Enter"); pg.wait_for_timeout(300)
        h = pg.evaluate("location.hash")
        cible = pg.evaluate("!!document.querySelector(location.hash || '#__aucun__')")
        return ("evitement" in lien) and visible and cible, f"actif={lien!r} top={box[0]} hash={h} cible={cible}"
    verif(res, "C4_lien_evitement", c4)
    verif(res, "C5_pas_de_requete_externe", lambda: (not ext, f"externes : {ext[:3]}"))
    verif(res, "T2_390px_accueil", lambda: largeur_ok(pg, "/"))
    verif(res, "T2_390px_chaine", lambda: largeur_ok(pg, "/chaine"))
    return res


# ---------------------------------------------------------------- 7.14
def s714(b):
    res = {}
    pg = b.new_page()
    pg.goto(BASE + "/"); pg.wait_for_timeout(1000)
    verif(res, "C1_carte", lambda: (pg.locator("#tableau-entites tbody tr").count() == 10 and pg.locator("#tuiles li").count() == 4,
                                    f"lignes={pg.locator('#tableau-entites tbody tr').count()}"))

    def c1b():
        from collections import Counter
        tuiles = sorted(int(pg.locator("#tuiles li .tuile-chiffre").nth(i).inner_text()) for i in range(pg.locator("#tuiles li").count()))
        lignes = Counter(pg.locator("#tableau-entites tbody tr").nth(i).get_attribute("data-meteo") for i in range(pg.locator("#tableau-entites tbody tr").count()))
        return tuiles == sorted(lignes.values()), f"tuiles={tuiles} lignes={dict(lignes)}"
    verif(res, "C1b_tuiles_coherentes", c1b)

    def c2():
        pg.evaluate("window.__marqueur = 1")
        pg.select_option("#filtre-meteo", label="Rouge"); pg.wait_for_timeout(300)
        vis = pg.locator("#tableau-entites tbody tr:visible").count()
        annonce = pg.locator("[role=status]#annonce-filtre").inner_text()
        garde = pg.evaluate("window.__marqueur === 1")
        pg.select_option("#filtre-meteo", label="Toutes"); pg.wait_for_timeout(300)
        vis2 = pg.locator("#tableau-entites tbody tr:visible").count()
        return vis == 2 and annonce == "2 Entités affichées" and garde and vis2 == 10, f"visibles={vis} annonce={annonce!r} sans_rechargement={garde} retour={vis2}"
    verif(res, "C2_filtre", c2)

    def c3():
        liens = pg.locator("#livrables a")
        n = liens.count(); mal = []
        for i in range(n):
            href = liens.nth(i).get_attribute("href")
            r = pg.request.get(BASE + href)
            if r.status != 200 or "attachment" not in (r.headers.get("content-disposition") or ""): mal.append((href, r.status))
        return n == 2 and not mal, f"liens={n} écarts={mal}"
    verif(res, "C3_livrables", c3)

    def c3b():
        pg.goto(BASE + "/"); pg.wait_for_timeout(800)
        pg.evaluate("document.activeElement && document.activeElement.blur()")
        atteints = 0
        for _ in range(80):
            pg.keyboard.press("Tab")
            if pg.evaluate("!!document.activeElement.closest('#livrables')"):
                atteints += 1
                if atteints >= 2: break
        return atteints >= 2, f"liens de livrables atteints au clavier : {atteints}"
    verif(res, "C3b_livrables_clavier", c3b)

    def c4():
        pg.goto(BASE + "/entites"); pg.wait_for_timeout(800)
        return pg.url.endswith("/entites/ENT-A") and pg.get_by_text("Règles déclenchantes").first.is_visible(), f"url={pg.url}"
    verif(res, "C4_detail", c4)

    def c4b():
        pg.goto(BASE + "/"); pg.wait_for_timeout(800)
        pg.get_by_role("link", name=re.compile(r"Détail ENT-B")).click(); pg.wait_for_timeout(800)
        return pg.url.endswith("/entites/ENT-B"), f"url={pg.url}"
    verif(res, "C4b_lien_detail_ligne", c4b)

    def c5():
        pg.goto(BASE + "/entites/ENT-X"); pg.wait_for_timeout(800)
        txt = pg.locator("#message").inner_text()
        pg.get_by_role("link", name=re.compile("Carte météo")).first.click() if pg.locator("#message-lien").is_hidden() else pg.locator("#message-lien").click()
        pg.wait_for_timeout(500)
        return txt == "Entité ENT-X absente du Passage affiché." and pg.url.rstrip("/") == BASE, f"message={txt!r} après clic={pg.url}"
    verif(res, "C5_entite_absente", c5)

    def c6():
        pg.goto(BASE + "/"); pg.wait_for_timeout(600)
        liens = pg.locator("#tableau-entites a.ticket").count()
        st = pg.request.get(BASE + "/livrables/autre").status
        return liens == 0 and st == 404, f"liens_ticket={liens} autre={st}"
    verif(res, "C6_tickets_texte_404", c6)
    verif(res, "T2_390px_carte", lambda: largeur_ok(pg, "/"))
    verif(res, "T2_390px_detail", lambda: largeur_ok(pg, "/entites/ENT-A"))
    return res


# ---------------------------------------------------------------- 7.14, version « agnostique » (volet 2 : sélecteurs par rôle et par texte de la spec)
def s714x(b):
    res = {}
    pg = b.new_page()
    pg.goto(BASE + "/"); pg.wait_for_timeout(1500)

    def lignes_visibles():
        return pg.get_by_role("row").filter(has_text=re.compile(r"ENT-[A-Z]")).filter(visible=True).count()

    verif(res, "K1_carte_dix_lignes", lambda: (lignes_visibles() == 10, f"lignes={lignes_visibles()}"))

    def k2():
        pg.evaluate("window.__marqueur = 1")
        combo = pg.get_by_role("combobox").first
        combo.select_option(label="Rouge"); pg.wait_for_timeout(500)
        vis = lignes_visibles()
        annonce = pg.get_by_role("status").filter(has_text=re.compile("Entit")).first.inner_text().strip()
        garde = pg.evaluate("window.__marqueur === 1")
        combo.select_option(index=0); pg.wait_for_timeout(500)
        return vis == 2 and annonce == "2 Entités affichées" and garde and lignes_visibles() == 10, f"visibles={vis} annonce={annonce!r} sans_rechargement={garde}"
    verif(res, "K2_filtre_rouge", k2)

    def k3():
        pg.goto(BASE + "/"); pg.wait_for_timeout(1000)
        hrefs = pg.eval_on_selector_all("a[href^='/livrables/']", "els => els.map(e => e.getAttribute('href'))")
        mal = []
        for h in hrefs:
            r = pg.request.get(BASE + h)
            if r.status != 200 or "attachment" not in (r.headers.get("content-disposition") or ""): mal.append((h, r.status))
        return len(hrefs) == 2 and not mal, f"liens={hrefs} écarts={mal}"
    verif(res, "K3_livrables", k3)

    def k4():
        pg.goto(BASE + "/entites"); pg.wait_for_timeout(1000)
        return pg.url.endswith("/entites/ENT-A"), f"url={pg.url}"
    verif(res, "K4_redirection_entites", k4)

    def k5():
        pg.goto(BASE + "/entites/ENT-X"); pg.wait_for_timeout(1000)
        ok_txt = pg.get_by_text("Entité ENT-X absente du Passage affiché.").first.is_visible()
        liens = pg.eval_on_selector_all("main a", "els => els.map(e => e.getAttribute('href'))")
        return ok_txt and ("/" in liens), f"texte={ok_txt} liens={liens[:4]}"
    verif(res, "K5_entite_absente", k5)

    def k6():
        pg.goto(BASE + "/"); pg.wait_for_timeout(1000)
        liens = pg.eval_on_selector_all("main a", "els => els.filter(e => /^DEMO-/.test(e.textContent.trim())).length")
        st = pg.request.get(BASE + "/livrables/autre").status
        return liens == 0 and st == 404, f"liens_ticket={liens} autre={st}"
    verif(res, "K6_tickets_texte_et_404", k6)
    return res


# ---------------------------------------------------------------- 7.15
def s715(b):
    res = {}
    pg = b.new_page()
    pg.goto(BASE + "/chaine"); pg.wait_for_timeout(1200)

    def c1():
        etapes = pg.get_by_text("En attente", exact=True).count()
        compteur = pg.get_by_text("0 / 10").first.is_visible()
        val = pg.get_by_role("progressbar").first.get_attribute("aria-valuenow")
        entete = pg.locator("header a", has_text="Lancer la Chaîne").count()
        lancer = pg.get_by_role("button", name="Lancer la Chaîne")
        return etapes >= 10 and compteur and val == "0" and entete == 0 and lancer.is_visible() and lancer.get_attribute("aria-disabled") != "true", \
            f"étapes={etapes} compteur={compteur} valuenow={val} entete={entete}"
    verif(res, "C1_etat_initial", c1)

    def c4():
        pg.evaluate("window.__marqueur = 1")
        pg.get_by_role("button", name="Passer en Mode repli").click()
        pg.get_by_text("Mode repli", exact=True).first.wait_for(timeout=8000)
        garde = pg.evaluate("window.__marqueur === 1")
        bandeau = pg.get_by_text(re.compile("Mode repli : la démo lit")).first.is_visible()
        pg.goto(BASE + "/"); pg.wait_for_timeout(900)
        lignes = pg.locator("table tbody tr").count()
        pg.goto(BASE + "/chaine"); pg.wait_for_timeout(900)
        pg.get_by_role("button", name=re.compile("Revenir au Mode réel")).click()
        pg.get_by_text("Mode réel", exact=True).first.wait_for(timeout=8000)
        pg.get_by_role("button", name="Passer en Mode repli").wait_for(timeout=5000)
        return garde and bandeau and lignes == 10, f"sans_rechargement={garde} bandeau={bandeau} lignes_carte={lignes}"
    verif(res, "C4_bascule_mode", c4)
    pg.goto(BASE + "/chaine"); pg.wait_for_timeout(1000)

    def c2():
        pg.get_by_role("button", name="Lancer la Chaîne").click()
        alerte = pg.get_by_role("alert").filter(has_text=re.compile("Échec"))
        alerte.first.wait_for(timeout=20000)
        txt = alerte.first.inner_text()
        ok = bool(re.search(r"code \d+", txt)) and re.search(r"hors d'une étape|extraction|étape", txt) and "Journal introuvable" in txt
        return ok, f"alerte={txt[:160]!r}"
    verif(res, "C2_echec", c2)

    def c3():
        pg.goto(BASE + "/"); pg.wait_for_timeout(600)
        pg.goto(BASE + "/chaine"); pg.wait_for_timeout(1500)
        alerte = pg.get_by_role("alert").filter(has_text=re.compile("Échec"))
        return alerte.count() >= 1 and "Journal introuvable" in alerte.first.inner_text(), f"alertes={alerte.count()}"
    verif(res, "C3_reprise_apres_rechargement", c3)

    def c5():
        pg.goto(BASE + "/chaine"); pg.wait_for_timeout(800)
        pg.get_by_role("button", name="Passer en Mode repli").click()
        pg.get_by_text("Mode repli", exact=True).first.wait_for(timeout=8000)
        pg.wait_for_timeout(1500)
        bouton = pg.get_by_role("button", name="Lancer la Chaîne")
        dis = bouton.get_attribute("aria-disabled")
        desc = bouton.get_attribute("aria-describedby")
        motif = pg.locator("#" + desc).inner_text() if desc else ""
        avant = pg.get_by_text("Échec").count()
        bouton.click(force=True); pg.wait_for_timeout(1500)
        apres = pg.get_by_text("Échec").count()
        motif_visible = pg.locator("#" + desc).is_visible() if desc else False
        return dis == "true" and bool(motif.strip()) and motif_visible and apres == avant, f"aria-disabled={dis} motif={motif[:80]!r} échec_avant={avant} après={apres}"
    verif(res, "C5_bouton_bloque_en_repli", c5)
    verif(res, "T2_390px_chaine", lambda: largeur_ok(pg, "/chaine"))
    return res


# ---------------------------------------------------------------- 7.16
def s716(b):
    res = {}
    pg = b.new_page()

    def c1():
        pg.goto(BASE + "/agent"); pg.wait_for_timeout(1200)
        saisie = pg.locator("textarea, input[type=text]:visible").filter(visible=True).count()
        msg = pg.get_by_text(re.compile("Mode repli", re.I)).count() > 0
        boutons = pg.locator("button.question-choix")
        n = boutons.count()
        boutons.first.click(); pg.wait_for_timeout(1500)
        texte = pg.locator("#reponse-texte").inner_text()
        badge = pg.locator("#reponse-badge").inner_text()
        mention = pg.locator("#reponse-repli").is_visible()
        actif = pg.evaluate("document.activeElement.id")
        return saisie == 0 and n >= 1 and texte.strip() and badge.strip() and mention and actif == "reponse", \
            f"saisie={saisie} questions={n} badge={badge!r} mention={mention} focus={actif}"
    verif(res, "C1_agent_repli", c1)

    def c1b():
        pg.goto(BASE + "/agent"); pg.wait_for_timeout(1200)
        n = pg.locator("button.question-choix").count(); avec_outils = 0
        for i in range(n):
            pg.locator("button.question-choix").nth(i).click(); pg.wait_for_timeout(700)
            if pg.locator("#reponse-outils .etiquette-outil").count() > 0: avec_outils += 1
        return avec_outils >= 1, f"questions avec outils listés : {avec_outils}/{n}"
    verif(res, "C1b_outils_listes", c1b)

    def c2():
        pg.goto(BASE + "/avant-apres"); pg.wait_for_timeout(1200)
        v1 = (pg.locator("#valeur-manuel").inner_text(), pg.locator("#valeur-chaine").inner_text())
        seg = pg.locator("#segment-periode button")
        seg.nth(1).click(); pg.wait_for_timeout(500)
        v2 = (pg.locator("#valeur-manuel").inner_text(), pg.locator("#valeur-chaine").inner_text())
        pressed = seg.nth(1).get_attribute("aria-pressed")
        return v1 != v2 and pressed == "true", f"avant={v1} après={v2} pressed={pressed}"
    verif(res, "C2_avant_apres_segment", c2)

    def c2b():
        pg.goto(BASE + "/avant-apres"); pg.wait_for_timeout(1200)
        n = pg.locator("#tableau-periodes tbody tr:visible").count()
        return n >= 1, f"lignes du tableau des périodes : {n}"
    verif(res, "C2b_tableau_periodes", c2b)

    def c3():
        pg.goto(BASE + "/pseudonymisation?ticket=DEMO-17"); pg.locator("#texte-original").wait_for(state="visible", timeout=90000)
        o = pg.locator("#texte-original").inner_text(); p_ = pg.locator("#texte-pseudo").inner_text()
        vus = set()
        for _ in range(40):
            pg.keyboard.press("Tab")
            vus.add(pg.evaluate("document.activeElement.id"))
        cote = pg.evaluate("(()=>{const a=document.getElementById('texte-original').getBoundingClientRect(),b=document.getElementById('texte-pseudo').getBoundingClientRect();return a.right<=b.left+1 && a.top<b.bottom && b.top<a.bottom})()")
        # autre ticket
        options = pg.locator("#choix-ticket option")
        autre = options.nth(1).get_attribute("value") if options.count() > 1 else None
        pg.select_option("#choix-ticket", value=autre)
        pg.get_by_role("button", name="Afficher").click(); pg.locator("#texte-original").wait_for(state="visible", timeout=60000)
        ok_url = f"ticket={autre}" in pg.url and pg.locator("#texte-original").inner_text().strip() != ""
        return o.strip() and p_.strip() and {"texte-original", "texte-pseudo"} <= vus and cote and ok_url, \
            f"focus_atteints={sorted(x for x in vus if x)} côte_à_côte={cote} autre={autre} url={pg.url[-30:]}"
    verif(res, "C3_pseudonymisation", c3)

    def c4():
        pg.goto(BASE + "/outillage"); pg.wait_for_timeout(1200)
        txt = pg.locator("#fiche").inner_text()
        pastilles = pg.locator("#fiche .pastille").count()
        return pastilles >= 1 and not re.search("[✅⚠❌]", txt) and "Oui" in txt, f"pastilles={pastilles}"
    verif(res, "C4_outillage", c4)

    def t2():
        mal = []
        for u in ("/avant-apres", "/pseudonymisation?ticket=DEMO-17"):
            ok, d = largeur_ok(pg, u)
            pg.set_viewport_size({"width": 390, "height": 844}); pg.goto(BASE + u); pg.wait_for_timeout(1000)
            pg.locator(".cartes-jumelles:visible").first.wait_for(timeout=60000)
            if pg.locator(".cartes-jumelles:visible").count():
                cols = pg.evaluate("getComputedStyle(Array.from(document.querySelectorAll('.cartes-jumelles')).find(e=>!e.hidden)).gridTemplateColumns.split(' ').length")
                if cols != 1: mal.append((u, "colonnes", cols))
            if not ok: mal.append((u, d))
            pg.set_viewport_size({"width": 1280, "height": 800})
        return not mal, f"écarts : {mal}"
    verif(res, "T2_390px", t2)
    return res


AXE = Path(os.environ["T12_AXE"]) if os.environ.get("T12_AXE") else None
PAGES_AXE = {
    "s714x": ["/", "/entites/ENT-A"],
    "s713": ["/", "/entites/ENT-A", "/chaine", "/agent", "/avant-apres", "/pseudonymisation", "/outillage"],
    "s714": ["/", "/entites/ENT-A"],
    "s715": ["/chaine"],
    "s716": ["/agent", "/avant-apres", "/pseudonymisation?ticket=DEMO-17", "/outillage"],
}


def axe_pages(b, story):
    """axe-core 4.x sur les pages de la story, à 1280 et 390 px. Rend {url@largeur: [ids de règles en violation]}."""
    if AXE is None:
        return {}
    sortie = {}
    pg = b.new_page()
    for largeur in (1280, 390):
        pg.set_viewport_size({"width": largeur, "height": 844})
        for u in PAGES_AXE[story]:
            try:
                pg.goto(BASE + u); pg.wait_for_timeout(1500)
                if "pseudonymisation?" in u:
                    pg.locator("#texte-original").wait_for(state="visible", timeout=60000)
                pg.add_script_tag(path=str(AXE))
                r = pg.evaluate("axe.run().then(r => r.violations.map(v => v.id + ':' + v.nodes.length))")
                sortie[f"{u}@{largeur}"] = r
            except Exception as exc:  # noqa: BLE001
                sortie[f"{u}@{largeur}"] = [f"exception : {str(exc).splitlines()[0][:100]}"]
    return sortie


HISTOIRES = {"s714x": s714x, "s713": s713, "s714": s714, "s715": s715, "s716": s716}

if __name__ == "__main__":
    arbre, story, mode = sys.argv[1], sys.argv[2], sys.argv[3]
    env = {k: v for k, v in os.environ.items() if not re.search(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", k, re.I)}
    env.pop("USINE_MODE_REPLI", None)
    env["USINE_CLE_PSEUDO"] = "cle-de-test-t12-pseudo"
    if mode == "repli":
        env["USINE_MODE_REPLI"] = "1"
    srv = subprocess.Popen([UV, "run", "--no-sync", "usine", "ui", "--port", str(PORT)], cwd=arbre, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        t0 = time.time()
        while time.time() - t0 < 60:
            try:
                urllib.request.urlopen(BASE + "/api/cadre", timeout=2).read(); break
            except Exception:
                time.sleep(0.5)
        with sync_playwright() as p:
            nav = p.chromium.launch(executable_path=str(CHROMIUM), headless=True)
            res = HISTOIRES[story](nav)
            axe = axe_pages(nav, story)
            nav.close()
        print(json.dumps({"checks": res, "axe": axe}, ensure_ascii=False))
    finally:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(srv.pid)], capture_output=True)
