r"""T5 elargi, etape 2 : mutation cosmic-ray bornee aux lignes ajoutees par la story (outillage de T4/mutation_story.py).

usage : mutants.py <id> [--budget-min 8] [--sample 70] [--seed 5]
Travaille sur T:\src\<id> avec le venv de T:\v\<depot>. Ecrit T:\mut\<id>\survivants.json.
Difference avec T4 : echantillon aleatoire (graine fixe) des mutants effectifs pour tenir le budget, lignes ajoutees
lues dans meta.json (pas de git dans la copie), PYTHONPATH sur l'arbre.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import random
import sqlite3
import subprocess
import time
from pathlib import Path

from lancer_tests import commande

T = Path("T:/")
spec = importlib.util.spec_from_file_location("t4", Path(__file__).resolve().parent.parent / "T4" / "mutation_story.py")
t4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t4)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("sid")
    ap.add_argument("--budget-min", type=float, default=8.0)
    ap.add_argument("--sample", type=int, default=70)
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--timeout-test", type=float, default=120.0)
    a = ap.parse_args()
    if (T / "mut" / a.sid / "temoin").exists():
        print(a.sid, "temoin : pas de mutation")
        return
    meta = json.loads((T / "jeu" / a.sid / "meta.json").read_text(encoding="utf-8"))
    cmd, arbre, env = commande(a.sid)
    py = cmd[0]
    scripts = Path(py).parent
    out = T / "mut" / a.sid
    out.mkdir(parents=True, exist_ok=True)
    test_cmd = " ".join(c.replace("\\", "/") for c in cmd if c not in ("--tb=short",)).replace("-q -x", "-q -x --tb=no")
    t0 = time.time()
    deadline = t0 + a.budget_min * 60
    # delai de base
    p = subprocess.run(test_cmd.split(), cwd=arbre, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    base_s = round(time.time() - t0, 1)
    res = {"story": a.sid, "test_command": test_cmd, "tests_seconds": base_s, "tests_rc": p.returncode, "modules": []}
    if p.returncode:
        res["erreur"] = "suite cible rouge sans mutation : " + p.stdout[-400:]
        (out / "survivants.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), "utf-8")
        print(a.sid, res["erreur"])
        return
    originaux = {m: (arbre / m).read_bytes() for m in meta["src"] if (arbre / m).exists()}  # un kill a l'echeance laisse le dernier mutant en place
    rng = random.Random(a.seed)
    plan = []  # (module, db, job_id)
    for module in meta["src"]:
        if not (arbre / module).exists() or Path(module).name == "__init__.py" and not meta["lignes_ajoutees"].get(module):
            continue
        keep = set(meta["lignes_ajoutees"].get(module, []))
        name = Path(module).stem
        cfg = arbre / f"cr-{name}.toml"
        db = out / f"cr-{name}.sqlite"
        db.unlink(missing_ok=True)
        cfg.write_text("[cosmic-ray]\n" f'module-path = "{module}"\n' f"timeout = {a.timeout_test}\n" "excluded-modules = []\n"
                       f'test-command = "{test_cmd}"\n\n[cosmic-ray.distributor]\nname = "local"\n', "utf-8")
        r = subprocess.run([str(scripts / "cosmic-ray.exe"), "init", cfg.name, str(db)], cwd=arbre, env=env, capture_output=True, text=True)
        if r.returncode:
            res["modules"].append({"module": module, "erreur_init": r.stderr[-300:]})
            continue
        con = sqlite3.connect(db)
        rows = con.execute("select job_id, start_pos_row, start_pos_col from mutation_specs").fetchall()
        spans = t4.annotation_spans((arbre / module).read_text(encoding="utf-8"))
        eff = [j for j, row, col in rows if row in keep and not t4.in_span(row, col, spans)]
        con.close()
        res["modules"].append({"module": module, "generes": len(rows), "effectifs": len(eff)})
        plan += [(module, cfg, db, j) for j in eff]
    rng.shuffle(plan)
    plan = plan[: a.sample]
    # ne garder dans chaque base que les mutants echantillonnes
    par_base: dict = {}
    for module, cfg, db, j in plan:
        par_base.setdefault((module, cfg, db), set()).add(j)
    for m in res["modules"]:
        m["echantillon"] = 0
    for (module, cfg, db), jobs in par_base.items():
        con = sqlite3.connect(db)
        tous = [r[0] for r in con.execute("select job_id from mutation_specs")]
        for j in tous:
            if j not in jobs:
                con.execute("delete from mutation_specs where job_id=?", (j,))
                con.execute("delete from work_items where job_id=?", (j,))
        con.commit()
        con.close()
        for m in res["modules"]:
            if m["module"] == module:
                m["echantillon"] = len(jobs)
    survivants = []
    for (module, cfg, db), jobs in par_base.items():
        remaining = deadline - time.time()
        if remaining < 5:
            break
        proc = subprocess.Popen([str(scripts / "cosmic-ray.exe"), "exec", cfg.name, str(db)], cwd=arbre, env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            t4.kill_tree(proc)
            res["budget_atteint"] = True
        con = sqlite3.connect(db)
        rows = con.execute("select w.test_outcome, w.diff, s.start_pos_row, s.start_pos_col, s.operator_name, s.occurrence, s.definition_name, s.module_path, s.job_id "
                           "from work_results w join mutation_specs s using (job_id)").fetchall()
        con.close()
        for m in res["modules"]:
            if m["module"] == module:
                m["executes"] = len(rows)
                m["tues"] = sum(1 for r in rows if r[0] == "KILLED")
        for o, diff, row, col, op, occ, fn, mp, job in rows:
            if o == "SURVIVED":
                survivants.append(dict(module=module, ligne=row, colonne=col, operateur=op, occurrence=occ, fonction=fn, job_id=job, db=str(db), diff=diff))
        (arbre / module).write_bytes(originaux[module])  # restaure le fichier (le dernier mutant peut rester applique)
    res["survivants"] = survivants
    res["total_seconds"] = round(time.time() - t0, 1)
    (out / "survivants.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), "utf-8")
    print(a.sid, {k: v for k, v in res.items() if k not in ("survivants", "test_command")}, "survivants", len(survivants))


if __name__ == "__main__":
    main()
