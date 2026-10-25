"""Génère tests-pratiques/T7ter-design-md/notation.html (12 rendus à l'aveugle, groupés par écran, lettres tirées par
`secrets` dans chaque écran) et correspondance.json (ignorée par git, non référencée par la page).

Usage : uv run --project <t7ter/mesures> python generer_notation.py
"""
import base64, io, json, secrets, string, sys
from html import escape
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from chemins import BRAS, DEPOT, ECRANS, ESSAIS, MESURES, nom

SORTIE = DEPOT
TITRES = {1: "Écran 1 : Demandes d'achat", 2: "Écran 2 : Notes de frais"}
VUES = [
    ("initial_1280", "Ordinateur (1280 px), état initial"),
    ("erreur_1280", "Ordinateur (1280 px), après un envoi invalide"),
    ("initial_768", "Tablette (768 px), état initial"),
    ("initial_390", "Téléphone (390 px), état initial"),
    ("erreur_390", "Téléphone (390 px), après un envoi invalide"),
]
CRITERES = [
    ("lisibilite", "Lisibilité", "On repère vite où saisir, ce qui est faux et où lire le tableau."),
    ("finition", "Finition", "Alignements, espacements, états des champs et du bouton, détails."),
    ("coherence", "Cohérence", "Une même logique de couleurs, de typographie et de composants sur tout l'écran."),
]


def data_uri(path: Path, largeur_max=1280) -> str:
    im = Image.open(path).convert("RGB")
    if im.width > largeur_max:
        im = im.resize((largeur_max, round(im.height * largeur_max / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=68, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def carte(l, dossier):
    d = MESURES / dossier
    figs = []
    for cle, legende in VUES:
        uri = data_uri(d / f"{cle}.png")
        cls = "mobile" if cle.endswith("390") else ("tablette" if cle.endswith("768") else "bureau")
        figs.append(f'<figure class="{cls}"><button type="button" class="zoom" aria-label="Agrandir : {escape(legende)}"><img src="{uri}" alt="Rendu {l} : {escape(legende)}" loading="lazy"></button><figcaption>{escape(legende)}</figcaption></figure>')
    grille = []
    for ck, cl, aide in CRITERES:
        radios = "".join(
            f'<label class="pastille"><input type="radio" name="{l}-{ck}" value="{n}" data-rendu="{l}" data-critere="{ck}"><span>{n}</span></label>'
            for n in range(1, 6))
        grille.append(f'<fieldset class="critere"><legend>{cl}</legend><p class="aide">{escape(aide)}</p><div class="echelle"><span class="borne">1 très insuffisant</span>{radios}<span class="borne">5 excellent</span></div></fieldset>')
    return f'''<section class="rendu" id="rendu-{l}" aria-labelledby="t-{l}">
  <h3 id="t-{l}">Rendu {l}</h3>
  <div class="vues">{"".join(figs)}</div>
  <div class="notes">{"".join(grille)}
    <label class="commentaire">Commentaire (facultatif)<textarea data-rendu="{l}" rows="2"></textarea></label>
  </div>
</section>'''


def main():
    rng = secrets.SystemRandom()
    lettres = list(string.ascii_uppercase)
    corr, groupes = {}, {}
    k = 0
    for e in ECRANS:
        rendus = [(b, r) for b in BRAS for r in ESSAIS]
        ls = lettres[k:k + len(rendus)]
        k += len(rendus)
        rng.shuffle(ls)  # tirage au sort des lettres à l'intérieur de l'écran
        groupes[e] = sorted(ls)
        for (b, r), l in zip(rendus, ls):
            corr[l] = {"ecran": e, "bras": b, "essai": r, "dossier": nom(b, e, r)}
    SORTIE.mkdir(parents=True, exist_ok=True)
    (SORTIE / "correspondance.json").write_text(json.dumps(dict(sorted(corr.items())), ensure_ascii=False, indent=1), encoding="utf-8")

    sections = []
    for e in ECRANS:
        cartes = "".join(carte(l, corr[l]["dossier"]) for l in groupes[e])
        sections.append(f'<section class="ecran" aria-labelledby="ecran-{e}"><h2 id="ecran-{e}">{escape(TITRES[e])}</h2>{cartes}</section>')
    total = len(corr)

    page = f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>T7 ter Notation à l'aveugle</title>
<style>
:root {{ --fond:#f6f5f2; --carte:#ffffff; --texte:#1c1f23; --discret:#5b6168; --trait:#d9d6cf; --accent:#1f4e8c; --accent-texte:#ffffff; --ok:#1c6b3a; --focus:#1f4e8c; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --fond:#15171a; --carte:#1d2024; --texte:#eceae6; --discret:#a3a8ae; --trait:#33373d; --accent:#7fb0ee; --accent-texte:#0f1a2a; --ok:#6fcf93; --focus:#7fb0ee; }} }}
:root[data-theme="dark"] {{ --fond:#15171a; --carte:#1d2024; --texte:#eceae6; --discret:#a3a8ae; --trait:#33373d; --accent:#7fb0ee; --accent-texte:#0f1a2a; --ok:#6fcf93; --focus:#7fb0ee; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:var(--fond); color:var(--texte); font:16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width: 1180px; margin: 0 auto; padding: 24px 16px 96px; }}
h1 {{ font-size: 1.6rem; margin: 0 0 8px; }}
h2 {{ font-size: 1.4rem; margin: 32px 0 12px; padding-top: 8px; border-top: 2px solid var(--trait); }}
h3 {{ font-size: 1.2rem; margin: 0 0 12px; }}
.intro {{ color: var(--discret); max-width: 70ch; }}
.intro strong {{ color: var(--texte); }}
.barre {{ position: sticky; top: 0; z-index: 5; background: var(--fond); border-bottom: 1px solid var(--trait); padding: 10px 0; display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin-bottom: 16px; }}
.barre .progres {{ font-variant-numeric: tabular-nums; }}
button.action {{ font: inherit; padding: 8px 14px; border-radius: 6px; border: 1px solid var(--accent); background: var(--accent); color: var(--accent-texte); cursor: pointer; }}
button.action.secondaire {{ background: transparent; color: var(--accent); }}
:focus-visible {{ outline: 3px solid var(--focus); outline-offset: 2px; }}
.rendu {{ background: var(--carte); border: 1px solid var(--trait); border-radius: 10px; padding: 16px; margin: 0 0 24px; }}
.vues {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; align-items: start; }}
figure {{ margin: 0; }}
figure.bureau {{ grid-column: span 2; }}
@media (max-width: 640px) {{ figure.bureau {{ grid-column: auto; }} }}
figure img {{ display:block; width:100%; height:auto; border:1px solid var(--trait); border-radius: 6px; background:#fff; }}
figure.mobile img {{ max-width: 260px; }}
figcaption {{ font-size: .85rem; color: var(--discret); margin-top: 4px; }}
button.zoom {{ padding:0; border:0; background:none; cursor: zoom-in; width:100%; text-align:left; }}
.notes {{ margin-top: 16px; display:grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
fieldset.critere {{ border: 1px solid var(--trait); border-radius: 8px; padding: 8px 12px 12px; margin:0; }}
legend {{ font-weight: 600; padding: 0 6px; }}
.aide {{ margin: 0 0 8px; font-size: .85rem; color: var(--discret); }}
.echelle {{ display:flex; align-items:center; gap: 8px; flex-wrap: wrap; }}
.borne {{ font-size: .75rem; color: var(--discret); }}
.pastille {{ position: relative; }}
.pastille input {{ position:absolute; opacity:0; inset:0; margin:0; cursor:pointer; }}
.pastille span {{ display:grid; place-items:center; width: 40px; height: 40px; border-radius: 50%; border: 1px solid var(--trait); font-weight: 600; background: var(--fond); }}
.pastille input:checked + span {{ background: var(--accent); color: var(--accent-texte); border-color: var(--accent); }}
.pastille input:focus-visible + span {{ outline: 3px solid var(--focus); outline-offset: 2px; }}
.commentaire {{ grid-column: 1 / -1; display:grid; gap: 4px; font-size: .9rem; color: var(--discret); }}
textarea {{ font: inherit; color: var(--texte); background: var(--fond); border: 1px solid var(--trait); border-radius: 6px; padding: 6px 8px; width:100%; }}
#export {{ display:none; margin-top: 16px; }}
#export textarea {{ font-family: ui-monospace, Consolas, monospace; font-size: .85rem; min-height: 14em; }}
dialog {{ border:0; padding:0; background: transparent; max-width: 96vw; max-height: 96vh; }}
dialog::backdrop {{ background: rgba(0,0,0,.7); }}
dialog img {{ max-width: 96vw; max-height: 92vh; display:block; background:#fff; }}
dialog button {{ position: fixed; top: 12px; right: 12px; }}
</style>
</head>
<body>
<main>
<h1>T7 ter Notation à l'aveugle des {total} rendus</h1>
<p class="intro">Deux écrans métier (formulaire de saisie, validation, tableau filtrable), construits chacun {total // len(ECRANS)} fois, présentés <strong>par écran</strong>. Les rendus portent des <strong>lettres tirées au hasard</strong> : rien n'indique comment chacun a été produit. Pour chaque rendu, note de <strong>1 à 5</strong> la lisibilité, la finition et la cohérence. Compare les rendus d'un même écran entre eux. Clique sur une capture pour l'agrandir. Tes notes sont gardées dans ce navigateur au fil de l'eau ; à la fin, « Exporter mes notes » donne un JSON à transmettre.</p>
<div class="barre" role="region" aria-label="Avancement">
  <span class="progres" id="progres" aria-live="polite">0 note sur {total * 3}</span>
  <button type="button" class="action" id="btn-export">Exporter mes notes</button>
  <button type="button" class="action secondaire" id="btn-raz">Tout effacer</button>
</div>
{"".join(sections)}
<section id="export" aria-label="Export des notes">
  <h2>Mes notes (JSON)</h2>
  <textarea id="export-zone" readonly></textarea>
  <p><button type="button" class="action" id="btn-copier">Copier</button> <button type="button" class="action secondaire" id="btn-dl">Télécharger notes-t7ter.json</button></p>
</section>
</main>
<dialog id="dlg"><button type="button" class="action" id="dlg-fermer">Fermer</button><img alt=""></dialog>
<script>
(function () {{
  var CLE = "t7ter-notation-v1";
  var etat = {{}};
  try {{ etat = JSON.parse(localStorage.getItem(CLE) || "{{}}"); }} catch (e) {{ etat = {{}}; }}
  function sauver() {{ try {{ localStorage.setItem(CLE, JSON.stringify(etat)); }} catch (e) {{}} }}
  function majProgres() {{
    var n = 0; Object.keys(etat).forEach(function (l) {{ ["lisibilite","finition","coherence"].forEach(function (c) {{ if (etat[l] && etat[l][c]) n++; }}); }});
    document.getElementById("progres").textContent = n + " note" + (n > 1 ? "s" : "") + " sur {total * 3}";
  }}
  document.querySelectorAll('input[type=radio][data-rendu]').forEach(function (r) {{
    var l = r.dataset.rendu, c = r.dataset.critere;
    if (etat[l] && String(etat[l][c]) === r.value) r.checked = true;
    r.addEventListener("change", function () {{ etat[l] = etat[l] || {{}}; etat[l][c] = Number(r.value); sauver(); majProgres(); }});
  }});
  document.querySelectorAll("textarea[data-rendu]").forEach(function (t) {{
    var l = t.dataset.rendu; if (etat[l] && etat[l].commentaire) t.value = etat[l].commentaire;
    t.addEventListener("input", function () {{ etat[l] = etat[l] || {{}}; etat[l].commentaire = t.value; sauver(); }});
  }});
  majProgres();
  var dlg = document.getElementById("dlg"), dimg = dlg.querySelector("img");
  document.querySelectorAll("button.zoom").forEach(function (b) {{
    b.addEventListener("click", function () {{ var im = b.querySelector("img"); dimg.src = im.src; dimg.alt = im.alt; dlg.showModal(); }});
  }});
  document.getElementById("dlg-fermer").addEventListener("click", function () {{ dlg.close(); }});
  dlg.addEventListener("click", function (e) {{ if (e.target === dlg) dlg.close(); }});
  function json() {{ var o = {{}}; Object.keys(etat).sort().forEach(function (l) {{ o[l] = etat[l]; }}); return JSON.stringify(o, null, 2); }}
  document.getElementById("btn-export").addEventListener("click", function () {{
    var s = document.getElementById("export"); s.style.display = "block"; document.getElementById("export-zone").value = json(); s.scrollIntoView({{behavior: "smooth"}});
  }});
  document.getElementById("btn-copier").addEventListener("click", function () {{
    var z = document.getElementById("export-zone"); z.select();
    if (navigator.clipboard) navigator.clipboard.writeText(z.value).catch(function () {{ document.execCommand("copy"); }}); else document.execCommand("copy");
  }});
  document.getElementById("btn-dl").addEventListener("click", function () {{
    var a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([json()], {{type: "application/json"}})); a.download = "notes-t7ter.json"; a.click();
  }});
  document.getElementById("btn-raz").addEventListener("click", function () {{
    if (!confirm("Effacer toutes les notes ?")) return; etat = {{}}; sauver();
    document.querySelectorAll("input[type=radio]").forEach(function (r) {{ r.checked = false; }});
    document.querySelectorAll("textarea[data-rendu]").forEach(function (t) {{ t.value = ""; }}); majProgres();
  }});
}})();
</script>
</body>
</html>
'''
    (SORTIE / "notation.html").write_text(page, encoding="utf-8")
    print("notation.html", round((SORTIE / "notation.html").stat().st_size / 1e6, 2), "Mo ;", total, "rendus")


if __name__ == "__main__":
    main()
