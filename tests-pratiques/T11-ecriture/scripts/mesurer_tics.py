"""Tics de surface en français, déterministes. Aucun appel à un modèle.

Pour chaque sortie : tirets, « pas X mais Y » et variantes, chutes en une ligne, triades, mots gonflés,
gras décoratif, emojis ou flèches, longueur ; plus un contrôle mécanique des chiffres et des renvois [n]
contre la source (écarts à faire confirmer par le juge).

Usage : uv run python mesurer_tics.py [X1 X2 ...]   -> donnees/tics.json
"""
import json, re, sys
from pathlib import Path
from config import T11, CONDITIONS, ESSAIS, langue, lire_source

CADRATINS = re.compile(r"[—–]|(?<=\s)--(?=\s)")

# « ce n'est pas X, c'est Y » et variantes (le français a les mêmes formes que l'anglais)
CONTRASTES = [
    ("ce n'est pas X, c'est Y", re.compile(r"\bce n['’]est (?:pas|plus)\b[^.!?\n]{0,90}?[,;:]?\s+(?:c['’]est|mais)\b", re.I)),
    ("ce n'est pas X mais Y (sans virgule)", re.compile(r"\bn['’]est pas\b[^.!?\n]{0,60}\bmais\b", re.I)),
    ("il ne s'agit pas de X mais de Y", re.compile(r"\bil ne s['’]agit (?:pas|plus)\b", re.I)),
    ("non pas X mais Y", re.compile(r"\bnon pas\b", re.I)),
    ("pas seulement / pas uniquement X mais Y", re.compile(r"\bpas (?:seulement|uniquement|simplement|juste)\b[^.!?\n]{0,80}\bmais\b|\bne (?:se limite|se résume) pas\b", re.I)),
    ("ne pas X mais Y", re.compile(r"\bne\s+\w+(?:\s+\w+)?\s+(?:pas|plus)\b[^.!?\n]{0,60}[,;]\s*mais\b", re.I)),
    ("X, pas Y", re.compile(r"\b\w+, (?:pas|non) (?:de |d['’]|un |une |des |le |la |les )?\w+", re.I)),
    ("cela ne veut pas dire X. Cela veut dire Y", re.compile(r"\b(?:cela|ça|ceci) ne (?:veut|signifie) pas\b[^.!?\n]*[.!?]\s+(?:cela|ça|ceci|il faut|c['’]est)\b", re.I)),
    ("la question n'est pas X", re.compile(r"\b(?:la question|le problème|l['’]enjeu|le sujet) n['’]est (?:pas|plus)\b", re.I)),
]
PLUTOT = re.compile(r"\bplutôt que\b|\bau lieu de\b", re.I)  # compté à part : tournure courante et légitime

# (étiquette, motif). Les motifs en « \w* » prennent toute la famille du mot.
GONFLES_RX = [(g, re.compile(r"(?<!\w)" + m, re.I)) for g, m in [
    ("crucial", r"cruci\w*"), ("essentiel", r"essentiel\w*"), ("véritable", r"véritabl\w*"),
    ("incontournable", r"incontournabl\w*"), ("levier", r"levier\w*"), ("clé", r"cl[ée]s?(?!\w)"),
    ("révolution", r"révolution\w*"), ("paysage", r"paysage\w*"), ("majeur", r"majeur\w*"),
    ("fondamental", r"fondamental\w*|fondamentaux"), ("capital", r"capital(?:e|es|aux)?(?!\w)"),
    ("stratégique", r"stratégi\w*"), ("puissant", r"puissan\w*"), ("remarquable", r"remarquabl\w*"),
    ("inédit", r"inédit\w*"), ("pivot", r"pivot\w*"), ("au cœur", r"au c(?:œ|oe)ur"),
    ("écosystème", r"écosystèm\w*"), ("à l'ère", r"à l['’]ère"), ("plonger", r"plong(?:er|eons|ez|e)(?!\w)"),
    ("décupler", r"décupl\w*"), ("tisser", r"tiss(?:er|e|ent)(?!\w)"), ("précieux", r"précieu\w*"),
    ("indispensable", r"indispensabl\w*"), ("déterminant", r"déterminan\w*"), ("décisif", r"décisi\w*"),
    ("profond", r"profond\w*"), ("transformateur", r"transformateur\w*"),
    ("sans précédent", r"sans précédent"), ("il est important/essentiel", r"il est (?:important|essentiel|crucial)"),
    ("force est de", r"force est de"), ("pas anodin", r"n['’]est pas anodin"),
    ("la vraie / le vrai / la véritable", r"(?:la vraie|le vrai) (?:découverte|enjeu|question|problème|gain|leçon)"),
]]

ITEM = r"[^\s,.;:()\[\]!?«»]+(?: [^\s,.;:()\[\]!?«»]+){0,3}"
TRIADE = re.compile(rf"(?<![\w»]){ITEM}, {ITEM},? (?:et|ou) {ITEM}", re.I)
GRAS = re.compile(r"\*\*[^*\n]+\*\*|__[^_\n]+__")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿←-⇿⬀-⯿✅✨]")
SENT_END = re.compile(r"(?<=[.!?…])\s+(?=[A-ZÀ-ÖÙ-Ý«\"“(\[*#])")
MOT = re.compile(r"[\wÀ-ÿ'’-]+")
NB_RX = re.compile(r"(?<![\w.,])\d+(?:[  .,]\d+)*(?![\w])")
REF_RX = re.compile(r"\[\d+\](?:\[\d+\])*")



from tics_en import CONTRASTES_EN, PLUTOT_EN, GONFLES_EN, TRIADE_EN


def texte_brut(md: str) -> str:
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", md)
    t = re.sub(r"`([^`]*)`", r"\1", t)
    t = GRAS.sub(lambda m: m.group()[2:-2], t)
    t = re.sub(r"^\s{0,3}#{1,6}\s+", "", t, flags=re.M)
    return t


def paragraphes(md: str):
    return [p.strip() for p in re.split(r"\n\s*\n", md) if p.strip()]


def phrases(texte: str):
    out = []
    for p in paragraphes(texte):
        for l in p.split("\n"):
            l = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s+", "", l).strip()
            if l:
                out.extend(s.strip() for s in SENT_END.split(l) if s.strip())
    return out


def est_titre_ou_puce(p: str) -> bool:
    return bool(re.match(r"^\s*(?:#{1,6}\s|[-*•]\s|\d+[.)]\s|\|)", p))


def chutes(md: str):
    """Paragraphe d'une seule phrase courte (<= 10 mots), hors titre, puce, hashtags, 1er et dernier paragraphes,
    et suite d'au moins 3 phrases de 5 mots ou moins."""
    ps = paragraphes(md)
    res = []
    for i, p in enumerate(ps):
        if i == 0 or i == len(ps) - 1 or est_titre_ou_puce(p) or p.startswith("#") or "\n" in p:
            continue
        n = len(MOT.findall(p))
        if n <= 10 and len(SENT_END.split(p)) == 1 and not p.endswith(("?", ":")):
            res.append(p[:80])
    fragments = 0
    for p in ps:
        court = [len(MOT.findall(s)) <= 5 for s in SENT_END.split(p.replace("\n", " "))]
        run = 0
        for c in court:
            run = run + 1 if c else 0
            if run == 3:
                fragments += 1
    return res, fragments


def norm_nb(s: str) -> str:
    s = re.sub(r"[  ]", "", s)
    return s.replace(",", ".").strip(".")


def chiffres(md: str):
    t = texte_brut(md)
    t = REF_RX.sub(" ", t)
    return [norm_nb(x) for x in NB_RX.findall(t)]


def renvois(md: str):
    return re.findall(r"\[(\d+)\]", md)


def mesurer(md: str, source: str, lang: str = "fr") -> dict:
    en = lang == "en"
    brut = texte_brut(md)
    sp = phrases(brut)
    mots = MOT.findall(brut)
    contrastes = []
    for nom, rx in (CONTRASTES_EN if en else CONTRASTES):
        for m in rx.finditer(brut):
            contrastes.append((nom, m.group()[:90]))
    # « X, pas Y » est très bruyant : on le compte à part
    contr_fortes = [c for c in contrastes if c[0] != "X, pas Y"]
    gonfles = []
    for g, rx in (GONFLES_EN if en else GONFLES_RX):
        gonfles += [(g, m.group()) for m in rx.finditer(brut)]
    triades = [m.group() for m in (TRIADE_EN if en else TRIADE).finditer(brut)]
    triades_fin = [t for t in triades if re.search(re.escape(t) + r"\s*(?:[.!?]|$)", brut, re.M)]
    ch, frag = chutes(md)
    nb_s, nb_o = chiffres(source), chiffres(md)
    manquants = [x for x in set(nb_s) if x not in nb_o]
    ajoutes = [x for x in set(nb_o) if x not in nb_s]
    rs, ro = renvois(source), renvois(md)
    return {
        "mots": len(mots), "phrases": len(sp),
        "mots_par_phrase": round(len(mots) / max(1, len(sp)), 1),
        "paragraphes": len(paragraphes(md)),
        "tirets": len(CADRATINS.findall(md)),
        "contrastes": len(contr_fortes), "contrastes_xpasy": len(contrastes) - len(contr_fortes),
        "plutot_que": len((PLUTOT_EN if en else PLUTOT).findall(brut)),
        "chutes_une_ligne": len(ch), "suites_fragments": frag,
        "triades": len(triades), "triades_fin_phrase": len(triades_fin),
        "gonfles": len(gonfles),
        "gras": len(GRAS.findall(md)), "emojis_fleches": len(EMOJI.findall(md)),
        "puces": len(re.findall(r"^\s*(?:[-*•])\s", md, re.M)),
        "titres": len(re.findall(r"^\s{0,3}#{1,6}\s", md, re.M)),
        "liens": len(re.findall(r"\[[^\]]+\]\([^)]+\)", md)),
        "hashtags": len(re.findall(r"(?<!\w)#\w+", md)) if not re.search(r"^#{1,6}\s", md, re.M) else 0,
        "renvois": len(ro), "renvois_source": len(rs),
        "renvois_manquants": sorted(set(rs) - set(ro), key=int), "renvois_ajoutes": sorted(set(ro) - set(rs), key=int),
        "chiffres_manquants": sorted(manquants), "chiffres_ajoutes": sorted(ajoutes),
        "voix": marques_voix(md),
        "detail": {"contrastes": contrastes, "chutes": ch, "triades": triades, "gonfles": gonfles},
    }


def main():
    textes = sys.argv[1:] or ["X1", "X2"]
    f = T11 / "donnees" / "tics.json"
    res = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    for tid in textes:
        src = lire_source(tid)
        lg = langue(tid)
        res[tid] = {"source": mesurer(src, src, lg)}
        for c in CONDITIONS:
            for e in ESSAIS:
                p = T11 / "sorties" / tid / f"{c}-{e}.md"
                if p.exists():
                    res[tid][f"{c}-{e}"] = mesurer(p.read_text(encoding="utf-8"), src, lg)
    f.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    cols = ["mots", "mots_par_phrase", "tirets", "contrastes", "chutes_une_ligne", "triades", "triades_fin_phrase", "gonfles", "gras"]
    for tid, d in res.items():
        print(tid)
        print("  ", "cond".ljust(8), *[c[:10].rjust(10) for c in cols])
        for k, v in d.items():
            print("  ", k.ljust(8), *[str(v[c]).rjust(10) for c in cols])


def marques_voix(md: str) -> dict:
    """Marques de voix (utile surtout pour X3) : emojis, interjections en capitales, questions, exclamations,
    points de suspension, parenthèses, première et deuxième personnes."""
    return {
        "emojis": "".join(EMOJI.findall(md)),
        "n_emojis": len(EMOJI.findall(md)),
        "interjections_capitales": re.findall(r"\b[A-ZÉÈ]{4,}\b(?!\s*[:(])", md)[:10],
        "questions": md.count("?"), "exclamations": md.count("!"),
        "points_suspension": md.count("...") + md.count("…"),
        "parentheses": md.count("("),
        "je": len(re.findall(r"\b(?:je|j['’]|m['’]|mon|ma|mes|moi)\b", md, re.I)),
        "vous": len(re.findall(r"\b(?:vous|votre|vos)\b", md, re.I)),
    }


if __name__ == "__main__":
    main()
