r"""T5 elargi : teste si un mutant ecrit a la main survit aux tests de la story (applique, lance les tests cibles, restaure).
usage : essai_mutant.py <id> <module> <ligne> "<ancien>" "<nouveau>"   -> affiche SURVIT ou TUE (et la derniere ligne de pytest)"""
import subprocess
import sys
from pathlib import Path

from lancer_tests import commande

sid, module, ligne, ancien, nouveau = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
arbre = Path("T:/src") / sid
fichier = arbre / module
brut = fichier.read_bytes()
texte = brut.decode("utf-8").split("\n")
cible = texte[ligne - 1]
if cible.strip() != ancien.strip():
    sys.exit(f"ligne {ligne} differente : {cible.strip()!r}")
indent = cible[: len(cible) - len(cible.lstrip())]
texte[ligne - 1] = indent + nouveau.strip()
try:
    fichier.write_bytes("\n".join(texte).encode("utf-8"))
    cmd, cwd, env = commande(sid)
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    fin = (p.stdout.strip().splitlines() or [""])[-1]
    print(("SURVIT" if p.returncode == 0 else "TUE"), "|", fin[:150])
finally:
    fichier.write_bytes(brut)
