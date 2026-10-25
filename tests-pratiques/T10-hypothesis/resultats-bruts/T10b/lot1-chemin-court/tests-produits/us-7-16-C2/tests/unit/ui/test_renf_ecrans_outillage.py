"""Renfort de la Story 7.16 : GardeSession, badges, modes de l'Agent, tableau, rendu de la fiche."""

from dataclasses import FrozenInstanceError
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from usine.contrats.llm import ReponseAgent, StatutControle
from usine.ui import agent, outillage
from usine.ui.ecrans import (
    TITRE_QUESTIONS_REEL,
    GardeSession,
    ServicesEcrans,
    vue_agent,
    vue_avant_apres,
    vue_reponse_agent,
)


def _services() -> ServicesEcrans:
    return ServicesEcrans(
        session_agent=MagicMock(),
        reponses_repli=MagicMock(),
        questions_suggerees=(),
        texte_hors_perimetre="x",
        apercu_pseudonymisation=MagicMock(),
        config_demo=MagicMock(),
        manifestes_avant_apres=MagicMock(),
        lire_fiche=MagicMock(),
    )


def test_services_ecrans_immuable() -> None:
    services = _services()
    with pytest.raises(FrozenInstanceError):
        cast(Any, services).texte_hors_perimetre = "autre"


class _Session:
    def __init__(self, passage_id: str) -> None:
        self.passage_id = passage_id
        self.fermee = False

    def repondre(self, question: str) -> ReponseAgent:
        return ReponseAgent(question=question, texte=self.passage_id)

    def fermer(self) -> None:
        self.fermee = True


def test_garde_session_rebatie_quand_le_passage_change_vers_un_id_plus_petit() -> None:
    creees: list[_Session] = []

    def fabrique(consultation: Any) -> _Session:
        session = _Session(consultation.manifeste().passage_id)
        creees.append(session)
        return session

    def consultation(passage_id: str) -> Any:
        return SimpleNamespace(manifeste=lambda: SimpleNamespace(passage_id=passage_id))

    garde = GardeSession(fabrique)
    assert garde.repondre(consultation("p-2"), "q").texte == "p-2"
    assert garde.repondre(consultation("p-2"), "q").texte == "p-2"
    assert len(creees) == 1
    assert garde.repondre(consultation("p-1"), "q").texte == "p-1"
    assert len(creees) == 2
    assert creees[0].fermee
    assert not creees[1].fermee


def test_badge_hors_perimetre_seulement_si_texte_egal() -> None:
    hors = "Hors périmètre"
    egal = vue_reponse_agent(ReponseAgent(question="q", texte=f" {hors} "), hors)
    assert egal.badge_code == "hors_perimetre"
    superieur = vue_reponse_agent(ReponseAgent(question="q", texte="Zzz"), hors)
    assert superieur.badge_code == StatutControle.non_controle.value
    inferieur = vue_reponse_agent(ReponseAgent(question="q", texte="Aaa"), hors)
    assert inferieur.badge_code == StatutControle.non_controle.value


def test_vue_agent_repli_sans_passage_titre_et_mode() -> None:
    vue = vue_agent(repli=True, consultation=None, services=_services())
    assert vue.mode == "repli"
    assert vue.titre_questions == agent.LIBELLE_CHOIX
    assert vue.titre_questions != TITRE_QUESTIONS_REEL


def test_vue_agent_reel_sans_passage_est_en_mode_reel() -> None:
    vue = vue_agent(repli=False, consultation=None, services=_services())
    assert vue.mode == "reel"
    assert vue.titre_questions == TITRE_QUESTIONS_REEL
    assert vue.message == agent.AUCUN_PASSAGE


def test_avant_apres_sans_config_ni_mesure_n_a_pas_de_tableau() -> None:
    vue = vue_avant_apres(minutes=None, mesure=None, dernier=cast(Any, MagicMock()))
    assert vue.tableau is None
    assert vue.manuel is None
    assert vue.chaine is None
    assert len(vue.avertissements) == 2


def test_fiche_titre_h1_retire_en_entier() -> None:
    html = outillage.rendre_fiche("# Titre unique\n\n## Section\n\ntexte\n")
    assert "Titre unique" not in html
    assert "h1" not in html
    assert "<h2>Section</h2>" in html


def test_fiche_premier_jeton_non_titre_conserve() -> None:
    html = outillage.rendre_fiche("Intro\n\n## Section\n")
    assert "<p>Intro</p>" in html


def test_fiche_marqueurs_rendus_en_pastilles() -> None:
    html = outillage.rendre_fiche("## S\n\navant ✅ milieu ⚠️ fin ❌\n")
    assert '<span class="pastille pastille--oui">Oui</span>' in html
    assert '<span class="pastille pastille--surveiller">À surveiller</span>' in html
    assert '<span class="pastille pastille--non">Non</span>' in html
    assert "avant " in html
    assert " milieu " in html
    assert " fin " in html


def test_fiche_jetons_non_texte_conserves_avant_une_pastille() -> None:
    html = outillage.rendre_fiche("## S\n\n**gras** ✅ fin `code ✅`\n")
    assert "<strong>gras</strong>" in html
    assert 'pastille--oui">Oui</span> fin ' in html
    assert "<code>code ✅</code>" in html
