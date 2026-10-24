from usine.ia.controles import controler_citations


def test_retire_une_phrase_citant_aussi_un_ticket_non_autorise() -> None:
    resultat = controler_citations(
        "Le ticket DEMO-1 est ouvert avec AUTRE-2.", {"DEMO-1"}
    )

    assert resultat.texte == ""
    assert resultat.phrases_retirees == 1
