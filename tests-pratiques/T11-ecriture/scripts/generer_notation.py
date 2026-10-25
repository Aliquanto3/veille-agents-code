"""Génère notation.html (autonome) : par texte, la source puis les sorties sous des lettres tirées au hasard.

La correspondance lettre -> condition est dans correspondance.json (hors dépôt, dans .gitignore) et n'est pas
référencée par la page. Les lettres déjà tirées sont conservées : on peut ajouter un texte (X3, X4) sans
changer celles des textes déjà notés.

Usage : uv run python generer_notation.py [X1 X2 X3 X4]
"""
import html, json, random, secrets, sys
import markdown
from config import T11, CONDITIONS, ESSAIS, NOMS, lire_source, langue

TITRES = {
    "X1": "X1 · Brouillon de post LinkedIn (écrit par un modèle)",
    "X2": "X2 · Texte technique dense (résumé exécutif)",
    "X3": "X3 · Post publié, écrit par toi",
    "X4": "X4 · Texte technique en anglais (arXiv 2609.00006)",
}
LECTEURS = {
    "X1": "tes contacts LinkedIn, consultants et développeurs",
    "X2": "un responsable technique qui décide de la configuration de son équipe",
    "X3": "tes contacts LinkedIn, consultants et développeurs",
    "X4": "an engineering lead choosing a coding-agent setup",
}


def md(t: str) -> str:
    t = t.replace("&", "&amp;").replace("<", "&lt;")
    return markdown.markdown(t, extensions=["nl2br", "sane_lists"])


def main():
    textes = sys.argv[1:] or sorted(d.name for d in (T11 / "sorties").iterdir() if d.is_dir())
    cf = T11 / "correspondance.json"
    corr = json.loads(cf.read_text(encoding="utf-8")) if cf.exists() else {}
    rng = random.SystemRandom()
    data = []
    for tid in textes:
        sorties = {f"{c}-{e}": (T11 / "sorties" / tid / f"{c}-{e}.md") for c in CONDITIONS for e in ESSAIS}
        sorties = {k: p for k, p in sorties.items() if p.exists()}
        if not sorties:
            continue
        if tid not in corr:
            cles = list(sorties)
            rng.shuffle(cles)
            # lettres tirées par secrets (ordre mélangé), A..H
            lettres = [chr(65 + i) for i in range(len(cles))]
            ordre = sorted(range(len(cles)), key=lambda _: secrets.randbelow(10**9))
            corr[tid] = {lettres[i]: cles[ordre[i]] for i in range(len(cles))}
        inv = {v: k for k, v in corr[tid].items()}
        items = [{"lettre": inv[k], "html": md(p.read_text(encoding="utf-8"))} for k, p in sorties.items() if k in inv]
        items.sort(key=lambda x: x["lettre"])
        lect_f = T11 / "textes" / tid / "lecteur.txt"
        lecteur = LECTEURS.get(tid) or (lect_f.read_text(encoding="utf-8").strip() if lect_f.exists() else "")
        data.append({"id": tid, "titre": TITRES.get(tid, tid), "lecteur": lecteur, "lang": langue(tid),
                     "source": md(lire_source(tid)), "sorties": items, "voix": tid == "X3"})
    cf.write_text(json.dumps(corr, ensure_ascii=False, indent=1), encoding="utf-8")
    page = PAGE.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    (T11 / "notation.html").write_text(page, encoding="utf-8")
    print("notation.html :", [(d["id"], len(d["sorties"])) for d in data])


PAGE = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Notation T11</title>
<style>
:root{--bg:#fafaf7;--fg:#1c1c1a;--mut:#62625c;--card:#fff;--bd:#d9d8d0;--ac:#1d4f91;--src:#f1efe6}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--fg:#ecebe4;--mut:#a3a29a;--card:#201f1c;--bd:#3a3935;--ac:#7fb0ee;--src:#26251f}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,sans-serif}
main{max-width:860px;margin:0 auto;padding:16px}
h1{font-size:1.3rem;margin:.4rem 0}
.mut{color:var(--mut);font-size:.9rem}
nav{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0}
nav button{border:1px solid var(--bd);background:var(--card);color:var(--fg);padding:8px 12px;border-radius:8px;cursor:pointer;font:inherit}
nav button[aria-pressed=true]{border-color:var(--ac);color:var(--ac);font-weight:600}
details.src{background:var(--src);border:1px solid var(--bd);border-radius:8px;padding:8px 14px;margin:12px 0}
details.src summary{cursor:pointer;font-weight:600}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:14px 16px;margin:18px 0}
.card h2{font-size:1.1rem;margin:0 0 8px}
.txt{border-left:3px solid var(--bd);padding:2px 12px;margin:8px 0 14px}
.txt p{margin:.5em 0}
.grille{display:grid;grid-template-columns:1fr;gap:8px}
.crit{display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px}
.crit>span{min-width:230px;font-size:.92rem}
.crit label{display:inline-flex;align-items:center;gap:4px;padding:4px 8px;border:1px solid var(--bd);border-radius:6px;cursor:pointer}
textarea{width:100%;min-height:60px;margin-top:10px;background:var(--bg);color:var(--fg);border:1px solid var(--bd);border-radius:6px;padding:8px;font:inherit}
.bar{position:sticky;bottom:0;background:var(--bg);border-top:1px solid var(--bd);padding:10px 0;display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.bar button{padding:8px 14px;border-radius:8px;border:1px solid var(--ac);background:var(--ac);color:#fff;cursor:pointer;font:inherit}
.bar button.sec{background:transparent;color:var(--ac)}
@media (max-width:520px){.crit>span{min-width:100%}}
</style>
</head>
<body>
<main>
<h1>Notation à l'aveugle, T11 : réécriture de textes</h1>
<p class="mut">Pour chaque texte, lis d'abord la source, puis note chaque version (les lettres sont tirées au hasard). Échelle de 1 (mauvais) à 5 (excellent). Tout est sauvegardé dans ton navigateur ; exporte le JSON à la fin.</p>
<ul class="mut">
<li><b>Fidélité</b> : la version dit la même chose que la source, sans rien ajouter ni durcir.</li>
<li><b>Clarté</b> : on comprend vite, la structure aide.</li>
<li><b>Naturel</b> : « on dirait un humain qui sait de quoi il parle ».</li>
<li><b>Je le publierais</b> : tel quel, sous mon nom, à ce lecteur.</li>
</ul>
<nav id="nav"></nav>
<div id="vue"></div>
<div class="bar"><button id="exp">Exporter en JSON</button><button class="sec" id="cop">Copier le JSON</button><span class="mut" id="etat"></span></div>
</main>
<script>
const DATA = __DATA__;
const CRITS = [["fidelite","Fidélité"],["clarte","Clarté"],["naturel","Naturel"],["publier","Je le publierais"]];
const KEY = "t11-notation-v1";
let S = {};
try { S = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch(e) { S = {}; }
function save(){ try { localStorage.setItem(KEY, JSON.stringify(S)); } catch(e) {} document.getElementById("etat").textContent = "Sauvegardé " + new Date().toLocaleTimeString(); }
let cur = 0;
function rendre(){
  const nav = document.getElementById("nav"); nav.innerHTML = "";
  DATA.forEach((d,i)=>{ const b = document.createElement("button"); b.textContent = d.id; b.setAttribute("aria-pressed", i===cur); b.onclick=()=>{cur=i;rendre();window.scrollTo(0,0)}; nav.appendChild(b); });
  const d = DATA[cur]; const v = document.getElementById("vue");
  const crits = d.voix ? CRITS.concat([["voix","Ça sonne comme moi (ma voix)"]]) : CRITS;
  let h = `<h2>${d.titre}</h2><p class="mut">Lecteur visé : ${d.lecteur}</p><details class="src" open><summary>Source (référence)</summary><div class="txt">${d.source}</div></details>`;
  d.sorties.forEach(s=>{
    const k = d.id + "/" + s.lettre; const e = S[k] || {};
    h += `<section class="card" id="c-${k.replace('/','-')}"><h2>Version ${s.lettre}</h2><div class="txt">${s.html}</div><div class="grille">`;
    crits.forEach(([c,l])=>{
      h += `<div class="crit"><span>${l}</span>`;
      for(let n=1;n<=5;n++) h += `<label><input type="radio" name="${k}-${c}" value="${n}" data-k="${k}" data-c="${c}" ${e[c]==n?"checked":""}>${n}</label>`;
      h += `</div>`;
    });
    h += `</div><textarea placeholder="Commentaire libre (facultatif)" data-k="${k}" data-c="commentaire">${(e.commentaire||"").replace(/</g,"&lt;")}</textarea></section>`;
  });
  v.innerHTML = h;
  v.querySelectorAll("input[type=radio]").forEach(i=>i.onchange=()=>{ (S[i.dataset.k] ||= {})[i.dataset.c] = +i.value; save(); });
  v.querySelectorAll("textarea").forEach(t=>t.oninput=()=>{ (S[t.dataset.k] ||= {})[t.dataset.c] = t.value; save(); });
}
function exporter(){ return JSON.stringify({version:"t11-v1", exporte_le:new Date().toISOString(), notes:S}, null, 1); }
document.getElementById("exp").onclick=()=>{ const a=document.createElement("a"); a.href=URL.createObjectURL(new Blob([exporter()],{type:"application/json"})); a.download="notation-t11.json"; a.click(); };
document.getElementById("cop").onclick=async()=>{ try{ await navigator.clipboard.writeText(exporter()); document.getElementById("etat").textContent="JSON copié"; }catch(e){ document.getElementById("etat").textContent="Copie impossible, utilise l'export"; } };
rendre();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
