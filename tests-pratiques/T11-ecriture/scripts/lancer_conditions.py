"""Joue les conditions A, B, C, D sur les textes donnés (par défaut X1 et X2), 2 essais chacune.
Ne rejoue pas une sortie déjà présente. 2 sessions `claude -p` au plus en même temps.
D = sortie de C (même essai) passée dans humanizer (projet B).
Usage : uv run python lancer_conditions.py [X1 X2 ...]"""
import json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from config import T11, PROJETS, CONSIGNE, SKILL_PHRASE, CONSIGNE_EN, SKILL_PHRASE_EN, LECTEURS, ESSAIS, langue, lire_source
from lancer_claude import lancer


def lecteur(tid):
    f = T11 / "textes" / tid / "lecteur.txt"
    return f.read_text(encoding="utf-8").strip() if f.exists() else LECTEURS[tid]


def prompt(cond_skill, tid, source):
    if langue(tid) == "en":
        return (CONSIGNE_EN.format(lecteur=lecteur(tid)) + " " + SKILL_PHRASE_EN[cond_skill]).strip() + \
            "\n\nText to rewrite:\n<<<\n" + source.strip() + "\n>>>\n"
    return (CONSIGNE.format(lecteur=lecteur(tid)) + " " + SKILL_PHRASE[cond_skill]).strip() + \
        "\n\nTexte à réécrire :\n<<<\n" + source.strip() + "\n>>>\n"


def jouer(cond, essai, tid, source, projet):
    """cond : A, B, C ou D (D utilise le projet B et la phrase de B)."""
    out = T11 / "sorties" / tid
    out.mkdir(parents=True, exist_ok=True)
    f = out / f"{cond}-{essai}.md"
    if f.exists():
        return f.read_text(encoding="utf-8")
    p = prompt("B" if cond == "D" else cond, tid, source)
    texte, meta, brut = lancer(PROJETS / projet, p)
    meta["prompt_debut"] = p[:260]
    f.write_text(texte.strip() + "\n", encoding="utf-8")
    (out / f"{cond}-{essai}.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / f"{cond}-{essai}.flux.jsonl").write_text(brut, encoding="utf-8")
    print(tid, cond, essai, "cout", meta.get("cout_usd"), "tours", meta.get("tours"),
          "skills", meta.get("skills_invoquees"), flush=True)
    return texte.strip()


def chaine_c(tid, source, essai):
    c = jouer("C", essai, tid, source, "C")
    jouer("D", essai, tid, c, "B")


def main():
    textes = sys.argv[1:] or ["X1", "X2"]
    taches = []
    with ThreadPoolExecutor(max_workers=2) as ex:
        for tid in textes:
            src = lire_source(tid)
            for e in ESSAIS:
                taches.append(ex.submit(jouer, "A", e, tid, src, "A"))
                taches.append(ex.submit(jouer, "B", e, tid, src, "B"))
                taches.append(ex.submit(chaine_c, tid, src, e))
        for t in taches:
            t.result()


if __name__ == "__main__":
    main()
