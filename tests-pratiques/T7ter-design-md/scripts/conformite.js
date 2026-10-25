// Contrôles de conformité aux règles de DESIGN.md, évalués dans la page (DOM + CSS calculé).
// Appel : page.evaluate(CONFORMITE_JS, {mode, cfg}) avec mode in {"initial", "erreur", "typo"}.
// Indicatif : la note humaine tranche. Les pseudo-éléments ne sont pas lus.
(arg) => {
  const {mode, cfg} = arg;
  const cv = document.createElement('canvas'); cv.width = cv.height = 1;
  const cx = cv.getContext('2d', {willReadFrequently: true});
  function parse(c) {
    if (!c || c === 'transparent') return {r: 0, g: 0, b: 0, a: 0};
    cx.clearRect(0, 0, 1, 1); cx.fillStyle = '#000'; cx.fillStyle = c; cx.fillRect(0, 0, 1, 1);
    const d = cx.getImageData(0, 0, 1, 1).data; return {r: d[0], g: d[1], b: d[2], a: d[3] / 255};
  }
  const over = (f, b) => ({r: f.r * f.a + b.r * (1 - f.a), g: f.g * f.a + b.g * (1 - f.a), b: f.b * f.a + b.b * (1 - f.a), a: 1});
  const lum = (c) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const ratio = (a, b) => { const l1 = lum(a), l2 = lum(b); return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05); };
  function bgOf(el) {
    const layers = []; let e = el;
    while (e) { const c = parse(getComputedStyle(e).backgroundColor); if (c.a > 0) { layers.push(c); if (c.a >= 0.99) break; } e = e.parentElement; }
    let base = {r: 255, g: 255, b: 255, a: 1};
    for (let i = layers.length - 1; i >= 0; i--) base = over(layers[i], base);
    return base;
  }
  const chroma = c => Math.max(c.r, c.g, c.b) - Math.min(c.r, c.g, c.b);
  function hue(c) {
    const mx = Math.max(c.r, c.g, c.b), mn = Math.min(c.r, c.g, c.b), d = mx - mn; if (d === 0) return -1;
    let h; if (mx === c.r) h = ((c.g - c.b) / d) % 6; else if (mx === c.g) h = (c.b - c.r) / d + 2; else h = (c.r - c.g) / d + 4;
    h *= 60; return h < 0 ? h + 360 : h;
  }
  const colored = c => c.a >= 0.3 && chroma(c) > 40;
  const redHue = c => { const h = hue(c); return h >= 0 && (h <= 15 || h >= 335); };
  const redBorder = c => c.a >= 0.3 && chroma(c) >= 40 && redHue(c);
  const redFill = c => c.a >= 0.3 && chroma(c) >= 8 && redHue(c);
  const visible = el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const lower = s => norm(s).toLowerCase();
  const fontW = cs => { const w = cs.fontWeight; return w === 'bold' ? 700 : (w === 'normal' ? 400 : parseInt(w)); };
  function textEl(cell) {
    const w = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT); let n;
    while (n = w.nextNode()) if (n.textContent.trim()) return n.parentElement;
    return cell;
  }
  function firstTextNode(cell) {
    const w = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT); let n;
    while (n = w.nextNode()) if (n.textContent.trim()) return n;
    return null;
  }
  const px = v => parseFloat(v) || 0;
  const out = {};

  const table = document.querySelector('table');
  function colIndex(name) {
    if (!table) return -1;
    const ths = Array.from(table.querySelectorAll('thead th, thead td'));
    return ths.findIndex(t => lower(t.textContent).startsWith(name.toLowerCase()));
  }
  function rows() {
    if (!table) return [];
    return Array.from(table.querySelectorAll('tbody tr')).filter(visible);
  }
  function cellsOf(idx) { return rows().map(r => r.children[idx]).filter(Boolean); }
  const tableLisible = table && rows().length > 0 && getComputedStyle(rows()[0]).display.startsWith('table');

  if (mode === 'typo') {
    const sel = {body: document.body, h1: document.querySelector('h1'),
      label: Array.from(document.querySelectorAll('label')).find(visible),
      th: table ? Array.from(table.querySelectorAll('th')).find(visible) : null,
      td: table ? Array.from(table.querySelectorAll('tbody td')).find(visible) : null,
      button: Array.from(document.querySelectorAll('button')).find(visible)};
    const snap = {};
    for (const [k, el] of Object.entries(sel)) {
      if (!el) { snap[k] = null; continue; }
      const cs = getComputedStyle(el);
      snap[k] = {famille: cs.fontFamily.split(',')[0].replace(/["']/g, '').trim().toLowerCase(), graisse: fontW(cs), casse: cs.textTransform,
        interlettrage: cs.letterSpacing === 'normal' ? 0 : Math.round(px(cs.letterSpacing) / px(cs.fontSize) * 1000) / 1000, style: cs.fontStyle, taille: px(cs.fontSize)};
    }
    out.snap = snap;
    const fam = new Set();
    for (const el of Array.from(document.querySelectorAll('body *')).slice(0, 500)) {
      if (!visible(el)) continue;
      const own = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim());
      if (own) fam.add(getComputedStyle(el).fontFamily.split(',')[0].replace(/["']/g, '').trim().toLowerCase());
    }
    out.familles = Array.from(fam).sort();
    return out;
  }

  const form = document.querySelector('form');
  const submit = Array.from(document.querySelectorAll('button')).find(b => visible(b) && lower(b.textContent).includes(cfg.submit.toLowerCase()));

  if (mode === 'erreur') {
    // R1 : pas de contour ni de bordure d'accent colorés autour du bloc d'alerte
    const alerts = Array.from(document.querySelectorAll('[role="alert"]')).filter(visible);
    if (!alerts.length) { out.R1 = null; out.R1bis = null; }
    else {
      const a = alerts[0], ar = a.getBoundingClientRect();
      const cand = [a];
      for (const d of a.querySelectorAll('*')) { const r = d.getBoundingClientRect(); if (r.width >= 0.9 * ar.width && r.height >= 0.6 * ar.height) cand.push(d); }
      const p = a.parentElement; if (p && p !== document.body) { const r = p.getBoundingClientRect(); if (r.width <= ar.width + 16 && r.height <= ar.height + 16) cand.push(p); }
      const fautes = [];
      for (const el of cand) {
        const cs = getComputedStyle(el);
        for (const s of ['Top', 'Right', 'Bottom', 'Left']) {
          if (px(cs['border' + s + 'Width']) > 0 && cs['border' + s + 'Style'] !== 'none' && colored(parse(cs['border' + s + 'Color']))) fautes.push(`bordure-${s.toLowerCase()} ${cs['border' + s + 'Width']} ${cs['border' + s + 'Color']}`);
        }
        if (px(cs.outlineWidth) > 0 && cs.outlineStyle !== 'none' && colored(parse(cs.outlineColor))) fautes.push('contour ' + cs.outlineColor);
        if (cs.boxShadow && cs.boxShadow !== 'none') {
          const m = cs.boxShadow.match(/(rgba?\([^)]*\)|oklch\([^)]*\)|color\([^)]*\)|#[0-9a-f]{3,8})/gi) || [];
          for (const c of m) if (colored(parse(c))) fautes.push('ombre ' + c);
        }
        if (cs.borderImageSource && cs.borderImageSource !== 'none') fautes.push('border-image');
      }
      out.R1 = fautes.length === 0; out.R1_detail = Array.from(new Set(fautes)).slice(0, 5);
      // R1 bis : bloc en haut du formulaire, près de l'action
      const champs = Array.from(document.querySelectorAll('form input:not([type=hidden]), form select, form textarea')).filter(visible);
      const premier = champs[0], dedans = form && form.contains(a);
      const auDessus = premier ? ar.top < premier.getBoundingClientRect().top : null;
      const prochedeAction = submit ? (submit.getBoundingClientRect().top - ar.bottom) <= 400 : null;
      out.R1bis = (auDessus === null) ? null : (auDessus && (dedans || prochedeAction === true));
      out.R1bis_detail = {au_dessus_du_premier_champ: auDessus, dans_le_formulaire: dedans, distance_action_px: submit ? Math.round(submit.getBoundingClientRect().top - ar.bottom) : null};
    }
    // R2 : champ invalide à bordure rouge, sans fond rouge
    const invalides = Array.from(document.querySelectorAll('[aria-invalid="true"]')).filter(visible);
    if (!invalides.length) { out.R2 = null; }
    else {
      let bordureOk = 0, fondRouge = 0; const det = [];
      for (const el of invalides) {
        const cs = getComputedStyle(el);
        let rouge = false;
        for (const s of ['Top', 'Right', 'Bottom', 'Left']) if (px(cs['border' + s + 'Width']) > 0 && cs['border' + s + 'Style'] !== 'none' && redBorder(parse(cs['border' + s + 'Color']))) rouge = true;
        if (!rouge && cs.boxShadow && cs.boxShadow !== 'none') { const m = cs.boxShadow.match(/(rgba?\([^)]*\)|oklch\([^)]*\)|#[0-9a-f]{3,8})/gi) || []; if (m.some(c => redBorder(parse(c)))) rouge = true; }
        if (rouge) bordureOk++;
        const bg = parse(cs.backgroundColor);
        if (redFill(bg)) { fondRouge++; det.push(cs.backgroundColor); }
      }
      out.R2 = bordureOk === invalides.length && fondRouge === 0;
      out.R2_detail = {invalides: invalides.length, avec_bordure_rouge: bordureOk, avec_fond_rouge: fondRouge, fonds: det.slice(0, 3)};
    }
    return out;
  }

  // mode initial (1280)
  // R3 : action principale en haut, repérable
  if (!submit) out.R3 = null;
  else {
    const r = submit.getBoundingClientRect(), top = r.top + window.scrollY;
    const cs = getComputedStyle(submit);
    const fond = bgOf(submit.parentElement || document.body), bouton = over(parse(cs.backgroundColor), fond);
    const page = bgOf(document.body);
    const contrasteFond = ratio(bouton, page);
    const autres = Array.from(document.querySelectorAll('button')).filter(b => b !== submit && visible(b));
    let plusMarque = true;
    for (const b of autres) {
      const rb = b.getBoundingClientRect(), cb = over(parse(getComputedStyle(b).backgroundColor), bgOf(b.parentElement || document.body));
      const plusGrand = r.width * r.height >= rb.width * rb.height * 1.0;
      const plusContraste = ratio(bouton, page) >= ratio(cb, page);
      if (!(plusGrand || plusContraste)) plusMarque = false;
    }
    out.R3 = top < 900 && contrasteFond >= 3 && plusMarque;
    out.R3_detail = {haut_px: Math.round(top), contraste_fond: Math.round(contrasteFond * 100) / 100, autres_boutons: autres.length, plus_marque: plusMarque};
  }
  if (!tableLisible) { out.R4 = out.R4bis = out.R5 = out.R6 = out.R7 = null; out.tableau = false; }
  else {
    out.tableau = true;
    const rs = rows();
    // R4 : lignes alternées
    const bgs = rs.slice(0, 4).map(r => bgOf(r.children[0]));
    const diff = (a, b) => Math.abs(a.r - b.r) + Math.abs(a.g - b.g) + Math.abs(a.b - b.b);
    let alt = bgs.length >= 3; for (let i = 0; i + 1 < bgs.length; i++) if (diff(bgs[i], bgs[i + 1]) < 4) alt = false;
    out.R4 = alt; out.R4_detail = bgs.map(c => `rgb(${Math.round(c.r)},${Math.round(c.g)},${Math.round(c.b)})`);
    // R4 bis : en-têtes distincts
    const th = Array.from(table.querySelectorAll('thead th')).find(visible), td0 = rs[0].children[0];
    if (!th) out.R4bis = null;
    else {
      const cth = getComputedStyle(th), ctd = getComputedStyle(td0), bth = bgOf(th), btd = bgOf(td0);
      const fond = diff(bth, btd) >= 12;
      const trait = px(cth.borderBottomWidth) >= 2 && cth.borderBottomStyle !== 'none';
      const typo = fontW(cth) >= 600 && fontW(cth) > fontW(ctd) && (cth.textTransform === 'uppercase' || px(cth.letterSpacing) > 0.3);
      out.R4bis = fond || trait || typo; out.R4bis_detail = {fond, trait, typo};
    }
    // R5 : colonne d'identité en gras
    const ii = colIndex(cfg.idCol), di = colIndex(cfg.descCol);
    if (ii < 0) out.R5 = null;
    else {
      const ws = cellsOf(ii).map(c => fontW(getComputedStyle(textEl(c))));
      const wd = di >= 0 ? cellsOf(di).map(c => fontW(getComputedStyle(textEl(c)))) : [400];
      out.R5 = ws.length > 0 && ws.every(w => w >= 600) && Math.min(...ws) > Math.max(...wd);
      out.R5_detail = {graisses_identite: Array.from(new Set(ws)), graisses_description: Array.from(new Set(wd))};
    }
    // R6 : montants à droite, chiffres tabulaires
    const mi = colIndex(cfg.montantCol);
    if (mi < 0) out.R6 = null;
    else {
      const cells = cellsOf(mi), head = Array.from(table.querySelectorAll('thead th, thead td'))[mi];
      const aDroite = c => {
        const cs = getComputedStyle(c), t = getComputedStyle(textEl(c));
        if (['right', 'end'].includes(cs.textAlign) || ['right', 'end'].includes(t.textAlign)) return true;
        const n = firstTextNode(c); if (!n) return false;
        const rg = document.createRange(); rg.selectNodeContents(n); const tr = rg.getBoundingClientRect(), cr = c.getBoundingClientRect();
        return (cr.right - px(cs.paddingRight) - tr.right) <= 3 && (tr.left - cr.left - px(cs.paddingLeft)) > 3;
      };
      const tab = c => { const t = getComputedStyle(textEl(c)); return /tabular-nums/.test(t.fontVariantNumeric) || /tnum/.test(t.fontFeatureSettings) || /mono|consolas|courier/i.test(t.fontFamily); };
      const droite = cells.every(aDroite) && (!head || aDroite(head));
      const tabulaire = cells.every(tab);
      out.R6 = droite && tabulaire; out.R6_detail = {droite, entete_droite: head ? aDroite(head) : null, tabulaire};
    }
    // R7 : valeurs de catégorie en étiquettes (une couleur par valeur, contraste suffisant)
    out.R7_colonnes = {};
    let tout = true, appl = false;
    for (const nom of cfg.catCols) {
      const ci = colIndex(nom); if (ci < 0) continue; appl = true;
      const cells = cellsOf(ci), parValeur = {}; let toutesEtiquettes = true, contrasteMin = 99;
      for (const c of cells) {
        const valeur = norm(c.textContent), te = textEl(c);
        let badge = (te !== c) ? te : null;
        // remonter jusqu'à l'élément qui entoure tout le texte (hors cellule)
        while (badge && badge.parentElement !== c && norm(badge.parentElement.textContent) === valeur) badge = badge.parentElement;
        let ok = false;
        if (badge && badge !== c) {
          const cs = getComputedStyle(badge), bg = parse(cs.backgroundColor);
          const bordure = px(cs.borderTopWidth) > 0 && cs.borderTopStyle !== 'none' && parse(cs.borderTopColor).a > 0.3 && chroma(parse(cs.borderTopColor)) > 20;
          const arrondi = px(cs.borderTopLeftRadius) > 0 || /%/.test(cs.borderTopLeftRadius);
          ok = (bg.a > 0.05 || bordure) && arrondi && norm(badge.textContent) === valeur;
          if (ok) {
            const fond = over(bg, bgOf(c)), txt = over(parse(cs.color), fond);
            contrasteMin = Math.min(contrasteMin, ratio(txt, fond));
            (parValeur[valeur] = parValeur[valeur] || new Set()).add(`${Math.round(fond.r)},${Math.round(fond.g)},${Math.round(fond.b)}`);
          }
        }
        if (!ok) toutesEtiquettes = false;
      }
      const valeurs = Object.keys(parValeur), toutes = new Set(valeurs.flatMap(v => Array.from(parValeur[v])));
      const uneParValeur = toutesEtiquettes && valeurs.every(v => parValeur[v].size === 1) && toutes.size === valeurs.length;
      const colOk = toutesEtiquettes && uneParValeur && contrasteMin >= 4.5;
      out.R7_colonnes[nom] = {etiquettes: toutesEtiquettes, une_couleur_par_valeur: uneParValeur, contraste_min: contrasteMin === 99 ? null : Math.round(contrasteMin * 100) / 100, valeurs: valeurs.length, couleurs: toutes.size, ok: colOk};
      if (!colOk) tout = false;
    }
    out.R7 = appl ? tout : null;
  }
  // R9 : pas trop sobre
  const teintes = new Set(), couleurs = new Set();
  for (const el of Array.from(document.querySelectorAll('body, body *')).slice(0, 700)) {
    if (!visible(el)) continue;
    const cs = getComputedStyle(el);
    const cands = [parse(cs.backgroundColor), parse(cs.color)];
    if (px(cs.borderTopWidth) > 0 && cs.borderTopStyle !== 'none') cands.push(parse(cs.borderTopColor));
    for (const c of cands) if (c.a >= 0.3 && chroma(c) > 40) { teintes.add(Math.floor(hue(c) / 30)); couleurs.add([c.r, c.g, c.b].map(v => Math.round(v / 16)).join(',')); }
  }
  out.R9 = teintes.size >= 2; out.R9_detail = {familles_de_teintes: teintes.size, couleurs_distinctes: couleurs.size};
  return out;
}
