"""Agrège les 12 exécutions : coûts, mesures automatiques, conformité aux règles. Écrit dans donnees/.
Copie aussi les métadonnées résumées (`_claude.meta.json`) et les mesures par page ; les flux bruts restent dans le scratchpad.
Les chemins locaux sont à anonymiser ensuite (banc-rejeu/anonymiser.py puis T13bis-sans-cadrage/anonymiser_complement.py).
"""
import json, shutil, statistics as st, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from chemins import ARMS, BRAS, DEPOT, ECRANS, ESSAIS, MESURES, nom

OUT = DEPOT / "donnees"
REGLES = ["R1", "R1bis", "R2", "R3", "R4", "R4bis", "R5", "R6", "R7", "R8", "R9"]


def ld(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def moy(xs):
    xs = [x for x in xs if x is not None]
    return round(st.mean(xs), 4) if xs else None


def lignes():
    L = []
    for b in BRAS:
        for e in ECRANS:
            for r in ESSAIS:
                n = nom(b, e, r)
                mp, mm = ARMS / n / "_claude.meta.json", MESURES / n / "mesures.json"
                if not mp.exists() or not mm.exists():
                    print("manquant", n); continue
                m, d = ld(mp), ld(mm)
                f, det, c = d["fonctionnel"], d["impeccable_detect"], d["conformite"]
                (OUT / "runs_design").mkdir(parents=True, exist_ok=True)
                (OUT / "mesures_pages").mkdir(parents=True, exist_ok=True)
                shutil.copy2(mp, OUT / "runs_design" / f"{n}.meta.json")
                shutil.copy2(mm, OUT / "mesures_pages" / f"{n}.json")
                css = ARMS / n / "app" / "static" / "style.css"
                L.append({
                    "rendu": n, "bras": b, "ecran": e, "essai": r,
                    "cout_usd": round(m["cout_usd"], 4), "duree_s": m["duree_s"], "tours": m["tours"], "tokens_out": m["tokens_out"],
                    "cache_creation": m["cache_creation"], "cache_read": m["cache_read"],
                    "tokens_in_total": (m["tokens_in"] or 0) + m["cache_creation"] + m["cache_read"],
                    "skills": m["skills_invoquees"], "design_md_lu": m.get("design_md_lu"), "refus": m["refus_permission"],
                    "erreurs_outils": m["tool_results_en_erreur"], "statut": m["statut"],
                    "fonctionnel": f"{f['_reussis']}/{f['_total']}",
                    "fonctionnel_echecs": sorted(k for k, v in f.items() if v is False and not k.startswith("_")),
                    "axe_violations": d["axe"]["violations_total"], "axe_noeuds": d["axe"]["noeuds_total"],
                    "detect_impeccable": det["n"], "detect_regles": sorted({x.get("antipattern") for x in (det["brut"] or [])}),
                    "contraste_min": d["contraste_perso"]["ratio_min"], "contraste_sous_seuil": d["contraste_perso"]["sous_seuil"],
                    "focus_sans_indicateur": d["focus"]["sans_indicateur"], "debordement_390": d["debordement_390"],
                    "poids_css_fichier": css.stat().st_size if css.exists() else None,
                    "poids_css": d["poids"]["css"], "poids_js": d["poids"]["js"], "poids_total": d["poids"]["total"],
                    "requetes_externes": d["poids"]["n_externes"], "cibles_sous_44_390": d["extra_390"]["cibles_sous_44"],
                    "css": d["css_signaux"],
                    "conformite": c["controles"], "conformite_score": c["score"],
                })
    (OUT / "design_runs.json").write_text(json.dumps(L, ensure_ascii=False, indent=1), encoding="utf-8")
    return L


def resume(L):
    res = {}
    for b in BRAS:
        for e in (1, 2, "tous"):
            S = [l for l in L if l["bras"] == b and (e == "tous" or l["ecran"] == e)]
            if not S:
                continue
            reg = {}
            for r in REGLES:
                v = [l["conformite"].get(r) for l in S if l["conformite"].get(r) is not None]
                reg[r] = f"{sum(1 for x in v if x)}/{len(v)}"
            res[f"{b} écran {e}"] = {
                "n": len(S), "cout_moy": moy([l["cout_usd"] for l in S]), "cout_min": min(l["cout_usd"] for l in S), "cout_max": max(l["cout_usd"] for l in S),
                "cout_total": round(sum(l["cout_usd"] for l in S), 4),
                "duree_moy_s": moy([l["duree_s"] for l in S]), "tours_moy": moy([l["tours"] for l in S]), "tokens_out_moy": moy([l["tokens_out"] for l in S]),
                "tokens_in_total_moy": moy([l["tokens_in_total"] for l in S]),
                "fonctionnel_complet": sum(1 for l in S if l["fonctionnel"].split("/")[0] == l["fonctionnel"].split("/")[1]),
                "axe_noeuds_moy": moy([l["axe_noeuds"] for l in S]), "detect_moy": moy([l["detect_impeccable"] for l in S]),
                "poids_css_moy": moy([l["poids_css"] for l in S]), "design_md_lu": sum(1 for l in S if l["design_md_lu"]),
                "skill_invoquee": sum(1 for l in S if l["skills"]), "refus_moy": moy([l["refus"] for l in S]),
                "conformite_score_moy": moy([l["conformite_score"]["vrais"] / l["conformite_score"]["applicables"] for l in S if l["conformite_score"]["applicables"]]),
                "conformite_par_regle": reg,
            }
    tot = {b: sum(l["cout_usd"] for l in L if l["bras"] == b) for b in BRAS}
    res["_surcout_b5_vs_b2"] = {
        "tous": round(moy([l["cout_usd"] for l in L if l["bras"] == "b5"]) / moy([l["cout_usd"] for l in L if l["bras"] == "b2"]) - 1, 4),
        "ecran1": round(moy([l["cout_usd"] for l in L if l["bras"] == "b5" and l["ecran"] == 1]) / moy([l["cout_usd"] for l in L if l["bras"] == "b2" and l["ecran"] == 1]) - 1, 4),
        "ecran2": round(moy([l["cout_usd"] for l in L if l["bras"] == "b5" and l["ecran"] == 2]) / moy([l["cout_usd"] for l in L if l["bras"] == "b2" and l["ecran"] == 2]) - 1, 4),
        "cout_total_usd": round(sum(tot.values()), 4)}
    (OUT / "design_resume.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    L = lignes()
    R = resume(L)
    for k, v in R.items():
        print(k, json.dumps(v, ensure_ascii=False))
