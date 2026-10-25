"""Renfort de la story 8.4 : valeurs exactes, bornes et branches d'erreur des lecteurs."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from wavedevsecops.ci import findings as parsers
from wavedevsecops.scenarios import SetupError
from wavedevsecops.scenarios.ops import replace_in_file


def _dc(total: int, percent: object, stats: object) -> str:
    return json.dumps(
        {"total_num_lines": total, "total_percent_covered": percent, "src_stats": stats}
    )


def test_ranges_formate_isoles_et_plages() -> None:
    assert parsers._ranges([5, 7]) == "5, 7"
    assert parsers._ranges([1, 3, 4]) == "1, 3-4"
    assert parsers._ranges([1, 2, 5]) == "1-2, 5"
    assert parsers._ranges([9, 7, 8, 7]) == "7-9"
    assert parsers._ranges([4]) == "4"
    assert parsers._ranges([]) == ""


def test_diff_cover_une_seule_ligne_mesuree_compte(tmp_path: Path) -> None:
    ok = parsers.parse_diff_cover_json(_dc(1, 100, {}), tmp_path)
    assert [(f.rule_id, f.severity) for f in ok] == [("diff_coverage", "info")]
    ko = parsers.parse_diff_cover_json(_dc(1, 0, {}), tmp_path)
    assert [(f.rule_id, f.severity) for f in ko] == [("diff_coverage", "error")]


def test_diff_cover_aucune_ligne_mesuree_sans_pourcentage(tmp_path: Path) -> None:
    found = parsers.parse_diff_cover_json(_dc(0, None, {}), tmp_path)
    assert [(f.rule_id, f.severity) for f in found] == [("diff_coverage_none", "info")]
    assert found[0].message_text == parsers.diff_coverage_text(None, True)


def test_diff_cover_pourcentage_absent_ou_faux_est_refuse(tmp_path: Path) -> None:
    for percent in (None, "90"):
        with pytest.raises(ValueError, match="inattendue"):
            parsers.parse_diff_cover_json(_dc(3, percent, {}), tmp_path)


def test_diff_cover_ignore_les_entrees_sans_manque_et_continue(tmp_path: Path) -> None:
    stats = {
        "a.py": "pas un dict",
        "b.py": {"violation_lines": []},
        "c.py": {"violation_lines": [3, "x", 4]},
    }
    found = parsers.parse_diff_cover_json(_dc(4, 50, stats), tmp_path)
    assert [f.rule_id for f in found] == ["diff_coverage", "uncovered_lines"]
    assert found[1].path == "c.py"
    assert found[1].line == 3
    assert found[1].message_text == "2 lignes du nouveau code sans test : 3-4"


def test_diff_cover_constat_par_fichier_singulier_pluriel_et_severite(tmp_path: Path) -> None:
    stats = {"a.py": {"violation_lines": [7]}, "b.py": {"violation_lines": [2, 9, 10]}}
    failed = parsers.parse_diff_cover_json(_dc(10, 79, stats), tmp_path)
    assert [f.severity for f in failed] == ["error", "error", "error"]
    assert failed[1].message_text == "1 ligne du nouveau code sans test : 7"
    assert failed[2].message_text == "3 lignes du nouveau code sans test : 2, 9-10"
    passed = parsers.parse_diff_cover_json(_dc(10, 80, stats), tmp_path)
    assert [f.severity for f in passed] == ["info", "info", "info"]


def _cov(totals: object, files: object) -> str:
    return json.dumps({"totals": totals, "files": files})


def test_coverage_json_valeur_exacte(tmp_path: Path) -> None:
    found = parsers.parse_coverage_json(_cov({"percent_covered": 87.9}, {"a.py": {}}), tmp_path)
    assert len(found) == 1
    assert found[0].message_text == "Couverture de l'ensemble du dépôt : 87 % (information)."


def test_coverage_json_totaux_ou_fichiers_invalides(tmp_path: Path) -> None:
    for totals, files in (
        (["x"], {"a.py": {}}),
        ({"percent_covered": 1}, ["a.py"]),
        ({"percent_covered": 1}, {}),
    ):
        with pytest.raises(ValueError, match="vide ou inattendue"):
            parsers.parse_coverage_json(_cov(totals, files), tmp_path)


def test_coverage_json_pourcentage_manquant_ou_illisible(tmp_path: Path) -> None:
    for totals in ({}, {"percent_covered": None}, {"percent_covered": "abc"}):
        with pytest.raises(ValueError, match="est inattendue") as err:
            parsers.parse_coverage_json(_cov(totals, {"a.py": {}}), tmp_path)
        assert "vide" not in str(err.value)


def test_replace_in_file_refuse_un_texte_vide() -> None:
    with pytest.raises(ValueError, match="vide"):
        replace_in_file.Args(op="replace_in_file", path="f.txt", old="", new="x")


def test_replace_in_file_fichier_illisible(tmp_path: Path) -> None:
    ctx = SimpleNamespace(layout=SimpleNamespace(repo=tmp_path))
    (tmp_path / "bin.txt").write_bytes(b"\xff\xfe\x00abc\x80")
    for name in ("bin.txt", "absent.txt"):
        args = replace_in_file.Args(op="replace_in_file", path=name, old="a", new="b")
        with pytest.raises(SetupError, match="n'a pas pu être lu"):
            replace_in_file.apply(args, ctx)  # type: ignore[arg-type]
