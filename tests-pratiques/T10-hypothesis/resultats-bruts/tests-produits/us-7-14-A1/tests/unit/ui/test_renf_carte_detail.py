"""Renfort Story 7.14 : bornes, branches d'erreur et valeurs exactes de la carte, du détail, des
livrables et des routes."""

from datetime import date
from typing import Literal

import pytest
from fastapi.testclient import TestClient

from tests.unit.ui.test_detail import DATE, _meteo, _prevision, _regle, _risque
from tests.unit.ui.test_vues_ecrans import XLSX, _Double, _url, client
from usine.contrats.erreurs import UsineErreur
from usine.contrats.llm import StatutControle
from usine.contrats.meteo import CodeIndicateur, Couleur, EvolutionMeteo
from usine.contrats.prevision import StatutPrevision
from usine.ui import carte, detail
from usine.ui.liens import vue_ticket
from usine.ui.serveur import HOTE, LectureEcrans, creer_application

NomLivrable = Literal["rapport_xlsx", "rapport_pptx"]


def _tickets(n: int) -> tuple[str, ...]:
    return tuple(f"DEMO-{i}" for i in range(1, n + 1))


def _couleur(entite: str, couleur: Couleur, n_tickets: int = 1):  # type: ignore[no-untyped-def]
    base = _meteo(entite, regles=(_regle(CodeIndicateur.ind_2, _tickets(n_tickets)),))
    return base.model_copy(update={"couleur": couleur})


# --- taille_lisible, libelle_suite, url_detail ---


@pytest.mark.parametrize(
    ("octets", "attendu"),
    [
        (0, "0 o"),
        (1, "1 o"),
        (1023, "1023 o"),
        (1024, "1 Ko"),
        (1535, "1 Ko"),
        (1536, "2 Ko"),
        (1024 * 1023, "1023 Ko"),
        (1024 * 1024 - 513, "1023 Ko"),
        (1024 * 1024 - 512, "1,0 Mo"),
        (1024 * 1024, "1,0 Mo"),
        (5 * 1024 * 1024, "5,0 Mo"),
        (int(2.55 * 1024 * 1024), "2,5 Mo"),
    ],
)
def test_taille_lisible_bornes(octets: int, attendu: str) -> None:
    assert carte.taille_lisible(octets) == attendu


@pytest.mark.parametrize(
    ("reste", "attendu"), [(-3, None), (-1, None), (0, None), (1, "+1"), (2, "+2"), (12, "+12")]
)
def test_libelle_suite(reste: int, attendu: str | None) -> None:
    assert carte.libelle_suite(reste) == attendu


def test_url_detail_encode_tout() -> None:
    assert carte.url_detail("ENT-B") == "/entites/ENT-B"
    assert carte.url_detail("A/B?x#y") == "/entites/A%2FB%3Fx%23y"
    assert carte.url_detail("É t") == "/entites/%C3%89%20t"


def test_nom_fichier_livrable() -> None:
    assert carte.nom_fichier_livrable("rapport_xlsx", date(2026, 1, 5)) == "rapport-2026-01-05.xlsx"
    assert carte.nom_fichier_livrable("rapport_pptx", date(2026, 12, 31)) == (
        "rapport-2026-12-31.pptx"
    )


def test_constantes_livrables() -> None:
    assert list(carte.LIVRABLES) == ["rapport_xlsx", "rapport_pptx"]
    assert carte.LIVRABLES["rapport_pptx"] == ("Comité de pilotage", "PowerPoint (.pptx)")
    assert set(carte.MIME_LIVRABLES) == set(carte.LIVRABLES)
    assert carte.NON_GENERE == "Non généré pour ce Passage"
    assert carte.TICKETS_MAX == 3


# --- tri, flèches, règle principale ---


def test_entites_triees_grave_puis_entite_et_vide() -> None:
    meteos = [
        _couleur("ENT-Z", Couleur.rouge),
        _couleur("ENT-B", Couleur.jaune),
        _couleur("ENT-A", Couleur.jaune),
        _meteo("ENT-C"),
        _couleur("ENT-D", Couleur.orange),
        _couleur("ENT-A2", Couleur.rouge),
    ]
    assert [m.entite for m in carte.entites_triees(meteos)] == [
        "ENT-A2",
        "ENT-Z",
        "ENT-D",
        "ENT-A",
        "ENT-B",
        "ENT-C",
    ]
    assert carte.entites_triees([]) == []


def test_fleches_et_tendance() -> None:
    assert carte.fleche(None, Couleur.rouge) == "—"
    assert carte.fleche(Couleur.vert, Couleur.rouge) == "↗"
    assert carte.fleche(Couleur.rouge, Couleur.vert) == "↘"
    assert carte.fleche(Couleur.jaune, Couleur.jaune) == "→"
    assert carte.tendance(None) == "J-1 — · J-5 —"
    evolution = EvolutionMeteo(
        date_arrete=DATE,
        entite="ENT-A",
        couleur=Couleur.orange,
        date_j1=date(2026, 10, 8),
        couleur_j1=Couleur.rouge,
        date_j5=date(2026, 10, 2),
        couleur_j5=None,
    )
    assert carte.tendance(evolution) == "J-1 ↘ · J-5 —"


def test_regle_principale_suffixe_autres_regles() -> None:
    deux = _meteo(
        "ENT-A",
        regles=(_regle(CodeIndicateur.ind_2, ("DEMO-1",)), _regle(CodeIndicateur.ind_3, ())),
    )
    assert carte.regle_principale(deux) == "IND-2 : 11 (seuil ≥ 10) (+1)"
    assert carte.regle_principale(_meteo("ENT-A")) == "—"


# --- vue_carte directe : bornes des tickets ---


@pytest.mark.parametrize(
    ("n", "visibles", "suite"),
    [(0, 0, None), (1, 1, None), (3, 3, None), (4, 3, "+1"), (5, 3, "+2"), (10, 3, "+7")],
)
def test_vue_carte_borne_tickets(n: int, visibles: int, suite: str | None) -> None:
    double = _Double(meteos=(_couleur("ENT-A", Couleur.rouge, n),))
    (ligne,) = carte.vue_carte(double).lignes
    assert [t.cle for t in ligne.tickets] == list(_tickets(n))[:visibles]
    assert ligne.suite == suite


def test_vue_carte_entite_verte_sans_regle() -> None:
    (ligne,) = carte.vue_carte(_Double(meteos=(_meteo("ENT-A"),))).lignes
    assert ligne.regle_principale == "—"
    assert ligne.tickets == []
    assert ligne.suite is None
    assert ligne.tendance == "J-1 — · J-5 —"
    assert ligne.meteo.libelle == "Vert"


def test_vue_carte_comptages_somme_et_ordre() -> None:
    meteos = (
        _couleur("ENT-A", Couleur.rouge),
        _couleur("ENT-B", Couleur.rouge),
        _couleur("ENT-C", Couleur.rouge),
        _couleur("ENT-D", Couleur.jaune),
        _meteo("ENT-E"),
    )
    vue = carte.vue_carte(_Double(meteos=meteos))
    assert [(c.meteo.couleur, c.meteo.libelle, c.nombre) for c in vue.comptages] == [
        ("rouge", "Rouge", 3),
        ("orange", "Orange", 0),
        ("jaune", "Jaune", 1),
        ("vert", "Vert", 1),
    ]
    assert sum(c.nombre for c in vue.comptages) == len(vue.lignes) == 5
    assert vue.erreur is None
    assert vue.message is None
    assert vue.lien_message is None


def test_vue_carte_filtre_message_vide_pour_chaque_couleur() -> None:
    filtre = carte.vue_carte(_Double()).filtre
    assert filtre is not None
    toutes = filtre.options[0]
    assert (toutes.valeur, toutes.libelle, toutes.message_vide) == ("toutes", "Toutes", "")
    messages = {o.valeur: o.message_vide for o in filtre.options[1:]}
    assert messages == {
        "rouge": "Aucune Entité en rouge à cette Date d'arrêté.",
        "orange": "Aucune Entité en orange à cette Date d'arrêté.",
        "jaune": "Aucune Entité en jaune à cette Date d'arrêté.",
        "vert": "Aucune Entité en vert à cette Date d'arrêté.",
    }


def test_vue_carte_message_et_erreur() -> None:
    lien = carte.VueLien(libelle="x", url="/y")
    vue = carte.vue_carte_message("m", lien)
    assert (vue.message, vue.lien_message, vue.erreur) == ("m", lien, None)
    assert vue.lignes == vue.livrables == vue.comptages == []
    assert vue.filtre is None
    assert vue.legende is None
    assert vue.sous_titre is None
    erreur = carte.vue_carte_erreur("boum")
    assert erreur.erreur == "boum"
    assert erreur.message is None
    assert erreur.lignes == []


def test_vue_carte_tendance_utilise_evolution() -> None:
    class _Evo(_Double):
        def evolution_meteo(self, date_arrete: date | None = None):  # type: ignore[no-untyped-def]
            return (
                EvolutionMeteo(
                    date_arrete=DATE,
                    entite="ENT-B",
                    couleur=Couleur.rouge,
                    date_j1=date(2026, 10, 8),
                    couleur_j1=Couleur.vert,
                    date_j5=date(2026, 10, 2),
                    couleur_j5=Couleur.rouge,
                ),
            )

    lignes = {ligne.entite: ligne.tendance for ligne in carte.vue_carte(_Evo()).lignes}
    assert lignes["ENT-B"] == "J-1 ↗ · J-5 →"
    assert lignes["ENT-A"] == "J-1 — · J-5 —"


# --- vues_livrables ---


def test_vues_livrables_les_deux_presents_et_aucun() -> None:
    deux = carte.vues_livrables(
        _Double(livrables={"rapport_xlsx": b"a" * 1023, "rapport_pptx": b"b" * 1024})
    )
    assert [(v.nom, v.fichier, v.url, v.absent) for v in deux] == [
        ("rapport_xlsx", "rapport-2026-10-09.xlsx", "/livrables/rapport_xlsx", None),
        ("rapport_pptx", "rapport-2026-10-09.pptx", "/livrables/rapport_pptx", None),
    ]
    assert [v.description for v in deux] == ["Excel (.xlsx) · 1023 o", "PowerPoint (.pptx) · 1 Ko"]
    aucun = carte.vues_livrables(_Double(livrables={}))
    assert [v.url for v in aucun] == [None, None]
    assert [v.absent for v in aucun] == ["Non généré pour ce Passage"] * 2
    assert [v.description for v in aucun] == ["", ""]


def test_livrable_vide_est_present() -> None:
    (xlsx, _pptx) = carte.vues_livrables(_Double(livrables={"rapport_xlsx": b""}))
    assert xlsx.url == "/livrables/rapport_xlsx"
    assert xlsx.description == "Excel (.xlsx) · 0 o"
    assert xlsx.absent is None


# --- vue_ticket ---


def test_vue_ticket_exact() -> None:
    assert vue_ticket("DEMO-1", "https://x/y").model_dump() == {
        "cle": "DEMO-1",
        "url": "https://x/y",
        "nom_accessible": "DEMO-1 (nouvel onglet)",
    }
    assert vue_ticket("DEMO-1", None).model_dump() == {
        "cle": "DEMO-1",
        "url": None,
        "nom_accessible": None,
    }


# --- Détail : sections ---


def test_section_prevision_branches() -> None:
    rouge = _couleur("ENT-A", Couleur.rouge)
    verte = _meteo("ENT-A")
    sortie = _prevision(StatutPrevision.sortie_projetee)
    assert detail.section_prevision(rouge, (sortie,), False).message == (
        "Prévision non calculée pour ce Passage"
    )
    assert detail.section_prevision(verte, (sortie,), True).message == (
        "Sans objet : l'Entité n'est pas rouge."
    )
    assert detail.section_prevision(rouge, (), True).message == (
        "Prévision non calculée pour cette Entité"
    )
    autre = _prevision(StatutPrevision.sortie_projetee, "ENT-Z")
    assert detail.section_prevision(rouge, (autre,), True).message == (
        "Prévision non calculée pour cette Entité"
    )


def test_section_prevision_blocs_exacts() -> None:
    rouge = _couleur("ENT-A", Couleur.rouge)
    (bloc,) = detail.section_prevision(
        rouge, (_prevision(StatutPrevision.sortie_projetee),), True
    ).blocs
    assert bloc.titre == "Sortie du rouge estimée : 20/10/2026"
    assert bloc.items == [
        "Fourchette : 16/10/2026 – 23/10/2026",
        "Probabilité de sortie dans l'horizon : 75 %",
        "Horizon : 10 jours ouvrés",
        "Méthode : baseline",
    ]
    assert bloc.sous_titre == "Facteurs explicatifs"
    assert bloc.sous_items == ["Stock d'Anomalies : 12", "Vélocité : 1,5"]
    (pas,) = detail.section_prevision(
        rouge, (_prevision(StatutPrevision.pas_de_sortie_projetee),), True
    ).blocs
    assert pas.titre == "pas de sortie projetée"
    assert pas.items == bloc.items[1:3]
    (non,) = detail.section_prevision(
        rouge, (_prevision(StatutPrevision.regle_non_projetable),), True
    ).blocs
    assert non.titre == "pas de sortie projetée : règle non projetable (IND-2)"


def test_section_prevision_narration_acceptee_ou_ignoree() -> None:
    from tests.unit.ui.test_detail import _narration

    rouge = _couleur("ENT-A", Couleur.rouge)
    previsions = (_prevision(StatutPrevision.sortie_projetee),)
    for statut, libelle in (
        (StatutControle.conforme, "conforme"),
        (StatutControle.corrige, "corrigée (phrases fautives retirées)"),
    ):
        (bloc,) = detail.section_prevision(
            rouge, previsions, True, (_narration(statut, "ENT-A"),)
        ).blocs
        assert bloc.texte == "La sortie du rouge est attendue sous deux semaines."
        assert bloc.note == f"narration contrôlée ({libelle})"
    for statut in (StatutControle.rejete, StatutControle.non_controle):
        (bloc,) = detail.section_prevision(
            rouge, previsions, True, (_narration(statut, "ENT-A"),)
        ).blocs
        assert bloc.texte is None
        assert bloc.titre.startswith("Sortie du rouge estimée")
    (bloc,) = detail.section_prevision(
        rouge, previsions, True, (_narration(StatutControle.conforme, "ENT-Z"),)
    ).blocs
    assert bloc.texte is None


def test_section_risque_branches() -> None:
    verte = _meteo("ENT-B")
    rouge = _couleur("ENT-B", Couleur.rouge)
    assert detail.section_risque(verte, (_risque("ENT-B"),), False).message == (
        "Risque d'entrée en rouge non calculé pour ce Passage"
    )
    assert detail.section_risque(rouge, (_risque("ENT-B"),), True).message == (
        "Sans objet : l'Entité est déjà rouge."
    )
    assert detail.section_risque(verte, (), True).message == (
        "Aucun Risque d'entrée en rouge dans l'horizon."
    )
    assert detail.section_risque(verte, (_risque("ENT-Z"),), True).message == (
        "Aucun Risque d'entrée en rouge dans l'horizon."
    )
    section = detail.section_risque(verte, (_risque("ENT-B"),), True)
    assert section.message is None
    assert section.tableau is not None
    assert section.tableau.colonnes[0] == "Indicateur"
    assert len(section.tableau.lignes) == 1
    assert all(len(ligne) == len(section.tableau.colonnes) for ligne in section.tableau.lignes)


def test_vue_detail_message_et_erreur_directs() -> None:
    message = detail.vue_detail_message("m", entite="ENT-A")
    assert message.message == "m"
    assert message.lien_message is not None
    assert (message.lien_message.libelle, message.lien_message.url) == ("Voir la carte météo", "/")
    assert message.lien_carte.libelle == "← Carte météo"
    assert message.palier == 2
    assert message.entites == []
    erreur = detail.vue_detail_erreur("boum")
    assert (erreur.erreur, erreur.message, erreur.lien_message) == ("boum", None, None)
    assert detail.entite_absente("ENT-X") == "Entité ENT-X absente du Passage affiché."


# --- Détail : bornes des tickets d'une Règle, KPI, sections ---


@pytest.mark.parametrize(
    ("n", "visibles", "restants", "suite"),
    [(0, 0, 0, None), (3, 3, 0, None), (4, 3, 1, "+1"), (7, 3, 4, "+4")],
)
def test_detail_regle_tickets_et_suite(n: int, visibles: int, restants: int, suite: str | None):
    double = _Double(meteos=(_couleur("ENT-B", Couleur.rouge, n),))
    (regle,) = detail.vue_detail(double, "ENT-B").regles
    assert [t.cle for t in regle.tickets] == list(_tickets(n))[:visibles]
    assert [t.cle for t in regle.tickets_suite] == list(_tickets(n))[visibles:]
    assert len(regle.tickets_suite) == restants
    assert regle.libelle_suite == suite


def test_detail_plusieurs_regles_dans_l_ordre() -> None:
    meteo = _meteo(
        "ENT-B",
        regles=(_regle(CodeIndicateur.ind_3, ("DEMO-1",)), _regle(CodeIndicateur.ind_2, ())),
    ).model_copy(update={"couleur": Couleur.rouge})
    vue = detail.vue_detail(_Double(meteos=(meteo,)), "ENT-B")
    assert [r.regle.split(" :")[0] for r in vue.regles] == ["IND-3", "IND-2"]
    assert vue.aucune_regle is None
    assert vue.regles[1].tickets == []
    assert vue.regles[1].libelle_suite is None


def test_detail_entite_verte_messages_et_kpi() -> None:
    vue = detail.vue_detail(_Double(), "ENT-A")
    assert vue.aucune_regle == "Aucune Règle déclenchante (Entité verte)."
    assert vue.aucun_kpi is not None or vue.kpi  # KPI du double renvoyés quelle que soit l'Entité
    vue_b = detail.vue_detail(_Double(), "ENT-B")
    assert vue_b.aucun_kpi is None
    assert vue_b.kpi[0].libelle == "Anomalies ouvertes"
    assert vue_b.kpi[0].valeur == "40"


def test_detail_sans_kpi() -> None:
    import polars as pl

    class _SansKpi(_Double):
        def kpi(self, date_arrete: date | None = None, entite: str | None = None):  # type: ignore[no-untyped-def]
            return pl.DataFrame(
                {
                    "date": [],
                    "perimetre": [],
                    "code_kpi": [],
                    "dimension": [],
                    "numerateur": [],
                    "denominateur": [],
                },
                schema={
                    "date": pl.Date,
                    "perimetre": pl.String,
                    "code_kpi": pl.String,
                    "dimension": pl.String,
                    "numerateur": pl.Int64,
                    "denominateur": pl.Int64,
                },
            )

    vue = detail.vue_detail(_SansKpi(), "ENT-B")
    assert vue.kpi == []
    assert vue.aucun_kpi == "Aucun KPI pour cette Entité à la Date d'arrêté du Passage."


def test_detail_entites_liste_triee_et_entite_absente_garde_la_liste() -> None:
    vue = detail.vue_detail(_Double(), "ENT-X")
    assert [(e.libelle, e.url) for e in vue.entites] == [
        ("ENT-B", "/entites/ENT-B"),
        ("ENT-C", "/entites/ENT-C"),
        ("ENT-A", "/entites/ENT-A"),
    ]
    assert vue.entite is None
    assert vue.regles == []
    assert vue.explication is None
    assert vue.risque is None


def test_detail_palier_1_explication_jamais_lue_sur_passage_palier_1() -> None:
    double = _Double(palier=1)
    detail.vue_detail(double, "ENT-B", 2)
    detail.vue_detail(double, "ENT-B", 1)
    assert double.appels_palier == [1, 1]


def test_detail_palier_2_demande_deux_appelle_palier_2() -> None:
    double = _Double()
    vue = detail.vue_detail(double, "ENT-B", 2)
    assert double.appels_palier == [2]
    assert vue.palier == 2
    assert vue.prevision is not None


# --- Routes ---


@pytest.mark.parametrize("valeur", ["0", "3", "", "01", "un", "1.0"])
def test_palier_hors_1_donne_palier_2(valeur: str) -> None:
    vue = client().get(f"/api/entites/ENT-B?palier={valeur}").json()
    assert vue["palier"] == 2
    assert vue["prevision"] is not None


def test_palier_1_explicite_masque_prevision() -> None:
    vue = client().get("/api/entites/ENT-B?palier=1").json()
    assert vue["palier"] == 1
    assert vue["prevision"] is None


def test_livrable_head_et_methodes() -> None:
    http = client()
    tete = http.head("/livrables/rapport_pptx")
    assert tete.status_code == 404
    assert http.head("/livrables/autre").status_code == 404
    assert http.post("/livrables/rapport_xlsx").status_code == 405
    ok = http.head("/livrables/rapport_xlsx")
    assert ok.headers["content-disposition"] == 'attachment; filename="rapport-2026-10-09.xlsx"'
    assert ok.headers["content-length"] == str(len(XLSX))


def test_livrable_absent_message_exact_et_html() -> None:
    reponse = client().get("/livrables/rapport_pptx")
    assert "Le livrable rapport-2026-10-09.pptx n&#x27;a pas été généré pour ce Passage." in (
        reponse.text
    )
    assert "<title>Livrable indisponible" in reponse.text
    assert 'role="alert"' in reponse.text
    assert "← Carte météo" in reponse.text


def test_livrable_sans_passage_message_exact() -> None:
    def aucun(_repli: bool) -> None:
        return None

    http = TestClient(creer_application(repli=False, lire_manifeste=aucun, lire_consultation=aucun))
    reponse = http.get("/livrables/rapport_pptx")
    assert reponse.status_code == 404
    assert "Le livrable rapport_pptx n&#x27;est pas disponible : Aucun Passage publié" in (
        reponse.text
    )


def test_livrable_oserror_et_erreur_de_manifeste() -> None:
    class _Os(_Double):
        def livrable(self, nom: NomLivrable) -> bytes | None:
            raise PermissionError(13, "refusé")

    reponse = client(_Os()).get("/livrables/rapport_pptx")
    assert reponse.status_code == 500
    assert "Lecture du livrable rapport-2026-10-09.pptx impossible" in reponse.text

    def casse(_repli: bool) -> LectureEcrans:
        raise UsineErreur("racine <x>")

    http = TestClient(
        creer_application(repli=False, lire_manifeste=lambda _: None, lire_consultation=casse)
    )
    erreur = http.get("/livrables/rapport_xlsx")
    assert erreur.status_code == 500
    assert "Lecture du livrable rapport_xlsx impossible : racine &lt;x&gt;" in erreur.text


def test_livrable_sert_le_mode_repli_donne() -> None:
    modes: list[bool] = []

    def lire(repli: bool) -> LectureEcrans:
        modes.append(repli)
        return _Double()

    http = TestClient(
        creer_application(repli=True, lire_manifeste=lambda _: None, lire_consultation=lire),
        base_url=f"http://{HOTE}",
    )
    http.get("/api/carte")
    http.get("/api/entites/ENT-A")
    http.get("/livrables/rapport_xlsx")
    http.get("/entites", follow_redirects=False)
    assert modes == [True] * 4


def test_entites_redirige_vers_la_plus_grave_puis_alphabetique() -> None:
    meteos = (_meteo("ENT-A"), _couleur("ENT-Z", Couleur.rouge), _couleur("ENT-M", Couleur.rouge))
    reponse = client(_Double(meteos=meteos)).get("/entites", follow_redirects=False)
    assert reponse.status_code == 307
    assert reponse.headers["location"] == "/entites/ENT-M"


def test_entites_sans_meteo_redirige_vers_carte() -> None:
    reponse = client(_Double(meteos=())).get("/entites", follow_redirects=False)
    assert reponse.status_code == 307
    assert reponse.headers["location"] == "/"


def test_entites_oserror_redirige_vers_carte() -> None:
    def illisible(_repli: bool) -> LectureEcrans:
        raise PermissionError(13, "refusé")

    http = TestClient(
        creer_application(repli=False, lire_manifeste=lambda _: None, lire_consultation=illisible)
    )
    assert http.get("/entites", follow_redirects=False).headers["location"] == "/"


def test_detail_oserror_message_exact() -> None:
    def illisible(_repli: bool) -> LectureEcrans:
        raise PermissionError(13, "refusé", "sorties")

    http = TestClient(
        creer_application(repli=False, lire_manifeste=lambda _: None, lire_consultation=illisible)
    )
    vue = http.get("/api/entites/ENT-A").json()
    assert vue["erreur"].startswith("Lecture du Passage impossible : ")
    assert vue["message"] is None
    assert vue["lien_message"] is None


def test_carte_sans_passage_aucune_erreur_et_champs_vides() -> None:
    http = TestClient(
        creer_application(
            repli=False, lire_manifeste=lambda _: None, lire_consultation=lambda _: None
        )
    )
    vue = http.get("/api/carte").json()
    assert vue["erreur"] is None
    assert vue["lignes"] == []
    assert vue["comptages"] == []
    assert vue["filtre"] is None
    assert vue["livrables"] == []


def test_api_carte_tickets_url_exacte() -> None:
    ligne = client().get("/api/carte").json()["lignes"][1]
    assert ligne["entite"] == "ENT-C"
    assert ligne["tickets"] == [
        {"cle": "DEMO-9", "url": _url("DEMO-9"), "nom_accessible": "DEMO-9 (nouvel onglet)"}
    ]
    assert ligne["suite"] is None
    assert ligne["regle_principale"] == "IND-3 : 11 (seuil ≥ 10)"
