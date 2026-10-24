"""Story 6.10 : des échecs non consécutifs ne doivent jamais faire échouer la classification."""

from tests.unit.ia.test_classification import (
    FournisseurEchouantSur,
    _classer,
    _reponse,
    textes,
)


def test_echecs_non_consecutifs_toleres_quels_qu_en_soit_le_nombre() -> None:
    """Matrice I/O « Échecs non consécutifs » : seul un échec consécutif fait échouer l'étape."""
    cles = {f"DEMO-{n}": ("Titre", "Description.") for n in range(1, 81)}
    # 40 échecs du fournisseur, tous séparés d'un succès (rang pair en échec).
    factice = FournisseurEchouantSur(set(range(0, 80, 2)), [_reponse()] * 40)
    sorties, traces = _classer(factice, textes(cles))
    assert len(sorties) == 40
    assert [t.cible for t in traces] == [s.cle_ticket for s in sorties]
