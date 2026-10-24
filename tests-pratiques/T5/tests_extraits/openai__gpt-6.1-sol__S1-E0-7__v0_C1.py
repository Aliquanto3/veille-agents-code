from usine.ia.controles import controler_citations


def test_retire_phrase_citant_un_ticket_d_un_autre_projet():
    resultat = controler_citations(
        'DEMO-1 dépend du ticket AUTRE-2.',
        ('DEMO-1',),
    )
    assert resultat.texte == ''
    assert resultat.citations == ()
    assert resultat.phrases_retirees == 1
    assert resultat.phrases_total == 1
