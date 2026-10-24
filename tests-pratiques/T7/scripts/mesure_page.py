"""Mesures automatiques sur la page rendue d'un bras (serveur lancé localement).

Usage : python mesure_page.py <repertoire_du_bras> <port> <sortie_dir>
"""
import io, json, os, re, subprocess, sys, time, unicodedata, urllib.request
from pathlib import Path
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

T7 = Path(__file__).resolve().parent.parent
AXE = T7 / "mesures" / "node" / "node_modules" / "axe-core" / "axe.min.js"
ENGINE = T7 / "tools" / "impeccable-engine" / "impeccable-windows-x64.exe"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
LARGEURS = (390, 768, 1280)

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


def remplir(page, demandeur, service, montant, motif):
    page.get_by_label("Demandeur", exact=True).fill(demandeur)
    sel = page.get_by_label("Service", exact=True)
    if service:
        sel.select_option(label=service)
    else:
        try:
            sel.select_option(index=0)
        except Exception:
            pass
    page.get_by_label("Montant (€)").fill(montant)
    page.get_by_label("Motif", exact=True).fill(motif)


def fonctionnel(browser, base):
    """Contrat fonctionnel : retourne {controle: bool}."""
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
    page.goto(base + "/demandes")
    check("h1", lambda: page.locator("h1").first.inner_text().strip() == "Demandes d'achat")
    check("champs_labels", lambda: all(page.get_by_label(l, exact=ex).count() == 1 for l, ex in [("Demandeur", True), ("Service", True), ("Montant (€)", False), ("Motif", True), ("Rechercher un demandeur", True), ("Filtrer par service", True)]))
    check("bouton", lambda: page.get_by_role("button", name="Enregistrer la demande").count() == 1)
    check("novalidate", lambda: page.locator("form[novalidate]").count() >= 1)
    check("six_lignes_initiales", lambda: page.locator("tbody tr:visible").count() == 6)
    # erreurs
    remplir(page, "", "", "-5", "court")
    with page.expect_response(lambda r: r.request.method == "POST") as ri:
        page.get_by_role("button", name="Enregistrer la demande").click()
    check("post_422", lambda: ri.value.status == 422)
    page.wait_for_load_state()
    check("bandeau_4_erreurs", lambda: page.locator('[role="alert"]').filter(has_text="Le formulaire contient 4 erreurs.").count() >= 1)
    for nom, m in [("msg_demandeur", "Le demandeur est obligatoire."), ("msg_service", "Choisissez un service."),
                   ("msg_montant", "Le montant doit être un nombre supérieur à 0 et au plus 50 000 €."),
                   ("msg_motif", "Le motif doit contenir entre 10 et 200 caractères.")]:
        check(nom, lambda m=m: m in txt())
    check("valeurs_conservees", lambda: page.get_by_label("Montant (€)").input_value() == "-5" and page.get_by_label("Motif", exact=True).input_value() == "court")
    check("aria_invalid", lambda: page.locator('[aria-invalid="true"]').count() >= 4)
    check("aria_describedby", lambda: page.locator('[aria-invalid="true"][aria-describedby]').count() >= 4)
    # une seule erreur : singulier
    page.goto(base + "/demandes")
    remplir(page, "Alice Test", "IT", "10", "Un motif suffisant")
    page.get_by_label("Montant (€)").fill("0")
    page.get_by_role("button", name="Enregistrer la demande").click()
    page.wait_for_load_state()
    check("bandeau_1_erreur", lambda: page.locator('[role="alert"]').filter(has_text="Le formulaire contient 1 erreur.").count() >= 1)
    # succès
    page.goto(base + "/demandes")
    remplir(page, "Alice Test", "IT", "123.45", "Achat de matériel de test")
    with page.expect_navigation():
        page.get_by_role("button", name="Enregistrer la demande").click()
    page.wait_for_load_state()
    check("confirmation", lambda: page.locator('[role="status"]').filter(has_text="Demande enregistrée.").count() >= 1)
    check("ligne_en_tete", lambda: "Alice Test" in page.locator("tbody tr").first.inner_text())
    check("montant_format", lambda: "123,45 €" in page.locator("tbody tr").first.inner_text().replace("\u202f", " ").replace("\u00a0", " "))
    check("date_format", lambda: re.search(r"\d{2}/\d{2}/\d{4}", page.locator("tbody tr").first.inner_text()) is not None)
    check("sept_lignes", lambda: page.locator("tbody tr:visible").count() == 7)
    page.reload()
    page.wait_for_load_state()
    check("confirmation_unique", lambda: page.locator('[role="status"]').filter(has_text="Demande enregistrée.").count() == 0)
    # filtres
    rech = page.get_by_label("Rechercher un demandeur", exact=True)
    svc = page.get_by_label("Filtrer par service", exact=True)
    rech.fill("alice")
    page.wait_for_timeout(200)
    check("filtre_nom", lambda: page.locator("tbody tr:visible").count() == 1)
    check("compteur_singulier", lambda: "1 demande affichée" in txt())
    rech.fill("lefevre")
    page.wait_for_timeout(200)
    check("filtre_accents", lambda: page.locator("tbody tr:visible").count() == 1)
    rech.fill("zzzz")
    page.wait_for_timeout(200)
    check("message_vide", lambda: "Aucune demande ne correspond aux filtres." in txt())
    rech.fill("")
    svc.select_option(label="IT")
    page.wait_for_timeout(200)
    check("filtre_service", lambda: page.locator("tbody tr:visible").count() == 3)
    check("compteur_pluriel", lambda: "3 demandes affichées" in txt())
    rech.fill("alice")
    page.wait_for_timeout(200)
    check("filtres_combines", lambda: page.locator("tbody tr:visible").count() == 1)
    svc.select_option(label="Finance")
    page.wait_for_timeout(200)
    check("combines_vide", lambda: "Aucune demande ne correspond aux filtres." in txt())
    check("tous_les_services", lambda: page.get_by_label("Filtrer par service", exact=True).locator("option").first.inner_text().strip() == "Tous les services")
    ctx.close()
    bools = [v for v in res.values() if isinstance(v, bool)]
    res["_reussis"] = sum(bools)
    res["_total"] = len(bools)
    return res


def main(arm_dir, port, sortie):
    arm_dir, sortie = Path(arm_dir).resolve(), Path(sortie).resolve()
    sortie.mkdir(parents=True, exist_ok=True)
    base = f"http://127.0.0.1:{port}"
    srv = subprocess.Popen(["uv", "run", "--project", str(arm_dir), "uvicorn", "app.main:app", "--port", str(port), "--log-level", "warning"],
                           cwd=arm_dir, stdout=open(sortie / "serveur.log", "wb"), stderr=subprocess.STDOUT)
    out = {"bras": arm_dir.name}
    try:
        if not attendre(base + "/demandes"):
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
                page.goto(base + "/demandes")
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
                        "couleurs_litterales": len(re.findall(r"#[0-9a-fA-F]{3,8}|rgba?\(|hsla?\(|oklch\(", css)),
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
                page.goto(base + "/demandes")
                remplir(page, "", "", "-5", "court")
                page.get_by_role("button", name="Enregistrer la demande").click()
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
                       IMPECCABLE_HOME=str(T7 / "tools" / "impeccable-home"), IMPECCABLE_BROWSER=EDGE)
            r = subprocess.run([str(ENGINE), "detect", "--json", "--no-config", base + "/demandes"], capture_output=True, text=True, env=env, cwd=str(T7 / "mesures"), timeout=180)
            try:
                dj = json.loads(r.stdout or "[]")
            except Exception:
                dj = None
            out["impeccable_detect"] = {"rc": r.returncode, "n": (len(dj) if isinstance(dj, list) else None), "brut": dj, "stderr": r.stderr[-300:]}
            out["fonctionnel"] = fonctionnel(browser, base)
            browser.close()
    finally:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(srv.pid)], capture_output=True)
    (sortie / "mesures.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return out


if __name__ == "__main__":
    o = main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
    a = o.get("axe", {})
    print(json.dumps({"bras": o.get("bras"), "poids": o.get("poids"), "focus": o.get("focus"), "deb390": o.get("debordement_390"),
                      "axe": {k: a.get(k) for k in ("violations_total", "noeuds_total", "regles_distinctes")},
                      "detect_n": (o.get("impeccable_detect") or {}).get("n"),
                      "fonc": [o.get("fonctionnel", {}).get("_reussis"), o.get("fonctionnel", {}).get("_total")]}, ensure_ascii=False, default=str))
