"""Renforcement de la Story 7.16 : rendu de la fiche outillage."""

from usine.ui.outillage import rendre_fiche


def test_titre_h1_retire_et_reste_rendu() -> None:
    html = rendre_fiche("# Titre unique\n\nintro\n\n## Section\n\ntexte")
    assert "Titre unique" not in html
    assert "h1" not in html
    assert "<p>intro</p>" in html
    assert "<h2>Section</h2>" in html


def test_premier_jeton_non_titre_est_conserve() -> None:
    assert rendre_fiche("texte seul") == (
        '<section class="carte carte--fiche"><p>texte seul</p>\n</section>'
    )


def test_pastille_suivie_d_autres_jetons_en_ligne() -> None:
    html = rendre_fiche("**gras** ✅ puis *italique* ❌ fin")
    assert '<span class="pastille pastille--oui">Oui</span>' in html
    assert '<span class="pastille pastille--non">Non</span>' in html
    assert "<strong>gras</strong>" in html
    assert "<em>italique</em>" in html
    assert html.endswith(" fin</p>\n</section>")


def test_marqueur_dans_un_code_en_ligne_reste_du_code() -> None:
    html = rendre_fiche("avant `✅` après")
    assert "<code>✅</code>" in html
    assert "pastille" not in html
