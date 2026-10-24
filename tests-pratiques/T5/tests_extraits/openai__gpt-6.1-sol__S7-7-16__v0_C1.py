from usine.contrats.llm import ReponseAgent, StatutControle
from usine.ia.agent.session import SANS_REPONSE
from usine.ui.ecrans import vue_reponse_agent


def test_refus_hors_perimetre_affiche_aucun_outil():
    reponse = ReponseAgent(
        question="Quel est le budget ?",
        texte=SANS_REPONSE,
        outils_appeles=("get_meteo",),
        statut_controle=StatutControle.conforme,
    )

    vue = vue_reponse_agent(reponse, SANS_REPONSE)

    assert vue.badge_code == "hors_perimetre"
    assert vue.outils == []
    assert vue.aucun_outil == "aucun"
