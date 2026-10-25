"""Renfort de la story 8.4 : plages de lignes, bornes du lecteur diff-cover, branches d'erreur."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from wavedevsecops.ci import findings as parsers
from wavedevsecops.scenarios import SetupError
from wavedevsecops.scenarios.ops import replace_in_file


def _doc(total: int, percent: object, stats: dict) -> str:
    return json.dumps(
        {"src_stats": stats, "total_num_lines": total, "total_percent_covered": percent}
    )


def test_les_plages_separent_les_lignes_isolees_des_suites(tmp_path: Path) -> None:
    text = _doc(9, 0, {"a.py": {"violation_lines": [6, 2, 1, 4]}})
    found = parsers.parse_diff_cover_json(text, tmp_path)
    assert found[1].message_text == "4 lignes du nouveau code sans test : 1-2, 4, 6"
    assert parsers._ranges([59, 60, 61, 65, 70, 72, 73]) == "59-61, 65, 70, 72-73"
    assert parsers._ranges([5]) == "5"
    assert parsers._ranges([]) == ""


def test_une_seule_ligne_mesuree_compte(tmp_path: Path) -> None:
    (summary,) = parsers.parse_diff_cover_json(_doc(1, 100, {"a.py": {}}), tmp_path)
    assert summary.rule_id == parsers.DIFF_COVERAGE_RULE
    assert summary.message_text == "Couverture du nouveau code 100 % · seuil 80 % · ✓"


def test_le_pourcentage_est_exige_seulement_si_des_lignes_sont_mesurees(tmp_path: Path) -> None:
    for percent in (None, "90"):
        with pytest.raises(ValueError):
            parsers.parse_diff_cover_json(_doc(1, percent, {}), tmp_path)
    (summary,) = parsers.parse_diff_cover_json(_doc(0, None, {}), tmp_path)
    assert summary.rule_id == parsers.NO_DIFF_RULE


def test_une_entree_ou_un_fichier_sans_manque_n_arrete_pas_la_lecture(tmp_path: Path) -> None:
    stats = {"x.py": 1, "y.py": {"violation_lines": []}, "z.py": {"violation_lines": [3]}}
    found = parsers.parse_diff_cover_json(_doc(2, 0, stats), tmp_path)
    assert [(f.rule_id, f.path, f.line) for f in found[1:]] == [("uncovered_lines", "z.py", 3)]
    stats = {"y.py": {"violation_lines": []}, "z.py": {"violation_lines": [3]}}
    assert len(parsers.parse_diff_cover_json(_doc(2, 0, stats), tmp_path)) == 2


def test_le_singulier_et_la_gravite_des_lignes_non_couvertes(tmp_path: Path) -> None:
    red = parsers.parse_diff_cover_json(_doc(2, 50, {"a.py": {"violation_lines": [4]}}), tmp_path)
    assert red[1].message_text == "1 ligne du nouveau code sans test : 4"
    assert red[1].severity == "error"
    green = parsers.parse_diff_cover_json(
        _doc(10, 90, {"a.py": {"violation_lines": [4, 5]}}), tmp_path
    )
    assert green[0].severity == "info"
    assert green[1].severity == "info"
    assert green[1].message_text.startswith("2 lignes ")


def test_coverage_json_refuse_les_structures_inattendues(tmp_path: Path) -> None:
    cases = [
        {"totals": [1], "files": {"a.py": {}}},
        {"totals": {"percent_covered": 50}, "files": [1]},
        {"totals": {"percent_covered": 50}, "files": 1},
    ]
    for case in cases:
        with pytest.raises(ValueError, match="vide ou inattendue"):
            parsers.parse_coverage_json(json.dumps(case), tmp_path)
    for totals in ({}, {"percent_covered": None}, {"percent_covered": "abc"}):
        text = json.dumps({"totals": totals, "files": {"a": {}}})
        with pytest.raises(ValueError, match="est inattendue"):
            parsers.parse_coverage_json(text, tmp_path)


def test_replace_in_file_refuse_un_texte_vide_ou_illisible(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="vide"):
        replace_in_file.Args(op="replace_in_file", path="f.txt", old="", new="x")
    ctx = SimpleNamespace(layout=SimpleNamespace(repo=tmp_path))
    (tmp_path / "bin.txt").write_bytes(b"\xff\xfe\x00\x80abc")
    for name in ("bin.txt", "absent.txt"):
        args = replace_in_file.Args(op="replace_in_file", path=name, old="a", new="b")
        with pytest.raises(SetupError, match="n'a pas pu être lu"):
            replace_in_file.apply(args, ctx)  # type: ignore[arg-type]
