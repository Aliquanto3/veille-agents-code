# ruff: noqa: E501
"""Renfort de la story 5.9 : bornes du schéma `Blocker`, lint de `blocked_by` (propriétés),
branches de `chain_barriers`, `catalogue_scenario_titles` et `blockers_body`."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from wavedevsecops.config import Settings
from wavedevsecops.scenarios import ScenarioError, parse_scenario
from wavedevsecops.scenarios.loader import FieldError
from wavedevsecops.web import blockers as bl
from wavedevsecops.web.catalogue import load_chain_texts

BASE = """
schema_version: 1
scenario_id: essai
mode: B
title_text: Essai
tracks: [llm]
"""

KEBAB = st.from_regex(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$", fullmatch=True).filter(
    lambda s: len(s) < 30 and s not in {"y", "n", "no", "yes", "on", "off", "true", "false", "null", "nan"}
)


def _decl(items: list[tuple[str, int, str]], reason: str = "Parce que.") -> str:
    if not items:
        return "blocked_by: []\n"
    out = "blocked_by:\n"
    for barrier, station, scenario in items:
        out += (
            f"  - barrier_id: {barrier}\n    station: {station}\n"
            f"    scenario_id: {scenario}\n    reason_text: {reason}\n"
        )
    return out


def _parse(items, **kwargs: Any):
    return parse_scenario(BASE + _decl(items), "essai.B.yaml", **kwargs)


def _real_scenario(key: str):
    from wavedevsecops.scenarios import load_scenario

    settings = Settings()
    return load_scenario(settings.scenarios_path() / f"{key}.yaml", settings).scenario


def _patch_chain(monkeypatch: pytest.MonkeyPatch, **changes: Any) -> Any:
    chain = load_chain_texts(Settings())
    assert chain is not None
    patched = chain.model_copy(update=changes)
    monkeypatch.setattr(bl, "load_chain_texts", lambda settings=None: patched)
    return patched


# ------------------------------------------------------------------------- schéma : bornes
@pytest.mark.parametrize("station", [1, 2, 3, 4])
def test_station_bornes_acceptees(station: int) -> None:
    assert _parse([("a-b", station, "c")]).blocked_by[0].station == station


@pytest.mark.parametrize("station", [0, 5, -1, 100])
def test_station_hors_bornes_refusee(station: int) -> None:
    with pytest.raises(ScenarioError):
        _parse([("a-b", station, "c")])


@pytest.mark.parametrize("bad", ["Majuscule", "avec_underscore", "-debut", "fin-", "a--b", "a b"])
def test_identifiants_non_kebab_refuses(bad: str) -> None:
    for items in ([(f'"{bad}"', 1, "c")], [("a", 1, f'"{bad}"')]):
        with pytest.raises(ScenarioError):
            _parse(items)


def test_phrase_vide_refusee_et_une_lettre_acceptee() -> None:
    with pytest.raises(ScenarioError):
        parse_scenario(BASE + _decl([("a", 1, "c")], reason='""'), "essai.B.yaml")
    ok = parse_scenario(BASE + _decl([("a", 1, "c")], reason="x"), "essai.B.yaml")
    assert ok.blocked_by[0].reason_text == "x"


def test_blocker_est_fige() -> None:
    blocker = _parse([("a", 1, "c")]).blocked_by[0]
    with pytest.raises(Exception):
        blocker.station = 2  # type: ignore[misc]


# ---------------------------------------------------------------------- lint : propriétés
@given(
    barrier=KEBAB,
    scenario=KEBAB,
    station=st.integers(1, 4),
    extra_barriers=st.dictionaries(KEBAB, st.integers(1, 4), max_size=4),
    extra_ids=st.sets(KEBAB, max_size=4),
)
def test_declaration_coherente_jamais_refusee(barrier, scenario, station, extra_barriers, extra_ids) -> None:
    barriers = {**extra_barriers, barrier: station}
    parsed = _parse([(barrier, station, scenario)], barriers=barriers, scenario_ids=extra_ids | {scenario})
    assert [(b.barrier_id, b.station, b.scenario_id) for b in parsed.blocked_by] == [
        (barrier, station, scenario)
    ]


@given(barrier=KEBAB, scenario=KEBAB, station=st.integers(1, 4), other=st.integers(1, 4))
def test_station_differente_toujours_refusee(barrier, scenario, station, other) -> None:
    if other == station:
        return
    with pytest.raises(ScenarioError) as error:
        _parse([(barrier, station, scenario)], barriers={barrier: other}, scenario_ids={scenario})
    assert f"est en station {other}, non {station}" in str(error.value)


@given(barrier=KEBAB, scenario=KEBAB, station=st.integers(1, 4))
def test_barriere_ou_scenario_inconnus_toujours_refuses(barrier, scenario, station) -> None:
    with pytest.raises(ScenarioError) as error:
        _parse([(barrier, station, scenario)], barriers={}, scenario_ids={scenario})
    assert f"barrière inconnue de la chaîne : « {barrier} »" in str(error.value)
    with pytest.raises(ScenarioError) as error:
        _parse([(barrier, station, scenario)], barriers={barrier: station}, scenario_ids=set())
    assert f"scénario inconnu du catalogue : « {scenario} »" in str(error.value)


@given(barrier=KEBAB, scenario=KEBAB, station=st.integers(1, 4))
def test_sans_parametres_aucune_verification(barrier, scenario, station) -> None:
    """Sans `barriers` ni `scenario_ids`, seul le doublon est contrôlé : pas de lint de chaîne."""
    assert _parse([(barrier, station, scenario)]).blocked_by


@given(barrier=KEBAB, scenario=KEBAB, station=st.integers(1, 4))
def test_doublon_refuse_meme_sans_parametres(barrier, scenario, station) -> None:
    with pytest.raises(ScenarioError) as error:
        _parse([(barrier, station, scenario), (barrier, station, scenario)])
    assert f"barrière « {barrier} » en double" in str(error.value)


def test_semantic_errors_chemins_exacts() -> None:
    scenario = _parse([("ok", 1, "s1"), ("ko", 2, "s2"), ("ok2", 1, "s3")])
    errors = scenario.semantic_errors(None, None, {"ok": 1, "ko": 3, "ok2": 1}, {"s1", "s3"})
    assert errors == [
        (("blocked_by", 1, "station"), "la barrière « ko » est en station 3, non 2"),
        (("blocked_by", 1, "scenario_id"), "scénario inconnu du catalogue : « s2 »"),
    ]


def test_semantic_errors_doublon_porte_l_index_du_second() -> None:
    base = _parse([("a", 1, "s"), ("b", 1, "s"), ("c", 1, "s")])
    blockers = [base.blocked_by[0], base.blocked_by[1], base.blocked_by[0]]
    scenario = base.model_copy(update={"blocked_by": blockers})
    assert scenario.semantic_errors() == [
        (("blocked_by", 2, "barrier_id"), "barrière « a » en double")
    ]


def test_barriere_inconnue_ne_signale_pas_aussi_la_station() -> None:
    scenario = _parse([("x", 1, "s")])
    errors = scenario.semantic_errors(None, None, {}, {"s"})
    assert [loc for loc, _ in errors] == [("blocked_by", 0, "barrier_id")]


def test_erreur_du_lint_nomme_le_champ(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ScenarioError) as error:
        _parse([("x", 1, "s")], barriers={}, scenario_ids={"s"})
    assert "blocked_by" in str(error.value) and "barrier_id" in str(error.value)
    assert FieldError  # le type d'écart du chargeur reste exporté


# ----------------------------------------------------------------------------- chain_barriers
def test_chain_barriers_contenu_reel() -> None:
    barriers = bl.chain_barriers(Settings())
    assert barriers["secret-scan"] == 1
    assert barriers["protection"] == 2
    chain = load_chain_texts(Settings())
    assert barriers == {b.id: s.number for s in chain.stations for b in s.barriers}


def test_chain_barriers_sans_chaine_donne_vide(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bl, "load_chain_texts", lambda settings=None: None)
    assert bl.chain_barriers() == {}


# ------------------------------------------------------------------ catalogue_scenario_titles
def _fake_scenarios(monkeypatch: pytest.MonkeyPatch, specs: dict[str, Any]) -> None:
    """`specs` : nom de fichier -> scénario factice ou exception à lever."""
    monkeypatch.setattr(bl, "scenario_files", lambda settings: [Path(n) for n in specs])

    def load(path: Path, settings: Settings):
        value = specs[path.name]
        if isinstance(value, Exception):
            raise value
        return SimpleNamespace(scenario=value)

    monkeypatch.setattr(bl, "load_scenario", load)


def _sc(scenario_id: str, mode: str, title: str, catalogue: bool = True):
    return SimpleNamespace(scenario_id=scenario_id, mode=mode, title_text=title, catalogue=catalogue)


def test_titres_le_mode_a_l_emporte_quel_que_soit_l_ordre(monkeypatch: pytest.MonkeyPatch) -> None:
    for order in (["x.A.yaml", "x.B.yaml"], ["x.B.yaml", "x.A.yaml"]):
        _fake_scenarios(
            monkeypatch,
            {n: _sc("x", n.split(".")[1], f"titre {n.split('.')[1]}") for n in order},
        )
        assert bl.catalogue_scenario_titles(Settings()) == {"x": "titre A"}


def test_titres_un_b_seul_est_retenu_et_hors_catalogue_ignore(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_scenarios(
        monkeypatch,
        {
            "solo.B.yaml": _sc("solo", "B", "Solo B"),
            "cache.A.yaml": _sc("cache", "A", "Caché", catalogue=False),
        },
    )
    assert bl.catalogue_scenario_titles(Settings()) == {"solo": "Solo B"}


def test_titres_premier_b_conserve_entre_deux_b(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_scenarios(
        monkeypatch,
        {"x.1.yaml": _sc("x", "B", "premier"), "x.2.yaml": _sc("x", "B", "second")},
    )
    assert bl.catalogue_scenario_titles(Settings()) == {"x": "premier"}


def test_titres_fichiers_illisibles_ignores_et_journalises(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _fake_scenarios(
        monkeypatch,
        {
            "a.A.yaml": ScenarioError("a.A.yaml", [FieldError("f", 1, "m")]),
            "b.A.yaml": OSError("disque"),
            "c.A.yaml": UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad"),
            "d.A.yaml": _sc("d", "A", "D"),
        },
    )
    with caplog.at_level(logging.WARNING, logger=bl.log.name):
        titles = bl.catalogue_scenario_titles(Settings())
    assert titles == {"d": "D"}
    assert len(caplog.records) == 3
    for name in ("a.A.yaml", "b.A.yaml", "c.A.yaml"):
        assert name in caplog.text


def test_titres_contenu_reel() -> None:
    titles = bl.catalogue_scenario_titles(Settings())
    assert titles["push-direct-main"] == "Voir la protection de main refuser un push direct"
    assert "secret-dans-un-commit" in titles


# --------------------------------------------------------------------------- blockers_body
def test_sans_chaine_pas_d_encart(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bl, "load_chain_texts", lambda settings=None: None)
    assert bl.blockers_body(_real_scenario("add-commit.B"), Settings()) is None


def test_constantes_de_texte() -> None:
    assert bl.TITLE_TEXT == "Ce qui l'aurait bloqué"
    assert bl.SOON_TEXT.format(milestone="v9") == "Arrive en v9"
    assert bl.SOON_FALLBACK_TEXT == "Bientôt"


def test_contenu_reel_forme_exacte_de_l_item() -> None:
    body = bl.blockers_body(_real_scenario("add-commit.B"), Settings())
    scenario = _real_scenario("add-commit.B")
    assert set(body) == {"title_text", "items"}
    (item,) = body["items"]
    assert set(item) == {
        "barrier_id", "label", "station", "station_text", "reason_text",
        "delivered", "soon_text", "scenario",
    }  # fmt: skip
    assert item["station"] == 1
    assert item["station_text"] == "Station 1 · Poste local"
    assert item["reason_text"] == scenario.blocked_by[0].reason_text
    assert item["scenario"]["id"] == "secret-dans-un-commit"


def test_mode_non_livre_utilise_le_texte_de_la_carte_sans_jalon(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = load_chain_texts(Settings())
    stations = [
        s.model_copy(update={"delivered": False, "milestone": ""}) if s.number == 1 else s
        for s in chain.stations
    ]
    cmap = chain.map.model_copy(update={"soon_text": "Prochainement"})
    _patch_chain(monkeypatch, stations=stations, map=cmap)
    (item,) = bl.blockers_body(_real_scenario("add-commit.B"), Settings())["items"]
    assert item["soon_text"] == "Prochainement"
    assert item["delivered"] is False and item["scenario"] is None


def test_non_livre_sans_jalon_ni_carte_porte_bientot(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = load_chain_texts(Settings())
    stations = [
        s.model_copy(update={"delivered": False, "milestone": ""}) if s.number == 1 else s
        for s in chain.stations
    ]
    _patch_chain(monkeypatch, stations=stations, map=None)
    (item,) = bl.blockers_body(_real_scenario("add-commit.B"), Settings())["items"]
    assert item["soon_text"] == "Bientôt"


def test_le_jalon_prime_sur_la_carte(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = load_chain_texts(Settings())
    stations = [
        s.model_copy(update={"delivered": False, "milestone": "v7.7"}) if s.number == 1 else s
        for s in chain.stations
    ]
    _patch_chain(monkeypatch, stations=stations)
    (item,) = bl.blockers_body(_real_scenario("add-commit.B"), Settings())["items"]
    assert item["soon_text"] == "Arrive en v7.7"


def test_jalon_ignore_quand_la_station_est_livree(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = load_chain_texts(Settings())
    stations = [
        s.model_copy(update={"delivered": True, "milestone": "v7.7"}) if s.number == 1 else s
        for s in chain.stations
    ]
    _patch_chain(monkeypatch, stations=stations)
    (item,) = bl.blockers_body(_real_scenario("add-commit.B"), Settings())["items"]
    assert item["soon_text"] is None and item["delivered"] is True


def test_station_absente_de_la_chaine_non_livree_nom_vide(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = load_chain_texts(Settings())
    _patch_chain(monkeypatch, stations=[s for s in chain.stations if s.number != 1])
    (item,) = bl.blockers_body(_real_scenario("add-commit.B"), Settings())["items"]
    assert item["delivered"] is False
    assert item["station_text"] == "Station 1 · "
    assert item["scenario"] is None
    assert item["soon_text"] == chain.map.soon_text


def test_libelle_de_repli_sur_l_identifiant_de_barriere(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = load_chain_texts(Settings())
    stations = [s.model_copy(update={"barriers": []}) if s.number == 1 else s for s in chain.stations]
    _patch_chain(monkeypatch, stations=stations)
    (item,) = bl.blockers_body(_real_scenario("add-commit.B"), Settings())["items"]
    assert item["label"] == "secret-scan"


def test_livree_sans_titre_au_catalogue_avertit_et_sans_lien(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(bl, "catalogue_scenario_titles", lambda settings: {})
    with caplog.at_level(logging.WARNING, logger=bl.log.name):
        (item,) = bl.blockers_body(_real_scenario("add-commit.B"), Settings())["items"]
    assert item["delivered"] is True and item["soon_text"] is None and item["scenario"] is None
    assert "add-commit.B" in caplog.text and "secret-dans-un-commit" in caplog.text


def test_titre_vide_donne_pas_de_lien(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bl, "catalogue_scenario_titles", lambda settings: {"secret-dans-un-commit": ""})
    (item,) = bl.blockers_body(_real_scenario("add-commit.B"), Settings())["items"]
    assert item["scenario"] is None


def test_non_livree_sans_titre_n_avertit_pas(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    chain = load_chain_texts(Settings())
    stations = [s.model_copy(update={"delivered": False}) if s.number == 1 else s for s in chain.stations]
    _patch_chain(monkeypatch, stations=stations)
    monkeypatch.setattr(bl, "catalogue_scenario_titles", lambda settings: {})
    with caplog.at_level(logging.WARNING, logger=bl.log.name):
        bl.blockers_body(_real_scenario("add-commit.B"), Settings())
    assert caplog.text == ""


def test_plusieurs_barrieres_gardent_l_ordre_de_declaration() -> None:
    scenario = _parse(
        [("protection", 2, "push-direct-main"), ("secret-scan", 1, "secret-dans-un-commit")]
    )
    body = bl.blockers_body(scenario, Settings())
    assert [i["barrier_id"] for i in body["items"]] == ["protection", "secret-scan"]
    assert [i["station"] for i in body["items"]] == [2, 1]


def test_scenario_sans_blocked_by_donne_none_sans_lire_la_chaine(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(settings=None):
        raise AssertionError("chaîne lue")

    monkeypatch.setattr(bl, "load_chain_texts", boom)
    assert bl.blockers_body(_parse([]).model_copy(), Settings()) is None
