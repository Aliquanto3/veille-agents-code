"""Tableaux Markdown de resultats.md, calcules depuis agregats.json et q5.json (aucune lecture de transcription).

Usage : uv run --no-project python -I tableaux.py > tableaux.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ICI = Path(__file__).parent
A = json.loads((ICI / "agregats.json").read_text(encoding="utf-8"))
Q5 = json.loads((ICI / "q5.json").read_text(encoding="utf-8"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]


def k(v: float) -> str:
    if abs(v) >= 1e6:
        return f"{v / 1e6:.1f} M".replace(".", ",")
    return f"{v / 1000:.1f} k".replace(".", ",")


def pct(v: float) -> str:
    return f"{100 * v:.1f} %".replace(".", ",")


def usd(v: float) -> str:
    return f"{v:,.0f} $".replace(",", " ")


def q1() -> None:
    print("### Q1\n")
    print("| Population | n | entrée + écriture, Q1 / médiane / Q3 | contexte total (avec lecture du cache), Q1 / médiane / Q3 |")
    print("|---|---|---|---|")
    for cle in ("principale|tous|tous", "principale|tous|fam:opus", "principale|tous|fam:sonnet", "principale|tous|fam:haiku",
                "sous-agent|tous|tous", "sous-agent|tous|general-purpose", "sous-agent|tous|agent-cost-kit:dev-story",
                "sous-agent|tous|agent-cost-kit:reviewer", "sous-agent|tous|agent-cost-kit:second-avis",
                "sous-agent|tous|agent-cost-kit:lookup", "sous-agent|tous|Explore"):
        v = A["q1"][cle]
        e, c = v["entree_ecriture"], v["ctx_total"]
        genre, _, pop = cle.split("|")
        print(f"| {genre}{'' if pop == 'tous' else ' / ' + pop.replace('fam:', 'modèle ')} | {e['n']} | {k(e['q1'])} / {k(e['mediane'])} / {k(e['q3'])} | {k(c['q1'])} / {k(c['mediane'])} / {k(c['q3'])} |")
    print("\nPar semaine ISO (premier appel, toutes populations d'un genre) :\n")
    print("| Semaine | principale n | principale médiane (entrée+écriture / total) | sous-agent n | sous-agent médiane (entrée+écriture / total) |")
    print("|---|---|---|---|---|")
    semaines = sorted({c.split("|")[1] for c in A["q1"] if "|S20" in c})
    for s in semaines:
        m, a = A["q1"].get(f"principale|{s}|tous"), A["q1"].get(f"sous-agent|{s}|tous")
        f = lambda x: f"{x['entree_ecriture']['n']} | {k(x['entree_ecriture']['mediane'])} / {k(x['ctx_total']['mediane'])}" if x else "0 | -"
        print(f"| {s[1:]} | {f(m)} | {f(a)} |")
    print("\nComposition estimée du premier appel (médianes, caractères / 3,5), sessions avec définitions d'outils :\n")
    print("| Composant | principale | sous-agent |")
    print("|---|---|---|")
    c = A["q1_composition_estimee_tokens_mediane"]
    for nom, cle in (("Prompt système (texte)", "systeme"), ("Définitions d'outils chargées", "outils_charges"), ("Pièces jointes de démarrage (liste des skills, CLAUDE.md, outils différés, agents, MCP...)", "attachments_total"),
                     ("Premier message utilisateur", "prompt_initial")):
        print(f"| {nom} | {k(c['principale'][cle])} | {k(c['sous-agent'][cle])} |")
    print(f"| Nombre d'outils chargés (différés en plus) | {c['principale']['n_outils_charges']} (+{c['principale']['n_outils_differes']}) | {c['sous-agent']['n_outils_charges']} (+{c['sous-agent']['n_outils_differes']}) |")
    print("\nPièces jointes de démarrage, médiane par type (tokens estimés) :\n")
    print("| Pièce jointe | principale | sous-agent |")
    print("|---|---|---|")
    pa = A["q1_attachments_avant_premier_appel_mediane"]
    for t in ("skill_listing", "prompt_snapshot", "instructions", "deferred_tools_delta", "mcp_instructions_delta", "agent_listing_delta", "session_context", "environment"):
        print(f"| {t} | {pa['principale'].get(t, {}).get('mediane', '-')} | {pa['sous-agent'].get(t, {}).get('mediane', '-')} |")
    print("\nDéfinitions d'outils chargées par type d'agent (médianes) :\n")
    print("| Type | n | outils chargés | tokens estimés | contexte total |")
    print("|---|---|---|---|---|")
    for t, v in sorted(A["q1_outils_par_type_agent"].items(), key=lambda kv: -kv[1]["n"]):
        print(f"| {t} | {v['n']} | {v['n_outils_charges_mediane']:.0f} | {k(v['outils_charges_tokens_mediane'])} | {k(v['ctx_total_mediane'])} |")


def q2() -> None:
    print("\n### Q2\n")
    n = {g: A["fichiers"][f"{g}:avec_definitions_outils"] for g in ("principale", "sous-agent")}
    print(f"Fichiers avec définitions d'outils : {n['principale']} sessions principales, {n['sous-agent']} sous-agents.\n")
    print("| Outil | tokens (déf.) | principale : chargé / appelé (sessions) | appels | sous-agent : chargé / appelé (fichiers) | appels | lecture du cache de la définition, 45 j | écriture unique |")
    print("|---|---|---|---|---|---|---|---|")
    for nom, v in A["q2_outils"].items():
        if v["taille_def_tokens_est"] == 0:
            continue
        print(f"| {nom} | {v['taille_def_tokens_est']} | {v['principale_charge']} / {v['principale_appelee']} | {v['principale_appels']} | {v['sous_agent_charge']} / {v['sous_agent_appele']} | {v['sous_agent_appels']} | {usd(v['cout_lecture_def_usd'])} | {usd(v['cout_ecriture_unique_def_usd'])} |")
    print("\nOutils appelés mais jamais chargés (différés, MCP) : fréquence d'appel sur la période :\n")
    print("| Outil | appels principale | appels sous-agent |")
    print("|---|---|---|")
    for nom, v in sorted(A["q2_outils"].items(), key=lambda kv: -(kv[1]["principale_appels"] + kv[1]["sous_agent_appels"])):
        if v["taille_def_tokens_est"] == 0 and v["principale_appels"] + v["sous_agent_appels"] > 0:
            print(f"| {nom.replace('mcp__', 'mcp:') if nom.startswith('mcp__') else nom} | {v['principale_appels']} | {v['sous_agent_appels']} |")


def q3() -> None:
    print("\n### Q3\n")
    T = A["tokens"]
    for g in ("principale", "sous-agent", "ensemble"):
        if g == "ensemble":
            groupes: dict = {}
            for gg in ("principale", "sous-agent"):
                for nom, v in A["q3"][gg].items():
                    d = groupes.setdefault(nom, {"n": 0, "car": 0, "img": 0, "tok_reads": 0, "cout": 0.0})
                    for cle in d:
                        d[cle] += v[cle]
            nouveau = sum(T[x]["entree"] + T[x]["ecrit"] for x in T)
            tout = nouveau + sum(T[x]["lu"] for x in T)
        else:
            groupes = A["q3"][g]
            nouveau = T[g]["entree"] + T[g]["ecrit"]
            tout = nouveau + T[g]["lu"]
        tok_tot = sum(v["car"] / 3.5 + v["img"] * 1500 for v in groupes.values())
        print(f"\n**{g}** : résultats d'outils = {k(tok_tot)} tokens estimés, soit {pct(tok_tot / nouveau)} des tokens d'entrée neufs (entrée + écriture de cache, {k(nouveau)}) ; "
              f"entrée totale avec lectures du cache : {k(tout)}.\n")
        print("| Outil | résultats | tokens estimés | part des résultats | part de l'entrée neuve | part de l'entrée relue (cumul des relectures) | coût équivalent API estimé |")
        print("|---|---|---|---|---|---|---|")
        for nom, v in sorted(groupes.items(), key=lambda kv: -kv[1]["car"])[:8]:
            tok = v["car"] / 3.5 + v["img"] * 1500
            print(f"| {nom} | {v['n']} | {k(tok)} | {pct(tok / tok_tot)} | {pct(tok / nouveau)} | {pct(v['tok_reads'] / tout)} | {usd(v['cout'])} |")
    # sensibilite
    print("\nSensibilité du chiffre « Shell / entrée neuve » (principale + sous-agent) au nombre de caractères par token :\n")
    sh = sum(A["q3"][g]["Shell"]["car"] for g in A["q3"])
    nouveau = sum(T[x]["entree"] + T[x]["ecrit"] for x in T)
    print("| caractères par token | part du Shell dans l'entrée neuve |")
    print("|---|---|")
    for c in (2.5, 3.0, 3.5, 4.0):
        print(f"| {c} | {pct(sh / c / nouveau)} |".replace(".", ",", 1) if False else f"| {str(c).replace('.', ',')} | {pct(sh / c / nouveau)} |")
    print("\nCe que contiennent les résultats Shell (catégorie du premier mot de la commande, sans conserver la commande) :\n")
    print("| Catégorie | résultats | part des caractères | caractères par résultat | coût équivalent API estimé |")
    print("|---|---|---|---|---|")
    sc = A["q3_shell_par_commande"]
    tot_car = sum(v["car"] for v in sc.values())
    for nom, v in sorted(sc.items(), key=lambda kv: -kv[1]["car"]):
        print(f"| {nom} | {v['n']} | {pct(v['car'] / tot_car)} | {v['car'] / v['n']:.0f} | {usd(v['cout'])} |")
    cout_total = sum(A["cout_equiv_api_usd"].values())
    cs = sum(A["q3"][g]["Shell"]["cout"] for g in A["q3"])
    print(f"\nCoût équivalent API total de la période : {usd(cout_total)} ; coût estimé des résultats Shell sur leur vie dans le contexte : {usd(cs)} ({pct(cs / cout_total)}).")


def q4() -> None:
    print("\n### Q4\n")
    for g, seuils in (("principale", (3600, 1800, 900, 300)), ("sous-agent", (300, 900, 1800, 3600))):
        c = A["q4"][g]
        cout_g = sum(v for kk, v in A["cout_equiv_api_usd"].items() if kk.startswith(g))
        print(f"\n**{g}** : {c['appels']} appels, écritures de cache {k(c['ecrit_tok'])} tokens, {usd(c['ecrit_cout'])} (coût total de ce genre : {usd(cout_g)}).\n")
        print("| Pause avant l'appel | appels | tokens écrits | part des tokens écrits | coût d'écriture | part du coût d'écriture | dont réécriture estimée (tokens relus si le cache avait tenu) | coût de la réécriture | part du coût total |")
        print("|---|---|---|---|---|---|---|---|---|")
        for s in seuils:
            print(f"| > {s // 60} min | {c[f's{s}_appels']} | {k(c[f's{s}_ecrit_tok'])} | {pct(c[f's{s}_ecrit_tok'] / c['ecrit_tok'])} | {usd(c[f's{s}_ecrit_cout'])} | {pct(c[f's{s}_ecrit_cout'] / c['ecrit_cout'])} | {k(c[f's{s}_reecrit_tok'])} | {usd(c[f's{s}_reecrit_cout'])} | {pct(c[f's{s}_reecrit_cout'] / cout_g)} |")
        print(f"\nPremier appel de chaque agent (écriture initiale) : {pct(c['ecrit_tok_premier'] / c['ecrit_tok'])} des tokens écrits. TTL observé : 5 min {k(c.get('ttl_5m_ecrit_tok', 0))} tokens, 1 h {k(c.get('ttl_1h_ecrit_tok', 0))} tokens (hors premiers appels). "
              f"Expirations au TTL réel (pause > TTL, écriture > 20 k) : {c['exp_ttl_propre_appels']} appels, {usd(c['exp_ttl_propre_reecrit_cout'])} de réécriture.")
    c = A["q4"]["sous-agent"]
    print("\nContrefactuel TTL 1 h par type de sous-agent :\n")
    print("| Type | appels | appels après une pause > 5 min | gain (pauses 5-60 min relues) | surcoût (écritures x 2 au lieu de x 1,25) | solde |")
    print("|---|---|---|---|---|---|")
    for t, v in A["q4_ctf1h_par_type"].items():
        print(f"| {t} | {v['appels']} | {v['appels_apres_pause_5m']} | {usd(v['gain_usd'])} | {usd(v['surcout_usd'])} | {usd(v['solde_usd'])} |")
    print(f"\nContrefactuel TTL 1 h pour les sous-agents : gain {usd(c['ctf1h_gain_pause_5m_a_1h'])} (pauses de 5 à 60 min relues au lieu de réécrites) contre un surcoût de {usd(c['ctf1h_surcout_toutes_ecritures_5m'])} "
          f"(toutes les écritures à 5 min passent de x 1,25 à x 2) : solde {usd(c['ctf1h_gain_pause_5m_a_1h'] - c['ctf1h_surcout_toutes_ecritures_5m'])}.")


def q5() -> None:
    print("\n### Q5\n")
    print("| Dépôt | stories avec constats | constats | corrigé (dont partiel) | rejeté | reporté | autre / indéterminé |")
    print("|---|---|---|---|---|---|---|")
    for nom, d in sorted(Q5["depots"].items(), key=lambda kv: -kv[1]["stories_avec_constats"]):
        if not d["stories_avec_constats"]:
            continue
        c = d["constats"]
        tot = sum(v for kk, v in c.items() if "|" in kk and not kk.startswith("rejet_motif"))
        cor = sum(v for kk, v in c.items() if kk.endswith(("|corrige", "|partiel")))
        rej = sum(v for kk, v in c.items() if kk.endswith("|rejete"))
        rep = sum(v for kk, v in c.items() if kk.endswith("|reporte"))
        print(f"| {nom} | {d['stories_avec_constats']} | {tot} | {cor} ({pct(cor / tot)}) | {rej} ({pct(rej / tot)}) | {rep} ({pct(rep / tot)}) | {tot - cor - rej - rep} |")
    pv, ps = Q5["par_verdict"], Q5["par_severite"]
    tot = sum(pv.values())
    print(f"\nTotal : {tot} constats sur {Q5['total_stories']} stories. " + ", ".join(f"{v} {kk}" for kk, v in pv.items()) + ". Sévérités : " + ", ".join(f"{v} {kk}" for kk, v in ps.items()) + ".")
    print(f"Motifs des rejets : {Q5['motifs_rejet']}.")
    print("\nPar sévérité (corrigé + partiel / total) :\n")
    print("| Sévérité | constats | corrigés | rejetés | reportés |")
    print("|---|---|---|---|---|")
    t = Q5["total_constats"]
    for s in ("high", "medium", "low"):
        tt = sum(v for kk, v in t.items() if kk.startswith(s + "|"))
        co = t.get(f"{s}|corrige", 0) + t.get(f"{s}|partiel", 0)
        print(f"| {s} | {tt} | {co} ({pct(co / tt)}) | {t.get(f'{s}|rejete', 0)} ({pct(t.get(f'{s}|rejete', 0) / tt)}) | {t.get(f'{s}|reporte', 0)} ({pct(t.get(f'{s}|reporte', 0) / tt)}) |")
    print(f"\nAgents lancés sur 45 jours : {Q5['agents_lances_45j']}.")
    for nom in ("wavedevsecops", "wavelocalai"):
        d = Q5["depots"][nom]
        print(f"Journal {nom} : {d['journal_lignes_resultat']} résultats de second avis, {d['journal_constats_declares']} constats déclarés (contre {sum(v for kk, v in d['constats'].items() if '|' in kk and not kk.startswith('rejet_motif'))} lignes de revue retrouvées).")


def q6() -> None:
    print("\n### Q6\n")
    print("| Population | agents | appels : Q1 / médiane / Q3 / max | coût total | coupure à 2 x médiane (plafond) | agents coupés | appels évités | économie brute | part du coût |")
    print("|---|---|---|---|---|---|---|---|---|")
    noms = {"tous": "tous les dev-story", "sonnet_seul": "dev-story sur Sonnet", "repos_run_autonome": "dépôts avec run-autonome.md",
            "sonnet_repos_run_autonome": "Sonnet, dépôts avec run-autonome.md", "sessions_3_stories_ou_plus": "sessions de 3 dev-story ou plus", "par_story_tous": "par story (reprises regroupées)"}
    for cle, nom in noms.items():
        q = A["q6"][cle]
        c = q["coupures"]["2"]
        a = q["appels"]
        print(f"| {nom} | {q['n_agents']} | {a['q1']} / {str(q['mediane_appels']).replace('.', ',')} / {a['q3']} / {a['max']} | {usd(q['cout_total_usd'])} | {c['plafond_appels']} | {c['agents_coupes']} ({pct(c['part_coupes'])}) | {c['appels_economises']} | {usd(c['economie_usd'])} | {pct(c['part_cout'])} |")
    print("\nSensibilité du multiple (tous les dev-story) :\n")
    print("| Multiple | plafond | agents coupés | économie brute | part du coût |")
    print("|---|---|---|---|---|")
    for m, c in A["q6"]["tous"]["coupures"].items():
        print(f"| {m.replace('.', ',')} x | {c['plafond_appels']} | {c['agents_coupes']} ({pct(c['part_coupes'])}) | {usd(c['economie_usd'])} | {pct(c['part_cout'])} |")
    m = A["q6"]["mediane_par_depot_x2"]
    print(f"\nPlafond à 2 x la médiane de chaque dépôt ({m['n_depots']} dépôts) : {m['agents_coupes']} agents coupés ({pct(m['part_coupes'])}), {m['appels_economises']} appels évités, économie brute {usd(m['economie_usd'])} ({pct(m['part_cout'])} du coût dev-story).")
    print(f"\nModèles des agents : {A['q6']['par_modele']} ; stories à plusieurs agents : {A['q6']['stories_a_plusieurs_agents']}.")


if __name__ == "__main__":
    print(f"Période : depuis le {A['coupure_utc']}, {A['fichiers']['principale']} sessions principales, {A['fichiers']['sous-agent']} sous-agents, {A['requetes_api']} requêtes API tracées.")
    q1()
    q2()
    q3()
    q4()
    q5()
    q6()
