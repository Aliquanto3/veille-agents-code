"""Renforcement de la Story 7.14 : bornes, branches et valeurs exactes des vues."""

import polars as pl
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from tests.unit.ui.test_detail import _meteo, _narration, _prevision, _regle, _risque, _url
from tests.unit.ui.test_vues_ecrans import _Double
from usine.contrats.llm import StatutControle
from usine.contrats.meteo import CodeIndicateur, Couleur, MeteoEntite
from usine.contrats.prevision import StatutPrevision
from usine.ui import carte
from usine.ui.carte import libelle_suite, taille_lisible, vue_meteo
from usine.ui.detail import (
    AUCUN_KPI,
    AUCUN_RISQUE,
    INCONNUE,
    NON_PROJETABLE,
    PAS_DE_SORTIE,
    PREVISION_NON_CALCULEE_ENTITE,
    _morceaux,
    section_prevision,
    section_risque,
    texte_avec_liens,
    vue_detail,
    vue_detail_message,
)
from usine.ui.liens import lien_ticket
from usine.ui.serveur import HOTE, LectureEcrans, creer_application

SEPT = tuple(f"DEMO-{n}" for n in range(1, 8))


def _rouge() -> MeteoEntite:
    return _meteo("ENT-A", regles=(_regle(CodeIndicateur.ind_2, ("DEMO-1",)),))


# --- libelle_suite / taille_lisible ---


def test_libelle_suite_bornes() -> None:
    assert libelle_suite(1) == "+1"
    assert libelle_suite(4) == "+4"
    assert libelle_suite(0) is None
    assert libelle_suite(-2) is None


@pytest.mark.parametrize(
    ("octets", "attendu"),
    [
        (0, "0 o"),
        (1023, "1023 o"),
        (1024, "1 Ko"),
        (1047041, "1023 Ko"),
        (1048063, "1023 Ko"),
        (1048064, "1,0 Mo"),
        (1048576, "1,0 Mo"),
        (100 * 1048576, "100,0 Mo"),
    ],
)
def test_taille_lisible(octets: int, attendu: str) -> None:
    assert taille_lisible(octets) == attendu


# --- carte : première règle et « +N » ---


def test_carte_tickets_de_la_premiere_regle_et_suite() -> None:
    premiere = _regle(CodeIndicateur.ind_2, SEPT)
    seconde = _regle(CodeIndicateur.ind_3, ("AUTRE-1",))
    meteo = _meteo("ENT-B", regles=(premiere, seconde))
    ligne = carte.vue_carte(_Double(meteos=(meteo,))).lignes[0]
    assert [t.cle for t in ligne.tickets] == ["DEMO-1", "DEMO-2", "DEMO-3"]
    assert ligne.suite == "+4"


def test_carte_sans_suite_a_trois_tickets() -> None:
    meteo = _meteo("ENT-B", regles=(_regle(CodeIndicateur.ind_2, SEPT[:3]),))
    ligne = carte.vue_carte(_Double(meteos=(meteo,))).lignes[0]
    assert ligne.suite is None
    assert len(ligne.tickets) == 3


# --- _morceaux / texte_avec_liens ---


def test_morceaux_sans_citation() -> None:
    assert _morceaux("DEMO-1 texte", ()) == [("DEMO-1 texte", False)]
    assert _morceaux("DEMO-1 texte", ("",)) == [("DEMO-1 texte", False)]


def test_morceaux_cles_repetees() -> None:
    texte = "a DEMO-1 b DEMO-1 c DEMO-1 d"
    assert _morceaux(texte, ("DEMO-1",)) == [
        ("a ", False),
        ("DEMO-1", True),
        (" b ", False),
        ("DEMO-1", True),
        (" c ", False),
        ("DEMO-1", True),
        (" d", False),
    ]


def test_texte_avec_liens_cle_en_lien_reste_echappe() -> None:
    attendu = f"\\*a\\* {lien_ticket('DEMO-1', _url('DEMO-1'))} \\_b\\_"
    assert texte_avec_liens("*a* DEMO-1 _b_", ("DEMO-1",), _url) == attendu
    assert texte_avec_liens("*a* DEMO-1", (), _url) == "\\*a\\* DEMO-1"


# --- prévision ---


def test_prevision_sortie_projetee_blocs() -> None:
    prevision = _prevision(StatutPrevision.sortie_projetee, "ENT-A")
    bloc = section_prevision(_rouge(), (prevision,), True).blocs[0]
    assert bloc.titre == "Sortie du rouge estimée : 20/10/2026"
    assert bloc.sous_titre == "Facteurs explicatifs"
    assert len(bloc.sous_items) == 2
    assert bloc.items[-1] == "Méthode : baseline"


def test_prevision_sortie_projetee_sans_date_ni_facteur() -> None:
    prevision = _prevision(StatutPrevision.sortie_projetee, "ENT-A").model_copy(
        update={"date_sortie_estimee": None, "facteurs": ()}
    )
    bloc = section_prevision(_rouge(), (prevision,), True).blocs[0]
    assert bloc.titre == f"Sortie du rouge estimée : {INCONNUE}"
    assert bloc.sous_titre is None
    assert bloc.sous_items == []


def test_prevision_pas_de_sortie_et_non_projetable() -> None:
    pas = _prevision(StatutPrevision.pas_de_sortie_projetee, "ENT-A")
    bloc = section_prevision(_rouge(), (pas,), True).blocs[0]
    assert bloc.titre == PAS_DE_SORTIE
    assert bloc.items
    non = _prevision(StatutPrevision.regle_non_projetable, "ENT-A")
    bloc = section_prevision(_rouge(), (non,), True).blocs[0]
    assert bloc.titre == f"{NON_PROJETABLE} ({CodeIndicateur.ind_2.value})"
    assert not bloc.items


def test_prevision_ignore_les_autres_entites() -> None:
    autre = _prevision(StatutPrevision.sortie_projetee, "ENT-B")
    section = section_prevision(_rouge(), (autre,), True)
    assert section.message == PREVISION_NON_CALCULEE_ENTITE
    assert section.blocs == []


def test_prevision_narration_autre_entite_ou_rejetee_ignoree() -> None:
    propre = _prevision(StatutPrevision.sortie_projetee, "ENT-A")
    autre_entite = _narration(StatutControle.conforme, "ENT-B")
    rejetee = _narration(StatutControle.rejete, "ENT-A")
    for narrations in ((autre_entite,), (rejetee,), (autre_entite, rejetee)):
        blocs = section_prevision(_rouge(), (propre,), True, narrations).blocs
        assert len(blocs) == 1
        assert blocs[0].texte is None
        assert blocs[0].titre is not None
        assert blocs[0].titre.startswith("Sortie du rouge estimée")
    acceptee = _narration(StatutControle.conforme, "ENT-A")
    blocs = section_prevision(_rouge(), (propre,), True, (autre_entite, acceptee)).blocs
    assert len(blocs) == 1
    assert blocs[0].texte == acceptee.texte


# --- risque ---


def test_risque_ignore_les_autres_entites() -> None:
    verte = _meteo("ENT-B")
    section = section_risque(verte, (_risque("ENT-C"),), True)
    assert section.message == AUCUN_RISQUE
    assert section.tableau is None
    propre = section_risque(verte, (_risque("ENT-B"),), True)
    assert propre.tableau is not None
    assert len(propre.tableau.lignes) == 1
    assert propre.tableau.colonnes[0] == "Indicateur"


# --- vue_detail : défauts et messages ---


def test_vue_detail_message_palier_2() -> None:
    assert vue_detail_message("m").palier == 2


def test_vue_detail_palier_par_defaut_2() -> None:
    vue = vue_detail(_Double(), "ENT-B")
    assert vue.palier == 2
    assert vue.prevision is not None
    assert vue.explication is not None
    assert vue.explication.explications


def test_vue_detail_suite_des_tickets() -> None:
    meteo = _meteo("ENT-B", regles=(_regle(CodeIndicateur.ind_2, SEPT),))
    regle = vue_detail(_Double(meteos=(meteo,)), "ENT-B").regles[0]
    assert [t.cle for t in regle.tickets] == ["DEMO-1", "DEMO-2", "DEMO-3"]
    assert [t.cle for t in regle.tickets_suite] == list(SEPT[3:])
    assert regle.libelle_suite == "+4"


class _SansKpi(_Double):
    def kpi(self, date_arrete=None, entite=None) -> pl.DataFrame:  # type: ignore[no-untyped-def]
        return super().kpi().clear()


def test_vue_detail_aucun_kpi() -> None:
    avec = vue_detail(_Double(), "ENT-B")
    assert avec.kpi
    assert avec.aucun_kpi is None
    sans = vue_detail(_SansKpi(), "ENT-B")
    assert sans.kpi == []
    assert sans.aucun_kpi == AUCUN_KPI


# --- vues figées ---


def test_vues_figees() -> None:
    vue = vue_meteo(Couleur.vert)
    with pytest.raises(ValidationError):
        vue.libelle = "autre"  # type: ignore[misc]


# --- serveur ---


def _client_qui_leve(erreur: Exception) -> TestClient:
    def casse(_repli: bool) -> LectureEcrans:
        raise erreur

    application = creer_application(
        repli=False, lire_manifeste=lambda _repli: None, lire_consultation=casse
    )
    return TestClient(application, base_url=f"http://{HOTE}")


def test_detail_oserror_bandeau_et_non_500() -> None:
    reponse = _client_qui_leve(OSError("disque")).get("/api/entites/ENT-A")
    assert reponse.status_code == 200
    assert reponse.json()["erreur"] == "Lecture du Passage impossible : disque"
    assert reponse.json()["message"] is None


def test_routes_html_hors_schema() -> None:
    chemins = creer_application(
        repli=False,
        lire_manifeste=lambda _repli: None,
        lire_consultation=lambda _repli: _Double(),
    ).openapi()["paths"]
    assert "/api/carte" in chemins
    assert "/api/entites/{entite}" in chemins
    assert "/entites" not in chemins
    assert "/livrables/{nom}" not in chemins
