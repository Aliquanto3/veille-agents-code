"""Renfort de la Story 7.16 : vues des écrans Agent, Avant / après, Pseudonymisation, Outillage."""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import polars as pl
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from usine.contrats.erreurs import UsineErreur
from usine.contrats.llm import ReponseAgent, StatutControle
from usine.ui import agent, avant_apres, outillage, pseudonymisation
from usine.ui import ecrans as e
from usine.ui.vues import DemandeQuestion

HORS = "Je ne peux pas répondre."


def _rep(
    texte: str = "ok", statut: StatutControle = StatutControle.conforme, **kw: Any
) -> ReponseAgent:
    return ReponseAgent(question="Q ?", texte=texte, statut_controle=statut, **kw)


# --- vue_reponse_agent ---


def test_reponse_conforme() -> None:
    v = e.vue_reponse_agent(_rep("Bonjour", outils_appeles=("get_meteo",)), HORS)
    assert v.texte == "Bonjour"
    assert v.texte_masque is None
    assert v.badge_code == "conforme"
    assert v.badge == "Contrôle : conforme : chiffres et tickets vérifiés"
    assert v.outils == ["get_meteo"]
    assert v.libelle_outils == e.LIBELLE_OUTILS
    assert v.aucun_outil == "aucun"
    assert v.annonce == e.ANNONCE_REPONSE
    assert v.mention_repli is None


@pytest.mark.parametrize("texte", [HORS, f"  {HORS}\n"])
def test_refus_hors_perimetre(texte: str) -> None:
    v = e.vue_reponse_agent(_rep(texte, StatutControle.non_controle), HORS)
    assert v.badge_code == "hors_perimetre"
    assert v.badge == e.BADGE_HORS_PERIMETRE
    assert v.outils == []


def test_refus_different_nest_pas_hors_perimetre() -> None:
    v = e.vue_reponse_agent(_rep(HORS + " !"), HORS)
    assert v.badge_code == "conforme"


def test_rejet_masque_le_texte_meme_si_refus() -> None:
    v = e.vue_reponse_agent(_rep(HORS, StatutControle.rejete), HORS)
    assert v.texte is None
    assert v.texte_masque == e.REPONSE_REJETEE
    assert v.badge_code == "rejete"
    assert v.badge == "Contrôle : rejetée par le contrôle"


@given(texte=st.text(min_size=1), statut=st.sampled_from(list(StatutControle)))
def test_texte_rejete_jamais_envoye(texte: str, statut: StatutControle) -> None:
    v = e.vue_reponse_agent(_rep(texte, statut), HORS)
    if statut is StatutControle.rejete:
        assert v.texte is None and v.texte_masque == e.REPONSE_REJETEE
    elif texte.strip() != HORS:
        assert v.texte == texte and v.texte_masque is None


def test_mention_repli() -> None:
    enr: Any = SimpleNamespace(horodatage=datetime(2026, 10, 1, 8, tzinfo=UTC), passage_id="P-1")
    v = e.vue_reponse_agent(_rep(), HORS, enr)
    assert v.mention_repli is not None
    assert "P-1" in v.mention_repli and v.mention_repli.startswith("Mode repli")


# --- vue_agent ---


class _Consult:
    def __init__(self, passage_id: str = "P-1", textes: pl.DataFrame | None = None) -> None:
        self._id = passage_id
        self._textes = textes
        self.urls: dict[str, str] = {}

    def manifeste(self) -> Any:
        return SimpleNamespace(passage_id=self._id)

    def textes_tickets(self) -> pl.DataFrame:
        assert self._textes is not None
        return self._textes

    def url_ticket(self, cle: str) -> str | None:
        return self.urls.get(cle)


def _c(passage_id: str = "P-1", textes: pl.DataFrame | None = None) -> Any:
    return _Consult(passage_id, textes)


def _services(**kw: Any) -> e.ServicesEcrans:
    base: dict[str, Any] = {
        "session_agent": lambda _c: None,
        "reponses_repli": lambda _p: (),
        "questions_suggerees": ("a ?", "b ?"),
        "texte_hors_perimetre": HORS,
        "apercu_pseudonymisation": lambda: str.upper,
        "config_demo": lambda: None,
        "manifestes_avant_apres": lambda _r: (None, None),
        "lire_fiche": lambda: None,
    }
    return e.ServicesEcrans(**(base | kw))


def test_agent_reel_sans_passage() -> None:
    v = e.vue_agent(repli=False, consultation=None, services=_services())
    assert v.mode == "reel"
    assert v.message == agent.AUCUN_PASSAGE
    assert v.lien_message == e.LIEN_CHAINE
    assert v.saisie is None and v.questions == []


def test_agent_reel_saisie_et_suggestions() -> None:
    v = e.vue_agent(repli=False, consultation=_c(), services=_services())
    assert v.saisie is not None
    assert v.saisie.valeur_defaut == agent.QUESTION_DEMO
    assert v.saisie.bouton == "Envoyer"
    assert [(q.rang, q.question) for q in v.questions] == [(0, "a ?"), (1, "b ?")]
    assert v.titre_questions == e.TITRE_QUESTIONS_REEL
    assert v.legende == agent.LEGENDE
    assert v.message_repli is None and v.erreur is None
    assert [o.nom for o in v.outils] == [
        "get_meteo",
        "list_anomalies",
        "get_tendance",
        "get_prevision",
        "get_risques",
    ]


def test_agent_repli_liste_les_questions_enregistrees() -> None:
    recus: list[str] = []

    def repli(pid: str) -> tuple[Any, ...]:
        recus.append(pid)
        return tuple(SimpleNamespace(reponse=_rep()) for _ in range(3))

    v = e.vue_agent(repli=True, consultation=_c("P-9"), services=_services(reponses_repli=repli))
    assert recus == ["P-9"]
    assert v.mode == "repli"
    assert v.saisie is None
    assert v.message_repli == agent.MESSAGE_REPLI
    assert [q.rang for q in v.questions] == [0, 1, 2]
    assert v.titre_questions == agent.LIBELLE_CHOIX


def test_agent_repli_refus_du_passage() -> None:
    def refuse(_p: str) -> tuple[Any, ...]:
        raise UsineErreur("passage étranger")

    v = e.vue_agent(repli=True, consultation=_c(), services=_services(reponses_repli=refuse))
    assert v.erreur == f"{agent.REFUS_REPLI} : passage étranger"
    assert v.questions == []


def test_agent_repli_sans_consultation() -> None:
    v = e.vue_agent(repli=True, consultation=None, services=_services())
    assert v.erreur is None and v.questions == [] and v.message_repli == agent.MESSAGE_REPLI


def test_agent_erreur_selon_le_mode() -> None:
    reel = e.vue_agent_erreur(False, "boom")
    assert reel.erreur == "boom" and reel.lien_repli == e.LIEN_REPLI and reel.message_repli is None
    repli = e.vue_agent_erreur(True, "boom")
    assert repli.lien_repli is None and repli.message_repli == agent.MESSAGE_REPLI


# --- GardeSession ---


class _Session:
    def __init__(self, passage_id: str) -> None:
        self.passage_id = passage_id
        self.fermee = False
        self.questions: list[str] = []

    def repondre(self, question: str) -> Any:
        self.questions.append(question)
        return f"{self.passage_id}:{question}"

    def fermer(self) -> None:
        self.fermee = True


def test_garde_session_reutilise_puis_rebatit() -> None:
    creees: list[_Session] = []

    def fabrique(c: Any) -> Any:
        s = _Session(c.manifeste().passage_id)
        creees.append(s)
        return s

    garde = e.GardeSession(fabrique)
    assert garde.repondre(_c("A"), "1") == "A:1"
    garde.repondre(_c("A"), "2")
    assert len(creees) == 1 and creees[0].questions == ["1", "2"]
    assert garde.repondre(_c("B"), "3") == "B:3"
    assert len(creees) == 2 and creees[0].fermee and not creees[1].fermee


def test_garde_session_echec_de_fabrique_nomme_la_cause_et_reessaie() -> None:
    appels: list[int] = []

    def fabrique(_c: Any) -> Any:
        appels.append(1)
        if len(appels) == 1:
            raise UsineErreur("clé absente")
        return _Session("A")

    garde = e.GardeSession(fabrique)
    with pytest.raises(e.SessionIndisponible, match=r"construite \(clé absente\)"):
        garde.repondre(_c("A"), "q")
    assert garde.repondre(_c("A"), "q") == "A:q"


def test_garde_session_erreur_hors_usine_remonte() -> None:
    def fabrique(_c: Any) -> Any:
        raise ValueError("x")

    with pytest.raises(ValueError):
        e.GardeSession(fabrique).repondre(_c(), "q")


# --- DemandeQuestion ---


@pytest.mark.parametrize("q", ["", "   ", "\n\t "])
def test_question_vide_refusee(q: str) -> None:
    with pytest.raises(ValidationError):
        DemandeQuestion(question=q)


def test_question_bornes() -> None:
    assert DemandeQuestion(question="x" * 2000).question == "x" * 2000
    with pytest.raises(ValidationError):
        DemandeQuestion(question="x" * 2001)
    with pytest.raises(ValidationError):
        DemandeQuestion.model_validate({"question": "a", "autre": 1})


@given(q=st.text(min_size=1, max_size=2000).filter(lambda s: s.strip()))
def test_question_rognee(q: str) -> None:
    assert DemandeQuestion(question=q).question == q.strip()


# --- Avant / après ---


def _manif(secondes: float = 12.34) -> Any:
    debut = datetime(2026, 10, 12, 7, 30, tzinfo=UTC)
    return SimpleNamespace(
        passage_id="P-7",
        horodatage_debut=debut,
        horodatage_fin=debut + timedelta(seconds=secondes),
        date_arrete=date(2026, 10, 11),
    )


def test_avant_apres_valeurs_exactes() -> None:
    v = e.vue_avant_apres(minutes=120, mesure=_manif(4.4), dernier=_manif())
    assert v.manuel is not None and v.chaine is not None
    assert v.manuel.valeurs == {"rapport": "120 min", "cumul": "600 min"}
    assert v.chaine.valeurs == {"rapport": "4,4 s", "cumul": "22 s"}
    assert (v.manuel.etiquette, v.chaine.etiquette) == ("déclaré", "mesuré")
    assert v.avertissements == []
    assert v.tableau is not None
    assert v.tableau.colonnes == ["Rapport", "Reporting manuel (déclaré)", "Chaîne (mesuré)"]
    assert v.tableau.lignes == [
        ["Par Rapport quotidien", "120 min", "4,4 s"],
        ["Cumulé sur 5 Rapports", "600 min", "22 s"],
    ]
    assert v.legende == avant_apres.legende(_manif(4.4))


def test_avant_apres_milliers() -> None:
    v = e.vue_avant_apres(minutes=1000, mesure=None, dernier=_manif())
    assert v.manuel is not None and v.manuel.valeurs["cumul"] == "5 000 min"


@given(minutes=st.integers(0, 10**6), s=st.integers(0, 10**4))
@settings(max_examples=50)
def test_avant_apres_cumul_cinq_fois(minutes: int, s: int) -> None:
    v = e.vue_avant_apres(minutes=minutes, mesure=_manif(s), dernier=_manif())
    assert v.manuel is not None and v.chaine is not None
    assert v.manuel.valeurs["cumul"] == e.formater_entier(minutes * 5) + " min"
    assert v.chaine.valeurs["cumul"] == e.texte_duree(timedelta(seconds=s) * 5)


def test_avant_apres_config_absente() -> None:
    v = e.vue_avant_apres(minutes=None, mesure=_manif(), dernier=_manif())
    assert v.avertissements == [avant_apres.CONFIG_ABSENTE]
    assert v.manuel is None and v.chaine is not None
    assert v.tableau is not None and v.tableau.colonnes == ["Rapport", "Chaîne (mesuré)"]
    assert v.tableau.lignes[0] == ["Par Rapport quotidien", "12,3 s"]


def test_avant_apres_classification_initiale() -> None:
    v = e.vue_avant_apres(minutes=30, mesure=None, dernier=_manif())
    assert v.avertissements == [avant_apres.SEULE_CLASSIFICATION_INITIALE]
    assert v.chaine is None and v.legende is None
    assert v.tableau is not None and v.tableau.colonnes[1] == "Reporting manuel (déclaré)"


def test_avant_apres_aucun_passage() -> None:
    v = e.vue_avant_apres(minutes=30, mesure=None, dernier=None, periode="cumul")
    assert v.message == avant_apres.AUCUN_PASSAGE
    assert v.lien_message == e.LIEN_CHAINE
    assert v.tableau is None and v.periode == "cumul"
    assert v.avertissements == []


def test_avant_apres_rien_du_tout_cumule_les_avertissements() -> None:
    v = e.vue_avant_apres(minutes=None, mesure=None, dernier=_manif())
    assert v.avertissements == [
        avant_apres.CONFIG_ABSENTE,
        avant_apres.SEULE_CLASSIFICATION_INITIALE,
    ]
    assert v.tableau is None


def test_avant_apres_periode_et_options() -> None:
    v = e.vue_avant_apres(minutes=1, mesure=_manif(), dernier=_manif(), periode="cumul")
    assert v.periode == "cumul"
    assert [(p.valeur, p.libelle) for p in v.periodes] == [
        ("rapport", "Par Rapport quotidien"),
        ("cumul", "Cumulé sur 5 Rapports"),
    ]
    assert e.vue_avant_apres_erreur("x").erreur == "x"
    assert e.vue_avant_apres_erreur("x").periode == "rapport"


# --- Pseudonymisation ---


def _tickets(rows: list[tuple[str, str | None]]) -> pl.DataFrame:
    return pl.DataFrame(
        {"cle_ticket": [r[0] for r in rows], "description": [r[1] for r in rows]},
        schema={"cle_ticket": pl.String, "description": pl.String},
    )


def test_descriptions_filtre_vides_et_garde_l_ordre() -> None:
    t = _tickets([("B-2", "deux"), ("A-1", None), ("C-3", "  \n"), ("D-4", " quatre ")])
    d = pseudonymisation.descriptions(t)
    assert list(d.items()) == [("B-2", "deux"), ("D-4", " quatre ")]


def test_moteur_indisponible_premiere_ligne() -> None:
    m = pseudonymisation.moteur_indisponible(OSError("modèle absent\nsuite secrète"))
    assert m.endswith("OSError : modèle absent")
    assert "secrète" not in m and "\n" not in m
    assert pseudonymisation.moteur_indisponible(RuntimeError("  ")).endswith(": RuntimeError")


def test_pseudo_aucune_description() -> None:
    c = _c(textes=_tickets([("A-1", " ")]))
    v = e.vue_pseudonymisation(c, lambda: str.upper, None)
    assert v.message == pseudonymisation.AUCUNE_DESCRIPTION and v.tickets == []


def test_pseudo_defaut_premier_ticket_trie_et_url() -> None:
    c = _c(textes=_tickets([("Z-9", "zz"), ("A-1", "aa")]))
    c.urls["A-1"] = "https://x.invalid/A-1"
    v = e.vue_pseudonymisation(c, lambda: str.upper, None)
    assert v.tickets == ["A-1", "Z-9"]
    assert v.ticket is not None and v.ticket.cle == "A-1"
    assert v.ticket.url == "https://x.invalid/A-1"
    assert (v.original, v.pseudonymise) == ("aa", "AA")
    assert v.legende == pseudonymisation.LEGENDE and v.erreur is None


def test_pseudo_ticket_choisi_sans_url() -> None:
    c = _c(textes=_tickets([("Z-9", "zz"), ("A-1", "aa")]))
    v = e.vue_pseudonymisation(c, lambda: str.upper, "Z-9")
    assert v.ticket is not None and v.ticket.url is None and v.ticket.nom_accessible is None
    assert v.original == "zz"


def test_pseudo_ticket_inconnu() -> None:
    c = _c(textes=_tickets([("A-1", "aa")]))
    v = e.vue_pseudonymisation(c, lambda: str.upper, "NOPE-1")
    assert v.erreur == "Le ticket NOPE-1 n'a pas de description non vide dans ce Passage."
    assert v.tickets == ["A-1"] and v.original is None and v.pseudonymise is None


def test_pseudo_erreur_usine_et_moteur() -> None:
    c = _c(textes=_tickets([("A-1", "aa")]))

    def cle_absente() -> Any:
        raise UsineErreur("USINE_CLE_PSEUDO absente")

    v = e.vue_pseudonymisation(c, cle_absente, None)
    assert v.erreur == "Aperçu de la Pseudonymisation impossible : USINE_CLE_PSEUDO absente"
    assert v.tickets == ["A-1"] and v.ticket is not None and v.original is None

    def apercu_en_echec() -> Any:
        def f(_t: str) -> str:
            raise ValueError("spaCy\ntrace")

        return f

    v = e.vue_pseudonymisation(c, apercu_en_echec, None)
    assert v.erreur == pseudonymisation.moteur_indisponible(ValueError("spaCy\ntrace"))
    assert v.tickets == ["A-1"] and v.pseudonymise is None


def test_pseudo_message_et_erreur() -> None:
    assert e.vue_pseudonymisation_erreur("x").erreur == "x"
    m = e.vue_pseudonymisation_message("m", e.LIEN_CHAINE)
    assert m.message == "m" and m.lien_message == e.LIEN_CHAINE


# --- Outillage ---


def test_vue_outillage_fiche_absente_et_erreur() -> None:
    a = e.vue_outillage(None)
    assert a.message == outillage.FICHE_ABSENTE and a.html is None and a.legende is None
    r = e.vue_outillage_erreur("illisible")
    assert (r.erreur, r.message, r.html, r.legende) == ("illisible", None, None, None)


def test_vue_outillage_fiche_vide_est_une_fiche() -> None:
    v = e.vue_outillage("")
    assert v.message is None and v.html == "" and v.legende == outillage.LEGENDE


def test_rendre_fiche_cartes_et_titre_h1_retire() -> None:
    html = outillage.rendre_fiche("# Titre\n\nIntro\n\n## A\n\ntexte a\n\n## B\n\ntexte b\n")
    assert "Titre" not in html
    assert html.count('<section class="carte carte--fiche">') == 3
    assert "<h2>A</h2>" in html and "<h2>B</h2>" in html
    assert html.startswith('<section class="carte carte--fiche"><p>Intro</p>')


def test_rendre_fiche_sans_intro_pas_de_carte_vide() -> None:
    html = outillage.rendre_fiche("# T\n\n## A\n\nx\n")
    assert html.count("<section") == 1
    assert html.startswith('<section class="carte carte--fiche"><h2>')


def test_rendre_fiche_pastilles() -> None:
    html = outillage.rendre_fiche("## S\n\n✅ ⚠️ ❌ fin\n")
    assert '<span class="pastille pastille--oui">Oui</span>' in html
    assert '<span class="pastille pastille--surveiller">À surveiller</span>' in html
    assert '<span class="pastille pastille--non">Non</span>' in html
    assert "️" not in html and "✅" not in html and "❌" not in html


def test_rendre_fiche_tableau_defilant() -> None:
    html = outillage.rendre_fiche("## S\n\n| a | b |\n|---|---|\n| ✅ | x |\n")
    assert html.count("<table>") == 1
    assert f'role="region" tabindex="0" aria-label="{outillage.LIBELLE_TABLEAU}"><table>' in html
    assert "</table></div>" in html and "Oui" in html


def test_rendre_fiche_html_brut_echappe() -> None:
    html = outillage.rendre_fiche(
        "## S\n\n<script>alert(1)</script> <img src=x onerror=alert(1)>\n\n"
        "[l](javascript:alert(1))\n"
    )
    assert "<script" not in html and "<img" not in html
    assert "&lt;script&gt;" in html
    assert 'href="javascript' not in html


@given(st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=200))
def test_rendre_fiche_ne_laisse_passer_aucune_balise_script(texte: str) -> None:
    html = outillage.rendre_fiche("## S\n\n" + texte.replace("\x00", ""))
    assert "<script" not in html.lower()


def test_lire_fiche(tmp_path: Path) -> None:
    assert outillage.lire_fiche(tmp_path) is None
    f = tmp_path / outillage.FICHIER_FICHE
    f.parent.mkdir(parents=True)
    f.write_bytes("﻿bonjour é".encode())
    assert outillage.lire_fiche(tmp_path) == "bonjour é"
    f.write_bytes(b"\xff\xfe\x00bad\x80")
    with pytest.raises(UnicodeDecodeError):
        outillage.lire_fiche(tmp_path)
