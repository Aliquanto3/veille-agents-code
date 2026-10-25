"""Renfort Story 7.16 : routes `/api/agent*`, `/api/avant-apres`, `/api/pseudonymisation`,
`/api/outillage` (codes d'erreur, garde d'origine, messages génériques)."""

import logging
from collections.abc import Callable
from datetime import UTC, datetime

import polars as pl
import pytest
from fastapi.testclient import TestClient

from tests.unit.ui.test_renf_ecrans_vues import HORS_PERIMETRE, _Consultation, _manifeste
from usine.contrats.config import ConfigDemo
from usine.contrats.erreurs import UsineErreur
from usine.contrats.llm import ReponseAgent, ReponseAgentEnregistree, StatutControle
from usine.contrats.passage import ManifestePassage
from usine.ui import agent, avant_apres, carte
from usine.ui.ecrans import MODE_REPLI_SANS_LLM, SERVICES_ABSENTS, ServicesEcrans
from usine.ui.serveur import (
    HOTE,
    REPONSE_IMPOSSIBLE,
    SEULEMENT_REPLI,
    creer_application,
)

INSTANT = datetime(2026, 10, 12, 7, 30, tzinfo=UTC)
PASSAGE = "20261012T073000Z-aaaaaa"


class _Session:
    def __init__(self, passage_id: str, comportement: Callable[[str], ReponseAgent]) -> None:
        self.passage_id = passage_id
        self._comportement = comportement

    def repondre(self, question: str) -> ReponseAgent:
        return self._comportement(question)

    def fermer(self) -> None:
        pass


def _ok(question: str) -> ReponseAgent:
    return ReponseAgent(
        question=question,
        texte=f"Réponse à {question}",
        outils_appeles=("get_meteo",),
        statut_controle=StatutControle.conforme,
    )


def _enregistrees(passage_id: str = PASSAGE) -> tuple[ReponseAgentEnregistree, ...]:
    return tuple(
        ReponseAgentEnregistree(
            passage_id=passage_id,
            horodatage=INSTANT,
            reponse=ReponseAgent(question=f"Q{n}", texte=f"T{n}"),
        )
        for n in range(2)
    )


def _services(**surcharges: object) -> ServicesEcrans:
    base: dict[str, object] = {
        "session_agent": lambda c: _Session(c.manifeste().passage_id, _ok),
        "reponses_repli": lambda _p: _enregistrees(),
        "questions_suggerees": ("S1", "S2"),
        "texte_hors_perimetre": HORS_PERIMETRE,
        "apercu_pseudonymisation": lambda: str.upper,
        "config_demo": lambda: ConfigDemo(temps_manuel_minutes_par_rapport=120),
        "manifestes_avant_apres": lambda _r: (_manifeste(duree_s=4.4), _manifeste()),
        "lire_fiche": lambda: "# T\n\n## A\n\n✅\n",
    }
    return ServicesEcrans(**(base | surcharges))  # type: ignore[arg-type]


def _client(
    services: ServicesEcrans | None = None,
    *,
    repli: bool = False,
    lire: Callable[[bool], object] | None = None,
    sans_services: bool = False,
) -> TestClient:
    def lecture(_repli: bool) -> object:
        return _Consultation({"DEMO-1": "un", "DEMO-17": "dix-sept"}, PASSAGE)

    application = creer_application(
        repli=repli,
        lire_manifeste=lambda _r: None,
        lire_consultation=lire or lecture,  # type: ignore[arg-type]
        services=None if sans_services else (services or _services()),
    )
    return TestClient(application, base_url=f"http://{HOTE}", raise_server_exceptions=False)


def _post(http: TestClient, question: object = "Bonjour ?", **entetes: str):  # noqa: ANN202
    return http.post("/api/agent/question", json={"question": question}, headers=entetes)


# --- Sans services ---


@pytest.mark.parametrize(
    "chemin", ["/api/agent", "/api/avant-apres", "/api/pseudonymisation", "/api/outillage"]
)
def test_sans_services_bandeau_d_erreur(chemin: str) -> None:
    reponse = _client(sans_services=True).get(chemin)
    assert reponse.status_code == 200
    assert reponse.json()["erreur"] == SERVICES_ABSENTS


def test_sans_services_question_et_rejeu() -> None:
    http = _client(sans_services=True)
    assert _post(http).status_code == 503
    assert _post(http).json()["detail"] == SERVICES_ABSENTS
    assert http.get("/api/agent/enregistrees/0").status_code == 503


# --- Question ---


def test_question_reelle_nominale() -> None:
    reponse = _post(_client(), "  Où ça ?  ")
    assert reponse.status_code == 200
    vue = reponse.json()
    assert vue["question"] == "Où ça ?"  # rognée
    assert vue["texte"] == "Réponse à Où ça ?"
    assert vue["badge_code"] == "conforme"
    assert vue["outils"] == ["get_meteo"]
    assert vue["texte_masque"] is None and vue["mention_repli"] is None


@pytest.mark.parametrize("corps", [{"question": ""}, {"question": "  \n"}, {}, {"q": "x"}])
def test_question_invalide_422(corps: dict[str, str]) -> None:
    assert _client().post("/api/agent/question", json=corps).status_code == 422


def test_question_trop_longue_422_et_limite_acceptee() -> None:
    http = _client()
    assert _post(http, "x" * 2001).status_code == 422
    assert _post(http, "x" * 2000).status_code == 200


def test_question_origine_refusee_403() -> None:
    http = _client()
    for origine in ("null", "http://evil.example", f"http://{HOTE}:1", "http://127.0.0.1:9"):
        reponse = _post(http, Origin=origine)
        assert reponse.status_code == 403, origine
        assert reponse.json()["detail"] == "Origine refusée."
    assert _post(http, Origin=f"http://{HOTE}").status_code == 200


def test_question_host_inconnu_refuse() -> None:
    http = _client()
    reponse = http.post(
        "/api/agent/question", json={"question": "x"}, headers={"Host": "evil.example"}
    )
    assert reponse.status_code == 400


def test_question_mode_repli_409_sans_appel_session() -> None:
    def fabrique(_c: object) -> object:
        pytest.fail("la session ne doit pas être construite en Mode repli")

    reponse = _post(_client(_services(session_agent=fabrique), repli=True))
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == MODE_REPLI_SANS_LLM


def test_question_sans_passage_409() -> None:
    reponse = _post(_client(lire=lambda _r: None))
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == agent.AUCUN_PASSAGE


def test_question_lecture_impossible_503() -> None:
    def casse(_r: bool) -> object:
        raise UsineErreur("manifeste illisible")

    def droits(_r: bool) -> object:
        raise PermissionError(13, "refusé")

    reponse = _post(_client(lire=casse))
    assert (reponse.status_code, reponse.json()["detail"]) == (503, "manifeste illisible")
    reponse = _post(_client(lire=droits))
    assert reponse.status_code == 503
    assert reponse.json()["detail"].startswith("Lecture du Passage impossible")


def test_question_session_indisponible_503() -> None:
    def fabrique(_c: object) -> object:
        raise UsineErreur("clé LLM absente")

    reponse = _post(_client(_services(session_agent=fabrique)))
    assert reponse.status_code == 503
    assert reponse.json()["detail"] == "Agent indisponible : la session ne peut être construite (clé LLM absente)"


def test_question_502_generique_et_journal(caplog: pytest.LogCaptureFixture) -> None:
    def secret(_q: str) -> ReponseAgent:
        raise RuntimeError("POST https://api.fournisseur.example/v1 clé sk-SECRET")

    services = _services(session_agent=lambda c: _Session(PASSAGE, secret))
    with caplog.at_level(logging.ERROR):
        reponse = _post(_client(services))
    assert reponse.status_code == 502
    assert reponse.json() == {"detail": REPONSE_IMPOSSIBLE}
    assert "sk-SECRET" not in reponse.text and "fournisseur.example" not in reponse.text
    assert any("sk-SECRET" in (r.exc_text or "") for r in caplog.records)


def test_question_rejetee_texte_non_envoye() -> None:
    def rejet(question: str) -> ReponseAgent:
        return ReponseAgent(
            question=question, texte="CHIFFRE INVENTÉ 42", statut_controle=StatutControle.rejete
        )

    services = _services(session_agent=lambda c: _Session(PASSAGE, rejet))
    reponse = _post(_client(services))
    assert reponse.status_code == 200
    assert "INVENTÉ" not in reponse.text
    assert reponse.json()["texte"] is None
    assert reponse.json()["badge_code"] == "rejete"


def test_question_session_reutilisee_entre_deux_questions() -> None:
    fabriques: list[int] = []

    def fabrique(c: object) -> _Session:
        fabriques.append(1)
        return _Session(PASSAGE, _ok)

    http = _client(_services(session_agent=fabrique))
    _post(http, "a")
    _post(http, "b")
    assert len(fabriques) == 1


def test_question_hors_perimetre() -> None:
    services = _services(
        session_agent=lambda c: _Session(
            PASSAGE, lambda q: ReponseAgent(question=q, texte=HORS_PERIMETRE)
        )
    )
    vue = _post(_client(services)).json()
    assert vue["badge_code"] == "hors_perimetre"
    assert vue["outils"] == []


# --- Rejeu ---


def test_rejeu_nominal_et_bornes() -> None:
    http = _client(repli=True)
    premiere = http.get("/api/agent/enregistrees/0")
    assert premiere.status_code == 200
    assert premiere.json()["texte"] == "T0"
    assert premiere.json()["mention_repli"] == (
        f"Mode repli : réponse enregistrée le 12/10/2026 sur le Passage {PASSAGE}, rejouée sans LLM"
    )
    assert http.get("/api/agent/enregistrees/1").json()["texte"] == "T1"
    for rang in ("2", "-1", "99"):
        reponse = http.get(f"/api/agent/enregistrees/{rang}")
        assert reponse.status_code == 404, rang
        assert reponse.json()["detail"] == "Question enregistrée inconnue."
    assert http.get("/api/agent/enregistrees/abc").status_code == 422


def test_rejeu_mode_reel_409() -> None:
    reponse = _client().get("/api/agent/enregistrees/0")
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == SEULEMENT_REPLI


def test_rejeu_sans_passage_409() -> None:
    reponse = _client(repli=True, lire=lambda _r: None).get("/api/agent/enregistrees/0")
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == agent.AUCUN_PASSAGE


def test_rejeu_passage_etranger_409() -> None:
    def refus(passage_id: str) -> tuple[ReponseAgentEnregistree, ...]:
        raise UsineErreur(f"passage {passage_id} étranger")

    http = _client(_services(reponses_repli=refus), repli=True)
    reponse = http.get("/api/agent/enregistrees/0")
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == f"{agent.REFUS_REPLI} : passage {PASSAGE} étranger"
    vue = http.get("/api/agent").json()
    assert vue["erreur"] == f"{agent.REFUS_REPLI} : passage {PASSAGE} étranger"
    assert vue["questions"] == []


def test_rejeu_lecture_oserror_503() -> None:
    def droits(_p: str) -> tuple[ReponseAgentEnregistree, ...]:
        raise PermissionError(13, "refusé")

    reponse = _client(_services(reponses_repli=droits), repli=True).get(
        "/api/agent/enregistrees/0"
    )
    assert reponse.status_code == 503
    assert reponse.json()["detail"].startswith("Lecture du Passage impossible")


# --- GET /api/agent ---


def test_agent_selon_mode() -> None:
    reel = _client().get("/api/agent").json()
    assert reel["mode"] == "reel"
    assert reel["saisie"]["bouton"] == "Envoyer"
    assert [q["question"] for q in reel["questions"]] == ["S1", "S2"]
    repli = _client(repli=True).get("/api/agent").json()
    assert repli["mode"] == "repli"
    assert repli["saisie"] is None
    assert repli["message_repli"] == agent.MESSAGE_REPLI
    assert [(q["rang"], q["question"]) for q in repli["questions"]] == [(0, "Q0"), (1, "Q1")]


def test_agent_lecture_impossible_en_bandeau() -> None:
    def casse(_r: bool) -> object:
        raise UsineErreur("illisible")

    def droits(_r: bool) -> object:
        raise PermissionError(13, "refusé")

    assert _client(lire=casse).get("/api/agent").json()["erreur"] == "illisible"
    erreur = _client(lire=droits).get("/api/agent").json()["erreur"]
    assert erreur.startswith("Lecture du Passage impossible")


# --- Avant / après ---


def test_avant_apres_periodes_et_validation() -> None:
    http = _client()
    assert http.get("/api/avant-apres").json()["periode"] == "rapport"
    vue = http.get("/api/avant-apres?periode=cumul").json()
    assert vue["periode"] == "cumul"
    assert vue["manuel"]["valeurs"] == {"rapport": "120 min", "cumul": "600 min"}
    assert vue["chaine"]["valeurs"] == {"rapport": "4,4 s", "cumul": "22 s"}
    assert http.get("/api/avant-apres?periode=semaine").status_code == 422


def test_avant_apres_repli_transmis_aux_manifestes() -> None:
    recus: list[bool] = []

    def manifestes(repli: bool) -> tuple[ManifestePassage | None, ManifestePassage | None]:
        recus.append(repli)
        return None, None

    for repli in (False, True):
        vue = _client(_services(manifestes_avant_apres=manifestes), repli=repli).get(
            "/api/avant-apres"
        )
        assert vue.json()["message"] == avant_apres.AUCUN_PASSAGE
    assert recus == [False, True]


def test_avant_apres_config_absente_et_invalide() -> None:
    absente = _client(_services(config_demo=lambda: None)).get("/api/avant-apres").json()
    assert absente["avertissements"] == [avant_apres.CONFIG_ABSENTE]
    assert absente["manuel"] is None

    def invalide() -> ConfigDemo:
        raise UsineErreur("temps_manuel négatif")

    vue = _client(_services(config_demo=invalide)).get("/api/avant-apres").json()
    assert vue["erreur"] == "Configuration de la démo invalide : temps_manuel négatif"
    assert vue["tableau"] is None


def test_avant_apres_lecture_manifestes_en_erreur() -> None:
    def casse(_r: bool) -> tuple[None, None]:
        raise UsineErreur("manifeste illisible")

    def droits(_r: bool) -> tuple[None, None]:
        raise PermissionError(13, "refusé")

    http = _client(_services(manifestes_avant_apres=casse))
    assert http.get("/api/avant-apres").json()["erreur"] == "manifeste illisible"
    http = _client(_services(manifestes_avant_apres=droits))
    assert http.get("/api/avant-apres").json()["erreur"].startswith("Lecture du Passage impossible")


# --- Pseudonymisation ---


def test_pseudonymisation_selection() -> None:
    http = _client()
    defaut = http.get("/api/pseudonymisation").json()
    assert defaut["tickets"] == ["DEMO-1", "DEMO-17"]
    assert defaut["ticket"]["cle"] == "DEMO-1"
    choisi = http.get("/api/pseudonymisation?ticket=DEMO-17").json()
    assert choisi["original"] == "dix-sept"
    assert choisi["pseudonymise"] == "DIX-SEPT"
    inconnu = http.get("/api/pseudonymisation?ticket=NOPE").json()
    assert inconnu["erreur"] == "Le ticket NOPE n'a pas de description non vide dans ce Passage."
    assert inconnu["tickets"] == ["DEMO-1", "DEMO-17"]


def test_pseudonymisation_sans_passage_et_lecture_en_erreur() -> None:
    vide = _client(lire=lambda _r: None).get("/api/pseudonymisation").json()
    assert vide["message"] == carte.AUCUN_PASSAGE
    assert vide["lien_message"] == {"libelle": "Lancer la Chaîne", "url": "/chaine"}

    def casse(_r: bool) -> object:
        raise UsineErreur("illisible")

    assert _client(lire=casse).get("/api/pseudonymisation").json()["erreur"] == "illisible"

    class _TableCassee(_Consultation):
        def textes_tickets(self) -> pl.DataFrame:
            raise PermissionError(13, "refusé")

    vue = _client(lire=lambda _r: _TableCassee()).get("/api/pseudonymisation").json()
    assert vue["erreur"].startswith("Lecture du Passage impossible")


def test_pseudonymisation_moteur_en_echec_nomme() -> None:
    def apercu() -> Callable[[str], str]:
        raise ValueError("spaCy fr_core_news_md absent\ndétail")

    vue = _client(_services(apercu_pseudonymisation=apercu)).get("/api/pseudonymisation").json()
    assert vue["erreur"] == (
        "Moteur de Pseudonymisation indisponible (Presidio ou modèle spaCy) :"
        " ValueError : spaCy fr_core_news_md absent"
    )
    assert vue["tickets"] == ["DEMO-1", "DEMO-17"]
    assert vue["pseudonymise"] is None


# --- Outillage ---


def test_outillage_etats() -> None:
    vue = _client().get("/api/outillage").json()
    assert vue["erreur"] is None and vue["message"] is None
    assert 'class="pastille pastille--oui">Oui</span>' in vue["html"]
    absente = _client(_services(lire_fiche=lambda: None)).get("/api/outillage").json()
    assert absente["html"] is None
    assert "Fiche absente" in absente["message"]


def test_outillage_fiche_illisible() -> None:
    def octets() -> str:
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    def droits() -> str:
        raise PermissionError(13, "refusé")

    for lire in (octets, droits):
        vue = _client(_services(lire_fiche=lire)).get("/api/outillage").json()
        assert vue["erreur"].startswith("Lecture de la fiche outillage impossible : ")
        assert vue["html"] is None


def test_outillage_html_brut_echappe_via_la_route() -> None:
    fiche = "## A\n\n<script>alert(1)</script>\n"
    vue = _client(_services(lire_fiche=lambda: fiche)).get("/api/outillage").json()
    assert "<script" not in vue["html"]
    assert "&lt;script&gt;" in vue["html"]

