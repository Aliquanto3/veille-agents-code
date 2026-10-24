"""T8 élargi : fait juger les 600 commandes de out/jeu.json par un juge donné et sauve out/<nom>.json.
Usage : uv run --no-project python -I lancer_juge.py regle|tev1|haiku|openrouter [limite]
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from juges import juge_regle, juge_tev1, juge_haiku, juge_openrouter

NOM = sys.argv[1]
LIMITE = int(sys.argv[2]) if len(sys.argv) > 2 else None
SORTIE = f"out/{NOM}.json"

jeu = json.load(open("out/jeu.json", encoding="utf-8"))
if LIMITE:
    jeu = jeu[:LIMITE]

if NOM == "regle":
    fn = lambda c: juge_regle(c)
elif NOM == "tev1":
    for c in [x["cmd"] for x in jeu[:3]]:
        juge_tev1(c)  # préchauffe
    fn = lambda c: juge_tev1(c)
elif NOM == "haiku":
    fn = lambda c: juge_haiku(c)
elif NOM == "openrouter":
    cle = os.environ.get("OPENROUTER_API_KEY")
    if not cle:
        print("OPENROUTER_API_KEY absente de l'environnement du process ; relancer avec la variable posée.")
        sys.exit(1)
    fn = lambda c: juge_openrouter(c, cle)
else:
    print("juge inconnu :", NOM); sys.exit(1)

res = []
cout_usd = 0.0
for i, x in enumerate(jeu):
    try:
        verdict, dt, extra = fn(x["cmd"])
    except Exception as e:
        verdict, dt, extra = "ask", None, f"ERREUR:{e}"  # échec de l'appel -> position prudente, jamais allow
    res.append({"cmd": x["cmd"], "attendu": x["attendu"], "categorie": x["categorie"], "outil": x["outil"],
                "predit": verdict, "latence_s": dt,
                "extra": (extra if NOM in ("regle",) else (extra.get("cost") if isinstance(extra, dict) else None))})
    if NOM == "openrouter" and isinstance(extra, dict) and "cost" in extra:
        cout_usd += extra["cost"]
        if cout_usd > 1.0:
            print(f"ARRET : plafond de 1 $ dépassé après {i+1} commandes ({cout_usd:.4f} $).")
            break
    if (i + 1) % 50 == 0:
        print(NOM, i + 1, "/", len(jeu))

json.dump(res, open(SORTIE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
ok = sum(r["attendu"] == r["predit"] for r in res)
print(NOM, "termine :", len(res), "jugees,", ok, "exactes", (f"; cout {cout_usd:.4f} $" if NOM == "openrouter" else ""))
