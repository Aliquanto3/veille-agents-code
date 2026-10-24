from playwright.sync_api import sync_playwright
import sys
url = "file:///C:/Users/Utilisateur/Documents/GitHub/veille-agents-code/tests-pratiques/T7/notation.html"
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    for w in (1280, 390):
        pg = b.new_page(viewport={"width": w, "height": 900})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url)
        n_img = pg.locator("img").count()
        pg.locator('input[data-rendu="A"][data-critere="finition"][value="4"]').check(force=True)
        prog = pg.locator("#progres").inner_text()
        sw = pg.evaluate("document.documentElement.scrollWidth")
        pg.click("#btn-export")
        z = pg.locator("#export-zone").input_value()
        print(w, "images", n_img, "progres", prog, "scrollWidth", sw, "erreurs", errs, "export", z.replace("\n", " ")[:80])
        pg.close()
    b.close()
