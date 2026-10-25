"""Renfort de la story 8.4 : lecteurs de couverture, op `replace_in_file`, PATH de diff-cover."""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from wavedevsecops import toolrun
from wavedevsecops.ci import findings as parsers
from wavedevsecops.scenarios import SetupError
from wavedevsecops.scenarios.ops import replace_in_file


def _payload(total: object, percent: object, stats: object) -> str:
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
        ([4, 4, 4], "4"),
        ([1, 3, 5], "1, 3, 5"),
        ([1, 2, 10, 11, 20], "1-2, 10-11, 20"),
    ],
)
def test_ranges_regroupe_les_lignes_consecutives(lines: list[int], expected: str) -> None:
    assert parsers._ranges(lines) == expected


# ------------------------------------------------------------------ diff_coverage_text
def test_texte_du_constat_de_couverture() -> None:
    assert parsers.diff_coverage_text(80, True) == "Couverture du nouveau code 80 % · seuil 80 % · ✓"
    assert parsers.diff_coverage_text(0, False) == "Couverture du nouveau code 0 % · seuil 80 % · ✗"
    assert parsers.diff_coverage_text(None, True) == (
        "Couverture du nouveau code aucune ligne à mesurer · seuil 80 % · ✓"
    )


def test_constantes_de_regles() -> None:
    assert parsers.QUALITY_GATE_THRESHOLD == 80
    assert parsers.DIFF_COVERAGE_RULE == "diff_coverage"
    assert parsers.NO_DIFF_RULE == "diff_coverage_none"
    assert parsers.UNCOVERED_RULE == "uncovered_lines"
    assert parsers.TOTAL_COVERAGE_RULE == "total_coverage"
    assert parsers.PARSERS["diff_cover_json"] is parsers.parse_diff_cover_json
    assert parsers.PARSERS["coverage_json"] is parsers.parse_coverage_json


# ------------------------------------------------------------------ parse_diff_cover_json
@pytest.mark.parametrize(
    ("percent", "shown", "ok"),
    [
        (0, 0, False),
        (79, 79, False),
        (79.9, 79, False),
        (80, 80, True),
        (80.4, 80, True),
        (100, 100, True),
    ],
)
def test_borne_du_seuil_et_troncature(tmp_path: Path, percent: float, shown: int, ok: bool) -> None:
    summary = parsers.parse_diff_cover_json(_payload(10, percent, {}), tmp_path)[0]
    assert summary.rule_id == "diff_coverage"
    assert summary.severity == ("info" if ok else "error")
    assert summary.message_text == (
        f"Couverture du nouveau code {shown} % · seuil 80 % · {'✓' if ok else '✗'}"
    )


def test_diff_vide_est_info_meme_avec_un_pourcentage_bas(tmp_path: Path) -> None:
    (summary,) = parsers.parse_diff_cover_json(_payload(0, 0, {}), tmp_path)
    assert (summary.rule_id, summary.severity) == ("diff_coverage_none", "info")
    # total = 0 : un pourcentage absent ou illisible n'est pas lu.
    (again,) = parsers.parse_diff_cover_json(_payload(0, None, {}), tmp_path)
    assert again.rule_id == "diff_coverage_none"


def test_pourcentage_absent_ou_texte_refuse_quand_des_lignes_sont_mesurees(tmp_path: Path) -> None:
    for percent in (None, "80", [80]):
        with pytest.raises(ValueError, match="inattendue"):
            parsers.parse_diff_cover_json(_payload(3, percent, {}), tmp_path)


@pytest.mark.parametrize(
    "text",
    [
        _payload("3", 50, {}),
        _payload(None, 50, {}),
        _payload(3.0, 50, {}),
        _payload(3, 50, []),
        _payload(3, 50, None),
        json.dumps({"total_num_lines": 3, "total_percent_covered": 50}),
    ],
)
def test_structure_inattendue_refusee(tmp_path: Path, text: str) -> None:
    with pytest.raises(ValueError, match="diff-cover"):
        parsers.parse_diff_cover_json(text, tmp_path)


def test_texte_illisible_ou_pas_un_objet(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="illisible"):
        parsers.parse_diff_cover_json("{", tmp_path)
    with pytest.raises(ValueError, match="inattendue"):
        parsers.parse_diff_cover_json("[1]", tmp_path)


def test_un_constat_par_fichier_au_singulier_et_au_pluriel(tmp_path: Path) -> None:
    stats = {
        "src/b.py": {"violation_lines": [9]},
        "src/a.py": {"violation_lines": [12, 4, 5, 5]},
    }
    found = parsers.parse_diff_cover_json(_payload(10, 10, stats), tmp_path)
    assert [f.rule_id for f in found] == ["diff_coverage", "uncovered_lines", "uncovered_lines"]
    single, plural = found[1], found[2]
    assert (single.path, single.line, single.severity) == ("src/b.py", 9, "error")
    assert single.message_text == "1 ligne du nouveau code sans test : 9"
    # Doublons comptés dans « n lignes », fusionnés dans la plage ; la ligne est la plus petite.
    assert (plural.path, plural.line) == ("src/a.py", 4)
    assert plural.message_text == "4 lignes du nouveau code sans test : 4-5, 12"


def test_au_vert_les_lignes_non_couvertes_sont_informatives(tmp_path: Path) -> None:
    stats = {"src/a.py": {"violation_lines": [7]}}
    found = parsers.parse_diff_cover_json(_payload(10, 90, stats), tmp_path)
    assert found[0].severity == "info"
    assert found[1].severity == "info"


def test_entrees_de_fichier_sans_ligne_ou_mal_formees_sont_ignorees(tmp_path: Path) -> None:
    stats = {
        "a.py": {"violation_lines": []},
        "b.py": {"violation_lines": None},
        "c.py": {},
        "d.py": "texte",
        "e.py": {"violation_lines": ["3", None, 2.5, 6]},
    }
    found = parsers.parse_diff_cover_json(_payload(5, 20, stats), tmp_path)
    assert [f.path for f in found[1:]] == ["e.py"]
    assert found[1].line == 6 and found[1].message_text.startswith("1 ligne ")


def test_chemin_absolu_dans_l_arbre_devient_relatif(tmp_path: Path) -> None:
    absolute = str(tmp_path / "src" / "a.py")
    stats = {absolute: {"violation_lines": [2]}}
    found = parsers.parse_diff_cover_json(_payload(2, 0, stats), tmp_path)
    assert found[1].path == "src/a.py"


# ------------------------------------------------------------------ parse_coverage_json
def _cov(percent: object, files: object = None) -> str:
    return json.dumps(
        {"files": {"a.py": {}} if files is None else files, "totals": {"percent_covered": percent}}
    )


@pytest.mark.parametrize(
    ("percent", "shown"),
    [(87.6, 87), (0.4, 0), (100, 100), ("42.9", 42), (99.99, 99)],
)
def test_couverture_totale_tronquee(tmp_path: Path, percent: object, shown: int) -> None:
    (total,) = parsers.parse_coverage_json(_cov(percent), tmp_path)
    assert total.rule_id == "total_coverage" and total.severity == "info"
    assert total.message_text == f"Couverture de l'ensemble du dépôt : {shown} % (information)."
    assert total.path is None and total.line is None


@pytest.mark.parametrize(
    "text",
    [
        _cov("abc"),
        _cov(None),
        _cov([1]),
        json.dumps({"files": {"a.py": {}}, "totals": {}}),
        json.dumps({"files": {"a.py": {}}}),
        json.dumps({"files": {"a.py": {}}, "totals": []}),
        json.dumps({"files": [], "totals": {"percent_covered": 50}}),
        json.dumps({"files": {}, "totals": {"percent_covered": 50}}),
        "not json",
        "[]",
    ],
)
def test_mesure_de_couverture_invalide_refusee(tmp_path: Path, text: str) -> None:
    with pytest.raises(ValueError):
        parsers.parse_coverage_json(text, tmp_path)


def test_messages_d_erreur_de_la_mesure(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="vide ou inattendue"):
        parsers.parse_coverage_json(_cov(50, {}), tmp_path)
    with pytest.raises(ValueError, match="inattendue"):
        parsers.parse_coverage_json(_cov("abc"), tmp_path)
    with pytest.raises(ValueError, match="illisible"):
        parsers.parse_coverage_json("nope", tmp_path)


# ------------------------------------------------------------------ with_tools_on_path
def test_with_tools_on_path_met_les_dossiers_en_tete(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    known = {
        "git": SimpleNamespace(ok=True, path=tmp_path / "g" / "git"),
        "uv": SimpleNamespace(ok=True, path=tmp_path / "u" / "uv"),
        "broken": SimpleNamespace(ok=False, path=tmp_path / "b" / "x"),
        "nopath": SimpleNamespace(ok=True, path=None),
    }
    monkeypatch.setattr(toolrun, "resolve", lambda tool_id, settings, **kw: known[tool_id])
    env = {"PATH": "/usr/bin", "KEEP": "1"}
    out = toolrun.with_tools_on_path(env, ("git", "broken", "nopath", "uv"), None)  # type: ignore[arg-type]
    assert out["PATH"] == os.pathsep.join([str(tmp_path / "g"), str(tmp_path / "u"), "/usr/bin"])
    assert out["KEEP"] == "1"
    assert env == {"PATH": "/usr/bin", "KEEP": "1"}  # l'original n'est pas modifié


def test_with_tools_on_path_respecte_la_casse_de_la_cle_et_un_path_vide(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        toolrun, "resolve", lambda *a, **k: SimpleNamespace(ok=True, path=tmp_path / "g" / "git")
    )
    out = toolrun.with_tools_on_path({"Path": "C:\\x"}, ("git",), None)  # type: ignore[arg-type]
    assert out == {"Path": os.pathsep.join([str(tmp_path / "g"), "C:\\x"])}
    # Sans PATH : pas de séparateur final.
    out = toolrun.with_tools_on_path({}, ("git",), None)  # type: ignore[arg-type]
    assert out == {"PATH": str(tmp_path / "g")}
    # Aucun outil résolu et PATH vide : PATH vide, sans séparateur.
    monkeypatch.setattr(toolrun, "resolve", lambda *a, **k: SimpleNamespace(ok=False, path=None))
    assert toolrun.with_tools_on_path({"PATH": ""}, ("git",), None) == {"PATH": ""}  # type: ignore[arg-type]


# ------------------------------------------------------------------ replace_in_file
def _ctx(repo: Path) -> SimpleNamespace:
    return SimpleNamespace(layout=SimpleNamespace(repo=repo))


def _apply(repo: Path, path: str, old: str, new: str) -> str:
    return replace_in_file.apply(
        replace_in_file.Args(op="replace_in_file", path=path, old=old, new=new),
        _ctx(repo),  # type: ignore[arg-type]
    )


def test_replace_in_file_rend_l_identifiant_de_l_element(tmp_path: Path) -> None:
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "f.txt").write_text("x=1\n", "utf-8")
    assert _apply(tmp_path, "d/f.txt", "x=1", "x=2") == "path:worktree:d/f.txt"
    assert (tmp_path / "d" / "f.txt").read_text("utf-8") == "x=2\n"


def test_replace_in_file_ne_remplace_qu_une_fois_meme_si_le_nouveau_texte_contient_l_ancien(
    tmp_path: Path,
) -> None:
    (tmp_path / "f.txt").write_text("a-b", "utf-8")
    _apply(tmp_path, "f.txt", "a", "aa")
    assert (tmp_path / "f.txt").read_text("utf-8") == "aa-b"


def test_replace_in_file_message_donne_le_nombre_d_occurrences(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_text("a a", "utf-8")
    with pytest.raises(SetupError, match=r"figure 2 fois \(une seule attendue\)"):
        _apply(tmp_path, "f.txt", "a", "b")
    with pytest.raises(SetupError, match="figure 0 fois"):
        _apply(tmp_path, "f.txt", "z", "b")
    assert (tmp_path / "f.txt").read_text("utf-8") == "a a"  # rien d'écrit en cas d'échec


def test_replace_in_file_normalise_les_fins_de_ligne(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_bytes(b"un\r\ndeux\r\ntrois\r\n")
    _apply(tmp_path, "f.txt", "un\ndeux\n", "UN\n")
    assert (tmp_path / "f.txt").read_text("utf-8").replace("\r\n", "\n") == "UN\ntrois\n"


def test_replace_in_file_fichier_absent_ou_illisible(tmp_path: Path) -> None:
    with pytest.raises(SetupError, match="n'a pas pu être lu"):
        _apply(tmp_path, "absent.txt", "a", "b")
    (tmp_path / "bin.dat").write_bytes(b"\xff\xfe\x00a")
    with pytest.raises(SetupError, match="n'a pas pu être lu"):
        _apply(tmp_path, "bin.dat", "a", "b")


@pytest.mark.parametrize("path", ["../x", "/etc/passwd", "a/../../x", ".git/config"])
def test_replace_in_file_refuse_les_chemins_hors_du_depot(path: str) -> None:
    with pytest.raises(ValueError):
        replace_in_file.Args(op="replace_in_file", path=path, old="a", new="b")


def test_replace_in_file_refuse_un_texte_vide_mais_accepte_un_remplacement_vide(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="vide"):
        replace_in_file.Args(op="replace_in_file", path="f.txt", old="", new="b")
    (tmp_path / "f.txt").write_text("abc", "utf-8")
    _apply(tmp_path, "f.txt", "b", "")
    assert (tmp_path / "f.txt").read_text("utf-8") == "ac"
