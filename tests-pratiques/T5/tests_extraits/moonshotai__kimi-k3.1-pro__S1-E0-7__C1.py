from usine.ia.controles import controler_citations


def test_une_cle_hors_cause_dun_autre_projet_fait_retirer_la_phrase() -> None:
    controle = controler_citations(
        "DEMO-1 et ABC-2 sont cités.",
        ("DEMO-1",),
    )

    assert controle.texte == ""
    assert controle.citations == ()
    assert controle.phrases_retirees == 1
