"""Portes dures : un juge `claude -p --model opus` (effort medium), aveugle à la condition, compare chaque
sortie à la source. Un appel par sortie, sans outils, prompt système court. 2 appels au plus en parallèle.

Usage : uv run python juge.py [X1 X2 ...]    -> juge/<texte>/<cond>-<essai>.json (n'écrase rien)
"""
import json, re, sys
from concurrent.futures import ThreadPoolExecutor
from config import T11, PROJETS, CONDITIONS, ESSAIS, LECTEURS, langue, lire_source
from lancer_claude import lancer

SYSTEME = ("Tu es un relecteur de fidélité, strict et factuel. Tu compares une réécriture à son texte source "
           "et tu ne juges que la fidélité, jamais le style. Tu réponds uniquement par un objet JSON valide.")

CONSIGNE_JUGE = """Compare la VERSION RÉÉCRITE au TEXTE SOURCE. La consigne donnée au réécrivain était : rendre le texte plus clair et plus naturel pour le lecteur « {lecteur} », sans inventer aucun fait, sans renforcer aucune affirmation, en gardant les chiffres et les renvois.

Cherche, un par un, les écarts de ces types (et seulement ceux-là) :
- fait_invente : information absente de la source (fait, chiffre, nom, durée, expérience vécue, cause, exemple, attribution).
- affirmation_renforcee : portée, modalité ou degré de certitude modifiés (peut devient va, quelques devient la plupart, mesuré devient prouvé, un auteur devient un fait établi, une nuance ou une réserve supprimée).
- chiffre_ou_renvoi_perdu_ou_modifie : un chiffre, une unité, une comparaison ou un renvoi du type [12] de la source manque, change ou se retrouve rattaché à une autre phrase.
- sens_change : le sens d'une phrase ou d'un enchaînement logique est différent (cause inversée, condition perdue, périmètre déplacé).
- structure_ou_lien_abime : titres, listes, liens, hashtags, appel à l'action final, ordre des idées essentiel ou question finale supprimés ou cassés. Le simple retrait du gras ou d'une puce décorative n'est PAS un écart de ce type : note-le dans "mise_en_forme".
{extra_x3}
Pour chaque écart, donne la citation exacte de la version réécrite et celle de la source (vide si l'élément a disparu ou n'existait pas), et une gravité : "porte" si l'écart franchit la porte dure (un lecteur pourrait être induit en erreur ou l'auteur ne reconnaîtrait pas son propos), "mineur" si c'est une reformulation sans conséquence factuelle. Ne signale pas les reformulations légitimes. Ne reproche pas à la réécriture ce qui est déjà dans la source (même si c'est faux).

Réponds par un seul objet JSON, sans texte autour :
{{"ecarts":[{{"type":"...","gravite":"porte|mineur","citation_sortie":"...","citation_source":"...","explication":"une phrase"}}],"porte_franchie":true|false,"mise_en_forme":"une phrase sur le gras, les puces, les titres modifiés","phrase_de_bilan":"une phrase"}}
"porte_franchie" vaut true si au moins un écart a la gravité "porte".

=== TEXTE SOURCE ===
{source}

=== VERSION RÉÉCRITE ===
{sortie}
"""

EXTRA_X3 = """- voix_effacee (texte d'un auteur réel, X3 uniquement) : la réécriture efface la voix ou les marques de l'auteur (emojis, interjections comme « WOUPS », questions au lecteur, ton personnel, anecdotes) au point de changer qui parle. Donne dans "marques_disparues" la liste de ce qui a disparu, même si l'écart est mineur.
"""


def juger(tid, cond, essai):
    f = T11 / "juge" / tid / f"{cond}-{essai}.json"
    if f.exists() or not (T11 / "sorties" / tid / f"{cond}-{essai}.md").exists():
        return
    f.parent.mkdir(parents=True, exist_ok=True)
    source = lire_source(tid)
    sortie = (T11 / "sorties" / tid / f"{cond}-{essai}.md").read_text(encoding="utf-8")
    lecteur_f = T11 / "textes" / tid / "lecteur.txt"
    lecteur = lecteur_f.read_text(encoding="utf-8").strip() if lecteur_f.exists() else LECTEURS[tid]
    p = CONSIGNE_JUGE.format(lecteur=lecteur, source=source.strip(), sortie=sortie.strip(),
                             extra_x3=EXTRA_X3 if tid == "X3" else "")
    if langue(tid) == "en":
        p = "(Les deux textes sont en anglais ; réponds en français pour les explications.)\n" + p
    texte, meta, _ = lancer(PROJETS / "juge", p, model="opus", tools="", budget=1.0,
                            extra=("--system-prompt", SYSTEME))
    m = re.search(r"\{.*\}", texte, re.S)
    try:
        verdict = json.loads(m.group(0))
    except Exception as e:
        verdict = {"erreur_parse": str(e), "brut": texte[:3000]}
    f.write_text(json.dumps({"verdict": verdict, "meta": meta}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(tid, cond, essai, verdict.get("porte_franchie"), len(verdict.get("ecarts", [])), meta.get("cout_usd"), flush=True)


def main():
    textes = sys.argv[1:] or ["X1", "X2"]
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(juger, t, c, e) for t in textes for c in CONDITIONS for e in ESSAIS]
        for x in futs:
            x.result()


if __name__ == "__main__":
    main()
