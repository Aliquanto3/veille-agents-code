# ruff: noqa: E501
"""Renforcement story 5.9 : bornes du schéma, branches du lint, projection `blockers_body`
(chaîne absente, station inconnue, jalon, libellés) et titres du catalogue."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any

import pytest
from hypothesis import given, settings as hsettings
from hypothesis import strategies as st

from wavedevsecops.config import Settings
from wavedevsecops.scenarios import ScenarioError, parse_scenario
from wavedevsecops.scenarios.model import Blocker
from wavedevsecops.web import blockers as bm
from wavedevsecops.web.blockers import blockers_body, catalogue_scenario_titles, chain_barriers

BASE = """
schema_version: 1
scenario_id: essai
mode: B
title_text: Essai
tracks: [llm]
"""
KEBAB = st.from_regex(r"[a-z][a-z0-9]*(-[a-z0-9]+)*", fullmatch=True)


def _decl(barrier="secret-scan", station=1, scenario="sc-a", reason="Parce que.") -> str:
    return (
        f"  - barrier_id: {barrier}\n    station: {station}\n"
        f"    scenario_id: {scenario}\n    reason_text: {reason}\n"
    )


def _parse(blockers: str, **kwargs: Any):
    return parse_scenario(BASE + "blocked_by:\n" + blockers, "essai.B.yaml", **kwargs)


def _blocker(**kw: Any) -> Blocker:
    base = {"barrier_id": "b", "station": 1, "scenario_id": "s", "reason_text": "x"}
    return Blocker(**{**base, **kw})


# ------------------------------------------------------------------------------------- schéma
@pytest.mark.parametrize("station", [1, 2, 3, 4])
def test_station_dans_les_bornes(station: int) -> None:
    assert _blocker(station=station).station == station


@pytest.mark.parametrize("station", [0, 5, -1])
def test_station_hors_bornes_refusee(station: int) -> None:
    with pytest.raises(ValueError):
        _blocker(station=station)


@pytest.mark.parametrize("bad", ["Majuscule", "a_b", "-a", "a--b", "", "a b"])
def test_identifiants_non_kebab_refuses(bad: str) -> None:
    with pytest.raises(ValueError):
        _blocker(barrier_id=bad)
    with pytest.raises(ValueError):
        _blocker(scenario_id=bad)


def test_phrase_vide_refusee_et_blocker_fige() -> None:
    with pytest.raises(ValueError):
        _blocker(reason_text="")
    b = _blocker()
    with pytest.raises(ValueError):
        b.station = 2  # type: ignore[misc]


@given(KEBAB, st.integers(1, 4), KEBAB, st.text(min_size=1))
def test_blocker_valide_garde_ses_valeurs(barrier: str, station: int, scenario: str, reason: str) -> None:
    b = Blocker(barrier_id=barrier, station=station, scenario_id=scenario, reason_text=reason)
    assert (b.barrier_id, b.station, b.scenario_id, b.reason_text) == (barrier, station, scenario, reason)


# ---------------------------------------------------------------------------------------- lint
def test_sans_parametres_aucune_verification() -> None:
    sc = _parse(_decl(barrier="inconnue", station=3, scenario="fantome"))
    assert [b.barrier_id for b in sc.blocked_by] == ["inconnue"]


def test_le_doublon_est_refuse_meme_sans_parametres() -> None:
    with pytest.raises(ScenarioError) as e:
        _parse(_decl() + _decl(station=2))
    assert "en double" in str(e.value)


def test_barriere_seule_ou_catalogue_seul() -> None:
    # barrières fournies, catalogue non : le scénario fantôme passe
    _parse(_decl(scenario="fantome"), barriers={"secret-scan": 1})
    # catalogue fourni, barrières non : la barrière inconnue passe
    _parse(_decl(barrier="inconnue"), scenario_ids={"sc-a"})
    with pytest.raises(ScenarioError, match="scénario inconnu"):
        _parse(_decl(), scenario_ids=set())
    with pytest.raises(ScenarioError, match="barrière inconnue"):
        _parse(_decl(), barriers={})


def test_station_incoherente_cite_les_deux_numeros() -> None:
    with pytest.raises(ScenarioError) as e:
        _parse(_decl(station=3), barriers={"secret-scan": 2})
    assert "est en station 2" in str(e.value) and "non 3" in str(e.value)


def test_barriere_inconnue_ne_cumule_pas_avec_station() -> None:
    with pytest.raises(ScenarioError) as e:
        _parse(_decl(barrier="inconnue"), barriers={"secret-scan": 1})
    assert "barrière inconnue" in str(e.value) and "est en station" not in str(e.value)


def test_plusieurs_erreurs_sont_toutes_remontees() -> None:
    text = _decl(barrier="x-un", scenario="fantome") + _decl(barrier="x-deux", scenario="fantome")
    with pytest.raises(ScenarioError) as e:
        _parse(text, barriers={}, scenario_ids=set())
    assert str(e.value).count("barrière inconnue") == 2
    assert str(e.value).count("scénario inconnu") == 2


@given(st.lists(KEBAB, min_size=1, max_size=5, unique=True))
def test_declarations_distinctes_et_coherentes_acceptees(ids: list[str]) -> None:
    text = "".join(_decl(barrier=i, station=(n % 4) + 1, scenario="sc-a") for n, i in enumerate(ids))
    barriers = {i: (n % 4) + 1 for n, i in enumerate(ids)}
    sc = _parse(text, barriers=barriers, scenario_ids={"sc-a"})
    assert [b.barrier_id for b in sc.blocked_by] == ids


@given(KEBAB, st.integers(1, 4), st.integers(1, 4))
def test_station_acceptee_ssi_egale_a_celle_de_la_chaine(barrier: str, declared: int, actual: int) -> None:
    text = _decl(barrier=barrier, station=declared)
    if declared == actual:
        assert _parse(text, barriers={barrier: actual})
    else:
        with pytest.raises(ScenarioError):
            _parse(text, barriers={barrier: actual})


# ------------------------------------------------------------------------- fausses chaînes
def _chain(stations: list[Any], map_: Any = None) -> SimpleNamespace:
    return SimpleNamespace(stations=stations, map=map_)


def _station(number: int, name="Nom", delivered=False, milestone="", barriers=()) -> SimpleNamespace:
    return SimpleNamespace(
        number=number,
        name=name,
        delivered=delivered,
        milestone=milestone,
        barriers=[SimpleNamespace(id=i, label=lbl) for i, lbl in barriers],
    )


def _scenario(*blockers: Blocker) -> SimpleNamespace:
    return SimpleNamespace(key="x.B", blocked_by=list(blockers))


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch):
    def install(chain: Any, titles: dict[str, str] | None = None) -> None:
        monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: chain)
        monkeypatch.setattr(bm, "catalogue_scenario_titles", lambda settings: titles or {})

    return install


def test_chain_barriers_sans_chaine_est_vide(fake) -> None:
    fake(None)
    assert chain_barriers(Settings()) == {}


def test_chain_barriers_associe_chaque_barriere_a_sa_station(fake) -> None:
    fake(_chain([_station(1, barriers=[("a", "A"), ("b", "B")]), _station(2), _station(3, barriers=[("c", "C")])]))
    assert chain_barriers() == {"a": 1, "b": 1, "c": 3}


def test_chain_barriers_du_contenu_reel() -> None:
    mapping = chain_barriers(Settings())
    assert mapping["secret-scan"] == 1 and mapping["protection"] == 2


def test_sans_chaine_pas_d_encart(fake) -> None:
    fake(None)
    assert blockers_body(_scenario(_blocker()), Settings()) is None


def test_sans_declaration_pas_d_encart_meme_avec_chaine(fake) -> None:
    fake(_chain([_station(1)]))
    assert blockers_body(_scenario(), Settings()) is None


def test_station_livree_avec_titre_donne_lien_et_libelle(fake) -> None:
    fake(_chain([_station(1, name="Poste", delivered=True, barriers=[("b", "Libellé B")])]), {"s": "Titre S"})
    body = blockers_body(_scenario(_blocker(reason_text="Phrase.")), Settings())
    assert body == {
        "title_text": "Ce qui l'aurait bloqué",
        "items": [
            {
                "barrier_id": "b",
                "label": "Libellé B",
                "station": 1,
                "station_text": "Station 1 · Poste",
                "reason_text": "Phrase.",
                "delivered": True,
                "soon_text": None,
                "scenario": {"id": "s", "title_text": "Titre S"},
            }
        ],
    }


def test_station_livree_sans_titre_avertit_et_n_a_ni_lien_ni_etiquette(fake, caplog) -> None:
    fake(_chain([_station(1, delivered=True)]), {})
    with caplog.at_level(logging.WARNING, logger=bm.__name__):
        (item,) = blockers_body(_scenario(_blocker()), Settings())["items"]
    assert item["scenario"] is None and item["soon_text"] is None and item["delivered"] is True
    assert "x.B" in caplog.text and "« s »" in caplog.text


def test_station_non_livree_sans_titre_n_avertit_pas(fake, caplog) -> None:
    fake(_chain([_station(1, delivered=False, milestone="v0.9")]), {})
    with caplog.at_level(logging.WARNING, logger=bm.__name__):
        blockers_body(_scenario(_blocker()), Settings())
    assert caplog.text == ""


def test_titre_vide_vaut_absence_de_lien(fake) -> None:
    fake(_chain([_station(1, delivered=True)]), {"s": ""})
    (item,) = blockers_body(_scenario(_blocker()), Settings())["items"]
    assert item["scenario"] is None


def test_non_livree_avec_titre_n_a_pas_de_lien(fake) -> None:
    fake(_chain([_station(1, milestone="v0.2")]), {"s": "Titre"})
    (item,) = blockers_body(_scenario(_blocker()), Settings())["items"]
    assert item["scenario"] is None and item["soon_text"] == "Arrive en v0.2"


def test_non_livree_sans_jalon_utilise_le_texte_de_la_carte(fake) -> None:
    fake(_chain([_station(1)], SimpleNamespace(soon_text="Bientôt chez nous")))
    (item,) = blockers_body(_scenario(_blocker()), Settings())["items"]
    assert item["soon_text"] == "Bientôt chez nous"


def test_non_livree_sans_jalon_ni_carte_porte_bientot(fake) -> None:
    fake(_chain([_station(1)], None))
    (item,) = blockers_body(_scenario(_blocker()), Settings())["items"]
    assert item["soon_text"] == "Bientôt"


def test_station_inconnue_de_la_chaine(fake) -> None:
    fake(_chain([_station(2, delivered=True)]), {"s": "T"})
    (item,) = blockers_body(_scenario(_blocker(station=1)), Settings())["items"]
    assert item["delivered"] is False
    assert item["station_text"] == "Station 1 · "
    assert item["scenario"] is None
    assert item["soon_text"] == "Bientôt"


def test_libelle_par_defaut_est_l_identifiant(fake) -> None:
    fake(_chain([_station(1, delivered=True)]), {"s": "T"})
    (item,) = blockers_body(_scenario(_blocker(barrier_id="orpheline")), Settings())["items"]
    assert item["label"] == "orpheline"


@given(
    st.lists(KEBAB, min_size=1, max_size=6, unique=True),
    st.lists(st.booleans(), min_size=4, max_size=4),
)
@hsettings(max_examples=50)
def test_un_item_par_declaration_dans_l_ordre(ids: list[str], delivered: list[bool]) -> None:
    mp = pytest.MonkeyPatch()
    try:
        chain = _chain([_station(n + 1, delivered=delivered[n], milestone="v1") for n in range(4)])
        mp.setattr(bm, "load_chain_texts", lambda settings=None: chain)
        mp.setattr(bm, "catalogue_scenario_titles", lambda settings: {"s": "T"})
        blockers = [_blocker(barrier_id=i, station=(n % 4) + 1) for n, i in enumerate(ids)]
        items = blockers_body(_scenario(*blockers), Settings())["items"]
    finally:
        mp.undo()
    assert [i["barrier_id"] for i in items] == ids
    for n, item in enumerate(items):
        live = delivered[n % 4]
        assert item["delivered"] is live
        # invariant : un lien XOR une étiquette pour une barrière dont le titre existe
        assert (item["scenario"] is not None) is live
        assert (item["soon_text"] is None) is live
        assert item["soon_text"] in (None, "Arrive en v1")


# --------------------------------------------------------------------- titres du catalogue
def _write(folder, name: str, scenario_id: str, mode: str, title: str, extra: str = "") -> None:
    (folder / name).write_text(
        f"schema_version: 1\nscenario_id: {scenario_id}\nmode: {mode}\n"
        f"title_text: {title}\ntracks: [llm]\n{extra}",
        encoding="utf-8",
    )


@pytest.fixture
def content(tmp_path):
    folder = tmp_path / "scenarios"
    folder.mkdir()
    return Settings(content_dir=tmp_path), folder


def test_titres_mode_a_prime_sur_mode_b_quel_que_soit_l_ordre(content) -> None:
    st_, folder = content
    _write(folder, "a-sc.A.yaml", "a-sc", "A", "Titre A")
    _write(folder, "a-sc.B.yaml", "a-sc", "B", "Titre B")
    assert catalogue_scenario_titles(st_) == {"a-sc": "Titre A"}


def test_titre_mode_b_seul_est_retenu(content) -> None:
    st_, folder = content
    _write(folder, "b-sc.B.yaml", "b-sc", "B", "Titre B")
    assert catalogue_scenario_titles(st_) == {"b-sc": "Titre B"}


def test_scenario_hors_catalogue_exclu(content) -> None:
    st_, folder = content
    _write(folder, "int.A.yaml", "int", "A", "Interne", "catalogue: false\n")
    assert catalogue_scenario_titles(st_) == {}


def test_scenario_invalide_ignore_avec_avertissement(content, caplog) -> None:
    st_, folder = content
    (folder / "casse.A.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    _write(folder, "ok.A.yaml", "ok", "A", "Bon")
    with caplog.at_level(logging.WARNING, logger=bm.__name__):
        titles = catalogue_scenario_titles(st_)
    assert titles == {"ok": "Bon"}
    assert "casse.A.yaml" in caplog.text


def test_fichier_non_utf8_ignore(content) -> None:
    st_, folder = content
    (folder / "bin.A.yaml").write_bytes(b"\xff\xfe\x00\xd8 titre")
    assert catalogue_scenario_titles(st_) == {}


def test_dossier_absent_donne_des_titres_vides(tmp_path) -> None:
    assert catalogue_scenario_titles(Settings(content_dir=tmp_path)) == {}


def test_titres_du_contenu_reel() -> None:
    titles = catalogue_scenario_titles(Settings())
    assert titles["push-direct-main"] == "Voir la protection de main refuser un push direct"
    assert "secret-dans-un-commit" in titles
