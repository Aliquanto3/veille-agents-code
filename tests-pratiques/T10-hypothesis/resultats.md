# T10 : Hypothesis contre tests d'exemples pour renforcer les tests d'une story

Date : 2026-10-25. Question : quand on demande à un agent de renforcer les tests d'une story, des tests de propriétés (Hypothesis) tuent-ils plus de mutants survivants que des tests d'exemples, à coût comparable ? Configuration testée : Python, pytest, Claude Code (`claude -p`, Sonnet 5.5, effort medium).

## Résultat en bref
- **Non.** Sur 75 survivants cibles (5 stories) et 20 exécutions, le bras exemples (A) en tue **52,7 %** en cumulé (56,0 % de moyenne par exécution) et le bras propriétés (B) **44,7 %** (52,2 %). B est **8 points sous A**, pas 15 au-dessus.
- Coût : 0,335 $ par exécution pour A, 0,363 $ pour B (**×1,08**). Durée de l'agent ×1,2, temps des nouveaux tests ×2,2 (5,6 s contre 2,6 s). Aucun test faux, aucun test instable, aucun fichier source touché.
- Aucune des 5 stories ne donne +15 points à B (écart moyen de B moins A par story : +10 sur wd-5-9, -8 sur wd-8-4, -25 sur us-7-14, 0 sur us-7-15, +3 sur us-7-16).
- Critère de décision non rempli : **ne rien ajouter à `dev-story`**.
- Taux A seul : environ la moitié des survivants est tuée par la seule consigne « renforce les tests » ; 26 cibles sur 75 sont tuées par les 4 exécutions, 22 par aucune. La leçon est « demander explicitement le renforcement », pas « imposer Hypothesis », et le reste des survivants demande une information ciblée (le rapport de mutation), pas un autre outil.

## Jeu : les survivants cibles
Source : `tests-pratiques/T4/resultats-bruts/<id>.json` (cosmic-ray 8.7, lignes ajoutées par la story, tests de la story). 193 survivants sur 96 lignes. Une cible par ligne : la variante la plus parlante (inversion, constante, exception, saut), pas les variantes de comparaison redondantes. 21 lignes retirées (mutants équivalents ou artefacts). Les cibles ne figurent dans aucun prompt.

| Story | Survivants T4 | Lignes | Retraits | **Cibles** |
|---|---|---|---|---|
| wd-5-9 | 27 | 11 | 1 | **10** |
| wd-8-4 | 30 | 14 | 1 | **13** |
| us-7-14 | 72 | 38 | 12 | **26** |
| us-7-15 | 32 | 16 | 5 | **11** |
| us-7-16 | 32 | 17 | 2 | **15** |
| Total | 193 | 96 | 21 | **75** |

Retraits (liste complète dans `cibles.json`) :
- **Identité contre égalité** sur chaîne ou `StrEnum` (équivalent) : us-7-14 `carte.py:339`, us-7-15 `chaine.py:193` et `:256`, us-7-16 `ecrans.py:285`.
- **Borne atteinte par construction** : `rouge`, `rejete`, `terminee` sont les valeurs maximales de leur chaîne (`>=` équivaut à `==`), `attente` est la minimale (`<=`). Lignes : us-7-14 `detail.py:455`, `:486`, `:504` ; us-7-15 `chaine.py:254`, `:258` ; us-7-16 `ecrans.py:142`. Vérifié par calcul sur les `StrEnum` (Couleur, StatutControle).
- **Domaine supposé à deux valeurs** (non vérifié dans le code, hypothèse de lecture) : `palier` vaut 1 ou 2 (us-7-14 `detail.py:538`, `:555`, `:556`, `:607`, `:608`, `:615`), `else 3` traité comme `else 2` (`serveur.py:122`), noms de livrable `rapport_pptx` < `rapport_xlsx` (`serveur.py:145`), mode `repli` ou `reel` (us-7-15 `serveur.py:150`).
- **Tri préalable** : wd-8-4 `findings.py:364`, `line == previous + 1` devient `<=`, équivalent car `sorted(set(lines))`.
- **Artefact de signature** : wd-5-9 `loader.py:254`, `*,` devenu `/,`.
- Les mutants sans effet de comportement attendu mais tuables (`frozen=True`, `include_in_schema`, `INTERVALLE_SONDAGE`) sont **gardés** (7 cibles « faibles »).

Limite du jeu : T4 n'a pas fini 3 stories dans son budget (wd-8-4, us-7-14, us-7-16 : modules de queue non mutés). Les cibles ne couvrent que la partie exécutée.

## Protocole
- **Worktrees** : un `git worktree add --detach --no-checkout` par exécution, au dernier commit de la story (wd-5-9 `66cefe8`, wd-8-4 `e5247df`, us-7-14 `23c1fd3`, us-7-15 `c86b2f7`, us-7-16 `cf54141`), checkout creux (sans `CLAUDE.md`, `.claude`, `_bmad`) sur un disque virtuel `T:` (chemins courts, usine dépasse 260 caractères sinon). Les dépôts d'origine ne sont pas modifiés.
- **Environnements** : un venv par bras et par dépôt (`uv sync --frozen`), `PYTHONPATH` sur l'arbre de l'exécution. Seul le venv de B contient `hypothesis` 6.170.9, installé hors `pyproject`. Le venv de A n'en a pas.
- **Agent** : `claude -p` Sonnet 5.5, `--effort medium`, `--setting-sources project,local` (ni `CLAUDE.md` global, ni mémoire, ni plugin ; vérifié par une question à l'agent), outils `Read, Edit, Write, Grep, Glob, Bash`, Bash limité à `python -m pytest`, `pytest`, `git status`, `--permission-mode acceptEdits`. Même plafond pour les deux bras : 40 tours et 3 $ (jamais atteints : 27 tours au maximum). Le drapeau `--max-turns` n'apparaît pas dans `claude --help` de la version 2.1.310 ; il a été accepté, mais son effet n'est pas prouvé.
- **Prompt** : spec de la story (chemin du fichier), liste des fichiers source modifiés, liste des tests existants, consigne du protocole. B ajoute la phrase Hypothesis. Les deux ajoutent : écrire dans de nouveaux fichiers `test_renf_*.py`, ne modifier ni source ni tests existants, tout doit passer. Le texte exact est dans `agent-<id>.json` (`prompt`).
- **2 essais par bras et par story, 20 exécutions**, deux sessions `claude -p` au plus en parallèle (A et B de la même story et du même essai ensemble). Coût total des agents : **6,98 $** (A 3,35 $, B 3,63 $), sous le plafond de 15 $.
- **Évaluation** (`evaluer.py`, un seul processus de test à la fois, `.hypothesis` supprimé avant chaque lancement) :
  - (a) fichiers suivis modifiés (rejet si oui : 0 cas) ;
  - (b) suite de la story plus nouveaux tests sur code non muté : passe dans les 20 exécutions ;
  - (c) nouveaux tests seuls, deux passages : échec dans les deux = test faux, échec dans un seul = instable (retirés du rejeu) : 0 et 0 ;
  - (d) rejeu des 75 cibles contre les nouveaux tests (mutant appliqué par remplacement de ligne d'après le diff de T4, compilé avec l'interpréteur de la story, source restaurée après chaque essai) ;
  - (e) pour B, un second tirage Hypothesis sur les cibles survivantes : 0 kill supplémentaire.
- **Rejeu sur les nouveaux tests seuls**, sans les tests de la story : les cibles survivent déjà aux tests de la story (c'est leur définition dans T4), donc la réunion tue exactement ce que tuent les nouveaux tests. Tous les kills sont des tests en échec (code retour 1), aucun délai dépassé ni erreur de collecte.

## Résultats par story et par bras

| Story | Bras | Tués / cibles (essai 1, essai 2) | Taux moyen | Coût moyen ($) | Tours | Durée agent (s) | Nouveaux tests | Dont `@given` | Temps des nouveaux tests (s) | Tests faux | Instables |
|---|---|---|---|---|---|---|---|---|---|---|---|
| wd-5-9 | A | 9/10, 7/10 | 80 % | 0,23 | 12 | 68 | 44 | 0 | 2,7 | 0 | 0 |
| wd-5-9 | B | 9/10, 9/10 | 90 % | 0,24 | 16 | 95 | 46 | 4,5 | 6,7 | 0 | 0 |
| wd-8-4 | A | 10/13, 10/13 | 77 % | 0,30 | 9 | 76 | 48 | 0 | 1,3 | 0 | 0 |
| wd-8-4 | B | 9/13, 9/13 | 69 % | 0,39 | 13 | 91 | 50 | 5,0 | 3,1 | 0 | 0 |
| us-7-14 | A | 16/26, 6/26 | 42 % | 0,42 | 18 | 112 | 68 | 0 | 2,8 | 0 | 0 |
| us-7-14 | B | 6/26, 3/26 | 17 % | 0,35 | 16 | 108 | 44 | 7,5 | 5,9 | 0 | 0 |
| us-7-15 | A | 5/11, 4/11 | 41 % | 0,28 | 14 | 98 | 40 | 0 | 3,5 | 0 | 0 |
| us-7-15 | B | 6/11, 3/11 | 41 % | 0,32 | 18 | 107 | 52 | 3,0 | 6,5 | 0 | 0 |
| us-7-16 | A | 5/15, 7/15 | 40 % | 0,43 | 20 | 109 | 48 | 0 | 2,7 | 0 | 0 |
| us-7-16 | B | 7/15, 6/15 | 43 % | 0,51 | 23 | 169 | 72 | 5,5 | 5,8 | 0 | 0 |

Totaux (`agreger.py md`) :
- **A** : 79/150 cibles tuées en cumulé (52,7 %), 56,0 % de moyenne par exécution (min 23 %, max 90 %), 0,335 $ et 14,4 tours par exécution, nouveaux tests en 2,6 s.
- **B** : 67/150 (44,7 %), 52,2 % de moyenne par exécution (min 12 %, max 90 %), 0,363 $ et 17,3 tours par exécution, nouveaux tests en 5,6 s.
- Sans l'essai le plus favorable à A (us-7-14 A1, 16/26), A tombe à 63/124 (50,8 %) : B reste en dessous.
- Refus de permission (commande Bash hors liste, par exemple un script Python en heredoc) : 14 chez A, 18 chez B. Les agents ont contourné.

Distribution par cible (4 exécutions : 2 de A, 2 de B) :
- 26 cibles tuées dans les 4 exécutions (35 %), 22 dans aucune (29 %).
- Union des deux essais : A tue 47 cibles distinctes, B en tue 39 (sur 75).
- Tuées par A seul (au moins un essai de A, aucun de B) : 14 cibles, dont 3 par les deux essais. Tuées par B seul : 6 cibles, dont 1 par les deux essais.

## Exemples de survivants tués par un seul bras
- **A seul, wd-8-4 `findings.py:406` et `:409`** (`continue` remplacé par `break` quand une entrée de fichier n'est pas un dict ou n'a pas de lignes manquantes) : les deux essais A tuent ces mutants. L'essai A1 écrit un exemple qui place des entrées mal formées parmi des entrées valides (`test_entrees_de_fichier_sans_ligne_ou_mal_formees_sont_ignorees`) et vérifie que les suivantes sortent quand même. L'essai B1 (relu) teste `_ranges`, le texte de couverture et le seuil par propriétés, sans ce cas de séquence ; B2 ne tue pas non plus ces mutants.
- **A seul, us-7-14 `detail.py:639`** (`aucun_kpi=None if kpi else AUCUN_KPI`) : les deux essais A le tuent ; A1 asserte le texte exact « Aucun KPI pour cette Entité… » et le cas `None`. Aucun essai B ne le tue.
- **B seul, wd-5-9 `model.py:132`** (`!=` remplacé par `<` sur la station d'une barrière) : B1 écrit `test_station_differente_toujours_refusee`, une propriété sur une station et une autre station tirées entre 1 et 4, donc des écarts dans les deux sens. Aucun essai A ne le tue ; leurs exemples ne semblent pas couvrir les deux sens (tests A non relus un par un).
- **B seul, wd-8-4 `findings.py:392`** (`measured = total > 0` devenu `> 1`) : B2 génère `total` entre 1 et 1000 (`test_diff_cover_seuil_exact_et_troncature`), donc atteint la valeur 1. Un seul essai B sur deux, aucun essai A.
- Lecture : Hypothesis aide quand la propriété est un invariant sur un domaine de valeurs (sens des comparaisons, bornes numériques). Il aide peu pour les branches de séquence (`continue`/`break`), les messages exacts et les champs optionnels : là, l'exemple précis gagne. Les deux effets se compensent à l'échelle du jeu.

## Limites
- **Petite taille** : 5 stories, 75 cibles, 2 essais par cellule. La variance entre essais est grande (us-7-14 A : 16 puis 6 cibles). Un écart de 8 points ne se distingue pas du bruit. Un écart de +15 pour B est en revanche peu plausible : B est inférieur en cumulé, inférieur sur 2 stories, égal sur 1 et supérieur de 10 et 3 points sur 2.
- **Un seul modèle** (Sonnet 5.5, effort medium) et une seule formulation de la consigne Hypothesis. Opus, un effort plus haut ou une consigne plus directive (« écris au moins une propriété par fonction pure ») pourraient donner un autre résultat.
- **Une variante par ligne** : un test peut tuer la variante choisie et pas les autres variantes de la même ligne. Le taux de survivants tués est un taux de lignes, pas de mutants.
- **Cibles issues de T4**, donc de stories déjà revues : ce sont les trous qui ont résisté à la chaîne `dev-story`, second avis et reviewer. Les cibles faciles ne sont pas dans le jeu (la moitié des trous réels vient déjà d'assertions manquantes que la consigne seule comble). Le jeu favorise donc l'outil qui trouve des cas inattendus, et B ne gagne quand même pas.
- **Équivalents retirés à la lecture** (domaines de `palier`, de `mode`, des noms de livrable supposés) : si l'un est faux, une cible est perdue, sans effet sur le sens de l'écart.
- **Hypothesis aléatoire** : un tirage par mutant (plus un second pour les survivants). Un tirage plus long (`max_examples` élevé) coûterait du temps de test, pas des tokens ; non mesuré.
- **Prompt sans le rapport de mutation** : l'agent ne sait pas où sont les trous. Les 22 cibles jamais tuées montrent la limite de la consigne générique. Donner la liste des survivants à l'agent n'a pas été testé ici (autre expérience).
- Agents lancés sans `CLAUDE.md` du projet ni conventions du dépôt : les tests produits ne suivent pas forcément le style maison.
- Mesure sur un poste Windows, une suite à la fois ; les deux sessions parallèles de la phase agent ont pu lancer deux `pytest` en même temps (courts).

## Décision
Critère : B tue au moins 15 points de survivants de plus que A, à coût au plus 1,5 fois, sans test instable.
- Écart mesuré : **-8 points** (cumul) ou **-4 points** (moyenne par exécution). Coût ×1,08, aucun test instable.
- **Le critère n'est pas rempli : ne rien ajouter à `dev-story` d'agent-cost-kit.**
- Taux A seul : 52,7 %. Les deux bras tuent environ la moitié des survivants et aucun n'en tue « la plupart » : la consigne explicite suffit pour la première moitié, et personne ne tue 29 % des cibles.
- Suite possible, hors de cette décision : mesurer si fournir au reviewer ou à un second passage de `dev-story` la liste dédoublonnée des survivants (rapport de T4) fait mieux que la consigne générique, avec ou sans Hypothesis. C'est l'expérience qui répond au reste des 22 cibles jamais tuées.

## Fichiers
- `cibles.py`, `cibles.json` : construction des cibles et retraits (motifs).
- `jeu.py` : stories, chemins, environnement ; `preparer.py` : worktree creux jetable ; `dryrun.py` : contrôle que les 75 mutants s'appliquent et se compilent.
- `lancer_agent.py`, `lot_agents.sh` : exécution des agents ; `evaluer.py`, `lot_eval.sh`, `mutation.py` : évaluation et rejeu ; `agreger.py` : tableaux.
- `resultats-bruts/agent-<story>-<bras><essai>.json` : sortie JSON de `claude -p` (coût, tours, durée, prompt, résultat) ; `eval-<…>.json` : validité, stabilité, rejeu par cible ; `tests-produits/` : tests écrits par les agents ; `resume.json`, `lot_*.log`, `log-*.txt`.
- Les dossiers jetables (venvs sous `T:\v` du scratchpad) n'ont pas été supprimés ; les 10 worktrees d'exécution, 2 de base et 5 de contrôle sont retirés et `git worktree prune` est passé dans les deux dépôts.
