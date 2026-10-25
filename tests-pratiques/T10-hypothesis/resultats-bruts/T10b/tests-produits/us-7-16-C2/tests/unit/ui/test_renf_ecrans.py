"""Renforcement de la Story 7.16 : écrans Agent et Avant / après."""

import dataclasses
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from usine.contrats.llm import ReponseAgent, StatutControle
from usine.contrats.passage import ManifestePassage
from usine.ui import agent, avant_apres
from usine.ui.ecrans import (
    TITRE_QUESTIONS_REEL,
    TITRE_QUESTIONS_REPLI,
    GardeSession,
    ServicesEcrans,
    vue_agent,
    vue_agent_erreur,
    vue_avant_apres,
    vue_reponse_agent,
)


def _manifeste(passage_id: str = "20261012T073000Z-aaaaaa") -> ManifestePassage:
    instant = datetime(2026, 10, 12, 7, 30, tzinfo=UTC)
    return ManifestePassage(
        passage_id=passage_id,
        date_arrete=date(2026, 10, 12),
        palier=2,
        source="journal",
        horodatage_debut=instant,
        horodatage_fin=instant,
        version_grille="abc",
        version_donnees="def",
        cout_llm_eur=Decimal(0),
        nb_alignements=0,
        nb_tickets=0,
        etapes=(),
    )


class _Lecture:
    def __init__(self, passage_id: str) -> None:
        self._id = passage_id

    def manifeste(self) -> ManifestePassage:
        return _manifeste(self._id)


class _Session:
    def __init__(self, passage_id: str) -> None:
        self.passage_id = passage_id
        self.fermee = False

    def fermer(self) -> None:
        self.fermee = True

    def repondre(self, question: str) -> ReponseAgent:
        return ReponseAgent(question=question, texte=self.passage_id)


def test_services_ecrans_est_fige() -> None:
    services = ServicesEcrans(
        session_agent=lambda _c: _Session("x"),  # type: ignore[arg-type,return-value]
        reponses_repli=lambda _p: (),
        questions_suggerees=(),
        texte_hors_perimetre="h",
        apercu_pseudonymisation=lambda: str,
        config_demo=lambda: None,
        manifestes_avant_apres=lambda _b: (None, None),
        lire_fiche=lambda: None,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        services.texte_hors_perimetre = "autre"  # type: ignore[misc]


def test_garde_session_rebatit_si_passage_anterieur() -> None:
    creees: list[_Session] = []

    def fabrique(consultation: _Lecture) -> _Session:
        session = _Session(consultation.manifeste().passage_id)
        creees.append(session)
        return session

    garde = GardeSession(fabrique)  # type: ignore[arg-type]
    garde.repondre(_Lecture("20261012T073000Z-bbbbbb"), "q")  # type: ignore[arg-type]
    garde.repondre(_Lecture("20261012T073000Z-bbbbbb"), "q")  # type: ignore[arg-type]
    assert len(creees) == 1
    reponse = garde.repondre(_Lecture("20261012T073000Z-aaaaaa"), "q")  # type: ignore[arg-type]
    assert len(creees) == 2
    assert creees[0].fermee
    assert reponse.texte == "20261012T073000Z-aaaaaa"


def test_reponse_texte_superieur_au_hors_perimetre_n_est_pas_hors_perimetre() -> None:
    reponse = ReponseAgent(
        question="q", texte="zzz", statut_controle=StatutControle.non_controle
    )
    vue = vue_reponse_agent(reponse, "abc")
    assert vue.badge_code == StatutControle.non_controle.value
    exact = vue_reponse_agent(ReponseAgent(question="q", texte=" abc "), "abc")
    assert exact.badge_code == "hors_perimetre"


def test_titre_questions_selon_le_mode() -> None:
    assert vue_agent_erreur(True, "e").titre_questions == TITRE_QUESTIONS_REPLI
    assert vue_agent_erreur(False, "e").titre_questions == TITRE_QUESTIONS_REEL


def test_vue_agent_reel_sans_passage() -> None:
    services = ServicesEcrans(
        session_agent=lambda _c: _Session("x"),  # type: ignore[arg-type,return-value]
        reponses_repli=lambda _p: (),
        questions_suggerees=(),
        texte_hors_perimetre="h",
        apercu_pseudonymisation=lambda: str,
        config_demo=lambda: None,
        manifestes_avant_apres=lambda _b: (None, None),
        lire_fiche=lambda: None,
    )
    vue = vue_agent(repli=False, consultation=None, services=services)
    assert vue.mode == "reel"
    assert vue.titre_questions == TITRE_QUESTIONS_REEL
    assert vue.message == agent.AUCUN_PASSAGE


def test_avant_apres_tableau_selon_les_cartes_presentes() -> None:
    manifeste = _manifeste()
    seul_manuel = vue_avant_apres(minutes=10, mesure=None, dernier=manifeste)
    assert seul_manuel.tableau is not None
    assert seul_manuel.tableau.colonnes == ["Rapport", "Reporting manuel (déclaré)"]
    seule_chaine = vue_avant_apres(minutes=None, mesure=manifeste, dernier=manifeste)
    assert seule_chaine.tableau is not None
    assert seule_chaine.tableau.colonnes == ["Rapport", "Chaîne (mesuré)"]
    aucune = vue_avant_apres(minutes=None, mesure=None, dernier=manifeste)
    assert aucune.tableau is None
    assert avant_apres.CONFIG_ABSENTE in aucune.avertissements
