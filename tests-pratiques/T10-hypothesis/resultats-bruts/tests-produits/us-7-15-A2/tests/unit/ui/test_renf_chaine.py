"""Renfort Story 7.15 : valeurs exactes, bornes et branches d'erreur de `GestionChaine` et des routes."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest

from tests.unit.ui.test_avant_apres import manifeste
from tests.unit.ui.test_chaine import PASSAGE, Banc, Lanceur, _evenement, ecrire_progression
from usine.contrats.passage import Etape, EvenementProgression, StatutEtape
from usine.ui.chaine import (
    AUCUN_PASSAGE_LANCE,
    AUCUN_PASSAGE_REPLI,
    DESCRIPTIONS,
    JOURNAL_ATTENTE,
    JOURNAL_VIDE,
    LIBELLE_LANCER,
    LIBELLE_PASSER_REPLI,
    LIBELLE_RELANCER,
    LIBELLE_REVENIR_REEL,
    MESSAGE_SUCCES,
    MOTIF_LANCEMENT_EN_COURS,
    MOTIF_MODE_EN_COURS,
    MOTIF_RACINE,
    GestionChaine,
    LancementRefuse,
    vue_dernier_passage,
)
from usine.ui.progression import AUCUN_RAPPORT
from usine.ui.textes import LANCEMENT_REPLI, LIGNES_ERREUR_MAX


def _gestion(racine: Path | None) -> tuple[GestionChaine, Lanceur]:
    lanceur = Lanceur()
    return GestionChaine(racine, popen=cast(Any, lanceur)), lanceur


def test_constantes_et_descriptions() -> None:
    assert LIGNES_ERREUR_MAX == 20
    assert set(DESCRIPTIONS) == set(Etape)
    assert len(DESCRIPTIONS) == 10


def test_lancement_refuse_en_mode_repli_sans_marques(tmp_path: Path) -> None:
    gestion, lanceur = _gestion(tmp_path)
    with pytest.raises(LancementRefuse) as exc:
        gestion.lancer(True)
    assert str(exc.value) == LANCEMENT_REPLI.replace("`", "")
    assert "`" not in str(exc.value)
    assert lanceur.appels == []


def test_lancement_refuse_sans_racine_et_racine_inexistante(tmp_path: Path) -> None:
    for racine in (None, tmp_path / "absente"):
        gestion, lanceur = _gestion(racine)
        with pytest.raises(LancementRefuse, match="introuvable"):
            gestion.lancer(False)
        assert lanceur.appels == []
        vue = gestion.vue(False, None)
        assert vue.bouton_lancement.bloque is True
        assert vue.bouton_lancement.motif == MOTIF_RACINE
        assert vue.bouton_lancement.libelle == LIBELLE_LANCER


def test_repli_prioritaire_sur_racine_absente(tmp_path: Path) -> None:
    gestion, _ = _gestion(None)
    vue = gestion.vue(True, None)
    assert vue.bouton_lancement.motif == LANCEMENT_REPLI.replace("`", "")
    assert vue.bouton_mode.libelle == LIBELLE_REVENIR_REEL
    assert vue.bouton_mode.bloque is False
    assert vue.bouton_mode.motif is None
    assert vue.mode_cible == "reel"
    assert vue.message_dernier_passage == AUCUN_PASSAGE_REPLI


def test_second_lancement_refuse_sans_second_processus(tmp_path: Path) -> None:
    gestion, lanceur = _gestion(tmp_path)
    gestion.lancer(False)
    assert gestion.en_cours() is True
    with pytest.raises(LancementRefuse) as exc:
        gestion.lancer(False)
    assert str(exc.value) == MOTIF_LANCEMENT_EN_COURS
    assert len(lanceur.appels) == 1


def test_relance_possible_apres_fin_et_efface_l_etat(tmp_path: Path) -> None:
    gestion, lanceur = _gestion(tmp_path)
    lanceur.sortie_erreur = b"boum\n"
    gestion.lancer(False)
    lanceur.finir(1)
    assert gestion.en_cours() is False
    assert gestion.vue(False, None).statut == "echec"
    lanceur.sortie_erreur = b""
    gestion.lancer(False)
    vue = gestion.vue(False, None)
    assert len(lanceur.appels) == 2
    assert vue.statut == "en_cours"
    assert vue.bandeau is None


def test_oserror_au_demarrage(tmp_path: Path) -> None:
    def popen(*_a: Any, **_k: Any) -> Any:
        raise OSError("pas de python")

    gestion = GestionChaine(tmp_path, popen=popen)
    gestion.lancer(False)
    vue = gestion.vue(False, None)
    assert vue.statut == "attente"
    assert vue.erreur == "Lancement de la Chaîne impossible : pas de python"
    assert gestion.en_cours() is False
    assert vue.bouton_lancement.bloque is False
    # un lancement ultérieur réussi efface l'erreur
    gestion2, _ = _gestion(tmp_path)
    gestion2.lancer(False)
    assert gestion2.vue(False, None).erreur is None


def test_etat_attente_textes(tmp_path: Path) -> None:
    gestion, _ = _gestion(tmp_path)
    vue = gestion.vue(False, None)
    assert vue.journal_vide == JOURNAL_ATTENTE
    assert vue.message_dernier_passage == AUCUN_PASSAGE_LANCE
    assert vue.bouton_mode.libelle == LIBELLE_PASSER_REPLI
    assert vue.total == 10
    assert vue.annonce == ""


def test_en_cours_sans_evenement(tmp_path: Path) -> None:
    gestion, _ = _gestion(tmp_path)
    gestion.lancer(False)
    vue = gestion.vue(False, None)
    assert vue.journal_vide == JOURNAL_VIDE
    assert vue.annonce == "Chaîne en cours…"
    assert vue.journal == []
    assert vue.bouton_mode.motif == MOTIF_MODE_EN_COURS


def test_suivi_etapes_annonce_journal_et_durees(tmp_path: Path) -> None:
    gestion, _ = _gestion(tmp_path)
    gestion.lancer(False)
    ecrire_progression(
        tmp_path,
        _evenement(Etape.extraction, StatutEtape.en_cours, 0),
        _evenement(Etape.extraction, StatutEtape.reussie, 1.5),
        _evenement(Etape.instantanes, StatutEtape.en_cours, 1.5),
        _evenement(Etape.instantanes, StatutEtape.sautee, 2.0),
        _evenement(Etape.kpi, StatutEtape.en_cours, 2.0),
    )
    vue = gestion.vue(False, None)
    assert vue.terminees == 2
    assert vue.compteur == "2 / 10"
    assert [e.etat for e in vue.etapes[:4]] == ["reussie", "sautee", "en_cours", "en_attente"]
    assert [e.numero for e in vue.etapes] == list(range(1, 11))
    assert vue.etapes[0].duree == "1,5 s"
    assert vue.etapes[1].duree == "0,5 s"
    assert vue.etapes[2].duree is None
    assert vue.etapes[0].libelle_etat == "Réussie"
    assert vue.etapes[0].description == DESCRIPTIONS[Etape.extraction]
    assert vue.annonce == "Étape 3 sur 10 : kpi"
    assert [(j.horodatage, j.texte) for j in vue.journal][0] == ("07:30:02", "kpi : En cours")
    assert vue.journal[-1].texte == "extraction : En cours"
    assert len(vue.journal) == 5


def test_annonce_vide_entre_deux_etapes(tmp_path: Path) -> None:
    gestion, _ = _gestion(tmp_path)
    gestion.lancer(False)
    ecrire_progression(
        tmp_path,
        _evenement(Etape.extraction, StatutEtape.en_cours, 0),
        _evenement(Etape.extraction, StatutEtape.reussie, 1),
    )
    assert gestion.vue(False, None).annonce == ""


def test_journal_message_et_heure_utc(tmp_path: Path) -> None:
    gestion, _ = _gestion(tmp_path)
    gestion.lancer(False)
    evenement = EvenementProgression(
        passage_id=PASSAGE,
        etape=Etape.kpi,
        statut=StatutEtape.echouee,
        horodatage=datetime(2026, 10, 12, 9, 5, 7, tzinfo=UTC),
        message="trop de tickets",
    )
    ecrire_progression(tmp_path, evenement.model_dump_json())
    ligne = gestion.vue(False, None).journal[0]
    assert ligne.horodatage == "09:05:07"
    assert ligne.texte == "kpi : Échec · trop de tickets"


def test_ligne_finale_partielle_ignoree(tmp_path: Path) -> None:
    gestion, _ = _gestion(tmp_path)
    gestion.lancer(False)
    ecrire_progression(
        tmp_path,
        _evenement(Etape.extraction, StatutEtape.en_cours),
        partielle='{"passage_id": "x"',
    )
    vue = gestion.vue(False, None)
    assert vue.erreur is None
    assert len(vue.journal) == 1


def test_progression_invalide_signalee_sondage_maintenu(tmp_path: Path) -> None:
    gestion, _ = _gestion(tmp_path)
    gestion.lancer(False)
    ecrire_progression(tmp_path, "pas du json")
    vue = gestion.vue(False, None)
    assert vue.erreur
    assert vue.statut == "en_cours"
    assert vue.etapes and vue.terminees == 0
    assert vue.journal == []


def test_fichier_preexistant_ignore(tmp_path: Path) -> None:
    ecrire_progression(tmp_path, _evenement(Etape.extraction, StatutEtape.reussie))
    gestion, _ = _gestion(tmp_path)
    gestion.lancer(False)
    vue = gestion.vue(False, None)
    assert vue.journal == []
    assert vue.terminees == 0


def test_succes_bandeau_et_annonce(tmp_path: Path) -> None:
    gestion, lanceur = _gestion(tmp_path)
    gestion.lancer(False)
    lanceur.finir(0)
    vue = gestion.vue(False, None)
    assert vue.statut == "terminee"
    assert vue.en_cours is False
    assert vue.annonce == MESSAGE_SUCCES == "Chaîne terminée : Passage publié."
    assert vue.bandeau is not None
    assert vue.bandeau.variante == "succes"
    assert vue.bandeau.texte == MESSAGE_SUCCES
    assert vue.bandeau.lignes == []
    assert vue.bandeau.complement is None
    assert (vue.bandeau.lien.libelle, vue.bandeau.lien.url) == ("Voir la carte météo", "/")
    assert vue.bouton_lancement.libelle == LIBELLE_RELANCER
    assert vue.bouton_lancement.bloque is False
    assert vue.bouton_mode.bloque is False


def test_echec_sans_sortie_ni_etape(tmp_path: Path) -> None:
    gestion, lanceur = _gestion(tmp_path)
    gestion.lancer(False)
    lanceur.finir(3)
    vue = gestion.vue(False, None)
    assert vue.statut == "echec"
    assert vue.bandeau is not None
    assert vue.bandeau.variante == "erreur"
    assert vue.bandeau.texte == "Échec de la Chaîne hors d'une étape (code 3)."
    assert vue.bandeau.lignes == ["aucun message"]
    assert vue.bandeau.complement == AUCUN_RAPPORT
    assert vue.bandeau.lien is None
    assert vue.annonce == "Échec de la Chaîne hors d'une étape."
    assert vue.bouton_lancement.libelle == LIBELLE_RELANCER


@pytest.mark.parametrize(
    ("total", "attendu_premiere"),
    [(19, 1), (20, 1), (21, 2), (25, 6)],
)
def test_echec_borne_des_lignes_d_erreur(tmp_path: Path, total: int, attendu_premiere: int) -> None:
    gestion, lanceur = _gestion(tmp_path)
    lanceur.sortie_erreur = "".join(f"l{i}\n" for i in range(1, total + 1)).encode()
    gestion.lancer(False)
    lanceur.finir(1)
    lignes = gestion.vue(False, None).bandeau.lignes  # type: ignore[union-attr]
    assert len(lignes) == min(total, 20)
    assert lignes[0] == f"l{attendu_premiere}"
    assert lignes[-1] == f"l{total}"


def test_echec_a_l_etape_et_erreur_lue_une_fois(tmp_path: Path) -> None:
    gestion, lanceur = _gestion(tmp_path)
    lanceur.sortie_erreur = b"Traceback\nValueError: x\n"
    gestion.lancer(False)
    ecrire_progression(
        tmp_path,
        _evenement(Etape.extraction, StatutEtape.reussie),
        _evenement(Etape.kpi, StatutEtape.echouee, 1),
    )
    lanceur.finir(2)
    premiere = gestion.vue(False, None)
    seconde = gestion.vue(False, None)
    assert premiere.bandeau == seconde.bandeau
    assert premiere.bandeau is not None
    assert premiere.bandeau.texte == "Échec de la Chaîne à l'étape « kpi » (code 2)."
    assert premiere.bandeau.lignes == ["Traceback", "ValueError: x"]
    assert premiere.annonce == "Échec de la Chaîne à l'étape « kpi »."
    assert premiere.terminees == 2
    assert [e.etat for e in premiere.etapes[:3]] == ["reussie", "en_attente", "echouee"]


def test_dernier_passage_vue() -> None:
    m = manifeste()
    vue = vue_dernier_passage(m)
    assert len(vue.lignes) == 3
    assert vue.lignes[0].startswith("Date d'arrêté ")
    assert " · durée " in vue.lignes[0]
    assert vue.lignes[1].endswith(" tickets extraits")
    assert vue.lignes[2] == f"Passage {m.passage_id}"


# --- routes ---


def test_api_lancement_409_en_mode_repli(tmp_path: Path) -> None:
    banc = Banc(tmp_path, repli=True)
    reponse = banc.lancer()
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == LANCEMENT_REPLI.replace("`", "")
    assert banc.lanceur.appels == []


def test_api_lancement_409_sans_racine() -> None:
    reponse = Banc(None).lancer()
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == MOTIF_RACINE


def test_api_deuxieme_lancement_409(tmp_path: Path) -> None:
    banc = Banc(tmp_path)
    assert banc.lancer().status_code == 202
    reponse = banc.lancer()
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == MOTIF_LANCEMENT_EN_COURS
    assert len(banc.lanceur.appels) == 1


def test_api_mode_bascule_et_retour(tmp_path: Path) -> None:
    banc = Banc(tmp_path, passage=manifeste())
    assert banc.mode("repli").status_code == 200
    vue = banc.etat()
    assert vue["mode_cible"] == "reel"
    assert vue["bouton_mode"]["libelle"] == LIBELLE_REVENIR_REEL
    assert banc.lectures[-1] is True
    assert banc.mode("reel").status_code == 200
    vue = banc.etat()
    assert vue["mode_cible"] == "repli"
    assert banc.lectures[-1] is False


def test_api_mode_409_pendant_la_chaine_et_mode_inchange(tmp_path: Path) -> None:
    banc = Banc(tmp_path)
    banc.lancer()
    reponse = banc.mode("repli")
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == MOTIF_MODE_EN_COURS
    assert banc.etat()["mode_cible"] == "repli"  # toujours en mode réel
    banc.lanceur.finir(0)
    assert banc.mode("repli").status_code == 200


@pytest.mark.parametrize("corps", [{"mode": "autre"}, {}, {"mode": 3}, {"mode": None}])
def test_api_mode_422(tmp_path: Path, corps: dict[str, Any]) -> None:
    banc = Banc(tmp_path)
    assert banc.http.post("/api/mode", json=corps).status_code == 422
    assert banc.http.post("/api/mode").status_code == 422
    assert banc.etat()["mode_cible"] == "repli"


def test_api_mode_repli_absent_dans_le_cadre(tmp_path: Path) -> None:
    from usine.contrats.erreurs import UsineErreur
    from usine.ui.textes import REPLI_ABSENT

    def lecteur(repli: bool) -> Any:
        if repli:
            raise UsineErreur(REPLI_ABSENT)
        return manifeste()

    banc = Banc(tmp_path, lecteur=lecteur)
    reponse = banc.mode("repli")
    assert reponse.status_code == 200
    assert REPLI_ABSENT in reponse.text
    vue = banc.etat()  # le bouton de retour reste utilisable
    assert vue["dernier_passage"] is None
    assert vue["bouton_mode"]["bloque"] is False
    assert banc.mode("reel").status_code == 200


@pytest.mark.parametrize("route", ["/api/chaine", "/api/mode"])
@pytest.mark.parametrize(
    "origine",
    ["http://evil.test", "null", "http://127.0.0.1:9999", "http://localhost"],
)
def test_api_origine_etrangere_403(tmp_path: Path, route: str, origine: str) -> None:
    banc = Banc(tmp_path)
    reponse = banc.http.post(route, json={"mode": "repli"}, headers={"Origin": origine})
    assert reponse.status_code == 403
    assert banc.lanceur.appels == []
    assert banc.etat()["mode_cible"] == "repli"


def test_api_origine_identique_acceptee(tmp_path: Path) -> None:
    banc = Banc(tmp_path)
    reponse = banc.http.post("/api/chaine", headers={"Origin": "http://127.0.0.1"})
    assert reponse.status_code == 202


@pytest.mark.parametrize("chemin", ["/api/chaine", "/api/cadre", "/"])
def test_host_forge_400(tmp_path: Path, chemin: str) -> None:
    banc = Banc(tmp_path)
    assert banc.http.get(chemin, headers={"Host": "evil.test"}).status_code == 400
    assert banc.http.post("/api/chaine", headers={"Host": "evil.test"}).status_code == 400
    assert banc.lanceur.appels == []
    assert banc.http.get(chemin, headers={"Host": "localhost"}).status_code == 200
