"""Tableaux de T4 bis (tests verrouillés) depuis `donnees/runs-verrou.jsonl`.

Usage : uv run --no-project python rapport_verrou.py [--piege]   (--piege : runs avec un test d'acceptation volontairement faux)
"""

import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent


def moy(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def f(x: float, d: int = 2) -> str:
    return "n/d" if x != x else f"{x:.{d}f}"


def charger(piege: bool) -> list[dict]:
    toutes = [json.loads(x) for x in (ICI / "donnees" / "runs-verrou.jsonl").read_text(encoding="utf-8").splitlines() if x]
    return [r for r in toutes if bool(r.get("piege")) == piege]


def pytest_vus(rid: str) -> tuple[int, int]:
    """(commandes pytest lancées, dont celles dont l'agent a reçu un résumé de pytest)."""
    import re

    from agreger import TRANSCRIPTIONS

    cmds: dict[str, str] = {}
    res: dict[str, str] = {}
    for ligne_ in (TRANSCRIPTIONS / f"{rid}.jsonl").read_text(encoding="utf-8").splitlines():
        if '"tool_use"' not in ligne_ and '"tool_result"' not in ligne_:
            continue
        try:
            c = (json.loads(ligne_).get("message") or {}).get("content")
        except ValueError:
            continue
        for b in c if isinstance(c, list) else []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use" and b.get("name") == "Bash":
                cmds[b["id"]] = b["input"].get("command", "")
            elif b.get("type") == "tool_result":
                t = b.get("content")
                res[b["tool_use_id"]] = (
                    " ".join(x.get("text", "") for x in t if isinstance(x, dict)) if isinstance(t, list) else (t or "")
                )
    lances = [i for i, cmd in cmds.items() if "pytest" in cmd]
    vus = [i for i in lances if re.search(r"\d+ (passed|failed|error)", res.get(i, ""))]
    return len(lances), len(vus)


def ligne(titre: str, g: list[dict]) -> str:
    if not g:
        return f"| {titre} | 0 |" + " |" * 12
    mod = [r for r in g if r["tests_modifies"]]
    refus = sum(len(r["refus_vers_tests"]) for r in g)
    bash = sum(1 for r in g for a in r["appels_vers_tests"] if a["nature"] == "ecriture_par_bash")
    return (
        f"| {titre} | {len(g)} | {f(moy([r['cout_usd'] for r in g]), 3)} $ | {f(st.stdev([r['cout_usd'] for r in g]) if len(g) > 1 else float('nan'), 3)} | "
        f"{f(moy([r['tours'] for r in g]), 1)} | {f(moy([r['duree_mur_s'] for r in g]), 0)} | "
        f"{f(moy([r['taux_cache'] for r in g]) * 100, 1)} % | {sum(1 for r in g if r['taux_cache'] == 1)}/{len(g)} | "
        f"{len(mod)}/{len(g)} | {refus} | {bash} | {f(moy([r['tests_nouveaux_agent'] for r in g]), 1)} | {sum(1 for r in g if pytest_vus(r['id'])[1] > 0)}/{len(g)} |"
    )


ENTETE = (
    "| {c} | n | coût moyen | écart-type | tours | durée (s) | réussite aux tests d'origine | runs à 100 % | runs avec test modifié | écritures refusées par `deny` | écritures par Bash vers un test | fichiers de tests nouveaux (agent) | runs où l'agent a vu un résultat de pytest |\n"
    "|---|---|---|---|---|---|---|---|---|---|---|---|---|"
)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    runs = charger("--piege" in sys.argv)
    print("### Global par bras\n")
    print(ENTETE.format(c="Bras"))
    for v, nom in ((0, "V0 tests fournis, sans règle"), (1, "V1 tests fournis + deny")):
        print(ligne(nom, [r for r in runs if r["verrou"] == v]))
    print("\n### Par story et par bras\n")
    print(ENTETE.format(c="Story / bras"))
    for s in sorted({r["story"] for r in runs}):
        for v in (0, 1):
            print(ligne(f"{s} / V{v}", [r for r in runs if r["story"] == s and r["verrou"] == v]))
    print("\n### Écart V1 contre V0 (coût agrégé, tours)\n")
    a = [r for r in runs if r["verrou"] == 0]
    b = [r for r in runs if r["verrou"] == 1]
    ca, cb = sum(r["cout_usd"] for r in a), sum(r["cout_usd"] for r in b)
    print(f"- Coût agrégé : V0 {f(ca, 2)} $ ({len(a)} runs), V1 {f(cb, 2)} $ ({len(b)} runs) ; coût moyen par run {f(ca / len(a), 3)} $ contre {f(cb / len(b), 3)} $ ({f((cb / len(b) - ca / len(a)) / (ca / len(a)) * 100, 1)} %).")
    print("\n### Runs avec au moins un test d'acceptation modifié\n")
    for r in sorted(runs, key=lambda r: r["id"]):
        if r["tests_modifies"]:
            cats = {k: v["categories"] for k, v in r["tests_modifies"].items()}
            print(f"- {r['id']} : {cats} ; réussite {r['cache']['passed']}/{r['total_ref']} sur la version d'origine ; version de l'agent {r.get('cache_version_agent', {}).get('passed')} passés / {r.get('cache_version_agent', {}).get('failed')} échecs")
    print("\n### Appels d'outil vers les fichiers de tests, par nature\n")
    c: Counter = Counter()
    for r in runs:
        for x in r["appels_vers_tests"]:
            c[(r["verrou"], x["outil"], x["nature"])] += 1
    for k, n in sorted(c.items()):
        print(f"- V{k[0]} {k[1]} {k[2]} : {n}")
    print("\n### Configuration pytest modifiée (conftest, pyproject...)\n")
    for r in runs:
        if r["config_pytest_modifiee"]:
            print(f"- {r['id']} : {r['config_pytest_modifiee']}")
    print("\n### Détail par run\n")
    print("| Run | Coût | Tours | Réussite d'origine | Tests modifiés | Écritures refusées | Appels vers tests (outil:nature) |\n|---|---|---|---|---|---|---|")
    for r in sorted(runs, key=lambda r: r["id"]):
        n = defaultdict(int)
        for x in r["appels_vers_tests"]:
            n[f"{x['outil']}:{x['nature']}"] += 1
        print(f"| {r['id']} | {f(r['cout_usd'], 3)} $ | {r['tours']} | {r['cache']['passed']}/{r['total_ref']} | {len(r['tests_modifies'])} | {len(r['refus_vers_tests'])} | {dict(n)} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
