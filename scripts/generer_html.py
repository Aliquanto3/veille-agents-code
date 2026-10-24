"""Génère la page de lecture HTML : synthèse visuelle (catégories, radar, carte outils × problèmes,
verdicts par problème, nouveautés) suivie du rapport complet.

Usage : uv run --no-project --with markdown python -I scripts/generer_html.py <dossier_du_run> <sortie.html>

Entrées : synthese/donnees.json et <dossier_du_run>/research.md. Sortie : un fichier HTML autonome.
"""

import html
import json
import math
import re
import sys
from pathlib import Path

import markdown

RACINE = Path(__file__).resolve().parent.parent
ANNEAUX = ["Adopter", "Essayer", "Évaluer", "Écarter"]
CLASSE_VERDICT = {
    "Adopter": "adopter",
    "Essayer": "essayer",
    "Évaluer": "evaluer",
    "Écarter": "ecarter",
    "Hors périmètre": "hors",
    "Non lu": "hors",
}
ORIGINE = {
    "liste": "liste initiale",
    "liste-doc": "liste initiale (article)",
    "nouveau": "nouveau",
    "natif": "natif Anthropic",
}
COURT = {
    "methode": "Méthode",
    "contexte": "Contexte",
    "front": "Front",
    "tests": "Tests",
    "revue": "Revue",
    "chaine": "Chaîne d'outils",
    "gouvernance": "Gouvernance",
    "couts": "Coûts",
    "routage": "Routage",
    "orchestration": "Orchestration",
    "observabilite": "Mesure",
    "experience": "Expérience",
    "veille": "Veille",
}
# Angles (degrés, sens trigonométrique, 0 = droite) : un quadrant par famille de problèmes.
ANGLES = {"concevoir": (90, 180), "verifier": (0, 90), "couts": (180, 270), "piloter": (270, 360)}


def e(texte: str) -> str:
    return html.escape(texte, quote=True)


def badge(verdict: str) -> str:
    return f'<span class="badge {CLASSE_VERDICT.get(verdict, "hors")}">{e(verdict)}</span>'


def lien_outil(outil: dict) -> str:
    return f'<a href="{e(outil["url"])}" target="_blank" rel="noopener">{e(outil["nom"])}</a>'


def etiquette_origine(outil: dict) -> str:
    origine = outil["origine"]
    return f'<span class="origine {origine}">{e(ORIGINE[origine])}</span>'


def radar(donnees: dict, outils: dict, quadrant_de: dict) -> tuple[str, dict]:
    """Construit le SVG du radar et renvoie aussi le numéro attribué à chaque outil."""
    taille, centre, rayon = 940, 470, 440
    bornes = [0, 0.3, 0.55, 0.8, 1.0]
    parties = []
    for i in range(4, 0, -1):
        parties.append(f'<circle cx="{centre}" cy="{centre}" r="{rayon * bornes[i]:.0f}" class="anneau a{i}"/>')
    parties.append(f'<line x1="{centre - rayon}" y1="{centre}" x2="{centre + rayon}" y2="{centre}" class="axe"/>')
    parties.append(f'<line x1="{centre}" y1="{centre - rayon}" x2="{centre}" y2="{centre + rayon}" class="axe"/>')
    etiquettes = []
    for i, nom in enumerate(ANNEAUX):
        r = rayon * (bornes[i] + bornes[i + 1]) / 2 if i else 0
        largeur = 8 * len(nom) + 12
        etiquettes.append(
            f'<rect x="{centre - largeur / 2:.0f}" y="{centre - r - 11:.0f}" width="{largeur}" height="20" rx="10" class="fond-anneau"/>'
            f'<text x="{centre}" y="{centre - r + 4:.0f}" text-anchor="middle" class="nom-anneau">{e(nom)}</text>'
        )
    noms_quadrants = {q["id"]: q["nom"] for q in donnees["quadrants"]}
    coins = {"concevoir": (14, 26, "start"), "verifier": (taille - 14, 26, "end"),
             "couts": (14, taille - 12, "start"), "piloter": (taille - 14, taille - 12, "end")}
    for q, (x, y, ancre) in coins.items():
        parties.append(f'<text x="{x}" y="{y}" text-anchor="{ancre}" class="nom-quadrant">{e(noms_quadrants[q])}</text>')

    numeros: dict[str, int] = {}
    n = 0
    for q in ["concevoir", "verifier", "couts", "piloter"]:
        for anneau_index, anneau in enumerate(ANNEAUX):
            cellule = [o for o in outils.values() if quadrant_de[o["problemes"][0]] == q and o["verdict"] == anneau]
            debut, fin = ANGLES[q]
            marge = 22 if anneau_index == 0 else 11
            for i, o in enumerate(cellule):
                n += 1
                numeros[o["id"]] = n
                angle = math.radians(debut + marge + (i + 0.5) * (fin - debut - 2 * marge) / len(cellule))
                r_in, r_out = rayon * bornes[anneau_index], rayon * bornes[anneau_index + 1]
                fraction = (0.3, 0.72, 0.5)[i % 3] if anneau_index else (0.55, 0.85, 0.7)[i % 3]
                r = r_in + (r_out - r_in) * fraction
                x, y = centre + r * math.cos(angle), centre - r * math.sin(angle)
                classe = f'blip {CLASSE_VERDICT[anneau]} {o["origine"]}'
                titre = f'{n}. {o["nom"]} : {anneau} ({ORIGINE[o["origine"]]})'
                if o["origine"] == "natif":
                    forme = f'<rect x="{x - 9:.1f}" y="{y - 9:.1f}" width="18" height="18" rx="3"/>'
                else:
                    forme = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10"/>'
                parties.append(
                    f'<a href="#pb-{o["problemes"][0]}" class="{classe}"><title>{e(titre)}</title>{forme}'
                    f'<text x="{x:.1f}" y="{y + 3.5:.1f}" text-anchor="middle">{n}</text></a>'
                )
    parties.extend(etiquettes)
    svg = (
        f'<svg viewBox="0 0 {taille} {taille}" role="img" aria-label="Radar des outils par famille de problèmes et par verdict">'
        + "".join(parties)
        + "</svg>"
    )
    return svg, numeros


def legende_radar(donnees: dict, outils: dict, numeros: dict, quadrant_de: dict) -> str:
    blocs = []
    for q in donnees["quadrants"]:
        lignes = []
        for o in sorted((o for o in outils.values() if o["id"] in numeros and quadrant_de[o["problemes"][0]] == q["id"]),
                        key=lambda o: numeros[o["id"]]):
            lignes.append(f'<li><span class="num">{numeros[o["id"]]}</span> {lien_outil(o)} {badge(o["verdict"])} {etiquette_origine(o)}</li>')
        blocs.append(f'<div class="legende-q"><h4>{e(q["nom"])}</h4><ol>{"".join(lignes)}</ol></div>')
    return '<div class="legendes">' + "".join(blocs) + "</div>"


def matrice(donnees: dict, outils: dict) -> str:
    ordre = [p["id"] for p in donnees["problemes"]]
    entete = "".join(f'<th scope="col"><span>{e(COURT[p])}</span></th>' for p in ordre)
    lignes = []
    for p in ordre:
        for o in (o for o in outils.values() if o["problemes"][0] == p):
            cellules = []
            for q in ordre:
                if q == o["problemes"][0]:
                    cellules.append(f'<td class="c principal {CLASSE_VERDICT[o["verdict"]]}" title="problème principal">●</td>')
                elif q in o["problemes"]:
                    cellules.append('<td class="c" title="problème secondaire">○</td>')
                else:
                    cellules.append('<td class="c"></td>')
            lignes.append(
                f'<tr data-origine="{o["origine"]}"><th scope="row">{lien_outil(o)} {etiquette_origine(o)}</th>'
                f'<td>{badge(o["verdict"])}</td>{"".join(cellules)}</tr>'
            )
    filtres = (
        '<div class="filtres" role="group" aria-label="Filtrer les outils">'
        '<button data-filtre="tous" class="actif">Tous</button>'
        '<button data-filtre="liste">Liste initiale</button>'
        '<button data-filtre="nouveau">Nouveaux</button>'
        '<button data-filtre="natif">Natifs Anthropic</button></div>'
    )
    return (
        filtres
        + '<div class="defile"><table class="matrice"><thead><tr><th scope="col">Outil</th><th scope="col">Verdict</th>'
        + entete
        + "</tr></thead><tbody>"
        + "".join(lignes)
        + "</tbody></table></div>"
    )


def liste_verdicts(entrees: list, outils: dict) -> str:
    if not entrees:
        return '<p class="vide">Aucun.</p>'
    items = []
    for entree in entrees:
        o = outils[entree["outil"]]
        items.append(f'<li><strong>{lien_outil(o)}</strong> {etiquette_origine(o)}<br>{e(entree["pourquoi"])}</li>')
    return "<ul>" + "".join(items) + "</ul>"


def section_probleme(p: dict, outils: dict, existants: list) -> str:
    nouveau = ' <span class="origine nouveau">problème nouveau</span>' if p.get("nouveau") else ""
    etat = "".join(f"<li>{e(x)}</li>" for x in p["etat_art"])
    outils_existants = ", ".join(e(x["nom"]) for x in existants if p["id"] in x["problemes"])
    hors = ""
    if p["hors"]:
        hors = '<details class="hors-perimetre"><summary>Hors périmètre</summary>' + liste_verdicts(p["hors"], outils) + "</details>"
    return f"""
<section class="probleme" id="pb-{p["id"]}">
  <h3>{e(p["nom"])}{nouveau}</h3>
  <p class="resume">{e(p["resume"])}</p>
  <div class="contexte-grille">
    <div class="carte"><h4>Le problème, d'après les sources</h4><p>{e(p["constat"])}</p></div>
    <div class="carte"><h4>État de l'art</h4><ul>{etat}</ul></div>
    <div class="carte toi"><h4>Chez toi</h4><p>{e(p["chez_toi"])}</p>{f'<p class="petit">Outils en place : {outils_existants}</p>' if outils_existants else ""}</div>
  </div>
  <div class="verdicts">
    <div class="col recommandes"><h4>Recommandés</h4>{liste_verdicts(p["recommandes"], outils)}</div>
    <div class="col doute"><h4>Un doute plane</h4>{liste_verdicts(p["doute"], outils)}</div>
    <div class="col ecartes"><h4>À écarter</h4>{liste_verdicts(p["ecartes"], outils)}</div>
  </div>
  {hors}
</section>"""


def rapport_complet(chemin: Path) -> str:
    texte = chemin.read_text(encoding="utf-8")
    if texte.startswith("---"):
        texte = texte.split("---", 2)[2]
    texte = re.sub(r"^# .*\n", "", texte, count=1, flags=re.M)
    corps = markdown.markdown(texte, extensions=["tables", "sane_lists", "toc"])
    corps = re.sub(r"<tr>\s*<td>(\d+)</td>", r'<tr id="src-\1"><td>\1</td>', corps)
    corps = re.sub(r"\[(\d+)\]", r'<a class="cite" href="#src-\1">[\1]</a>', corps)
    corps = corps.replace("<table>", '<div class="defile"><table>').replace("</table>", "</table></div>")
    corps = re.sub(r"<h2 id=\"", '<h2 id="r-', corps)
    return corps


CSS = """
:root{--fond:#f7f7f5;--surface:#ffffff;--surface2:#f0efeb;--texte:#1d1d1f;--doux:#5b5b60;--trait:#dcdad3;--lien:#1f5fbf;
--adopter:#1f7a4d;--essayer:#2463b8;--evaluer:#a86200;--ecarter:#b3261e;--hors:#6b6b70;--accent:#5a3fc0;
--adopter-f:#e3f2ea;--essayer-f:#e4edf9;--evaluer-f:#fbefdc;--ecarter-f:#f9e3e1;--hors-f:#ececec}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--fond:#151517;--surface:#1e1e21;--surface2:#26262a;--texte:#ececee;--doux:#a5a5ab;--trait:#36363b;--lien:#8ab4ff;
--adopter:#5cc98f;--essayer:#78a9f0;--evaluer:#e2a64d;--ecarter:#f08a82;--hors:#9a9aa0;--accent:#a996ff;
--adopter-f:#16301f;--essayer-f:#172538;--evaluer-f:#33260f;--ecarter-f:#3a1a18;--hors-f:#2a2a2d}}
:root[data-theme="dark"]{--fond:#151517;--surface:#1e1e21;--surface2:#26262a;--texte:#ececee;--doux:#a5a5ab;--trait:#36363b;--lien:#8ab4ff;
--adopter:#5cc98f;--essayer:#78a9f0;--evaluer:#e2a64d;--ecarter:#f08a82;--hors:#9a9aa0;--accent:#a996ff;
--adopter-f:#16301f;--essayer-f:#172538;--evaluer-f:#33260f;--ecarter-f:#3a1a18;--hors-f:#2a2a2d}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:16px}
body{margin:0;background:var(--fond);color:var(--texte);font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--lien)}
.page{display:grid;grid-template-columns:250px minmax(0,1fr);max-width:1400px;margin:0 auto}
nav.sommaire{position:sticky;top:0;align-self:start;height:100vh;overflow:auto;padding:24px 16px;border-right:1px solid var(--trait);font-size:14px}
nav.sommaire a{display:block;padding:3px 0;color:var(--doux);text-decoration:none}
nav.sommaire a:hover{color:var(--texte)}
nav.sommaire .niv2{padding-left:12px}
nav.sommaire h2{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--doux);margin:16px 0 6px}
main{padding:32px 40px 80px;min-width:0}
header.titre h1{font-size:2rem;line-height:1.2;margin:0 0 6px}
header.titre p{color:var(--doux);margin:0}
.chiffres{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:24px 0}
.chiffre{background:var(--surface);border:1px solid var(--trait);border-radius:10px;padding:12px 14px}
.chiffre b{display:block;font-size:1.6rem;line-height:1.2}
.chiffre span{color:var(--doux);font-size:14px}
h2.partie{font-size:1.5rem;margin:56px 0 8px;padding-top:8px;border-top:2px solid var(--trait)}
.intro{color:var(--doux);max-width:75ch}
.essentiel{background:var(--surface);border:1px solid var(--trait);border-left:4px solid var(--accent);border-radius:10px;padding:16px 20px}
.essentiel li{margin:6px 0}
.quadrants{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.quadrant{background:var(--surface);border:1px solid var(--trait);border-radius:12px;padding:16px}
.quadrant h3{margin:0 0 10px;font-size:1.1rem}
.pb-carte{display:block;text-decoration:none;color:inherit;border:1px solid var(--trait);border-radius:8px;padding:10px 12px;margin:8px 0;background:var(--surface2)}
.pb-carte:hover{border-color:var(--accent)}
.pb-carte b{display:block}
.pb-carte small{color:var(--doux)}
.compte{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}
.badge{display:inline-block;font-size:12px;font-weight:600;padding:1px 8px;border-radius:999px;white-space:nowrap}
.badge.adopter{background:var(--adopter-f);color:var(--adopter)}
.badge.essayer{background:var(--essayer-f);color:var(--essayer)}
.badge.evaluer{background:var(--evaluer-f);color:var(--evaluer)}
.badge.ecarter{background:var(--ecarter-f);color:var(--ecarter)}
.badge.hors{background:var(--hors-f);color:var(--hors)}
.origine{display:inline-block;font-size:11px;padding:0 6px;border:1px solid var(--trait);border-radius:4px;color:var(--doux);white-space:nowrap}
.origine.nouveau{border-color:var(--accent);color:var(--accent)}
.origine.natif{border-color:var(--essayer);color:var(--essayer)}
.radar-bloc{display:grid;grid-template-columns:1fr;gap:24px}
.radar-bloc svg{width:100%;max-width:920px;margin:0 auto;display:block;height:auto;background:var(--surface);border:1px solid var(--trait);border-radius:12px}
.anneau{fill:none;stroke:var(--trait);stroke-width:1.5}
.anneau.a1{fill:var(--adopter-f)}.anneau.a2{fill:var(--essayer-f)}.anneau.a3{fill:var(--evaluer-f)}.anneau.a4{fill:var(--ecarter-f)}
.axe{stroke:var(--trait);stroke-width:2}
.nom-anneau{font-size:13px;fill:var(--texte);font-weight:600}
.fond-anneau{fill:var(--surface);opacity:.9;stroke:var(--trait)}
.nom-quadrant{font-size:17px;font-weight:700;fill:var(--texte)}
.blip circle,.blip rect{stroke-width:2}
.blip text{font-size:10px;font-weight:700;pointer-events:none}
.blip.adopter circle,.blip.adopter rect{fill:var(--adopter);stroke:var(--adopter)}
.blip.essayer circle,.blip.essayer rect{fill:var(--essayer);stroke:var(--essayer)}
.blip.evaluer circle,.blip.evaluer rect{fill:var(--evaluer);stroke:var(--evaluer)}
.blip.ecarter circle,.blip.ecarter rect{fill:var(--ecarter);stroke:var(--ecarter)}
.blip text{fill:#fff}
.blip.nouveau circle{fill:var(--surface)}
.blip.nouveau.adopter text{fill:var(--adopter)}.blip.nouveau.essayer text{fill:var(--essayer)}.blip.nouveau.evaluer text{fill:var(--evaluer)}.blip.nouveau.ecarter text{fill:var(--ecarter)}
.legende-formes{display:flex;gap:16px;flex-wrap:wrap;font-size:14px;color:var(--doux);margin:8px 0}
.legendes{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px 24px;font-size:14px}
.legende-q h4{margin:0 0 4px}
.legende-q ol{list-style:none;margin:0;padding:0}
.legende-q li{padding:2px 0}
.num{display:inline-block;min-width:24px;font-weight:700;color:var(--doux)}
.filtres{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.filtres button{font:inherit;font-size:14px;padding:4px 12px;border-radius:999px;border:1px solid var(--trait);background:var(--surface);color:var(--texte);cursor:pointer}
.filtres button.actif{background:var(--accent);border-color:var(--accent);color:#fff}
.defile{overflow-x:auto;-webkit-overflow-scrolling:touch;max-width:100%}
table{border-collapse:collapse;font-size:14px;background:var(--surface)}
th,td{border:1px solid var(--trait);padding:6px 8px;vertical-align:top;text-align:left}
thead th{background:var(--surface2);position:sticky;top:0}
.matrice th[scope=row]{min-width:240px;font-weight:400}
.matrice thead th span{writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap;font-size:13px}
.matrice td.c{text-align:center;width:34px;color:var(--doux)}
.matrice td.principal.adopter{color:var(--adopter)}.matrice td.principal.essayer{color:var(--essayer)}.matrice td.principal.evaluer{color:var(--evaluer)}.matrice td.principal.ecarter{color:var(--ecarter)}.matrice td.principal.hors{color:var(--hors)}
.probleme{background:var(--surface);border:1px solid var(--trait);border-radius:12px;padding:20px;margin:20px 0}
.probleme h3{margin:0;font-size:1.25rem}
.probleme .resume{color:var(--doux);margin:4px 0 12px}
.contexte-grille{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.carte{background:var(--surface2);border-radius:8px;padding:12px 14px;font-size:15px}
.carte h4,.col h4{margin:0 0 6px;font-size:14px;text-transform:uppercase;letter-spacing:.04em;color:var(--doux)}
.carte ul{margin:0;padding-left:18px}
.carte.toi{border-left:3px solid var(--accent)}
.petit{font-size:13px;color:var(--doux)}
.verdicts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:14px}
.col{border-radius:8px;padding:12px 14px;font-size:15px}
.col ul{margin:0;padding-left:18px}.col li{margin:0 0 10px}
.col.recommandes{background:var(--adopter-f)}.col.recommandes h4{color:var(--adopter)}
.col.doute{background:var(--evaluer-f)}.col.doute h4{color:var(--evaluer)}
.col.ecartes{background:var(--ecarter-f)}.col.ecartes h4{color:var(--ecarter)}
.vide{color:var(--doux);font-style:italic;margin:0}
details.hors-perimetre{margin-top:10px;font-size:15px}
details summary{cursor:pointer;color:var(--doux)}
.nouveautes{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.nouveautes .carte ul{padding-left:18px}
.nouveautes li{margin:6px 0}
.rapport{background:var(--surface);border:1px solid var(--trait);border-radius:12px;padding:24px 28px;max-width:100%}
.rapport h2{font-size:1.3rem;margin-top:36px}
.rapport p,.rapport li{max-width:85ch}
.rapport table{font-size:13px}
a.cite{font-size:.8em;text-decoration:none;vertical-align:super}
tr:target{background:var(--evaluer-f)}
.theme{position:fixed;right:16px;bottom:16px;font:inherit;font-size:13px;padding:6px 12px;border-radius:999px;border:1px solid var(--trait);background:var(--surface);color:var(--texte);cursor:pointer}
@media (max-width:1100px){.radar-bloc{grid-template-columns:1fr}.contexte-grille,.verdicts{grid-template-columns:1fr}}
@media (max-width:860px){.page{grid-template-columns:1fr}nav.sommaire{position:static;height:auto;border-right:0;border-bottom:1px solid var(--trait)}
main{padding:20px 16px 60px}.quadrants,.nouveautes,.legendes{grid-template-columns:1fr}.rapport{padding:16px}}
@media print{nav.sommaire,.theme,.filtres{display:none}.page{display:block}main{padding:0}.probleme,.quadrant{break-inside:avoid}}
"""

JS = """
(function(){
  var racine=document.documentElement;
  try{var t=localStorage.getItem('theme');if(t)racine.setAttribute('data-theme',t);}catch(e){}
  document.querySelector('.theme').addEventListener('click',function(){
    var sombre=racine.getAttribute('data-theme')==='dark'||(!racine.getAttribute('data-theme')&&matchMedia('(prefers-color-scheme: dark)').matches);
    var t=sombre?'light':'dark';racine.setAttribute('data-theme',t);try{localStorage.setItem('theme',t);}catch(e){}
  });
  document.querySelectorAll('.filtres button').forEach(function(b){
    b.addEventListener('click',function(){
      document.querySelectorAll('.filtres button').forEach(function(x){x.classList.remove('actif');});
      b.classList.add('actif');var f=b.dataset.filtre;
      document.querySelectorAll('.matrice tbody tr').forEach(function(tr){
        var o=tr.dataset.origine;var vu=f==='tous'||o===f||(f==='liste'&&o==='liste-doc');
        tr.style.display=vu?'':'none';
      });
    });
  });
})();
"""


def main() -> None:
    dossier, sortie = Path(sys.argv[1]), Path(sys.argv[2])
    donnees = json.loads((RACINE / "synthese" / "donnees.json").read_text(encoding="utf-8"))
    outils = {o["id"]: o for o in donnees["outils"]}
    quadrant_de = {p["id"]: p["quadrant"] for p in donnees["problemes"]}
    au_radar = {k: o for k, o in outils.items() if o["verdict"] in ANNEAUX}
    svg, numeros = radar(donnees, au_radar, quadrant_de)

    nb_liste = sum(1 for o in outils.values() if o["origine"] == "liste")
    nb_docs = sum(1 for o in outils.values() if o["origine"] == "liste-doc")
    nb_nouveaux = sum(1 for o in outils.values() if o["origine"] in ("nouveau", "natif"))
    chiffres = [
        (f"{nb_liste} + {nb_docs}", "dépôts et articles de ta liste"),
        (str(len(donnees["problemes"])), "problèmes, en 4 familles"),
        (str(nb_nouveaux), "ressources ajoutées par la veille"),
        (str(len(donnees["nouveaux_problemes"])), "problèmes absents de ta liste"),
        ("21", "affirmations porteuses revérifiées"),
    ]
    bloc_chiffres = "".join(f'<div class="chiffre"><b>{e(a)}</b><span>{e(b)}</span></div>' for a, b in chiffres)

    cartes_quadrants = []
    for q in donnees["quadrants"]:
        cartes = []
        for p in (p for p in donnees["problemes"] if p["quadrant"] == q["id"]):
            compte = (
                f'<span class="badge adopter">{len(p["recommandes"])} recommandés</span>'
                f'<span class="badge evaluer">{len(p["doute"])} en doute</span>'
                f'<span class="badge ecarter">{len(p["ecartes"])} à écarter</span>'
            )
            nouveau = ' <span class="origine nouveau">nouveau</span>' if p.get("nouveau") else ""
            cartes.append(f'<a class="pb-carte" href="#pb-{p["id"]}"><b>{e(p["nom"])}{nouveau}</b><small>{e(p["resume"])}</small><div class="compte">{compte}</div></a>')
        cartes_quadrants.append(f'<div class="quadrant"><h3>{e(q["nom"])}</h3>{"".join(cartes)}</div>')

    sections = "".join(section_probleme(p, outils, donnees["existants"]) for p in donnees["problemes"])

    nouveaux_pb = "".join(f'<li><strong>{e(x["nom"])}</strong> : {e(x["detail"])}</li>' for x in donnees["nouveaux_problemes"])
    nouvelles_ressources = []
    for p in donnees["problemes"]:
        ajoutes = [o for o in outils.values() if o["origine"] in ("nouveau", "natif") and o["problemes"][0] == p["id"]]
        if ajoutes:
            items = ", ".join(f'{lien_outil(o)} {badge(o["verdict"])}' for o in ajoutes)
            nouvelles_ressources.append(f'<li><strong>{e(p["nom"])}</strong> : {items}</li>')
    sources = "".join(
        f'<li><a href="{e(s["url"])}" target="_blank" rel="noopener">{e(s["nom"])}</a> : {e(s["apport"])}</li>'
        for s in donnees["nouvelles_sources"]
    )

    rapport = rapport_complet(dossier / "research.md")
    titres_rapport = re.findall(r'<h2 id="(r-[^"]+)">(.*?)</h2>', rapport)
    nav_rapport = "".join(f'<a class="niv2" href="#{i}">{re.sub("<[^>]+>", "", t)}</a>' for i, t in titres_rapport)
    nav_problemes = "".join(f'<a class="niv2" href="#pb-{p["id"]}">{e(p["nom"])}</a>' for p in donnees["problemes"])

    essentiel = """
<ul>
<li><strong>Aucun des 47 dépôts ne fait strictement mieux que son équivalent natif</strong> dans ta configuration : 1 à adopter (en partie), 13 à essayer, 15 à évaluer, 10 à écarter, 8 hors périmètre.</li>
<li><strong>Le levier, c'est le cadrage de l'agent, pas les plugins</strong> : un contexte court, des contrôles automatiques qui jugent son travail, une validation tôt dans la story. Littérature, Thoughtworks Radar et praticiens convergent.</li>
<li><strong>Le coût caché, c'est le contexte fixe et le cache</strong>, pas la sortie : compresser les sorties rapporte ~2,7 %, retirer les outils inutilisés 13 à 18 %.</li>
<li><strong>Les plugins sont peu prouvés ; les contrôles déterministes le sont un peu plus</strong> : tests verrouillés, mutation testing, tests de propriétés, plutôt que des consignes.</li>
<li><strong>Ta configuration actuelle va déjà dans ce sens</strong> (BMAD, agent-cost-kit, CLAUDE.md et MEMORY.md courts) ; ce qui lui manque : la mesure du contexte fixe, la protection des tests, une preuve empirique en revue, une boucle de vérification du front.</li>
</ul>"""

    page = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Veille agents de code</title>
<meta name="description" content="Synthèse visuelle et rapport complet de la veille du {e(donnees["date"])} sur les outils, plugins et pratiques des agents de code.">
<style>{CSS}</style>
</head>
<body>
<div class="page">
<nav class="sommaire" aria-label="Sommaire">
  <h2>Synthèse</h2>
  <a href="#essentiel">L'essentiel</a>
  <a href="#categories">1. Les catégories de problèmes</a>
  <a href="#radar">2. Le radar</a>
  <a href="#carte">3. Quels outils pour quels problèmes</a>
  <a href="#problemes">4. Problème par problème</a>
  {nav_problemes}
  <a href="#nouveautes">5. Ce que la veille a ajouté</a>
  <h2>Rapport complet</h2>
  <a href="#rapport">Rapport</a>
  {nav_rapport}
</nav>
<main>
<header class="titre">
  <h1>{e(donnees["titre"])}</h1>
  <p>Veille du {e(donnees["date"])} sur les outils, plugins et pratiques des agents de code, pour la configuration Claude Code d'Anaël : Windows, abonnement Max, BMAD, agent-cost-kit, FastAPI + Jinja2 + HTML/CSS/JS vanilla.</p>
</header>
<div class="chiffres">{bloc_chiffres}</div>

<h2 class="partie" id="essentiel">L'essentiel</h2>
<div class="essentiel">{essentiel}</div>

<h2 class="partie" id="categories">1. Les catégories de problèmes</h2>
<p class="intro">Treize problèmes que rencontrent les agents de code, regroupés en quatre familles. Chaque carte mène au détail : le problème selon les sources, l'état de l'art, ce que tu as déjà, et les verdicts.</p>
<div class="quadrants">{"".join(cartes_quadrants)}</div>

<h2 class="partie" id="radar">2. Le radar</h2>
<p class="intro">Chaque point est un outil ou une pratique, placé dans la famille de son problème principal et dans l'anneau de son verdict, du centre (Adopter) vers l'extérieur (Écarter). Les outils hors périmètre n'y figurent pas. Survole un point pour son nom, clique pour aller au problème.</p>
<div class="legende-formes"><span>● plein : liste initiale</span><span>○ creux : nouveau, ajouté par la veille</span><span>■ carré : fonction native ou plugin officiel d'Anthropic</span></div>
<div class="radar-bloc">{svg}{legende_radar(donnees, au_radar, numeros, quadrant_de)}</div>

<h2 class="partie" id="carte">3. Quels outils pour quels problèmes</h2>
<p class="intro">● problème principal de l'outil (couleur du verdict), ○ problème secondaire. Les filtres séparent ta liste initiale des ressources ajoutées par la veille.</p>
{matrice(donnees, outils)}

<h2 class="partie" id="problemes">4. Problème par problème</h2>
<p class="intro">Pour chaque problème : ce que disent les sources, l'état de l'art, ce que tu as déjà, puis les outils recommandés, ceux sur lesquels un doute plane, et ceux à écarter, avec la raison à chaque fois.</p>
{sections}

<h2 class="partie" id="nouveautes">5. Ce que la veille a ajouté à ta liste</h2>
<div class="nouveautes">
  <div class="carte"><h4>Problèmes que ta liste ne couvrait pas</h4><ul>{nouveaux_pb}</ul></div>
  <div class="carte"><h4>Études, radars et enquêtes</h4><ul>{sources}</ul></div>
</div>
<div class="carte" style="margin-top:16px"><h4>Ressources ajoutées, par problème</h4><ul>{"".join(nouvelles_ressources)}</ul></div>

<h2 class="partie" id="rapport">Rapport complet</h2>
<p class="intro">Le rapport de recherche, avec ses 142 sources numérotées (cliquer sur un renvoi mène à la source), la carte des affirmations à revérifier et les tests proposés.</p>
<article class="rapport">{rapport}</article>
</main>
</div>
<button class="theme" type="button">Clair / sombre</button>
<script>{JS}</script>
</body>
</html>"""
    sortie.write_text(page, encoding="utf-8")
    print(f"{sortie} : {len(page) // 1024} Ko, {len(numeros)} points au radar", file=sys.stderr)


if __name__ == "__main__":
    main()
