# Digest — dimension `contexte-memoire` (tour 1, 2026-10-24)

Outils : thedotmack/claude-mem, Graphify-Labs/graphify, elstongun/leviathan, tt-a1i/archify, cathrynlavery/diagram-design.
Budget consommé : 24 appels web sur 25, environ 16 lectures de dépôt sur 20. Arrêt après le tour 2 : les questions du brief étaient couvertes et le budget web presque épuisé. Les pistes restantes sont listées en section 5.

## 1. Résumé

- Claude Code couvre déjà l'essentiel de la mémoire entre sessions de façon native. Il a CLAUDE.md, AGENTS.md et des règles par chemin. La mémoire automatique tient dans un index `MEMORY.md` de 200 lignes ou 25 Ko au plus, avec des fichiers par sujet lus à la demande. La compaction recharge CLAUDE.md. La commande `/doctor prompt-audit` repère les contradictions. Les sous-agents peuvent avoir une mémoire, et le sous-agent Explore isole l'exploration [N1–N6].
- **claude-mem** ajoute la capture automatique de chaque appel d'outil et sa compression par un modèle « observateur ». En échange, il pose 9 types de hooks, dont un PreToolUse synchrone sur Read, Bash, Grep et Glob, et fait des appels de modèle supplémentaires. Ses données vont par défaut vers un service hébergé après inscription. Son historique de sécurité et de fiabilité est lourd (secrets, API locale sans authentification, processus qui fuient). Aucun gain n'est mesuré de façon indépendante [C1–C10].
- **graphify** construit en local, sans modèle, un graphe AST de qualité correcte. Mais sa seule preuve sur du code est son propre banc : 6 questions, comparées à grep et à la lecture de fichiers, sans LSP ni Explore, à environ 140 000 tokens par requête [G1–G3]. Une issue ouverte du dépôt conteste justement ce point de comparaison [G5].
- **leviathan** n'est pas un outil de code. C'est un index plein texte (FTS5) pour des jeux d'enregistrements : tickets, logs, exports. Son module de mémoire à « slots » versionnés traite bien la péremption sur le papier, mais le dépôt a 19 jours et un seul contributeur [L1–L4].
- **archify** et **diagram-design** sont des skills chargées à la demande, sans coût par tour hors leur description. diagram-design se dit elle-même moins adaptée que Mermaid pour la documentation versionnée [D1]. archify interroge son serveur toutes les 24 h pour vérifier les mises à jour [A2].
- La littérature récente montre trois choses. Un index structurel aide surtout sur les changements multi-fichiers [R3]. Les résumés en langage naturel restituent mal le comportement du code (4/45 questions, contre 27/45 avec le code source) [R4]. L'empoisonnement de mémoire est un risque réel, y compris pour la mémoire de Claude Code [R6, R7].

## 2. Fiches outils

### 2.1 thedotmack/claude-mem

- **Ce que c'est** : un plugin Claude Code (marketplace), soit des hooks, un worker HTTP local géré par Bun, SQLite avec FTS5, Chroma pour la recherche vectorielle, un serveur MCP et 29 skills [C1, C2].
  - Les hooks couvrent Setup, SessionStart (injection de contexte), UserPromptSubmit, PreToolUse (`file-context`, sur `Read|Bash|Grep|Glob`, synchrone, délai 15 s), PostToolUse et PostToolUseFailure (observation, asynchrones), Stop (résumé), SubagentStop et SessionEnd [C2].
  - **Contexte injecté** :
    - environ 1 579 tokens plus 13 schémas d'outils MCP à chaque session, mesuré par un utilisateur en avril 2026 [C3] ;
    - les descriptions des 29 skills relues à chaque appel (le corps des skills fait 210 000 caractères au total, chargé à la demande ; la taille des seules descriptions n'a pas été mesurée) ;
    - un contexte de fichier ajouté avant chaque Read, Bash, Grep ou Glob.
  - Le README annonce « ~10x token savings » pour le parcours de recherche en 3 couches, sans protocole [C1].
- **Ce qu'il capture** : toutes les entrées et sorties d'outils. Un « observateur » (un modèle) les compresse en observations. La compression tourne soit sur le service hébergé claude-mem (essai gratuit de 30 jours, « memory runs off-plan »), soit sur une clé OpenRouter ou Gemini, soit sur le forfait Anthropic de l'utilisateur [C1]. Sans service hébergé, chaque session consomme donc du quota Max en plus.
- **Stockage et secrets** : les données sont dans `~/.claude-mem/` (SQLite et Chroma), avec une synchronisation optionnelle vers cmem.ai [C1].
  - La confidentialité repose sur des balises `<private>` posées à la main [C4].
  - La rédaction automatique ne reconnaissait que les clés au format d'un fournisseur (AWS, GitHub, OpenAI…). `password=…` et `Authorization: Bearer` étaient stockés en clair, et sous Windows le filtre de commandes ignorait l'outil PowerShell. La correction (octobre 2026) est **optionnelle** : `CLAUDE_MEM_REDACT_GENERIC_ENABLED=true` [C5].
  - Une API locale sans authentification renvoyait les clés des fournisseurs en clair, et un outil MCP lisait n'importe quel fichier, `~/.ssh` compris, ce qui l'expose à l'injection de prompt. C'est corrigé en septembre 2026 [C6].
- **Preuves d'efficacité** : aucune mesure indépendante trouvée. Les articles sont des tutoriels (DataCamp, Medium, Augment) [C7]. À l'inverse, des issues signalent des coûts : un observateur à 17 $ en 3 h (#1742), des centaines de processus Claude CLI fuités (#1090), un compactage de l'observateur qui consomme environ 97 % du volume de prompts (#2108), toutes fermées [C8].
- **Maturité** :
  - créé le 2025-08-31 ; 102 745 étoiles ; 100 contributeurs et 100 commits en 90 jours (valeurs qui semblent plafonnées par la collecte) ; v15.0.2 du 2026-10-23, soit 15 versions majeures en 14 mois ; 110 issues ouvertes [M].
  - Anomalies : le README promeut un jeton crypto « CMEM » que l'auteur dit soutenir [C1]. Une source de mars 2026 décrit la licence comme AGPL-3.0, alors qu'elle est aujourd'hui Apache-2.0 [C7, M].
  - Des régressions de versions sous Windows ont tué le worker à chaque hook (#3857 et #3940, septembre 2026) [C9].
- **Risques** : hooks sur tous les outils ; données de session envoyées à un tiers si l'observateur hébergé est choisi ; secrets génériques en clair par défaut ; skill `agent-cost-report` en doublon du plugin de coûts maison ; surface d'attaque (worker HTTP, MCP).
- **Compatibilité** : support Windows documenté, avec un lanceur `.exe` dans `%LOCALAPPDATA%` [C1]. Fonctionne aussi avec Codex, Cursor, OpenCode et d'autres [M].
- **Équivalent natif** : la mémoire automatique, activée par défaut, locale à la machine, propre à chaque dépôt et partagée entre worktrees [N1]. Elle ignore volontairement ce qui se déduit du code (architecture, chemins, correctifs) [N1]. claude-mem capture justement cela, alors que les résultats de [R4] suggèrent qu'un résumé restitue mal le comportement du code.
- **Verdict provisoire : `Écarter`.** Le coût par tour et le quota consommé sont réels, la sécurité est fragile, les données partent par défaut vers un service hébergé, et aucun gain n'est mesuré au-delà de la mémoire native. À réévaluer seulement si une mesure indépendante paraît.

### 2.2 Graphify-Labs/graphify

- **Ce que c'est** :
  - Une CLI Python (`uv tool install graphifyy`) et une skill `/graphify`. Le code est analysé par tree-sitter (environ 40 langages), en local et sans modèle. La documentation, les PDF et les images passent par un modèle. Le résultat est `graph.json`, `GRAPH_REPORT.md` et `graph.html`, avec les commandes `query`, `path` et `explain` [G1].
  - **Contexte injecté** :
    - la skill fait 47,5 k caractères (`skill-windows.md` : 49,9 k), chargée quand on l'appelle ;
    - le mode « always-on » ajoute 1 159 caractères dans CLAUDE.md, avec une règle qui impose de lancer `graphify query` avant tout grep ou toute lecture, y compris dans chaque prompt de sous-agent [G4] ;
    - il ajoute aussi un hook PreToolUse avant les recherches et les lectures [G1].
  - La description de la skill l'appelle pour « any question about a codebase » [G5].
- **Problème résolu** : naviguer dans un grand dépôt et ses relations sans tout relire.
- **Preuves** :
  - Le banc est celui de l'éditeur. Sur ERPNext (environ 1 M de lignes, n = 6 questions, Opus 4.8, au plus 14 tours), la couverture des faits clés passe de 70,8 % avec grep et lecture à 82,0 % avec graphify, pour environ 140 000 tokens par requête [G2].
  - Les autres chiffres (LOCOMO, LongMemEval) mesurent la mémoire conversationnelle, pas le code [G2].
  - Un audit manuel trouve 12 arêtes INFERRED correctes sur 12 dans FastAPI [G2].
  - Les retours tiers vont de « 71x » (contenu promotionnel) à environ 8 % d'économie dans un test vidéo comparant deux sessions [G6]. La revue roborhythms ne l'a pas testé elle-même [G7].
  - Rien ne compare graphify au LSP ni au sous-agent Explore.
- **Défauts vérifiés** :
  - Le hook PreToolUse est resté inactif après la suppression des outils Grep et Glob dans Claude Code v2.1.117. L'issue #578 a été **fermée le jour même** (2026-04-27), donc la revue [G7], qui le disait non corrigé, est périmée [G8].
  - Encore ouvertes : des nœuds périmés après `--update` (#2908), aucune détection d'un graphe périmé ou partiel (#2841), des communautés non déterministes (#1667), des collisions d'ID entre fichiers de même nom de base (#1829), et la description de skill trop large (#2216) [G5, G9].
- **Maturité** : créé le 2026-04-03 ; **134 266 étoiles en 6 mois** ; 1 609 issues ouvertes ; v0.9.95 du 2026-10-23 ; entreprise YC S26 avec une offre Cloud payante mise en avant dans le README [M, G1]. Ces étoiles sont hors norme, et le README est en partie promotionnel (« Cut agent token spend by 80% » sans source).
- **Risques** :
  - Les requêtes sont journalisées par défaut dans `~/.cache/graphify-queries.log` (désactivable). Il n'y a pas de télémétrie [G1].
  - Le mode always-on détourne toutes les recherches vers un graphe qui peut être périmé.
  - Pour la documentation, le fournisseur de modèle est choisi automatiquement selon les clés d'API présentes (Gemini en premier). Il faut `GRAPHIFY_BACKEND=none` ou `--code-only` pour rester local [G1].
  - Le git hook d'installation écrit des chemins absolus (#3129) [G9].
- **Compatibilité** : Windows explicitement pris en charge (`--platform windows`), plus une vingtaine d'agents, dont Codex, Cursor et Copilot [G1].
- **Équivalent natif** : les outils natifs de recherche, le sous-agent Explore (lecture seule, qui garde l'exploration hors du contexte principal) [N4] et le LSP par plugin (définitions et références, déjà installé ici avec `pyright-lsp`). Aucun ne construit de graphe ni de « god nodes ».
- **Verdict provisoire : `Évaluer`.** À tester uniquement en mode code seul, à la demande, sans le mode always-on, contre grep, LSP et Explore sur un dépôt réel (protocole en 3.4). Les preuves actuelles (n = 6, un seul éditeur, sans comparaison au LSP) ne suffisent pas.

### 2.3 elstongun/leviathan

- **Ce que c'est** : un binaire Rust qui indexe en FTS5 (SQLite) des enregistrements JSONL, CSV ou SQL. Il offre une CLI, une skill (3,5 k caractères, à la demande), un serveur MCP optionnel (« ~640 tokens per session ») et une mémoire optionnelle (`remember`, `recall`, briefing de début de session, hooks via `leviathan wrap claude --hooks`) [L1].
- **Problème résolu** : retrouver quelques enregistrements pertinents dans de gros exports (tickets, logs) sans les lire avec grep. Pour la mémoire : des faits à clé dont la nouvelle valeur remplace l'ancienne, ce qui traite la contradiction et la péremption [L1, L2].
- **Preuves** : bancs de l'auteur, sur des données synthétiques.
  - Index : 436 tokens médians contre 107 122 pour la meilleure stratégie grep, sur 1 M d'enregistrements [L1].
  - Mémoire, sur 300 sessions : 736 tokens au démarrage et 0 % de valeurs périmées, contre 33 313 tokens et 73,8 % de valeurs périmées pour un `MEMORY.md` lu en entier [L3].
  - Limite : la référence « MEMORY.md lu en entier » ne correspond pas à la conception native (index plus fichiers par sujet, 200 lignes ou 25 Ko, rappel à élaguer les entrées périmées) [N1]. La comparaison est donc biaisée en faveur de l'outil. L'auteur reconnaît que « The workload is synthetic » [L2].
- **Maturité** : créé le **2026-10-05** (19 jours) ; **1 seul contributeur** ; 855 étoiles ; v0.2.0 ; 6 commits en 90 jours [M].
- **Risques** : faibles côté sécurité. L'index est en lecture seule, l'outil hors ligne, le code sans `unsafe`, et les secrets sont refusés d'office à l'écriture en mémoire [L1, L2]. Le risque principal est l'abandon du projet.
- **Compatibilité** : binaire unique (des binaires précompilés sont publiés) ; 24 agents via `wrap` [L1]. Windows n'a pas été vérifié.
- **Équivalent natif** : aucun pour l'indexation de jeux de données. Pour la mémoire, c'est la mémoire automatique [N1].
- **Verdict provisoire : `Hors périmètre`** pour la configuration de développement. À garder en tête pour des missions client qui analysent de gros exports (tickets, logs). L'idée de faits à clé avec historique est à retenir pour traiter la dérive de la mémoire.

### 2.4 tt-a1i/archify

- **Ce que c'est** : une skill (installée par `npx skills add`), avec un `SKILL.md` de 18,9 k caractères et des références lues à la demande, dont deux de 43 à 50 k caractères. L'agent écrit un JSON typé, qu'une CLI Node déterministe valide puis compile en HTML interactif autonome. Le modèle de contenu compte 10 types de diagrammes, des pages « explainer » et un comparatif avant/après d'architecture [A1, M].
- **Problème résolu** : des diagrammes d'architecture interactifs, et dans le mode dépôt, des nœuds reliés au code (commit et lignes).
- **Preuves** :
  - Le banc de l'auteur donne aux modèles sans la skill un premier diagramme utilisable 8 fois sur 15 (53 %). Il ne mesure pas la précision d'archify [A3].
  - Une revue souligne que la validation vérifie le dessin, pas le système ; le lien au code n'existe qu'en mode dépôt et seulement si Node tourne [A3].
  - Aucun audit indépendant de fidélité n'a été trouvé.
- **Maturité** : créé le 2026-04-15 ; **88 635 étoiles en 6 mois** ; 299 issues ouvertes ; v3.2.0 du 2026-10-19 [M]. Les sponsors du README sont des revendeurs d'API à prix cassés (« 1 % » à « 8 % » des tarifs officiels) [A1], ce qui est un signal de confiance faible.
- **Risques** : un contrôle de mise à jour interroge un manifeste toutes les 24 h environ. Le serveur voit l'adresse IP et l'heure, mais aucune donnée de projet selon le README [A2]. Node est requis. La sortie HTML n'est pas facile à comparer dans une PR.
- **Compatibilité** : Cursor, Claude Code, Codex et OpenCode [A1]. Windows n'a pas été vérifié.
- **Équivalent natif** : Mermaid écrit par l'agent. Le rendu Mermaid par GitHub est une croyance non vérifiée dans ce run.
- **Verdict provisoire : `Évaluer`.** Intéressant pour expliquer une architecture à un client (HTML interactif, lien au code). Mais la fidélité n'est pas prouvée, le dépôt envoie une requête réseau périodique et le signal des sponsors est mauvais. Pour la documentation BMAD versionnée, Mermaid reste plus simple.

### 2.5 cathrynlavery/diagram-design

- **Ce que c'est** : une skill et un plugin Claude Code, avec un `SKILL.md` de 30,8 k caractères (chargé quand on l'appelle) et des références à la demande, dont une de 106 k caractères pour les icônes. La sortie est un fichier HTML avec SVG inline, dans un style éditorial imposé : 45 types de diagrammes, import depuis Mermaid, draw.io ou Excalidraw, export PNG ou SVG [D1, M].
- **Problème résolu** : des diagrammes de qualité publication (présentations, articles, livrables).
- **Preuves** : aucune mesure. La revue la plus détaillée (andrew.ooo) lit le dépôt sans le tester [D3]. Le README reconnaît ses limites : la sortie dépend du modèle, une même demande peut donner deux mises en page différentes, et le format n'est pas comparable dans une PR. « For docs that live in Git and change every sprint, Mermaid is still the better fit » [D1].
- **Maturité** : créé le 2026-04-16 ; 60 614 étoiles ; 62 contributeurs ; aucune release GitHub (version dans `plugin.json`) [M].
- **Risques** : pas de serveur ni de télémétrie. La seule requête réseau sert à charger des polices Google Fonts, que l'option `system fonts` évite [D2]. Licence MIT.
- **Compatibilité** : plugin Claude Code, Codex, Copilot et une dizaine d'hôtes Agent Skills [D1]. Windows n'a pas été vérifié, mais le format (HTML et SVG) ne dépend pas de l'OS.
- **Équivalent natif** : Mermaid écrit par l'agent (voir 2.4).
- **Verdict provisoire : `Essayer`**, pour les livrables client et les présentations seulement. Le risque est faible et la skill ne coûte rien entre deux appels. Pour la documentation de dépôt, Mermaid reste le choix, comme l'auteure le recommande.

## 3. Analyse de catégorie

### 3.1 Doublons et complémentarités

- **Mémoire entre sessions** : claude-mem, la mémoire de leviathan et la mémoire automatique native se recouvrent. Aucun n'est strictement meilleur que les autres.
  - La mémoire native gagne sur le coût, l'absence de dépendance et la sécurité. Sa limite : pas de recherche, et la péremption gérée par un simple rappel à élaguer.
  - leviathan gagne sur la péremption (faits à clé et historique) et sur les secrets (refusés d'office). Sa limite : écriture explicite et projet de 19 jours.
  - claude-mem gagne sur la capture automatique et la recherche, mais perd sur le coût, la sécurité et la fiabilité.
- **Compréhension du code** : graphify complète, sans les remplacer, grep, le LSP et Explore. Ses atouts sont le graphe global, les communautés et les chemins A → B. Ses limites : le graphe peut être périmé et il n'y a pas de numéros de ligne [G7].
- **Diagrammes** : archify et diagram-design se recouvrent partiellement. archify vise l'exploration interactive et le lien au code. diagram-design vise l'esthétique éditoriale et la stabilité du style. Mermaid gagne pour tout ce qui est versionné. Aucun n'est strictement meilleur.

### 3.2 État de l'art hors liste et fonctions natives

- **Fonctions natives de Claude Code**, sources [N1] à [N6] :
  - CLAUDE.md de moins de 200 lignes, sous-dossiers et règles `paths:` chargés à la demande ;
  - CLAUDE.md racine rechargé après `/compact` ;
  - `/doctor prompt-audit` pour les instructions contradictoires ou périmées ;
  - mémoire automatique et mémoire de sous-agent (`memory: project`) ;
  - sous-agent Explore en lecture seule ;
  - **coût en contexte affiché par plugin** (« Every turn » et « When invoked ») et commande `claude plugin details <nom>` qui donne les tokens « Always-on ».
- **Ingénierie du contexte** : Anthropic recommande la récupération au moment du besoin (glob, grep, head) plutôt qu'un index pré-calculé. Les sous-agents rendent un résumé de 1 000 à 2 000 tokens [R2]. Le rapport de Chroma montre que la performance baisse avec la longueur du contexte, sur 18 modèles. Sur LongMemEval, les prompts ciblés (environ 300 tokens) battent nettement l'historique complet (environ 113 000 tokens) [R1].
- **Récupération de code** :
  - Un index structurel dans le harness améliore la localisation et la résolution, sans coût supplémentaire. Il ne fait pas moins bien que grep piloté par l'agent, mais le gain dépend des changements multi-fichiers (SWE-PolyBench, SWE-bench Pro, un seul modèle) [R3].
  - Des squelettes de type UML ou signatures ne résolvent pas plus d'issues que la suppression du reste du fichier (N = 70, p = 0,75). Les résumés restituent mal le comportement : 4/45 contre 27/45 avec le code source [R4]. Ce résultat va contre les mémoires « résumées » et les rapports de graphe, au moins pour répondre à des questions de comportement.
  - Cursor (éditeur) mesure +12,5 % de précision en moyenne avec la recherche sémantique ajoutée à grep [R5].
  - La carte de dépôt d'Aider classe les fichiers par graphe dans un budget de 1 000 tokens par défaut [R8].
  - Serena (outils LSP par MCP) existe, mais seules des évaluations de l'éditeur ont été trouvées [R9].

### 3.3 Problèmes que rien ne traite bien

- **Empoisonnement et dérive de la mémoire** :
  - Cisco a empoisonné le `MEMORY.md` de Claude Code par un dépôt non fiable, avec des conseils non sécurisés qui persistaient entre projets. Anthropic a retiré les mémoires utilisateur du prompt système en v2.1.50 [R7].
  - MPBench donne 50,46 % de réussite moyenne aux attaques, et plus l'agent écrit en mémoire, plus il est vulnérable [R6].
  - claude-mem, qui écrit à chaque outil, maximise cette surface. Aucun des outils ne lie chaque mémoire à sa source et à son autorité.
- **Péremption** : graphify ne détecte pas un graphe périmé (#2841). La mémoire native se contente d'un rappel à élaguer. Aucune étude ne mesure la péremption des mémoires des agents de code ; la recherche n'en a pas trouvé.
- **Dégradation sur longue session (« context rot »)** : aucun outil de la liste ne mesure la dégradation en cours de session. La seule parade documentée reste `/clear`, les sous-agents et la compaction.
- **Bruit des mesures** : selon [R4], 9 % des résultats changent entre deux exécutions identiques à température 0. Les gains de quelques points (graphify : +11 points sur n = 6) sont sous ce bruit.

### 3.4 Hypothèses à tester en pratique

1. **graphify contre grep, LSP et Explore** :
   - Tâche : 15 questions transverses (« qui appelle… », « chemin de la requête X à la table Y », « impact de renommer Z ») sur un dépôt FastAPI réel de 10 à 30 k lignes ; graphify en mode `--code-only`, sans hook always-on.
   - Mesures : faits corrects jugés à l'aveugle, tokens et tours (avec `/agent-cost-kit:mesurer-couts`), puis erreurs dues à un graphe périmé après 10 commits sans `update`.
   - Décision : adopter si la couverture gagne au moins 15 points et le coût baisse d'au moins 20 %, sur deux exécutions.
2. **claude-mem contre la mémoire native**, seulement si 1 est positif ou si une source indépendante paraît :
   - Tâche : 8 sessions BMAD sur deux semaines, chacune exigeant de rappeler une décision antérieure ; observateur sur clé locale, rédaction générique activée.
   - Mesures : tokens par tour (`claude plugin details`, transcriptions), quota consommé, rappels corrects et valeurs périmées citées.
   - Décision : adopter si les rappels corrects gagnent au moins 20 points avec un surcoût de tokens de 5 % au plus.
3. **Context rot sur une story** :
   - Tâche : la même story développée en une longue session, contre des sessions découpées par `/clear` avec un fichier de reprise.
   - Mesures : défauts trouvés en revue, tokens, nombre de compactions.
   - Décision : formaliser le découpage si le nombre de défauts baisse.
4. **Diagrammes** :
   - Tâche : 3 diagrammes (architecture, séquence, flux de données) d'un projet existant, faits avec archify, diagram-design et Mermaid.
   - Mesures : arêtes correctes vérifiées contre le code, tokens de génération, coût d'une modification, lisibilité pour un client (avis humain).
   - Décision : garder Mermaid par défaut et un outil pour les livrables si sa fidélité est au moins égale.

## 4. Affirmations

| ref | affirmation | source (URL) | éditeur | date publi | consultée | confiance | classe |
|---|---|---|---|---|---|---|---|
| N1 | Mémoire automatique : index MEMORY.md (200 lignes ou 25 Ko chargés), fichiers par sujet, locale à la machine, par dépôt ; ignore architecture, chemins et correctifs ; rappel à élaguer les entrées périmées | https://code.claude.com/docs/en/memory | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| N2 | CLAUDE.md : moins de 200 lignes recommandé ; sous-dossiers et règles `paths:` à la demande ; CLAUDE.md racine rechargé après /compact ; AGENTS.md lu en l'absence de CLAUDE.md | https://code.claude.com/docs/en/memory | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| N3 | `/doctor prompt-audit` détecte les instructions périmées ou contradictoires | https://code.claude.com/docs/en/memory | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| N4 | Explore : sous-agent en lecture seule, qui garde l'exploration hors du contexte principal ; 3 niveaux d'exhaustivité | https://code.claude.com/docs/en/sub-agents | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| N5 | Mémoire de sous-agent (`memory: user/project/local`), 200 lignes ou 25 Ko de MEMORY.md chargés | https://code.claude.com/docs/en/sub-agents | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| N6 | Coût en contexte affiché par plugin (« Every turn » et « When invoked ») ; `claude plugin details` donne les tokens « Always-on » | https://code.claude.com/docs/en/discover-plugins | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| C1 | claude-mem : architecture, inscription et observateur hébergé par défaut (« off-plan »), synchronisation cmem.ai, jeton CMEM, support Windows | https://github.com/thedotmack/claude-mem (README) | auteur de l'outil | 2026-10 | 2026-10-24 | haute (pour la description) | source primaire, vendeur |
| C2 | Hooks de claude-mem : 9 événements, PreToolUse synchrone sur Read, Bash, Grep et Glob | https://github.com/thedotmack/claude-mem/blob/main/plugin/hooks/hooks.json | auteur de l'outil | 2026-10 | 2026-10-24 | haute | code |
| C3 | claude-mem injecte environ 1 579 tokens et 13 schémas MCP par session | https://github.com/anthropics/claude-code/issues/50133 | utilisateur | 2026-04-17 | 2026-10-24 | moyenne | retour d'usage |
| C4 | Confidentialité par balises `<private>` ; injection de commandes critique corrigée (2025-12) | https://github.com/thedotmack/claude-mem/blob/main/SECURITY.md | auteur de l'outil | 2026 | 2026-10-24 | haute | source primaire |
| C5 | Rédaction limitée aux clés de fournisseurs ; secrets génériques en clair ; correctif optionnel (`REDACT_GENERIC_ENABLED`) ; le filtre de commandes ignorait PowerShell | https://github.com/thedotmack/claude-mem/issues/4745 | utilisateur et mainteneurs | 2026-10-13 (fermée le 15) | 2026-10-24 | haute | issue |
| C6 | API du worker sans authentification qui exposait les clés ; lecture de fichiers arbitraires par un outil MCP ; corrigé | https://github.com/thedotmack/claude-mem/issues/3861 | utilisateur | 2026-09-03 (fermée le 11) | 2026-10-24 | haute | issue |
| C7 | Retours publiés : tutoriels positifs, pas d'évaluation longue ; licence décrite comme AGPL-3.0 à l'époque | https://www.datacamp.com/tutorial/claude-mem-guide | DataCamp | 2026 | 2026-10-24 (résumé de recherche) | basse | agrégateur |
| C8 | Coûts excessifs de l'observateur (17 $ en 3 h ; processus fuités ; environ 97 % du volume de prompts) | https://github.com/thedotmack/claude-mem/issues/1742 · /1090 · /2108 | utilisateurs | 2026-02 à 04 | 2026-10-24 | moyenne (corrigé depuis) | issues |
| C9 | Boucle de « kill » du worker à chaque hook après décalage de version (régressions) | https://github.com/thedotmack/claude-mem/issues/3857 · /3940 | utilisateurs | 2026-09 | 2026-10-24 | moyenne | issues |
| G1 | graphify : analyse AST locale sans modèle ; mode always-on avec hook ; journal des requêtes ; pas de télémétrie ; offre Cloud payante | https://github.com/Graphify-Labs/graphify (README) | éditeur (YC S26) | 2026-10 | 2026-10-24 | haute (pour la description) | source primaire, vendeur |
| G2 | Banc code : 70,8 % → 82,0 % de faits clés (n = 6, ERPNext), environ 140 000 tokens par requête ; 12 arêtes INFERRED correctes sur 12 | https://github.com/Graphify-Labs/graphify/blob/v8/BENCHMARKS.md | éditeur | 2026-07-05 | 2026-10-24 | basse (auto-évalué, n = 6) | banc de l'éditeur |
| G3 | Les bancs LOCOMO et LongMemEval mesurent la mémoire conversationnelle, pas le code | idem G2 | éditeur | 2026-07-05 | 2026-10-24 | haute | source primaire |
| G4 | Bloc CLAUDE.md always-on (1 159 caractères) : interroger le graphe avant tout grep, y compris dans les sous-agents | https://github.com/Graphify-Labs/graphify/blob/v8/graphify/always_on/claude-md.md | éditeur | 2026 | 2026-10-24 | haute | code |
| G5 | Issue ouverte : la description de skill fait passer toute question par un graphe peut-être périmé ; le gain disparaît face à grep et quelques lectures | https://github.com/Graphify-Labs/graphify/issues/2216 | contributeur | 2026-07-26 | 2026-10-24 | moyenne | issue |
| G6 | Gains tiers de 8 % (test vidéo) à « 71x » (contenu promotionnel) | https://www.mindstudio.ai/blog/graphify-claude-code-knowledge-graph-large-codebase-70x | MindStudio et autres | 2026 | 2026-10-24 (résumé de recherche) | basse | agrégateur |
| G7 | Revue : outil non testé par l'auteur ; pas de numéros de ligne ; rapport jusqu'à 131 000 caractères ; graphe périmé sans hook git | https://www.roborhythms.com/graphify-review/ | blog | 2026-05-28 | 2026-10-24 | basse | blog |
| G8 | Hook inactif après la suppression de Grep et Glob dans Claude Code v2.1.117 : corrigé le jour même | https://github.com/Graphify-Labs/graphify/issues/578 | utilisateur | 2026-04-27 | 2026-10-24 | haute | issue |
| G9 | Issues ouvertes : nœuds périmés (#2908), pas de détection de graphe périmé (#2841), non-déterminisme (#1667), collisions d'ID (#1829), chemins absolus (#3129) | https://github.com/Graphify-Labs/graphify/issues | utilisateurs | 2026-07 à 08 | 2026-10-24 | haute | issues |
| L1 | leviathan : FTS5 et BM25, 436 contre 107 122 tokens médians à 1 M d'enregistrements (synthétique) ; MCP environ 640 tokens par session ; hors ligne | https://github.com/elstongun/leviathan (README) | auteur | 2026-10 | 2026-10-24 | moyenne | source primaire, auto-évalué |
| L2 | Mémoire : faits à clé, historique, secrets toujours refusés ; « The workload is synthetic » | https://github.com/elstongun/leviathan/blob/main/docs/MEMORY.md | auteur | 2026-10 | 2026-10-24 | moyenne | source primaire |
| L3 | Banc mémoire : 736 contre 33 313 tokens ; 0 % contre 73,8 % de valeurs périmées (référence non native) | https://github.com/elstongun/leviathan/blob/main/bench/results/MEMORY_SUMMARY.md | auteur | 2026-10-09 | 2026-10-24 | basse | banc de l'auteur |
| L4 | Maturité de leviathan : créé le 2026-10-05, 1 contributeur | depots.json (collecte du 2026-10-24) | GitHub | 2026-10-24 | 2026-10-24 | haute | métadonnées |
| A1 | archify : JSON typé, CLI Node de validation, 10 types ; sponsors revendeurs d'API | https://github.com/tt-a1i/archify (README) | auteur | 2026-10 | 2026-10-24 | haute (description) | source primaire |
| A2 | Contrôle de mise à jour : GET d'un manifeste toutes les 24 h environ (IP et heure visibles) | idem A1 | auteur | 2026-10 | 2026-10-24 | haute | source primaire |
| A3 | La validation vérifie le dessin, pas le système ; référence de l'auteur : 8/15 diagrammes utilisables sans la skill | https://andrew.ooo/posts/archify-review-verified-architecture-diagrams-agent-skill/ | blog | 2026 | 2026-10-24 (résumé de recherche) | basse | blog |
| D1 | diagram-design : HTML et SVG, 45 types ; « Mermaid is still the better fit » pour la documentation versionnée | https://github.com/cathrynlavery/diagram-design (README) | auteure | 2026-10 | 2026-10-24 | haute | source primaire |
| D2 | Pas de télémétrie ; seule requête réseau : Google Fonts (évitable) | https://github.com/cathrynlavery/diagram-design/blob/main/PRIVACY.md | auteure | 2026-10-01 | 2026-10-24 | haute | source primaire |
| D3 | Revue la plus détaillée faite sans installation ni exécution | https://andrew.ooo/posts/diagram-design-review-editorial-diagrams-agent-skill/ | blog | 2026-10 | 2026-10-24 (résumé de recherche) | basse | blog |
| M | Métadonnées des dépôts (étoiles, dates, contributeurs, releases) | `veille-agents-code/data/depots.json` | GitHub | 2026-10-24 | 2026-10-24 | haute | métadonnées |
| R1 | Context rot : la performance baisse avec la longueur sur 18 modèles ; LongMemEval ciblé (environ 300 tokens) bien meilleur que complet (environ 113 000) ; un seul distracteur suffit à dégrader | https://www.trychroma.com/research/context-rot | Chroma | 2025-07-14 | 2026-10-24 | haute (étude primaire, éditeur d'une base vectorielle) | rapport technique |
| R2 | Récupération au moment du besoin (glob, grep) dans Claude Code ; sous-agents qui rendent 1 000 à 2 000 tokens ; compaction ; notes structurées | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | Anthropic | 2025-09-29 | 2026-10-24 | haute | source primaire |
| R3 | Un index structurel améliore localisation et résolution sans surcoût ; pas de régression face à grep piloté par l'agent ; gain lié aux changements multi-fichiers | https://arxiv.org/abs/2606.22417 | Bhola et al. | 2026-06-21 | 2026-10-24 | moyenne (préprint, un seul modèle, chiffres absents du résumé) | article |
| R4 | Résumés : 4/45 contre 27/45 avec le source ; squelettes pas meilleurs que la suppression (N = 70, p = 0,75) ; 9 % de résultats changent à température 0 | https://arxiv.org/abs/2607.09691 | Sam-Bodden | 2026-06-19 | 2026-10-24 | moyenne (préprint, un seul auteur) | article |
| R5 | Recherche sémantique : +12,5 % de précision (de 6,5 à 23,5 %) ; +2,6 % de rétention du code au-delà de 1 000 fichiers | https://cursor.com/en-US/blog/semsearch | Cursor | n.d. (non vérifiée) | 2026-10-24 (résumé de recherche) | moyenne (éditeur) | blog de l'éditeur |
| R6 | MPBench : 50,46 % de réussite moyenne des attaques par empoisonnement de mémoire ; plus l'agent écrit, plus il est vulnérable | https://arxiv.org/pdf/2606.04329 | auteurs ICML 2026 | 2026-06 | 2026-10-24 (résumé de recherche) | moyenne | article |
| R7 | Empoisonnement du MEMORY.md de Claude Code par un dépôt non fiable ; mesure d'atténuation en v2.1.50 | https://blogs.cisco.com/ai/identifying-and-remediating-a-persistent-memory-compromise-in-claude-code | Cisco | 2026-04-01 | 2026-10-24 | haute | recherche sécurité |
| R8 | Carte de dépôt d'Aider : classement par graphe de dépendances, 1 000 tokens par défaut, taille adaptée au chat | https://aider.chat/docs/repomap.html | Aider | n.d. | 2026-10-24 | haute | doc officielle |
| R9 | Serena : navigation par symboles (LSP) par MCP ; seules des évaluations de l'éditeur trouvées | https://archestra.ai/mcp-catalog/oraios__serena | catalogue | n.d. | 2026-10-24 (résumé de recherche) | basse | agrégateur |

## 5. Pistes non suivies et recherches sans résultat

- **Non trouvé** :
  - une évaluation indépendante et mesurée de claude-mem (tokens, qualité) ; les recherches Reddit et HN n'ont rien donné d'utilisable ;
  - une comparaison de graphify au LSP ou au sous-agent Explore ;
  - une étude de la péremption des mémoires des agents de code ;
  - des retours d'usage sur leviathan, trop récent.
- **Non suivi, faute de budget** :
  - le contenu exact de l'injection SessionStart de claude-mem (code du hook `context`) et la taille cumulée des 29 descriptions de skills ;
  - les chiffres détaillés de [R3] (PDF et dépôt) ;
  - la date du billet Cursor [R5] ;
  - le rendu Mermaid par GitHub et dans Claude Code (croyance non vérifiée) ;
  - le statut de Serena dans le marketplace officiel ;
  - le support Windows réel d'archify, de diagram-design et de leviathan ;
  - l'outil `claude-historian`, cité comme alternative légère à claude-mem.
- **À creuser** :
  - la tâche native « Dream » ou de consolidation de la mémoire, si elle existe (non vérifié) ;
  - la piste « attacher chaque mémoire à sa source, son autorité et sa date » (MemSecBench, cité par promptfoo, non lu en source primaire).
