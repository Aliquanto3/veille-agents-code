"""Mesures automatiques sur la page rendue d'un bras (serveur lancé localement). Adapté de T7/scripts/mesure_page.py
pour deux écrans (1 : Demandes d'achat ; 2 : Notes de frais) et ajoute la conformité aux règles de DESIGN.md.

Usage (depuis le projet de mesure, qui porte playwright et pillow) :
    uv run --project <t7ter/mesures> python mesure_page.py <rendu> <ecran 1|2> <port> <sortie_dir>
"""
import io, json, os, re, subprocess, sys, time, urllib.request
from datetime import date
from pathlib import Path
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from chemins import ARMS, EDGE, OUTILS

AXE = OUTILS / "axe.min.js"
ENGINE = OUTILS / "impeccable-windows-x64.exe"
CONFORMITE_JS = (Path(__file__).parent / "conformite.js").read_text(encoding="utf-8")
LARGEURS = (390, 768, 1280)

ECRANS = {
    1: dict(chemin="/demandes", id="Demandeur", cat="Service", montant="Montant (€)", date=None, texte="Motif", submit="Enregistrer la demande",
            idCol="Demandeur", montantCol="Montant", catCols=["Service"], descCol="Motif"),
    2: dict(chemin="/notes-de-frais", id="Collaborateur", cat="Catégorie", montant="Montant (€)", date="Date de la dépense", texte="Description",
            submit="Enregistrer la note", idCol="Collaborateur", montantCol="Montant", catCols=["Catégorie", "Statut"], descCol="Description"),
}

JS_CONTRASTE = r"""
() => {
  const _cv=document.createElement('canvas'); _cv.width=_cv.height=1; const _cx=_cv.getContext('2d',{willReadFrequently:true});
  function parse(c){ if(!c||c==='transparent') return {r:0,g:0,b:0,a:0}; _cx.clearRect(0,0,1,1); _cx.fillStyle='#000'; _cx.fillStyle=c; _cx.fillRect(0,0,1,1); const d=_cx.getImageData(0,0,1,1).data; return {r:d[0],g:d[1],b:d[2],a:d[3]/255}; }
  function over(f,b){const a=f.a; return {r:f.r*a+b.r*(1-a), g:f.g*a+b.g*(1-a), b:f.b*a+b.b*(1-a), a:1};}
  function lum(c){const f=v=>{v/=255; return v<=0.03928? v/12.92 : Math.pow((v+0.055)/1.055,2.4)}; return 0.2126*f(c.r)+0.7152*f(c.g)+0.0722*f(c.b);}
  function bgOf(el){let layers=[]; let e=el; while(e){const cs=getComputedStyle(e); const c=parse(cs.backgroundColor); if(cs.backgroundImage!=='none') layers.push('image'); if(c&&c.a>0){layers.push(c); if(c.a>=0.99) break;} e=e.parentElement;} let base={r:255,g:255,b:255,a:1}; for(let i=layers.length-1;i>=0;i--){ if(layers[i]==='image') continue; base=over(layers[i],base);} return base;}
  const out=[]; const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT); let n;
  while(n=w.nextNode()){ const t=n.textContent.trim(); if(!t) continue; const el=n.parentElement; if(!el) continue; const cs=getComputedStyle(el); if(cs.visibility==='hidden'||cs.display==='none') continue; const r=el.getBoundingClientRect(); if(r.width===0||r.height===0) continue; if(['SCRIPT','STYLE','OPTION'].includes(el.tagName)) continue;
    let fg=parse(cs.color); if(!fg) continue; const bg=bgOf(el); fg=over(fg,bg); const L1=lum(fg),L2=lum(bg); const ratio=(Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05); const size=parseFloat(cs.fontSize); const bold=parseInt(cs.fontWeight)>=700; const large=size>=24||(size>=18.66&&bold);
    out.push({t:t.slice(0,30), ratio:Math.round(ratio*100)/100, large, size});
  }
  return out;
}
"""

JS_FOCUSABLES = r"""
() => Array.from(document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea,summary,[tabindex]:not([tabindex="-1"])'))
  .filter(e=>{const r=e.getBoundingClientRect(); const cs=getComputedStyle(e); return r.width>0&&r.height>0&&cs.visibility!=='hidden'&&!e.disabled;})
  .map((e,i)=>{e.setAttribute('data-mesure-idx',i); return (e.tagName+'#'+(e.id||'')+'.'+(e.className||'')).slice(0,60);})
"""

JS_EXTRA = r"""
() => {
  const els=Array.from(document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea')).filter(e=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0});
  let p24=0,p44=0; for(const e of els){const r=e.getBoundingClientRect(); const m=Math.min(r.width,r.height); if(m<24) p24++; if(m<44) p44++;}
  let minfs=999; const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT); let n; while(n=w.nextNode()){ if(!n.textContent.trim()) continue; const el=n.parentElement; if(!el||['SCRIPT','STYLE'].includes(el.tagName)) continue; const r=el.getBoundingClientRect(); if(r.width===0) continue; minfs=Math.min(minfs,parseFloat(getComputedStyle(el).fontSize)); }
  const body=getComputedStyle(document.body);
  return {interactifs:els.length, cibles_sous_24:p24, cibles_sous_44:p44, police_min_px:minfs, police_corps_px:parseFloat(body.fontSize)};
}
"""

JS_DEBORD = "() => ({sw: document.documentElement.scrollWidth, iw: window.innerWidth})"

# Totaux par statut (écran 2) : pour chaque statut, texte du plus petit bloc qui le contient avec un montant.
JS_TOTAUX = r"""
(statuts) => {
  const h2 = Array.from(document.querySelectorAll('h2')).find(h => h.textContent.trim() === 'Total par statut');
  if (!h2) return null;
  let sec = h2.closest('section'); if (!sec) return null;
  const norm = s => s.replace(/[\s  ]+/g, ' ').trim();
  const res = {texte: norm(sec.innerText), blocs: {}};
  for (const s of statuts) {
    let best = null;
    for (const el of sec.querySelectorAll('*')) {
      const t = norm(el.textContent);
      if (!t.includes(s) || !/\d[\d ]*,\d{2} €/.test(t)) continue;
      const autres = statuts.filter(x => x !== s && t.includes(x));
      if (autres.length) continue;
      if (!best || t.length < best.length) best = t;
    }
    res.blocs[s] = best;
  }
  return res;
}
"""


def attendre(url, t=60):
    t0 = time.time()
    while time.time() - t0 < t:
        try:
            urllib.request.urlopen(url, timeout=2).read()
            return True
        except Exception:
            time.sleep(0.5)
    return False


def axe_run(page):
    page.add_script_tag(path=str(AXE))
    return page.evaluate("async () => { const r = await axe.run(document); return {v: r.violations.map(x=>({id:x.id,impact:x.impact,nodes:x.nodes.length})), inc: r.incomplete.map(x=>({id:x.id,nodes:x.nodes.length}))}; }")


def focus_test(page):
    noms = page.evaluate(JS_FOCUSABLES)
    sans, details = 0, []
    page.mouse.move(0, 0)
    for i, nom in enumerate(noms):
        loc = page.locator(f'[data-mesure-idx="{i}"]')
        try:
            loc.scroll_into_view_if_needed(timeout=2000)
            bb = loc.bounding_box()
            if not bb:
                continue
            clip = {"x": max(bb["x"] - 8, 0), "y": max(bb["y"] - 8, 0), "width": bb["width"] + 16, "height": bb["height"] + 16}
            page.evaluate("document.activeElement && document.activeElement.blur()")
            a = Image.open(io.BytesIO(page.screenshot(clip=clip))).convert("RGB")
            page.keyboard.press("Shift")
            loc.focus()
            b = Image.open(io.BytesIO(page.screenshot(clip=clip))).convert("RGB")
            if ImageChops.difference(a, b).getbbox() is None:
                sans += 1
                details.append(nom)
        except Exception as e:
            details.append(f"{nom}: erreur {e.__class__.__name__}")
    return {"focusables": len(noms), "sans_indicateur": sans, "liste_sans": details[:10]}


def poids(reponses):
    tot = {"html": 0, "css": 0, "js": 0, "autre": 0}
    ext = []
    for url, typ, taille in reponses:
        if not url.startswith("http://127.0.0.1"):
            ext.append(url)
            continue
        k = {"document": "html", "stylesheet": "css", "script": "js"}.get(typ, "autre")
        tot[k] += taille
    tot["total"] = sum(tot.values())
    tot["requetes_externes"] = ext[:10]
    tot["n_externes"] = len(ext)
    return tot


def remplir(page, cfg, ident, cat, montant, texte, jour=None):
    page.get_by_label(cfg["id"], exact=True).fill(ident)
    sel = page.get_by_label(cfg["cat"], exact=True)
    if cat:
        sel.select_option(label=cat)
    else:
        try:
            sel.select_option(index=0)
        except Exception:
            pass
    page.get_by_label("Montant (€)").fill(montant)
    if cfg["date"]:
        page.get_by_label(cfg["date"], exact=True).fill(jour or "")
    page.get_by_label(cfg["texte"], exact=True).fill(texte)


def sp(s):
    return s.replace(" ", " ").replace(" ", " ")


def fonctionnel(browser, base, ecran):
    """Contrat fonctionnel : retourne {controle: bool}."""
    cfg = ECRANS[ecran]
    res = {}
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()

    def check(nom, fn):
        try:
            res[nom] = bool(fn())
        except Exception as e:
            res[nom] = False
            res[nom + "_err"] = f"{e.__class__.__name__}: {str(e)[:120]}"

    txt = lambda: page.locator("body").inner_text()
    bouton = lambda: page.get_by_role("button", name=cfg["submit"])
    page.goto(base + cfg["chemin"])
    aujourdhui = date.today().isoformat()
    if ecran == 1:
        check("h1", lambda: page.locator("h1").first.inner_text().strip() == "Demandes d'achat")
        labels = [("Demandeur", True), ("Service", True), ("Montant (€)", False), ("Motif", True), ("Rechercher un demandeur", True), ("Filtrer par service", True)]
        n_init, n_apres, sing, plur, vide = 6, 7, "1 demande affichée", "3 demandes affichées", "Aucune demande ne correspond aux filtres."
        msgs = [("msg_demandeur", "Le demandeur est obligatoire."), ("msg_service", "Choisissez un service."),
                ("msg_montant", "Le montant doit être un nombre supérieur à 0 et au plus 50 000 €."),
                ("msg_motif", "Le motif doit contenir entre 10 et 200 caractères.")]
        conf, ident, cat, rech_l, filt_l, tous = "Demande enregistrée.", "Alice Test", "IT", "Rechercher un demandeur", "Filtrer par service", "Tous les services"
        filt_val, nb_filt, filt_autre = "IT", 3, "Finance"
        accent_q, accent_n = "lefevre", 1
        texte_ok, montant_ok = "Achat de matériel de test", "123.45"
        err_n = 4
    else:
        check("h1", lambda: page.locator("h1").first.inner_text().strip() == "Notes de frais")
        labels = [("Collaborateur", True), ("Catégorie", True), ("Montant (€)", False), ("Date de la dépense", True), ("Description", True), ("Rechercher un collaborateur", True), ("Filtrer par statut", True)]
        n_init, n_apres, sing, plur, vide = 8, 9, "1 note affichée", "3 notes affichées", "Aucune note ne correspond aux filtres."
        msgs = [("msg_collaborateur", "Le collaborateur est obligatoire."), ("msg_categorie", "Choisissez une catégorie."),
                ("msg_montant", "Le montant doit être un nombre supérieur à 0 et au plus 5 000 €."),
                ("msg_date", "La date de la dépense est obligatoire et ne peut pas être dans le futur."),
                ("msg_description", "La description doit contenir entre 10 et 200 caractères.")]
        conf, ident, cat, rech_l, filt_l, tous = "Note de frais enregistrée.", "Alice Test", "Repas", "Rechercher un collaborateur", "Filtrer par statut", "Tous les statuts"
        filt_val, nb_filt, filt_autre = "Validée", 3, "Refusée"
        accent_q, accent_n = "lefevre", 2
        texte_ok, montant_ok = "Repas client à l'issue de la démonstration", "123.45"
        err_n = 5
    check("champs_labels", lambda: all(page.get_by_label(l, exact=ex).count() == 1 for l, ex in labels))
    check("bouton", lambda: bouton().count() == 1)
    check("novalidate", lambda: page.locator("form[novalidate]").count() >= 1)
    check("lignes_initiales", lambda: page.locator("tbody tr:visible").count() == n_init)
    if ecran == 2:
        premiers = ["Emma Lefèvre", "Lucas Petit", "Karim Haddad", "Sofia Bernard", "Camille Martin", "Emma Lefèvre", "Julien Moreau", "Camille Martin"]
        check("tri_initial", lambda: len(page.locator("tbody tr").all()) == len(premiers) and all(n in r.locator("td, th").first.inner_text() for r, n in zip(page.locator("tbody tr").all(), premiers)))
        att = {"Soumise": (2, "441,90"), "Validée": (3, "2 074,60"), "Refusée": (1, "36,75"), "Remboursée": (2, "100,40")}

        def totaux_ok(att):
            t = page.evaluate(JS_TOTAUX, list(att))
            if not t:
                return False
            for s, (n, m) in att.items():
                b = t["blocs"].get(s)
                if not b:
                    # repli : segment de texte qui suit le nom
                    i = t["texte"].find(s)
                    nxt = [t["texte"].find(x, i + 1) for x in att if x != s and t["texte"].find(x, i + 1) > i]
                    b = t["texte"][i: (min(nxt) if nxt else len(t["texte"]))] if i >= 0 else ""
                if f"{m} €" not in b or not re.search(rf"(?<![\d,]){n}(?![\d,])", b.replace(f"{m} €", "")):
                    return False
            return True
        check("totaux_initiaux", lambda: totaux_ok(att))
    # erreurs
    if ecran == 1:
        remplir(page, cfg, "", "", "-5", "court")
    else:
        remplir(page, cfg, "", "", "-5", "court", "")
    with page.expect_response(lambda r: r.request.method == "POST") as ri:
        bouton().click()
    check("post_422", lambda: ri.value.status == 422)
    page.wait_for_load_state()
    check(f"bandeau_{err_n}_erreurs", lambda: page.locator('[role="alert"]').filter(has_text=f"Le formulaire contient {err_n} erreurs.").count() >= 1)
    for nom, m in msgs:
        check(nom, lambda m=m: m in txt())
    check("valeurs_conservees", lambda: page.get_by_label("Montant (€)").input_value() == "-5" and page.get_by_label(cfg["texte"], exact=True).input_value() == "court")
    check("aria_invalid", lambda: page.locator('[aria-invalid="true"]').count() >= err_n)
    check("aria_describedby", lambda: page.locator('[aria-invalid="true"][aria-describedby]').count() >= err_n)
    # une seule erreur : singulier
    page.goto(base + cfg["chemin"])
    remplir(page, cfg, "Alice Test", cat, "10", "Un motif suffisant", "2026-10-20")
    page.get_by_label("Montant (€)").fill("0")
    bouton().click()
    page.wait_for_load_state()
    check("bandeau_1_erreur", lambda: page.locator('[role="alert"]').filter(has_text="Le formulaire contient 1 erreur.").count() >= 1)
    if ecran == 2:
        page.goto(base + cfg["chemin"])
        remplir(page, cfg, "Alice Test", cat, "10", "Un motif suffisant", "2099-01-01")
        with page.expect_response(lambda r: r.request.method == "POST") as rf:
            bouton().click()
        page.wait_for_load_state()
        check("date_future_refusee", lambda: rf.value.status == 422 and "La date de la dépense est obligatoire et ne peut pas être dans le futur." in txt())
    # succès
    page.goto(base + cfg["chemin"])
    remplir(page, cfg, ident, cat, montant_ok, texte_ok, aujourdhui)
    with page.expect_navigation():
        bouton().click()
    page.wait_for_load_state()
    check("confirmation", lambda: page.locator('[role="status"]').filter(has_text=conf).count() >= 1)
    check("ligne_en_tete", lambda: ident in page.locator("tbody tr").first.inner_text())
    check("montant_format", lambda: "123,45 €" in sp(page.locator("tbody tr").first.inner_text()))
    check("date_format", lambda: re.search(r"\d{2}/\d{2}/\d{4}", page.locator("tbody tr").first.inner_text()) is not None)
    check("lignes_apres_ajout", lambda: page.locator("tbody tr:visible").count() == n_apres)
    if ecran == 2:
        check("statut_soumise", lambda: "Soumise" in page.locator("tbody tr").first.inner_text())
        check("totaux_apres_ajout", lambda: totaux_ok({"Soumise": (3, "565,35"), "Validée": (3, "2 074,60"), "Refusée": (1, "36,75"), "Remboursée": (2, "100,40")}))
    page.reload()
    page.wait_for_load_state()
    check("confirmation_unique", lambda: page.locator('[role="status"]').filter(has_text=conf).count() == 0)
    # filtres
    rech = page.get_by_label(rech_l, exact=True)
    svc = page.get_by_label(filt_l, exact=True)
    rech.fill("alice")
    page.wait_for_timeout(200)
    check("filtre_nom", lambda: page.locator("tbody tr:visible").count() == 1)
    check("compteur_singulier", lambda: sing in txt())
    rech.fill(accent_q)
    page.wait_for_timeout(200)
    check("filtre_accents", lambda: page.locator("tbody tr:visible").count() == accent_n)
    rech.fill("zzzz")
    page.wait_for_timeout(200)
    check("message_vide", lambda: vide in txt())
    rech.fill("")
    svc.select_option(label=filt_val)
    page.wait_for_timeout(200)
    check("filtre_categorie", lambda: page.locator("tbody tr:visible").count() == nb_filt)
    check("compteur_pluriel", lambda: plur in txt())
    if ecran == 2:
        check("totaux_independants_des_filtres", lambda: totaux_ok({"Soumise": (3, "565,35"), "Validée": (3, "2 074,60"), "Refusée": (1, "36,75"), "Remboursée": (2, "100,40")}))
    rech.fill("alice")
    page.wait_for_timeout(200)
    if ecran == 1:
        check("filtres_combines", lambda: page.locator("tbody tr:visible").count() == 1)
    else:
        check("filtres_combines", lambda: page.locator("tbody tr:visible").count() == 0 and vide in txt())
        rech.fill(accent_q)
        page.wait_for_timeout(200)
        check("filtres_combines_2", lambda: page.locator("tbody tr:visible").count() == 1)
        rech.fill("alice")
        page.wait_for_timeout(200)
    svc.select_option(label=filt_autre)
    page.wait_for_timeout(200)
    check("combines_vide", lambda: vide in txt())
    check("tous_les_choix", lambda: page.get_by_label(filt_l, exact=True).locator("option").first.inner_text().strip() == tous)
    ctx.close()
    bools = [v for v in res.values() if isinstance(v, bool)]
    res["_reussis"] = sum(bools)
    res["_total"] = len(bools)
    return res


def conformite(browser, base, ecran):
    """Conformité aux règles de DESIGN.md : initial 1280, erreur 1280, typographie 390 et 1280."""
    cfg = ECRANS[ecran]
    out = {}
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(base + cfg["chemin"])
    page.wait_for_load_state("networkidle")
    out["initial"] = page.evaluate(CONFORMITE_JS, {"mode": "initial", "cfg": cfg})
    typo1280 = page.evaluate(CONFORMITE_JS, {"mode": "typo", "cfg": cfg})
    remplir(page, cfg, "", "", "-5", "court", "") if ecran == 2 else remplir(page, cfg, "", "", "-5", "court")
    page.get_by_role("button", name=cfg["submit"]).click()
    page.wait_for_load_state("networkidle")
    out["erreur"] = page.evaluate(CONFORMITE_JS, {"mode": "erreur", "cfg": cfg})
    ctx.close()
    ctx = browser.new_context(viewport={"width": 390, "height": 900})
    page = ctx.new_page()
    page.goto(base + cfg["chemin"])
    page.wait_for_load_state("networkidle")
    typo390 = page.evaluate(CONFORMITE_JS, {"mode": "typo", "cfg": cfg})
    ctx.close()
    # R8 : même famille, mêmes styles de libellé aux deux largeurs (taille notée à part)
    diffs, tailles = [], []
    for k, a in typo1280["snap"].items():
        b = typo390["snap"].get(k)
        if a is None or b is None:
            continue
        for champ in ("famille", "graisse", "casse", "interlettrage", "style"):
            if a[champ] != b[champ]:
                diffs.append(f"{k}.{champ}: {a[champ]} -> {b[champ]}")
        if a["taille"] != b["taille"]:
            tailles.append(f"{k}: {a['taille']} -> {b['taille']}")
    familles_ok = typo1280["familles"] == typo390["familles"]
    out["R8"] = (not diffs) and familles_ok
    out["R8_detail"] = {"ecarts": diffs[:8], "familles_1280": typo1280["familles"], "familles_390": typo390["familles"], "ecarts_de_taille": tailles[:8]}
    # synthèse des contrôles
    regles = ["R1", "R1bis", "R2", "R3", "R4", "R4bis", "R5", "R6", "R7", "R8", "R9"]
    vals = {}
    for r in regles:
        v = out["initial"].get(r) if r in out["initial"] else out["erreur"].get(r)
        if r == "R8":
            v = out["R8"]
        vals[r] = v
    out["controles"] = vals
    appl = [v for v in vals.values() if v is not None]
    out["score"] = {"vrais": sum(1 for v in appl if v), "applicables": len(appl)}
    return out


def main(rendu, ecran, port, sortie):
    arm_dir, sortie = (Path(rendu) if Path(rendu).is_absolute() else ARMS / rendu).resolve(), Path(sortie).resolve()
    rendu = arm_dir.name
    cfg = ECRANS[ecran]
    sortie.mkdir(parents=True, exist_ok=True)
    base = f"http://127.0.0.1:{port}"
    srv = subprocess.Popen(["uv", "run", "--project", str(arm_dir), "uvicorn", "app.main:app", "--port", str(port), "--log-level", "warning"],
                           cwd=arm_dir, stdout=open(sortie / "serveur.log", "wb"), stderr=subprocess.STDOUT)
    out = {"rendu": rendu, "ecran": ecran}
    try:
        if not attendre(base + cfg["chemin"]):
            out["erreur"] = "serveur indisponible"
            return out
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            axe_tot = {}
            for w in LARGEURS:
                ctx = browser.new_context(viewport={"width": w, "height": 900})
                page = ctx.new_page()
                rep = []
                page.on("response", lambda r: rep.append((r.url, r.request.resource_type, len(r.body()) if r.ok else 0)))
                csstxt = []
                page.on("response", lambda r: csstxt.append(r.text()) if (r.ok and r.request.resource_type == "stylesheet") else None)
                page.goto(base + cfg["chemin"])
                page.wait_for_load_state("networkidle")
                page.screenshot(path=str(sortie / f"initial_{w}.png"), full_page=True)
                deb = page.evaluate(JS_DEBORD)
                if w == 1280:
                    out["poids"] = poids(rep)
                    out["poids"]["inline"] = page.evaluate("() => ({css: Array.from(document.querySelectorAll('style')).reduce((a,s)=>a+s.textContent.length,0), js: Array.from(document.querySelectorAll('script:not([src])')).reduce((a,s)=>a+s.textContent.length,0)})")
                    c = page.evaluate(JS_CONTRASTE)
                    bas = [x for x in c if x["ratio"] < (3.0 if x["large"] else 4.5)]
                    out["contraste_perso"] = {"textes": len(c), "ratio_min": min((x["ratio"] for x in c), default=None), "sous_seuil": len(bas), "exemples": bas[:5]}
                    out["focus"] = focus_test(page)
                    css = "\n".join(csstxt) + "\n" + page.evaluate("() => Array.from(document.querySelectorAll('style')).map(s=>s.textContent).join(' ')")
                    out["css_signaux"] = {
                        "reduced_motion": "prefers-reduced-motion" in css,
                        "focus_visible": ":focus-visible" in css,
                        "custom_props": len(re.findall(r"--[a-zA-Z0-9_-]+\s*:", css)),
                        "couleurs_litterales": len(re.findall(r"#[0-9a-fA-F]{3,8}|rgba?\(|hsla?\(|oklch\(", css)),
                        "transition_all": bool(re.search(r"transition\s*:\s*all", css)),
                        "media_queries": len(re.findall(r"@media", css)),
                    }
                    out["extra_1280"] = page.evaluate(JS_EXTRA)
                    out["polices"] = page.evaluate("() => Array.from(new Set(Array.from(document.querySelectorAll('body *')).slice(0,400).map(e=>getComputedStyle(e).fontFamily.split(',')[0].trim()))).slice(0,8)")
                axe_tot[f"initial_{w}"] = axe_run(page)
                if w == 390:
                    out["extra_390"] = page.evaluate(JS_EXTRA)
                    out["debordement_390"] = deb["sw"] > deb["iw"]
                    out["debordement_390_detail"] = deb
                ctx.close()
            for w in (1280, 390):
                ctx = browser.new_context(viewport={"width": w, "height": 900})
                page = ctx.new_page()
                page.goto(base + cfg["chemin"])
                if ecran == 2:
                    remplir(page, cfg, "", "", "-5", "court", "")
                else:
                    remplir(page, cfg, "", "", "-5", "court")
                page.get_by_role("button", name=cfg["submit"]).click()
                page.wait_for_load_state("networkidle")
                page.screenshot(path=str(sortie / f"erreur_{w}.png"), full_page=True)
                if w == 1280:
                    axe_tot["erreur_1280"] = axe_run(page)
                ctx.close()
            regles = set()
            noeuds = inst = 0
            par_impact = {}
            for etat, a in axe_tot.items():
                for v in a["v"]:
                    inst += 1
                    noeuds += v["nodes"]
                    regles.add(v["id"])
                    par_impact[v["impact"]] = par_impact.get(v["impact"], 0) + 1
            out["axe"] = {"violations_total": inst, "noeuds_total": noeuds, "regles_distinctes": sorted(regles), "par_impact": par_impact,
                          "contraste_axe_noeuds": sum(v["nodes"] for a in axe_tot.values() for v in a["v"] if v["id"] == "color-contrast"),
                          "detail": axe_tot}
            env = dict(os.environ, IMPECCABLE_NO_TELEMETRY="1", IMPECCABLE_NO_UPDATE_CHECK="1", IMPECCABLE_NO_STALENESS_CHECK="1",
                       IMPECCABLE_HOME=str(OUTILS / "impeccable-home"), IMPECCABLE_BROWSER=EDGE)
            try:
                r = subprocess.run([str(ENGINE), "detect", "--json", "--no-config", base + cfg["chemin"]], capture_output=True, text=True, env=env, cwd=str(OUTILS), timeout=180)
                try:
                    dj = json.loads(r.stdout or "[]")
                except Exception:
                    dj = None
                out["impeccable_detect"] = {"rc": r.returncode, "n": (len(dj) if isinstance(dj, list) else None), "brut": dj, "stderr": r.stderr[-300:]}
            except Exception as e:
                out["impeccable_detect"] = {"rc": None, "n": None, "brut": None, "stderr": f"{e.__class__.__name__}: {e}"}
            out["conformite"] = conformite(browser, base, ecran)
            out["fonctionnel"] = fonctionnel(browser, base, ecran)
            browser.close()
    finally:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(srv.pid)], capture_output=True)
    (sortie / "mesures.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return out


if __name__ == "__main__":
    o = main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    a = o.get("axe", {})
    print(json.dumps({"rendu": o.get("rendu"), "poids": (o.get("poids") or {}).get("css"), "deb390": o.get("debordement_390"),
                      "axe": {k: a.get(k) for k in ("violations_total", "noeuds_total", "regles_distinctes")},
                      "detect_n": (o.get("impeccable_detect") or {}).get("n"),
                      "conformite": (o.get("conformite") or {}).get("score"),
                      "fonc": [o.get("fonctionnel", {}).get("_reussis"), o.get("fonctionnel", {}).get("_total")]}, ensure_ascii=False, default=str))
