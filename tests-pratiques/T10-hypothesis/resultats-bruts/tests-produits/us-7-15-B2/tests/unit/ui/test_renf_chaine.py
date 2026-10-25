"""Renfort de la Story 7.15 : valeurs exactes, bornes et branches d'erreur de la Chaîne et du mode."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from tests.unit.ui.test_avant_apres import manifeste
from tests.unit.ui.test_chaine import PASSAGE, Banc, Lanceur
from usine.contrats.passage import Etape, EvenementProgression, StatutEtape
from usine.ui import chaine as module_chaine
from usine.ui.chaine import (
    AUCUN_PASSAGE_LANCE,
    AUCUN_PASSAGE_REPLI,
    DESCRIPTIONS,
    JOURNAL_ATTENTE,
    JOURNAL_VIDE,
    LIBELLE_RELANCER,
    MESSAGE_SUCCES,
    MOTIF_LANCEMENT_EN_COURS,
    MOTIF_RACINE,
    GestionChaine,
    LancementRefuse,
    vue_dernier_passage,
)
from usine.ui.progression import AUCUN_RAPPORT
from usine.ui.serveur import HOTE, creer_application
from usine.ui.textes import LANCEMENT_REPLI, LIGNES_ERREUR_MAX

DEBUT = datetime(2026, 10, 12, 7, 30, tzinfo=UTC)
SANS_FIXTURE = settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=40)


def _ligne(
    etape: Etape, statut: StatutEtape, secondes: float = 0.0, message: str = ""
) -> str:
    return EvenementProgression(
        passage_id=PASSAGE,
        etape=etape,
        statut=statut,
        horodatage=DEBUT + timedelta(seconds=secondes),
        message=message,
    ).model_dump_json()


def _ecrire(racine: Path, *lignes: str, partielle: str = "") -> None:
    repertoire = racine / "sorties" / "progression"
    repertoire.mkdir(parents=True, exist_ok=True)
    texte = "".join(f"{ligne}\n" for ligne in lignes) + partielle
    (repertoire / f"{PASSAGE}.jsonl").write_text(texte, encoding="utf-8")


def _gestion(racine: Path | None, erreur: bytes = b"") -> tuple[GestionChaine, Lanceur]:
    lanceur = Lanceur()
    lanceur.sortie_erreur = erreur
    return GestionChaine(racine, popen=cast(Any, lanceur)), lanceur


# --- refus de lancement ---


def test_lancement_refuse_en_mode_repli_sans_marques(tmp_path: Path) -> None:
    gestion, lanceur = _gestion(tmp_path)
    with pytest.raises(LancementRefuse) as exc:
        gestion.lancer(repli=True)
    assert str(exc.value) == LANCEMENT_REPLI.replace("`", "")
    assert "`" not in str(exc.value)
    assert lanceur.appels == []


def test_lancement_refuse_sans_racine() -> None:
    gestion, lanceur = _gestion(None)
    with pytest.raises(LancementRefuse, match="introuvable"):
        gestion.lancer(repli=False)
    assert lanceur.appels == []
    vue = gestion.vue(False, None)
    assert vue.bouton_lancement.bloque is True
    assert vue.bouton_lancement.motif == MOTIF_RACINE


def test_lancement_refuse_racine_inexistante(tmp_path: Path) -> None:
    gestion, _ = _gestion(tmp_path / "absente")
    with pytest.raises(LancementRefuse) as exc:
        gestion.lancer(repli=False)
    assert str(exc.value) == MOTIF_RACINE


def test_second_lancement_refuse_un_seul_processus(tmp_path: Path) -> None:
    gestion, lanceur = _gestion(tmp_path)
    gestion.lancer(repli=False)
    assert gestion.en_cours() is True
    with pytest.raises(LancementRefuse) as exc:
        gestion.lancer(repli=False)
    assert str(exc.value) == MOTIF_LANCEMENT_EN_COURS
    assert len(lanceur.appels) == 1


def test_motif_en_cours_prioritaire_sur_le_repli(tmp_path: Path) -> None:
    gestion, _ = _gestion(tmp_path)
    gestion.lancer(repli=False)
    with pytest.raises(LancementRefuse) as exc:
        gestion.lancer(repli=True)
    assert str(exc.value) == MOTIF_LANCEMENT_EN_COURS


def test_relance_possible_apres_la_fin(tmp_path: Path) -> None:
    gestion, lanceur = _gestion(tmp_path)
    gestion.lancer(repli=False)
    lanceur.finir(0)
    assert gestion.en_cours() is False
    gestion.lancer(repli=False)
    assert len(lanceur.appels) == 2
    assert gestion.en_cours() is True


def test_demarrage_en_oserror_donne_attente_avec_erreur(tmp_path: Path) -> None:
    def echec(*_args: Any, **_options: Any) -> Any:
        raise OSError("boom")

    gestion = GestionChaine(tmp_path, popen=cast(Any, echec))
    gestion.lancer(repli=False)
    assert gestion.en_cours() is False
    vue = gestion.vue(False, None)
    assert vue.statut == "attente"
    assert vue.erreur == "Lancement de la Chaîne impossible : boom"
    assert vue.bouton_lancement.libelle == "Lancer la Chaîne"
    assert vue.bouton_lancement.bloque is False
    assert vue.bandeau is None


def test_relance_efface_l_erreur_de_lancement(tmp_path: Path) -> None:
    appels = {"n": 0}
    lanceur = Lanceur()

    def popen(commande: list[str], **options: Any) -> Any:
        appels["n"] += 1
        if appels["n"] == 1:
            raise OSError("boom")
        return lanceur(commande, **options)

    gestion = GestionChaine(tmp_path, popen=cast(Any, popen))
    gestion.lancer(repli=False)
    assert gestion.vue(False, None).erreur is not None
    gestion.lancer(repli=False)
    vue = gestion.vue(False, None)
    assert vue.erreur is None
    assert vue.statut == "en_cours"


# --- vue : étapes, durée, compteur ---


def test_vue_etapes_durees_et_compteur(tmp_path: Path) -> None:
    gestion, _ = _gestion(tmp_path)
    gestion.lancer(repli=False)
    _ecrire(
        tmp_path,
        _ligne(Etape.extraction, StatutEtape.en_cours, 0),
        _ligne(Etape.extraction, StatutEtape.reussie, 0.3),
        _ligne(Etape.instantanes, StatutEtape.en_cours, 0.3),
        _ligne(Etape.instantanes, StatutEtape.sautee, 0.4),
        _ligne(Etape.kpi, StatutEtape.en_cours, 0.4),
    )
    vue = gestion.vue(False, None)
    assert [e.numero for e in vue.etapes] == list(range(1, 11))
    assert [e.description for e in vue.etapes] == [DESCRIPTIONS[e] for e in Etape]
    premiere, deuxieme, troisieme, quatrieme = vue.etapes[:4]
    assert (premiere.etat, premiere.libelle_etat, premiere.duree) == ("reussie", "Réussie", "0,3 s")
    assert (deuxieme.etat, deuxieme.libelle_etat) == ("sautee", "Sautée")
    assert (troisieme.etat, troisieme.libelle_etat, troisieme.duree) == ("en_cours", "En cours", None)
    assert (quatrieme.etat, quatrieme.libelle_etat, quatrieme.duree) == (
        "en_attente",
        "En attente",
        None,
    )
    assert vue.terminees == 2
    assert vue.total == 10
    assert vue.compteur == "2 / 10"
    assert vue.annonce == "Étape 3 sur 10 : kpi"


@SANS_FIXTURE
@given(
    statuts=st.lists(
        st.sampled_from([StatutEtape.reussie, StatutEtape.sautee, StatutEtape.echouee, None]),
        min_size=10,
        max_size=10,
    )
)
def test_terminees_egale_nombre_d_etapes_finies(
    tmp_path_factory: pytest.TempPathFactory, statuts: list[StatutEtape | None]
) -> None:
    racine = tmp_path_factory.mktemp("prop")
    gestion, _ = _gestion(racine)
    gestion.lancer(repli=False)
    lignes: list[str] = []
    for rang, (etape, final) in enumerate(zip(Etape, statuts, strict=True)):
        lignes.append(_ligne(etape, StatutEtape.en_cours, rang))
        if final is not None:
            lignes.append(_ligne(etape, final, rang + 0.5))
    _ecrire(racine, *lignes)
    vue = gestion.vue(False, None)
    attendu = sum(1 for final in statuts if final is not None)
    assert vue.terminees == attendu
    assert vue.total == 10
    assert vue.compteur == f"{attendu} / 10"
    assert len(vue.etapes) == 10


# --- journal ---


def test_journal_recent_en_haut_avec_message_et_heure_utc(tmp_path: Path) -> None:
    gestion, _ = _gestion(tmp_path)
    gestion.lancer(repli=False)
    _ecrire(
        tmp_path,
        _ligne(Etape.extraction, StatutEtape.en_cours, 0),
        _ligne(Etape.extraction, StatutEtape.reussie, 5, message="12 tickets"),
    )
    journal = gestion.vue(False, None).journal
    assert [(j.horodatage, j.texte) for j in journal] == [
        ("07:30:05", "extraction : Réussie · 12 tickets"),
        ("07:30:00", "extraction : En cours"),
    ]


def test_journal_vide_selon_le_statut(tmp_path: Path) -> None:
    gestion, _ = _gestion(tmp_path)
    assert gestion.vue(False, None).journal_vide == JOURNAL_ATTENTE
    gestion.lancer(repli=False)
    vue = gestion.vue(False, None)
    assert vue.journal_vide == JOURNAL_VIDE
    assert vue.journal == []
    assert vue.annonce == "Chaîne en cours…"


def test_ligne_finale_partielle_ignoree(tmp_path: Path) -> None:
    gestion, _ = _gestion(tmp_path)
    gestion.lancer(repli=False)
    _ecrire(
        tmp_path,
        _ligne(Etape.extraction, StatutEtape.en_cours, 0),
        partielle=_ligne(Etape.extraction, StatutEtape.reussie, 1)[:30],
    )
    vue = gestion.vue(False, None)
    assert len(vue.journal) == 1
    assert vue.terminees == 0
    assert vue.erreur is None


def test_progression_invalide_signalee_sondage_maintenu(tmp_path: Path) -> None:
    gestion, _ = _gestion(tmp_path)
    gestion.lancer(repli=False)
    _ecrire(tmp_path, "pas du json")
    vue = gestion.vue(False, None)
    assert vue.erreur
    assert vue.statut == "en_cours"
    assert vue.etapes[0].etat == "en_attente"
    assert vue.journal == []


# --- fin et échec ---


def test_fin_reussie(tmp_path: Path) -> None:
    gestion, lanceur = _gestion(tmp_path, erreur=b"bruit ignore")
    gestion.lancer(repli=False)
    lanceur.finir(0)
    vue = gestion.vue(False, manifeste())
    assert vue.statut == "terminee"
    assert vue.en_cours is False
    assert vue.annonce == MESSAGE_SUCCES
    assert vue.bouton_lancement.libelle == LIBELLE_RELANCER
    assert vue.bouton_lancement.bloque is False
    assert vue.bouton_mode.bloque is False
    assert vue.bouton_mode.motif is None
    bandeau = vue.bandeau
    assert bandeau is not None
    assert bandeau.variante == "succes"
    assert bandeau.texte == MESSAGE_SUCCES
    assert bandeau.lignes == []
    assert bandeau.complement is None
    assert bandeau.lien is not None
    assert (bandeau.lien.libelle, bandeau.lien.url) == ("Voir la carte météo", "/")


def test_echec_sans_sortie_ni_etape(tmp_path: Path) -> None:
    gestion, lanceur = _gestion(tmp_path)
    gestion.lancer(repli=False)
    lanceur.finir(3)
    vue = gestion.vue(False, None)
    assert vue.statut == "echec"
    assert vue.annonce == "Échec de la Chaîne hors d'une étape."
    assert vue.bouton_lancement.libelle == LIBELLE_RELANCER
    bandeau = vue.bandeau
    assert bandeau is not None
    assert bandeau.variante == "erreur"
    assert bandeau.texte == "Échec de la Chaîne hors d'une étape (code 3)."
    assert bandeau.lignes == ["aucun message"]
    assert bandeau.complement == AUCUN_RAPPORT
    assert bandeau.lien is None


def test_echec_nomme_l_etape(tmp_path: Path) -> None:
    gestion, lanceur = _gestion(tmp_path, erreur=b"Traceback\nBoum\n")
    gestion.lancer(repli=False)
    _ecrire(
        tmp_path,
        _ligne(Etape.extraction, StatutEtape.en_cours, 0),
        _ligne(Etape.extraction, StatutEtape.reussie, 1),
        _ligne(Etape.instantanes, StatutEtape.en_cours, 1),
        _ligne(Etape.instantanes, StatutEtape.echouee, 2),
    )
    lanceur.finir(1)
    vue = gestion.vue(False, None)
    assert vue.etapes[1].etat == "echouee"
    assert vue.etapes[1].libelle_etat == "Échec"
    assert vue.terminees == 2
    assert vue.annonce == "Échec de la Chaîne à l'étape « instantanes »."
    assert vue.bandeau is not None
    assert vue.bandeau.texte == "Échec de la Chaîne à l'étape « instantanes » (code 1)."
    assert vue.bandeau.lignes == ["Traceback", "Boum"]


@SANS_FIXTURE
@given(
    lignes=st.lists(
        st.text(alphabet="abcdefXYZ0123456789_-", min_size=1, max_size=15),
        min_size=1,
        max_size=60,
    ),
    code=st.integers(min_value=1, max_value=255),
)
def test_bandeau_garde_les_dernieres_lignes_d_erreur(
    tmp_path_factory: pytest.TempPathFactory, lignes: list[str], code: int
) -> None:
    racine = tmp_path_factory.mktemp("err")
    gestion, lanceur = _gestion(racine, erreur="\n".join(lignes).encode())
    gestion.lancer(repli=False)
    lanceur.finir(code)
    bandeau = gestion.vue(False, None).bandeau
    assert bandeau is not None
    assert len(bandeau.lignes) == min(len(lignes), LIGNES_ERREUR_MAX)
    assert bandeau.lignes == lignes[-LIGNES_ERREUR_MAX:]
    assert f"(code {code})" in bandeau.texte


def test_borne_exacte_de_20_lignes(tmp_path: Path) -> None:
    assert LIGNES_ERREUR_MAX == 20
    erreur = "\n".join(f"l{i}" for i in range(21)).encode()
    gestion, lanceur = _gestion(tmp_path, erreur=erreur)
    gestion.lancer(repli=False)
    lanceur.finir(1)
    bandeau = gestion.vue(False, None).bandeau
    assert bandeau is not None
    assert bandeau.lignes == [f"l{i}" for i in range(1, 21)]


def test_erreur_standard_lue_une_seule_fois(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lectures: list[int] = []
    reel = module_chaine.lancement.lire_erreurs

    def espion(fichier: Any) -> str:
        lectures.append(1)
        return cast(str, reel(fichier))

    monkeypatch.setattr(module_chaine.lancement, "lire_erreurs", espion)
    gestion, lanceur = _gestion(tmp_path, erreur=b"x\n")
    gestion.lancer(repli=False)
    lanceur.finir(2)
    premier = gestion.vue(False, None)
    second = gestion.vue(False, None)
    assert len(lectures) == 1
    assert premier.bandeau == second.bandeau


# --- boutons de mode ---


def test_bouton_mode_en_repli(tmp_path: Path) -> None:
    gestion, _ = _gestion(tmp_path)
    vue = gestion.vue(True, None)
    assert vue.bouton_mode.libelle == "Revenir au Mode réel"
    assert vue.mode_cible == "reel"
    assert vue.bouton_lancement.bloque is True
    assert vue.bouton_lancement.motif == LANCEMENT_REPLI.replace("`", "")
    assert vue.message_dernier_passage == AUCUN_PASSAGE_REPLI
    assert gestion.vue(False, None).message_dernier_passage == AUCUN_PASSAGE_LANCE


def test_vue_dernier_passage_lignes() -> None:
    m = manifeste()
    vue = vue_dernier_passage(m)
    assert len(vue.lignes) == 3
    assert vue.lignes[0].startswith("Date d'arrêté ")
    assert " · durée " in vue.lignes[0]
    assert vue.lignes[1].endswith(" tickets extraits")
    assert vue.lignes[2] == f"Passage {m.passage_id}"


# --- API : mode, origines, corps ---


def _banc(tmp_path: Path, **options: Any) -> Banc:
    return Banc(tmp_path, passage=manifeste(), **options)


def test_bascule_aller_retour(tmp_path: Path) -> None:
    banc = _banc(tmp_path)
    assert banc.mode("repli").status_code == 200
    assert banc.etat()["mode_cible"] == "reel"
    assert banc.lectures[-1] is True
    assert banc.mode("reel").status_code == 200
    assert banc.etat()["mode_cible"] == "repli"
    assert banc.lectures[-1] is False


def test_bascule_refusee_pendant_une_chaine(tmp_path: Path) -> None:
    banc = _banc(tmp_path)
    assert banc.lancer().status_code == 202
    reponse = banc.mode("repli")
    assert reponse.status_code == 409
    assert "Chaîne" in reponse.json()["detail"]
    assert banc.etat()["mode_cible"] == "repli"  # toujours en Mode réel


def test_lancement_409_en_repli_et_pendant_une_chaine(tmp_path: Path) -> None:
    banc = _banc(tmp_path, repli=True)
    reponse = banc.lancer()
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == LANCEMENT_REPLI.replace("`", "")
    assert banc.lanceur.appels == []
    banc = _banc(tmp_path)
    assert banc.lancer().status_code == 202
    second = banc.lancer()
    assert second.status_code == 409
    assert second.json()["detail"] == MOTIF_LANCEMENT_EN_COURS
    assert len(banc.lanceur.appels) == 1


def test_lancement_sans_racine_409() -> None:
    application = creer_application(
        repli=False,
        lire_manifeste=lambda _r: None,
        lire_consultation=lambda _r: None,
        chaine=GestionChaine(None),
    )
    reponse = TestClient(application, base_url=f"http://{HOTE}").post("/api/chaine")
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == MOTIF_RACINE


@pytest.mark.parametrize(
    "corps",
    [
        {"mode": "autre"},
        {"mode": ""},
        {"mode": "REPLI"},
        {},
        {"mode": "repli", "extra": 1},
        {"mode": None},
        {"mode": 1},
    ],
)
def test_corps_invalide_422(tmp_path: Path, corps: dict[str, Any]) -> None:
    banc = _banc(tmp_path)
    assert banc.http.post("/api/mode", json=corps).status_code == 422
    assert banc.etat()["mode_cible"] == "repli"


def test_corps_non_json_422(tmp_path: Path) -> None:
    banc = _banc(tmp_path)
    reponse = banc.http.post(
        "/api/mode", content=b"pas du json", headers={"content-type": "application/json"}
    )
    assert reponse.status_code == 422


@pytest.mark.parametrize(
    "origine",
    ["null", "http://evil.test", f"http://{HOTE}:9999", "http://localhost", "https://127.0.0.1:1"],
)
def test_origine_etrangere_403_sans_effet(tmp_path: Path, origine: str) -> None:
    banc = _banc(tmp_path)
    assert banc.http.post("/api/chaine", headers={"Origin": origine}).status_code == 403
    assert banc.lanceur.appels == []
    reponse = banc.http.post("/api/mode", json={"mode": "repli"}, headers={"Origin": origine})
    assert reponse.status_code == 403
    assert banc.etat()["mode_cible"] == "repli"


def test_meme_origine_acceptee(tmp_path: Path) -> None:
    banc = _banc(tmp_path)
    reponse = banc.http.post("/api/mode", json={"mode": "repli"}, headers={"Origin": f"http://{HOTE}"})
    assert reponse.status_code == 200


@pytest.mark.parametrize("hote", ["evil.test", "evil.test:8765", "127.0.0.2", "testserver"])
def test_host_forge_400_partout(tmp_path: Path, hote: str) -> None:
    banc = _banc(tmp_path)
    for methode, chemin in (("get", "/api/chaine"), ("get", "/api/cadre"), ("post", "/api/chaine")):
        reponse = getattr(banc.http, methode)(chemin, headers={"Host": hote})
        assert reponse.status_code == 400
    assert banc.lanceur.appels == []


def test_host_localhost_accepte_avec_port(tmp_path: Path) -> None:
    banc = _banc(tmp_path)
    for hote in ("localhost", "localhost:8765", f"{HOTE}:8765"):
        assert banc.http.get("/api/chaine", headers={"Host": hote}).status_code == 200


def test_get_chaine_ne_lance_rien(tmp_path: Path) -> None:
    banc = _banc(tmp_path)
    for _ in range(3):
        banc.etat()
    assert banc.lanceur.appels == []
