"""Renfort de la Story 7.14 : bornes, branches et contrats des vues Carte et Détail."""

from datetime import date
from fractions import Fraction

import polars as pl
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from tests.unit.ui.test_detail import _meteo, _narration, _prevision, _regle, _risque
from tests.unit.ui.test_vues_ecrans import _Double, _url, client
from usine.contrats.format import formater_date, formater_pourcentage
from usine.contrats.llm import StatutControle
from usine.contrats.meteo import CodeIndicateur, Couleur
from usine.contrats.prevision import StatutPrevision
from usine.ui import carte, detail
from usine.ui.detail import (
    _bloc_une_prevision,
    _morceaux,
    section_prevision,
    section_risque,
    texte_avec_liens,
    vue_detail,
    vue_detail_message,
)
from usine.ui.serveur import HOTE, LectureEcrans, creer_application

SIX = tuple(f"DEMO-{n}" for n in range(1, 7))
ROUGE_A = _meteo("ENT-A", regles=(_regle(CodeIndicateur.ind_2, ("DEMO-1",)),))


def test_libelle_suite_un_seul_reste() -> None:
    assert carte.libelle_suite(1) == "+1"
    assert carte.libelle_suite(0) is None
    assert carte.libelle_suite(-2) is None


def test_taille_lisible_bornes() -> None:
    assert carte.taille_lisible(1023) == "1023 o"
    assert carte.taille_lisible(1024) == "1 Ko"
    assert carte.taille_lisible(1_047_500) == "1023 Ko"
    assert carte.taille_lisible(104_857_600) == "100,0 Mo"


def _double_deux_regles(tickets: tuple[str, ...]) -> _Double:
    regles = (
        _regle(CodeIndicateur.ind_2, tickets),
        _regle(CodeIndicateur.ind_3, ("AUTRE-1",)),
    )
    return _Double(meteos=(_meteo("ENT-B", regles=regles),))


def test_carte_tickets_de_la_premiere_regle_seulement() -> None:
    vue = client(_double_deux_regles(("DEMO-1", "DEMO-2"))).get("/api/carte").json()
    (ligne,) = vue["lignes"]
    assert [t["cle"] for t in ligne["tickets"]] == ["DEMO-1", "DEMO-2"]
    assert ligne["suite"] is None


def test_carte_suite_six_tickets() -> None:
    (ligne,) = client(_double_deux_regles(SIX)).get("/api/carte").json()["lignes"]
    assert len(ligne["tickets"]) == 3
    assert ligne["suite"] == "+3"


def test_detail_suite_six_tickets() -> None:
    vue = vue_detail(_double_deux_regles(SIX), "ENT-B")
    assert vue.regles[0].libelle_suite == "+3"
    assert [t.cle for t in vue.regles[0].tickets_suite] == ["DEMO-4", "DEMO-5", "DEMO-6"]
    court = vue_detail(_double_deux_regles(SIX[:2]), "ENT-B")
    assert court.regles[0].libelle_suite is None
    assert court.regles[0].tickets_suite == []


def test_morceaux_sans_citation() -> None:
    assert _morceaux("texte DEMO-1", ()) == [("texte DEMO-1", False)]
    assert _morceaux("texte DEMO-1", ("",)) == [("texte DEMO-1", False)]


def test_morceaux_plusieurs_cles() -> None:
    assert _morceaux("DEMO-1 et DEMO-2 fin", ("DEMO-1", "DEMO-2")) == [
        ("", False),
        ("DEMO-1", True),
        (" et ", False),
        ("DEMO-2", True),
        (" fin", False),
    ]


def test_texte_avec_liens_cles_liees_et_reste_echappe() -> None:
    texte = texte_avec_liens("a_b DEMO-1 (x)", ("DEMO-1",), _url)
    assert texte == f"a\\_b [DEMO-1]({_url('DEMO-1')}) \\(x\\)"


def test_bloc_prevision_sortie_projetee() -> None:
    prevision = _prevision(StatutPrevision.sortie_projetee)
    bloc = _bloc_une_prevision(prevision)
    assert bloc.titre == f"Sortie du rouge estimée : {formater_date(date(2026, 10, 20))}"
    assert bloc.sous_titre == "Facteurs explicatifs"
    assert len(bloc.sous_items) == 2
    assert bloc.items[-1] == "Méthode : baseline"
    sans = _bloc_une_prevision(
        prevision.model_copy(update={"facteurs": (), "date_sortie_estimee": None})
    )
    assert sans.titre == f"Sortie du rouge estimée : {carte.INCONNUE}"
    assert sans.sous_titre is None
    assert sans.sous_items == []


def test_bloc_prevision_pas_de_sortie_et_non_projetable() -> None:
    pas = _bloc_une_prevision(_prevision(StatutPrevision.pas_de_sortie_projetee))
    assert pas.titre == detail.PAS_DE_SORTIE
    probabilite = formater_pourcentage(Fraction(3, 4))
    assert pas.items == [
        f"Probabilité de sortie dans l'horizon : {probabilite}",
        "Horizon : 10 jours ouvrés",
    ]
    non = _bloc_une_prevision(_prevision(StatutPrevision.regle_non_projetable))
    assert non.titre == f"{detail.NON_PROJETABLE} (IND-2)"
    assert non.items == []


def test_section_prevision_ignore_les_autres_entites() -> None:
    section = section_prevision(
        ROUGE_A, (_prevision(StatutPrevision.sortie_projetee, "ENT-B"),), True
    )
    assert section.message == detail.PREVISION_NON_CALCULEE_ENTITE
    assert section.blocs == []


def test_section_prevision_narration_autre_entite_ou_rejetee_ignoree() -> None:
    previsions = (_prevision(StatutPrevision.sortie_projetee, "ENT-A"),)
    autre = (_narration(StatutControle.conforme, "ENT-B"),)
    rejetee = (_narration(StatutControle.rejete, "ENT-A"),)
    for narrations in (autre, rejetee):
        section = section_prevision(ROUGE_A, previsions, True, narrations)
        assert section.message is None
        assert len(section.blocs) == 1
        assert section.blocs[0].texte is None
        assert section.blocs[0].titre.startswith("Sortie du rouge estimée")


def test_section_risque_ignore_les_autres_entites() -> None:
    section = section_risque(_meteo("ENT-A"), (_risque("ENT-B"),), True)
    assert section.message == detail.AUCUN_RISQUE
    assert section.tableau is None


def test_section_risque_tableau_propre_a_l_entite() -> None:
    section = section_risque(_meteo("ENT-B"), (_risque("ENT-A"), _risque("ENT-B")), True)
    assert section.message is None
    assert section.tableau is not None
    assert len(section.tableau.lignes) == 1
    assert section.tableau.lignes[0][0] == "IND-1"


def test_palier_par_defaut_deux() -> None:
    assert vue_detail_message("x").palier == 2
    assert vue_detail(_Double(), "ENT-B").palier == 2
    assert vue_detail(_Double(), "ENT-B", 1).palier == 1


class _SansKpi(_Double):
    def kpi(self, date_arrete: date | None = None, entite: str | None = None) -> pl.DataFrame:
        schema = {
            "date": pl.Date,
            "perimetre": pl.String,
            "code_kpi": pl.String,
            "dimension": pl.String,
            "numerateur": pl.Int64,
            "denominateur": pl.Int64,
        }
        return pl.DataFrame(schema=schema)


def test_aucun_kpi() -> None:
    sans = vue_detail(_SansKpi(), "ENT-B")
    assert sans.kpi == []
    assert sans.aucun_kpi == detail.AUCUN_KPI
    avec = vue_detail(_Double(), "ENT-B")
    assert avec.aucun_kpi is None
    assert len(avec.kpi) == 2


def test_vues_immuables() -> None:
    vue = carte.vue_meteo(Couleur.rouge)
    with pytest.raises(ValidationError):
        vue.libelle = "autre"  # type: ignore[misc]


def test_detail_oserror_devient_bandeau_d_erreur() -> None:
    def illisible(_repli: bool) -> LectureEcrans:
        raise PermissionError(13, "accès refusé", "sorties/passages")

    application = creer_application(
        repli=False, lire_manifeste=lambda _r: None, lire_consultation=illisible
    )
    reponse = TestClient(application, base_url=f"http://{HOTE}").get("/api/entites/ENT-A")
    assert reponse.status_code == 200
    assert reponse.json()["erreur"].startswith("Lecture du Passage impossible : ")
    assert reponse.json()["message"] is None


def test_routes_internes_hors_schema() -> None:
    application = creer_application(
        repli=False, lire_manifeste=lambda _r: None, lire_consultation=lambda _r: _Double()
    )
    chemins = application.openapi()["paths"]
    assert "/entites" not in chemins
    assert "/livrables/{nom}" not in chemins
    assert "/api/carte" in chemins
