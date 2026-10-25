"""Renfort story 8.4 : valeurs exactes, bornes et branches d'erreur des lecteurs de couverture,
de `with_tools_on_path` et de l'op `replace_in_file`."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import pytest

from wavedevsecops import toolrun
from wavedevsecops.ci import findings as parsers
from wavedevsecops.config import Settings
from wavedevsecops.scenarios import SetupError
from wavedevsecops.scenarios.ops import replace_in_file


def _diff(total: object, percent: object, stats: object) -> str:
    return json.dumps(
        {"total_num_lines": total, "total_percent_covered": percent, "src_stats": stats}
    )


# ------------------------------------------------------------------ _ranges
@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        ([], ""),
        ([5], "5"),
        ([59, 60, 61, 65], "59-61, 65"),
        ([3, 1, 2], "1-3"),
        ([2, 2, 2], "2"),
        ([1, 3, 5], "1, 3, 5"),
        ([1, 2, 4, 5, 9], "1-2, 4-5, 9"),
    ],
)
def test_ranges_regroupe_les_lignes_consecutives(lines: list[int], expected: str) -> None:
    assert parsers._ranges(lines) == expected


# ------------------------------------------------------------------ diff_coverage_text
def test_texte_du_constat_de_couverture() -> None:
    assert parsers.QUALITY_GATE_THRESHOLD == 80
    assert parsers.diff_coverage_text(100, True) == (
        "Couverture du nouveau code 100 % · seuil 80 % · ✓"
    )
    assert parsers.diff_coverage_text(0, False) == (
        "Couverture du nouveau code 0 % · seuil 80 % · ✗"
    )
    assert parsers.diff_coverage_text(None, True) == (
        "Couverture du nouveau code aucune ligne à mesurer · seuil 80 % · ✓"
    )


# ------------------------------------------------------------------ parse_diff_cover_json
@pytest.mark.parametrize(
    ("percent", "ok"), [(79, False), (80, True), (81, True), (0, False), (100, True)]
)
def test_borne_du_seuil(tmp_path: Path, percent: int, ok: bool) -> None:
    (summary, *_) = parsers.parse_diff_cover_json(_diff(10, percent, {}), tmp_path)
    assert summary.rule_id == "diff_coverage"
    assert summary.severity == ("info" if ok else "error")
    assert summary.message_text.endswith("✓" if ok else "✗")


def test_pourcentage_flottant_tronque_vers_le_bas(tmp_path: Path) -> None:
    (summary,) = parsers.parse_diff_cover_json(_diff(1000, 79.9, {}), tmp_path)
    assert summary.severity == "error"
    assert "79 % · seuil" in summary.message_text
    (summary,) = parsers.parse_diff_cover_json(_diff(1000, 80.9, {}), tmp_path)
    assert summary.severity == "info" and "80 % ·" in summary.message_text


def test_sans_ligne_mesuree_le_pourcentage_est_ignore(tmp_path: Path) -> None:
    for percent in (None, "x", 0):
        (summary,) = parsers.parse_diff_cover_json(_diff(0, percent, {}), tmp_path)
        assert summary.rule_id == "diff_coverage_none"
        assert summary.severity == "info"
        assert "aucune ligne à mesurer" in summary.message_text


def test_pourcentage_absent_avec_des_lignes_mesurees_est_refuse(tmp_path: Path) -> None:
    for percent in (None, "80", [80]):
        with pytest.raises(ValueError, match="inattendue"):
            parsers.parse_diff_cover_json(_diff(3, percent, {}), tmp_path)


def test_champs_de_structure_invalides_sont_refuses(tmp_path: Path) -> None:
    for text in (_diff("3", 50, {}), _diff(None, 50, {}), _diff(3, 50, []), _diff(3, 50, None)):
        with pytest.raises(ValueError, match="inattendue"):
            parsers.parse_diff_cover_json(text, tmp_path)
    with pytest.raises(ValueError, match="illisible"):
        parsers.parse_diff_cover_json("{", tmp_path)
    with pytest.raises(ValueError, match="inattendue"):
        parsers.parse_diff_cover_json("[1]", tmp_path)


def test_lignes_non_couvertes_singulier_et_pluriel(tmp_path: Path) -> None:
    stats = {
        "src/one.py": {"violation_lines": [7]},
        "src/many.py": {"violation_lines": [10, 4, 5, 6]},
    }
    summary, one, many = parsers.parse_diff_cover_json(_diff(5, 0, stats), tmp_path)
    assert summary.severity == "error"
    assert one.message_text == "1 ligne du nouveau code sans test : 7"
    assert (one.path, one.line, one.severity, one.rule_id) == (
        "src/one.py",
        7,
        "error",
        "uncovered_lines",
    )
    assert many.message_text == "4 lignes du nouveau code sans test : 4-6, 10"
    assert many.line == 4


def test_lignes_non_couvertes_en_information_quand_le_seuil_est_atteint(tmp_path: Path) -> None:
    stats = {"src/a.py": {"violation_lines": [3]}}
    summary, detail = parsers.parse_diff_cover_json(_diff(10, 90, stats), tmp_path)
    assert summary.severity == "info" and detail.severity == "info"


def test_fichiers_et_lignes_invalides_sont_ignores(tmp_path: Path) -> None:
    stats = {
        "src/skip1.py": "texte",
        "src/skip2.py": {"violation_lines": []},
        "src/skip3.py": {"violation_lines": None},
        "src/skip4.py": {},
        "src/skip5.py": {"violation_lines": ["a", None, 1.5]},
        "src/keep.py": {"violation_lines": ["x", 2, 3]},
    }
    found = parsers.parse_diff_cover_json(_diff(5, 0, stats), tmp_path)
    assert [f.path for f in found[1:]] == ["src/keep.py"]
    assert found[1].message_text == "2 lignes du nouveau code sans test : 2-3"


def test_ligne_nulle_donne_une_ligne_absente(tmp_path: Path) -> None:
    stats = {"src/a.py": {"violation_lines": [0, 4]}}
    found = parsers.parse_diff_cover_json(_diff(5, 0, stats), tmp_path)
    assert found[1].line is None  # min = 0, hors bornes


# ------------------------------------------------------------------ parse_coverage_json
def _cov(totals: object, files: object = None) -> str:
    return json.dumps({"totals": totals, "files": {"a.py": {}} if files is None else files})


def test_couverture_totale_tronquee_et_information(tmp_path: Path) -> None:
    for raw, shown in ((87.6, 87), (0, 0), (100, 100), ("42.9", 42), (99.99, 99)):
        (total,) = parsers.parse_coverage_json(_cov({"percent_covered": raw}), tmp_path)
        assert total.rule_id == "total_coverage" and total.severity == "info"
        assert total.message_text == f"Couverture de l'ensemble du dépôt : {shown} % (information)."


def test_couverture_totale_refuse_les_mesures_inattendues(tmp_path: Path) -> None:
    for text in (
        _cov({}),
        _cov({"percent_covered": None}),
        _cov({"percent_covered": "abc"}),
        _cov([]),
        _cov({"percent_covered": 5}, files=[]),
        _cov({"percent_covered": 5}, files={}),
        json.dumps({"totals": {"percent_covered": 5}}),
    ):
        with pytest.raises(ValueError, match="mesure de couverture"):
            parsers.parse_coverage_json(text, tmp_path)
    with pytest.raises(ValueError, match="illisible"):
        parsers.parse_coverage_json("nope", tmp_path)


def test_les_lecteurs_sont_enregistres() -> None:
    assert parsers.PARSERS["diff_cover_json"] is parsers.parse_diff_cover_json
    assert parsers.PARSERS["coverage_json"] is parsers.parse_coverage_json


# ------------------------------------------------------------------ with_tools_on_path
def _fake_resolve(table: dict[str, Path | None]) -> Callable[..., SimpleNamespace]:
    def resolve(tool_id: str, settings: Settings | None = None, **_: object) -> SimpleNamespace:
        path = table.get(tool_id)
        return SimpleNamespace(ok=path is not None, path=path)

    return resolve


def test_with_tools_on_path_met_les_dossiers_en_tete(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        toolrun,
        "resolve",
        _fake_resolve({"git": Path("/opt/git/bin/git"), "uv": Path("/opt/uv/uv")}),
    )
    env = {"PATH": "/usr/bin", "OTHER": "1"}
    out = toolrun.with_tools_on_path(env, ("git", "uv"), Settings())
    expected = [str(Path("/opt/git/bin")), str(Path("/opt/uv")), "/usr/bin"]
    assert out["PATH"] == os.pathsep.join(expected)
    assert out["OTHER"] == "1"
    assert env == {"PATH": "/usr/bin", "OTHER": "1"}  # l'entrée n'est pas modifiée


def test_with_tools_on_path_ignore_un_outil_introuvable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(toolrun, "resolve", _fake_resolve({"git": None}))
    out = toolrun.with_tools_on_path({"PATH": "/usr/bin"}, ("git",), Settings())
    assert out["PATH"] == "/usr/bin"


def test_with_tools_on_path_sans_path_pas_de_separateur_pendant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(toolrun, "resolve", _fake_resolve({"git": Path("/g/git")}))
    out = toolrun.with_tools_on_path({}, ("git",), Settings())
    assert out["PATH"] == str(Path("/g"))
    assert toolrun.with_tools_on_path({}, (), Settings())["PATH"] == ""


def test_with_tools_on_path_respecte_la_casse_de_la_cle(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(toolrun, "resolve", _fake_resolve({"git": Path("/g/git")}))
    out = toolrun.with_tools_on_path({"Path": "/usr/bin"}, ("git",), Settings())
    assert out["Path"] == os.pathsep.join([str(Path("/g")), "/usr/bin"])
    assert "PATH" not in out


def test_hook_environment_garde_gitleaks_uv_et_le_venv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        toolrun, "resolve", _fake_resolve({"gitleaks": Path("/a/gitleaks"), "uv": Path("/b/uv")})
    )
    out = toolrun.hook_environment({"PATH": "/p"}, Path("/venv"), Settings())
    assert out["PATH"] == os.pathsep.join([str(Path("/a")), str(Path("/b")), "/p"])
    assert out["UV_PROJECT_ENVIRONMENT"] == str(Path("/venv"))


# ------------------------------------------------------------------ replace_in_file
def _ctx(root: Path) -> SimpleNamespace:
    return SimpleNamespace(layout=SimpleNamespace(repo=root))


def _args(path: str, old: str, new: str) -> replace_in_file.Args:
    return replace_in_file.Args(op="replace_in_file", path=path, old=old, new=new)


def _apply(root: Path, path: str, old: str, new: str) -> str:
    return replace_in_file.apply(_args(path, old, new), _ctx(root))  # type: ignore[arg-type]


def test_replace_in_file_retourne_l_identifiant_et_ecrit(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_text("alpha beta", "utf-8")
    result = _apply(tmp_path, "f.txt", "beta", "gamma")
    assert result.endswith("f.txt") and "worktree" in result
    assert (tmp_path / "f.txt").read_text("utf-8") == "alpha gamma"


def test_replace_in_file_message_compte_les_occurrences(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_text("a a a", "utf-8")
    with pytest.raises(SetupError, match="3 fois"):
        _apply(tmp_path, "f.txt", "a", "b")
    with pytest.raises(SetupError, match="0 fois"):
        _apply(tmp_path, "f.txt", "z", "b")
    assert (tmp_path / "f.txt").read_text("utf-8") == "a a a"  # rien d'écrit en cas d'échec


def test_replace_in_file_normalise_les_fins_de_ligne(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_bytes(b"x\r\ny\r\nz\r\n")
    _apply(tmp_path, "f.txt", "x\r\ny\n", "X\nY\n")
    assert (tmp_path / "f.txt").read_bytes().replace(b"\r\n", b"\n") == b"X\nY\nz\n"


def test_replace_in_file_fichier_absent_ou_illisible(tmp_path: Path) -> None:
    with pytest.raises(SetupError, match="pas pu être lu"):
        _apply(tmp_path, "absent.txt", "a", "b")
    (tmp_path / "bin.dat").write_bytes(b"\xff\xfe\x00\x80")
    with pytest.raises(SetupError, match="pas pu être lu"):
        _apply(tmp_path, "bin.dat", "a", "b")


def test_replace_in_file_remplace_par_une_chaine_vide(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_text("keep drop", "utf-8")
    _apply(tmp_path, "f.txt", " drop", "")
    assert (tmp_path / "f.txt").read_text("utf-8") == "keep"


@pytest.mark.parametrize("path", ["../x", "/etc/passwd", "a/../../x"])
def test_replace_in_file_refuse_les_chemins_hors_depot(path: str) -> None:
    with pytest.raises(ValueError):
        _args(path, "a", "b")


def test_replace_in_file_refuse_un_texte_vide() -> None:
    with pytest.raises(ValueError, match="vide"):
        _args("f.txt", "", "b")


def test_replace_in_file_refuse_une_op_differente() -> None:
    with pytest.raises(ValueError):
        replace_in_file.Args(op="autre", path="f", old="a", new="b")  # type: ignore[arg-type]
