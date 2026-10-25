"""Agrège `donnees/runs.jsonl` en tableaux Markdown et en `donnees/agregats.json`.

Usage : uv run --no-project python -I agreger.py [--modeles ...] [--out donnees/agregats.json]
Les groupes sont : (modèle principal, conseiller, condition CLAUDE.md). Les statistiques par story
moyennent les répétitions ; les écarts appariés comparent la même story et la même répétition.
"""

import argparse
import json
import math
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent
COURT = {"claude-sonnet-5-5": "Sonnet", "claude-opus-5-5": "Opus", "claude-haiku-5-5": "Haiku"}


def charger(chemin: Path = ICI / "donnees" / "runs.jsonl") -> list[dict]:
    brut = [json.loads(ligne) for ligne in chemin.read_text(encoding="utf-8").splitlines() if ligne]
    for e in brut:
        u = e.get("usage") or {}
        e["tok_entree_neuve"] = (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
        e["tok_lecture_cache"] = u.get("cache_read_input_tokens") or 0
        e["tok_sortie"] = u.get("output_tokens") or 0
        e["taux"] = e.get("taux_cache") or 0.0
        e["suite_ko"] = (e["suite"]["failed"] + e["suite"]["errors"]) if e.get("suite") else None
        mu = e.get("modelUsage") or {}
        e["cout_conseiller"] = sum(v.get("costUSD", 0) for k, v in mu.items() if k != e["modele"])
        e["cout_principal"] = (mu.get(e["modele"]) or {}).get("costUSD", 0)
        e["groupe"] = groupe(e)
        e["appels_conseiller"] = appels_conseiller(e["id"]) if e.get("advisor") else 0
    return brut


def groupe(e: dict) -> str:
    nom = COURT.get(e["modele"], e["modele"])
    if e.get("advisor"):
        nom += "+" + COURT.get(e["advisor"], e["advisor"])
        if e.get("consigne"):
            nom += " (consigne)"
    return nom


TRANSCRIPTIONS = Path(
    r"C:\Users\UTILIS~1\AppData\Local\Temp\claude\C--Users-Utilisateur-Documents-GitHub"
    r"\791fed94-a8b0-414e-8a6c-8fe967283749\scratchpad\rejeu\_transcriptions"
)


def appels_conseiller(rid: str) -> int:
    """Nombre d'appels au conseiller : blocs `server_tool_use` nommés advisor, comptés par identifiant."""
    chemin = TRANSCRIPTIONS / f"{rid}.jsonl"
    if not chemin.exists():
        return -1
    ids: set[str] = set()
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        if '"server_tool_use"' not in ligne or '"type":"assistant"' not in ligne.replace(" ", ""):
            continue
        try:
            contenu = json.loads(ligne).get("message", {}).get("content") or []
        except ValueError:
            continue
        for b in contenu:
            if isinstance(b, dict) and b.get("type") == "server_tool_use" and b.get("name") == "advisor":
                ids.add(b.get("id"))
    return len(ids)


def moy(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def sd(xs: list[float]) -> float:
    return st.stdev(xs) if len(xs) > 1 else float("nan")


def f(x: float | None, d: int = 2) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/d"
    return f"{x:.{d}f}"


def resume_groupe(runs: list[dict]) -> dict:
    cout = [r["cout_usd"] for r in runs]
    par_story = defaultdict(list)
    for r in runs:
        par_story[r["story"]].append(r)
    cout_story = {s: moy([r["cout_usd"] for r in v]) for s, v in par_story.items()}
    taux_story = {s: moy([r["taux"] for r in v]) for s, v in par_story.items()}
    return {
        "n": len(runs),
        "cout_moyen": moy(cout), "cout_median": st.median(cout), "cout_ecart_type": sd(cout),
        "cout_moyen_par_story": moy(list(cout_story.values())),
        "tours_moyen": moy([r["tours"] or 0 for r in runs]),
        "duree_mur_moyenne_s": moy([r["duree_mur_s"] for r in runs]),
        "tok_entree_neuve": moy([r["tok_entree_neuve"] for r in runs]),
        "tok_lecture_cache": moy([r["tok_lecture_cache"] for r in runs]),
        "tok_sortie": moy([r["tok_sortie"] for r in runs]),
        "taux_moyen": moy([r["taux"] for r in runs]),
        "taux_moyen_par_story": moy(list(taux_story.values())),
        "runs_au_plafond": sum(1 for r in runs if r["taux"] >= max(x["taux"] for x in runs)),
        "suite_ko_runs": sum(1 for r in runs if (r["suite_ko"] or 0) > 0),
        "ruff_erreurs_moyennes": moy([max(r["ruff_erreurs"], 0) for r in runs]),
        "ruff_runs_propres": sum(1 for r in runs if r["ruff_erreurs"] == 0 and r["ruff_format_fichiers"] == 0),
        "expires": sum(1 for r in runs if r["expire"]),
        "refus_moyens": moy([r["refus_permission"] for r in runs]),
        "cout_conseiller_moyen": moy([r["cout_conseiller"] for r in runs]),
        "tests_ecrits_moyens": moy([r["diff"]["tests_ecrits"] for r in runs]),
        "lignes_ajoutees_moyennes": moy([r["diff"]["ajoutes"] for r in runs]),
    }


def tableau_global(runs: list[dict], cles: list[tuple[str, str]], titre_cle: str) -> str:
    lignes = [
        f"| {titre_cle} | n | coût moyen | médiane | écart-type | tours | durée (s) | entrée neuve (k) | lecture cache (k) | sortie (k) | taux cachés | suite KO | ruff propre |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for etiquette, sel in cles:
        g = [r for r in runs if sel(r)]
        if not g:
            continue
        s = resume_groupe(g)
        lignes.append(
            f"| {etiquette} | {s['n']} | {f(s['cout_moyen'], 3)} $ | {f(s['cout_median'], 3)} $ | {f(s['cout_ecart_type'], 3)} | "
            f"{f(s['tours_moyen'], 1)} | {f(s['duree_mur_moyenne_s'], 0)} | {f(s['tok_entree_neuve'] / 1000, 1)} | "
            f"{f(s['tok_lecture_cache'] / 1000, 0)} | {f(s['tok_sortie'] / 1000, 1)} | {f(s['taux_moyen'] * 100, 1)} % | "
            f"{s['suite_ko_runs']}/{s['n']} | {s['ruff_runs_propres']}/{s['n']} |"
        )
    return "\n".join(lignes)


def tableau_story(runs: list[dict], variantes: list[tuple[str, callable]]) -> str:  # type: ignore[valid-type]
    stories = sorted({r["story"] for r in runs})
    entete = "| Story | " + " | ".join(f"{v} coût / taux (par rép.)" for v, _ in variantes) + " |"
    lignes = [entete, "|---|" + "---|" * len(variantes)]
    for s in stories:
        cellules = []
        for _, sel in variantes:
            g = sorted([r for r in runs if r["story"] == s and sel(r)], key=lambda r: r["rep"])
            if not g:
                cellules.append("-")
                continue
            cellules.append(
                f"{f(moy([r['cout_usd'] for r in g]), 3)} $ ; {f(moy([r['taux'] for r in g]) * 100, 0)} % "
                f"({' / '.join(f(r['cout_usd'], 2) + ' ' + str(round(r['taux'] * 100)) for r in g)})"
            )
        lignes.append(f"| {s} | " + " | ".join(cellules) + " |")
    return "\n".join(lignes)


def ecarts_apparies(runs: list[dict], sel_a: callable, sel_b: callable) -> dict:  # type: ignore[valid-type]
    """Écart relatif de coût et écart de taux, B contre A, sur les couples (story, répétition)."""
    a = {(r["story"], r["rep"]): r for r in runs if sel_a(r)}
    b = {(r["story"], r["rep"]): r for r in runs if sel_b(r)}
    cles = sorted(set(a) & set(b))
    rel = [(b[k]["cout_usd"] - a[k]["cout_usd"]) / a[k]["cout_usd"] for k in cles]
    dt = [b[k]["taux"] - a[k]["taux"] for k in cles]
    # écart relatif par story (moyenne des répétitions des deux côtés)
    par_story = {}
    for s in sorted({k[0] for k in cles}):
        ca = moy([a[k]["cout_usd"] for k in cles if k[0] == s])
        cb = moy([b[k]["cout_usd"] for k in cles if k[0] == s])
        par_story[s] = (cb - ca) / ca
    return {
        "couples": len(cles),
        "delta_cout_relatif_moyen": moy(rel), "delta_cout_relatif_median": st.median(rel) if rel else float("nan"),
        "delta_cout_relatif_ecart_type": sd(rel),
        "delta_cout_relatif_par_story": par_story,
        "moins_cher_dans": sum(1 for x in rel if x < 0),
        "delta_taux_moyen": moy(dt), "delta_taux_ecart_type": sd(dt),
        "meilleur_taux_dans": sum(1 for x in dt if x > 1e-9), "pire_taux_dans": sum(1 for x in dt if x < -1e-9),
        "delta_cout_agrege": (sum(b[k]["cout_usd"] for k in cles) - sum(a[k]["cout_usd"] for k in cles))
        / sum(a[k]["cout_usd"] for k in cles) if cles else float("nan"),
    }


def bootstrap_ic(xs: list[float], n: int = 4000, graine: int = 7) -> tuple[float, float]:
    import random

    if len(xs) < 3:
        return (float("nan"), float("nan"))
    rng = random.Random(graine)
    moyennes = sorted(moy([rng.choice(xs) for _ in xs]) for _ in range(n))
    return moyennes[int(0.025 * n)], moyennes[int(0.975 * n)]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--entree", type=Path, default=ICI / "donnees" / "runs.jsonl")
    p.add_argument("--out", type=Path, default=ICI / "donnees" / "agregats.json")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    runs = charger(a.entree)
    out: dict = {"n_runs": len(runs), "groupes": {}}
    cles = sorted({(r["groupe"], r["cond"]) for r in runs})
    for g, c in cles:
        sel = [r for r in runs if r["groupe"] == g and r["cond"] == c]
        out["groupes"][f"{g}|{c}"] = resume_groupe(sel)
    a.out.write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(tableau_global(runs, [(f"{g} / {c}", lambda r, g=g, c=c: r["groupe"] == g and r["cond"] == c) for g, c in cles], "Groupe / condition"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
