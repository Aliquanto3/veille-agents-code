"""Rejoue l'oracle FINAL (verite.py, figé) sur chaque version (défauts + témoins) : champ oracle_final.
Usage : T12_STORIES=storiesv uv run --no-project python rejouer_oracle.py [ID...]"""
import json, sys
from commun import *
import semer
from verite_run import verite

SORTIE = ICI / "donnees" / "oracle_final.jsonl"
MODE = {"s713": "repli", "s714": "repli", "s715": "reel", "s716": "repli"}

def un(ident):
    temoin = ident.startswith("t")
    sid = "s" + ident[1:] if temoin else semer.DEFAUTS[ident]["story"]
    if not temoin: semer.appliquer(ident)
    try:
        res, axe = verite(semer.arbre(sid), sid, MODE[sid], PORT)
    finally:
        semer.retirer(sid)
    ko = sorted(k for k, (ok, _) in res.items() if not ok)
    with SORTIE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"id": ident, "story": sid, "ko": ko, "checks": res, "axe": axe}, ensure_ascii=False) + "\n")
    print(ident, "KO:", ko, flush=True)

if __name__ == "__main__":
    ids = sys.argv[1:] or [f"t{n}" for n in (713, 714, 715, 716)] + list(semer.DEFAUTS)
    for i in ids: un(i)
