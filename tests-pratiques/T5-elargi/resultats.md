# T5 élargi : rappel des relecteurs sur défauts semés (20 stories, 4 dépôts)

Mesuré les 24 et 25 octobre 2026. Le premier T5 (`../T5/resultats.md`) n'avait que 5 défauts manqués connus. Ici on sème 1 défaut connu dans 16 diffs réels et on laisse 4 stories sans défaut (témoins), pour mesurer le **rappel** de chaque relecteur et ce qu'un critique d'une autre famille ajoute à la chaîne Haiku puis Opus. Aucune clé n'est écrite dans les fichiers ni les journaux ; coût OpenRouter total 1,45 $ (plafond 5 $).

## 1. Résultat en bref

- **Rappel sur 16 défauts semés** (un constat qui désigne le bon fichier à ±5 lignes et la bonne logique) : Haiku 11 (69 %), Opus 11 (69 %), `gpt-6.1-sol` 11 (69 %), `gpt-6-luna` 8 (50 %). Intervalles de Wilson à 95 % : [44 ; 86] pour 11 sur 16, [28 ; 72] pour 8 sur 16. À cette taille, les écarts entre relecteurs ne sont pas significatifs.
- **Haiku et Opus détectent exactement les mêmes 11 défauts.** Leur union (la chaîne, en passes indépendantes) reste à 11 sur 16 : Opus n'ajoute aucun défaut à Haiku. Opus se distingue par la sévérité : 9 défauts sur 16 reconnus au niveau Important contre 6 pour Haiku, qui range les mêmes défauts en `low`. Coût équivalent API par story : 0,02 $ pour Haiku, 0,53 $ pour Opus.
- **Gain d'un critique d'une autre famille : +1 story sur 16 (+6 points), pas plus.** Chaîne + luna : 12 sur 16 (75 %). Chaîne + sol : 12 sur 16 (75 %). Dans les deux cas, l'unique défaut en plus est le même : `range(1, 10)` devenu `range(1, 9)` dans la liste des périphériques réservés LPT (`ws-v2s2`). Une seconde passe des deux critiques GPT, sur les mêmes diffs, donne le même résultat (voir 4.5).
- **Le critère de la veille n'est pas rempli** : il demande au moins 10 points de rappel en plus, soit au moins 2 stories sur 16. Le bruit n'est en revanche pas doublé : 22 constats Important hors défaut semé ou sur témoin pour la chaîne, 35 avec luna (× 1,6), 34 avec sol (× 1,5), et 12 à 13 de ces constats supplémentaires sont presque tous « discutables ».
- **5 défauts échappent à la chaîne, dont 4 à tous les relecteurs** (`us611`, `us713`, `wd59`, `wd81`) : constante de seuil 3 devenue 4, `frozen=True` devenu `False`, `min_length=1` devenu 2, motif de repli vidé. Ce sont des survivants que la spec ne contredit pas : aucun lecteur ne peut les décider sans connaître l'intention.

## 2. Jeu de données

**Stories** : 20 stories fusionnées et développées par agents, 5 par dépôt public Python (`usine-migration-jira-demo`, `wavedevsecops`, `wavelocalai`, `wavestack`). Pour chacune : le diff entre le parent et le commit fusionné, restreint aux fichiers Python (`src`, `tests`, `scripts`, `tools`), en `-U1`, 40 000 caractères au plus (de 8 757 à 38 300) ; la spec de la story, en retirant les sections écrites après le développement (revue, tests, journal, notes d'implémentation, `## Revue`), 14 000 caractères au plus. Les fichiers non Python (JSON, JS, HTML, YAML) sont absents du diff. Pour `usine`, la story est la paire de commits « feature + correctifs de revue » (7.13, 7.11) ou la fusion de branche (6.11, 6.12, 6.13), et pour les trois autres dépôts la fusion de la PR ou de la branche (diff entre le premier parent et le commit de fusion).

**Témoins** (4) : un par dépôt, tirés au sort avec la graine 20261024 : `us711` (usine 7.11), `wd56` (wavedevsecops 5.6), `wl93` (wavelocalai 9.3), `ws-v2s7` (wavestack V1.1 vague 2, story 7). **Défauts semés** (16) dans les 16 autres.

**Choix du défaut.** On a d'abord lancé cosmic-ray 8.7 sur les lignes ajoutées par la story (outillage de `../T4/mutation_story.py` : annotations de type écartées, tests de la story seulement, `pytest -x`, 8 minutes au plus par story, échantillon aléatoire de 70 mutants au plus). Sur les 615 mutants exécutés (toutes stories candidates, `mutation/<id>.json`), 493 sont tués et 116 survivent. On ne garde que les familles réalistes : condition niée ou inversée, `or`/`and` échangés, `continue` devenu `break`, borne ou constante numérique décalée, booléen littéral inversé, `+`/`-` échangés ; les remplacements par des opérateurs binaires binaires (`^`, `|`, `>>`) ou par `is`, `in`, ou par `CosmicRayTestingException` sont écartés parce qu'ils sautent aux yeux et ne ressemblent pas à un défaut d'agent. Le défaut est tiré au sort (graine fixe) parmi les survivants admissibles (une ligne, un mutant). Un mutant équivalent par lecture est écarté et on tire à nouveau : `ws-minicpm` (`0 <= opening < end` devenu `<=`, deux motifs distincts ne peuvent pas coïncider) et `wl91` (`time.monotonic() < deadline` devenu `<=`).

**Mutants écrits à la main** (3 stories sur 16, aucun survivant admissible en 8 minutes : tests solides ou suite lente). Chacun a été essayé contre les tests de la story avec `essai_mutant.py` et n'est retenu que s'il **survit** : `wd81` (motif de repli `"fichier illisible"` remplacé par `""`, 3 essais dont 2 tués), `wl27` (`0 <= value <= MAX` devenu `< MAX`, 3 essais dont 2 tués), `ws-v2s2` (`range(1, 10)` devenu `range(1, 9)`). Les 13 autres défauts sont des survivants cosmic-ray.

**Remplacements de stories en cours de route.** `wd86` (wavedevsecops 8.6) ne contient que 5 lignes de code source (le reste est du YAML et des tests) : remplacée par `wd56`, tirée ensuite comme témoin. `wl95` (wavelocalai 9.5) : 35 lignes de source, surtout docstrings et imports ; trois mutants manuels, tous tués : remplacée par `wl25` (2.5).

| Id | Dépôt | Commit fusionné | Diff (car.) | Lignes source ajoutées | Défaut semé | Nature | Origine | Haiku | Opus | luna | sol |
|---|---|---|---|---|---|---|---|---|---|---|---|
| us611 | usine | bad2e74ea7 | 20438 | 177 | `doublons.py:31` `LONGUEUR_MIN_JETON = 3` → `4` | constante décalée | cosmic-ray | non | non | non | non |
| us612 | usine | d82b42d636 | 8757 | 41 | `fournisseur.py:407` `== "local"` → `>= "local"` | comparaison | cosmic-ray | oui | oui | oui | oui |
| us613 | usine | 5a448819cf | 14424 | 148 | `passerelle.py:518` `traces_outils[-1]` → `[-0]` | indice | cosmic-ray | oui | oui | oui | oui |
| us713 | usine | bc8ab219fc | 28335 | 236 | `vues.py:27` `ConfigDict(frozen=True)` → `False` | booléen | cosmic-ray | non | non | non | non |
| wd58 | wavedevsecops | da4a38bafd | 19268 | 26 | `designation.py:131` `s.sha == …` → `>= …` | comparaison | cosmic-ray | oui | oui | oui | oui |
| wd59 | wavedevsecops | 4c0a0e936c | 25450 | 210 | `model.py:63` `min_length=1` → `2` | borne | cosmic-ray | non | non | non | non |
| wd81 | wavedevsecops | 69fdb68fe2 | 22711 | 66 | `findings.py:146` repli `"fichier illisible"` → `""` | valeur par défaut | manuel | non | non | non | non |
| wd96 | wavedevsecops | d57132f746 | 18382 | 103 | `links.py:113` `ref != EXPLAIN_CHECK` → `<=` | comparaison | cosmic-ray | oui | oui | non | non |
| wl25 | wavelocalai | a5585c3c66 | 38300 | 231 | `cloud_estimate.py:30` `KG_TO_MG = 1_000_000.0` → `999999.0` | constante décalée | cosmic-ray | oui | oui | oui | oui |
| wl27 | wavelocalai | f6e3841efc | 36590 | 55 | `catalog.py:66` `<= MAX_TEMPERATURE` → `<` | borne | manuel | oui | oui | oui | oui |
| wl91 | wavelocalai | 257574a65b | 11330 | 62 | `__main__.py:158` `daemon=True` → `False` | booléen | cosmic-ray | oui | oui | non | oui |
| wl94 | wavelocalai | dfa17ef8e9 | 15008 | 36 | `config.py:229` `testing_no_fake_embedder = False` → `True` | valeur par défaut | cosmic-ray | oui | oui | oui | oui |
| ws-granite | wavestack | 971f7c37ff | 13503 | 81 | `capabilities.py:88` `at < 0` → `at < -1` | borne | cosmic-ray | oui | oui | non | oui |
| ws-minicpm | wavestack | 53793b6077 | 21834 | 142 | `parser.py:128` `return -1` → `-0` | constante décalée | cosmic-ray | oui | oui | oui | oui |
| ws-v2s2 | wavestack | 1a7b015751 | 18652 | 160 | `sandbox.py:27` `range(1, 10)` → `range(1, 9)` (LPT9) | borne | manuel | non | non | oui | oui |
| ws-v2s6 | wavestack | f3e45a7aa6 | 10204 | 77 | `cloud_base.py:341` `max(0, …)` → `max(-1, …)` | borne | cosmic-ray | oui | oui | non | oui |
| us711 | usine | 846542d926 | 22808 | 224 | témoin | | | | | | |
| wd56 | wavedevsecops | 9071c0533c | 28193 | 235 | témoin | | | | | | |
| wl93 | wavelocalai | 3f9e9a2b6a | 26158 | 145 | témoin | | | | | | |
| ws-v2s7 | wavestack | 998729ffc6 | 20126 | 120 | témoin | | | | | | |

Colonnes relecteurs : défaut détecté ou non, tous niveaux de sévérité, passe officielle. Le fichier `verite.json` (jamais montré aux relecteurs) donne la ligne, l'ancien et le nouveau texte, la fonction, l'opérateur et l'origine. `jeu.json` donne les commits de base et de fusion et la liste des fichiers.

La mutation est restreinte à 70 mutants par story (échantillon tiré avec la graine 5) et à 8 minutes ; les stories à suite lente (`wd58` 79 s par exécution, `ws-v2s2` 61 s, `wd81` 65 s) n'ont pu exécuter que 6 à 26 mutants. Détail par story dans `mutation/<id>.json` (comptes et survivants avec leur diff).

## 3. Protocole

**Copies.** Tout travail est fait dans des copies du scratchpad (`…\scratchpad\t5e`, lecteur `T:` créé par `subst` pour des chemins courts), jamais dans les dépôts : `git archive` du commit fusionné (sans `.git`, sans `_bmad`, `_bmad-output`, `.claude`, `docs`, `CLAUDE.md`, `AGENTS.md`, sans images), un `uv sync --frozen --no-install-project` par dépôt (une seule `.venv` par dépôt, `PYTHONPATH` sur l'arbre de la story, aucune variable de secret dans l'environnement des tests). Les tests rouges dans cet environnement (paquet non installé, `streamlit` absent, sous-processus `python -m wavestack`) sont écartés une fois pour toutes par un premier passage sans `-x` (`lancer_tests.py --controle`) : 38 tests pour `ws-v2s2`, 32 pour `us611`, 9 pour `us713`, 2 pour `wl25`, un fichier pour `us711`.

**Semis.** La ligne mutée est réécrite dans l'arbre vu par les relecteurs Claude et dans le diff envoyé à tous (`semer.py` : la ligne ajoutée correspondante du diff est modifiée, assertion de cohérence). La vérité terrain vit dans un dossier que ni les relecteurs Claude (confinés à l'arbre de la story) ni les modèles GPT (spec et diff seulement) ne voient.

**Relecteurs, mêmes diff et même spec.**
1. **Haiku 5.5** : `claude -p --model haiku --effort medium --output-format json`, corps de `agents/second-avis.md` d'agent-cost-kit en `--append-system-prompt`.
2. **Opus 5.5** : idem avec `--model opus` et le corps de `agents/reviewer.md`.
3. **`openai/gpt-6-luna`** et 4. **`openai/gpt-6.1-sol`** via OpenRouter, prompt de T5 inchangé (JSON de constats, test pytest obligatoire pour un Important), température 0, 32 000 jetons de sortie, un appel par modèle et par story.

Les relecteurs Claude tournent avec `--safe-mode --restricted --tools Read,Grep,Glob --allowedTools Read,Grep,Glob --strict-mcp-config --permission-mode dontAsk --no-session-persistence`, dans l'arbre de la story (sans historique, sans accès au dépôt d'origine), 2 sessions `claude -p` au plus à la fois. Le diff et la spec sont dans le message, comme pour les modèles GPT ; en plus les relecteurs Claude lisent l'arbre fusionné, que les modèles GPT n'ont pas. Un paragraphe d'adaptation ajouté à chaque consigne (`revue_claude.py`) dit : lecture seule sans `Bash` ni `git`, signaler sans corriger, pas de section `## Revue`, rapport en une ligne par constat `étiquette | sévérité | chemin:ligne | mécanisme | certitude`, sans limite de longueur. Aucun relecteur n'exécute de code : c'est une dégradation par rapport à la chaîne réelle, où le reviewer lance des tests.

**Jugement.** La grille (`grille.md`) est écrite avant la première revue et n'a pas changé : localisation à ±5 lignes (scriptée, `juger.py`), puis lecture de la logique. Deux rappels : tout constat, ou seulement les constats de niveau Important (GPT : sévérité Important ; Opus : étiquette Important ; Haiku : sévérité high ou medium). 46 constats localisés en passe officielle (43 détections, 3 constats « près mais autre motif » : validation de `errors` dans `wd81` ×2, texte hors `<param>` dans `ws-minicpm`), 19 en seconde passe GPT (19 détections). **Un seul juge, le même agent qui a conçu le test** ; l'identifiant du relecteur est masqué et l'ordre mélangé, mais le format d'un constat (`Nit | low | …` contre un JSON) trahit sa famille : le jugement n'est donc pas strictement aveugle.

**Combinaisons.** Chaîne = Haiku ∪ Opus, en passes indépendantes sur le même diff (en production, Opus reçoit la liste de Haiku, ce qui n'est pas simulé ici). Chaîne + critique = union. Bruit = constats Important qui ne détectent pas le défaut semé (stories semées) ou qui tombent sur un témoin.

## 4. Résultats

### 4.1 Rappel par relecteur

| Relecteur | Rappel (tous niveaux) | IC Wilson 95 % | Rappel Important | Constats (tous) | Important | Important hors défaut semé (16 stories) | Important sur les 4 témoins |
|---|---|---|---|---|---|---|---|
| Haiku 5.5 (`second-avis`) | 11 / 16 = 69 % | 44 à 86 % | 6 / 16 = 38 % | 74 | 19 | 8 | 4 |
| Opus 5.5 (`reviewer`) | 11 / 16 = 69 % | 44 à 86 % | 9 / 16 = 56 % | 76 | 19 | 7 | 3 |
| `gpt-6-luna` | 8 / 16 = 50 % | 28 à 72 % | 4 / 16 = 25 % | 25 | 17 | 8 | 5 |
| `gpt-6.1-sol` | 11 / 16 = 69 % | 44 à 86 % | 8 / 16 = 50 % | 30 | 20 | 7 | 5 |

Les relecteurs GPT rendent presque uniquement des Important (un test pytest est exigé, sinon Nit) ; les relecteurs Claude rendent aussi des Nit en nombre. Important par story, tous relecteurs : 0,85 à 1,0.

### 4.2 Combinaisons

| Combinaison | Rappel | IC Wilson 95 % | Rappel Important | Bruit Important (hors semis + témoins) |
|---|---|---|---|---|
| Haiku seul | 11 / 16 = 69 % | 44 à 86 % | 6 / 16 | 12 |
| Opus seul | 11 / 16 = 69 % | 44 à 86 % | 9 / 16 | 10 |
| **Chaîne (Haiku + Opus)** | **11 / 16 = 69 %** | 44 à 86 % | **9 / 16 = 56 %** | **22** |
| Chaîne + luna | 12 / 16 = 75 % | 51 à 90 % | 10 / 16 | 35 (× 1,6) |
| Chaîne + sol | 12 / 16 = 75 % | 51 à 90 % | 10 / 16 | 34 (× 1,5) |
| Chaîne + luna + sol | 12 / 16 = 75 % | 51 à 90 % | 10 / 16 | 47 (× 2,1) |
| luna + sol (sans Claude) | 11 / 16 = 69 % | 44 à 86 % | 8 / 16 | 25 |

**Gain de rappel d'un critique d'une autre famille au-dessus de la chaîne : +6 points** (1 story sur 16), tous niveaux comme au niveau Important. Il vaut `ws-v2s2` (LPT9) pour luna comme pour sol, et rien d'autre. Les défauts qui séparent les familles sont peu nombreux : `ws-v2s2` n'est trouvé que par luna et sol, `wd96` que par Haiku et Opus, et luna rate en plus `ws-granite`, `wl91` et `ws-v2s6` que sol trouve.

### 4.3 Faux positifs sur les témoins

Les 17 constats Important tombés sur les 4 témoins ont été classés à la lecture du code et de la spec (`classification_temoins.json`) : `démontré` (comportement réel vérifié), `discutable` (plausible mais non vérifié, ou écart à la spec sans effet démontré), `faux` (le code est correct), `artefact` (le constat vient d'un fichier non Python que mon diff n'envoyait pas).

| Relecteur | Important sur témoins | démontré | discutable | faux | artefact du diff |
|---|---|---|---|---|---|
| Haiku | 4 | 0 | 4 | 0 | 0 |
| Opus | 3 | 0 | 3 | 0 | 0 |
| luna | 5 | 0 | 2 | 1 | 2 |
| sol | 5 | 1 | 3 | 0 | 1 |
| Chaîne | 7 | 0 | 7 | 0 | 0 |
| Chaîne + luna | 12 | 0 | 9 | 1 | 2 |
| Chaîne + sol | 12 | 1 | 10 | 0 | 1 |

Un seul constat démontré, par exécution, dans toute l'étude : `git check-ignore -q --no-index` accepte aussi `.git/info/exclude` (sol, `wd56`), contraire à la lettre de la spec mais sans effet dans le bac à sable. Le faux positif franc de luna (`except OSError, UnicodeDecodeError:` jugé invalide) est une erreur de version : `wavedevsecops` exige Python 3.14, où la syntaxe est valide (PEP 758). Trois constats viennent de ce que le diff exclut les fichiers non Python (données JSON de repli, JavaScript) : ils sont comptés à part, ce sont des artefacts du protocole et non des erreurs de relecteur. Aucun constat de la chaîne n'est faux au sens strict ; 7 sur 7 sont « discutables » (cas limites non couverts par la spec, performance).

### 4.4 Coût et latence

| Relecteur | Coût sur 20 stories | Par story | Latence moyenne |
|---|---|---|---|
| Haiku | 0,45 $ (équivalent API) | 0,022 $ | 88 s |
| Opus | 10,66 $ (équivalent API) | 0,53 $ | 79 s |
| luna | 0,05 $ (passe 1) | 0,003 $ | 35 s |
| sol | 0,60 $ (passe 1) | 0,030 $ | 22 s |

Les relecteurs Claude passent par l'abonnement : les montants sont ceux que `claude -p` renvoie (`total_cost_usd`, tarif de liste), pas une facturation. Opus coûte 24 fois Haiku pour le même rappel tous niveaux. Coût d'OpenRouter pour toute l'étude, passes de reprise et seconde passe comprises : 1,45 $.

### 4.5 Seconde passe des critiques GPT (stabilité)

Mêmes diffs, mêmes prompts, un deuxième tirage (`reponses/gpt-r2`, `analyse_r2.py`).

| | Passe 1 | Passe 2 | Union des deux | Communs |
|---|---|---|---|---|
| luna | 8 / 16 | 8 / 16 | 10 / 16 | 6 |
| sol | 11 / 16 | 11 / 16 | 12 / 16 | 10 |

`sol` est plus stable (10 défauts sur 11 communs) que `luna` (6 sur 8). Au-dessus de la chaîne, le gain reste `ws-v2s2` : chaîne + luna passe 2 = 11 / 16 (pas de gain), chaîne + sol passe 2 = 12 / 16 (+ `ws-v2s2`). L'union de deux tirages ne rattrape ni `us611`, ni `us713`, ni `wd59`, ni `wd81`. Les Important de luna passent de 17 à 23 d'un tirage à l'autre : le bruit varie plus que le rappel.

### 4.6 Par origine du défaut et par dépôt

| Strate | Haiku | Opus | luna | sol | Chaîne |
|---|---|---|---|---|---|
| Survivants cosmic-ray (13) | 10 | 10 | 6 | 9 | 10 |
| Mutants manuels (3) | 1 | 1 | 2 | 2 | 1 |
| usine (4) | 2 | 2 | 2 | 2 | 2 |
| wavedevsecops (4) | 2 | 2 | 1 | 1 | 2 |
| wavelocalai (4) | 4 | 4 | 3 | 4 | 4 |
| wavestack (4) | 3 | 3 | 2 | 4 | 3 |

Les trois mutants manuels sont des bornes (`<=` devenu `<`, `range(1, 9)`) et un repli : les deux critiques GPT en trouvent 2 sur 3, la chaîne 1 sur 3. Trois points sur ce sous-échantillon ne permettent aucune conclusion, mais l'unique gain de l'étude vient de l'un d'eux.

## 5. Limites

1. **16 défauts, 1 défaut par story.** Une story de plus ou de moins vaut 6 points de rappel et les intervalles de Wilson font environ 40 points de large : le critère « +10 points » ne peut pas être établi ni réfuté à cette taille. Il aurait fallu 50 à 100 défauts pour trancher 10 points.
2. **Quatre défauts jamais trouvés** (`us611`, `us713`, `wd59`, `wd81`) : survivants dont la spec ne contredit pas la valeur (seuil, immutabilité, longueur minimale, message de repli). Ils tirent le rappel de tous vers le bas sans départager les relecteurs. À l'inverse, plusieurs défauts sont explicitement contredits par la spec (`wl27` « de 0 à 2 », `wl91` `daemon=True`, `ws-v2s2` « quelle que soit l'extension », `wl25` « kgCO2eq converti en mg ») : la grille favorise un relecteur qui compare le code à la spec, surtout pour les mutants à constante ou à borne.
3. **Les specs des dépôts BMAD ne sont pas toutes des specs d'avant le développement.** Celles de `wavedevsecops`, `wavestack` (V1.1 vague 2) et `wavelocalai` décrivent ce qui est livré (« Livré », « Contrat ajouté ») plutôt qu'une intention ; seul `usine` (et `wavestack` pour `ws-granite` et `ws-minicpm`) a des sections `Intent` et `Boundaries`. J'en retire les sections de revue, de tests et de journal, mais le contenu reste proche du code.
4. **Mutants à bornes et à constantes**, 8 sur 16 sont des bornes ou des constantes décalées, faciles à voir pour un lecteur qui cherche les `<=`. Les défauts d'un agent réel (oubli de branchement, de cas, de dépendance) ne sont pas représentés.
5. **Asymétrie d'information.** Les modèles GPT ne voient que le diff Python et la spec ; les relecteurs Claude lisent aussi l'arbre fusionné. Aucun relecteur n'exécute de code (la chaîne réelle le fait). Les fichiers non Python sont absents du diff : 3 constats GPT sur témoins en découlent.
6. **La chaîne simulée est une union de deux passes indépendantes**, pas la chaîne réelle où Opus reçoit la liste de Haiku, confirme ou écarte, et corrige. Le résultat « Opus n'ajoute rien à Haiku » est donc propre à cette mesure.
7. **Un seul juge**, non strictement aveugle (le format trahit la famille). 3 constats ont été jugés « autre motif » ; aucun n'est limite. La classification des faux positifs porte sur 17 constats seulement, un seul a été vérifié par exécution.
8. **Un tirage de chaque relecteur Claude**, deux pour les critiques GPT. La variabilité de Haiku et d'Opus d'un tirage à l'autre n'est pas mesurée ; les GPT montrent qu'elle peut valoir 2 défauts sur 16 (luna).
9. **Dépôts de l'auteur, écrits par des agents Claude** : les relecteurs Claude et les défauts semés partagent peut-être des angles morts ; c'est précisément l'hypothèse que testent les critiques d'une autre famille, mais le jeu ne la favorise pas.
10. **Mutation partielle** : 6 à 70 mutants par story selon la durée de la suite (615 exécutés sur 1 481 effectifs). Les survivants tirés ne représentent pas tous les trous de test de la story.
11. **Incidents de procédure**, tous traités, listés pour la traçabilité : (a) cosmic-ray tué à l'échéance laisse le dernier mutant dans le fichier ; des arbres étaient souillés au moment du premier semis (constaté sur `ws-v2s2` : `range( 0, 10)` laissé dans le fichier) ; les arbres ont été reconstruits depuis `git archive`, 4 défauts ont changé (`wd58`, `wl91`, `ws-granite`, `ws-minicpm`), et toutes les revues obtenues avant la reconstruction pour les stories semées (6 Haiku, 1 Opus, 6 réponses GPT) ont été jetées et refaites ; `mutants.py` restaure désormais les fichiers à la fin ; (b) parmi ces 6 Haiku figurait un essai sur `wd59` qui avait lu le `CLAUDE.md` du dépôt (retiré des copies ensuite) ; (c) la limite de session a fait échouer 3 appels Opus (`us613`, `us713`, `wl25`) et 1 appel Haiku, repris après sa levée ; (d) mon script de semis sans normalisation aurait laissé des espaces parasites (`max( -1`) trahissant la mutation, corrigé avant le premier semis retenu.

## 6. Décision

**Ne pas ajouter de critique externe à la chaîne sur la foi de cette mesure.** Le critère (au moins 10 points de rappel sans doubler les faux positifs) n'est pas rempli : +6 points, la valeur d'une seule story sur 16, la même pour luna et sol, confirmée par un second tirage ; le bruit n'est pas doublé mais passe de 22 à 34 ou 35 constats Important, presque tous « discutables ».

Si l'on veut tout de même un critique d'une autre famille : **`gpt-6.1-sol`**, plus stable que luna d'un tirage à l'autre (10 défauts sur 11 communs), 22 s et 0,03 $ par story, et un seul constat démontré parmi 5 sur les témoins, à placer après la chaîne sans pouvoir bloquer. Écarter luna seul (8 sur 16, instable) ; ne pas empiler luna et sol (bruit × 2,1 pour aucun défaut de plus).

**Piste d'économie signalée par le test, à confirmer avant d'agir** : en passes indépendantes, Haiku (0,02 $ par story) détecte les 11 mêmes défauts qu'Opus (0,53 $), mais les classe en `low`, d'où 6 Important contre 9. Le rôle d'Opus dans la chaîne (corriger, confirmer, écarter les faux constats de Haiku) n'est pas mesuré ici ; ce résultat n'autorise pas à retirer Opus, seulement à tester une variante « Haiku, puis Opus uniquement si Haiku signale un medium ou plus ».

**Suite utile.** Si l'on veut trancher la question du critique externe, un test de 60 à 100 défauts (3 à 5 par story sur 20 stories, mutants de nature plus variée, dont des omissions de branchement et de cas) avec 2 tirages par relecteur, et le reviewer en mode chaîne réelle (liste de Haiku transmise).

## 7. Fichiers et reproduction

Dossier `tests-pratiques/T5-elargi/` : `stories.py` (les stories candidates : base, commit fusionné, motif de la spec), `candidates.py` (inventaire des fusions par taille de diff), `construire.py` (arbre, diff et spec de chaque story), `lancer_tests.py` (tests ciblés et déselection automatique), `mutants.py` (cosmic-ray borné, réutilise `../T4/mutation_story.py`), `semer.py` (tirage et écriture du défaut, mode `--manuel`, `--temoin`), `essai_mutant.py` (un mutant manuel survit-il aux tests), `revue_claude.py` et `lot_claude.sh` (Haiku et Opus), `revue_gpt.py` (luna et sol, prompt de `../T5/revue.py`), `extraire.py` (constats unifiés), `juger.py` (localisation, préparation de la lecture, application), `analyse.py` et `analyse_r2.py` (agrégats), `grille.md`, `jugements.json`, `jugements_r2.json`, `classification_temoins.json`, `verite.json`, `jeu.json`, `constats*.json`, `detections*.json`, `candidats.json`, `analyse*.json`, `mutation/` (sorties cosmic-ray), `cout_gpt.json`, `reponses/` (réponses brutes : `claude-haiku`, `claude-opus`, `gpt-r1`, `gpt-r2`). Les copies de travail (arbres, environnements, bases cosmic-ray) ont été supprimées.

```
uv run --no-project --python 3.14 python construire.py            # 20 stories
uv run --no-project --python 3.14 python lancer_tests.py <id> --controle
uv run --no-project --python 3.14 python mutants.py <id> --budget-min 8 --sample 70
uv run --no-project --python 3.14 python semer.py <id>            # ou --manuel, --temoin
./lot_claude.sh id1,id2,...                                       # Haiku puis Opus, 2 sessions
uv run --no-project --python 3.14 python revue_gpt.py             # luna et sol (--dossier rep_gpt_r2 pour la passe 2)
uv run --no-project --python 3.14 python extraire.py && uv run --no-project --python 3.14 python juger.py candidats
uv run --no-project --python 3.14 python juger.py appliquer && uv run --no-project --python 3.14 python analyse.py
```

Les scripts supposent le lecteur `T:` (`subst T: <dossier de travail>`) et des `.venv` par dépôt sous `T:\v\<dépôt>` ; Python 3.14 est nécessaire pour analyser la syntaxe de `wavedevsecops`.
