"""Renforcement Story 7.14 : bornes, branches et valeurs exactes (mutations survivantes)."""

from datetime import date

import polars as pl
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from tests.unit.ui.test_detail import (
    _meteo,
    _narration,
    _prevision,
    _regle,
    _risque,
)
from tests.unit.ui.test_vues_ecrans import _Double, _url, client
from usine.contrats.llm import StatutControle
from usine.contrats.meteo import CodeIndicateur, MeteoEntite
from usine.contrats.prevision import StatutPrevision
from usine.ui import carte, detail
from usine.ui.detail import (
    AUCUN_KPI,
    NON_PROJETABLE,
    PAS_DE_SORTIE,
    PREVISION_NON_CALCULEE_ENTITE,
    RISQUE_SANS_OBJET,
    _morceaux,
    section_prevision,
    section_risque,
    texte_avec_liens,
    vue_detail,
    vue_detail_message,
)
from usine.ui.liens import lien_ticket
from usine.ui.serveur import HOTE, LectureEcrans, creer_application


def _rouge(entite: str = "ENT-A") -> MeteoEntite:
    return _meteo(entite, regles=(_regle(CodeIndicateur.ind_2, ("DEMO-1",)),))


# --- carte.py ---


def test_libelle_suite_un_seul_reste() -> None:  # M1
    assert carte.libelle_suite(1) == "+1"
    assert carte.libelle_suite(0) is None
    assert carte.libelle_suite(-2) is None


def test_taille_lisible_bornes() -> None:  # M2, M3, M4
    assert carte.taille_lisible(1023) == "1023 o"
    assert carte.taille_lisible(1024) == "1 Ko"
    assert carte.taille_lisible(1_047_500) == "1023 Ko"
    assert carte.taille_lisible(104_857_600) == "100,0 Mo"


def test_carte_premiere_regle_et_suite_exacte() -> None:  # M5, M6
    sept = tuple(f"DEMO-{n}" for n in range(1, 8))
    meteo = _meteo(
        "ENT-B",
        regles=(
            _regle(CodeIndicateur.ind_2, sept),
            _regle(CodeIndicateur.ind_3, ("AUTRE-1",)),
        ),
    )
    ligne = client(_Double(meteos=(meteo,))).get("/api/carte").json()["lignes"][0]
    assert [t["cle"] for t in ligne["tickets"]] == ["DEMO-1", "DEMO-2", "DEMO-3"]
    assert ligne["suite"] == "+4"


def test_vue_detail_suite_exacte() -> None:  # M31
    sept = tuple(f"DEMO-{n}" for n in range(1, 8))
    meteo = _meteo("ENT-B", regles=(_regle(CodeIndicateur.ind_2, sept),))
    vue = vue_detail(_Double(meteos=(meteo,)), "ENT-B")
    assert vue.regles[0].libelle_suite == "+4"
    assert len(vue.regles[0].tickets_suite) == 4


# --- detail.py : découpage et liens ---


def test_morceaux_sans_citation() -> None:  # M8
    assert _morceaux("ENT-A bloque", ()) == [("ENT-A bloque", False)]
    assert texte_avec_liens("a_b", (), _url) == "a\\_b"


def test_morceaux_plusieurs_cles() -> None:  # M9
    assert _morceaux("DEMO-1 et DEMO-2", ("DEMO-1", "DEMO-2")) == [
        ("", False),
        ("DEMO-1", True),
        (" et ", False),
        ("DEMO-2", True),
        ("", False),
    ]


def test_texte_avec_liens_cle_liee_et_reste_echappe() -> None:  # M10
    attendu = f"a\\_b {lien_ticket('DEMO-1', _url('DEMO-1'))} c\\_d"
    assert texte_avec_liens("a_b DEMO-1 c_d", ("DEMO-1",), _url) == attendu
    assert texte_avec_liens("a_b DEMO-1", ("DEMO-1",), lambda _c: None) == "a\\_b DEMO-1"


# --- detail.py : Prévision ---


def _section(prevision, meteo=None, narrations=()):  # noqa: ANN001, ANN202
    return section_prevision(meteo or _rouge(), (prevision,), True, narrations)


def test_bloc_prevision_sortie_projetee() -> None:  # M11, M12, M13
    bloc = _section(_prevision(StatutPrevision.sortie_projetee)).blocs[0]
    assert bloc.titre == "Sortie du rouge estimée : 20/10/2026"
    assert bloc.sous_titre == "Facteurs explicatifs"
    assert len(bloc.sous_items) == 2
    sans_date = _prevision(StatutPrevision.sortie_projetee).model_copy(
        update={"date_sortie_estimee": None, "facteurs": ()}
    )
    bloc = _section(sans_date).blocs[0]
    assert bloc.titre == f"Sortie du rouge estimée : {carte.INCONNUE}"
    assert bloc.sous_titre is None
    assert bloc.sous_items == []


def test_bloc_prevision_autres_statuts() -> None:  # M11, M14
    bloc = _section(_prevision(StatutPrevision.pas_de_sortie_projetee)).blocs[0]
    assert bloc.titre == PAS_DE_SORTIE
    assert bloc.items
    bloc = _section(_prevision(StatutPrevision.regle_non_projetable)).blocs[0]
    assert bloc.titre == f"{NON_PROJETABLE} (IND-2)"
    assert bloc.items == []


def test_section_prevision_filtre_entite_et_narration() -> None:  # M16, M17
    autre = _prevision(StatutPrevision.sortie_projetee, "ENT-Z")
    assert section_prevision(_rouge("ENT-A"), (autre,), True).message == (
        PREVISION_NON_CALCULEE_ENTITE
    )
    propre = _prevision(StatutPrevision.sortie_projetee, "ENT-A")
    etrangere = _narration(StatutControle.conforme, "ENT-Z")
    section = section_prevision(_rouge("ENT-A"), (propre,), True, (etrangere,))
    assert section.blocs[0].texte is None
    assert section.blocs[0].titre.startswith("Sortie du rouge estimée")
    rejetee = _narration(StatutControle.rejete, "ENT-A")
    section = section_prevision(_rouge("ENT-A"), (propre,), True, (rejetee,))
    assert section.blocs[0].texte is None


# --- detail.py : Risque ---


def test_section_risque_filtre_entite() -> None:  # M19
    section = section_risque(_meteo("ENT-A"), (_risque("ENT-Z"),), True)
    assert section.message == detail.AUCUN_RISQUE
    assert section.tableau is None
    assert section_risque(_rouge(), (_risque("ENT-A"),), True).message == RISQUE_SANS_OBJET
    propre = section_risque(_meteo("ENT-A"), (_risque("ENT-A"), _risque("ENT-Z")), True)
    assert propre.tableau is not None
    assert len(propre.tableau.lignes) == 1


# --- detail.py : vue_detail ---


def test_vue_detail_message_palier_2() -> None:  # M26
    assert vue_detail_message("x").palier == 2


def test_vue_detail_palier_par_defaut_2() -> None:  # M27
    vue = vue_detail(_Double(), "ENT-B")
    assert vue.palier == 2
    assert vue.prevision is not None
    assert vue.explication is not None
    assert vue.explication.explications


def test_vue_detail_aucun_kpi() -> None:  # M32
    class _SansKpi(_Double):
        def kpi(self, date_arrete: date | None = None, entite: str | None = None) -> pl.DataFrame:
            return super().kpi().clear()

    vue = vue_detail(_SansKpi(), "ENT-B")
    assert vue.kpi == []
    assert vue.aucun_kpi == AUCUN_KPI
    avec = vue_detail(_Double(), "ENT-B")
    assert avec.aucun_kpi is None
    assert len(avec.kpi) == 2


# --- vues.py ---


def test_vues_immuables() -> None:  # M33
    vue = carte.vue_carte_message("x")
    with pytest.raises(ValidationError):
        vue.message = "y"


# --- serveur.py ---


def test_detail_lecture_impossible_oserror() -> None:  # M35
    def illisible(_repli: bool) -> LectureEcrans:
        raise PermissionError(13, "accès refusé", "sorties/passages")

    http = TestClient(
        creer_application(repli=False, lire_manifeste=lambda _r: None, lire_consultation=illisible),
        base_url=f"http://{HOTE}",
    )
    reponse = http.get("/api/entites/ENT-A")
    assert reponse.status_code == 200
    assert reponse.json()["erreur"].startswith("Lecture du Passage impossible")
    assert reponse.json()["message"] is None


def test_routes_hors_schema() -> None:  # M36, M38
    application = creer_application(
        repli=False, lire_manifeste=lambda _r: None, lire_consultation=lambda _r: None
    )
    chemins = application.openapi()["paths"]
    assert "/entites" not in chemins
    assert "/livrables/{nom}" not in chemins
    assert "/api/carte" in chemins
