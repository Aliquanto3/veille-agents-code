"""Renforcement de la Story 7.15 : valeurs exactes, bornes et branches d'erreur."""

from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from tests.unit.ui.test_chaine import (
    Banc,
    Lanceur,
    _evenement,
    ecrire_progression,
)
from usine.contrats.passage import Etape, StatutEtape
from usine.ui import chaine as module_chaine
from usine.ui import textes
from usine.ui.chaine import JOURNAL_ATTENTE, JOURNAL_VIDE, GestionChaine
from usine.ui.serveur import HOTE, creer_application
from usine.ui.vues import DemandeMode


@pytest.fixture
def racine(tmp_path: Path) -> Path:
    return tmp_path


def _en_cours(racine: Path, *lignes: str) -> Banc:
    banc = Banc(racine)
    banc.etat()
    assert banc.lancer().status_code == 202
    ecrire_progression(racine, *lignes)
    return banc


def test_intervalle_exact(racine: Path) -> None:
    assert textes.INTERVALLE_SONDAGE == 1.0
    assert Banc(racine).etat()["intervalle_ms"] == 1000


def test_numeros_d_etapes_commencent_a_un(racine: Path) -> None:
    etapes = Banc(racine).etat()["etapes"]
    assert [e["numero"] for e in etapes] == list(range(1, 11))


def test_journal_vide_selon_le_statut(racine: Path) -> None:
    banc = Banc(racine)
    assert banc.etat()["journal_vide"] == JOURNAL_ATTENTE
    banc.lancer()
    vue = banc.etat()
    assert vue["statut"] == "en_cours"
    assert vue["journal_vide"] == JOURNAL_VIDE


@pytest.mark.parametrize("code", [-1, -9])
def test_code_negatif_est_un_echec(racine: Path, code: int) -> None:
    banc = Banc(racine)
    banc.lancer()
    banc.lanceur.finir(code)
    vue = banc.etat()
    assert vue["statut"] == "echec"
    assert vue["bandeau"]["variante"] == "erreur"
    assert f"(code {code})" in vue["bandeau"]["texte"]
    assert vue["annonce"].startswith("Échec de la Chaîne")
    assert vue["bouton_lancement"]["libelle"] == "Relancer la Chaîne"


def test_code_zero_est_un_succes(racine: Path) -> None:
    banc = Banc(racine)
    banc.lancer()
    banc.lanceur.finir(0)
    vue = banc.etat()
    assert vue["statut"] == "terminee"
    assert vue["bandeau"]["variante"] == "succes"


@pytest.mark.parametrize(
    ("etape", "rang"), [(Etape.extraction, 1), (Etape.instantanes, 2), (Etape.kpi, 3)]
)
def test_annonce_rang_de_l_etape(racine: Path, etape: Etape, rang: int) -> None:
    banc = _en_cours(racine, _evenement(etape, StatutEtape.en_cours))
    assert banc.etat()["annonce"] == f"Étape {rang} sur 10 : {etape.value}"


def test_etape_echouee_n_est_plus_courante(racine: Path) -> None:
    banc = _en_cours(
        racine,
        _evenement(Etape.kpi, StatutEtape.en_cours),
        _evenement(Etape.kpi, StatutEtape.echouee, 1),
    )
    assert banc.etat()["annonce"] == ""


def test_evenement_termine_sans_etape_courante(racine: Path) -> None:
    banc = _en_cours(racine, _evenement(Etape.extraction, StatutEtape.reussie))
    assert banc.etat()["annonce"] == ""


def test_fin_d_une_autre_etape_garde_la_courante(racine: Path) -> None:
    banc = _en_cours(
        racine,
        _evenement(Etape.kpi, StatutEtape.en_cours),
        _evenement(Etape.narration, StatutEtape.reussie, 1),
    )
    assert banc.etat()["annonce"] == "Étape 3 sur 10 : kpi"


def test_echec_de_demarrage_ferme_le_fichier_d_erreurs(
    racine: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ouverts: list[Any] = []
    vrai = module_chaine.lancement.fichier_erreurs

    def suivi() -> Any:
        fichier = vrai()
        ouverts.append(fichier)
        return fichier

    monkeypatch.setattr(module_chaine.lancement, "fichier_erreurs", suivi)

    def echec(*_a: Any, **_o: Any) -> None:
        raise OSError("introuvable")

    GestionChaine(racine, popen=cast(Any, echec)).lancer(False)
    assert len(ouverts) == 1
    assert ouverts[0].closed


def test_echec_avant_fichier_d_erreurs_sans_exception(
    racine: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def echec(_racine: Path) -> None:
        raise OSError("illisible")

    monkeypatch.setattr(module_chaine.progression, "fichiers_progression", echec)
    gestion = GestionChaine(racine, popen=cast(Any, Lanceur()))
    gestion.lancer(False)  # ne lève pas (AttributeError sur un fichier d'erreurs absent)
    assert gestion.en_cours() is False


def test_demande_mode_immuable() -> None:
    demande = DemandeMode(mode="repli")
    with pytest.raises(ValidationError):
        demande.mode = "reel"  # type: ignore[misc]


def test_origine_de_netloc_different_refusee_et_identique_acceptee() -> None:
    application = creer_application(
        repli=False, lire_manifeste=lambda _r: None, lire_consultation=lambda _r: None
    )
    http = TestClient(application, base_url=f"http://{HOTE}:8000")
    refuse = http.post("/api/mode", json={"mode": "repli"}, headers={"origin": f"http://{HOTE}"})
    assert refuse.status_code == 403
    accepte = http.post(
        "/api/mode", json={"mode": "repli"}, headers={"origin": f"http://{HOTE}:8000"}
    )
    assert accepte.status_code == 200
