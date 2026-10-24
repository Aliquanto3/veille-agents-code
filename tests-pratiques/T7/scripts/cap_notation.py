from playwright.sync_api import sync_playwright
url = "file:///C:/Users/Utilisateur/Documents/GitHub/veille-agents-code/tests-pratiques/T7/notation.html"
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 1000})
    pg.goto(url); pg.wait_for_timeout(500)
    pg.screenshot(path=r"C:\Users\UTILIS~1\AppData\Local\Temp\claude\C--Users-Utilisateur-Documents-GitHub\791fed94-a8b0-414e-8a6c-8fe967283749\scratchpad\t7\notation_cap.png")
    b.close()
