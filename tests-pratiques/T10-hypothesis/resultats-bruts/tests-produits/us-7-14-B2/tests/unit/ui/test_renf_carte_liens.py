"""Renfort Story 7.14 : carte, liens de tickets, livrables et routes (valeurs exactes, bornes)."""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from hypothesis import given
from hypothesis import strategies as st

from tests.unit.ui.test_detail import DATE, _meteo, _regle
from tests.unit.ui.test_vues_ecrans import XLSX, _Double, client
from usine.contrats.meteo import (
    CodeIndicateur,
    Couleur,
    EvolutionMeteo,
    MeteoEntite,
    Operateur,
    RegleDeclenchante,
)
from usine.ui import carte
from usine.ui.liens import echapper_markdown, lien_ticket, vue_ticket
from usine.ui.serveur import HOTE, creer_application

couleurs = st.sampled_from(list(Couleur))


def _avec_couleur(entite: str, couleur: Couleur) -> MeteoEntite:
    return _meteo(entite).model_copy(update={"couleur": couleur})


def _regle_n(numerateur: int, denominateur: int) -> RegleDeclenchante:
    return _regle(CodeIndicateur.ind_2, ()).model_copy(
        update={"numerateur": numerateur, "denominateur": denominateur}
    )


# --- taille_lisible ---


@given(st.integers(min_value=0, max_value=1023))
def test_taille_sous_un_ko_en_octets(n: int) -> None:
    assert carte.taille_lisible(n) == f"{n} o"


@pytest.mark.parametrize(
    ("octets", "attendu"),
    [
        (0, "0 o"),
        (1023, "1023 o"),
        (1024, "1 Ko"),
        (1535, "1 Ko"),
        (1536, "2 Ko"),
        (1048575, "1,0 Mo"),
        (1048576, "1,0 Mo"),
        (1572864, "1,5 Mo"),
    ],
)
def test_taille_bornes(octets: int, attendu: str) -> None:
    assert carte.taille_lisible(octets) == attendu


@given(st.integers(min_value=1024, max_value=10**9))
def test_taille_jamais_1024_ko(n: int) -> None:
    texte = carte.taille_lisible(n)
    assert texte != "1024 Ko"
    assert texte.endswith((" Ko", " Mo"))
    if texte.endswith(" Ko"):
        assert int(texte.split()[0]) < 1024


# --- libelle_suite, url_detail ---


@given(st.integers(min_value=-5, max_value=10_000))
def test_libelle_suite(reste: int) -> None:
    assert carte.libelle_suite(reste) == (f"+{reste}" if reste > 0 else None)


@given(st.text(min_size=1))
def test_url_detail_encode_tout(entite: str) -> None:
    reste = carte.url_detail(entite).removeprefix("/entites/")
    assert carte.url_detail(entite) == f"/entites/{reste}"
    assert not any(c in reste for c in "/?# ")


def test_url_detail_exemples() -> None:
    assert carte.url_detail("ENT-B") == "/entites/ENT-B"
    assert carte.url_detail("A B/C") == "/entites/A%20B%2FC"


# --- fleche, tendance ---


@given(st.none() | couleurs, couleurs)
def test_fleche_propriete(avant: Couleur | None, maintenant: Couleur) -> None:
    if avant is None:
        attendu = "—"
    elif maintenant > avant:
        attendu = "↗"
    elif maintenant < avant:
        attendu = "↘"
    else:
        attendu = "→"
    assert carte.fleche(avant, maintenant) == attendu


def test_fleche_exemples() -> None:
    assert carte.fleche(Couleur.vert, Couleur.rouge) == "↗"
    assert carte.fleche(Couleur.rouge, Couleur.vert) == "↘"
    assert carte.fleche(Couleur.jaune, Couleur.jaune) == "→"
    assert carte.fleche(None, Couleur.jaune) == "—"


def test_tendance() -> None:
    assert carte.tendance(None) == "J-1 — · J-5 —"
    evolution = EvolutionMeteo(
        entite="ENT-A",
        date_arrete=DATE,
        couleur=Couleur.orange,
        date_j1=date(2026, 10, 8),
        couleur_j1=Couleur.jaune,
        date_j5=date(2026, 10, 2),
        couleur_j5=None,
    )
    assert carte.tendance(evolution) == "J-1 ↗ · J-5 —"


# --- tri des Entités ---


@given(st.lists(st.tuples(st.from_regex(r"ENT-[A-Z0-9]{1,3}", fullmatch=True), couleurs)))
def test_entites_triees_propriete(paires: list[tuple[str, Couleur]]) -> None:
    meteos = [_avec_couleur(e, c) for e, c in paires]
    triees = carte.entites_triees(meteos)
    assert sorted((m.entite, m.couleur) for m in triees) == sorted(paires)
    for a, b in zip(triees, triees[1:], strict=False):
        assert a.couleur >= b.couleur
        if a.couleur == b.couleur:
            assert a.entite <= b.entite


def test_entites_triees_exemple() -> None:
    meteos = [
        _avec_couleur("ENT-Z", Couleur.vert),
        _avec_couleur("ENT-B", Couleur.jaune),
        _avec_couleur("ENT-A", Couleur.jaune),
        _avec_couleur("ENT-Y", Couleur.rouge),
    ]
    noms = [m.entite for m in carte.entites_triees(meteos)]
    assert noms == ["ENT-Y", "ENT-A", "ENT-B", "ENT-Z"]


# --- règles et tickets ---


def test_formater_regle_infini_et_symboles() -> None:
    assert carte.formater_regle(_regle_n(11, 0)).startswith("IND-2 : ∞ (seuil ≥ ")
    stricte = _regle(CodeIndicateur.ind_2, ()).model_copy(update={"operateur": Operateur.superieur})
    assert "(seuil > " in carte.formater_regle(stricte)


def test_regle_principale() -> None:
    assert carte.regle_principale(_meteo("ENT-A")) == "—"
    premiere = _regle(CodeIndicateur.ind_2, ())
    une = _meteo("ENT-A", regles=(premiere,))
    assert carte.regle_principale(une) == carte.formater_regle(premiere)
    deux = _meteo("ENT-A", regles=(premiere, _regle(CodeIndicateur.ind_3, ())))
    assert carte.regle_principale(deux) == carte.formater_regle(premiere) + " (+1)"


@pytest.mark.parametrize(
    ("nb", "suite"), [(0, None), (1, None), (3, None), (4, "+1"), (7, "+4")]
)
def test_vue_carte_coupe_les_tickets(nb: int, suite: str | None) -> None:
    cles = tuple(f"DEMO-{n}" for n in range(nb))
    regle = _regle(CodeIndicateur.ind_2, cles)
    double = _Double(meteos=(_meteo("ENT-B", regles=(regle,)),))
    ligne = carte.vue_carte(double).lignes[0]
    assert [t.cle for t in ligne.tickets] == list(cles[:3])
    assert ligne.suite == suite


def test_tickets_principaux_markdown() -> None:
    cles = ("D1", "D2", "D3", "D4", "D5")
    meteo = _meteo("ENT-B", regles=(_regle(CodeIndicateur.ind_2, cles),))
    assert carte.tickets_principaux(meteo, lambda _c: None) == "D1, D2, D3 +2"
    trois = _meteo("ENT-B", regles=(_regle(CodeIndicateur.ind_2, cles[:3]),))
    assert carte.tickets_principaux(trois, lambda _c: None) == "D1, D2, D3"
    assert carte.tickets_principaux(_meteo("ENT-A"), lambda _c: None) == "—"
    sans = _meteo("ENT-B", regles=(_regle(CodeIndicateur.ind_2, ()),))
    assert carte.tickets_principaux(sans, lambda _c: None) == "—"


# --- liens ---


@given(st.text(), st.none() | st.text(min_size=1))
def test_vue_ticket_propriete(cle: str, url: str | None) -> None:
    vue = vue_ticket(cle, url)
    assert (vue.cle, vue.url) == (cle, url)
    assert vue.nom_accessible == (None if url is None else f"{cle} (nouvel onglet)")


@given(st.text())
def test_lien_ticket_sans_url_est_la_cle_echappee(cle: str) -> None:
    assert lien_ticket(cle, None) == echapper_markdown(cle)


@given(st.text(alphabet="abcXYZ019 -.", max_size=20))
def test_echapper_markdown_neutre_sans_special(texte: str) -> None:
    assert echapper_markdown(texte) == texte


def test_lien_ticket_exemples() -> None:
    attendu = "[DEMO\\-1](https://x.test/a%20b%28c%29)"
    assert lien_ticket("DEMO-1", "https://x.test/a b(c)") == attendu.replace("\\-", "-")
    assert echapper_markdown("A]B|C") == "A\\]B\\|C"
    assert echapper_markdown("a_b*c") == "a\\_b\\*c"


# --- tableau Markdown ---


def test_tableau_markdown() -> None:
    assert carte.tableau_markdown([]) == ""
    tableau = carte.tableau_markdown([{"A": "x|y", "B": "l1\nl2"}, {"A": "a\\|b", "B": "-"}])
    assert tableau.splitlines() == [
        "| A | B |",
        "| --- | --- |",
        "| x\\|y | l1 l2 |",
        "| a\\|b | - |",
    ]


# --- vue_carte : comptages, filtre, livrables ---


def test_vue_carte_comptages_et_filtre() -> None:
    vue = carte.vue_carte(_Double())
    comptes = [(c.meteo.couleur, c.nombre) for c in vue.comptages]
    assert comptes == [("rouge", 1), ("orange", 1), ("jaune", 0), ("vert", 1)]
    assert vue.filtre is not None
    valeurs = [o.valeur for o in vue.filtre.options]
    assert valeurs == ["toutes", "rouge", "orange", "jaune", "vert"]
    assert vue.filtre.options[1].message_vide == "Aucune Entité en rouge à cette Date d'arrêté."
    assert vue.filtre.options[0].message_vide == ""
    assert vue.filtre.annonce_une == "1 Entité affichée"
    assert vue.filtre.annonce_plusieurs.format(n=4) == "4 Entités affichées"
    assert [ligne.entite for ligne in vue.lignes] == ["ENT-B", "ENT-C", "ENT-A"]
    assert vue.sous_titre == "Date d'arrêté : 09/10/2026"
    assert vue.lignes[0].libelle_detail == "Détail ENT-B"
    assert vue.lignes[0].url_detail == "/entites/ENT-B"


def test_vue_carte_erreur_et_message() -> None:
    erreur = carte.vue_carte_erreur("boum")
    assert erreur.erreur == "boum"
    assert erreur.message is None
    assert erreur.lignes == [] and erreur.livrables == []
    message = carte.vue_carte_message("m")
    assert message.erreur is None and message.message == "m" and message.lien_message is None


def test_livrables_exacts() -> None:
    xlsx, pptx = carte.vues_livrables(_Double())
    assert xlsx.nom == "rapport_xlsx"
    assert xlsx.libelle == "Rapport quotidien"
    assert xlsx.fichier == "rapport-2026-10-09.xlsx"
    assert xlsx.url == "/livrables/rapport_xlsx"
    assert xlsx.description == f"Excel (.xlsx) · {carte.taille_lisible(len(XLSX))}"
    assert xlsx.absent is None
    assert pptx.libelle == "Comité de pilotage"
    assert pptx.url is None
    assert pptx.description == ""
    assert pptx.absent == "Non généré pour ce Passage"


def test_nom_fichier_livrable() -> None:
    assert carte.nom_fichier_livrable("rapport_pptx", date(2026, 1, 2)) == "rapport-2026-01-02.pptx"


# --- routes ---


def test_api_carte_http() -> None:
    donnees = client().get("/api/carte").json()
    assert donnees["erreur"] is None
    assert [ligne["entite"] for ligne in donnees["lignes"]] == ["ENT-B", "ENT-C", "ENT-A"]
    assert donnees["lignes"][0]["suite"] == "+2"
    assert donnees["lignes"][0]["tickets"][0]["nom_accessible"] == "DEMO-1 (nouvel onglet)"


def test_api_carte_sans_url_texte_simple() -> None:
    donnees = client(_Double(avec_url=False)).get("/api/carte").json()
    ticket = donnees["lignes"][0]["tickets"][0]
    assert ticket["url"] is None and ticket["nom_accessible"] is None


def test_oserror_de_lecture() -> None:
    def casse(_repli: bool) -> None:
        raise OSError("disque")

    http = TestClient(
        creer_application(repli=False, lire_manifeste=casse, lire_consultation=casse),
        base_url=f"http://{HOTE}",
    )
    assert http.get("/api/carte").json()["erreur"] == "Lecture du Passage impossible : disque"
    assert http.get("/entites", follow_redirects=False).headers["location"] == "/"
    assert http.get("/livrables/rapport_xlsx").status_code == 500


def test_livrable_head_hors_liste_et_absent() -> None:
    assert client().head("/livrables/autre").status_code == 404
    assert client().head("/livrables/rapport_pptx").status_code == 404


def test_api_detail_palier_illisible_vaut_palier_2() -> None:
    double = _Double()
    client(double).get("/api/entites/ENT-B?palier=abc")
    assert set(double.appels_palier) == {2}
    client(double).get("/api/entites/ENT-B?palier=3")
    assert set(double.appels_palier) == {2}
    client(double).get("/api/entites/ENT-B?palier=1")
    assert double.appels_palier.count(1) == 1


def test_entite_inconnue_avec_message() -> None:
    donnees = client().get("/api/entites/ENT-X").json()
    assert donnees["message"] == "Entité ENT-X absente du Passage affiché."
    assert donnees["lien_message"]["url"] == "/"
