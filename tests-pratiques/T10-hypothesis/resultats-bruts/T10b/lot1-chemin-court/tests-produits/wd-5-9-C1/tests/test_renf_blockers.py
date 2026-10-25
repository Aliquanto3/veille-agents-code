"""Renfort de la story 5.9 : tolérance du catalogue, priorité des modes, réglages, textes de repli."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

from wavedevsecops.config import Settings
from wavedevsecops.scenarios import ScenarioError, parse_scenario
from wavedevsecops.scenarios.model import Blocker
from wavedevsecops.web import blockers as bm
from wavedevsecops.web.catalogue import load_chain_texts

BASE = "schema_version: 1\nscenario_id: essai\nmode: B\ntitle_text: Essai\ntracks: [llm]\n"


def _scn(sid: str, mode: str, title: str, catalogue: bool = True) -> Any:
    return SimpleNamespace(
        scenario=SimpleNamespace(scenario_id=sid, mode=mode, title_text=title, catalogue=catalogue)
    )


def _patch_catalogue(monkeypatch: pytest.MonkeyPatch, entries: list[Any]) -> None:
    paths = [Path(f"f{i}.yaml") for i in range(len(entries))]
    by_path = dict(zip(paths, entries, strict=True))
    monkeypatch.setattr(bm, "scenario_files", lambda settings: paths)

    def load(path: Path, settings: Any) -> Any:
        entry = by_path[path]
        if isinstance(entry, Exception):
            raise entry
        return entry

    monkeypatch.setattr(bm, "load_scenario", load)


# ----------------------------------------------------------------- catalogue_scenario_titles
@pytest.mark.parametrize("error", [ScenarioError("x.yaml", []), OSError("nope")])
def test_fichier_invalide_ignore_et_suivants_lus(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    _patch_catalogue(monkeypatch, [error, _scn("un", "A", "Un"), _scn("deux", "A", "Deux")])
    assert bm.catalogue_scenario_titles(Settings()) == {"un": "Un", "deux": "Deux"}


def test_un_scenario_b_seul_figure_au_catalogue(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_catalogue(monkeypatch, [_scn("seul", "B", "Seul B")])
    assert bm.catalogue_scenario_titles(Settings()) == {"seul": "Seul B"}


def test_mode_a_prime_sur_b_dans_les_deux_ordres(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_catalogue(monkeypatch, [_scn("x", "B", "Titre B"), _scn("x", "A", "Titre A")])
    assert bm.catalogue_scenario_titles(Settings()) == {"x": "Titre A"}
    _patch_catalogue(monkeypatch, [_scn("x", "A", "Titre A"), _scn("x", "B", "Titre B")])
    assert bm.catalogue_scenario_titles(Settings()) == {"x": "Titre A"}


def test_scenario_interne_exclu(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_catalogue(monkeypatch, [_scn("interne", "A", "I", catalogue=False)])
    assert bm.catalogue_scenario_titles(Settings()) == {}


# ---------------------------------------------------------------------------- blockers_body
def _blocked(
    station: int = 1, barrier: str = "secret-scan", scenario: str = "secret-dans-un-commit"
) -> Any:
    extra = (
        f"blocked_by:\n  - barrier_id: {barrier}\n    station: {station}\n"
        f"    scenario_id: {scenario}\n    reason_text: Parce que.\n"
    )
    return parse_scenario(BASE + extra, "essai.B.yaml")


def _absent_warnings(caplog: pytest.LogCaptureFixture) -> list[Any]:
    return [r for r in caplog.records if "absent du catalogue" in r.getMessage()]


def test_reglages_par_defaut_et_explicites(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = load_chain_texts(Settings())
    seen: list[Any] = []
    sentinel_default, sentinel_given = object(), object()

    def fake_chain(settings: Any = None) -> Any:
        seen.append(settings)
        return chain

    monkeypatch.setattr(bm, "load_chain_texts", fake_chain)
    monkeypatch.setattr(bm, "catalogue_scenario_titles", lambda settings: {})
    monkeypatch.setattr(bm, "get_settings", lambda: sentinel_default)
    bm.blockers_body(_blocked())
    bm.blockers_body(_blocked(), sentinel_given)  # type: ignore[arg-type]
    assert seen == [sentinel_default, sentinel_given]


def test_avertissement_livree_et_titre_absent(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(bm, "catalogue_scenario_titles", lambda settings: {})
    with caplog.at_level(logging.WARNING, logger=bm.log.name):
        body = bm.blockers_body(_blocked(1), Settings())  # station 1 livrée
    assert body["items"][0]["scenario"] is None
    assert len(_absent_warnings(caplog)) == 1


def test_pas_d_avertissement_si_non_livree(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    chain = load_chain_texts(Settings())
    stations = [
        s.model_copy(update={"delivered": False}) if s.number == 1 else s for s in chain.stations
    ]
    patched = chain.model_copy(update={"stations": stations})
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: patched)
    monkeypatch.setattr(bm, "catalogue_scenario_titles", lambda settings: {})
    with caplog.at_level(logging.WARNING, logger=bm.log.name):
        bm.blockers_body(_blocked(1), Settings())
    assert not _absent_warnings(caplog)


def test_pas_d_avertissement_si_livree_et_titre_present(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(
        bm, "catalogue_scenario_titles", lambda settings: {"secret-dans-un-commit": "T"}
    )
    with caplog.at_level(logging.WARNING, logger=bm.log.name):
        body = bm.blockers_body(_blocked(1), Settings())
    assert not _absent_warnings(caplog)
    assert body["items"][0]["scenario"] == {"id": "secret-dans-un-commit", "title_text": "T"}


def _unshipped_chain(soon: str | None) -> Any:
    chain = load_chain_texts(Settings())
    stations = [
        s.model_copy(update={"delivered": False, "milestone": ""}) if s.number == 2 else s
        for s in chain.stations
    ]
    update: dict[str, Any] = {"stations": stations}
    if soon is None:
        update["map"] = None
    else:
        assert chain.map is not None
        update["map"] = chain.map.model_copy(update={"soon_text": soon})
    return chain.model_copy(update=update)


def test_sans_jalon_texte_de_la_carte(monkeypatch: pytest.MonkeyPatch) -> None:
    patched = _unshipped_chain("Prochainement")
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: patched)
    body = bm.blockers_body(_blocked(2, "protection", "push-direct-main"), Settings())
    assert body["items"][0]["soon_text"] == "Prochainement"


def test_sans_jalon_ni_carte_repli_bientot(monkeypatch: pytest.MonkeyPatch) -> None:
    patched = _unshipped_chain(None)
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: patched)
    body = bm.blockers_body(_blocked(2, "protection", "push-direct-main"), Settings())
    assert body["items"][0]["soon_text"] == "Bientôt"


# ------------------------------------------------------------------------------ Blocker
def _blk(**changes: Any) -> Blocker:
    data = {"barrier_id": "secret-scan", "station": 1, "scenario_id": "x", "reason_text": "r"}
    return Blocker(**{**data, **changes})


def test_blocker_est_fige() -> None:
    blocker = _blk()
    with pytest.raises(ValidationError):
        blocker.station = 2  # type: ignore[misc]


def test_blocker_bornes_de_station() -> None:
    assert _blk(station=1).station == 1
    assert _blk(station=4).station == 4
    for bad in (0, 5):
        with pytest.raises(ValidationError):
            _blk(station=bad)


def test_blocker_phrase_non_vide() -> None:
    assert _blk(reason_text="a").reason_text == "a"
    with pytest.raises(ValidationError):
        _blk(reason_text="")


def test_lint_station_differente_dans_les_deux_sens() -> None:
    barriers = {"secret-scan": 2}
    assert _blocked(1).semantic_errors(barriers=barriers) == [
        (("blocked_by", 0, "station"), "la barrière « secret-scan » est en station 2, non 1")
    ]
    assert len(_blocked(3).semantic_errors(barriers=barriers)) == 1
    assert _blocked(2).semantic_errors(barriers=barriers) == []
