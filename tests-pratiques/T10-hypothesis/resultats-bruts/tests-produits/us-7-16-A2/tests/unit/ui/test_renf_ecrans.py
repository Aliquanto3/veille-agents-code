"""Renfort Story 7.16 : valeurs exactes et branches d'erreur des vues des quatre écrans."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import polars as pl
import pytest

from usine.contrats.erreurs import UsineErreur
from usine.contrats.llm import ReponseAgent, ReponseAgentEnregistree, StatutControle
from usine.contrats.passage import ManifestePassage
from usine.contrats.tickets import SCHEMA_TICKET_TEXTE
from usine.ui import agent, avant_apres, outillage, pseudonymisation
from usine.ui.ecrans import (
    ANNONCE_REPONSE,
    AUCUN_OUTIL,
    BADGE_HORS_PERIMETRE,
    LIEN_CHAINE,
    LIEN_REPLI,
    OUTILS_AGENT,
    REPONSE_REJETEE,
    TITRE_QUESTIONS_REEL,
    TITRE_QUESTIONS_REPLI,
    GardeSession,
    ServicesEcrans,
    SessionIndisponible,
    vue_agent,
    vue_agent_erreur,
    vue_avant_apres,
    vue_avant_apres_erreur,
    vue_outillage,
    vue_outillage_erreur,
    vue_pseudonymisation,
    vue_pseudonymisation_erreur,
    vue_pseudonymisation_message,
    vue_reponse_agent,
)

HORS_PERIMETRE = "Aucune donnée disponible pour répondre."
PA = "20261012T073000Z-aaaaaa"
PB = "20261012T073000Z-bbbbbb"
DEBUT = datetime(2026, 10, 12, 7, 30, tzinfo=UTC)


def _reponse(
    texte: str = "Réponse.",
    statut: StatutControle = StatutControle.conforme,
    outils: tuple[str, ...] = (),
) -> ReponseAgent:
    return ReponseAgent(
        question="Q ?", texte=texte, outils_appeles=outils, statut_controle=statut
    )


def _enregistree(passage_id: str = "20261012T073000Z-aaaaaa", question: str = "Q ?") -> Any:
    return ReponseAgentEnregistree(
        passage_id=passage_id,
        horodatage=datetime(2026, 10, 11, 9, 0, tzinfo=UTC),
        reponse=ReponseAgent(question=question, texte="T"),
    )


def _manifeste(secondes: float = 3.4, passage_id: str = "20261012T073000Z-aaaaaa") -> Any:
    return ManifestePassage(
        passage_id=passage_id,
        date_arrete=datetime(2026, 10, 9, tzinfo=UTC).date(),
        palier=1,
        source="journal",
        horodatage_debut=DEBUT,
        horodatage_fin=DEBUT + timedelta(seconds=secondes),
        version_grille="abc",
        version_donnees="def",
        cout_llm_eur=Decimal(0),
        nb_alignements=0,
        nb_tickets=0,
        etapes=(),
    )


class _Consultation:
    def __init__(self, textes: dict[str, str | None] | None = None, passage_id: str = PA) -> None:
        self._textes = textes or {}
        self.passage_id = passage_id

    def manifeste(self) -> Any:
        return _manifeste(passage_id=self.passage_id)

    def textes_tickets(self) -> pl.DataFrame:
        cles = list(self._textes)
        return pl.DataFrame(
            {
                "cle_ticket": cles,
                "type_ticket": ["anomalie"] * len(cles),
                "entite": ["ENT-A"] * len(cles),
                "titre": ["t"] * len(cles),
                "description": [self._textes[c] for c in cles],
            },
            schema={
                nom: (pl.Utf8() if nom != "type_ticket" else pl.Utf8())
                for nom in SCHEMA_TICKET_TEXTE.colonnes
            },
        )

    def url_ticket(self, cle: str) -> str | None:
        return f"https://jira.example.invalid/browse/{cle}"


def _services(
    repli: tuple[Any, ...] = (), suggerees: tuple[str, ...] = ("A ?", "B ?"), erreur: bool = False
) -> ServicesEcrans:
    def reponses(_passage_id: str) -> tuple[Any, ...]:
        if erreur:
            raise UsineErreur("passage étranger")
        return repli

    return ServicesEcrans(
        session_agent=lambda _c: None,  # type: ignore[arg-type, return-value]
        reponses_repli=reponses,
        questions_suggerees=suggerees,
        texte_hors_perimetre=HORS_PERIMETRE,
        apercu_pseudonymisation=lambda: str.upper,
        config_demo=lambda: None,
        manifestes_avant_apres=lambda _r: (None, None),
        lire_fiche=lambda: None,
    )


# --- vue_reponse_agent ---


def test_reponse_conforme_texte_badge_et_outils() -> None:
    vue = vue_reponse_agent(_reponse("Texte.", outils=("get_meteo", "get_risques")), HORS_PERIMETRE)
    assert vue.texte == "Texte."
    assert vue.texte_masque is None
    assert vue.badge == "Contrôle : conforme : chiffres et tickets vérifiés"
    assert vue.badge_code == "conforme"
    assert vue.outils == ["get_meteo", "get_risques"]
    assert vue.aucun_outil == AUCUN_OUTIL == "aucun"
    assert vue.libelle_outils == "Outils appelés :"
    assert vue.mention_repli is None
    assert vue.annonce == ANNONCE_REPONSE


@pytest.mark.parametrize(
    ("statut", "code"),
    [
        (StatutControle.non_controle, "non_controle"),
        (StatutControle.conforme, "conforme"),
        (StatutControle.corrige, "corrige"),
    ],
)
def test_reponse_code_du_badge_suit_le_statut(statut: StatutControle, code: str) -> None:
    vue = vue_reponse_agent(_reponse(statut=statut), HORS_PERIMETRE)
    assert vue.badge_code == code
    assert vue.texte == "Réponse."


def test_reponse_rejetee_masque_le_texte() -> None:
    vue = vue_reponse_agent(_reponse("secret 42", StatutControle.rejete), HORS_PERIMETRE)
    assert vue.texte is None
    assert vue.texte_masque == REPONSE_REJETEE
    assert vue.badge == "Contrôle : rejetée par le contrôle"
    assert vue.badge_code == "rejete"


def test_reponse_rejetee_au_texte_de_refus_reste_rejetee() -> None:
    vue = vue_reponse_agent(_reponse(HORS_PERIMETRE, StatutControle.rejete), HORS_PERIMETRE)
    assert vue.badge_code == "rejete"
    assert vue.texte is None


def test_reponse_hors_perimetre_meme_avec_espaces_autour() -> None:
    vue = vue_reponse_agent(_reponse(f"  {HORS_PERIMETRE}\n"), HORS_PERIMETRE)
    assert vue.badge_code == "hors_perimetre"
    assert vue.badge == BADGE_HORS_PERIMETRE
    assert vue.texte == f"  {HORS_PERIMETRE}\n"  # texte transmis tel quel
    assert vue.outils == []


def test_reponse_proche_du_refus_n_est_pas_hors_perimetre() -> None:
    vue = vue_reponse_agent(_reponse(HORS_PERIMETRE + " Mais"), HORS_PERIMETRE)
    assert vue.badge_code == "conforme"


def test_reponse_rejouee_porte_la_mention_repli() -> None:
    enregistree = _enregistree()
    vue = vue_reponse_agent(_reponse(), HORS_PERIMETRE, enregistree)
    assert vue.mention_repli == agent.mention_repli(enregistree)
    assert "20261012T073000Z-aaaaaa" in (vue.mention_repli or "")
    assert "11/10/2026" in (vue.mention_repli or "")


# --- vue_agent ---


def test_agent_erreur_reel_propose_le_repli() -> None:
    vue = vue_agent_erreur(False, "boom")
    assert vue.mode == "reel"
    assert vue.erreur == "boom"
    assert vue.lien_repli == LIEN_REPLI
    assert vue.message_repli is None
    assert vue.saisie is None
    assert vue.questions == []


def test_agent_erreur_repli_porte_le_message_sans_lien() -> None:
    vue = vue_agent_erreur(True, "boom")
    assert vue.mode == "repli"
    assert vue.lien_repli is None
    assert vue.message_repli == agent.MESSAGE_REPLI


def test_agent_reel_sans_passage() -> None:
    vue = vue_agent(repli=False, consultation=None, services=_services())
    assert vue.message == agent.AUCUN_PASSAGE
    assert vue.lien_message == LIEN_CHAINE
    assert vue.saisie is None
    assert vue.questions == []
    assert vue.legende is None


def test_agent_reel_saisie_suggestions_et_outils_fixes() -> None:
    vue = vue_agent(repli=False, consultation=_Consultation(), services=_services())  # type: ignore[arg-type]
    assert vue.mode == "reel"
    assert vue.saisie is not None
    assert vue.saisie.valeur_defaut == agent.QUESTION_DEMO
    assert vue.saisie.libelle == agent.LIBELLE_QUESTION
    assert vue.saisie.bouton == "Envoyer"
    assert [(q.rang, q.question) for q in vue.questions] == [(0, "A ?"), (1, "B ?")]
    assert vue.titre_questions == TITRE_QUESTIONS_REEL
    assert vue.legende == agent.LEGENDE
    assert vue.message_repli is None
    assert [o.nom for o in vue.outils] == [
        "get_meteo",
        "list_anomalies",
        "get_tendance",
        "get_prevision",
        "get_risques",
    ]
    assert tuple(vue.outils) == OUTILS_AGENT


def test_agent_repli_liste_les_questions_enregistrees_dans_l_ordre() -> None:
    services = _services((_enregistree(question="Premiere"), _enregistree(question="Seconde")))
    vue = vue_agent(repli=True, consultation=_Consultation(), services=services)  # type: ignore[arg-type]
    assert vue.mode == "repli"
    assert vue.saisie is None
    assert vue.erreur is None
    assert vue.message_repli == agent.MESSAGE_REPLI
    assert vue.titre_questions == TITRE_QUESTIONS_REPLI
    assert [(q.rang, q.question) for q in vue.questions] == [(0, "Premiere"), (1, "Seconde")]
    assert vue.legende is None


def test_agent_repli_refus_du_passage_nomme_la_cause() -> None:
    vue = vue_agent(repli=True, consultation=_Consultation(), services=_services(erreur=True))  # type: ignore[arg-type]
    assert vue.erreur == f"{agent.REFUS_REPLI} : passage étranger"
    assert vue.questions == []
    assert vue.message_repli == agent.MESSAGE_REPLI


def test_agent_repli_sans_passage_ne_lit_pas_les_reponses() -> None:
    vue = vue_agent(repli=True, consultation=None, services=_services(erreur=True))
    assert vue.erreur is None
    assert vue.questions == []
    assert vue.message_repli == agent.MESSAGE_REPLI


# --- GardeSession ---


class _Session:
    def __init__(self, passage_id: str) -> None:
        self.passage_id = passage_id
        self.fermee = 0
        self.questions: list[str] = []

    def repondre(self, question: str) -> ReponseAgent:
        self.questions.append(question)
        return _reponse(question)

    def fermer(self) -> None:
        self.fermee += 1


def test_garde_session_reutilise_puis_ferme_a_chaque_changement() -> None:
    sessions: list[_Session] = []

    def fabrique(c: Any) -> _Session:
        sessions.append(_Session(c.passage_id))
        return sessions[-1]

    garde = GardeSession(fabrique)
    a, b = _Consultation(passage_id=PA), _Consultation(passage_id=PB)
    assert garde.repondre(a, "1").texte == "1"  # type: ignore[arg-type]
    garde.repondre(a, "2")  # type: ignore[arg-type]
    assert sessions[0].questions == ["1", "2"]
    assert sessions[0].fermee == 0
    garde.repondre(b, "3")  # type: ignore[arg-type]
    garde.repondre(a, "4")  # type: ignore[arg-type]
    assert len(sessions) == 3
    assert [s.fermee for s in sessions] == [1, 1, 0]


def test_garde_session_echec_de_fabrique_puis_nouvel_essai() -> None:
    appels: list[int] = []

    def fabrique(c: Any) -> _Session:
        appels.append(1)
        if len(appels) == 1:
            raise UsineErreur("clé absente")
        return _Session(c.passage_id)

    garde = GardeSession(fabrique)
    with pytest.raises(SessionIndisponible) as info:
        garde.repondre(_Consultation(), "Q")  # type: ignore[arg-type]
    assert str(info.value) == "Agent indisponible : la session ne peut être construite (clé absente)"
    assert isinstance(info.value.__cause__, UsineErreur)
    assert garde.repondre(_Consultation(), "Q").texte == "Q"  # type: ignore[arg-type]
    assert len(appels) == 2


def test_garde_session_autre_exception_n_est_pas_masquee() -> None:
    def fabrique(_c: Any) -> _Session:
        raise ValueError("bug")

    with pytest.raises(ValueError, match="bug"):
        GardeSession(fabrique).repondre(_Consultation(), "Q")  # type: ignore[arg-type]


# --- vue_avant_apres ---


def test_avant_apres_valeurs_exactes() -> None:
    vue = vue_avant_apres(minutes=120, mesure=_manifeste(3.4), dernier=_manifeste())
    assert vue.avertissements == []
    assert vue.manuel is not None
    assert vue.manuel.titre == "Reporting manuel"
    assert vue.manuel.etiquette == "déclaré"
    assert vue.manuel.valeurs == {"rapport": "120 min", "cumul": "600 min"}
    assert vue.chaine is not None
    assert vue.chaine.titre == "Chaîne"
    assert vue.chaine.etiquette == "mesuré"
    assert vue.chaine.valeurs == {"rapport": "3,4 s", "cumul": "17 s"}
    assert vue.periode == "rapport"
    assert vue.legende == avant_apres.legende(_manifeste(3.4))
    assert [p.valeur for p in vue.periodes] == ["rapport", "cumul"]
    assert vue.periodes[1].libelle == "Cumulé sur 5 Rapports"


def test_avant_apres_tableau_deux_colonnes_de_valeurs() -> None:
    vue = vue_avant_apres(minutes=120, mesure=_manifeste(3.4), dernier=None)
    assert vue.tableau is not None
    assert vue.tableau.colonnes == ["Rapport", "Reporting manuel (déclaré)", "Chaîne (mesuré)"]
    assert vue.tableau.lignes == [
        ["Par Rapport quotidien", "120 min", "3,4 s"],
        ["Cumulé sur 5 Rapports", "600 min", "17 s"],
    ]


def test_avant_apres_grand_nombre_de_minutes_separe_les_milliers() -> None:
    vue = vue_avant_apres(minutes=1200, mesure=None, dernier=_manifeste())
    assert vue.manuel is not None
    assert vue.manuel.valeurs["rapport"].split() == ["1", "200", "min"]
    assert vue.manuel.valeurs["cumul"].split() == ["6", "000", "min"]


def test_avant_apres_zero_minute() -> None:
    vue = vue_avant_apres(minutes=0, mesure=None, dernier=_manifeste())
    assert vue.manuel is not None
    assert vue.manuel.valeurs == {"rapport": "0 min", "cumul": "0 min"}


def test_avant_apres_configuration_absente() -> None:
    vue = vue_avant_apres(minutes=None, mesure=_manifeste(2.0), dernier=_manifeste())
    assert vue.avertissements == [avant_apres.CONFIG_ABSENTE]
    assert vue.manuel is None
    assert vue.chaine is not None
    assert vue.tableau is not None
    assert vue.tableau.colonnes == ["Rapport", "Chaîne (mesuré)"]
    assert vue.tableau.lignes == [
        ["Par Rapport quotidien", "2 s"],
        ["Cumulé sur 5 Rapports", "10 s"],
    ]


def test_avant_apres_classification_initiale_seule() -> None:
    vue = vue_avant_apres(minutes=120, mesure=None, dernier=_manifeste())
    assert vue.avertissements == [avant_apres.SEULE_CLASSIFICATION_INITIALE]
    assert vue.chaine is None
    assert vue.legende is None
    assert vue.message is None
    assert vue.tableau is not None
    assert vue.tableau.colonnes == ["Rapport", "Reporting manuel (déclaré)"]
    assert vue.tableau.lignes[0] == ["Par Rapport quotidien", "120 min"]


def test_avant_apres_config_absente_et_classification_initiale() -> None:
    vue = vue_avant_apres(minutes=None, mesure=None, dernier=_manifeste())
    assert vue.avertissements == [
        avant_apres.CONFIG_ABSENTE,
        avant_apres.SEULE_CLASSIFICATION_INITIALE,
    ]
    assert vue.manuel is None
    assert vue.chaine is None
    assert vue.tableau is None


def test_avant_apres_aucun_passage_garde_la_periode() -> None:
    vue = vue_avant_apres(minutes=120, mesure=None, dernier=None, periode="cumul")
    assert vue.message == avant_apres.AUCUN_PASSAGE
    assert vue.lien_message == LIEN_CHAINE
    assert vue.periode == "cumul"
    assert vue.manuel is None
    assert vue.tableau is None
    assert vue.avertissements == []


def test_avant_apres_aucun_passage_et_config_absente_ne_garde_que_le_message() -> None:
    vue = vue_avant_apres(minutes=None, mesure=None, dernier=None)
    assert vue.message == avant_apres.AUCUN_PASSAGE
    assert vue.avertissements == []  # le retour anticipé ignore l'avertissement de config


def test_avant_apres_periode_transmise() -> None:
    assert vue_avant_apres(minutes=1, mesure=_manifeste(), dernier=None, periode="cumul").periode == (
        "cumul"
    )


def test_avant_apres_duree_sous_la_seconde() -> None:
    vue = vue_avant_apres(minutes=1, mesure=_manifeste(0.04), dernier=None)
    assert vue.chaine is not None
    assert vue.chaine.valeurs["rapport"] == "0 s"
    assert vue.chaine.valeurs["cumul"] == "0,2 s"


def test_avant_apres_erreur() -> None:
    vue = vue_avant_apres_erreur("illisible")
    assert vue.erreur == "illisible"
    assert vue.tableau is None
    assert vue.periode == "rapport"
    assert vue.libelle_periode == "Période"
    assert len(vue.periodes) == 2


# --- Pseudonymisation ---


def test_pseudonymisation_ticket_choisi_original_et_apercu() -> None:
    consultation = _Consultation({"DEMO-2": "Jean Dupont", "DEMO-1": "Marie"})
    vue = vue_pseudonymisation(consultation, lambda: str.upper, "DEMO-2")  # type: ignore[arg-type]
    assert vue.tickets == ["DEMO-1", "DEMO-2"]  # triés
    assert vue.ticket is not None
    assert vue.ticket.cle == "DEMO-2"
    assert vue.ticket.url == "https://jira.example.invalid/browse/DEMO-2"
    assert vue.original == "Jean Dupont"
    assert vue.pseudonymise == "JEAN DUPONT"
    assert vue.legende == pseudonymisation.LEGENDE
    assert vue.erreur is None
    assert vue.titre_original == "Original"
    assert vue.titre_pseudonymise == "Version pseudonymisée"
    assert vue.etiquette_pseudonymise == "envoyée au LLM"
    assert vue.libelle_ticket == "Ticket"


def test_pseudonymisation_ticket_par_defaut_est_le_premier_trie() -> None:
    consultation = _Consultation({"DEMO-9": "x", "DEMO-10": "y", "DEMO-2": "z"})
    vue = vue_pseudonymisation(consultation, lambda: str.upper, None)  # type: ignore[arg-type]
    assert vue.tickets == ["DEMO-10", "DEMO-2", "DEMO-9"]  # tri lexicographique
    assert vue.ticket is not None
    assert vue.ticket.cle == "DEMO-10"
    assert vue.original == "y"


def test_pseudonymisation_ignore_les_descriptions_vides_ou_nulles() -> None:
    consultation = _Consultation({"A-1": None, "A-2": "   ", "A-3": "", "A-4": "ok"})
    vue = vue_pseudonymisation(consultation, lambda: str.upper, None)  # type: ignore[arg-type]
    assert vue.tickets == ["A-4"]


def test_pseudonymisation_aucune_description() -> None:
    consultation = _Consultation({"A-1": None, "A-2": " \n"})
    vue = vue_pseudonymisation(consultation, lambda: str.upper, None)  # type: ignore[arg-type]
    assert vue.message == pseudonymisation.AUCUNE_DESCRIPTION
    assert vue.tickets == []
    assert vue.original is None
    assert vue.ticket is None


def test_pseudonymisation_table_vide() -> None:
    vue = vue_pseudonymisation(_Consultation(), lambda: str.upper, "X-1")  # type: ignore[arg-type]
    assert vue.message == pseudonymisation.AUCUNE_DESCRIPTION
    assert vue.erreur is None


def test_pseudonymisation_ticket_inconnu_garde_la_selection() -> None:
    appels: list[str] = []

    def fabrique() -> Any:
        appels.append("x")
        return str.upper

    consultation = _Consultation({"A-2": "b", "A-1": "a", "A-3": " "})
    vue = vue_pseudonymisation(consultation, fabrique, "A-3")  # type: ignore[arg-type]
    assert vue.erreur == "Le ticket A-3 n'a pas de description non vide dans ce Passage."
    assert vue.tickets == ["A-1", "A-2"]
    assert vue.original is None
    assert vue.pseudonymise is None
    assert appels == []  # le moteur n'est pas chargé


def test_pseudonymisation_erreur_usine_est_prefixee() -> None:
    def fabrique() -> Any:
        raise UsineErreur("USINE_CLE_PSEUDO absente")

    vue = vue_pseudonymisation(_Consultation({"A-1": "a"}), fabrique, None)  # type: ignore[arg-type]
    assert vue.erreur == "Aperçu de la Pseudonymisation impossible : USINE_CLE_PSEUDO absente"
    assert vue.tickets == ["A-1"]
    assert vue.ticket is not None
    assert vue.original is None


def test_pseudonymisation_erreur_pendant_l_apercu_est_prefixee() -> None:
    def apercu(_texte: str) -> str:
        raise UsineErreur("table verrouillée")

    vue = vue_pseudonymisation(_Consultation({"A-1": "a"}), lambda: apercu, None)  # type: ignore[arg-type]
    assert vue.erreur == "Aperçu de la Pseudonymisation impossible : table verrouillée"


def test_pseudonymisation_moteur_en_echec_nomme_la_premiere_ligne() -> None:
    def apercu(_texte: str) -> str:
        raise OSError("modèle fr_core introuvable\nligne 2")

    vue = vue_pseudonymisation(_Consultation({"A-1": "a"}), lambda: apercu, None)  # type: ignore[arg-type]
    assert vue.erreur == (
        "Moteur de Pseudonymisation indisponible (Presidio ou modèle spaCy) : "
        "OSError : modèle fr_core introuvable"
    )
    assert vue.pseudonymise is None
    assert vue.tickets == ["A-1"]


def test_pseudonymisation_original_en_texte_brut_non_modifie() -> None:
    texte = "<b>Jean</b> & co\nligne 2"
    vue = vue_pseudonymisation(_Consultation({"A-1": texte}), lambda: str.strip, None)  # type: ignore[arg-type]
    assert vue.original == texte


def test_pseudonymisation_vues_erreur_et_message() -> None:
    assert vue_pseudonymisation_erreur("e").erreur == "e"
    assert vue_pseudonymisation_erreur("e").tickets == []
    message = vue_pseudonymisation_message("m", LIEN_CHAINE)
    assert (message.message, message.lien_message) == ("m", LIEN_CHAINE)
    assert vue_pseudonymisation_message("m").lien_message is None


@pytest.mark.parametrize(
    ("exc", "attendu"),
    [
        (ValueError(), "ValueError"),
        (ValueError("  \n "), "ValueError"),
        (ValueError("\n\n première \nseconde"), "ValueError : première "),
        (KeyError("k"), "KeyError : 'k'"),
    ],
)
def test_moteur_indisponible_cause(exc: Exception, attendu: str) -> None:
    assert pseudonymisation.moteur_indisponible(exc) == (
        f"Moteur de Pseudonymisation indisponible (Presidio ou modèle spaCy) : {attendu}"
    )


def test_descriptions_ordre_de_la_table_et_texte_conserve() -> None:
    table = _Consultation({"B": " x ", "A": "y"}).textes_tickets()
    assert list(pseudonymisation.descriptions(table).items()) == [("B", " x "), ("A", "y")]


# --- Outillage ---


def test_vue_outillage_fiche_presente() -> None:
    vue = vue_outillage("# Titre\n\n## Section\n\nTexte\n")
    assert vue.erreur is None
    assert vue.message is None
    assert vue.legende == outillage.LEGENDE
    assert vue.html == outillage.rendre_fiche("# Titre\n\n## Section\n\nTexte\n")


def test_vue_outillage_fiche_absente() -> None:
    vue = vue_outillage(None)
    assert vue.message == outillage.FICHE_ABSENTE
    assert vue.html is None
    assert vue.legende is None


def test_vue_outillage_fiche_vide_est_rendue_pas_absente() -> None:
    vue = vue_outillage("")
    assert vue.message is None
    assert vue.html == ""


def test_vue_outillage_erreur() -> None:
    vue = vue_outillage_erreur("illisible")
    assert (vue.erreur, vue.message, vue.legende, vue.html) == ("illisible", None, None, None)


# --- outillage.rendre_fiche / lire_fiche ---


def test_rendre_fiche_pastilles_exactes() -> None:
    html = outillage.rendre_fiche("## S\n\n✅ a, ⚠️ b, ❌ c, ⚠ d\n")
    assert html.count('<span class="pastille pastille--oui">Oui</span>') == 1
    assert html.count('<span class="pastille pastille--surveiller">À surveiller</span>') == 2
    assert html.count('<span class="pastille pastille--non">Non</span>') == 1
    for marqueur in "✅⚠❌️":
        assert marqueur not in html


def test_rendre_fiche_titre_h1_retire_et_sections_en_cartes() -> None:
    html = outillage.rendre_fiche("# Titre écran\n\nIntro\n\n## Un\n\na\n\n## Deux\n\nb\n")
    assert "Titre écran" not in html
    assert "<h1" not in html
    assert html.count('<section class="carte carte--fiche">') == 3
    assert html.count("</section>") == 3
    assert html.startswith('<section class="carte carte--fiche"><p>Intro</p>')
    assert "<h2>Un</h2>" in html
    assert "<h2>Deux</h2>" in html


def test_rendre_fiche_sans_intro_commence_par_la_premiere_section() -> None:
    html = outillage.rendre_fiche("# T\n\n## Un\n\na\n")
    assert html.count("<section") == 1
    assert html.startswith('<section class="carte carte--fiche"><h2>Un</h2>')


def test_rendre_fiche_tableau_defilant() -> None:
    html = outillage.rendre_fiche("## S\n\n| a | b |\n|---|---|\n| ✅ | x |\n")
    assert html.count('<div class="table-defile" role="region" tabindex="0"') == 1
    assert f'aria-label="{outillage.LIBELLE_TABLEAU}"' in html
    assert html.count("</table></div>") == 1
    assert '<td><span class="pastille pastille--oui">Oui</span></td>' in html


def test_rendre_fiche_html_brut_echappe() -> None:
    html = outillage.rendre_fiche("## S\n\n<script>alert(1)</script> <img src=x onerror=y>\n")
    assert "<script>" not in html
    assert "<img" not in html
    assert "&lt;script&gt;" in html


def test_rendre_fiche_vide() -> None:
    assert outillage.rendre_fiche("") == ""
    assert outillage.rendre_fiche("# Seul titre\n") == ""


def test_pastille_dans_le_texte_en_gras_et_en_liste() -> None:
    html = outillage.rendre_fiche("## S\n\n- **✅** oui\n- ❌\n")
    assert "<strong>" in html
    assert 'pastille--oui">Oui' in html
    assert 'pastille--non">Non' in html


def test_lire_fiche_absente_presente_et_bom(tmp_path: Any) -> None:
    assert outillage.lire_fiche(tmp_path) is None
    fichier = tmp_path / outillage.FICHIER_FICHE
    fichier.parent.mkdir(parents=True)
    fichier.write_bytes("﻿# Fiche é\n".encode())
    assert outillage.lire_fiche(tmp_path) == "# Fiche é\n"


def test_lire_fiche_non_utf8_remonte(tmp_path: Any) -> None:
    fichier = tmp_path / outillage.FICHIER_FICHE
    fichier.parent.mkdir(parents=True)
    fichier.write_bytes(b"\xff\xfe\x00bad\xc3(")
    with pytest.raises(UnicodeDecodeError):
        outillage.lire_fiche(tmp_path)


def test_lire_fiche_repertoire_remonte_oserror(tmp_path: Any) -> None:
    (tmp_path / outillage.FICHIER_FICHE).mkdir(parents=True)
    with pytest.raises(OSError):  # noqa: PT011
        outillage.lire_fiche(tmp_path)


def test_messages_outillage_citent_le_fichier() -> None:
    assert "docs/fiche-outillage.md" in outillage.FICHE_ABSENTE
    assert "docs/fiche-outillage.md" in outillage.LEGENDE
