Période : depuis le 2026-09-09, 257 sessions principales, 2109 sous-agents, 42332 requêtes API tracées.
### Q1

| Population | n | entrée + écriture, Q1 / médiane / Q3 | contexte total (avec lecture du cache), Q1 / médiane / Q3 |
|---|---|---|---|
| principale | 254 | 15,8 k / 18,9 k / 21,3 k | 36,7 k / 51,7 k / 54,5 k |
| principale / modèle opus | 184 | 17,9 k / 19,5 k / 21,9 k | 50,7 k / 53,0 k / 56,1 k |
| principale / modèle sonnet | 36 | 11,5 k / 11,6 k / 18,4 k | 27,7 k / 27,8 k / 34,8 k |
| principale / modèle haiku | 33 | 11,5 k / 11,6 k / 19,2 k | 28,5 k / 28,5 k / 35,6 k |
| sous-agent | 2105 | 14,7 k / 15,8 k / 19,2 k | 36,3 k / 38,2 k / 39,4 k |
| sous-agent / general-purpose | 1105 | 15,4 k / 15,9 k / 18,1 k | 38,1 k / 38,5 k / 39,1 k |
| sous-agent / agent-cost-kit:dev-story | 288 | 15,2 k / 18,5 k / 24,3 k | 37,4 k / 40,5 k / 42,6 k |
| sous-agent / agent-cost-kit:reviewer | 274 | 14,7 k / 18,1 k / 23,4 k | 37,3 k / 39,2 k / 41,6 k |
| sous-agent / agent-cost-kit:second-avis | 297 | 6,7 k / 7,5 k / 11,3 k | 11,5 k / 11,8 k / 13,7 k |
| sous-agent / agent-cost-kit:lookup | 9 | 6,1 k / 8,4 k / 10,5 k | 10,5 k / 10,7 k / 12,0 k |
| sous-agent / Explore | 30 | 23,7 k / 24,0 k / 24,9 k | 23,8 k / 24,1 k / 24,9 k |

Par semaine ISO (premier appel, toutes populations d'un genre) :

| Semaine | principale n | principale médiane (entrée+écriture / total) | sous-agent n | sous-agent médiane (entrée+écriture / total) |
|---|---|---|---|---|
| 2026-39 | 15 | 19,4 k / 52,0 k | 27 | 15,1 k / 37,1 k |
| 2026-40 | 12 | 20,0 k / 53,6 k | 32 | 24,9 k / 38,6 k |
| 2026-41 | 27 | 21,1 k / 53,4 k | 198 | 17,9 k / 38,6 k |
| 2026-42 | 181 | 18,4 k / 49,2 k | 1578 | 15,5 k / 38,2 k |
| 2026-43 | 19 | 18,5 k / 52,6 k | 270 | 18,2 k / 40,0 k |

Composition estimée du premier appel (médianes, caractères / 3,5), sessions avec définitions d'outils :

| Composant | principale | sous-agent |
|---|---|---|
| Prompt système (texte) | 3,9 k | 0,9 k |
| Définitions d'outils chargées | 25,5 k | 17,4 k |
| Pièces jointes de démarrage (liste des skills, CLAUDE.md, outils différés, agents, MCP...) | 16,8 k | 10,9 k |
| Premier message utilisateur | 0,2 k | 0,7 k |
| Nombre d'outils chargés (différés en plus) | 17 (+2) | 11 (+2) |

Pièces jointes de démarrage, médiane par type (tokens estimés) :

| Pièce jointe | principale | sous-agent |
|---|---|---|
| skill_listing | 5090 | 5090 |
| prompt_snapshot | 3997 | 923 |
| instructions | 3091 | 2931 |
| deferred_tools_delta | 1765 | 1622 |
| mcp_instructions_delta | 1315 | - |
| agent_listing_delta | 1301 | - |
| session_context | 297 | 322 |
| environment | 155 | 155 |

Définitions d'outils chargées par type d'agent (médianes) :

| Type | n | outils chargés | tokens estimés | contexte total |
|---|---|---|---|---|
| agent-cost-kit:second-avis | 297 | 5 | 2,9 k | 11,8 k |
| agent-cost-kit:dev-story | 285 | 11 | 17,8 k | 40,5 k |
| agent-cost-kit:reviewer | 271 | 11 | 17,8 k | 39,3 k |
| MAIN | 93 | 17 | 25,5 k | 53,4 k |
| general-purpose | 83 | 11 | 17,8 k | 36,4 k |
| dev-story | 54 | 11 | 17,6 k | 36,1 k |
| reviewer | 20 | 11 | 17,6 k | 34,8 k |
| agent-cost-kit:lookup | 8 | 5 | 2,9 k | 11,1 k |
| lookup | 5 | 5 | 2,9 k | 11,5 k |
| Explore | 4 | 8 | 6,6 k | 16,5 k |
| claude-code-guide | 3 | 6 | 2,7 k | 27,7 k |

### Q2

Fichiers avec définitions d'outils : 95 sessions principales, 1031 sous-agents.

| Outil | tokens (déf.) | principale : chargé / appelé (sessions) | appels | sous-agent : chargé / appelé (fichiers) | appels | lecture du cache de la définition, 45 j | écriture unique |
|---|---|---|---|---|---|---|---|
| Artifact | 10763 | 92 / 6 | 41 | 714 / 1 | 1 | 61 $ | 38 $ |
| PowerShell | 2771 | 95 / 36 | 707 | 718 / 143 | 1850 | 15 $ | 10 $ |
| SendFeedback | 1605 | 92 / 1 | 1 | 0 / 0 | 0 | 3 $ | 1 $ |
| Workflow | 1553 | 95 / 0 | 1 | 0 / 0 | 0 | 3 $ | 1 $ |
| Agent | 1526 | 95 / 48 | 1548 | 4 / 0 | 565 | 2 $ | 1 $ |
| AskUserQuestion | 1445 | 92 / 31 | 123 | 0 / 0 | 0 | 3 $ | 1 $ |
| ScheduleWakeup | 1342 | 95 / 0 | 1 | 0 / 0 | 0 | 2 $ | 1 $ |
| EnterWorktree | 1161 | 8 / 0 | 0 | 49 / 1 | 1 | 0 $ | 0 $ |
| Bash | 1119 | 95 / 80 | 7891 | 1028 / 1008 | 45690 | 5 $ | 3 $ |
| Grep | 956 | 95 / 30 | 221 | 1031 / 87 | 1649 | 6 $ | 3 $ |
| ReportFindings | 658 | 95 / 0 | 0 | 0 / 0 | 0 | 1 $ | 0 $ |
| Read | 570 | 95 / 65 | 920 | 1031 / 404 | 6671 | 3 $ | 2 $ |
| Skill | 531 | 95 / 25 | 74 | 718 / 8 | 85 | 3 $ | 2 $ |
| ToolSearch | 428 | 95 / 33 | 110 | 718 / 68 | 291 | 2 $ | 2 $ |
| ShareOnboardingGuide | 389 | 19 / 0 | 0 | 0 / 0 | 0 | 0 $ | 0 $ |
| WebSearch | 371 | 0 / 8 | 54 | 3 / 40 | 452 | 0 $ | 0 $ |
| ListAgents | 345 | 95 / 3 | 7 | 0 / 0 | 0 | 1 $ | 0 $ |
| WebFetch | 327 | 0 / 13 | 66 | 3 / 48 | 901 | 0 $ | 0 $ |
| Edit | 295 | 95 / 57 | 1184 | 714 / 333 | 5617 | 2 $ | 1 $ |
| SubagentHandback | 261 | 0 / 0 | 0 | 1028 / 1024 | 2196 | 1 $ | 1 $ |
| Glob | 224 | 95 / 3 | 10 | 1031 / 13 | 131 | 1 $ | 1 $ |
| Write | 198 | 95 / 55 | 529 | 714 / 387 | 3569 | 1 $ | 1 $ |

Outils appelés mais jamais chargés (différés, MCP) : fréquence d'appel sur la période :

| Outil | appels principale | appels sous-agent |
|---|---|---|
| mcp:claude-in-chrome__computer | 236 | 55 |
| SendMessage | 106 | 171 |
| Monitor | 73 | 137 |
| mcp:claude-in-chrome__javascript_tool | 34 | 83 |
| TaskStop | 48 | 40 |
| mcp:claude_ai_Hugging_Face__hf_fs | 19 | 51 |
| mcp:claude-in-chrome__navigate | 40 | 20 |
| mcp:claude-in-chrome__browser_batch | 30 | 0 |
| mcp:claude_ai_Hugging_Face__hub_repo_search | 12 | 10 |
| PushNotification | 19 | 0 |
| mcp:claude_ai_Hugging_Face__hub_repo_details | 6 | 13 |
| mcp:claude-in-chrome__tabs_close_mcp | 13 | 5 |
| mcp:claude-in-chrome__tabs_context_mcp | 14 | 4 |
| mcp:claude-in-chrome__find | 16 | 1 |
| mcp:claude_ai_Claude_Docs__read | 8 | 0 |
| bash | 0 | 8 |
| mcp:claude-in-chrome__resize_window | 4 | 3 |
| mcp:claude-in-chrome__read_console_messages | 1 | 4 |
| mcp:claude-in-chrome__get_page_text | 5 | 0 |
| mcp:claude-in-chrome__file_upload | 4 | 0 |
| ArtifactData | 2 | 0 |
| mcp:claude_ai_Claude_Docs__guide | 1 | 1 |
| mcp:claude-in-chrome__read_page | 2 | 0 |
| mcp:claude-in-chrome__list_connected_browsers | 2 | 0 |
| mcp:plugin-authoring__scan_secrets | 2 | 0 |
| mcp:claude-in-chrome__tabs_create_mcp | 2 | 0 |
| ExitPlanMode | 1 | 0 |
| bash_placeholder | 0 | 1 |
| mcp:claude-in-chrome__read_network_requests | 1 | 0 |
| mcp:claude-in-chrome__select_browser | 1 | 0 |
| mcp:claude-in-chrome__switch_browser | 1 | 0 |

### Q3


**principale** : résultats d'outils = 8,5 M tokens estimés, soit 18,3 % des tokens d'entrée neufs (entrée + écriture de cache, 46,1 M) ; entrée totale avec lectures du cache : 3476,2 M.

| Outil | résultats | tokens estimés | part des résultats | part de l'entrée neuve | part de l'entrée relue (cumul des relectures) | coût équivalent API estimé |
|---|---|---|---|---|---|---|
| Shell | 8597 | 4,4 M | 51,7 % | 9,5 % | 10,4 % | 93 $ |
| Read | 920 | 2,9 M | 33,8 % | 6,2 % | 5,2 % | 50 $ |
| Agent | 1548 | 507,7 k | 6,0 % | 1,1 % | 2,5 % | 20 $ |
| MCP | 454 | 310,0 k | 3,7 % | 0,7 % | 1,4 % | 11 $ |
| Grep | 221 | 99,7 k | 1,2 % | 0,2 % | 0,2 % | 2 $ |
| Artifact | 41 | 84,7 k | 1,0 % | 0,2 % | 0,1 % | 1 $ |
| Edit | 1184 | 68,8 k | 0,8 % | 0,1 % | 0,1 % | 1 $ |
| WebSearch | 54 | 46,0 k | 0,5 % | 0,1 % | 0,1 % | 1 $ |

**sous-agent** : résultats d'outils = 73,6 M tokens estimés, soit 23,5 % des tokens d'entrée neufs (entrée + écriture de cache, 313,8 M) ; entrée totale avec lectures du cache : 7590,5 M.

| Outil | résultats | tokens estimés | part des résultats | part de l'entrée neuve | part de l'entrée relue (cumul des relectures) | coût équivalent API estimé |
|---|---|---|---|---|---|---|
| Shell | 47582 | 44,6 M | 60,6 % | 14,2 % | 20,9 % | 390 $ |
| Read | 6672 | 25,5 M | 34,7 % | 8,1 % | 8,5 % | 246 $ |
| Grep | 1650 | 1,1 M | 1,5 % | 0,4 % | 0,3 % | 9 $ |
| WebFetch | 901 | 890,9 k | 1,2 % | 0,3 % | 0,1 % | 4 $ |
| WebSearch | 452 | 395,2 k | 0,5 % | 0,1 % | 0,0 % | 2 $ |
| Edit | 5618 | 273,3 k | 0,4 % | 0,1 % | 0,1 % | 2 $ |
| Write | 3569 | 231,4 k | 0,3 % | 0,1 % | 0,1 % | 2 $ |
| MCP | 250 | 259,3 k | 0,4 % | 0,1 % | 0,1 % | 2 $ |

**ensemble** : résultats d'outils = 82,1 M tokens estimés, soit 22,8 % des tokens d'entrée neufs (entrée + écriture de cache, 359,9 M) ; entrée totale avec lectures du cache : 11066,6 M.

| Outil | résultats | tokens estimés | part des résultats | part de l'entrée neuve | part de l'entrée relue (cumul des relectures) | coût équivalent API estimé |
|---|---|---|---|---|---|---|
| Shell | 56179 | 49,0 M | 59,7 % | 13,6 % | 17,6 % | 484 $ |
| Read | 7592 | 28,4 M | 34,6 % | 7,9 % | 7,4 % | 296 $ |
| Grep | 1871 | 1,2 M | 1,5 % | 0,3 % | 0,3 % | 11 $ |
| WebFetch | 967 | 912,7 k | 1,1 % | 0,3 % | 0,1 % | 4 $ |
| Agent | 2113 | 687,7 k | 0,8 % | 0,2 % | 0,8 % | 22 $ |
| WebSearch | 506 | 441,3 k | 0,5 % | 0,1 % | 0,1 % | 3 $ |
| MCP | 704 | 569,3 k | 0,7 % | 0,2 % | 0,5 % | 13 $ |
| Edit | 6802 | 342,1 k | 0,4 % | 0,1 % | 0,1 % | 4 $ |

Sensibilité du chiffre « Shell / entrée neuve » (principale + sous-agent) au nombre de caractères par token :

| caractères par token | part du Shell dans l'entrée neuve |
|---|---|
| 2,5 | 19,1 % |
| 3,0 | 15,9 % |
| 3,5 | 13,6 % |
| 4,0 | 11,9 % |

Ce que contiennent les résultats Shell (catégorie du premier mot de la commande, sans conserver la commande) :

| Catégorie | résultats | part des caractères | caractères par résultat | coût équivalent API estimé |
|---|---|---|---|---|
| lecture_fichier | 18938 | 54,4 % | 4924 | 278 $ |
| recherche | 11950 | 17,9 % | 2568 | 85 $ |
| git | 9288 | 15,3 % | 2817 | 55 $ |
| python | 5389 | 4,4 % | 1389 | 25 $ |
| liste | 2801 | 4,3 % | 2620 | 23 $ |
| tests_lint | 5647 | 2,9 % | 896 | 12 $ |
| gh | 877 | 0,5 % | 895 | 3 $ |
| attente | 713 | 0,2 % | 574 | 1 $ |
| autre | 576 | 0,2 % | 576 | 2 $ |

Coût équivalent API total de la période : 4 359 $ ; coût estimé des résultats Shell sur leur vie dans le contexte : 484 $ (11,1 %).

### Q4


**principale** : 14659 appels, écritures de cache 46,0 M tokens, 352 $ (coût total de ce genre : 1 296 $).

| Pause avant l'appel | appels | tokens écrits | part des tokens écrits | coût d'écriture | part du coût d'écriture | dont réécriture estimée (tokens relus si le cache avait tenu) | coût de la réécriture | part du coût total |
|---|---|---|---|---|---|---|---|---|
| > 60 min | 42 | 6,7 M | 14,6 % | 51 $ | 14,5 % | 6,7 M | 51 $ | 3,9 % |
| > 30 min | 98 | 6,8 M | 14,8 % | 52 $ | 14,7 % | 6,7 M | 51 $ | 3,9 % |
| > 15 min | 231 | 7,0 M | 15,2 % | 53 $ | 15,1 % | 6,8 M | 51 $ | 4,0 % |
| > 5 min | 855 | 7,9 M | 17,1 % | 60 $ | 17,0 % | 7,0 M | 53 $ | 4,1 % |

Premier appel de chaque agent (écriture initiale) : 10,0 % des tokens écrits. TTL observé : 5 min 3,5 M tokens, 1 h 38,0 M tokens (hors premiers appels). Expirations au TTL réel (pause > TTL, écriture > 20 k) : 39 appels, 51 $ de réécriture.

**sous-agent** : 60391 appels, écritures de cache 313,7 M tokens, 1 275 $ (coût total de ce genre : 3 063 $).

| Pause avant l'appel | appels | tokens écrits | part des tokens écrits | coût d'écriture | part du coût d'écriture | dont réécriture estimée (tokens relus si le cache avait tenu) | coût de la réécriture | part du coût total |
|---|---|---|---|---|---|---|---|---|
| > 5 min | 779 | 90,6 M | 28,9 % | 379 $ | 29,7 % | 89,6 M | 375 $ | 12,2 % |
| > 15 min | 63 | 12,0 M | 3,8 % | 58 $ | 4,5 % | 11,9 M | 57 $ | 1,9 % |
| > 30 min | 13 | 2,4 M | 0,8 % | 11 $ | 0,8 % | 2,4 M | 11 $ | 0,3 % |
| > 60 min | 4 | 662,9 k | 0,2 % | 3 $ | 0,2 % | 660,1 k | 3 $ | 0,1 % |

Premier appel de chaque agent (écriture initiale) : 12,6 % des tokens écrits. TTL observé : 5 min 257,1 M tokens, 1 h 17,0 M tokens (hors premiers appels). Expirations au TTL réel (pause > TTL, écriture > 20 k) : 634 appels, 373 $ de réécriture.

Contrefactuel TTL 1 h par type de sous-agent :

| Type | appels | appels après une pause > 5 min | gain (pauses 5-60 min relues) | surcoût (écritures x 2 au lieu de x 1,25) | solde |
|---|---|---|---|---|---|
| general-purpose | 27952 | 266 | 204 $ | 482 $ | -278 $ |
| dev-story | 16470 | 302 | 82 $ | 117 $ | -35 $ |
| reviewer | 9212 | 203 | 70 $ | 102 $ | -32 $ |
| Explore | 560 | 0 | 0 $ | 8 $ | -8 $ |
| fork | 322 | 1 | 0 $ | 3 $ | -3 $ |
| second-avis | 5668 | 7 | 0 $ | 2 $ | -1 $ |

Contrefactuel TTL 1 h pour les sous-agents : gain 355 $ (pauses de 5 à 60 min relues au lieu de réécrites) contre un surcoût de 713 $ (toutes les écritures à 5 min passent de x 1,25 à x 2) : solde -358 $.

### Q5

| Dépôt | stories avec constats | constats | corrigé (dont partiel) | rejeté | reporté | autre / indéterminé |
|---|---|---|---|---|---|---|
| autre | 88 | 597 | 426 (71,4 %) | 100 (16,8 %) | 40 (6,7 %) | 31 |
| wavelocalai | 51 | 315 | 177 (56,2 %) | 107 (34,0 %) | 28 (8,9 %) | 3 |
| wavedevsecops | 47 | 335 | 211 (63,0 %) | 93 (27,8 %) | 25 (7,5 %) | 6 |
| usine-migration-jira-demo | 7 | 63 | 44 (69,8 %) | 18 (28,6 %) | 1 (1,6 %) | 0 |

Total : 1310 constats sur 193 stories. 94 reporte, 837 corrige, 21 partiel, 318 rejete, 37 indetermine, 3 requalifie. Sévérités : 402 medium, 868 low, 40 high.
Motifs des rejets : {'voulu': 97, 'autre': 165, 'faux': 4, 'deja_regle': 52}.

Par sévérité (corrigé + partiel / total) :

| Sévérité | constats | corrigés | rejetés | reportés |
|---|---|---|---|---|
| high | 40 | 35 (87,5 %) | 2 (5,0 %) | 2 (5,0 %) |
| medium | 402 | 349 (86,8 %) | 32 (8,0 %) | 12 (3,0 %) |
| low | 868 | 474 (54,6 %) | 284 (32,7 %) | 80 (9,2 %) |

Agents lancés sur 45 jours : {'dev-story': 350, 'second-avis': 297, 'reviewer': 299}.
Journal wavedevsecops : 61 résultats de second avis, 442 constats déclarés (contre 335 lignes de revue retrouvées).
Journal wavelocalai : 44 résultats de second avis, 226 constats déclarés (contre 315 lignes de revue retrouvées).

### Q6

| Population | agents | appels : Q1 / médiane / Q3 / max | coût total | coupure à 2 x médiane (plafond) | agents coupés | appels évités | économie brute | part du coût |
|---|---|---|---|---|---|---|---|---|
| tous les dev-story | 350 | 23 / 36,5 / 62 / 196 | 628 $ | 73 | 62 (17,7 %) | 2065 | 124 $ | 19,7 % |
| dev-story sur Sonnet | 313 | 22 / 35 / 61 / 165 | 496 $ | 70 | 59 (18,8 %) | 1927 | 101 $ | 20,3 % |
| dépôts avec run-autonome.md | 246 | 29 / 48,0 / 72 / 196 | 546 $ | 96 | 36 (14,6 %) | 932 | 58 $ | 10,6 % |
| Sonnet, dépôts avec run-autonome.md | 213 | 29 / 49 / 76 / 165 | 427 $ | 98 | 29 (13,6 %) | 694 | 37 $ | 8,8 % |
| sessions de 3 dev-story ou plus | 327 | 23 / 37 / 63 / 196 | 602 $ | 74 | 59 (18,0 %) | 1960 | 118 $ | 19,7 % |
| par story (reprises regroupées) | 320 | 24 / 40,5 / 67 / 337 | 628 $ | 81 | 56 (17,5 %) | 2257 | 114 $ | 18,2 % |

Sensibilité du multiple (tous les dev-story) :

| Multiple | plafond | agents coupés | économie brute | part du coût |
|---|---|---|---|---|
| 1,5 x | 54 | 111 (31,7 %) | 204 $ | 32,5 % |
| 2 x | 73 | 62 (17,7 %) | 124 $ | 19,7 % |
| 3 x | 109 | 20 (5,7 %) | 39 $ | 6,2 % |

Plafond à 2 x la médiane de chaque dépôt (15 dépôts) : 34 agents coupés (9,7 %), 618 appels évités, économie brute 42 $ (6,7 % du coût dev-story).

Modèles des agents : {'haiku': 1, 'sonnet': 313, 'opus': 36} ; stories à plusieurs agents : 27.
