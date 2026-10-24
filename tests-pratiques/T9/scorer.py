"""T9 : demande a un bras (Jev ou un LLM) la probabilite de derapage de chaque story, a partir de la seule spec.

Bras
- ``jev`` : endpoint de decisions d'OpenRouter ``POST /api/alpha/decisions`` (modele ``~typesafe/jev-latest``
  ou ``typesafe/jev-1.13``), deux questions ``noul`` independantes (derapage, defaut de revue).
- ``llm`` : ``/api/v1/chat/completions`` avec sortie structuree (json_schema) ; modele passe en argument.

Contraintes : cle OpenRouter lue par ``cle.py`` (jamais affichee ni ecrite) ; cout lu dans ``usage.cost`` de chaque
reponse et cumule dans un fichier de budget partage ; arret avant le plafond ; appels sequentiels ou 3 fils.

Usage : uv run --no-project python scorer.py --bras jev --modele "~typesafe/jev-latest" --textes <textes.json> --out scores_jev_latest.json
        uv run --no-project python scorer.py --bras llm --modele openai/gpt-6-luna --textes <textes.json> --out scores_luna.json [--limite 3] [--fils 3]
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from cle import cle_openrouter

BUDGET_FICHIER = Path(__file__).with_name("budget.json")  # cumul des couts (nombres seulement)
PLAFOND_USD = 2.8  # marge sous les 3 $ autorises
URL_DECISIONS = "https://openrouter.ai/api/alpha/decisions"
URL_CHAT = "https://openrouter.ai/api/v1/chat/completions"
verrou = threading.Lock()

CONTEXTE = (
    "Une story logicielle est confiee a un agent de code (modele Claude Sonnet, boucle d'appels d'outils). "
    "On compte les appels d'API de cet agent de developpement. La story « derape » quand l'agent fait plus de "
    "2 fois le nombre median d'appels des stories du meme depot (de l'ordre de 100 a 180 appels, contre 35 a 90 "
    "pour une story typique) ; environ 1 story sur 14 derape. Apres le developpement, une revue independante "
    "lit le code ; environ 3 stories sur 4 recoivent au moins un constat de severite medium ou high que la revue "
    "juge fonde (non rejete)."
)
Q1 = "Le developpement de cette story va-t-il deraper (plus de 2 fois le nombre median d'appels d'un depot) ?"
Q2 = "La revue trouvera-t-elle au moins un defaut de severite medium ou high dans le code livre pour cette story ?"


def budget_lire() -> float:
    try:
        return float(json.loads(BUDGET_FICHIER.read_text(encoding="utf-8")).get("cumul_usd", 0.0))
    except (OSError, ValueError):
        return 0.0


def budget_ajouter(cout: float, bras: str) -> float:
    with verrou:
        d = {"cumul_usd": 0.0, "par_bras": {}}
        try:
            d = json.loads(BUDGET_FICHIER.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        d["cumul_usd"] = round(d.get("cumul_usd", 0.0) + cout, 8)
        d["par_bras"][bras] = round(d["par_bras"].get(bras, 0.0) + cout, 8)
        BUDGET_FICHIER.write_text(json.dumps(d, indent=1), encoding="utf-8")
        return d["cumul_usd"]


def post(url: str, corps: dict, cle: str, essais: int = 6, delai: int = 180) -> tuple[dict, float]:
    donnees = json.dumps(corps).encode("utf-8")
    for essai in range(essais):
        r = urllib.request.Request(url, data=donnees, method="POST",
                                   headers={"Authorization": "Bearer " + cle, "Content-Type": "application/json"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(r, timeout=delai) as x:
                return json.loads(x.read()), time.time() - t0
        except urllib.error.HTTPError as e:
            code = e.code
            if code in (408, 429, 500, 502, 503, 504) and essai < essais - 1:
                time.sleep(8 * (essai + 1))
                continue
            raise RuntimeError(f"HTTP {code}") from None  # le corps n'est pas relaye (pas de contenu de spec ni de cle)
        except (urllib.error.URLError, TimeoutError):
            if essai < essais - 1:
                time.sleep(8 * (essai + 1))
                continue
            raise RuntimeError("reseau") from None
    raise RuntimeError("echec")


def appel_jev(modele: str, texte: str, cle: str) -> dict:
    corps = {
        "model": modele,
        "state": {"story_spec": texte},
        "questions": {
            "derapage": {"type": "noul", "instructions": CONTEXTE + " " + Q1 + " Reponds a partir de `story_spec` seulement.",
                         "criteria": {"true": "La story demandera beaucoup plus d'appels que la normale (derapage).",
                                      "false": "La story restera dans la plage habituelle d'appels."}},
            "defaut_revue": {"type": "noul", "instructions": CONTEXTE + " " + Q2 + " Reponds a partir de `story_spec` seulement.",
                             "criteria": {"true": "La revue consignera un defaut medium ou high retenu.",
                                          "false": "La revue ne consignera aucun defaut medium ou high retenu."}},
        },
    }
    rep, dt = post(URL_DECISIONS, corps, cle)
    ans = rep.get("answers", {})
    u = rep.get("usage", {})
    return {"p_derapage": ans.get("derapage", {}).get("noul"), "p_defaut_revue": ans.get("defaut_revue", {}).get("noul"),
            "cout": float(u.get("cost") or 0.0), "tokens_in": u.get("input_tokens"), "tokens_out": u.get("output_tokens"),
            "latence_s": round(dt, 3), "modele_repondu": rep.get("model")}


SCHEMA = {
    "name": "pronostic_story",
    "strict": True,
    "schema": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "derapage": {"type": "object", "additionalProperties": False,
                         "properties": {"reponse": {"type": "string", "enum": ["oui", "non"]}, "probabilite_oui": {"type": "number"}},
                         "required": ["reponse", "probabilite_oui"]},
            "defaut_revue": {"type": "object", "additionalProperties": False,
                             "properties": {"reponse": {"type": "string", "enum": ["oui", "non"]}, "probabilite_oui": {"type": "number"}},
                             "required": ["reponse", "probabilite_oui"]},
        },
        "required": ["derapage", "defaut_revue"],
    },
}


def appel_llm(modele: str, texte: str, cle: str, max_tokens: int) -> dict:
    consigne = (CONTEXTE + "\n\nTu vois la seule spec de la story (avant tout developpement). Reponds a deux questions fermees, "
                "chacune par oui ou non et une probabilite que la reponse soit oui (entre 0 et 1).\n"
                f"1. derapage : {Q1}\n2. defaut_revue : {Q2}")
    corps = {
        "model": modele, "max_tokens": max_tokens,
        "messages": [{"role": "system", "content": consigne}, {"role": "user", "content": "Spec de la story :\n\n" + texte}],
        "response_format": {"type": "json_schema", "json_schema": SCHEMA},
        "reasoning": {"effort": "low"},
    }
    rep, dt = post(URL_CHAT, corps, cle)
    u = rep.get("usage", {})
    contenu = (rep.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    try:
        j = json.loads(contenu)
        p1 = float(j["derapage"]["probabilite_oui"])
        p2 = float(j["defaut_revue"]["probabilite_oui"])
        r1, r2 = j["derapage"]["reponse"], j["defaut_revue"]["reponse"]
    except (ValueError, KeyError, TypeError):
        p1 = p2 = r1 = r2 = None
    det = u.get("completion_tokens_details") or {}
    return {"p_derapage": p1, "p_defaut_revue": p2, "reponse_derapage": r1, "reponse_defaut_revue": r2,
            "cout": float(u.get("cost") or 0.0), "tokens_in": u.get("prompt_tokens"), "tokens_out": u.get("completion_tokens"),
            "tokens_raisonnement": det.get("reasoning_tokens"), "latence_s": round(dt, 3), "modele_repondu": rep.get("model"),
            "fin": (rep.get("choices") or [{}])[0].get("finish_reason")}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bras", choices=["jev", "llm"], required=True)
    ap.add_argument("--modele", required=True)
    ap.add_argument("--textes", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--fils", type=int, default=1)
    ap.add_argument("--max-tokens", type=int, default=3000)
    o = ap.parse_args()

    cle = cle_openrouter()
    textes = json.loads(o.textes.read_text(encoding="utf-8"))
    cles = sorted(textes)
    if o.limite:
        cles = cles[: o.limite]
    deja = {}
    if o.out.exists():
        deja = json.loads(o.out.read_text(encoding="utf-8")).get("scores", {})
    a_faire = [k for k in cles if k not in deja or deja[k].get("p_derapage") is None]
    nom_bras = f"{o.bras}:{o.modele}"
    arret = threading.Event()

    def un(k: str):
        if arret.is_set():
            return k, None
        if budget_lire() >= PLAFOND_USD:
            arret.set()
            return k, None
        try:
            r = appel_jev(o.modele, textes[k], cle) if o.bras == "jev" else appel_llm(o.modele, textes[k], cle, o.max_tokens)
        except RuntimeError as e:
            return k, {"erreur": str(e), "p_derapage": None}
        budget_ajouter(r["cout"], nom_bras)
        return k, r

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=o.fils) as ex:
        for k, r in ex.map(un, a_faire):
            if r is not None:
                deja[k] = r
    sortie = {"bras": o.bras, "modele": o.modele, "n": len(deja), "duree_s": round(time.time() - t0),
              "cout_usd": round(sum(v.get("cout", 0.0) for v in deja.values()), 6), "scores": deja}
    o.out.write_text(json.dumps(sortie, ensure_ascii=False, indent=0), encoding="utf-8")
    ok = sum(1 for v in deja.values() if v.get("p_derapage") is not None)
    print(f"{nom_bras} : {ok}/{len(cles)} scores, cout {sortie['cout_usd']:.4f} $, cumul budget {budget_lire():.4f} $, arret_budget={arret.is_set()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
