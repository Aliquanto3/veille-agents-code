from usine.contrats.llm import ReponseAgent, StatutControle
from usine.ui.ecrans import vue_reponse_agent


def test_refus_hors_perimetre_ne_declare_aucun_outil() -> None:
    reponse = ReponseAgent(
        question="Budget ?",
        texte="SANS_REPONSE",
        outils_appeles=("get_meteo",),
        statut_controle=StatutControle.conforme,
    )

    vue = vue_reponse_agent(reponse, "SANS_REPONSE")

    assert vue.badge_code == "hors_perimetre"
    assert vue.outils == []
    assert vue.aucun_outil == "aucun"
