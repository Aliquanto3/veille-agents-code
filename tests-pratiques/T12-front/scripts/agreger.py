"""Agrège le volet 1 : détection par le sous-agent, par pytest, par axe-core, par l'oracle scripté ; faux positifs ; coûts.
Usage : uv run --no-project python agreger.py   -> donnees/volet1_resume.json + tableaux Markdown sur stdout"""
import json, math, re, statistics
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
DEFAUTS = {d["id"]: d for d in json.loads((Path(__file__).parent / "defauts.json").read_text(encoding="utf-8"))}


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - m) / d, (c + m) / d)


def lire_jsonl(chemin):
    if not chemin.exists():
        return []
    return [json.loads(l) for l in chemin.read_text(encoding="utf-8").splitlines() if l.strip()]


def rapport_agent(meta):
    m = re.search(r"\{.*\}", meta.get("result", ""), re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def verdicts(rap):
    out = {}
    if rap:
        for it in (rap.get("criteres") or []) + (rap.get("transverses") or []):
            out[it.get("id")] = (it.get("verdict"), it.get("preuve", ""))
    return out


def main():
    runs = lire_jsonl(ICI / "donnees" / "verif_runs.jsonl")
    # dernière exécution valide par version
    par_id = {}
    for r in runs:
        if not r["temoin"] and r["id"] not in DEFAUTS:
            continue  # exécutions écartées (d13 initial, refusé car visible par pytest)
        par_id[r["run"]] = r
    pyt = {}
    for f in ("pytest_defauts_lot1.jsonl", "pytest_defauts_lot2.jsonl", "pytest_defauts_lot3.jsonl"):
        for r in lire_jsonl(ICI / "donnees" / f):
            pyt[r["id"]] = r
    ofinal = {r["id"]: r for r in lire_jsonl(ICI / "donnees" / "oracle_final.jsonl")}
    lignes, resume = [], {"versions": {}}
    base_axe = {}
    for _k, r in par_id.items():
        if r["temoin"]:
            base_axe[r["story"]] = r.get("axe", {})
    n_def = n_det = n_det_oracle = n_det_axe = n_pyt_voit = n_all = n_all_det = 0
    fp_temoins, fp_def, couts_def, couts_tem, durees = [], [], [], [], []
    for cle, r in sorted(par_id.items(), key=lambda kv: (kv[1]["temoin"], kv[1]["id"], kv[0])):
        ident = r["id"] if not r["temoin"] else cle
        rap = rapport_agent(r)
        v = verdicts(rap)
        fails = {k for k, (vd, _) in v.items() if vd == "FAIL"}
        cibles = set(r.get("cibles") or [])
        oid = r["id"] if not r["temoin"] else r["id"]
        ko_oracle = set((ofinal.get(oid) or {}).get("ko", []))
        axe = r.get("axe") or {}
        ba = base_axe.get(r["story"], {})
        axe_nouveau = {p: sorted(set(x) - set(ba.get(p, []))) for p, x in axe.items() if set(x) - set(ba.get(p, []))}
        info = {"story": r["story"], "temoin": r["temoin"], "cout": r.get("cout_usd"), "duree_s": r.get("duree_mur_s"),
                "tours": r.get("tours"), "appels_outils": sum((r.get("outils") or {}).values()), "statut": r.get("statut"),
                "rapport_json_ok": rap is not None, "fails_agent": sorted(fails), "ko_oracle": sorted(ko_oracle),
                "axe_nouveaux": axe_nouveau, "pytest_code": (pyt.get(ident) or {}).get("code")}
        if r.get("cout_usd") is not None:
            (couts_tem if r["temoin"] else couts_def).append(r["cout_usd"]); durees.append(r["duree_mur_s"])
        if r["temoin"]:
            info["faux_positifs"] = sorted(fails)
            fp_temoins.append((ident, sorted(fails)))
        else:
            cl = [c for c in cibles]
            detecte = any((c in fails) for c in cl)
            visible_oracle = any(any(k.startswith(c) for k in ko_oracle) for c in cl)
            info.update({"cibles": cl, "detecte_agent": detecte, "visible_oracle": visible_oracle,
                         "detecte_axe": bool(axe_nouveau), "pytest_voit": (pyt.get(ident) or {}).get("code") not in (0, None)})
            info["faux_positifs"] = sorted(fails - set(cl))
            principal = (not info["pytest_voit"]) and visible_oracle
            info["principal"] = principal
            n_all += 1; n_all_det += detecte
            if principal:
                n_def += 1; n_det += detecte; n_det_oracle += visible_oracle; n_det_axe += bool(axe_nouveau)
            n_pyt_voit += info["pytest_voit"]
            fp_def.append((ident, info["faux_positifs"]))
        resume["versions"][ident] = info
    lo, hi = wilson(n_det, n_def)
    resume["synthese"] = {
        "defauts_tous": n_all, "detectes_tous": n_all_det, "defauts": n_def, "detectes_agent": n_det, "rappel": round(n_det / n_def, 3) if n_def else None, "wilson95": [round(lo, 3), round(hi, 3)],
        "visibles_oracle": n_det_oracle, "detectes_axe": n_det_axe, "vus_par_pytest": n_pyt_voit,
        "temoins": len(fp_temoins), "temoins_avec_faux_positif": sum(1 for _, f in fp_temoins if f), "fp_temoins": fp_temoins,
        "defauts_avec_critere_non_cible_en_fail": sum(1 for _, f in fp_def if f),
        "cout_moyen_defaut": round(statistics.mean(couts_def), 3) if couts_def else None,
        "cout_moyen_temoin": round(statistics.mean(couts_tem), 3) if couts_tem else None,
        "cout_moyen_tous": round(statistics.mean(couts_def + couts_tem), 3) if couts_def + couts_tem else None,
        "cout_total": round(sum(couts_def + couts_tem), 3), "duree_moyenne_s": round(statistics.mean(durees), 1) if durees else None,
    }
    (ICI / "donnees" / "volet1_resume.json").write_text(json.dumps(resume, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(resume["synthese"], ensure_ascii=False, indent=1))
    print("| Version | Défaut | Cible | FAIL de l'agent | Détecté | Oracle KO | Coût | Durée | Faux FAIL |")
    print("|---|---|---|---|---|---|---|---|---|")
    for ident, i in resume["versions"].items():
        d = DEFAUTS.get(ident, {})
        print(f"| {ident} | {d.get('classe', 'témoin')} | {','.join(i.get('cibles', []))} | {','.join(i['fails_agent']) or '-'} | "
              f"{'oui' if i.get('detecte_agent') else ('non' if not i['temoin'] else '-')} | {','.join(i['ko_oracle']) or '-'} | "
              f"{i['cout']} | {i['duree_s']} | {','.join(i['faux_positifs']) or '-'} |")


if __name__ == "__main__":
    main()
