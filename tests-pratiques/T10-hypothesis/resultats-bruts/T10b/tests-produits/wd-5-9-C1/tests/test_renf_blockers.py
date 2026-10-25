"""Renfort story 5.9 : branches d'erreur du catalogue, réglages, repli « Bientôt », schéma et lint."""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from wavedevsecops.config import Settings
from wavedevsecops.scenarios import ScenarioError, parse_scenario
from wavedevsecops.scenarios.model import Blocker
from wavedevsecops.web import blockers as bm
from wavedevsecops.web.blockers import blockers_body, catalogue_scenario_titles
from wavedevsecops.web.catalogue import load_chain_texts


def _fake(sid: str, mode: str, title: str, catalogue: bool = True):
    return SimpleNamespace(
        scenario=SimpleNamespace(scenario_id=sid, mode=mode, title_text=title, catalogue=catalogue)
    )


def _titles(monkeypatch: pytest.MonkeyPatch, entries: list) -> dict[str, str]:
    """`entries` : objets chargés, ou exception levée au chargement de ce fichier."""
    paths = [SimpleNamespace(name=f"f{i}.yaml", index=i) for i in range(len(entries))]
    monkeypatch.setattr(bm, "scenario_files", lambda settings: paths)

    def load(path, settings):
        entry = entries[path.index]
        if isinstance(entry, Exception):
            raise entry
        return entry

    monkeypatch.setattr(bm, "load_scenario", load)
    return catalogue_scenario_titles(Settings())


@pytest.mark.parametrize(
    "error",
    [ScenarioError("x", []),OSError("x"), UnicodeDecodeError("utf-8", b"", 0, 1, "x")],
)
def test_fichier_illisible_ignore_et_suite_chargee(monkeypatch, caplog, error) -> None:
    entries = [error, _fake("a", "A", "Titre A"), _fake("b", "A", "Titre B")]
    with caplog.at_level(logging.WARNING):
        titles = _titles(monkeypatch, entries)
    assert titles == {"a": "Titre A", "b": "Titre B"}
    assert "f0.yaml" in caplog.text


def test_mode_b_seul_est_liste(monkeypatch) -> None:
    assert _titles(monkeypatch, [_fake("x", "B", "Titre B")]) == {"x": "Titre B"}


def test_mode_a_l_emporte_quel_que_soit_l_ordre(monkeypatch) -> None:
    assert _titles(monkeypatch, [_fake("x", "B", "B"), _fake("x", "A", "A")]) == {"x": "A"}
    assert _titles(monkeypatch, [_fake("x", "A", "A"), _fake("x", "B", "B")]) == {"x": "A"}


def test_scenario_hors_catalogue_ignore(monkeypatch) -> None:
    assert _titles(monkeypatch, [_fake("x", "A", "A", catalogue=False)]) == {}


def test_reglages_explicites_utilises_sinon_ceux_du_processus(monkeypatch) -> None:
    seen: list = []
    default, explicit = object(), object()
    monkeypatch.setattr(bm, "get_settings", lambda: default)
    monkeypatch.setattr(bm, "load_chain_texts", lambda s=None: seen.append(s))
    scenario = SimpleNamespace(blocked_by=[object()])
    assert blockers_body(scenario, explicit) is None
    assert blockers_body(scenario) is None
    assert seen == [explicit, default]


def _blocker_scenario():
    return SimpleNamespace(
        key="essai.B",
        blocked_by=[
            Blocker(barrier_id="secret-scan", station=1, scenario_id="absent", reason_text="r")
        ],
    )


def _patch_station_one(monkeypatch, **changes):
    chain = load_chain_texts(Settings())
    stations = [s.model_copy(update=changes) if s.number == 1 else s for s in chain.stations]
    patched = chain.model_copy(update={"stations": stations})
    monkeypatch.setattr(bm, "load_chain_texts", lambda s=None: patched)


def test_avertissement_seulement_si_livree_et_sans_titre(monkeypatch, caplog) -> None:
    _patch_station_one(monkeypatch, delivered=True)
    monkeypatch.setattr(bm, "catalogue_scenario_titles", lambda s: {})
    with caplog.at_level(logging.WARNING):
        (item,) = blockers_body(_blocker_scenario(), Settings())["items"]
    assert "essai.B" in caplog.text and "absent" in caplog.text
    assert item["delivered"] is True and item["scenario"] is None

    caplog.clear()
    monkeypatch.setattr(bm, "catalogue_scenario_titles", lambda s: {"absent": "T"})
    with caplog.at_level(logging.WARNING):
        (item,) = blockers_body(_blocker_scenario(), Settings())["items"]
    assert caplog.text == ""
    assert item["scenario"] == {"id": "absent", "title_text": "T"}

    _patch_station_one(monkeypatch, delivered=False)
    monkeypatch.setattr(bm, "catalogue_scenario_titles", lambda s: {})
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        blockers_body(_blocker_scenario(), Settings())
    assert caplog.text == ""


def _soon(monkeypatch, chain_map):
    chain = load_chain_texts(Settings())
    stations = [
        s.model_copy(update={"delivered": False, "milestone": ""}) if s.number == 1 else s
        for s in chain.stations
    ]
    patched = chain.model_copy(update={"stations": stations, "map": chain_map})
    monkeypatch.setattr(bm, "load_chain_texts", lambda s=None: patched)
    return blockers_body(_blocker_scenario(), Settings())["items"][0]["soon_text"]


def test_sans_jalon_texte_de_la_carte_sinon_bientot(monkeypatch) -> None:
    real = load_chain_texts(Settings()).map
    assert real is not None
    custom = real.model_copy(update={"soon_text": "Plus tard"})
    assert _soon(monkeypatch, custom) == "Plus tard"
    assert _soon(monkeypatch, None) == "Bientôt"


# ---------------------------------------------------------------------------------- schéma, lint
def _blocker(**changes):
    data = {"barrier_id": "secret-scan", "station": 1, "scenario_id": "x", "reason_text": "r"}
    return Blocker(**{**data, **changes})


def test_blocker_est_fige() -> None:
    blocker = _blocker()
    with pytest.raises(ValidationError):
        blocker.station = 2


def test_station_bornes() -> None:
    assert _blocker(station=4).station == 4
    assert _blocker(station=1).station == 1
    for bad in (0, 5):
        with pytest.raises(ValidationError):
            _blocker(station=bad)


def test_phrase_vide_refusee() -> None:
    with pytest.raises(ValidationError):
        _blocker(reason_text="")
    assert _blocker(reason_text="a").reason_text == "a"


def test_lint_station_declaree_inferieure_a_celle_de_la_chaine() -> None:
    text = (
        "schema_version: 1\nscenario_id: essai\nmode: B\ntitle_text: E\ntracks: [llm]\n"
        "blocked_by:\n  - barrier_id: protection\n    station: 1\n"
        "    scenario_id: x\n    reason_text: r\n"
    )
    with pytest.raises(ScenarioError) as error:
        parse_scenario(text, "essai.B.yaml", barriers={"protection": 2})
    assert "est en station 2, non 1" in str(error.value)
    ok = parse_scenario(text.replace("station: 1", "station: 2"), "essai.B.yaml", barriers={"protection": 2})
    assert ok.blocked_by[0].station == 2
