"""X1 : fait écrire UNE fois un brouillon de post LinkedIn par Opus (effort medium), puis le fige.
X2 : extrait le « Résumé exécutif » du rapport de recherche (copie exacte)."""
import json, re, sys
from pathlib import Path
from config import T11, PROJETS
from lancer_claude import lancer

REPO = T11.parent.parent
RECH = next((REPO / "recherche").glob("technical-outils-*/research.md"))


def x2():
    txt = RECH.read_text(encoding="utf-8")
    m = re.search(r"^## Résumé exécutif\n(.*?)(?=^## 1\. )", txt, re.S | re.M)
    out = T11 / "textes" / "X2"
    out.mkdir(parents=True, exist_ok=True)
    (out / "source.md").write_text(m.group(1).strip() + "\n", encoding="utf-8")
    (out / "lecteur.txt").write_text("un responsable technique qui décide de la configuration de son équipe\n", encoding="utf-8")


def x1():
    out = T11 / "textes" / "X1"
    if (out / "source.md").exists():
        print("X1 déjà figé"); return
    bilan = json.loads((REPO / "synthese" / "bilan.json").read_text(encoding="utf-8"))
    essentiel = "\n".join("- " + re.sub(r"<[^>]+>", "", x) for x in bilan["essentiel"])
    txt = RECH.read_text(encoding="utf-8")
    m = re.search(r"^## 7 bis\..*?(?=^## 8\. )", txt, re.S | re.M)
    prompt = (
        "Écris un brouillon de post LinkedIn en français, de 200 à 300 mots, sur les conclusions de la veille "
        "décrite ci-dessous. Rends seulement le post.\n\n"
        "=== L'essentiel (synthèse) ===\n" + essentiel + "\n\n"
        "=== Résultats des tests pratiques (section 7 bis du rapport) ===\n" + m.group(0)
    )
    (out / "prompt_generation.txt").write_text(prompt, encoding="utf-8")
    texte, meta, brut = lancer(PROJETS / "gen", prompt, model="opus", tools="", budget=1.5)
    (out / "source.md").write_text(texte.strip() + "\n", encoding="utf-8")
    (out / "lecteur.txt").write_text("tes contacts LinkedIn, consultants et développeurs\n", encoding="utf-8")
    (out / "generation.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: meta.get(k) for k in ("cout_usd", "tours", "duree_s", "modeles")}, ensure_ascii=False))


if __name__ == "__main__":
    x2(); x1()
