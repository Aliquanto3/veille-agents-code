"""Renfort Story 7.16 : valeurs exactes, bornes et branches d'erreur des vues pures."""

from pathlib import Path
from typing import Any

import polars as pl
import pytest
from pydantic import ValidationError

from tests.unit.ui.test_avant_apres import manifeste
from usine.contrats.erreurs import UsineErreur
from usine.contrats.llm import ReponseAgent, StatutControle
from usine.ui import agent, avant_apres, outillage, pseudonymisation
from usine.ui.ecrans import (
    AUCUN_OUTIL,
    BADGE_HORS_PERIMETRE,
    LIBELLE_OUTILS,
    OUTILS_AGENT,
    REPONSE_REJETEE,
    ServicesEcrans,
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
from usine.ui.outillage import lire_fiche, rendre_fiche
from usine.ui.vues import DemandeQuestion

REFUS = "Aucune donnée disponible."


def rep(texte: str, statut: StatutControle, outils: tuple[str, ...] = ()) -> ReponseAgent:
    return ReponseAgent(question="Q ?", texte=texte, outils_appeles=outils, statut_controle=statut)


# --- vue_reponse_agent ---


@pytest.mark.parametrize(
    ("statut", "code"),
    [
        (StatutControle.conforme, "conforme"),
        (StatutControle.corrige, "corrige"),
        (StatutControle.non_controle, "non_controle"),
    ],
)
def test_badge_code_suit_le_statut(statut: StatutControle, code: str) -> None:
    vue = vue_reponse_agent(rep("Texte.", statut, ("get_risques", "get_meteo")), REFUS)
    assert vue.badge_code == code
    assert vue.badge == agent.texte_statut(rep("Texte.", statut))
    assert vue.texte == "Texte."
    assert vue.texte_masque is None
    assert vue.outils == ["get_risques", "get_meteo"]  # ordre conservé
    assert vue.libelle_outils == LIBELLE_OUTILS
    assert vue.aucun_outil == AUCUN_OUTIL
    assert vue.mention_repli is None


def test_refus_reconnu_malgre_les_espaces() -> None:
    vue = vue_reponse_agent(rep(f"  {REFUS}\n", StatutControle.conforme), REFUS)
    assert vue.badge_code == "hors_perimetre"
    assert vue.badge == BADGE_HORS_PERIMETRE
    assert vue.texte == f"  {REFUS}\n"  # texte transmis tel quel


def test_texte_proche_du_refus_n_est_pas_hors_perimetre() -> None:
    vue = vue_reponse_agent(rep(f"{REFUS} Mais ENT-B.", StatutControle.conforme), REFUS)
    assert vue.badge_code == "conforme"
    vue = vue_reponse_agent(rep(REFUS.lower(), StatutControle.conforme), REFUS)
    assert vue.badge_code == "conforme"


def test_rejet_prime_sur_le_refus() -> None:
    vue = vue_reponse_agent(rep(REFUS, StatutControle.rejete), REFUS)
    assert vue.badge_code == "rejete"
    assert vue.badge == agent.texte_statut(rep(REFUS, StatutControle.rejete))
    assert vue.texte is None
    assert vue.texte_masque == REPONSE_REJETEE
    assert REFUS not in vue.model_dump_json()


# --- vue_agent / erreur ---


class _Manifeste:
    passage_id = "p1"


class _Consultation:
    def manifeste(self) -> _Manifeste:
        return _Manifeste()


def services(**remplacements: Any) -> ServicesEcrans:
    base: dict[str, Any] = {
        "session_agent": lambda _c: None,
        "reponses_repli": lambda _p: (),
        "questions_suggerees": ("A ?", "B ?"),
        "texte_hors_perimetre": REFUS,
        "apercu_pseudonymisation": lambda: lambda t: t,
        "config_demo": lambda: None,
        "manifestes_avant_apres": lambda _r: (None, None),
        "lire_fiche": lambda: None,
    }
    return ServicesEcrans(**(base | remplacements))


def test_vue_agent_reel_valeurs() -> None:
    vue = vue_agent(repli=False, consultation=_Consultation(), services=services())  # type: ignore[arg-type]
    assert vue.mode == "reel"
    assert vue.titre_questions == "Questions enregistrées (suggestions)"
    assert [(q.rang, q.question) for q in vue.questions] == [(0, "A ?"), (1, "B ?")]
    assert vue.saisie is not None
    assert vue.saisie.bouton == "Envoyer"
    assert vue.saisie.valeur_defaut == agent.QUESTION_DEMO
    assert vue.titre_outils == "Outils de l'Agent"
    assert tuple(vue.outils) == OUTILS_AGENT
    assert vue.lien_repli is None


def test_vue_agent_repli_sans_passage_n_appelle_pas_le_service() -> None:
    def interdit(_p: str) -> Any:
        raise AssertionError("ne doit pas être appelé")

    vue = vue_agent(repli=True, consultation=None, services=services(reponses_repli=interdit))
    assert vue.mode == "repli"
    assert vue.questions == []
    assert vue.erreur is None
    assert vue.titre_questions == agent.LIBELLE_CHOIX
    assert vue.message_repli == agent.MESSAGE_REPLI


def test_vue_agent_repli_transmet_le_passage_et_numerote() -> None:
    recus: list[str] = []

    class Enr:
        def __init__(self, question: str) -> None:
            self.reponse = ReponseAgent(question=question, texte="t")

    def lire(passage_id: str) -> Any:
        recus.append(passage_id)
        return (Enr("Q0"), Enr("Q1"), Enr("Q2"))

    vue = vue_agent(
        repli=True,
        consultation=_Consultation(),  # type: ignore[arg-type]
        services=services(reponses_repli=lire),
    )
    assert recus == ["p1"]
    assert [(q.rang, q.question) for q in vue.questions] == [(0, "Q0"), (1, "Q1"), (2, "Q2")]


def test_vue_agent_repli_refus_nomme_la_cause() -> None:
    def refuser(_p: str) -> Any:
        raise UsineErreur("passage étranger")

    vue = vue_agent(
        repli=True,
        consultation=_Consultation(),  # type: ignore[arg-type]
        services=services(reponses_repli=refuser),
    )
    assert vue.erreur == f"{agent.REFUS_REPLI} : passage étranger"
    assert vue.questions == []


def test_vue_agent_erreur_selon_le_mode() -> None:
    reel = vue_agent_erreur(False, "boom")
    assert (reel.mode, reel.erreur) == ("reel", "boom")
    assert reel.lien_repli is not None and reel.lien_repli.url == "/chaine"
    assert reel.message_repli is None
    assert reel.saisie is None
    repli = vue_agent_erreur(True, "boum")
    assert (repli.mode, repli.erreur) == ("repli", "boum")
    assert repli.lien_repli is None
    assert repli.message_repli == agent.MESSAGE_REPLI


def test_vue_agent_reel_sans_passage() -> None:
    vue = vue_agent(repli=False, consultation=None, services=services())
    assert vue.message == agent.AUCUN_PASSAGE
    assert vue.lien_message is not None and vue.lien_message.libelle == "Lancer la Chaîne"
    assert vue.saisie is None
    assert vue.questions == []


# --- DemandeQuestion ---


def test_demande_question_bornes() -> None:
    assert DemandeQuestion(question="a" * 2000).question == "a" * 2000
    with pytest.raises(ValidationError):
        DemandeQuestion(question="a" * 2001)
    with pytest.raises(ValidationError):
        DemandeQuestion(question="")
    with pytest.raises(ValidationError):
        DemandeQuestion(question=" \t\n ")
    assert DemandeQuestion(question="\n x \n").question == "x"
    with pytest.raises(ValidationError):
        DemandeQuestion.model_validate({"question": "x", "autre": 1})


# --- Avant / après ---


def test_avant_apres_valeurs_exactes_zero_minute() -> None:
    vue = vue_avant_apres(minutes=0, mesure=manifeste(secondes=10), dernier=manifeste())
    assert vue.manuel is not None
    assert vue.manuel.valeurs == {"rapport": "0 min", "cumul": "0 min"}
    assert vue.chaine is not None
    assert vue.chaine.valeurs == {"rapport": "10 s", "cumul": "50 s"}
    assert vue.periode == "rapport"
    assert vue.avertissements == []


def test_avant_apres_arrondi_des_durees_courtes() -> None:
    vue = vue_avant_apres(
        minutes=120, mesure=manifeste(secondes=0.04), dernier=manifeste(), periode="cumul"
    )
    assert vue.periode == "cumul"
    assert vue.chaine is not None
    assert vue.chaine.valeurs == {"rapport": "0 s", "cumul": "0,2 s"}
    assert vue.manuel is not None
    assert vue.manuel.valeurs == {"rapport": "120 min", "cumul": "600 min"}


def test_avant_apres_config_absente_et_aucun_passage() -> None:
    vue = vue_avant_apres(minutes=None, mesure=None, dernier=None)
    assert vue.message == avant_apres.AUCUN_PASSAGE
    assert vue.avertissements == []  # le message remplace l'écran
    assert vue.tableau is None and vue.manuel is None and vue.chaine is None
    assert vue.lien_message is not None and vue.lien_message.url == "/chaine"


def test_avant_apres_config_absente_et_classification_initiale() -> None:
    dernier = manifeste(classification_initiale=True)
    vue = vue_avant_apres(minutes=None, mesure=None, dernier=dernier)
    assert vue.avertissements == [
        avant_apres.CONFIG_ABSENTE,
        avant_apres.SEULE_CLASSIFICATION_INITIALE,
    ]
    assert vue.tableau is None  # rien à tabuler
    assert vue.legende is None
    assert vue.message is None


def test_avant_apres_tableau_une_seule_colonne_de_valeurs() -> None:
    seul_manuel = vue_avant_apres(
        minutes=30, mesure=None, dernier=manifeste(classification_initiale=True)
    )
    assert seul_manuel.tableau is not None
    assert seul_manuel.tableau.colonnes == ["Rapport", "Reporting manuel (déclaré)"]
    assert seul_manuel.tableau.lignes == [
        ["Par Rapport quotidien", "30 min"],
        ["Cumulé sur 5 Rapports", "150 min"],
    ]
    seul_chaine = vue_avant_apres(minutes=None, mesure=manifeste(secondes=2), dernier=manifeste())
    assert seul_chaine.tableau is not None
    assert seul_chaine.tableau.colonnes == ["Rapport", "Chaîne (mesuré)"]
    assert seul_chaine.tableau.lignes[1] == ["Cumulé sur 5 Rapports", "10 s"]
    assert seul_chaine.legende is not None
    assert "20261012T073000Z-aaaaaa" in seul_chaine.legende


def test_avant_apres_erreur_et_periodes() -> None:
    vue = vue_avant_apres_erreur("lecture KO")
    assert vue.erreur == "lecture KO"
    assert [(o.valeur, o.libelle) for o in vue.periodes] == [
        ("rapport", "Par Rapport quotidien"),
        ("cumul", "Cumulé sur 5 Rapports"),
    ]
    assert vue.libelle_periode == "Période"
    assert vue.periode == "rapport"
    assert vue.tableau is None


# --- Pseudonymisation ---


class _Textes:
    def __init__(self, tableau: pl.DataFrame) -> None:
        self._table = tableau

    def textes_tickets(self) -> pl.DataFrame:
        return self._table

    def url_ticket(self, cle: str) -> str | None:
        return f"https://jira.test/{cle}"


def table(*lignes: tuple[str, str | None]) -> pl.DataFrame:
    return pl.DataFrame(
        {"cle_ticket": [c for c, _ in lignes], "description": [d for _, d in lignes]},
        schema={"cle_ticket": pl.Utf8, "description": pl.Utf8},
    )


def test_descriptions_filtre_vides_et_garde_l_ordre() -> None:
    res = pseudonymisation.descriptions(
        table(("B-2", "texte b"), ("A-1", None), ("C-3", "   \n"), ("D-4", ""), ("E-5", " e "))
    )
    assert list(res.items()) == [("B-2", "texte b"), ("E-5", " e ")]


def test_moteur_indisponible_formats() -> None:
    prefixe = "Moteur de Pseudonymisation indisponible (Presidio ou modèle spaCy) : "
    assert pseudonymisation.moteur_indisponible(ValueError()) == prefixe + "ValueError"
    assert pseudonymisation.moteur_indisponible(ValueError("  \n ")) == prefixe + "ValueError"
    assert pseudonymisation.moteur_indisponible(OSError("\n  ligne 1\nligne 2")) == (
        prefixe + "OSError : ligne 1"
    )


def test_vue_pseudonymisation_tickets_tries_et_lien() -> None:
    consultation = _Textes(table(("B-2", "texte b"), ("A-1", "texte a")))
    vus: list[str] = []

    def apercu() -> Any:
        def transformer(texte: str) -> str:
            vus.append(texte)
            return texte.upper()

        return transformer

    vue = vue_pseudonymisation(consultation, apercu, None)  # type: ignore[arg-type]
    assert vue.tickets == ["A-1", "B-2"]
    assert vue.ticket is not None and vue.ticket.cle == "A-1"
    assert vue.ticket.url == "https://jira.test/A-1"
    assert (vue.original, vue.pseudonymise) == ("texte a", "TEXTE A")
    assert vus == ["texte a"]
    assert vue.legende == pseudonymisation.LEGENDE
    assert vue.erreur is None


def test_vue_pseudonymisation_ticket_sans_description_refuse() -> None:
    consultation = _Textes(table(("A-1", "a"), ("V-9", "  ")))

    def apercu() -> Any:
        raise AssertionError("le moteur ne doit pas être chargé")

    vue = vue_pseudonymisation(consultation, apercu, "V-9")  # type: ignore[arg-type]
    assert vue.erreur == "Le ticket V-9 n'a pas de description non vide dans ce Passage."
    assert vue.tickets == ["A-1"]
    assert vue.ticket is None and vue.original is None


def test_vue_pseudonymisation_aucune_description() -> None:
    vue = vue_pseudonymisation(_Textes(table(("A-1", None))), lambda: str, None)  # type: ignore[arg-type]
    assert vue.message == pseudonymisation.AUCUNE_DESCRIPTION
    assert vue.tickets == []


def test_vue_pseudonymisation_erreur_usine_garde_ticket() -> None:
    def apercu() -> Any:
        raise UsineErreur("clé absente")

    vue = vue_pseudonymisation(_Textes(table(("A-1", "a"))), apercu, "A-1")  # type: ignore[arg-type]
    assert vue.erreur == "Aperçu de la Pseudonymisation impossible : clé absente"
    assert vue.ticket is not None and vue.ticket.cle == "A-1"
    assert vue.original is None and vue.pseudonymise is None
    assert vue.legende is None


def test_vue_pseudonymisation_erreur_et_message() -> None:
    erreur = vue_pseudonymisation_erreur("KO")
    assert erreur.erreur == "KO" and erreur.tickets == []
    assert erreur.titre_original == "Original"
    message = vue_pseudonymisation_message("Rien")
    assert message.message == "Rien" and message.lien_message is None


# --- Outillage ---


def test_vue_outillage_valeurs() -> None:
    vide = vue_outillage(None)
    assert (vide.message, vide.html, vide.legende, vide.erreur) == (
        outillage.FICHE_ABSENTE,
        None,
        None,
        None,
    )
    ok = vue_outillage("# T\n\n## S\n\ntexte\n")
    assert ok.message is None and ok.erreur is None
    assert ok.legende == outillage.LEGENDE
    assert ok.html == rendre_fiche("# T\n\n## S\n\ntexte\n")
    err = vue_outillage_erreur("illisible")
    assert (err.erreur, err.html, err.message, err.legende) == ("illisible", None, None, None)


def test_fiche_vide_ou_titre_seul_ne_donne_aucune_carte() -> None:
    assert rendre_fiche("") == ""
    assert rendre_fiche("# Titre seul\n") == ""


def test_fiche_pastilles_exactes_et_variantes() -> None:
    html = rendre_fiche("# T\n\nA ✅ B ⚠️ C ❌ D ⚠ E\n")
    assert html == (
        '<section class="carte carte--fiche"><p>A '
        '<span class="pastille pastille--oui">Oui</span> B '
        '<span class="pastille pastille--surveiller">À surveiller</span> C '
        '<span class="pastille pastille--non">Non</span> D '
        '<span class="pastille pastille--surveiller">À surveiller</span> E</p>\n</section>'
    )


def test_fiche_intro_puis_sections_et_tableau_enveloppe() -> None:
    html = rendre_fiche("# T\n\nIntro\n\n## Un\n\n| a | b |\n|---|---|\n| 1 | 2 |\n")
    assert html.count("<section") == 2
    assert html.startswith('<section class="carte carte--fiche"><p>Intro</p>')
    assert f'aria-label="{outillage.LIBELLE_TABLEAU}"' in html
    assert html.count("</table></div>") == 1
    assert html.count('<div class="table-defile"') == 1


def test_fiche_sans_intro_commence_par_h2() -> None:
    html = rendre_fiche("# T\n\n## Un\n\nx\n")
    assert html.startswith('<section class="carte carte--fiche"><h2>Un</h2>')
    assert html.count("<section") == 1


def test_lire_fiche(tmp_path: Path) -> None:
    assert lire_fiche(tmp_path) is None
    chemin = tmp_path / outillage.FICHIER_FICHE
    chemin.parent.mkdir(parents=True)
    chemin.write_bytes(b"\xef\xbb\xbf# Titre \xc3\xa9\n")
    assert lire_fiche(tmp_path) == "# Titre é\n"  # BOM toléré
    chemin.write_bytes(b"\xff\xfe\x00bad")
    with pytest.raises(UnicodeDecodeError):
        lire_fiche(tmp_path)


def test_messages_de_fiche_citent_le_fichier() -> None:
    assert "docs/fiche-outillage.md" in outillage.FICHE_ABSENTE
    assert "docs/fiche-outillage.md" in outillage.LEGENDE
