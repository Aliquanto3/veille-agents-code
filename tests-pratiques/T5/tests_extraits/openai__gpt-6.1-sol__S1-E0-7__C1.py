from usine.ia.controles import controler_citations


def test_citation_non_autorisee_d_un_autre_projet_retire_la_phrase():
    resultat = controler_citations(
        "DEMO-1 dépend de AUTRE-2.",
        ["DEMO-1"],
    )

    assert resultat.texte == ""
    assert resultat.citations == ()
    assert resultat.phrases_retirees == 1
    assert resultat.phrases_total == 1
