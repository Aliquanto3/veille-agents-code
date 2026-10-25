r"""T5 elargi : extrait les constats de toutes les reponses (Claude et GPT) vers T:\constats.json, format unifie.

Constat : {relecteur, story, n, fichier, lignes:[a,b], refs:[[fichier,a,b],...], severite, etiquette, important, description}
Regle « important » (grille.md) : GPT = severite Important ; Opus = etiquette Important ; Haiku = severite high ou medium.
usage : extraire.py [--sortie T:/constats.json]
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

T = Path("T:/")
SUF = os.environ.get("T5E_SUF", "")  # "_r2" : seconde passe GPT seule
RE_REF = re.compile(r"([\w./\\-]+\.py)\s*(?:[:#(]\s*(?:l\.?\s*|L)?(\d+)(?:\s*[-–]\s*(?:L)?(\d+))?|\s+l(?:ignes?)?\.?\s*(\d+)(?:\s*[-–]\s*(\d+))?)")
SEV = re.compile(r"\b(high|medium|low)\b", re.I)
ETQ = re.compile(r"\b(Important|Nit|Pre-existing)\b", re.I)


def refs_de(texte: str) -> list[list]:
    out = []
    for m in RE_REF.finditer(texte):
        f = m.group(1).replace("\\", "/").lstrip("./")
        a = int(m.group(2) or m.group(4))
        b = int(m.group(3) or m.group(5) or a)
        out.append([f, min(a, b), max(a, b)])
    return out


def claude(agent: str, sid: str, texte: str) -> list[dict]:
    blocs: list[str] = []
    for ligne in texte.splitlines():
        if not ligne.strip():
            continue
        entete = "|".join(ligne.split("|")[:4])
        debut_constat = bool(refs_de(entete)) and ligne.count("|") >= 2
        if debut_constat:
            blocs.append(ligne.strip())
        elif blocs and ligne.startswith((" ", "\t", "-", "*")) and not ETQ.match(ligne.strip().lstrip("-* ")):
            blocs[-1] += " " + ligne.strip()
    constats = []
    for n, b in enumerate(blocs, 1):
        champs = [c.strip() for c in b.lstrip("-*0123456789.) ").split("|")]
        entete = " | ".join(champs[:3])
        e = ETQ.search(entete)
        s = SEV.search(entete)
        etiquette = e.group(1).capitalize() if e else None
        sev = s.group(1).lower() if s else None
        refs = refs_de(" | ".join(champs[:3])) or refs_de(b)
        if not refs:
            continue
        if agent == "opus":
            important = etiquette == "Important"
        else:
            important = sev in ("high", "medium")
        constats.append(dict(relecteur=agent, story=sid, n=n, fichier=refs[0][0], lignes=[refs[0][1], refs[0][2]], refs=refs,
                             severite=sev, etiquette=etiquette, important=important, description=b))
    return constats


def gpt(modele: str, sid: str, contenu: str) -> list[dict]:
    try:
        data = json.loads(contenu)
        objets = data.get("constats", [])
    except json.JSONDecodeError:
        objets = []
        for m in re.finditer(r'\{\s*"id"\s*:.*?"test_pytest"\s*:\s*(?:null|"(?:[^"\\]|\\.)*")\s*\}', contenu, re.S):
            try:
                objets.append(json.loads(m.group(0)))
            except json.JSONDecodeError:
                pass
    out = []
    for n, o in enumerate(objets, 1):
        f = str(o.get("fichier", "")).replace("\\", "/").lstrip("./")
        try:
            a = int(o.get("ligne") or 0)
        except (TypeError, ValueError):
            a = 0
        sev = str(o.get("severite", ""))
        out.append(dict(relecteur=modele, story=sid, n=n, fichier=f, lignes=[a, a], refs=[[f, a, a]], severite=sev,
                        etiquette=sev, important=sev.lower() == "important", description=str(o.get("description", "")),
                        test_pytest=bool(o.get("test_pytest"))))
    return out


def tout() -> list[dict]:
    res = []
    for agent in (() if SUF else ("haiku", "opus")):
        for f in sorted((T / "rep" / agent).glob("*.json")):
            d = json.loads(f.read_text(encoding="utf-8"))
            res += claude(agent, f.stem, d.get("result", ""))
    for f in sorted((T / ("rep_gpt" + SUF)).glob("*.json")) if (T / ("rep_gpt" + SUF)).exists() else []:
        d = json.loads(f.read_text(encoding="utf-8"))
        modele = f.stem.rsplit("__", 1)[0].replace("__", "/")
        sid = f.stem.rsplit("__", 1)[1]
        res += gpt(modele, sid, d.get("contenu", ""))
    return res


if __name__ == "__main__":
    c = tout()
    sortie = Path(sys.argv[sys.argv.index("--sortie") + 1]) if "--sortie" in sys.argv else T / f"constats{SUF}.json"
    sortie.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print(len(c), "constats", Counter((x["relecteur"], x["important"]) for x in c))
