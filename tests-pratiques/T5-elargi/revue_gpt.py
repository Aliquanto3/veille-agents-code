r"""T5 elargi : revue par openai/gpt-6-luna et openai/gpt-6.1-sol via OpenRouter, avec le prompt de T5 (T5/revue.py, inchange).

usage : revue_gpt.py [--modeles id1,id2] [--stories a,b] [--dossier rep_gpt] [--plafond 3.0]
Le relecteur ne voit que la spec et le diff seme (pas de depot). Reprise automatique : une reponse deja ecrite n'est pas redemandee.
La cle est lue par cle.py (T5), jamais affichee ni ecrite. Cout lu dans usage.cost.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import threading
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "T5"))
spec = importlib.util.spec_from_file_location("t5revue", ICI.parent / "T5" / "revue.py")
t5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t5)  # SYSTEM, appeler, cout_de, slug

T = Path("T:/")
MODELES = ["openai/gpt-6-luna", "openai/gpt-6.1-sol"]
COUT = ICI / "cout_gpt.json"


def message(sid: str) -> str:
    sp = (T / "jeu" / sid / "spec.md").read_text(encoding="utf-8")
    diff = (T / "sem" / sid / "diff.patch").read_text(encoding="utf-8")
    return ("## Spec de la story (sections ecrites avant le developpement)\n\n" + sp
            + "\n\n## Diff fusionne de la story, correctifs de revue compris (le depot est dans l'etat apres fusion)\n\n```diff\n" + diff + "\n```\n")


class Compteur:
    def __init__(self, plafond: float) -> None:
        self.plafond, self.verrou = plafond, threading.Lock()
        self.total = json.loads(COUT.read_text())["total_usd"] if COUT.exists() else 0.0

    def ajouter(self, usd: float) -> None:
        with self.verrou:
            self.total += usd
            COUT.write_text(json.dumps({"total_usd": round(self.total, 5)}))


def tache(modele: str, sid: str, cle: str, dossier: Path, compteur: Compteur) -> str:
    sortie = dossier / f"{t5.slug(modele)}__{sid}.json"
    if sortie.exists():
        return f"{modele} {sid} : deja fait"
    if compteur.total >= compteur.plafond:
        return f"{modele} {sid} : plafond atteint"
    msg = message(sid)
    effort, cout_total, lat_totale, tentatives, essai = None, 0.0, 0.0, [], 0
    while True:
        try:
            brut = t5.appeler(modele, msg, cle, effort)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            essai += 1
            code = getattr(exc, "code", None)
            if essai >= 4 or (code is not None and 400 <= code < 500 and code != 429):
                sortie.with_suffix(".erreur.txt").write_text(f"{type(exc).__name__} {code}", encoding="utf-8")
                return f"{modele} {sid} : ERREUR {type(exc).__name__} {code}"
            time.sleep(20 * essai)
            continue
        usage = brut.get("usage", {})
        usd = t5.cout_de(modele, usage)
        compteur.ajouter(usd)
        cout_total += usd
        lat_totale += brut["_latence_s"]
        choix = (brut.get("choices") or [{}])[0]
        contenu = (choix.get("message") or {}).get("content") or ""
        tentatives.append({"effort": effort, "finish_reason": choix.get("finish_reason"), "jetons_sortis": usage.get("completion_tokens"),
                           "cout_usd": usd, "latence_s": brut["_latence_s"]})
        if not contenu.strip() and choix.get("finish_reason") == "length" and effort is None:
            effort = "low"
            continue
        break
    sortie.write_text(json.dumps({"modele": modele, "story": sid, "latence_s": round(lat_totale, 1), "usage": usage, "cout_usd": cout_total,
                                  "finish_reason": choix.get("finish_reason"), "tentatives": tentatives, "contenu": contenu},
                                 ensure_ascii=False, indent=1), encoding="utf-8")
    return f"{modele} {sid} : {cout_total:.3f} $ {lat_totale:.0f} s, total {compteur.total:.2f} $"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modeles", default=",".join(MODELES))
    ap.add_argument("--stories", default="")
    ap.add_argument("--dossier", default="rep_gpt")
    ap.add_argument("--plafond", type=float, default=3.0)
    o = ap.parse_args()
    cle = t5_cle()
    if not cle:
        raise SystemExit("OPENROUTER_API_KEY introuvable")
    dossier = T / o.dossier
    dossier.mkdir(exist_ok=True)
    ids = [s for s in o.stories.split(",") if s] or sorted(d.name for d in (T / "sem").iterdir() if (d / "verite.json").exists())
    compteur = Compteur(o.plafond)
    verrous = {m: threading.Semaphore(2) for m in o.modeles.split(",")}

    def une(a):
        m, s = a
        with verrous[m]:
            print(tache(m, s, cle, dossier, compteur), flush=True)

    with ThreadPoolExecutor(max_workers=6) as ex:
        list(ex.map(une, [(m, s) for m in o.modeles.split(",") for s in ids]))
    print(f"total {compteur.total:.3f} $")


def t5_cle() -> str:
    from cle import lire_cle
    return lire_cle()


if __name__ == "__main__":
    main()
