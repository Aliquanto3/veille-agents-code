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
updated: '2026-10-24'
claims: 'registre : 21 affirmations porteuses, 15 verified, 4 unverified, 2 disputed, 0 overturned (recon_kit tally)'
---

# Veille : outils, plugins et pratiques des agents de code (octobre 2026)

**Décision servie :** quelle configuration Claude Code adopter pour la conception, le front, le back, les tests, les coûts et le confort d'usage, sur un poste Windows avec un abonnement Max, la méthode BMAD et le plugin maison agent-cost-kit ; et quelle base donner à une veille continue.

## Résumé exécutif

**Ce que disent les preuves.** En 2026, ce qui fait la différence n'est plus le modèle ni le nombre d'outils installés, c'est le **cadrage de l'agent** : un contexte court, des contrôles automatiques qui jugent son travail, et une validation tôt dans la story. Le Thoughtworks Radar d'avril 2026 met le *context engineering* en Adopt et les fichiers d'instructions qui enflent en Caution {verif:C3}. La recherche situe les échecs des agents dans leurs premières étapes, invisibles jusqu'à être irrécupérables {litt:A1}, et la qualité ne s'obtient pas par le prompt mais par l'outillage et la revue {litt:A19,A21}.

**Les trois constats qui pilotent la recommandation.**
1. **Le natif couvre déjà l'essentiel de la liste.** Mémoire, orchestration parallèle, routage par modèle, revue, navigateur, mesure des coûts : pour chaque catégorie, Claude Code a une fonction native ou un plugin officiel au moins équivalent pour un développeur seul {doc:sub-agents}{orch:A1,A3}{contexte:N1}. Sur les 47 dépôts, aucun n'est « strictement meilleur » que son équivalent natif dans la configuration étudiée : 1 est à adopter (en partie), 13 à essayer, 15 à évaluer, 10 à écarter et 8 hors périmètre (tableau en section 2).
2. **Le coût caché, c'est le contexte fixe et le cache, pas la sortie.** L'écriture du cache pèse 42 à 44 % de la dépense, et compresser les sorties de commandes n'économise que 0,5 à 2,7 % {verif:A3}. Le seul gain mesuré sérieusement vient du retrait des outils et du contexte inutiles : −18 à −31 % {verif:A2}. Les gros packs de skills vont dans le mauvais sens : ECC ajoute ~131 k caractères de contexte fixe {methode:M1}, et la liste des skills est plafonnée à 1 % de la fenêtre, au-delà de quoi des descriptions disparaissent {verif:A4}.
3. **Les preuves d'efficacité des plugins sont faibles.** Les skills de méthode et de design ne sont évaluées que par leurs auteurs ; le seul test « en aveugle » publié pour une skill de design tombe dans le bruit (7,7 avec, 7,8 sans) {verif:C1}. À l'inverse, les contrôles déterministes ont des preuves : tests en lecture seule contre la triche {verif:B2}, mutation testing contre les tests faibles {tests:A16,A17}, détecteurs exécutés sur la page rendue {design:A2}.

**Recommandation.** Garder BMAD et agent-cost-kit comme colonne vertébrale, ne pas installer de pack de méthode concurrent, et investir dans des **contrôles automatiques** plutôt que dans des consignes : protection des tests, porte empirique en revue, boucle de vérification du front, mesure du contexte fixe. Six réglages sont sans regret et applicables tout de suite ; huit hypothèses demandent un test pratique avant décision (section 6).

**Principale réserve.** Presque toutes les études sont des préprints d'un seul laboratoire, et plusieurs chiffres portent sur des modèles de 2025 : chez Claude 5.5, un audit d'octobre 2026 ne voit presque plus de triche aux tests {verif:B2}. D'où l'importance des tests pratiques sur tes propres stories.

## 1. Méthode et limites

- **Corpus.** 50 ressources recommandées (47 dépôts GitHub après retrait de 3 doublons, 6 articles ou pages). Métadonnées relues par `gh api` le 2026-10-24 (`data/depots.json`).
- **Recherche.** 10 dimensions confiées à des chercheurs Opus en parallèle (3 tours au plus, 25 appels web chacun), plus un inventaire des fonctions natives depuis la documentation officielle, puis un tour 2 sur les trous. Chaque affirmation porte sa source ; 21 affirmations porteuses ont été revérifiées par des agents au contexte vierge : 15 confirmées, 4 non vérifiées faute de source indépendante (mais conformes à leur source primaire), 2 contestées et corrigées ici.
- **Limites.** Reddit est inaccessible aux outils ; ses retours ne passent que par la presse ou les issues GitHub. L'article Medium comparant Superpowers, agent-skills, Pocock et ECC est derrière un paywall (non lu). Aucun outil n'a encore été exécuté : les verdicts « Essayer » et « Évaluer » attendent les tests de la section 6. Le Thoughtworks Radar vol. 35 n'est pas encore paru (attendu début novembre 2026) {verif:C3}.

## 2. Les 47 dépôts, regroupés par problématique

Verdicts pour la configuration étudiée (Windows, Max, BMAD, FastAPI + Jinja2 + HTML/CSS/JS vanilla). **Adopter** : à installer ou appliquer tel quel. **Essayer** : test court avant adoption. **Évaluer** : intérêt possible, preuves insuffisantes. **Écarter** : moins bon que l'existant ou risqué. **Hors périmètre** : pas un outil d'agent de code pour cette configuration.

| Problématique | Outil | Verdict | Doublon ou équivalent natif | Pourquoi |
|---|---|---|---|---|
| Méthode | obra/superpowers | Évaluer | BMAD ; plan mode, `feature-dev` | Revendique les mêmes étapes que BMAD, règle « 1 % de chance → invoquer » {verif:C6}, gains auto-mesurés, plaintes de lenteur {methode:U1,U2,U3} |
| Méthode | mattpocock/skills | Essayer, à la carte | — | Skills manuelles sans conflit (`grill-with-docs`, `diagnosing-bugs`), 2,3 k caractères {methode:M1} |
| Méthode | addyosmani/agent-skills | Évaluer | BMAD | Méta-routeur concurrent de BMAD, ~11 k caractères {methode:M1} |
| Méthode | affaan-m/ECC | Écarter | — | ~131 k caractères de contexte fixe, 311 skills : dépasse le budget de la liste d'un ordre de grandeur {methode:M1} |
| Méthode | multica-ai/andrej-karpathy-skills | Essayer (4 principes dans CLAUDE.md, sans plugin) | — | 0,2 à 2,4 k caractères ; dépôt inactif depuis avril |
| Méthode | liza-mas/liza | Évaluer (lecture seulement) | dev-story → second-avis → reviewer | Même idée que la chaîne maison, rendue mécanique ; WSL2, contrat de ~54 k caractères {methode:M1}{orch:A25} |
| Méthode | deepakkamboj/developer-assistant-skills | Écarter | BMAD | 1 étoile, ~15 k caractères |
| Méthode | spotify/portal-ai-plugins | Hors périmètre | — | Lié à Spotify Portal (Backstage) |
| Méthode | anthropics/skills | Adopter `skill-creator` seulement | officiel | Bench avec et sans skill pour mesurer les skills maison {methode:D1} |
| Design front | pbakaus/impeccable | Essayer (sans hooks ni télémétrie) | `frontend-design` (officiel) | Seul détecteur déterministe sur URL rendue (62 règles), donc compatible Jinja ; télémétrie par défaut {design:A1,A2} |
| Design front | Leonxlnx/taste-skill | Évaluer | — | Landing pages seulement ; centaines de milliers de tokens par page ; gain dans le bruit {verif:C1} |
| Design front | Nutlope/hallmark | Évaluer | — | Ne se déclenche pas sans être nommé (0/12), sous-agent imbriqué, bloque 30 % des essais non interactifs {verif:C1} |
| Design front | nextlevelbuilder/ui-ux-pro-max-skill | Écarter | — | Tailwind par défaut, publication npm cassée depuis août |
| Design front | google-labs-code/design.md | Essayer | Claude Design | Contrat commun lu ou écrit par les autres skills ; format en alpha {verif:C2}{design:A11} |
| Design front | VoltAgent/awesome-design-md | Évaluer (exemples du format) | — | Collection de DESIGN.md de marques |
| Design front | nexu-io/open-design | Hors périmètre | Claude Design (inclus dans Max) {design:A22} | Espace de design complet, doublon du natif |
| Design front | emilkowalski/skills | Essayer, sélectivement | — | Règles d'animation et de performance CSS utiles en vanilla |
| Design front | greensock/gsap-skills | Hors périmètre | — | Utile seulement si GSAP est adopté |
| Design front | DavidHDev/react-bits, DavidHDev/canvas-ui, oso95/scroll-world | Écarter | — | Liés à React / shadcn / WebGL |
| Contexte, mémoire | thedotmack/claude-mem | Écarter | mémoire automatique native | 9 types de hooks dont un PreToolUse synchrone, faille corrigée en septembre, aucun gain mesuré {verif:B7}{contexte:C1} |
| Contexte, mémoire | Graphify-Labs/graphify | Évaluer (mode code seul, à la demande) | grep + LSP + Explore | Seul banc : 6 questions, comparé à grep et jamais au LSP {contexte:G1,G3,G5} |
| Contexte, mémoire | elstongun/leviathan | Hors périmètre | — | Index de jeux d'enregistrements ; 19 jours, un contributeur {contexte:L1} |
| Diagrammes | tt-a1i/archify | Évaluer | Mermaid | Fidélité au code non prouvée ; contacte son serveur toutes les 24 h {contexte:A2} |
| Diagrammes | cathrynlavery/diagram-design | Essayer (livrables client) | Mermaid pour la doc versionnée | Se dit lui-même moins adapté que Mermaid à la doc versionnée {contexte:D1} |
| Coûts | microsoft/TokenEconomizer | Évaluer ; reprendre son idée | — | Meilleures preuves de la liste (−18 à −31 %), mais pas de Windows natif {verif:A2} |
| Coûts | alexei-led/claude-router | Écarter | `/advisor`, effort, modèle des sous-agents | Aucune économie mesurée, de l'aveu de l'auteur ; prompts envoyés à un classifieur tiers {couts:C10,C11} |
| Coûts, sobriété | Institut-du-Numerique-Responsable/green-claude | Évaluer (audit d'écoconception à la demande) | — | Ne mesure rien, ajoute ~15,8 k caractères et des hooks {couts:C12,C13} |
| Routage | BerriAI/litellm | Évaluer | endpoint Anthropic natif d'Ollama / LM Studio | Utile seulement pour mêler cloud et local facturés à l'API ; paquets PyPI compromis en mars 2026 {routage:A17} |
| Routage | felipevicens/aaif-labs (agentgateway) | Hors périmètre ; agentgateway : Évaluer | Claude apps gateway | Le dépôt est un lab K8s personnel ; agentgateway (AAIF, Apache-2.0, binaire Windows) est la piste pour conseiller des clients {routage:A20,A21,A22} |
| Routage | theroyallab/tabbyAPI | Écarter | Ollama, llama.cpp | Pas d'endpoint Anthropic, GPU NVIDIA requis, AGPL {routage:A24} |
| Modèles locaux | AlexsJones/llmfit | Essayer (présélection) | — | Estimations optimistes sur matériel modeste ; ne pas installer sa skill (faite pour OpenClaw) |
| Revue | alibaba/open-code-review | Essayer (en délégation) | `/code-review` | Déterministe + LLM, ~15× moins de tokens selon l'éditeur, contredit par une reproduction sur 10 PR {revue:A16,A17} |
| Sécurité | cloudflare/security-audit-skill | Évaluer (sous WSL) | `/security-review`, ultrareview | Meilleure méthode (vérificateur frais qui tente de réfuter), mais validateurs cassés sous Windows natif {revue:A22,A23} |
| Sécurité des skills | NVIDIA/SkillSpector | Essayer (`--no-llm`, avant installation) | — | Aucun taux de détection publié ; tous les scanners testés ont été contournés {verif:B6} |
| Tests | microsoft/playwright-cli | Essayer (vérification headless) | Claude in Chrome, Playwright MCP | Plus d'écart de tokens notable avec le MCP {verif:B1} ; génère des tests TypeScript hors de pytest {tests:A1} |
| Orchestration | paperclipai/paperclip | Écarter | agent view | « Entreprise d'agents » hors méthode supervisée ; blocages silencieux, bugs Windows, télémétrie ; 106 k étoiles pour très peu de discussions {orch:A6,A7,A8,A9} |
| Orchestration | stablyai/orca | Évaluer | agent view | Multi-fournisseurs, annotation de diffs, Design Mode ; usage réel attesté {orch:A10,A11,A12} |
| Orchestration | SmythOS/smythos-studio | Hors périmètre | — | Constructeur d'agents visuel, dormant {orch:A28} |
| Expérience | ayghri/i-have-adhd | Évaluer (essayer d'abord le style natif Concise) | output style Concise | Régression en débogage : pousse à affirmer une cause sans preuve {orch:A19,A20} |
| Rédaction | blader/humanizer | Essayer (rédaction seulement) | — | Préféré en aveugle (16/16, petit échantillon), mais les détecteurs le repèrent toujours {orch:A22,A23} |
| Veille, données web | firecrawl/firecrawl | Essayer (veille, service hébergé) | WebFetch | WebFetch échoue sur les pages rendues en JavaScript ; cœur sous AGPL {tour2:A29,A30} |
| Veille, données web | apify/apify-mcp-server | Évaluer | WebFetch, WebSearch | Télémétrie par défaut, paiements par l'agent à interdire |
| Données | public-apis/public-apis | Hors périmètre | — | Annuaire d'API |
| Marketing | every-app/open-seo | Hors périmètre | — | Utile seulement en mission SEO |
| Démonstrations | heygen-com/hyperframes | Essayer (vidéos de démo) | — | Vidéo à partir de HTML, comme ta pile ; Windows non vérifié {tour2:A31} |

Articles et pages de la liste : la page **advisor** décrit une fonction native à essayer {couts:C14} ; l'article d'Anthropic sur **sa revue de code** donne des règles de convergence à adopter {revue:A1,A2} ; le billet **MLflow** confirme que l'OpenTelemetry natif suffit pour tracer {orch:A16} ; **agent-standup** est trop jeune pour conclure ; le billet **RTK** mesure un gain marginal {verif:A3} ; l'article **Medium** n'a pas pu être lu.

## 3. Constats par problématique

### 3.1 Méthode de développement
- Trois philosophies : pipeline imposé (Superpowers, Liza, ECC), boîte à outils à la carte (Pocock, Karpathy), cycle complet routé par une méta-skill (addy, deepakkamboj) {methode:M3,M4}. Superpowers, addy et BMAD revendiquent les mêmes étapes : en faire tourner deux comme routeurs automatiques crée deux sources de vérité. Seules les skills **manuelles** (`disable-model-invocation`) s'ajoutent à BMAD sans conflit {methode:D1}.
- Aucun banc indépendant ne compare ces méthodes. Les skills curées aident (+11,6 points en génie logiciel dans SkillsBench v4), celles générées par le modèle font **moins bien** que rien ; multiplier les skills disponibles ne fait pas chuter la réussite, mais rend leur usage imprécis {verif:C6}.
- Natif : plan mode, `/goal`, hook Stop, `/code-review`, plugins officiels `feature-dev` et `skill-creator` {methode:D2,D3}.
- **Face à tes projets** : BMAD + agent-cost-kit couvre déjà toutes les étapes, avec des mesures (1,18 à 1,60 $ par story contre 6,77 à 7,31 $ avec l'ancien setup). Aucun pack n'a de raison de le remplacer.

### 3.2 Design et front
- Aucune skill anti-« AI slop » n'est strictement meilleure ; chacune gagne dans un cas (tableau de la section 2). Leur point faible commun est l'**activation** : sans être nommées, elles ne se déclenchent pas, et leurs fichiers de règles ne sont pas lus {verif:C1}. Dans un sous-agent `dev-story`, il faut donc nommer la skill dans le prompt.
- Ce qui a des preuves : la vérification **sur la page rendue** (détecteurs déterministes, puis critique visuelle sur capture, jusqu'à +17,8 % en 3 cycles) {design:A2,A10}{verif:C2}.
- Trous : aucune skill ne lit les templates Jinja (il faut passer par l'URL rendue), aucune n'intègre un audit d'accessibilité sémantique (axe), aucune ne traite la sobriété {design:A34,A8}.
- Natif ou officiel : skill `frontend-design`, plugins `playwright`, `chrome-devtools-mcp` et `modern-web-guidance` (Google Chrome, utile pour les API HTML/CSS natives), Claude in Chrome, Claude Design {design:A20,A21,A22,A23}.

### 3.3 Contexte, mémoire, compréhension du code
- Le natif suffit : CLAUDE.md court et règles par chemin chargées à la demande, mémoire automatique (index de 200 lignes ou 25 Ko), `/doctor prompt-audit`, sous-agent Explore, LSP, et coût de contexte affiché par plugin {contexte:N1,N2}.
- Les résumés en langage naturel restituent mal le comportement du code (4 questions sur 45, contre 27 avec le code source) : un argument contre les mémoires « résumées » {contexte:R4}. L'empoisonnement de mémoire est démontré, y compris sur le MEMORY.md de Claude Code {contexte:R6,R7}.
- **Face à tes projets** : ta mémoire automatique et ton `MEMORY.md` court suivent déjà la bonne pratique ; aucun outil ne traite la péremption des mémoires.

### 3.4 Coûts et tokens
- Postes de coût : écriture du cache 42 à 44 %, lecture 35 à 38 %, sortie 10 à 29 % selon les mesures {verif:A3}, ce que confirment tes propres mesures (39 à 42 / 38 à 40 / 19 à 21 %).
- Leviers natifs : TTL du cache des sous-agents (5 min par défaut, même sur abonnement) {verif:A5}, éviter tout changement de modèle en cours de session (`opusplan` en est un) {couts:C17}, `/clear` plutôt que `/compact` {couts:C18}, réduire la liste des skills et les outils jamais appelés {verif:A4,A2}, filtrer les sorties de tests par hook {couts:C20}.
- `/advisor` (Opus conseille un exécutant moins cher) : +2,7 points et −11,9 % de coût sur des modèles 4.6, non mesuré sur les 5.5 {couts:C14,C15}.
- Empreinte : rien n'est mesuré pour un modèle fermé ; EcoLogits ne compte que les tokens de sortie {couts:C21,C22}. agent-cost-kit hérite de cette limite.
- **Face à tes projets** : agent-cost-kit couvre déjà la mesure, l'estimation EcoLogits et la règle du TTL ; il lui manque la mesure du **contexte fixe** (skills, hooks, outils) et une règle sur le retrait des outils inutilisés.

### 3.5 Routage cloud / local
- Claude Code se branche sur tout serveur au format Anthropic Messages via `ANTHROPIC_BASE_URL`, mais Anthropic ne prend pas en charge les modèles non-Claude {routage:A1}. Ollama, LM Studio et llama.cpp exposent nativement `/v1/messages` : pas besoin de passerelle pour le local {routage:A10,A12,A13}. Ollama n'a ni cache de prompt ni `count_tokens` {verif:A6}.
- Une passerelle avec sa propre clé **fait sortir de l'abonnement Max** (facturation au token) ; `ANTHROPIC_BASE_URL` seul le conserve {verif:A6}.
- Une requête Claude Code pèse ~29 k tokens, surtout des définitions d'outils (une mesure de blog) {routage:A31} : un modèle ≤ 4B sur CPU ne peut pas servir de moteur à Claude Code ; il reste utile en appel direct (lookup, résumé). Les MoE à ~3 B actifs (Qwen3.6-35B-A3B, que tu as) sont la classe crédible {routage:A33}.
- Les en-têtes d'indice de passerelle (v2.1.273+) permettent de router et d'attribuer les coûts par sous-agent ; ils sont désactivés par défaut sur une URL personnalisée {verif:A7}.
- **Face à tes projets** : slm-quality-bench et wavelocalai appellent Ollama directement ; c'est la bonne voie pour les SLM. La comparaison cloud / local « en situation d'agent » demande un protocole dédié (section 6, après ton benchmark).

### 3.6 Revue de code et sécurité
- Anthropic ne publie pour sa revue ni taux de faux positifs ni coût ; ce qui se transpose à un dev solo, ce sont ses **règles de convergence** : 3 passes au plus, ne relire que le nouveau diff, constats étiquetés Important / Nit / Pre-existing {revue:A1,A2}.
- Sur Max, le service Code Review (GitHub) est inaccessible ; restent `/code-review`, `/code-review ultra` (3 essais gratuits puis 5 à 25 $) et `/security-review` {verif:B5}.
- La précision des revues par LLM reste basse (5,6 à 39,9 % selon les modèles, une étude) ; l'accord de plusieurs relecteurs ne prouve rien, un test si {verif:B4}. Ta chaîne Sonnet → Haiku → Opus reste dans une seule famille de modèles ; l'apport d'un critique d'une autre famille est une hypothèse, pas une mesure {verif:B4}.
- Chaîne d'approvisionnement : les scanners de skills ont tous été contournés {verif:B6} ; lire une skill avant de l'installer reste indispensable. Le sandbox natif exige WSL2 sous Windows {doc:sandboxing}.

### 3.7 Tests et vérification
- Navigateurs pour agents : plus d'écart de tokens notable entre playwright-cli et Playwright MCP {verif:B1}. Claude in Chrome pour la vérification interactive (pas en CI), une CLI headless pour les runs autonomes ; agent-browser est le seul à intégrer diff visuel et audit d'accessibilité {tests:A7,A26}.
- Triche aux tests : chez les modèles de 2025, elle passait surtout par la modification des tests, que des tests en lecture seule bloquent {verif:B2}. Règle native `deny Edit(tests/**)` (ne couvre pas un script Python qui écrit le fichier) {tests:A12}.
- Tests faibles : 36 % des commits d'agents ajoutent des mocks contre 26 % des commits non-agents {verif:B3} ; les tests jetables (`print`) coûtent jusqu'à 49 % de tokens d'entrée pour ~2 points de résolution {tests:A14}. Parades étayées : mutation testing (cosmic-ray tourne nativement sous Windows, mutmut exige WSL) {tests:A16,A17,A19}, property-based testing {tests:A20}, couverture différentielle en CI {tests:A21}.
- Playwright Python n'a pas de comparaison de captures et ne l'aura pas ; il a les snapshots ARIA {tests:A23,A24}.

### 3.8 Orchestration, observabilité, expérience
- Natif : agent view (sessions en arrière-plan, worktree par session, notifications), dynamic workflows, `/batch`, agent teams (expérimental, sans reprise après `/resume`, sans panneaux dans Windows Terminal) {orch:A1,A2,A3}.
- OpenTelemetry natif : coût et tokens par agent (`agent_id`, `parent_agent_id`, `workflow.run_id`) ; le tracing de base est en bêta, seule sa version détaillée demande une liste blanche en CLI interactive {verif:C7}. Il pourrait remplacer une partie de l'analyse des transcriptions d'agent-cost-kit.
- Lisibilité : le style natif **Concise** recouvre l'essentiel d'i-have-adhd {orch:A19}.

### 3.9 Capacités voisines
Pas des outils d'agent de code, mais utiles à la veille et aux démonstrateurs.
- **firecrawl** : Essayer pour la veille, en service hébergé (le cœur est sous AGPL). WebFetch natif convertit en Markdown avec perte et échoue sur les pages rendues en JavaScript {tour2:A28,A29,A30}.
- **apify-mcp-server** : Évaluer ; télémétrie par défaut, et paiements par l'agent à interdire.
- **public-apis** : Hors périmètre (annuaire). **open-seo** : Hors périmètre, sauf mission SEO.
- **hyperframes** : Essayer pour les vidéos de démo de tes applications, car il part de HTML, comme ta pile ; environ 3 min de rendu pour 30 s en 1080p, Windows non vérifié {tour2:A31}.

**Voix des analystes et des autres outils.** Gartner conseille de ne pas confier toutes les tâches aux agents et met la gouvernance de tout le cycle de développement au premier plan {tour2:A3} ; Forrester juge le code produit « souvent problématique » {tour2:A5}. Les plaintes vues pour Claude Code sont transverses : quotas opaques chez Codex, Copilot (facturé au token depuis le 2026-06-01) et Cursor {tour2:A16,A18,A20}, question tranchée d'office après 60 s dans Claude Code et Codex {tour2:A17}.

## 4. Problématiques que rien ne traite bien

| Problème | Ce qui existe | Source |
|---|---|---|
| Évaluer sa configuration d'agent dans le temps | `claude plugin eval`, `skill-creator`, `/skill-doctor` pour une skill ; rien pour une configuration entière | {prat:R2}{doc:plugin-evals} |
| Charge de l'humain qui relit | Agent view regroupe ce qui est prêt ; span `blocked_on_user` en traces bêta ; rien ne régule | {orch:A3}{verif:C7} |
| Tests trichés ou faibles, mesurés à chaque story | Mutation testing trop lent tel quel ; détection de triche à 42–65 % | {tests:A10,A17} |
| Robustesse du relecteur à l'injection de prompt | `/security-review` non durci ; aucun outil ne mesure la sienne | {revue:A12,A13} |
| Contrôle à l'exécution des skills tierces | Scanners statiques contournés ; rien de prêt sous Windows | {verif:B6} |
| Péremption et empoisonnement de la mémoire | Rappel à élaguer dans la doc ; rien ne lie une mémoire à sa source | {contexte:R6,R7} |
| Garder l'abonnement Max en routant une partie vers le local | Non documenté | {verif:A6} |
| Empreinte réelle d'un modèle fermé | Estimations sur les seuls tokens de sortie | {couts:C21} |
| Accessibilité sémantique et sobriété du front généré | Aucune skill n'intègre axe ; aucune ne vise la sobriété | {design:A34} |
| Traçabilité exigences → code et attribution du code IA, licences | Git AI, Agent Trace en Assess ; voir tour 2 | {prat:R2}{tour2:A12,A13} |
| Propriété intellectuelle du code livré à un client | L'indemnisation d'Anthropic figure dans les Commercial Terms (API, Team, Enterprise), pas dans les Consumer Terms qui couvrent Max ; elle exclut le code modifié ou combiné | {tour2:A8,A9} |
| Évaluer une configuration complète | `claude plugin eval` exécute sans CLAUDE.md, réglages, hooks ni autres plugins | {tour2:A25} |
| Conflits sémantiques entre stories parallèles | Isolement par worktree seulement | {orch:A12} |
| Coût des reprises après pause (cache expiré) | Rien ; un praticien attribue 55 % de ses écritures de cache aux reprises après une heure | {prat:R13} |

## 5. Enseignements transverses

1. **Du prompt vers le contrôle.** Les dimensions méthode, tests, revue et design convergent : les consignes (skills, CLAUDE.md, prompts de sécurité) ont un effet faible ou non mesuré {litt:A21}{verif:C1}, les contrôles déterministes ont des preuves {verif:B2}{tests:A16}{design:A2}. Le Radar fait la même lecture : « feedback sensors » en Trial, « instruction bloat » en Caution {verif:C3}.
2. **Le contexte fixe est un coût et un risque.** Chaque skill, hook ou plugin installé est relu à chaque appel, consomme le budget de la liste des skills, et élargit la surface d'attaque {verif:A4,B6}. La meilleure économie mesurée vient du retrait {verif:A2}. Corollaire : le critère d'entrée d'un outil dans ta configuration doit inclure son coût de contexte, mesuré.
3. **Le natif rattrape les plugins en 6 mois.** Mémoire, orchestration, navigateur, design system, évaluations de plugins : la plupart des fonctions vendues par les dépôts les plus étoilés de la liste ont un équivalent natif apparu en 2026. Pour la veille, un changelog Claude Code vaut plus qu'un classement d'étoiles.
4. **Les étoiles ne disent rien.** paperclip (106 k étoiles) a très peu de discussions ; TokenEconomizer (223 étoiles) a les meilleures preuves de la liste {orch:A9}{verif:A2}.

## 6. Recommandations

### 6.1 Sans regret, applicables maintenant (confiance haute, réglages réversibles)
1. **Ne pas installer de pack de méthode à côté de BMAD** (Superpowers, addy, ECC, deepakkamboj). Base : conflit d'étapes et coût fixe mesurés {methode:M1,M3}.
2. **Mesurer ton contexte fixe actuel** (`/context`, `/skill-doctor`, `claude plugin details`) avant tout ajout, et faire de ce coût un critère d'entrée. Base : {verif:A4}{contexte:N1}.
3. **Adopter les règles de convergence d'Anthropic dans le reviewer** d'agent-cost-kit : 3 passes au plus, nouveau diff seulement, étiquettes Important / Nit / Pre-existing. Base : {revue:A2} (pratique publiée, non chiffrée).
4. **Ajouter au prompt de `dev-story` une consigne anti-mock et anti-`print`** (pas de mock des modules internes, assertions plutôt que `print`, pas de script de test jetable), plutôt que dans CLAUDE.md, pour ne pas alourdir le contexte de toutes les sessions. Base : {verif:B3}{tests:A14} (études sur des modèles de 2025).
5. **Écarter** claude-mem, claude-router, RTK, paperclip, ui-ux-pro-max, tabbyAPI. Base : section 2.
6. **Avant toute installation d'une skill tierce** : la lire, puis la passer à SkillSpector `--no-llm` ; ne jamais considérer un scan propre comme une preuve. Base : {verif:B6}.

### 6.2 À décider après un test pratique (section 7)
Les huit tests ci-dessous portent les décisions qui restent : CLAUDE.md minimal, protection des tests et mutation testing, porte empirique et critique d'une autre famille en revue, `/advisor`, boucle de vérification front et choix de la skill de design, choix du navigateur, OpenTelemetry natif contre l'analyse des transcriptions, modèles locaux.

### 6.3 À construire en s'inspirant des outils (évolutions d'agent-cost-kit ou nouveaux mods)
| Outil à construire | Inspiré de | Pourquoi le construire plutôt que l'installer |
|---|---|---|
| **Mesure et garde-fou du contexte fixe** : coût par skill, plugin, hook et outil depuis les transcriptions, alerte au-delà d'un seuil, liste des outils jamais appelés | TokenEconomizer, `/skill-doctor` | TokenEconomizer ne tourne pas sous Windows ; le levier est le plus rentable mesuré {verif:A2} |
| **Boucle de vérification du front** pour FastAPI + Jinja : page rendue, captures à 3 largeurs, audit axe, snapshots ARIA, détecteur de motifs | impeccable `detect`, hallmark `sloplint`, agent-browser | Aucune skill ne traite Jinja ni l'accessibilité sémantique {design:A34} |
| **Second avis d'une autre famille** (GPT, Gemini ou Mistral via OpenRouter) | Refute-or-Promote, Cloudflare | Hypothèse à tester ; ta chaîne est mono-famille {verif:B4} |
| **Porte empirique** : un test qui échoue exigé pour tout constat Important | Refute-or-Promote, revue d'Anthropic | Le consensus ne prouve rien, un test si {verif:B4} |
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
