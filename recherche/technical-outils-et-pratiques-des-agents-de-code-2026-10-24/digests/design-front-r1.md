# Digest « design-front » : tour 1 (run du 2026-10-24)

Dimension : qualité visuelle et UX des interfaces produites par les agents (éviter le « AI slop »), design systems lisibles par l'agent, animation, composants. Pile cible : FastAPI + Jinja2 + HTML/CSS/JS vanilla.
Budget consommé : 20 appels web sur 25, environ 19 lectures de dépôt sur 20. Arrêt après le tour 2 : budget de dépôt presque épuisé, et les questions sont couvertes au niveau que permettent les sources (aucune ne publie de mesure indépendante solide).

## 1. Résumé

- Aucune skill anti-slop n'est **strictement meilleure** que les autres. La seule mesure en aveugle publiée par un éditeur, celle de taste-skill, donne **7,7 avec la skill contre 7,8 sans skill** [A7]. La seule ablation externe, faite sur hallmark, montre un effet net sur **une** règle (noir et blanc purs : 100 % → 50 % des pages) et un effet inverse sur une autre [A12].
- Le maillon faible commun est l'**activation et la lecture des références**. Une skill ne se déclenche pas toujours quand on ne la nomme pas (0/10 sur un cas impeccable, aucune activation sur hallmark [A5][A13]), et les fichiers de règles derrière le SKILL.md ne sont pas ouverts [A13]. Dans un sous-agent `dev-story`, il faut donc **nommer la skill** et **placer les règles critiques dans le contexte chargé**.
- La **vérification** utile repose sur des outils déterministes exécutés sur la page rendue : `impeccable detect <url>` (62 règles, sans LLM), `sloplint --render` de hallmark (8 largeurs) et `inspect.mjs` de taste (3 largeurs) [A2][A10][A6]. La critique d'images par le modèle vient ensuite. Dans la littérature, une boucle « critique visuelle » sur capture d'écran apporte jusqu'à +17,8 % en 3 tours [A24].
- Pour la pile vanilla : impeccable (scan d'URL), hallmark (pages HTML/CSS autonomes), DESIGN.md, emil (règles d'animation) et la skill officielle `frontend-design` restent utiles. Restent liés à React/shadcn ou hors sujet : react-bits, canvas-ui (build vanilla existant mais distribué via shadcn), ui-ux-pro-max (Tailwind par défaut), scroll-world et open-design.
- **DESIGN.md** (Google, Apache-2.0, alpha) devient le point de convergence : impeccable l'écrit, hallmark le lit comme système verrouillé, open-design et awesome-design-md le consomment [A1][A11][A17][A19]. Il lui manque encore les jetons d'animation et les jetons responsive [A16], et il n'exporte pas en `:root` CSS pur [A15].
- L'**accessibilité** est traitée par contraste, focus et mouvement réduit (plancher de hallmark, audit d'impeccable, lint DESIGN.md). La **sobriété** n'est traitée par aucun outil : taste-skill exige même au moins 4 photos et au moins 8 éléments animés [A8].
- Équivalents natifs ou officiels : la skill `frontend-design` d'Anthropic (mise à jour le 2026-09-03), les plugins officiels `playwright`, `chrome-devtools-mcp`, `figma` et `modern-web-guidance` (Google Chrome), l'intégration Chrome de Claude Code et Claude Design (research preview, inclus dans Max) [A20][A21][A22][A23].

## 2. Fiches outils

Tailles mesurées dans les dépôts le 2026-10-24 (frontmatter = nom + description + champs, relu à chaque tour quand la skill est installée ; corps = chargé à l'invocation).

### pbakaus/impeccable
- **Ce que c'est** : une skill unique `/impeccable` à 24 sous-commandes (`init`, `shape`, `critique`, `audit`, `polish`, `harden`, `animate`, `document`, `live`…), complétée par un moteur Rust (binaire téléchargé au premier usage dans `~/.impeccable/bin/`), une CLI `npx impeccable detect`, une extension navigateur et des **hooks** PostToolUse/Stop. Sous Claude Code, ces hooks vont dans `.claude/settings.local.json` [A1]. La skill écrit `PRODUCT.md` et `DESIGN.md`. **Injection** : frontmatter de 896 c (la description a déjà été raccourcie après l'issue #375) et corps SKILL.md de 12 009 c, plus des références chargées à la demande (`reference/document.md` seul pèse 27 844 octets [A5]). Le hook renvoie ses constats au modèle après chaque édition d'UI [A1].
- **Problème résolu** : les « tells » de l'IA (Inter partout, dégradés violets, cartes imbriquées, gris sur couleur) et la qualité générale (longueur de ligne, cibles tactiles, titres sautés) [A1].
- **Preuves** : l'étude de cas Neo Mirai ne contient que des captures avant/après, sans métrique ni témoin [A3]. Un test tiers sur une page générique compte 19 avertissements, détecte des contrastes (4,1:1 et 3,4:1) que taste manque, mais pas les emojis-icônes [A6]. Une mesure externe donne une précision d'activation de 100 % (N=28), mais **0/10 activation** sur une demande de type `document` : le modèle écrit lui-même un DESIGN.md sans ouvrir la référence [A5].
- **Maturité** : 86 k étoiles, 61 contributeurs, 100 commits/90 j, Apache-2.0, créé le 2025-11-16, release `engine-v0.1.17` du 2026-10-23. Dépôt actif et collectif, sans anomalie.
- **Risques** : (1) **chaîne d'approvisionnement** : le binaire exécuté par les hooks n'a pas de contrôle d'intégrité indépendant (sha256 dans la même release) ; issue #813 ouverte, correctif planifié mais pas livré au 2026-10-23 [A4]. (2) Les hooks s'exécutent **même si l'appel du modèle est refusé**, et le premier événement peut télécharger le moteur [A1]. (3) **Télémétrie** activée par défaut (appel à l'API « roll » d'impeccable.style à chaque nouveau design ; anonyme, désactivable par `IMPECCABLE_NO_TELEMETRY=1`) [A1]. (4) Le mode live peut lancer un script `package.json` [A1]. (5) Des références « exigent un travail coûteux non demandé » (#985 ouverte) et le scan statique produit de faux contrastes (#988 ouverte). (6) Conflit avec la règle « pas d'imbrication » : un sous-agent `asset-producer` est fourni.
- **Compatibilité** : Windows pris en charge (`impeccable.cmd`). Plusieurs bugs de hooks PowerShell ont été corrigés en septembre-octobre (#878, #848, #1098, fermés). La skill fonctionne dans 17 harnais, dont Copilot, Codex et Cursor [A1]. **Jinja** : le détecteur ne liste pas `.j2`/`.jinja` (seulement HTML, CSS, JSX, Vue, Svelte, Astro ; extensions configurables), mais `detect http://localhost:8000/...` scanne le DOM rendu, donc n'importe quel template [A2].
- **Équivalent officiel** : `frontend-design` (Anthropic), dont impeccable dit être parti [A1].
- **Verdict : Essayer.** C'est l'outil le plus complet pour **auditer et polir un produit existant**, et le seul à offrir un détecteur déterministe utilisable sur une URL Jinja rendue. À installer sans hooks (`--no-hooks`), avec la télémétrie coupée, tant que #813 reste ouverte.

### Leonxlnx/taste-skill
- **Ce que c'est** : une skill `design-taste-frontend` et des scripts Node 22 (`draw.mjs`, `lint.mjs`, `inspect.mjs`, `assets.mjs`) qui pilotent Chrome ou Edge par le protocole DevTools. La skill tire 3 directions parmi 20, cherche des images libres sur le réseau (Wikimedia, Openverse, Met), inspecte la page à 3 largeurs et fait jusqu'à 3 tours « regarder et corriger » sur ses captures [A9]. **Injection** : frontmatter de 1 015 c (la plus longue des skills mesurées) et corps de 38 458 c.
- **Problème résolu** : pages marketing et landing pages « génériques » ; depuis la v2.1, aussi tableaux de bord et écrans d'app [A9].
- **Preuves** : le test de l'éditeur (5 tours en aveugle, juge LLM, un juré par brief) donne au dernier tour **v2 7,7, sans skill 7,8, autre skill 7,2**. L'éditeur reconnaît environ 0,5 point de bruit et des briefs réutilisés. Les pages v2 ont 0 échec à son propre inspecteur contre 8 à 13 sans skill [A7]. Le test tiers donne 21 FAIL au lint et 16 à l'inspecteur sur la page générique ; taste ignore le texte sur image et ne signale que les contrastes sous 2,6:1 [A6].
- **Coût** : **30 à 45 min et « quelques centaines de milliers de tokens » par page** [A7].
- **Maturité** : 102 k étoiles, 21 contributeurs, 95 commits/90 j, MIT, créé le 2026-02-19, v2.1.4 du 2026-10-20. Sponsors et appli « TasteCode » associée : registre partiellement commercial.
- **Risques** : accès réseau (images), Chrome piloté localement, historique stocké dans `~/.taste-skill/`. Le style maison impose au moins 4 photos et au moins 8 éléments animés (échec sinon) [A8], ce qui va contre la sobriété et ne convient pas à une appli métier.
- **Compatibilité** : neutre vis-à-vis du framework (« HTML/CSS… ») [A9] ; il faut Node 22 et Chrome ou Edge sous Windows. Plugin Claude Code, plugin Codex, `npx skills`.
- **Verdict : Évaluer.** Elle n'a de sens que pour une landing page vitrine, et son propre test ne montre pas de gain sur l'absence de skill, pour un coût élevé en tokens.

### Nutlope/hallmark
- **Ce que c'est** : une skill (v2.0.0) avec 48 thèmes de 8 Ko au plus chacun, des scripts Node (`theme.mjs`, `sloplint.mjs`, `capture.mjs`), 755 photos libres référencées et un **relecteur en contexte neuf (sous-agent)** en fin de construction. Les pages produites sont **en HTML et CSS autonomes** [A10][A11]. **Injection** : frontmatter de 392 c, corps de 18 239 c. La skill pèse environ 1 Mo sur disque (#50 ouverte).
- **Problème résolu** : pages nouvelles « faites, pas générées », plus refonte et audit nommés (`/hallmark redesign|audit`). `sloplint --before/--kept` vérifie qu'aucun lien, champ ou gestionnaire ne disparaît pendant une refonte [A10].
- **Preuves** : une ablation externe (4 briefs, 100 essais, contrôles déterministes) mesure le noir et blanc purs à **100 % sans la skill contre 50 % avec**, avec des intervalles disjoints. En revanche, `transition: all` passe de 35 % à 57 % (non significatif, mais dans le mauvais sens). Les fichiers `anti-patterns.md` et `slop-test.md` **ne sont jamais ouverts**. **12 essais sur 40** s'arrêtent sur la question de contexte (aucune page produite en non interactif), et la skill **ne s'active pas** si on ne la nomme pas [A12][A13]. Cette mesure date du 2026-09-10 ; la v2 a pu changer ces comportements, ce qui reste à vérifier.
- **Maturité** : 31,7 k étoiles, **5 contributeurs**, 100 commits/90 j, MIT, créé le 2026-04-27, aucune release GitHub. Portée par Together AI.
- **Risques** : le relecteur en sous-agent entre en **conflit avec la règle « pas d'imbrication »** dans un sous-agent `dev-story`. Il faut `puppeteer-core` global pour le rendu. Un hook optionnel (`install-hook.mjs`) contrôle le plancher à l'édition. Le dépôt signale des contradictions dans la doc (#62 ouverte).
- **Accessibilité** : c'est la skill qui la traite le plus explicitement. Le **plancher** est non négociable : contraste, `:focus-visible`, repli `prefers-reduced-motion`, contenu visible sans JS, mise en page mobile [A11].
- **Compatibilité** : Claude Code, Codex, Cursor, OpenCode, Copilot via `npx skills` ; Windows non documenté.
- **Verdict : Évaluer.** Le format (HTML/CSS autonome, plancher a11y, contrôle de préservation en refonte) colle à la pile vanilla. L'activation, le blocage en non interactif et le sous-agent imbriqué restent à vérifier avant tout usage en run autonome.

### nextlevelbuilder/ui-ux-pro-max-skill
- **Ce que c'est** : une skill avec une base CSV interrogée par un script Python BM25 (`search.py`) : 79 styles, 192 palettes et règles par secteur, 74 paires de polices, 119 règles UX, 22 piles techniques. Elle génère un « design system » en ASCII ou en Markdown, persistable dans `design-system/<app>/MASTER.md`. Pile **par défaut : HTML + Tailwind** [A14]. **Injection** : frontmatter de 531 c et corps de 15 969 c ; le dépôt contient 7 skills `.claude/skills/` (banner, brand, slides…).
- **Preuves** : un seul avant/après, « illustratif, contribué par la communauté » [A14]. Une issue signale une **régression visuelle** après usage (#446 ouverte), et un commentateur juge les consignes lourdes contre-productives sur les modèles récents [A25]. Dans #484 (fermée), un audit externe trouvait que 82 % des fichiers livrés n'étaient jamais ouverts.
- **Maturité** : 140 k étoiles, 100 contributeurs, MIT, créé le 2025-11-30, v2.15.0 du 2026-08-13. **La publication npm échoue depuis le 18 août** (#457 ouverte). Une version « Premium » payante existe.
- **Risques** : registre marketing, offre premium ; le défaut Tailwind contredit la pile. Les bugs Windows (cp1252, boucle infinie) ont été corrigés en août (#459).
- **Verdict : Écarter.** C'est un catalogue de styles et de palettes plus qu'un contrôle, sans preuve d'effet, centré sur Tailwind, avec une chaîne de publication cassée. Ses règles UX peuvent servir de lecture ponctuelle.

### google-labs-code/design.md
- **Ce que c'est** : une **spécification de format** (YAML de jetons + prose Markdown en 8 sections ordonnées) et une CLI `@google/design.md` qui offre `lint` (11 règles, dont le **contraste WCAG AA** des paires composant), `diff` (régression entre versions), `export` (Tailwind v3/v4, **DTCG**) et `spec` [A15]. Statut **alpha** ; ouvert par Google Labs/Stitch le 2026-04-21 [A18].
- **Problème résolu** : un design system persistant, lisible par l'agent et vérifiable mécaniquement.
- **Adoption** : impeccable (`document` génère DESIGN.md), hallmark (le lit comme système verrouillé, prioritaire), open-design (« contrat de marque »), awesome-design-md (84 fichiers) [A1][A11][A17][A19]. La skill BMAD `bmad-ux` de la session produit aussi un DESIGN.md, mais je n'ai pas vérifié s'il suit le schéma de Google (hors firewall).
- **Limites** : pas de jetons d'animation (#156 ouverte), pas de jetons responsive (#154 ouverte), export DTCG non conforme pour la typographie (#172 ouverte). **Pas d'export en `:root { --… }` CSS pur** : `css-tailwind` émet un bloc `@theme` que seul Tailwind v4 interprète [A15][A16]. Sous Windows/PowerShell, il faut l'alias `designmd` (`npx -p @google/design.md designmd lint`) [A15].
- **Maturité** : 28,5 k étoiles, 26 contributeurs, 7 commits/90 j (rythme lent), Apache-2.0, release 0.4.0 du 2026-07-27.
- **Verdict : Essayer.** C'est le contrat de design le moins coûteux (un fichier relu à la demande) et le standard de fait vers lequel convergent les outils. Pour la pile vanilla, prévoir un petit convertisseur DTCG → variables CSS et épingler la version alpha.

### VoltAgent/awesome-design-md
- **Ce que c'est** : 84 DESIGN.md « extraits » de sites de marques (Stripe, Notion…), avec un `preview.html` par site [A19]. Aucun code, aucune skill.
- **Preuves** : aucune ; une issue signale un DESIGN.md « obviously wrong » (Notion, #421).
- **Maturité** : 123 k étoiles pour **4 contributeurs** et 6 commits/90 j, une anomalie à signaler. Service commercial de « request a DESIGN.md » (getdesign.md).
- **Risques** : pour un consultant, reproduire l'identité visuelle d'une marque tierce pose un problème de propriété intellectuelle et d'imitation. Les sections du dépôt ne suivent pas l'ordre canonique de Google (9 sections « étendues »).
- **Verdict : Évaluer**, seulement comme exemples du format, jamais pour cloner une marque.

### nexu-io/open-design
- **Ce que c'est** : un **espace de travail de design** complet (appli de bureau Windows/macOS, démon, serveur MCP `od mcp install claude`, proxy BYOK, offre cloud payante) qui pilote l'agent CLI installé. Il embarque 151 design systems DESIGN.md et des centaines de SKILL.md de gabarits [A17].
- **Maturité** : 104 k étoiles, 100 contributeurs, **1 281 issues ouvertes**, créé le 2026-04-28, release du 2026-10-22, Apache-2.0. Croissance très rapide et promotion commerciale (« credits doubled »).
- **Risques** : surface d'attaque large (démon, proxy, MCP), verrouillage dans un outil tiers, doublon de Claude Design (natif).
- **Verdict : Hors périmètre.** C'est un produit de prototypage, pas une brique de configuration Claude Code ; Claude Design couvre ce besoin nativement [A22].

### emilkowalski/skills
- **Ce que c'est** : 15 skills en Markdown pur (sans script) : `emil-design-eng` (principale), `animate`, `review-animations`, `improve-animations`, `animation-performance`, `break-ui` (données pires cas), `mobile-native`, `apple-design`, plus des skills propres à React Native, Swift ou Sonner [A26]. **Injection** : 191 c de frontmatter pour la principale ; le total des 15 descriptions n'est pas mesuré. Le corps de `emil-design-eng` fait 27 123 c.
- **Preuves** : expertise d'auteur (Vercel, Linear), aucune mesure.
- **Maturité** : 49 k étoiles, 3 contributeurs, 16 commits/90 j, MIT, sans release.
- **Pile vanilla** : les règles d'animation (courbes, durées, propriétés transform/opacity, mouvement réduit) sont pour l'essentiel en CSS et indépendantes du framework. `animate-expo`, `write-swift` et `ask-sonner` sont hors sujet.
- **Verdict : Essayer, sélectivement** : `review-animations`, `animation-performance`, `break-ui` et `mobile-native` seulement, pour limiter les descriptions relues à chaque tour.

### greensock/gsap-skills
- **Ce que c'est** : 8 skills officielles GSAP (core, timeline, scrolltrigger, plugins, utils, react, performance, frameworks), vanilla JS inclus [A27].
- **Maturité** : 17 k étoiles, 4 contributeurs, **0 commit/90 j**, MIT pour les skills.
- **Risques** : le README demande à l'agent de **recommander GSAP par défaut** [A27], une consigne promotionnelle injectée. La licence GSAP elle-même est la « Standard No Charge » de Webflow, pas une licence libre : elle interdit l'usage dans des outils d'animation visuelle concurrents de Webflow [A28].
- **Verdict : Hors périmètre** tant que la pile n'adopte pas GSAP. Pour la sobriété, préférer les animations CSS natives (View Transitions, `@starting-style`), que couvre `modern-web-guidance` [A23].

### DavidHDev/react-bits
- Composants animés **React** (JS/TS, CSS/Tailwind) installés via la CLI shadcn ou le MCP shadcn ; portages officiels Vue et Svelte, pas de vanilla [A29]. Licence **MIT + Commons Clause** (pas open source au sens OSI), offre Pro payante. 50 k étoiles, créé en 2024-08.
- **Verdict : Écarter** (lié à React, licence restrictive).

### DavidHDev/canvas-ui
- Effets WebGL/WebGPU par-dessus le DOM, via l'API **expérimentale** HTML-in-canvas, avec un build **vanilla** existant mais distribué via la CLI shadcn [A30]. Licence **MIT + Commons Clause** (LICENSE.md lu). 5 k étoiles, 18 contributeurs, créé le 2026-07-16, sans release.
- **Risques** : poids, consommation GPU, accessibilité (contenu redessiné en texture), API non standard.
- **Verdict : Écarter** pour une appli métier.

### oso95/scroll-world
- Skill qui génère une landing page « vol 3D au scroll » à partir de vidéos IA **payantes** : la CLI Monid (Seedance) ou Higgsfield, environ **27 $ pour une chaîne de 6 scènes en 1080p**, plus ffmpeg et Pillow. Le moteur de défilement est en vanilla JS [A31].
- **Maturité** : 10,4 k étoiles pour **1 contributeur et 11 fichiers**, une anomalie à signaler. MIT.
- **Verdict : Écarter** (coût externe, dépendances payantes, pur effet marketing).

## 3. Analyse de catégorie

### Doublons : impeccable, taste-skill, hallmark, ui-ux-pro-max et `frontend-design`
Aucun n'est strictement meilleur. Chacun gagne dans un cas précis :

| Cas | Gagnant | Pourquoi |
|---|---|---|
| Nouvelle page, coût minimal | `frontend-design` (officiel) | 279 c de description, 9,4 k de corps, maintenu par Anthropic (dernière mise à jour 2026-09-03) [A20] ; aucun script ni réseau |
| Audit et polissage d'un produit existant, écran Jinja | impeccable | Détecteur déterministe sur URL rendue, `audit` (a11y, perf, responsive), `harden`, `critique` [A1][A2] |
| Page autonome HTML/CSS avec plancher a11y | hallmark | Plancher (focus, mouvement réduit, contraste), contrôle de préservation en refonte [A10][A11] |
| Landing page vitrine avec photos | taste-skill | Boucle navigateur la plus poussée, mais 30 à 45 min et des centaines de milliers de tokens, sans gain mesuré [A7] |
| — | ui-ux-pro-max | Pas de cas où il gagne clairement pour cette pile |

Ce qu'ils partagent : ils déclarent tous les mêmes « tells » (Inter, dégradé violet, cartes imbriquées). Les comparatifs de blogs sont des tests uniques et informels [A6]. Le DESIGN.md de Google est **complémentaire**, pas concurrent : c'est le contrat que les skills lisent ou écrivent. Attention au **conflit d'écriture** : impeccable, open-design et peut-être `bmad-ux` écrivent tous un DESIGN.md (plus `PRODUCT.md` pour impeccable). Il faut désigner un seul propriétaire du fichier.

### Comment ces outils vérifient le rendu
| Outil | Mécanisme | Déterministe ? |
|---|---|---|
| impeccable | `detect` (62 règles, fichiers ou URL via Chrome/Edge), hook post-édition et Stop, captures de `critique`/`polish`, mode live | Oui (détecteur) + LLM (critique) |
| taste-skill | `lint.mjs` (source), `inspect.mjs` (CDP, 3 largeurs : contraste, débordement, marges, nombre d'éléments animés), 3 tours de critique sur captures | Oui + LLM |
| hallmark | `sloplint --render` (8 largeurs, puppeteer), revue du héros puis revue finale par un sous-agent en contexte neuf | Oui + LLM (sous-agent) |
| ui-ux-pro-max | Checklist « pre-delivery » en texte | Non |
| `frontend-design` | Consignes | Non |
| DESIGN.md CLI | Lint des jetons (références, contraste des paires composant) | Oui, statique |
| Natif Claude Code | `/chrome` (vérification de design, régressions visuelles), plugins officiels `playwright` et `chrome-devtools-mcp` (captures, snapshot d'accessibilité, Lighthouse, traces de performance) [A21][A32] | Outils, la boucle reste à écrire |

**Preuves d'efficacité** : aucune comparaison indépendante et contrôlée des skills. Côté recherche, la boucle « critique VLM sur capture » apporte jusqu'à +17,8 % sur des requêtes WebDev Arena en 3 cycles [A24]. Elle reste coûteuse ; un fine-tuning LoRA n'en récupère qu'environ 25 %. Les classements « Design Arena » (votes humains en paires) comparent des **modèles**, pas des skills, et changent tous les mois [A33].

### Accessibilité, performance, sobriété
- **Contraste** : traité par hallmark, impeccable, design.md (jetons) et taste (seuil bas, 2,6:1, et texte sur image ignoré [A6]). Les outils divergent sur les mêmes paires [A6], et impeccable produit de faux positifs avec les `@media` (#988).
- **Focus et mouvement réduit** : hallmark (plancher), ui-ux-pro-max (checklist), emil et taste (page en mouvement réduit).
- **Accessibilité sémantique** (libellés, alt, rôles) : aucune skill n'intègre axe-core. Une étude CHI EA '26 (lue via un résumé secondaire) relève environ 1,8 violation sémantique par UI générée par Claude Sonnet 4, Gemini 2.5 Flash ou GPT-4o [A34], ce qui confirme que le trou est réel.
- **Performance** : impeccable `audit`/`optimize`, emil `animation-performance`. Côté natif, `chrome-devtools-mcp` (Lighthouse, traces) et `modern-web-guidance` (INP, API natives plutôt que JS lourd) [A23][A32].
- **Sobriété** : **non traitée**. taste-skill et canvas-ui vont à l'inverse (images et animations obligatoires, WebGL).

### État de l'art hors liste
1. **Natif Anthropic** : skill/plugin officiel `frontend-design` [A20][A35] ; intégration Chrome de Claude Code (`/chrome`, beta, Chrome/Edge, pas WSL) [A21] ; **Claude Design** (2026-04-17, research preview, inclus dans Pro/Max) qui construit un design system depuis le code et produit un « handoff bundle » pour Claude Code [A22].
2. **Marketplace officiel** : plugins `playwright` (Microsoft), `chrome-devtools-mcp`, `figma` (serveur MCP officiel : jetons, composants, design vers code), `superdesign`, `modern-web-guidance` (Google Chrome/Edge, preview, guides « token-efficient » élagués par évaluations) [A23][A35]. Pour une pile vanilla, **modern-web-guidance** est probablement le plus utile (API CSS et HTML natives, a11y intégrée). C'est une hypothèse à tester.
3. **Boucle de critique visuelle maison** : Playwright pour piloter, captures à 3 largeurs, critique par le modèle avec une grille, plus `impeccable detect <url>` et un contrôle axe. Les sources recommandent Playwright pour agir et DevTools MCP pour inspecter [A32].

### Problèmes que rien ne traite
- **Templates serveur (Jinja)** : aucune skill ne les comprend comme source ; il faut passer par l'URL rendue.
- **Runs autonomes** : activation non fiable quand la skill n'est pas nommée, questions bloquantes en non interactif (hallmark), sous-agents imbriqués (hallmark, impeccable). Aucune skill n'a de mode « sous-agent de dev » documenté.
- **Cohérence entre stories et agents parallèles** : seul le couple DESIGN.md + lint ou détection de dérive d'impeccable l'aborde.
- **Sobriété et poids de page**, **accessibilité sémantique** (axe), **coût en tokens** : aucun outil ne les mesure, sauf taste qui donne un ordre de grandeur.

### Hypothèses à tester (protocoles courts)
- **H1 : quelle skill pour un écran métier Jinja ?** Tâche de référence : un écran formulaire + tableau dans une appli FastAPI de test. Quatre bras : rien, `frontend-design`, impeccable (sans hook), hallmark. Sous-agent Sonnet, 3 essais par bras, **skill nommée dans le prompt**. Mesures : constats de `impeccable detect <url>`, violations axe (via Playwright), contraste et focus, tokens et coût (`/agent-cost-kit:mesurer-couts`), note humaine en aveugle de 1 à 5. Critère : adopter si on obtient au moins 30 % de violations en moins et une note d'au moins +1 pour au plus +50 % de coût ; sinon garder `frontend-design`.
- **H2 : la boucle native suffit-elle ?** Comparer « `frontend-design` + étape de vérification maison (Playwright 3 largeurs + `impeccable detect` + axe, au plus 2 tours) » avec la meilleure skill de H1. Critère : la boucle native l'emporte si elle atteint au moins 90 % de la qualité de H1 pour un coût moindre.
- **H3 : DESIGN.md réduit-il la dérive ?** Sur 3 stories d'UI successives, avec et sans DESIGN.md lu par le sous-agent, compter les couleurs et tailles codées en dur hors jetons et les écarts de `designmd diff`. Critère : au moins 50 % de valeurs hors jetons en moins.
- **H4 : activation en sous-agent.** Une skill installée se déclenche-t-elle dans un sous-agent `dev-story` sans être nommée ? Ouvre-t-elle ses références ? On compte les appels `Skill` et `Read` dans les transcriptions sur 10 essais. Critère : moins de 8 sur 10, et il faut l'appeler explicitement dans le prompt de story.
- **H5 : modern-web-guidance.** Tâche : une modale animée et un menu déroulant en vanilla, avec et sans la skill. Mesures : octets de JS, usage d'API natives (`<dialog>`, `popover`, `@starting-style`), Lighthouse.

## 4. Affirmations

| ref | affirmation | source (URL) | éditeur | date publi | consultée | confiance | classe |
|---|---|---|---|---|---|---|---|
| A1 | Impeccable : 1 skill, 24 commandes, 62 règles déterministes, hooks Claude Code dans settings.local.json, hooks exécutés même si l'appel du modèle est refusé, télémétrie par défaut (opt-out), dérivé de frontend-design | https://github.com/pbakaus/impeccable | pbakaus (auteur) | README au 2026-10-24 | 2026-10-24 | haute (faits de config) | primaire, éditeur |
| A2 | Le détecteur scanne HTML/CSS/JSX/Vue/Svelte/Astro et des URL rendues ; Jinja non listé ; un scan propre n'est pas une preuve de qualité | https://impeccable.style/docs/detector | impeccable | n.d. | 2026-10-24 | haute | primaire, éditeur |
| A3 | L'étude de cas Neo Mirai ne contient aucune métrique ni témoin | https://impeccable.style/cases/neo-mirai | impeccable | n.d. | 2026-10-24 | haute | primaire, éditeur |
| A4 | Le binaire du moteur n'a pas de vérification d'intégrité indépendante ; correctif planifié, non livré au 2026-10-23 | https://github.com/pbakaus/impeccable/issues/813 | contributeur externe + mainteneur | 2026-09-12 (MAJ oct.) | 2026-10-24 | haute | primaire, issue |
| A5 | Précision d'activation 100 % (N=28) mais 0/10 activations sur un cas « document » ; DESIGN.md écrit 10/10 sans la skill | https://github.com/pbakaus/impeccable/issues/744 | contributeur externe | 2026-09-06 | 2026-10-24 | moyenne (un auteur, version 4.2.x) | primaire, mesure externe |
| A6 | Test sur une page générique : taste 21 FAIL lint et 16 inspect ; impeccable 19 avertissements ; ils divergent sur le contraste (taste ignore le texte sur image, seuil 2,6:1) | https://devtoollab.com/blog/ai-taste-skills | DevToolLab | 2026-10-16 | 2026-10-24 | moyenne (un seul essai) | secondaire, test |
| A7 | Test en aveugle de taste v2 : 7,7 contre 7,8 sans skill, 7,2 pour une autre skill ; 30 à 45 min et « quelques centaines de milliers de tokens » par page | https://github.com/Leonxlnx/taste-skill/blob/main/CHANGELOG.md | Leonxlnx (auteur) | v2.0.0 (2026) | 2026-10-24 | haute (l'éditeur rapporte contre son intérêt) | primaire, éditeur |
| A8 | taste échoue une page avec moins de 4 photos réelles ou moins de 8 éléments en mouvement | https://github.com/Leonxlnx/taste-skill/blob/main/CHANGELOG.md | Leonxlnx | 2026 | 2026-10-24 | haute | primaire, éditeur |
| A9 | taste : 6 étapes, inspection à 3 largeurs, 3 tours de critique, Node 22 et Chrome, réseau pour les images, neutre vis-à-vis du framework | https://github.com/Leonxlnx/taste-skill | Leonxlnx | README au 2026-10-24 | 2026-10-24 | haute | primaire, éditeur |
| A10 | hallmark : 48 thèmes, sloplint à 8 largeurs, relecteur en contexte neuf, pages HTML/CSS autonomes, contrôle de préservation en refonte | https://github.com/Nutlope/hallmark | Nutlope / Together AI | README au 2026-10-24 | 2026-10-24 | haute | primaire, éditeur |
| A11 | Plancher de hallmark : focus-visible, repli reduced-motion, contenu sans JS ; DESIGN.md à la racine prioritaire ; relecteur en sous-agent | https://github.com/Nutlope/hallmark/blob/main/skills/hallmark/SKILL.md | Nutlope | v2.0.0 | 2026-10-24 | haute | primaire, code |
| A12 | Ablation de hallmark : noir et blanc purs 100 % → 50 % ; `transition: all` 35 % → 57 % | https://github.com/Nutlope/hallmark/issues/74 | contributeur externe | 2026-09-10 | 2026-10-24 | moyenne (un auteur, version antérieure à la v2 ?) | primaire, mesure externe |
| A13 | hallmark : références anti-patterns jamais ouvertes ; 12/40 essais bloqués par la question de contexte ; pas d'activation si la skill n'est pas nommée | https://github.com/Nutlope/hallmark/issues/74 | contributeur externe | 2026-09-10 | 2026-10-24 | moyenne | primaire, mesure externe |
| A14 | ui-ux-pro-max : base BM25, HTML + Tailwind par défaut, exemple « illustratif », version premium | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill | nextlevelbuilder | README au 2026-10-24 | 2026-10-24 | haute | primaire, éditeur |
| A15 | DESIGN.md : YAML + prose, 8 sections, lint en 11 règles dont le contraste AA, export Tailwind/DTCG, alias `designmd` sous Windows, statut alpha | https://github.com/google-labs-code/design.md | Google Labs | README au 2026-10-24 | 2026-10-24 | haute | primaire |
| A16 | Pas de jetons d'animation ni responsive ; l'export DTCG de la typographie est non conforme (issues ouvertes) | https://github.com/google-labs-code/design.md/issues | Google Labs (dépôt) | 2026-07/08 | 2026-10-24 | haute | primaire, issues |
| A17 | open-design : appli de bureau, MCP `od mcp install claude`, 151 design systems DESIGN.md, offre cloud | https://github.com/nexu-io/open-design | nexu-io | README au 2026-10-24 | 2026-10-24 | haute | primaire, éditeur |
| A18 | DESIGN.md ouvert le 2026-04-21, Apache-2.0, alpha ; recoupe partiellement DTCG | https://the-decoder.com/googles-open-source-design-md-gives-ai-agents-a-prompt-ready-blueprint-for-brand-consistent-design/ | The Decoder | 2026-04 | 2026-10-24 | moyenne | secondaire, presse |
| A19 | awesome-design-md : 84 DESIGN.md extraits de sites publics, sections étendues, demandes privées payantes | https://github.com/VoltAgent/awesome-design-md | VoltAgent | README au 2026-10-24 | 2026-10-24 | haute | primaire |
| A20 | frontend-design (Anthropic) : dernière mise à jour 2026-09-03 « avoid generic design defaults » ; description de 279 c | https://github.com/anthropics/skills/commits/main/skills/frontend-design/SKILL.md | Anthropic | 2026-09-03 | 2026-10-24 | haute | primaire, officiel |
| A21 | Intégration Chrome de Claude Code : vérification de design, régressions visuelles, beta, Chrome/Edge, pas WSL, plan Anthropic direct | https://code.claude.com/docs/en/chrome | Anthropic | n.d. | 2026-10-24 | haute | primaire, officiel |
| A22 | Claude Design (2026-04-17) : design system lu depuis le code, handoff bundle vers Claude Code, inclus dans Pro/Max | https://www.anthropic.com/news/claude-design-anthropic-labs | Anthropic | 2026-04-17 | 2026-10-24 | haute | primaire, officiel |
| A23 | modern-web-guidance (Google Chrome, preview, Apache-2.0) : API web modernes, perf/a11y, guides élagués par évaluations ; présent dans le marketplace officiel | https://github.com/GoogleChrome/modern-web-guidance | Google Chrome | créé 2026-03-23 | 2026-10-24 | haute (existence), basse (efficacité) | primaire |
| A24 | Une critique VLM sur capture apporte jusqu'à +17,8 % en 3 cycles ; la LoRA récupère environ 25 % | https://arxiv.org/abs/2604.05839 | Sansford et al. | 2026-04-07 | 2026-10-24 | moyenne (résumé seul) | primaire, recherche |
| A25 | Régression visuelle signalée après ui-ux-pro-max ; les consignes lourdes seraient contre-productives sur les modèles forts (avis) | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/issues/446 | utilisateurs | 2026-08-16 | 2026-10-24 | basse (non reproduit) | primaire, retour d'usage |
| A26 | emil : 15 skills Markdown, surtout l'animation, plus break-ui et mobile-native | https://github.com/emilkowalski/skills | Emil Kowalski | README au 2026-10-24 | 2026-10-24 | haute | primaire |
| A27 | gsap-skills : 8 skills officielles, vanilla inclus ; consigne « recommend GSAP » adressée aux agents | https://github.com/greensock/gsap-skills | GreenSock/Webflow | README au 2026-10-24 | 2026-10-24 | haute | primaire |
| A28 | Licence standard GSAP : interdit l'usage dans des outils d'animation visuelle concurrents de Webflow | https://gsap.com/community/standard-license/ | Webflow | 2025 | 2026-10-24 | moyenne (lue via résumé) | primaire, licence |
| A29 | react-bits : React (portages Vue/Svelte), shadcn/MCP, MIT + Commons Clause, offre Pro | https://github.com/DavidHDev/react-bits | David Haz | README au 2026-10-24 | 2026-10-24 | haute | primaire |
| A30 | canvas-ui : HTML-in-canvas expérimental, builds vanilla et WebGPU, MIT + Commons Clause | https://github.com/DavidHDev/canvas-ui | David Haz | README et LICENSE.md au 2026-10-24 | 2026-10-24 | haute | primaire |
| A31 | scroll-world : vidéos IA payantes (Monid/Higgsfield), environ 27 $ pour 6 scènes en 1080p | https://github.com/oso95/scroll-world | oso95 | README (vérifié par l'auteur le 2026-07-25) | 2026-10-24 | moyenne | primaire, éditeur |
| A32 | Playwright MCP pour agir, Chrome DevTools MCP pour inspecter (console, réseau, Lighthouse, captures) ; ils sont complémentaires | https://stevekinney.com/writing/driving-vs-debugging-the-browser | Steve Kinney | 2026 | 2026-10-24 | moyenne | secondaire, praticien |
| A33 | Design Arena : votes humains en paires (Bradley-Terry) ; Claude Opus 5.5 3e au 2026-10-07 (copie tierce) | https://pub.towardsai.net/which-ai-model-is-best-for-web-design-5-picks-for-2026-6b7b5abfb937 | Towards AI | 2026-10 | 2026-10-24 | basse | secondaire, agrégateur |
| A34 | Environ 1,8 violation sémantique d'accessibilité par UI générée (300 UI, 3 modèles, CHI EA '26) | https://a11y-paradise.onrender.com/reviews/69e8d16a891b0e7c69dbcfff | résumé d'un article de Calò et al. | 2026 | 2026-10-24 | basse (résumé secondaire) | secondaire, recherche |
| A35 | Le marketplace officiel contient frontend-design, playwright, chrome-devtools-mcp, figma, superdesign, modern-web-guidance ; aucun des outils de la liste n'y figure | https://github.com/anthropics/claude-plugins-official/blob/main/.claude-plugin/marketplace.json | Anthropic | au 2026-10-24 | 2026-10-24 | haute | primaire, officiel |

## 5. Pistes non suivies et recherches infructueuses
- **Retours Reddit/HN après usage** sur impeccable, taste ou hallmark : non trouvés (la recherche ne renvoie que des annuaires et des blogs promotionnels). À relancer avec `site:reddit.com r/ClaudeCode`.
- **Réécriture de `frontend-design`** (DEV.to, « contredit l'ancienne version ») : non lue. L'historique confirme deux mises à jour (2026-06-09, 2026-09-03) ; le contenu des changements n'a pas été comparé.
- **Évaluation formelle de hallmark** (« generation tests v0.5.0 ») : citée par un agrégateur, non trouvée dans le dépôt.
- **Reprise des mesures d'impeccable 4.5.2** (#744, deuxième série, 120 essais par mode sous `claude-haiku-4-5`) : le détail des deltas n'a pas été lu.
- **Plugin Figma officiel** : prérequis (siège Dev payant pour le serveur desktop) vus seulement via un blog ; à vérifier dans la doc Figma.
- **Format DESIGN.md de `bmad-ux`** : à comparer au schéma de Google (hors firewall de ce run).
- **ReLook, MM-WebAgent, VisRefiner** (critique visuelle, arXiv 2025-2026) : seuls les titres ont été vus.
- **Superdesign** (plugin officiel du marketplace) : non examiné.
