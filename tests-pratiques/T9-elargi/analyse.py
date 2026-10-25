"""T9 elargi : compare les bras (heuristique, Jev, LLM) pour predire derapage, cout et defaut de revue d'une story.

Entrees : ``etiquettes.csv`` (construire_donnees.py), ``scores_*.json`` (scorer.py), ``budget.json``.
Sorties : ``resultats.json`` (agregats), ``tableaux.md`` (tableaux prets a coller dans le rapport), resume sur la sortie standard.

Etiquettes
- principales : ``derapage`` (appels > 2 x mediane du depot), ``cout80`` (cout > 80e centile du depot), ``defaut_revue`` ;
- exploratoires : ``derapage_par_agent`` (critere de T1) et ``haut20`` (appels > 80e centile du depot).

Bras : heuristique (regression logistique L2, C = 1, validation croisee stratifiee 5 plis x 10 ; seuil sur la seule
longueur) sur log(caracteres), criteres, elements de liste, fichiers cites, centres et reduits par depot (sans etiquette) ;
Jev (deux versions) ; gpt-6-luna (deux executions et leur moyenne).

Mesures : AUC et IC a 95 % (bootstrap stratifie), precision et rappel a 20 % d'alertes au plus (ex aequo non separes), AUC
intra-depot, AUC et precision/rappel par depot, ecart d'AUC a l'heuristique de reference (bootstrap apparie). Critere : AUC
> 0,7 et au moins 0,05 au-dessus de la reference. Analyse de puissance : positifs necessaires pour detecter AUC = 0,65 contre
0,5 (Hanley et McNeil, verifiee par simulation binormale).

Groupes : les seuils des etiquettes, le centrage de l'heuristique et l'AUC intra-groupe se font par ``groupe`` (colonne de
``etiquettes.csv`` : ``<depot>`` pour l'ere kit, ``<depot>/avant-kit`` pour les stories d'avant le kit ; sans colonne, le depot).
``--ere kit`` restreint l'analyse aux stories de l'ere kit (sorties ``resultats_kit.json`` et ``tableaux_kit.md``).

Usage : uv run --no-project --with numpy --with scikit-learn --with scipy python analyse.py [--ere kit]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm, rankdata
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RepeatedStratifiedKFold

ICI = Path(__file__).resolve().parent
ALERTES = 0.20
BOOT = 3000
RNG = np.random.default_rng(20261024)
CARAC = ["n_car", "n_criteres", "n_puces", "n_fichiers"]
PRINCIPALES = ["derapage", "cout80", "defaut_revue"]
EXPLORATOIRES = ["derapage_par_agent", "haut20"]
# etiquette -> champ de probabilite demande aux modeles
CHAMP = {"derapage": "p_derapage", "cout80": "p_cout80", "defaut_revue": "p_defaut_revue",
         "derapage_par_agent": "p_derapage", "haut20": "p_derapage"}
FICHIERS = {"jev_latest": ["scores_jev_latest.json"], "jev_1_13": ["scores_jev_1_13.json"], "luna": ["scores_luna_r1.json", "scores_luna_r2.json"]}
LIBELLE = {"heuristique_longueur": "Heuristique : longueur seule", "heuristique_lr": "Heuristique : régression logistique (CV)",
           "jev_latest": "Jev latest", "jev_1_13": "Jev 1,13", "luna_r1": "gpt-6-luna, exéc. 1", "luna_r2": "gpt-6-luna, exéc. 2",
           "luna_moyenne": "gpt-6-luna, moyenne"}
ORDRE = ["heuristique_longueur", "heuristique_lr", "jev_latest", "jev_1_13", "luna_r1", "luna_r2", "luna_moyenne"]
NOM_ETIQ = {"derapage": "dérapage (appels > 2 × médiane du dépôt)", "cout80": "coût au-dessus du 80e centile du dépôt",
            "defaut_revue": "défaut de revue (constat medium ou high corrigé)", "derapage_par_agent": "dérapage par agent (critère de T1)",
            "haut20": "appels au-dessus du 80e centile du dépôt"}


def auc(y, s) -> float:
    y = np.asarray(y)
    n1 = int(y.sum())
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rankdata(s)
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def _tirages(y, boot):
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    for _ in range(boot):
        yield np.concatenate([RNG.choice(pos, len(pos)), RNG.choice(neg, len(neg))])


def auc_ic(y, s, boot=BOOT):
    y, s = np.asarray(y), np.asarray(s)
    if y.sum() == 0 or y.sum() == len(y):
        return float("nan"), float("nan"), float("nan")
    v = [auc(y[i], s[i]) for i in _tirages(y, boot)]
    return auc(y, s), float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def delta_ic(y, s_a, s_b, boot=BOOT):
    y, s_a, s_b = np.asarray(y), np.asarray(s_a), np.asarray(s_b)
    d = [auc(y[i], s_a[i]) - auc(y[i], s_b[i]) for i in _tirages(y, boot)]
    return auc(y, s_a) - auc(y, s_b), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def alertes(y, s, part=ALERTES):
    """Precision et rappel avec au plus ``part`` d'alertes (les ex aequo ne sont pas separes)."""
    y, s = np.asarray(y), np.asarray(s)
    n = len(y)
    maxi = int(np.floor(part * n))
    choisi = np.zeros(n, bool)
    for v in np.unique(s)[::-1]:
        g = s == v
        if choisi.sum() + g.sum() > maxi:
            break
        choisi |= g
    k = int(choisi.sum())
    tp = int(y[choisi].sum())
    return {"alertes": k, "vrais_positifs": tp, "precision": round(tp / k, 3) if k else None,
            "rappel": round(tp / y.sum(), 3) if y.sum() else None}


def groupes(depots):
    return {d: np.array([x == d for x in depots]) for d in sorted(set(depots))}


def centrer_depot(valeurs, depots):
    valeurs = np.asarray(valeurs, float)
    sortie = np.zeros_like(valeurs)
    for m in groupes(depots).values():
        v = valeurs[m]
        sd = v.std()
        sortie[m] = (v - v.mean()) / sd if sd > 0 else 0.0
    return sortie


def rang_depot(valeurs, depots):
    valeurs = np.asarray(valeurs, float)
    sortie = np.zeros_like(valeurs)
    for m in groupes(depots).values():
        r = rankdata(valeurs[m]) - 1
        sortie[m] = r / max(m.sum() - 1, 1)
    return sortie


def spearman(a, b):
    return float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])


def heuristique_lr(X, y, repetitions=10, plis=5):
    """Probabilites hors echantillon moyennees sur les repetitions de la validation croisee."""
    n = len(y)
    somme, compte = np.zeros(n), np.zeros(n)
    cv = RepeatedStratifiedKFold(n_splits=plis, n_repeats=repetitions, random_state=7)
    for a, b in cv.split(X, y):
        m = LogisticRegression(C=1.0, max_iter=1000).fit(X[a], y[a])
        somme[b] += m.predict_proba(X[b])[:, 1]
        compte[b] += 1
    return somme / compte


# ---------------- analyse de puissance ----------------
def var_hm(a, n1, n0):
    """Variance de l'AUC (Hanley et McNeil, 1982) pour n1 positifs et n0 negatifs."""
    q1, q2 = a / (2 - a), 2 * a * a / (1 + a)
    return (a * (1 - a) + (n1 - 1) * (q1 - a * a) + (n0 - 1) * (q2 - a * a)) / (n1 * n0)


def puissance(a1, n1, n0, alpha=0.05, a0=0.5):
    """Puissance (test bilateral) pour detecter AUC = a1 contre a0 avec n1 positifs et n0 negatifs."""
    s0, s1 = np.sqrt(var_hm(a0, n1, n0)), np.sqrt(var_hm(a1, n1, n0))
    z = norm.ppf(1 - alpha / 2)
    return float(norm.cdf((a1 - a0 - z * s0) / s1) + norm.cdf((a0 - a1 - z * s0) / s1))


def positifs_necessaires(a1, prevalence, alpha=0.05, puiss=0.8):
    r = (1 - prevalence) / prevalence
    for n1 in range(3, 5000):
        if puissance(a1, n1, max(2, int(round(n1 * r))), alpha) >= puiss:
            return n1
    return None


def positifs_pour_ecart(prevalence, a_haut=0.70, a_bas=0.65, r=0.5, z=2.8):
    """Positifs necessaires pour distinguer deux AUC correlees (ecart a_haut - a_bas) ; z = 1,96 + 0,84 (5 % bilateral, 80 %).
    Variance de l'ecart : v1 + v2 - 2 r sqrt(v1 v2), ``r`` etant la correlation entre les deux estimations (hypothese)."""
    k = (1 - prevalence) / prevalence
    for n1 in range(5, 20000):
        n0 = max(2, int(round(n1 * k)))
        v1, v2 = var_hm(a_haut, n1, n0), var_hm(a_bas, n1, n0)
        if (a_haut - a_bas) / np.sqrt(v1 + v2 - 2 * r * np.sqrt(v1 * v2)) >= z:
            return n1
    return None


def auc_detectable(n1, n0, alpha=0.05, puiss=0.8):
    """Plus petite AUC detectable (puissance donnee) avec n1 positifs et n0 negatifs."""
    for a in np.arange(0.51, 0.999, 0.005):
        if puissance(a, n1, n0, alpha) >= puiss:
            return round(float(a), 3)
    return None


def simulation_puissance(a1, n1, n0, essais=2000):
    """Verification par simulation binormale : part des essais ou l'IC a 95 % (Hanley et McNeil) exclut 0,5."""
    d = np.sqrt(2) * norm.ppf(a1)
    rng = np.random.default_rng(11)
    ok = 0
    for _ in range(essais):
        s = np.concatenate([rng.normal(d, 1, n1), rng.normal(0, 1, n0)])
        y = np.concatenate([np.ones(n1, int), np.zeros(n0, int)])
        a = auc(y, s)
        se = np.sqrt(var_hm(a, n1, n0))
        ok += int(a - 1.96 * se > 0.5)
    return ok / essais


def charger_scores(nom):
    p = ICI / nom
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ere", choices=["toutes", "kit"], default="toutes", help="kit : seulement les stories de l'ere kit (groupe sans /avant-kit)")
    suffixe = "" if ap.parse_args().ere == "toutes" else "_kit"
    with open(ICI / "etiquettes.csv", encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    for r in lignes:
        r.setdefault("groupe", r["depot"])
    if suffixe:
        lignes = [r for r in lignes if not r["groupe"].endswith("/avant-kit")]
    cles = [r["cle"] for r in lignes]
    depots = [r["groupe"] for r in lignes]
    n = len(lignes)
    liste_depots = sorted(set(depots))
    appels = np.array([float(r["appels"]) for r in lignes])
    cout = np.array([float(r["cout_usd"]) for r in lignes])
    etiq = {e: np.array([int(r[e]) for r in lignes]) for e in PRINCIPALES[:2] + EXPLORATOIRES}
    rev_ok = np.array([r["defaut_revue"] != "" for r in lignes])
    etiq["defaut_revue"] = np.array([int(r["defaut_revue"]) if r["defaut_revue"] != "" else -1 for r in lignes])
    tous = PRINCIPALES + EXPLORATOIRES
    masque = {e: (rev_ok if e == "defaut_revue" else np.ones(n, bool)) for e in tous}

    res: dict = {"n": n, "depots": {d: int(sum(1 for x in depots if x == d)) for d in liste_depots}}
    res["positifs"] = {e: int(etiq[e][masque[e]].sum()) for e in tous}
    res["n_par_etiquette"] = {e: int(masque[e].sum()) for e in tous}
    res["positifs_par_depot"] = {e: {d: [int(etiq[e][masque[e] & (np.array(depots) == d)].sum()), int((masque[e] & (np.array(depots) == d)).sum())] for d in liste_depots} for e in tous}

    # ---- heuristique
    brut = np.array([[float(r[c]) for c in CARAC] for r in lignes])
    brut[:, 0] = np.log(brut[:, 0])
    X = np.column_stack([centrer_depot(brut[:, j], depots) for j in range(brut.shape[1])])
    longueur = X[:, 0]
    scores: dict[str, dict[str, np.ndarray]] = {"heuristique_longueur": {}, "heuristique_lr": {}}  # scores sur le sous-ensemble masque[e]
    for e in tous:
        m = masque[e]
        scores["heuristique_longueur"][e] = longueur[m]
        scores["heuristique_lr"][e] = heuristique_lr(X[m], etiq[e][m])

    # ---- bras modeles
    couts, latences, stab, calib, manq = {}, {}, {}, {}, {}
    for nom, fs in FICHIERS.items():
        runs = [r for r in (charger_scores(f) for f in fs) if r]
        if not runs:
            continue
        arr = {c: [] for c in set(CHAMP.values())}
        c_tot, lat, manquants = 0.0, [], 0
        for r in runs:
            sc = r["scores"]
            for champ in arr:
                arr[champ].append([np.nan if sc.get(k, {}).get(champ) is None else sc[k][champ] for k in cles])
            manquants += sum(1 for k in cles if sc.get(k, {}).get("p_derapage") is None)
            c_tot += sum(v.get("cout", 0.0) for v in sc.values())
            lat += [v["latence_s"] for v in sc.values() if v.get("latence_s") is not None]
        arr = {c: np.array(v, float) for c, v in arr.items()}
        couts[nom] = {"cout_total_usd": round(c_tot, 4), "cout_par_story_et_run_usd": round(c_tot / (len(runs) * n), 6), "runs": len(runs)}
        latences[nom] = {"p50_s": round(float(np.median(lat)), 2), "p90_s": round(float(np.percentile(lat, 90)), 2)}
        manq[nom] = manquants
        variantes = {f"{nom}_r{i + 1}": {c: arr[c][i] for c in arr} for i in range(len(runs))} if len(runs) > 1 else {nom: {c: arr[c][0] for c in arr}}
        if len(runs) > 1:
            variantes[f"{nom}_moyenne"] = {c: np.nanmean(arr[c], axis=0) for c in arr}
            ok = ~np.isnan(arr["p_derapage"]).any(axis=0)
            stab[nom] = {c: {"spearman_entre_runs": round(spearman(arr[c][0][ok], arr[c][1][ok]), 3),
                             "ecart_moyen_abs_proba": round(float(np.mean(np.abs(arr[c][0][ok] - arr[c][1][ok]))), 3)} for c in sorted(arr)}
        for v, par_champ in variantes.items():
            scores[v] = {}
            for e in tous:
                p = par_champ[CHAMP[e]]
                scores[v][e] = np.where(np.isnan(p), np.nanmedian(p), p)[masque[e]]
            calib[v] = {c: round(float(np.nanmean(par_champ[c])), 3) for c in sorted(par_champ)}
    res["cout"], res["latence"], res["stabilite"], res["scores_manquants"] = couts, latences, stab, manq
    res["calibration_proba_moyenne"] = calib
    res["taux_observes"] = {e: round(res["positifs"][e] / res["n_par_etiquette"][e], 3) for e in tous}

    # ---- metriques
    table: dict = {}
    for v in scores:
        table[v] = {}
        for e in tous:
            y = etiq[e][masque[e]]
            s = scores[v][e]
            dep = [d for d, ok in zip(depots, masque[e]) if ok]
            a, lo, hi = auc_ic(y, s)
            ligne = {"auc": round(a, 3), "ic95": [round(lo, 3), round(hi, 3)], "alertes20": alertes(y, s),
                     "auc_intra_depot": round(auc(y, rang_depot(s, dep)), 3), "par_depot": {}}
            for d, m in groupes(dep).items():
                yd, sd_ = y[m], s[m]
                npos = int(yd.sum())
                ligne["par_depot"][d] = {"n": int(m.sum()), "positifs": npos,
                                         "auc": round(auc(yd, sd_), 3) if 2 <= npos <= m.sum() - 2 else None,
                                         "alertes20": alertes(yd, sd_) if npos >= 1 else None}
            table[v][e] = ligne
    comparaisons: dict = {}
    for e in tous:
        y = etiq[e][masque[e]]
        cand = {h: table[h][e]["auc"] for h in ("heuristique_lr", "heuristique_longueur")}
        ref = max(cand, key=cand.get)
        comparaisons[e] = {"reference": ref, "auc_reference": cand[ref], "bras": {}}
        for v in scores:
            if v.startswith("heuristique"):
                continue
            d, lo, hi = delta_ic(y, scores[v][e], scores[ref][e])
            a = table[v][e]["auc"]
            comparaisons[e]["bras"][v] = {"auc": a, "delta_vs_ref": round(d, 3), "delta_ic95": [round(lo, 3), round(hi, 3)],
                                          "critere": bool(a > 0.7 and d >= 0.05)}
    res["table"], res["comparaisons"] = table, comparaisons

    # ---- diagnostics continus (derapage et cout)
    diag = {}
    for v in scores:
        s = scores[v]["derapage"]
        s_c = scores[v]["cout80"]
        par = lambda s_, cible: round(float(np.mean([spearman(s_[m], cible[m]) for m in groupes(depots).values()])), 3)  # noqa: E731
        diag[v] = {"spearman_derapage_avec_longueur": round(spearman(s, brut[:, 0]), 3), "spearman_derapage_avec_appels": round(spearman(s, appels), 3),
                   "spearman_derapage_avec_appels_intra_depot": par(s, appels),
                   "spearman_cout80_avec_cout": round(spearman(s_c, cout), 3), "spearman_cout80_avec_cout_intra_depot": par(s_c, cout)}
    res["diagnostics_continus"] = diag
    res["spearman_longueur_appels"] = round(spearman(brut[:, 0], appels), 3)
    res["spearman_longueur_cout"] = round(spearman(brut[:, 0], cout), 3)

    # ---- sensibilites
    sens = {}
    fam = np.array([r.get("familles", "") for r in lignes])
    sonnet = fam == "sonnet"
    sens["stories_sonnet_seul"] = {"n": int(sonnet.sum())}
    for e in ("derapage", "cout80"):
        y = etiq[e]
        if y[sonnet].sum() >= 3:
            sens["stories_sonnet_seul"][e] = {"positifs": int(y[sonnet].sum()),
                                              **{v: round(auc(y[sonnet], scores[v][e][sonnet]), 3) for v in ("heuristique_longueur", "jev_latest", "luna_r1") if v in scores}}
    avant = np.array([r["source_epics"] == "avant" for r in lignes])
    sens["version_epics"] = {"avant": int(avant.sum()), "jour": int((~avant).sum())}
    res["sensibilites"] = sens

    # ---- puissance
    puis = {}
    for e in PRINCIPALES + EXPLORATOIRES:
        n1, tot = res["positifs"][e], res["n_par_etiquette"][e]
        n0 = tot - n1
        prev = n1 / tot
        besoin = positifs_necessaires(0.65, prev)
        puis[e] = {"positifs": n1, "negatifs": n0, "prevalence": round(prev, 3),
                   "positifs_necessaires_auc065": besoin,
                   "stories_necessaires_auc065": int(round(besoin / prev)) if besoin else None,
                   "puissance_actuelle_auc065": round(puissance(0.65, n1, n0), 3),
                   "auc_detectable_actuelle_80pct": auc_detectable(n1, n0),
                   "positifs_necessaires_ecart_005_vs_heuristique": positifs_pour_ecart(prev)}
    # verification par simulation pour l'etiquette principale de rarete (positifs necessaires) et la plus frequente
    ref_e = "derapage"
    b = puis[ref_e]["positifs_necessaires_auc065"]
    prev = puis[ref_e]["prevalence"]
    puis["verification_simulation"] = {"etiquette": ref_e, "positifs": b, "negatifs": int(round(b * (1 - prev) / prev)),
                                       "puissance_simulee": round(simulation_puissance(0.65, b, int(round(b * (1 - prev) / prev))), 3)}
    puis["hypotheses_ecart"] = "ecart de 0,05 (AUC 0,70 contre 0,65) entre deux bras correles (r = 0,5 supposee), 5 % bilateral, puissance 80 %"
    puis["hypotheses"] = "AUC 0,65 contre 0,5, test bilateral alpha 5 %, puissance 80 %, variance de Hanley et McNeil, prevalence observee"
    res["puissance"] = puis
    try:
        res["budget"] = json.loads((ICI / "budget.json").read_text(encoding="utf-8"))
    except OSError:
        res["budget"] = None
    (ICI / f"resultats{suffixe}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    (ICI / f"tableaux{suffixe}.md").write_text(tableaux_md(res), encoding="utf-8")

    print(f"n={n} positifs={res['positifs']}")
    for e in tous:
        print(f"\n== {e} (reference {comparaisons[e]['reference']} AUC {comparaisons[e]['auc_reference']})")
        for v in ORDRE:
            t = table.get(v, {}).get(e)
            if t:
                al = t["alertes20"]
                print(f"{v:22s} AUC {t['auc']:.3f} [{t['ic95'][0]:.2f};{t['ic95'][1]:.2f}] intra {t['auc_intra_depot']:.3f} alertes {al['alertes']} P={al['precision']} R={al['rappel']}")
    print("\npuissance", json.dumps(puis, ensure_ascii=False))
    return 0


def fmt(x, d=2):
    return "n.d." if x is None else f"{x:.{d}f}".replace(".", ",")


def pct(x):
    return "n.d." if x is None else f"{round(100 * x)} %"


def tableaux_md(res: dict) -> str:
    out = []
    t, comp = res["table"], res["comparaisons"]
    out.append("### Positifs par étiquette et par dépôt (positifs / stories étiquetées)\n")
    deps = list(res["depots"])
    out.append("| Étiquette | Total | " + " | ".join(deps) + " |")
    out.append("|---|---|" + "---|" * len(deps))
    for e in PRINCIPALES + EXPLORATOIRES:
        out.append(f"| {NOM_ETIQ[e]} | {res['positifs'][e]} / {res['n_par_etiquette'][e]} | " + " | ".join(f"{res['positifs_par_depot'][e][d][0]} / {res['positifs_par_depot'][e][d][1]}" for d in deps) + " |")
    for e in PRINCIPALES + EXPLORATOIRES:
        out.append(f"\n### {NOM_ETIQ[e]} : {res['positifs'][e]} positifs sur {res['n_par_etiquette'][e]} (taux de base {pct(res['taux_observes'][e])})\n")
        out.append("| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes (≤ 20 %) | Vrais positifs | Précision | Rappel | Écart à la référence [IC] | Critère |")
        out.append("|---|---|---|---|---|---|---|---|---|")
        for v in ORDRE:
            if v not in t:
                continue
            x = t[v][e]
            al = x["alertes20"]
            c = comp[e]["bras"].get(v)
            ecart = f"{fmt(c['delta_vs_ref'])} [{fmt(c['delta_ic95'][0])} ; {fmt(c['delta_ic95'][1])}]" if c else ("référence" if v == comp[e]["reference"] else "")
            crit = ("oui" if c["critere"] else "non") if c else ""
            out.append(f"| {LIBELLE[v]} | {fmt(x['auc'], 3)} [{fmt(x['ic95'][0])} ; {fmt(x['ic95'][1])}] | {fmt(x['auc_intra_depot'], 3)} | {al['alertes']} | {al['vrais_positifs']} | {pct(al['precision'])} | {pct(al['rappel'])} | {ecart} | {crit} |")
    out.append("\n### AUC par dépôt (positifs entre parenthèses ; n.d. si moins de 2 positifs ou de 2 négatifs)\n")
    bras_depot = [v for v in ("heuristique_longueur", "jev_latest", "luna_r1") if v in t]
    out.append("| Étiquette | Bras | " + " | ".join(deps) + " |")
    out.append("|---|---|" + "---|" * len(deps))
    for e in PRINCIPALES:
        for v in bras_depot:
            cells = []
            for d in deps:
                pd = t[v][e]["par_depot"].get(d)
                cells.append("n.d." if not pd else f"{fmt(pd['auc'])} ({pd['positifs']})")
            out.append(f"| {e} | {LIBELLE[v]} | " + " | ".join(cells) + " |")
    out.append("\n### Précision et rappel à 20 % d'alertes par dépôt (vrais positifs / alertes ; positifs du dépôt)\n")
    out.append("| Étiquette | Bras | " + " | ".join(deps) + " |")
    out.append("|---|---|" + "---|" * len(deps))
    for e in PRINCIPALES:
        for v in bras_depot:
            cells = []
            for d in deps:
                pd = t[v][e]["par_depot"].get(d)
                al = pd and pd["alertes20"]
                cells.append("n.d." if not al or not al["alertes"] else f"{al['vrais_positifs']}/{al['alertes']} ; {pd['positifs']} pos.")
            out.append(f"| {e} | {LIBELLE[v]} | " + " | ".join(cells) + " |")
    out.append("\n### Analyse de puissance (AUC 0,65 contre 0,5, bilatéral 5 %, puissance 80 %)\n")
    out.append("| Étiquette | Positifs | Négatifs | Taux de base | Positifs nécessaires | Stories nécessaires | Puissance actuelle (AUC 0,65) | AUC détectable aujourd'hui (80 %) | Positifs pour un écart de 0,05 à l'heuristique |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    p = res["puissance"]
    for e in PRINCIPALES + EXPLORATOIRES:
        q = p[e]
        out.append(f"| {NOM_ETIQ[e]} | {q['positifs']} | {q['negatifs']} | {pct(q['prevalence'])} | {q['positifs_necessaires_auc065']} | {q['stories_necessaires_auc065']} | {pct(q['puissance_actuelle_auc065'])} | {fmt(q['auc_detectable_actuelle_80pct'])} | {q['positifs_necessaires_ecart_005_vs_heuristique']} |")
    v = p["verification_simulation"]
    out.append(f"\nVérification par simulation binormale ({v['etiquette']}, {v['positifs']} positifs et {v['negatifs']} négatifs, AUC 0,65) : puissance simulée {pct(v['puissance_simulee'])}.")
    out.append(f"\nDernière colonne : {p['hypotheses_ecart']}.")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.exit(main())
