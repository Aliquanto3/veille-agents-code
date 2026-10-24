"""Prépare les 8 répertoires de bras (copie de la base + skill au niveau projet + prompt)."""
import json, shutil, sys
from pathlib import Path

T7 = Path(__file__).resolve().parent.parent
BASE = T7 / "base"
VENDOR = T7 / "vendor"
ENGINE = T7 / "tools" / "impeccable-engine" / "impeccable-windows-x64.exe"
ARMS = T7 / "arms"
TACHE = (Path(__file__).parent / "tache.md").read_text(encoding="utf-8")

BRAS = {
    "b1-aucune": None,
    "b2-frontend-design": "frontend-design",
    "b3-impeccable": "impeccable",
    "b4-hallmark": "hallmark",
}
CONSIGNE = {
    "frontend-design": "Pour la conception de l'interface, charge et applique d'abord la skill `frontend-design` (outil Skill), puis construis l'écran.\n\n",
    "impeccable": "Pour la conception de l'interface, charge et applique d'abord la skill `impeccable` (outil Skill), puis construis l'écran.\n\n",
    "hallmark": "Pour la conception de l'interface, charge et applique d'abord la skill `hallmark` (outil Skill), puis construis l'écran.\n\n",
}
SRC = {
    "frontend-design": VENDOR / "skills" / "skills" / "frontend-design",
    "impeccable": VENDOR / "impeccable" / "plugin" / "skills" / "impeccable",
    "hallmark": VENDOR / "hallmark" / "skills" / "hallmark",
}

def main(reps=(1, 2)):
    ARMS.mkdir(exist_ok=True)
    for nom, skill in BRAS.items():
        for r in reps:
            d = ARMS / f"{nom}_r{r}"
            if d.exists():
                print("existe déjà, ignoré", d.name); continue
            if False:
                shutil.rmtree(d)
            d.mkdir()
            for f in ("app", "tests"):
                shutil.copytree(BASE / f, d / f, ignore=shutil.ignore_patterns("__pycache__"))
            for f in ("pyproject.toml", "uv.lock", ".gitignore"):
                shutil.copy2(BASE / f, d / f)
            if skill:
                dst = d / ".claude" / "skills" / skill
                shutil.copytree(SRC[skill], dst)
                if skill == "impeccable":
                    b = dst / "scripts" / "bin" / "windows-x64"
                    b.mkdir(parents=True)
                    shutil.copy2(ENGINE, b / "impeccable.exe")
            prompt = (CONSIGNE.get(skill, "")) + TACHE
            (d / "_prompt.txt").write_text(prompt, encoding="utf-8")
            (d / "_arm.json").write_text(json.dumps({"bras": nom, "skill": skill, "rep": r}), encoding="utf-8")
            print("prêt", d.name)

if __name__ == "__main__":
    main(tuple(int(x) for x in sys.argv[1:]) or (1, 2))
