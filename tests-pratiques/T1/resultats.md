# T1 : diagnostics sans rejeu sur les transcriptions locales de Claude Code

Test pratique T1 de la veille sur les agents de code (`recherche/technical-outils-et-pratiques-des-agents-de-code-2026-10-24`, section 7). Mesure faite le 2026-10-24, sans rejouer aucune story. Tous les chiffres sont des agrégats ; aucun contenu de prompt, de code ni de sortie d'outil n'est recopié.

## 1. Contexte et méthode commune

**Données.** Les transcriptions de `~/.claude/projects` modifiées depuis le 2026-09-09 (45 jours) : 257 sessions principales et 2 109 sous-agents (3,8 Go, 42 dossiers de projet). Les premières transcriptions datent du 2026-09-09 et plus de 90 % des sessions sont d'octobre (la semaine ISO 42 pèse à elle seule 181 sessions principales et 1 578 sous-agents) : tout chiffre « par mois » repose sur peu de septembre. Période totale : 75 050 appels d'API, soit 4 359 $ en équivalent API (écriture de cache 37,3 %, lecture 42,7 %, sortie 19,9 %, entrée 0,0 %), dont 1 296 $ en sessions principales et 3 063 $ en sous-agents. Par type d'agent : `general-purpose` 1 938 $ (44 %), sessions principales 1 296 $, `dev-story` 628 $, `reviewer` 418 $, `second-avis` 9 $.

**Réutilisation de `agent-cost-kit`.** `analyse.py` importe `scripts/mesurer_couts.py` (prix par identifiant de modèle de `tarifs.json`, familles, multiplicateurs de long contexte et de zone, tarifs d'écriture 5 min et 1 h, lecture des horodatages, sortie réestimée à 2,2 caractères par token) et en reprend les règles : un appel par `message.id`, chaque réponse comptée une fois dans la transcription qui a démarré en premier, les réponses recopiées par une reprise restant le « précédent » des pauses. Même règle pour les résultats d'outils (`tool_use_id`). Ce qui est nouveau : lecture en flux (la fonction du plugin charge tout le fichier), lecture des définitions d'outils, tailles des résultats d'outils.

**Contraintes de poste respectées.** Un seul processus Python, séquentiel, lancé par `uv run --no-project python -I`, lecture ligne par ligne ; seules les lignes `assistant`, `user`, `attachment`, `api-request` et `api-request-shape` sont décodées (les `api-request-blob`, qui font l'essentiel du volume, sont ignorés sans décodage). Une passe complète prend 30 s. Aucun fichier n'est chargé en entier.

**Nouveauté du format.** Les transcriptions récentes contiennent des lignes `api-request-shape` avec les définitions d'outils envoyées au modèle (nom, description, schéma, drapeau `defer_loading`) : la question 2 peut donc compter les outils présents, et pas seulement ceux appelés. Elles n'existent que dans 95 sessions principales sur 257 et 1 031 sous-agents sur 2 109 (les plus récents).

**Conversion caractères vers tokens.** Résultats d'outils et définitions : 1 token pour 3,5 caractères (règle de la veille). `bancs/caracteres_par_token.py` mesure autre chose : la sortie du modèle (2,13 à 2,2 caractères par token), qui ne s'applique pas à l'entrée. Contrôle de plausibilité : la somme des composants estimés du premier appel (46,4 k tokens) atteint 90 % du premier contexte réel (51,7 k) : l'estimation sous-évalue légèrement.

**Confidentialité.** Les noms de projet sont ramenés à la liste blanche des dépôts publics (`agent-cost-kit`, `wavestack`, `wavedevsecops`, `wavelocalai`, `slm-quality-bench`, `usine-migration-jira-demo`, `veille-agents-code`, `WaveEval`, `claude-code-mods`), sinon « autre ». Les commandes Shell ne sont conservées que sous forme de catégorie (premier mot ramené à une famille).

**Fichiers.** `analyse.py` (questions 1 à 4 et 6, sortie `agregats.json`), `q5_second_avis.py` (question 5, sortie `q5.json`), `tableaux.py` (tableaux de `tableaux.md`). Les tableaux détaillés de ce rapport viennent de `tableaux.md`.

## 2. Question 1 : contexte fixe

**Méthode.** Premier appel de chaque session ou sous-agent dont la première réponse est propre (les 3 sessions principales et 4 sous-agents qui reprennent une réponse recopiée sont exclus). Deux mesures : « entrée + écriture » (demandée) et « contexte total » avec la lecture du cache, car le préfixe fixe (prompt système, outils) est déjà en cache d'une session à l'autre et n'apparaît donc que pour une part dans l'écriture du premier appel.

| Population | n | entrée + écriture (Q1 / médiane / Q3) | contexte total (Q1 / médiane / Q3) |
|---|---|---|---|
| Session principale | 254 | 15,8 k / 18,9 k / 21,3 k | 36,7 k / 51,7 k / 54,5 k |
| Principale, premier appel sur Opus | 184 | 17,9 k / 19,5 k / 21,9 k | 50,7 k / 53,0 k / 56,1 k |
| Sous-agent (tous) | 2 105 | 14,7 k / 15,8 k / 19,2 k | 36,3 k / 38,2 k / 39,4 k |
| `general-purpose` | 1 105 | 15,4 k / 15,9 k / 18,1 k | 38,1 k / 38,5 k / 39,1 k |
| `agent-cost-kit:dev-story` | 288 | 15,2 k / 18,5 k / 24,3 k | 37,4 k / 40,5 k / 42,6 k |
| `agent-cost-kit:reviewer` | 274 | 14,7 k / 18,1 k / 23,4 k | 37,3 k / 39,2 k / 41,6 k |
| `agent-cost-kit:second-avis` | 297 | 6,7 k / 7,5 k / 11,3 k | 11,5 k / 11,8 k / 13,7 k |
| `agent-cost-kit:lookup` | 9 | 6,1 k / 8,4 k / 10,5 k | 10,5 k / 10,7 k / 12,0 k |

**Évolution.** Pas de dérive mesurable. Septembre contre octobre (principale, médiane entrée + écriture / total) : 19,4 k / 52,0 k (n = 15) contre 18,8 k / 51,3 k (n = 239). Sous-agents : 15,1 k / 37,1 k (n = 27) contre 15,8 k / 38,2 k (n = 2 078). Par semaine ISO, le contexte total médian reste entre 49 k et 54 k (principale) et entre 37 k et 40 k (sous-agent).

**Répartition estimée du premier appel** (médianes, sessions avec définitions d'outils) :

| Composant | Principale | Sous-agent |
|---|---|---|
| Prompt système | 3,9 k | 0,9 k |
| Définitions d'outils chargées | 25,5 k (17 outils, +2 différés) | 17,4 k (11 outils, +2 différés) |
| Pièces jointes de démarrage (skills, CLAUDE.md, outils différés, agents, MCP) | 16,8 k | 10,9 k |
| Premier message | 0,2 k | 0,7 k |

Pièces jointes médianes (tokens estimés) : liste des skills 5,1 k (identique en principale et en sous-agent), instructions (CLAUDE.md, mémoire) 3,1 k, liste des outils différés 1,8 k, instructions MCP 1,3 k, liste des agents 1,3 k. Les sous-agents sont plus légers que les sessions (11 outils chargés au lieu de 17) ; `second-avis`, dont le frontmatter fixe `tools: Read, Grep, Glob, Bash`, n'en charge que 5 (2,9 k) : une liste d'outils réduit bien les définitions envoyées.

**Répartition officielle.** `claude plugin details agent-cost-kit` (v0.9.0) : 4 skills, 4 agents, 0 hook, 0 serveur MCP, 1 029 tokens toujours chargés. `claude -p "/context"` depuis `GitHub` (mode non interactif, modèle Opus 5.5) : 25 k au total, soit prompt système 2,3 k, outils système 11,5 k (+16,4 k d'outils différés non chargés), agents 0,6 k, fichiers de mémoire 5,6 k (CLAUDE.md global 3,1 k, du projet 2,1 k, MEMORY.md 0,4 k), skills 5,0 k, messages 0. Le mode `-p` porte moins d'outils que les sessions interactives (11,5 k contre 25,5 k estimés) : l'écart vient pour l'essentiel d'outils propres à l'interface (Artifact, ScheduleWakeup, SendFeedback...). `claude -p "/skill-doctor"` : 34 skills listées, 12 jamais invoquées (BMAD : agents, brainstorming, customize, prfaq, product-brief, project-context, qa ; plus `bilan-tokens`) pour environ 0,9 k de liste, soit moins de 2 % du premier appel. Les 29 skills BMAD pèsent environ 2,5 k dans la liste, les skills intégrées environ 1,4 k.

**Limites.** (1) La répartition est une estimation par caractères, pas un comptage de tokens ; le total estimé retrouve 90 % du réel. (2) `-p /context` ne reflète pas les sessions interactives. (3) Les définitions ne sont connues que pour les transcriptions récentes. (4) L'écriture du premier appel ne prouve pas un coût payé : le préfixe est lu en cache quand une autre session l'a déjà écrit (médiane principale : 32,8 k lus et 18,9 k écrits au premier appel).

**Décision proposée.** Le contexte fixe vaut 51,7 k (principale) et 38,2 k (sous-agent) tokens, dont 25,5 k et 17,4 k de définitions d'outils : c'est la première cible du garde-fou. Les skills et le CLAUDE.md pèsent beaucoup moins (5,1 k et 3,1 k) ; retirer les 12 skills inutilisées ne rapporterait pas 2 % du premier appel. Le garde-fou doit donc d'abord porter sur les outils (question 2), pas sur les skills.

## 3. Question 2 : outils jamais appelés

**Méthode.** Pour chaque transcription avec définitions : outils chargés (hors `defer_loading`) et outils appelés au moins une fois par un appel propre. Pour les autres : fréquence d'appel seule. Coût d'une définition : tokens estimés (caractères / 3,5) x requêtes de la session x prix de lecture du cache, plus une écriture unique (x 1,25 du prix d'entrée), comme une borne haute (le préfixe est partagé entre sessions).

| Outil | Tokens (déf.) | Principale : chargé / appelé (sessions) | Appels | Sous-agent : chargé / appelé (fichiers) | Appels | Lecture + écriture de la déf. |
|---|---|---|---|---|---|---|
| Artifact | 10 763 | 92 / 6 | 41 | 714 / 1 | 1 | 61 $ + 38 $ |
| SendFeedback | 1 605 | 92 / 1 | 1 | 0 / 0 | 0 | 3 $ + 1 $ |
| Workflow | 1 553 | 95 / 0 | 1 | 0 / 0 | 0 | 3 $ + 1 $ |
| ScheduleWakeup | 1 342 | 95 / 0 | 1 | 0 / 0 | 0 | 2 $ + 1 $ |
| EnterWorktree | 1 161 | 8 / 0 | 0 | 49 / 1 | 1 | 0 $ + 0 $ |
| ReportFindings | 658 | 95 / 0 | 0 | 0 / 0 | 0 | 1 $ + 0 $ |
| ShareOnboardingGuide | 389 | 19 / 0 | 0 | 0 / 0 | 0 | 0 $ + 0 $ |
| ListAgents | 345 | 95 / 3 | 7 | 0 / 0 | 0 | 1 $ + 0 $ |
| PowerShell (pour comparaison) | 2 771 | 95 / 36 | 707 | 718 / 143 | 1 850 | 15 $ + 10 $ |
| Bash (pour comparaison) | 1 119 | 95 / 80 | 7 869 | 1 028 / 1 008 | 45 668 | 5 $ + 3 $ |

Les outils différés (MCP du navigateur, Hugging Face, Claude Docs, `SendMessage`, `Monitor`, `TaskStop`) ne coûtent que leur nom dans la liste des outils différés (1,7 k) ; ils sont appelés quand on les charge (`mcp:claude-in-chrome__computer` 291 appels, `SendMessage` 277, `Monitor` 210).

**Chiffre.** Les 8 premiers outils du tableau (appelés dans moins de 10 % des sessions où ils sont chargés) pèsent 17,8 k tokens estimés, dont 10,8 k pour `Artifact` seul : environ un tiers du premier contexte d'une session principale (51,7 k) et 60 % des définitions d'un sous-agent `dev-story` (17,8 k de définitions pour 40,5 k de contexte). Leur coût est de 71 $ en lecture et 41 $ en écriture, soit 112 $ sur 1 873 $ de coût des sessions où les définitions sont visibles : environ 6 %, dont 5,3 % pour `Artifact`. La part en dollars est bien plus faible que la part du contexte parce que ce contexte est surtout lu à 0,05 x le prix d'entrée et que la conversation grossit (contexte moyen par appel : 237 k en principale, 126 k en sous-agent).

**Limites.** Définitions visibles dans 44 % des fichiers seulement. Les « appelés » d'une session de planification ou d'un sous-agent court sous-estiment l'usage d'outils rares mais utiles (Artifact est utilisé dans 6 sessions sur 92 : il ne faut pas le retirer du poste, mais des agents qui n'en ont pas besoin). Les tailles sont des estimations par caractères. Le gain en dollars suppose que retirer l'outil ne déplace pas ailleurs ses tokens.

**Décision proposée.** Ajouter `Artifact` (et `EnterWorktree`, `ListAgents`, `ReportFindings`, `ScheduleWakeup`, `SendFeedback`, `ShareOnboardingGuide`, `Workflow`) à `disallowedTools` des agents `dev-story` et `reviewer` de `agent-cost-kit`, ou leur donner une liste `tools:` explicite comme à `second-avis` (la liste réduit bien les définitions, preuve ci-dessus ; l'effet de `disallowedTools` sur la définition n'est pas démontré par ces transcriptions et doit être vérifié sur le premier appel). Gain attendu : environ 11 k tokens (27 %) sur le premier appel de `dev-story` et `reviewer`, soit 3 à 6 % du coût total en dollars (borne haute 6 %). Pour la session principale, tester une règle `permissions.deny` par projet après avoir vérifié qu'elle retire bien la définition de l'outil. À valider par un A contre B avec `mesurer-couts`. L'écart avec les −13 à −18 % attribués par TokenEconomizer au retrait des outils inutilisés n'est pas reproduit ici : l'effet de l'outil sur la facture est borné à environ 6 % sur ces projets.

## 4. Question 3 : part de Bash dans les tokens d'entrée

**Méthode.** Taille en caractères de chaque `tool_result`, rattaché à son outil par `tool_use_id`, convertie à 3,5 caractères par token (une image compte 1 500 tokens). Trois dénominateurs : (a) les tokens d'entrée neufs (entrée + écriture de cache, 359,8 M) ; (b) l'entrée relue (chaque résultat compté autant de fois que d'appels qui le suivent dans le même fichier, rapporté à l'entrée totale avec lecture du cache, 11 065 M) ; (c) le coût équivalent API (écriture une fois, puis relectures). « Shell » regroupe `Bash` et `PowerShell`.

| Outil | Résultats | Tokens estimés | Part des résultats | Part de l'entrée neuve | Part de l'entrée relue | Coût estimé |
|---|---|---|---|---|---|---|
| Shell (Bash + PowerShell) | 56 171 | 49,0 M | 59,7 % | **13,6 %** | 17,6 % | 484 $ |
| Read | 7 591 | 28,4 M | 34,6 % | 7,9 % | 7,4 % | 296 $ |
| Grep | 1 871 | 1,2 M | 1,5 % | 0,3 % | 0,3 % | 11 $ |
| WebFetch | 967 | 0,9 M | 1,1 % | 0,3 % | 0,1 % | 4 $ |
| Agent (retours de sous-agent) | 2 113 | 0,7 M | 0,8 % | 0,2 % | 0,8 % | 22 $ |
| MCP | 704 | 0,6 M | 0,7 % | 0,2 % | 0,5 % | 13 $ |
| Edit, Write, Artifact, Glob et 20 autres | 14 582 | 0,9 M | 1,1 % | 0,2 % | 0,3 % | 9 $ |

Par genre : Shell représente 9,5 % de l'entrée neuve en session principale (10,4 % relue) et 14,2 % en sous-agent (20,9 % relue). Au total, les résultats d'outils pèsent 22,8 % de l'entrée neuve et le Shell 11,1 % du coût total (484 $ sur 4 359 $). Sensibilité à la conversion : 11,9 % à 4 caractères par token, 15,9 % à 3, 19,1 % à 2,5.

**Ce que contiennent les résultats Shell** (catégorie du premier mot de la commande) :

| Catégorie | Résultats | Part des caractères | Caractères par résultat | Coût estimé |
|---|---|---|---|---|
| Lecture de fichier (`cat`, `sed`, `head`, `tail`, `Get-Content`) | 18 935 | 54,4 % | 4 925 | 278 $ |
| Recherche (`grep`, `rg`, `find`) | 11 949 | 17,9 % | 2 568 | 85 $ |
| `git` | 9 288 | 15,3 % | 2 817 | 55 $ |
| `python` / `uv` | 5 387 | 4,4 % | 1 388 | 25 $ |
| Liste (`ls`, `dir`, `wc`) | 2 800 | 4,3 % | 2 619 | 23 $ |
| Tests et lint (`pytest`, `ruff`...) | 5 647 | 2,9 % | 896 | 12 $ |
| `gh` | 876 | 0,5 % | 895 | 3 $ |
| Attente, autres | 1 289 | 0,4 % | environ 570 | 2 $ |

Aucun résultat Shell ne dépasse 10 k tokens (la sortie est plafonnée en amont).

**Limites.** Approximation par caractères (la conversion fait varier le chiffre de 12 à 19 %) ; une sortie Shell de code ou de journal se tokenise souvent en moins de 3,5 caractères par token, donc ces valeurs sont plutôt basses. Le dénominateur « entrée neuve » contient aussi les réécritures de cache après expiration (environ 15 à 30 % des écritures) et les sorties du modèle : la part est sous-estimée d'autant. La catégorisation par premier mot classe un `cat` suivi d'un pipe dans « lecture » ; une commande composée est classée par son premier mot. Les résultats tronqués ou déportés dans un fichier par l'outil comptent pour la taille du texte renvoyé.

**Décision proposée.** Le critère de la veille (sous 10 %) n'est pas satisfait à la lettre : 13,6 % de l'entrée neuve, 9,5 % en principale et 14,2 % en sous-agent. Il ne conclut pourtant pas en faveur d'un outil de compression, car la part compressible est faible : 54 % du Shell est de la lecture de fichier, dont le contenu est ce que l'agent a demandé et ne se compresse pas sans perte ; git, tests, gh, Python et listes ne font que 27 % du Shell, soit environ 3,7 % de l'entrée neuve, et une compression de 60 % ne rapporterait que 2 à 3 % du coût (cohérent avec les 2,7 % mesurés dans la source de la veille). Ne pas installer d'outil de compression des sorties. Levier plus rentable : lire des extraits (`sed -n` par plage, `Read` avec `offset` et `limit`) et laisser `second-avis` lire le diff plutôt que des fichiers entiers. Refaire la mesure si la part du Shell en session principale dépasse 15 %.

## 5. Question 4 : reprises après pause

**Méthode.** Pour chaque appel propre qui a un précédent dans la même transcription (le précédent peut être une réponse recopiée), pause = écart d'horodatage ; on additionne les tokens et le coût d'écriture de cache des appels dont la pause dépasse 5 min (sous-agents) ou 60 min (principale). « Réécriture estimée » = écriture moins la croissance réelle du contexte, soit ce qui aurait été lu si le cache avait tenu. Les seuils 15 et 30 min sont donnés en sensibilité. Le contrefactuel TTL 1 h reprend la règle du plugin : les pauses de 5 à 60 min deviennent des lectures, mais toutes les écritures à 5 min passent de x 1,25 à x 2.

Sessions principales (46,0 M de tokens écrits, 352 $) :

| Pause avant l'appel | Appels | Tokens écrits | Part des écrits | Coût d'écriture | Part du coût d'écriture | Réécriture estimée | Part du coût total principal |
|---|---|---|---|---|---|---|---|
| > 60 min | 42 | 6,7 M | **14,6 %** | 51 $ | 14,5 % | 51 $ | 3,9 % |
| > 30 min | 98 | 6,8 M | 14,8 % | 52 $ | 14,7 % | 51 $ | 3,9 % |
| > 5 min | 855 | 7,9 M | 17,1 % | 60 $ | 17,0 % | 53 $ | 4,1 % |

Sous-agents (313,7 M de tokens écrits, 1 275 $) :

| Pause avant l'appel | Appels | Tokens écrits | Part des écrits | Coût d'écriture | Part du coût d'écriture | Réécriture estimée | Part du coût total sous-agent |
|---|---|---|---|---|---|---|---|
| > 5 min | 779 | 90,6 M | **28,9 %** | 379 $ | 29,7 % | 375 $ | 12,2 % |
| > 15 min | 63 | 12,0 M | 3,8 % | 58 $ | 4,5 % | 57 $ | 1,9 % |
| > 30 min | 13 | 2,4 M | 0,8 % | 11 $ | 0,8 % | 11 $ | 0,3 % |
| > 60 min | 4 | 0,7 M | 0,2 % | 3 $ | 0,2 % | 3 $ | 0,1 % |

Un appel de reprise après plus de 60 min en session principale réécrit en moyenne 160 k tokens (42 appels, 6,7 M). TTL observé : 92 % des écritures principales (hors premier appel) sont à 1 h, 94 % des écritures de sous-agents à 5 min. Expirations au TTL réel (pause supérieure au TTL, écriture de plus de 20 k) : 39 en principale (51 $), 634 en sous-agents (373 $).

**Contrefactuel TTL 1 h pour les sous-agents** : gain 355 $ (pauses de 5 à 60 min relues), surcoût 713 $ (toutes les écritures à 5 min passent à x 2), solde **−358 $**. Aucun type d'agent ne profite du TTL 1 h :

| Type | Appels | Appels après > 5 min | Gain | Surcoût | Solde |
|---|---|---|---|---|---|
| `general-purpose` | 27 952 | 266 | 204 $ | 482 $ | −278 $ |
| `dev-story` | 16 470 | 302 | 82 $ | 117 $ | −35 $ |
| `reviewer` | 9 212 | 203 | 70 $ | 102 $ | −32 $ |
| `second-avis` | 5 668 | 7 | 0 $ | 2 $ | −1 $ |

**Limites.** Une pause d'horodatage mêle attente de l'utilisateur, exécution d'un outil long (tests, CI) et attente d'un sous-agent bloquant ; on ne distingue pas la cause. Le TTL réel de chaque écriture est lu dans `usage.cache_creation` ; un cache peut être prolongé par un autre appel de la même session (agents parallèles). La part des écritures « après pause » comprend la fraction réellement neuve : la colonne « réécriture estimée » est la bonne mesure du gaspillage. Écart avec la veille : la part des écritures dans le coût (37,3 %) est un peu sous les 42 à 44 % qu'elle cite.

**Décision proposée.** Ne pas poser `subagentPromptCacheTtl: "1h"` : le solde est négatif en global (−358 $) et pour chaque type d'agent, conformément à la règle du CLAUDE.md. Pour les sessions principales (déjà à 1 h), la réécriture après plus de 60 min coûte 51 $ en 45 jours (1,2 % du coût total) : ne pas construire de mécanisme, mais garder le réflexe `/clear` (avec `/rename`) avant une pause longue. La cible utile, si on veut agir, est ailleurs : les 771 appels de `dev-story`, `reviewer` et `general-purpose` repartis après plus de 5 min (attentes de CI ou de tests longs) ; relever alors si ces attentes peuvent passer en tâche de fond pour que l'agent ne rouvre pas un contexte froid.

## 6. Question 5 : second avis retenu

**Où la revue est consignée.** Dans les fichiers de story `_bmad-output/implementation-artifacts/*.md`, section « Revue », sous forme de puces « sévérité, second avis N : constat. Corrigé / Rejeté / Reporté… » écrites par le reviewer (Opus) après lecture de la liste de Haiku ; le journal `run-autonome.md` donne le nombre de constats déclarés à l'étape `second-avis`.

**Méthode.** `q5_second_avis.py` lit ligne par ligne les `.md` des dépôts qui ont ce dossier (hors worktrees), retient les puces qui commencent par une sévérité et citent « second avis », classe le verdict par le premier mot-clé qui suit (corrigé, rejeté, reporté…) et dédoublonne les lignes identiques entre dépôts. Les rejets sont ensuite répartis par motif apparent (« déjà réglé », « comportement voulu », « faux »).

| Dépôt | Stories avec constats | Constats | Corrigés (dont partiels) | Rejetés | Reportés |
|---|---|---|---|---|---|
| `wavelocalai` | 51 | 315 | 177 (56,2 %) | 107 (34,0 %) | 28 (8,9 %) |
| `wavedevsecops` | 47 | 335 | 211 (63,0 %) | 93 (27,8 %) | 25 (7,5 %) |
| `usine-migration-jira-demo` | 7 | 63 | 44 (69,8 %) | 18 (28,6 %) | 1 (1,6 %) |
| autres dépôts | 88 | 597 | 426 (71,4 %) | 100 (16,8 %) | 40 (6,7 %) |
| **Total** | **193** | **1 310** | **858 (65,5 %)** | **318 (24,3 %)** | **94 (7,2 %)** |

Les 40 constats restants sont indéterminés (37) ou requalifiés (3). Par sévérité :

| Sévérité | Constats | Corrigés | Rejetés | Reportés |
|---|---|---|---|---|
| high | 40 | 35 (87,5 %) | 2 (5,0 %) | 2 (5,0 %) |
| medium | 402 | 349 (86,8 %) | 32 (8,0 %) | 12 (3,0 %) |
| low | 868 | 474 (54,6 %) | 284 (32,7 %) | 80 (9,2 %) |

Motifs des 318 rejets : comportement voulu ou décision de la story 97 (7,4 % des constats), constat déjà réglé ou lu sur une base en retard 52 (4,0 %), faux explicite 4 (0,3 %), motif non classé 165. Les agents ont tourné 297 fois (`second-avis`), 299 fois (`reviewer`) et 350 fois (`dev-story`) sur la période. Coût de `second-avis` : 8,8 $ pour 297 exécutions (0,03 $ par story, environ 1 cent par constat corrigé), contre 418 $ pour `reviewer`.

**Limites.** (1) Les verdicts viennent d'un classement par mot-clé : environ 3 % de constats indéterminés, et « faux » est presque jamais écrit tel quel par le reviewer (il écrit « rejeté : déjà réglé » ou « comportement voulu »). Les 4 faux sont donc une borne basse ; la mesure des « faux » demande une relecture humaine d'un échantillon. (2) Le journal annonce plus de constats (442 pour `wavedevsecops`) que de lignes de revue retrouvées (335) : un quart des constats n'est pas retrouvé sous cette forme ; s'ils ont été écartés sans trace, la part retenue est surestimée (pour `wavelocalai`, c'est l'inverse : 226 déclarés pour 315 lignes). (3) Les stories sans constat ne laissent pas de trace dans les fichiers : le nombre de stories est un minimum. (4) Le périmètre dépend de la convention d'écriture du reviewer (aucune puce de ce format dans `wavestack`). (5) Corrigé n'est pas prouvé utile : on ne sait pas si le constat aurait été attrapé par le reviewer sans lui.

**Décision proposée.** Garder `second-avis` dans la chaîne : 87 % des constats de sévérité medium ou high sont corrigés, pour environ 0,03 $ la story, alors que le reviewer coûte 1,4 $ par story. Les `low` (66 % des constats, 55 % corrigés) n'ont pas besoin d'être traités avec le même soin ; garder la règle « rebaser avant de juger », qui vise les 4 % de constats déjà réglés. Pour trancher l'apport propre du second avis, comparer sur 5 stories le même reviewer avec et sans la liste (test T5).

## 7. Question 6 : critère d'arrêt simulé

**Méthode.** Les agents `dev-story` (350 sur la période, dont 313 sur Sonnet, 36 sur Opus et 1 sur Haiku) : nombre d'appels propres, coût de chaque appel, médiane. Simulation : on coupe l'agent au plafond de `k` x la médiane (k = 2) ; l'économie brute est le coût des appels au-delà du plafond. Trois choix de médiane : celle de tous les agents, celle de chaque dépôt (la médiane varie de 19 à 68 appels selon le dépôt), celle des dépôts qui ont un fichier d'état de run autonome (`run-autonome*.md`, `etat-run*.md`, `etat-nuit*.md`, `rapport-de-nuit*.md`).

| Population | Agents | Appels : Q1 / médiane / Q3 / max | Coût | Plafond 2 x | Agents coupés | Appels évités | Économie brute | Part du coût |
|---|---|---|---|---|---|---|---|---|
| Tous, médiane globale | 350 | 23 / 36,5 / 62 / 196 | 628 $ | 73 | 62 (17,7 %) | 2 065 | 124 $ | 19,7 % |
| Tous, médiane de chaque dépôt | 350 | | 628 $ | 2 x la médiane du dépôt | 34 (9,7 %) | 618 | 42 $ | 6,7 % |
| Dépôts en run autonome | 246 | 29 / 48 / 72 / 196 | 546 $ | 96 | 36 (14,6 %) | 932 | 58 $ | 10,6 % |
| Idem, Sonnet seul | 213 | 29 / 49 / 76 / 165 | 427 $ | 98 | 29 (13,6 %) | 694 | 37 $ | 8,8 % |
| Par story (reprises regroupées) | 320 | 24 / 40,5 / 67 / 337 | 628 $ | 81 | 56 (17,5 %) | 2 257 | 114 $ | 18,2 % |

Sensibilité (tous, médiane globale) : plafond à 1,5 x, 111 agents coupés (31,7 %) pour 204 $ (32,5 %) ; à 3 x, 20 agents (5,7 %) pour 39 $ (6,2 %). 27 stories ont plus d'un agent `dev-story` (reprises).

**Limites.** (1) L'économie est brute : une story coupée n'est pas terminée, il faut une reprise (au minimum une réécriture du contexte puis les appels restants) ; les stories les plus longues sont aussi les plus difficiles ; la reprise peut absorber la moitié de l'économie ou plus (hypothèse, non mesurée). (2) Le plafond sur la médiane globale confond des dépôts très différents (19 à 68 appels) : il coupe surtout les dépôts à longs runs, d'où l'écart entre 19,7 % et 6,7 %. (3) Les appels d'un agent ne sont pas tous coûteux de la même façon : les derniers, dans un contexte plus gros, valent plus que les premiers, ce que la simulation prend en compte appel par appel. (4) Le numéro de story est lu dans la description courte de l'agent ; 79 % des descriptions des agents de la chaîne (dev-story, second-avis, reviewer) en ont un.

**Décision proposée.** Ne pas couper à 2 x la médiane : le gain brut est de 42 à 58 $ en 45 jours (1 % à 1,3 % du coût total) et 10 à 15 % des stories seraient interrompues, ce qui coûterait, par hypothèse, la moitié de ce gain en reprises et risquerait de laisser des stories à moitié faites. Utiliser plutôt le plafond comme une alerte (notification à l'orchestrateur à 2 x la médiane du dépôt, décision manuelle). La coupure franche n'a de sens qu'à 3 x (20 agents, 39 $), et seulement si la reprise est gratuite.

## 8. Synthèse des décisions proposées

| Question | Chiffre clé | Décision |
|---|---|---|
| 1. Contexte fixe | 51,7 k (principale) et 38,2 k (sous-agent) tokens au premier appel, stable ; 25,5 k et 17,4 k de définitions d'outils | Garde-fou du contexte fixe centré sur les outils, pas sur les skills (12 skills inutilisées = moins de 2 %) |
| 2. Outils jamais appelés | 8 outils (17,8 k tokens, dont Artifact 10,8 k) appelés dans moins de 10 % des sessions ; 112 $ (≈ 6 % du coût) | `disallowedTools` ou `tools:` explicite dans `dev-story` et `reviewer` (−27 % de contexte) ; règle `permissions.deny` à tester en principale ; A contre B avec `mesurer-couts` |
| 3. Part de Bash | 13,6 % de l'entrée neuve (9,5 % principale, 14,2 % sous-agent), 11,1 % du coût ; 54 % de lecture de fichier | Pas d'outil de compression (27 % seulement du Shell est compressible, gain 2 à 3 %) ; lire des extraits ; refaire la mesure si > 15 % en principale |
| 4. Reprises après pause | 14,6 % des écritures principales après > 60 min (51 $) ; 28,9 % des écritures de sous-agents après > 5 min (375 $) | Pas de TTL 1 h (solde −358 $, négatif pour chaque type) ; pas de mécanisme pour la principale ; `/clear` avant une pause longue |
| 5. Second avis | 1 310 constats, 65,5 % corrigés, 24,3 % rejetés, 0,3 % faux explicites ; 87 % de corrigés en medium et high ; 0,03 $ la story | Garder `second-avis` ; comparer avec et sans liste sur 5 stories (T5) |
| 6. Critère d'arrêt | Coupure à 2 x la médiane du dépôt : 34 agents (9,7 %), 42 $ bruts (6,7 % du coût dev-story) | Ne pas couper ; alerte à 2 x ; coupure franche seulement à 3 x |

**Autre constat.** Les agents `general-purpose` représentent 44 % du coût (1 938 $), plus que `dev-story` et `reviewer` réunis (1 046 $) : à examiner dans une prochaine mesure (quelles tâches, quel modèle, quels outils chargés).

## 9. Reproduire

Depuis ce dossier, dans cet ordre, un seul processus à la fois :

```
uv run --no-project python -I analyse.py --out agregats.json [--detail-dir <dossier hors dépôt>]
uv run --no-project python -I q5_second_avis.py --out q5.json
uv run --no-project python -I tableaux.py > tableaux.md
```

`analyse.py` lit `~/.claude/projects` et `agent-cost-kit/scripts/mesurer_couts.py` (chemin en tête de fichier). Les résultats dépendent de l'état des transcriptions au moment de la mesure (la session en cours s'y ajoute) : deux passes à quelques minutes d'écart diffèrent de moins de 0,1 %.
