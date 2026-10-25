"""T10 : evalue une execution d'agent : validite des nouveaux tests, stabilite, puis rejeu des survivants cibles.
usage : evaluer.py <story> <A|B> <essai>   -> resultats-bruts/eval-<story>-<bras><essai>.json
Un seul processus de test a la fois ; .hypothesis supprime avant chaque lancement (pas de contamination entre mutants)."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from jeu import BRUTS, STORIES, arbre, env_pour, python
from mutation import applique

DELAI_MUTANT = 180
DELAI_BASE = 900


def git_status(a: Path):
    st = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=a, capture_output=True,
                        text=True, encoding="utf-8").stdout.splitlines()
    return [l[3:].strip('"') for l in st if not l.startswith("??")], [l[3:].strip('"') for l in st if l.startswith("??")]


def pytest(story, bras, essai, args, delai, tb="line"):
    a = arbre(story, bras, essai)
    shutil.rmtree(a / ".hypothesis", ignore_errors=True)
    cmd = [python(story, bras), "-m", "pytest", "-q", f"--tb={tb}", "-p", "no:cacheprovider", *args]
    t = time.time()
    try:
        p = subprocess.run(cmd, cwd=a, env=env_pour(story, bras, essai), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=delai)
        rc, out = p.returncode, p.stdout
    except subprocess.TimeoutExpired:
        rc, out = "timeout", ""
    return rc, out, round(time.time() - t, 2)


def echecs(sortie: str, fichiers: list[str]) -> tuple[set[str], set[str]]:
    """(tests en echec, fichiers en erreur de collecte) d'apres -rfE."""
    tests, fich = set(), set()
    for l in sortie.splitlines():
        m = re.match(r"(FAILED|ERROR) (\S+)", l)
        if not m:
            continue
        nid = m.group(2).replace("\\", "/")
        if "::" in nid:
            tests.add(nid)
        elif nid.endswith(".py"):
            fich.add(nid)
    return tests, fich


def main():
    story, bras, essai = sys.argv[1], sys.argv[2], int(sys.argv[3])
    nom = f"{story}-{bras}{essai}"
    meta = STORIES[story]
    a = arbre(story, bras, essai)
    cibles = json.loads((Path(__file__).parent / "cibles.json").read_text(encoding="utf-8"))[story]["cibles"]
    modifies, crees = git_status(a)
    nouveaux = sorted(c for c in crees if c.endswith(".py") and ".hypothesis" not in c)
    res = {"story": story, "bras": bras, "essai": essai, "nouveaux_fichiers": nouveaux, "modifies_suivis": modifies,
           "cibles_total": len(cibles)}
    sortie = BRUTS / f"eval-{nom}.json"
    if modifies:
        res["rejet"] = "fichiers suivis modifies : " + ", ".join(modifies)
        sortie.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(nom, "REJETE", res["rejet"])
        return
    if not nouveaux:
        res["rejet"] = "aucun nouveau fichier de test"
        sortie.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(nom, "REJETE", res["rejet"])
        return
    src_nouveaux = "\n".join((a / f).read_text(encoding="utf-8", errors="replace") for f in nouveaux)
    res["utilise_hypothesis"] = bool(re.search(r"^\s*(from|import) hypothesis", src_nouveaux, re.M))
    res["nb_given"] = len(re.findall(r"@given\(", src_nouveaux))
    res["lignes_tests"] = src_nouveaux.count("\n") + 1

    # collecte
    rc, out, _ = pytest(story, bras, essai, ["--collect-only", "-q", *nouveaux], DELAI_BASE)
    n_id = len([l for l in out.splitlines() if "::" in l])
    n_fich = sum(int(m.group(1)) for m in re.finditer(r"^\S+\.py: (\d+)$", out, re.M))
    res["nb_tests_nouveaux"] = n_id or n_fich

    # (a) validite : suite de la story + nouveaux tests, code non mute
    rc, out, dur = pytest(story, bras, essai, ["-rfE", *meta["tests"], *nouveaux], DELAI_BASE)
    res["union"] = {"rc": rc, "fin": (out.strip().splitlines() or [""])[-1][:160], "secondes": dur}
    # nouveaux tests seuls, deux passages (stabilite)
    passages = []
    for _ in range(2):
        rc, out, dur = pytest(story, bras, essai, ["-rfE", *nouveaux], DELAI_BASE)
        t, f = echecs(out, nouveaux)
        passages.append({"rc": rc, "secondes": dur, "echecs": sorted(t), "fichiers_en_erreur": sorted(f),
                         "fin": (out.strip().splitlines() or [""])[-1][:160]})
    res["passages"] = passages
    f1, f2 = set(passages[0]["echecs"]), set(passages[1]["echecs"])
    ef1, ef2 = set(passages[0]["fichiers_en_erreur"]), set(passages[1]["fichiers_en_erreur"])
    res["tests_faux"] = sorted(f1 & f2)
    res["tests_instables"] = sorted(f1 ^ f2)
    res["fichiers_en_erreur"] = sorted(ef1 | ef2)
    res["secondes_nouveaux_tests"] = min(p["secondes"] for p in passages)
    ecarter = [f"--deselect={t}" for t in sorted(f1 | f2)] + [f"--ignore={f}" for f in sorted(ef1 | ef2)]
    utiles = [f for f in nouveaux if f not in (ef1 | ef2)]
    res["rejeu_possible"] = bool(utiles)

    # (b) rejeu des survivants cibles contre les nouveaux tests (les survivants de T4 survivent deja aux tests de la story)
    resultats = []
    if utiles:
        for c in cibles:
            chemin = a / c["module"]
            for pyc in chemin.parent.glob("__pycache__"):
                shutil.rmtree(pyc, ignore_errors=True)
            try:
                with applique(chemin, c):
                    rc, out, dur = pytest(story, bras, essai, ["-x", "--tb=no", *ecarter, *utiles], DELAI_MUTANT)
                    rc2 = None
                    if rc == 0 and res["utilise_hypothesis"]:  # nouveau tirage Hypothesis sur les survivants
                        rc2, _, _ = pytest(story, bras, essai, ["-x", "--tb=no", *ecarter, *utiles], DELAI_MUTANT)
            except Exception as e:  # mutant non applicable
                resultats.append({"id": c["id"], "etat": "erreur", "detail": repr(e)[:200]})
                continue
            etat = "survit" if rc in (0, 5) else ("tue_timeout" if rc == "timeout" else "tue")
            resultats.append({"id": c["id"], "etat": etat, "rc": rc, "secondes": dur,
                              "tue_au_second_tirage": (rc2 not in (None, 0, 5)) if etat == "survit" else None})
        res["rejeu"] = resultats
        res["tues"] = sum(1 for r in resultats if r["etat"].startswith("tue"))
        res["tues_avec_second_tirage"] = res["tues"] + sum(1 for r in resultats if r.get("tue_au_second_tirage"))
        res["erreurs_rejeu"] = sum(1 for r in resultats if r["etat"] == "erreur")
    # le code source doit etre intact apres le rejeu
    res["modifies_suivis_apres"] = git_status(a)[0]
    sortie.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(nom, "tues", res.get("tues"), "/", len(cibles), "faux", len(res["tests_faux"]), "instables", len(res["tests_instables"]),
          "nouveaux tests", res["nb_tests_nouveaux"], "s", res["secondes_nouveaux_tests"], "hyp", res["utilise_hypothesis"], res["nb_given"])


if __name__ == "__main__":
    main()
