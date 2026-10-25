"""Renfort de la story 8.4 : bornes, branches d'erreur et valeurs exactes des lecteurs."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from wavedevsecops.ci import findings as parsers


def _diff(total: int, stats: dict, percent: object = 100) -> str:
    return json.dumps(
        {"src_stats": stats, "total_num_lines": total, "total_percent_covered": percent}
    )


def test_ranges_isole_les_lignes_seules_et_groupe_les_suites() -> None:
    assert parsers._ranges([5]) == "5"
    assert parsers._ranges([1, 3, 4]) == "1, 3-4"
    assert parsers._ranges([1, 2, 5]) == "1-2, 5"
    assert parsers._ranges([59, 60, 61, 65]) == "59-61, 65"
    assert parsers._ranges([7, 7, 3]) == "3, 7"


def test_une_seule_ligne_mesuree_compte(tmp_path: Path) -> None:
    (summary,) = parsers.parse_diff_cover_json(_diff(1, {}, 100), tmp_path)
    assert summary.rule_id == parsers.DIFF_COVERAGE_RULE
    assert summary.message_text == "Couverture du nouveau code 100 % · seuil 80 % · ✓"


def test_pourcentage_illisible_refuse_seulement_si_des_lignes_sont_mesurees(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="inattendue"):
        parsers.parse_diff_cover_json(_diff(1, {}, None), tmp_path)
    with pytest.raises(ValueError, match="inattendue"):
        parsers.parse_diff_cover_json(_diff(3, {}, "80"), tmp_path)
    (summary,) = parsers.parse_diff_cover_json(_diff(0, {}, None), tmp_path)
    assert summary.rule_id == parsers.NO_DIFF_RULE


def test_les_entrees_sans_manque_n_arretent_pas_la_lecture(tmp_path: Path) -> None:
    stats = {
        "bad": 1,
        "ok.py": {"violation_lines": [], "covered_lines": [1]},
        "sans_cle.py": {},
        "ko.py": {"violation_lines": [4, "x", 6]},
    }
    found = parsers.parse_diff_cover_json(_diff(5, stats, 20), tmp_path)
    assert [f.path for f in found[1:]] == ["ko.py"]
    assert found[1].message_text == "2 lignes du nouveau code sans test : 4, 6"
    assert found[1].line == 4


def test_une_ligne_non_couverte_est_au_singulier(tmp_path: Path) -> None:
    stats = {"a.py": {"violation_lines": [9]}}
    found = parsers.parse_diff_cover_json(_diff(2, stats, 50), tmp_path)
    assert found[1].message_text == "1 ligne du nouveau code sans test : 9"


def test_la_severite_des_lignes_non_couvertes_suit_le_seuil(tmp_path: Path) -> None:
    stats = {"a.py": {"violation_lines": [10]}}
    red = parsers.parse_diff_cover_json(_diff(10, stats, 10), tmp_path)
    assert (red[0].severity, red[1].severity) == ("error", "error")
    green = parsers.parse_diff_cover_json(_diff(10, stats, 90), tmp_path)
    assert (green[0].severity, green[1].severity) == ("info", "info")


@pytest.mark.parametrize(
    "data",
    [
        {"files": {"a.py": {}}, "totals": None},
        {"files": {"a.py": {}}, "totals": []},
        {"files": "abc", "totals": {"percent_covered": 50}},
        {"files": None, "totals": {"percent_covered": 50}},
        {"files": {}, "totals": {"percent_covered": 50}},
    ],
)
def test_coverage_refuse_une_forme_vide_ou_inattendue(data: dict, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="vide ou inattendue"):
        parsers.parse_coverage_json(json.dumps(data), tmp_path)


@pytest.mark.parametrize("totals", [{}, {"percent_covered": "abc"}, {"percent_covered": None}])
def test_coverage_refuse_un_pourcentage_absent_ou_illisible(totals: dict, tmp_path: Path) -> None:
    text = json.dumps({"files": {"a.py": {}}, "totals": totals})
    with pytest.raises(ValueError, match="est inattendue"):
        parsers.parse_coverage_json(text, tmp_path)


def test_replace_in_file_refuse_un_texte_vide() -> None:
    from wavedevsecops.scenarios.ops import replace_in_file

    with pytest.raises(ValueError, match="vide"):
        replace_in_file.Args(op="replace_in_file", path="f.txt", old="", new="b")


def test_replace_in_file_refuse_un_fichier_non_utf8(tmp_path: Path) -> None:
    from wavedevsecops.scenarios import SetupError
    from wavedevsecops.scenarios.ops import replace_in_file

    (tmp_path / "f.bin").write_bytes(b"\xff\xfe\x00\xc3(")
    ctx = SimpleNamespace(layout=SimpleNamespace(repo=tmp_path))
    args = replace_in_file.Args(op="replace_in_file", path="f.bin", old="a", new="b")
    with pytest.raises(SetupError, match="n'a pas pu être lu"):
        replace_in_file.apply(args, ctx)  # type: ignore[arg-type]
