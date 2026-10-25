"""Renfort Story 7.16 : rendu de la fiche outillage (titre, pastilles, code en ligne)."""

from usine.ui.outillage import rendre_fiche


def test_titre_h1_absent_et_sections_conservees() -> None:
    html = rendre_fiche("# Titre\n\n## Section\n\ntexte\n")
    assert "Titre" not in html
    assert "</h1>" not in html
    assert "<h1>" not in html
    assert html.count('<section class="carte carte--fiche">') == 1
    assert "<h2>Section</h2>" in html


def test_titre_h1_en_milieu_de_fiche_saute_trois_jetons() -> None:
    html = rendre_fiche("## A\n\n# Titre\n\npara\n")
    assert "</h1>" not in html
    assert "Titre" not in html
    assert "<p>para</p>" in html


def test_code_en_ligne_garde_son_marqueur() -> None:
    html = rendre_fiche("## S\n\n`✅` et ✅\n")
    assert "<code>✅</code>" in html
    assert html.count("pastille--oui") == 1


def test_jetons_apres_un_code_en_ligne_sont_gardes() -> None:
    html = rendre_fiche("## S\n\navant `code` apres ❌ fin\n")
    assert "apres" in html
    assert "fin" in html
    assert "pastille--non" in html
