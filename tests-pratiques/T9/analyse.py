"""T9 : compare les bras (heuristique, Jev, LLM) pour predire le derapage d'une story a partir de sa seule spec.

Entrees : ``etiquettes.csv`` (construire_donnees.py), ``scores_*.json`` (scorer.py), ``budget.json``.
Sortie : ``resultats.json`` (agregats seulement) et un resume sur la sortie standard.

Etiquettes
- principale  ``derapage`` : appels du dev-story de la story (reprises regroupees) > 2 x la mediane de son depot ;
- exploratoire ``derapage_par_agent`` : le plus long agent de la story > 2 x la mediane par agent du depot (critere de T1) ;
- exploratoire ``haut20`` : la story est dans les 20 % des plus longues de son depot (plus de positifs, meme question) ;
- secondaire  ``defaut_revue`` : la revue consigne un defaut medium ou high non rejete.

Heuristique : regression logistique (L2, C = 1) sur log(caracteres), nombre de criteres, de clauses, de fichiers cites, de
references AD, centres et reduits par depot (sans etiquette), validation croisee stratifiee repetee (5 x 10) ; et le seuil
sur la seule longueur (aucun apprentissage). Le meilleur des deux sert de reference (comparaison prudente).

Usage : uv run --no-project --with numpy --with scikit-learn python analyse.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold

ICI = Path(__file__).parent
ALERTES = 0.20
BOOT = 3000
RNG = np.random.default_rng(20261024)
CARAC = ["n_car", "n_criteres", "n_clauses", "n_fichiers", "n_ad"]


def charger():
    with open(ICI / "etiquettes.csv", encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    return lignes


def auc(y, s):
    y = np.asarray(y)
    if y.min() == y.max():
        return float("nan")
    return float(roc_auc_score(y, s))


def auc_ic(y, s, boot=BOOT):
    """AUC et intervalle de Bootstrap a 95 % (reechantillonnage stratifie)."""
    y, s = np.asarray(y), np.asarray(s)
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    vals = []
    for _ in range(boot):
        i = np.concatenate([RNG.choice(pos, len(pos)), RNG.choice(neg, len(neg))])
        vals.append(roc_auc_score(y[i], s[i]))
    return auc(y, s), float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def delta_ic(y, s_a, s_b, boot=BOOT):
    """Difference d'AUC (a - b) et IC a 95 % par Bootstrap apparie stratifie."""
    y, s_a, s_b = np.asarray(y), np.asarray(s_a), np.asarray(s_b)
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    d = []
    for _ in range(boot):
        i = np.concatenate([RNG.choice(pos, len(pos)), RNG.choice(neg, len(neg))])
        d.append(roc_auc_score(y[i], s_a[i]) - roc_auc_score(y[i], s_b[i]))
    return auc(y, s_a) - auc(y, s_b), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def alertes(y, s, part=ALERTES):
    """Precision et rappel quand on alerte sur au plus ``part`` des stories (les ex aequo ne sont pas separes)."""
    y, s = np.asarray(y), np.asarray(s)
    n = len(y)
    maxi = int(np.floor(part * n))
    ordre = np.argsort(-s, kind="stable")
    valeurs = np.unique(s)[::-1]
    choisi = np.zeros(n, bool)
    for v in valeurs:
        groupe = s == v
        if choisi.sum() + groupe.sum() > maxi:
            break
        choisi |= groupe
    k = int(choisi.sum())
    tp = int(y[choisi].sum())
    return {"alertes": k, "part_alertes": round(k / n, 3), "vrais_positifs": tp,
            "precision": round(tp / k, 3) if k else None, "rappel": round(tp / y.sum(), 3) if y.sum() else None}


def centrer_depot(valeurs, depots):
    valeurs = np.asarray(valeurs, float)
    sortie = np.zeros_like(valeurs)
    for d in set(depots):
        m = np.array([x == d for x in depots])
        v = valeurs[m]
        sd = v.std()
        sortie[m] = (v - v.mean()) / sd if sd > 0 else 0.0
    return sortie


def rang_depot(valeurs, depots):
    """Rang percentile des scores a l'interieur de chaque depot (pour l'AUC intra-depot)."""
    valeurs = np.asarray(valeurs, float)
    sortie = np.zeros_like(valeurs)
    for d in set(depots):
        m = np.array([x == d for x in depots])
        v = valeurs[m]
        r = v.argsort().argsort() + 0.0
        # ex aequo : rang moyen
        for x in np.unique(v):
            r[v == x] = r[v == x].mean()
        sortie[m] = r / max(len(v) - 1, 1)
    return sortie


def spearman(a, b):
    ra = np.asarray(a, float).argsort().argsort()
    rb = np.asarray(b, float).argsort().argsort()
    return float(np.corrcoef(ra, rb)[0, 1])


def heuristique_lr(X, y, repetitions=10, plis=5):
    """Probabilites hors echantillon moyennees sur les repetitions de la validation croisee."""
    n = len(y)
    somme, compte = np.zeros(n), np.zeros(n)
    aucs = []
    cv = RepeatedStratifiedKFold(n_splits=plis, n_repeats=repetitions, random_state=7)
    pas = []
    for k, (a, b) in enumerate(cv.split(X, y)):
        m = LogisticRegression(C=1.0, max_iter=1000).fit(X[a], y[a])
        somme[b] += m.predict_proba(X[b])[:, 1]
        compte[b] += 1
    # AUC par repetition (chaque repetition couvre tous les points une fois)
    cv2 = RepeatedStratifiedKFold(n_splits=plis, n_repeats=repetitions, random_state=7)
    oof = np.zeros(n)
    for k, (a, b) in enumerate(cv2.split(X, y)):
        m = LogisticRegression(C=1.0, max_iter=1000).fit(X[a], y[a])
        oof[b] = m.predict_proba(X[b])[:, 1]
        if (k + 1) % plis == 0:
            aucs.append(auc(y, oof))
    return somme / compte, float(np.mean(aucs)), float(np.std(aucs))


def charger_scores(nom):
    p = ICI / nom
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    lignes = charger()
    cles = [r["cle"] for r in lignes]
    depots = [r["depot"] for r in lignes]
    n = len(lignes)
    appels = np.array([float(r["appels"]) for r in lignes])
    # etiquette exploratoire : les 20 % les plus longues de chaque depot
    haut20 = np.zeros(n, int)
    for d in set(depots):
        idx = [i for i, x in enumerate(depots) if x == d]
        seuil = np.percentile(appels[idx], 80)
        for i in idx:
            haut20[i] = int(appels[i] > seuil)
    etiq = {
        "derapage": np.array([int(r["derapage"]) for r in lignes]),
        "derapage_par_agent": np.array([int(r["derapage_par_agent"]) for r in lignes]),
        "haut20": haut20,
    }
    rev_ok = np.array([r["defaut_revue"] != "" for r in lignes])
    defaut = np.array([int(r["defaut_revue"]) if r["defaut_revue"] != "" else -1 for r in lignes])

    # ---- heuristique
    brut = np.array([[float(r[c]) for c in CARAC] for r in lignes])
    brut[:, 0] = np.log(brut[:, 0])
    X = np.column_stack([centrer_depot(brut[:, j], depots) for j in range(brut.shape[1])])
    longueur = X[:, 0]
    res = {"n": n, "positifs": {k: int(v.sum()) for k, v in etiq.items()}, "defaut_revue_n": int(rev_ok.sum()), "defaut_revue_positifs": int((defaut == 1).sum()),
           "par_depot": {d: {"n": depots.count(d), "derapages": int(sum(etiq["derapage"][i] for i, x in enumerate(depots) if x == d))} for d in sorted(set(depots))}}
    bras: dict[str, dict] = {"heuristique_lr": {}, "heuristique_longueur": {}}
    scores: dict[str, dict[str, np.ndarray]] = {"heuristique_lr": {}, "heuristique_longueur": {}}
    for nom_e, y in etiq.items():
        s_lr, a_moy, a_sd = heuristique_lr(X, y)
        scores["heuristique_lr"][nom_e] = s_lr
        scores["heuristique_longueur"][nom_e] = longueur
        bras["heuristique_lr"][nom_e] = {"auc_cv_moyenne_repetitions": round(a_moy, 3), "ecart_type_repetitions": round(a_sd, 3)}
    # secondaire : defaut de revue
    yr = defaut[rev_ok]
    s_lr_r, a_moy, a_sd = heuristique_lr(X[rev_ok], yr)
    scores["heuristique_lr"]["defaut_revue"] = s_lr_r
    scores["heuristique_longueur"]["defaut_revue"] = longueur[rev_ok]
    bras["heuristique_lr"]["defaut_revue"] = {"auc_cv_moyenne_repetitions": round(a_moy, 3), "ecart_type_repetitions": round(a_sd, 3)}

    # ---- bras modeles
    fichiers = {
        "jev_latest": ["scores_jev_latest.json"], "jev_1_13": ["scores_jev_1_13.json"],
        "luna": ["scores_luna_r1.json", "scores_luna_r2.json"], "mimo": ["scores_mimo_r1.json", "scores_mimo_r2.json"],
    }
    couts, latences, stab = {}, {}, {}
    for nom, fs in fichiers.items():
        runs = [charger_scores(f) for f in fs]
        runs = [r for r in runs if r]
        if not runs:
            continue
        mat_d, mat_r, c, lat, manq = [], [], 0.0, [], 0
        for r in runs:
            sc = r["scores"]
            mat_d.append([sc.get(k, {}).get("p_derapage") for k in cles])
            mat_r.append([sc.get(k, {}).get("p_defaut_revue") for k in cles])
            manq += sum(1 for k in cles if sc.get(k, {}).get("p_derapage") is None)
            c += sum(v.get("cout", 0.0) for v in sc.values())
            lat += [v["latence_s"] for v in sc.values() if v.get("latence_s") is not None]
        arr_d = np.array([[np.nan if x is None else x for x in m] for m in mat_d], float)
        arr_r = np.array([[np.nan if x is None else x for x in m] for m in mat_r], float)
        couts[nom] = {"cout_total_usd": round(c, 4), "cout_par_story_et_run_usd": round(c / (len(runs) * n), 6), "runs": len(runs), "scores_manquants": manq}
        latences[nom] = {"p50_s": round(float(np.median(lat)), 2), "p90_s": round(float(np.percentile(lat, 90)), 2)}
        variantes = {f"{nom}_r{i + 1}": (arr_d[i], arr_r[i]) for i in range(len(runs))}
        if len(runs) > 1:
            variantes[f"{nom}_moyenne"] = (np.nanmean(arr_d, axis=0), np.nanmean(arr_r, axis=0))
            ok = ~np.isnan(arr_d).any(axis=0)
            stab[nom] = {"spearman_entre_runs": round(spearman(arr_d[0][ok], arr_d[1][ok]), 3),
                         "ecart_moyen_abs_proba": round(float(np.mean(np.abs(arr_d[0][ok] - arr_d[1][ok]))), 3)}
        for v, (d_, r_) in variantes.items():
            scores[v] = {}
            bras[v] = {}
            for nom_e in etiq:
                scores[v][nom_e] = np.where(np.isnan(d_), np.nanmedian(d_), d_)
            scores[v]["defaut_revue"] = np.where(np.isnan(r_[rev_ok]), np.nanmedian(r_), r_[rev_ok])
    res["cout"], res["latence"], res["stabilite"] = couts, latences, stab

    # ---- metriques
    table = {}
    for v in bras.keys() | set(scores):
        table[v] = {}
        for nom_e in list(etiq) + ["defaut_revue"]:
            s = scores[v].get(nom_e)
            if s is None:
                continue
            y = etiq[nom_e] if nom_e != "defaut_revue" else yr
            dep = depots if nom_e != "defaut_revue" else [d for d, ok in zip(depots, rev_ok) if ok]
            a, lo, hi = auc_ic(y, s)
            ligne = {"auc": round(a, 3), "ic95": [round(lo, 3), round(hi, 3)], "alertes20": alertes(y, s)}
            # AUC intra-depot (rang percentile dans chaque depot) : retire l'effet de niveau entre depots
            ligne["auc_intra_depot"] = round(auc(y, rang_depot(s, dep)), 3)
            table[v][nom_e] = ligne
    # reference heuristique : meilleur AUC des deux heuristiques par etiquette (comparaison prudente)
    comparaisons = {}
    for nom_e in list(etiq) + ["defaut_revue"]:
        y = etiq[nom_e] if nom_e != "defaut_revue" else yr
        cand = {h: table[h][nom_e]["auc"] for h in ("heuristique_lr", "heuristique_longueur")}
        ref = max(cand, key=cand.get)
        comparaisons[nom_e] = {"reference": ref, "auc_reference": cand[ref], "bras": {}}
        for v in scores:
            if v.startswith("heuristique"):
                continue
            d, lo, hi = delta_ic(y, scores[v][nom_e], scores[ref][nom_e])
            a = table[v][nom_e]["auc"]
            comparaisons[nom_e]["bras"][v] = {"auc": a, "delta_vs_ref": round(d, 3), "delta_ic95": [round(lo, 3), round(hi, 3)],
                                              "critere_auc_sup_0_7_et_delta_sup_0_05": bool(a > 0.7 and d >= 0.05)}
    res["table"], res["comparaisons"], res["bras_heuristiques"] = table, comparaisons, bras

    # ---- diagnostics : correlation des scores avec la longueur et avec les appels (continu)
    diag = {}
    for v in scores:
        s = scores[v]["derapage"]
        diag[v] = {"spearman_avec_longueur": round(spearman(s, brut[:, 0]), 3), "spearman_avec_appels": round(spearman(s, appels), 3),
                   "spearman_avec_appels_intra_depot": round(float(np.mean([spearman(s[[i for i, x in enumerate(depots) if x == d]], appels[[i for i, x in enumerate(depots) if x == d]]) for d in sorted(set(depots))])), 3)}
    res["diagnostics_continus"] = diag
    res["spearman_longueur_appels"] = round(spearman(brut[:, 0], appels), 3)
    # sensibilite : stories dont la version d'epics.md est strictement anterieure au debut du dev (et non « du jour »)
    avant = np.array([r["source_epics"] == "avant" for r in lignes])
    sens = {"n_avant": int(avant.sum()), "positifs_haut20": int(etiq["haut20"][avant].sum()), "positifs_derapage": int(etiq["derapage"][avant].sum()), "auc_haut20": {}}
    if etiq["haut20"][avant].min() != etiq["haut20"][avant].max():
        for v in ("heuristique_longueur", "jev_latest_r1", "luna_r1", "mimo_r1"):
            if v in scores:
                sens["auc_haut20"][v] = round(auc(etiq["haut20"][avant], scores[v]["haut20"][avant]), 3)
    res["sensibilite_version_epics"] = sens
    # accord des reponses oui/non des LLM avec la proba (coherence de la sortie structuree)
    # budget
    try:
        res["budget"] = json.loads((ICI / "budget.json").read_text(encoding="utf-8"))
    except OSError:
        res["budget"] = None
    (ICI / "resultats.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- resume lisible
    print(f"n={n} positifs={res['positifs']} defaut_revue positifs={res['defaut_revue_positifs']}/{res['defaut_revue_n']}")
    for nom_e in ["derapage", "derapage_par_agent", "haut20", "defaut_revue"]:
        print(f"\n== {nom_e} (reference prudente : {comparaisons[nom_e]['reference']} AUC {comparaisons[nom_e]['auc_reference']})")
        for v in sorted(table):
            t = table[v].get(nom_e)
            if not t:
                continue
            al = t["alertes20"]
            print(f"{v:24s} AUC {t['auc']:.3f} [{t['ic95'][0]:.2f};{t['ic95'][1]:.2f}] intra {t['auc_intra_depot']:.3f}  alertes {al['alertes']} P={al['precision']} R={al['rappel']}")
    print("\ncout", json.dumps(couts), "\nlatence", json.dumps(latences), "\nstabilite", json.dumps(stab))
    return 0


if __name__ == "__main__":
    sys.exit(main())
