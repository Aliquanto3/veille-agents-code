from usine.ia.controles import controler_citations


def test_citation_d_un_autre_projet_est_refusee():
    controle = controler_citations(
        "DEMO-1 dépend de AUTRE-99.",
        ("DEMO-1",),
    )
    assert controle.texte == ""
    assert controle.citations == ()
    assert controle.phrases_retirees == 1
    assert controle.phrases_total == 1
