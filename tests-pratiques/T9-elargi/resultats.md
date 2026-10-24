# T9 élargi : la spec d'une story prédit-elle dérapage, coût ou défaut de revue ? (226 stories, 7 dépôts publics)

Test pratique de la veille sur les agents de code (2026-10-24), suite de T9 (`../T9/resultats.md`, 125 stories et 9 dérapages : aucun bras ne prédisait, mais le test manquait de puissance). Cette version prend **toutes les données disponibles** et la chaîne est **relançable** quand d'autres transcriptions arriveront. Tous les chiffres sont des agrégats ; aucun texte de spec n'est recopié ici ni écrit dans le dépôt (les specs restent dans le dossier de travail `--travail`, hors dépôt).

**Conclusion courte.** Aucun bras (heuristique, Jev, gpt-6-luna) ne satisfait le critère (AUC > 0,7 et +0,05 sur l'heuristique), pour aucune des trois étiquettes ni des deux exploratoires. Le passage à 226 stories et 15 dérapages (contre 125 et 9) resserre l'intervalle sans changer la conclusion : les modèles retrouvent à peu près l'AUC de la **longueur de la spec** (0,65 sur le coût, 0,61 sur le dérapage), écart à l'heuristique de −0,08 à +0,03 sur le dérapage et le coût. Le test reste sous-puissant sur le dérapage (15 positifs, il en faut 32 pour détecter 0,65), mais il est assez puissant sur le coût (46 positifs, puissance 88 % pour 0,65) : un signal de 0,65 existe, c'est la longueur. Décision proposée : ne rien brancher dans `agent-cost-kit`.

## 1. Ce qui change par rapport à T9

| | T9 | T9 élargi |
|---|---|---|
| Dépôts | 3 (wavedevsecops, wavelocalai, usine-migration-jira-demo) | 5 avec stories : + wavelibrarian, service-public-slm-fine-tuning (wavestack et agent-cost-kit n'ont aucune story numérotée) |
| Transcriptions | 45 derniers jours | toutes, sans limite de date, un seul processus ; paramètre `--transcriptions` répétable |
| Stories étiquetées | 125 | **226** |
| Dérapages | 9 | **15** |
| Étiquettes | dérapage ; défaut de revue (+ 2 exploratoires) | dérapage ; **coût au-dessus du 80e centile du dépôt** ; défaut de revue (+ 2 exploratoires) |
| Bras | heuristique, Jev (2 versions), gpt-6-luna, mimo | heuristique, Jev (2 versions), gpt-6-luna (2 exécutions) ; mimo retiré (hors consigne, très bruité en T9) |
| Spec | `epics.md`, 60 stories à version strictement antérieure | `epics.md` au dernier commit strictement antérieur au premier appel de l'agent (horodatage exact) : **226 sur 226** |

Correction d'un point de T9 : T9 classait `wavelibrarian` et `service-public-slm-fine-tuning` comme privés ; `gh repo view` (2026-10-24) les donne publics, comme les cinq autres. Ils sont inclus, ce qui explique l'essentiel des 101 stories supplémentaires.

## 2. Données

**Extraction.** 354 agents `dev-story` lus dans `~/.claude/projects` (dossiers `scratchpad` des tests de la veille exclus), 333 retenus (21 hors liste : rejeux `usine-lanes-t1-*`, `slm-quality-bench`, `Aliquanto3`, `veille-agents-code`, dossiers non rattachés à un dépôt de la liste), dont 257 avec un numéro de story lu dans la description. Dépôt déterminé par le `cwd` de la transcription (élément du chemin qui porte le nom d'un dépôt de la liste, ce qui couvre sous-dossiers et worktrees `.claude`), donc indépendant du nom d'utilisateur ou du PC d'origine. Dédoublonnage par `message.id` (une réponse recopiée par une reprise n'est comptée qu'une fois) : vérifié en passant deux fois la même racine, aucun doublon (333 agents retenus dans les deux cas). Les agents dont le dernier appel date de moins de 30 minutes sont marqués « en cours » et leur story écartée (aucune story concernée ici).

**Stories.** 230 stories distinctes (dépôt, numéro), 4 écartées faute de section dans `epics.md` avant le développement (wavelocalai), **226 étiquetées**. Répartition et seuils de dépôt :

| Dépôt | Stories | Médiane d'appels | 80e centile du coût | Dérapages | Coût élevé |
|---|---|---|---|---|---|
| wavelibrarian | 65 | 26 | 1,03 $ | 5 | 13 |
| wavedevsecops | 64 | 52,5 | 4,22 $ | 4 | 13 |
| wavelocalai | 54 | 87 | 4,74 $ | 1 | 11 |
| service-public-slm-fine-tuning | 31 | 33 | 1,68 $ | 1 | 6 |
| usine-migration-jira-demo | 12 | 34,5 | 2,81 $ | 4 | 3 |

Les développements datent du 2026-10-13 au 2026-10-19 : le type d'agent `dev-story` n'existe qu'à partir de l'installation du kit. **Les stories d'avant (service-public-slm-fine-tuning : 107 agents, usine-migration-jira-demo : 214 agents, au numéro de story lisible) passaient par des agents `general-purpose`**, qui mélangent développement, revue et recherche : c'est une piste de données supplémentaires, non testée ici (`extraire_agents.py --types dev-story general-purpose` la rend possible, avec le tri à faire). Coût équivalent API des 226 stories : 469 $ (médiane 1,49 $ par story, de 0,11 à 10,37 $). 205 stories ont été développées par Sonnet seul, les autres mélangent Opus ou Haiku (le coût mélange alors les tarifs ; voir sensibilité).

**Étiquettes** (seuils par dépôt, calculés sur toutes les stories numérotées du dépôt) :
- `derapage` : somme des appels propres des agents `dev-story` de la story (reprises regroupées) supérieure à 2 fois la médiane des sommes du dépôt : **15 positives sur 226 (6,6 %)** ;
- `cout80` : coût de la story supérieur (strictement) au 80e centile de son dépôt : **46 sur 226 (20,4 %)** ; c'est le coût des agents `dev-story`, pas celui de la revue ;
- `defaut_revue` : la revue consigne au moins un constat de sévérité medium ou high retenu et traité (ni rejeté, ni reporté ; le critère « corrigé » est lu ainsi car certains formats de revue n'écrivent pas le mot), ou, pour l'usine, un triage `patch`, `defer`, `bad_spec`, `intent_gap` ou `decision` de sévérité medium ou high : **174 sur 225 stories lisibles (77 %)** ;
- exploratoires : `derapage_par_agent` (le plus long agent dépasse 2 fois la médiane par agent du dépôt, critère de T1 : 15) et `haut20` (appels au-dessus du 80e centile du dépôt : 43).

**Spec et anti-fuite.** Section « Story X.Y » de `epics.md` au dernier commit antérieur au premier appel de l'agent : 226 stories sur 226 (aucun repli sur le fichier de story ni sur la version « du jour »), aucune ligne post-développement à retirer. Longueur médiane 1 810 caractères (de 541 à 3 979), 4 critères (de 0 à 12), 3 fichiers cités (de 0 à 18). Les sections d'`epics.md` n'ont ni cases à cocher ni liste de tâches : la mesure « nombre de tâches » du cahier des charges est donc remplacée par le nombre d'éléments de liste (`n_puces`, médiane 0), presque constante ; l'heuristique repose en pratique sur la longueur, les critères et les fichiers cités.

## 3. Protocole

Même entrée (la section de spec) et mêmes trois questions fermées pour tous les bras ; le prompt donne la définition de chaque étiquette et les taux de base globaux (1 dérapage sur 15, 1 coût élevé sur 5, 3 défauts de revue sur 4), qui sont des priors et non des informations sur la story.

1. **Heuristique sans modèle** : logarithme de la longueur, nombre de critères, d'éléments de liste, de fichiers cités, centrés et réduits par dépôt (sans étiquette). Deux versions : régression logistique (L2, C = 1) en validation croisée stratifiée 5 plis répétée 10 fois ; seuil sur la seule longueur (aucun apprentissage). La meilleure des deux sert de référence (comparaison prudente) : c'est la longueur pour les cinq étiquettes (la régression est sous 0,5 sur le dérapage : surapprentissage).
2. **Jev en mode décision** (`POST /api/alpha/decisions` d'OpenRouter, trois questions `noul` dans une requête) : `~typesafe/jev-latest` (principal) et `typesafe/jev-1.13`. Une exécution chacun (déterministe).
3. **`openai/gpt-6-luna`** via `chat/completions`, sortie structurée JSON, effort de raisonnement bas, deux exécutions (la première est la mesure principale).

Mesures : AUC avec IC à 95 % (bootstrap stratifié, 3 000 tirages) ; précision et rappel avec au plus 20 % d'alertes (ex æquo non séparés), global et par dépôt ; AUC intra-dépôt (scores ramenés à leur rang dans le dépôt) ; AUC par dépôt ; écart d'AUC à la référence et son IC (bootstrap apparié). Critère inchangé : AUC > 0,7 et au moins 0,05 au-dessus de la référence. La clé OpenRouter est lue dans l'environnement ou `HKCU\Environment`, jamais affichée ni écrite.

## 4. Résultats

### Synthèse : AUC et écart à la longueur de la spec (IC à 95 %)

| Bras | Dérapage (15 pos.) | Coût au-dessus du 80e centile (46 pos.) | Défaut de revue (174 / 225) |
|---|---|---|---|
| Heuristique : longueur (référence) | 0,606 [0,45 ; 0,75] | 0,650 [0,56 ; 0,74] | 0,519 [0,42 ; 0,62] |
| Heuristique : régression logistique | 0,348 (CV) | 0,614 | 0,469 |
| Jev latest | 0,613 [0,50 ; 0,72], écart +0,01 [−0,16 ; +0,18] | 0,649 [0,56 ; 0,73], écart 0,00 [−0,09 ; +0,09] | 0,508 [0,41 ; 0,60], écart −0,01 |
| Jev 1,13 | 0,633 [0,51 ; 0,75], écart +0,03 [−0,14 ; +0,21] | 0,654 [0,57 ; 0,74], écart 0,00 [−0,09 ; +0,11] | 0,551 [0,46 ; 0,64], écart +0,03 |
| gpt-6-luna, exéc. 1 / 2 / moyenne | 0,522 / 0,545 / 0,544 | 0,620 / 0,628 / 0,637 | 0,599 / 0,522 / 0,571 |
| Écart de luna à la référence (exéc. 1) | −0,08 [−0,26 ; +0,11] | −0,03 [−0,14 ; +0,08] | +0,08 [−0,00 ; +0,16] |
| Critère satisfait | non (aucun bras) | non (aucun bras) | non (aucun bras) |

Étiquettes exploratoires (AUC, première exécution) : `haut20` longueur 0,662, Jev latest 0,667, **Jev 1,13 0,688 [0,61 ; 0,77]** (écart +0,03 [−0,08 ; +0,14]), luna 0,658 ; `derapage_par_agent` longueur 0,657, Jev latest 0,622, Jev 1,13 0,664, luna 0,594. Le meilleur chiffre du test (0,688) reste sous 0,7 et n'est qu'un maximum parmi 25 comparaisons (5 étiquettes, 5 variantes de modèle) : un franchissement isolé n'aurait pas valu preuve.

### Précision et rappel à 20 % d'alertes (global)

| Étiquette | Tirage au hasard (précision) | Longueur | Jev latest | Jev 1,13 | gpt-6-luna (exéc. 1 / 2) |
|---|---|---|---|---|---|
| Dérapage (taux 6,6 %) | 6,6 % ; 3 vrais positifs sur 45 alertes | 6 sur 45 (13 %, rappel 40 %) | 2 sur 43 | 3 sur 40 | 2 sur 41 / 1 sur 33 |
| Coût élevé (taux 20 %) | 20 % ; 9 sur 45 | 17 sur 45 (38 %, rappel 37 %) | 13 sur 45 (29 %) | 14 sur 44 (32 %) | 9 sur 30 (30 %) / 9 sur 30 |
| Défaut de revue (taux 77 %) | 77 % | 30 sur 45 (67 %) | 27 sur 36 (75 %) | 31 sur 39 (80 %) | 22 sur 24 (92 %) / 20 sur 27 (74 %) |

Sur le dérapage, seule la longueur dépasse nettement le hasard (6 vrais positifs contre 3 attendus) ; aucun bras ne fait mieux que la longueur. Sur le coût, longueur et modèles font 1,5 à 1,9 fois mieux que le hasard (précision de 29 à 38 % pour 20 % de base), sans que les modèles améliorent la longueur. Sur le défaut de revue, toutes les précisions sont dans la plage du taux de base (77 %) ; les 92 % de luna à la première exécution tombent à 74 % à la seconde.

### Par dépôt (tableaux complets en annexe)

- **AUC du dérapage par dépôt** : seulement trois dépôts ont au moins 2 positifs (usine 4, wavedevsecops 4, wavelibrarian 5) : longueur 0,78 / 0,52 / 0,62, Jev latest 0,52 / 0,57 / 0,67, luna 0,72 / 0,52 / 0,52. Sur 4 ou 5 positifs, ces chiffres sont du bruit (IC de plusieurs dixièmes).
- **Coût** : longueur 0,91 (service-public, 6 positifs), 0,85 (usine, 3), 0,64 (wavedevsecops, 13), 0,55 (wavelibrarian, 13), 0,57 (wavelocalai, 11) ; Jev latest 0,83, 0,56, 0,60, 0,68, 0,63. Le signal de longueur est fort dans les petits dépôts, faible dans les gros ; aucun bras n'est constant d'un dépôt à l'autre.
- **Défaut de revue** : l'AUC de la longueur change de sens selon le dépôt (0,83 ; 0,77 ; 0,41 ; 0,72 ; 0,29) : pas de signal transférable.

### Signal continu et diagnostics

- Les scores des modèles suivent la longueur de la spec : corrélation de rang du score de dérapage avec la longueur 0,49 à 0,54 (Jev), 0,51 à 0,59 (luna). Corrélation du score de coût avec le coût réel (intra-dépôt) : longueur 0,40, luna 0,33 à 0,36, Jev 0,30 ; avec le nombre d'appels pour le dérapage (intra-dépôt) : longueur 0,35, luna 0,29 à 0,31, Jev 0,18 à 0,20. Les modèles ne voient pas plus que l'heuristique.
- Bruit : deux exécutions de gpt-6-luna ont une corrélation de rang de 0,77 (dérapage), 0,78 (coût) et 0,65 (défaut de revue), d'où l'écart d'AUC de 0,599 à 0,522 sur le défaut de revue. Jev est déterministe.
- Calibration : probabilité moyenne de dérapage de 0,28 (Jev latest), 0,34 (Jev 1,13) et 0,27 (luna) pour 6,6 % observé ; de coût élevé 0,45 à 0,51 pour 20 % ; de défaut de revue 0,68 à 0,80 pour 77 %. Seuls les rangs sont utilisables.
- Sensibilité au mélange de modèles : sur les 205 stories développées par Sonnet seul (11 dérapages, 34 coûts élevés), AUC du dérapage : longueur 0,564, Jev latest 0,607, luna 0,525 ; du coût : 0,623, 0,677, 0,643. L'écart de Jev à la longueur pour le coût passe de 0,00 à +0,05, dans le bruit (non testé par bootstrap, 34 positifs) ; à confirmer si l'écart tient avec plus de données.
- Spec : toutes les specs viennent de la version antérieure au développement : pas de sensibilité à étudier de ce côté.

### Coût et latence

| Bras | Coût par story et par exécution | Coût d'une exécution (226 stories) | Latence médiane / p90 |
|---|---|---|---|
| Jev latest ou 1,13 (3 questions) | 0,000075 $ | 0,017 $ | 0,25 s / 0,29 s |
| gpt-6-luna (effort bas) | 0,00018 $ | 0,04 $ | 3,2 s / 3,8 s |

Dépense totale du test : **0,12 $** sur le plafond de 4 $ (`budget.json`, y compris 6 appels d'essai). Extraction des transcriptions : 9 s, un processus, aucune charge locale notable (pas d'Ollama ni de GPU).

## 5. Analyse de puissance

AUC de 0,65 contre 0,5, test bilatéral à 5 %, puissance de 80 %, variance de Hanley et McNeil à la prévalence observée de chaque étiquette. Vérifié par simulation binormale (étiquette de dérapage, 32 positifs et 453 négatifs, 2 000 essais : puissance simulée 82 %).

| Étiquette | Positifs actuels | Taux de base | **Positifs nécessaires (AUC 0,65)** | Stories nécessaires | Puissance actuelle | Plus petite AUC détectable aujourd'hui (80 %) | Positifs pour un écart de 0,05 à l'heuristique |
|---|---|---|---|---|---|---|---|
| **Dérapage** | 15 | 6,6 % | **32** | 482 | 49 % | 0,72 | 289 |
| Coût élevé | 46 | 20,4 % | 37 | 182 | 88 % | 0,64 | 320 |
| Défaut de revue | 174 | 77 % | 122 | 158 | 93 % | 0,63 | 855 |
| Appels au-dessus du 80e centile (`haut20`) | 43 | 19 % | 37 | 194 | 86 % | 0,64 | 316 |

Lecture :
- **Pour le dérapage, il faut 32 positifs (environ 480 stories au taux de 6,6 %)** pour détecter une AUC de 0,65 ; on en a 15, soit une puissance de 49 % : une AUC de 0,60 à 0,65 sur le dérapage ne pourrait être ni confirmée ni exclue. Il faudrait environ 2,1 fois le jeu actuel de stories, soit environ quatre autres projets de la taille de wavelibrarian.
- Pour le coût et `haut20`, la puissance suffit déjà pour 0,65 : le résultat « 0,65 sans mieux que la longueur » est donc informatif. Pour le coût, il exclut une AUC de 0,75 ou plus (bornes hautes des IC de Jev à 0,73 et 0,74).
- Le critère de la veille demande un **écart de 0,05 à l'heuristique** : le détecter (AUC 0,70 contre 0,65, deux bras corrélés à r = 0,5, hypothèse) exige près de 300 positifs, soit environ 1 500 stories pour le coût. Aucune des remontées de données prévisibles n'y suffit ; un test d'écart ne se tranchera qu'avec de très gros volumes, ou avec un bras dont l'AUC est nettement plus haute (0,8 et plus).

## 6. Limites

1. **Une seule source de données** : un auteur, une semaine (2026-10-13 au 19), cinq dépôts, une chaîne d'agents, des specs de forme proche. Pas de généralisation à d'autres équipes ou outils.
2. **Le dérapage reste sous-puissant** (15 positifs, voir section 5). Les IC par dépôt ne servent à rien : les chiffres par dépôt sont indicatifs.
3. **Étiquettes bruitées** : le nombre d'appels et le coût dépendent aussi des reprises, des attentes de CI, du parallélisme, des échecs d'intégration entre stories parallèles et du modèle (21 stories ne sont pas 100 % Sonnet) ; le numéro de story est lu par expression régulière dans la description de l'agent (76 agents sans numéro, dont les rejeux de banc, `agent-cost-kit` et `wavestack`). Le défaut de revue est lu par motifs dans des formats de revue qui diffèrent selon le dépôt, et 77 % de positifs prédisent mal par construction.
4. **La spec testée est la section d'`epics.md`**, pas le fichier de story complet que lit `dev-story` (contexte d'architecture, tâches, fichiers à toucher) : un modèle avec tout ce contexte pourrait mieux faire. Les fichiers de story n'ont pas pu servir : leurs premiers commits contiennent déjà des sections remplies pendant le développement.
5. **Un prompt par bras**, effort de raisonnement bas, une formulation par question ; pas de réglage de seuil par bras. Le prompt contient des taux de base et des plages tirés de ces données (médianes de 26 à 87 appels, coût de 1 à 5 $) : sur une relance avec beaucoup de nouvelles stories, mettre à jour `CONTEXTE` dans `scorer.py` et changer `VERSION_PROMPT` (les anciens scores sont alors refaits).
6. **L'alias `~typesafe/jev-latest`** peut changer de version entre deux relances (il pointait sur 1,14 le 2026-10-14) : pour comparer, relancer avec `--forcer-scores` ou figer `typesafe/jev-1.13`.
7. **Comparaisons multiples** : 25 AUC comparées à la référence, aucune ne passe ; un passage isolé serait à confirmer sur de nouvelles données.
8. Le test ne mesure pas directement le choix du modèle de développement (Sonnet ou Opus) : il suppose qu'un signal de risque en serait le préalable.

## 7. Décision proposée

- **Ne brancher ni Jev, ni gpt-6-luna dans `agent-cost-kit`** comme alerte de dérapage, de coût ou sélecteur de modèle : aucun n'atteint 0,7 ni ne bat la longueur de la spec de 0,05 (meilleur écart : +0,03 pour Jev 1,13 sur `haut20` ou sur le dérapage, dans le bruit).
- Si une alerte est voulue, la **longueur de la spec** (AUC 0,65 sur le coût et 0,66 sur `haut20`, 38 % de précision à 20 % d'alertes pour un taux de base de 20 %) fait aussi bien qu'un LLM pour un coût nul ; elle est faible et ne dépasse pas 0,7. Garder l'alerte **observée et non prédite** proposée par T1 (notifier l'orchestrateur quand l'agent dépasse 2 fois la médiane d'appels du dépôt).
- **Relancer le test** quand l'une de ces conditions est atteinte : au moins **32 dérapages** (environ 480 stories, soit le double d'aujourd'hui) ; transcriptions d'un autre PC ; fichier de story complet avec tâches et fichiers à toucher écrit avant le développement ; piste des stories d'avant le 2026-10-13 en agents `general-purpose` (service-public, usine : plusieurs centaines d'agents), à trier avant usage. Coût d'une relance : moins de 0,25 $ (scores incrémentaux, seules les nouvelles stories sont demandées).
- Piste d'économie à garder en tête : les transcriptions se conservent déjà depuis le 2026-09-25, mais le type `dev-story` n'a que 11 jours d'historique ; aucun `cleanupPeriodDays` n'est réglé (valeur par défaut, 30 jours sauf erreur) : les transcriptions du 2026-09-25 vont être purgées ; rapatrier ou allonger la durée avant les prochaines relances.

## 8. Relancer avec d'autres transcriptions

Depuis `tests-pratiques/T9-elargi`, un seul processus à la fois. Chaque racine `--transcriptions` a la même structure que `~/.claude/projects` (`<racine>/<projet>/<session>/subagents/agent-*.jsonl` et `.meta.json` voisin) ; la racine locale est toujours incluse (`--sans-racine-locale` pour l'ignorer). Les dépôts publics doivent être clonés sous `--racine-depots` (défaut `~/Documents/GitHub`) pour lire `epics.md` et les revues, mais les chemins de transcription d'un autre PC (Windows ou POSIX, autre nom d'utilisateur) sont reconnus par le nom du dépôt.

```
cd <user>\Documents\GitHub\veille-agents-code\tests-pratiques\T9-elargi
uv run --no-project --with numpy --with scikit-learn --with scipy python relancer.py --transcriptions D:\rapatrie\pc2\projects --transcriptions D:\rapatrie\pc3\projects
```

`relancer.py` enchaîne : `extraire_agents.py` (transcriptions vers `agents.json`), `construire_donnees.py` (specs et étiquettes vers `etiquettes.csv` et `bilan_donnees.json`), `scorer.py` (Jev latest, Jev 1,13, gpt-6-luna deux fois ; seules les stories nouvelles sont demandées, plafond 3,8 $ appliqué sur 4 $ cumulés dans `budget.json`), puis `analyse.py` (`resultats.json`, `tableaux.md`, puissance). Il suffit ensuite de reporter les chiffres dans ce rapport. Options : `--travail <dossier>` (défaut `~/.cache/veille-t9-elargi`, hors dépôt : y vivent `agents.json` et `textes.json`), `--sans-scoring` (aucun appel payant), `--forcer-scores`. La clé est la variable utilisateur `OPENROUTER_API_KEY`, lue par `cle.py` dans l'environnement puis dans `HKCU\Environment`, jamais affichée ni écrite. Chaque étape se lance aussi seule (`--help`). Pour cette exécution, le dossier de travail était un dossier temporaire de session (`--travail`).

Fichiers : `relancer.py`, `extraire_agents.py` (réutilise `lire_fichier` et `cout_appel` de `../T1/analyse.py`), `construire_donnees.py`, `scorer.py`, `analyse.py`, `cle.py` ; données agrégées : `etiquettes.csv` (clé de story, étiquettes, caractéristiques numériques : aucun texte), `bilan_donnees.json`, `scores_*.json` (probabilités, coûts, latences, empreinte du texte : aucun texte), `resultats.json`, `tableaux.md`, `budget.json`.

---

## Annexe : tableaux complets (générés par `analyse.py`, fichier `tableaux.md`)

### Positifs par étiquette et par dépôt (positifs / stories étiquetées)

| Étiquette | Total | service-public-slm-fine-tuning | usine-migration-jira-demo | wavedevsecops | wavelibrarian | wavelocalai |
|---|---|---|---|---|---|---|
| dérapage (appels > 2 × médiane du dépôt) | 15 / 226 | 1 / 31 | 4 / 12 | 4 / 64 | 5 / 65 | 1 / 54 |
| coût au-dessus du 80e centile du dépôt | 46 / 226 | 6 / 31 | 3 / 12 | 13 / 64 | 13 / 65 | 11 / 54 |
| défaut de revue (constat medium ou high corrigé) | 174 / 225 | 29 / 31 | 6 / 11 | 42 / 64 | 53 / 65 | 44 / 54 |
| dérapage par agent (critère de T1) | 15 / 226 | 1 / 31 | 1 / 12 | 7 / 64 | 3 / 65 | 3 / 54 |
| appels au-dessus du 80e centile du dépôt | 43 / 226 | 6 / 31 | 3 / 12 | 12 / 64 | 12 / 65 | 10 / 54 |

### dérapage (appels > 2 × médiane du dépôt) : 15 positifs sur 226 (taux de base 7 %)

| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes (≤ 20 %) | Vrais positifs | Précision | Rappel | Écart à la référence [IC] | Critère |
|---|---|---|---|---|---|---|---|---|
| Heuristique : longueur seule | 0,606 [0,45 ; 0,75] | 0,607 | 45 | 6 | 13 % | 40 % | référence |  |
| Heuristique : régression logistique (CV) | 0,348 [0,21 ; 0,50] | 0,370 | 45 | 1 | 2 % | 7 % |  |  |
| Jev latest | 0,613 [0,50 ; 0,72] | 0,636 | 43 | 2 | 5 % | 13 % | 0,01 [-0,16 ; 0,18] | non |
| Jev 1,13 | 0,633 [0,51 ; 0,75] | 0,657 | 40 | 3 | 8 % | 20 % | 0,03 [-0,14 ; 0,21] | non |
| gpt-6-luna, exéc. 1 | 0,522 [0,38 ; 0,66] | 0,592 | 41 | 2 | 5 % | 13 % | -0,08 [-0,26 ; 0,11] | non |
| gpt-6-luna, exéc. 2 | 0,545 [0,42 ; 0,67] | 0,594 | 33 | 1 | 3 % | 7 % | -0,06 [-0,18 ; 0,07] | non |
| gpt-6-luna, moyenne | 0,544 [0,41 ; 0,67] | 0,622 | 44 | 2 | 4 % | 13 % | -0,06 [-0,21 ; 0,10] | non |

### coût au-dessus du 80e centile du dépôt : 46 positifs sur 226 (taux de base 20 %)

| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes (≤ 20 %) | Vrais positifs | Précision | Rappel | Écart à la référence [IC] | Critère |
|---|---|---|---|---|---|---|---|---|
| Heuristique : longueur seule | 0,650 [0,56 ; 0,74] | 0,649 | 45 | 17 | 38 % | 37 % | référence |  |
| Heuristique : régression logistique (CV) | 0,614 [0,52 ; 0,70] | 0,616 | 45 | 17 | 38 % | 37 % |  |  |
| Jev latest | 0,649 [0,56 ; 0,73] | 0,658 | 45 | 13 | 29 % | 28 % | -0,00 [-0,09 ; 0,09] | non |
| Jev 1,13 | 0,654 [0,57 ; 0,74] | 0,660 | 44 | 14 | 32 % | 30 % | 0,00 [-0,09 ; 0,11] | non |
| gpt-6-luna, exéc. 1 | 0,620 [0,53 ; 0,71] | 0,635 | 30 | 9 | 30 % | 20 % | -0,03 [-0,14 ; 0,08] | non |
| gpt-6-luna, exéc. 2 | 0,628 [0,54 ; 0,71] | 0,650 | 30 | 9 | 30 % | 20 % | -0,02 [-0,12 ; 0,08] | non |
| gpt-6-luna, moyenne | 0,637 [0,55 ; 0,72] | 0,650 | 43 | 13 | 30 % | 28 % | -0,01 [-0,11 ; 0,09] | non |

### défaut de revue (constat medium ou high corrigé) : 174 positifs sur 225 (taux de base 77 %)

| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes (≤ 20 %) | Vrais positifs | Précision | Rappel | Écart à la référence [IC] | Critère |
|---|---|---|---|---|---|---|---|---|
| Heuristique : longueur seule | 0,519 [0,42 ; 0,62] | 0,513 | 45 | 30 | 67 % | 17 % | référence |  |
| Heuristique : régression logistique (CV) | 0,469 [0,38 ; 0,55] | 0,460 | 45 | 35 | 78 % | 20 % |  |  |
| Jev latest | 0,508 [0,41 ; 0,60] | 0,504 | 36 | 27 | 75 % | 16 % | -0,01 [-0,11 ; 0,09] | non |
| Jev 1,13 | 0,551 [0,46 ; 0,64] | 0,544 | 39 | 31 | 80 % | 18 % | 0,03 [-0,06 ; 0,12] | non |
| gpt-6-luna, exéc. 1 | 0,599 [0,51 ; 0,68] | 0,580 | 24 | 22 | 92 % | 13 % | 0,08 [-0,00 ; 0,16] | non |
| gpt-6-luna, exéc. 2 | 0,522 [0,43 ; 0,61] | 0,497 | 27 | 20 | 74 % | 12 % | 0,00 [-0,08 ; 0,09] | non |
| gpt-6-luna, moyenne | 0,571 [0,48 ; 0,66] | 0,536 | 45 | 36 | 80 % | 21 % | 0,05 [-0,02 ; 0,13] | non |

### dérapage par agent (critère de T1) : 15 positifs sur 226 (taux de base 7 %)

| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes (≤ 20 %) | Vrais positifs | Précision | Rappel | Écart à la référence [IC] | Critère |
|---|---|---|---|---|---|---|---|---|
| Heuristique : longueur seule | 0,657 [0,50 ; 0,80] | 0,662 | 45 | 7 | 16 % | 47 % | référence |  |
| Heuristique : régression logistique (CV) | 0,540 [0,39 ; 0,69] | 0,543 | 45 | 3 | 7 % | 20 % |  |  |
| Jev latest | 0,622 [0,48 ; 0,75] | 0,627 | 43 | 5 | 12 % | 33 % | -0,03 [-0,17 ; 0,13] | non |
| Jev 1,13 | 0,664 [0,51 ; 0,81] | 0,663 | 40 | 6 | 15 % | 40 % | 0,01 [-0,12 ; 0,17] | non |
| gpt-6-luna, exéc. 1 | 0,594 [0,46 ; 0,72] | 0,585 | 41 | 2 | 5 % | 13 % | -0,06 [-0,22 ; 0,10] | non |
| gpt-6-luna, exéc. 2 | 0,603 [0,46 ; 0,74] | 0,617 | 33 | 3 | 9 % | 20 % | -0,05 [-0,13 ; 0,03] | non |
| gpt-6-luna, moyenne | 0,593 [0,46 ; 0,72] | 0,604 | 44 | 4 | 9 % | 27 % | -0,06 [-0,17 ; 0,04] | non |

### appels au-dessus du 80e centile du dépôt : 43 positifs sur 226 (taux de base 19 %)

| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes (≤ 20 %) | Vrais positifs | Précision | Rappel | Écart à la référence [IC] | Critère |
|---|---|---|---|---|---|---|---|---|
| Heuristique : longueur seule | 0,662 [0,57 ; 0,75] | 0,660 | 45 | 17 | 38 % | 40 % | référence |  |
| Heuristique : régression logistique (CV) | 0,632 [0,54 ; 0,73] | 0,629 | 45 | 15 | 33 % | 35 % |  |  |
| Jev latest | 0,667 [0,58 ; 0,74] | 0,672 | 43 | 12 | 28 % | 28 % | 0,01 [-0,10 ; 0,12] | non |
| Jev 1,13 | 0,688 [0,61 ; 0,77] | 0,700 | 40 | 13 | 32 % | 30 % | 0,03 [-0,08 ; 0,14] | non |
| gpt-6-luna, exéc. 1 | 0,658 [0,57 ; 0,74] | 0,653 | 41 | 14 | 34 % | 33 % | -0,00 [-0,10 ; 0,10] | non |
| gpt-6-luna, exéc. 2 | 0,645 [0,56 ; 0,73] | 0,661 | 33 | 7 | 21 % | 16 % | -0,02 [-0,10 ; 0,07] | non |
| gpt-6-luna, moyenne | 0,654 [0,57 ; 0,74] | 0,669 | 44 | 14 | 32 % | 33 % | -0,01 [-0,09 ; 0,08] | non |

### AUC par dépôt (positifs entre parenthèses ; n.d. si moins de 2 positifs ou de 2 négatifs)

| Étiquette | Bras | service-public-slm-fine-tuning | usine-migration-jira-demo | wavedevsecops | wavelibrarian | wavelocalai |
|---|---|---|---|---|---|---|
| derapage | Heuristique : longueur seule | n.d. (1) | 0,78 (4) | 0,52 (4) | 0,62 (5) | n.d. (1) |
| derapage | Jev latest | n.d. (1) | 0,52 (4) | 0,57 (4) | 0,67 (5) | n.d. (1) |
| derapage | gpt-6-luna, exéc. 1 | n.d. (1) | 0,72 (4) | 0,52 (4) | 0,52 (5) | n.d. (1) |
| cout80 | Heuristique : longueur seule | 0,91 (6) | 0,85 (3) | 0,64 (13) | 0,55 (13) | 0,57 (11) |
| cout80 | Jev latest | 0,83 (6) | 0,56 (3) | 0,60 (13) | 0,68 (13) | 0,63 (11) |
| cout80 | gpt-6-luna, exéc. 1 | 0,86 (6) | 0,67 (3) | 0,59 (13) | 0,60 (13) | 0,59 (11) |
| defaut_revue | Heuristique : longueur seule | 0,83 (29) | 0,77 (6) | 0,41 (42) | 0,72 (53) | 0,29 (44) |
| defaut_revue | Jev latest | 0,78 (29) | 0,47 (6) | 0,37 (42) | 0,68 (53) | 0,48 (44) |
| defaut_revue | gpt-6-luna, exéc. 1 | 0,85 (29) | 0,58 (6) | 0,46 (42) | 0,77 (53) | 0,53 (44) |

### Précision et rappel à 20 % d'alertes par dépôt (vrais positifs / alertes ; positifs du dépôt)

| Étiquette | Bras | service-public-slm-fine-tuning | usine-migration-jira-demo | wavedevsecops | wavelibrarian | wavelocalai |
|---|---|---|---|---|---|---|
| derapage | Heuristique : longueur seule | 1/6 ; 1 pos. | 1/2 ; 4 pos. | 0/12 ; 4 pos. | 3/13 ; 5 pos. | 0/10 ; 1 pos. |
| derapage | Jev latest | 1/4 ; 1 pos. | 0/1 ; 4 pos. | 0/11 ; 4 pos. | 2/12 ; 5 pos. | 1/10 ; 1 pos. |
| derapage | gpt-6-luna, exéc. 1 | 1/6 ; 1 pos. | 1/2 ; 4 pos. | 1/12 ; 4 pos. | 1/11 ; 5 pos. | 0/9 ; 1 pos. |
| cout80 | Heuristique : longueur seule | 3/6 ; 6 pos. | 1/2 ; 3 pos. | 4/12 ; 13 pos. | 5/13 ; 13 pos. | 3/10 ; 11 pos. |
| cout80 | Jev latest | 5/6 ; 6 pos. | 0/2 ; 3 pos. | 3/12 ; 13 pos. | 4/11 ; 13 pos. | 1/8 ; 11 pos. |
| cout80 | gpt-6-luna, exéc. 1 | 3/6 ; 6 pos. | 1/2 ; 3 pos. | 4/11 ; 13 pos. | 5/12 ; 13 pos. | 2/10 ; 11 pos. |
| defaut_revue | Heuristique : longueur seule | 6/6 ; 29 pos. | 1/2 ; 6 pos. | 6/12 ; 42 pos. | 11/13 ; 53 pos. | 4/10 ; 44 pos. |
| defaut_revue | Jev latest | 2/2 ; 29 pos. | 0/1 ; 6 pos. | 6/10 ; 42 pos. | 9/10 ; 53 pos. | 3/3 ; 44 pos. |
| defaut_revue | gpt-6-luna, exéc. 1 | 6/6 ; 29 pos. | 2/2 ; 6 pos. | 8/12 ; 42 pos. | 13/13 ; 53 pos. | 8/9 ; 44 pos. |

### Analyse de puissance (AUC 0,65 contre 0,5, bilatéral 5 %, puissance 80 %)

| Étiquette | Positifs | Négatifs | Taux de base | Positifs nécessaires | Stories nécessaires | Puissance actuelle (AUC 0,65) | AUC détectable aujourd'hui (80 %) | Positifs pour un écart de 0,05 à l'heuristique |
|---|---|---|---|---|---|---|---|---|
| dérapage (appels > 2 × médiane du dépôt) | 15 | 211 | 7 % | 32 | 482 | 49 % | 0,72 | 289 |
| coût au-dessus du 80e centile du dépôt | 46 | 180 | 20 % | 37 | 182 | 88 % | 0,64 | 320 |
| défaut de revue (constat medium ou high corrigé) | 174 | 51 | 77 % | 122 | 158 | 93 % | 0,63 | 855 |
| dérapage par agent (critère de T1) | 15 | 211 | 7 % | 32 | 482 | 49 % | 0,72 | 289 |
| appels au-dessus du 80e centile du dépôt | 43 | 183 | 19 % | 37 | 194 | 86 % | 0,64 | 316 |

Vérification par simulation binormale (derapage, 32 positifs et 453 négatifs, AUC 0,65) : puissance simulée 82 %.

Dernière colonne : ecart de 0,05 (AUC 0,70 contre 0,65) entre deux bras correles (r = 0,5 supposee), 5 % bilateral, puissance 80 %.
