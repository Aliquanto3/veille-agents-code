"""Renfort de la story 5.9 : bornes du schéma, lint, projection serveur et branches d'erreur."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from wavedevsecops.config import Settings
from wavedevsecops.scenarios import ScenarioError, load_scenario, parse_scenario
from wavedevsecops.web import blockers as bm
from wavedevsecops.web.blockers import blockers_body, catalogue_scenario_titles, chain_barriers
from wavedevsecops.web.catalogue import load_chain_texts

BASE = """
schema_version: 1
scenario_id: essai
mode: B
title_text: Essai
tracks: [llm]
"""


def _decl(barrier="secret-scan", station=1, scenario="secret-dans-un-commit", reason="Parce que."):
    return (
        "blocked_by:\n"
        f"  - barrier_id: {barrier}\n    station: {station}\n"
        f'    scenario_id: {scenario}\n    reason_text: "{reason}"\n'
    )


def _parse(extra: str, **kw: Any):
    return parse_scenario(BASE + extra, "essai.B.yaml", **kw)


def _scenario(key: str):
    s = Settings()
    return load_scenario(s.scenarios_path() / f"{key}.yaml", s).scenario


def _patch_chain(monkeypatch, **changes):
    chain = load_chain_texts(Settings())
    patched = chain.model_copy(update=changes)
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: patched)
    return chain


def _station1_undelivered(milestone: str = ""):
    chain = load_chain_texts(Settings())
    station = next(s for s in chain.stations if s.number == 1).model_copy(
        update={"delivered": False, "milestone": milestone}
    )
    return chain, [station if s.number == 1 else s for s in chain.stations]


# ------------------------------------------------------------------------------------- schéma
@pytest.mark.parametrize("station", [1, 4])
def test_station_aux_bornes_acceptee(station: int) -> None:
    (b,) = _parse(_decl(station=station)).blocked_by
    assert b.station == station


@pytest.mark.parametrize("station", [0, 5, -1])
def test_station_hors_bornes_refusee(station: int) -> None:
    with pytest.raises(ScenarioError):
        _parse(_decl(station=station))


@pytest.mark.parametrize("field", ["barrier", "scenario"])
def test_identifiants_non_kebab_refuses(field: str) -> None:
    with pytest.raises(ScenarioError):
        _parse(_decl(**{field: "Pas_Kebab"}))


def test_phrase_vide_refusee_et_phrase_d_un_caractere_acceptee() -> None:
    with pytest.raises(ScenarioError):
        _parse(_decl(reason=""))
    assert _parse(_decl(reason="x")).blocked_by[0].reason_text == "x"


def test_blocker_est_fige() -> None:
    (b,) = _parse(_decl()).blocked_by
    with pytest.raises(Exception):
        b.station = 2  # type: ignore[misc]


# --------------------------------------------------------------------------------------- lint
def test_sans_parametres_aucune_verification() -> None:
    sc = _parse(_decl(barrier="inventee", station=3, scenario="fantome"))
    assert sc.blocked_by[0].barrier_id == "inventee"


def test_barriers_seul_ne_verifie_pas_le_catalogue() -> None:
    assert _parse(_decl(scenario="fantome"), barriers={"secret-scan": 1})


def test_scenario_ids_seul_ne_verifie_pas_la_chaine() -> None:
    assert _parse(_decl(barrier="inventee"), scenario_ids={"secret-dans-un-commit"})


def test_message_exact_station() -> None:
    with pytest.raises(ScenarioError) as e:
        _parse(_decl(station=3), barriers={"secret-scan": 1})
    assert "la barrière « secret-scan » est en station 1, non 3" in str(e.value)


def test_message_barriere_inconnue_et_scenario_inconnu() -> None:
    with pytest.raises(ScenarioError) as e:
        _parse(_decl(barrier="zzz", scenario="fantome"), barriers={}, scenario_ids=set())
    text = str(e.value)
    assert "barrière inconnue de la chaîne : « zzz »" in text
    assert "scénario inconnu" in text and "fantome" in text


def test_doublon_signale_sans_verification_externe() -> None:
    extra = _decl() + (
        "  - barrier_id: secret-scan\n    station: 1\n    scenario_id: x-y\n    reason_text: Z\n"
    )
    with pytest.raises(ScenarioError) as e:
        _parse(extra)
    assert "barrière « secret-scan » en double" in str(e.value)


def test_deux_barrieres_distinctes_acceptees() -> None:
    extra = _decl() + (
        "  - barrier_id: protection\n    station: 2\n    scenario_id: push-direct-main\n"
        "    reason_text: Z\n"
    )
    sc = _parse(
        extra,
        barriers={"secret-scan": 1, "protection": 2},
        scenario_ids={"secret-dans-un-commit", "push-direct-main"},
    )
    assert [b.barrier_id for b in sc.blocked_by] == ["secret-scan", "protection"]


# ----------------------------------------------------------------------------- chain_barriers
def test_chain_barriers_contenu_reel() -> None:
    got = chain_barriers(Settings())
    assert got["secret-scan"] == 1 and got["protection"] == 2
    assert set(got.values()) <= {1, 2, 3, 4}


def test_chain_barriers_sans_chaine(monkeypatch) -> None:
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: None)
    assert chain_barriers(Settings()) == {}


# ------------------------------------------------------------------ catalogue_scenario_titles
def test_titres_du_catalogue_reel() -> None:
    titles = catalogue_scenario_titles(Settings())
    assert titles["push-direct-main"] == "Voir la protection de main refuser un push direct"
    assert "secret-dans-un-commit" in titles


def _fake_scenarios(monkeypatch, entries):
    paths = [Path(name) for name, _ in entries]
    by_name = dict(entries)
    monkeypatch.setattr(bm, "scenario_files", lambda settings: paths)

    def fake_load(path, settings):
        v = by_name[path.name]
        if isinstance(v, Exception):
            raise v
        return SimpleNamespace(scenario=v)

    monkeypatch.setattr(bm, "load_scenario", fake_load)


def _sc(sid, mode, title, catalogue=True):
    return SimpleNamespace(scenario_id=sid, mode=mode, title_text=title, catalogue=catalogue)


def test_titre_mode_a_prioritaire_quel_que_soit_l_ordre(monkeypatch) -> None:
    a, b = _sc("s", "A", "titre A"), _sc("s", "B", "titre B")
    _fake_scenarios(monkeypatch, [("b.yaml", b), ("a.yaml", a)])
    assert catalogue_scenario_titles(Settings()) == {"s": "titre A"}
    _fake_scenarios(monkeypatch, [("a.yaml", a), ("b.yaml", b)])
    assert catalogue_scenario_titles(Settings()) == {"s": "titre A"}


def test_titre_b_garde_si_pas_de_a_et_premier_b_conserve(monkeypatch) -> None:
    _fake_scenarios(
        monkeypatch, [("1.yaml", _sc("s", "B", "premier")), ("2.yaml", _sc("s", "B", "second"))]
    )
    assert catalogue_scenario_titles(Settings()) == {"s": "premier"}


def test_hors_catalogue_exclu(monkeypatch) -> None:
    _fake_scenarios(monkeypatch, [("1.yaml", _sc("s", "A", "t", catalogue=False))])
    assert catalogue_scenario_titles(Settings()) == {}


@pytest.mark.parametrize(
    "error",
    [OSError("io"), UnicodeDecodeError("utf-8", b"", 0, 1, "bad")],
)
def test_scenario_illisible_ignore_et_journalise(monkeypatch, caplog, error) -> None:
    _fake_scenarios(monkeypatch, [("casse.yaml", error), ("ok.yaml", _sc("ok", "A", "T"))])
    with caplog.at_level(logging.WARNING, logger=bm.log.name):
        assert catalogue_scenario_titles(Settings()) == {"ok": "T"}
    assert any("casse.yaml" in r.getMessage() for r in caplog.records)


# ----------------------------------------------------------------------------- blockers_body
def test_corps_exact_station_livree() -> None:
    body = blockers_body(_scenario("add-commit.B"), Settings())
    assert body is not None and set(body) == {"title_text", "items"}
    (item,) = body["items"]
    assert set(item) == {
        "barrier_id",
        "label",
        "station",
        "station_text",
        "reason_text",
        "delivered",
        "soon_text",
        "scenario",
    }
    assert item["station"] == 1 and item["station_text"] == "Station 1 · Poste local"
    assert item["scenario"]["id"] == "secret-dans-un-commit"
    assert item["reason_text"] == _scenario("add-commit.B").blocked_by[0].reason_text


def test_sans_chaine_lisible_aucun_encart(monkeypatch) -> None:
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: None)
    assert blockers_body(_scenario("add-commit.B"), Settings()) is None


def test_constantes_de_texte() -> None:
    assert bm.TITLE_TEXT == "Ce qui l'aurait bloqué"
    assert bm.SOON_TEXT.format(milestone="v9") == "Arrive en v9"
    assert bm.SOON_FALLBACK_TEXT == "Bientôt"


def test_non_livree_sans_jalon_utilise_le_texte_de_la_carte(monkeypatch) -> None:
    chain, stations = _station1_undelivered()
    new_map = chain.map.model_copy(update={"soon_text": "Patience"})
    _patch_chain(monkeypatch, stations=stations, map=new_map)
    (item,) = blockers_body(_scenario("add-commit.B"), Settings())["items"]
    assert item["soon_text"] == "Patience"


def test_non_livree_sans_jalon_ni_carte_porte_bientot(monkeypatch) -> None:
    _, stations = _station1_undelivered()
    _patch_chain(monkeypatch, stations=stations, map=None)
    (item,) = blockers_body(_scenario("add-commit.B"), Settings())["items"]
    assert item["soon_text"] == "Bientôt"


def test_jalon_prime_sur_le_texte_de_la_carte(monkeypatch) -> None:
    _, stations = _station1_undelivered("v7.1")
    _patch_chain(monkeypatch, stations=stations)
    (item,) = blockers_body(_scenario("add-commit.B"), Settings())["items"]
    assert item["soon_text"] == "Arrive en v7.1"


def test_station_absente_de_la_chaine_non_livree_et_nom_vide(monkeypatch) -> None:
    chain = load_chain_texts(Settings())
    _patch_chain(monkeypatch, stations=[s for s in chain.stations if s.number != 1])
    (item,) = blockers_body(_scenario("add-commit.B"), Settings())["items"]
    assert item["delivered"] is False and item["scenario"] is None
    assert item["station_text"] == "Station 1 · "
    assert item["soon_text"] == chain.map.soon_text


def test_barriere_hors_chaine_retombe_sur_son_identifiant(monkeypatch) -> None:
    chain = load_chain_texts(Settings())
    stations = [
        s.model_copy(update={"barriers": [b for b in s.barriers if b.id != "secret-scan"]})
        for s in chain.stations
    ]
    _patch_chain(monkeypatch, stations=stations)
    (item,) = blockers_body(_scenario("add-commit.B"), Settings())["items"]
    assert item["label"] == "secret-scan"


def test_livree_sans_titre_au_catalogue_avertit_sans_lien(monkeypatch, caplog) -> None:
    monkeypatch.setattr(bm, "catalogue_scenario_titles", lambda settings: {})
    with caplog.at_level(logging.WARNING, logger=bm.log.name):
        (item,) = blockers_body(_scenario("add-commit.B"), Settings())["items"]
    assert item["delivered"] is True and item["scenario"] is None and item["soon_text"] is None
    assert any(
        "add-commit.B" in r.getMessage() and "secret-dans-un-commit" in r.getMessage()
        for r in caplog.records
    )


def test_titre_vide_donne_pas_de_lien(monkeypatch) -> None:
    monkeypatch.setattr(bm, "catalogue_scenario_titles", lambda settings: {"secret-dans-un-commit": ""})
    (item,) = blockers_body(_scenario("add-commit.B"), Settings())["items"]
    assert item["scenario"] is None


def test_non_livree_sans_titre_n_avertit_pas(monkeypatch, caplog) -> None:
    _, stations = _station1_undelivered("v2")
    _patch_chain(monkeypatch, stations=stations)
    monkeypatch.setattr(bm, "catalogue_scenario_titles", lambda settings: {})
    with caplog.at_level(logging.WARNING, logger=bm.log.name):
        blockers_body(_scenario("add-commit.B"), Settings())
    assert not caplog.records
