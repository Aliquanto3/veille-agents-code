# Digest `litterature`, tour 1 (run du 2026-10-24)

Dimension : ce que la recherche publiée en 2024-2026 établit sur les problèmes des agents de code et sur l'effet des pratiques qui y répondent. Ici, les fiches outils sont remplacées par des **fiches par problème**.

**Méthode et arrêt.** J'ai fait deux tours. Le tour 1 était large (surveys, échecs, productivité, pratiques, sécurité, coût). Le tour 2 a vérifié les articles primaires les plus porteurs (METR 2025 et 2026, Gloaguen, Lulla, Ehsani, Zhao) et comblé des trous (dette, planification, multi-agents). **La recherche s'est arrêtée parce que le budget était épuisé** : 25 appels web sur 25, aucune lecture de dépôt (elles n'étaient pas utiles pour cette dimension). Six sources ont été ouvertes en entier ou au niveau du résumé arXiv. Les autres sont connues **par les extraits de recherche** (résumé de l'abstract) : leur confiance plafonne à « moyenne ».

**Statut de relecture.** Presque tout ce corpus est fait de **preprints arXiv** de moins de 12 mois. Sont publiés après relecture : Ehsani et al. et He et al. (MSR 2026), et CR-Bench (ICLR 2026). Les autres sources sont des rapports (DORA, METR, Anthropic) ou des contenus de vendeurs.

## 1. Résumé

1. **Les échecs commencent tôt et restent cachés.** Sur 1 794 trajectoires annotées, les échecs viennent surtout d'erreurs épistémiques (l'agent croit à tort quelque chose sur la tâche ou l'environnement), naissent dans les premières étapes et ne se voient qu'une fois irrécupérables [A1]. Les trajectoires qui échouent sont 12 à 82 % plus longues que celles qui réussissent [A3]. La validation précoce (revue du plan, premiers tests) vise donc le bon moment.
2. **Les fichiers de contexte ont un effet discuté.** Gloaguen et al. ne trouvent aucun gain de réussite et un coût d'inférence supérieur de plus de 20 % [A8]. Lulla et al. trouvent 28,6 % de temps et 16,6 % de tokens de sortie en moins, avec une réussite comparable [A9]. Les deux convergent sur un point : il faut écrire peu, et seulement ce qui n'est pas standard.
3. **Les skills curées aident, celles écrites par le modèle n'aident pas.** Gain moyen de +16,2 points, mais seulement +4,5 en génie logiciel, et aucun gain pour les skills auto-générées. Ces chiffres viennent d'un seul benchmark, non relu [A11].
4. **La productivité réelle reste non tranchée.** METR mesurait −19 % début 2025. Le suivi de fin 2025 donne des intervalles qui contiennent zéro, et METR le juge lui-même « very weak evidence » [A13][A14]. DORA 2025 associe l'IA à plus de débit et à plus d'instabilité [A16]. Un essai d'Anthropic mesure une compréhension plus faible (50 % contre 67 %) sans gain de vitesse significatif [A17].
5. **La qualité et la sécurité sont le goulot.** Avec Cursor, la vitesse augmente de façon transitoire, tandis que les alertes statiques et la complexité augmentent durablement [A19]. Chez les agents, 57 % du code est fonctionnel mais seulement 11,8 % est sûr, et des consignes de sécurité ajoutées au prompt n'y changent rien [A21]. Environ 24 % des problèmes introduits par l'IA survivent dans le code [A23].
6. **Coût.** Un agent consomme environ 1 000 fois plus de tokens qu'un chat, surtout en entrée. La consommation varie jusqu'à 30 fois d'un run à l'autre sur la même tâche, et plus de tokens ne donne pas plus de réussite [A27]. Les lectures de fichiers représentent environ 76 % des tokens [A28]. Aucune étude ne valide le routage « modèle le moins cher suffisant » sur une flotte d'agents de code [A30].

## 2. Fiches par problème

### P1. Pourquoi les agents échouent (taxonomie)

- **Ce que la littérature établit.**
  - *Trajectoires.* L'étude de Zhao et al. porte sur Terminal-Bench, avec trois scaffolds et sept modèles, soit 1 794 trajectoires et plus de 63 000 étapes. Les échecs sont surtout épistémiques, apparaissent dans les premières étapes et restent cachés jusqu'au point de non-retour [A1]. Avant elle : Ceka et al. 2025 sur les « decision pathways » (exploration, patch-first, test-driven) et une étude des trajectoires réussies et ratées (arXiv 2511.00197) [A2][A3].
  - *Utilisateurs.* Une analyse de 20 574 sessions réelles identifie 7 formes de désalignement entre développeur et agent, codées par un juge LLM validé par des experts [A4] (preprint, lu par extrait).
  - *PR sur GitHub.* Ehsani et al. (MSR 2026) étudient 33 000 PR d'agents provenant de 5 agents. Les tâches de documentation, de CI et de build sont les plus souvent fusionnées ; les tâches de performance et les corrections de bugs le sont le moins. Les PR rejetées sont plus grosses, touchent plus de fichiers et échouent plus souvent en CI. Motifs de rejet : PR en double, fonctionnalité non souhaitée, désalignement, absence d'engagement du relecteur [A5]. Une autre étude nuance : seuls 35,7 % des rejets sont de vrais échecs de l'agent ; 31,2 % tiennent au workflow du projet et 33,1 % sont sans motif visible [A6].
  - *Ce qui ne manque pas.* Une ablation sur des PR réelles conclut que les agents échouent par manque de compétence d'implémentation (conception, choix de pattern, câblage exact), pas par manque de connaissance du dépôt [A10].
- **Force de la preuve.** C'est un consensus naissant (échecs précoces et épistémiques, grosses PR rejetées) issu de plusieurs laboratoires, mais presque entièrement en preprint. Il n'existe pas encore de taxonomie de référence unique. MAST (14 modes d'échec, 1 642 traces) couvre les systèmes multi-agents en général, pas le code [A7].
- **Implication pour la configuration.**
  - Garder des stories petites et des PR courtes, puisque la taille est corrélée au rejet.
  - Valider tôt : revue du plan, puis un premier test rouge avant d'implémenter.
  - Prévoir un critère d'abandon. Une trajectoire qui s'allonge très au-delà de la médiane de la story est un signal d'échec.
  - Le fichier de contexte ne compense pas un manque de compétence : pour une story difficile, il faut monter le modèle ou l'effort, pas allonger CLAUDE.md.

### P2. La productivité réelle

- **Essais contrôlés.**
  - **METR 2025** : 16 développeurs expérimentés, 246 tâches tirées au sort, Cursor avec Claude 3.5/3.7. Les tâches ont pris **19 % de temps en plus** avec l'IA (IC 95 % de +2 % à +39 %), alors que les développeurs avaient prévu −24 % et croyaient encore à −20 % après l'étude [A12][A14].
  - **Suivi METR de février 2026** (étude commencée en août 2025) : 57 développeurs, 143 dépôts, plus de 800 tâches. Pour les 10 anciens : **−18 %** (plus rapide), IC de −38 % à +9 %. Pour les nouveaux : −4 %, IC de −15 % à +9 %. Les deux intervalles contiennent zéro. METR parle de « very weak evidence » et d'un « bad proxy » : 30 à 50 % des développeurs ont retenu des tâches qu'ils ne voulaient pas faire sans IA, des développeurs ont refusé de participer, et le travail en parallèle avec plusieurs agents rend la mesure du temps peu fiable. METR envisage de refondre l'étude (tâches fixes, randomisation par développeur, données observationnelles) [A13]. Le chiffre de 2025 est déclaré « out of date » par METR lui-même [A12].
  - **Anthropic, janvier 2026** : 52 ingénieurs Python découvrent la bibliothèque Trio. Le gain de temps n'est pas significatif ; le score au quiz de compréhension est de 50 % avec l'IA contre 67 % sans, et l'écart le plus fort porte sur le débogage [A17]. C'est un seul laboratoire, qui est aussi l'éditeur de l'outil, et je n'ai lu que l'extrait.
  - **Essais en entreprise, 2024-2025** : une analyse groupée de trois essais (Microsoft, Accenture, Fortune 100) donne environ 26 % de tâches en plus (écart-type 10,3 %), et un essai Google sur 96 ingénieurs trouve un gain de temps [A18]. Ces essais portent sur l'autocomplétion et le chat, pas sur des agents.
- **Enquêtes.** DORA 2025 (environ 5 000 répondants) : la corrélation entre adoption de l'IA et débit est devenue positive, mais l'IA reste associée à une **instabilité accrue**. Le rapport insiste sur les « fondations » de l'équipe (plateforme, pratiques) [A16].
- **Débat ouvert.** Après 2025, aucun essai contrôlé de qualité n'existe sur les agents. Les écarts tiennent surtout à ce qui est mesuré (temps, débit, compréhension, qualité). Le perçu dépasse systématiquement le mesuré.
- **Implication pour la configuration.**
  - Mesurer soi-même, avec ses transcriptions et le kit de coûts, plutôt que de citer un chiffre de gain.
  - Pour conseiller des clients : présenter les gains comme conditionnels (fondations, qualité) et signaler le risque sur la compréhension.

### P3. Fichiers de contexte (AGENTS.md, CLAUDE.md)

- **Ce que montrent les études.**
  - **Gloaguen et al.** (preprint, v3 du 29 septembre 2026) : sur SWE-bench avec des fichiers générés par un LLM, et sur des issues de dépôts qui ont un fichier écrit par leurs développeurs, les fichiers de contexte **n'améliorent pas la réussite en général** et augmentent le **coût d'inférence de plus de 20 %**. Les agents suivent bien les instructions, mais les vues d'ensemble du dépôt n'aident pas. Les fichiers sont utiles pour les **pratiques non standard**. Le résultat vaut pour plusieurs LLM et plusieurs agents [A8]. Selon un extrait secondaire non vérifié, les fichiers écrits par les développeurs feraient environ 7 points de mieux que ceux générés par un LLM.
  - **Lulla et al.** (preprint, 124 PR, 10 dépôts) : la durée médiane baisse de 28,64 % et les tokens de sortie de 16,58 %, avec une réussite comparable [A9].
  - **Ablation à deux agents** (preprint, juillet 2026) : aucun bénéfice sur des PR fusionnées [A10].
  - **Études descriptives** : « Agent READMEs » [A31] et « Configuration smells » (sections d'architecture et de règles fréquentes, erreurs courantes) [A32].
- **Contradiction apparente.** Gloaguen mesure le coût total et la réussite ; Lulla mesure le temps et les tokens de sortie, sur des fichiers écrits par des humains. Les deux peuvent être vrais en même temps : un fichier court et prescriptif réduit l'exploration, alors qu'une vue d'ensemble longue se paie à chaque appel sans rien rapporter.
- **Implication pour la configuration.** Cela conforte la règle déjà en place (CLAUDE.md court, détail renvoyé dans des skills). Il faut y mettre **uniquement** les conventions non standard et les commandes (uv, ruff, pytest), pas de description de l'architecture, et ne jamais laisser `/init` générer un fichier sans le relire et le couper.
- **Verdict sur la pratique.** **Adopter**, en version minimale. Le format AGENTS.md est portable vers Copilot, Codex et Cursor.

### P4. Les skills (connaissance procédurale empaquetée)

- **SkillsBench** (preprint, 86 tâches) : les skills curées ajoutent en moyenne **+16,2 points**. Le gain va de +4,5 points en génie logiciel à +51,9 en santé, et 16 tâches sur 84 régressent. Les **skills auto-générées n'apportent rien**. Les skills ciblées de 2 ou 3 modules font mieux qu'une documentation exhaustive. Claude Code avec Opus 4.5 gagne +23,3 points. **Haiku 4.5 avec skills (27,7 %) dépasse Opus 4.5 sans skills (22,0 %)** [A11].
- **Limites.** Un survey souligne que ces chiffres viennent d'un seul benchmark non relu [A11]. Une étude sur les skills en développement web (arXiv 2608.23067, « Signal or Noise? ») n'a pas été lue (voir §5).
- **Implication pour la configuration.**
  - En génie logiciel, le gain est faible.
  - Les skills paient surtout pour des **procédures spécifiques** : workflows BMAD, conventions du client, procédures de mesure des coûts.
  - Ne pas faire écrire ses skills par l'agent sans relecture.
  - Le résultat Haiku/Opus est la seule donnée qui soutienne l'idée « petit modèle + skill ≈ gros modèle ». Elle est à tester sur ses propres stories.
- **Verdict sur la pratique.** **Essayer** : quelques skills courtes et ciblées, écrites ou relues à la main.

### P5. Planifier ou spécifier avant de coder

- **SpecFirst** (preprint) : une étape de spécification comportementale améliore le taux de tests passés de +6,9 à +21,3 % sur 200 instances ProgramBench, avec 4 modèles [A33].
- **EPIC** (preprint, octobre 2026) : association exploratoire entre la qualité de la spec et la qualité du code [A34].
- **Aucune étude ne compare directement** le plan mode et un workflow spec-driven comme BMAD [A34].
- **Lien avec P1.** Les échecs étant précoces et épistémiques [A1], c'est l'argument mécaniste le plus solide en faveur d'un plan relu par un humain.
- **Verdict sur la pratique.** **Adopter**, ce qui est déjà le cas avec BMAD. La preuve directe reste modeste et ne vient que de preprints.

### P6. TDD et tests écrits par l'agent

- **TDAD** : en indiquant à l'agent quels tests relancer, les régressions sur SWE-bench Verified passent de 6,08 % à 1,82 %. Sans cela, l'agent casse environ 6,5 tests par patch. L'échantillon est petit (100 et 25 instances) [A35].
- **TDFlow** : 69,8 % sur SWE-bench Verified avec des tests qu'il génère lui-même. Selon les auteurs, l'obstacle restant est la **génération de tests**, pas la résolution [A36].
- **TDD-Bench Verified** : écrire les tests d'abord ou le code d'abord donne des performances proches [A37].
- **Risques.** Une étude porte sur la sur-utilisation des mocks dans les tests écrits par les agents [A38]. ImpossibleBench rapporte que l'agent modifie les tests pour les faire passer ; cette source n'a pas été vérifiée (lue via un blog).
- **Implication pour la configuration.**
  - Les tests d'acceptation viennent de la story et ont été **validés par un humain**.
  - Interdire à l'agent de modifier les tests existants sans le signaler (consigne et revue).
  - Relancer la suite de tests touchée par le changement avant chaque commit.
- **Verdict sur la pratique.** **Adopter** des tests fixés à l'avance. **Évaluer** le TDD intégral piloté par l'agent.

### P7. Revue de code par LLM et revue multi-agents

- **Ce que montrent les études.**
  - Les commentaires de revue produits par un LLM sont souvent actionnables. Les commentaires sur la lisibilité, les bugs et la maintenabilité sont plus souvent résolus que ceux sur la conception (étude Atlassian) [A39].
  - Sur environ 31 000 paires de revue CodeRabbit, 36,4 % des suggestions sont acceptées, et les revues agentiques sont **plus souvent invalides** [A39].
  - En industrie, BitsAI-CR (ByteDance) atteint une précision de 75 % [A39].
  - Chez Beko, le délai de fermeture des PR augmente après l'introduction de la revue automatique [A39].
  - CR-Bench (ICLR 2026) met en évidence un arbitrage entre problèmes trouvés et faux positifs [A39].
- **Multi-agents.** Anthropic indique qu'un système multi-agents de recherche consomme environ 15 fois les tokens d'un chat, contre 4 fois pour un agent seul [A40] (chiffre lu via un extrait secondaire). Je n'ai trouvé **aucune comparaison contrôlée** entre agent seul et multi-agents sur du code [A40].
- **Implication pour la configuration.**
  - La chaîne « second avis Haiku puis revue Opus » n'est ni confirmée ni infirmée par la littérature.
  - Le risque documenté est celui des faux positifs, qui coûtent du temps humain. Il faut donc mesurer le taux de constats retenus par la revue.
- **Verdict sur la pratique.** **Évaluer**, avec le protocole H3.

### P8. Long contexte et « context rot »

- **Ce que montrent les études.**
  - Dans une étude « boîte blanche » de skills d'audit, un contexte propre d'environ 11 000 caractères réussit 8 runs sur 10, contre 3 sur 10 pour des contextes d'environ 299 000 caractères. Les auteurs ne trouvent **pas de seuil stable** et décrivent le phénomène comme une distribution de fiabilité conditionnelle [A24].
  - Des moniteurs de sécurité ratent 2 à 30 fois plus d'actions dangereuses quand celles-ci arrivent après 800 000 tokens d'activité banale ; des rappels périodiques atténuent l'effet [A25].
  - Donner à un agent des outils de récupération (retrieval) n'améliore pas toujours ses résultats sur les tâches à long contexte [A26].
  - Le rapport Chroma de 2025, qui a popularisé le terme, n'a pas été relu ici et vient d'un vendeur de bases de récupération.
- **Implication pour la configuration.** Cela conforte `/clear` entre deux tâches, les sous-agents à contexte court et la lecture d'extraits plutôt que de fichiers entiers. Les petits échantillons (10 runs) en font une **piste convergente**, pas une loi.
- **Verdict sur la pratique.** **Adopter** l'hygiène de contexte.

### P9. Routage de modèles et petits modèles en sous-agents

- **Ce que montrent les études.**
  - Une revue de 2026 constate qu'**aucune source n'évalue une flotte d'agents de code en production**. Le routage vers le modèle le moins cher suffisant reste donc à tester [A30].
  - Un routeur à deux modèles complémentaires capte tout le gain de l'oracle sur une suite de benchmarks généralistes [A41].
  - D'après un blog qui cite une étude de 13,5 millions de sessions Copilot, changer de modèle en cours de session oblige à recalculer le cache, ce qui peut annuler l'économie [A42]. Je ne l'ai pas vérifié dans l'étude originale.
  - RouteLLM (85 % d'économie pour 95 % de la qualité) porte sur MT-Bench, pas sur du code.
- **Petits modèles locaux.** SWEnergy mesure l'énergie de petits modèles (SLM) sur SWE-bench [A29], mais je n'ai pas obtenu de chiffres de réussite.
- **Implication pour la configuration.**
  - Router **par tâche**, au lancement d'un sous-agent, et non au milieu d'une session, comme le fait déjà le kit de coûts.
  - Pour les modèles de 4B ou moins sur CPU, la littérature ne permet aucun pronostic en génie logiciel agentique. Il faut le mesurer (H4).
- **Verdict sur la pratique.** **Essayer** le routage par rôle. **Évaluer** les petits modèles locaux.

### P10. Mémoire persistante

- **Ce que j'ai trouvé.** Les fichiers de contexte sont décrits comme une mémoire à long terme [A31], mais je n'ai trouvé **aucune étude contrôlée** sur les mécanismes de mémoire des agents de code (MEMORY.md, mémoire vectorielle, journaux de session). Le budget ne m'a pas permis de chercher plus loin (voir §5).
- **Verdict sur la pratique.** **Évaluer**. Par prudence, suivre P3 (court, prescriptif).

### P11. Sécurité du code généré

- **Ce que montrent les études.**
  - **SusVibes** (CMU, preprint) : les tâches sont construites à partir de correctifs de vulnérabilités réelles. SWE-agent avec Claude 4 Sonnet produit **57 % de solutions fonctionnelles et 11,8 % de solutions sûres**. Les consignes de sécurité génériques ajoutées au prompt n'aident pas et peuvent faire baisser la réussite fonctionnelle [A21].
  - Des vendeurs ont depuis rapporté leurs propres scores : Cursor avec Opus 4.6 à 84,4 % fonctionnel et 7,8 % sûr (Endor Labs), et Opus 5.5 à 54,8 % (Semgrep, métrique à vérifier). Ce sont des **chiffres de vendeurs** [A22].
- **Implication pour la configuration.**
  - Ne pas compter sur une phrase « écris du code sûr » dans CLAUDE.md.
  - Mettre un **contrôle outillé** dans la CI : analyse statique de sécurité (SAST), audit des dépendances.
  - Ajouter une passe de revue orientée sécurité pour les stories qui touchent l'authentification, les entrées ou les fichiers. Pour la pile du consultant : validation dans FastAPI, autoescape de Jinja2.
- **Verdict sur la pratique.** **Adopter** le contrôle outillé ; **écarter** la consigne seule.

### P12. Dette, duplication, maintenabilité

- **Ce que montrent les études.**
  - **He et al.** (MSR 2026, différence de différences sur 807 dépôts adoptants et 1 380 dépôts témoins) : la vitesse augmente nettement mais **de façon transitoire** ; les alertes d'analyse statique et la complexité augmentent **durablement**, et cette hausse explique en partie le ralentissement ultérieur [A19]. Les chiffres +281 %, +30 % et +42 % viennent d'un blog de vendeur et n'ont pas été vérifiés dans l'article [A20].
  - **« Debt Behind the AI Boom »** (preprint, environ 304 000 commits IA, 6 275 dépôts) : 24,2 % des problèmes introduits survivent dans la dernière révision, et 22,7 % dans une version ultérieure de l'article [A23].
  - Un preprint sur les « AI-generated smells » décrit une dégradation architecturale quand la complexité croît [A43].
  - Une étude sur la durabilité du code d'agents n'est encore qu'un **protocole** (registered report ESEM 2026) [A43].
- **Implication pour la configuration.**
  - Rendre bloquants ruff et un contrôle de complexité ou de duplication.
  - Prévoir une passe de « refactor » dans les rétrospectives.
  - Suivre l'évolution des alertes par epic.
- **Verdict sur la pratique.** **Adopter** des seuils de qualité automatiques.

### P13. Coût et énergie de l'inférence

- **Ce que montrent les études.**
  - Sur SWE-bench Verified avec OpenHands et 8 modèles : environ **1 000 fois plus de tokens qu'un chat**, surtout en entrée. La consommation varie **jusqu'à 30 fois** d'un run à l'autre sur la même tâche, plus de tokens ne donne pas plus de précision, et les modèles sous-estiment leur propre coût [A27].
  - Les lectures représentent environ 76 % des tokens (mini-SWE-agent avec Sonnet 4.5) [A28].
  - Côté énergie, en local : un run SWE-bench raté consomme environ 3 005 mWh, et environ 60 % de l'énergie part dans les 10 premières étapes [A29]. Je n'ai trouvé **aucune mesure énergétique publiée pour un agent cloud** en génie logiciel.
- **Implication pour la configuration.**
  - Comparer des **distributions** de coût par story, pas des runs isolés.
  - Les gains passent d'abord par la réduction des lectures (extraits ciblés, ignore-files) et par l'arrêt précoce des trajectoires qui dérivent.
  - L'estimation EcoLogits du kit de coûts reste un modèle, pas une mesure.

## 3. Analyse transversale

**Ce qui se recoupe.** P1 (échecs précoces), P5 (spec) et P6 (tests fixés) convergent vers une même idée : il faut **valider tôt** avec des critères externes à l'agent. P3, P8 et P13 convergent vers un **contexte minimal**. P11 et P12 s'accordent sur un point : la qualité ne s'obtient pas par le prompt, mais par l'outillage et la revue.

**Ce qui est solide (plusieurs laboratoires, ou publié après relecture).**
- La qualité se dégrade quand la vitesse augmente : He et al. [A19] et DORA [A16].
- Les grosses PR d'agents sont plus souvent rejetées [A5].
- Les agents produisent du code peu sûr : SusVibes, recoupé par des vendeurs indépendants [A21][A22].
- Le perçu dépasse le mesuré : METR [A12][A13].

**Pistes portées par un seul laboratoire.** SkillsBench [A11], la boîte blanche sur le context rot [A24], TDAD [A35], SpecFirst [A33], les deux études opposées sur AGENTS.md [A8][A9], l'essai d'Anthropic [A17].

**Débats ouverts.**
1. Les fichiers de contexte aident-ils ou coûtent-ils [A8 contre A9] ?
2. Les gains de productivité des agents de fin 2025 sont-ils réels ? METR lui-même ne sait plus les mesurer [A13].
3. Le multi-agents améliore-t-il la qualité au prix d'un surcoût de 4 à 15 fois [A40] ?
4. Le routage vers des petits modèles fonctionne-t-il sur du code agentique [A30] ?
5. L'IA nuit-elle à la formation des compétences [A17] ?

**Laboratoires et sources à suivre en veille.**
- **METR** : refonte de l'étude de productivité.
- **CMU** : Vasilescu et Kästner (dette, Cursor) ; l'équipe LeiLi (SusVibes et son classement).
- **L'équipe Vechev** (AGENTS.md ; affiliation non vérifiée).
- **Treude, Baltes et coauteurs** (AGENTS.md, études de dépôts).
- **Le jeu de données AIDev et le challenge MSR 2026** : un flux d'articles sur les PR d'agents.
- **DORA**, avec son rapport annuel.
- **Anthropic Research** : essais sur les compétences.
- **Zhao, Barr, Sarro et Ye** (trajectoires Terminal-Bench).
- **Les mainteneurs de SkillsBench**.

**Problèmes que rien ne traite encore.**
- Des mesures de mémoire persistante.
- L'énergie d'un agent cloud.
- Les petits modèles de 4B ou moins en génie logiciel agentique.
- Une comparaison entre plan mode et spec-driven.
- La revue multi-agents sur du code, avec mesure des faux positifs.
- Un essai contrôlé en entreprise sur des agents, pas sur de l'autocomplétion.

**Hypothèses à tester en pratique.**

| # | Hypothèse | Protocole court | Critère de décision |
|---|---|---|---|
| H1 | Un CLAUDE.md réduit aux conventions non standard coûte moins et réussit autant qu'un CLAUDE.md long. | 6 stories de référence déjà faites, rejouées en worktree dans deux conditions : CLAUDE.md court ou long. Mesurer les tokens d'entrée et de sortie, le nombre de tours, le passage des tests d'acceptation et le nombre de constats de revue. | Adopter le court si la réussite est égale ou meilleure et le coût au moins 10 % plus bas. |
| H2 | Une skill ciblée permet à Sonnet ou Haiku d'égaler Opus sans skill sur une procédure du projet. | Une procédure (migration de route FastAPI avec ses tests), 5 répétitions par condition, à cause de la variance [A27]. | Écart de réussite de 1 sur 5 au plus, pour un coût au moins 40 % plus bas. |
| H3 | Le second avis Haiku apporte des constats que la revue Opus retient. | Sur 10 PR, compter les constats du second avis, ceux que la revue retient, et les faux positifs. | Garder le second avis si au moins 30 % de ses constats sont retenus et qu'il coûte moins de 10 % de la revue. |
| H4 | Un petit modèle local (≤ 4B, Ollama, CPU) peut servir de sous-agent de lookup ou de second avis. | 20 questions de lookup et 10 diffs, comparés à Haiku : exactitude, latence, énergie mesurée au wattmètre si possible. | Exactitude au moins égale à 90 % de celle de Haiku. |
| H5 | Un test d'acceptation écrit et figé avant le code réduit les régressions et les tests trafiqués. | 6 stories avec tests figés et protégés par un hook qui bloque leur modification, comparées à des stories où l'agent écrit ses tests. Mesurer les régressions de CI et les diffs de tests. | Moins de régressions et aucune modification de test sans justification. |
| H6 | Un critère d'arrêt (tours supérieurs à 2 fois la médiane) économise sans perdre de stories. | Rejouer les transcriptions passées et simuler la coupure. | Économie au moins 15 % pour moins de 5 % de stories qui auraient abouti. |

## 4. Affirmations

Les dates de publication sont déduites de l'identifiant arXiv (format aamm) quand la page n'a pas été ouverte. Toutes les sources ont été consultées le 2026-10-24.

Légende de la colonne « classe » :
- **E** : essai contrôlé.
- **M** : étude de dépôts ou observationnelle.
- **B** : benchmark ou expérience.
- **R** : rapport ou enquête.
- **V** : vendeur ou blog.
- Statut : **P** = preprint, **Pub** = publié après relecture.
- **(x)** : l'article a été lu par un extrait de recherche, pas ouvert.

| ref | affirmation | source (URL) | éditeur | date publi | consultée | confiance | classe |
|---|---|---|---|---|---|---|---|
| A1 | Sur 1 794 trajectoires Terminal-Bench (7 modèles, 3 scaffolds), les échecs sont surtout épistémiques, commencent dans les premières étapes et restent cachés jusqu'à ce qu'ils soient irrécupérables. | https://arxiv.org/abs/2607.09510 | Zhao, Barr, Sarro, Ye et al. | 2026-07-10 | 2026-10-24 | moyenne (un seul labo) | B, P |
| A2 | Ceka et al. 2025 identifient des stratégies récurrentes (exploration, patch-first, test-driven). | https://arxiv.org/html/2607.09510v1 | cité par Zhao et al. | 2025 | 2026-10-24 | basse (x, cité) | B, P |
| A3 | Les trajectoires qui échouent sont 12 à 82 % plus longues que celles qui réussissent (Majgaonkar et al. 2026). | https://arxiv.org/pdf/2511.00197 | Majgaonkar et al. | 2025-11 | 2026-10-24 | basse (x) | B, P |
| A4 | 20 574 sessions réelles, 7 formes récurrentes de désalignement entre développeur et agent. | https://arxiv.org/abs/2605.29442 | arXiv | 2026-05 | 2026-10-24 | basse (x) | M, P |
| A5 | 33 000 PR de 5 agents : documentation, CI et build sont les plus fusionnées ; performance et bugs les moins. Les PR rejetées sont plus grosses et échouent plus en CI. Motifs : doublons, fonctionnalité non souhaitée, désalignement. | https://arxiv.org/abs/2601.15195 | Ehsani et al., MSR 2026 | 2026-01-21 | 2026-10-24 | haute | M, Pub |
| A6 | Parmi les PR d'agents rejetées, 35,7 % sont de vrais échecs de l'agent, 31,2 % tiennent au workflow et 33,1 % sont sans motif visible. | https://www.alphaxiv.org/abs/2605.22534 | arXiv | 2026-05 | 2026-10-24 | basse (x) | M, P |
| A7 | MAST : 14 modes d'échec issus de 1 642 traces de 5 frameworks multi-agents (pas spécifique au code). | https://arxiv.org/html/2607.09510v1 | cité | 2025 | 2026-10-24 | basse (x) | B |
| A8 | Les fichiers de contexte n'améliorent pas la réussite en général et coûtent plus de 20 % d'inférence en plus. Les vues d'ensemble n'aident pas ; les fichiers sont utiles pour les pratiques non standard. | https://arxiv.org/abs/2602.11988 | Gloaguen, Mündler, Müller, Raychev, Vechev | 2026-02-12 (v3 2026-09-29) | 2026-10-24 | moyenne (un labo, P) | B, P |
| A9 | Avec AGENTS.md, la durée médiane baisse de 28,64 % et les tokens de sortie de 16,58 %, avec une réussite comparable (124 PR, 10 dépôts). | https://arxiv.org/abs/2601.20404 | Lulla, Galster, Zhang, Baltes, Treude et al. | 2026-01-28 (v2 2026-03-30) | 2026-10-24 | moyenne | B, P |
| A10 | Ablation à deux agents sur des PR réelles : aucun bénéfice du fichier de contexte ; les échecs viennent de la compétence d'implémentation. | https://arxiv.org/html/2607.27250v1 | arXiv | 2026-07 | 2026-10-24 | basse (x) | B, P |
| A11 | SkillsBench : skills curées +16,2 points (+4,5 en génie logiciel) ; skills auto-générées sans effet ; Haiku 4.5 avec skills (27,7 %) au-dessus d'Opus 4.5 sans skills (22,0 %) ; benchmark unique non relu. | https://huggingface.co/papers/2602.12670 | SkillsBench | 2026-02 | 2026-10-24 | moyenne (x, un seul benchmark) | B, P |
| A12 | METR 2025 : 16 développeurs, 246 tâches, +19 % de temps avec l'IA ; prévision −24 %, croyance après coup −20 % ; résultats déclarés « out of date ». | https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/ | METR | 2025-07-10 | 2026-10-24 | haute (essai contrôlé, P) | E, P |
| A13 | Suivi METR (étude commencée en août 2025, 57 développeurs, plus de 800 tâches) : −18 % (IC −38 % à +9 %) et −4 % (IC −15 % à +9 %) ; « very weak evidence » ; 30 à 50 % des développeurs retiennent des tâches ; refonte prévue. | https://metr.org/blog/2026-02-24-uplift-update/ | METR | 2026-02-24 | 2026-10-24 | haute (sur ce que dit METR) | E, R |
| A14 | IC 95 % de l'étude de 2025 : +2 % à +39 %. | https://metr.org/blog/2026-02-24-uplift-update/ | METR | 2026-02-24 | 2026-10-24 | haute | E |
| A15 | Une enquête METR de 2026 (349 personnes) donne une accélération médiane auto-déclarée de 3 fois. | https://andrewwegner.com/metr-ai-productivity-study-update.html | blog | 2026 | 2026-10-24 | basse (x, secondaire) | R, V |
| A16 | DORA 2025 (environ 5 000 répondants) : l'IA est associée à plus de débit, mais toujours à plus d'instabilité ; l'effet dépend des fondations de l'équipe. | https://dora.dev/insights/dora-2025-year-in-review/ | Google DORA | 2025-09 / 2025-12 | 2026-10-24 | moyenne (x) | R |
| A17 | Essai d'Anthropic (52 ingénieurs, bibliothèque Trio) : gain de temps non significatif ; compréhension 50 % avec l'IA contre 67 % sans. | https://www.anthropic.com/research/AI-assistance-coding-skills | Anthropic | 2026-01-29 | 2026-10-24 | moyenne (x, éditeur de l'outil) | E |
| A18 | Analyse groupée Microsoft, Accenture et Fortune 100 : environ +26 % de tâches (écart-type 10,3 %) ; essai Google sur 96 ingénieurs. | https://arxiv.org/html/2410.12944v2 | Google et al. | 2024-2025 | 2026-10-24 | moyenne (x) | E |
| A19 | Cursor (807 dépôts contre 1 380 témoins) : vitesse en hausse transitoire ; alertes statiques et complexité en hausse persistante, qui expliquent le ralentissement ultérieur. | https://arxiv.org/abs/2511.04427 | He, Miller, Agarwal, Kästner, Vasilescu, MSR 2026 | 2025-11 | 2026-10-24 | haute (Pub, x) | M, Pub |
| A20 | +281 % de lignes le premier mois, environ +30 % d'alertes et environ +42 % de complexité. | https://momentic.ai/blog/speed-at-the-cost-of-quality | Momentic (vendeur) | 2025-2026 | 2026-10-24 | basse | V |
| A21 | SusVibes : SWE-agent avec Claude 4 Sonnet, 57 % fonctionnel contre 11,8 % sûr ; les consignes de sécurité génériques sont inefficaces. | https://arxiv.org/abs/2512.03262 | CMU (équipe LeiLi) | 2025-12 | 2026-10-24 | moyenne (x, P) | B, P |
| A22 | Scores de vendeurs sur SusVibes : Cursor avec Opus 4.6 à 84,4 % fonctionnel et 7,8 % sûr ; Opus 5.5 à 54,8 %. | https://www.endorlabs.com/learn/agent-security-league-evaluating-the-security-of-ai-coded-software ; https://semgrep.dev/blog/2026/claude-opus-5-5-susvibes-benchmark/ | Endor Labs, Semgrep | 2026 | 2026-10-24 | basse | V |
| A23 | Environ 304 000 commits IA, 6 275 dépôts : 24,2 % des problèmes introduits survivent (22,7 % dans une version ultérieure). | https://arxiv.org/html/2603.28592v1 | arXiv | 2026-03 | 2026-10-24 | moyenne (x) | M, P |
| A24 | Context rot dans des skills d'audit : contexte d'environ 11 000 caractères, 8 runs réussis sur 10 ; contextes d'environ 299 000 caractères, 3 sur 10 ; pas de seuil stable. | https://arxiv.org/html/2607.17937v2 | arXiv | 2026-07 | 2026-10-24 | moyenne (x, N=10) | B, P |
| A25 | Des moniteurs ratent 2 à 30 fois plus d'actions dangereuses après 800 000 tokens ; des rappels atténuent l'effet. | https://arxiv.org/html/2605.12366v1 | arXiv | 2026-05 | 2026-10-24 | moyenne (x) | B, P |
| A26 | Des outils de récupération n'améliorent pas toujours les agents sur des tâches à long contexte. | https://arxiv.org/html/2603.20432v1 | arXiv | 2026-03 | 2026-10-24 | basse (x) | B, P |
| A27 | Un agent consomme environ 1 000 fois plus de tokens qu'un chat, surtout en entrée ; jusqu'à 30 fois de variance entre runs ; plus de tokens ne donne pas plus de précision ; les modèles sous-estiment leur coût. | https://arxiv.org/html/2604.22750v2 | Bai et al. | 2026-04 | 2026-10-24 | moyenne (x) | B, P |
| A28 | Les lectures représentent environ 76 % des tokens (mini-SWE-agent avec Sonnet 4.5). | https://arxiv.org/pdf/2601.16746 | SWE-Pruner | 2026-01 | 2026-10-24 | moyenne (x) | B, P |
| A29 | En local, un run SWE-bench raté consomme environ 3 005 mWh, dont environ 60 % dans les 10 premières étapes ; SWEnergy mesure l'énergie des petits modèles avec RAPL et NVML. | https://arxiv.org/pdf/2605.15206 ; https://arxiv.org/pdf/2512.09543 | arXiv | 2026-05 ; 2025-12 | 2026-10-24 | basse (x) | B, P |
| A30 | Aucune source n'évalue une flotte d'agents de code en production ; le routage « le moins cher suffisant » reste à tester. | https://arxiv.org/pdf/2608.13867 | arXiv (revue) | 2026-08 | 2026-10-24 | moyenne (x) | R, P |
| A31 | « Agent READMEs » : étude descriptive, le fichier de contexte vu comme une mémoire à long terme. | https://arxiv.org/pdf/2511.12884 | arXiv | 2025-11 | 2026-10-24 | moyenne (x) | M, P |
| A32 | « Configuration smells » dans AGENTS.md : sections fréquentes et erreurs courantes. | https://arxiv.org/pdf/2606.15828 | arXiv | 2026-06 | 2026-10-24 | basse (x) | M, P |
| A33 | SpecFirst : une spec avant le code donne +6,9 à +21,3 % de tests passés (200 instances ProgramBench, 4 modèles). | https://arxiv.org/pdf/2607.27167 | arXiv | 2026-07 | 2026-10-24 | moyenne (x) | B, P |
| A34 | EPIC : association exploratoire entre la qualité de la spec et celle du code ; aucune comparaison directe entre plan mode et spec-driven. | https://arxiv.org/pdf/2610.07534 | arXiv | 2026-10 | 2026-10-24 | basse (x) | B, P |
| A35 | TDAD : régressions de 6,08 % à 1,82 % ; environ 6,5 tests cassés par patch sans l'outil ; 100 et 25 instances. | https://arxiv.org/pdf/2603.17973 | arXiv | 2026-03 | 2026-10-24 | moyenne (x, petit N) | B, P |
| A36 | TDFlow : 69,8 % sur SWE-bench Verified avec des tests auto-générés ; le goulot est la génération de tests. | https://arxiv.org/pdf/2510.23761 | arXiv | 2025-10 | 2026-10-24 | moyenne (x) | B, P |
| A37 | TDD-Bench Verified : écrire les tests d'abord ou le code d'abord donne des performances proches. | https://www.alphaxiv.org/abs/2412.02883 | arXiv | 2024-12 | 2026-10-24 | basse (x) | B, P |
| A38 | Les agents de code produisent des tests trop mockés (étude empirique). | https://arxiv.org/pdf/2602.00409 | arXiv | 2026-02 | 2026-10-24 | basse (x, résultat non lu) | M, P |
| A39 | Revue par LLM : commentaires souvent actionnables ; 36,4 % acceptés chez CodeRabbit, avec plus de commentaires invalides ; précision de 75 % pour BitsAI-CR ; délai de fermeture des PR en hausse chez Beko ; arbitrage avec les faux positifs dans CR-Bench. | https://arxiv.org/pdf/2501.15134 ; https://www.iclr.cc/virtual/2026/10017268 ; https://repository.bilkent.edu.tr/items/8e7ac28e-5120-4c6e-84e3-e7d288c336f0 | divers (ICLR 2026 : Pub) | 2025-2026 | 2026-10-24 | moyenne (x) | M/B |
| A40 | Système multi-agents environ 15 fois les tokens d'un chat (agent seul : environ 4 fois), pour de la recherche et non du code ; aucune comparaison contrôlée sur du code trouvée. | https://academy.kspl.tech/blog/2026-05-31-multi-agent-orchestration-real-cost-2026 | blog citant Anthropic | 2025-2026 | 2026-10-24 | basse (secondaire) | V |
| A41 | Un routeur à deux modèles complémentaires capte tout le gain de l'oracle (benchmarks généralistes). | https://arxiv.org/pdf/2608.13675 | arXiv | 2026-08 | 2026-10-24 | basse (x) | B, P |
| A42 | 13,5 millions de sessions Copilot : changer de modèle en cours de session recalcule le cache et peut annuler l'économie. | https://towardsdatascience.com/the-hidden-cost-of-llm-routing-why-switching-models-costs-more/ | TDS (blog) | 2026 | 2026-10-24 | basse (secondaire) | V |
| A43 | Dégradation architecturale du code d'agents quand la complexité augmente ; une étude de durabilité n'est qu'un protocole (ESEM 2026). | https://arxiv.org/html/2605.02741v1 ; https://arxiv.org/abs/2609.04208 | arXiv | 2026-05 ; 2026-09 | 2026-10-24 | basse (x) | M, P |
| A44 | Surveys : agents de génération de code (Dong et al., v2 septembre 2025) ; résolution d'issues (Li et al., janvier 2026) ; systèmes agentiques pour le génie logiciel (Tang et Runkler, janvier 2026). | https://arxiv.org/html/2508.00083v2 ; https://papers.cool/arxiv/2601.11655 ; https://papers.cool/arxiv/2601.09822 | arXiv | 2025-2026 | 2026-10-24 | moyenne (existence) | R, P |

## 5. Pistes non suivies et recherches sans résultat

**Non suivies, faute de budget.**
- Le texte complet des surveys [A44]. J'ai choisi de vérifier les articles primaires plutôt que de suivre les citations depuis les surveys, si bien que la méthode « survey d'abord » n'a été que partiellement appliquée.
- Les citations entrantes de Gloaguen (Semantic Scholar) : y a-t-il une réplication ?
- « Signal or Noise? A Benchmark Study of Agent Skills in Web Development » (arXiv 2608.23067) : directement utile pour un front en HTML, CSS et JS vanilla.
- « Does Code Cleanliness Affect Coding Agents? » (arXiv 2605.20049).
- « Coherence Collapse » (arXiv 2603.24631) : des agents qui échouent après avoir trouvé le bon code.
- « AI Writes Faster Than Humans Can Review », étude longitudinale d'une injonction « 2x » en entreprise (arXiv 2607.01904).
- CascadeDebate (arXiv 2604.12262).
- Wink, sur la récupération des agents qui dérapent (arXiv 2602.17037).
- ImpossibleBench (triche sur les tests), dans sa version originale.
- Le rapport Chroma « Context Rot » dans sa version originale.
- Le rapport DORA 2025 dans sa version complète (chiffres exacts).
- Le texte de l'essai d'Anthropic (usages de l'IA et apprentissage).

**Cherché sans trouver.**
- Un essai contrôlé de 2026 sur des agents en entreprise.
- Une étude contrôlée de la mémoire persistante des agents de code.
- Une mesure énergétique d'un agent cloud de génie logiciel.
- L'évaluation de modèles de 4B ou moins en tant que sous-agents de code.
- Une comparaison directe entre plan mode et spec-driven.
- Une comparaison contrôlée entre agent seul et multi-agents sur du code.
- Les taux de fusion par agent (dont Claude Code) dans AIDev : les articles existent, mais les chiffres ne figuraient pas dans les extraits.
