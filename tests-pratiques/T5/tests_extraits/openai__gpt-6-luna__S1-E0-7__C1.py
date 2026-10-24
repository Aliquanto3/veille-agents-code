from usine.ia.controles import controler_citations


def test_retire_une_phrase_citant_un_ticket_d_un_autre_projet() -> None:
    resultat = controler_citations("Voir DEMO-1 et AUTRE-2.", ["DEMO-1"])

    assert resultat.texte == ""
    assert resultat.citations == ()
    assert resultat.phrases_retirees == 1
