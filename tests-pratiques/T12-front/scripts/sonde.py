"""Exploration : sert un arbre de reference et affiche le texte des pages. Usage : sonde.py SID MODE(repli|reel) URL..."""
import sys, subprocess, time
from commun import *
from playwright.sync_api import sync_playwright

sid, mode, urls = sys.argv[1], sys.argv[2], sys.argv[3:]
arbre = SCRATCH / "ref" / sid
env = env_enfant()
env["USINE_CLE_PSEUDO"] = "cle-de-test-t12-pseudo"
if mode == "repli": env["USINE_MODE_REPLI"] = "1"
srv = subprocess.Popen([UV, "run", "--no-sync", "usine", "ui", "--port", str(PORT)], cwd=arbre, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    assert attendre(f"http://127.0.0.1:{PORT}/api/cadre")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=str(CHROMIUM), headless=True)
        pg = b.new_page()
        for u in urls:
            pg.goto(f"http://127.0.0.1:{PORT}{u}"); pg.wait_for_timeout(800)
            print("=====", u, pg.title(), pg.url)
            print(pg.inner_text("body")[:2500])
        b.close()
finally:
    subprocess.run(["taskkill", "/T", "/F", "/PID", str(srv.pid)], capture_output=True)
