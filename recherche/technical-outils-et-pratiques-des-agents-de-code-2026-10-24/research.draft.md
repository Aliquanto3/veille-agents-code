---
title: 'Veille : outils, plugins et pratiques des agents de code'
type: 'technical (+ user-voice, academic-lit), forme « select »'
topic: 'outils, plugins et pratiques des agents de code (Claude Code)'
decision: "Composer la configuration Claude Code d'Anaël et poser la base de la veille continue"
source: 'run natif bmad-deep-recon'
status: complete
preset: 'deep'
validation: 'normal'
created: '2026-10-24'
updated: '2026-10-25'
claims: 'registre : 21 affirmations porteuses, 15 verified, 4 unverified, 2 disputed, 0 overturned (recon_kit tally)'
---

# Veille : outils, plugins et pratiques des agents de code (octobre 2026)

**Décision servie :** quelle configuration Claude Code adopter pour la conception, le front, le back, les tests, les coûts et le confort d'usage, sur un poste Windows avec un abonnement Max, la méthode BMAD et le plugin maison agent-cost-kit ; et quelle base donner à une veille continue.

## Résumé exécutif

**Ce que disent les preuves.** En 2026, ce qui fait la différence n'est plus le modèle ni le nombre d'outils installés, c'est le **cadrage de l'agent** : un contexte court, des contrôles automatiques qui jugent son travail, et une validation tôt dans la story. Le Thoughtworks Radar d'avril 2026 met le *context engineering* en Adopt et les fichiers d'instructions qui enflent en Caution {verif:C3}. La recherche situe les échecs des agents dans leurs premières étapes, invisibles jusqu'à être irrécupérables {litt:A1}, l'usage d'agents fait monter durablement alertes statiques et complexité {litt:A19}, et des consignes de sécurité ajoutées au prompt n'améliorent pas la sûreté du code {litt:A21}.

**Les trois constats qui pilotent la recommandation.**

1. **Le natif couvre déjà l'essentiel de la liste.** Mémoire, orchestration parallèle, routage par modèle, revue, navigateur, mesure des coûts : Claude Code couvre en grande partie chaque catégorie par une fonction native ou un plugin officiel {doc:sub-agents}{orch:A1,A3}{contexte:N1}{design:A21}{verif:B5}{couts:C18} ; les manques qui restent sont listés en section 4. Sur les 47 dépôts, aucun n'est « strictement meilleur » que son équivalent natif dans la configuration étudiée : 1 est à adopter (en partie), 13 à essayer, 15 à évaluer, 10 à écarter et 8 hors périmètre (tableau en section 2).
2. **Le coût caché, c'est le contexte fixe et le cache, pas la sortie.** L'écriture du cache pèse 42 à 44 % de la dépense ; compresser les sorties de commandes économise environ 2,7 % mesuré (0,5 % estimé), et une compression agressive peut même augmenter la facture {verif:A3}. Le gain le mieux mesuré vient de TokenEconomizer : −18 à −31 % pour le plugin complet, dont −13 à −18 % pour le seul retrait des outils inutilisés, et −15 % dans un essai indépendant {verif:A2}. Les gros packs de skills vont dans le mauvais sens : ECC injecte ~131 k caractères (skills, commandes, agents, hooks) {methode:M1}, alors que la liste des descriptions de skills est plafonnée par défaut à 1 % de la fenêtre (réglable), au-delà de quoi les descriptions des skills les moins utilisées disparaissent {verif:A4}.
3. **Les preuves d'efficacité des plugins sont faibles.** Les skills de méthode et de design ne sont évaluées que par leurs auteurs ou par un seul tiers ; le test « en aveugle » publié par taste-skill, noté par un modèle avec ±0,5 point de bruit, tombe dans ce bruit (7,7 avec, 7,8 sans) {verif:C1}. Les contrôles déterministes sont mieux étayés, sans être tous mesurés : des tests en lecture seule bloquent la modification des tests (pas les cas codés en dur ; modèles de 2025) {verif:B2} ; le mutation testing révèle des suites écrites par LLM qui ne détectent que 36 % des mutants {tests:A17} ; le property-based testing piloté par agent trouve des bugs réels {tests:A20}. Les détecteurs de motifs sur page rendue, eux, n'ont pas encore de mesure d'efficacité {design:A2}.

**Recommandation.** Garder BMAD et agent-cost-kit comme colonne vertébrale, ne pas installer de pack de méthode concurrent, et investir dans des **contrôles automatiques** plutôt que dans des consignes : protection des tests, porte empirique en revue, boucle de vérification du front, mesure du contexte fixe. Six réglages sont sans regret et applicables tout de suite ; huit hypothèses demandent un test pratique avant décision (section 6).

**Principale réserve.** Presque toutes les études sont des préprints d'un seul laboratoire, et plusieurs chiffres portent sur des modèles de 2025 : sur LiveCodeBench, un audit d'octobre 2026 ne voit presque plus de triche chez Claude 5.5, avec des taux sensibles au prompt et au harnais {verif:B2}. D'où l'importance des tests pratiques sur tes propres stories.

## 1. Méthode et limites

- **Corpus.** 50 ressources recommandées (47 dépôts GitHub après retrait de 3 doublons, 6 articles ou pages). Métadonnées relues par `gh api` le 2026-10-24 (`data/depots.json`).
- **Recherche.** 10 dimensions confiées à des chercheurs Opus en parallèle (3 tours au plus, 25 appels web chacun), plus un inventaire des fonctions natives depuis la documentation officielle, puis un tour 2 sur les trous. Chaque affirmation porte sa source ; 21 affirmations porteuses ont été revérifiées par des agents au contexte vierge : 15 confirmées, 4 non vérifiées faute de source indépendante (mais conformes à leur source primaire), 2 contestées et corrigées ici.
- **Limites.** Reddit est inaccessible aux outils ; ses retours ne passent que par la presse ou les issues GitHub. L'article Medium comparant Superpowers, agent-skills, Pocock et ECC est derrière un paywall (non lu). Aucun outil n'a encore été exécuté : les verdicts « Essayer » et « Évaluer » attendent les tests de la section 6. Le Thoughtworks Radar vol. 35 n'est pas encore paru (attendu début novembre 2026) {verif:C3}.

## 2. Les 47 dépôts, regroupés par problématique

Verdicts pour la configuration étudiée (Windows, Max, BMAD, FastAPI + Jinja2 + HTML/CSS/JS vanilla). **Adopter** : à installer ou appliquer tel quel. **Essayer** : test court avant adoption. **Évaluer** : intérêt possible, preuves insuffisantes. **Écarter** : moins bon que l'existant ou risqué. **Hors périmètre** : pas un outil d'agent de code pour cette configuration.

| Problématique | Outil | Verdict | Doublon ou équivalent natif | Pourquoi |
|---|---|---|---|---|
| Méthode | obra/superpowers | Évaluer | BMAD ; plan mode, `feature-dev` | Revendique les mêmes étapes que BMAD, règle « 1 % de chance → invoquer » {verif:C6}, gains auto-mesurés ; plaintes de lenteur {methode:U1}, de budget épuisé (sous Codex) {methode:U2} et de qualité {methode:U3} |
| Méthode | mattpocock/skills | Essayer, à la carte | — | Skills manuelles sans conflit (`grill-with-docs`, `diagnosing-bugs`), 2,3 k caractères {methode:M1} |
| Méthode | addyosmani/agent-skills | Évaluer | BMAD | Méta-routeur concurrent de BMAD, ~11 k caractères {methode:M1} |
| Méthode | affaan-m/ECC | Écarter | — | ~131 k caractères injectés (311 skills, 97 commandes, 71 agents, 27 hooks) {methode:M1} ; ses seules descriptions dépassent le budget par défaut de la liste {methode:D1} |
| Méthode | multica-ai/andrej-karpathy-skills | Essayer (4 principes dans CLAUDE.md, sans plugin) | — | 0,2 à 2,4 k caractères ; dépôt inactif depuis avril |
| Méthode | liza-mas/liza | Évaluer (lecture seulement) | dev-story → second-avis → reviewer | Même idée que la chaîne maison, rendue mécanique ; WSL2, contrat de ~54 k caractères {methode:M1}{orch:A25} |
| Méthode | deepakkamboj/developer-assistant-skills | Écarter | BMAD | 1 étoile, ~15 k caractères |
| Méthode | spotify/portal-ai-plugins | Hors périmètre | — | Lié à Spotify Portal (Backstage) |
| Méthode | anthropics/skills | Adopter `skill-creator` seulement | officiel | Bench avec et sans skill pour mesurer les skills maison {methode:D1} |
| Design front | pbakaus/impeccable | Essayer (sans hooks ni télémétrie) | `frontend-design` (officiel) | Détecteur déterministe de 62 règles, utilisable sur l'URL rendue (Jinja n'est pas lu comme source) ; télémétrie par défaut {design:A1,A2} |
| Design front | Leonxlnx/taste-skill | Évaluer | — | Pensé pour les landing pages, coûteux en tokens {design:A7} ; gain dans le bruit {verif:C1} |
| Design front | Nutlope/hallmark | Évaluer | — | Sur Haiku 4.5 et selon un seul auteur : ne se déclenche pas sans être nommé (0/12), bloque 30 % des essais non interactifs {verif:C1} ; lance un sous-agent {design:A10} |
| Design front | nextlevelbuilder/ui-ux-pro-max-skill | Écarter | — | Tailwind par défaut, publication npm cassée depuis août |
| Design front | google-labs-code/design.md | Essayer | Claude Design | Contrat commun lu ou écrit par les autres skills ; format en alpha {verif:C2}{design:A11} |
| Design front | VoltAgent/awesome-design-md | Évaluer (exemples du format) | — | Collection de DESIGN.md de marques |
| Design front | nexu-io/open-design | Hors périmètre | Claude Design (inclus dans Max) {design:A22} | Espace de design complet, doublon du natif |
| Design front | emilkowalski/skills | Essayer, sélectivement | — | Règles d'animation et de performance CSS utiles en vanilla |
| Design front | greensock/gsap-skills | Hors périmètre | — | Utile seulement si GSAP est adopté |
| Design front | DavidHDev/react-bits, DavidHDev/canvas-ui, oso95/scroll-world | Écarter | — | Liés à React / shadcn / WebGL |
| Contexte, mémoire | thedotmack/claude-mem | Écarter | mémoire automatique native | 9 types de hooks dont un PreToolUse synchrone ; faille de lecture de fichiers et de clés corrigée en septembre, mais API du worker sans authentification si elle est exposée hors de la machine ; aucun gain mesuré {verif:B7}{contexte:C1} |
| Contexte, mémoire | Graphify-Labs/graphify | Évaluer (mode code seul, à la demande) | grep + LSP + Explore | Seul banc : 6 questions, comparé à grep et jamais au LSP {contexte:G1,G3,G5} |
| Contexte, mémoire | elstongun/leviathan | Hors périmètre | — | Index de jeux d'enregistrements ; 19 jours, un contributeur {contexte:L1} |
| Diagrammes | tt-a1i/archify | Évaluer | Mermaid | Fidélité au code non prouvée ; contacte son serveur toutes les 24 h {contexte:A2} |
| Diagrammes | cathrynlavery/diagram-design | Essayer (livrables client) | Mermaid pour la doc versionnée | Se dit lui-même moins adapté que Mermaid à la doc versionnée {contexte:D1} |
| Coûts | microsoft/TokenEconomizer | Évaluer ; reprendre son idée | — | Meilleures preuves de la liste (−18 à −31 % pour le plugin complet), mais déclare ne pas tourner sous Windows natif {verif:A2} |
| Coûts | alexei-led/claude-router | Écarter | `/advisor`, effort, modèle des sous-agents | La version actuelle n'a aucun résultat mesuré, de l'aveu de l'auteur (l'ancienne passerelle : −4 à −16 %, un seul développeur) ; prompts envoyés par défaut à un classifieur tiers {couts:C10,C11} |
| Coûts, sobriété | Institut-du-Numerique-Responsable/green-claude | Évaluer (audit d'écoconception à la demande) | — | Ne mesure rien, ajoute ~15,8 k caractères et des hooks {couts:C12,C13} |
| Routage | BerriAI/litellm | Évaluer | endpoint Anthropic natif d'Ollama / LM Studio | Utile seulement pour mêler cloud et local facturés à l'API ; paquets PyPI compromis en mars 2026 {routage:A17} |
| Routage | felipevicens/aaif-labs (agentgateway) | Hors périmètre ; agentgateway : Évaluer | Claude apps gateway | Le dépôt est un lab K8s personnel ; agentgateway (AAIF, Apache-2.0, binaire Windows) est la piste pour conseiller des clients {routage:A20,A21,A22} |
| Routage | theroyallab/tabbyAPI | Écarter | Ollama, llama.cpp | Pas d'endpoint Anthropic {routage:A24} ; GPU NVIDIA (ou AMD sous Linux), AGPL {routage:A25} |
| Modèles locaux | AlexsJones/llmfit | Essayer (présélection) | — | Estimations optimistes sur matériel modeste ; ne pas installer sa skill (faite pour OpenClaw) |
| Revue | alibaba/open-code-review | Essayer (en délégation) | `/code-review` | Déterministe + LLM, ~15× moins de tokens selon le banc de l'éditeur {revue:A16} ; une reproduction indépendante sur 10 PR (confiance basse) mesure une précision bien plus basse {revue:A17} |
| Sécurité | cloudflare/security-audit-skill | Évaluer (sous WSL) | `/security-review`, ultrareview | Méthode la plus rigoureuse vue par le chercheur (vérificateur frais qui tente de réfuter) ; validateurs cassés sous Windows natif, d'après la lecture du code {revue:A22,A23} |
| Sécurité des skills | NVIDIA/SkillSpector | Essayer (`--no-llm`, avant installation) | — | Aucun taux de détection publié ; tous les scanners testés ont été contournés {verif:B6} |
| Tests | microsoft/playwright-cli | Essayer (vérification headless) | Claude in Chrome, Playwright MCP | Plus d'écart de tokens notable avec le MCP {verif:B1} ; génère des tests TypeScript hors de pytest {tests:A1} |
| Orchestration | paperclipai/paperclip | Écarter | agent view | « Entreprise d'agents » hors méthode supervisée ; blocages silencieux, bugs Windows, télémétrie {orch:A6,A7,A8} ; 106 k étoiles, mais 3 à 4 points sur HN et au plus 34 commentaires par issue {orch:A9,A13,A14} |
| Orchestration | stablyai/orca | Évaluer | agent view | Multi-fournisseurs, annotation de diffs, Design Mode ; usage réel attesté {orch:A10,A11,A12} |
| Orchestration | SmythOS/smythos-studio | Hors périmètre | — | Constructeur d'agents visuel, dormant {orch:A28} |
| Expérience | ayghri/i-have-adhd | Évaluer (essayer d'abord le style natif Concise) | output style Concise | Auto-évaluation : +0,43/5, mais régression sur les cas de succès partiel, attribuée de façon plausible à une règle qui pousse à affirmer une cause {orch:A20} |
| Rédaction | blader/humanizer | Essayer (rédaction seulement) | — | Préféré en aveugle (16/16, petit échantillon), mais les détecteurs le repèrent toujours {orch:A22,A23} |
| Veille, données web | firecrawl/firecrawl | Essayer (veille, service hébergé) | WebFetch | WebFetch jugé inefficace sur les pages rendues en JavaScript (par deux fournisseurs concurrents, confiance basse) ; cœur sous AGPL {tour2:A29,A30} |
| Veille, données web | apify/apify-mcp-server | Évaluer | WebFetch, WebSearch | Télémétrie par défaut, paiements par l'agent à interdire |
| Données | public-apis/public-apis | Hors périmètre | — | Annuaire d'API |
| Marketing | every-app/open-seo | Hors périmètre | — | Utile seulement en mission SEO |
| Démonstrations | heygen-com/hyperframes | Essayer (vidéos de démo) | — | Vidéo à partir de HTML, comme ta pile ; Windows non vérifié {tour2:A31} |

Articles et pages de la liste : la page **advisor** décrit une fonction native à essayer {couts:C14} ; l'article d'Anthropic sur **sa revue de code** donne des règles de convergence à adopter {revue:A1,A2} ; le billet **MLflow** montre que MLflow reçoit directement les traces OpenTelemetry natives (contenu masqué par défaut, erreurs d'export silencieuses) {orch:A16} ; **agent-standup** est trop jeune pour conclure ; le billet **RTK** mesure un gain marginal {verif:A3} ; l'article **Medium** n'a pas pu être lu.

## 3. Constats par problématique

### 3.1 Méthode de développement
- Le chercheur distingue trois philosophies : pipeline imposé (Superpowers, Liza, ECC), boîte à outils à la carte (Pocock, Karpathy), cycle complet routé par une méta-skill (addy, deepakkamboj). Superpowers, addy et BMAD revendiquent les mêmes étapes, et deux projets déconseillent d'en faire tourner deux comme routeurs automatiques {methode:M3,M4}. Seules les skills **manuelles** (`disable-model-invocation`) s'ajoutent à BMAD sans conflit {methode:D1}.
- Aucun banc indépendant ne compare ces méthodes. Les skills curées aident (+11,6 points en génie logiciel dans SkillsBench v4), celles générées par le modèle font **moins bien** que rien ; multiplier les skills disponibles ne fait pas chuter la réussite, mais rend leur usage imprécis {verif:C6}.
- Natif : plan mode, `/goal`, hook Stop, `/code-review`, plugins officiels `feature-dev` et `skill-creator` {methode:D2,D3}.
- **Face à tes projets** : BMAD + agent-cost-kit couvre déjà toutes les étapes, avec des mesures (1,18 à 1,60 $ par story contre 6,77 à 7,31 $ avec l'ancien setup). Aucun pack n'a de raison de le remplacer.

### 3.2 Design et front
- Aucune skill anti-« AI slop » n'est strictement meilleure ; chacune gagne dans un cas (tableau de la section 2). Leur point faible mesuré est l'**activation** : hallmark (sur Haiku 4.5) et impeccable ne se sont pas déclenchés sans être nommés, et leurs fichiers de règles n'ont pas été lus ; ce sont deux mesures d'un même auteur {verif:C1}. Dans un sous-agent `dev-story`, il faut donc nommer la skill dans le prompt.
- Ce qui a une mesure : la critique visuelle sur capture d'écran, jusqu'à +17,8 % en 3 cycles (préprint, une équipe) {verif:C2}. Les détecteurs déterministes sur page rendue sont bon marché mais sans mesure d'efficacité {design:A2,A10}.
- Trous : aucune skill de design ne lit les templates Jinja (il faut passer par l'URL rendue) ni n'intègre d'audit d'accessibilité sémantique, que seul l'outil navigateur agent-browser embarque (axe-core) {tests:A26} ; les UI générées gardent des violations sémantiques {design:A34}. La sobriété n'est visée que par green-claude, côté code {couts:C12}, et taste-skill va même à l'inverse {design:A8}.
- Natif ou officiel : skill `frontend-design`, plugins `playwright`, `chrome-devtools-mcp` et `modern-web-guidance` (Google Chrome, utile pour les API HTML/CSS natives), Claude in Chrome, Claude Design {design:A20,A21,A22,A23}.

### 3.3 Contexte, mémoire, compréhension du code
- Le natif couvre l'essentiel : CLAUDE.md court et règles par chemin chargées à la demande, mémoire automatique (index de 200 lignes ou 25 Ko) {contexte:N1,N2}, `/doctor prompt-audit`, sous-agent Explore, LSP et coût de contexte affiché par plugin {contexte:N3,N4,N5,N6}.
- Les résumés en langage naturel restituent mal le comportement du code (4 questions sur 45, contre 27 avec le code source) : un argument contre les résumés de code comme substitut du code source (préprint) {contexte:R4}. L'empoisonnement de mémoire est démontré, y compris sur le MEMORY.md de Claude Code {contexte:R6,R7}.
- **Face à tes projets** : ta mémoire automatique et ton `MEMORY.md` court suivent déjà la bonne pratique ; aucun outil ne traite la péremption des mémoires.

### 3.4 Coûts et tokens
- Postes de coût : écriture du cache 42 à 44 %, lecture du cache ~35 % (PointFive), sortie 10 à 29 % selon les mesures {verif:A3} ; tes propres mesures donnent 39 à 42 / 38 à 40 / 19 à 21 %.
- Leviers natifs : TTL du cache des sous-agents (5 min par défaut, même sur abonnement) {verif:A5}, éviter tout changement de modèle en cours de session (`opusplan` en est un) {couts:C17}, `/clear` plutôt que `/compact` {couts:C18}, réduire la liste des skills et les outils jamais appelés {verif:A4,A2}, filtrer les sorties de tests par hook {couts:C20}.
- `/advisor` (Opus conseille un exécutant moins cher) : +2,7 points et −11,9 % de coût sur des modèles 4.6, non mesuré sur les 5.5 {couts:C14,C15}.
- Empreinte : rien n'est mesuré pour un modèle fermé ; EcoLogits ne compte que les tokens de sortie {couts:C21,C22}. agent-cost-kit hérite de cette limite.
- **Face à tes projets** : agent-cost-kit couvre déjà la mesure, l'estimation EcoLogits et la règle du TTL ; il lui manque la mesure du **contexte fixe** (skills, hooks, outils) et une règle sur le retrait des outils inutilisés.

### 3.5 Routage cloud / local
- Claude Code se branche sur tout serveur au format Anthropic Messages via `ANTHROPIC_BASE_URL`, mais Anthropic ne prend pas en charge les modèles non-Claude {routage:A1}. Ollama, LM Studio et llama.cpp exposent nativement `/v1/messages` : pas besoin de passerelle pour le local {routage:A10,A12,A13}. L'API compatible d'Ollama ne prend en charge ni `cache_control` ni `count_tokens` {verif:A6}.
- Une passerelle avec son propre identifiant **fait sortir de l'abonnement Max** : la facture va au titulaire de la clé transmise. `ANTHROPIC_BASE_URL` seul conserve l'abonnement, à condition que la passerelle relaie la capacité OAuth (`anthropic-beta`), sinon erreur 401 {verif:A6}.
- Une requête Claude Code pèse ~29 k tokens, surtout des définitions d'outils, d'après une mesure de blog {routage:A31} : un modèle ≤ 4B sur CPU paraît inadapté comme moteur de Claude Code, mais reste utile en appel direct (lookup, résumé). La classe crédible est celle des MoE à ~3 B actifs, comme Qwen3-Coder-Next (70,6 % sur SWE-bench Verified selon l'éditeur) {routage:A33} ou Qwen3.6-35B-A3B, que tu as (source unique) {routage:A36}.
- Les en-têtes d'indice de passerelle (v2.1.273+, à activer par `CLAUDE_CODE_GATEWAY_HINT_HEADERS=1` sur une URL personnalisée) donnent la classe de requête et le type d'agent ; avec l'en-tête `agent-id`, envoyé à part, une passerelle peut router et attribuer les coûts par sous-agent. Une passerelle à clé propre sort toutefois de l'abonnement {verif:A7,A6}.
- **Face à tes projets** : slm-quality-bench et wavelocalai appellent Ollama directement ; c'est la bonne voie pour les SLM. La comparaison cloud / local « en situation d'agent » demande un protocole dédié (section 6, après ton benchmark).

### 3.6 Revue de code et sécurité
- Anthropic ne publie pour sa revue ni taux de faux positifs ni coût ; ce qui se transpose à un dev solo, ce sont ses **règles de convergence** : 3 passes au plus, ne relire que le nouveau diff, constats étiquetés Important / Nit / Pre-existing {revue:A1,A2}.
- Sur Max, le service Code Review (GitHub) est inaccessible ; restent `/code-review`, `/code-review ultra` (research preview : 3 essais gratuits par compte Pro ou Max, puis 5 à 25 $ en crédits d'usage à activer) et `/security-review` {verif:B5}.
- La précision des revues par LLM reste basse (5,6 à 39,9 % selon les modèles, une seule étude) {verif:B4}. Un préprint relate un cas où dix relecteurs unanimes ont validé une faille inexistante, réfutée par un seul test, et recommande de remplacer le consensus par un test et par un critique d'une autre famille ; c'est une recommandation, pas une comparaison mesurée {verif:B4}. Ta chaîne Sonnet → Haiku → Opus reste dans une seule famille.
- Chaîne d'approvisionnement : les scanners statiques de skills testés ont été contournés ; une détection dynamique (exécution surveillée) fait mieux dans un préprint {verif:B6}. Lire une skill avant de l'installer reste indispensable. Le sandbox natif exige WSL2 sous Windows {doc:sandboxing}.

### 3.7 Tests et vérification
- Navigateurs pour agents : plus d'écart de tokens notable entre playwright-cli et Playwright MCP {verif:B1}. Claude in Chrome pour la vérification interactive (pas en CI) {tests:A7}, une CLI headless pour les runs autonomes ; agent-browser intègre diff visuel et audit axe-core, sans équivalent vu par le chercheur {tests:A26}.
- Triche aux tests : chez les modèles de 2025, elle passait surtout par la modification des tests, que des tests en lecture seule bloquent {verif:B2}. Règle native `deny Edit(tests/**)` (ne couvre pas un script Python qui écrit le fichier) {tests:A12}.
- Tests faibles : 36 % des commits d'agents ajoutent des mocks contre 26 % des commits non-agents (commits de 2025, étude unique) {verif:B3} ; les tests jetables (`print`) coûtent jusqu'à 49 % de tokens d'entrée pour ~2 points de résolution {tests:A14}. Parades plausibles : mutation testing, qui mesure la force des assertions (cosmic-ray affiche un support Windows, non testé ; mutmut exige WSL) {tests:A16,A17,A19}, couverture différentielle en CI {tests:A21}. Seul le property-based testing piloté par agent a une mesure d'efficacité (56 % de bugs signalés valides) {tests:A20}.
- Playwright Python n'a pas de comparaison de captures, et elle n'est pas prévue ; il a les snapshots ARIA {tests:A23,A24}.

### 3.8 Orchestration, observabilité, expérience
- Natif : agent view (sessions en arrière-plan, worktree par session, notifications), dynamic workflows, `/batch`, agent teams (expérimental, sans reprise après `/resume`, sans panneaux dans Windows Terminal) {orch:A1,A2,A3}.
- OpenTelemetry natif : coût et tokens par agent (`agent_id`, `parent_agent_id`, `workflow.run_id`) ; le tracing de base est en bêta, seule sa version détaillée demande une liste blanche en CLI interactive {verif:C7}. Il pourrait remplacer une partie de l'analyse des transcriptions d'agent-cost-kit.
- Lisibilité : d'après le chercheur, le style natif **Concise** {orch:A19} recouvre l'essentiel d'i-have-adhd {orch:A20}.

### 3.9 Capacités voisines
Pas des outils d'agent de code, mais utiles à la veille et aux démonstrateurs.

- **firecrawl** : Essayer pour la veille, en service hébergé (le cœur est sous AGPL). WebFetch natif convertit en Markdown avec perte et échoue sur les pages rendues en JavaScript {tour2:A28,A29,A30}.
- **apify-mcp-server** : Évaluer ; télémétrie par défaut, et paiements par l'agent à interdire.
- **public-apis** : Hors périmètre (annuaire). **open-seo** : Hors périmètre, sauf mission SEO.
- **hyperframes** : Essayer pour les vidéos de démo de tes applications, car il part de HTML, comme ta pile ; environ 3 min de rendu pour 30 s en 1080p (source de confiance basse), Windows non vérifié {tour2:A31}.

**Voix des analystes et des autres outils.** Gartner conseille de ne pas confier toutes les tâches aux agents et met la gouvernance de tout le cycle de développement au premier plan {tour2:A3} ; Forrester juge le code produit « souvent problématique » {tour2:A5}. Les plaintes de quotas ne sont pas propres à Claude Code {prat:R13} : hausse du coût par token chez Codex {tour2:A16}, passage de Copilot à la facturation au token le 2026-06-01 {tour2:A18}, plaintes sur les limites de Cursor (2025) {tour2:A20}. La question tranchée d'office après 60 s a touché Claude Code (corrigé en juillet) et reste ouverte chez Codex {tour2:A17}.

## 4. Problématiques que rien ne traite bien

| Problème | Ce qui existe | Source |
|---|---|---|
| Évaluer sa configuration d'agent dans le temps | `claude plugin eval`, `skill-creator`, `/skill-doctor` pour une skill ; rien pour une configuration entière ; le Radar ne place « measuring collaboration quality » qu'en Assess | {doc:plugin-evals}{tour2:A25}{prat:R2} |
| Charge de l'humain qui relit | Agent view regroupe ce qui est prêt ; span `blocked_on_user` en traces bêta ; rien ne régule | {orch:A3}{verif:C7} |
| Tests trichés ou faibles, mesurés à chaque story | Mutation testing non borné à la story (durée à mesurer) ; moniteurs de triche à 42–65 % de détection | {tests:A10} |
| Robustesse du relecteur à l'injection de prompt | `/security-review` non durci ; aucun outil ne mesure la sienne | {revue:A12,A13} |
| Contrôle à l'exécution des skills tierces | Scanners statiques contournés ; détection dynamique au stade de la recherche | {verif:B6} |
| Péremption et empoisonnement de la mémoire | Rappel à élaguer dans la doc ; rien ne lie une mémoire à sa source | {contexte:N1,R6,R7} |
| Garder l'abonnement Max en routant une partie vers le local | Non documenté | {verif:A6} |
| Empreinte réelle d'un modèle fermé | Estimations sur les seuls tokens de sortie | {couts:C21} |
| Accessibilité sémantique et sobriété du front généré | Aucune skill de design n'intègre axe (l'outil navigateur agent-browser, si) ; la sobriété n'est visée que par green-claude, côté code | {design:A34}{tests:A26}{couts:C12} |
| Traçabilité exigences → code et attribution du code IA, licences | Git AI, Agent Trace en Assess ; voir tour 2 | {prat:R2}{tour2:A12,A13} |
| Propriété intellectuelle du code livré à un client | L'indemnisation d'Anthropic figure dans les Commercial Terms (API, Team, Enterprise), annoncée « not for consumer use » ; Max relève des Consumer Terms, non lus ; elle exclut le code modifié ou combiné | {tour2:A8,A9} |
| Évaluer une configuration complète | `claude plugin eval` exécute sans CLAUDE.md, réglages, hooks ni autres plugins | {tour2:A25} |
| Conflits sémantiques entre stories parallèles | Isolement par worktree seulement | {orch:A2,A3} |
| Coût des reprises après pause (cache expiré) | TTL du cache réglable {verif:A5}, mais ni mesure ni règle de reprise ; un praticien attribue 55 % de ses écritures de cache aux reprises après une heure (chiffre individuel) | {prat:R13} |

## 5. Enseignements transverses

1. **Du prompt vers le contrôle.** Les dimensions méthode, tests, revue et design convergent : les consignes de sécurité ajoutées au prompt n'améliorent pas la sûreté du code {litt:A21} et les skills de design n'ont pas d'effet mesurable {verif:C1} ; seules les skills curées montrent un gain net {verif:C6}. Les contrôles déterministes (tests verrouillés, mutation testing, tests de propriétés) sont mieux étayés {verif:B2}{tests:A17,A20}. Le Radar fait la même lecture : « feedback sensors » en Trial, « instruction bloat » en Caution {verif:C3}.
2. **Le contexte fixe est un coût et un risque.** Les descriptions des skills installées occupent le budget de leur liste (sauf skills manuelles) {verif:A4}{methode:D1}, les hooks injectent leur sortie, et chaque ajout élargit la surface d'attaque {verif:B6}. La meilleure économie mesurée vient du retrait {verif:A2}. Corollaire : le critère d'entrée d'un outil dans ta configuration doit inclure son coût de contexte, mesuré.
3. **Le natif rattrape les plugins en 6 mois.** Mémoire, orchestration, navigateur, design system, évaluations de plugins : la plupart des fonctions vendues par les dépôts les plus étoilés de la liste ont un équivalent natif apparu en 2026. Pour la veille, un changelog Claude Code vaut plus qu'un classement d'étoiles.
4. **Les étoiles ne disent rien.** paperclip (106 k étoiles) a au plus 34 commentaires par issue {orch:A9} ; TokenEconomizer (223 étoiles au 2026-10-24, d'après `data/depots.json`) a les meilleures preuves de la liste {verif:A2}.

## 6. Recommandations

### 6.1 Sans regret, applicables maintenant (confiance haute, réglages réversibles)
1. **Ne pas installer de pack de méthode à côté de BMAD** (Superpowers, addy, ECC, deepakkamboj). Base : coût fixe mesuré {methode:M1}, conflit d'étapes déclaré par les projets eux-mêmes {methode:M3}.
2. **Mesurer ton contexte fixe actuel** (`/context`, `/skill-doctor`, `claude plugin details`) avant tout ajout, et faire de ce coût un critère d'entrée. Base : {verif:A4}{methode:D1}.
3. **Adopter les règles de convergence d'Anthropic dans le reviewer** d'agent-cost-kit : 3 passes au plus, nouveau diff seulement, étiquettes Important / Nit / Pre-existing. Base : {revue:A2} (pratique publiée avec des chiffres internes : boucles de plus de 50 passes, 59 % de constats répétés sur du code déjà présent).
4. **Ajouter au prompt de `dev-story` une consigne anti-mock** (pas de mock des modules internes), recommandée par les auteurs de l'étude, plutôt que dans CLAUDE.md, pour ne pas alourdir le contexte de toutes les sessions. Base : {verif:B3} (commits de 2025). La consigne contre les tests jetables à base de `print` relève d'un compromis (−33 à −49 % de tokens d'entrée contre −1,8 à −2,6 points de résolution) {tests:A14} et passe dans le test T4.
5. **Écarter** claude-mem, claude-router, RTK, paperclip, ui-ux-pro-max, tabbyAPI. Base : section 2 et, pour RTK, {verif:A3}.
6. **Avant toute installation d'une skill tierce** : la lire, puis la passer à SkillSpector `--no-llm` ; ne jamais considérer un scan propre comme une preuve. Base : {verif:B6}.

### 6.2 À décider après un test pratique (section 7)
Les huit tests ci-dessous portent les décisions qui restent : CLAUDE.md minimal, protection des tests et mutation testing, porte empirique et critique d'une autre famille en revue, `/advisor`, boucle de vérification front et choix de la skill de design, choix du navigateur, OpenTelemetry natif contre l'analyse des transcriptions, modèles locaux.

### 6.3 À construire en s'inspirant des outils (évolutions d'agent-cost-kit ou nouveaux mods)
| Outil à construire | Inspiré de | Pourquoi le construire plutôt que l'installer |
|---|---|---|
| **Mesure et garde-fou du contexte fixe** : coût par skill, plugin, hook et outil depuis les transcriptions, alerte au-delà d'un seuil, liste des outils jamais appelés | TokenEconomizer, `/skill-doctor` | TokenEconomizer déclare ne pas tourner sous Windows (lanceur POSIX `sh`) ; son levier est le mieux mesuré {verif:A2} |
| **Boucle de vérification du front** pour FastAPI + Jinja : page rendue, captures à 3 largeurs, audit axe, snapshots ARIA, détecteur de motifs | impeccable `detect`, hallmark `sloplint`, agent-browser | Aucune skill de design ne lit Jinja ni n'intègre d'audit d'accessibilité sémantique {design:A34}{tests:A26} |
| **Second avis d'une autre famille** (GPT, Gemini ou Mistral via OpenRouter) | Refute-or-Promote, Cloudflare | Hypothèse à tester ; ta chaîne est mono-famille {verif:B4} |
| **Porte empirique** : un test qui échoue exigé pour tout constat Important | Refute-or-Promote, revue d'Anthropic | Recommandation d'un préprint (remplacer le consensus par un test), non mesurée {verif:B4} |
| **Protection des tests par phase** : tests de la story relus puis verrouillés pendant l'implémentation (hook PreToolUse), contrôle du diff sur `tests/` par le second avis | ImpossibleBench, superpowers TDD | La règle `deny` native vaut pour toute la session {tests:A12} |
| **Veille continue** : `watchlist` des dépôts et sources, collecte `gh api` mensuelle, routine planifiée qui signale releases et nouveaux candidats | ce run | Aucun outil de la liste ne fait de veille sur sa propre catégorie |

## 7. Tests pratiques proposés (phase 4)

Contraintes : ni Ollama ni GPU avant la fin du benchmark local (~2026-10-27), charge locale minimale (pas de rejeu de stories ni de suite complète en local) ; les tests lourds passent par la CI GitHub ou une session cloud. Appels hors Claude via OpenRouter (facturés à l'usage).

| # | Test | Décide | Coût et contrainte | Quand |
|---|---|---|---|---|
| T1 | **Diagnostics sans rejeu** : contexte fixe actuel ; sur tes transcriptions passées, part de Bash dans les tokens d'entrée, coût des reprises après pause, part des constats du second avis Haiku retenus par le reviewer, simulation d'un critère d'arrêt | Garde-fou du contexte fixe ; utilité du second avis ; règle de reprise | Très faible, scripts sur fichiers | Maintenant |
| T2 | **OpenTelemetry natif contre `mesurer-couts`** sur une session | Simplification d'agent-cost-kit | Faible | Maintenant |
| T3 | **CLAUDE.md minimal contre actuel**, 5 stories rejouées | Taille de tes CLAUDE.md | Élevé ; en CI ou après le benchmark | Après accord |
| T4 | **Tests** : consigne anti-mock + tests verrouillés pendant l'implémentation + couverture différentielle + mutation testing (cosmic-ray) borné à la story | Protection des tests, porte de CI | Moyen ; mutation en CI | Après accord |
| T5 | **Revue** : porte empirique + règles de convergence + second avis d'une autre famille (OpenRouter), sur 5 PR aux bugs connus ; open-code-review en option | Chaîne de revue | Moyen ; quelques dollars OpenRouter | Après accord et clé |
| T6 | **`/advisor`** : Sonnet + conseiller Opus contre le pipeline actuel, 5 stories | Modèle de `dev-story` | Élevé | Après T3 |
| T7 | **Front** : rien / `frontend-design` / impeccable / hallmark, puis boucle déterministe, sur un écran Jinja ; navigateur : Claude in Chrome / playwright-cli / agent-browser sur un parcours de 7 étapes | Skill de design, boucle de vérification, navigateur | Moyen ; ta note à l'aveugle requise | Après accord |
| T8 | **Local** : ≤ 4B en appel direct comme lookup contre Haiku ; MoE 35B-A3B dans Claude Code ; routage des sous-agents Explore par en-têtes | Place des modèles locaux | GPU et Ollama | Après le benchmark |

Tests écartés faute d'enjeu suffisant pour l'instant : graphify contre LSP, agent view contre le run autonome, orca, Concise contre i-have-adhd (à faire au fil de l'eau), humanizer en français (à faire avec le post LinkedIn).

## 7 bis. Résultats des tests pratiques (24 et 25 octobre 2026)

Ajouté le 2026-10-25. Les protocoles, données brutes et scripts sont dans `tests-pratiques/` (un dossier par test, `PLAN.md` pour l'état). Le coût de chaque test est dans son fichier de résultats. Le benchmark local d'Anaël était en pause pendant T3, T4, T6, T7, T8 et T10.

| # | Question | Résultat | Décision |
|---|---|---|---|
| T1 | Où passent les tokens ? (transcriptions de 45 jours) | Contexte fixe 51,7 k (principale), 38,2 k (sous-agent), dont 25,5 k et 17,4 k de définitions d'outils ; 8 outils rarement appelés pèsent 17,8 k. Bash fait 13,6 % de l'entrée, dont 54 % de lectures de fichiers. TTL 1 h des sous-agents : −358 $. Second avis : 87 % de ses constats medium ou high corrigés, 0,03 $ la story. | Listes `tools:` explicites (kit 0.11.0) ; pas d'outil de compression ; pas de TTL 1 h ; garder le second avis ; alerte de dérapage plutôt que coupure |
| T2 | OpenTelemetry natif contre mesurer-couts | Tokens identiques à l'unité, coût à ±0,2 % | Transcriptions pour l'historique, OpenTelemetry en contrôle croisé |
| T3 | CLAUDE.md minimal contre actuel | 4 stories × 5 répétitions (Sonnet) : minimal −3,6 % de coût, IC [−8 ; +7], réussite égale (86 %) ; lint propre 20/20 contre 12/20 | Ne pas tailler un CLAUDE.md de quelques k tokens pour économiser ; y mettre les commandes de contrôle |
| T4 | Mutation bornée à la story, couverture différentielle | Vrai trou de test dans 5 stories sur 5 ; 1 story sur 5 sous 10 min ; les 5 passent diff-cover à 80 % alors que ~72 % des lignes à survivants sont couvertes | Pas de porte de mutation ; diff-cover en CI ; mutation en étape optionnelle de la revue |
| T4 bis | Tests verrouillés pendant l'implémentation | 40 runs Sonnet, tests d'acceptation fournis : 0 test modifié avec ou sans règle deny ; face à un test faux, l'agent le signale sans y toucher ; la règle est contournable par `uv run python -c` | Pas de verrou imposé ; `git diff -- tests/` dans le contrôle rapide |
| T5 | Critique d'une autre famille, porte empirique (7 stories, défauts réels) | 0 défaut manqué retrouvé sur 5 ; 23 tests Important sur 23 échouent bien, 48 % déjà tranchés par la chaîne | Porte empirique : idée à garder, pas un filtre |
| T5 élargi | Rappel sur 16 défauts semés, 20 stories, 4 dépôts | Haiku 11, Opus 11 (les mêmes), gpt-6.1-sol 11, gpt-6-luna 8 ; chaîne + GPT 12 (+6 points), constats Important ×1,5 | Pas de critique externe |
| T6 | `/advisor` | Conseiller appelé 1 run sur 12 sans consigne (+21 % de coût) ; avec consigne 1,19 $ par story contre 0,53 $ (Sonnet seul) et 1,33 $ (Opus seul), réussite 85 à 89 % partout | Pas d'`/advisor` ; Sonnet pour implémenter, Opus en recours |
| T7 | Skills de design ; navigateur | 0 violation axe dans les 16 pages, aucune skill à −30 % ; frontend-design +1 %, impeccable +16 %, hallmark +21 %. Navigateur : Playwright MCP 6/6, playwright-cli 6/6 (+18 %), agent-browser 5/6 (refus de permission) | frontend-design (sous réserve de la note à l'aveugle) ; Playwright MCP pour le sous-agent de vérification |
| T8 | Modèles locaux | Lookup : Haiku 40/40, qwen3.5:4b 37/40 ; qwen3.6:35b-a3b réussit mais 52 à 78 s avant le premier jeton, RAM saturée | Haiku pour le lookup ; local pour comparer seulement |
| T8 élargi | Juge de commandes shell (600 commandes) | Aucune combinaison n'atteint 0 fuite et < 2 % de faux refus (règle + Haiku : 1 fuite, 10 %) | Règles deny natives et auto mode, pas de juge |
| T9, T9 élargi | Jev et autres modèles pour prédire le dérapage d'une story (226 stories) | AUC 0,61 à 0,65, comme la longueur de la spec | Rien à brancher |
| T10 | Hypothesis contre tests d'exemples (75 survivants de mutation) | Exemples 53 %, Hypothesis 45 %, coût égal | Rien à ajouter ; demander explicitement le renforcement des tests |
| T10b | Mutation guidée : survivants montrés à l'agent | 134/134 non équivalents tués (59 % sans les montrer), 0,22 $ par story, 35 équivalents sur 35 bien reconnus | Étape optionnelle de revue : mutation puis tests écrits par un agent |

**Ce que les tests changent aux recommandations de la section 6.**
- **Confirmé** : Sonnet pour implémenter, Opus en recours (T6) ; le contexte fixe est le premier poste (T1) ; les outils de compression ne valent rien sur ce profil (T1) ; aucun outil tiers de navigateur ou de design ne bat l'option la plus simple (T7) ; le local ne remplace pas Haiku (T8).
- **Renversé** : la protection des tests par phase (6.3) n'est pas nécessaire sur Claude 5.5 (T4 bis) ; le second avis d'une autre famille (6.3) n'apporte pas assez (T5, T5 élargi) ; la porte empirique (6.3) ne filtre rien (T5) ; `/advisor` (T6) ; le property-based testing (constat 3 du résumé) n'aide pas un agent à mieux tester que des exemples (T10).
- **Nouveau** : la mutation n'est pas seulement un diagnostic, elle sert de consigne : montrer les survivants à l'agent bouche tous les trous non équivalents pour quelques centimes (T10b). C'est le gain le plus net de la série.
- **Reste ouvert** : la note à l'aveugle du design (T7) ; les prédictions de dérapage (T9, il faudrait ~480 stories) ; voir la partie « Après les tests » de la page HTML pour le bilan outil par outil.

## 8. Questions ouvertes

- **Les chiffres sur la triche et les mocks valent-ils pour Claude 5.5 ?** Les études portent sur des modèles de 2025 {verif:B2,B3}. T4 y répond sur tes stories.
- **Un critique d'une autre famille trouve-t-il des défauts qu'Opus manque ?** Aucune mesure contrôlée {verif:B4}. T5.
- **Les gains de `/advisor` tiennent-ils sur les modèles 5.5 ?** {couts:C14}. T6.
- **Que dit le Thoughtworks Radar vol. 35 ?** Attendu début novembre 2026 : premier contrôle de la veille continue.
- **Productivité réelle** : non tranchée par la recherche {verif:C4} ; seule la mesure sur tes propres projets (coût, défauts, temps humain) peut trancher pour toi.
- **Code produit sous Max et livré à un client** : quelles garanties de propriété intellectuelle ? Les Consumer Terms n'ont pas été lus ; avant une mission, vérifier ou passer par une offre commerciale (API, Team, Enterprise) {tour2:A8,A9}.
- **BCG, Accenture, Capgemini, Deloitte** : aucune publication publique trouvée sur les agents de code en 2026.

## 9. Preuves contraires

Le passage « red team » (recherche délibérée de preuves contraires sur chaque conclusion majeure) n'a pas été lancé à ce stade (validation « normal »). Les vérifications ont toutefois renversé ou nuancé trois idées reçues de départ : l'avantage de tokens des CLI sur les MCP {verif:B1}, l'effondrement des skills en grand nombre {verif:C6}, et le gain des skills de design {verif:C1}. Un passage red team sur la recommandation finale est proposé après les tests.

## 10. Sources

<!-- ANNEXE -->

## 11. Carte de péremption

Calculée par `recon_kit.py staleness` sur les 21 affirmations du registre (`claims.json`, `staleness.json`). Fenêtres en mois : versions et comportement de Claude Code 1, prix 3, paysage 3, performance 6, sécurité 6, résultats empiriques 6 (domaine IA).

| À revoir | Affirmations | Pourquoi |
|---|---|---|
| **Déjà dépassé** (6) | B2 triche aux tests, B3 mocks, B4 précision des revues, C2 critique visuelle, C3 Radar vol. 34, C4 METR et essai d'Anthropic | Résultats publiés il y a plus de 6 mois (ou 3 pour le Radar) ; les modèles ont changé depuis. Le vol. 35 du Radar et les tests T4 et T5 les remplacent. |
| **2026-11-01** | A4 budget des skills, A5 TTL du cache, A6 passerelles et abonnement, A7 en-têtes de passerelle, C7 OpenTelemetry | Comportement de Claude Code, qui change à chaque version : à recontrôler chaque mois contre le changelog. |
| 2026-12-01 | C6 SkillsBench | Nouvelle version du benchmark probable. |
| 2027-01 à 2027-04 | B1, B5, B6, A3, B7, C1, A1, A2, C5 | Mesures et prix récents. |

Premier contrôle : **2026-11-01**, à faire avec la parution du Radar vol. 35.
