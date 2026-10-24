"""Agrège les mesures du volet A (design) et du volet B (navigateur) ; écrit data dans tests-pratiques/T7/donnees."""
import json, statistics as st, sys
from pathlib import Path

T7 = Path(__file__).resolve().parent.parent
OUT = Path(r"C:\Users\Utilisateur\Documents\GitHub\veille-agents-code\tests-pratiques\T7\donnees")
OUT.mkdir(parents=True, exist_ok=True)
BRAS = ["b1-aucune", "b2-frontend-design", "b3-impeccable", "b4-hallmark"]


def ld(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def design():
    lignes = []
    for b in BRAS:
        for r in (1, 2, 3, 4):
            nom = f"{b}_r{r}"
            meta = T7 / "arms" / nom / "_claude.meta.json"
            mes = T7 / "resultats_mesures" / nom / "mesures.json"
            if not meta.exists() or not mes.exists():
                print("manquant", nom)
                continue
            m, d = ld(meta), ld(mes)
            f = d["fonctionnel"]
            det = d["impeccable_detect"]
            constats = (d["axe"]["noeuds_total"] + (det["n"] or 0) + d["focus"]["sans_indicateur"]
                        + d["contraste_perso"]["sous_seuil"] + (1 if d["debordement_390"] else 0))
            lignes.append({
                "bras": b, "rep": r, "serie": "notation" if r <= 2 else "supplementaire",
                "cout_usd": round(m["cout_usd"], 4), "duree_s": m["duree_s"], "tours": m["tours"],
                "tokens_out": m["tokens_out"], "cache_creation": m["cache_creation"], "cache_read": m["cache_read"],
                "tokens_in_total": (m["tokens_in"] or 0) + m["cache_creation"] + m["cache_read"],
                "skills": m["skills_invoquees"], "refus": m["refus_permission"], "erreurs_outils": m["tool_results_en_erreur"],
                "fonctionnel": f"{f['_reussis']}/{f['_total']}",
                "axe_violations": d["axe"]["violations_total"], "axe_noeuds": d["axe"]["noeuds_total"],
                "detect_impeccable": det["n"], "detect_regles": sorted({x.get("antipattern") for x in (det["brut"] or [])}),
                "contraste_min": d["contraste_perso"]["ratio_min"], "contraste_sous_seuil": d["contraste_perso"]["sous_seuil"],
                "focus_sans_indicateur": d["focus"]["sans_indicateur"], "focusables": d["focus"]["focusables"],
                "debordement_390": d["debordement_390"],
                "poids_html": d["poids"]["html"], "poids_css": d["poids"]["css"], "poids_js": d["poids"]["js"], "poids_total": d["poids"]["total"],
                "requetes_externes": d["poids"]["n_externes"],
                "cibles_sous_44_390": d["extra_390"]["cibles_sous_44"], "police_min_px": d["extra_390"]["police_min_px"],
                "css": d["css_signaux"], "polices": d["polices"][:3],
                "constats_deterministes": constats,
            })
    (OUT / "design_runs.json").write_text(json.dumps(lignes, ensure_ascii=False, indent=1), encoding="utf-8")
    return lignes


def moy(xs):
    xs = [x for x in xs if x is not None]
    return round(st.mean(xs), 3) if xs else None


def resume_design(lignes):
    res = {}
    for b in BRAS:
        for portee, filtre in (("n=2", lambda l: l["rep"] <= 2), ("n=4", lambda l: True)):
            L = [l for l in lignes if l["bras"] == b and filtre(l)]
            res[f"{b} ({portee})"] = {
                "n": len(L), "cout_moy": moy([l["cout_usd"] for l in L]), "cout_min": min(l["cout_usd"] for l in L), "cout_max": max(l["cout_usd"] for l in L),
                "duree_moy_s": moy([l["duree_s"] for l in L]), "tokens_out_moy": moy([l["tokens_out"] for l in L]),
                "tokens_in_total_moy": moy([l["tokens_in_total"] for l in L]), "tours_moy": moy([l["tours"] for l in L]),
                "axe_noeuds_moy": moy([l["axe_noeuds"] for l in L]), "detect_moy": moy([l["detect_impeccable"] for l in L]),
                "constats_moy": moy([l["constats_deterministes"] for l in L]),
                "poids_total_moy": moy([l["poids_total"] for l in L]), "poids_css_moy": moy([l["poids_css"] for l in L]),
                "fonctionnel_complet": sum(1 for l in L if l["fonctionnel"].split("/")[0] == l["fonctionnel"].split("/")[1]),
                "skill_invoquee": sum(1 for l in L if l["skills"]), "refus_moy": moy([l["refus"] for l in L]),
            }
    (OUT / "design_resume.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


def parcours():
    lignes = []
    for d in sorted((T7 / "parcours" / "runs").iterdir()):
        mp = d / "_claude.meta.json"
        if not mp.exists():
            continue
        m = ld(mp)
        outil, serie = d.name.rsplit("_", 1)
        sc = m.get("score", {})
        lignes.append({
            "run": d.name, "outil": outil, "serie": {"r": "stricte", "e": "elargie"}[serie[0]], "rep": int(serie[1:]),
            "reussite": sc.get("reussite"), "cout_usd": round(m["cout_usd"], 4), "duree_s": m["duree_s"], "tours": m["tours"],
            "tokens_out": m["tokens_out"], "tokens_in_total": (m["tokens_in"] or 0) + m["cache_creation"] + m["cache_read"],
            "cache_creation": m["cache_creation"], "cache_read": m["cache_read"],
            "appels_outils": sum(m["outils"].values()), "outils": m["outils"], "refus": m["refus_permission"], "erreurs_outils": m["tool_results_en_erreur"],
            "detail": {k: v for k, v in sc.items() if k != "reussite"},
        })
    (OUT / "parcours_runs.json").write_text(json.dumps(lignes, ensure_ascii=False, indent=1), encoding="utf-8")
    res = {}
    for serie in ("stricte", "elargie"):
        for o in ("playwright-cli", "playwright-mcp", "agent-browser"):
            L = [l for l in lignes if l["outil"] == o and l["serie"] == serie]
            if not L:
                continue
            res[f"{o} ({serie})"] = {
                "n": len(L), "reussites": sum(1 for l in L if l["reussite"]),
                "cout_moy": moy([l["cout_usd"] for l in L]), "cout_total": round(sum(l["cout_usd"] for l in L), 4),
                "cout_succes_moy": moy([l["cout_usd"] for l in L if l["reussite"]]),
                "duree_moy_s": moy([l["duree_s"] for l in L]), "tours_moy": moy([l["tours"] for l in L]),
                "tokens_out_moy": moy([l["tokens_out"] for l in L]), "tokens_in_total_moy": moy([l["tokens_in_total"] for l in L]),
                "appels_outils_moy": moy([l["appels_outils"] for l in L]), "refus_total": sum(l["refus"] for l in L),
                "erreurs_outils_total": sum(l["erreurs_outils"] for l in L),
            }
    (OUT / "parcours_resume.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return lignes, res


if __name__ == "__main__":
    L = design()
    R = resume_design(L)
    for k, v in R.items():
        print(k, json.dumps(v, ensure_ascii=False))
    P, PR = parcours()
    print()
    for k, v in PR.items():
        print(k, json.dumps(v, ensure_ascii=False))
