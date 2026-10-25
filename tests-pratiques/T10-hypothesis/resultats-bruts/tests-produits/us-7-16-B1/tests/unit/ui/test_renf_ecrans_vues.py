"""Renfort Story 7.16 : vues pures de `ui/ecrans.py` (valeurs exactes, bornes, erreurs)."""

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import polars as pl
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from usine.contrats.erreurs import UsineErreur
from usine.contrats.format import formater_entier
from usine.contrats.llm import ReponseAgent, ReponseAgentEnregistree, StatutControle
from usine.contrats.passage import ManifestePassage
from usine.ui import agent, avant_apres, pseudonymisation
from usine.ui.ecrans import (
    ANNONCE_REPONSE,
    AUCUN_OUTIL,
    BADGE_HORS_PERIMETRE,
    LIBELLE_OUTILS,
    LIEN_CHAINE,
    LIEN_REPLI,
    OUTILS_AGENT,
    PERIODES,
    REPONSE_REJETEE,
    SERVICES_ABSENTS,
    GardeSession,
    ServicesEcrans,
    SessionIndisponible,
    vue_agent,
    vue_agent_erreur,
    vue_avant_apres,
    vue_outillage,
    vue_outillage_erreur,
    vue_pseudonymisation,
    vue_pseudonymisation_erreur,
    vue_pseudonymisation_message,
    vue_reponse_agent,
)
from usine.ui.vues import DemandeQuestion

HORS_PERIMETRE = "Je ne peux pas répondre : hors périmètre."
INSTANT = datetime(2026, 10, 12, 7, 30, tzinfo=UTC)


def _manifeste(passage_id: str = "20261012T073000Z-aaaaaa", duree_s: float = 0.0) -> ManifestePassage:
    return ManifestePassage(
        passage_id=passage_id,
        date_arrete=date(2026, 10, 9),
        palier=2,
        source="journal",
        horodatage_debut=INSTANT,
        horodatage_fin=INSTANT + timedelta(seconds=duree_s),
        version_grille="abc",
        version_donnees="def",
        cout_llm_eur=Decimal(0),
        nb_alignements=0,
        nb_tickets=0,
        etapes=(),
    )


def _reponse(
    texte: str = "Réponse.",
    statut: StatutControle = StatutControle.conforme,
    outils: tuple[str, ...] = (),
) -> ReponseAgent:
    return ReponseAgent(question="Q ?", texte=texte, outils_appeles=outils, statut_controle=statut)


class _Consultation:
    def __init__(self, textes: dict[str, str | None] | None = None, passage: str | None = None):
        self._textes = textes or {}
        self._passage = passage or "20261012T073000Z-aaaaaa"

    def manifeste(self) -> ManifestePassage:
        return _manifeste(self._passage)

    def textes_tickets(self) -> pl.DataFrame:
        return pl.DataFrame(
            {"cle_ticket": list(self._textes), "description": list(self._textes.values())},
            schema={"cle_ticket": pl.String, "description": pl.String},
        )

    def url_ticket(self, cle: str) -> str | None:
        return f"https://jira.example.invalid/browse/{cle}"


def _services(**surcharges: object) -> ServicesEcrans:
    base: dict[str, object] = {
        "session_agent": lambda _c: pytest.fail("session non attendue"),
        "reponses_repli": lambda _p: (),
        "questions_suggerees": ("A ?", "B ?"),
        "texte_hors_perimetre": HORS_PERIMETRE,
        "apercu_pseudonymisation": lambda: (lambda t: t.upper()),
        "config_demo": lambda: None,
        "manifestes_avant_apres": lambda _r: (None, None),
        "lire_fiche": lambda: None,
    }
    return ServicesEcrans(**(base | surcharges))  # type: ignore[arg-type]


# --- Réponse de l'Agent ---


@pytest.mark.parametrize("statut", list(StatutControle))
def test_badge_selon_statut(statut: StatutControle) -> None:
    vue = vue_reponse_agent(_reponse("Un texte.", statut), HORS_PERIMETRE)
    assert vue.badge_code == statut.value
    assert vue.badge == agent.texte_statut(_reponse(statut=statut))
    assert vue.libelle_outils == LIBELLE_OUTILS
    assert vue.aucun_outil == AUCUN_OUTIL
    assert vue.annonce == ANNONCE_REPONSE
    assert vue.mention_repli is None
    if statut is StatutControle.rejete:
        assert vue.texte is None
        assert vue.texte_masque == REPONSE_REJETEE
    else:
        assert vue.texte == "Un texte."
        assert vue.texte_masque is None


def test_refus_hors_perimetre_et_outils() -> None:
    vue = vue_reponse_agent(_reponse(f"  {HORS_PERIMETRE}\n"), HORS_PERIMETRE)
    assert vue.badge == BADGE_HORS_PERIMETRE
    assert vue.badge_code == "hors_perimetre"
    assert vue.outils == []
    avec = vue_reponse_agent(_reponse(outils=("get_meteo", "get_risques")), HORS_PERIMETRE)
    assert avec.outils == ["get_meteo", "get_risques"]


def test_rejet_au_texte_de_refus_reste_rejete() -> None:
    vue = vue_reponse_agent(_reponse(HORS_PERIMETRE, StatutControle.rejete), HORS_PERIMETRE)
    assert vue.badge_code == "rejete"
    assert vue.texte is None
    assert vue.badge != BADGE_HORS_PERIMETRE


def test_mention_repli_de_la_reponse_rejouee() -> None:
    enregistree = ReponseAgentEnregistree(
        passage_id="20261012T073000Z-aaaaaa", horodatage=INSTANT, reponse=_reponse()
    )
    vue = vue_reponse_agent(enregistree.reponse, HORS_PERIMETRE, enregistree)
    assert vue.mention_repli == (
        "Mode repli : réponse enregistrée le 12/10/2026 sur le Passage"
        " 20261012T073000Z-aaaaaa, rejouée sans LLM"
    )


@given(texte=st.text(max_size=80), statut=st.sampled_from(list(StatutControle)))
def test_propriete_texte_rejete_jamais_envoye(texte: str, statut: StatutControle) -> None:
    vue = vue_reponse_agent(_reponse(texte, statut), HORS_PERIMETRE)
    if statut is StatutControle.rejete:
        assert vue.texte is None and vue.texte_masque == REPONSE_REJETEE
    else:
        assert vue.texte == texte and vue.texte_masque is None
    assert (vue.badge_code == "hors_perimetre") == (
        statut is not StatutControle.rejete and texte.strip() == HORS_PERIMETRE
    )


# --- Question ---


def test_demande_question_bornes() -> None:
    assert DemandeQuestion(question="  a  ").question == "a"
    assert len(DemandeQuestion(question="x" * 2000).question) == 2000
    for invalide in ("", "   \n\t", "x" * 2001):
        with pytest.raises(ValidationError):
            DemandeQuestion(question=invalide)
    with pytest.raises(ValidationError):
        DemandeQuestion.model_validate({"question": "ok", "autre": 1})


@given(st.text(min_size=1, max_size=200))
def test_propriete_question_rognee_ou_refusee(texte: str) -> None:
    if texte.strip():
        assert DemandeQuestion(question=texte).question == texte.strip()
    else:
        with pytest.raises(ValidationError):
            DemandeQuestion(question=texte)


# --- GardeSession ---


class _Session:
    def __init__(self, passage_id: str) -> None:
        self.passage_id = passage_id
        self.questions: list[str] = []
        self.fermee = False

    def repondre(self, question: str) -> ReponseAgent:
        self.questions.append(question)
        return _reponse(question)

    def fermer(self) -> None:
        self.fermee = True


def test_garde_session_conserve_puis_rebatit() -> None:
    sessions: list[_Session] = []

    def fabrique(consultation: object) -> _Session:
        session = _Session(consultation.manifeste().passage_id)  # type: ignore[attr-defined]
        sessions.append(session)
        return session

    garde = GardeSession(fabrique)
    ancien = _Consultation(passage="20261012T073000Z-aaaaaa")
    garde.repondre(ancien, "un")  # type: ignore[arg-type]
    garde.repondre(ancien, "deux")  # type: ignore[arg-type]
    assert len(sessions) == 1
    assert sessions[0].questions == ["un", "deux"]
    assert not sessions[0].fermee
    nouveau = _Consultation(passage="20261013T073000Z-bbbbbb")
    reponse = garde.repondre(nouveau, "trois")  # type: ignore[arg-type]
    assert reponse.texte == "trois"
    assert len(sessions) == 2
    assert sessions[0].fermee and not sessions[1].fermee
    assert sessions[1].questions == ["trois"]


def test_garde_session_erreur_de_fabrique_nommee_et_reessayee() -> None:
    appels: list[int] = []

    def fabrique(_c: object) -> _Session:
        appels.append(1)
        if len(appels) == 1:
            raise UsineErreur("clé absente")
        return _Session("20261012T073000Z-aaaaaa")

    garde = GardeSession(fabrique)
    with pytest.raises(SessionIndisponible, match=r"Agent indisponible .*\(clé absente\)"):
        garde.repondre(_Consultation(), "q")  # type: ignore[arg-type]
    assert garde.repondre(_Consultation(), "q").texte == "q"  # type: ignore[arg-type]
    assert len(appels) == 2


def test_garde_session_exception_non_usine_se_propage() -> None:
    def fabrique(_c: object) -> _Session:
        raise ValueError("autre")

    with pytest.raises(ValueError, match="autre"):
        GardeSession(fabrique).repondre(_Consultation(), "q")  # type: ignore[arg-type]


# --- Vue Agent ---


def test_vue_agent_reel_avec_passage() -> None:
    vue = vue_agent(repli=False, consultation=_Consultation(), services=_services())  # type: ignore[arg-type]
    assert vue.mode == "reel"
    assert vue.erreur is None and vue.message is None and vue.message_repli is None
    assert vue.legende == agent.LEGENDE
    assert vue.saisie is not None
    assert vue.saisie.valeur_defaut == agent.QUESTION_DEMO
    assert vue.saisie.libelle == agent.LIBELLE_QUESTION
    assert vue.saisie.bouton == "Envoyer"
    assert [(q.rang, q.question) for q in vue.questions] == [(0, "A ?"), (1, "B ?")]
    assert vue.titre_questions == "Questions enregistrées (suggestions)"
    assert [o.nom for o in vue.outils] == [
        "get_meteo",
        "list_anomalies",
        "get_tendance",
        "get_prevision",
        "get_risques",
    ]
    assert tuple(vue.outils) == OUTILS_AGENT


def test_vue_agent_reel_sans_passage() -> None:
    vue = vue_agent(repli=False, consultation=None, services=_services())
    assert vue.message == agent.AUCUN_PASSAGE
    assert vue.lien_message == LIEN_CHAINE
    assert vue.saisie is None
    assert vue.questions == []


def test_vue_agent_repli_rang_et_questions() -> None:
    def enregistrees(passage_id: str) -> tuple[ReponseAgentEnregistree, ...]:
        assert passage_id == "20261012T073000Z-aaaaaa"
        return tuple(
            ReponseAgentEnregistree(
                passage_id=passage_id,
                horodatage=INSTANT,
                reponse=ReponseAgent(question=f"Q{n}", texte="t"),
            )
            for n in range(3)
        )

    vue = vue_agent(
        repli=True,
        consultation=_Consultation(),  # type: ignore[arg-type]
        services=_services(reponses_repli=enregistrees),
    )
    assert vue.mode == "repli"
    assert vue.saisie is None
    assert vue.message_repli == agent.MESSAGE_REPLI
    assert vue.titre_questions == agent.LIBELLE_CHOIX
    assert [(q.rang, q.question) for q in vue.questions] == [(0, "Q0"), (1, "Q1"), (2, "Q2")]
    assert vue.erreur is None


def test_vue_agent_repli_refus_et_sans_passage() -> None:
    def refus(_p: str) -> tuple[ReponseAgentEnregistree, ...]:
        raise UsineErreur("passage étranger")

    vue = vue_agent(
        repli=True,
        consultation=_Consultation(),  # type: ignore[arg-type]
        services=_services(reponses_repli=refus),
    )
    assert vue.erreur == f"{agent.REFUS_REPLI} : passage étranger"
    assert vue.questions == []
    sans = vue_agent(repli=True, consultation=None, services=_services(reponses_repli=refus))
    assert sans.erreur is None
    assert sans.questions == []
    assert sans.message_repli == agent.MESSAGE_REPLI


def test_vue_agent_erreur_selon_mode() -> None:
    reel = vue_agent_erreur(False, "boom")
    assert reel.mode == "reel" and reel.erreur == "boom"
    assert reel.lien_repli == LIEN_REPLI and reel.message_repli is None
    repli = vue_agent_erreur(True, "boom")
    assert repli.mode == "repli" and repli.lien_repli is None
    assert repli.message_repli == agent.MESSAGE_REPLI
    assert vue_agent_erreur(False, SERVICES_ABSENTS).erreur == SERVICES_ABSENTS


# --- Avant / après ---


def test_periodes_exactes() -> None:
    assert [(p.valeur, p.libelle) for p in PERIODES] == [
        ("rapport", "Par Rapport quotidien"),
        ("cumul", "Cumulé sur 5 Rapports"),
    ]


def test_avant_apres_valeurs_exactes() -> None:
    vue = vue_avant_apres(minutes=120, mesure=_manifeste(duree_s=4.4), dernier=_manifeste())
    assert vue.avertissements == []
    assert vue.manuel is not None and vue.chaine is not None
    assert vue.manuel.titre == "Reporting manuel" and vue.manuel.etiquette == "déclaré"
    assert vue.manuel.valeurs == {"rapport": "120 min", "cumul": "600 min"}
    assert vue.chaine.titre == "Chaîne" and vue.chaine.etiquette == "mesuré"
    assert vue.chaine.valeurs == {"rapport": "4,4 s", "cumul": "22 s"}
    assert vue.tableau is not None
    assert vue.tableau.colonnes == ["Rapport", "Reporting manuel (déclaré)", "Chaîne (mesuré)"]
    assert vue.tableau.lignes == [
        ["Par Rapport quotidien", "120 min", "4,4 s"],
        ["Cumulé sur 5 Rapports", "600 min", "22 s"],
    ]
    assert vue.periode == "rapport"
    assert vue.legende == avant_apres.legende(_manifeste(duree_s=4.4))


def test_avant_apres_periode_transmise() -> None:
    vue = vue_avant_apres(
        minutes=1, mesure=_manifeste(), dernier=_manifeste(), periode="cumul"
    )
    assert vue.periode == "cumul"
    vide = vue_avant_apres(minutes=1, mesure=None, dernier=None, periode="cumul")
    assert vide.periode == "cumul"


def test_avant_apres_aucun_passage() -> None:
    vue = vue_avant_apres(minutes=120, mesure=None, dernier=None)
    assert vue.message == avant_apres.AUCUN_PASSAGE
    assert vue.lien_message == LIEN_CHAINE
    assert vue.tableau is None and vue.manuel is None and vue.chaine is None
    assert vue.avertissements == []
    # configuration absente et aucun Passage : le message prime, sans avertissement
    sans_config = vue_avant_apres(minutes=None, mesure=None, dernier=None)
    assert sans_config.message == avant_apres.AUCUN_PASSAGE
    assert sans_config.avertissements == []


def test_avant_apres_classification_initiale_seule() -> None:
    vue = vue_avant_apres(minutes=120, mesure=None, dernier=_manifeste())
    assert vue.avertissements == [avant_apres.SEULE_CLASSIFICATION_INITIALE]
    assert vue.message is None
    assert vue.chaine is None and vue.legende is None
    assert vue.manuel is not None
    assert vue.tableau is not None
    assert vue.tableau.colonnes == ["Rapport", "Reporting manuel (déclaré)"]
    assert vue.tableau.lignes == [
        ["Par Rapport quotidien", "120 min"],
        ["Cumulé sur 5 Rapports", "600 min"],
    ]


def test_avant_apres_config_absente() -> None:
    vue = vue_avant_apres(minutes=None, mesure=_manifeste(duree_s=2.0), dernier=_manifeste())
    assert vue.avertissements == [avant_apres.CONFIG_ABSENTE]
    assert vue.manuel is None and vue.chaine is not None
    assert vue.tableau is not None
    assert vue.tableau.colonnes == ["Rapport", "Chaîne (mesuré)"]
    assert vue.tableau.lignes == [["Par Rapport quotidien", "2 s"], ["Cumulé sur 5 Rapports", "10 s"]]


def test_avant_apres_config_absente_et_classification_initiale() -> None:
    vue = vue_avant_apres(minutes=None, mesure=None, dernier=_manifeste())
    assert vue.avertissements == [
        avant_apres.CONFIG_ABSENTE,
        avant_apres.SEULE_CLASSIFICATION_INITIALE,
    ]
    assert vue.tableau is None


@given(minutes=st.integers(min_value=1, max_value=10**7), ms=st.integers(0, 10**6))
def test_propriete_cumul_cinq_fois_la_mesure(minutes: int, ms: int) -> None:
    vue = vue_avant_apres(
        minutes=minutes,
        mesure=_manifeste(duree_s=ms / 1000),
        dernier=_manifeste(),
    )
    assert vue.manuel is not None and vue.tableau is not None
    assert vue.manuel.valeurs["rapport"] == f"{formater_entier(minutes)} min"
    assert vue.manuel.valeurs["cumul"] == f"{formater_entier(minutes * 5)} min"
    assert [ligne[1] for ligne in vue.tableau.lignes] == [
        vue.manuel.valeurs["rapport"],
        vue.manuel.valeurs["cumul"],
    ]
    assert vue.chaine is not None
    assert [ligne[2] for ligne in vue.tableau.lignes] == [
        vue.chaine.valeurs["rapport"],
        vue.chaine.valeurs["cumul"],
    ]


# --- Pseudonymisation ---

Apercu = Callable[[], Callable[[str], str]]


def test_pseudonymisation_ticket_par_defaut_premier_trie() -> None:
    consultation = _Consultation({"DEMO-9": "neuf", "DEMO-17": "dix-sept", "DEMO-2": "deux"})
    vue = vue_pseudonymisation(consultation, lambda: str.upper, None)  # type: ignore[arg-type]
    assert vue.tickets == ["DEMO-17", "DEMO-2", "DEMO-9"]  # tri lexical
    assert vue.ticket is not None and vue.ticket.cle == "DEMO-17"
    assert vue.ticket.url == "https://jira.example.invalid/browse/DEMO-17"
    assert vue.original == "dix-sept"
    assert vue.pseudonymise == "DIX-SEPT"
    assert vue.legende == pseudonymisation.LEGENDE
    assert vue.erreur is None and vue.message is None


def test_pseudonymisation_ticket_choisi_et_texte_brut() -> None:
    texte = "<b>Jean</b> & Marie\nligne 2"
    consultation = _Consultation({"A-1": "x", "B-2": texte})
    vue = vue_pseudonymisation(consultation, lambda: (lambda t: f"[{t}]"), "B-2")  # type: ignore[arg-type]
    assert vue.original == texte
    assert vue.pseudonymise == f"[{texte}]"
    assert vue.ticket is not None and vue.ticket.cle == "B-2"


def test_pseudonymisation_descriptions_vides_ignorees() -> None:
    consultation = _Consultation({"A": None, "B": "  \n", "C": "ok", "D": ""})
    vue = vue_pseudonymisation(consultation, lambda: str, None)  # type: ignore[arg-type]
    assert vue.tickets == ["C"]
    sans = vue_pseudonymisation(_Consultation({"A": None, "B": " "}), lambda: str, None)  # type: ignore[arg-type]
    assert sans.message == pseudonymisation.AUCUNE_DESCRIPTION
    assert sans.tickets == [] and sans.original is None
    assert vue_pseudonymisation(_Consultation(), lambda: str, "A").message == (  # type: ignore[arg-type]
        pseudonymisation.AUCUNE_DESCRIPTION
    )


def test_pseudonymisation_ticket_inconnu_ou_sans_description() -> None:
    consultation = _Consultation({"A": "ok", "B": None})
    for ticket in ("Z", "B"):
        vue = vue_pseudonymisation(consultation, lambda: pytest.fail("pas d'aperçu"), ticket)  # type: ignore[arg-type]
        assert vue.erreur == f"Le ticket {ticket} n'a pas de description non vide dans ce Passage."
        assert vue.tickets == ["A"]
        assert vue.original is None and vue.pseudonymise is None and vue.ticket is None


def test_pseudonymisation_erreur_usine_du_service() -> None:
    def apercu() -> Callable[[str], str]:
        raise UsineErreur("clé USINE_CLE_PSEUDO absente")

    vue = vue_pseudonymisation(_Consultation({"A": "ok"}), apercu, None)  # type: ignore[arg-type]
    assert vue.erreur == (
        "Aperçu de la Pseudonymisation impossible : clé USINE_CLE_PSEUDO absente"
    )
    assert vue.tickets == ["A"] and vue.ticket is not None
    assert vue.original is None and vue.pseudonymise is None and vue.legende is None


def test_pseudonymisation_erreur_a_l_appel_du_moteur() -> None:
    def apercu() -> Callable[[str], str]:
        def moteur(_t: str) -> str:
            raise OSError("modèle fr_core introuvable\nsuite")

        return moteur

    vue = vue_pseudonymisation(_Consultation({"A": "ok"}), apercu, None)  # type: ignore[arg-type]
    assert vue.erreur == pseudonymisation.moteur_indisponible(OSError("modèle fr_core introuvable"))
    assert "suite" not in (vue.erreur or "")
    assert vue.tickets == ["A"]


def test_moteur_indisponible_formes() -> None:
    prefixe = "Moteur de Pseudonymisation indisponible (Presidio ou modèle spaCy) : "
    assert pseudonymisation.moteur_indisponible(ValueError("a\nb")) == prefixe + "ValueError : a"
    assert pseudonymisation.moteur_indisponible(RuntimeError()) == prefixe + "RuntimeError"
    assert pseudonymisation.moteur_indisponible(KeyError("  \n ")) == prefixe + (
        "KeyError : '  \\n '"
    )


@given(message=st.text(max_size=100))
def test_propriete_moteur_indisponible_une_ligne(message: str) -> None:
    texte = pseudonymisation.moteur_indisponible(RuntimeError(message))
    assert texte.startswith("Moteur de Pseudonymisation indisponible")
    assert "RuntimeError" in texte
    premiere = message.strip().splitlines()
    if premiere:
        assert texte.endswith(f"RuntimeError : {premiere[0]}")
    else:
        assert texte.endswith("RuntimeError")


@given(
    st.dictionaries(
        st.text(alphabet="ABCDEF-0123456789", min_size=1, max_size=8),
        st.one_of(st.none(), st.text(max_size=20)),
        max_size=8,
    )
)
@settings(max_examples=60)
def test_propriete_descriptions_filtre_et_tri(textes: dict[str, str | None]) -> None:
    table = _Consultation(textes).textes_tickets()
    attendu = {c: d for c, d in textes.items() if d is not None and d.strip()}
    assert dict(pseudonymisation.descriptions(table)) == attendu
    vue = vue_pseudonymisation(_Consultation(textes), lambda: str, None)  # type: ignore[arg-type]
    if attendu:
        assert vue.tickets == sorted(attendu)
        assert vue.original == attendu[sorted(attendu)[0]]
    else:
        assert vue.message == pseudonymisation.AUCUNE_DESCRIPTION


def test_vues_erreur_et_message_pseudonymisation() -> None:
    erreur = vue_pseudonymisation_erreur("boom")
    assert erreur.erreur == "boom" and erreur.tickets == [] and erreur.original is None
    message = vue_pseudonymisation_message("rien", LIEN_CHAINE)
    assert message.message == "rien" and message.lien_message == LIEN_CHAINE
    assert vue_pseudonymisation_message("rien").lien_message is None


# --- Outillage ---


def test_vue_outillage_absente_presente_erreur() -> None:
    absente = vue_outillage(None)
    assert absente.message is not None and "docs/fiche-outillage.md" in absente.message
    assert absente.html is None and absente.legende is None and absente.erreur is None
    presente = vue_outillage("# Titre\n\n## A\n\ntexte\n")
    assert presente.message is None and presente.erreur is None
    assert presente.html == '<section class="carte carte--fiche"><h2>A</h2>\n<p>texte</p>\n</section>'
    assert presente.legende is not None and "lecture seule" in presente.legende
    vide = vue_outillage("")
    assert vide.html == "" and vide.message is None
    erreur = vue_outillage_erreur("illisible")
    assert erreur.erreur == "illisible"
    assert erreur.html is None and erreur.message is None and erreur.legende is None
