"""T10b : agrege les executions du bras C (resultats-bruts/T10b) et les compare aux bras A et B de T10 (resultats-bruts).
usage : agreger_c.py [equivalents.json]
equivalents.json (optionnel) : liste des ids de cibles jugees equivalentes a la main ; sert au denominateur « non equivalentes »."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ICI = Path(__file__).parent
T10 = ICI / "resultats-bruts"
T10B = T10 / "T10b"
CIBLES = json.loads((ICI / "cibles.json").read_text(encoding="utf-8"))
ORDRE = ["wd-5-9", "wd-8-4", "us-7-14", "us-7-15", "us-7-16"]
EQUIV = set(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))) if len(sys.argv) > 1 else set()


def charger(dossier: Path, bras: str):
    runs = []
    for f in sorted(dossier.glob(f"eval-*-{bras}[12].json")):
        e = json.loads(f.read_text(encoding="utf-8"))
        ag = json.loads((dossier / f"agent-{e['story']}-{e['bras']}{e['essai']}.json").read_text(encoding="utf-8"))
        s = ag["sortie"]
        e["cout"] = s.get("total_cost_usd") or 0
        e["tours"] = s.get("num_turns") or 0
        e["duree_s"] = round((s.get("duration_ms") or 0) / 1000, 1)
        e["duree_mur_s"] = ag["duree_mur_s"]
        e["tues_ids"] = {x["id"] for x in e.get("rejeu", []) if x["etat"].startswith("tue")}
        runs.append(e)
    return runs


def moy(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def main():
    brs = {"A": charger(T10, "A"), "B": charger(T10, "B"), "C": charger(T10B, "C")}
    out = []
    ids_tous = {s: [c["id"] for c in CIBLES[s]["cibles"]] for s in ORDRE}
    out.append("| Story | Cibles | A (tués par essai, moyenne) | B | **C** | C : coût moyen ($) | C : tours | C : durée agent (s) | C : tests faux / instables |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    glob = {b: defaultdict(float) for b in "ABC"}
    for s in ORDRE:
        n = len(ids_tous[s])
        ne = len([i for i in ids_tous[s] if i not in EQUIV])
        cel = [str(n) if not EQUIV else f"{n} ({ne} non éq.)"]
        for b in "ABC":
            rs = sorted([r for r in brs[b] if r["story"] == s], key=lambda r: r["essai"])
            for r in rs:
                g = glob[b]
                g["runs"] += 1; g["tues"] += r["tues"]; g["n"] += n
                g["tues_ne"] += len(r["tues_ids"] - EQUIV); g["n_ne"] += ne
                g["cout"] += r["cout"]; g["tours"] += r["tours"]; g["duree"] += r["duree_s"]; g["mur"] += r["duree_mur_s"]
                g["faux"] += len(r["tests_faux"]); g["inst"] += len(r["tests_instables"]); g["sec"] += r["secondes_nouveaux_tests"]
            if b != "C":
                cel.append(f"{', '.join(str(r['tues']) for r in rs)} ({100*moy(r['tues'] for r in rs)/n:.0f} %)")
            else:
                cel.append(f"**{', '.join(str(r['tues']) for r in rs)} ({100*moy(r['tues'] for r in rs)/n:.0f} %)**")
                cel.append(f"{moy(r['cout'] for r in rs):.2f}")
                cel.append(f"{moy(r['tours'] for r in rs):.0f}")
                cel.append(f"{moy(r['duree_s'] for r in rs):.0f}")
                cel.append(f"{sum(len(r['tests_faux']) for r in rs)} / {sum(len(r['tests_instables']) for r in rs)}")
        out.append("| " + " | ".join([s] + cel) + " |")
    out.append("")
    for b in "ABC":
        g = glob[b]
        if not g["runs"]:
            continue
        txt = (f"- {b} : {int(g['tues'])}/{int(g['n'])} cibles tuées ({100*g['tues']/g['n']:.1f} %)")
        if EQUIV:
            txt += f" ; hors équivalents vérifiés {int(g['tues_ne'])}/{int(g['n_ne'])} ({100*g['tues_ne']/g['n_ne']:.1f} %)"
        txt += (f" ; coût {g['cout']/g['runs']:.3f} $ par exécution ({g['cout']:.2f} $ au total) ; tours {g['tours']/g['runs']:.1f} ; "
                f"durée agent {g['duree']/g['runs']:.0f} s (mur {g['mur']/g['runs']:.0f} s) ; tests des nouveaux fichiers {g['sec']/g['runs']:.1f} s ; "
                f"faux {int(g['faux'])}, instables {int(g['inst'])}")
        out.append(txt)
    # par cible
    out.append("")
    kill = defaultdict(lambda: {"A": [], "B": [], "C": []})
    for b, rs in brs.items():
        for r in rs:
            for c in ids_tous[r["story"]]:
                kill[c][b].append(c in r["tues_ids"])
    tot = {b: sum(1 for c, d in kill.items() if any(d[b])) for b in "ABC"}
    jamais = [c for c, d in kill.items() if not any(d["A"] + d["B"] + d["C"])]
    c_seul = [c for c, d in kill.items() if any(d["C"]) and not any(d["A"] + d["B"])]
    out.append(f"- Union des essais : A {tot['A']}, B {tot['B']}, C {tot['C']} cibles distinctes tuées (sur 75). Tuées par C seul : {len(c_seul)}. Jamais tuées (A, B, C) : {len(jamais)}.")
    out.append("- Jamais tuées : " + ", ".join(jamais))
    # par cible : taux dans C
    surv_c = [c for c, d in kill.items() if not any(d["C"])]
    out.append(f"- Survivantes de C (aucun des deux essais) : {len(surv_c)} : " + ", ".join(surv_c))
    print("\n".join(out))
    (T10B / "resume-c.json").write_text(json.dumps({"tot": tot, "jamais": jamais, "c_seul": c_seul, "surv_c": surv_c}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
