from tests.unit.ia.test_classification import FournisseurEchouantSur, _classer, _reponse, textes


def test_erreurs_isolees_non_consecutives_ne_font_pas_echouer_le_passage() -> None:
    cles = {f"DEMO-{n}": ("Titre", "Description.") for n in range(1, 41)}
    fournisseur = FournisseurEchouantSur(set(range(0, 40, 2)), [_reponse()] * 20)

    sorties, _ = _classer(fournisseur, textes(cles))

    assert len(sorties) == 20