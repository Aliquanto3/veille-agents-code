"""Réduit les flux bruts (retire les images en base64 des résultats d'outils) puis anonymise les chemins locaux.
Usage : uv run --no-project python compacter.py"""
import glob, json, re, sys
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI.parent / "banc-rejeu"))
from anonymiser import anonymiser


def nettoyer(o):
    if isinstance(o, dict):
        if o.get("type") == "image" and isinstance(o.get("source"), dict) and "data" in o["source"]:
            o = dict(o); o["source"] = {"type": "base64", "data": "<image retirée>", "media_type": o["source"].get("media_type")}
            return o
        return {k: nettoyer(v) for k, v in o.items()}
    if isinstance(o, list):
        return [nettoyer(x) for x in o]
    return o


def main():
    for f in glob.glob(str(ICI / "donnees" / "**" / "*.jsonl"), recursive=True):
        p = Path(f)
        if p.name not in ("flux.jsonl",) and not p.name.endswith(".flux.jsonl"):
            continue
        lignes = []
        for l in p.read_text(encoding="utf-8").splitlines():
            try:
                lignes.append(json.dumps(nettoyer(json.loads(l)), ensure_ascii=False))
            except ValueError:
                lignes.append(l)
        p.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    n = 0
    for f in glob.glob(str(ICI / "donnees" / "**" / "*"), recursive=True):
        p = Path(f)
        if p.is_file() and p.suffix in (".json", ".jsonl", ".log", ".md", ".txt", ".py", ".diff"):
            n += anonymiser(p)
    print("remplacements de chemins :", n)


if __name__ == "__main__":
    main()
