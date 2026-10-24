# Tour 2 — trous du premier tour (r1)

Chercheur : dimension `tour2-trous`. Date : 2026-10-24. Budget consommé : 25 appels web sur 25, environ 9 lectures de dépôt sur 20. **Arrêt : budget web épuisé** au tour 2 ; les questions 2, 4 et 5 sont couvertes, la question 1 seulement en partie (Gartner, Forrester, McKinsey ; rien de trouvé chez BCG, Accenture, Capgemini ou Deloitte).

## 1. Résumé

- **Analystes** : Gartner fixe le cadre du marché (Magic Quadrant du 15/09/2025, 14 fournisseurs [A1]) et, en 2026, conseille de **ne pas employer les agents de code pour toutes les tâches** et de viser tout le cycle de vie (exigences, sécurité, revue, tests, SRE, doc) [A3]. Forrester juge le code produit « souvent problématique » [A5]. Le chiffre McKinsey (« jusqu'à 2× plus vite ») date de 2023 et baisse sur les tâches complexes [A6]. Les chiffres d'adoption et de ROI qui circulent viennent surtout des fournisseurs.
- **Propriété intellectuelle** : utilisé avec un abonnement **Max**, Claude Code relève des **Consumer Terms** [A8]. L'indemnisation de propriété intellectuelle d'Anthropic figure dans les **Commercial Terms** (API, Team, Enterprise) et exclut les sorties modifiées ou combinées avec d'autres contenus [A9]. Copilot conditionne la sienne au filtre de code public [A10]. Pour du code livré à un client, l'offre utilisée change donc la couverture.
- **Traçabilité** : la trace `Co-Authored-By` se pose au niveau du commit. Git AI enregistre l'auteur ligne par ligne dans des Git Notes ; il est classé « Assess » par Thoughtworks en avril 2026 et ne voit pas les fusions faites dans l'interface web [A12][A13].
- **AI Act** : un assistant de code est a priori hors du « haut risque ». La bascule possible vient de l'usage de sa télémétrie pour évaluer des salariés ; les dates sont mouvantes à cause de l'Omnibus [A14][A15].
- **Plaintes transverses**, constatées dans au moins deux outils : quotas et facturation opaques (Codex, Copilot, Cursor), questions de l'agent auto-répondues au bout de 60 s (Claude Code et Codex), perte du contrôle fin de la revue (Copilot), démons d'arrière-plan sous Windows (Codex) [A16–A22].
- **Évals de configuration** : `claude plugin eval` (depuis la v2.1.269) compare avec et sans le plugin, sur 3 passes, avec un seuil pour la CI. Il **ne charge ni `CLAUDE.md`, ni les réglages, ni les autres plugins**, et un cas qui donne accès au shell exige WSL2 sous Windows natif [A23–A26]. Évaluer une configuration complète dans le temps reste un trou.

## 2. Fiches outils

> Note de maturité : dans `depots.json`, `commits_90j` et `contributeurs` valent **exactement 100** pour quatre dépôts sur cinq. C'est très probablement un plafond de pagination de l'API, pas une mesure : ces valeurs se lisent « ≥ 100 ».

### firecrawl/firecrawl
- **Ce que c'est** : une API de collecte web (search, scrape, interact, crawl, map, parse, monitor) qui renvoie du Markdown ou du JSON prêt pour un LLM. Elle existe en service hébergé et en auto-hébergement. Côté agent, trois accès : une CLI avec skills (`npx -y firecrawl-cli@latest init --all --browser`), un serveur MCP (`firecrawl-mcp`, `npx`) et un SDK Python, utilisable depuis un projet `uv` [README].
- **Contexte injecté** : les 5 SKILL.md du dépôt (skills « build », pour développer avec l'API) font 2,9 à 8,3 k caractères chacun. Seules les descriptions sont relues à chaque appel, le corps se charge à l'invocation. La taille des skills installées par la CLI n'a pas été mesurée. Le serveur MCP ajoute ses schémas d'outils.
- **Problème résolu** : les pages rendues en JavaScript et les protections anti-robots. Le WebFetch natif convertit la réponse HTML en Markdown, puis la fait résumer par un modèle secondaire selon un prompt ; c'est « lossy by design », avec 100 000 caractères au plus par appel [A28]. La doc ne mentionne aucune exécution de JavaScript ; c'est une inférence, confirmée seulement par des sources de fournisseurs [A29].
- **Preuves** : le chiffre « 96 % du web, P95 de 3,4 s » vient de l'éditeur. Le test « 42 s contre plus de 4 min 30 avec WebFetch » est un test isolé publié sur un blog promotionnel [A29]. Aucune mesure indépendante trouvée.
- **Maturité** : 194 900 étoiles, créé en avril 2024, release v2.11.0 du 19/06/2026, dernier push le jour même, 665 issues ouvertes.
- **Risques** : licence **AGPL-3.0** pour le cœur (SDK sous MIT) ; l'auto-héberger puis l'exposer comme service à un client déclenche l'obligation de publier les sources modifiées. La version cloud a « des fonctions en plus », donc l'auto-hébergement est moins complet. Le README contient une section qui s'adresse directement aux agents (« Are you an AI agent? Fetch this skill to sign up your user ») : c'est un motif d'injection à bloquer. Côté légal, le respect des conditions des sites incombe à l'utilisateur.
- **Compatibilité** : Claude Code sous Windows via `npx` ou le SDK Python ; Antigravity, OpenCode et tout client MCP.
- **Équivalent natif** : WebFetch et WebSearch (200 recherches au plus par session interactive) [A28][A30], ou `curl` en Bash pour obtenir la page brute.
- **Verdict : Essayer**, seulement pour la veille sur des sources rendues en JavaScript, en clé hébergée (pas d'auto-hébergement AGPL), après le test H1.

### apify/apify-mcp-server
- **Ce que c'est** : un serveur MCP, hébergé (`https://mcp.apify.com`, OAuth) ou en stdio (`npx @apify/actors-mcp-server`), qui expose les milliers d'« Actors » de l'Apify Store (scrapers pour Google, réseaux sociaux, Maps, RAG Web Browser, Web Fetch). Outils par défaut : `search-actors`, `fetch-actor-details`, `call-actor`, plus des outils de runs et de stockage injectés automatiquement. Le paramètre `tools=` restreint la liste [README].
- **Contexte injecté** : les schémas d'environ 7 outils par défaut, plus les Actors ajoutés comme outils. `fetch-actor-details` renvoie le README de l'Actor (résumé quand il existe), ce qui peut peser lourd.
- **Problème résolu** : des collectes spécialisées (réseaux sociaux, SERP, Maps) sans écrire de scraper.
- **Preuves** : aucune mesure indépendante cherchée ni trouvée (budget).
- **Maturité** : 12 900 étoiles, licence MIT, release v0.19.3 du 21/10/2026, 52 contributeurs, créé en janvier 2025 ; la version 0.x change vite (sélecteurs `tools=` retirés ou renommés).
- **Risques** : **télémétrie activée par défaut**, avec un identifiant de session transmis et Sentry en stdio ; désactivation par `TELEMETRY_ENABLED=false`. L'outil `report-problem` est servi par défaut **précisément aux clients Anthropic** (Claude.ai, Desktop, Code). Les **paiements agentiques** (x402 en USDC, Skyfire, AGI) permettent à un agent de dépenser de l'argent : à interdire par permission. Les Actors sont écrits par des tiers, et leur sortie est une source d'injection possible. Les conditions d'utilisation des sites collectés (réseaux sociaux) restent à respecter.
- **Équivalent natif** : WebFetch et WebSearch pour le générique ; rien de natif pour les réseaux sociaux ou Maps.
- **Verdict : Évaluer**, seulement si une veille demande des sources sociales ou des SERP structurées ; sinon Firecrawl ou le natif couvrent le besoin.

### public-apis/public-apis
- **Ce que c'est** : une liste de liens Markdown (environ 2 280 lignes de tableau) vers des API gratuites. Ce n'est ni un outil ni un skill. Le README fait **322 000 caractères** et ne doit jamais être chargé dans le contexte. La liste est sponsorisée par APILayer (bloc de liens commerciaux en tête).
- **Utilité** : choisir une API gratuite pour un démonstrateur (météo, géocodage, données ouvertes). Une recherche ciblée (`gh api …contents/README.md | grep`) suffit.
- **Maturité** : 491 800 étoiles, MIT, créé en 2016, sans release, 2 338 issues ouvertes : fraîcheur des liens non garantie.
- **Risques** : liens morts, API tierces sans engagement de service, placement commercial.
- **Verdict : Hors périmètre** de la configuration d'agent ; à mettre en favori comme annuaire.

### every-app/open-seo
- **Ce que c'est** : une alternative open source à Semrush et Ahrefs (mots-clés, positions, backlinks, audit, « AI visibility »), avec serveur MCP, plugin Claude et 39 SKILL.md. Elle exige une clé payante **DataForSEO** ; l'offre hébergée coûte 10 $/mois, et l'éditeur ajoute 28 % sur chaque requête DataForSEO [README].
- **Contexte injecté** : les SKILL.md du plugin font 5,7 à **22,2 k** caractères (`seo-report`). Le plugin est lourd s'il est installé en entier.
- **Maturité** : 24 800 étoiles pour un dépôt créé le 27/02/2026 (huit mois), 20 contributeurs, version v0.1.14 : beaucoup d'étoiles pour l'âge et la taille de l'équipe, une anomalie à noter.
- **Risques** : coût à l'usage, auto-hébergement conseillé sur Cloudflare, données de tiers.
- **Verdict : Hors périmètre**, sauf mission SEO ou référencement d'un contenu client. Intérêt annexe : son dépôt contient des skills `evaluate-skill` et `deslop`, des exemples de pratiques à lire (non lus ici).

### heygen-com/hyperframes
- **Ce que c'est** : un framework qui rend du **HTML, du CSS et des animations repérables dans le temps (GSAP) en MP4 déterministe**, avec Chrome sans interface (Puppeteer) et FFmpeg. Il s'installe en plugin Claude Code (`claude plugin marketplace add heygen-com/hyperframes`) ou en skills (`npx hyperframes skills update`) ; 7 skills sont publiées, dont 4 dans le noyau. Licence **Apache-2.0**, sans frais par rendu, alors que la licence de Remotion n'est que « source-available » [README].
- **Contexte injecté** : SKILL.md du noyau de 4,2 à 7,2 k caractères (`hyperframes` 7,2 k, `hyperframes-cli` 7,1 k, `media-use` 5,1 k, `hyperframes-registry` 4,2 k), soit environ 24 k caractères quand les quatre sont invoquées.
- **Problème résolu** : produire une **vidéo de démo** d'une application (titres, captures, sous-titres) en écrivant du HTML, ce qui correspond à la pile sans framework front.
- **Preuves** : retours de blogs surtout enthousiastes ; un test indépendant aurait mesuré environ 3 min de rendu pour 30 s en 1080p, chiffre tronqué donc non confirmé [A31]. Aucun fil HN ou Reddit trouvé.
- **Maturité** : 71 300 étoiles en sept mois (créé le 10/03/2026, une anomalie), release v0.8.192 publiée le jour même : cadence quotidienne en 0.x, donc API instable.
- **Risques** : Node ≥ 22 et FFmpeg requis ; le README annonce une application native **Mac et Linux**, la CLI sous Windows n'est pas vérifiée (seule l'installation de git-lfs y est documentée pour Windows). Le registre skills.sh peut avoir « des heures de retard » sur `main`.
- **Équivalent natif** : aucun dans Claude Code (pas de rendu vidéo). Remotion est l'alternative la plus proche, en React.
- **Verdict : Essayer** pour les contenus (vidéo de démo), hors configuration permanente : à installer à la demande, après le test H2 sous Windows.

## 3. Analyse de catégorie

### 3.1 Cabinets et analystes : problématiques et chiffres

| Source | Problématiques listées | Chiffres sourcés |
|---|---|---|
| Gartner, Magic Quadrant AI Code Assistants (15/09/2025) | Marché des assistants (14 fournisseurs) ; leaders : GitHub, Amazon, Cognition (Windsurf), GitLab, Google [A1] | Rapport payant ; positions relayées par les fournisseurs eux-mêmes |
| Gartner, communiqué (11/04/2024) | Un ROI centré sur les coûts sous-estime la valeur : flux, rétention, qualité [A2] | 75 % des ingénieurs en entreprise utiliseront un assistant en 2028 (moins de 10 % début 2023) ; 63 % des organisations en pilote ou en déploiement (n = 598, T3 2023) [A2]. **Plus d'un an : à replacer en contexte** |
| Gartner, notes 2026 (résumés) | « Don't Use AI Coding Agents for Every Software Engineering Task » : élargir aux exigences, à la sécurité, à la revue, aux tests, au SRE et à la documentation ; marché des agents de code en entreprise (sept. 2026) : exécution autonome, orchestration du contexte, **gouvernance sur tout le SDLC** [A3] | Aucun (résumés payants, vus via le moteur de recherche seulement) |
| Forrester, prédictions 2026 | Les outils produisent « souvent du code problématique » ; passage du « vibe coding » au « vibe engineering » sur tout le cycle de vie [A5] ; paysage des « Agentic Development Platforms » au T3 2026, distinct des assistants (couverture seule) | Les ROI des études TEI (par ex. 327 %) sont **commandés par les fournisseurs** [A5b] |
| McKinsey, « Unleashing developer productivity with generative AI » (juin 2023) | Gains plus faibles sur les tâches complexes ; lisibilité légèrement meilleure | Tâches de code jusqu'à 2× plus rapides [A6] ; environ 40 développeurs selon une source secondaire. McKinsey Technology Trends 2026, « baisse de productivité dans près de 30 % des entreprises après les agents » : **source de presse non vérifiée** [A7] |
| Anthropic, 2026 Agentic Coding Trends Report (éditeur) | Passage de l'assistant aux équipes d'agents | IA dans environ 60 % du travail, mais **0 à 20 % des tâches entièrement déléguées** [A4], chiffre d'un fournisseur |
| BCG, Accenture, Capgemini, Deloitte | **Rien trouvé ce tour-ci** (2 requêtes) | — |

Ce qui ressort : les analystes déplacent la question de la vitesse de code vers la **gouvernance du SDLC**, le **choix des tâches à déléguer** et la **mesure de la valeur hors coûts**. Les chiffres de productivité de première main sont rares et anciens (McKinsey 2023) ; les chiffres récents viennent des fournisseurs.

### 3.2 Propriété intellectuelle, licences, conformité

| Risque | État des faits | Réponse disponible |
|---|---|---|
| Couverture contractuelle selon l'offre | Claude Code sous Free, Pro ou Max relève des **Consumer Terms** ; sous Team, Enterprise ou API, des **Commercial Terms** [A8]. L'indemnisation (Section K) se trouve dans les Commercial Terms, avec des exclusions : sorties **modifiées**, sorties **combinées** avec des contenus non fournis par Anthropic, usage que le client « devrait savoir » contrefaisant, brevets, marques [A9]. L'absence d'indemnisation dans les Consumer Terms n'a **pas été vérifiée** (texte non lu) | Pour un livrable client : facturer le travail sous une offre commerciale (API ou Team) si le client exige une garantie. En pratique, du code relu, modifié et intégré tombe souvent sous l'exclusion « modifié ou combiné » (inférence) |
| Code sous licence reproduit | Copilot : filtre de « code public » (environ 150 caractères de contexte) et « code referencing » ; l'indemnisation suppose le filtre actif, ou le respect des licences citées en Business et Enterprise [A10]. Le filtre a été critiqué parce qu'il ne détecte que les correspondances exactes (plainte de 2023) [A11] | **Aucun équivalent du filtre de code public trouvé côté Claude Code** (piste non approfondie). Alternative : analyse de composition logicielle avec détection d'extraits en CI (non vérifiée ce tour-ci) |
| Traçabilité du code IA | `Co-Authored-By` : une trace par commit, perdue au squash si le message est réécrit. **Git AI** : les agents (Claude Code, Cursor, Copilot) signalent eux-mêmes leurs blocs ; l'attribution ligne par ligne vit dans des Git Notes, est recopiée au rebase, au squash et au cherry-pick, et s'interroge avec `git ai blame` ou `stats`. Les transcriptions restent hors de git [A12]. Limites : ne prouve ni sécurité, ni licence, ni conformité ; fusions faites dans l'interface web non suivies [A13] | Git AI, à **évaluer** (Thoughtworks Radar : Assess, avril 2026) |
| AI Act | Assistant de code a priori **hors annexe III**. Bascule possible si sa télémétrie alimente un tableau de bord qui évalue des salariés (emploi, annexe III). L'article 50 (transparence) s'applique depuis le 02/08/2026, surtout aux fournisseurs. Un fine-tuning substantiel peut faire requalifier une équipe en fournisseur (article 25) [A14]. Omnibus : échéance du haut risque reportée au 02/12/2027, adoption formelle **non vérifiée** [A15] | Ne pas brancher les métriques d'usage (coûts par développeur, `git ai stats`) sur l'évaluation individuelle chez un client sans analyse juridique |

### 3.3 Plaintes des utilisateurs : transverses ou propres à Claude Code ?

Sources : issues GitHub de `openai/codex`, `anthropics/claude-code` et `microsoft/vscode` (triées par réactions, créées après le 01/06/2026), forum Cursor, blogs qui relaient Reddit.

| Problème | Claude Code | Codex | Copilot | Cursor | Transverse ? |
|---|---|---|---|---|---|
| Quotas et coût par token opaques ou en hausse | (voir les digests du tour 1) | #28879, coût par token × 10 à 20 depuis le 16/06, budget de 5 h vidé en 2 ou 3 prompts (561 réactions, fermée) ; #34035 (279) [A16] | Passage aux **crédits IA facturés au token** le 01/06/2026 [A18] ; Reddit, relayé par des blogs : le mode agent consomme le quota sans qu'on le voie [A19] | Fils 2025 à début 2026 sur les limites du forfait Pro et le manque de transparence [A20], **antérieurs à la fenêtre de fraîcheur** | **Oui** (au moins 3 outils) |
| Question de l'agent répondue d'office au bout de 60 s | #73125 (414 réactions, fermée le 04/07/2026) [A17] | #28969, ouverte (221) [A17] | — | — | **Oui** (2 outils) |
| Perte de la revue fine des changements | — | — | VS Code #339363 : suppression de Keep/Undo par changement (281 réactions, oct. 2026) [A21] | — | Non établi |
| Processus d'arrière-plan et poste local | — | #28224, logs SQLite jusqu'à environ 640 To/an (corrigé) ; #48195, démon auto-démarré ; #48074, fenêtres qui clignotent sous Windows [A22] | — | — | Propre à Codex ici |
| Piste d'audit des multi-agents | — | #28058, messages MultiAgentV2 chiffrés, piste d'audit illisible [A22] | — | — | À surveiller (lien avec la traçabilité) |
| Choix du modèle des sous-agents | — | #31814, sous-agents forcés sur le modèle principal (corrigé) [A22] | — | — | Lien direct avec le routage des coûts |
| Style et instructions ignorés (commentaires verbeux, tics) | #65961 (ouverte), #77136 [A17] | — | — | — | Non établi hors Claude Code |

Conclusion prudente : la **prévisibilité des quotas** est un problème de marché, vu dans au moins trois communautés, pas un défaut propre à Claude Code. Cela renforce l'intérêt d'une mesure locale des coûts, devenue la norme chez Copilot depuis la facturation au token. Les **questions auto-répondues** touchent deux outils : dans un run autonome, elles peuvent faire passer une décision qui revenait à l'humain.

### 3.4 Évaluer sa configuration d'agent dans le temps

| Existant | Ce que ça fait | Limites |
|---|---|---|
| `claude plugin eval` (v2.1.269+, semaine 37 de 2026) | Cas = prompt + graders (`regex`, `tool_used`, `tool_order`, `file_exists` gratuits ; `llm` et `baseline` jugés par un modèle) ; **3 passes par défaut** ; groupe sans plugin et écart `Δ` ; `--threshold` (code de sortie 1 en CI) ; `--model` à épingler « pour qu'une nouvelle version du modèle ne soit pas prise pour une régression » ; `--max-cost-usd` ; `init` rédige les cas ; serveurs MCP simulés et rejouables [A23][A24] | **Isolation** : ni `CLAUDE.md`, ni réglages, ni hooks utilisateur, ni autres plugins, ni mémoire [A25]. Impossible d'évaluer une configuration complète ou l'interaction entre plugins (BMAD + plugin de coûts). Windows natif : pas de bac à sable, donc **WSL2** pour les cas qui ouvrent le shell [A26]. Chaque passe compte dans le quota ; un cas = 6 passes avec la comparaison |
| skill-creator (évals d'une skill dans une conversation) | Format `evals/evals.json`, incompatible avec `plugin eval` [A23] | Deux formats officiels concurrents |
| Skills communautaires (`eval-harness` d'ECC, `eval-harness-kit`) | Définitions, journaux et bases de référence dans `.claude/evals/`, pass@k [A27] | Revue Tessl : contenu noté 57 %, aucun scénario d'éval exécuté [A27] |
| Classements (skills.sh, Skillselion, Tessl) | skills.sh classe par **installations** (plus de 59 000 skills selon un miroir) ; Tessl note la qualité du contenu [A27b] | La popularité n'est pas la qualité ; aucun classement mesure l'effet `Δ` |

**Ce qui manque** : (1) l'évaluation de `CLAUDE.md` et de la configuration complète, puisque l'isolation de `plugin eval` l'exclut ; (2) un suivi longitudinal (historique des scores d'une version de modèle à l'autre) ; (3) le **coût par tâche réussie** comme métrique de premier rang (la colonne COST est une estimation au prix catalogue, pas une mesure sur le forfait) ; (4) un fonctionnement complet sous Windows natif.

### 3.5 Doublons et complémentarités (outils de la fiche)

- **Firecrawl contre Apify MCP** : recouvrement sur le scraping générique. Firecrawl gagne pour le Markdown propre, le crawl d'un site et la surveillance de changements (utile en veille). Apify gagne pour les sources spécialisées (réseaux sociaux, Maps, SERP). Aucun n'est strictement meilleur. Le WebFetch natif suffit pour les pages statiques et coûte zéro clé ; `curl` en Bash donne la page brute.
- **public-apis et open-seo** : sans recouvrement avec les autres ; hors du cœur de la configuration.
- **HyperFrames** : seul de sa catégorie dans la liste (Remotion en dehors).

### 3.6 Hypothèses à tester

- **H1. WebFetch contre Firecrawl pour la veille.** Jeu de référence : 20 URL de veille (pages GitHub, docs rendues en JavaScript, blogs, changelogs). Mesures : faits clés extraits sur une grille de 3 par page, tokens de la session, durée, échecs. Critère : adopter Firecrawl si au moins 20 % de pages exploitables en plus **et** un coût qui reste dans le quota gratuit ou peu cher ; sinon garder WebFetch, plus `curl` au besoin.
- **H2. HyperFrames sous Windows 11.** Tâche : une démo de 30 s d'une application FastAPI (3 captures, titre, sous-titres). Mesures : temps d'installation, temps de rendu, tours et tokens de l'agent, retouches manuelles. Critère : moins d'une heure de bout en bout et aucune retouche bloquante ; sinon passer par WSL2 ou écarter.
- **H3. `plugin eval` sur le plugin de réduction des coûts.** 5 cas (routage vers dev-story, second-avis, reviewer, lookup, mesure des coûts), `--model` épinglé, 3 passes, comparaison activée, sous WSL2 pour les cas qui ouvrent le shell. Mesures : `Δ` par cas, coût de la suite. Critère : `Δ > 0` sur au moins 4 cas sur 5 et une suite à moins de 5 $ au prix catalogue ; ensuite, la rejouer à chaque nouvelle version de modèle.
- **H4. Survie de Git AI à une fusion squash GitHub.** Une PR de 3 commits écrits par l'agent, fusionnée en squash depuis l'interface web. Mesure : part des lignes encore attribuées après fusion. Critère : au moins 90 %, sinon fusionner en ligne de commande ou se contenter de `Co-Authored-By`.

## 4. Affirmations

| ref | affirmation | source (URL) | éditeur | date publi | consultée | confiance | classe |
|---|---|---|---|---|---|---|---|
| A1 | MQ AI Code Assistants publié le 15/09/2025, 14 fournisseurs ; leaders GitHub, Amazon, Cognition, GitLab, Google | https://github.blog/ai-and-ml/github-copilot/gartner-positions-github-as-a-leader-in-the-2025-magic-quadrant-for-ai-code-assistants-for-the-second-year-in-a-row/ ; https://gartner.com/en/documents/6948266 | GitHub (fournisseur) ; Gartner | 2025-09 | 2026-10-24 | moyenne | analyste |
| A2 | 75 % des ingénieurs en entreprise utiliseront un assistant en 2028 ; 63 % des organisations en pilote ou en déploiement ; un ROI centré sur les coûts sous-estime la valeur | https://www.gartner.com/en/newsroom/press-releases/2024-04-11-gartner-says-75-percent-of-enterprise-software-engineers-will-use-ai-code-assistants-by-2028 | Gartner | 2024-04-11 | 2026-10-24 | haute (mais ancienne) | analyste |
| A3 | Note Gartner 2026 « Don't Use AI Coding Agents for Every Software Engineering Task » ; marché des agents de code en entreprise : gouvernance sur tout le SDLC | https://www.gartner.com/en/documents/7721957 (et résumés voisins, 403 à la lecture directe) | Gartner | 2026-06 / 2026-09 | 2026-10-24 | basse (vu via un moteur de recherche seulement) | analyste |
| A4 | IA dans environ 60 % du travail, 0 à 20 % des tâches entièrement déléguées | https://resources.anthropic.com/ty-2026-agentic-coding-trends-report | Anthropic (fournisseur) | 2026 | 2026-10-24 | moyenne | fournisseur |
| A5 | Forrester 2026 : outils produisant souvent du code problématique ; « vibe engineering » | https://sdtimes.com/softwaredev/forrester-shares-its-predictions-for-how-ai-will-continue-to-shape-software-development-in-2026/ | SD Times (relaie Forrester) | 2025-10 | 2026-10-24 | moyenne | analyste (presse) |
| A5b | Études TEI de Forrester avec des ROI de plus de 300 %, commandées par les fournisseurs | https://agentmarketcap.ai/blog/2026/04/05/376-percent-enterprise-roi-coding-agents-developer-productivity | blog | 2026-04 | 2026-10-24 | basse | presse |
| A6 | McKinsey 2023 : tâches de code jusqu'à 2× plus rapides, moins sur les tâches complexes | https://mckinsey.com/~/media/mckinsey/business%20functions/mckinsey%20digital/our%20insights/unleashing%20developer%20productivity%20with%20generative%20ai/unleashing-developer-productivity-with-generative-ai.pdf | McKinsey | 2023-06 | 2026-10-24 | moyenne (résumé de recherche, PDF non lu en entier) | analyste |
| A7 | McKinsey Tech Trends 2026 : baisse de productivité dans près de 30 % des entreprises avec des agents | https://www.newkerala.com/news/a/mckinsey-report-shows-productivity-decline-30-companies-using-382.htm | presse | 2026-09 | 2026-10-24 | basse (non vérifiée) | presse |
| A8 | Claude Code : Commercial Terms pour Team, Enterprise et API ; Consumer Terms pour Free, Pro et Max | https://code.claude.com/docs/en/legal-and-compliance | Anthropic | courant | 2026-10-24 | haute | doc officielle |
| A9 | Indemnisation PI des sorties (Section K) avec exclusions : modification, combinaison, usage contrefaisant connu, brevets, marques ; « not for consumer use » | https://www.anthropic.com/legal/commercial-terms | Anthropic | 2025-06-17 | 2026-10-24 | haute | doc officielle |
| A10 | Indemnisation Copilot liée au filtre de code public ; étendue au « code referencing » si les licences sont respectées (Business, Enterprise) | https://github.blog/news-insights/product-news/code-referencing-now-generally-available-in-github-copilot-and-with-microsoft-azure-ai/ ; https://resources.github.com/learn/pathways/copilot/essentials/establishing-trust-in-using-github-copilot/ | GitHub | 2024 | 2026-10-24 | haute | doc officielle |
| A11 | Filtre critiqué comme limité aux correspondances exactes (plainte collective de 2023) | https://www.theregister.com/2023/06/09/github_copilot_lawsuit/ | The Register | 2023-06 | 2026-10-24 | moyenne | presse |
| A12 | Git AI : attribution ligne par ligne déclarée par l'agent, stockée dans des Git Notes, conservée au rebase et au squash ; prend en charge Claude Code, Cursor et Copilot | https://github.com/acunniffe/git-ai ; https://usegitai.com | projet | 2026 | 2026-10-24 | moyenne | dépôt |
| A13 | Thoughtworks Radar : Git AI en « Assess » (avril 2026) ; ne prouve pas la licence ; fusions faites dans l'interface web non suivies | https://www.thoughtworks.com/radar/tools/git-ai ; https://www.rubinlake.com/en/technology-radar/developer-ai-and-delivery/git-ai | Thoughtworks ; Rubin Lake | 2026-04 | 2026-10-24 | moyenne | analyste |
| A14 | AI Act : assistant de code a priori hors annexe III ; risque si la télémétrie sert à évaluer des salariés ; article 50 appliqué depuis le 02/08/2026 | https://knowledge.dlapiper.com/dlapiperknowledge/globalemploymentlatestdevelopments/2026/deployer-obligations-under-the-ai-act-implications-for-employers-from-2-august-2026 ; https://www.augmentcode.com/tools/ai-coding-tools-eu-ai-act-compliance | DLA Piper ; Augment (fournisseur) | 2026 | 2026-10-24 | moyenne | juridique |
| A15 | Omnibus : échéance du haut risque reportée au 02/12/2027, adoption formelle en attente (juin 2026) | https://www.processexcellencenetwork.com/ai/articles/eu-ai-act-2026-what-actually-changed-and-what-deployers-still-must-do | presse | 2026-06 | 2026-10-24 | basse | presse |
| A16 | Codex : coût par token × 10 à 20 depuis le 16/06/2026 (561 réactions) ; demande de supprimer la limite de 5 h | https://github.com/openai/codex/issues/28879 ; https://github.com/openai/codex/issues/34035 | issues | 2026-06 / 2026-07 | 2026-10-24 | haute (fait d'usage) | retour d'usage |
| A17 | Question auto-répondue au bout de 60 s dans Claude Code (#73125, fermée le 04/07) et Codex (#28969, ouverte) ; commentaires verbeux et tics de style dans Claude Code | https://github.com/anthropics/claude-code/issues/73125 ; https://github.com/openai/codex/issues/28969 ; https://github.com/anthropics/claude-code/issues/65961 ; https://github.com/anthropics/claude-code/issues/77136 | issues | 2026-06 / 2026-07 | 2026-10-24 | haute | retour d'usage |
| A18 | Copilot facturé en crédits IA au token (entrée, sortie, cache) depuis le 01/06/2026 | https://github.blog/changelog/2026/04/27/github-copilot-is-moving-to-usage-based-billing/ ; https://github.blog/changelog/2026-06-01-updates-to-github-copilot-billing-and-plans/ | GitHub | 2026-04 / 2026-06 | 2026-10-24 | haute | doc officielle |
| A19 | Plaintes Reddit : le mode agent Copilot consomme le quota sans qu'on le voie | https://codemyspec.com/blog/github-copilot-review-2026 | blog (relaie Reddit) | 2026 | 2026-10-24 | basse | retour d'usage indirect |
| A20 | Cursor : limites et manque de transparence du forfait Pro, plaintes sur le forum | https://forum.cursor.com/t/pro-plan-rate-limit-transparency-issues-need-specific-usage-details/113028 | forum Cursor | 2025 | 2026-10-24 | moyenne (hors fenêtre de fraîcheur) | retour d'usage |
| A21 | VS Code et Copilot : suppression de Keep/Undo par changement, retours de friction (281 réactions) | https://github.com/microsoft/vscode/issues/339363 | Microsoft (issue) | 2026-10-02 | 2026-10-24 | haute | retour d'usage |
| A22 | Codex : logs SQLite (environ 640 To/an), démon auto-démarré, clignotement sous Windows, piste d'audit multi-agents chiffrée, modèle des sous-agents imposé | https://github.com/openai/codex/issues/28224 ; https://github.com/openai/codex/issues/48195 ; https://github.com/openai/codex/issues/48074 ; https://github.com/openai/codex/issues/28058 ; https://github.com/openai/codex/issues/31814 | issues | 2026-06 à 2026-09 | 2026-10-24 | haute | retour d'usage |
| A23 | `claude plugin eval` : graders, 3 passes, comparaison sans plugin `Δ`, seuil pour la CI, `init` ; format distinct de skill-creator | https://code.claude.com/docs/en/plugin-evals.md | Anthropic | 2026-09 | 2026-10-24 | haute | doc officielle |
| A24 | Prérequis v2.1.269 ; `--model` à épingler en CI ; `--max-cost-usd` | https://code.claude.com/docs/en/plugin-evals.md ; https://code.claude.com/docs/en/whats-new/2026-w37.md | Anthropic | 2026-09 | 2026-10-24 | haute | doc officielle |
| A25 | Les passes n'ont ni `CLAUDE.md`, ni réglages, ni hooks, ni autres plugins, ni mémoire | https://code.claude.com/docs/en/plugin-evals.md | Anthropic | 2026-09 | 2026-10-24 | haute | doc officielle |
| A26 | Windows natif sans bac à sable : WSL2 pour les suites qui ouvrent le shell | https://code.claude.com/docs/en/plugin-evals.md | Anthropic | 2026-09 | 2026-10-24 | haute | doc officielle |
| A27 | Skill `eval-harness` d'ECC : `.claude/evals/`, pass@k ; revue Tessl à 57 %, aucun scénario exécuté | https://tessl.io/registry/skills/github/affaan-m/ECC/eval-harness/review | Tessl | 2026 | 2026-10-24 | moyenne | registre |
| A27b | skills.sh classe par installations ; environ 59 000 skills selon un miroir | https://skillselion.com/skills | Skillselion (miroir commercial) | 2026 | 2026-10-24 | basse | agrégateur |
| A28 | WebFetch : conversion en Markdown, extraction par un modèle secondaire, « lossy by design », 100 000 caractères par appel, cache de 15 min ; 200 WebSearch par session | https://code.claude.com/docs/en/tools-reference.md | Anthropic | courant | 2026-10-24 | haute | doc officielle |
| A29 | WebFetch inefficace sur les pages rendues en JavaScript ; test isolé : 42 s avec Firecrawl contre plus de 4 min 30 | https://www.firecrawl.dev/blog/claude-web-fetch-vs-firecrawl ; https://scrapingant.com/blog/claude-code-cant-scrape-javascript-sites | Firecrawl, ScrapingAnt (fournisseurs) | 2026 | 2026-10-24 | basse | fournisseur |
| A30 | Firecrawl : AGPL-3.0 (SDK sous MIT), cloud avec des fonctions en plus, section du README adressée aux agents | README `firecrawl__firecrawl.md` | dépôt | 2026-10 | 2026-10-24 | haute | dépôt |
| A31 | HyperFrames : environ 3 min de rendu pour 30 s en 1080p (test indépendant, chiffre tronqué) | https://yuv.ai/blog/heygen-hyperframes-html-video | blog | 2026 | 2026-10-24 | basse | retour d'usage |

## 5. Pistes non suivies et recherches vaines

- **BCG, Accenture, Capgemini, Deloitte** : aucun rapport trouvé en 2 requêtes. Piste : leurs sites (par ex. « Capgemini Research Institute generative AI software engineering » ou « Deloitte Tech Trends 2026 »), qui demandent des requêtes nominatives.
- **Texte du Magic Quadrant 2025 et des notes Gartner 2026** : 403 sur gartner.com et sur Visual Studio Magazine. Leurs mises en garde par fournisseur restent inconnues.
- **Consumer Terms d'Anthropic** : non lus. L'absence d'indemnisation pour Max est une inférence à vérifier.
- **Équivalent du filtre de code public côté Claude Code et Codex** : non trouvé. Pistes non vérifiées : détection d'extraits en CI (FOSSA, ScanCode).
- **Cursor après mars 2026** : aucune plainte fraîche trouvée ; la facturation actuelle de Cursor n'a pas été vérifiée.
- **Reddit en direct** (r/ChatGPTCoding, r/cursor) : seules des sources secondaires ont été trouvées.
- **HyperFrames sous Windows**, Firecrawl en auto-hébergement sous Windows, poids des schémas MCP d'Apify : non mesurés.
- **Skills d'évaluation dans les dépôts de la liste** : `apify/.claude/skills/creating-mcp-agent-evals` et `open-seo/.agents/skills/evaluate-skill` sont des exemples de pratiques d'éval, non lus faute de budget.
- **Suivi longitudinal d'une configuration** (scores par version de modèle) : aucun outil trouvé ; trou probable, à confirmer.
