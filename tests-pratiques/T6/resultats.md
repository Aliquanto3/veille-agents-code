# T6 : `/advisor` (Sonnet avec conseiller Opus) contre Sonnet seul et Opus seul

Test pratique T6 de la veille sur les agents de code (`recherche/technical-outils-et-pratiques-des-agents-de-code-2026-10-24`, section 7). Mesuré le 25 octobre 2026 avec le banc de rejeu `tests-pratiques/banc-rejeu/`, mêmes 4 stories, mêmes mesures et même isolation que T3 (voir `tests-pratiques/T3/resultats.md`, sections 2 à 4, pour le corpus, la spec, l'interface imposée, la commande et ce qui est chargé). Toutes les sessions passent par l'abonnement Max : les coûts sont l'estimation client `total_cost_usd` de Claude Code, qui **inclut le conseiller** (`modelUsage` par modèle), en dollars aux tarifs catalogue, pas une facture.

## 1. Résultat en cinq lignes

- **Le conseiller n'est presque jamais appelé** avec le prompt du protocole : 1 run sur 12 (un appel). Sonnet décide seul de le consulter et, sans consigne, il ne le fait pas. Ce bras (b) se comporte donc comme Sonnet seul, avec **20,8 % de coût en plus** (+17,5 % sur les 11 runs sans appel : l'outil ajoute 1,4 k tokens au contexte et 2,7 tours en moyenne) et aucun gain de réussite (+1,1 pt, non significatif).
- **Avec une consigne explicite de consulter** (bras b' ajouté : « consulte-le avant de commencer à coder, puis avant de déclarer la story terminée »), le conseiller est appelé 1,9 fois par run (23 appels en 12 runs), à 0,29 $ l'appel (41 k tokens lus, 6 k écrits, hors cache) : il pèse 45 % du coût. Le run coûte **1,19 $ contre 0,53 $** pour Sonnet seul (+123 %) et 1,33 $ pour Opus seul : −10,5 % seulement, IC 95 % [−23 % ; +16 %].
- **Réussite** : 85,4 % (Sonnet seul, mêmes répétitions), 86,5 % (b), 89,4 % (b'), 87,5 % (Opus seul). Les écarts de 1 à 4 points sont dans le bruit (écart-type de 2 à 8 points dans une cellule) et bornés par les cas que la spec ne dit pas.
- **Critère de la veille** : (b) ne gagne pas. Contre Opus seul, il est certes 51,6 % moins cher, mais parce qu'il est du Sonnet seul ; il ne fait pas mieux que (a) (+21 % de coût, +1 pt). (b') n'est pas 15 % moins cher qu'Opus seul (−10,5 %, IC qui contient 0) ; il réussit mieux que Sonnet seul de 4 points pour +123 % de coût, ce qui n'est pas un surcoût raisonnable.
- **Décision proposée** : ne pas activer `/advisor` ni `advisorModel` par défaut. Pour des stories bien cadrées, Sonnet seul reste le meilleur rapport (0,53 $ pour 85 % de réussite, contre 1,33 $ pour 87 % avec Opus). Si une story bute deux fois, passer à Opus seul plutôt qu'ajouter un conseiller, qui coûte aussi cher qu'Opus sans l'égaler en prévisibilité (coefficient de variation du coût 33 %, contre 11 %).

## 2. Protocole

**Bras** (condition CLAUDE.md retenue en T3 : (a), le fichier actuel, car le minimal n'a pas atteint les 10 % d'économie) :

| Bras | Modèle principal | Conseiller | Prompt | Runs |
|---|---|---|---|---|
| (a) Sonnet seul | `claude-sonnet-5-5` | aucun | protocole | 20 (les exécutions de T3, 5 répétitions) ; 12 pour les comparaisons appariées (répétitions 1 à 3) |
| (b) Sonnet + conseiller | `claude-sonnet-5-5` | `--advisor claude-opus-5-5` | protocole | 12 (4 stories × 3 répétitions) |
| (b') Sonnet + conseiller, consigne | `claude-sonnet-5-5` | `--advisor claude-opus-5-5` | protocole + une phrase : « Tu disposes d'un conseiller (outil advisor) : consulte-le avant de commencer à coder, puis avant de déclarer la story terminée. » | 12 |
| (c) Opus seul | `claude-opus-5-5` | aucun | protocole | 12 |

Tous en `--effort medium`, explicite, y compris pour Opus (le réglage utilisateur d'Anaël met Opus 5.5 à `high`, mais ses réglages sont exclus et la chaîne `agent-cost-kit` utilise `medium`). Le bras (b') n'est pas dans le protocole d'origine : la documentation (`code.claude.com/docs/en/advisor`) indique que Claude décide seul quand consulter, qu'aucun réglage ne force l'appel et qu'on peut le demander dans le prompt. (b) mesure donc l'usage par défaut, (b') l'usage voulu.

Vérifications préalables : `--advisor opus` est accepté pour Sonnet 5.5 comme principal (tableau des paires de la doc) ; en mode `-p` le JSON de sortie donne `modelUsage` par modèle avec `costUSD` du conseiller, inclus dans `total_cost_usd` ; les appels se lisent dans la transcription comme des blocs `server_tool_use` nommés `advisor` (comptés par identifiant). Les options `--setting-sources`, `claudeMdExcludes` et `--tools` de T3 n'empêchent pas l'outil de conseiller. Les mêmes 4 stories et les mêmes tests cachés que T3 ; 3 répétitions pour (b), (b') et (c) au lieu d'une ou deux (le coût d'un run est de 0,5 à 2,5 $, la durée de 2 à 16 min).

Le coût du conseiller compte : il relit la conversation entière sans cache (« Each advisor call processes the full transcript anew »), aux tarifs d'Opus.

## 3. Mesures

### Global par bras

| Bras | n | coût moyen | médiane | écart-type | tours | durée (s) | entrée neuve (k) | lecture cache (k) | sortie (k) | taux cachés | suite KO | ruff propre |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (a) Sonnet seul, 5 répétitions | 20 | 0,532 $ | 0,415 $ | 0,229 | 36,3 | 263 | 55,5 | 968 | 21,3 | 85,6 % | 6/20 | 12/20 |
| (a) Sonnet seul, répétitions 1 à 3 | 12 | 0,533 $ | 0,404 $ | 0,220 | 35,7 | 247 | 55,6 | 954 | 21,5 | 85,4 % | 3/12 | 7/12 |
| (b) Sonnet + conseiller, prompt du protocole | 12 | 0,644 $ | 0,554 $ | 0,269 | 38,4 | 295 | 63,1 | 1 112 | 24,0 | 86,5 % | 3/12 | 8/12 |
| (b') Sonnet + conseiller, consigne | 12 | 1,191 $ | 1,117 $ | 0,452 | 41,7 | 397 | 68,6 | 1 216 | 24,3 | 89,4 % | 2/12 | 8/12 |
| (c) Opus seul | 12 | 1,330 $ | 1,084 $ | 0,574 | 34,9 | 330 | 69,6 | 1 189 | 26,8 | 87,5 % | 1/12 | 12/12 |

Les durées sont le temps mural par run avec 2 sessions en parallèle. Durée d'API moyenne (répétitions 1 à 3) : 137 s (a), 167 s (b), 290 s (b'), 237 s (c). Le coût total de ces 36 runs est 14,3 $ pour (b'), 7,7 $ pour (b), 16,0 $ pour (c) en équivalent API.

### Par story (moyenne ; entre parenthèses coût et taux de chaque répétition)

| Story | (a) Sonnet | (b) Sonnet + conseiller | (b') avec consigne | (c) Opus |
|---|---|---|---|---|
| s32 KPI | 0,406 $ ; 87 % | 0,728 $ ; 87 % (0,58 / 0,53 / 1,08) | 1,091 $ ; 88 % (1,15 / 1,47 / 0,65) | 1,065 $ ; 88 % (0,96 / 1,00 / 1,23) |
| s42 Risque | 0,467 $ ; 83 % | 0,509 $ ; 81 % (0,52 / 0,58 / 0,43) | 1,195 $ ; 86 % (0,78 / 1,42 / 1,38) | 1,134 $ ; 83 % (1,23 / 1,13 / 1,04) |
| s64 Classification | 0,901 $ ; 74 % | 0,963 $ ; 80 % (1,00 / 0,97 / 0,91) | 1,586 $ ; 83 % (1,81 / 2,06 / 0,88) | 2,246 $ ; 81 % (2,24 / 2,46 / 2,05) |
| s78 Outils | 0,352 $ ; 97 % | 0,374 $ ; 99 % (0,37 / 0,40 / 0,35) | 0,892 $ ; 100 % (0,97 / 0,62 / 1,08) | 0,876 $ ; 97 % (0,77 / 0,90 / 0,95) |

Tests cachés passés par cellule : s64, la seule story où un modèle plus capable semble aider, donne 13 ou 14 sur 18 pour Sonnet seul, 13 à 16 pour (b), 15 dans les trois runs de (b') et 14 ou 15 pour Opus ; s32 reste à 20 ou 21 sur 23 dans tous les bras, s78 à 20-23 sur 23.

### Comparaisons appariées (même story, même répétition, répétitions 1 à 3 ; 12 couples)

| Comparaison (B contre A) | Écart de coût agrégé | Écart relatif moyen [IC 95 % bootstrap] | Médian | B moins cher | Écart de taux moyen |
|---|---|---|---|---|---|
| (b) conseiller contre (c) Opus seul | −51,6 % | −50,6 % [−57 ; −42] | −55,2 % | 12 sur 12 | −0,9 pt (+3 / −5) |
| (b) conseiller contre (a) Sonnet seul | +20,8 % | +25,9 % [+5 ; +58] | +7,9 % | 2 sur 12 | +1,1 pt (+3 / −3) |
| (b') conseiller avec consigne contre (c) Opus seul | −10,5 % | −3,5 % [−23 ; +16] | −1,3 % | 6 sur 12 | +1,9 pt (+5 / −2) |
| (b') conseiller avec consigne contre (a) Sonnet seul | +123,5 % | +134,9 % [+94 ; +175] | +145,9 % | 0 sur 12 | +4,0 pt (+6 / −1) |
| (c) Opus seul contre (a) Sonnet seul | +149,7 % | +151,6 % [+130 ; +177] | +140,9 % | 0 sur 12 | +2,1 pt (+5 / −3) |

### Conseiller

- (b), prompt du protocole : 11 runs sur 12 sans aucun appel ; un seul run (s32, répétition 3) a consulté une fois (0,48 $ de conseiller, run à 1,08 $). Part du coût due au conseiller : 4 % en moyenne.
- (b'), consigne explicite : 0 run sur 12 sans appel ; 1 à 3 appels par run (moyenne 1,9) ; coût moyen du conseiller 0,556 $ pour un run à 1,19 $ (part de 27 % à 59 %, moyenne 45 %) ; le coût principal de Sonnet y est de 0,635 $, au niveau de Sonnet seul (+19 %), le reste étant le conseiller. Par appel : 41 k tokens d'entrée et 6 k de sortie, 0,29 $.
- Coefficient de variation du coût entre répétitions : (a) 11 %, (b) 17 %, (b') 33 %, (c) 11 %. Le nombre d'appels (1 à 3) fait varier le coût de (b') de 0,65 à 2,06 $ sur une même story.
- Une régression de la suite existante dans (b') : `s64-asvc3` casse 10 tests existants (le run le moins cher de sa cellule, 0,88 $ et 40 tours) ; deux consultations n'ont pas évité ce défaut. Aucun autre bras n'a de régression de plus de 2 tests (les 2 tests de `test_import_linter` de s78 sont communs à presque tous les runs).

Détail par run : `banc-rejeu/donnees/rapport-t6.md`.

## 4. Limites

- Trois répétitions seulement par bras ; les IC bootstrap sont larges (±20 points pour (b') contre (c)). L'écart (b') contre (c) de −10,5 % ne permet de conclure ni à « moins de 15 % » ni à « pas moins cher ».
- Une réussite saturée : le plafond de chaque story est fixé par les cas que la spec ne décrit pas (voir T3, section 4). Les bras ne se distinguent que de 1 à 4 points, dont une partie vient de la story s64. Le test ne dit pas que le conseiller est inutile sur des tâches difficiles, longues ou ambiguës (le cas pour lequel la documentation le recommande : grosses refontes, erreur récurrente) ; il dit qu'il n'aide pas ici, sur des stories bien cadrées de 2 à 16 min.
- Effort `medium` imposé aux trois bras (Opus aurait été à `high` dans la configuration d'Anaël) et outils restreints à six ; le conseiller reçoit toute la conversation, qui est courte (60 k tokens au plus).
- Le bras (b') est une variante ajoutée par le banc ; la phrase de consigne a été écrite une fois et n'a pas été optimisée (une consigne ciblée, par exemple « une seule fois avant de coder », réduirait le nombre d'appels et le coût).
- Le conseiller est facturé aux limites d'usage de l'abonnement Max ; l'estimation en dollars est celle du client, pas une facture. Les runs `-p` n'ont pas consommé de clé API.
- Une limite de session a interrompu deux runs de T3 avant T6 ; ils ont été relancés (voir T3). Aucun run de T6 n'a été interrompu.

## 5. Reproduire

Depuis `tests-pratiques/banc-rejeu/` (le corpus et `interface.md` sont déjà construits ; au plus 2 sessions à la fois) :

```
uv run --no-project python -I banc.py lot plans/t6.json --max 2            # (b) et (c), 3 répétitions
uv run --no-project python -I banc.py lot plans/t6_consigne.json --max 2   # (b')
uv run --no-project python rapport.py t6 --cond a
```
