"""Renfort Story 7.14 : bornes et branches de la carte, du détail, des tickets et des livrables."""

from datetime import date
from typing import Any, Literal

import pytest
from fastapi.testclient import TestClient

from tests.unit.ui.test_detail import _meteo, _regle
from tests.unit.ui.test_vues_ecrans import XLSX, _Double, _url, client
from usine.contrats.erreurs import UsineErreur
from usine.contrats.meteo import CodeIndicateur, Couleur, EvolutionMeteo, MeteoEntite
from usine.ui import carte, detail
from usine.ui.carte import (
    fleche,
    libelle_suite,
    nom_fichier_livrable,
    taille_lisible,
    tendance,
    url_detail,
    vue_carte,
    vue_carte_erreur,
    vue_carte_message,
    vue_meteo,
)
from usine.ui.liens import vue_ticket
from usine.ui.serveur import HOTE, LectureEcrans, creer_application
from usine.ui.vues import VueLien


def _tickets(n: int) -> tuple[str, ...]:
    return tuple(f"DEMO-{i}" for i in range(1, n + 1))


def _rouge(entite: str, n: int) -> MeteoEntite:
    return _meteo(entite, regles=(_regle(CodeIndicateur.ind_2, _tickets(n)),))


@pytest.mark.parametrize(
    ("octets", "attendu"),
    [
        (0, "0 o"),
        (1023, "1023 o"),
        (1024, "1 Ko"),
        (1535, "1 Ko"),
        (1536, "2 Ko"),
        (1_048_063, "1023 Ko"),
        (1_048_064, "1,0 Mo"),
        (1_048_576, "1,0 Mo"),
        (1_572_864, "1,5 Mo"),
        (10 * 1024 * 1024, "10,0 Mo"),
    ],
)
def test_taille_lisible_bornes(octets: int, attendu: str) -> None:
    assert taille_lisible(octets) == attendu


@pytest.mark.parametrize(
    ("reste", "attendu"), [(-3, None), (-1, None), (0, None), (1, "+1"), (7, "+7")]
)
def test_libelle_suite(reste: int, attendu: str | None) -> None:
    assert libelle_suite(reste) == attendu


def test_fleches() -> None:
    assert fleche(None, Couleur.rouge) == "—"
    assert fleche(Couleur.vert, Couleur.rouge) == "↗"
    assert fleche(Couleur.rouge, Couleur.vert) == "↘"
    assert fleche(Couleur.orange, Couleur.orange) == "→"
    assert fleche(Couleur.jaune, Couleur.orange) == "↗"


def test_tendance() -> None:
    assert tendance(None) == "J-1 — · J-5 —"
    evolution = EvolutionMeteo(
        date_arrete=date(2026, 10, 9),
        entite="ENT-A",
        couleur=Couleur.orange,
        date_j1=date(2026, 10, 8),
        date_j5=date(2026, 10, 2),
        couleur_j1=Couleur.rouge,
        couleur_j5=None,
    )
    assert tendance(evolution) == "J-1 ↘ · J-5 —"


def test_url_detail_et_nom_fichier() -> None:
    assert url_detail("ENT-A") == "/entites/ENT-A"
    assert url_detail("A/B c") == "/entites/A%2FB%20c"
    assert nom_fichier_livrable("rapport_xlsx", date(2026, 1, 2)) == "rapport-2026-01-02.xlsx"
    assert nom_fichier_livrable("rapport_pptx", date(2026, 1, 2)) == "rapport-2026-01-02.pptx"


def test_vue_meteo_toutes_couleurs() -> None:
    vus = {c: vue_meteo(c) for c in Couleur}
    assert {c: (v.couleur, v.libelle) for c, v in vus.items()} == {
        Couleur.vert: ("vert", "Vert"),
        Couleur.jaune: ("jaune", "Jaune"),
        Couleur.orange: ("orange", "Orange"),
        Couleur.rouge: ("rouge", "Rouge"),
    }


def test_vue_ticket_avec_et_sans_url() -> None:
    avec = vue_ticket("DEMO-1", "https://x.invalid/DEMO-1")
    assert (avec.cle, avec.url, avec.nom_accessible) == (
        "DEMO-1",
        "https://x.invalid/DEMO-1",
        "DEMO-1 (nouvel onglet)",
    )
    sans = vue_ticket("DEMO-1", None)
    assert (sans.cle, sans.url, sans.nom_accessible) == ("DEMO-1", None, None)


def test_messages_de_carte() -> None:
    lien = VueLien(libelle="L", url="/l")
    vue = vue_carte_message("m", lien)
    assert (vue.message, vue.lien_message, vue.erreur) == ("m", lien, None)
    assert vue.lignes == [] and vue.livrables == [] and vue.comptages == []
    assert vue.filtre is None and vue.legende is None and vue.sous_titre is None
    erreur = vue_carte_erreur("boom")
    assert (erreur.erreur, erreur.message, erreur.lien_message) == ("boom", None, None)


@pytest.mark.parametrize(
    ("n", "affiches", "suite"),
    [
        (0, [], None),
        (1, ["DEMO-1"], None),
        (3, ["DEMO-1", "DEMO-2", "DEMO-3"], None),
        (4, ["DEMO-1", "DEMO-2", "DEMO-3"], "+1"),
        (10, ["DEMO-1", "DEMO-2", "DEMO-3"], "+7"),
    ],
)
def test_carte_borne_des_trois_tickets(n: int, affiches: list[str], suite: str | None) -> None:
    (ligne,) = vue_carte(_Double(meteos=(_rouge("ENT-B", n),))).lignes  # type: ignore[arg-type]
    assert [t.cle for t in ligne.tickets] == affiches
    assert ligne.suite == suite


def test_detail_borne_des_trois_tickets() -> None:
    for n, suite_cles, libelle in ((3, [], None), (4, ["DEMO-4"], "+1")):
        double = _Double(meteos=(_rouge("ENT-B", n),))
        (regle,) = detail.vue_detail(double, "ENT-B").regles  # type: ignore[arg-type]
        assert [t.cle for t in regle.tickets] == ["DEMO-1", "DEMO-2", "DEMO-3"]
        assert [t.cle for t in regle.tickets_suite] == suite_cles
        assert regle.libelle_suite == libelle


def test_carte_tri_grave_puis_entite_alphabetique() -> None:
    orange = _meteo("ENT-D", regles=(_regle(CodeIndicateur.ind_3, ("DEMO-9",)),)).model_copy(
        update={"couleur": Couleur.orange}
    )
    meteos = (_meteo("ENT-Z"), _meteo("ENT-A"), orange, _rouge("ENT-M", 1), _rouge("ENT-C", 1))
    vue = vue_carte(_Double(meteos=meteos))  # type: ignore[arg-type]
    assert [ligne.entite for ligne in vue.lignes] == ["ENT-C", "ENT-M", "ENT-D", "ENT-A", "ENT-Z"]
    assert [(c.meteo.couleur, c.nombre) for c in vue.comptages] == [
        ("rouge", 2),
        ("orange", 1),
        ("jaune", 0),
        ("vert", 2),
    ]
    assert sum(c.nombre for c in vue.comptages) == len(vue.lignes)


def test_carte_ligne_verte_sans_regle_ni_ticket() -> None:
    vue = vue_carte(_Double(meteos=(_meteo("ENT-A"),)))  # type: ignore[arg-type]
    (ligne,) = vue.lignes
    assert ligne.regle_principale == "—"
    assert ligne.tickets == []
    assert ligne.suite is None
    assert ligne.tendance == "J-1 — · J-5 —"


def test_carte_filtre_messages_vides_et_options() -> None:
    filtre = vue_carte(_Double()).filtre  # type: ignore[arg-type]
    assert filtre is not None
    assert [(o.valeur, o.libelle) for o in filtre.options] == [
        ("toutes", "Toutes"),
        ("rouge", "Rouge"),
        ("orange", "Orange"),
        ("jaune", "Jaune"),
        ("vert", "Vert"),
    ]
    assert filtre.options[0].message_vide == ""
    assert filtre.options[1].message_vide == "Aucune Entité en rouge à cette Date d'arrêté."
    assert filtre.options[4].message_vide == "Aucune Entité en vert à cette Date d'arrêté."
    assert "{n}" in filtre.annonce_plusieurs and "{n}" not in filtre.annonce_une


def test_carte_livrables_deux_presents_tailles() -> None:
    double = _Double(livrables={"rapport_xlsx": XLSX, "rapport_pptx": bytes(300)})
    xlsx, pptx = vue_carte(double).livrables  # type: ignore[arg-type]
    assert (xlsx.nom, xlsx.url, xlsx.absent) == ("rapport_xlsx", "/livrables/rapport_xlsx", None)
    assert pptx.description == "PowerPoint (.pptx) · 300 o"
    assert pptx.url == "/livrables/rapport_pptx"
    assert pptx.fichier == "rapport-2026-10-09.pptx"


def test_carte_livrables_aucun() -> None:
    xlsx, pptx = vue_carte(_Double(livrables={})).livrables  # type: ignore[arg-type]
    for vue in (xlsx, pptx):
        assert vue.url is None
        assert vue.description == ""
        assert vue.absent == "Non généré pour ce Passage"


def test_livrable_vide_est_present() -> None:
    xlsx, _pptx = vue_carte(_Double(livrables={"rapport_xlsx": b""})).livrables  # type: ignore[arg-type]
    assert xlsx.url == "/livrables/rapport_xlsx"
    assert xlsx.description == "Excel (.xlsx) · 0 o"
    assert xlsx.absent is None


def test_mime_et_libelles_des_livrables() -> None:
    assert set(carte.MIME_LIVRABLES) == set(carte.LIVRABLES) == {"rapport_xlsx", "rapport_pptx"}
    assert carte.MIME_LIVRABLES["rapport_xlsx"].endswith("spreadsheetml.sheet")
    assert carte.LIVRABLES["rapport_pptx"] == ("Comité de pilotage", "PowerPoint (.pptx)")


# --- Détail ---


def test_detail_entite_absente_message_et_liens() -> None:
    vue = client().get("/api/entites/ENT-X").json()
    assert vue["message"] == "Entité ENT-X absente du Passage affiché."
    assert vue["lien_message"] == {"libelle": "Voir la carte météo", "url": "/"}
    assert [e["url"] for e in vue["entites"]] == [
        "/entites/ENT-B",
        "/entites/ENT-C",
        "/entites/ENT-A",
    ]
    assert vue["meteo"] is None and vue["prevision"] is None and vue["explication"] is None
    assert vue["regles"] == [] and vue["kpi"] == []


def test_detail_sans_meteo() -> None:
    vue = client(_Double(meteos=())).get("/api/entites/ENT-A").json()
    assert vue["message"] == "Ce Passage ne contient aucune Météo."
    assert vue["entites"] == []


def test_detail_verte_sans_regle() -> None:
    vue = detail.vue_detail(_Double(), "ENT-A")  # type: ignore[arg-type]
    assert vue.regles == []
    assert vue.aucune_regle == detail.AUCUNE_REGLE
    assert detail.vue_detail(_Double(), "ENT-B").aucune_regle is None  # type: ignore[arg-type]


def test_detail_kpi_vide() -> None:
    class _SansKpi(_Double):
        def kpi(self, date_arrete: date | None = None, entite: str | None = None) -> Any:
            return super().kpi().clear()

    vue = detail.vue_detail(_SansKpi(), "ENT-B")  # type: ignore[arg-type]
    assert vue.kpi == []
    assert vue.aucun_kpi == detail.AUCUN_KPI


@pytest.mark.parametrize("palier", ["", "0", "3", "-1", "un", "1.0", "2"])
def test_detail_palier_autre_que_un_donne_palier_deux(palier: str) -> None:
    vue = client().get(f"/api/entites/ENT-B?palier={palier}").json()
    assert vue["palier"] == 2
    assert vue["prevision"] is not None


def test_detail_sans_parametre_palier_est_palier_deux() -> None:
    assert client().get("/api/entites/ENT-B").json()["palier"] == 2


def test_detail_palier_lu_selon_la_demande() -> None:
    double = _Double()
    client(double).get("/api/entites/ENT-B?palier=1")
    assert double.appels_palier == [1]
    double2 = _Double()
    client(double2).get("/api/entites/ENT-B")
    assert double2.appels_palier == [2]


def test_detail_segment_palier_etat_actif() -> None:
    vue = detail.vue_detail(_Double(), "ENT-B", 1)  # type: ignore[arg-type]
    assert vue.segment_palier is not None
    assert [(o.valeur, o.actif) for o in vue.segment_palier.options] == [(2, False), (1, True)]
    assert vue.palier == 1


def test_detail_passage_palier_1_ignore_palier_demande() -> None:
    double = _Double(palier=1)
    vue = detail.vue_detail(double, "ENT-B", 2)  # type: ignore[arg-type]
    assert vue.palier == 1 and vue.segment_palier is None
    assert double.appels_palier == [1]


def test_detail_mode_repli_texte_simple() -> None:
    vue = detail.vue_detail(_Double(avec_url=False), "ENT-B")  # type: ignore[arg-type]
    (regle,) = vue.regles
    tickets = regle.tickets + regle.tickets_suite
    assert all(t.url is None and t.nom_accessible is None for t in tickets)
    assert vue.explication is not None
    for explication in vue.explication.explications:
        assert all(t.url is None for t in explication.citations)
        assert all(s.ticket is None or s.ticket.url is None for s in explication.segments)


def test_detail_url_ticket_avec_lien() -> None:
    (regle,) = detail.vue_detail(_Double(), "ENT-B").regles  # type: ignore[arg-type]
    assert regle.tickets[0].url == _url("DEMO-1")
    assert regle.tickets[0].nom_accessible == "DEMO-1 (nouvel onglet)"


def test_detail_erreur() -> None:
    vue = detail.vue_detail_erreur("boom")
    assert (vue.erreur, vue.message, vue.lien_message) == ("boom", None, None)
    assert vue.lien_carte.url == "/"


# --- Serveur ---


def _http(lire: Any) -> TestClient:
    application = creer_application(repli=False, lire_manifeste=lambda _r: None, lire_consultation=lire)
    return TestClient(application, base_url=f"http://{HOTE}")


def _aucun(_repli: bool) -> None:
    return None


def _casse(_repli: bool) -> LectureEcrans:
    raise UsineErreur("manifeste illisible")


def _illisible(_repli: bool) -> LectureEcrans:
    raise PermissionError(13, "accès refusé", "sorties/passages")


def test_api_detail_sans_passage() -> None:
    vue = _http(_aucun).get("/api/entites/ENT-A").json()
    assert vue["message"] == carte.AUCUN_PASSAGE
    assert vue["lien_message"] == {"libelle": "Lancer la Chaîne", "url": "/chaine"}
    assert vue["erreur"] is None


def test_api_detail_erreurs() -> None:
    usine = _http(_casse).get("/api/entites/ENT-A").json()
    assert usine["erreur"] == "manifeste illisible"
    assert usine["message"] is None
    os_err = _http(_illisible).get("/api/entites/ENT-A").json()
    assert os_err["erreur"].startswith("Lecture du Passage impossible : ")
    assert "accès refusé" in os_err["erreur"]


def test_api_carte_erreurs_exactes() -> None:
    usine = _http(_casse).get("/api/carte").json()
    assert (usine["erreur"], usine["message"]) == ("manifeste illisible", None)
    os_err = _http(_illisible).get("/api/carte").json()
    assert os_err["erreur"].startswith("Lecture du Passage impossible : ")


def test_navigation_oserror_retourne_a_la_carte() -> None:
    reponse = _http(_illisible).get("/entites", follow_redirects=False)
    assert reponse.status_code == 307
    assert reponse.headers["location"] == "/"


def test_navigation_sans_meteo_retourne_a_la_carte() -> None:
    reponse = client(_Double(meteos=())).get("/entites", follow_redirects=False)
    assert reponse.headers["location"] == "/"


def test_navigation_premiere_entite_est_la_plus_grave() -> None:
    meteos = (_meteo("ENT-A"), _rouge("ENT-Q", 1), _rouge("ENT-F", 1))
    reponse = client(_Double(meteos=meteos)).get("/entites", follow_redirects=False)  # type: ignore[arg-type]
    assert reponse.headers["location"] == "/entites/ENT-F"


def test_livrable_head_absent_et_present() -> None:
    http = client()
    present = http.head("/livrables/rapport_xlsx")
    assert present.status_code == 200
    assert "attachment" in present.headers["content-disposition"]
    assert http.head("/livrables/rapport_pptx").status_code == 404


def test_livrable_absent_page_exacte() -> None:
    reponse = client().get("/livrables/rapport_pptx")
    assert "rapport-2026-10-09.pptx" in reponse.text
    assert "pas été généré pour ce Passage" in reponse.text
    assert "Livrable indisponible" in reponse.text


def test_livrable_sans_passage_message() -> None:
    reponse = _http(_aucun).get("/livrables/rapport_pptx")
    assert reponse.status_code == 404
    assert "rapport_pptx" in reponse.text
    assert "pas disponible" in reponse.text


def test_livrable_oserror_et_manifeste_illisible_donnent_500() -> None:
    class _Os(_Double):
        def livrable(self, nom: Literal["rapport_xlsx", "rapport_pptx"]) -> bytes | None:
            raise PermissionError(13, "refusé", "x")

    reponse = client(_Os()).get("/livrables/rapport_pptx")
    assert reponse.status_code == 500
    assert "Lecture du livrable rapport-2026-10-09.pptx impossible" in reponse.text
    cassee = _http(_casse).get("/livrables/rapport_xlsx")
    assert cassee.status_code == 500
    assert "Lecture du livrable rapport_xlsx impossible : manifeste illisible" in cassee.text


def test_livrable_contenu_octet_pour_octet() -> None:
    contenu = bytes(range(256)) * 3
    reponse = client(_Double(livrables={"rapport_pptx": contenu})).get("/livrables/rapport_pptx")
    assert reponse.content == contenu
    assert reponse.headers["content-length"] == str(len(contenu))


def test_livrable_nom_hors_liste_sans_lire() -> None:
    appels: list[bool] = []

    def lire(_repli: bool) -> Any:
        appels.append(True)
        return _Double()

    assert _http(lire).get("/livrables/autre").status_code == 404
    assert appels == []
