# T10b : mutation guidée, montrer les survivants à l'agent

Date : 2026-10-25. Question : si l'on montre à un agent les mutants survivants d'une story (fichier, ligne, diff d'une ligne) et qu'on lui demande d'écrire les tests qui les tuent, combien en tue-t-il, à quel coût, et à quel délai ? Suite de T10 (`resultats.md`) : mêmes 75 cibles, mêmes 5 stories, même modèle (Sonnet 5.5, effort medium), même plafond (3 $, 40 tours), mêmes outils permis. Seul le prompt change (bras C).

## Résultat en bref
- **Oui, c'est efficace.** Le bras C tue **134 cibles sur 150** (10 exécutions), soit **89,3 %**. Les 16 qui survivent sont 8 cibles, chacune sur les deux essais, et **les 8 sont des mutants équivalents** (vérifiés un par un). Sur les **cibles non équivalentes : 100 %** (134/134), dans les 10 exécutions.
- Bras A de T10 : 52,7 % (59,0 % hors équivalents). Bras B : 44,7 % (50,0 %). **C gagne 41 points sur A** (37 points sur les 150 cibles brutes).
- **Coût : 0,22 $ par exécution** (0,15 à 0,34 $), contre 0,335 $ pour A et 0,363 $ pour B. C coûte moins cher que A : moins de tours (11,2 contre 14,4), moins de tests (15 contre 50). Durée de l'agent : 73 s (A 93 s, B 114 s).
- Aucun test faux, aucun test instable, aucun fichier source modifié. Les 134 kills sont des tests en échec (code 1).
- **Délai de l'étape : 3 à 13 minutes par story, environ 12 minutes pour 4 stories sur 5.** La mutation (bornée à 10 min) fait 80 à 95 % du temps, l'agent 1 à 2 minutes.
- **Critère rempli** (au moins 80 % des non équivalentes, au moins 20 points de plus que A, moins de 1 $ par story). Recommandation : ajouter à l'étape mutation du reviewer d'agent-cost-kit « montrer les survivants dédoublonnés à l'agent et lui faire écrire les tests ». Voir la décision.

## Protocole
- **Outillage de T10 réutilisé** : `jeu.py`, `preparer.py`, `lancer_agent.py`, `evaluer.py`, `mutation.py`, `cibles.json` (75 cibles, une variante par ligne). Trois ajouts sans effet sur A et B : variables d'environnement `T10_RACINE`, `T10_BRUTS` et `T10_CIBLES` (jeu, lancer_agent, evaluer), et le bras C dans `lancer_agent.py`. Le prompt du bras A reconstruit est identique à celui de T10, sauf pour la partie propre à C.
- **Prompt C** = prompt A (spec, fichiers source, tests existants, consigne « renforce les tests ») plus la liste `M1…Mn` (fichier:ligne, fonction, diff d'une ligne `-` / `+`), plus la consigne demandée (mot pour mot) et, à la fin, « pour chaque mutation Mn, le test qui la tue, ou équivalente avec la raison en une phrase ». Une ligne d'aide explique `CosmicRayTestingException` (classe d'exception jamais levée). Le texte exact est dans `agent-<story>-C<essai>.json` (`prompt`).
- **Environnement** : worktrees détachés jetables, checkout creux, dans `…\scratchpad\t10b\s\` (noms courts, pas de `subst`) ; un venv par dépôt (`uv sync --frozen`, sans Hypothesis ; `--no-install-project` pour wavedevsecops, dont le README est hors checkout creux). Ni Ollama ni GPU.
- **Charge** : 2 sessions `claude -p` au plus (deux stories en parallèle) ; évaluation avec un seul processus de test à la fois, `.hypothesis` supprimé avant chaque lancement.
- **Évaluation** : celle de T10 (`evaluer.py`) : fichiers suivis intacts, suite de la story plus nouveaux tests sur le code non muté, deux passages des nouveaux tests seuls (faux, instables), rejeu des 75 cibles contre les nouveaux tests seuls.
- **2 essais par story, 10 exécutions.** Deux mesures en plus, hors protocole : mutants hors liste (généralisation) et lignes retirées (équivalents bruts).
- **Premier lot écarté** : le premier lot de 10 exécutions a utilisé le chemin court Windows `UTILIS~1`. Claude Code a refusé les écritures de fichiers par cet alias (hook de sécurité), et 3 exécutions n'ont écrit aucun test. Lot écarté (2,74 $, conservé dans `resultats-bruts/T10b/lot1-chemin-court/`), relancé en entier avec le chemin long. Les chiffres ci-dessous viennent du second lot.

## Résultats par story

Taux sur les cibles **non équivalentes** (moyenne des 2 essais ; équivalents : voir plus bas). A et B : données de T10, recalculées sur le même dénominateur (A et B n'ont jamais tué un des 8 équivalents).

| Story | Cibles (non éq.) | A | B | **C** | C : tués (essai 1, 2) | C : coût ($) | C : tours | C : agent (s) | Faux / instables |
|---|---|---|---|---|---|---|---|---|---|
| wd-5-9 | 10 (10) | 80 % | 90 % | **100 %** | 10, 10 | 0,23 | 11 | 72 | 0 / 0 |
| wd-8-4 | 13 (12) | 83 % | 75 % | **100 %** | 12, 12 | 0,17 | 10 | 53 | 0 / 0 |
| us-7-14 | 26 (24) | 46 % | 19 % | **100 %** | 24, 24 | 0,30 | 12 | 75 | 0 / 0 |
| us-7-15 | 11 (11) | 41 % | 41 % | **100 %** | 11, 11 | 0,20 | 8 | 59 | 0 / 0 |
| us-7-16 | 15 (10) | 60 % | 65 % | **100 %** | 10, 10 | 0,22 | 15 | 97 | 0 / 0 |
| **Total** | 75 (67) | 59,0 % | 50,0 % | **100 %** | 134/134 | 0,221 | 11,2 | 71 | 0 / 0 |

Sur les 150 cibles brutes : A 79 (52,7 %), B 67 (44,7 %), C 134 (89,3 %). Coût moyen par exécution : A 0,335 $, B 0,363 $, C 0,221 $. Tests écrits par exécution : A 50, B 53, C 15. Temps des nouveaux tests : 2,5 s (A 2,6 s, B 5,6 s). Coût total du lot C : 2,21 $.

Union des essais (cibles distinctes tuées sur 75) : A 47, B 39, **C 67**. 14 cibles sont tuées par C seul. Jamais tuées par A, B ni C : 8 (les équivalents).

Les deux essais de C tuent exactement les mêmes cibles dans chaque story. La variance entre essais, forte en A (us-7-14 : 16 puis 6), est nulle ici.

## Équivalents : déclarés et vérifiés
Les agents ont déclaré 8 mutations équivalentes (les mêmes dans les deux essais de la story), sans écrire de test. Ce sont exactement les 8 cibles qui survivent. Je les ai vérifiées toutes (8 sur 8, pas un échantillon).

| Cible | Mutation | Verdict | Vérification |
|---|---|---|---|
| us-7-14 `detail.py:492` | `lignes[0]` devient `lignes[-1]` | équivalent | Code lu : `_lignes_risques` construit toutes les lignes avec les mêmes clés dans le même ordre. |
| us-7-14 `detail.py:517` | `[0]` devient `[-1]` | équivalent | La liste vient de `vues_tickets([morceau], …)`, une compréhension sur un seul élément. |
| us-7-16 `outillage.py:55` | `Token("html_inline", "", 1)` | équivalent | Le rendu des jetons `html_inline` ne lit pas `nesting`. |
| us-7-16 `outillage.py:72` | `Token("text", "", -1)` | équivalent | Idem pour `text`. |
| us-7-16 `outillage.py:87` | `rang < len(jetons)` devient `!=` | équivalent | Un titre `h1` saute toujours exactement 3 jetons : `rang` atteint `len` sans le dépasser. |
| us-7-16 `outillage.py:89` | `jeton.type == "heading_open"` devient `<=` | équivalent | Seuls `heading_open` et `heading_close` portent le tag `h1`, et `heading_close` est déjà sauté par le `+= 3`. |
| us-7-16 `outillage.py:92` | `and` devient `or` | équivalent | Seuls les jetons `inline` ont des enfants ; `_pastilles([])` renvoie `[]`. |
| wd-8-4 `replace_in_file.py:27` | retrait de `@classmethod` | équivalent | Pydantic v2 enveloppe lui-même en méthode de classe un validateur dont le premier paramètre est `cls`. |

Contrôle empirique (`sonde_equiv.py`) pour les 6 dernières lignes : pour chaque mutant, signature des sorties comparée à celle du code d'origine. us-7-16 : `rendre_fiche` sur 1 881 documents Markdown (fragments avec titres, code en ligne, tableaux, pastilles, titres vides ; graine fixe). wd-8-4 : validation de `Args` sur 9 cas. Résultat : **sorties identiques** pour les 6. Témoins : 4 mutants non équivalents d'`outillage.py` (lignes 64, 66, 86, 90) et le retrait du validateur `old` donnent bien des sorties **différentes**. La sonde sait donc voir une différence.

Aucune fausse déclaration d'équivalence (0 sur 16 déclarations ici, 0 sur 19 dans l'extension) et aucune mutation non équivalente laissée sans test.

### Extension : liste brute, sans le tri manuel de T10
Les 75 cibles de T10 sortent d'un tri manuel (21 lignes retirées : équivalents supposés et artefacts). Un vrai rapport ne serait pas trié. Un essai de plus (C4, hors protocole) sur les deux stories qui ont le plus de lignes retirées, avec la liste **brute** (`resultats-bruts/T10b/ext/`) :

| Story | Lignes montrées | Tuées | Déclarées équivalentes | Survivantes | Coût ($) |
|---|---|---|---|---|---|
| us-7-14 | 38 (26 + 12 retirées) | 24 | 14 (12 retirées + 2) | 14 | 0,34 |
| us-7-15 | 16 (11 + 5 retirées) | 11 | 5 (les 5 retirées) | 5 | 0,25 |

Les 17 lignes retirées sont toutes déclarées équivalentes par l'agent, aucun test n'est écrit pour elles, et aucune n'est tuée au rejeu. Le tri manuel de T10 n'est donc pas nécessaire : l'agent trie. La borne `palier` repose sur `Palier = Literal[1, 2]` (`detail.py:94` et `ports/consultation.py:21`), que j'ai vérifié dans le code ; l'hypothèse de lecture de T10 est confirmée.

## Généralisation : mutants non montrés
Un test écrit pour tuer un mutant précis peut ne tuer que celui-là. Pour le mesurer, rejeu des **74 mutants non montrés** (autres variantes de T4 sur les mêmes lignes, sans les équivalents identité/égalité) contre les tests de A et de C (`holdout.py`, `evaluer_holdout.py`, mêmes tests pour les deux essais).

| Story | Mutants hors liste | A (2 essais cumulés) | C (2 essais cumulés) |
|---|---|---|---|
| wd-5-9 | 14 | 25/28 | 24/28 |
| wd-8-4 | 13 | 18/26 | 17/26 |
| us-7-14 | 26 | 20/52 | 39/52 |
| us-7-15 | 10 | 15/20 | 17/20 |
| us-7-16 | 11 | 6/22 | 8/22 |
| **Total** | 74 | **84/148 (56,8 %)** | **105/148 (70,9 %)** |

C tue 14 points de plus que A sur des mutants qu'il n'a pas vus, 6 mutants distincts que A ne tue pas, et aucun que A tue et que C rate. L'écart est moindre que sur les mutants montrés (41 points), et c'est normal. Les tests de C ne sont donc pas calqués sur les diffs montrés. 19 de ces 74 mutants ne sont tués ni par A ni par C : le jeu contient des équivalents non triés (variantes `<=` sur des énumérations par exemple), je ne les ai pas vérifiés un par un.

## Coût et délai de l'étape
Coût de l'agent : 0,22 $ par story en moyenne (maximum 0,34 $), soit 2,21 $ pour les 10 exécutions. L'étape de mutation ne coûte pas de jeton.

Délai réaliste par story : mutation T4 bornée à 10 min, plus l'agent C (temps mur mesuré, 2 sessions en parallèle), plus le rejeu des survivants contre les nouveaux tests (somme des temps mesurés sur les cibles, pour que le reviewer sache lesquels sont tués).

| Story | Mutation T4 | Agent C | Rejeu des survivants | **Étape** |
|---|---|---|---|---|
| wd-5-9 | 1,7 min (complète) | 1,2 min | 0,3 min | **3,2 min** |
| wd-8-4 | 10 min (T4 : plein estimé 42 min) | 0,9 min | 0,25 min | **11,2 min** |
| us-7-14 | 10 min (plein 23,5 min) | 1,3 min | 1,3 min | **12,6 min** |
| us-7-15 | 10 min (plein 13,5 min) | 1,0 min | 0,75 min | **11,8 min** |
| us-7-16 | 10 min (plein 27,7 min) | 1,65 min | 0,65 min | **12,3 min** |

- La mutation domine. Pour 4 stories sur 5, la borne de 10 min coupe la liste : à 20 min, T4 avait encore 54 %, 16 % et 29 % des mutants en attente sur wd-8-4, us-7-14 et us-7-16. L'agent ne voit alors qu'une partie des survivants.
- Les durées de l'agent vont de 54 à 121 s. Le rejeu est facultatif, mais il coûte moins de 90 s par story.
- La phase agent peut commencer dès que la mutation rend sa liste, donc après la porte de 10 min ; on ne gagne rien à la paralléliser avec la revue d'Opus (celle-ci a besoin du résultat).

## Limites
- **Taille** : 5 stories, 75 cibles, 2 essais. Les deux essais de C donnent les mêmes résultats, ce qui est encourageant, mais cinq stories d'un même auteur et d'un même style ne couvrent pas tous les projets.
- **Mesure sur les mutants montrés** : l'agent voit les mutants qu'on rejoue, donc le taux (100 %) est optimiste par construction. La mesure hors liste (70,9 % contre 56,8 %) est la plus honnête sur la qualité des tests. Ce n'est pas un taux de survie globale de la story.
- **Les agents n'ont pas exécuté les mutants** : seuls `python -m pytest` et `git status` étaient permis (comme en A et B). Les liens test vers mutation viennent de leur lecture du code. Les 134 prédictions se sont vérifiées au rejeu.
- **Une variante par ligne** : comme en T10, le taux est un taux de lignes. La mesure hors liste en donne une idée.
- **Cibles issues de stories déjà revues**, et liste de T4 coupée par le budget (modules de queue non mutés pour 3 stories).
- **Tests changeurs de comportement** : C écrit aussi des tests pour les 7 cibles « faibles » de T10 (`frozen`, `include_in_schema`, `INTERVALLE_SONDAGE == 1.0`, valeurs par défaut de paramètre). Ils tuent bien le mutant, mais ils figent des détails d'implémentation. Je n'ai pas relu tous les tests ; aucun ne lit le code source (`getsource`, `read_text`). Le reviewer doit trancher sur ces tests cosmétiques.
- **Tests écrits par un agent seul, sans les conventions du dépôt** : ils réutilisent les aides des tests existants, mais n'ont pas été relus au style maison.
- **Alias de chemin Windows** : l'alias court `UTILIS~1` fait refuser les écritures de fichier par Claude Code. À éviter pour tout chemin donné à un agent (premier lot perdu).
- **Un seul modèle** (Sonnet 5.5, effort medium), une seule formulation de la consigne.
- Mesure sur un poste Windows ; les deux sessions parallèles de la phase agent ont pu lancer deux `pytest` en même temps (courts).

## Décision
Critère de T10b : C tue au moins 80 % des cibles non équivalentes, au moins 20 points de plus que A, pour moins de 1 $ par story.

| Condition | Seuil | Mesure | Verdict |
|---|---|---|---|
| Part des non équivalentes tuées | au moins 80 % | 100 % (134/134), 89 % sur les 150 brutes | rempli |
| Écart avec A | au moins 20 points | +41 points (+37 sur les brutes) | rempli |
| Coût par story | moins de 1 $ | 0,22 $ en moyenne, 0,34 $ au maximum | rempli |

**Recommandation : ajouter à l'étape mutation du reviewer d'agent-cost-kit « montrer les survivants dédoublonnés à l'agent et lui faire écrire les tests ».** Forme proposée, à valider par Anaël (je n'ai rien modifié dans agent-cost-kit) :
1. Mutation bornée aux lignes de la story (T4, 10 min), rapport dédoublonné **par ligne** : une variante par ligne (inversion, constante, exception, saut de préférence à une variante de comparaison). Le tri manuel des équivalents n'est pas nécessaire (extension).
2. Un agent de la famille `dev-story` (Sonnet, effort medium, 3 $ de plafond) reçoit la liste en diffs d'une ligne avec la consigne du bras C, écrit les tests dans de nouveaux fichiers, déclare les équivalentes sans test.
3. Rejeu des survivants contre les nouveaux tests (moins de 90 s) et rapport au reviewer : tués, équivalents déclarés (à relire ; 35 déclarations sur 35 justes ici), survivants restants.
4. Le reviewer (Opus) ne relit que les tests cosmétiques et les équivalents déclarés.
- Hors sujet de cette décision : la mutation reste optionnelle et bornée (pas de porte de CI), comme T4 l'a décidé.
- Hypothesis (T10) reste écarté.

## Fichiers
- Outillage : `lancer_agent.py` (bras C), `lot_agents_c.sh`, `lot_eval_c.sh`, `evaluer.py` (inchangé hors `T10_CIBLES`), `agreger_c.py` (tableaux ; `resultats-bruts/T10b/equivalents.json` pour le dénominateur hors équivalents), `sonde_equiv.py` (vérification des équivalents), `holdout.py`, `evaluer_holdout.py`, `lot_holdout.sh`, `cibles_etendues.py` (extension).
- Données brutes sous `resultats-bruts/T10b/` : `agent-<story>-C<essai>.json` (prompt, coût, tours, durée, résultat), `eval-<story>-C<essai>.json` (validité, stabilité, rejeu des 75 cibles), `finaux-agents-C.txt` (rapports finaux des agents), `holdout*.json`, `sonde-*.json`, `tests-produits/` (tests écrits), `ext/` (extension), `lot1-chemin-court/` (lot écarté), `resume-c.json`.
- Les chemins personnels des fichiers bruts sont remplacés par `<user>` ; aucune clé ni donnée privée.
- Nettoyage : tous les worktrees créés (2 lots d'exécution, 5 de contrôle, 2 de l'extension) retirés (`git worktree remove`, `git worktree prune` dans les deux dépôts), venvs et dossier `t10b` du scratchpad supprimés (`robocopy /MIR` d'un dossier vide). Les dépôts d'origine ne sont pas modifiés.
- Budget : 5,53 $ d'équivalent API (lot écarté 2,74 $, lot retenu 2,21 $, extension 0,58 $), sous le plafond de 8 $.
