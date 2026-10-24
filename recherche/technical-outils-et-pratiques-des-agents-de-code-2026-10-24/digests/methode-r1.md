# Digest `methode` : méthodes et skills de discipline de développement (r1)

Chercheur : dimension `methode`. Run du 2026-10-24. Deux tours sur trois : le tour 1 a couvert les README, les métadonnées et la mesure des dépôts, le tour 2 les issues, les études et la documentation officielle. Je me suis arrêté là parce que le budget web était presque épuisé (23 appels sur 25, dont 3 en échec ou refusés) et que les questions étaient couvertes. Lectures de dépôt : 15 sur 20. Huit dépôts ont été lus d'un bloc par archive tar, sans rien exécuter ; s'y ajoutent 3 lectures du marketplace officiel et 4 lectures d'issues.

## 1. Résumé

- Les cadres se répartissent en trois philosophies :
  - **pipeline imposé** : Superpowers, Liza, ECC ;
  - **boîte à outils à la carte** : Pocock, Karpathy ;
  - **cycle de vie complet routé par une méta-skill** : addyosmani/agent-skills, developer-assistant-skills.

  Superpowers, addy et BMAD revendiquent tous les mêmes étapes (cadrage, spec ou plan, implémentation, revue). On ne peut pas en faire tourner deux comme routeur actif sur le même changement [M3][M4].
- **Coût fixe mesuré** (descriptions listées à chaque tour, sortie des hooks de démarrage) :

  | Cadre | Contexte fixe |
  |---|---|
  | Karpathy | ~0,2 k caractères (plugin) ou 2,4 k (CLAUDE.md) |
  | Pocock | 2,3 k (11 skills listées sur 27) |
  | Superpowers | ~6 k (dont 3,4 k de hook SessionStart) |
  | addy | ~11 k |
  | deepakkamboj | ~15 k |
  | Liza | ~59 k (contrat chargé comme CLAUDE.md) |
  | ECC | ~131 k |

  La liste des skills de Claude Code est plafonnée à **1 % de la fenêtre de contexte**. Au-delà, elle perd d'abord les descriptions des skills les moins invoquées [D1]. ECC dépasse ce plafond d'un ordre de grandeur, et un gros pack peut faire disparaître les descriptions de BMAD.
- **Preuves de qualité** : aucun banc indépendant ne compare ces packs de méthode. Les études générales sur les skills montrent un gain modeste en génie logiciel (+4,5 points), meilleur avec 2 à 3 skills ciblées, et qui s'effondre quand le nombre de skills disponibles grandit [E1][E3][E4]. Les gains annoncés par les auteurs sont auto-mesurés.
- **Retours négatifs documentés sur Superpowers** : lenteur, budget épuisé en exécution par sous-agents, questions de cadrage jugées inutiles en v7 [U1][U2][U3].
- **Équivalents natifs** : plan mode, interview par `AskUserQuestion` vers `SPEC.md`, `/goal`, hook Stop, skill `/code-review` intégrée, sous-agent de vérification [D2]. Côté plugins officiels : `feature-dev`, `code-review`, `pr-review-toolkit`, `code-simplifier`, `skill-creator` (bench avec et sans skill) [D3][D4].

## 2. Fiches outils

### obra/superpowers

- **Ce que c'est.** Un plugin de 15 skills et un hook `SessionStart` (déclenché par `startup|clear|compact`). Le hook injecte en entier la skill `using-superpowers` (3 192 caractères plus un en-tête `<EXTREMELY_IMPORTANT>`) [R1]. Cette skill pose la règle « s'il y a 1 % de chance qu'une skill s'applique, tu DOIS l'invoquer », avant même une question de clarification, et impose `brainstorming` avant le plan mode [R1].
- **Pipeline.** brainstorming → worktree → writing-plans → subagent-driven-development (ou executing-plans) → TDD (supprime le code écrit avant ses tests) → revue → finishing-branch [R2].
- **Coût de contexte (mesure M1).**
  - Fixe : 2 632 caractères de descriptions plus ~3,4 k d'injection, soit ~1,5 k tokens. Le calcul de developertoolkit, à partir de `claude plugin details`, donne ~838 tokens [M4].
  - À l'invocation : 140 k caractères de corps de skills au total. `subagent-driven-development` coûte à lui seul ~11,8 k tokens par déclenchement [M4].
- **Problème résolu.** L'agent qui code avant d'avoir compris, et qui se déclare fini sans preuve.
- **Preuves.** Toutes auto-déclarées par le projet :
  - v6.0.0 : « roughly twice as fast … almost 50% fewer tokens » par rapport à la version précédente [S1] ;
  - v6.4.2 : plans en un quart du temps et un tiers des tokens [S1] ;
  - les évaluations vivent dans un dépôt séparé.

  Côté externe : une seule expérience sur une seule tâche, contre addy, citée de seconde main par le dépôt d'addy. Résultat : tokens équivalents, plus de raisonnement amont pour Superpowers, plus de validation pour addy [S2]. Un blog annonce −14 % de tokens sur 12 sessions [B1], confiance basse.
- **Retours négatifs.**
  - #743 : lenteur, ouverte, 27 commentaires [U1].
  - #1152 : en exécution par sous-agents, un plan simple consomme tout le budget de 5 h sous Codex ; ouverte, reproduite à plus grande échelle en 2026-09 [U2].
  - #2530 (2026-10) : en v7, les questions de brainstorming sont « annoying » et de faible valeur ; le mainteneur reproduit aussi un saut d'implémentation dans 24 essais sur 24 [U3].
  - #895 : plans sur-spécifiés, close [U4].
  - Un blog conseille de n'en garder que 3 skills sur 14 [B1].
- **Maturité** (depots.json).
  - 304 k étoiles, 44 contributeurs, MIT, créé le 2025-10-09, release v7.0.1 du 2026-10-21.
  - Anomalie apparente : 7 commits en 90 jours sur `main`, mais le développement se fait sur la branche `dev` (README) et les notes de version sont denses.
  - Présent dans le marketplace officiel `claude-plugins-official` en tant que plugin externe [D4].
- **Risques.**
  - Hook shell à chaque démarrage. Sous Windows, il exige Git Bash (`shell: "bash"`, Claude Code ≥ 2.1.81). Il a un long passif de pannes et a reçu un correctif de sécurité en v7.0.0 : un dépôt pouvait déposer un `bash.cmd` exécuté au démarrage [S1].
  - Télémétrie opt-out : le logo du compagnon visuel est chargé depuis primeradiant.com avec la version [R2].
  - Conflit frontal avec BMAD (§3).
- **Compatibilité.** Claude Code sous Windows : oui, depuis les correctifs de v6.2 à v7.0. Le plus large éventail d'agents de la liste (Codex, Cursor, Copilot CLI, Gemini, OpenCode…).
- **Équivalent officiel.** `feature-dev` (7 phases, agents explorer, architect et reviewer), plan mode, `/code-review` [D2][D3].
- **Verdict : `Évaluer`.** C'est le pipeline le plus abouti, mais il revendique les mêmes étapes que BMAD et que la chaîne dev-story → second-avis → reviewer, avec une règle d'invocation agressive. À tester sur une story avant toute adoption, ou à piller à la carte (systematic-debugging, verification-before-completion).

### mattpocock/skills

- **Ce que c'est.** Un plugin de 27 skills, dont 16 en `disable-model-invocation` : elles ne s'invoquent qu'à la main et leur description n'est pas en contexte [D1]. Il n'a aucun hook [M1].
- **Philosophie.** Des skills petites et composables. Le dépôt critique explicitement BMAD, GSD et Spec Kit : ces méthodes « take away your control » en possédant le processus [R3].
  - La skill phare est le *grilling* : un interrogatoire une question à la fois.
  - Il défend un `GLOSSARY.md` de langage commun et des ADR, du TDD par tranches verticales, et `/code-review` sur deux axes (standards et spec) par sous-agents parallèles.
- **Coût de contexte (M1).** 11 skills listées, 2 266 caractères, soit ~570 tokens. C'est le plus économe des packs complets.
- **Preuves.** Aucune évaluation dans le dépôt [S2]. Aucun retour critique substantiel trouvé (une recherche). Une source tierce note un fort *churn* : `/to-prd` et `/to-issues` ont été remplacés par `/to-spec` et `/to-tickets` en juillet 2026 [B2].
- **Maturité.** 302 k étoiles pour un dépôt créé le 2026-02-03, avec seulement 8 contributeurs. C'est une anomalie : la popularité vient de l'audience de l'auteur (newsletter de ~60 k inscrits). 100 commits en 90 jours, MIT, v1.3.1 du 2026-10-04. Présent dans le marketplace officiel [D4].
- **Risques.**
  - Collision de nom : la skill `code-review` du pack avec `/code-review` intégré et `bmad-code-review`.
  - `setup-matt-pocock-skills` écrit des conventions de tracker dans le dépôt.
  - Renommages fréquents.
- **Compatibilité.** Prévu d'abord pour Claude Code. Codex, Copilot et Gemini sont supportés avec une fidélité variable [S2].
- **Équivalent officiel.** L'interview `AskUserQuestion` → `SPEC.md` des bonnes pratiques [D2].
- **Verdict : `Essayer`** à la carte. `grill-with-docs` (manuelle, sans coût fixe) et `diagnosing-bugs` se glissent dans BMAD sans revendiquer d'étape automatiquement.

### addyosmani/agent-skills

- **Ce que c'est.** 25 skills, 9 commandes (`/spec /plan /build /test /review /ship`…) et 4 agents (personas de revue). La méta-skill `using-agent-skills` route vers la bonne skill [R4].
  - Le script `hooks/session-start.sh` injecterait cette méta-skill (10,4 k caractères), mais il n'est pas branché par défaut dans le plugin Claude Code : il n'y a pas de `hooks/hooks.json`, et il demande `jq` [M1].
  - Chaque skill contient une table « anti-rationalisation ».
- **Coût de contexte (M1).** 9 425 + 830 + 819 caractères, soit ~11 k caractères (~2,8 k tokens). La plus longue description fait 909 caractères (`constraint-driven-development`).
- **Preuves.**
  - Un cadre d'évaluation en trois niveaux dans le dépôt : structure, routage des descriptions en CI, et notation de traces. Le registre des changements rejetés est vide [M2].
  - Le seul face-à-face (Om Mishra) est de seconde main ; je ne l'ai pas consulté [S2].
- **Maturité.** 110 k étoiles, 93 contributeurs, 100 commits en 90 jours, MIT, release 0.6.13 du 2026-10-13. C'est la gouvernance la plus ouverte des trois grands packs.
- **Risques.**
  - Collision de `/review` avec la commande intégrée : il faut utiliser `/agent-skills:review`.
  - `spec-driven-development` et `/build auto` chevauchent bmad-prd, bmad-spec et bmad-build.
  - Le document de comparaison est publié par le projet lui-même (juge et partie), même s'il se veut équilibré.
- **Compatibilité.** Windows : le clone SSH du marketplace échoue sans clé ; contournement par `git config url.insteadOf` [R4]. Le pack le plus portable (Copilot, Cursor, Codex, Kiro, Gemini…).
- **Équivalent officiel.** `feature-dev`, `pr-review-toolkit`, `code-simplifier` [D4].
- **Verdict : `Évaluer`.** Le cycle de vie est le plus large et le seul outillé en évaluations, mais c'est un second routeur concurrent de BMAD. Mieux vaut emprunter deux skills (`constraint-driven-development`, `doubt-driven-development`) comme références que l'installer en entier.

### affaan-m/ECC (everything-claude-code)

- **Ce que c'est.** Un « système d'exploitation du harnais » : 311 skills, 71 agents, 97 commandes historiques, 27 hooks répartis sur 8 événements, plus des règles, de la mémoire, AgentShield et un MCP [R5][M1].
  - Les hooks comprennent un `PreToolUse` sur `.*` et 8 hooks `Stop` à chaque fin de tour, dont `format-typecheck` (délai max 300 s), `cost-tracker`, `evaluate-session` et `desktop-notify`.
  - Il exige Node.
- **Coût de contexte (M1).** 101 046 caractères de descriptions de skills, 13 797 de commandes et 15 921 d'agents, soit ~131 k caractères (~33 k tokens bruts). Le plafond de 1 % de la fenêtre (≈ 8 k caractères à 200 k tokens, ≈ 40 k à 1 M) coupe la majorité des descriptions : la plupart des skills deviennent invisibles au déclenchement automatique, et celles de BMAD risquent de l'être aussi [D1].
- **Preuves.** Aucune mesure indépendante trouvée. Un relecteur de skills (Tessl) juge `configure-ecc` « monolithic and verbose » [B3]. Le périmètre déborde largement le développement (investor-outreach, x-api, video-editing…).
- **Maturité.** 288 k étoiles et 42,7 k forks pour un dépôt créé le 2026-01-18 : anomalie de popularité. 100 contributeurs, MIT, v2.2.3 du 2026-10-01. Le README lui-même met en garde contre des miroirs piégés.
- **Risques.**
  - Surface d'exécution très large : hooks Node à chaque outil et à chaque fin de tour.
  - Doublon direct avec le plugin maison de coûts (`cost-tracker`).
  - Une application GitHub et un service ecc.tools ; je n'ai pas vérifié leurs accès réseau.
- **Compatibilité.** Windows : `install.ps1` et un profil `minimal` sans hooks.
- **Équivalent officiel.** `hookify`, `security-guidance`, `claude-md-management`, `/skill-doctor` [D1][D4].
- **Verdict : `Écarter`.** Le coût fixe dépasse le plafond de liste d'un ordre de grandeur, les hooks s'exécutent à chaque tour et il fait doublon avec BMAD et le kit de coûts. Au besoin, copier une skill isolée après l'avoir lue.

### multica-ai/andrej-karpathy-skills

- **Ce que c'est.** Un `CLAUDE.md` de 2 357 caractères, ou une skill unique (description de 238 caractères), sur quatre principes : réfléchir avant de coder, simplicité d'abord, changements chirurgicaux, exécution guidée par des critères vérifiables [R6][M1]. Ni script ni hook.
- **Preuves.**
  - Aucune mesure publiée. Le chiffre « 41 % → 3 % d'erreurs » circule pour une variante étendue à 12 règles, sans méthode ni données : non vérifié [B4].
  - Le contenu recoupe la doc officielle : critères vérifiables, CLAUDE.md court, signaler l'ambiguïté [D2].
- **Maturité.** 223 k étoiles pour un fichier, 0 commit en 90 jours (dernier push 2026-04-20). Le champ `licence` est vide dans depots.json alors que le README annonce MIT : la licence n'est pas détectée par GitHub. Le dépôt a été transféré depuis `forrestchang/` (les commandes d'installation le citent encore) et sert de vitrine à Multica.
- **Risques.** Faibles : un texte statique. Le risque est de doublonner des règles déjà présentes dans le CLAUDE.md global.
- **Équivalent officiel.** Les bonnes pratiques Claude Code [D2].
- **Verdict : `Essayer`.** Intégrer les 4 principes en une dizaine de lignes dans le CLAUDE.md global, sans installer le plugin, puis mesurer l'effet sur la taille des diffs (H2).

### liza-mas/liza (angle méthode)

- **Ce que c'est.**
  - Un « contrat comportemental » : machine à états, règles d'or, cartographie de 55 modes d'échec, pré-autorisation écrite avant d'agir, droit de dire « je suis bloqué ».
  - 30 skills (spec, revue, red-testing, lean, systemic thinking…).
  - Un orchestrateur Go pour le mode multi-agents, traité dans une autre dimension [R7].
- **Coût de contexte.** Le contrat se branche en lien symbolique sur `~/.claude/CLAUDE.md` : il **remplace** le CLAUDE.md global [R7]. CORE (38,7 k caractères) et PAIRING_MODE (15,3 k) sont lus au démarrage, soit ~54 k caractères (~13,5 k tokens) par session, plus 5 k de descriptions de skills [M1].
- **Preuves.** L'auteur écrit que le taux de « production-ready », la précision des relecteurs et le coût jusqu'à la production ne sont pas établis de façon indépendante [R7]. Seuls des enregistrements de démonstration existent.
- **Maturité.** 411 étoiles, 9 contributeurs, 100 commits en 90 jours, Apache-2.0, v0.9.1 du 2026-09-21. Pas d'inflation d'étoiles.
- **Risques.** Remplace le CLAUDE.md et conteste l'autorité de BMAD (une comparaison détaillée Liza / BMAD figure dans le dépôt). Coût fixe élevé.
- **Verdict : `Évaluer`** comme lecture : y prendre 2 ou 3 règles (pré-autorisation écrite, refus de faire semblant d'avancer). Ne pas l'installer.

### deepakkamboj/developer-assistant-skills

- **Ce que c'est.** 36 skills et 20 agents (15 critiques), un CLI npm de validation et des workflows CI autonomes désactivés par défaut [R8].
- **Coût de contexte (M1).** 9 941 + 4 914 caractères, soit ~15 k caractères (~3,7 k tokens).
- **Preuves.** Aucune.
- **Maturité.** 1 étoile, 3 contributeurs, créé le 2026-09-12, v1.0.3. Trop jeune.
- **Verdict : `Écarter`.** Aucune preuve, un projet trop jeune, et un recouvrement complet avec BMAD et les plugins officiels. Seul le groupe accessibilité (a11y-*) pourrait intéresser la dimension front.

### spotify/portal-ai-plugins

- **Ce que c'est.** L'intégration du produit Spotify Portal (Backstage) : catalogue, actions, Fleetshift [R9]. Le plugin `shunt` route la lecture de masse et le code passe-partout vers des modèles « worker » moins chers, mais via AiKA / Portal.
- **Verdict : `Hors périmètre`.** Ce n'est pas une méthode et il dépend de Portal. L'idée de `shunt` est à signaler à la dimension coûts et routage.

### anthropics/skills (angle méthode)

- **Ce que c'est.** Des skills d'exemple. Pour la méthode, seule `skill-creator` compte : elle sert à créer des skills et à **mesurer** leur effet (benchmark avec et sans skill, A/B en aveugle entre versions, réglage des descriptions par prompts qui doivent ou ne doivent pas déclencher) [D1].
  - 19 skills, 9 635 caractères de descriptions si tout est installé [M1].
  - Les autres (docx, pdf, frontend-design, webapp-testing…) ne relèvent pas de la méthode.
- **Maturité.** 183 k étoiles, 16 contributeurs, 14 commits en 90 jours. `licence` vide dans depots.json : un mélange d'Apache 2.0 et de source-available pour les skills de documents [R10].
- **Verdict : `Adopter` `skill-creator` seulement**, pour mesurer les skills BMAD et celles du kit de coûts plutôt que d'en ajouter. Le reste est hors périmètre.

## 3. Analyse de catégorie

### Recouvrements et combinaisons

| Étape | BMAD (en place) | Superpowers | addy | Pocock | Officiel |
|---|---|---|---|---|---|
| Cadrage / interview | bmad-brainstorming, bmad-forge-idea | brainstorming (auto, « MUST ») | interview-me, idea-refine | grill-me / grilling | AskUserQuestion → SPEC.md |
| Spec / PRD | bmad-prd, bmad-spec | design doc | spec-driven-development (/spec) | to-spec | (Spec Kit, OpenSpec : autre dimension) |
| Plan / stories | bmad-create-epics…, sprint-planning | writing-plans | planning-and-task-breakdown | to-tickets, wayfinder | plan mode |
| Implémentation | bmad-build, dev-story (kit) | subagent-driven-development | /build, /build auto | implement, implement-spec | feature-dev |
| TDD | (dans bmad-build) | test-driven-development (supprime le code) | test-driven-development | tdd | — |
| Debug | — | systematic-debugging | debugging-and-error-recovery | diagnosing-bugs | — |
| Revue | bmad-code-review, reviewer (kit) | requesting-code-review | /review + personas | code-review | /code-review intégré, plugin code-review, pr-review-toolkit |

- **Conflits.** Dès que deux routeurs automatiques revendiquent la même étape, on obtient deux sources de vérité et des collisions de noms. addy (juge et partie) et developertoolkit (vendeur d'un guide) le disent tous deux ; leur conclusion converge malgré ce biais [M3][M4]. Superpowers est le plus intrusif : règle du « 1 % », hook à chaque `/clear` et `compact`, brainstorming imposé avant le plan mode.
  - Deux atténuations existent : la skill déclare que les instructions utilisateur (CLAUDE.md) priment, et la clause `SUBAGENT-STOP` protège les sous-agents [R1].
  - Leur efficacité face à BMAD n'est pas vérifiée.
- **Combinaisons sans conflit.** Les skills **manuelles** (`disable-model-invocation`) ne revendiquent rien : `grill-with-docs` de Pocock ou la lecture de `systematic-debugging` peuvent s'ajouter à BMAD. C'est la voie qu'ont prise Pocock (16 sur 27) et la doc officielle [D1].
- **Strictement meilleur ?** Aucun pack ne l'est sur tous les critères.
  - Pocock gagne sur le coût fixe et la non-intrusion.
  - addy gagne sur la largeur, les évaluations et la portabilité.
  - Superpowers gagne sur l'autonomie longue et la discipline anti-rationalisation, au prix du coût et de l'intrusion.
  - Karpathy est dominé en largeur, mais c'est le moins cher.

### État de l'art hors liste

- **Natif Claude Code** [D2] :
  - plan mode, à réserver aux changements multi-fichiers ou incertains (« if you could describe the diff in one sentence, skip the plan ») ;
  - `/goal`, avec un évaluateur séparé qui reteste à chaque tour ;
  - hook Stop comme porte déterministe ;
  - skill `/code-review` intégrée ;
  - sous-agent de vérification ;
  - consigne explicite de demander au relecteur de ne signaler que les écarts de correction ou d'exigence, faute de quoi il pousse à la sur-ingénierie.

  Les règles qui doivent tenir à chaque fois vont dans des **hooks**, pas dans des skills [D1].
- **Gestion du coût des skills** [D1] :
  - `/skill-doctor` (coût et usage par skill) ;
  - `/doctor` (coût de la liste) ;
  - `skillOverrides: "name-only"` ;
  - `skillListingBudgetFraction` ;
  - `claude plugin eval` avec un correcteur `tool_used: Skill` pour mesurer le taux de déclenchement.
- **Recherche** :
  - les skills stabilisent l'action plus qu'elles n'apportent de savoir (« procedural anchoring » : 65,7 % des cas) ;
  - la précision de récupération chute de 29,6 % à 3,3 % quand le nombre de skills disponibles passe de 5 à 100 [E4] ;
  - curated skills +16,2 points en moyenne mais +4,5 en génie logiciel ; skills ciblées de 2 à 3 modules meilleures que la documentation exhaustive [E1] ;
  - les gains s'effacent en conditions réalistes, parmi 34 k skills [E3] ;
  - 26,1 % des 31 132 skills communautaires analysées ont une vulnérabilité exploitable [E2].

  Conséquence pratique : **peu de skills, procédurales, bien décrites**.

### Problèmes que rien ne traite

- Aucun protocole d'**arbitrage entre packs** : pas de priorité déclarable ni de « propriétaire d'étape ». Seul le CLAUDE.md peut trancher.
- Pas de banc indépendant et reproductible de méthodes de bout en bout (qualité, coût, temps) ; seulement des auto-évaluations ou des expériences sur une seule tâche.
- Pas de mémoire inter-sessions durable des apprentissages, de l'aveu même d'addy [S2].
- La question « quand ne pas déclencher le processus » reste mal réglée : les retours de Superpowers v7 montrent à la fois des questions superflues et des sauts d'étape [U3].

### Hypothèses à tester (protocoles)

- **H1. Superpowers contre BMAD avec le kit de coûts.**
  - Tâche : une story FastAPI + Jinja bien cadrée (un endpoint, un template, des tests), faite deux fois depuis le même commit.
  - Mesures : tokens (`/agent-cost-kit:mesurer-couts`), durée, interventions humaines, tests ajoutés, constats d'une revue Opus en aveugle.
  - Décision : n'adopter que si la qualité est au moins égale et le surcoût en tokens d'au plus 20 %.
- **H2. Principes Karpathy dans CLAUDE.md.**
  - Tâches : 5 correctifs ou refactorings, avec et sans les principes.
  - Mesures : lignes modifiées hors périmètre, lignes ajoutées, tests verts.
  - Décision : garder si le diff hors périmètre baisse d'au moins 30 % sans régression.
- **H3. `grill-with-docs` contre `bmad-spec` en cadrage.**
  - Tâche : cadrer 2 stories.
  - Mesure : nombre d'ambiguïtés découvertes ensuite, en dev ou en revue (reprises).
  - Décision : garder `grill-with-docs` s'il élimine au moins une reprise par story.
- **H4. Plafond de la liste de skills.**
  - Procédure : installer addy, ou ECC en profil minimal, à côté de BMAD dans un projet jetable. Relever la ligne Skills de `/context`, puis `/doctor`. Lancer 10 prompts qui doivent déclencher des skills BMAD (`claude plugin eval`, correcteur `tool_used: Skill`).
  - Décision : écarter tout pack qui fait chuter le taux de déclenchement de BMAD.
- **H5. `skill-creator` en mode benchmark sur `dev-story` (kit) ou `bmad-build`.** Mesurer le gain avec et sans la skill, et le surcoût en tokens et en temps, pour savoir ce que les skills maison rapportent vraiment.

## 4. Affirmations

| ref | affirmation | source (URL) | éditeur | date publi | consultée | confiance | classe |
|---|---|---|---|---|---|---|---|
| M1 | Coût fixe mesuré (caractères de descriptions listées et injection au démarrage) : Superpowers 2 632 + ~3,4 k ; Pocock 2 266 (11 listées sur 27) ; addy ~11 k ; ECC ~131 k (311 skills, 97 commandes, 71 agents, 27 hooks) ; Liza 5 k + contrat ~54 k ; deepak ~15 k ; Karpathy 238 ou 2 357 | archives des dépôts (`gh api …/tarball`), script local | mesure du chercheur | — | 2026-10-24 | haute | mesure |
| D1 | La liste des skills est plafonnée à 1 % de la fenêtre ; en cas de dépassement, les descriptions des skills les moins invoquées sont retirées ; plafond de 1 536 caractères par entrée ; `disable-model-invocation` retire la description du contexte ; `/skill-doctor`, `skillOverrides`, `claude plugin eval` ; `skill-creator` fait du bench avec et sans skill | https://code.claude.com/docs/en/skills | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| D2 | Bonnes pratiques officielles : vérification, explore → plan → code, plan mode inutile si le diff tient en une phrase, interview AskUserQuestion → SPEC.md, hooks pour les règles impératives, `/code-review` intégré, relecteur qui pousse à la sur-ingénierie | https://code.claude.com/docs/en/best-practices | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| D3 | `feature-dev` : 7 phases, agents code-explorer, code-architect et code-reviewer | https://github.com/anthropics/claude-plugins-official/tree/main/plugins/feature-dev | Anthropic | dépôt poussé le 2026-10-24 | 2026-10-24 | haute | fait |
| D4 | Plugins officiels : code-review, pr-review-toolkit, code-simplifier, skill-creator, hookify, security-guidance, claude-md-management, ralph-loop… ; `superpowers` et `mattpocock-skills` figurent dans le marketplace officiel | https://github.com/anthropics/claude-plugins-official | Anthropic | 2026-10-24 | 2026-10-24 | haute | fait |
| R1 | `using-superpowers` : règle du « 1 % », invocation avant toute réponse, brainstorming avant le plan mode, instructions utilisateur prioritaires, SUBAGENT-STOP ; injecté par un hook SessionStart sur startup, clear et compact | https://github.com/obra/superpowers/blob/main/skills/using-superpowers/SKILL.md | obra / Prime Radiant | v7.0.1, 2026-10-21 | 2026-10-24 | haute | fait |
| R2 | Pipeline Superpowers, TDD qui supprime le code écrit avant les tests, télémétrie opt-out du compagnon visuel | https://github.com/obra/superpowers | obra | 2026-10 | 2026-10-24 | haute | fait |
| S1 | Superpowers v6.0.0 : « ~2× plus rapide, ~50 % de tokens en moins » ; v6.4.2 : plans en ¼ du temps et ⅓ des tokens ; v7.0.0 : correctifs Windows dont un `bash.cmd` déposé exécuté au démarrage | https://github.com/obra/superpowers/blob/main/RELEASE-NOTES.md | obra | 2026-06-16 / 2026-09-25 / 2026-10-09 | 2026-10-24 | moyenne | auto-déclaré |
| U1 | Lenteur de réponse attribuée à Superpowers (issue ouverte, 27 commentaires) | https://github.com/obra/superpowers/issues/743 | GitHub | 2026-03-15 | 2026-10-24 | moyenne | retour d'usage |
| U2 | En exécution par sous-agents, un plan simple épuise le budget de 5 h (Codex) ; reproduit en 2026-09 | https://github.com/obra/superpowers/issues/1152 | GitHub | 2026-04-13 | 2026-10-24 | moyenne | retour d'usage |
| U3 | v7 : questions de brainstorming de faible valeur ; le mainteneur reproduit un saut d'implémentation dans 24 essais sur 24 | https://github.com/obra/superpowers/issues/2530 | GitHub | 2026-10-16 | 2026-10-24 | haute | retour d'usage |
| U4 | `writing-plans` sur-spécifie l'implémentation | https://github.com/obra/superpowers/issues/895 | GitHub | 2026-03-23 | 2026-10-24 | moyenne | retour d'usage |
| R3 | Pocock : skills petites et composables ; BMAD, GSD et Spec Kit « take away your control » ; séparation entre skills manuelles et skills invocables par le modèle | https://github.com/mattpocock/skills | Matt Pocock | v1.3.1, 2026-10-04 | 2026-10-24 | haute | fait / opinion |
| R4 | addy : 25 skills, 9 commandes, méta-skill routeur, `/review` en collision avec la commande intégrée, problème SSH sous Windows | https://github.com/addyosmani/agent-skills | Addy Osmani | 0.6.13, 2026-10-13 | 2026-10-24 | haute | fait |
| M2 | addy : évaluations à trois niveaux, routage en CI, registre des rejets vide | https://github.com/addyosmani/agent-skills/tree/main/evals | Addy Osmani | 2026-10 | 2026-10-24 | haute | fait |
| S2 | Comparaison addy / Superpowers / Pocock et résumé du test d'Om Mishra (tokens équivalents, addy plus validant, Superpowers plus de raisonnement amont) ; pas d'évaluations chez Pocock ; mémoire inter-sessions non résolue | https://github.com/addyosmani/agent-skills/blob/main/docs/comparison.md | projet addy (juge et partie) | n.d. | 2026-10-24 | moyenne | opinion / seconde main |
| M3 | Ne pas faire tourner deux routeurs (méta-skills) en même temps : collisions de commandes, philosophies TDD divergentes | même source que S2 | projet addy | n.d. | 2026-10-24 | moyenne | opinion |
| M4 | « Never run two on the same change » ; coût fixe estimé : BMAD ~1 676 tokens, Superpowers ~838, `subagent-driven-development` ~11,8 k par déclenchement | https://developertoolkit.ai/en/ecosystem/frameworks/spec-driven-frameworks/ | M. Jaskólski (vend un guide) | 2026-09-26 | 2026-10-24 | moyenne | mesure tierce |
| R5 | ECC : 71 agents, 311 skills, 97 commandes, profils de hooks minimal, standard et strict, `install.ps1` | https://github.com/affaan-m/ECC | Affaan Mustafa | v2.2.3, 2026-10-01 | 2026-10-24 | haute | fait |
| R6 | Karpathy : 4 principes dans un CLAUDE.md, aucune mesure | https://github.com/multica-ai/andrej-karpathy-skills | forrestchang / Multica | 2026-04-20 | 2026-10-24 | haute | fait |
| R7 | Liza : contrat branché sur `~/.claude/CLAUDE.md` ; taux de production-ready et coût non établis indépendamment | https://github.com/liza-mas/liza | liza-mas | v0.9.1, 2026-09-21 | 2026-10-24 | haute | fait / auto-déclaré |
| R8 | developer-assistant-skills : 36 skills et 20 agents | https://github.com/deepakkamboj/developer-assistant-skills | D. Kamboj | 2026-09-29 | 2026-10-24 | haute | fait |
| R9 | Spotify Portal plugins et `shunt` (délégation vers des modèles worker AiKA) | https://github.com/spotify/portal-ai-plugins | Spotify | 2026-10-23 | 2026-10-24 | haute | fait |
| R10 | anthropics/skills : exemples, en partie Apache 2.0 et en partie source-available | https://github.com/anthropics/skills | Anthropic | 2026-10-09 | 2026-10-24 | haute | fait |
| E1 | SkillsBench : curated skills +16,2 points en moyenne, génie logiciel +4,5 ; skills auto-générées sans gain moyen ; skills ciblées de 2 à 3 modules meilleures que la documentation exhaustive | https://www.oreilly.com/radar/agent-skills-work-but-the-research-shows-most-teams-are-building-them-wrong (cite arXiv 2602.12670) | O'Reilly Radar | 2026-05-18 | 2026-10-24 | moyenne | étude (seconde main) |
| E2 | 26,1 % des 31 132 skills communautaires ont une vulnérabilité exploitable | même article (cite arXiv 2601.10338) | O'Reilly Radar | 2026-05-18 | 2026-10-24 | moyenne | étude (seconde main) |
| E3 | Les gains des skills se dégradent en conditions réalistes (34 k skills), jusqu'à approcher la base sans skill | https://arxiv.org/abs/2604.04323 | UCSB, MIT CSAIL, MIT-IBM | 2026-04 | 2026-10-24 (via résultats de recherche) | moyenne | étude |
| E4 | Procedural anchoring : 65,7 % des cas ; précision de récupération de 29,6 % à 3,3 % quand le nombre de skills passe de 5 à 100 | https://arxiv.org/abs/2608.14036 | Jiang et al. | 2026-08-14 | 2026-10-24 | moyenne | étude |
| B1 | Superpowers : −14 % de tokens sur 12 sessions ; « overkill » pour les petits changements ; un auteur ne garde que 3 skills sur 14 | https://www.mejba.me/blog/superpowers-plugin-claude-code-review ; https://pub.towardsai.net/i-installed-40-claude-skills-three-survived-29fe64f802ec | blogs | 2026 | 2026-10-24 (extraits de recherche) | basse | retour d'usage |
| B2 | Churn de Pocock : `/to-prd` et `/to-issues` remplacés en juillet 2026 | https://skillselion.com/guide/matt-pocock-skills-map | tiers | 2026 | 2026-10-24 (extrait) | basse | fait (tiers) |
| B3 | `configure-ecc` jugé monolithique et verbeux | https://tessl.io/registry/skills/github/xu-xiang/everything-claude-code-zh/configure-ecc/quality | Tessl | n.d. | 2026-10-24 (extrait) | basse | opinion |
| B4 | « 41 % → 3 % d'erreurs » pour un CLAUDE.md Karpathy étendu, sans méthode publiée | https://agentpedia.codes/blog/karpathy-claude-md-rules-extended | blog | 2026 | 2026-10-24 (extrait) | basse | non vérifié |

## 5. Pistes non suivies et recherches infructueuses

- **Article Medium imposé** (Jordanovski, « four philosophies ») : non lu. Medium a répondu 403, le miroir scribe.rip 404, et le classifieur a refusé le miroir freedium (contenu sous paywall). Son contenu n'est donc pas intégré ; à lire à la main.
- **Expérience d'Om Mishra** (LinkedIn) : non consultée, citée seulement via le document d'addy.
- **Retours Reddit et HN indépendants sur Superpowers** : deux recherches sans résultat utile. Les issues GitHub ont servi de substitut.
- **Accès réseau des hooks ECC et de l'application GitHub ecc.tools** : pas audités ; à confier à la dimension sécurité.
- **Compatibilité Windows de l'orchestrateur Liza (Go)** : non vérifiée.
- **Fenêtre de contexte exacte d'Opus 5.5 dans l'abonnement Max** : non vérifiée, donc le plafond de 1 % est donné pour 200 k et pour 1 M tokens.
- **Idée de `shunt` (Spotify)**, délégation des E/S massives vers un modèle moins cher : à transmettre aux dimensions coûts et routage.
- **Le chiffre « 5 plugins = 55 k tokens »** relayé par un blog semble être une mauvaise attribution du billet d'Anthropic sur les serveurs MCP. Non vérifié, donc non retenu.
