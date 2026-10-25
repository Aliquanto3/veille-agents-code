# T13 : une spec courte façon OpenSpec suffit-elle pour une petite story ?

Test pratique T13 de la veille sur les agents de code (`synthese/bilan.json`, entrée `openspec`, laissée « à trancher »). Mesuré le 25 octobre 2026 avec le banc de rejeu (`tests-pratiques/banc-rejeu/`), étendu ici à trois dépôts (`t13.py`). Toutes les sessions passent par l'abonnement Max : les coûts sont l'estimation client `total_cost_usd`, en dollars aux tarifs catalogue. Total engagé : **29,28 $** (cadrages 15,33 $, développements 12,93 $, pilote écarté 1,01 $).

## 1. Résultat en bref

- **Coût** : la voie légère (B) coûte **46 % de moins** que la story BMAD complète (A), cadrage compris : 0,74 $ contre 1,38 $ par story, IC 95 % bootstrap apparié [−55 % ; −36 %]. Le gain vient du cadrage (0,39 $ contre 1,00 $, 13 tours contre 25) ; le développement ne baisse que de 9 % (0,35 $ contre 0,38 $).
- **Réussite aux tests cachés** : B réussit **10,2 points de moins** que A (62,3 % contre 71,9 % des tests cachés ; IC [−18,8 ; −2,6]). B n'est jamais meilleure que A sur une story (5 stories en dessous, 5 à égalité). Le seuil de 3 points n'est pas tenu.
- **Critère de la veille** : coût −25 % atteint, réussite non tenue. **Décision : ne pas adopter la voie légère, garder BMAD.**
- **Constat hors protocole, à confirmer** : un bras D sans aucun cadrage (l'entrée de `epics.md` plus l'interface imposée, directement à dev-story) réussit autant que A (70,3 % contre 71,9 % ; D moins A : −2,7 points, IC [−13 ; +8]) pour **0,34 $** par story, soit 76 % de moins que A et 55 % de moins que B. Sur ces petites stories, dont l'entrée `epics.md` contient déjà des critères Given/When/Then, aucun des deux cadrages ne s'est payé.
- **Plan réduit** : le budget de 30 $ n'a permis qu'**une répétition** par bras et par story (sauf une story à deux répétitions), soit 35 développements et 22 cadrages au lieu de 60 et 40. Voir sections 2 et 7.

## 2. Protocole exact

**Question.** Pour une petite story (un ou deux fichiers source), une spec courte façon OpenSpec suffit-elle, à réussite égale et pour moins cher au total (cadrage compris) qu'une story BMAD complète ?

**Banc.** `banc-rejeu/banc.py` (T3) généralisé dans `T13-story-legere/t13.py`. Pour chaque exécution : dossier jetable créé par `git archive <base> | tar -x` puis `git init` et un commit (aucun historique) ; `.claude/`, `CLAUDE.md` et `AGENTS.md` du dépôt retirés ; un `CLAUDE.md` minimal par dépôt (`claude_md/`, commandes `uv run`, ruff et pytest, mêmes règles pour tous les bras) ; tests cachés retirés ; `uv sync --frozen` ; `claudeMdExcludes` pour le CLAUDE.md utilisateur ; `--setting-sources project,local` ; mémoire automatique coupée ; variables KEY, TOKEN, SECRET, PASSWORD, CREDENTIAL retirées. Au plus 2 sessions `claude -p` à la fois, une seule suite de tests à la fois (verrou). Aucun dépôt d'origine modifié, rien commité ni poussé.

**Entrée commune.** L'entrée de la story dans `epics.md` à la base (`corpus/<id>/epics.md`), plus l'interface imposée du banc (`interface.md` : noms que les tests cachés importent et qui manquent à la base). Les trois dépôts sont publics (`gh repo view` : PUBLIC).

**Cadrage.** Session `claude -p --model claude-opus-5-5 --effort medium`, outils Read, Glob, Grep seulement, dans le dépôt à la base, sans interaction. La réponse finale est le document de spec (`donnees/specs/`).

- **Bras A, BMAD complet.** Méthode de `bmad-build` (étape 1 « clarifier » et étape 2 « planifier », norme « Ready for Development » et norme de taille de `workflow.md`, modèle `spec-template.md`), copiée telle quelle dans `prompts/bmad-build/`, avec un en-tête qui retire les interactions (`prompts/cadrage-A.md`) : les questions ouvertes sont tranchées par l'agent et notées dans une section « Décisions prises sans l'utilisateur », voie complète imposée (pas de voie one-shot). **Écart au protocole** : le skill `bmad-create-story` n'existe plus dans l'installation (`GitHub/.claude/skills/` ne contient que `bmad-build`, `bmad-spec`, etc., et le dépôt `usine-migration-jira-demo` n'en a pas non plus). `bmad-build` est le skill qui a produit les specs `spec-*.md` de ces dépôts : c'est sa moitié « planification » qui sert de cadrage BMAD.
- **Bras B, voie légère.** Format du schéma `spec-driven` de OpenSpec, commit `6d04a1b58dedc95729d34e4f223d9d483aae210a` de `Fission-AI/OpenSpec` (24 octobre 2026) : instructions des artefacts `proposal`, `specs`, `tasks` et leurs modèles, copiés dans `prompts/openspec/` (pas de paquet npm installé). Production : `proposal.md` (Why, What Changes, Capabilities, Impact, plus une section Hypothèses pour les décisions de l'agent), delta de spec (`ADDED Requirements`, scénarios WHEN/THEN) et `tasks.md`. Pas de `design.md` (les critères du schéma pour en écrire un ne sont pas réunis). `prompts/cadrage-B.md` ajoute la consigne de taille « 500 à 900 tokens, une dizaine de lectures au plus » (voir la limite 5).
- **Bras C, référence.** La spec BMAD d'origine du dépôt, nettoyée comme en T3 (Intent, Boundaries, matrice d'E/S, Code Map, Tasks, Design Notes ; frontmatter, journaux de revue et de dev retirés). Un seul développement, sans cadrage.
- **Bras D, ajouté hors protocole.** Aucun cadrage : entrée de `epics.md` et interface seulement.

**Développement.** Identique pour tous les bras : `claude -p --model claude-sonnet-5-5 --effort medium`, outils Read, Edit, Write, Glob, Grep, Bash, mêmes `--allowedTools` que T3, budget 5 $ par run, délai 25 min. Prompt : « Implémente la story suivante, avec ses tests ; lance les tests ciblés avant de finir. », puis l'entrée de `epics.md`, la spec du bras (rien pour D) et l'interface.

**Mesures.** Par étape : coût, tours, durée, tokens (JSON de sortie et transcription). Développement : fraction des tests cachés qui passent (`taux`), `ruff check` et `ruff format --check` sur les fichiers modifiés par l'agent, fichiers touchés hors du périmètre du commit d'origine. La suite complète du dépôt n'est pas rejouée (charge locale). Les tests cachés sont les fichiers de tests **ajoutés** par le commit de la story, plus les fichiers d'appui de tests (`conftest.py`, aides) que le commit **modifie** : voir la limite 3.

**Statistique.** Unité du bootstrap : la story (coûts et taux moyennés sur ses répétitions). 5 000 rééchantillonnages, graine 13. Coût : somme des coûts totaux de B divisée par celle de A, moins 1. Réussite : moyenne des écarts de taux, en points. Lecture de `A_vs_B` : B relativement à A ; `A_vs_D` : D relativement à A.

## 3. Stories choisies

Critères : 1 ou 2 fichiers source modifiés (voir la note), moins de ~150 lignes de source, tests ajoutés par le commit exécutables en quelques secondes, entrée de la story dans `epics.md` à la base, spec présente au commit de la story. 12 candidats validés par `t13.py reference` (les tests cachés échouent à la base, passent au commit) ; deux écartés : `slmsp` 13.2 (tests marqués `ui`, 0 test exécuté) et `wavelocalai` 5.6 (les 8 tests cachés passent déjà à la base). Les dépôts `wavedevsecops` (stories rédigées après coup, front JavaScript) et `service-public-slm-fine-tuning` (aucune story Python seule avec test rapide) n'ont fourni aucune story utilisable : **3 dépôts au lieu de 5**.

| Id | Dépôt | Story | Commit (base) | Tests cachés | Source | C |
|---|---|---|---|---|---|---|
| u51 | usine-migration-jira-demo | 5.1 Étapes déterministes et Passage autoportant | `00b07955` (`affbd8fe`) | 6, plus `environnement.py` | `etapes.py`, `composition.py` (143 l.) | oui |
| u25 | usine-migration-jira-demo | 2.5 Source Journal à l'échelle | `5f083236` (`f80fa13e`) | 13, plus `fabriques.py` | `journal/__init__.py`, `manifeste.py`, `composition.py` (70 l.) | oui |
| u45 | usine-migration-jira-demo | 4.5 Recette de la Prévision | `0febaeba` (`a663bf35`) | 3 (52 s) | `risque.py` (8 l.) | non jouée |
| u75 | usine-migration-jira-demo | 7.5 Écran « Ce qu'il faut pour le faire en vrai » | `97734e64` (`54606dc3`) | 8, plus `conftest.py` | `app.py`, `navigation.py`, `outillage.py` (56 l.) | non jouée |
| l63 | wavelibrarian | 6.3 HyDE | `558b621f` (`67792b6c`) | 8 | `hyde.py` (94 l.) | oui |
| l65 | wavelibrarian | 6.5 CAG | `8900082d` (`54506ed0`) | 8 | `cag.py`, `llm.py` (74 l.) | non jouée |
| l27 | wavelibrarian | 2.7 Paliers de volume | `347310df` (`a0591dbb`) | 9 | `cli.py`, `tiers.py` (77 l.) | non jouée |
| l51 | wavelibrarian | 5.1 Annotations humaines et kappa | `2229b27c` (`ddd19521`) | 14 | `calibration.py`, `kappa.py` (148 l.) | non jouée |
| l23 | wavelibrarian | 2.3 Ingestion PDF par page | `fe4f03d3` (`5e10d2be`) | 7 | `pdf_text.py`, `ingest.py` (70 l.) | non jouée |
| w91 | wavelocalai | 9.1 Le lanceur ouvre le navigateur | `ab1fcfec` (`ba606cb2`) | 6 | `__main__.py`, `config.py` (57 l.) | non (story rédigée après coup) |

Notes. u75 touche 3 fichiers source, u25 et w91 aussi si l'on compte `composition.py` ou le `.toml` : la contrainte « un ou deux fichiers » est tenue à un fichier de câblage près. La spec d'origine de wavelibrarian cite les tests dans ses tâches : ces renvois sont retirés pour C. Les entrées de `epics.md` sont déjà détaillées (critères Given/When/Then), ce qui pèse sur la lecture des résultats (limite 1).

## 4. Résultats par bras

Moyennes par exécution (11 pour A et B car la story l51 a deux répétitions). Données : `donnees/runs.jsonl`, `donnees/cadrages.jsonl`, `donnees/analyse.md`, `donnees/agregats.json`.

| Bras | n | Cadrage $ | tours | s | Dév. $ | tours | s | **Total $** | tours | s | Tests cachés | 100 % | ruff propre |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A BMAD complet | 11 | 1,00 | 25,1 | 152 | 0,38 | 27,7 | 232 | **1,38** | 52,8 | 384 | **71,9 %** | 2/11 | 10/10 |
| B voie légère | 11 | 0,39 | 12,9 | 83 | 0,35 | 27,5 | 270 | **0,74** | 40,4 | 352 | **62,3 %** | 2/11 | 9/10 |
| D sans cadrage (hors protocole) | 10 | 0 | 0 | 0 | 0,34 | 23,8 | 137 | **0,34** | 23,8 | 137 | **70,3 %** | 2/10 | 8/9 |
| C spec d'origine | 3 | 0 | 0 | 0 | 0,51 | 37,0 | 227 | **0,51** | 37,0 | 227 | 97,4 % | 2/3 | 3/3 |

La taille de la spec produite est de 9 900 caractères en moyenne pour A (environ 2,5 k tokens, au-dessus de la norme de 900 à 1 600 tokens de BMAD) et de 6 600 pour B (environ 1,7 k tokens, au-dessus de la cible de 500 à 900 que je lui avais donnée). `ruff` : mesuré sur 10 des 11 runs A ; non mesurable pour `wavelocalai` (ruff absent de l'environnement, −1 dans les données). Fichiers hors périmètre (fichiers modifiés par l'agent qui ne le sont pas par le commit d'origine) : A 3/11, B 5/11, D 6/10 ; ce sont surtout des fichiers de tests que l'agent nomme autrement ; trois cas touchent du source (`execution.py` en u51-A1, `long_context.py` en l65-B1 et l65-D1, `etapes.py` en u45-D1).

### Comparaisons appariées (10 stories, IC 95 % bootstrap)

| Comparaison | Coût total | Dont développement seul | Tests cachés (points) | Moins cher |
|---|---|---|---|---|
| B contre A | **−46,4 %** [−55,3 ; −36,1] | −9,3 % | **−10,2** [−18,8 ; −2,6] | 10/10 |
| D contre A | −76,1 % [−79,7 ; −71,4] | −15,1 % | −2,7 [−13,2 ; +7,6] | 10/10 |
| D contre B | −55,4 % [−61,0 ; −49,6] | −6,4 % | **+7,5** [+1,1 ; +13,8] | 10/10 |

(Le coût relatif moyen par story donne −42,4 % [−50,9 ; −34,7] pour B contre A.)

### Par story (total en dollars, dont cadrage entre parenthèses ; fraction des tests cachés)

| Story | A | B | D | C |
|---|---|---|---|---|
| l23 | 0,87 (0,64) ; 100 % | 0,67 (0,39) ; 100 % | 0,27 ; 100 % | n.j. |
| l27 | 0,99 (0,72) ; 89 % | 0,61 (0,33) ; 67 % | 0,28 ; 78 % | n.j. |
| l51 (2 rép.) | 1,05 (0,82) ; 61 % | 0,57 (0,37) ; 57 % | 0,27 ; 71 % | n.j. |
| l63 | 1,39 (1,08) ; 88 % | 0,67 (0,38) ; 62 % | 0,41 ; 75 % | 0,50 ; 100 % |
| l65 | 1,33 (0,86) ; 62 % | 0,86 (0,35) ; 62 % | 0,49 ; 88 % | n.j. |
| u25 | 1,46 (0,90) ; 85 % | 0,76 (0,39) ; 46 % | 0,32 ; 54 % | 0,52 ; 92 % |
| u45 | 2,45 (1,91) ; 100 % | 0,75 (0,39) ; 100 % | 0,38 ; 100 % | n.j. |
| u51 | 2,40 (1,72) ; 50 % | 1,15 (0,64) ; 50 % | 0,49 ; 67 % | 0,49 ; 100 % |
| u75 | 1,07 (0,68) ; 62 % | 0,69 (0,36) ; 50 % | 0,22 ; 38 % | n.j. |
| w91 | 1,14 (0,84) ; 33 % | 0,86 (0,37) ; 33 % | 0,27 ; 33 % | n.j. |

Bruit : sur la seule story rejouée, l51, les deux répétitions de B donnent 71 % et 43 % (A : 57 % et 64 %). Un seul run par story ne sépare donc pas bien deux bras proches ; l'écart de 10 points de B contre A repose sur 10 stories, pas sur la répétition.

## 5. Coût par étape

| Étape | Coût moyen | Tours | Durée |
|---|---|---|---|
| Cadrage A (Opus, medium) | 1,00 $ (de 0,63 à 1,91) | 25 | 152 s |
| Cadrage B (Opus, medium) | 0,39 $ (de 0,33 à 0,64) | 13 | 83 s |
| Développement A (Sonnet, medium) | 0,38 $ | 27,7 | 232 s |
| Développement B | 0,35 $ | 27,5 | 270 s |
| Développement D | 0,34 $ | 23,8 | 137 s |
| Développement C | 0,51 $ | 37,0 | 227 s |

Le cadrage A pèse 72 % du coût total de A. Les deux cadrages coûtent d'abord des lectures du dépôt (le cadrage A lit en plus les documents de planification et la story précédente). Le développement profite peu de la spec : le développement de A coûte 0,38 $ contre 0,35 $ pour B et 0,34 $ pour D, et les specs A et B ne diminuent pas le nombre de tours de dev (27,7 et 27,5, contre 23,8 pour D).

Coût engagé : cadrages 15,33 $ (22 runs), développements 12,93 $ (35 runs), pilote écarté 1,01 $ (un cadrage B sans consigne de taille : 13 850 caractères, 1,01 $, plus cher que le cadrage A du même essai, 1,08 $ ; copie dans `donnees/pilote/`). Projeté pour le plan complet à 2 répétitions : environ 50 à 55 $.

## 6. Exemples de specs courtes

**Réussie : l23-B1 (ingestion PDF, 7 tests sur 7, 0,67 $ au total).** Le proposal tient en 15 lignes ; il nomme le Parser, l'Ancrage `<doc_id>#p<page>`, et surtout un test existant qu'il faut adapter (`tests/unit/corpus/test_ingest.py:215-216` affirme que `pdf_text` est indisponible). Les hypothèses fixent les cas que l'entrée `epics.md` laisse ouverts : une page sans texte donne un Ancrage sans Block, toute erreur pypdfium2 devient `ValueError("PDF illisible : ...")`. C'est le profil des succès : une story à un fichier neuf, un comportement que le dépôt voisin permet de copier.

**Ratée : u25-B1 (Source Journal, 6 tests sur 13).** Le delta de spec est propre (cinq requirements, scénarios WHEN/THEN) mais l'hypothèse « les entrées de la correspondance qui n'apparaissent pas dans le Journal sont tolérées » est fausse : un test caché exige une `UsineErreur` qui nomme le fichier et la clé obsolète (cas ajouté par la revue de la story, absent de `epics.md`). La spec A (11 sur 13) avait fait le même choix, « entrées en trop ignorées », et ne rate que ce cas et celui de la date d'injection incohérente. B échoue en plus sur cinq tests qui dépendent de la forme exacte de l'API, que ni `epics.md` ni sa liste de tâches ne fixent (par exemple le message attendu « objet JSON attendu » pour un manifeste qui n'est pas un objet, le comportement sans manifeste). Dans les deux bras, la limite de fond est la même : un cas de bord que ni l'entrée de la story ni le code ne disent.

**Ratée, causes mixtes : l63-B1 (HyDE, 5 sur 8).** Le seul échec de A (7 sur 8) est `test_retriever_lexical_refuse` (un Retriever lexical doit lever `ConfigError`), que ni A ni B ne demandaient. B manque en plus `test_enregistrement_defauts_et_meme_index_que_naive_rag` et `test_reponse_hypothetique_vide_se_rabat_sur_la_question`. Je n'ai pas analysé ces deux échecs plus loin : la spec A donnait une matrice d'E/S et des paramètres exacts (`query_params`, repli sur la Question), la spec B des scénarios plus généraux.

Les trois specs complètes sont dans `donnees/specs/` (`l23-B1.md`, `u25-B1.md`, `l63-B1.md`, et leurs équivalents A) ; un exemple de spec B trop longue est dans `donnees/pilote/`.

## 7. Limites

1. **Une entrée de story déjà riche.** Les entrées de `epics.md` de ces dépôts portent des critères Given/When/Then. Le développeur les reçoit dans tous les bras ; c'est ce qui explique qu'un bras sans cadrage (D) égale A. Sur une story dont l'entrée est une ligne, le cadrage pèserait davantage. Le résultat vaut pour ces dépôts.
2. **Une répétition au lieu de deux.** Le budget (30 $) n'a pas permis le plan complet (environ 50 à 55 $). La règle prévue (C à une répétition) ne suffisait pas : j'ai choisi une répétition pour A, B et D sur 10 stories plutôt que deux répétitions sur 5, et une seconde répétition sur l51 seulement. C n'est joué que sur 3 stories. L'IC repose sur 10 stories ; il ne mesure pas la variance d'un run (voir le bruit de l51).
3. **Plafond et définition des tests cachés.** Les tests cachés contiennent des cas ajoutés par la revue de la story (voir u25) : seulement 2 runs sur 11 passent tous les tests, dans A comme dans B. Le banc discrimine mal les petits écarts. Les fichiers d'appui de tests modifiés par le commit (`environnement.py`, `fabriques.py`, `conftest.py`) sont remis dans leur version finale à la mesure ; sans eux, u51 mesurait 0 sur 6 pour les trois bras (erreur de collecte), ce que j'ai corrigé en mesurant de nouveau les trois runs à partir de leurs patches (champ `reeval` des données).
4. **C n'est pas une vérification de réalisme de A.** La spec d'origine est le fichier du commit : sa Code Map et ses tâches ont été mises à jour pendant le développement et la revue, elle contient en partie la solution (97 % de réussite, contre 72 % pour A). C sert de plafond optimiste, non de preuve que A est réaliste. Pour `wavelocalai`, aucune spec d'origine n'est exploitable (story rédigée après coup).
5. **B n'est pas l'OpenSpec brut.** Sans consigne de taille, le premier cadrage B (pilote) a produit 13 850 caractères et coûté 1,01 $. J'ai ajouté une cible de taille (500 à 900 tokens, une dizaine de lectures) pour qu'il soit une voie légère ; les specs obtenues font encore 1,7 k tokens. Ni la CLI `openspec`, ni son dossier `openspec/specs`, ni les commandes `/opsx` ne sont utilisés : seul le format et les consignes d'écriture le sont. Pas de `design.md`.
6. **A est `bmad-build` sans interaction**, pas `bmad-create-story` (absent). Les points de validation humaine (questions ouvertes, découpage) sont remplacés par des décisions notées de l'agent. La voie one-shot de BMAD, qui produirait une spec très courte pour une petite story sans zone d'ombre, est volontairement désactivée.
7. **Trois dépôts, un seul auteur, un seul modèle de développement** (Sonnet 5.5, effort medium). Les stories ont toutes été écrites avec la chaîne BMAD du même auteur : les tests cachés reflètent ses revues.
8. **Mesures annexes** : « fichiers hors périmètre » compte aussi les fichiers de tests que l'agent nomme autrement ; la suite complète du dépôt n'a pas été rejouée ; le lint de `wavelocalai` n'est pas mesurable ; u45 s'exécute en 53 s sous charge, pas en quelques secondes. Deux modèles de cadrage seulement (Opus medium) ; pas de test avec Sonnet au cadrage.

## 8. Décision

Selon le critère posé :

- Coût total de B au moins 25 % sous A : **oui** (−46 %, IC [−55 ; −36]).
- Réussite de B pas inférieure de plus de 3 points à A : **non** (−10,2 points, IC [−18,8 ; −2,6]).

**La voie légère n'est pas adoptée ; BMAD reste la voie par défaut, y compris pour les petites stories.** L'entrée `openspec` du bilan peut passer de « à trancher » à « testée, non retenue pour le cadrage de story ». Raisons : sa spec courte ne laisse pas à dev-story les valeurs exactes (cas d'erreur, signatures, constantes) qu'une matrice d'E/S et une section « Never » lui donnent, et ses « Hypothèses » écrites sans l'utilisateur ont tranché à tort plusieurs cas de bord.

**Piste plus intéressante que B, à tester avant d'en tirer une règle** : pour une petite story dont l'entrée de `epics.md` est déjà détaillée, le cadrage BMAD complet ne s'est pas payé (A = 1,38 $ contre 0,34 $ pour D, à réussite voisine : −2,7 points, IC [−13 ; +8], donc non-infériorité non démontrée). Une étape de décision, « la story est-elle assez détaillée pour aller directement à dev-story ? », pourrait économiser jusqu'aux trois quarts du coût de ces stories. Test suivant (T13 bis, environ 35 $ pour D et A sur 10 autres petites stories à deux répétitions chacun) : avec un critère de non-infériorité de 3 points sur un IC resserré, et un contrôle des cas de bord par le `reviewer` plutôt que par les seuls tests cachés. Ne pas modifier la chaîne `agent-cost-kit` avant ce second test.

## 9. Reproduire

Depuis `tests-pratiques/T13-story-legere/` (un seul processus à la fois ; `-I` pour les scripts autonomes) :

```
uv run --no-project python -I t13.py extraire tout      # corpus depuis les trois dépôts (epics, tests cachés, spec nettoyée)
uv run --no-project python -I t13.py reference u51 ...   # tests cachés : commit = tout passe, base = échec ; écrit interface.md
uv run --no-project python -I t13.py appui u51 u25 u75 w91   # fichiers d'appui de tests, puis référence
uv run --no-project python -I t13.py lot plan1.json --max 2  # bras A, B, C (cadrage Opus puis dev Sonnet)
uv run --no-project python -I t13.py lot plan2.json --max 2  # bras D
uv run --no-project python -I t13.py lot plan3.json --max 2  # seconde répétition de l51
uv run --no-project python -I analyse.py > donnees/analyse.md
```

Fichiers : `t13.py` (banc), `analyse.py`, `cout.py`, `stories13.json`, `plan1.json` à `plan3.json`, `prompts/` (consignes de cadrage et sources BMAD et OpenSpec utilisées), `claude_md/`, `corpus/<id>/` (meta, entrée `epics.md`, interface, spec d'origine brute et nettoyée, tests cachés), `donnees/` (`runs.jsonl`, `cadrages.jsonl`, `specs/` produites, `patches/`, `brut/` JSON de sortie, journaux de lots, `pilote/`). Les chemins locaux des fichiers bruts sont anonymisés (`banc-rejeu/anonymiser.py`). `lot1-partie1.log` est le journal de la première partie du lot 1, interrompue pour ajouter les fichiers d'appui ; `lot1.log` et `lot1b.log` en sont la suite.

## 10. Synthèse

- B coûte 46 % de moins que A (0,74 $ contre 1,38 $ par story, IC [−55 ; −36]), le gain venant du cadrage (0,39 $ contre 1,00 $).
- B réussit 10,2 points de moins que A aux tests cachés (62 % contre 72 %, IC [−19 ; −3]) : le seuil de 3 points n'est pas tenu.
- Décision : voie légère non adoptée, BMAD reste la voie par défaut, y compris pour les petites stories.
- Constat à confirmer : sans aucun cadrage, dev-story réussit autant que A (70 % contre 72 %) pour 0,34 $ ; piste T13 bis (D contre A, 2 répétitions, 10 autres stories).
- Plan réduit à une répétition (29,28 $ sur 30 $, 35 développements et 22 cadrages), trois dépôts sur cinq, `bmad-create-story` absent remplacé par `bmad-build`.
