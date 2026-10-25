"""Renfort Story 7.16 : session de l'Agent, vues Agent et Avant / après (valeurs exactes)."""

import dataclasses
from types import SimpleNamespace
from typing import Any

import pytest

from tests.unit.ui.test_avant_apres import manifeste
from usine.contrats.llm import ReponseAgent, StatutControle
from usine.ui import agent
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


class _Session:
    def __init__(self, passage_id: str) -> None:
        self.passage_id = passage_id
        self.fermee = False

    def repondre(self, question: str) -> ReponseAgent:
        return ReponseAgent(question=question, texte=self.passage_id)

    def fermer(self) -> None:
        self.fermee = True


def _consultation(passage_id: str) -> Any:
    return SimpleNamespace(manifeste=lambda: SimpleNamespace(passage_id=passage_id))


def test_services_ecrans_est_fige() -> None:
    services = ServicesEcrans(
        session_agent=lambda _c: _Session("a"),
        reponses_repli=lambda _p: (),
        questions_suggerees=(),
        texte_hors_perimetre="x",
        apercu_pseudonymisation=lambda: str,
        config_demo=lambda: None,
        manifestes_avant_apres=lambda _b: (None, None),
        lire_fiche=lambda: None,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        services.texte_hors_perimetre = "y"  # type: ignore[misc]


def test_garde_session_rebatit_quand_le_passage_precedent_est_plus_grand() -> None:
    creees: list[_Session] = []

    def fabrique(consultation: Any) -> _Session:
        session = _Session(consultation.manifeste().passage_id)
        creees.append(session)
        return session

    garde = GardeSession(fabrique)
    garde.repondre(_consultation("b"), "q")
    reponse = garde.repondre(_consultation("a"), "q")
    assert reponse.texte == "a"
    assert creees[0].fermee is True
    assert len(creees) == 2


def test_garde_session_garde_la_session_du_meme_passage() -> None:
    creees: list[_Session] = []

    def fabrique(consultation: Any) -> _Session:
        creees.append(_Session(consultation.manifeste().passage_id))
        return creees[-1]

    garde = GardeSession(fabrique)
    garde.repondre(_consultation("b"), "q")
    garde.repondre(_consultation("b"), "q")
    assert len(creees) == 1
    assert creees[0].fermee is False


def test_reponse_texte_different_du_hors_perimetre_n_est_pas_hors_perimetre() -> None:
    reponse = ReponseAgent(question="q", texte="zzz", statut_controle=StatutControle.conforme)
    assert vue_reponse_agent(reponse, "aaa").badge_code == "conforme"
    egale = vue_reponse_agent(reponse.model_copy(update={"texte": " aaa "}), "aaa")
    assert egale.badge_code == "hors_perimetre"


def test_titre_des_questions_selon_le_mode() -> None:
    assert vue_agent_erreur(True, "e").titre_questions == TITRE_QUESTIONS_REPLI
    assert vue_agent_erreur(False, "e").titre_questions == TITRE_QUESTIONS_REEL


def test_agent_sans_passage_en_mode_reel() -> None:
    vue = vue_agent(repli=False, consultation=None, services=object())  # type: ignore[arg-type]
    assert vue.mode == "reel"
    assert vue.titre_questions == TITRE_QUESTIONS_REEL
    assert vue.message == agent.AUCUN_PASSAGE


def test_avant_apres_sans_rien_a_comparer_n_a_pas_de_tableau() -> None:
    vue = vue_avant_apres(minutes=None, mesure=None, dernier=manifeste())
    assert vue.tableau is None
    assert vue.manuel is None
    assert vue.chaine is None


def test_avant_apres_avec_declare_seul_a_un_tableau() -> None:
    vue = vue_avant_apres(minutes=30, mesure=None, dernier=manifeste())
    assert vue.tableau is not None
    assert vue.tableau.colonnes == ["Rapport", "Reporting manuel (déclaré)"]
