"""Renforcement Story 7.15 : valeurs exactes, bornes et branches d'erreur de la Chaîne."""

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from tests.unit.ui.test_chaine import Banc, _evenement, ecrire_progression
from usine.contrats.passage import Etape, StatutEtape
from usine.ui import lancement, textes
from usine.ui.chaine import JOURNAL_ATTENTE, JOURNAL_VIDE, GestionChaine
from usine.ui.vues import DemandeMode


class _Fichier:
    def __init__(self) -> None:
        self.ferme = False

    def close(self) -> None:
        self.ferme = True


@pytest.fixture
def racine_(tmp_path: Path) -> Path:
    return tmp_path


def test_echec_de_popen_ferme_le_fichier_d_erreurs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fichier = _Fichier()
    monkeypatch.setattr(lancement, "fichier_erreurs", lambda: fichier)

    def popen(*_a: Any, **_k: Any) -> Any:
        raise OSError("boom")

    GestionChaine(tmp_path, popen=popen).lancer(False)
    assert fichier.ferme is True


def test_echec_de_creation_du_fichier_d_erreurs_ne_leve_pas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def impossible() -> Any:
        raise OSError("disque plein")

    monkeypatch.setattr(lancement, "fichier_erreurs", impossible)
    gestion = GestionChaine(tmp_path)
    gestion.lancer(False)
    vue = gestion.vue(False, None)
    assert vue.erreur == "Lancement de la Chaîne impossible : disque plein"
    assert vue.statut == "attente"


def test_code_negatif_est_un_echec(racine_: Path) -> None:
    banc = Banc(racine_)
    banc.lancer()
    banc.lanceur.finir(-9)
    vue = banc.etat()
    assert vue["statut"] == "echec"
    assert vue["bandeau"]["variante"] == "erreur"
    assert "(code -9)" in vue["bandeau"]["texte"]
    assert vue["annonce"].startswith("Échec de la Chaîne")
    assert vue["bouton_lancement"]["libelle"] == "Relancer la Chaîne"


def test_code_zero_est_un_succes(racine_: Path) -> None:
    banc = Banc(racine_)
    banc.lancer()
    banc.lanceur.finir(0)
    vue = banc.etat()
    assert vue["statut"] == "terminee"
    assert vue["bandeau"]["variante"] == "succes"


def test_numeros_d_etapes_partent_de_un(racine_: Path) -> None:
    vue = Banc(racine_).etat()
    assert [e["numero"] for e in vue["etapes"]] == list(range(1, 11))


def test_journal_vide_selon_le_statut(racine_: Path) -> None:
    banc = Banc(racine_)
    assert banc.etat()["journal_vide"] == JOURNAL_ATTENTE
    banc.lancer()
    assert banc.etat()["journal_vide"] == JOURNAL_VIDE


@pytest.mark.parametrize(("etape", "rang"), [(Etape.extraction, 1), (Etape.kpi, 3)])
def test_annonce_rang_de_l_etape(racine_: Path, etape: Etape, rang: int) -> None:
    banc = Banc(racine_)
    banc.lancer()
    ecrire_progression(racine_, _evenement(etape, StatutEtape.en_cours))
    assert banc.etat()["annonce"] == f"Étape {rang} sur 10 : {etape.value}"


def test_etape_echouee_n_est_plus_courante(racine_: Path) -> None:
    banc = Banc(racine_)
    banc.lancer()
    ecrire_progression(
        racine_,
        _evenement(Etape.extraction, StatutEtape.en_cours),
        _evenement(Etape.extraction, StatutEtape.echouee, 1),
    )
    assert banc.etat()["annonce"] == ""


def test_fin_d_une_autre_etape_ne_termine_pas_la_courante(racine_: Path) -> None:
    banc = Banc(racine_)
    banc.lancer()
    ecrire_progression(
        racine_,
        _evenement(Etape.extraction, StatutEtape.en_cours),
        _evenement(Etape.kpi, StatutEtape.reussie, 1),
    )
    assert banc.etat()["annonce"] == "Étape 1 sur 10 : extraction"


def test_intervalle_de_sondage_une_seconde(racine_: Path) -> None:
    assert textes.INTERVALLE_SONDAGE == 1.0
    assert Banc(racine_).etat()["intervalle_ms"] == 1000


def test_demande_mode_est_figee() -> None:
    demande = DemandeMode(mode="reel")
    with pytest.raises(ValidationError):
        demande.mode = "repli"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("origine", "host", "statut"),
    [
        ("http://127.0.0.1", "127.0.0.1:8000", 403),
        ("http://127.0.0.1:8000", "127.0.0.1:8000", 200),
        ("http://127.0.0.1:9", "127.0.0.1:8000", 403),
    ],
)
def test_origine_doit_egaler_l_hote_et_le_port(
    racine_: Path, origine: str, host: str, statut: int
) -> None:
    banc = Banc(racine_)
    reponse = banc.http.post(
        "/api/mode", json={"mode": "repli"}, headers={"origin": origine, "host": host}
    )
    assert reponse.status_code == statut
