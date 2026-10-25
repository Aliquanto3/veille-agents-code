"""Renforcement de la Story 7.15 : `GestionChaine`, annonces, journal, serveur (valeurs exactes)."""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from tests.unit.ui.test_avant_apres import manifeste
from tests.unit.ui.test_chaine import PASSAGE, Lanceur, ecrire_progression
from usine.contrats.passage import Etape, EvenementProgression, StatutEtape
from usine.ui import chaine as mod
from usine.ui.chaine import (
    AUCUN_PASSAGE_LANCE,
    AUCUN_PASSAGE_REPLI,
    DESCRIPTIONS,
    JOURNAL_ATTENTE,
    JOURNAL_VIDE,
    LIBELLE_LANCER,
    LIBELLE_RELANCER,
    MESSAGE_SUCCES,
    MOTIF_LANCEMENT_EN_COURS,
    MOTIF_MODE_EN_COURS,
    MOTIF_RACINE,
    GestionChaine,
    LancementRefuse,
    _annonce,
    _etape_courante,
    _journal,
    _lieu_echec,
    _sans_marques,
    vue_dernier_passage,
)
from usine.ui.progression import AUCUN_RAPPORT
from usine.ui.serveur import HOTE, creer_application
from usine.ui.textes import LANCEMENT_REPLI, LIGNES_ERREUR_MAX
from usine.ui.vues import DemandeMode

T0 = datetime(2026, 10, 12, 7, 30, tzinfo=UTC)


def ev(etape: Etape, statut: StatutEtape, s: float = 0.0, message: str = "") -> Any:
    return EvenementProgression(
        passage_id=PASSAGE,
        etape=etape,
        statut=statut,
        horodatage=T0 + timedelta(seconds=s),
        message=message,
    )


def gestion(racine: Path | None) -> tuple[GestionChaine, Lanceur]:
    lanceur = Lanceur()
    return GestionChaine(racine, popen=cast(Any, lanceur)), lanceur


# --- constantes et texte ---


def test_descriptions_couvrent_les_dix_etapes() -> None:
    assert list(DESCRIPTIONS) == list(Etape)
    assert len(DESCRIPTIONS) == 10
    assert all(DESCRIPTIONS.values())


def test_sans_marques() -> None:
    assert _sans_marques("a `b` c``") == "a b c"
    assert "`" not in _sans_marques(LANCEMENT_REPLI)


@given(st.text())
def test_sans_marques_propriete(texte: str) -> None:
    resultat = _sans_marques(texte)
    assert "`" not in resultat
    assert len(resultat) == len(texte) - texte.count("`")


# --- lancement ---


def test_lancer_en_repli_refuse_avec_motif_sans_marques(tmp_path: Path) -> None:
    g, lanceur = gestion(tmp_path)
    with pytest.raises(LancementRefuse) as exc:
        g.lancer(True)
    assert str(exc.value) == _sans_marques(LANCEMENT_REPLI)
    assert lanceur.appels == []


@pytest.mark.parametrize("racine", [None, "absente", "fichier"])
def test_lancer_racine_invalide(tmp_path: Path, racine: str | None) -> None:
    chemin: Path | None
    if racine is None:
        chemin = None
    elif racine == "absente":
        chemin = tmp_path / "absente"
    else:
        chemin = tmp_path / "f"
        chemin.write_text("x")
    g, lanceur = gestion(chemin)
    with pytest.raises(LancementRefuse, match="racine du projet est introuvable"):
        g.lancer(False)
    assert lanceur.appels == []
    vue = g.vue(False, None)
    assert vue.bouton_lancement.bloque is True
    assert vue.bouton_lancement.motif == MOTIF_RACINE
    assert vue.statut == "attente"


def test_lancer_deux_fois_refuse_un_seul_processus(tmp_path: Path) -> None:
    g, lanceur = gestion(tmp_path)
    g.lancer(False)
    assert g.en_cours() is True
    with pytest.raises(LancementRefuse) as exc:
        g.lancer(False)
    assert str(exc.value) == MOTIF_LANCEMENT_EN_COURS
    assert len(lanceur.appels) == 1


def test_motif_en_cours_prime_sur_repli(tmp_path: Path) -> None:
    g, _ = gestion(tmp_path)
    g.lancer(False)
    vue = g.vue(True, None)
    assert vue.bouton_lancement.motif == MOTIF_LANCEMENT_EN_COURS


def test_relance_possible_apres_fin(tmp_path: Path) -> None:
    g, lanceur = gestion(tmp_path)
    g.lancer(False)
    lanceur.finir(0)
    assert g.en_cours() is False
    g.lancer(False)
    assert len(lanceur.appels) == 2
    assert g.en_cours() is True


def test_oserror_au_demarrage_vue_attente_avec_erreur(tmp_path: Path) -> None:
    def popen(*_a: Any, **_k: Any) -> Any:
        raise OSError("introuvable")

    g = GestionChaine(tmp_path, popen=popen)
    g.lancer(False)
    vue = g.vue(False, None)
    assert vue.statut == "attente"
    assert vue.erreur == "Lancement de la Chaîne impossible : introuvable"
    assert vue.bouton_lancement.bloque is False
    assert g.en_cours() is False
    # un lancement réussi efface l'erreur précédente
    g2, _ = gestion(tmp_path)
    g2.lancer(False)
    assert g2.vue(False, None).erreur is None


def test_oserror_sur_fichiers_progression_est_consigne(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boum(_racine: Path) -> Any:
        raise OSError("disque")

    monkeypatch.setattr(mod.progression, "fichiers_progression", boum)
    g, lanceur = gestion(tmp_path)
    g.lancer(False)
    assert lanceur.appels == []
    assert "disque" in (g.vue(False, None).erreur or "")


# --- vue : statuts, boutons, bandeaux ---


def test_vue_attente_textes(tmp_path: Path) -> None:
    g, _ = gestion(tmp_path)
    vue = g.vue(False, None)
    assert vue.journal_vide == JOURNAL_ATTENTE
    assert vue.message_dernier_passage == AUCUN_PASSAGE_LANCE
    assert vue.bouton_lancement.libelle == LIBELLE_LANCER
    assert vue.bouton_mode.bloque is False
    assert vue.bouton_mode.motif is None
    assert vue.dernier_passage is None
    assert vue.total == 10
    assert vue.etapes[0].numero == 1 and vue.etapes[-1].numero == 10


def test_vue_repli_textes(tmp_path: Path) -> None:
    g, _ = gestion(tmp_path)
    vue = g.vue(True, None)
    assert vue.message_dernier_passage == AUCUN_PASSAGE_REPLI
    assert vue.bouton_mode.libelle == "Revenir au Mode réel"
    assert vue.mode_cible == "reel"
    assert vue.bouton_lancement.bloque is True
    assert vue.bouton_lancement.motif == _sans_marques(LANCEMENT_REPLI)


def test_vue_en_cours_sans_fichier_annonce_et_journal_vide(tmp_path: Path) -> None:
    g, _ = gestion(tmp_path)
    g.lancer(False)
    vue = g.vue(False, None)
    assert vue.statut == "en_cours"
    assert vue.annonce == "Chaîne en cours…"
    assert vue.journal == []
    assert vue.journal_vide == JOURNAL_VIDE
    assert vue.bandeau is None
    assert vue.bouton_mode.bloque is True
    assert vue.bouton_mode.motif == MOTIF_MODE_EN_COURS


def test_vue_succes(tmp_path: Path) -> None:
    g, lanceur = gestion(tmp_path)
    g.lancer(False)
    lanceur.finir(0)
    vue = g.vue(False, manifeste())
    assert vue.statut == "terminee"
    assert vue.en_cours is False
    assert vue.annonce == MESSAGE_SUCCES
    assert vue.bouton_lancement.libelle == LIBELLE_RELANCER
    assert vue.bouton_lancement.bloque is False
    assert vue.bandeau is not None
    assert vue.bandeau.variante == "succes"
    assert vue.bandeau.texte == MESSAGE_SUCCES
    assert vue.bandeau.lignes == []
    assert vue.bandeau.complement is None
    assert vue.bandeau.lien is not None
    assert (vue.bandeau.lien.libelle, vue.bandeau.lien.url) == ("Voir la carte météo", "/")


def test_echec_sans_sortie_aucun_message_et_hors_etape(tmp_path: Path) -> None:
    g, lanceur = gestion(tmp_path)
    g.lancer(False)
    lanceur.finir(3)
    vue = g.vue(False, None)
    assert vue.statut == "echec"
    assert vue.bouton_lancement.libelle == LIBELLE_RELANCER
    assert vue.bandeau is not None
    assert vue.bandeau.variante == "erreur"
    assert vue.bandeau.texte == "Échec de la Chaîne hors d'une étape (code 3)."
    assert vue.bandeau.lignes == ["aucun message"]
    assert vue.bandeau.complement == AUCUN_RAPPORT
    assert vue.bandeau.lien is None
    assert vue.annonce == "Échec de la Chaîne hors d'une étape."


def test_echec_avec_etape_et_lignes(tmp_path: Path) -> None:
    ecrire_progression(tmp_path)  # fichier présent avant le lancement : ignoré
    g, lanceur = gestion(tmp_path)
    lanceur.sortie_erreur = b"boum\n"
    g.lancer(False)
    chemin = tmp_path / "sorties" / "progression" / "20261012T073100Z-bbbbbb.jsonl"
    chemin.write_text(
        ev(Etape.extraction, StatutEtape.en_cours).model_dump_json()
        + "\n"
        + ev(Etape.extraction, StatutEtape.echouee, 2).model_dump_json()
        + "\n",
        encoding="utf-8",
    )
    lanceur.finir(1)
    vue = g.vue(False, None)
    assert vue.bandeau is not None
    assert vue.bandeau.texte == "Échec de la Chaîne à l'étape « extraction » (code 1)."
    assert vue.bandeau.lignes == ["boum"]
    assert vue.etapes[0].etat == "echouee"
    assert vue.etapes[0].libelle_etat == "Échec"
    assert vue.etapes[0].duree == "2 s"
    assert vue.terminees == 1
    assert vue.compteur == "1 / 10"


@pytest.mark.parametrize("n", [0, 1, 19, 20, 21, 45])
def test_echec_garde_les_dernieres_lignes_derreur(tmp_path: Path, n: int) -> None:
    g, lanceur = gestion(tmp_path)
    lanceur.sortie_erreur = "".join(f"l{i}\n" for i in range(n)).encode()
    g.lancer(False)
    lanceur.finir(2)
    vue = g.vue(False, None)
    assert vue.bandeau is not None
    attendu = [f"l{i}" for i in range(n)][-LIGNES_ERREUR_MAX:] or ["aucun message"]
    assert vue.bandeau.lignes == attendu
    assert len(vue.bandeau.lignes) <= LIGNES_ERREUR_MAX


def test_erreur_standard_lue_une_fois(tmp_path: Path) -> None:
    g, lanceur = gestion(tmp_path)
    lanceur.sortie_erreur = b"a\nb\n"
    g.lancer(False)
    lanceur.finir(1)
    premiere = g.vue(False, None)
    seconde = g.vue(False, None)
    assert premiere.bandeau == seconde.bandeau
    assert premiere.bandeau is not None and premiere.bandeau.lignes == ["a", "b"]


def test_progression_invalide_signalee_sondage_maintenu(tmp_path: Path) -> None:
    g, _ = gestion(tmp_path)
    g.lancer(False)
    ecrire_progression(tmp_path, "pas du json")
    vue = g.vue(False, None)
    assert vue.statut == "en_cours"
    assert vue.erreur is not None and "progression invalide" in vue.erreur
    assert vue.etapes[0].etat == "en_attente"


def test_ligne_partielle_ignoree(tmp_path: Path) -> None:
    g, _ = gestion(tmp_path)
    g.lancer(False)
    complete = ev(Etape.extraction, StatutEtape.en_cours).model_dump_json()
    ecrire_progression(tmp_path, complete, partielle='{"passage_id": "x')
    vue = g.vue(False, None)
    assert vue.erreur is None
    assert vue.etapes[0].etat == "en_cours"
    assert len(vue.journal) == 1


def test_etapes_sautee_et_en_cours(tmp_path: Path) -> None:
    g, _ = gestion(tmp_path)
    g.lancer(False)
    ecrire_progression(
        tmp_path,
        ev(Etape.extraction, StatutEtape.en_cours, 0).model_dump_json(),
        ev(Etape.extraction, StatutEtape.reussie, 1.25).model_dump_json(),
        ev(Etape.instantanes, StatutEtape.sautee, 1.5).model_dump_json(),
        ev(Etape.kpi, StatutEtape.en_cours, 2).model_dump_json(),
    )
    vue = g.vue(False, None)
    assert [e.etat for e in vue.etapes[:4]] == ["reussie", "sautee", "en_cours", "en_attente"]
    assert vue.terminees == 2
    assert vue.compteur == "2 / 10"
    assert vue.etapes[0].duree in {"1,2 s", "1,3 s"}
    assert vue.etapes[1].duree is None  # sautée sans en_cours
    assert vue.etapes[2].duree is None
    assert vue.etapes[2].description == DESCRIPTIONS[Etape.kpi]
    assert vue.annonce == "Étape 3 sur 10 : kpi"


def test_vue_intervalle_ms() -> None:
    assert GestionChaine(None).vue(False, None).intervalle_ms == 1000


# --- fonctions pures ---


def test_annonce_cas() -> None:
    assert _annonce("attente", ()) == ""
    assert _annonce("terminee", ()) == MESSAGE_SUCCES
    assert _annonce("en_cours", ()) == "Chaîne en cours…"
    entre_deux = (
        ev(Etape.extraction, StatutEtape.en_cours),
        ev(Etape.extraction, StatutEtape.reussie),
    )
    assert _annonce("en_cours", entre_deux) == ""
    assert _annonce("en_cours", entre_deux[:1]) == "Étape 1 sur 10 : extraction"
    assert _annonce("echec", (ev(Etape.rendu, StatutEtape.echouee),)) == (
        "Échec de la Chaîne à l'étape « rendu »."
    )


@given(st.sampled_from(list(Etape)))
def test_annonce_numero_etape(etape: Etape) -> None:
    texte = _annonce("en_cours", (ev(etape, StatutEtape.en_cours),))
    assert texte == f"Étape {list(Etape).index(etape) + 1} sur 10 : {etape.value}"


def test_etape_courante() -> None:
    assert _etape_courante(()) is None
    e1, e2 = Etape.extraction, Etape.kpi
    assert _etape_courante((ev(e1, StatutEtape.en_cours),)) is e1
    assert _etape_courante((ev(e1, StatutEtape.en_cours), ev(e1, StatutEtape.reussie))) is None
    # la fin d'une autre étape ne clôt pas l'étape courante
    assert _etape_courante((ev(e1, StatutEtape.en_cours), ev(e2, StatutEtape.sautee))) is e1


def test_lieu_echec() -> None:
    assert _lieu_echec(()) == "hors d'une étape"
    assert _lieu_echec((ev(Etape.kpi, StatutEtape.echouee),)) == "à l'étape « kpi »"


def test_journal_recent_en_haut_et_message() -> None:
    evenements = (
        ev(Etape.extraction, StatutEtape.en_cours, 0),
        ev(Etape.extraction, StatutEtape.echouee, 5, message="oups"),
    )
    lignes = _journal(evenements)
    assert [(entree.horodatage, entree.texte) for entree in lignes] == [
        ("07:30:05", "extraction : Échec · oups"),
        ("07:30:00", "extraction : En cours"),
    ]


def test_journal_horodatage_converti_en_utc() -> None:
    from datetime import timezone

    instant = datetime(2026, 10, 12, 9, 5, 7, tzinfo=timezone(timedelta(hours=2)))
    evenement = EvenementProgression(
        passage_id=PASSAGE, etape=Etape.kpi, statut=StatutEtape.reussie, horodatage=instant
    )
    assert _journal((evenement,))[0].horodatage == "07:05:07"


@given(st.lists(st.sampled_from(list(Etape)), max_size=15))
def test_journal_propriete(etapes: list[Etape]) -> None:
    evenements = tuple(ev(e, StatutEtape.en_cours, i) for i, e in enumerate(etapes))
    lignes = _journal(evenements)
    assert len(lignes) == len(evenements)
    assert [ligne.texte for ligne in lignes] == [f"{e.value} : En cours" for e in reversed(etapes)]


def test_vue_dernier_passage_valeurs_exactes() -> None:
    vue = vue_dernier_passage(manifeste(secondes=3.4, passage_id="20261012T073000Z-abc123"))
    assert vue.lignes == [
        "Date d'arrêté 09/10/2026 · durée 3,4 s",
        "0 tickets extraits",
        "Passage 20261012T073000Z-abc123",
    ]


@given(st.floats(min_value=0, max_value=10_000, allow_nan=False))
@settings(max_examples=40)
def test_vue_dernier_passage_forme(secondes: float) -> None:
    lignes = vue_dernier_passage(manifeste(secondes=secondes)).lignes
    assert len(lignes) == 3
    assert lignes[0].endswith(" s")
    assert lignes[2].startswith("Passage ")


# --- serveur ---


def test_demande_mode_valide() -> None:
    assert DemandeMode(mode="repli").mode == "repli"
    for corps in ({"mode": "autre"}, {}, {"mode": "reel", "x": 1}):
        with pytest.raises(ValidationError):
            DemandeMode.model_validate(corps)


def client(racine: Path | None, repli: bool = False) -> tuple[TestClient, Lanceur]:
    g, lanceur = gestion(racine)
    app = creer_application(
        repli=repli,
        lire_manifeste=lambda _r: None,
        lire_consultation=lambda _r: None,
        chaine=g,
    )
    return TestClient(app, base_url=f"http://{HOTE}"), lanceur


def test_serveur_lancement_repli_409(tmp_path: Path) -> None:
    http, lanceur = client(tmp_path, repli=True)
    reponse = http.post("/api/chaine")
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == _sans_marques(LANCEMENT_REPLI)
    assert lanceur.appels == []


def test_serveur_sans_gestion_racine_absente_409() -> None:
    app = creer_application(
        repli=False, lire_manifeste=lambda _r: None, lire_consultation=lambda _r: None
    )
    reponse = TestClient(app, base_url=f"http://{HOTE}").post("/api/chaine")
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == MOTIF_RACINE


def test_serveur_mode_409_pendant_chaine_et_422(tmp_path: Path) -> None:
    http, lanceur = client(tmp_path)
    assert http.post("/api/chaine").status_code == 202
    reponse = http.post("/api/mode", json={"mode": "repli"})
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == MOTIF_MODE_EN_COURS
    assert http.post("/api/chaine").status_code == 409
    assert len(lanceur.appels) == 1
    lanceur.finir(0)
    assert http.post("/api/mode", json={"mode": "repli"}).status_code == 200
    for corps in ({"mode": "x"}, {}, {"mode": "reel", "extra": 1}):
        assert http.post("/api/mode", json=corps).status_code == 422


def test_serveur_bascule_aller_retour(tmp_path: Path) -> None:
    http, _ = client(tmp_path)
    assert http.get("/api/chaine").json()["mode_cible"] == "repli"
    assert http.post("/api/mode", json={"mode": "repli"}).status_code == 200
    vue = http.get("/api/chaine").json()
    assert vue["mode_cible"] == "reel"
    assert vue["bouton_lancement"]["bloque"] is True
    assert http.post("/api/mode", json={"mode": "reel"}).status_code == 200
    assert http.get("/api/chaine").json()["mode_cible"] == "repli"


@pytest.mark.parametrize("route", ["/api/chaine", "/api/mode"])
@pytest.mark.parametrize(
    ("origine", "code"),
    [
        (f"http://{HOTE}", 200),
        ("http://localhost", 403),  # autre nom que le Host (127.0.0.1)
        ("http://evil.test", 403),
        ("null", 403),
        (f"http://{HOTE}:9999", 403),
        ("http://localhost.evil.test", 403),
    ],
)
def test_serveur_origine(tmp_path: Path, route: str, origine: str, code: int) -> None:
    http, _ = client(tmp_path)
    kwargs: dict[str, Any] = {"headers": {"Origin": origine}}
    if route == "/api/mode":
        kwargs["json"] = {"mode": "reel"}
    reponse = http.post(route, **kwargs)
    if route == "/api/chaine" and code == 200:
        code = 202
    assert reponse.status_code == code


def test_serveur_origine_localhost_avec_port_identique_au_host(tmp_path: Path) -> None:
    http, _ = client(tmp_path)
    entetes = {"Host": "localhost:8765", "Origin": "http://localhost:8765"}
    assert http.post("/api/mode", json={"mode": "reel"}, headers=entetes).status_code == 200
    autre_port = {"Host": "localhost:8765", "Origin": "http://localhost:8766"}
    assert http.post("/api/mode", json={"mode": "reel"}, headers=autre_port).status_code == 403


def test_serveur_host_forge_400(tmp_path: Path) -> None:
    http, _ = client(tmp_path)
    assert http.get("/api/chaine", headers={"Host": "evil.test"}).status_code == 400
    assert http.get("/api/chaine", headers={"Host": "localhost:8765"}).status_code == 200
    assert http.post("/api/mode", json={"mode": "reel"}, headers={"Host": "evil.test"}).status_code == 400


def test_python_executable_dans_commande(tmp_path: Path) -> None:
    g, lanceur = gestion(tmp_path)
    g.lancer(False)
    assert lanceur.appels[0][0] == [sys.executable, "-m", "usine", "rapport"]
