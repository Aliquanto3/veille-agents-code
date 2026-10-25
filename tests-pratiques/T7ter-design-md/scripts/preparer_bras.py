"""Prépare les répertoires de bras : base de l'écran + skill au niveau projet (+ DESIGN.md pour b5) + prompt.

Usage : uv run --no-project python scripts/preparer_bras.py            (les 12)
"""
import json, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from chemins import ARMS, BASES, BRAS, DEPOT, ECRANS, ESSAIS, SKILL_SRC, TACHES, nom

CONSIGNE_SKILL = "Pour la conception de l'interface, charge et applique d'abord la skill `frontend-design` (outil Skill), puis construis l'écran.\n\n"
CONSIGNE_DESIGN = "Applique aussi les règles de `DESIGN.md` à la racine du projet ; en cas de conflit avec la skill, elles l'emportent.\n\n"


def main():
    ARMS.mkdir(parents=True, exist_ok=True)
    for bras in BRAS:
        for ecran in ECRANS:
            for r in ESSAIS:
                d = ARMS / nom(bras, ecran, r)
                if d.exists():
                    print("existe déjà, ignoré", d.name); continue
                d.mkdir()
                base = BASES[ecran]
                for f in ("app", "tests"):
                    shutil.copytree(base / f, d / f, ignore=shutil.ignore_patterns("__pycache__"))
                for f in ("pyproject.toml", "uv.lock", ".gitignore"):
                    shutil.copy2(base / f, d / f)
                shutil.copytree(SKILL_SRC, d / ".claude" / "skills" / "frontend-design")
                consigne = CONSIGNE_SKILL
                if bras == "b5":
                    shutil.copy2(DEPOT / "DESIGN.md", d / "DESIGN.md")
                    consigne += CONSIGNE_DESIGN
                prompt = consigne + TACHES[ecran].read_text(encoding="utf-8")
                (d / "_prompt.txt").write_text(prompt, encoding="utf-8")
                (d / "_arm.json").write_text(json.dumps({"bras": bras, "ecran": ecran, "essai": r}), encoding="utf-8")
                print("prêt", d.name)


if __name__ == "__main__":
    main()
