"""Agrège coûts, portes dures et tics -> donnees/resume.json et donnees/tableaux.md.
Les notes d'Anaël (si `--notes notation-t11.json` est donné) sont croisées avec correspondance.json."""
import json, statistics as st, sys
from config import T11, CONDITIONS, ESSAIS, NOMS

TEXTES = sorted(d.name for d in (T11 / "sorties").iterdir() if d.is_dir())


def charger(p):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def porte(verdict):
    """Porte franchie hors voix effacée (X3 : la note d'Anaël tranche)."""
    return any(e.get("gravite") == "porte" and e.get("type") != "voix_effacee" for e in verdict.get("ecarts", []))


def main():
    tics = charger(T11 / "donnees" / "tics.json") or {}
    L = []
    res = {"couts": {}, "portes": {}}
    # coûts
    L.append("### Coûts, tours, durée (moyenne par essai ; D = C + passage humanizer)\n")
    L.append("| Condition | Coût par essai ($) | Tours | Durée (s) | Tokens sortie |\n|---|---|---|---|---|")
    for c in CONDITIONS:
        couts, tours, durees, tout = [], [], [], []
        for t in TEXTES:
            for e in ESSAIS:
                m = charger(T11 / "sorties" / t / f"{c}-{e}.meta.json")
                if not m:
                    continue
                cc, tt, dd, oo = m["cout_usd"] or 0, m["tours"] or 0, m["duree_s"], m["tokens_out"] or 0
                if c == "D":
                    mc = charger(T11 / "sorties" / t / f"C-{e}.meta.json")
                    cc, tt, dd, oo = cc + mc["cout_usd"], tt + mc["tours"], dd + mc["duree_s"], oo + (mc["tokens_out"] or 0)
                couts.append(cc); tours.append(tt); durees.append(dd); tout.append(oo)
        if couts:
            res["couts"][c] = {"n": len(couts), "total": round(sum(couts), 3), "moyen": round(st.mean(couts), 3)}
            L.append(f"| {c} {NOMS[c]} | {st.mean(couts):.3f} (total {sum(couts):.2f}) | {st.mean(tours):.1f} | {st.mean(durees):.0f} | {st.mean(tout):.0f} |")
    total_sorties = sum(v["total"] for k, v in res["couts"].items() if k != "D")
    total_sorties += sum(
        (charger(T11 / "sorties" / t / f"D-{e}.meta.json") or {}).get("cout_usd", 0) or 0 for t in TEXTES for e in ESSAIS)
    res["cout_total_conditions"] = round(total_sorties, 3)
    # portes dures
    L.append("\n### Portes dures (juge aveugle ; voix effacée de X3 exclue du décompte)\n")
    L.append("| Condition | " + " | ".join(TEXTES) + " | Total essais franchis | Taux |\n|---|" + "---|" * (len(TEXTES) + 2))
    for c in CONDITIONS:
        cells, tot, n = [], 0, 0
        for t in TEXTES:
            nb, ne = 0, 0
            for e in ESSAIS:
                j = charger(T11 / "juge" / t / f"{c}-{e}.json")
                if j and "verdict" in j and "ecarts" in j["verdict"]:
                    ne += 1; nb += porte(j["verdict"])
            cells.append(f"{nb}/{ne}"); tot += nb; n += ne
        res["portes"][c] = {"franchies": tot, "essais": n}
        L.append(f"| {c} {NOMS[c]} | " + " | ".join(cells) + f" | {tot}/{n} | {tot / n:.0%} |" if n else f"| {c} | - |")
    # tics
    cols = [("mots", "mots"), ("mots_par_phrase", "mots/phr."), ("tirets", "tirets"), ("contrastes", "pas X mais Y"),
            ("chutes_une_ligne", "chutes"), ("triades", "triades"), ("triades_fin_phrase", "triades fin"),
            ("gonfles", "gonflés"), ("gras", "gras")]
    for t in TEXTES:
        if t not in tics:
            continue
        L.append(f"\n### Tics de surface, {t} (valeurs par sortie ; la source en tête)\n")
        L.append("| Version | " + " | ".join(n for _, n in cols) + " | chiffres manquants | chiffres ajoutés | renvois manquants |\n|---|" + "---|" * (len(cols) + 3))
        for k, v in tics[t].items():
            L.append(f"| {k} | " + " | ".join(str(v[c]) for c, _ in cols) +
                     f" | {','.join(v['chiffres_manquants']) or '-'} | {','.join(v['chiffres_ajoutes']) or '-'} | {','.join(v['renvois_manquants']) or '-'} |")
    L.append("\n### Tics, moyenne par condition (tous textes ; X4 en anglais compté à part dans le détail)\n")
    L.append("| Condition | " + " | ".join(n for _, n in cols) + " |\n|---|" + "---|" * len(cols))
    for c in CONDITIONS:
        vals = [v for t in TEXTES for k, v in tics.get(t, {}).items() if k.startswith(c + "-")]
        if vals:
            L.append(f"| {c} {NOMS[c]} | " + " | ".join(f"{st.mean(v[x] for v in vals):.1f}" for x, _ in cols) + " |")
    # notes d'Anaël
    if "--notes" in sys.argv:
        notes = json.loads(open(sys.argv[sys.argv.index("--notes") + 1], encoding="utf-8").read())["notes"]
        corr = json.loads((T11 / "correspondance.json").read_text(encoding="utf-8"))
        par = {}
        for tid, m in corr.items():
            for lettre, cle in m.items():
                n = notes.get(f"{tid}/{lettre}")
                if not n:
                    continue
                par.setdefault(cle.split("-")[0], []).append((tid, n))
        L.append("\n### Notes d'Anaël (moyennes par condition)\n")
        crit = ["fidelite", "clarte", "naturel", "publier"]
        L.append("| Condition | " + " | ".join(crit) + " | moyenne |\n|---|---|---|---|---|---|")
        for c in CONDITIONS:
            if c in par:
                ms = [st.mean(n[k] for _, n in par[c] if k in n) for k in crit]
                L.append(f"| {c} {NOMS[c]} | " + " | ".join(f"{m:.2f}" for m in ms) + f" | {st.mean(ms):.2f} |")
    (T11 / "donnees" / "resume.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    (T11 / "donnees" / "tableaux.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
