"""Renfort de la Story 7.15 : valeurs exactes, bornes et branches d'erreur de la Chaîne."""

from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import ValidationError

from tests.unit.ui.test_chaine import (
    Banc,
    Processus,
    _evenement,
    ecrire_progression,
)
from usine.contrats.passage import Etape, StatutEtape
from usine.ui import lancement, textes
from usine.ui.chaine import GestionChaine
from usine.ui.vues import DemandeMode


@pytest.fixture
def racine(tmp_path: Path) -> Path:
    return tmp_path


def test_echec_de_demarrage_ferme_le_fichier_d_erreurs(racine: Path) -> None:
    """M1 : le fichier d'erreurs ouvert est fermé quand le lancement échoue."""
    ouverts: list[Any] = []

    def echec(*_args: Any, **options: Any) -> Processus:
        ouverts.append(options["stderr"])
        raise OSError("introuvable")

    gestion = GestionChaine(racine, popen=cast(Any, echec))
    gestion.lancer(False)
    assert len(ouverts) == 1
    assert ouverts[0].closed is True


def test_echec_de_creation_du_fichier_d_erreurs_est_consigne(
    racine: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M1 : sans fichier d'erreurs créé, rien à fermer et l'échec est affiché, sans lever."""

    def impossible() -> Any:
        raise OSError("disque plein")

    monkeypatch.setattr(lancement, "fichier_erreurs", impossible)
    gestion = GestionChaine(racine, popen=cast(Any, None))
    gestion.lancer(False)
    vue = gestion.vue(False, None)
    assert vue.erreur == "Lancement de la Chaîne impossible : disque plein"
    assert vue.statut == "attente"


def test_etapes_numerotees_de_un_a_dix(racine: Path) -> None:
    """M3 : la numérotation commence à 1."""
    etapes = Banc(racine).etat()["etapes"]
    assert [etape["numero"] for etape in etapes] == list(range(1, 11))


def test_journal_vide_selon_le_statut(racine: Path) -> None:
    """M4 : texte d'attente avant lancement, texte de progression vide pendant la Chaîne."""
    banc = Banc(racine)
    assert banc.etat()["journal_vide"] == "En attente d'un lancement."
    assert banc.lancer().json()["journal_vide"] == "Aucun événement de progression pour l'instant."


def test_code_de_sortie_negatif_est_un_echec(racine: Path) -> None:
    """M2, M5 : un processus tué par signal (code < 0) n'est pas un succès."""
    banc = Banc(racine)
    banc.lancer()
    banc.lanceur.finir(-9)
    vue = banc.etat()
    assert vue["statut"] == "echec"
    assert vue["annonce"] == "Échec de la Chaîne hors d'une étape."
    assert vue["bandeau"]["variante"] == "erreur"
    assert vue["bandeau"]["texte"] == "Échec de la Chaîne hors d'une étape (code -9)."
    assert vue["bandeau"]["lien"] is None
    assert vue["bouton_lancement"]["libelle"] == "Relancer la Chaîne"


def test_code_zero_est_un_succes(racine: Path) -> None:
    """M2, M5 : borne exacte du succès."""
    banc = Banc(racine)
    banc.lancer()
    banc.lanceur.finir(0)
    vue = banc.etat()
    assert vue["statut"] == "terminee"
    assert vue["bandeau"]["variante"] == "succes"


def test_annonce_numero_de_l_etape_courante(racine: Path) -> None:
    """M6 : le rang annoncé est l'indice de l'étape + 1."""
    banc = Banc(racine)
    banc.lancer()
    ecrire_progression(racine, _evenement(Etape.extraction, StatutEtape.en_cours))
    assert banc.etat()["annonce"] == "Étape 1 sur 10 : extraction"
    ecrire_progression(
        racine,
        _evenement(Etape.extraction, StatutEtape.reussie),
        _evenement(Etape.instantanes, StatutEtape.reussie),
        _evenement(Etape.kpi, StatutEtape.reussie),
        _evenement(Etape.meteo, StatutEtape.en_cours),
    )
    assert banc.etat()["annonce"] == "Étape 4 sur 10 : meteo"


def test_etape_echouee_n_est_plus_courante(racine: Path) -> None:
    """M7 : seule `en_cours` ouvre une étape courante ; `echouee` la ferme."""
    banc = Banc(racine)
    banc.lancer()
    ecrire_progression(
        racine,
        _evenement(Etape.extraction, StatutEtape.en_cours),
        _evenement(Etape.extraction, StatutEtape.echouee),
    )
    assert banc.etat()["annonce"] == ""


def test_etape_courante_survit_a_l_evenement_d_une_autre_etape(racine: Path) -> None:
    """M8 : la fin d'une autre étape ne ferme pas l'étape courante."""
    banc = Banc(racine)
    banc.lancer()
    ecrire_progression(
        racine,
        _evenement(Etape.extraction, StatutEtape.en_cours),
        _evenement(Etape.instantanes, StatutEtape.reussie),
    )
    assert banc.etat()["annonce"] == "Étape 1 sur 10 : extraction"


def test_evenement_termine_sans_etape_courante(racine: Path) -> None:
    """M8 : un événement de fin sans étape ouverte ne plante pas le sondage."""
    banc = Banc(racine)
    banc.lancer()
    ecrire_progression(racine, _evenement(Etape.kpi, StatutEtape.reussie))
    reponse = banc.http.get("/api/chaine")
    assert reponse.status_code == 200
    assert reponse.json()["annonce"] == ""


def test_demande_mode_est_immuable() -> None:
    """M9 : le modèle est figé."""
    demande = DemandeMode(mode="reel")
    with pytest.raises(ValidationError):
        demande.mode = "repli"  # type: ignore[misc]


@pytest.mark.parametrize(
    "origine", ["http://127.0.0.1:1234", "http://127.0.0.1:80", "http://localhost"]
)
def test_origine_inferieure_au_host_refusee(racine: Path, origine: str) -> None:
    """M10 : l'Origin doit être égale au Host, pas seulement ordonnée avant lui."""
    banc = Banc(racine)
    entetes = {"Host": "127.0.0.1:8765", "Origin": origine}
    assert banc.http.post("/api/mode", json={"mode": "repli"}, headers=entetes).status_code == 403
    assert banc.http.post("/api/chaine", headers=entetes).status_code == 403
    assert banc.lanceur.appels == []


def test_origine_identique_au_host_acceptee(racine: Path) -> None:
    """M10 : même hôte et même port, avec port explicite."""
    banc = Banc(racine)
    entetes = {"Host": "127.0.0.1:8765", "Origin": "http://127.0.0.1:8765"}
    assert banc.http.post("/api/mode", json={"mode": "repli"}, headers=entetes).status_code == 200


def test_intervalle_de_sondage_une_seconde(racine: Path) -> None:
    """M11 : le navigateur sonde toutes les secondes, jamais en boucle serrée."""
    assert textes.INTERVALLE_SONDAGE == 1.0
    assert Banc(racine).etat()["intervalle_ms"] == 1000
