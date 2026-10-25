# ruff: noqa: E501
"""Renfort story 5.9 : bornes du schéma `Blocker`, lint partiel, cumul d'erreurs, branches de
`blockers_body`, `chain_barriers` et `catalogue_scenario_titles`."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any

import pytest

from wavedevsecops.config import Settings
from wavedevsecops.scenarios import ScenarioError, load_scenario, parse_scenario
from wavedevsecops.web import blockers as bm
from wavedevsecops.web.blockers import (
    SOON_FALLBACK_TEXT,
    SOON_TEXT,
    TITLE_TEXT,
    blockers_body,
    catalogue_scenario_titles,
    chain_barriers,
)
from wavedevsecops.web.catalogue import load_chain_texts

BASE = """
schema_version: 1
scenario_id: essai
mode: B
title_text: Essai
tracks: [llm]
"""


def _item(barrier="secret-scan", station=1, scenario="secret-dans-un-commit", reason="Parce que."):
    return (
        f"  - barrier_id: {barrier}\n    station: {station}\n"
        f"    scenario_id: {scenario}\n    reason_text: {reason}\n"
    )


def _parse(*items: str, **kwargs: Any):
    return parse_scenario(BASE + "blocked_by:\n" + "".join(items), "essai.B.yaml", **kwargs)


def _scenario(key: str):
    settings = Settings()
    return load_scenario(settings.scenarios_path() / f"{key}.yaml", settings).scenario


def _patch_chain(monkeypatch: pytest.MonkeyPatch, station: int | None = None, **changes: Any):
    chain = load_chain_texts(Settings())
    assert chain is not None
    stations = [
        s.model_copy(update=changes) if s.number == station else s for s in chain.stations
    ]
    patched = chain.model_copy(update={"stations": stations})
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: patched)
    return patched


# ------------------------------------------------------------------------------------ constantes
def test_constantes_de_texte() -> None:
    assert TITLE_TEXT == "Ce qui l'aurait bloqué"
    assert SOON_TEXT.format(milestone="v1.2") == "Arrive en v1.2"
    assert SOON_FALLBACK_TEXT == "Bientôt"


# ------------------------------------------------------------------------------ schéma (bornes)
@pytest.mark.parametrize("station", [1, 2, 3, 4])
def test_station_dans_les_bornes(station: int) -> None:
    (blocker,) = _parse(_item(station=station)).blocked_by
    assert blocker.station == station


@pytest.mark.parametrize("station", [0, 5, -1])
def test_station_hors_bornes_refusee(station: int) -> None:
    with pytest.raises(ScenarioError):
        _parse(_item(station=station))


@pytest.mark.parametrize("field", ["barrier_id", "scenario_id"])
@pytest.mark.parametrize("value", ["Secret_Scan", "a b", "-x", "x-"])
def test_identifiants_non_kebab_refuses(field: str, value: str) -> None:
    kwargs = {"barrier": value} if field == "barrier_id" else {"scenario": value}
    with pytest.raises(ScenarioError):
        _parse(_item(**kwargs))


def test_phrase_vide_refusee() -> None:
    with pytest.raises(ScenarioError):
        _parse(_item(reason='""'))


def test_blocker_est_fige() -> None:
    (blocker,) = _parse(_item()).blocked_by
    with pytest.raises(Exception):  # noqa: B017, PT011 - pydantic ValidationError (frozen)
        blocker.station = 2  # type: ignore[misc]


def test_station_non_entiere_refusee() -> None:
    with pytest.raises(ScenarioError):
        _parse(_item(station="premiere"))


# --------------------------------------------------------------------------- lint (branches)
def test_sans_parametres_aucune_verification_de_contenu() -> None:
    scenario = _parse(_item(barrier="inventee", station=3, scenario="fantome"))
    assert scenario.blocked_by[0].barrier_id == "inventee"


def test_barriers_seul_ne_verifie_pas_le_catalogue() -> None:
    scenario = _parse(_item(scenario="fantome"), barriers={"secret-scan": 1})
    assert scenario.blocked_by[0].scenario_id == "fantome"


def test_scenario_ids_seul_ne_verifie_pas_les_barrieres() -> None:
    scenario = _parse(_item(barrier="inventee", station=4), scenario_ids={"secret-dans-un-commit"})
    assert scenario.blocked_by[0].station == 4


def test_scenario_ids_vide_refuse_tout_scenario() -> None:
    with pytest.raises(ScenarioError) as error:
        _parse(_item(), scenario_ids=set())
    assert "scénario inconnu" in str(error.value)


def test_barriers_vide_refuse_toute_barriere() -> None:
    with pytest.raises(ScenarioError) as error:
        _parse(_item(), barriers={})
    assert "barrière inconnue" in str(error.value)
    assert "« secret-scan »" in str(error.value)


def test_station_fausse_message_exact() -> None:
    with pytest.raises(ScenarioError) as error:
        _parse(_item(station=3), barriers={"secret-scan": 1})
    assert "la barrière « secret-scan » est en station 1, non 3" in str(error.value)


def test_barriere_inconnue_ne_signale_pas_aussi_la_station() -> None:
    with pytest.raises(ScenarioError) as error:
        _parse(_item(barrier="inventee", station=2), barriers={"secret-scan": 1})
    assert "est en station" not in str(error.value)


def test_les_erreurs_se_cumulent_avec_leur_ligne() -> None:
    with pytest.raises(ScenarioError) as error:
        _parse(
            _item(barrier="inventee"),
            _item(barrier="secret-scan", station=2, scenario="fantome"),
            barriers={"secret-scan": 1},
            scenario_ids={"secret-dans-un-commit"},
        )
    text = str(error.value)
    assert "barrière inconnue" in text
    assert "est en station 1, non 2" in text
    assert "scénario inconnu" in text
    fields = {e.field for e in error.value.errors} if hasattr(error.value, "errors") else set()
    if fields:
        assert any("blocked_by" in f for f in fields)


def test_doublon_detecte_sans_parametres_de_lint() -> None:
    with pytest.raises(ScenarioError) as error:
        _parse(_item(), _item(scenario="autre"))
    assert "barrière « secret-scan » en double" in str(error.value)


def test_trois_occurrences_donnent_deux_doublons() -> None:
    with pytest.raises(ScenarioError) as error:
        _parse(_item(), _item(), _item())
    assert str(error.value).count("en double") == 2


def test_deux_barrieres_distinctes_valides() -> None:
    scenario = _parse(
        _item(),
        _item(barrier="protection", station=2, scenario="push-direct-main"),
        barriers={"secret-scan": 1, "protection": 2},
        scenario_ids={"secret-dans-un-commit", "push-direct-main"},
    )
    assert [b.barrier_id for b in scenario.blocked_by] == ["secret-scan", "protection"]


# ------------------------------------------------------------------------------ chain_barriers
def test_chain_barriers_contenu_reel() -> None:
    barriers = chain_barriers(Settings())
    assert barriers["secret-scan"] == 1
    assert barriers["protection"] == 2
    chain = load_chain_texts(Settings())
    assert barriers == {b.id: s.number for s in chain.stations for b in s.barriers}
    assert all(isinstance(n, int) and 1 <= n <= 4 for n in barriers.values())


def test_chain_barriers_sans_chaine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: None)
    assert chain_barriers(Settings()) == {}


# --------------------------------------------------------------------------------- blockers_body
def test_sans_chaine_lisible_aucun_encart(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: None)
    assert blockers_body(_scenario("add-commit.B"), Settings()) is None


def test_structure_exacte_de_l_encart_livre() -> None:
    body = blockers_body(_scenario("add-commit.B"), Settings())
    assert body is not None
    assert set(body) == {"title_text", "items"}
    assert body["title_text"] == TITLE_TEXT
    (item,) = body["items"]
    assert set(item) == {
        "barrier_id", "label", "station", "station_text", "reason_text",
        "delivered", "soon_text", "scenario",
    }  # fmt: skip
    assert item["barrier_id"] == "secret-scan"
    assert item["station"] == 1
    assert item["station_text"] == "Station 1 · Poste local"
    assert item["label"] == "Pas de secret dans le commit"
    assert item["scenario"]["id"] == "secret-dans-un-commit"
    assert set(item["scenario"]) == {"id", "title_text"}


def test_station_non_livree_avec_jalon_n_a_pas_de_lien_meme_si_titre_connu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_chain(monkeypatch, 2, delivered=False, milestone="v9.9")
    (item,) = blockers_body(_scenario("push-pull.B"), Settings())["items"]
    assert item["delivered"] is False
    assert item["soon_text"] == "Arrive en v9.9"
    assert item["scenario"] is None
    assert item["station_text"].startswith("Station 2 · ")


def test_sans_jalon_utilise_le_texte_de_la_carte(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = _patch_chain(monkeypatch, 2, delivered=False, milestone=None)
    (item,) = blockers_body(_scenario("push-pull.B"), Settings())["items"]
    expected = chain.map.soon_text if chain.map else SOON_FALLBACK_TEXT
    assert item["soon_text"] == expected


def test_sans_jalon_ni_carte_repli_bientot(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = _patch_chain(monkeypatch, 2, delivered=False, milestone="")
    patched = chain.model_copy(update={"map": None})
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: patched)
    (item,) = blockers_body(_scenario("push-pull.B"), Settings())["items"]
    assert item["soon_text"] == "Bientôt"


def test_station_inconnue_de_la_chaine(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = load_chain_texts(Settings())
    patched = chain.model_copy(update={"stations": [s for s in chain.stations if s.number != 2]})
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: patched)
    (item,) = blockers_body(_scenario("push-pull.B"), Settings())["items"]
    assert item["delivered"] is False
    assert item["station_text"] == "Station 2 · "
    assert item["scenario"] is None
    assert item["soon_text"] == (chain.map.soon_text if chain.map else "Bientôt")


def test_libelle_de_repli_est_l_identifiant(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = load_chain_texts(Settings())
    stations = [
        s.model_copy(update={"barriers": []}) if s.number == 1 else s for s in chain.stations
    ]
    patched = chain.model_copy(update={"stations": stations})
    monkeypatch.setattr(bm, "load_chain_texts", lambda settings=None: patched)
    (item,) = blockers_body(_scenario("add-commit.B"), Settings())["items"]
    assert item["label"] == "secret-scan"
    assert item["delivered"] is True


def test_livree_sans_titre_au_catalogue_avertit_et_sans_lien(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(bm, "catalogue_scenario_titles", lambda settings: {})
    with caplog.at_level(logging.WARNING, logger=bm.log.name):
        (item,) = blockers_body(_scenario("add-commit.B"), Settings())["items"]
    assert item["delivered"] is True
    assert item["soon_text"] is None
    assert item["scenario"] is None
    assert any(
        "add-commit.B" in r.getMessage() and "secret-dans-un-commit" in r.getMessage()
        for r in caplog.records
    )


def test_titre_vide_donne_pas_de_lien(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bm, "catalogue_scenario_titles", lambda settings: {"secret-dans-un-commit": ""})
    (item,) = blockers_body(_scenario("add-commit.B"), Settings())["items"]
    assert item["scenario"] is None


def test_non_livree_sans_titre_n_avertit_pas(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _patch_chain(monkeypatch, 1, delivered=False, milestone="v0.2")
    monkeypatch.setattr(bm, "catalogue_scenario_titles", lambda settings: {})
    with caplog.at_level(logging.WARNING, logger=bm.log.name):
        blockers_body(_scenario("add-commit.B"), Settings())
    assert not caplog.records


def test_plusieurs_barrieres_gardent_l_ordre_et_chaque_station() -> None:
    base = _scenario("add-commit.B")
    other = _scenario("push-pull.B")
    merged = base.model_copy(update={"blocked_by": [*other.blocked_by, *base.blocked_by]})
    body = blockers_body(merged, Settings())
    assert [i["barrier_id"] for i in body["items"]] == ["protection", "secret-scan"]
    assert [i["station"] for i in body["items"]] == [2, 1]


def test_parametre_settings_par_defaut(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[Any] = []
    sentinel = Settings()
    monkeypatch.setattr(bm, "get_settings", lambda: sentinel)
    real = bm.load_chain_texts

    def spy(settings=None):
        seen.append(settings)
        return real(settings)

    monkeypatch.setattr(bm, "load_chain_texts", spy)
    assert blockers_body(_scenario("add-commit.B")) is not None
    assert seen and seen[0] is sentinel


def test_sans_declaration_ne_lit_pas_la_chaine(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(settings=None):
        raise AssertionError("chaîne lue pour rien")

    monkeypatch.setattr(bm, "load_chain_texts", boom)
    assert blockers_body(_scenario("rebase.B"), Settings()) is None


# ---------------------------------------------------------------------- catalogue_scenario_titles
def _fake_catalogue(monkeypatch: pytest.MonkeyPatch, entries: dict[str, Any]) -> None:
    """entries : nom de fichier -> (scenario simulé) ou exception à lever."""
    from pathlib import Path

    monkeypatch.setattr(bm, "scenario_files", lambda settings: [Path(n) for n in entries])

    def fake_load(path, settings):
        value = entries[path.name]
        if isinstance(value, Exception):
            raise value
        return SimpleNamespace(scenario=value)

    monkeypatch.setattr(bm, "load_scenario", fake_load)


def _sc(sid: str, mode: str, title: str, catalogue: bool = True):
    return SimpleNamespace(scenario_id=sid, mode=mode, title_text=title, catalogue=catalogue)


def test_titres_mode_a_prime_sur_b_quel_que_soit_l_ordre(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_catalogue(
        monkeypatch,
        {
            "x.B.yaml": _sc("x", "B", "titre B"),
            "x.A.yaml": _sc("x", "A", "titre A"),
            "y.A.yaml": _sc("y", "A", "y A"),
            "y.B.yaml": _sc("y", "B", "y B"),
        },
    )
    assert catalogue_scenario_titles(Settings()) == {"x": "titre A", "y": "y A"}


def test_titre_b_seul_est_retenu(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_catalogue(monkeypatch, {"z.B.yaml": _sc("z", "B", "z B")})
    assert catalogue_scenario_titles(Settings()) == {"z": "z B"}


def test_premier_b_garde_face_a_un_second_b(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_catalogue(
        monkeypatch, {"z1.B.yaml": _sc("z", "B", "premier"), "z2.B.yaml": _sc("z", "B", "second")}
    )
    assert catalogue_scenario_titles(Settings()) == {"z": "premier"}


def test_scenario_hors_catalogue_ignore(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_catalogue(monkeypatch, {"h.A.yaml": _sc("h", "A", "caché", catalogue=False)})
    assert catalogue_scenario_titles(Settings()) == {}


@pytest.mark.parametrize(
    "error",
    [
        ScenarioError("x.yaml", []),
        OSError("disque"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "octet invalide"),
    ],
)
def test_fichier_illisible_ignore_avec_avertissement(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, error: Exception
) -> None:
    _fake_catalogue(monkeypatch, {"bad.A.yaml": error, "ok.A.yaml": _sc("ok", "A", "ok A")})
    with caplog.at_level(logging.WARNING, logger=bm.log.name):
        titles = catalogue_scenario_titles(Settings())
    assert titles == {"ok": "ok A"}
    assert any("bad.A.yaml" in r.getMessage() for r in caplog.records)


def test_erreur_inattendue_n_est_pas_avalee(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_catalogue(monkeypatch, {"bad.A.yaml": RuntimeError("bug")})
    with pytest.raises(RuntimeError):
        catalogue_scenario_titles(Settings())


def test_catalogue_reel_contient_les_scenarios_cites() -> None:
    titles = catalogue_scenario_titles(Settings())
    assert titles["push-direct-main"] == "Voir la protection de main refuser un push direct"
    assert titles["secret-dans-un-commit"]
