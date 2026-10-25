"""Prépare les projets jetables (un par condition) avec les skills copiées à la main.
Rien n'est installé au niveau utilisateur. Vérifie les SHA épinglés."""
import shutil, subprocess, sys
from pathlib import Path
from config import VENDOR, PROJETS

SHA_CLARITY = "e27ceeff60368cf6966b4ea00a5b9b36418ee9a0"


def sha(dep: Path) -> str:
    return subprocess.run(["git", "-C", str(dep), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def main():
    c, h = VENDOR / "clarity", VENDOR / "humanizer"
    assert sha(c) == SHA_CLARITY, "clarity n'est pas au commit épinglé"
    print("clarity", sha(c)); print("humanizer", sha(h))
    for nom in ("A", "B", "C", "gen", "juge"):
        (PROJETS / nom).mkdir(parents=True, exist_ok=True)
    # B : humanizer seul (sert aussi à la 2e étape de D)
    dst = PROJETS / "B" / ".claude" / "skills" / "humanizer"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(h / "SKILL.md", dst / "SKILL.md")
    # C : clarity (SKILL.md, references/, scripts/ ; pas de site, pas d'exemples)
    dst = PROJETS / "C" / ".claude" / "skills" / "clarity"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(c / "SKILL.md", dst / "SKILL.md")
    for sous in ("references", "scripts"):
        shutil.copytree(c / sous, dst / sous, dirs_exist_ok=True)
    print("projets prêts :", sorted(p.name for p in PROJETS.iterdir()))


if __name__ == "__main__":
    sys.exit(main())
