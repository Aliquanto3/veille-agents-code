"""Renforcement de la Story 7.15 : bornes, codes de sortie et branches d'erreur."""

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from tests.unit.ui.test_chaine import Banc, _evenement, ecrire_progression
from usine.contrats.passage import Etape, StatutEtape
from usine.ui import lancement
from usine.ui.chaine import JOURNAL_ATTENTE, JOURNAL_VIDE, GestionChaine
from usine.ui.serveur import HOTE
from usine.ui.vues import DemandeMode


class Fichier:
    """Fichier d'erreurs factice qui note sa fermeture."""

    def __init__(self) -> None:
        self.ferme = False

    def close(self) -> None:
        self.ferme = True


def test_echec_de_demarrage_ferme_le_fichier_d_erreurs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # M1
    fichier = Fichier()
    monkeypatch.setattr(lancement, "fichier_erreurs", lambda: fichier)

    def popen(*_args: Any, **_options: Any) -> Any:
        raise OSError("boom")

    gestion = GestionChaine(tmp_path, popen=popen)
    gestion.lancer(False)
    assert fichier.ferme is True
    assert not gestion.en_cours()
    assert "boom" in (gestion.vue(False, None).erreur or "")


def test_echec_avant_creation_du_fichier_ne_plante_pas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # M1
    def sans_fichier() -> Any:
        raise OSError("disque plein")

    monkeypatch.setattr(lancement, "fichier_erreurs", sans_fichier)
    gestion = GestionChaine(tmp_path)
    gestion.lancer(False)
    assert "disque plein" in (gestion.vue(False, None).erreur or "")


def test_code_de_sortie_negatif_est_un_echec(tmp_path: Path) -> None:  # M2, M5
    banc = Banc(tmp_path)
    banc.lancer()
    banc.lanceur.finir(-9)
    vue = banc.etat()
    assert vue["statut"] == "echec"
    assert vue["bandeau"]["variante"] == "erreur"
    assert "(code -9)" in vue["bandeau"]["texte"]
    assert vue["bouton_lancement"]["libelle"] == "Relancer la Chaîne"
    assert vue["annonce"].startswith("Échec de la Chaîne")


def test_code_zero_est_un_succes(tmp_path: Path) -> None:
    banc = Banc(tmp_path)
    banc.lancer()
    banc.lanceur.finir(0)
    vue = banc.etat()
    assert vue["statut"] == "terminee"
    assert vue["bandeau"]["variante"] == "succes"


def test_numeros_d_etapes_commencent_a_un(tmp_path: Path) -> None:  # M3
    vue = Banc(tmp_path).etat()
    assert [e["numero"] for e in vue["etapes"]] == list(range(1, len(Etape) + 1))


def test_journal_vide_selon_le_statut(tmp_path: Path) -> None:  # M4
    banc = Banc(tmp_path)
    assert banc.etat()["journal_vide"] == JOURNAL_ATTENTE
    banc.lancer()
    assert banc.etat()["journal_vide"] == JOURNAL_VIDE


@pytest.mark.parametrize(("etape", "rang"), [(Etape.extraction, 1), (Etape.kpi, 3)])
def test_annonce_rang_de_l_etape(tmp_path: Path, etape: Etape, rang: int) -> None:  # M6
    banc = Banc(tmp_path)
    banc.lancer()
    ecrire_progression(tmp_path, _evenement(etape, StatutEtape.en_cours))
    assert banc.etat()["annonce"] == f"Étape {rang} sur {len(Etape)} : {etape.value}"


def test_etape_echouee_n_est_plus_courante(tmp_path: Path) -> None:  # M7
    banc = Banc(tmp_path)
    banc.lancer()
    ecrire_progression(
        tmp_path,
        _evenement(Etape.extraction, StatutEtape.en_cours, 0),
        _evenement(Etape.extraction, StatutEtape.echouee, 1),
    )
    assert banc.etat()["annonce"] == ""


def test_fin_d_une_autre_etape_ne_termine_pas_la_courante(tmp_path: Path) -> None:  # M8
    banc = Banc(tmp_path)
    banc.lancer()
    ecrire_progression(
        tmp_path,
        _evenement(Etape.extraction, StatutEtape.en_cours, 0),
        _evenement(Etape.kpi, StatutEtape.reussie, 1),
    )
    assert banc.etat()["annonce"] == f"Étape 1 sur {len(Etape)} : extraction"


def test_demande_mode_est_figee() -> None:  # M9
    demande = DemandeMode(mode="reel")
    with pytest.raises(ValidationError):
        demande.mode = "repli"  # type: ignore[misc]


def test_origine_sur_un_autre_port_refusee(tmp_path: Path) -> None:  # M10
    banc = Banc(tmp_path)
    entetes = {"Host": f"{HOTE}:8765", "Origin": f"http://{HOTE}"}
    assert banc.http.post("/api/mode", json={"mode": "repli"}, headers=entetes).status_code == 403
    entetes = {"Host": f"{HOTE}:8765", "Origin": f"http://{HOTE}:8765"}
    assert banc.http.post("/api/mode", json={"mode": "repli"}, headers=entetes).status_code == 200


def test_intervalle_de_sondage_exact(tmp_path: Path) -> None:  # M11
    assert Banc(tmp_path).etat()["intervalle_ms"] == 1000
