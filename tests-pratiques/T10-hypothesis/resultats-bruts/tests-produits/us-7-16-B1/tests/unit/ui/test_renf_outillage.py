"""Renfort Story 7.16 : `ui/outillage.py` (lecture et rendu de la fiche)."""

from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from usine.ui import outillage
from usine.ui.outillage import (
    FICHE_ABSENTE,
    FICHIER_FICHE,
    LEGENDE,
    PASTILLES,
    lire_fiche,
    rendre_fiche,
)

SECTION = '<section class="carte carte--fiche">'


def _pastille(variante: str, libelle: str) -> str:
    return f'<span class="pastille pastille--{variante}">{libelle}</span>'


# --- lire_fiche ---


def test_lire_fiche_absente(tmp_path: Path) -> None:
    assert lire_fiche(tmp_path) is None


def test_lire_fiche_utf8_et_bom(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    chemin = tmp_path / FICHIER_FICHE
    chemin.write_bytes("﻿# Fiche é✅\n".encode())
    assert lire_fiche(tmp_path) == "# Fiche é✅\n"
    chemin.write_bytes(b"")
    assert lire_fiche(tmp_path) == ""


def test_lire_fiche_octets_invalides_remontent(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / FICHIER_FICHE).write_bytes(b"\xff\xfe\xfa invalide")
    with pytest.raises(UnicodeDecodeError):
        lire_fiche(tmp_path)


def test_lire_fiche_repertoire_remonte_oserror(tmp_path: Path) -> None:
    (tmp_path / FICHIER_FICHE).mkdir(parents=True)
    with pytest.raises(OSError):  # noqa: PT011
        lire_fiche(tmp_path)


def test_messages_citent_le_fichier() -> None:
    assert FICHIER_FICHE.as_posix() == "docs/fiche-outillage.md"
    assert "`docs/fiche-outillage.md`" in FICHE_ABSENTE
    assert "`docs/fiche-outillage.md`" in LEGENDE


# --- rendre_fiche ---


def test_pastilles_table() -> None:
    assert PASTILLES == {
        "✅": ("oui", "Oui"),
        "⚠": ("surveiller", "À surveiller"),
        "❌": ("non", "Non"),
    }


@pytest.mark.parametrize(
    ("marqueur", "variante", "libelle"),
    [
        ("✅", "oui", "Oui"),
        ("⚠", "surveiller", "À surveiller"),
        ("⚠️", "surveiller", "À surveiller"),  # avec sélecteur de variante
        ("❌", "non", "Non"),
    ],
)
def test_pastille_remplace_le_marqueur(marqueur: str, variante: str, libelle: str) -> None:
    html = rendre_fiche(f"## S\n\navant {marqueur} après\n")
    assert f"<p>avant {_pastille(variante, libelle)} après</p>" in html
    assert marqueur not in html


def test_pastilles_multiples_et_collees() -> None:
    html = rendre_fiche("## S\n\n✅❌⚠\n")
    assert f"<p>{_pastille('oui', 'Oui')}{_pastille('non', 'Non')}" in html
    assert html.count('class="pastille ') == 3
    assert _pastille("surveiller", "À surveiller") in html


def test_pastille_dans_cellule_de_tableau() -> None:
    fiche = "## S\n\n| Outil | Dispo |\n|---|---|\n| A | ✅ |\n| B | ❌ |\n"
    html = rendre_fiche(fiche)
    assert f"<td>{_pastille('oui', 'Oui')}</td>" in html
    assert f"<td>{_pastille('non', 'Non')}</td>" in html


def test_pastille_dans_code_en_ligne_non_remplacee() -> None:
    html = rendre_fiche("## S\n\n`✅` texte\n")
    assert "<code>✅</code>" in html
    assert "pastille" not in html


def test_tableau_defilant_enveloppe() -> None:
    html = rendre_fiche("## S\n\n| a | b |\n|---|---|\n| 1 | 2 |\n")
    ouverture = (
        '<div class="table-defile" role="region" tabindex="0"'
        ' aria-label="Tableau de la fiche, défilant"><table>'
    )
    assert html.count(ouverture) == 1
    assert html.count("</table></div>") == 1
    assert html.index(ouverture) < html.index("</table></div>")


def test_titre_h1_non_rendu_mais_h2_et_h3_gardes() -> None:
    html = rendre_fiche("# Titre unique\n\n## Deux\n\n### Trois\n\ntexte\n")
    assert "Titre unique" not in html
    assert "<h1" not in html
    assert "<h2>Deux</h2>" in html
    assert "<h3>Trois</h3>" in html


def test_sections_en_cartes() -> None:
    html = rendre_fiche("# T\n\nintro\n\n## A\n\na\n\n## B\n\nb\n")
    assert html == (
        f"{SECTION}<p>intro</p>\n</section>"
        f"{SECTION}<h2>A</h2>\n<p>a</p>\n</section>"
        f"{SECTION}<h2>B</h2>\n<p>b</p>\n</section>"
    )


def test_sans_intro_pas_de_carte_vide() -> None:
    html = rendre_fiche("# T\n\n## A\n\na\n")
    assert html.count(SECTION) == 1
    assert html.startswith(f"{SECTION}<h2>A</h2>")


def test_fiche_vide_ou_titre_seul() -> None:
    assert rendre_fiche("") == ""
    assert rendre_fiche("# Seulement un titre\n") == ""


def test_html_brut_echappe() -> None:
    fiche = (
        "## S\n\n<script>alert(1)</script>\n\n"
        '<img src=x onerror="alert(1)">\n\n'
        "texte <b>gras</b> et [lien](javascript:alert(1))\n"
    )
    html = rendre_fiche(fiche)
    assert "<script" not in html
    assert "<img" not in html
    assert "<b>" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;img" in html
    assert "&lt;b&gt;gras&lt;/b&gt;" in html
    assert 'href="javascript:' not in html


def test_lien_http_conserve() -> None:
    html = rendre_fiche("## S\n\n[x](https://example.invalid/a)\n")
    assert '<a href="https://example.invalid/a">x</a>' in html


@given(st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=200))
def test_propriete_aucune_balise_script_ou_pastille_parasite(texte: str) -> None:
    html = rendre_fiche(texte)
    assert "<script" not in html.lower().replace("&lt;script", "")
    # les seuls <span> du rendu sont les pastilles du serveur
    assert html.count("<span") == html.count('<span class="pastille pastille--')


@given(
    st.lists(
        st.sampled_from(["✅", "⚠", "⚠️", "❌"]) | st.text(alphabet="abc ", max_size=3),
        max_size=12,
    )
)
def test_propriete_un_marqueur_une_pastille(morceaux: list[str]) -> None:
    ligne = "x" + "".join(morceaux) + "x"
    html = rendre_fiche(f"## S\n\n{ligne}\n")
    attendu = sum(m in ("✅", "⚠", "⚠️", "❌") for m in morceaux)
    assert html.count('<span class="pastille ') == attendu
    for marqueur in ("✅", "⚠", "❌"):
        assert marqueur not in html


def test_constantes_publiques() -> None:
    assert outillage.LIBELLE_TABLEAU == "Tableau de la fiche, défilant"
