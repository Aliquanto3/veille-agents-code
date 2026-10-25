"""T10 : applique un survivant cible (extrait des diffs de T4) sur un fichier, par remplacement de ligne."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

EXC = 'type("CR", (Exception,), {})'   # remplace CosmicRayTestingException (classe sans instance)


def muter(texte_brut: bytes, ligne: int, moins: list[str], plus: list[str]) -> bytes:
    crlf = b"\r\n" in texte_brut
    lignes = texte_brut.decode("utf-8").split("\n")
    mn = [m for m in moins if m.strip()]
    candidats = [i for i in range(max(0, ligne - 4), min(len(lignes), ligne + 3))
                 if lignes[i].rstrip("\r").strip() == mn[0].strip()]
    if not candidats:
        raise ValueError(f"ligne {ligne} introuvable : {mn[0].strip()!r}")
    i = min(candidats, key=lambda j: abs(j - (ligne - 1)))
    for j, m in enumerate(mn):
        if lignes[i + j].rstrip("\r").strip() != m.strip():
            raise ValueError(f"ligne {ligne} : suite differente a {j}")
    nouv = [p.replace("CosmicRayTestingException", EXC) + ("\r" if crlf else "") for p in plus]
    lignes[i:i + len(mn)] = nouv
    return "\n".join(lignes).encode("utf-8")


@contextmanager
def applique(chemin: Path, cible: dict):
    brut = chemin.read_bytes()
    nouveau = muter(brut, cible["ligne"], cible["moins"], cible["plus"])
    try:
        chemin.write_bytes(nouveau)
        yield
    finally:
        chemin.write_bytes(brut)
