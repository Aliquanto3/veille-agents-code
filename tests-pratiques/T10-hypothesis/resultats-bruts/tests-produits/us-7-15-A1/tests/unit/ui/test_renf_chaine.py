"""Renfort de la Story 7.15 : valeurs exactes, bornes et branches d'erreur."""

from pathlib import Path
from typing import Any, cast

import pytest

from tests.unit.ui.test_avant_apres import manifeste
from tests.unit.ui.test_chaine import INSTANT, PASSAGE, Banc, _evenement, ecrire_progression
from usine.contrats.passage import Etape, EvenementProgression, StatutEtape
from usine.ui import app, textes
from usine.ui.chaine import (
    AUCUN_PASSAGE_LANCE,
    AUCUN_PASSAGE_REPLI,
    DESCRIPTIONS,
    JOURNAL_ATTENTE,
    JOURNAL_VIDE,
    MESSAGE_SUCCES,
    MOTIF_LANCEMENT_EN_COURS,
    MOTIF_MODE_EN_COURS,
    MOTIF_RACINE,
    GestionChaine,
    LancementRefuse,
    vue_dernier_passage,
)
from usine.ui.progression import AUCUN_RAPPORT


@pytest.fixture
def racine_tmp(tmp_path: Path) -> Path:
    return tmp_path


def test_constantes_et_reexport_app() -> None:
    assert textes.INTERVALLE_SONDAGE == 1.0
    assert textes.LIGNES_ERREUR_MAX == 20
    assert app.INTERVALLE_SONDAGE == textes.INTERVALLE_SONDAGE
    assert app.LIGNES_ERREUR_MAX == textes.LIGNES_ERREUR_MAX
    assert app.LANCEMENT_REPLI == textes.LANCEMENT_REPLI


def test_descriptions_couvrent_les_dix_etapes() -> None:
    assert set(DESCRIPTIONS) == set(Etape)
    assert len(DESCRIPTIONS) == 10
    assert all(DESCRIPTIONS.values())


def test_vue_dernier_passage_valeurs_exactes() -> None:
    base = manifeste(secondes=3.4)
    vue = vue_dernier_passage(base.model_copy(update={"nb_tickets": 1234567}))
    assert vue.lignes == [
        "Date d'arrêté 09/10/2026 · durée 3,4 s",
        "1 234 567 tickets extraits",
        "Passage 20261012T073000Z-aaaaaa",
    ]
    assert vue_dernier_passage(base).lignes[1] == "0 tickets extraits"


def test_message_dernier_passage_selon_le_mode(racine_tmp: Path) -> None:
    assert Banc(racine_tmp).etat()["message_dernier_passage"] == AUCUN_PASSAGE_LANCE
    assert Banc(racine_tmp, repli=True).etat()["message_dernier_passage"] == AUCUN_PASSAGE_REPLI


def test_etat_initial_journal_attente(racine_tmp: Path) -> None:
    vue = Banc(racine_tmp).etat()
    assert vue["journal_vide"] == JOURNAL_ATTENTE
    assert vue["total"] == 10


def test_lancement_refuse_en_repli_sans_marques(racine_tmp: Path) -> None:
    banc = Banc(racine_tmp, repli=True)
    motif = textes.LANCEMENT_REPLI.replace("`", "")
    reponse = banc.lancer()
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == motif
    assert banc.lanceur.appels == []
    vue = banc.etat()
    assert vue["bouton_lancement"]["bloque"] is True
    assert vue["bouton_lancement"]["motif"] == motif
    assert vue["bouton_mode"] == {
        "libelle": "Revenir au Mode réel",
        "bloque": False,
        "motif": None,
    }
    assert vue["mode_cible"] == "reel"


def test_lancement_refuse_racine_absente_ou_inexistante(tmp_path: Path) -> None:
    for racine in (None, tmp_path / "absente"):
        banc = Banc(racine)
        reponse = banc.lancer()
        assert reponse.status_code == 409
        assert reponse.json()["detail"] == MOTIF_RACINE
        assert banc.lanceur.appels == []
        assert banc.etat()["bouton_lancement"]["motif"] == MOTIF_RACINE


def test_gestion_leve_lancement_refuse() -> None:
    gestion = GestionChaine(None)
    with pytest.raises(LancementRefuse, match="racine"):
        gestion.lancer(False)
    assert gestion.en_cours() is False


def test_deuxieme_lancement_409_sans_second_processus(racine_tmp: Path) -> None:
    banc = Banc(racine_tmp)
    assert banc.lancer().status_code == 202
    reponse = banc.lancer()
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == MOTIF_LANCEMENT_EN_COURS
    assert len(banc.lanceur.appels) == 1


def test_bascule_refusee_pendant_la_chaine_puis_permise(racine_tmp: Path) -> None:
    banc = Banc(racine_tmp)
    banc.lancer()
    reponse = banc.mode("repli")
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == MOTIF_MODE_EN_COURS
    banc.lanceur.finir(0)
    assert banc.mode("repli").status_code == 200
    assert banc.etat()["mode_cible"] == "reel"
    assert banc.mode("reel").status_code == 200
    assert banc.etat()["mode_cible"] == "repli"


@pytest.mark.parametrize("corps", [{"mode": "autre"}, {}, {"mode": "repli", "x": 1}, {"mode": 1}])
def test_mode_corps_invalide_422(racine_tmp: Path, corps: dict[str, Any]) -> None:
    banc = Banc(racine_tmp)
    assert banc.http.post("/api/mode", json=corps).status_code == 422
    assert banc.etat()["mode_cible"] == "repli"


def test_mode_bascule_lit_le_manifeste_du_nouveau_mode(racine_tmp: Path) -> None:
    banc = Banc(racine_tmp)
    banc.mode("repli")
    assert banc.lectures[-1] is True
    banc.mode("reel")
    assert banc.lectures[-1] is False


@pytest.mark.parametrize(
    ("origine", "statut"),
    [
        ("http://evil.test", 403),
        ("null", 403),
        ("http://127.0.0.1:9999", 403),
        ("http://localhost", 403),  # autre netloc que le Host 127.0.0.1
        ("http://127.0.0.1", 200),
    ],
)
def test_origine_sur_post_mode(racine_tmp: Path, origine: str, statut: int) -> None:
    banc = Banc(racine_tmp)
    reponse = banc.http.post("/api/mode", json={"mode": "repli"}, headers={"Origin": origine})
    assert reponse.status_code == statut


def test_origine_etrangere_ne_lance_rien(racine_tmp: Path) -> None:
    banc = Banc(racine_tmp)
    reponse = banc.http.post("/api/chaine", headers={"Origin": "http://evil.test"})
    assert reponse.status_code == 403
    assert banc.lanceur.appels == []


def test_host_forge_400(racine_tmp: Path) -> None:
    banc = Banc(racine_tmp)
    assert banc.http.get("/api/chaine", headers={"Host": "evil.test"}).status_code == 400
    assert banc.http.post("/api/chaine", headers={"Host": "evil.test"}).status_code == 400
    assert banc.http.get("/api/chaine", headers={"Host": "localhost"}).status_code == 200


def test_demarrage_oserror_vue_attente_avec_erreur(racine_tmp: Path) -> None:
    def echoue(*_a: Any, **_k: Any) -> None:
        raise OSError("boum")

    gestion = GestionChaine(racine_tmp, popen=cast(Any, echoue))
    gestion.lancer(False)
    vue = gestion.vue(False, None)
    assert vue.statut == "attente"
    assert vue.erreur == "Lancement de la Chaîne impossible : boum"
    assert vue.bouton_lancement.bloque is False
    assert vue.bouton_lancement.libelle == "Lancer la Chaîne"
    assert gestion.en_cours() is False


def test_suivi_etapes_annonce_journal_et_compteur(racine_tmp: Path) -> None:
    banc = Banc(racine_tmp, passage=manifeste())
    banc.lancer()
    ecrire_progression(
        racine_tmp,
        _evenement(Etape.extraction, StatutEtape.en_cours, 0),
        _evenement(Etape.extraction, StatutEtape.reussie, 1.5),
        _evenement(Etape.instantanes, StatutEtape.sautee, 2),
        _evenement(Etape.kpi, StatutEtape.en_cours, 3),
        partielle='{"passage_id": "tronque',
    )
    vue = banc.etat()
    assert vue["statut"] == "en_cours"
    assert vue["terminees"] == 2
    assert vue["compteur"] == "2 / 10"
    assert vue["annonce"] == "Étape 3 sur 10 : kpi"
    etats = [etape["etat"] for etape in vue["etapes"]]
    assert etats[:4] == ["reussie", "sautee", "en_cours", "en_attente"]
    assert vue["etapes"][0]["numero"] == 1
    assert vue["etapes"][0]["duree"] == "1,5 s"
    assert vue["etapes"][0]["libelle_etat"] == "Réussie"
    assert vue["etapes"][2]["libelle_etat"] == "En cours"
    assert vue["etapes"][3]["duree"] is None
    assert vue["etapes"][0]["description"] == DESCRIPTIONS[Etape.extraction]
    assert [ligne["texte"] for ligne in vue["journal"]] == [
        "kpi : En cours",
        "instantanes : Sautée",
        "extraction : Réussie",
        "extraction : En cours",
    ]
    assert vue["journal"][0]["horodatage"] == "07:30:03"
    assert vue["journal"][-1]["horodatage"] == "07:30:00"
    assert vue["bandeau"] is None
    assert vue["erreur"] is None


def test_en_cours_sans_evenement_annonce_et_journal_vide(racine_tmp: Path) -> None:
    banc = Banc(racine_tmp)
    banc.lancer()
    vue = banc.etat()
    assert vue["annonce"] == "Chaîne en cours…"
    assert vue["journal_vide"] == JOURNAL_VIDE
    assert vue["journal"] == []


def test_annonce_vide_entre_deux_etapes(racine_tmp: Path) -> None:
    banc = Banc(racine_tmp)
    banc.lancer()
    ecrire_progression(
        racine_tmp,
        _evenement(Etape.extraction, StatutEtape.en_cours, 0),
        _evenement(Etape.extraction, StatutEtape.reussie, 1),
    )
    assert banc.etat()["annonce"] == ""


def test_message_de_progression_dans_le_journal(racine_tmp: Path) -> None:
    banc = Banc(racine_tmp)
    banc.lancer()
    ligne = EvenementProgression(
        passage_id=PASSAGE,
        etape=Etape.kpi,
        statut=StatutEtape.echouee,
        horodatage=INSTANT,
        message="détail",
    ).model_dump_json()
    ecrire_progression(racine_tmp, ligne)
    assert banc.etat()["journal"][0]["texte"] == "kpi : Échec · détail"


def test_fin_reussie(racine_tmp: Path) -> None:
    banc = Banc(racine_tmp)
    banc.lancer()
    banc.lanceur.finir(0)
    vue = banc.etat()
    assert vue["statut"] == "terminee"
    assert vue["en_cours"] is False
    assert vue["annonce"] == MESSAGE_SUCCES
    assert vue["bandeau"] == {
        "variante": "succes",
        "texte": MESSAGE_SUCCES,
        "lignes": [],
        "complement": None,
        "lien": {"libelle": "Voir la carte météo", "url": "/"},
    }
    assert vue["bouton_lancement"] == {
        "libelle": "Relancer la Chaîne",
        "bloque": False,
        "motif": None,
    }
    assert vue["bouton_mode"]["bloque"] is False
    assert vue["bouton_mode"]["motif"] is None


def test_echec_hors_etape_sans_sortie_erreur(racine_tmp: Path) -> None:
    banc = Banc(racine_tmp)
    banc.lancer()
    banc.lanceur.finir(3)
    vue = banc.etat()
    assert vue["statut"] == "echec"
    assert vue["annonce"] == "Échec de la Chaîne hors d'une étape."
    bandeau = vue["bandeau"]
    assert bandeau["variante"] == "erreur"
    assert bandeau["texte"] == "Échec de la Chaîne hors d'une étape (code 3)."
    assert bandeau["lignes"] == ["aucun message"]
    assert bandeau["complement"] == AUCUN_RAPPORT
    assert bandeau["lien"] is None
    assert vue["bouton_lancement"]["libelle"] == "Relancer la Chaîne"


@pytest.mark.parametrize(("total", "attendu"), [(19, 19), (20, 20), (21, 20), (45, 20)])
def test_echec_borne_des_lignes_d_erreur(racine_tmp: Path, total: int, attendu: int) -> None:
    banc = Banc(racine_tmp)
    banc.lanceur.sortie_erreur = "".join(f"ligne {i}\n" for i in range(1, total + 1)).encode()
    banc.lancer()
    banc.lanceur.finir(1)
    lignes = banc.etat()["bandeau"]["lignes"]
    assert len(lignes) == attendu
    assert lignes[-1] == f"ligne {total}"
    assert lignes[0] == f"ligne {total - attendu + 1}"


def test_echec_nomme_l_etape_et_garde_le_passage(racine_tmp: Path) -> None:
    banc = Banc(racine_tmp, passage=manifeste())
    avant = banc.etat()["dernier_passage"]
    banc.lancer()
    ecrire_progression(
        racine_tmp,
        _evenement(Etape.extraction, StatutEtape.reussie, 1),
        _evenement(Etape.kpi, StatutEtape.echouee, 2),
    )
    banc.lanceur.finir(2)
    vue = banc.etat()
    assert vue["bandeau"]["texte"] == "Échec de la Chaîne à l'étape « kpi » (code 2)."
    assert vue["annonce"] == "Échec de la Chaîne à l'étape « kpi »."
    assert vue["etapes"][2]["etat"] == "echouee"
    assert vue["etapes"][2]["libelle_etat"] == "Échec"
    assert vue["terminees"] == 2  # l'échec compte comme terminée
    assert vue["dernier_passage"] == avant


def test_relance_apres_fin_repart_a_zero(racine_tmp: Path) -> None:
    banc = Banc(racine_tmp)
    banc.lanceur.sortie_erreur = b"boum\n"
    banc.lancer()
    banc.lanceur.finir(1)
    assert banc.etat()["bandeau"]["lignes"] == ["boum"]
    assert banc.lancer().status_code == 202
    assert len(banc.lanceur.appels) == 2
    vue = banc.etat()
    assert vue["statut"] == "en_cours"
    assert vue["bandeau"] is None
    assert vue["erreur"] is None


def test_progression_invalide_signalee_sondage_maintenu(racine_tmp: Path) -> None:
    banc = Banc(racine_tmp)
    banc.lancer()
    ecrire_progression(racine_tmp, "pas du json")
    reponse = banc.http.get("/api/chaine")
    assert reponse.status_code == 200
    vue = reponse.json()
    assert vue["erreur"]
    assert vue["etapes"]
    assert vue["terminees"] == 0
    assert vue["statut"] == "en_cours"
