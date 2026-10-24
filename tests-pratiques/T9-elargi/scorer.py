"""T9 elargi : demande a un bras (Jev ou un LLM) trois probabilites par story, a partir de la seule spec.

Questions (les memes pour tous les bras) : derapage du developpement (appels > 2 x mediane du depot), cout de la story
au-dessus du 80e centile du depot, defaut de revue (au moins un constat medium ou high retenu et traite).

Bras
- ``jev`` : endpoint de decisions d'OpenRouter ``POST /api/alpha/decisions`` (modele ``~typesafe/jev-latest`` ou
  ``typesafe/jev-1.13``), trois questions ``noul`` independantes dans une seule requete.
- ``llm`` : ``/api/v1/chat/completions`` avec sortie structuree (json_schema) ; modele passe en argument.

Relancable : les scores deja obtenus (meme texte de spec, meme version de prompt) ne sont pas redemandes ; seules les
nouvelles stories sont scorees (``--forcer`` pour tout refaire).

Contraintes : cle OpenRouter lue par ``cle.py`` (jamais affichee ni ecrite ; les corps d'erreur HTTP ne sont pas relayes) ;
cout lu dans ``usage.cost`` de chaque reponse et cumule dans ``budget.json`` (nombres seulement) ; arret avant le plafond
de 4 $ (``PLAFOND_USD``, 3,8 $ de marge appliquee).

Usage : uv run --no-project python scorer.py --bras jev --modele "~typesafe/jev-latest" --textes <textes.json> --out scores_jev_latest.json
        uv run --no-project python scorer.py --bras llm --modele openai/gpt-6-luna --textes <textes.json> --out scores_luna_r1.json --fils 2
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from cle import cle_openrouter

ICI = Path(__file__).resolve().parent
BUDGET_FICHIER = ICI / "budget.json"
PLAFOND_USD = 3.8  # marge sous le plafond de 4 $
URL_DECISIONS = "https://openrouter.ai/api/alpha/decisions"
URL_CHAT = "https://openrouter.ai/api/v1/chat/completions"
VERSION_PROMPT = "t9e-1"  # a changer quand les consignes changent : les anciens scores sont alors refaits
verrou = threading.Lock()

CONTEXTE = (
    "Une story logicielle est confiee a un agent de code (modele Claude, boucle d'appels d'outils). "
    "On compte les appels d'API de cet agent de developpement et on mesure son cout. La story « derape » quand l'agent "
    "fait plus de 2 fois le nombre median d'appels des stories du meme depot (mediane de 26 a 87 appels selon le depot) ; "
    "environ 1 story sur 15 derape. Le cout d'une story est « eleve » quand il depasse le 80e centile des stories du meme "
    "depot (1 story sur 5 ; de l'ordre de 1 a 5 dollars selon le depot). Apres le developpement, une revue independante "
    "lit le code ; environ 3 stories sur 4 recoivent au moins un constat de severite medium ou high que la revue "
    "juge fonde, et qui est corrige (ni rejete, ni reporte)."
)
Q1 = "Le developpement de cette story va-t-il deraper (plus de 2 fois le nombre median d'appels d'un depot) ?"
Q2 = "Le cout de developpement de cette story sera-t-il parmi les 20 % les plus eleves de son depot ?"
Q3 = "La revue trouvera-t-elle au moins un defaut de severite medium ou high, corrige, dans le code livre pour cette story ?"
CHAMPS = ("derapage", "cout80", "defaut_revue")


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
    def q(question: str, vrai: str, faux: str) -> dict:
        return {"type": "noul", "instructions": CONTEXTE + " " + question + " Reponds a partir de `story_spec` seulement.",
                "criteria": {"true": vrai, "false": faux}}
    corps = {
        "model": modele,
        "state": {"story_spec": texte},
        "questions": {
            "derapage": q(Q1, "La story demandera beaucoup plus d'appels que la normale (derapage).", "La story restera dans la plage habituelle d'appels."),
            "cout80": q(Q2, "Le cout de la story sera parmi les 20 % les plus eleves du depot.", "Le cout de la story restera dans la plage habituelle."),
            "defaut_revue": q(Q3, "La revue consignera un defaut medium ou high retenu et corrige.", "La revue ne consignera aucun defaut medium ou high retenu."),
        },
    }
    rep, dt = post(URL_DECISIONS, corps, cle)
    ans = rep.get("answers", {})
    u = rep.get("usage", {})
    return {**{f"p_{c}": ans.get(c, {}).get("noul") for c in CHAMPS},
            "cout": float(u.get("cost") or 0.0), "tokens_in": u.get("input_tokens"), "tokens_out": u.get("output_tokens"),
            "latence_s": round(dt, 3), "modele_repondu": rep.get("model")}


def _objet() -> dict:
    return {"type": "object", "additionalProperties": False,
            "properties": {"reponse": {"type": "string", "enum": ["oui", "non"]}, "probabilite_oui": {"type": "number"}},
            "required": ["reponse", "probabilite_oui"]}


SCHEMA = {
    "name": "pronostic_story",
    "strict": True,
    "schema": {"type": "object", "additionalProperties": False, "properties": {c: _objet() for c in CHAMPS}, "required": list(CHAMPS)},
}


def appel_llm(modele: str, texte: str, cle: str, max_tokens: int) -> dict:
    consigne = (CONTEXTE + "\n\nTu vois la seule spec de la story (avant tout developpement). Reponds a trois questions fermees, "
                "chacune par oui ou non et une probabilite que la reponse soit oui (entre 0 et 1).\n"
                f"1. derapage : {Q1}\n2. cout80 : {Q2}\n3. defaut_revue : {Q3}")
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
        p = {f"p_{c}": float(j[c]["probabilite_oui"]) for c in CHAMPS}
    except (ValueError, KeyError, TypeError):
        p = {f"p_{c}": None for c in CHAMPS}
    det = u.get("completion_tokens_details") or {}
    return {**p, "cout": float(u.get("cost") or 0.0), "tokens_in": u.get("prompt_tokens"), "tokens_out": u.get("completion_tokens"),
            "tokens_raisonnement": det.get("reasoning_tokens"), "latence_s": round(dt, 3), "modele_repondu": rep.get("model"),
            "fin": (rep.get("choices") or [{}])[0].get("finish_reason")}


def empreinte(texte: str) -> str:
    return hashlib.sha1(texte.encode("utf-8")).hexdigest()[:12]


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
    ap.add_argument("--forcer", action="store_true", help="refaire tous les scores meme deja obtenus")
    o = ap.parse_args()

    cle = cle_openrouter()
    textes = json.loads(o.textes.read_text(encoding="utf-8"))
    cles = sorted(textes)
    if o.limite:
        cles = cles[: o.limite]
    deja = {}
    if o.out.exists() and not o.forcer:
        ancien = json.loads(o.out.read_text(encoding="utf-8"))
        if ancien.get("version_prompt") == VERSION_PROMPT:
            deja = ancien.get("scores", {})
    a_faire = [k for k in cles if k not in deja or deja[k].get("p_derapage") is None or deja[k].get("sha") != empreinte(textes[k])]
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
        r["sha"] = empreinte(textes[k])
        budget_ajouter(r["cout"], nom_bras)
        return k, r

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=o.fils) as ex:
        for k, r in ex.map(un, a_faire):
            if r is not None:
                deja[k] = r
    sortie = {"bras": o.bras, "modele": o.modele, "version_prompt": VERSION_PROMPT, "n": len(deja), "duree_s": round(time.time() - t0),
              "cout_usd": round(sum(v.get("cout", 0.0) for v in deja.values()), 6), "scores": deja}
    o.out.write_text(json.dumps(sortie, ensure_ascii=False, indent=0), encoding="utf-8")
    ok = sum(1 for v in deja.values() if v.get("p_derapage") is not None)
    print(f"{nom_bras} : {ok}/{len(cles)} scores ({len(a_faire)} demandes), cout {sortie['cout_usd']:.4f} $, cumul budget {budget_lire():.4f} $, arret_budget={arret.is_set()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
