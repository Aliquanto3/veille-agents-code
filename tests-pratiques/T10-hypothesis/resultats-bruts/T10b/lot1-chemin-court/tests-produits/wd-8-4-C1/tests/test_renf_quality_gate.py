"""Renfort de la story 8.4 : bornes des lecteurs diff-cover / coverage et de l'op replace_in_file."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from wavedevsecops.ci import findings as parsers
from wavedevsecops.scenarios import SetupError
from wavedevsecops.scenarios.ops import replace_in_file

TREE = Path("tree")


def _diff(total: int, percent: object, stats: dict) -> str:
    return json.dumps(
        {"total_num_lines": total, "total_percent_covered": percent, "src_stats": stats}
    )


@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        ([5], "5"),
        ([5, 7], "5, 7"),
        ([1, 2, 3, 9], "1-3, 9"),
        ([9, 1, 2, 2, 3, 20, 21], "1-3, 9, 20-21"),
        ([4, 6, 8], "4, 6, 8"),
        ([], ""),
    ],
)
def test_ranges_exactes(lines: list[int], expected: str) -> None:
    assert parsers._ranges(lines) == expected


def test_une_seule_ligne_mesuree_est_mesuree() -> None:
    found = parsers.parse_diff_cover_json(_diff(1, 100, {}), TREE)
    assert [f.rule_id for f in found] == [parsers.DIFF_COVERAGE_RULE]
    assert found[0].severity == "info"
    assert "100 %" in found[0].message_text


def test_aucune_ligne_mesuree_sans_pourcentage() -> None:
    found = parsers.parse_diff_cover_json(_diff(0, None, {}), TREE)
    assert [f.rule_id for f in found] == [parsers.NO_DIFF_RULE]
    assert found[0].severity == "info"
    assert "aucune ligne à mesurer" in found[0].message_text


def test_pourcentage_invalide_avec_lignes_mesurees_est_refuse() -> None:
    with pytest.raises(ValueError, match="inattendue"):
        parsers.parse_diff_cover_json(_diff(3, "beaucoup", {}), TREE)
    with pytest.raises(ValueError, match="inattendue"):
        parsers.parse_diff_cover_json(_diff(3, None, {}), TREE)


def test_les_entrees_illisibles_ou_sans_ligne_n_arretent_pas_la_lecture() -> None:
    stats = {
        "bad.py": "pas un dict",
        "ok.py": {"violation_lines": []},
        "none.py": {"violation_lines": None},
        "last.py": {"violation_lines": [3]},
    }
    found = parsers.parse_diff_cover_json(_diff(10, 50, stats), TREE)
    uncovered = [f for f in found if f.rule_id == parsers.UNCOVERED_RULE]
    assert len(uncovered) == 1
    assert uncovered[0].path == "last.py"
    assert uncovered[0].line == 3


def test_entree_non_dict_suivie_d_une_entree_a_constat() -> None:
    stats = {"bad.py": 3, "last.py": {"violation_lines": [1, 2]}}
    found = parsers.parse_diff_cover_json(_diff(10, 50, stats), TREE)
    assert [f.path for f in found if f.rule_id == parsers.UNCOVERED_RULE] == ["last.py"]


def test_singulier_et_pluriel_du_constat_par_fichier() -> None:
    stats = {"a.py": {"violation_lines": [7]}, "b.py": {"violation_lines": [4, 5, 9]}}
    found = parsers.parse_diff_cover_json(_diff(10, 50, stats), TREE)
    texts = {f.path: f.message_text for f in found if f.rule_id == parsers.UNCOVERED_RULE}
    assert texts["a.py"] == "1 ligne du nouveau code sans test : 7"
    assert texts["b.py"] == "3 lignes du nouveau code sans test : 4-5, 9"


def test_gravite_des_constats_par_fichier_suit_le_seuil() -> None:
    stats = {"a.py": {"violation_lines": [7]}}
    sous = parsers.parse_diff_cover_json(_diff(10, 79, stats), TREE)
    assert [f.severity for f in sous] == ["error", "error"]
    au_seuil = parsers.parse_diff_cover_json(_diff(10, 80, stats), TREE)
    assert [f.severity for f in au_seuil] == ["info", "info"]


def test_coverage_json_totals_illisible_est_refuse_comme_vide() -> None:
    text = json.dumps({"totals": [], "files": {"a.py": {}}})
    with pytest.raises(ValueError, match="vide ou inattendue"):
        parsers.parse_coverage_json(text, TREE)
    text = json.dumps({"totals": {"percent_covered": 90}, "files": []})
    with pytest.raises(ValueError, match="vide ou inattendue"):
        parsers.parse_coverage_json(text, TREE)
    text = json.dumps({"totals": {"percent_covered": 90}, "files": {}})
    with pytest.raises(ValueError, match="vide ou inattendue"):
        parsers.parse_coverage_json(text, TREE)


def test_coverage_json_sans_pourcentage_est_refuse() -> None:
    for totals in ({}, {"percent_covered": None}, {"percent_covered": "x"}):
        text = json.dumps({"totals": totals, "files": {"a.py": {}}})
        with pytest.raises(ValueError, match="mesure de couverture est inattendue"):
            parsers.parse_coverage_json(text, TREE)


def test_coverage_json_valide() -> None:
    text = json.dumps({"totals": {"percent_covered": 87.9}, "files": {"a.py": {}}})
    (found,) = parsers.parse_coverage_json(text, TREE)
    assert found.message_text == "Couverture de l'ensemble du dépôt : 87 % (information)."


def test_replace_in_file_refuse_un_texte_vide() -> None:
    with pytest.raises(ValueError, match="vide"):
        replace_in_file.Args(op="replace_in_file", path="f.txt", old="", new="x")


def test_replace_in_file_fichier_non_utf8_ou_absent(tmp_path: Path) -> None:
    ctx = SimpleNamespace(layout=SimpleNamespace(repo=tmp_path))
    (tmp_path / "bin.txt").write_bytes(b"\xff\xfe\x00\xff")
    for name in ("bin.txt", "absent.txt"):
        args = replace_in_file.Args(op="replace_in_file", path=name, old="a", new="b")
        with pytest.raises(SetupError, match="n'a pas pu être lu"):
            replace_in_file.apply(args, ctx)  # type: ignore[arg-type]
