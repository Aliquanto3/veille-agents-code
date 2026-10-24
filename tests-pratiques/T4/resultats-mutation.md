# T4 (volet sans rejeu) : mutation testing borné aux fichiers d'une story

Date : 2026-10-24. Question : le mutation testing, borné aux fichiers d'une story, révèle-t-il des tests faibles écrits par des agents, en un temps acceptable ? Critère de la veille : porte de CI ou étape du reviewer si moins de 10 minutes par story et au moins un vrai test faible sur 2 stories.

## Verdict en bref
- **Révélation : oui, sur 5 stories sur 5.** Chaque story contient au moins un vrai trou de test que la couverture ne voit pas (détail plus bas). Le critère « au moins un vrai test faible sur 2 stories » est rempli.
- **Délai : non en général.** Seule 1 story sur 5 tient sous 10 minutes (5.9 : 1,7 min) ; 7.15 prend 13,5 min ; les trois autres dépassent le budget de 20 min (estimation du plein : 24 à 42 min). Le critère « moins de 10 minutes par story » n'est pas rempli tel quel.
- **Décision proposée : pas de porte de CI bloquante.** Étape optionnelle du reviewer (ou job CI nocturne en matrice par fichier), bornée aux lignes modifiées, avec budget de 10 min et rapport des survivants dédoublonnés par ligne. Voir la fin.

## Protocole
- **Stories** (5 fusionnées, développées par la chaîne d'agents, dépôts publics Python) :

| Id | Dépôt | Story | Commits (feat..revue) | Fichiers source mutés | Tests de la story |
|---|---|---|---|---|---|
| wd-5-9 | wavedevsecops | 5.9 encart « Ce qui l'aurait bloqué » | 45fb3b4..66cefe8 | `web/blockers.py`, `scenarios/model.py`, `scenarios/loader.py` | `tests/test_blockers.py` |
| wd-8-4 | wavedevsecops | 8.4 quality gate de couverture | 462f726..e5247df | `ci/findings.py`, `scenarios/ops/replace_in_file.py`, `toolrun/__init__.py`, `ci/__init__.py` | `tests/test_quality_gate.py` |
| us-7-14 | usine-migration-jira-demo | 7.14 carte météo, détail d'une entité, livrables | 9e4639c..23c1fd3 | `ui/carte.py`, `detail.py`, `vues.py`, `serveur.py`, `cli.py`, `liens.py` | `test_vues_ecrans.py`, `test_serveur.py`, `contrat/consultation/test_contrat.py` |
| us-7-15 | usine-migration-jira-demo | 7.15 lancement de la Chaîne, bouton de mode | d58ce6c..c86b2f7 | `ui/chaine.py`, `vues.py`, `serveur.py`, `app.py`, `textes.py` | `test_chaine.py`, `test_serveur.py`, `test_vues_ecrans.py`, `test_cli.py` |
| us-7-16 | usine-migration-jira-demo | 7.16 Agent, Avant / après, Pseudonymisation, Outillage | 5545523..cf54141 | `ui/ecrans.py`, `outillage.py`, `pseudonymisation.py`, `vues.py`, `serveur.py`, `cli.py` | `test_ecrans_web.py`, `test_vues_ecrans.py`, `test_serveur.py`, `test_chaine.py` |

  wavelocalai écarté : ses stories récentes (v2) sont surtout du JavaScript, hors périmètre Python.
- **Copies jetables** : `git worktree add --detach` au dernier commit de la story, dans `…\scratchpad\t4\<id>` ; les dépôts ne sont pas touchés (trois `git worktree` à retirer, voir « Nettoyage »). Pour usine, le chemin dépasse la limite Windows de 260 caractères : checkout creux (`src`, `tests`, `config`, `docs/*.md`, `demo`, `outils`, `evals`, `gabarits`, `donnees`).
- **Mutation bornée** à trois niveaux : (1) fichiers source de la story ; (2) seules les lignes ajoutées ou modifiées par la story (`git diff -U0 <base> HEAD`) ; (3) tests de la story seulement, `pytest -x` (arrêt au premier échec). Un mutant dans une annotation de type est retiré du plan (équivalent sous `from __future__ import annotations` : cosmic-ray y mute `X | None` en `X ** None`, 33 faux survivants sur 68 dans la première story).
- Budget : 20 min par story (arbre de processus tué à l'échéance). Un seul outil de mutation à la fois, un seul processus de test à la fois, pas de parallélisme.

## Outil retenu : cosmic-ray 8.7.0
- **WSL non installé** (`wsl -l -v` : « Le sous-système Windows pour Linux n'est pas installé »), donc **mutmut est exclu** sur ce poste (il exige WSL ou Linux).
- **cosmic-ray fonctionne sous Windows**, avec deux pièges :
  1. `uv run --with cosmic-ray` ne convient pas : la commande de test lancée par cosmic-ray résout `python` vers l'interpréteur de base, pas celui de l'overlay, et la ligne de base échoue sans message (tous les mutants sont alors « tués » à tort, résultat 0 % de survie trompeur). Solution : `uv pip install cosmic-ray` dans le `.venv` de la copie jetable (isolé, jetable) et chemin absolu de l'interpréteur dans `test-command`.
  2. Si l'on tue cosmic-ray à l'échéance, le fichier du dernier mutant reste muté dans la copie : `git checkout -- src` avant toute mesure suivante (la première série de diff-cover tournait sur des fichiers mutés, refaite).
- Python 3.14 : cosmic-ray 8.7 gère la syntaxe `except A, B:` du dépôt wavedevsecops.

## Résultats de mutation
Taux de survie = survivants / mutants exécutés. « Effectifs » = mutants après retrait des annotations et des lignes hors diff.

| Story | Générés (fichiers entiers) | Retirés : annotations | Retirés : hors diff | Effectifs | Exécutés | Tués | Survivants | En attente (budget) | Taux de survie | Délai | s par mutant | Estimation du plein |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| wd-5-9 | 606 | 200 | 336 | 70 | 70 | 43 | 27 | 0 | **38,6 %** | 1,7 min | 1,4 | 1,6 min |
| wd-8-4 | 2102 | 442 | 1397 | 263 | 122 | 92 | 30 | 141 | **24,6 %** | 20 min (budget atteint) | 9,6 | 42 min |
| us-7-14 | 1376 | 481 | 511 | 384 | 322 | 250 | 72 | 62 | **22,4 %** | 20 min (budget atteint) | 3,7 | 23,5 min |
| us-7-15 | 853 | 214 | 418 | 221 | 221 | 184 | 32 (+5 incompétents) | 0 | **14,5 %** | 13,5 min | 3,6 | 13,1 min |
| us-7-16 | 1048 | 382 | 326 | 340 | 241 | 209 | 32 | 99 | **13,3 %** | 20 min (budget atteint) | 4,9 | 27,7 min |

Lecture :
- Les survivants sont **concentrés** : 96 lignes distinctes pour 193 survivants. 55 % des survivants sont des variantes d'opérateur de comparaison (jusqu'à 11 variantes de `==` sur la même ligne) ; après dédoublonnage par ligne, il reste 11, 14, 38, 16 et 17 lignes à examiner par story.
- Le coût est surtout le **temps de la suite ciblée par mutant** : 1,9 s (wd-5-9) à 24,7 s (wd-8-4, vrais outils bandit/coverage lancés dans les tests) par exécution de la suite, 1,4 à 9,6 s par mutant avec `-x`.
- Estimation du plein pour les stories coupées : pour wd-8-4, us-7-14 et us-7-16, l'extrapolation suppose le même temps par mutant sur les mutants non exécutés (modules restants plus petits : estimation haute).

## Ce que révèlent les survivants (exemples)
Classement : **trou réel** (comportement non vérifié), **faible** (vrai mais peu utile), **équivalent / bruit**.

**wd-5-9 (`web/blockers.py`, `model.py`)**
- `except (ScenarioError, OSError, UnicodeDecodeError)` : remplacer **chacune** des trois exceptions survit, ainsi que `continue` -> `break`. Aucun test ne fournit un scénario illisible : la branche « scénario ignoré avec avertissement » est non testée (diff-cover le voit aussi : lignes 41-43 non couvertes). **Trou réel.**
- `scenario.mode == "A" or scenario.scenario_id not in titles` : `==` -> `!=`, `or` -> `and` survivent. Le choix du titre quand un scénario existe en mode A et B n'est pas vérifié. La ligne est couverte, mais l'assertion ne distingue pas les deux titres. **Trou réel (test sans assertion discriminante).**
- `station: int = Field(ge=1, le=4)` : bornes 0/3/5 survivent ; `reason_text` `min_length` 0 ou 2 survivent. Bornes de validation non testées. **Trou réel, faible** (le schéma est validé en amont par le lint `chain.yaml`).
- `if delivered and title is None:` (avertissement de scénario absent du catalogue) : `is None` -> `is not None`, `not delivered` survivent : message de journal non vérifié. **Faible.**
- `ConfigDict(frozen=True)` -> `False` : immutabilité non testée. **Faible.**

**wd-8-4 (quality gate, `ci/findings.py`)**
- `_ranges` (met en forme « 12 » ou « 12-15 » les lignes non couvertes) : douze variantes de `start == previous` et `line == previous + 1` survivent. Le texte du constat affiché à l'apprenant n'est testé qu'avec une forme. **Trou réel** : une régression ferait afficher « 12-12 ».
- `parse_diff_cover_json` : `measured = total > 0` -> `> 1` ou `!= 0`, `continue` -> `break` (deux fois), `noun = "ligne" if count == 1` -> `== 0` / `== 2`, `severity="error" if not passed` inversé : seuil de mesure, pluriel et sévérité d'un constat non vérifiés. **Trou réel** (le cas d'une seule ligne manquante et celui d'aucune ligne mesurée ne sont pas testés ; diff-cover voit les lignes 394, 406 non couvertes).
- `parse_coverage_json` : `except KeyError, TypeError, ValueError` remplacé : couverture illisible non testée (lignes 437-438). **Trou réel**, et recoupé par diff-cover.
- `replace_in_file.py` : `@classmethod` et `@field_validator("old")` supprimés survivent : validateur d'entrée jamais exercé. **Trou réel.**

**us-7-14 (`ui/carte.py`, `detail.py`)**
- `detail.py` `_bloc_une_prevision` / `section_prevision` : toute la logique de statut de prévision (`is StatutPrevision.sortie_projetee`, `pas_de_sortie_projetee`, `AddNot` sur le titre et les facteurs) survit, avec 20 variantes de comparaison. Le bloc de prévision (facteurs explicatifs, sortie du rouge estimée) n'est pas testé dans ses branches. **Trou réel** (diff-cover le voit partiellement : 438-439, 459).
- `carte.py` `taille_lisible` : toutes les bornes 1023/1024/1025 survivent, `libelle_suite` à `reste > 1` : le formatage « 1,0 Mo / 512 octets » n'est testé que loin des seuils. **Trou réel de cas limites.**
- `vue_carte` : `len(cles) - TICKETS_MAX` -> `% TICKETS_MAX` et `regles[0]` -> `regles[-1]` survivent : « +N tickets » et choix du premier ticket non discriminés par les données de test. **Trou réel.**
- `serveur.py` : `include_in_schema=False` -> `True` : **faible**.

**us-7-15 (`ui/chaine.py`)**
- `journal_vide=JOURNAL_ATTENTE if statut == "attente" else JOURNAL_VIDE` : tous les opérateurs, y compris `!=`, survivent : le message du journal vide (« en attente » ou « vide ») n'est pas assert. **Trou réel.**
- `enumerate(suivis, start=1)` : `start=0` ou `2` survivent : numéro d'étape affiché non vérifié. **Trou réel.**
- `if erreurs is not None:` inversé, `list(Etape).index(courante) + 1` -> `<< 1` : validation d'un lancement et rang annoncé. **Trou réel / équivalent partiel** (`+ 1` et `<< 1` coïncident pour rang 0 et 1).
- `statut == "terminee"` -> `is "terminee"` : **équivalent** (chaînes internées).
- `INTERVALLE_SONDAGE = 1.0` -> `0.0` ou `2.0` : constante de sondage non testée. **Faible.**

**us-7-16 (`ui/ecrans.py`, `outillage.py`)**
- `vue_agent` : `_vue_agent(False, message=AUCUN_PASSAGE …)` -> `True` et `TITRE_QUESTIONS_REPLI if repli` inversé survivent : le titre des questions selon le mode (repli ou réel) n'est pas assert. **Trou réel.**
- `repondre` : `passage_id != passage_id` -> `<` : garde de session périmée testée dans un seul sens. **Trou réel.**
- `outillage.py` `rendre_fiche` : `rang += 3` -> `2` ou `4`, `jeton.type == "inline" and jeton.children` -> `or`, `continue` -> `break` : le rendu Markdown de la fiche est testé sur un document trop simple. **Faible à réel** (le rendu est contrôlé par ailleurs ; certains survivants de la boucle sont équivalents).
- `ConfigDict(frozen=True)`, `@dataclass(frozen=True)` : **faible**.

Synthèse qualitative : sur 5 stories, les survivants qui sont des **trous réels** sont des assertions manquantes sur un texte ou un cas limite (formatage, pluriel, bornes, branche d'erreur) et des branches d'erreur non exercées ; aucun cas de « mock qui masque », de test qui ne vérifie qu'un `print`, ni de code mort n'a été identifié parmi les survivants examinés (je n'ai pas relu les tests un à un : ces trois catégories ne sont donc pas exclues).

## Bonus : diff-cover (couverture des lignes modifiées, seuil 80 %)
Commande : `pytest --cov=<src> --cov-report=xml` (tests de la story), puis `diff-cover coverage.xml --compare-branch=<base> --fail-under=80`. Base : le parent du premier commit de la story. Mesuré sur les mêmes copies, sources restaurées.

| Story | Lignes modifiées | Non couvertes | diff-cover | Porte 80 % | Durée | Survie mutation |
|---|---|---|---|---|---|---|
| wd-5-9 | 99 | 8 | 91 % | passe | 4 s | 38,6 % |
| wd-8-4 | 157 | 20 | 87 % | passe | 22 s | 24,6 % |
| us-7-14 | 378 | 12 | 96 % | passe | 11 s | 22,4 % |
| us-7-15 | 266 | 3 | 98 % | passe | 14 s | 14,5 % |
| us-7-16 | 400 | 9 | 97 % | passe | 15 s | 13,3 % |

- **Les 5 stories passent la porte à 80 % (87 à 98 %)** alors que la mutation y trouve 14 à 39 % de survivants : la couverture des lignes modifiées ne distingue pas les stories solides des faibles.
- Croisement (`croiser.py`) : sur 96 lignes distinctes à survivants, **69 sont des lignes couvertes** par diff-cover (test qui exécute la ligne sans la vérifier : 8/11, 10/14, 23/38, 14/16, 14/17) et 27 sont non couvertes (les deux outils concordent : par exemple les branches d'erreur de wd-5-9 et wd-8-4). Donc diff-cover trouve la **partie « branche non exécutée »** (environ 28 % des lignes à survivants), la mutation trouve en plus la partie « exécutée mais non vérifiée » (environ 72 %), qui est la plus caractéristique des tests d'agent.
- diff-cover coûte 4 à 22 s par story contre 2 à 20+ min pour la mutation.

## Limites
- 3 stories sur 5 n'ont pas été menées à terme dans les 20 minutes (141, 62 et 99 mutants en attente, soit 54 %, 16 % et 29 % des effectifs) ; leur taux de survie porte sur la partie exécutée, qui commence par les fichiers dans l'ordre de la liste (les fichiers de queue, `serveur.py`/`cli.py`/`toolrun`, sont moins ou pas testés).
- Le jugement « trou réel » est manuel et relève d'un seul relecteur : pas de revérification en aveugle.
- Les variantes de comparaison sont redondantes (55 % des survivants) : le taux de survie surévalue le nombre de trous ; la liste dédoublonnée par ligne est plus parlante.
- Les opérateurs de cosmic-ray ne mutent pas les chaînes ni les valeurs de retour : certains trous de texte (formatage) ne sont vus que par leur arithmétique. Les mutants équivalents (`==` -> `is` sur chaînes internées, `frozen`) restent en bruit non filtré.
- Mesure sur poste Windows en pause du benchmark (une suite à la fois) ; sur CI Linux avec plusieurs cœurs, les délais seraient différents. Le script `mutation_story.py` suppose Windows (`.venv\Scripts`, `taskkill`).
- Pas de rejeu : on mesure la qualité des tests de stories **déjà fusionnées** (après la revue), pas leur évolution avec le contrôle.

## Décision proposée
1. **Pas de porte de CI bloquante** sur le mutation testing : 1 story sur 5 tient sous 10 minutes, les autres 13 à 42 minutes ; un seuil de score serait en plus bruité par les mutants équivalents.
2. **Étape optionnelle du reviewer** (Opus, après le second avis), sur les fichiers **neufs ou lourdement modifiés** par la story, lignes ajoutées seulement, **budget de 10 minutes**, rapport dédoublonné par ligne (ignorer `==`/`is` sur chaînes et `frozen`). Le rapport sert de liste de pistes : « assertion manquante sur la ligne X ». Gain attendu : un trou réel par story observé sur 5 sur 5 ; coût : quelques minutes de poste, pas de tokens supplémentaires hormis la lecture du rapport.
3. **Alternative CI** : job nocturne en matrice par fichier (un fichier par job, parallèle) pour tenir sous 10 minutes par job ; rapport en commentaire de PR, non bloquant.
4. **Garder diff-cover** comme porte de CI (déjà en place dans wavedevsecops, 4 à 22 s) pour les branches non exécutées : il est rapide, il voit environ 28 % des lignes à survivants, mais il ne remplace pas la mutation.
5. Accélérations à tester avant de généraliser (non mesurées ici) : opérateurs de comparaison réduits à une variante par ligne, `pytest -x` avec le test le plus rapide en premier, exécution parallèle (distributeur HTTP de cosmic-ray ou `pytest-xdist`), exclusion des fichiers de câblage (`cli.py`, `serveur.py`).

### Commande à mettre dans le reviewer (ou en CI, non bloquant)
Une fois par copie du dépôt : `uv sync` puis `uv pip install cosmic-ray`. Puis, par story (Windows ; adapter `.venv/bin` et `kill` sous Linux) :

```
python tests-pratiques/T4/mutation_story.py --worktree . --base <commit-avant-la-story> \
  --modules <fichiers src modifiés, séparés par des virgules> \
  --tests <tests de la story, séparés par des virgules> \
  --story <id> --out <dossier du rapport> --budget-min 10 --timeout-test 60
```
La sortie `<dossier>/<id>.json` donne, par fichier : mutants générés, retirés, tués, survivants (ligne, opérateur, diff) et délai. Commande unitaire sous-jacente : `.venv\Scripts\cosmic-ray init cr.toml cr.sqlite` puis `cosmic-ray exec cr.toml cr.sqlite` puis `cr-report cr.sqlite --surviving-only --show-diff`.

## Fichiers
- `mutation_story.py` : mutation bornée (fichiers, lignes, annotations, budget), sortie JSON.
- `run_all.sh` : enchaînement des 5 stories (variables `S` = dossier des copies, `PY` = interpréteur).
- `diffcover_story.sh` : couverture différentielle d'une story.
- `croiser.py` : croisement survivants / couverture.
- `resultats-bruts/` : un JSON par story (survivants avec diff), `croisement.json`, `diffcover.log`, `run_all.log`.

## Nettoyage
Les 5 entrées `git worktree` sont retirées des dépôts. Les dossiers des trois copies usine restent dans le scratchpad (chemins trop longs pour la suppression sous Windows) ; ils sont jetables.
