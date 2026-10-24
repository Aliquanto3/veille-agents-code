from datetime import date

from usine.contrats.llm import SortieExplication, StatutControle
from usine.ui.detail import texte_explication
from usine.ui.liens import lien_ticket


def test_citation_d_une_explication_rejetee_reste_un_lien() -> None:
    url = "https://jira.example/browse/DEMO-1"
    sortie = SortieExplication(
        date_arrete=date(2026, 10, 9),
        entite="ENT-A",
        texte="Remplacement pour DEMO-1.",
        citations=("DEMO-1",),
        brouillon_commentaire="",
        phrases_retirees=0,
        statut_controle=StatutControle.rejete,
    )

    texte = texte_explication(2, (sortie,), lambda cle: url if cle == "DEMO-1" else None)

    assert lien_ticket("DEMO-1", url) in texte