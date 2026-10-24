"""T5 : demande une revue au format JSON fixe a chaque modele, pour chaque story du jeu, via OpenRouter.

Usage : uv run --no-project python revue.py [--modeles id1,id2] [--stories S1-E0-7,...] [--plafond 6.0]
Reprise : une reponse deja enregistree n'est pas redemandee. Ne jamais afficher ni ecrire la cle.
Seuls diff.patch et spec.md de depots publics sont envoyes.
"""
from __future__ import annotations

import argparse
import json
import re
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from cle import lire_cle

ICI = Path(__file__).parent
JEU = ICI / "jeu"
REPONSES = ICI / "reponses"
MODELES = ["openai/gpt-6-luna", "xiaomi/mimo-v2.6-pro", "openai/gpt-6.1-sol", "moonshotai/kimi-k3.1-pro"]
# prix par jeton (liste OpenRouter du 2026-10-24), repli si le champ usage.cost manque
PRIX = {
    "openai/gpt-6-luna": (1e-7, 5e-7), "xiaomi/mimo-v2.6-pro": (4.35e-7, 8.7e-7),
    "openai/gpt-6.1-sol": (2e-6, 1e-5), "moonshotai/kimi-k3.1-pro": (2e-6, 1e-5),
}
MAX_TOKENS = 32000
RAISONNEMENT_MAX: int | None = None  # --budget-raisonnement : plafond de jetons de raisonnement (complement)

SYSTEM = """Tu es relecteur de code senior. Tu fais une revue concise d'une story fusionnee, dans la langue du depot (francais), en lisant uniquement le diff et la spec fournis.

Consignes (inspirees de la consigne reviewer d'un pipeline de revue) :
- Cherche les vrais defauts : criteres d'acceptation non couverts, chemins d'erreur non traites, cas limites, regressions, integration (le nouveau code est-il branche la ou la story l'exige ?), securite (secrets, donnees, appels reseau inattendus), coherence avec les contraintes de la spec. Ignore le style et les preferences.
- Ne t'arrete pas au diff : raisonne sur les appelants et les points d'entree que le diff laisse voir.
- Prouve plutot que de supposer. Questionne les tests de l'implementeur : un oracle qui recalcule la valeur attendue avec la meme formule que le code ne prouve rien.
- Severite. "Important" = defaut reel, demontrable, qui aurait justifie un correctif avant fusion (comportement faux, plantage, regle de la spec violee, fuite). "Nit" = reste (robustesse mineure, lisibilite, test manquant sans defaut demontre).
- Pour chaque constat "Important", fournis un test pytest minimal et autonome qui ECHOUERAIT sur le code fusionne (il affirme le comportement correct attendu) et qui reussirait une fois le defaut corrige. Si tu ne peux pas ecrire un tel test, le constat n'est pas "Important" : classe-le "Nit". Les faux positifs coutent cher : ne signale "Important" que ce dont tu es raisonnablement sur.
- Contraintes du test : fichier unique, imports complets, tourne avec pytest sur le depot (paquet Python `usine` sous src/, aussi `evals`, `outils` a la racine) ; aucun reseau, aucun sous-processus, n'ecrit que sous la fixture `tmp_path` (jamais ailleurs), ne supprime rien hors de `tmp_path`, ne lit pas de secret ; utilise des doublures simples (monkeypatch) pour isoler. N'invente pas d'API : n'utilise que des noms visibles dans le diff ou la spec ; si tu hesites, ecris le test pour qu'il echoue sur l'assertion de comportement plutot que sur un import.
- Au plus 6 constats Important et 6 Nit. Mieux vaut 0 Important qu'un faux.

Reponds UNIQUEMENT par un objet JSON (sans Markdown, sans texte autour) de la forme :
{"constats": [{"id": "C1", "fichier": "chemin/relatif.py", "ligne": 123, "severite": "Important" | "Nit", "description": "ce qui est faux, pourquoi, avec quelle entree", "test_pytest": "source complete du fichier de test (chaine JSON), ou null pour un Nit"}]}
"""


def construire_message(story: Path) -> str:
    spec = (story / "spec.md").read_text(encoding="utf-8")
    diff = (story / "diff.patch").read_text(encoding="utf-8")
    return (
        "## Spec de la story (sections ecrites avant le developpement)\n\n" + spec
        + "\n\n## Diff fusionne de la story, correctifs de revue compris (le depot est dans l'etat apres fusion)\n\n```diff\n" + diff + "\n```\n"
    )


def slug(modele: str) -> str:
    return modele.replace("/", "__")


class Compteur:
    def __init__(self, plafond: float) -> None:
        self.plafond = plafond
        self.total = 0.0
        self.verrou = threading.Lock()
        fichier = ICI / "cout.json"
        if fichier.exists():
            self.total = json.loads(fichier.read_text(encoding="utf-8")).get("total_usd", 0.0)

    def ajouter(self, usd: float) -> None:
        with self.verrou:
            self.total += usd
            (ICI / "cout.json").write_text(json.dumps({"total_usd": round(self.total, 5)}), encoding="utf-8")

    def depasse(self) -> bool:
        return self.total >= self.plafond


def appeler(modele: str, message: str, cle: str, effort: str | None = None) -> dict:
    corps = {
        "model": modele,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": message}],
        "max_tokens": MAX_TOKENS,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "usage": {"include": True},
    }
    if RAISONNEMENT_MAX and not effort:
        corps["reasoning"] = {"max_tokens": RAISONNEMENT_MAX}
    if effort:  # seulement en reprise, apres une reponse vide par epuisement du budget de raisonnement
        corps["reasoning"] = {"effort": effort}
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=json.dumps(corps).encode("utf-8"),
        headers={"Authorization": "Bearer " + cle, "Content-Type": "application/json", "X-Title": "veille-agents-code T5"},
    )
    debut = time.time()
    with urllib.request.urlopen(req, timeout=900) as r:
        brut = json.load(r)
    brut["_latence_s"] = round(time.time() - debut, 1)
    return brut


def cout_de(modele: str, usage: dict) -> float:
    if isinstance(usage.get("cost"), (int, float)):
        return float(usage["cost"])
    p, c = PRIX[modele]
    return usage.get("prompt_tokens", 0) * p + usage.get("completion_tokens", 0) * c


def tache(modele: str, story: Path, cle: str, compteur: Compteur) -> str:
    sortie = REPONSES / f"{slug(modele)}__{story.name}.json"
    if sortie.exists():
        return f"{modele} {story.name} : deja fait"
    if compteur.depasse():
        return f"{modele} {story.name} : plafond atteint, non lance"
    message = construire_message(story)
    effort = None
    cout_total, latence_totale, tentatives = 0.0, 0.0, []
    essai = 0
    while True:
        try:
            brut = appeler(modele, message, cle, effort)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            essai += 1
            code = getattr(exc, "code", None)
            if essai >= 4 or (code is not None and 400 <= code < 500 and code != 429):
                sortie.with_suffix(".erreur.txt").write_text(f"{type(exc).__name__} {code}", encoding="utf-8")
                return f"{modele} {story.name} : ERREUR {type(exc).__name__} {code}"
            time.sleep(20 * essai)
            continue
        usage = brut.get("usage", {})
        usd = cout_de(modele, usage)
        compteur.ajouter(usd)
        cout_total += usd
        latence_totale += brut["_latence_s"]
        choix = (brut.get("choices") or [{}])[0]
        contenu = (choix.get("message") or {}).get("content") or ""
        tentatives.append({"effort": effort, "finish_reason": choix.get("finish_reason"), "jetons_sortis": usage.get("completion_tokens"), "cout_usd": usd, "latence_s": brut["_latence_s"]})
        if not contenu.strip() and choix.get("finish_reason") == "length" and effort is None:
            effort = "low"  # reprise unique a effort de raisonnement reduit
            continue
        break
    sortie.write_text(json.dumps({
        "modele": modele, "story": story.name, "latence_s": round(latence_totale, 1), "usage": usage, "cout_usd": cout_total,
        "finish_reason": choix.get("finish_reason"), "tentatives": tentatives, "contenu": contenu,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    return f"{modele} {story.name} : {cout_total:.3f} $ {latence_totale:.0f} s, {len(tentatives)} tentative(s), {usage.get('completion_tokens')} jetons sortis, total {compteur.total:.2f} $"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modeles", default=",".join(MODELES))
    ap.add_argument("--stories", default="")
    ap.add_argument("--plafond", type=float, default=6.0)
    ap.add_argument("--budget-raisonnement", type=int, default=0)
    ap.add_argument("--dossier", default="reponses")
    o = ap.parse_args()
    cle = lire_cle()
    if not cle:
        raise SystemExit("OPENROUTER_API_KEY introuvable")
    global REPONSES, RAISONNEMENT_MAX
    REPONSES = ICI / o.dossier
    RAISONNEMENT_MAX = o.budget_raisonnement or None
    REPONSES.mkdir(exist_ok=True)
    stories = [d for d in sorted(JEU.iterdir()) if d.is_dir() and (not o.stories or d.name in o.stories.split(","))]
    compteur = Compteur(o.plafond)

    modeles = o.modeles.split(",")
    verrous = {m: threading.Semaphore(2) for m in modeles}  # au plus 2 appels simultanes par modele (limites de debit)

    def une(args: tuple[str, Path]) -> None:
        modele, s = args
        with verrous[modele]:
            print(tache(modele, s, cle, compteur), flush=True)

    with ThreadPoolExecutor(max_workers=12) as ex:
        list(ex.map(une, [(m, s) for m in modeles for s in stories]))
    print(f"total {compteur.total:.3f} $")


if __name__ == "__main__":
    main()
