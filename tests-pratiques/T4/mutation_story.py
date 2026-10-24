"""T4 : mutation testing borne aux fichiers (et aux lignes) d'une story, avec cosmic-ray.

Usage (depuis n'importe ou, stdlib seule) :
  python mutation_story.py --worktree <copie jetable> --base <commit avant la story> \
      --modules src/pkg/a.py,src/pkg/b.py --tests tests/test_a.py,tests/test_b.py \
      --story wd-5-9 --out <dossier des resultats> [--budget-min 20] [--timeout-test 60]

Ce que fait le script :
  1. installe cosmic-ray dans le venv de la copie jetable (jamais global) ;
  2. par module : `cosmic-ray init`, puis retire du plan les mutants
     - dans une annotation de type (equivalents sous `from __future__ import annotations`),
     - hors des lignes ajoutees ou modifiees par la story (`git diff -U0 <base> HEAD`) ;
  3. `cosmic-ray baseline` puis `cosmic-ray exec` sous un budget de temps (arbre de processus tue a l'echeance) ;
  4. ecrit <out>/<story>.json : comptes, delais, survivants avec leur diff.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path


def run(cmd, cwd, timeout=None, check=False):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    if check and p.returncode != 0:
        sys.exit(f"echec {cmd}: {p.stdout[-800:]} {p.stderr[-800:]}")
    return p


def added_lines(worktree: Path, base: str, module: str) -> set[int]:
    out = run(["git", "diff", "-U0", base, "HEAD", "--", module], worktree).stdout
    lines: set[int] = set()
    for m in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", out, re.M):
        start, n = int(m.group(1)), int(m.group(2) or 1)
        lines.update(range(start, start + n))
    return lines


def annotation_spans(source: str) -> list[tuple[int, int, int, int]]:
    spans = []
    for node in ast.walk(ast.parse(source)):
        anns = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            for a in [*args.posonlyargs, *args.args, *args.kwonlyargs, args.vararg, args.kwarg]:
                if a is not None and a.annotation is not None:
                    anns.append(a.annotation)
            if node.returns is not None:
                anns.append(node.returns)
        elif isinstance(node, ast.AnnAssign):
            anns.append(node.annotation)
        for a in anns:
            spans.append((a.lineno, a.col_offset, a.end_lineno, a.end_col_offset))
    return spans


def in_span(row: int, col: int, spans) -> bool:
    return any((sr, sc) <= (row, col) < (er, ec) for sr, sc, er, ec in spans)


def kill_tree(proc):
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--modules", required=True)
    ap.add_argument("--tests", required=True)
    ap.add_argument("--story", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--budget-min", type=float, default=20.0)
    ap.add_argument("--timeout-test", type=float, default=60.0)
    ap.add_argument("--no-diff-filter", action="store_true", help="garde les mutants hors diff")
    ap.add_argument("--sync", action="store_true", help="uv sync + installe cosmic-ray")
    a = ap.parse_args()

    wt = Path(a.worktree).resolve()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    scripts = wt / ".venv" / "Scripts"
    py = scripts / "python.exe"
    t0 = time.time()
    deadline = t0 + a.budget_min * 60

    if a.sync or not py.exists():
        run(["uv", "sync", "-q"], wt, check=True)
        run(["uv", "pip", "install", "-q", "cosmic-ray"], wt, check=True)

    tests = " ".join(a.tests.split(","))
    test_cmd = f"{py.as_posix()} -m pytest -x -q --tb=no -p no:cacheprovider {tests}"
    result = {"story": a.story, "base": a.base, "tests": a.tests.split(","), "modules": [],
              "test_command": test_cmd}

    # delai de la suite cible, hors mutation
    t = time.time()
    p = run(test_cmd.split(), wt)
    result["tests_seconds"] = round(time.time() - t, 1)
    result["tests_rc"] = p.returncode
    result["tests_tail"] = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""
    if p.returncode != 0:
        (out / f"{a.story}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), "utf-8")
        sys.exit(f"suite cible rouge sans mutation : {p.stdout[-500:]}")

    for module in a.modules.split(","):
        name = Path(module).stem
        cfg = wt / f"cr-{name}.toml"
        db = wt / f"cr-{name}.sqlite"
        db.unlink(missing_ok=True)
        cfg.write_text(
            "[cosmic-ray]\n"
            f'module-path = "{module}"\n'
            f"timeout = {a.timeout_test}\n"
            "excluded-modules = []\n"
            f'test-command = "{test_cmd}"\n\n'
            "[cosmic-ray.distributor]\n"
            'name = "local"\n', "utf-8")
        run([str(scripts / "cosmic-ray"), "init", cfg.name, db.name], wt, check=True)

        con = sqlite3.connect(db)
        rows = con.execute(
            "select job_id, start_pos_row, start_pos_col, operator_name from mutation_specs").fetchall()
        generated = len(rows)
        spans = annotation_spans((wt / module).read_text(encoding="utf-8"))
        keep_lines = None if a.no_diff_filter else added_lines(wt, a.base, module)
        drop_ann, drop_diff = [], []
        for job, row, col, _op in rows:
            if in_span(row, col, spans):
                drop_ann.append(job)
            elif keep_lines is not None and row not in keep_lines:
                drop_diff.append(job)
        for job in drop_ann + drop_diff:
            con.execute("delete from mutation_specs where job_id=?", (job,))
            con.execute("delete from work_items where job_id=?", (job,))
        con.commit()
        con.close()
        effective = generated - len(drop_ann) - len(drop_diff)

        mod = {"module": module, "generated": generated, "excluded_annotations": len(drop_ann),
               "excluded_outside_diff": len(drop_diff), "effective": effective}
        remaining = deadline - time.time()
        t = time.time()
        timed_out = False
        if effective and remaining > 5:
            proc = subprocess.Popen([str(scripts / "cosmic-ray"), "exec", cfg.name, db.name], cwd=wt,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                proc.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                kill_tree(proc)
                timed_out = True
        mod["exec_seconds"] = round(time.time() - t, 1)
        mod["budget_exceeded"] = timed_out

        con = sqlite3.connect(db)
        res = con.execute(
            "select w.test_outcome, w.diff, s.start_pos_row, s.operator_name, s.definition_name "
            "from work_results w join mutation_specs s using (job_id)").fetchall()
        con.close()
        done = len(res)
        killed = sum(1 for r in res if r[0] == "KILLED")
        surv = [r for r in res if r[0] == "SURVIVED"]
        mod.update(done=done, killed=killed, survived=len(surv),
                   incompetent=sum(1 for r in res if r[0] == "INCOMPETENT"),
                   pending=effective - done,
                   survival_rate=round(len(surv) / done, 3) if done else None,
                   survivors=[{"line": r[2], "operator": r[3], "function": r[4],
                               "diff": "\n".join(l for l in (r[1] or "").splitlines()
                                                 if l[:1] in "+-" and not l.startswith(("---", "+++")))}
                              for r in sorted(surv, key=lambda r: r[2])])
        result["modules"].append(mod)

    result["total_seconds"] = round(time.time() - t0, 1)
    (out / f"{a.story}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), "utf-8")
    for m in result["modules"]:
        print(m["module"], {k: v for k, v in m.items() if k not in ("survivors", "module")})
    print("total_seconds", result["total_seconds"])


if __name__ == "__main__":
    main()
