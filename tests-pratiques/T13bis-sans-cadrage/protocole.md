# T13 bis : protocole (figé avant les runs)

Écrit le 25 octobre 2026 à 10 h 15, avant le premier run de cadrage ou de développement de T13 bis. Les seuls résultats vus à ce moment sont ceux de T13 (`../T13-story-legere/resultats.md`) et la validation des tests cachés des nouvelles stories (aucun agent lancé). Toute modification ultérieure est notée comme écart dans `resultats.md`.

## 1. Question

Pour une petite story, peut-on sauter le cadrage BMAD et donner l'entrée de `epics.md` directement à dev-story sans perdre en réussite ? Et cela dépend-il de la richesse de l'entrée ?

T13 a trouvé, hors protocole et sur une seule répétition, que D (sans cadrage) réussit presque autant que A (cadrage BMAD complet) : −2,7 points, IC 95 % [−13 ; +8], pour 76 % de moins. T13 bis confirme ou infirme ce constat avec plus de données et un critère écrit d'avance.

## 2. Bras

Banc de T13 réutilisé sans modification (`t13bis.py` importe `../T13-story-legere/t13.py` et ne fait que rediriger ses chemins). Mêmes réglages d'isolation, mêmes consignes de cadrage (`../T13-story-legere/prompts/`), mêmes CLAUDE.md minimaux (`../T13-story-legere/claude_md/`), même prompt de développement. Claude Code 2.1.310, uv 0.12.23.

- **A, cadrage BMAD complet** : étapes « clarifier » et « planifier » de `bmad-build`, sans interaction (`prompts/cadrage-A.md` de T13), `claude -p --model claude-opus-5-5 --effort medium`, outils Read, Glob, Grep ; puis développement.
- **D, sans cadrage** : l'entrée de `epics.md` et l'interface imposée (`interface.md`) vont directement au développement.
- **Dc, D-court** : comme D, mais l'entrée de `epics.md` est réduite à son titre et à sa phrase « As a… I want… So that… » (ou « En tant que… je veux… afin que… »), sans exigences ni critères (`corpus/<id>/epics_court.md`). L'interface imposée reste donnée (les tests cachés en ont besoin pour importer le code).
- **Développement** (tous les bras) : `claude -p --model claude-sonnet-5-5 --effort medium`, outils Read, Edit, Write, Glob, Grep, Bash, budget 5 $ par run, délai 25 min. Prompt : « Implémente la story suivante, avec ses tests ; lance les tests ciblés avant de finir. », puis l'entrée, la spec du bras (rien pour D et Dc) et l'interface.

Le bras B (voie légère OpenSpec) n'est pas rejoué : T13 l'a écarté.

## 3. Échantillon

**Stories de T13 (10)** : l23, l27, l51, l63, l65, u25, u45, u51, u75, w91, corpus copié de T13 sans changement. Seconde répétition de A et de D (`rep = 2`), sauf A sur l51, qui a déjà deux répétitions en T13.

**Nouvelles stories (12 candidates)**, repérées par `candidats.py` dans les dépôts publics du compte `Aliquanto3` qui ont un `epics.md` (vérifié par `gh repo view Aliquanto3/<nom> --json visibility` : wavelibrarian, usine-migration-jira-demo, service-public-slm-fine-tuning, wavelocalai, wavedevsecops sont PUBLIC ; WaveEval, waveaudit, wavestack, slm-quality-bench sont publics mais sans `epics.md` ; Budget_Tags est privé). Mêmes critères que T13 section 3 : un commit qui ajoute au moins un fichier `tests/**/test_*.py`, au plus trois fichiers source (un fichier de câblage toléré, comme en T13), moins de ~200 lignes de source, l'entrée de la story dans `epics.md` à la base, tests cachés rapides, qui échouent à la base et passent au commit (`t13bis.py reference`). Écartés à la lecture : front JavaScript, Dockerfile, données de fixtures volumineuses, scénarios YAML de wavedevsecops (le gros du travail hors Python), commits « WIP » ou de correction. Aucun dossier `contexte/`, ni `wavestone-content-plugin`, ni `wt-suite`. La spec d'origine n'est pas nécessaire (pas de bras C).

Ordre de priorité fixé maintenant (dépôts alternés), et ordre d'exécution du lot 2 :

| Ordre | Id | Dépôt | Story | Commit | Tests cachés | Source modifiée |
|---|---|---|---|---|---|---|
| 1 | l35 | wavelibrarian | 3.5 Filtre closed-book | `6cf75613` | 11 | `closed_book.py`, `cli.py` (184 l.) |
| 2 | u611 | usine-migration-jira-demo | 6.11 Détection de doublons | `81a97cf0` | 10 | `doublons.py`, `cli.py`, `composition.py` (149 l.) |
| 3 | s52 | service-public-slm-fine-tuning | 5.2 Fonctions de texte partagées | `6db33d0f` | 86 (paramétrés) | `texte.py` (198 l.) |
| 4 | l71 | wavelibrarian | 7.1 RAPTOR | `b9d5cb43` | 7 | `raptor.py` (184 l.) |
| 5 | u78 | usine-migration-jira-demo | 7.8 Outils de consultation de l'Agent | `def3da4a` | 23 | `outils.py`, `pyproject.toml` (196 l.) |
| 6 | l34 | wavelibrarian | 3.4 Juge LLM et exact_match | `037bfab5` | 7 | `llm.py`, `answer.py`, `__init__.py` (115 l.) |
| 7 | s102 | service-public-slm-fine-tuning | 10.2 Rendu en tokens et masque de perte | `670a1000` | 10 | `masque.py`, `rendu.py` (180 l.) |
| 8 | l36 | wavelibrarian | 3.6 Gel et séparation dev / test | `1a5638b0` | 18 | `freeze.py`, `io.py`, `cli.py` (184 l.) |
| 9 | u57 | usine-migration-jira-demo | 5.7 Porte Palier 1 | `5428cbb2` | 8 | `outils/verifier_rejeu.py` (211 l.) |
| 10 | l410 | wavelibrarian | 4.10 Statistiques | `f83b806f` | 6 | 4 petits modules `stats/` (193 l.) |
| 11 | l13 | wavelibrarian | 1.3 Registre de Composants | `2de29d56` | 6 | `registry.py`, `cli.py` (145 l.) |
| 12 | s32 | service-public-slm-fine-tuning | 3.2 Bac à sable MCP | `154ece10` | 41 | `bac_a_sable.py`, `outils.py`, `.toml` (215 l.) |

Les 12 sont validées : tous leurs tests cachés passent au commit et échouent à la base (l35 : 1 test sur 11 passe déjà à la base, gardé comme en T13).

## 4. Strates de richesse de l'entrée

Constat préalable : **toutes** les entrées candidates portent des critères Given/When/Then (ou « Étant donné / quand / alors » dans service-public-slm-fine-tuning). La strate « courte, sans critères » n'existe pas naturellement dans ces dépôts ; le bras Dc la fabrique.

Strates retenues, sur la longueur de l'entrée `epics.md` (seuil fixé à **1 200 caractères**) :

- **détaillée** (≥ 1 200 caractères, plusieurs critères) : l23, l27, l51, l63, l65, u45, u51, et les nouvelles l13, l34, l35, l36, l410, l71, s102, s32, s52 ;
- **brève** (< 1 200 caractères, souvent un seul critère) : u25, u75, w91, et les nouvelles u57, u611, u78.

Honnêteté : ce seuil est fixé après avoir lu les résultats par story de T13, où les trois stories brèves (u25, u75, w91) sont celles où D perd le plus (−18,6 points). Sur les données de T13, l'analyse par strate est donc exploratoire. Elle n'est confirmatoire que sur les **runs de T13 bis seuls** (seconde répétition et nouvelles stories). La strate brève est presque entièrement le dépôt usine-migration-jira-demo (plus w91) : strate et dépôt sont confondus.

## 5. Analyse de puissance (faite avant les runs)

Script `puissance.py`, sortie `donnees/puissance.md`, à partir des seules données de T13 :

- écart type des écarts appariés D − A par story (une répétition) : **17,6 points** ;
- bruit entre deux runs du même bras (l51) : écart type **14,7 points** par run. À lui seul, il expliquerait une variance d'écart de 434, plus que la variance observée (311) : presque tout l'écart entre bras sur une story est du bruit de run ;
- plan simulé : 10 stories de T13 à deux répétitions, plus N nouvelles à une répétition, bootstrap apparié par story, 2 000 simulations.

| N nouvelles | Demi-largeur de l'IC | Puissance, marge 3 | marge 5 | marge 8 | marge 10 |
|---|---|---|---|---|---|
| 8 | 6,6 à 7,2 points | 15 à 18 % | 30 à 34 % | 58 à 64 % | 76 à 82 % |
| 10 | 6,3 à 6,9 | 16 à 17 % | 30 à 34 % | 60 à 67 % | 78 à 84 % |
| 12 | 6,2 à 6,6 | 17 à 18 % | 36 % | 67 à 69 % | 82 à 86 % |

(Puissance si le vrai écart est nul ; si le vrai écart est celui de T13, −2,7 points, la puissance à 10 points tombe à 50 à 64 %.)

**Conclusion** : une marge de 3 points est hors de portée avec 40 $ (moins de 20 % de chances de la démontrer même si les deux bras sont égaux). 5 points aussi (environ un tiers). Il faudrait environ 90 stories pour 5 points. **La marge atteignable est 10 points** (environ 80 % de puissance si les bras sont égaux).

## 6. Critère de décision (écrit avant les runs)

Mesure principale : fraction des tests cachés réussis, moyenne par story sur ses répétitions. Écart D − A en points, moyenne des écarts par story, IC 95 % bootstrap apparié par story, 5 000 rééchantillonnages, graine 13 (`analyse.py`). Toutes les stories où A et D ont au moins un run comptent (T13 répétition 1 comprise).

1. **Non-infériorité principale** : si la borne basse de l'IC de D − A est **au-dessus de −10 points**, D est déclaré non inférieur à A à 10 points près. Sinon : non-infériorité non démontrée, on garde le cadrage.
2. **Coût** : D doit coûter au moins 50 % de moins que A, cadrage compris (ratio agrégé). Attendu largement tenu (−76 % en T13).
3. **Lecture à 5 points** (secondaire) : si la borne basse est aussi au-dessus de −5, la conclusion est renforcée. Avec la puissance calculée, l'échec à 5 points n'est pas une preuve d'infériorité.
4. **Robustesse** : même calcul sur les seuls runs de T13 bis (sans la répétition 1 de T13, qui a fait naître l'hypothèse). Si sa borne basse est sous −10 alors que le critère principal est tenu, la décision est déclarée « fragile ».
5. **Strates** (sur les runs de T13 bis seuls pour la partie confirmatoire) : si, dans la strate brève, l'estimation ponctuelle de D − A est sous −10 points, la règle proposée exclut les entrées brèves.
6. **D-court** : écart Dc − D (même méthode). Si la borne haute de l'IC est sous 0, les critères de l'entrée comptent : la règle exigera des critères Given/When/Then. Si l'IC contient 0 et que l'estimation est au-dessus de −5, l'effet des critères n'est pas démontré.

Mesures secondaires, décrites sans test : coût, tours, durée, `ruff` sur les fichiers modifiés, fichiers hors périmètre, runs à 100 %.

## 7. Plan et budget

Plafond strict : **40 $** de coût client cumulé pour T13 bis (`total_cost_usd`, cadrages et développements). Le garde-fou de `t13bis.py` réserve avant chaque tâche 2,60 $ pour A, 0,70 $ pour D et Dc, et ne lance pas une tâche qui ferait dépasser le plafond du lot ; si A d'une story est sautée, son D l'est aussi.

| Lot | Contenu | Tâches | Coût prévu | Plafond du lot (cumul) |
|---|---|---|---|---|
| 1 | A2 et D2 sur les 10 stories de T13 (pas A sur l51) | 19 | ~15,8 $ | 33,5 $ |
| 2 | A1 et D1 sur les nouvelles stories, dans l'ordre de la section 3 | 24 | ~1,72 $ par story | 33,5 $ |
| 3 | Dc1 sur les stories de T13, puis sur les nouvelles dans l'ordre | 22 | ~0,34 $ par run | 40 $ |

Avec les coûts de T13, le lot 2 devrait s'arrêter vers 10 nouvelles stories et le lot 3 couvrir 15 à 20 stories. Priorité : A et D d'abord, Dc ensuite. Coût suivi après chaque lot (`t13bis.py cout`).

**Avenant (2026-10-25 10:56, pendant le lot 1, transmis par l'orchestrateur, validé par Anaël)** : plafond strict relevé de 40 $ à **45 $** pour couvrir tout le plan : les 12 nouvelles stories en A1 et D1 (lot 2, plafond cumulé 37,5 $), puis tous les runs Dc (lot 3, plafond cumulé 45 $). Le critère de décision (section 6) ne change pas.

Charge : au plus 2 sessions `claude -p` à la fois (`--max 2`), une seule suite de tests à la fois côté banc, seulement les tests cachés ciblés (jamais la suite complète d'un dépôt), ni Ollama ni GPU. Un autre test (T12) tourne sur le poste en même temps. Dossiers jetables sous le scratchpad (chemin long), retirés à la fin. Aucun dépôt d'origine modifié, rien commité.

## 8. Limites connues d'avance

- Tests cachés à plafond bas (cas ajoutés par la revue de la story) : le banc discrimine mal les petits écarts (T13, limite 3).
- Un seul auteur, trois dépôts pour les nouvelles stories (wavelibrarian, usine-migration-jira-demo, service-public-slm-fine-tuning), toutes écrites avec la chaîne BMAD : les entrées `epics.md` sont plus riches qu'une story ordinaire.
- Dc garde l'interface imposée (noms de modules et de classes) : c'est une entrée courte mais pas nue.
- A est `bmad-build` sans interaction, pas `bmad-create-story` (absent), comme en T13.
