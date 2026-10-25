# T7 : skill de design, boucle de vérification et navigateur pour un front FastAPI + Jinja2 vanilla

Test du 2026-10-24. Protocole d'origine : hypothèses H1 et H2 de `digests/design-front-r1.md` (section 3) et H1 de `digests/tests-verification-r1.md` (section 3.6). Volet A conclu le 2026-10-25 par la note à l'aveugle d'Anaël (section 3, « Note à l'aveugle ») : **garder `frontend-design`, écarter impeccable et hallmark**.

## 1. Résumé

- **Volet A (design).** Aucune des trois skills ne réduit les défauts mesurables : axe-core trouve **0 violation sur les 16 pages** (aucune skill, `frontend-design`, impeccable, hallmark), et `impeccable detect` en trouve **plus** avec une skill (0 sur 4 sans skill, 2 sur 4 avec `frontend-design`, 4 sur 4 avec impeccable, 3 sur 4 avec hallmark), presque toujours la règle « palette crème ». Le critère « au moins 30 % de violations en moins » n'est donc atteint par aucun bras. Surcoût mesuré sur 4 essais par bras : `frontend-design` +1 % (0,317 $ contre 0,314 $), impeccable +16 %, hallmark +21 %. **Décision : garder `frontend-design`.** La note à l'aveugle d'Anaël le place en tête (4,17 sur 5, contre 4,00 sans skill, 3,67 pour impeccable et 3,50 pour hallmark) : aucune autre skill n'atteint le +1 point requis.
- **Volet B (navigateur).** Les trois outils réussissent le parcours de 7 étapes (17 réussites sur 18 exécutions ; l'échec est un refus de permission, pas une erreur de l'outil). Coût d'un parcours : 0,08 à 0,12 $, 20 à 30 s. **Décision proposée : Playwright MCP** si on applique le critère à la lettre (seul le moins cher des outils qui réussissent à chaque fois avec la liste d'autorisations stricte), mais l'écart avec agent-browser (0,087 $ contre 0,088 $ avec la liste élargie) est dans le bruit.
- **Le contrôle fonctionnel dans un vrai navigateur** est le seul des contrôles automatiques qui ait relevé un écart sur les 16 pages (hallmark, 3e essai : le message de confirmation, porté par `?ok=1`, réapparaît après rechargement alors que l'énoncé demandait un message à usage unique ; mon énoncé citait pourtant le paramètre de requête comme exemple possible, donc l'écart est en partie le mien). Les tests pytest de l'agent disaient couvrir ce point (via `?ok=1`) et passaient.

## 2. Versions installées et contrôles de sécurité

Tout est installé dans le projet jetable `scratchpad\t7\` (`vendor\`, `tools\`, `arms\`), jamais dans `~/.claude` ni dans un dépôt d'Anaël. Aucun hook installé (ni `impeccable install`, ni `install-hook.mjs` de hallmark, ni `playwright-cli install`). Les skills sont copiées à la main dans `.claude/skills/` de chaque répertoire de bras ; les sessions `claude -p` tournent avec `--setting-sources project,local` (ni plugins ni CLAUDE.md d'Anaël).

| Élément | Version épinglée | Ce qui a été lu | SkillSpector 2.12.0 `--no-llm` | Verdict après lecture |
|---|---|---|---|---|
| SkillSpector | v2.12.0, commit `d7338f58`, `uv tool install git+…@sha` avec `UV_TOOL_DIR` dans le scratchpad | README | sans objet | `--output` n'est pas géré sous Windows : sortie JSON redirigée |
| `frontend-design` | anthropics/skills, commit `dbd4588f` | SKILL.md en entier (9,4 k), LICENSE ; aucun script ni hook | 13/100, LOW, SAFE (1 HIGH) | Faux positif : « Errors don't apologize » lu comme une consigne anti-refus |
| impeccable | 4.7.1, commit `93686754` (dossier `plugin/skills/impeccable`, sans `agents/` ni hooks) ; moteur `engine-v0.1.17` | SKILL.md en entier, lanceurs `impeccable` (sh) et `.cmd`, cli.js, `hooks.md` (par grep), chaînes du binaire | 100/100, CRITICAL, DO_NOT_INSTALL (41 constats, 7 fichiers inspectés partiellement) | Tout trié à la main : motifs de texte (« without approval », « no consent »), `live-browser.js` (fetch vers localhost, mode live seulement), mentions de `~/.claude/settings.json` dans la doc des hooks, `npx impeccable` non épinglé dans `doctor.md`. Rien d'exécuté hors mode live. |
| Moteur d'impeccable (binaire Windows) | 0.1.17 | sha256 comparé au fichier `.sha256` de la release et au condensat de l'API GitHub : identiques ; `gh attestation verify` : **aucune attestation** (404) ; pas de `cargo`, donc pas de build depuis les sources ; chaînes : `impeccable.style/api/roll`, GitHub (mise à jour), `fonts.googleapis.com` | non scannable (binaire) | **Risque résiduel accepté** : binaire non vérifiable de façon indépendante. Variables posées : `IMPECCABLE_NO_TELEMETRY=1`, `IMPECCABLE_NO_UPDATE_CHECK=1`, `IMPECCABLE_NO_STALENESS_CHECK=1`, `IMPECCABLE_HOME` dans le projet ; binaire placé à côté du lanceur pour éviter tout téléchargement. `~/.impeccable` n'existe pas. |
| hallmark | 2.0.0, commit `7ec82686` | SKILL.md en entier ; recherche par grep de tout appel réseau ou exécution dans les 10 scripts `.mjs` | 100/100, CRITICAL, DO_NOT_INSTALL (27 constats) | Tout trié : constats d'« évasion » = gros fichiers analysés en partie, « keyring » = étiquette d'une photo, `169.254.169.254` = liste de blocage dans la doc. Seul appel réseau : `imagegen.mjs` vers api.together.xyz, qui exige `TOGETHER_API_KEY` (absente, jamais lancé). |
| puppeteer-core (pour hallmark) | 25.11.0, `--ignore-scripts` | n/a | n/a | `HALLMARK_PUPPETEER` pointe sur `tools\puppeteer` |
| `@playwright/cli` | 0.1.22 | SKILL.md, README, package.json | 45/100, MEDIUM, CAUTION | Texte de doc (`npx playwright`, exemples) ; provenance npm vérifiée (`npm audit signatures`) |
| `@playwright/mcp` | 0.0.83 | package.json, README, options de `cli.js` | 58/100, HIGH | Tout dans le README (`~/.codex/config.toml`, `npx`) ; provenance npm vérifiée |
| agent-browser | 0.39.0 (`--ignore-scripts` : le `postinstall` télécharge un binaire, ignoré car le `.exe` est dans le paquet) | skill-stub, `skill-data/core`, `trust-boundaries.md`, postinstall.js, chaînes du binaire | 100/100, CRITICAL | Faux positifs de doc (`trust-boundaries.md` cite « ignore previous instructions » comme exemple à refuser). Provenance npm vérifiée ; sha256 du `.exe` = condensat de la release GitHub ; aucune adresse de télémétrie (seul `registry.npmjs.org` pour `upgrade`). |
| Chromium | Playwright Python 1.64.1, build 1248, dans `tools\browsers` | n/a | n/a | Même binaire pour les trois outils navigateur |
| axe-core | 4.13.0 (npm, `--ignore-scripts`) | n/a | n/a | Injecté par Playwright Python |
| Claude Code | 2.1.310, modèle `claude-sonnet-5-5`, effort `medium` | n/a | n/a | n/a |

Constat sur SkillSpector : en `--no-llm`, il classe CRITICAL ou HIGH les trois dépôts réputés sains (score 100 pour impeccable, hallmark et agent-browser) et SAFE la seule skill d'une page. Il ne remplace pas la lecture ; il sert de filtre à relire. Le moteur d'impeccable reste le seul composant exécuté qui n'a ni scan ni attestation.

**Effets de bord hors projet à signaler** : agent-browser écrit son état de session dans `~/.agent-browser` (12 Ko, 8 fichiers `.config`, `.target`, `.engine`) et laisse un démon par session ; supprimés à la fin du test, comme les dossiers vides `~/.claude/projects/*scratchpad-t7*` (créés par Claude Code pour chaque répertoire de travail).

## 3. Volet A : design

### Protocole
- **Application** : `scratchpad\t7\base\` (FastAPI 0.162, Jinja2 3.1.6, uvicorn 0.54, pytest 9.1) avec une page `/demandes` qui n'affiche qu'une liste brute.
- **Tâche identique pour tous les bras** (`scripts/tache.md`) : un écran « Demandes d'achat » avec formulaire de saisie (4 champs), validation côté serveur (HTTP 422, bandeau d'erreur, messages par champ liés par `aria-describedby`), message de confirmation à usage unique, tableau filtrable en JavaScript vanilla (recherche sans accents et filtre par service combinés, compteur, message « aucune demande »). Libellés et messages imposés mot pour mot : un script Playwright vérifie 30 points du contrat sur chaque page.
- **Bras** : (b1) aucune skill ; (b2) `frontend-design` ; (b3) impeccable sans hooks ; (b4) hallmark. La skill est **nommée dans le prompt** (« charge et applique d'abord la skill `X` (outil Skill) »), installée au niveau du projet.
- **Exécution** : `claude -p` Sonnet 5.5, effort `medium`, `--permission-mode acceptEdits --permission-prompts none`, `--tools Read,Write,Edit,Glob,Grep,Bash,Skill`, `--allowedTools` limité à Read/Write/Edit/Glob/Grep/Skill et à `Bash(uv run *)`, `Bash(node *)`, `Bash(*impeccable*)`, `Bash(ls *)`, `Bash(cat *)`, `--max-budget-usd 6`, jamais `--dangerously-skip-permissions`. Pas de démarrage de serveur permis par la consigne. Format `stream-json --verbose` à la place de `json` : le dernier évènement est le même objet, et le flux donne en plus les appels d'outils. 2 sessions au plus en même temps.
- **Répétitions** : 2 par bras pour la note à l'aveugle (les 8 rendus de `notation.html`) **plus 2 répétitions supplémentaires par bras (16 au total) pour les mesures automatiques seulement**, car chaque exécution coûte environ 0,35 $.
- **Mesures sur la page rendue** (serveur uvicorn local, Playwright Python sur Edge 155) : axe-core 4.13 (390, 768 et 1280 px, plus l'état d'erreur à 1280 px), `impeccable detect --json --no-config <url>`, contraste calculé par script (ratio minimal, nombre de textes sous 4,5:1 ou 3:1 pour le grand texte), focus visible (différence de capture avant et après `focus()` sur chacun des 7 éléments focalisables), débordement horizontal à 390 px, cibles tactiles, poids en octets (HTML, CSS, JS, requêtes externes), captures à 390, 768 et 1280 px.

### Résultats (moyennes sur 4 essais ; entre parenthèses, les 2 essais notés)
| | b1 aucune | b2 `frontend-design` | b3 impeccable | b4 hallmark |
|---|---|---|---|---|
| Coût (USD) | 0,314 (0,362) | 0,317 (0,316) | 0,365 (0,361) | 0,381 (0,389) |
| Écart à `frontend-design` | −1 % | référence | +15 % | +20 % |
| Fourchette de coût | 0,26 à 0,43 | 0,30 à 0,33 | 0,29 à 0,44 | 0,34 à 0,43 |
| Durée moyenne | 95 s | 95 s | 109 s | 108 s |
| Tours | 13,8 | 14,8 | 17,0 | 20,8 |
| Tokens de sortie | 16,7 k | 16,9 k | 18,2 k | 16,3 k |
| Tokens d'entrée (cache compris) | 221 k | 146 k | 276 k | 474 k |
| Skill invoquée | 0/4 | 4/4 | 4/4 | 4/4 |
| Références de la skill ouvertes (au moins) | n/a | 0 | `craft-floor.md` seul | 0 à 2 fichiers |
| Refus de permission par exécution | 1,3 | 1,5 | 1,5 | 2,0 |
| **Contrat fonctionnel (30 points)** | 4/4 complets | 4/4 | 4/4 | 3/4 (un point raté) |
| **Violations axe-core** | 0 | 0 | 0 | 0 |
| **`impeccable detect`** (pages avec au moins un constat) | 0/4 | 2/4 (`border-accent-on-rounded`, `side-tab`) | 4/4 (`cream-palette`) | 3/4 (`cream-palette`) |
| Contraste, ratio minimal | 5,8 à 6,2 | 5,6 à 6,6 | 5,5 à 7,6 | 6,0 à 6,3 |
| Textes sous le seuil de contraste | 0 | 0 | 0 | 0 |
| Éléments sans focus visible | 0/7 | 0/7 | 0/7 | 0/7 |
| Débordement horizontal à 390 px | non | non | non | non |
| Cibles tactiles de moins de 44 px à 390 px | 0 | 0 | 0 | 0 |
| `prefers-reduced-motion` présent | 0/4 | 4/4 | 4/4 | 4/4 |
| Variables CSS déclarées | 9 | 12 | 13 | 37 |
| Poids de page : CSS (octets) | 3 011 | 4 305 | 4 939 | 6 925 |
| Poids de page : total (octets) | 9 015 | 10 797 | 11 621 | 13 626 |
| Requêtes externes | 0 | 0 | 0 | 0 |

Données par exécution : `donnees/design_runs.json`, `donnees/design_resume.json`, `donnees/mesures_pages/`.

### Lecture
1. **Les défauts mesurables sont saturés à zéro.** Sonnet écrit déjà un écran accessible sans skill (labels liés, rôles `alert` et `status`, focus visible, contraste supérieur à 5,4:1). Le critère « 30 % de violations en moins » est sans objet, faute de violations à réduire. Le seul écart visible va **dans le mauvais sens** : les skills ajoutent des « tells » que le détecteur d'impeccable lui-même repère, en premier lieu la palette crème, y compris quand c'est impeccable qui construit la page (4 pages sur 4). Le détecteur annonce des faux positifs connus (#988) ; ce chiffre mesure l'accord avec ses règles, pas la qualité réelle.
2. **Les skills changent le style, pas la robustesse** : plus de variables CSS (hallmark 37 contre 9), un mouvement réduit prévu, un peu plus de CSS (+130 % pour hallmark, +64 % pour impeccable, +43 % pour `frontend-design`, de 1,3 à 3,9 ko). Cela relève de ta note à l'aveugle.
3. **Le coût suit le nombre de tours, pas la longueur du code.** `frontend-design` (un seul appel de skill, 9 k) coûte comme l'absence de skill. Impeccable (`context`, `craft-floor.md`) et surtout hallmark (thèmes, lint) ajoutent 3 à 7 tours et font passer les tokens d'entrée (cache compris) à 1,3 et 2,1 fois ceux de l'absence de skill. Les fourchettes de coût se chevauchent largement dans chaque bras (de 0,26 à 0,43 $ sans skill) : seul l'écart de hallmark (+20 %) dépasse un peu le bruit.
4. **Les skills sont appelées, mais leurs références presque jamais ouvertes** : 12 appels `Skill` sur 12 quand elle est nommée (cohérent avec la veille), mais impeccable n'ouvre que `craft-floor.md` et hallmark 0 à 2 fichiers (borne basse : les commandes relatives dans Bash ne sont pas toutes repérables). Ni `PRODUCT.md` ni `DESIGN.md` n'ont été produits par impeccable (0 sur 4), et hallmark n'a créé `.hallmark/` qu'une fois sur 4 : en non interactif, les deux ont fait une version allégée de leur flux, sans bloquer (aucune question dans la réponse finale des 8 exécutions, contrairement aux 12/40 arrêts mesurés par la veille sur hallmark).
5. **Un écart, vu seulement par le navigateur** : hallmark, 3e essai, le message « Demande enregistrée. » reste affiché après rechargement (point `confirmation_unique` du contrat) parce qu'il dépend d'un paramètre `?ok=1` laissé dans l'URL. Les tests pytest de l'agent (5 tests, dont un « message à usage unique ») passaient : un client de test sans navigateur ne voit pas un rechargement. Le bras b1 (4e essai) utilise aussi `?ok=` mais l'efface côté navigateur et passe.

### Critère de la veille
| Skill | Violations en moins (≥ 30 %) | Surcoût (≤ +50 %) | Note (≥ +1) | Conclusion |
|---|---|---|---|---|
| `frontend-design` (contre aucune skill) | non applicable (0 contre 0 ; detect : 2 contre 0) | +1 % | +0,17 (4,17 contre 4,00) | garder, par défaut (coût nul) |
| impeccable (contre `frontend-design`) | non (4 contre 2 constats detect, 0 contre 0 axe) | +15 % | −0,50 (3,67 contre 4,17) | écarter |
| hallmark (contre `frontend-design`) | non (3 contre 2 ; 0 contre 0 axe) | +20 % | −0,67 (3,50 contre 4,17) | écarter |

**Décision** : garder `frontend-design` ; impeccable et hallmark sont écartés (note inférieure, coût supérieur, aucune violation en moins).

### Note à l'aveugle
`notation.html` (autonome, 5 Mo, captures en base64) présente les 8 rendus (2 par bras) sous les lettres A à H, tirées au hasard par `secrets` ; cinq captures par rendu (1280, 768 et 390 px à l'état initial, et 1280 et 390 px après un envoi invalide) ; trois grilles de 1 à 5 (lisibilité, finition, cohérence), un commentaire facultatif, sauvegarde automatique dans le navigateur et export JSON. La table de correspondance est dans `correspondance.json`, non référencée par la page. Pour dépouiller : `uv run --no-project python scripts/notes.py` (croise `donnees/notes-anael.json` avec `correspondance.json`, écrit `donnees/notes_resume.json`). (J'ai regardé deux captures pour contrôler le rendu des pages, sans noter.)

**Résultat (export d'Anaël du 2026-10-25, 8 rendus, notes de 1 à 5)** :

| Bras | lisibilité | finition | cohérence | moyenne | coût par essai |
|---|---|---|---|---|---|
| b1 aucune skill | 4,00 | 3,00 | **5,00** | 4,00 | 0,314 $ |
| b2 `frontend-design` | **4,00** | **4,00** | 4,50 | **4,17** | 0,317 $ |
| b3 impeccable | 3,50 | 3,50 | 4,00 | 3,67 | 0,365 $ |
| b4 hallmark | 3,00 | 3,00 | 4,50 | 3,50 | 0,381 $ |

Lecture :
1. **`frontend-design` est le style préféré** : Anaël trouve le rendu B « probablement le style le plus "joli"/"travaillé" ». Il apprécie le tableau aux lignes alternées, les noms des demandeurs en gras et le bouton « Nouvelle demande » mis en avant. Son seul défaut récurrent est le contour coloré du bloc « Le formulaire contient 4 erreurs », vert en B et bleu en G. `impeccable detect` avait relevé ce défaut sur G (`border-accent-on-rounded`), mais pas sur B. L'écart avec l'absence de skill (+0,17) reste sous le point, pour 1 % de coût en plus : on garde la skill parce qu'elle ne coûte rien, pas parce qu'elle gagne.
2. **Sans skill, le rendu est sobre et cohérent** (5 sur 5 en cohérence), avec le meilleur placement des erreurs, mais « un peu trop sobre ».
3. **impeccable et hallmark sont tous deux en dessous de l'absence de skill** (−0,33 et −0,50), pour 15 à 20 % de coût en plus. Le rendu A (hallmark) est « peu de mise en évidence des actions », et le rendu E (hallmark) est « le cul entre deux chaises ». Le critère « +1 point » n'est atteint par aucun : impeccable et hallmark sont écartés.
4. Limite : 2 rendus par bras sur un seul écran. Les deux rendus d'un même bras ont des notes proches (écart de 0,33 au plus).

## 4. Boucle de vérification (H2, partiel)

La comparaison complète « `frontend-design` + boucle maison contre la meilleure skill » n'a pas été jouée : sans défaut à corriger sur ces pages, la boucle n'avait rien à améliorer, et le critère de 90 % de qualité n'est pas mesurable. Ce que le test établit :
- **axe-core, contraste, focus et débordement** : 0 anomalie sur 16 pages. Pour cet écran simple, l'intérêt est un filet de sécurité, pas un correcteur.
- **Contrôle du contrat fonctionnel dans un navigateur** : 1 défaut réel sur 16 pages, hors de portée de pytest. C'est le meilleur rendement de la boucle.
- **`impeccable detect <url>`** : signale surtout des tells esthétiques (palette crème, bordure d'accent sur élément arrondi) ; il tourne en 5 s sans modèle.
- **Coût d'un parcours de vérification** : 0,08 à 0,12 $ (section 5), soit environ 25 à 30 % du coût d'une exécution de développement de cet écran (0,31 à 0,38 $).

Proposition (à valider par Anaël) : dans la chaîne agent-cost-kit, ajouter à la revue d'une story front un parcours navigateur des critères d'acceptation (outil de la section 5), et lancer axe-core et `detect` en CI de branche plutôt qu'en boucle de l'agent.

## 5. Volet B : navigateur pour vérifier une story

### Protocole
- **Page testée** : celle du bras (b1) 1er essai (30 points du contrat sur 30), figée dans `parcours\ref_app\`. Un serveur neuf (état en mémoire réinitialisé) pour chaque exécution, arrêté ensuite.
- **Parcours (7 étapes)** : ouvrir ; remplir le formulaire avec une erreur (montant « -50 ») ; constater le message ; corriger (« 150,75 ») ; valider ; filtrer sur « Finance » ; vérifier le résultat. L'agent répond par un JSON (`scripts/lancer_parcours.py`).
- **Réussite** (contrôle automatique) : JSON valide, 7 étapes à vrai, texte exact du message d'erreur, texte de confirmation, compteur « 2 demandes affichées », 2 lignes visibles dont « Test Parcours », **et** état du serveur (7 lignes, une seule demande « Test Parcours », montant 150,75).
- **Un seul outil par exécution** (`claude -p` Sonnet, effort `medium`, `--setting-sources project,local`, `--strict-mcp-config`) : `playwright-cli` 0.1.22 avec sa skill installée dans le projet (Bash, Read, Skill ; `Bash(playwright-cli *)`) ; agent-browser 0.39.0 avec sa skill (idem, `Bash(agent-browser *)`) ; Playwright MCP 0.0.83 (`--headless --isolated`, outils `mcp__playwright`, Read seul). Même Chromium 1248 pour les trois, headless.
- **Deux séries de 3 exécutions par outil (18 au total)** : « stricte » (liste d'autorisations limitée à l'outil, comme prévu) et « élargie » (ajout de `export`, `sed`, `grep`, `head`, `tail`, `echo`, `wc` pour les deux CLI, parce qu'un refus de `export` a fait échouer une exécution stricte d'agent-browser). Le brief demandait 2 répétitions ; la 3e est un ajout.
- **Claude in Chrome** : non testé, comme demandé. Il n'est pas pilotable en headless : il commande la fenêtre visible du Chrome ou de l'Edge d'Anaël, avec ses sessions ouvertes. À réserver à la vérification manuelle en session interactive.

### Résultats
| Outil | Série | Réussites | Coût moyen (USD) | Durée | Tours | Appels d'outil | Refus de permission |
|---|---|---|---|---|---|---|---|
| Playwright MCP | stricte | 3/3 | 0,095 | 21 s | 13,0 | 12,0 | 0 |
| Playwright MCP | élargie | 3/3 | 0,087 | 23 s | 13,3 | 12,3 | 0 |
| playwright-cli | stricte | 3/3 | 0,111 | 31 s | 9,7 | 7,7 | 1 |
| playwright-cli | élargie | 3/3 | 0,104 | 28 s | 9,0 | 7,0 | 0 |
| agent-browser | stricte | **2/3** | 0,077 | 20 s | 8,0 | 6,7 | 3 |
| agent-browser | élargie | 3/3 | 0,088 | 22 s | 9,3 | 7,3 | 0 |
| **Total par outil (6)** | | MCP 6/6 · CLI 6/6 · agent-browser 5/6 | **0,091 · 0,108 · 0,082** | 22 s · 30 s · 21 s | | | |

Tokens d'entrée (cache compris) : MCP 194 k, playwright-cli 161 k, agent-browser 126 k en moyenne ; tokens de sortie : environ 1,2 à 1,5 k. Données : `donnees/parcours_runs.json`, `donnees/parcours_resume.json`, `donnees/parcours/`.

### Lecture
- **L'échec d'agent-browser (stricte, 2e essai) est un refus de permission**, pas une erreur de l'outil : la skill recommande `export AGENT_BROWSER_SESSION=…`, que la liste `Bash(agent-browser *)` n'autorise pas ; sans personne pour approuver, l'agent s'est arrêté à l'étape 2 en le disant sans inventer de résultat. Les deux autres exécutions strictes ont perdu un tour sur une commande enchaînée avec `sed`. **Pour un sous-agent en run autonome, il faut donc autoriser `export` et les filtres usuels** (ou fixer la session par variable d'environnement).
- **Écarts de coût faibles** (0,02 $ par parcours au plus), du même ordre que la dispersion d'un outil (Playwright MCP : 0,082 à 0,117 $, la première exécution payant l'écriture du cache). Le nombre de tours et la façon d'enchaîner les commandes comptent plus que l'outil : les CLI font tenir plusieurs actions dans une commande (8 tours), le MCP appelle un outil par action (13 tours).
- **Critère de la veille** (« le moins cher parmi ceux qui réussissent à chaque fois ») : liste stricte, **Playwright MCP** (0,095 $, 3/3) devant playwright-cli (0,111 $, 3/3) ; agent-browser est écarté (2/3). Liste élargie : agent-browser (0,088 $) et Playwright MCP (0,087 $) sont à égalité, playwright-cli est à 0,104 $.
- **Documentation chargée à l'exécution** : playwright-cli charge sa skill (15 k) dans 6 essais sur 6 ; agent-browser charge sa skill puis `agent-browser skills get core` (38 k) dans 4 essais sur 6 (les 3 de la série élargie et le 2e essai strict) et s'en passe dans les 2 autres ; le MCP n'a besoin d'aucune lecture (schémas chargés directement, aucun `ToolSearch` dans cette configuration). Une part de l'écart de coût vient de ces lectures, et agent-browser est le moins cher quand l'agent ne les fait pas.

**Décision proposée** : retenir **Playwright MCP** pour les sous-agents de vérification de story (aucune commande Bash à autoriser, aucun refus constaté, le moins cher sous la liste stricte, parcours en 22 s), et ne pas garder playwright-cli (+18 % contre MCP sur les 6 essais). agent-browser reste une option si on autorise `export` ; l'argument en sa faveur (audit axe, `diff screenshot`) n'a pas été testé ici.

## 6. Limites
- **Petits effectifs, une seule tâche.** 2 essais par bras pour la note, 4 pour les mesures automatiques, 3 par outil et par série pour le navigateur. Les écarts de coût entre skills (+1 à +21 %) sont du même ordre que la dispersion dans un bras (jusqu'à 0,26 à 0,43 $). Un écran simple, que Sonnet réussit déjà sans aide, ne distingue pas les skills sur l'accessibilité.
- **Le contrat impose les libellés, les messages et `novalidate`**, ce qui réduit la marge de design ; il garantit en revanche que les rendus sont comparables et que le parcours de l'étape B marche sur n'importe lequel.
- **Les skills n'ont pas disposé de leur boucle de vérification** : la consigne interdit de lancer un serveur et aucun navigateur n'est donné. `sloplint --render` de hallmark, les captures d'impeccable et son mode live n'ont pas pu tourner. On mesure leur texte de consignes et leurs scripts statiques, pas leur boucle complète. Aucun hook n'est installé (consigne de sécurité).
- **Refus de permission** (1,3 à 2,0 par exécution de design) : commandes composées (`cd … && python`, `sed`, redirections) refusées, l'agent contourne. Le taux est comparable entre bras, légèrement plus élevé pour hallmark.
- **Format de sortie** : `stream-json` au lieu de `json` (même objet final).
- **Hallmark et impeccable ont tourné en non interactif** : le flux complet (questions, `PRODUCT.md`, `.hallmark/log.json`) n'a pas été suivi. Leur comportement en session interactive peut différer.
- **`impeccable detect`** : une seule largeur, règles déterministes avec faux positifs connus ; il évalue l'accord avec ses propres règles.
- **Mesure de focus** : différence de capture avant et après `focus()` ; un indicateur de focus invisible sur la capture (par exemple dans un état rendu hors écran) ne serait pas vu.
- **Edge** : un essai manuel d'agent-browser avec le chemin d'Edge a renvoyé le snapshot de la page d'accueil d'Edge au lieu de la page ouverte ; avec le Chromium de Playwright, aucun problème. Constat d'un seul essai, non creusé.
- **Coût total du test** : environ 7,2 $ (16 exécutions de design : 5,5 $ ; 18 parcours : 1,7 $), 0,06 $ pour une sonde.

## 7. Décisions (volet A tranché par la note du 2026-10-25)
1. **Design** : garder `frontend-design`. Écarter impeccable et hallmark : la note les place sous l'absence de skill. Ne pas installer les hooks d'impeccable. Son détecteur (`impeccable detect <url>`) reste une option de CI, puisqu'il a vu un des deux défauts de contour relevés par Anaël.
2. **Navigateur** : Playwright MCP pour les sous-agents de vérification de story ; autoriser `export` et les filtres usuels si on retient une CLI.
3. **Boucle** : parcours navigateur des critères d'acceptation dans la revue d'une story front ; axe-core et `impeccable detect <url>` en CI plutôt que dans la boucle de l'agent.
4. **À suivre** : rejouer le volet A sur une page plus complexe (tableau de bord, plusieurs écrans) où la cohérence entre écrans compte, avec un serveur disponible pour la boucle des skills ; tester `modern-web-guidance` (H5) et DESIGN.md (H3), non couverts ici.

## 8. Fichiers
- `notation.html`, `correspondance.json` (ne pas ouvrir avant d'avoir noté).
- `scripts/` : `tache.md` (énoncé du volet A), `preparer_bras.py`, `lancer_claude.py`, `lancer_bras.py`, `mesure_page.py`, `lancer_parcours.py`, `agreger.py`, `generer_notation.py`, `refs_ouvertes.py`, `nettoyer.ps1` (les commandes d'installation sont décrites en section 2).
- `donnees/` : agrégats, une mesure par page et un méta par exécution (coûts, tokens, outils appelés, refus), prompts (`prompts/`).
- `securite/` : six rapports SkillSpector en JSON.
- Les flux bruts `_claude.jsonl` et les captures sont dans `scratchpad\t7\arms\` et `scratchpad\t7\resultats_mesures\` (temporaires).
