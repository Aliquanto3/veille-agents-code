"""Renfort de la story 8.4 : valeurs exactes, bornes et branches d'erreur des lecteurs de
couverture, de l'op `replace_in_file`, de `toolrun.with_tools_on_path` et de l'exécution du job
`quality_gate` (avec des outils simulés)."""

from __future__ import annotations

import json
import os
from itertools import groupby
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from wavedevsecops import ci, toolrun
from wavedevsecops.ci import findings as parsers
from wavedevsecops.config import Settings
from wavedevsecops.scenarios import SetupError
from wavedevsecops.scenarios.ops import replace_in_file

SETTINGS = Settings()
PIPELINE = ci.load_pipeline(SETTINGS)


def _diff_json(total: Any, percent: Any, stats: Any) -> str:
    return json.dumps(
        {"total_num_lines": total, "total_percent_covered": percent, "src_stats": stats}
    )


# ------------------------------------------------------------------ _ranges
def _reference_ranges(lines: list[int]) -> str:
    out = []
    for _, group in groupby(enumerate(sorted(set(lines))), key=lambda p: p[1] - p[0]):
        run = [n for _, n in group]
        out.append(str(run[0]) if len(run) == 1 else f"{run[0]}-{run[-1]}")
    return ", ".join(out)


@given(st.lists(st.integers(min_value=1, max_value=60), max_size=40))
def test_ranges_regroupe_les_lignes_consecutives(lines: list[int]) -> None:
    assert parsers._ranges(lines) == _reference_ranges(lines)


def test_ranges_exemples() -> None:
    assert parsers._ranges([]) == ""
    assert parsers._ranges([5]) == "5"
    assert parsers._ranges([59, 60, 61, 65]) == "59-61, 65"
    assert parsers._ranges([3, 1, 2, 2]) == "1-3"
    assert parsers._ranges([1, 3, 5]) == "1, 3, 5"
    assert parsers._ranges([4, 5]) == "4-5"


# ------------------------------------------------------------------ diff_coverage_text
@given(st.integers(min_value=0, max_value=100), st.booleans())
def test_diff_coverage_text_format(percent: int, passed: bool) -> None:
    mark = "✓" if passed else "✗"
    assert (
        parsers.diff_coverage_text(percent, passed)
        == f"Couverture du nouveau code {percent} % · seuil 80 % · {mark}"
    )


def test_diff_coverage_text_sans_ligne() -> None:
    assert parsers.diff_coverage_text(None, True) == (
        "Couverture du nouveau code aucune ligne à mesurer · seuil 80 % · ✓"
    )
    assert parsers.diff_coverage_text(0, False).endswith("✗")


# ------------------------------------------------------------------ parse_diff_cover_json
@given(
    st.one_of(
        st.integers(min_value=0, max_value=100),
        st.floats(min_value=0, max_value=100, allow_nan=False),
    )
)
@settings(max_examples=200)
def test_le_seuil_porte_sur_la_valeur_tronquee(percent: float) -> None:
    summary = parsers.parse_diff_cover_json(_diff_json(10, percent, {}), Path("."))[0]
    value = int(percent)
    passed = value >= parsers.QUALITY_GATE_THRESHOLD
    assert summary.rule_id == "diff_coverage"
    assert summary.severity == ("info" if passed else "error")
    assert summary.message_text == parsers.diff_coverage_text(value, passed)


@pytest.mark.parametrize(
    ("percent", "ok"),
    [(79, False), (79.0, False), (79.99, False), (80, True), (80.0, True), (80.4, True), (100, True)],
)
def test_bornes_du_seuil(percent: float, ok: bool) -> None:
    summary = parsers.parse_diff_cover_json(_diff_json(10, percent, {}), Path("."))[0]
    assert summary.message_text.endswith("✓" if ok else "✗")
    assert summary.severity == ("info" if ok else "error")


def test_diff_vide_ignore_le_pourcentage_et_reste_info() -> None:
    for percent in (None, 0, "n/a"):
        (summary,) = parsers.parse_diff_cover_json(_diff_json(0, percent, {}), Path("."))
        assert (summary.rule_id, summary.severity) == ("diff_coverage_none", "info")
        assert summary.path is None and summary.line is None


def test_pourcentage_absent_ou_non_numerique_avec_lignes_mesurees_est_refuse() -> None:
    for percent in (None, "80", [80], {}):
        with pytest.raises(ValueError, match="inattendue"):
            parsers.parse_diff_cover_json(_diff_json(3, percent, {}), Path("."))


@pytest.mark.parametrize(
    "text",
    [
        _diff_json(None, 50, {}),
        _diff_json("3", 50, {}),
        _diff_json(3.0, 50, {}),
        _diff_json(3, 50, []),
        _diff_json(3, 50, None),
        json.dumps({"total_percent_covered": 50}),
        "null",
        "42",
    ],
)
def test_forme_inattendue_leve_value_error(text: str) -> None:
    with pytest.raises(ValueError):
        parsers.parse_diff_cover_json(text, Path("."))


def test_un_constat_par_fichier_avec_pluriel_ligne_et_gravite(tmp_path: Path) -> None:
    stats = {
        "src/a.py": {"violation_lines": [9, 4, 5, 6], "covered_lines": [1]},
        "src/b.py": {"violation_lines": [12]},
        "src/c.py": {"violation_lines": []},
        "src/d.py": {"violation_lines": None},
        "src/e.py": "pas un dict",
        "src/f.py": {"violation_lines": ["x", 3.5, None]},
    }
    found = parsers.parse_diff_cover_json(_diff_json(6, 16, stats), tmp_path)
    assert found[0].message_text == "Couverture du nouveau code 16 % · seuil 80 % · ✗"
    a, b = found[1:]
    assert len(found) == 3
    assert (a.rule_id, a.severity, a.path, a.line) == ("uncovered_lines", "error", "src/a.py", 4)
    assert a.message_text == "4 lignes du nouveau code sans test : 4-6, 9"
    assert (b.path, b.line) == ("src/b.py", 12)
    assert b.message_text == "1 ligne du nouveau code sans test : 12"


def test_constats_de_fichier_en_info_quand_le_seuil_est_atteint(tmp_path: Path) -> None:
    stats = {"src/a.py": {"violation_lines": [2]}}
    found = parsers.parse_diff_cover_json(_diff_json(10, 90, stats), tmp_path)
    assert [f.severity for f in found] == ["info", "info"]
    assert found[1].rule_id == "uncovered_lines"


def test_ligne_zero_n_est_pas_une_ligne_de_fichier(tmp_path: Path) -> None:
    stats = {"src/a.py": {"violation_lines": [0, 3]}}
    found = parsers.parse_diff_cover_json(_diff_json(2, 0, stats), tmp_path)
    assert found[1].line is None
    assert found[1].message_text == "2 lignes du nouveau code sans test : 0, 3"


def test_chemin_absolu_dans_l_arbre_devient_relatif(tmp_path: Path) -> None:
    target = tmp_path / "src" / "a.py"
    stats = {str(target): {"violation_lines": [1]}}
    found = parsers.parse_diff_cover_json(_diff_json(1, 0, stats), tmp_path)
    assert found[1].path == "src/a.py"


# ------------------------------------------------------------------ parse_coverage_json
def _coverage(percent: Any, files: Any = None) -> str:
    return json.dumps(
        {"files": {"a.py": {}} if files is None else files, "totals": {"percent_covered": percent}}
    )


@given(st.floats(min_value=0.001, max_value=100, allow_nan=False))
def test_couverture_totale_tronquee(percent: float) -> None:
    (total,) = parsers.parse_coverage_json(_coverage(percent), Path("."))
    assert total.message_text == f"Couverture de l'ensemble du dépôt : {int(percent)} % (information)."
    assert (total.rule_id, total.severity) == ("total_coverage", "info")


def test_couverture_totale_exemples() -> None:
    (total,) = parsers.parse_coverage_json(_coverage("87.6"), Path("."))
    assert "87 %" in total.message_text
    (zero,) = parsers.parse_coverage_json(_coverage(0), Path("."))  # fichiers présents : mesure valide
    assert "0 %" in zero.message_text


@pytest.mark.parametrize(
    "text",
    [
        "",
        "pas du json",
        "[]",
        "{}",
        json.dumps({"files": {}, "totals": {"percent_covered": 50}}),
        json.dumps({"files": [1], "totals": {"percent_covered": 50}}),
        json.dumps({"files": {"a": {}}, "totals": []}),
        json.dumps({"files": {"a": {}}, "totals": {}}),
        json.dumps({"files": {"a": {}}, "totals": {"percent_covered": None}}),
        json.dumps({"files": {"a": {}}, "totals": {"percent_covered": "abc"}}),
    ],
)
def test_couverture_illisible_est_refusee(text: str) -> None:
    with pytest.raises(ValueError):
        parsers.parse_coverage_json(text, Path("."))


def test_les_lecteurs_sont_enregistres() -> None:
    assert parsers.PARSERS["diff_cover_json"] is parsers.parse_diff_cover_json
    assert parsers.PARSERS["coverage_json"] is parsers.parse_coverage_json
    assert parsers.QUALITY_GATE_THRESHOLD == 80


# ------------------------------------------------------------------ replace_in_file
def _apply(root: Path, path: str, old: str, new: str) -> str:
    ctx = SimpleNamespace(layout=SimpleNamespace(repo=root))
    args = replace_in_file.Args(op="replace_in_file", path=path, old=old, new=new)
    return replace_in_file.apply(args, ctx)  # type: ignore[arg-type]


@given(
    prefix=st.text(alphabet="abc \n", max_size=20),
    suffix=st.text(alphabet="abc \n", max_size=20),
    new=st.text(alphabet="xyz \n", max_size=20),
)
@settings(max_examples=60, deadline=None)
def test_remplace_exactement_une_occurrence(
    tmp_path_factory: pytest.TempPathFactory, prefix: str, suffix: str, new: str
) -> None:
    root = tmp_path_factory.mktemp("rif")
    (root / "f.txt").write_bytes(f"{prefix}#MARK#{suffix}".encode())
    _apply(root, "f.txt", "#MARK#", new)
    assert (root / "f.txt").read_bytes().decode() == f"{prefix}{new}{suffix}"


def test_retour_de_l_op_et_fins_de_ligne(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_bytes(b"a\r\nb\r\nc\r\n")
    element = _apply(tmp_path, "f.txt", "b\r\n", "B\n")
    assert element.endswith("f.txt") and "worktree" in element
    assert (tmp_path / "f.txt").read_bytes() == b"a\nB\nc\n"


def test_remplacement_par_le_vide_et_comptage_dans_le_message(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_text("x-y-x", "utf-8")
    with pytest.raises(SetupError, match="2 fois"):
        _apply(tmp_path, "f.txt", "x", "z")
    with pytest.raises(SetupError, match="0 fois"):
        _apply(tmp_path, "f.txt", "q", "z")
    assert (tmp_path / "f.txt").read_text("utf-8") == "x-y-x"  # rien d'écrit en cas d'échec
    _apply(tmp_path, "f.txt", "-y-", "")
    assert (tmp_path / "f.txt").read_text("utf-8") == "xx"


def test_fichier_absent_ou_illisible(tmp_path: Path) -> None:
    with pytest.raises(SetupError, match="n'a pas pu être lu"):
        _apply(tmp_path, "absent.txt", "a", "b")
    (tmp_path / "bin.dat").write_bytes(b"\xff\xfe\x00")
    with pytest.raises(SetupError, match="n'a pas pu être lu"):
        _apply(tmp_path, "bin.dat", "a", "b")


@pytest.mark.parametrize("bad", ["../x", "/abs/x", "a/../../x", "C:\\x", ".git/config"])
def test_chemins_refuses_par_les_arguments_ou_le_confinement(tmp_path: Path, bad: str) -> None:
    (tmp_path / "x").write_text("a", "utf-8")
    with pytest.raises((ValueError, SetupError, Exception)) as info:
        _apply(tmp_path, bad, "a", "b")
    assert not isinstance(info.value, (KeyboardInterrupt,))
    assert (tmp_path / "x").read_text("utf-8") == "a"


def test_old_vide_est_refuse() -> None:
    with pytest.raises(ValueError, match="vide"):
        replace_in_file.Args(op="replace_in_file", path="f.txt", old="", new="x")


# ------------------------------------------------------------------ with_tools_on_path
def _fake_resolve(mapping: dict[str, Path | None]):  # noqa: ANN202
    def resolve(tool_id: str, settings: Settings, venv: Path | None = None) -> SimpleNamespace:
        path = mapping.get(tool_id)
        return SimpleNamespace(ok=path is not None, path=path, reason="absent", state="missing")

    return resolve


def test_les_dossiers_des_outils_passent_en_tete_du_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        toolrun,
        "resolve",
        _fake_resolve({"git": tmp_path / "g" / "git", "uv": tmp_path / "u" / "uv", "x": None}),
    )
    env = {"PATH": "/orig", "OTHER": "1"}
    out = toolrun.with_tools_on_path(env, ("git", "x", "uv"), SETTINGS)
    assert out["PATH"] == os.pathsep.join([str(tmp_path / "g"), str(tmp_path / "u"), "/orig"])
    assert out["OTHER"] == "1"
    assert env == {"PATH": "/orig", "OTHER": "1"}  # l'original n'est pas modifié


def test_path_sans_outil_resolu_reste_inchange_sans_separateur_final(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(toolrun, "resolve", _fake_resolve({}))
    assert toolrun.with_tools_on_path({"PATH": "/orig"}, ("git",), SETTINGS)["PATH"] == "/orig"
    assert toolrun.with_tools_on_path({}, ("git",), SETTINGS) == {"PATH": ""}


def test_la_casse_de_la_cle_path_est_respectee(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(toolrun, "resolve", _fake_resolve({"git": tmp_path / "g" / "git"}))
    out = toolrun.with_tools_on_path({"Path": "/orig"}, ("git",), SETTINGS)
    assert set(out) == {"Path"}
    assert out["Path"] == os.pathsep.join([str(tmp_path / "g"), "/orig"])


# ------------------------------------------------------------------ spawn_tool : diff-cover
def test_diff_cover_recoit_le_git_du_registre_dans_son_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    seen: dict[str, Any] = {}
    paths = {
        "diff-cover": tmp_path / "dc",
        "git": tmp_path / "gitdir" / "git",
        "pytest": tmp_path / "pt",
    }
    monkeypatch.setattr(toolrun, "resolve", _fake_resolve(paths))
    monkeypatch.setattr(
        toolrun.procs, "spawn", lambda argv, **kw: seen.update(argv=argv, **kw) or "handle"
    )
    for tool in ("diff-cover", "pytest"):
        seen.clear()
        toolrun.spawn_tool(tool, ["a"], cwd=tmp_path, venv=tmp_path, timeout=5, settings=SETTINGS)
        head = seen["env"]["PATH"].split(os.pathsep)[0]
        assert (head == str(tmp_path / "gitdir")) is (tool == "diff-cover")
        assert seen["argv"] == [paths[tool], "a"]


def test_outil_indisponible_leve_tool_unavailable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(toolrun, "resolve", _fake_resolve({}))
    with pytest.raises(toolrun.ToolUnavailable):
        toolrun.spawn_tool("diff-cover", [], cwd=tmp_path, venv=tmp_path, timeout=1)


# ------------------------------------------------------------------ run_job (outils simulés)
class _Fake:
    """Enchaîne des sorties prédéfinies, une par lancement ; garde argv et outil lancés."""

    def __init__(self, outputs: list[dict[str, Any]]) -> None:
        self.outputs = list(outputs)
        self.launched: list[tuple[str, list[str]]] = []

    def spawn(self, tool_id: str, args: Any, **kw: Any) -> SimpleNamespace:
        self.launched.append((tool_id, list(args)))
        return SimpleNamespace(interrupted=False, out=self.outputs.pop(0))

    def collect(self, handle: SimpleNamespace) -> SimpleNamespace:
        base = {"stdout": "", "stderr": "", "returncode": 0, "timed_out": False}
        return SimpleNamespace(**{**base, **handle.out})


def _run_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, outputs: list[dict[str, Any]]
) -> tuple[ci.JobResult, _Fake]:
    fake = _Fake(outputs)
    monkeypatch.setattr(toolrun, "spawn_tool", fake.spawn)
    monkeypatch.setattr(toolrun, "collect", fake.collect)
    tree = tmp_path / "tree"
    tree.mkdir(parents=True)
    job = PIPELINE.job("quality_gate")
    assert job is not None
    result = ci.run_job(
        job,
        tree=tree,
        venv=None,
        tokens={"repo": str(tree), "base_sha": "b" * 40},
        settings=Settings(data_dir=tmp_path / "data"),
    )
    return result, fake


def test_pytest_en_echec_arrete_le_job_avant_diff_cover(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result, fake = _run_gate(
        monkeypatch, tmp_path, [{"stdout": "FAILED x", "stderr": "boom", "returncode": 1}]
    )
    assert [t for t, _ in fake.launched] == ["pytest"]
    assert result.state == "failure"
    assert result.output == "FAILED xboom"
    (finding,) = result.findings
    assert finding.rule_id == ci.BEFORE_FAILED_RULE
    assert finding.message_text == (
        "pytest a échoué (code 1) : diff-cover n'a rien à mesurer tant que pytest échoue."
    )


def test_pytest_hors_delai_donne_une_erreur_de_l_outil(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result, fake = _run_gate(
        monkeypatch, tmp_path, [{"stdout": "partiel", "returncode": None, "timed_out": True}]
    )
    assert len(fake.launched) == 1
    assert result.state == "error" and result.output == "partiel"
    assert result.findings[0].rule_id == ci.TOOL_ERROR_RULE
    assert "n'a pas fini en" in result.findings[0].message_text


def test_sortie_de_pytest_precede_celle_de_diff_cover_et_les_constats_sont_lus(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    diff = _diff_json(5, 20, {"src/a.py": {"violation_lines": [2, 3]}})
    cov = _coverage(55.5)
    result, fake = _run_gate(
        monkeypatch,
        tmp_path,
        [
            {"stdout": "PYTEST|"},
            {"stdout": "DIFF", "stderr": "|ERR", "returncode": 1},
            {"stdout": diff},
            {"stdout": cov},
        ],
    )
    assert [t for t, _ in fake.launched] == ["pytest", "diff-cover", "diff-cover", "coverage"]
    assert result.state == "failure"
    assert result.output == "PYTEST|DIFF|ERR"
    assert [f.rule_id for f in result.findings] == [
        "diff_coverage",
        "uncovered_lines",
        "total_coverage",
    ]
    assert result.findings[0].message_text == "Couverture du nouveau code 20 % · seuil 80 % · ✗"
    assert "55 %" in result.findings[2].message_text
    # Le seuil et la base vont à diff-cover tels que le job les déclare.
    human = fake.launched[1][1]
    assert "--fail-under=80" in human and f"--compare-branch={'b' * 40}" in human


def test_vert_lit_quand_meme_les_constats_et_un_code_inattendu_est_une_erreur(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ok, _ = _run_gate(
        monkeypatch,
        tmp_path / "ok",
        [{}, {}, {"stdout": _diff_json(0, None, {})}, {"stdout": _coverage(90)}],
    )
    assert ok.state == "success"
    assert [f.rule_id for f in ok.findings] == ["diff_coverage_none", "total_coverage"]
    bad, fake = _run_gate(monkeypatch, tmp_path / "bad", [{}, {"returncode": 2}])
    assert bad.state == "error" and len(fake.launched) == 2
    assert "code 2" in bad.findings[0].message_text


def test_rapport_illisible_en_echec_laisse_un_constat_sans_detail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result, _ = _run_gate(
        monkeypatch,
        tmp_path,
        [{}, {"returncode": 1}, {"stdout": "pas du json"}, {"stdout": _coverage(10)}],
    )
    assert result.state == "failure"
    assert [f.rule_id for f in result.findings] == [ci.NO_DETAIL_RULE, "total_coverage"]
