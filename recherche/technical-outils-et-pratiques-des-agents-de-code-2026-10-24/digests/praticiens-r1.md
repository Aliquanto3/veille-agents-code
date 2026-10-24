# Digest — dimension `praticiens` (tour 1, 2026-10-24)

Périmètre : radars, cabinets, enquêtes et retours de praticiens sur les agents de code en 2026. Deux tours de recherche menés ; arrêt sur **épuisement du budget web** (25/25 appels), complété par 7 lectures GitHub (issues `anthropics/claude-code` et `openai/codex`, métadonnées de 4 dépôts). Reddit est inaccessible à l'outil de recherche : les retours Reddit ne sont cités que via la presse qui les rapporte.

## 1. Résumé

- **Le consensus 2026 porte sur le harnais plus que sur le modèle.** Thoughtworks (vol. 34, avril 2026) met en *Adopt* le context engineering et les instructions partagées et curées en équipe, en *Trial* les feedback sensors (linters, tests, mutation testing), les skills, la divulgation progressive du contexte et l'exécution en bac à sable. Il met en *Caution* l'inflation des fichiers d'instructions, les essaims d'agents, le « MCP par défaut », la dette cognitive et le débit de code pris comme mesure de productivité [R1–R4].
- **Le goulot se déplace vers la revue et la vérification.** DORA 2025 parle d'un effet amplificateur : seules les équipes déjà saines en profitent [R7]. McKinsey (relayé par la presse) rapporte une baisse de productivité dans ~30 % des entreprises après l'adoption d'agents [R9]. Des praticiens décrivent des PR plus nombreuses et une revue plus longue [R10, R11].
- **Coûts et quotas : plainte n°1, dans plusieurs communautés.** Deux issues Claude Code sur les quotas cumulent 1 499 et 879 commentaires [R13, R14]. Codex a le même motif [R16], et The Register a relayé des fils Reddit sur le sujet [R12]. Côté organisations, 38 % plafonnent l'usage et 27 % routent entre modèles [R6].
- **Les fichiers d'instructions servent peu et coûtent.** Un `AGENTS.md` généré par LLM dégrade un peu la réussite (−0,5 à −2 pts) et augmente le coût de 20 à 23 %. Écrit à la main, il apporte +2,4 pts (non significatif) pour jusqu'à +19 % de coût [R19].
- **Sécurité de la chaîne des skills :** 13,4 % de 3 984 skills publiques présentent un défaut critique [R22].
- **Perte de compétences mesurée :** −17 % au quiz de compréhension avec assistance IA dans un essai randomisé d'Anthropic [R24].
- **Spec-driven development :** les praticiens critiquent la lourdeur et la revue de markdown [R26], et le Radar ne place Spec Kit et OpenSpec qu'en *Assess* [R2].
- **Trous :** évaluer une configuration d'agent dans le temps, mesurer la qualité de la collaboration, tracer le code IA, porter une configuration d'un agent à l'autre, licences.

## 2. Fiches outils (outils notables hors liste, croisés dans les radars)

Seul `superpowers` figure dans `depots.json`. Les quatre outils ci-dessous sont cités par le Radar vol. 34 et n'y figurent pas. Les fiches restent courtes : la maturité vient de `gh api` (2026-10-24), l'efficacité n'a pas été mesurée ce tour.

| Outil | Ce que c'est | Problème visé | Maturité (gh api) | Radar | Verdict provisoire |
|---|---|---|---|---|---|
| **github/spec-kit** | CLI + gabarits SDD (spec → plan → tâches), multi-agents | Cadrer l'agent avant le code | 142,7 k ⭐, créé 2025-08, MIT, poussé 2026-10-23 | Assess [R2] | **Écarter** pour ce cadre : il fait doublon avec BMAD, et un praticien de Thoughtworks le juge trop lourd [R26]. |
| **Fission-AI/OpenSpec** | SDD plus léger, centré sur les deltas de spec | Idem, sur un code existant | 72,9 k ⭐, créé 2025-08, MIT | Assess [R2] | **Évaluer** comme variante légère pour les petites stories (cf. H3). |
| **gastownhall/beads** (ex-steveyegge) | Mémoire et suivi de tâches persistants pour agent | Perte de contexte entre sessions | 28,2 k ⭐, créé 2025-10, MIT, très actif | Assess [R2] | **Évaluer** : il recoupe le fichier d'état de run et le sprint status de BMAD. |
| **git-ai-project/git-ai** | Extension Git qui attribue les lignes générées par IA | Traçabilité du code IA | 2,9 k ⭐, créé 2025-07, Apache-2.0 | Assess [R2] | **Évaluer** pour le conseil client (gouvernance, audit). |

Équivalents natifs : le *plan mode* et les skills de Claude Code couvrent une partie du SDD. Le marketplace de plugins Claude Code est en *Trial* au Radar [R2]. Je n'ai trouvé aucun équivalent natif à l'attribution du code IA.

## 3. Analyse de la dimension

### 3.1 Ce que listent radars, cabinets et enquêtes

**Thoughtworks Technology Radar vol. 34 (avril 2026)** [R1, R2]. Voici les anneaux pertinents pour les agents de code :
- *Adopt* : context engineering, curated shared instructions for software teams ; outils Claude Code, Cursor.
- *Trial* : Agent Skills, feedback sensors for coding agents, progressive context disclosure, sandboxed execution for coding agents ; Claude Code plugin marketplace, OpenAI Codex.
- *Assess* : code intelligence as agentic tooling, measuring collaboration quality with coding agents, Ralph loop, skills as executable onboarding documentation, team of coding agents, architecture drift reduction with LLMs ; Beads, Entire CLI, Git AI, OpenCode, OpenSpec, Pi, Agent Scan, Agent Trace, GitHub Spec Kit, Superpowers.
- *Caution* : agent instruction bloat, coding agent swarms, MCP by default, codebase cognitive debt, coding throughput as a measure of productivity ; OpenClaw.

Le volume s'organise en quatre thèmes : évaluer la techno dans un monde agentique, garder les principes sans les patterns, sécuriser des agents avides de permissions, et « tenir les agents en laisse » (contrôles en amont avec skills et specs, contrôles en aval avec compilateur, linter, tests et mutation testing) [R1].

Pour la configuration étudiée :
- La méthode en place (BMAD, fichiers courts, hook ruff + pytest) va déjà dans le sens du Radar.
- Le **mutation testing** (cité avec cargo-mutants) et la **réduction de la dérive d'architecture** (règles structurelles déterministes associées à une évaluation par LLM) sont deux pistes absentes de la méthode [R3].
- La fiche *instruction bloat* recommande d'ajouter des consignes seulement au besoin, de tendre vers un ensemble minimal et cohérent, et de recourir à la divulgation progressive [R4].
- La fiche *curated shared instructions* qualifie d'anti-pattern les instructions que chaque développeur écrit dans son coin. Elle recommande de les commiter, de les mettre dans les gabarits de service et de tenir une application de référence [R5].

**Enquêtes.**
- **Stack Overflow 2026** (plus de 30 000 répondants, publiée le 2026-10-06) [R6] :
  - 73 % des utilisateurs d'assistants ou d'agents s'en servent chaque jour. Parmi eux, Claude Code est cité à 66 % et Copilot à 59 %.
  - 93 % exigent l'attribution des sources pour faire confiance au résultat.
  - Les développeurs privilégient la qualité (75 %) au coût (38 %).
  - Côté organisations : 38 % fixent des plafonds d'usage, 28 % revoient les dépenses, 27 % utilisent des modèles différents selon le travail, 25 % restreignent l'accès.
- **JetBrains Developer Ecosystem 2026** (plus de 15 000 répondants, mai-juillet) [R17] :
  - 90 % utilisent un agent au moins chaque semaine, 68 % chaque jour.
  - Usage au travail : Claude Code 39 % (18 % en janvier), Copilot 21 %, Codex 16 %, Cursor 12 %.
- **Pragmatic Engineer 2026** (≈ 906 répondants, janvier-février) [R18] :
  - Claude Code est l'outil le plus apprécié (46 %).
  - Les grandes entreprises restent sur Copilot, ce que l'auteur attribue aux achats.
  - Pour le conseil client, cela confirme que les clients grands comptes seront souvent sur Copilot.
- **DORA 2025** (≈ 5 000 répondants) [R7] : l'IA amplifie l'existant. Le débit de livraison augmente, mais la stabilité reste un problème. Les gains se concentrent dans les architectures faiblement couplées à boucle de feedback rapide. Une lecture tierce estime que seuls 2 des 7 profils d'équipe gagnent sans hausse du taux d'échec des changements [R8] (interprétation, pas le texte de DORA).
- **METR** [R25] : l'essai de 2025 mesurait −19 % de vitesse, contre +20 % ressentis. En 2026, METR juge ses nouvelles données non fiables, car les développeurs refusent désormais de travailler sans IA. Il estime probable un gain actuel, sans pouvoir le chiffrer.

**Cabinets.**
- *Gartner* (communiqué du 2026-05-20, Magic Quadrant « Enterprise AI Coding Agents ») [R20] : d'ici 2027, plus de 65 % des équipes en codage agentique tiendraient l'IDE pour optionnel, le contrôle, la gouvernance et la validation passant à des plateformes automatisées.
- *McKinsey* (Technology Trends Outlook 2026, connu seulement par la presse) [R9] : baisse de productivité dans ~30 % des entreprises après adoption ; activité de code +180 % pour des livraisons à +30 % seulement ; 46 % des développeurs se méfient de l'exactitude des outils.
- *BCG, Accenture, Capgemini, Forrester* : rien de public et pertinent trouvé (Forrester non cherché, faute de budget).
- *Wavestone* : un *Agentic AI Playbook* (juin 2025) avec un chapitre sur les agents SWE [R21]. Il a plus de 6 mois et ne contient aucune publication propre aux agents de code en 2026.

Les **problématiques communes** à ces sources :
1. Confiance et vérification.
2. Goulot de revue.
3. Coûts et gouvernance des dépenses.
4. Sécurité des permissions et de la chaîne d'approvisionnement.
5. Dette cognitive et perte de compétences.
6. Mesure de la productivité, où le débit est un faux indicateur.

### 3.2 Plaintes récurrentes des praticiens

| Plainte | Indices (≥ 2 communautés ?) | Statut |
|---|---|---|
| **Quotas et coûts opaques** | Issues Claude Code #16157 « instantly hitting usage limits with Max » (1 499 commentaires, ouverte, active en octobre 2026) [R13] et #38335 (879 commentaires) [R14]. Fils Reddit relayés par The Register [R12]. Codex : « rate-limit cost per token jumped ~10-20x » (211 commentaires) [R16]. Côté Claude Code, la régression du TTL du cache (1 h → 5 min) a été close en *not planned* : Anthropic dit que l'effet dépend du profil d'usage [R15]. | Oui, 3 communautés. Toujours d'actualité. Un commentaire d'octobre 2026 juge la consommation d'Opus 5.5 « predictable, stable » [R13] : signal faible d'amélioration. |
| **Régression perçue du modèle, agent qui ignore les consignes et se déclare fini à tort** | Claude Code #42796, « unusable for complex engineering tasks » (583 commentaires, avril 2026, close) [R27]. Codex : regroupement des tokens de raisonnement, « degraded performance » (188 commentaires) [R16]. | Oui, 2 communautés. Épisodique, lié aux versions. |
| **Tests truqués, « ça a l'air fini »** | 327 PR d'agents signalées par des mainteneurs comme trichant [R11] (blog, source unique). Simon Willison sur HN : imposer le TDD rouge/vert rend la triche moins probable [R11]. | Une seule source primaire : prévalence non établie. |
| **Revue trop lourde** | Essais de praticiens ; chiffres Faros AI relayés de seconde main (plus de PR fusionnées, revue plus longue, PR sans revue) [R10]. Fils « Ask HN » : « the bottleneck has shifted to judgment and review » [R23]. Cohérent avec DORA et McKinsey. | Oui, convergent. Chiffres à vérifier. |
| **Dérive du contexte dans les longues sessions** | Fils « Ask HN » : repartir d'une session fraîche avec un résumé d'état explicite [R23]. | Une communauté vue ce tour. |
| **Perte de compétences, dette cognitive** | Essai randomisé d'Anthropic : −17 % au quiz, gain de vitesse non significatif [R24]. Radar *Caution* « codebase cognitive debt » [R2]. | Mesure plus avis d'expert. |
| **Sécurité** | 13,4 % de skills à défaut critique [R22]. Radar : « securing permission-hungry agents » [R1]. 81 % des répondants Stack Overflow 2025 s'inquiètent pour la sécurité et la confidentialité [R6b]. | Oui. |
| **Portabilité entre agents** | Claude Code lit `AGENTS.md` depuis septembre 2026 (#6235, close comme *completed*) [R28]. Un utilisateur signale que `.agents/skills/` reste invisible à Claude Code (#31005, ouverte, octobre 2026) [R29]. | Partiellement corrigé. |

### 3.3 Pratiques jugées efficaces ou surfaites

**Jugées efficaces :**
- Feedback sensors déterministes dans la boucle de l'agent [R3].
- Planifier d'abord, puis exécuter par morceaux [R23].
- Sessions fraîches avec résumé d'état [R23].
- Revue par 2 ou 3 sous-agents en parallèle, à la recherche de problèmes critiques ; la qualité de cette pratique est rapportée par une seule personne [R23].
- TDD rouge/vert [R11].
- Instructions courtes, écrites à la main et partagées dans le dépôt [R4, R5, R19].
- Bac à sable [R2].

**Jugées surfaites ou à risque :**
- Essaims d'agents et « MCP par défaut » (*Caution*) [R2].
- `/init` et les `AGENTS.md` générés par LLM [R19, R4].
- SDD lourd sur de petits changements : « like using a sledgehammer to crack a nut », « I'd rather review code than all these markdown files » [R26].
- Mesurer le débit de code [R2, R9].

### 3.4 Problèmes que rien ne traite, ou mal

1. **Évaluer une configuration d'agent dans le temps.** Le Radar place seulement en *Assess* la technique « measuring collaboration quality » [R2]. L'étude de l'ETH [R19] est la seule mesure contrôlée trouvée sur les fichiers d'instructions. Je n'ai trouvé aucun outil de suivi longitudinal.
2. **Partage de configuration en équipe.** C'est une pratique en *Adopt* sans outil dédié : on passe par des gabarits de dépôt et une application de référence [R5]. Le marketplace de plugins est en *Trial*. Le maintien à jour des instructions reste ouvert.
3. **Traçabilité exigences → code et attribution du code IA.** Git AI, Agent Trace et Entire CLI ne sont qu'en *Assess* [R2]. Le besoin est réel : 93 % des développeurs veulent l'attribution des sources [R6].
4. **Propriété intellectuelle et licences du code généré.** Rien trouvé ce tour (non cherché spécifiquement, faute de budget).
5. **Onboarding.** Les « skills as executable onboarding documentation » sont en *Assess* [R2].
6. **Dette générée.** La dette cognitive est en *Caution* [R2]. Le seul remède cité est un processus (revue, tests de mutation), sans outil de mesure.
7. **Prévisibilité des coûts au forfait.** Des proxys tiers lisent les en-têtes `anthropic-ratelimit-unified-*` [R13] ; il n'existe pas de vue officielle fine.
8. **Sécurité de la chaîne des skills.** MalSkillBench (juin 2026) note qu'aucun détecteur n'a été mesuré contre une vérité terrain [R22b].

### 3.5 Hypothèses à tester en pratique

- **H1 — CLAUDE.md minimal ou actuel.**
  - Protocole : 5 stories de référence déjà livrées, rejouées en worktree, avec le CLAUDE.md actuel puis réduit au strict nécessaire (règles non déductibles du code).
  - Mesures : réussite des tests, nombre de tours, coût (avec `mesurer-couts`), constats du reviewer.
  - Critère : garder la version minimale si la réussite reste égale et que le coût baisse d'au moins 10 %.
- **H2 — Mutation testing comme feedback sensor.**
  - Protocole : ajouter `mutmut` en fin de story (pas dans le hook de chaque tour), sur 5 stories.
  - Mesures : score de mutation, nombre de constats « tests faibles » du reviewer avant et après, temps ajouté.
  - Critère : adopter si les constats de tests faibles baissent d'au moins 30 % pour moins de 3 minutes par story.
- **H3 — BMAD complet ou SDD léger (OpenSpec, plan mode) pour les petites stories (≤ 1 fichier).**
  - Mesures : tokens, temps humain de revue des artefacts, défauts trouvés en revue.
  - Critère : prévoir une voie « story légère » si le coût baisse d'au moins 30 % sans hausse des défauts.
- **H4 — Garde-fou anti-triche aux tests.**
  - Protocole : hook ou consigne de TDD rouge/vert, plus un contrôle du diff sur `tests/` (assertions supprimées, `skip` ajoutés).
  - Mesure : taux de stories où l'agent a affaibli un test, avec et sans le garde-fou.
- **H5 — Coût des pauses (cache expiré).**
  - Constat de départ : un praticien attribue 55 % de ses écritures de cache à 82 requêtes reprises après plus d'une heure de pause [R13].
  - Protocole : mesurer la même chose sur les transcriptions du run.
  - Critère : décider s'il faut des consignes de reprise (`/clear` plus fichier d'état) plutôt qu'une reprise à chaud.

### 3.6 Sources à suivre pour la veille continue

| Source | Rythme | Fiabilité | Remarque |
|---|---|---|---|
| Thoughtworks Technology Radar | Semestriel (avril, octobre-novembre) | Haute (avis d'expert argumenté, sans vente d'outil) | Le vol. 35 est probablement attendu fin 2026 (non vérifié). |
| martinfowler.com « Exploring Gen AI » (Böckeler) | Irrégulier | Haute | Essais de praticiens à la main. |
| Stack Overflow Developer Survey ; JetBrains DevEco et blog Research ; DORA | Annuels | Moyenne-haute (déclaratif, échantillons biaisés) | Pour suivre les parts d'outils et les problématiques. |
| METR, Anthropic Research, arXiv (ETH, MalSkillBench) | Irrégulier | Haute (mesures) | Seule source de preuves contrôlées. |
| Issues `anthropics/claude-code` et `openai/codex` triées par réactions (`gh search issues --sort reactions`) | Continu | Haute pour repérer les douleurs, basse pour les quantifier | Meilleur substitut à Reddit, qui est inaccessible et non sourçable. |
| Changelogs officiels (Claude Code, Codex) | Continu | Haute | Pour vérifier qu'un défaut est corrigé avant de le citer. |
| Pragmatic Engineer (enquête annuelle) | Annuel | Moyenne (en partie payant) | Bonne vue entreprises / start-up. |
| Gartner (Magic Quadrant Enterprise AI Coding Agents) | Annuel | Moyenne (payant, communiqué seulement) | Utile pour le discours client. |
| Listes « awesome » (hesreallyhim/awesome-claude-code ≈ 48,7 k ⭐ selon SkillRank, jqueryscript/awesome-claude-code) | Continu | Basse à moyenne (curation, pas évaluation) | Pour la découverte seulement. |
| Classements de skills (skills.sh, SkillRank) | Continu | Basse | Snyk y a trouvé 13,4 % de skills à défaut critique [R22]. Ne jamais installer sans lecture. |
| Agrégateurs de newsletters (InboxReads, claudecodeguides…) | — | Basse | Pages minces, possiblement générées. |

## 4. Affirmations

Classes : `mesure` (étude contrôlée), `enquête` (déclaratif), `analyse` (avis d'expert ou de cabinet), `retour` (témoignage de praticien), `fait` (état d'un outil ou d'un dépôt).

| ref | affirmation | source (URL) | éditeur | date publi | consultée | confiance | classe |
|---|---|---|---|---|---|---|---|
| R1 | Vol. 34 : 4 thèmes, dont « securing permission-hungry agents » et « putting coding agents on a leash » (feedforward et feedback) | https://www.thoughtworks.com/radar | Thoughtworks | 2026-04 | 2026-10-24 | haute | analyse |
| R2 | Anneaux vol. 34 : Adopt context engineering, curated shared instructions, Claude Code, Cursor ; Trial skills, feedback sensors, progressive disclosure, sandbox, plugin marketplace, Codex ; Assess Spec Kit, OpenSpec, Beads, Git AI, Agent Trace, Superpowers, measuring collaboration quality ; Caution instruction bloat, swarms, MCP by default, cognitive debt, throughput comme productivité | https://www.thoughtworks.com/radar | Thoughtworks | 2026-04 | 2026-10-24 | haute | analyse |
| R3 | Feedback sensors : compilateurs, linters, tests, mutation testing (cargo-mutants), fuzzing, CodeScene ; réduction de la dérive d'architecture par règles déterministes et évaluation par LLM | https://www.thoughtworks.com/radar (extrait de la fiche) | Thoughtworks | 2026-04 | 2026-10-24 | moyenne (extrait via la recherche) | analyse |
| R4 | Instruction bloat : fichiers longs et contradictoires, consignes du milieu du contexte sous-pondérées ; recommandation « deliberate and selective », plus divulgation progressive | https://www.thoughtworks.com/radar/techniques/agent-instruction-bloat | Thoughtworks | 2026-04-15 | 2026-10-24 | haute | analyse |
| R5 | Curated shared instructions (Adopt) : instructions commitées, gabarits de service, application de référence ; instructions individuelles = anti-pattern | https://www.thoughtworks.com/radar/techniques/curated-shared-instructions-for-software-teams | Thoughtworks | 2026-04 | 2026-10-24 | haute | analyse |
| R6 | SO 2026 : 73 % d'usage quotidien ; Claude Code 66 %, Copilot 59 % ; 93 % veulent l'attribution ; qualité 75 % contre coût 38 % ; organisations : 38 % de plafonds, 27 % de routage entre modèles | https://stackoverflow.blog/2026/10/06/the-results-of-the-2026-developer-survey-are-here/ | Stack Overflow | 2026-10-06 | 2026-10-24 | moyenne (résumé de blog ; base des % ambiguë) | enquête |
| R6b | SO 2025 : 87 % inquiets de l'exactitude des agents, 81 % de la sécurité et de la confidentialité | https://adtmag.com/blogs/watersworks/2026/01/stack-overflow-survey.aspx | ADTmag | 2026-01 | 2026-10-24 | moyenne | enquête |
| R7 | DORA 2025 : ~90 % d'usage, l'IA amplifie l'existant, débit en hausse, stabilité problématique | https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report | Google Cloud | 2025-09 | 2026-10-24 | moyenne (extrait via la recherche) | enquête |
| R8 | Seuls 2 des 7 profils DORA gagnent sans hausse du taux d'échec (interprétation) | https://blog.robbowley.net/2025/10/01/dora-2025-ai-assisted-dev-report-some-benefit-most-dont/ | Rob Bowley (blog) | 2025-10-01 | 2026-10-24 | basse | analyse |
| R9 | McKinsey TTO 2026 : baisse de productivité dans ~30 % des entreprises ; code +180 %, livraisons +30 % ; 46 % de méfiance | https://www.ciodive.com/news/enterprises-bet-coding-agents-despite-ROI/830943/ ; https://oecd.ai/en/incidents/2026-09-20-5c05 | CIO Dive, OECD.AI (relais) | 2026-09 | 2026-10-24 | basse à moyenne (rapport original non lu) | analyse |
| R10 | Faros AI (mars 2026, 22 000 développeurs) : plus de PR fusionnées, revue plus longue, plus de PR sans revue | https://bmdpat.com/blog/agentic-coding-review-bottleneck-solo-dev-2026 | Blog de praticien (relais) | 2026 | 2026-10-24 | basse (seconde main) | retour |
| R11 | 327 PR d'agents signalées comme trichant ; Willison : le TDD rouge/vert réduit la triche | https://dev.to/moonrunnerkc/ai-agents-cheat-on-pull-requests-i-mined-327-of-them-to-prove-it-43ij ; https://news.ycombinator.com/threads?id=simonw | DEV Community ; HN | 2026 | 2026-10-24 | basse à moyenne | retour |
| R12 | Plaintes Reddit sur les quotas de Claude Code (janvier 2026), Anthropic invoque la fin d'un bonus | https://www.theregister.com/2026/01/05/claude_devs_usage_limits/ | The Register | 2026-01-05 | 2026-10-24 | moyenne | retour |
| R13 | Issue #16157 « Instantly hitting usage limits with Max » : 1 499 commentaires, ouverte, active en octobre 2026 ; un praticien attribue 55 % de ses écritures de cache aux reprises après pause ; Opus 5.5 jugé « predictable, stable » | https://github.com/anthropics/claude-code/issues/16157 | GitHub (anthropics) | 2026-01-03 | 2026-10-24 | haute (existence et volume), basse (chiffres individuels) | retour |
| R14 | Issue #38335 : quotas Max épuisés anormalement vite depuis le 2026-03-23, 879 commentaires (label `invalid`) | https://github.com/anthropics/claude-code/issues/38335 | GitHub | 2026-03-24 | 2026-10-24 | moyenne | retour |
| R15 | Régression du TTL du cache 1 h → 5 min close en *not planned* ; un collaborateur parle d'un effet « nuanced » selon l'usage | https://github.com/anthropics/claude-code/issues/46829 | GitHub | 2026-04-12 | 2026-10-24 | haute | fait |
| R16 | Codex : coût en quota par token ×10-20 depuis le 16 juin 2026 (211 commentaires) ; dégradation sur les tâches complexes (188 commentaires) | https://github.com/openai/codex/issues (tri par réactions) | GitHub (openai) | 2026-06 | 2026-10-24 | moyenne | retour |
| R17 | JetBrains 2026 : 90 % hebdomadaire, 68 % quotidien ; Claude Code 39 % (18 % en janvier), Copilot 21 %, Codex 16 %, Cursor 12 % | https://blog.jetbrains.com/research/2026/08/ai-coding-agent-adoption-2026/ | JetBrains | 2026-08-18 | 2026-10-24 | moyenne (extrait via la recherche) | enquête |
| R18 | Pragmatic Engineer 2026 : Claude Code le plus apprécié (46 %) ; les grandes entreprises sur Copilot | https://newsletter.pragmaticengineer.com/p/ai-tooling-2026 | The Pragmatic Engineer | 2026-03 | 2026-10-24 | moyenne | enquête |
| R19 | ETH : AGENTS.md généré par LLM −0,5 / −2 pts et +20-23 % de coût ; écrit à la main +2,4 pts (non significatif) et jusqu'à +19 % de coût | https://arxiv.org/pdf/2602.11988 | arXiv (ETH Zurich) | 2026-02 | 2026-10-24 | haute | mesure |
| R20 | Gartner : d'ici 2027, plus de 65 % des équipes en codage agentique tiendront l'IDE pour optionnel | https://www.gartner.com/en/newsroom/press-releases/2026-05-20-gartner-says-the-market-for-enterprise-ai-coding-agents-is-entering-a-new-phase-of-expansion-and-competitive-realignment | Gartner | 2026-05-20 | 2026-10-24 | moyenne (prédiction) | analyse |
| R21 | Wavestone : Agentic AI Playbook avec un chapitre sur les agents SWE (juin 2025) | https://www.wavestone.com/en/insight/agentic-ai-playbook/ | Wavestone | 2025-06 | 2026-10-24 | moyenne (plus de 6 mois) | analyse |
| R22 | Snyk ToxicSkills : 3 984 skills (ClawHub, skills.sh), 13,4 % à défaut critique, 36,8 % avec un défaut | https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub | Snyk (vendeur sécurité) | 2026-02 | 2026-10-24 | moyenne (éditeur intéressé) | mesure |
| R22b | MalSkillBench : 3 944 skills malveillantes vérifiées à l'exécution ; détecteurs jamais mesurés contre une vérité terrain | https://www.emergentmind.com/papers/2606.07131 | arXiv | 2026-06 | 2026-10-24 | moyenne | mesure |
| R23 | Ask HN : plan d'abord, CLAUDE.md maintenu, session fraîche avec résumé d'état, 3 sous-agents de revue en parallèle ; « bottleneck shifted to judgment and review » ; scepticisme sur les gros codes anciens | https://news.ycombinator.com/item?id=46573860 ; https://news.ycombinator.com/item?id=48413629 | Hacker News | 2026 | 2026-10-24 | moyenne | retour |
| R24 | Essai randomisé d'Anthropic (≈ 52 développeurs) : −17 % au quiz avec IA, gain de vitesse non significatif, l'usage interrogatif préserve l'apprentissage | https://www.anthropic.com/research/AI-assistance-coding-skills | Anthropic | 2026-01 | 2026-10-24 | moyenne (chiffre de 17 % via la couverture presse) | mesure |
| R25 | METR : −19 % de vitesse en 2025 ; en 2026, données jugées non fiables (refus de travailler sans IA), gain probable non chiffré | https://birchtree.me/blog/an-update-from-the-study-that-said-devs-were-actually-slower-with-coding-agents/ | Relais de METR | 2026-03 | 2026-10-24 | moyenne | mesure |
| R26 | Böckeler (Kiro, Spec Kit, Tessl) : trop lourd pour les petits changements, revue de markdown fastidieuse, agents qui ignorent la spec | https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html | martinfowler.com (Thoughtworks) | 2025-10-15 | 2026-10-24 | haute (mais plus de 6 mois) | retour |
| R27 | Issue #42796 « unusable for complex engineering tasks with the Feb updates » : ignore les consignes, se déclare fini à tort (583 commentaires, close) | https://github.com/anthropics/claude-code/issues/42796 | GitHub | 2026-04-02 | 2026-10-24 | moyenne | retour |
| R28 | Support d'AGENTS.md dans Claude Code : issue #6235 close comme *completed* le 2026-08-17 ; un commentaire le dit fonctionnel en 2.1.281+ | https://github.com/anthropics/claude-code/issues/6235 | GitHub | 2026-08-17 | 2026-10-24 | moyenne (changelog non vérifié) | fait |
| R29 | `.agents/skills/` non lu par Claude Code selon un utilisateur (octobre 2026) | https://github.com/anthropics/claude-code/issues/31005 | GitHub | 2026-10-20 | 2026-10-24 | basse (témoignage unique) | retour |

## 5. Pistes non suivies et recherches sans résultat

- **Reddit** : inaccessible à l'outil de recherche. Les plaintes passent par The Register et par les issues GitHub. À compléter à la main si une prévalence propre à Reddit est nécessaire.
- **Cursor et Copilot** : pas de fouille de leurs forums ou issues (budget). Seuls les volets Claude Code et Codex ont été couverts au-delà des enquêtes.
- **Forrester, BCG, Accenture, Capgemini** : rien de public et pertinent trouvé (Forrester non cherché).
- **Rapport McKinsey original** et **rapport Faros AI** : non lus, chiffres de seconde main seulement.
- **Propriété intellectuelle et licences du code généré** : non cherché, faute de budget.
- **Thoughtworks vol. 35** : non vérifié s'il est sorti. La page radar montre encore le vol. 34 au 2026-10-24.
- **Fiches Radar non ouvertes** : « measuring collaboration quality », « Agent Trace », « codebase cognitive debt », « team of coding agents ».
- **Étude citée par Addy Osmani** (AGENTS.md : −28,6 % de temps, −16,6 % de tokens) : non identifiée, elle contredit en partie l'ETH [R19].
- **Changelog Claude Code** : pas vérifié directement pour la version qui lit AGENTS.md ni pour la consommation de quota en octobre 2026.
- **Newsletters** : je n'ai trouvé aucun classement fiable ; celles de Simon Willison, Addy Osmani et Latent Space n'ont pas été vérifiées ce tour.
