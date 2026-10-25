"""Renfort de la Story 7.14 : bornes, branches et contrats des vues carte / détail / serveur."""

import pytest
from pydantic import ValidationError

from tests.unit.ui.test_detail import _explication, _meteo, _narration, _prevision, _regle, _risque
from tests.unit.ui.test_vues_ecrans import _Double, _url, client
from usine.contrats.llm import StatutControle
from usine.contrats.meteo import CodeIndicateur
from usine.contrats.prevision import StatutPrevision
from usine.ui import carte, detail
from usine.ui.liens import vue_ticket

MIO = 1024 * 1024


class _SansKpi(_Double):
    def kpi(self, date_arrete=None, entite=None):  # type: ignore[no-untyped-def]
        return super().kpi().clear()


# --- carte : libelle_suite, taille_lisible ---


def test_libelle_suite_bornes() -> None:
    assert carte.libelle_suite(1) == "+1"
    assert carte.libelle_suite(0) is None
    assert carte.libelle_suite(-2) is None


@pytest.mark.parametrize(
    ("octets", "attendu"),
    [
        (0, "0 o"),
        (1023, "1023 o"),
        (1024, "1 Ko"),
        (MIO - 513, "1023 Ko"),
        (100 * MIO, "100,0 Mo"),
        (3 * MIO // 2, "1,5 Mo"),
    ],
)
def test_taille_lisible_exacte(octets: int, attendu: str) -> None:
    assert carte.taille_lisible(octets) == attendu


# --- carte : tickets de la première règle, suite ---


def test_carte_premiere_regle_et_suite() -> None:
    sept = tuple(f"DEMO-{n}" for n in range(1, 8))
    meteo = _meteo(
        "ENT-B",
        regles=(_regle(CodeIndicateur.ind_2, sept), _regle(CodeIndicateur.ind_3, ("AUTRE-1",))),
    )
    vue = client(_Double(meteos=(meteo,))).get("/api/carte").json()
    ligne = vue["lignes"][0]
    assert [t["cle"] for t in ligne["tickets"]] == ["DEMO-1", "DEMO-2", "DEMO-3"]
    assert ligne["suite"] == "+4"


def test_carte_trois_tickets_sans_suite() -> None:
    meteo = _meteo("ENT-B", regles=(_regle(CodeIndicateur.ind_2, ("D-1", "D-2", "D-3")),))
    ligne = client(_Double(meteos=(meteo,))).get("/api/carte").json()["lignes"][0]
    assert ligne["suite"] is None


# --- détail : découpage et liens ---


def test_morceaux_sans_citation() -> None:
    assert detail._morceaux("abc", ()) == [("abc", False)]


def test_morceaux_alternance_des_cles() -> None:
    morceaux = detail._morceaux("A DEMO-1 b DEMO-2 c", ("DEMO-1", "DEMO-2"))
    assert morceaux == [
        ("A ", False),
        ("DEMO-1", True),
        (" b ", False),
        ("DEMO-2", True),
        (" c", False),
    ]


def test_texte_avec_liens_cles_liees_texte_echappe() -> None:
    texte = detail.texte_avec_liens("a_b DEMO-1 c", ("DEMO-1",), _url)
    assert texte == "a\\_b [DEMO-1](" + _url("DEMO-1") + ") c"
    assert detail.texte_avec_liens("a_b", (), _url) == "a\\_b"


# --- détail : prévision ---


def _bloc(statut: StatutPrevision, **maj: object):  # type: ignore[no-untyped-def]
    prevision = _prevision(statut, "ENT-B").model_copy(update=maj)
    meteo = _meteo("ENT-B", regles=(_regle(CodeIndicateur.ind_2, ("D-1",)),))
    section = detail.section_prevision(meteo, (prevision,), True)
    assert section.message is None
    return section.blocs[0]


def test_bloc_sortie_projetee() -> None:
    bloc = _bloc(StatutPrevision.sortie_projetee)
    assert bloc.titre == "Sortie du rouge estimée : 20/10/2026"
    assert bloc.sous_titre == "Facteurs explicatifs"
    assert len(bloc.sous_items) == 2


def test_bloc_sortie_projetee_sans_date_ni_facteur() -> None:
    bloc = _bloc(StatutPrevision.sortie_projetee, date_sortie_estimee=None, facteurs=())
    assert bloc.titre == f"Sortie du rouge estimée : {carte.INCONNUE}"
    assert bloc.sous_titre is None
    assert bloc.sous_items == []


def test_bloc_pas_de_sortie_et_non_projetable() -> None:
    assert _bloc(StatutPrevision.pas_de_sortie_projetee).titre == detail.PAS_DE_SORTIE
    bloc = _bloc(StatutPrevision.regle_non_projetable)
    assert bloc.titre == f"{detail.NON_PROJETABLE} (IND-2)"


def test_prevision_filtrée_sur_l_entite() -> None:
    meteo = _meteo("ENT-A", regles=(_regle(CodeIndicateur.ind_2, ("D-1",)),))
    autre = _prevision(StatutPrevision.sortie_projetee, "ENT-B")
    section = detail.section_prevision(meteo, (autre,), True)
    assert section.message == detail.PREVISION_NON_CALCULEE_ENTITE
    assert section.blocs == []


def test_narration_seulement_de_l_entite_et_acceptee() -> None:
    meteo = _meteo("ENT-A", regles=(_regle(CodeIndicateur.ind_2, ("D-1",)),))
    propre = _prevision(StatutPrevision.sortie_projetee, "ENT-A")
    autre_entite = _narration(StatutControle.conforme, "ENT-B")
    rejetee = _narration(StatutControle.rejete, "ENT-A")
    section = detail.section_prevision(meteo, (propre,), True, (autre_entite, rejetee))
    assert [b.titre for b in section.blocs] == ["Sortie du rouge estimée : 20/10/2026"]
    acceptee = _narration(StatutControle.conforme, "ENT-A")
    section = detail.section_prevision(meteo, (propre,), True, (autre_entite, rejetee, acceptee))
    assert [b.texte for b in section.blocs] == [acceptee.texte]


# --- détail : risque ---


def test_risque_filtré_sur_l_entite() -> None:
    meteo = _meteo("ENT-A")
    section = detail.section_risque(meteo, (_risque("ENT-B"),), True)
    assert section.message == detail.AUCUN_RISQUE
    assert section.tableau is None
    propre = detail.section_risque(meteo, (_risque("ENT-A"),), True)
    assert propre.tableau is not None
    assert len(propre.tableau.lignes) == 1


# --- détail : vue, palier, KPI, suite ---


def test_vue_detail_palier_par_defaut_est_2() -> None:
    assert vue_detail_par_defaut().palier == 2
    assert vue_detail_par_defaut().explication.message is None


def vue_detail_par_defaut():  # type: ignore[no-untyped-def]
    return detail.vue_detail(_Double(), "ENT-B")


def test_vue_detail_message_palier_2() -> None:
    vue = client().get("/api/entites/INCONNUE").json()
    assert vue["palier"] == 2
    assert vue["message"] == detail.entite_absente("INCONNUE")


def test_detail_suite_des_tickets() -> None:
    sept = tuple(f"DEMO-{n}" for n in range(1, 8))
    meteo = _meteo("ENT-B", regles=(_regle(CodeIndicateur.ind_2, sept),))
    vue = detail.vue_detail(_Double(meteos=(meteo,)), "ENT-B")
    assert vue.regles[0].libelle_suite == "+4"
    assert len(vue.regles[0].tickets) == 3
    assert len(vue.regles[0].tickets_suite) == 4


def test_detail_aucun_kpi() -> None:
    avec = detail.vue_detail(_Double(), "ENT-B")
    assert avec.kpi
    assert avec.aucun_kpi is None
    sans = detail.vue_detail(_SansKpi(), "ENT-B")
    assert sans.kpi == []
    assert sans.aucun_kpi == detail.AUCUN_KPI


# --- vues figées ---


def test_vues_immuables() -> None:
    vue = vue_ticket("DEMO-1", None)
    with pytest.raises(ValidationError):
        vue.cle = "AUTRE"  # type: ignore[misc]


# --- serveur ---


def test_detail_oserror_devient_bandeau() -> None:
    from fastapi.testclient import TestClient

    from usine.ui.serveur import HOTE, creer_application

    def lire(_repli: bool):  # type: ignore[no-untyped-def]
        raise OSError("disque")

    app = creer_application(repli=False, lire_manifeste=lambda _r: None, lire_consultation=lire)
    reponse = TestClient(app, base_url=f"http://{HOTE}").get("/api/entites/ENT-B")
    assert reponse.status_code == 200
    assert reponse.json()["erreur"] == "Lecture du Passage impossible : disque"


def test_routes_hors_schema() -> None:
    from usine.ui.serveur import creer_application

    app = creer_application(repli=False, lire_manifeste=lambda _r: None, lire_consultation=lambda _: None)
    chemins = app.openapi()["paths"]
    assert "/entites" not in chemins
    assert "/livrables/{nom}" not in chemins
    assert "/api/carte" in chemins
