"""Numérote les citations d'un brouillon de rapport et construit l'annexe des sources.

Usage : uv run --no-project python -I scripts/numeroter_citations.py <dossier_du_run>

Lit <dossier>/research.draft.md, où une citation s'écrit {dimension:REF} (plusieurs : {dimension:REF1,REF2}),
avec dimension = nom d'un digest (digests/<dimension>-r1.md), `verif` (verifications/lot-*.md)
ou `doc` (page de code.claude.com/docs/en/<chemin>).
Écrit <dossier>/research.md : chaque citation devient [n] (ordre de première apparition) et l'annexe
« Sources » est ajoutée à la place du marqueur <!-- ANNEXE -->. Les références introuvables sont listées.
"""

import re
import sys
from pathlib import Path

MOTIF_CITATION = re.compile(r"\{([a-z0-9-]+):([^{}]+)\}")
MOTIF_URL = re.compile(r"https?://[^\s|)>\]`]+")
ALIAS = {
    "litt": "litterature",
    "prat": "praticiens",
    "orch": "orchestration-ux",
    "contexte": "contexte-memoire",
    "couts": "couts-tokens",
    "routage": "routage-local",
    "revue": "revue-securite",
    "tests": "tests-verification",
    "design": "design-front",
    "tour2": "tour2-trous",
}


def lignes_tableau(texte: str) -> list[list[str]]:
    lignes = []
    for ligne in texte.splitlines():
        if not ligne.startswith("|") or re.match(r"^\|\s*-", ligne):
            continue
        lignes.append([c.strip() for c in ligne.strip().strip("|").split("|")])
    return lignes


def charger_affirmations(dossier: Path) -> dict[tuple[str, str], dict]:
    table: dict[tuple[str, str], dict] = {}
    for digest in sorted((dossier / "digests").glob("*-r1.md")):
        dimension = digest.name.removesuffix("-r1.md")
        texte = digest.read_text(encoding="utf-8")
        section = texte.split("## 4.", 1)[-1].split("## 5.", 1)[0] if "## 4." in texte else ""
        for cellules in lignes_tableau(section):
            if len(cellules) < 7 or cellules[0].lower() == "ref":
                continue
            ref = cellules[0].strip("[]` ")
            url = MOTIF_URL.search(cellules[2])
            table[(dimension, ref)] = {
                "affirmation": cellules[1],
                "url": url.group(0) if url else None,
                "source": cellules[2],
                "editeur": cellules[3],
                "date": cellules[4],
                "consultee": cellules[5],
                "confiance": cellules[6],
            }
    for lot in sorted((dossier / "verifications").glob("lot-*.md")):
        for cellules in lignes_tableau(lot.read_text(encoding="utf-8")):
            if len(cellules) < 5 or cellules[0] == "id":
                continue
            urls = MOTIF_URL.findall(" ".join(cellules[2:4]))
            table[("verif", cellules[0])] = {
                "affirmation": f"Vérification {cellules[0]} : {cellules[1]}",
                "url": urls[0] if urls else None,
                "source": lot.name,
                "editeur": "vérification du run",
                "date": "—",
                "consultee": "2026-10-24",
                "confiance": cellules[1],
            }
    return table


def main() -> None:
    dossier = Path(sys.argv[1])
    brouillon = (dossier / "research.draft.md").read_text(encoding="utf-8")
    affirmations = charger_affirmations(dossier)
    numeros: dict[tuple[str, str], int] = {}
    introuvables: list[str] = []

    def numero(dimension: str, ref: str) -> int:
        cle = (dimension, ref)
        if cle not in numeros:
            numeros[cle] = len(numeros) + 1
            if dimension != "doc" and cle not in affirmations:
                introuvables.append(f"{dimension}:{ref}")
        return numeros[cle]

    def remplacer(m: re.Match) -> str:
        nom = m.group(1) or ""
        dimension = ALIAS.get(nom, nom)
        refs = [r.strip() for r in m.group(2).split(",") if r.strip()]
        return "".join(f"[{numero(dimension, r)}]" for r in refs)

    texte = MOTIF_CITATION.sub(remplacer, brouillon)
    lignes = [
        "| n | affirmation ou constat appuyé | éditeur (lien) | date de publication | consultée | confiance | trace |",
        "|---|---|---|---|---|---|---|",
    ]
    for (dimension, ref), n in sorted(numeros.items(), key=lambda e: e[1]):
        if dimension == "doc":
            url = f"https://code.claude.com/docs/en/{ref}"
            lignes.append(f"| {n} | Documentation officielle Claude Code : `{ref}` | [Anthropic]({url}) | page vivante | 2026-10-24 | haute | digests/natif-anthropic-r1.md |")
            continue
        a = affirmations.get((dimension, ref))
        if a is None:
            lignes.append(f"| {n} | (référence introuvable : {dimension}:{ref}) | — | — | — | — | — |")
            continue
        editeur = a["editeur"].replace("|", "/")
        lien = f"[{editeur}]({a['url']})" if a["url"] else f"{editeur} ({a['source'][:80]})"
        affirmation = a["affirmation"].replace("|", "/")
        trace = f"verifications ({ref})" if dimension == "verif" else f"digests/{dimension}-r1.md ({ref})"
        lignes.append(f"| {n} | {affirmation} | {lien} | {a['date']} | {a['consultee']} | {a['confiance']} | {trace} |")
    texte = texte.replace("<!-- ANNEXE -->", "\n".join(lignes))
    (dossier / "research.md").write_text(texte, encoding="utf-8")
    print(f"{len(numeros)} sources numérotées ; introuvables : {introuvables or 'aucune'}", file=sys.stderr)


if __name__ == "__main__":
    main()
