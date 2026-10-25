# ruff: noqa: E501
"""Renfort de la story 5.9 : titres du catalogue, projection de l'encart, schéma et lint de `Blocker`."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from wavedevsecops.config import Settings
from wavedevsecops.scenarios import load_scenario, parse_scenario
from wavedevsecops.scenarios.model import Blocker
from wavedevsecops.web import blockers as blockers_module
from wavedevsecops.web.blockers import blockers_body, catalogue_scenario_titles
from wavedevsecops.web.catalogue import load_chain_texts


def _yaml(scenario_id: str, mode: str, title: str, extra: str = "") -> str:
    return (
        f"schema_version: 1\nscenario_id: {scenario_id}\nmode: {mode}\n"
        f"title_text: {title}\ntracks: [llm]\n{extra}"
    )


def _write(folder: Path, name: str, text: str) -> None:
    (folder / f"{name}.yaml").write_text(text, encoding="utf-8")


@pytest.fixture
def content(tmp_path: Path) -> Settings:
    (tmp_path / "scenarios").mkdir()
    return Settings(content_dir=tmp_path)


def _blocker_kwargs(**changes: Any) -> dict[str, Any]:
    base = {
        "barrier_id": "secret-scan",
        "station": 1,
        "scenario_id": "secret-dans-un-commit",
        "reason_text": "Parce que.",
    }
    return base | changes


# ----------------------------------------------------------------- catalogue_scenario_titles
def test_titres_ignorent_un_fichier_invalide_et_continuent(content: Settings, caplog) -> None:
    folder = content.scenarios_path()
    _write(folder, "aaa.A", "schema_version: 1\nscenario_id: aaa\n")  # invalide, trié en premier
    _write(folder, "bbb.A", _yaml("bbb", "A", "Titre B"))
    _write(folder, "ccc.A", _yaml("ccc", "A", "Titre C"))
    with caplog.at_level(logging.WARNING):
        titles = catalogue_scenario_titles(content)
    assert titles == {"bbb": "Titre B", "ccc": "Titre C"}
    assert "aaa.A.yaml" in caplog.text


def test_titres_ignorent_un_fichier_illisible_et_continuent(content: Settings) -> None:
    folder = content.scenarios_path()
    (folder / "aaa.A.yaml").write_bytes(b"\xff\xfe\x00 titre: \x80")
    _write(folder, "bbb.A", _yaml("bbb", "A", "Titre B"))
    assert catalogue_scenario_titles(content) == {"bbb": "Titre B"}


def test_titres_un_scenario_b_seul_est_retenu(content: Settings) -> None:
    _write(content.scenarios_path(), "seul.B", _yaml("seul", "B", "Seul en B"))
    assert catalogue_scenario_titles(content) == {"seul": "Seul en B"}


def test_titres_le_mode_a_prime_sur_le_b(content: Settings) -> None:
    folder = content.scenarios_path()
    _write(folder, "dup.A", _yaml("dup", "A", "Titre A"))
    _write(folder, "dup.B", _yaml("dup", "B", "Titre B"))
    assert catalogue_scenario_titles(content) == {"dup": "Titre A"}


def test_titres_ecartent_les_scenarios_hors_catalogue(content: Settings) -> None:
    folder = content.scenarios_path()
    _write(folder, "interne.A", _yaml("interne", "A", "Interne", "catalogue: false\n"))
    _write(folder, "visible.A", _yaml("visible", "A", "Visible"))
    assert catalogue_scenario_titles(content) == {"visible": "Visible"}


# ---------------------------------------------------------------------------- blockers_body
def _scenario(key: str):
    settings = Settings()
    return load_scenario(settings.scenarios_path() / f"{key}.yaml", settings).scenario


def _patch_chain(monkeypatch: pytest.MonkeyPatch, station: int, **changes: Any) -> None:
    chain = load_chain_texts(Settings())
    assert chain is not None
    stations = [s.model_copy(update=changes) if s.number == station else s for s in chain.stations]
    patched = chain.model_copy(update={"stations": stations})
    monkeypatch.setattr(blockers_module, "load_chain_texts", lambda settings=None: patched)


def test_reglages_par_defaut_viennent_de_get_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = Settings()
    seen: list[Any] = []
    chain = load_chain_texts(sentinel)

    def fake_chain(settings=None):
        seen.append(settings)
        return chain

    monkeypatch.setattr(blockers_module, "get_settings", lambda: sentinel)
    monkeypatch.setattr(blockers_module, "load_chain_texts", fake_chain)
    assert blockers_body(_scenario("add-commit.B")) is not None
    assert seen == [sentinel]


def _absent_warnings(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records if "absent du catalogue" in r.getMessage()]


def test_avertissement_seulement_si_livree_et_scenario_absent(
    monkeypatch: pytest.MonkeyPatch, caplog
) -> None:
    monkeypatch.setattr(blockers_module, "catalogue_scenario_titles", lambda settings: {})
    scenario = _scenario("add-commit.B")
    with caplog.at_level(logging.WARNING):
        _patch_chain(monkeypatch, 1, delivered=True)
        body = blockers_body(scenario, Settings())
        warned = _absent_warnings(caplog)
        assert len(warned) == 1 and "secret-dans-un-commit" in warned[0]
        assert body["items"][0]["scenario"] is None  # livrée mais sans titre : pas de lien
        caplog.clear()
        _patch_chain(monkeypatch, 1, delivered=False, milestone="v0.2")
        blockers_body(scenario, Settings())
        assert _absent_warnings(caplog) == []


def test_pas_d_avertissement_si_livree_et_scenario_present(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        blockers_body(_scenario("add-commit.B"), Settings())
    assert _absent_warnings(caplog) == []


def _patch_unlabelled_chain(monkeypatch: pytest.MonkeyPatch, soon_text: str | None) -> None:
    chain = load_chain_texts(Settings())
    assert chain is not None and chain.map is not None
    stations = [
        s.model_copy(update={"delivered": False, "milestone": ""}) if s.number == 1 else s
        for s in chain.stations
    ]
    new_map = None if soon_text is None else chain.map.model_copy(update={"soon_text": soon_text})
    patched = chain.model_copy(update={"stations": stations, "map": new_map})
    monkeypatch.setattr(blockers_module, "load_chain_texts", lambda settings=None: patched)


def test_non_livree_sans_jalon_reprend_le_texte_de_la_carte(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_unlabelled_chain(monkeypatch, "Prochainement")
    (item,) = blockers_body(_scenario("add-commit.B"), Settings())["items"]
    assert item["soon_text"] == "Prochainement"


def test_non_livree_sans_jalon_ni_carte_porte_bientot(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_unlabelled_chain(monkeypatch, None)
    (item,) = blockers_body(_scenario("add-commit.B"), Settings())["items"]
    assert item["soon_text"] == "Bientôt"


# ------------------------------------------------------------------------------- Blocker
def test_blocker_est_immuable() -> None:
    blocker = Blocker(**_blocker_kwargs())
    with pytest.raises(ValidationError):
        blocker.station = 2  # type: ignore[misc]


@pytest.mark.parametrize("station", [1, 2, 3, 4])
def test_blocker_accepte_les_stations_1_a_4(station: int) -> None:
    assert Blocker(**_blocker_kwargs(station=station)).station == station


@pytest.mark.parametrize("station", [0, 5])
def test_blocker_refuse_les_stations_hors_bornes(station: int) -> None:
    with pytest.raises(ValidationError):
        Blocker(**_blocker_kwargs(station=station))


def test_blocker_refuse_une_phrase_vide() -> None:
    with pytest.raises(ValidationError):
        Blocker(**_blocker_kwargs(reason_text=""))
    assert Blocker(**_blocker_kwargs(reason_text="x")).reason_text == "x"


# ------------------------------------------------------------------------- lint des stations
def _lint(station: int) -> list[tuple[tuple, str]]:
    scenario = parse_scenario(
        _yaml(
            "essai",
            "B",
            "Essai",
            f"blocked_by:\n  - barrier_id: protection\n    station: {station}\n"
            "    scenario_id: push-direct-main\n    reason_text: Parce que.\n",
        ),
        "essai.B.yaml",
    )
    return scenario.semantic_errors(barriers={"secret-scan": 1, "protection": 2})


def test_lint_station_declaree_inferieure_a_celle_de_la_chaine() -> None:
    ((path, message),) = _lint(1)
    assert path == ("blocked_by", 0, "station")
    assert message == "la barrière « protection » est en station 2, non 1"


def test_lint_station_declaree_superieure_a_celle_de_la_chaine() -> None:
    ((path, message),) = _lint(3)
    assert path == ("blocked_by", 0, "station")
    assert message == "la barrière « protection » est en station 2, non 3"


def test_lint_station_egale_sans_ecart() -> None:
    assert _lint(2) == []
