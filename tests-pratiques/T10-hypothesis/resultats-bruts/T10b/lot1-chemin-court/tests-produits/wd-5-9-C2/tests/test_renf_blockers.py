"""Renforcement de la story 5.9 : branches d'erreur, bornes et priorités de l'encart."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from wavedevsecops.config import Settings
from wavedevsecops.scenarios import ScenarioError, parse_scenario
from wavedevsecops.scenarios.model import Blocker
from wavedevsecops.web import blockers as bm
from wavedevsecops.web.catalogue import load_chain_texts

BASE = "schema_version: 1\nscenario_id: {sid}\nmode: {mode}\ntitle_text: {title}\ntracks: [llm]\n"


def _scenario(sid: str, mode: str, title: str, extra: str = ""):
    return parse_scenario(BASE.format(sid=sid, mode=mode, title=title) + extra, f"{sid}.{mode}.yaml")


class _Loaded:
    def __init__(self, scenario) -> None:
        self.scenario = scenario


def _fake_catalogue(monkeypatch: pytest.MonkeyPatch, entries: dict[str, Any]) -> None:
    """`entries` : nom de fichier -> scénario, ou exception à lever."""
    monkeypatch.setattr(bm, "scenario_files", lambda settings: [Path(n) for n in entries])

    def load(path, settings):
        value = entries[path.name]
        if isinstance(value, BaseException):
            raise value
        return _Loaded(value)

    monkeypatch.setattr(bm, "load_scenario", load)


# ------------------------------------------------------------- catalogue_scenario_titles (M1-M3)
def test_scenario_illisible_ignore_et_les_suivants_restent(monkeypatch, caplog) -> None:
    good = _scenario("beta", "A", "Titre bêta")
    _fake_catalogue(
        monkeypatch,
        {
            "a.yaml": ScenarioError("a.yaml", []),
            "b.yaml": OSError("disque"),
            "c.yaml": UnicodeDecodeError("utf-8", b"", 0, 1, "x"),
            "d.yaml": good,
        },
    )
    with caplog.at_level(logging.WARNING, logger=bm.log.name):
        assert bm.catalogue_scenario_titles(Settings()) == {"beta": "Titre bêta"}
    assert sum("Scénario ignoré" in r.message for r in caplog.records) == 3


def test_mode_b_seul_est_liste_et_le_mode_a_l_emporte(monkeypatch) -> None:
    _fake_catalogue(
        monkeypatch,
        {
            "1.yaml": _scenario("seul", "B", "B seul"),
            "2.yaml": _scenario("duo", "B", "Duo B"),
            "3.yaml": _scenario("duo", "A", "Duo A"),
            "4.yaml": _scenario("tard", "A", "Tard A"),
            "5.yaml": _scenario("tard", "B", "Tard B"),
        },
    )
    assert bm.catalogue_scenario_titles(Settings()) == {
        "seul": "B seul",
        "duo": "Duo A",
        "tard": "Tard A",
    }


def test_scenario_hors_catalogue_est_exclu(monkeypatch) -> None:
    _fake_catalogue(monkeypatch, {"1.yaml": _scenario("interne", "A", "Interne", "catalogue: false\n")})
    assert bm.catalogue_scenario_titles(Settings()) == {}


# ------------------------------------------------------------------------- blockers_body (M4-M6)
def _declared(station: int = 1, barrier: str = "secret-scan", sid: str = "secret-dans-un-commit"):
    extra = (
        f"blocked_by:\n  - barrier_id: {barrier}\n    station: {station}\n"
        f"    scenario_id: {sid}\n    reason_text: Parce que.\n"
    )
    return _scenario("essai", "B", "Essai", extra)


def test_blockers_body_utilise_les_reglages_fournis_ou_les_globaux(monkeypatch) -> None:
    seen: list[Any] = []
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: seen.append(settings))
    given, default = Settings(), Settings()
    monkeypatch.setattr(bm, "get_settings", lambda: default)
    assert bm.blockers_body(_declared(), given) is None
    assert bm.blockers_body(_declared()) is None
    assert seen[0] is given and seen[1] is default


def test_station_livree_sans_titre_au_catalogue_journalise(monkeypatch, caplog) -> None:
    monkeypatch.setattr(bm, "catalogue_scenario_titles", lambda settings: {})
    with caplog.at_level(logging.WARNING, logger=bm.log.name):
        body = bm.blockers_body(_declared(), Settings())
    (item,) = body["items"]
    assert item["delivered"] is True and item["scenario"] is None
    assert any("absent du catalogue" in r.message for r in caplog.records)


def test_pas_d_avertissement_si_titre_present_ou_station_non_livree(monkeypatch, caplog) -> None:
    chain = load_chain_texts(Settings())
    stations = [
        s.model_copy(update={"delivered": False}) if s.number == 1 else s for s in chain.stations
    ]
    patched = chain.model_copy(update={"stations": stations})
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: patched)
    monkeypatch.setattr(bm, "catalogue_scenario_titles", lambda settings: {})
    with caplog.at_level(logging.WARNING, logger=bm.log.name):
        bm.blockers_body(_declared(), Settings())  # non livrée, sans titre : pas d'alerte
    assert not caplog.records
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: chain)
    monkeypatch.setattr(
        bm, "catalogue_scenario_titles", lambda settings: {"secret-dans-un-commit": "T"}
    )
    with caplog.at_level(logging.WARNING, logger=bm.log.name):
        bm.blockers_body(_declared(), Settings())  # livrée, titre présent : pas d'alerte
    assert not caplog.records


def test_sans_jalon_le_texte_vient_de_la_carte_puis_du_repli(monkeypatch) -> None:
    chain = load_chain_texts(Settings())
    assert chain.map is not None
    stations = [
        s.model_copy(update={"delivered": False, "milestone": ""}) if s.number == 1 else s
        for s in chain.stations
    ]
    with_map = chain.model_copy(
        update={
            "stations": stations,
            "map": chain.map.model_copy(update={"soon_text": "Plus tard"}),
        }
    )
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: with_map)
    (item,) = bm.blockers_body(_declared(), Settings())["items"]
    assert item["soon_text"] == "Plus tard"
    without_map = with_map.model_copy(update={"map": None})
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: without_map)
    (item,) = bm.blockers_body(_declared(), Settings())["items"]
    assert item["soon_text"] == bm.SOON_FALLBACK_TEXT


# ---------------------------------------------------------------------------------- modèle (M7-M10)
def _blocker(**changes: Any) -> Blocker:
    data = {"barrier_id": "secret-scan", "station": 1, "scenario_id": "x", "reason_text": "r"}
    return Blocker(**{**data, **changes})


def test_blocker_est_immuable() -> None:
    blocker = _blocker()
    with pytest.raises(ValidationError):
        blocker.station = 2  # type: ignore[misc]


def test_blocker_station_bornes() -> None:
    assert _blocker(station=4).station == 4
    assert _blocker(station=1).station == 1
    for bad in (0, 5):
        with pytest.raises(ValidationError):
            _blocker(station=bad)


def test_blocker_phrase_vide_refusee() -> None:
    assert _blocker(reason_text="a").reason_text == "a"
    with pytest.raises(ValidationError):
        _blocker(reason_text="")


def test_lint_station_declaree_inferieure_a_celle_de_la_chaine() -> None:
    scenario = _declared(station=1, barrier="protection")
    errors = scenario.semantic_errors(barriers={"protection": 2})
    assert errors == [
        (("blocked_by", 0, "station"), "la barrière « protection » est en station 2, non 1")
    ]
    assert _declared(station=2, barrier="protection").semantic_errors(barriers={"protection": 2}) == []
