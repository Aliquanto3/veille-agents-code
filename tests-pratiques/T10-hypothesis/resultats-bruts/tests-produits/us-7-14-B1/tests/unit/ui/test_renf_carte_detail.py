"""Renfort Story 7.14 : bornes, propriétés et branches d'erreur des vues et routes (AD-25)."""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

from tests.unit.ui.test_detail import _meteo, _regle
from tests.unit.ui.test_vues_ecrans import XLSX, _Double, _url, client
from usine.contrats.erreurs import UsineErreur
from usine.contrats.meteo import CodeIndicateur, Couleur, MeteoEntite
from usine.ui import carte
from usine.ui.detail import EXPLICATION_PALIER_1, entite_absente, vue_detail
from usine.ui.liens import vue_ticket
from usine.ui.serveur import HOTE, creer_application

CODES = st.from_regex(r"ENT-[A-Z0-9]{1,6}", fullmatch=True)
ORDRE = sorted(Couleur)


def _avec_couleur(entite: str, couleur: Couleur) -> MeteoEntite:
    return _meteo(entite).model_copy(update={"couleur": couleur})


def _rouge(entite: str, nb_tickets: int) -> MeteoEntite:
    cles = tuple(f"DEMO-{n}" for n in range(1, nb_tickets + 1))
    return _meteo(entite, regles=(_regle(CodeIndicateur.ind_2, cles),))


def _client_avec(lire) -> TestClient:  # type: ignore[no-untyped-def]
    app = creer_application(repli=False, lire_manifeste=lambda _: None, lire_consultation=lire)
    return TestClient(app, base_url=f"http://{HOTE}")


# --- taille_lisible ---


@pytest.mark.parametrize(
    ("octets", "attendu"),
    [
        (0, "0 o"),
        (1023, "1023 o"),
        (1024, "1 Ko"),
        (1536, "2 Ko"),
        (1024 * 1023, "1023 Ko"),
        (1048575, "1,0 Mo"),
        (1048576, "1,0 Mo"),
        (1048576 * 3 + 524288, "3,5 Mo"),
    ],
)
def test_taille_lisible_valeurs_exactes(octets: int, attendu: str) -> None:
    assert carte.taille_lisible(octets) == attendu


@given(st.integers(min_value=0, max_value=10**10))
def test_taille_lisible_jamais_1024_ko(octets: int) -> None:
    texte = carte.taille_lisible(octets)
    assert texte != "1024 Ko"
    if octets < 1024:
        assert texte == f"{octets} o"
    elif texte.endswith(" Ko"):
        assert 1 <= int(texte.removesuffix(" Ko")) <= 1023
    else:
        assert texte.endswith(" Mo")
        assert "," in texte


# --- tri, suite, tickets, URLs ---


@given(
    st.lists(
        st.tuples(CODES, st.sampled_from(ORDRE)), unique_by=lambda t: t[0], max_size=12
    ),
    st.randoms(use_true_random=False),
)
def test_entites_triees_gravite_decroissante_puis_entite(
    paires: list[tuple[str, Couleur]], hasard: object
) -> None:
    meteos = [_avec_couleur(e, c) for e, c in paires]
    hasard.shuffle(meteos)  # type: ignore[attr-defined]
    triees = carte.entites_triees(meteos)
    assert sorted(m.entite for m in triees) == sorted(e for e, _ in paires)
    cles = [(-ORDRE.index(m.couleur), m.entite) for m in triees]
    assert cles == sorted(cles)


@given(st.integers(min_value=-5, max_value=50))
def test_libelle_suite(reste: int) -> None:
    assert carte.libelle_suite(reste) == (f"+{reste}" if reste > 0 else None)


@given(st.text(min_size=1, max_size=20), st.one_of(st.none(), st.text(min_size=1, max_size=40)))
def test_vue_ticket_propriete(cle: str, url: str | None) -> None:
    vue = vue_ticket(cle, url)
    assert vue.cle == cle
    assert vue.url == url
    assert vue.nom_accessible == (None if url is None else f"{cle} (nouvel onglet)")


def test_url_detail_et_nom_fichier() -> None:
    assert carte.url_detail("ENT-B") == "/entites/ENT-B"
    assert carte.url_detail("a/b c") == "/entites/a%2Fb%20c"
    assert carte.nom_fichier_livrable("rapport_xlsx", date(2026, 10, 9)) == "rapport-2026-10-09.xlsx"
    assert carte.nom_fichier_livrable("rapport_pptx", date(2026, 1, 2)).endswith("2026-01-02.pptx")


@settings(deadline=None, max_examples=40)
@given(st.integers(min_value=1, max_value=12))
def test_carte_tickets_coupes_cote_serveur(n: int) -> None:
    ligne = carte.vue_carte(_Double(meteos=(_rouge("ENT-B", n),))).lignes[0]
    assert [t.cle for t in ligne.tickets] == [f"DEMO-{k}" for k in range(1, min(n, 3) + 1)]
    assert ligne.suite == (f"+{n - 3}" if n > 3 else None)
    assert ligne.regle_principale == "IND-2 : 11 (seuil ≥ 10)"


@settings(deadline=None, max_examples=40)
@given(st.integers(min_value=1, max_value=12))
def test_detail_tickets_et_suite(n: int) -> None:
    vue = vue_detail(_Double(meteos=(_rouge("ENT-B", n),)), "ENT-B")
    regle = vue.regles[0]
    assert [t.cle for t in regle.tickets] == [f"DEMO-{k}" for k in range(1, min(n, 3) + 1)]
    assert [t.cle for t in regle.tickets_suite] == [f"DEMO-{k}" for k in range(4, n + 1)]
    assert regle.libelle_suite == (f"+{n - 3}" if n > 3 else None)


def test_carte_comptages_et_ordre() -> None:
    meteos = (
        _avec_couleur("ENT-A", Couleur.jaune),
        _avec_couleur("ENT-B", Couleur.jaune),
        _rouge("ENT-C", 1),
        _avec_couleur("ENT-D", Couleur.vert),
    )
    vue = carte.vue_carte(_Double(meteos=meteos))
    assert [(c.meteo.couleur, c.nombre) for c in vue.comptages] == [
        ("rouge", 1),
        ("orange", 0),
        ("jaune", 2),
        ("vert", 1),
    ]
    assert [ligne.entite for ligne in vue.lignes] == ["ENT-C", "ENT-A", "ENT-B", "ENT-D"]
    assert [ligne.tickets for ligne in vue.lignes[1:]] == [[], [], []]
    assert [ligne.suite for ligne in vue.lignes[1:]] == [None, None, None]
    assert vue.lignes[1].regle_principale == carte.INCONNUE


def test_carte_messages_vides_du_filtre() -> None:
    filtre = carte.vue_carte(_Double()).filtre
    assert filtre is not None
    messages = {o.valeur: o.message_vide for o in filtre.options}
    assert messages["toutes"] == ""
    assert messages["rouge"] == "Aucune Entité en rouge à cette Date d'arrêté."
    assert messages["orange"] == "Aucune Entité en orange à cette Date d'arrêté."
    assert filtre.annonce_une == "1 Entité affichée"
    assert filtre.annonce_plusieurs == "{n} Entités affichées"


def test_carte_message_et_erreur_formes() -> None:
    sans = carte.vue_carte_message("m")
    assert (sans.message, sans.erreur, sans.lignes, sans.livrables, sans.filtre) == (
        "m",
        None,
        [],
        [],
        None,
    )
    erreur = carte.vue_carte_erreur("boum")
    assert (erreur.erreur, erreur.message, erreur.lien_message) == ("boum", None, None)


def test_carte_aucune_meteo_message() -> None:
    vue = carte.vue_carte(_Double(meteos=()))
    assert vue.message == carte.AUCUNE_METEO
    assert vue.lignes == []


def test_livrables_vues_exactes() -> None:
    xlsx, pptx = carte.vues_livrables(_Double(livrables={"rapport_xlsx": XLSX, "rapport_pptx": b""}))
    assert (xlsx.nom, xlsx.libelle, xlsx.fichier) == (
        "rapport_xlsx",
        "Rapport quotidien",
        "rapport-2026-10-09.xlsx",
    )
    assert xlsx.description == "Excel (.xlsx) · 2 Ko"
    assert (xlsx.url, xlsx.absent) == ("/livrables/rapport_xlsx", None)
    # un fichier vide existe : il reste proposé
    assert pptx.description == "PowerPoint (.pptx) · 0 o"
    assert (pptx.url, pptx.absent) == ("/livrables/rapport_pptx", None)


def test_livrables_absents_sans_lien() -> None:
    vues = carte.vues_livrables(_Double(livrables={}))
    assert len(vues) == 2
    for vue in vues:
        assert vue.url is None
        assert vue.description == ""
        assert vue.absent == "Non généré pour ce Passage"


# --- détail ---


def test_detail_palier_demande_et_passage() -> None:
    double = _Double(palier=2)
    un = vue_detail(double, "ENT-B", 1)
    deux = vue_detail(double, "ENT-B", 2)
    assert un.palier == 1
    assert deux.palier == 2
    assert un.prevision is None
    assert deux.prevision is not None
    assert un.explication is not None
    assert EXPLICATION_PALIER_1 in un.explication.model_dump_json()
    for champ in ("meteo", "regles", "kpi", "risque"):
        assert getattr(un, champ) == getattr(deux, champ)
    assert double.appels_palier == [1, 2]
    assert un.segment_palier is not None
    assert deux.segment_palier is not None
    assert [o.actif for o in un.segment_palier.options] == [False, True]
    assert [o.actif for o in deux.segment_palier.options] == [True, False]
    assert [o.valeur for o in deux.segment_palier.options] == [2, 1]


def test_detail_passage_palier_1_ne_lit_aucune_sortie_llm() -> None:
    double = _Double(palier=1)
    vue = vue_detail(double, "ENT-B", 2)
    assert vue.segment_palier is None
    assert vue.palier == 1
    assert vue.prevision is not None
    assert set(double.appels_palier) == {1}


@pytest.mark.parametrize("palier", [None, "", "2", "3", "0", "abc", "01", "1.0"])
def test_api_palier_illisible_vaut_palier_2(palier: str | None) -> None:
    suffixe = "" if palier is None else f"?palier={palier}"
    vue = client().get(f"/api/entites/ENT-B{suffixe}").json()
    assert vue["palier"] == 2
    assert vue["prevision"] is not None


def test_api_palier_1_masque_la_prevision() -> None:
    vue = client().get("/api/entites/ENT-B?palier=1").json()
    assert vue["palier"] == 1
    assert vue["prevision"] is None


def test_detail_entite_absente_exact() -> None:
    vue = vue_detail(_Double(), "ENT-X")
    assert vue.message == "Entité ENT-X absente du Passage affiché."
    assert vue.message == entite_absente("ENT-X")
    assert vue.lien_message is not None
    assert (vue.lien_message.libelle, vue.lien_message.url) == ("Voir la carte météo", "/")
    assert [e.libelle for e in vue.entites] == ["ENT-B", "ENT-C", "ENT-A"]
    assert vue.meteo is None


def test_detail_entite_verte_sans_regle() -> None:
    vue = vue_detail(_Double(), "ENT-A")
    assert vue.regles == []
    assert vue.aucune_regle is not None
    assert vue.meteo is not None
    assert vue.meteo.couleur == "vert"


# --- routes ---


def test_navigation_redirection_307_sans_suivre() -> None:
    reponse = client().get("/entites", follow_redirects=False)
    assert reponse.status_code == 307
    assert reponse.headers["location"] == "/entites/ENT-B"


def test_navigation_erreur_de_lecture_redirige_vers_la_carte() -> None:
    def casse(_repli: bool) -> None:
        raise UsineErreur("illisible")

    reponse = _client_avec(casse).get("/entites", follow_redirects=False)
    assert (reponse.status_code, reponse.headers["location"]) == (307, "/")


def test_livrable_en_tetes_exacts_get_et_head() -> None:
    c = client()
    get = c.get("/livrables/rapport_xlsx")
    assert get.status_code == 200
    assert get.content == XLSX
    assert get.headers["content-type"] == carte.MIME_LIVRABLES["rapport_xlsx"]
    assert get.headers["content-disposition"] == 'attachment; filename="rapport-2026-10-09.xlsx"'
    head = c.head("/livrables/rapport_xlsx")
    assert head.status_code == 200
    assert head.headers["content-disposition"] == get.headers["content-disposition"]
    assert head.content == b""


@pytest.mark.parametrize("nom", ["autre", "rapport_XLSX", "rapport_xlsx.xlsx", "rapport"])
def test_livrable_nom_hors_liste_404(nom: str) -> None:
    assert client().get(f"/livrables/{nom}").status_code == 404


def test_livrable_absent_page_404_nomme_le_fichier() -> None:
    reponse = client(_Double(livrables={})).get("/livrables/rapport_pptx")
    assert reponse.status_code == 404
    assert reponse.headers["content-type"].startswith("text/html")
    assert "rapport-2026-10-09.pptx" in reponse.text
    assert 'href="/"' in reponse.text


def test_livrable_lecture_impossible_500_message_echappe() -> None:
    class Casse(_Double):
        def livrable(self, nom: str) -> bytes | None:  # type: ignore[override]
            raise OSError("<b>&boum")

    reponse = client(Casse()).get("/livrables/rapport_xlsx")
    assert reponse.status_code == 500
    assert "&lt;b&gt;&amp;boum" in reponse.text
    assert "<b>&boum" not in reponse.text
    assert "rapport-2026-10-09.xlsx" in reponse.text


@pytest.mark.parametrize(
    ("exc", "attendu"),
    [
        (OSError("disque"), "Lecture du Passage impossible : disque"),
        (UsineErreur("grille"), "grille"),
    ],
)
def test_api_lecture_impossible(exc: Exception, attendu: str) -> None:
    def casse(_repli: bool) -> None:
        raise exc

    c = _client_avec(casse)
    assert c.get("/api/carte").json()["erreur"] == attendu
    assert c.get("/api/entites/ENT-A").json()["erreur"] == attendu


def test_api_sans_passage_lien_chaine() -> None:
    c = _client_avec(lambda _: None)
    vue = c.get("/api/carte").json()
    assert vue["message"] == carte.AUCUN_PASSAGE
    assert vue["lien_message"] == {"libelle": "Lancer la Chaîne", "url": "/chaine"}
    detail = c.get("/api/entites/ENT-A").json()
    assert detail["message"] == carte.AUCUN_PASSAGE
    assert detail["lien_message"] == {"libelle": "Lancer la Chaîne", "url": "/chaine"}
    assert c.get("/livrables/rapport_xlsx").status_code == 404


def test_api_carte_url_ticket_en_donnee() -> None:
    ligne = client().get("/api/carte").json()["lignes"][0]
    assert ligne["tickets"][0] == {
        "cle": "DEMO-1",
        "url": _url("DEMO-1"),
        "nom_accessible": "DEMO-1 (nouvel onglet)",
    }
    repli = client(_Double(avec_url=False)).get("/api/carte").json()["lignes"][0]
    assert repli["tickets"][0] == {"cle": "DEMO-1", "url": None, "nom_accessible": None}
