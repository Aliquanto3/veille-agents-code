"""Renfort de la story 8.4 : lecteurs de couverture (propriétés et bornes), commandes `before`
de `ci.run_job`, `toolrun.with_tools_on_path` et op `replace_in_file`."""

from __future__ import annotations

import json
import os
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

TREE = Path(__file__).resolve().parent


def _ref_ranges(lines: list[int]) -> str:
    out: list[str] = []
    values = sorted(set(lines))
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[j + 1] == values[j] + 1:
            j += 1
        out.append(str(values[i]) if i == j else f"{values[i]}-{values[j]}")
        i = j + 1
    return ", ".join(out)


def _payload(total: Any, percent: Any, stats: Any) -> str:
    return json.dumps(
        {"total_num_lines": total, "total_percent_covered": percent, "src_stats": stats}
    )


# ------------------------------------------------------------------ _ranges
def test_ranges_exemples_exacts() -> None:
    assert parsers._ranges([59, 60, 61, 65]) == "59-61, 65"
    assert parsers._ranges([]) == ""
    assert parsers._ranges([7]) == "7"
    assert parsers._ranges([3, 1, 2, 2]) == "1-3"
    assert parsers._ranges([1, 3, 5]) == "1, 3, 5"
    assert parsers._ranges([4, 5]) == "4-5"


@given(st.lists(st.integers(min_value=1, max_value=60), max_size=30))
def test_ranges_correspond_a_la_reference_et_couvre_les_memes_lignes(lines: list[int]) -> None:
    text = parsers._ranges(lines)
    assert text == _ref_ranges(lines)
    covered: set[int] = set()
    for part in filter(None, text.split(", ")):
        low, _, high = part.partition("-")
        covered |= set(range(int(low), int(high or low) + 1))
    assert covered == set(lines)


# ------------------------------------------------------------------ diff_coverage_text
@pytest.mark.parametrize(
    ("percent", "passed", "expected"),
    [
        (0, False, "Couverture du nouveau code 0 % · seuil 80 % · ✗"),
        (100, True, "Couverture du nouveau code 100 % · seuil 80 % · ✓"),
        (None, True, "Couverture du nouveau code aucune ligne à mesurer · seuil 80 % · ✓"),
    ],
)
def test_diff_coverage_text(percent: int | None, passed: bool, expected: str) -> None:
    assert parsers.diff_coverage_text(percent, passed) == expected


# ------------------------------------------------------------------ parse_diff_cover_json
@given(
    total=st.integers(min_value=1, max_value=1000),
    percent=st.floats(min_value=0, max_value=100, allow_nan=False),
)
def test_diff_cover_seuil_exact_et_troncature(total: int, percent: float) -> None:
    (summary,) = parsers.parse_diff_cover_json(_payload(total, percent, {}), TREE)
    value = int(percent)
    passed = value >= 80
    assert summary.rule_id == "diff_coverage"
    assert summary.severity == ("info" if passed else "error")
    assert summary.message_text == parsers.diff_coverage_text(value, passed)


@pytest.mark.parametrize(
    ("percent", "severity", "mark"),
    [(79, "error", "✗"), (79.99, "error", "✗"), (80, "info", "✓"), (80.0, "info", "✓")],
)
def test_diff_cover_bornes_du_seuil(percent: float, severity: str, mark: str) -> None:
    (summary,) = parsers.parse_diff_cover_json(_payload(10, percent, {}), TREE)
    assert summary.severity == severity
    assert summary.message_text.endswith(f"seuil 80 % · {mark}")


def test_diff_cover_sans_ligne_mesuree_ignore_le_pourcentage() -> None:
    (summary,) = parsers.parse_diff_cover_json(_payload(0, None, {}), TREE)
    assert (summary.rule_id, summary.severity) == ("diff_coverage_none", "info")
    (other,) = parsers.parse_diff_cover_json(_payload(0, 3, {}), TREE)
    assert other.message_text == summary.message_text


@given(
    missing=st.lists(st.integers(min_value=1, max_value=500), min_size=1, max_size=20),
    passed=st.booleans(),
)
def test_diff_cover_un_constat_par_fichier_non_couvert(missing: list[int], passed: bool) -> None:
    percent = 90 if passed else 10
    stats = {"src/a.py": {"violation_lines": missing}, "src/ok.py": {"violation_lines": []}}
    summary, item = parsers.parse_diff_cover_json(_payload(10, percent, stats), TREE)
    assert summary.severity == ("info" if passed else "error")
    assert item.rule_id == "uncovered_lines"
    assert item.severity == ("info" if passed else "error")
    assert item.path == "src/a.py"
    assert item.line == min(missing)
    count = len(missing)
    noun = "ligne" if count == 1 else "lignes"
    assert item.message_text == (
        f"{count} {noun} du nouveau code sans test : {_ref_ranges(missing)}"
    )


def test_diff_cover_singulier_et_filtrage_des_entrees_invalides() -> None:
    stats = {
        "src/a.py": {"violation_lines": [4]},
        "src/b.py": "pas un dict",
        "src/c.py": {"violation_lines": ["x", None, 2.5]},
        "src/d.py": {},
        "src/e.py": {"violation_lines": None},
    }
    found = parsers.parse_diff_cover_json(_payload(5, 20, stats), TREE)
    assert [f.path for f in found[1:]] == ["src/a.py"]
    assert found[1].message_text == "1 ligne du nouveau code sans test : 4"
    assert found[1].line == 4


@pytest.mark.parametrize(
    "bad",
    [
        _payload("5", 50, {}),
        _payload(None, 50, {}),
        _payload(5, 50, []),
        _payload(5, 50, None),
        _payload(5, None, {}),
        _payload(5, "80", {}),
        '"texte"',
        "null",
    ],
)
def test_diff_cover_refuse_une_forme_inattendue(bad: str) -> None:
    with pytest.raises(ValueError):
        parsers.parse_diff_cover_json(bad, TREE)


def test_diff_cover_messages_d_erreur() -> None:
    with pytest.raises(ValueError, match="illisible"):
        parsers.parse_diff_cover_json("{pas json", TREE)
    with pytest.raises(ValueError, match="inattendue"):
        parsers.parse_diff_cover_json("[]", TREE)


# ------------------------------------------------------------------ parse_coverage_json
@given(st.floats(min_value=0, max_value=100, allow_nan=False))
def test_coverage_json_tronque_le_pourcentage(percent: float) -> None:
    text = json.dumps({"files": {"a.py": {}}, "totals": {"percent_covered": percent}})
    (total,) = parsers.parse_coverage_json(text, TREE)
    assert total.severity == "info" and total.rule_id == "total_coverage"
    assert total.message_text == (
        f"Couverture de l'ensemble du dépôt : {int(percent)} % (information)."
    )


def test_coverage_json_accepte_un_pourcentage_texte_et_refuse_le_reste() -> None:
    ok = json.dumps({"files": {"a.py": {}}, "totals": {"percent_covered": "42.9"}})
    assert "42 %" in parsers.parse_coverage_json(ok, TREE)[0].message_text
    for totals in ({}, {"percent_covered": None}, {"percent_covered": "abc"}, []):
        text = json.dumps({"files": {"a.py": {}}, "totals": totals})
        with pytest.raises(ValueError):
            parsers.parse_coverage_json(text, TREE)
    with pytest.raises(ValueError, match="vide"):
        parsers.parse_coverage_json(json.dumps({"files": [], "totals": {}}), TREE)


def test_les_lecteurs_de_couverture_sont_enregistres() -> None:
    assert parsers.PARSERS["diff_cover_json"] is parsers.parse_diff_cover_json
    assert parsers.PARSERS["coverage_json"] is parsers.parse_coverage_json


# ------------------------------------------------------------------ Step et jetons
def test_step_refuse_le_jeton_report_et_les_jetons_inconnus() -> None:
    assert ci.Step(tool="pytest", argv=["--x={config}/a", "{reports}/b"]).tool == "pytest"
    for bad in (["{report}"], ["{inconnu}"]):
        with pytest.raises(ValueError):
            ci.Step(tool="pytest", argv=bad)
    with pytest.raises(ValueError):
        ci.Step(tool="", argv=["x"])
    with pytest.raises(ValueError):
        ci.Step(tool="pytest", argv=[])
    assert ci.MachineRun(argv=["{report}"], parse="coverage_json").tool is None


def test_expand_jeton_vide_ou_absent_leve_keyerror() -> None:
    assert ci.expand(["a={x}-{x}"], {"x": "1"}) == ["a=1-1"]
    with pytest.raises(KeyError):
        ci.expand(["{x}"], {"x": ""})
    with pytest.raises(KeyError):
        ci.expand(["{y}"], {})


# ------------------------------------------------------------------ run_job et `before`
class _Fake:
    def __init__(self, outcomes: list[dict[str, Any]]) -> None:
        self.outcomes = outcomes
        self.calls: list[tuple[str, list[str]]] = []

    def spawn(self, tool: str, argv: list[str], **_: Any) -> Any:
        self.calls.append((tool, argv))
        return SimpleNamespace(interrupted=False, outcome=self.outcomes[len(self.calls) - 1])

    @staticmethod
    def collect(handle: Any) -> Any:
        base = {"stdout": "", "stderr": "", "returncode": 0, "timed_out": False}
        return SimpleNamespace(**{**base, **handle.outcome})


def _job() -> ci.Job:
    return ci.Job(
        job_id="quality_gate",
        label_text="QG",
        tool="diff-cover",
        before=[ci.Step(tool="pytest", argv=["--cfg={config}/c.ini", "--o={reports}/x.xml"])],
        human=["{reports}/coverage.xml", "--compare-branch={base_sha}"],
    )


def _patch(monkeypatch: pytest.MonkeyPatch, outcomes: list[dict[str, Any]]) -> _Fake:
    fake = _Fake(outcomes)
    monkeypatch.setattr(toolrun, "spawn_tool", fake.spawn)
    monkeypatch.setattr(toolrun, "collect", fake.collect)
    return fake


def _run(tmp_path: Path, job: ci.Job, tokens: dict[str, str] | None = None) -> ci.JobResult:
    tree = tmp_path / "tree"
    tree.mkdir(exist_ok=True)
    return ci.run_job(
        job,
        tree=tree,
        venv=None,
        tokens={"base_sha": "abc"} if tokens is None else tokens,
        settings=Settings(data_dir=tmp_path / "data"),
    )


def test_before_en_echec_arrete_le_job_avec_le_constat_before_failed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake = _patch(monkeypatch, [{"returncode": 3, "stdout": "OUT", "stderr": "ERR"}])
    result = _run(tmp_path, _job())
    assert len(fake.calls) == 1  # diff-cover n'est pas lancé
    assert result.state == "failure"
    assert result.output == "OUTERR"
    (finding,) = result.findings
    assert finding.rule_id == ci.BEFORE_FAILED_RULE and finding.severity == "error"
    assert finding.message_text == (
        "pytest a échoué (code 3) : diff-cover n'a rien à mesurer tant que pytest échoue."
    )


def test_before_reussi_puis_sortie_humaine_concatenee(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake = _patch(
        monkeypatch,
        [{"stdout": "avant|"}, {"stdout": "apres", "stderr": "|e", "returncode": 1}],
    )
    result = _run(tmp_path, _job())
    assert [t for t, _ in fake.calls] == ["pytest", "diff-cover"]
    assert result.state == "failure" and result.output == "avant|apres|e"
    reports = str(ci.reports_dir(tmp_path / "tree"))
    cfg = str(Settings(data_dir=tmp_path / "data").ci_config_path())
    assert fake.calls[0][1] == [f"--cfg={cfg}/c.ini", f"--o={reports}/x.xml"]
    assert fake.calls[1][1] == [f"{reports}/coverage.xml", "--compare-branch=abc"]


def test_before_sans_fin_est_une_erreur_de_l_outil(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    for outcome in ({"timed_out": True, "returncode": 0}, {"returncode": None}):
        fake = _patch(monkeypatch, [{**outcome, "stdout": "partiel"}])
        result = _run(tmp_path, _job())
        assert len(fake.calls) == 1
        assert result.state == "error" and result.output == "partiel"
        (finding,) = result.findings
        assert finding.rule_id == ci.TOOL_ERROR_RULE
        assert finding.message_text.startswith("diff-cover n'a pas fini en ")
        assert finding.message_text.endswith(f" s et a été arrêté. {ci.NOT_YOUR_CODE}")


def test_jeton_manquant_est_une_erreur_sans_lancer_d_outil(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake = _patch(monkeypatch, [])
    result = _run(tmp_path, _job(), tokens={})
    assert fake.calls == [] and result.state == "error"
    assert "base_sha" in result.findings[0].message_text


def test_outil_before_qui_ne_demarre_pas_est_une_erreur(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def boom(*_: Any, **__: Any) -> Any:
        raise OSError("non")

    monkeypatch.setattr(toolrun, "spawn_tool", boom)
    result = _run(tmp_path, _job())
    assert result.state == "error"
    assert "n'a pas démarré (OSError)" in result.findings[0].message_text


# ------------------------------------------------------------------ with_tools_on_path
def test_with_tools_on_path_met_les_dossiers_en_tete(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def resolve(tool_id: str, _settings: Settings) -> Any:
        if tool_id == "absent":
            return SimpleNamespace(ok=False, path=None)
        return SimpleNamespace(ok=True, path=tmp_path / tool_id / "bin")

    monkeypatch.setattr(toolrun, "resolve", resolve)
    env = {"Path": "ancien", "X": "1"}
    out = toolrun.with_tools_on_path(env, ("git", "absent", "uv"), Settings())
    assert out["Path"] == os.pathsep.join([str(tmp_path / "git"), str(tmp_path / "uv"), "ancien"])
    assert out["X"] == "1" and env["Path"] == "ancien"  # l'original n'est pas modifié
    assert toolrun.with_tools_on_path({}, ("absent",), Settings()) == {"PATH": ""}
    assert toolrun.with_tools_on_path({}, ("git",), Settings()) == {"PATH": str(tmp_path / "git")}


# ------------------------------------------------------------------ replace_in_file
def _apply(repo: Path, path: str, old: str, new: str) -> str:
    ctx = SimpleNamespace(layout=SimpleNamespace(repo=repo))
    return replace_in_file.apply(
        replace_in_file.Args(op="replace_in_file", path=path, old=old, new=new),
        ctx,  # type: ignore[arg-type]
    )


def test_replace_in_file_normalise_les_fins_de_ligne_et_rend_l_identifiant(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_bytes(b"un\r\ndeux\r\ntrois\r\n")
    ident = _apply(tmp_path, "f.txt", "un\r\ndeux\n", "X\n")
    assert (tmp_path / "f.txt").read_bytes().replace(b"\r\n", b"\n") == b"X\ntrois\n"
    assert "f.txt" in ident


def test_replace_in_file_messages_et_fichier_intact(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_text("a-a-b", "utf-8")
    with pytest.raises(SetupError, match="2 fois"):
        _apply(tmp_path, "f.txt", "a", "z")
    with pytest.raises(SetupError, match="0 fois"):
        _apply(tmp_path, "f.txt", "q", "z")
    assert (tmp_path / "f.txt").read_text("utf-8") == "a-a-b"
    with pytest.raises(SetupError, match="n'a pas pu être lu"):
        _apply(tmp_path, "inexistant.txt", "a", "z")
    (tmp_path / "bin.dat").write_bytes(b"\xff\xfe\x00")
    with pytest.raises(SetupError, match="n'a pas pu être lu"):
        _apply(tmp_path, "bin.dat", "a", "z")


@pytest.mark.parametrize("path", ["../x", "/abs", "a/../../x", ".git/config"])
def test_replace_in_file_refuse_les_chemins_hors_de_l_arbre(path: str) -> None:
    with pytest.raises(ValueError):
        replace_in_file.Args(op="replace_in_file", path=path, old="a", new="b")


def test_replace_in_file_refuse_un_texte_vide() -> None:
    with pytest.raises(ValueError, match="vide"):
        replace_in_file.Args(op="replace_in_file", path="f", old="", new="b")


@settings(max_examples=60, deadline=None)
@given(
    prefix=st.text(alphabet="abc\n", max_size=20),
    suffix=st.text(alphabet="abc\n", max_size=20),
    new=st.text(alphabet="xyz\n", max_size=10),
)
def test_replace_in_file_ne_touche_que_l_occurrence_unique(
    tmp_path_factory: pytest.TempPathFactory, prefix: str, suffix: str, new: str
) -> None:
    repo = tmp_path_factory.mktemp("r")
    (repo / "f.txt").write_bytes((prefix + "#" + suffix).encode())
    _apply(repo, "f.txt", "#", new)
    assert (repo / "f.txt").read_bytes().decode().replace("\r\n", "\n") == prefix + new + suffix
