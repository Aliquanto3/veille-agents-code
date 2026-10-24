# T5 : un relecteur d'une autre famille trouve-t-il ce que la chaîne Claude a manqué, et la porte empirique élimine-t-elle les faux positifs ?

Test pratique T5 de la veille sur les agents de code (`recherche/technical-outils-et-pratiques-des-agents-de-code-2026-10-24`, section 7). Mesuré le 2026-10-24 via OpenRouter, sans charge locale notable (un fichier de test à la fois, délai de 60 s). Aucune clé n'est écrite dans les fichiers ni les journaux. Les chiffres de coût viennent du champ `usage.cost` des réponses.

## 1. Résultat en bref

- **Défauts connus manqués par la chaîne : 0 retrouvé sur 5** dans la passe officielle, par les quatre modèles. Une passe exploratoire antérieure (voir 4.6) en a retrouvé 1 sur 5 (`gpt-6.1-sol`). Sur les 4 défauts « connus de la chaîne mais non corrigés à la fusion », 1 est retrouvé (`kimi-k3.1-pro`).
- **Défauts nouveaux** (jamais consignés par la chaîne ni par la rétrospective, confirmés par un test qui échoue et qui échoue encore sur la tête de `main`) : 2 distincts, tous deux mineurs. Ce sont l'affichage d'une progression périmée en statut « attente » (trouvé par `luna` et `sol`) et un identifiant séparé par des tabulations ou des sauts de ligne qui échappe au balayage SM-7 (trouvé par `kimi`).
- **La porte empirique n'a éliminé aucun faux positif** : les 23 constats Important de l'ensemble des passes (4 modèles, 7 stories, 2 passes pour `luna` et `sol`) sont accompagnés d'un test, et les 23 échouent bel et bien sur le code fusionné. Aucun test ne passe, aucun ne plante à l'import, aucun n'est refusé. La porte prouve que le constat est reproductible, pas qu'il est pertinent : 2 Important sur 23 relèvent de « rien de vérifiable », 6 sont « discutables » (écart littéral à la spec, durcissement) et 11 (48 %) avaient déjà été vus et tranchés par la chaîne.
- **Un seul des quatre modèles est inutilisable tel quel** : `mimo-v2.6-pro` épuise 32 000 jetons de sortie en raisonnement et rend une réponse vide sur 5 stories sur 7 (une 6e est tronquée).

## 2. Jeu de données

**Dépôt de référence** : `usine-migration-jira-demo` (public). Aucun autre dépôt n'a été nécessaire. **7 stories**, dont 1 témoin sans défaut connu. Le diff envoyé est le **diff net** de la story avec son commit de correctifs de revue (appliqués seuls sur le parent du premier commit, dans un worktree jetable), en `-U1`, limité à 60 000 caractères : fichiers Python de `src`, `evals` et `outils` d'abord, puis tests, puis le reste ; les fichiers de `_bmad-output`, les résultats d'évaluation et les `.lock` sont exclus. Les fichiers statiques (`.js`, `.html`, `.css`) de 7.15 et 7.16 ne tiennent pas dans la limite et sont omis. La spec envoyée ne contient que les sections écrites avant le développement (Intent, Boundaries, matrice I/O, Code Map, Tasks, Design Notes), jamais le journal de revue.

| Id | Story | Commits | État testé | Défaut(s) connu(s) | Source de la vérité |
|---|---|---|---|---|---|
| S1 | 0.7 passerelle LLM minimale | `674dd68` + `e34200a` | `e34200a` | D1 manqué : grammaire des jetons de pseudonymisation dupliquée, jetons préfixés non réidentifiés | rétrospective de l'Epic 0, constat 8 |
| S2 | 0.8 UI minimale | `05ee86f` + `4171da2` | `4171da2` | D1 manqué : `ValidationError` brute de `Secrets` dans `construire_rapport` (vérifié par exécution) ; D2 manqué : `USINE_RACINE` lu par `os.environ` hors `Secrets` (AD-19) ; D3 manqué : `Popen` sans nouveau groupe de processus, Ctrl+C arrête aussi la Chaîne | rétrospective constats 13 et 14 ; revue de 7.17-b |
| S3 | 6.10 classification tolérante, préchauffage, SM-7 | `22d7079` + `3ac720e` | `3ac720e` | D1 connu de la chaîne : appel en échec absent des traces et de `cout_llm_eur` ; D2 connu : relances du préchauffage non bornées (reportés par la revue, corrigés en 6.10-b) | spec 6.10-b |
| S4 | 7.7 explication sourcée, aperçu de pseudonymisation | `adba54b` | `adba54b` | D1 connu : erreur hors `UsineErreur` du moteur Presidio non interceptée (notée par la revue, corrigée en 7.7-a) | spec 7.7, commit `4056a97` |
| S5 | 7.10 suite d'évaluation de l'agent | `56f0de6` | `56f0de6` | D1 connu : erreur réseau non `UsineErreur` en `--reel` (rejetée low, corrigée en 7.10-a) | spec 7.10, commit `5ca440d` |
| S6 | 7.15 lancement de la Chaîne | `d58ce6c` + `c86b2f7` | `c86b2f7` | aucun (témoin) | : |
| S7 | 7.16 Agent, Avant/après, Pseudonymisation, Outillage | `5545523` + `cf54141` | `cf54141` | D1 manqué : badge « hors périmètre » par égalité stricte avec `SANS_REPONSE` | spec 7.17-b, commit `40e44ad` |

Soit **5 défauts manqués** (S1 D1, S2 D1 à D3, S7 D1) et **4 défauts connus de la chaîne** (S3 D1 et D2, S4 D1, S5 D1). Pour chaque story, `jeu/<id>/` contient `diff.patch`, `spec.md` et `chaine.md` (revue d'origine, second avis et reviewer, avec le sort de chaque constat : jamais envoyée aux modèles). Le sort des constats d'origine n'est pas retraité ici : la section « Revue » ou « Review Triage Log » de chaque spec sert de référence pour classer les constats des modèles comme « déjà trouvés par la chaîne ». La story 7.15 sert de témoin : elle ne figure dans la vérité terrain que comme story sans défaut consigné (la revue d'origine y avait trouvé le DNS rebinding avec Opus).

**Pourquoi si peu de défauts.** Le dépôt fusionne dans `main` presque linéairement et la chaîne y corrige elle-même ses constats avant fusion. Les défauts « découverts après coup » sont rares : la rétrospective de l'Epic 0, la revue de 7.17-b, les constats reportés puis soldés en 6.10-b, 7.7-a et 7.10-a. Les commits « intégration de la Story X » sont des correctifs de fixtures de test, pas des défauts de la story, et n'ont pas été retenus.

## 3. Protocole

- **Modèles et tarifs** (OpenRouter, par million de jetons entrée / sortie) : `openai/gpt-6-luna` 0,10 $ / 0,50 $, `xiaomi/mimo-v2.6-pro` 0,435 $ / 0,87 $, `openai/gpt-6.1-sol` 2 $ / 10 $, `moonshotai/kimi-k3.1-pro` 2 $ / 10 $.
- **Prompt** (`revue.py`, le même pour tous) : consigne de relecteur inspirée de `agents/reviewer.md` d'agent-cost-kit (vrais défauts, suivre les appelants, prouver plutôt que supposer, questionner les tests de l'implémenteur, ignorer le style). Format fixe en JSON : `{"constats": [{id, fichier, ligne, severite: Important|Nit, description, test_pytest}]}`. Pour chaque Important, un test pytest minimal et autonome qui échouerait sur le code fusionné ; si le modèle ne peut pas l'écrire, le constat est un Nit. Contraintes du test : pas de réseau, pas de sous-processus, écritures sous `tmp_path` seulement. Au plus 6 Important et 6 Nit. Le relecteur ne voit que la spec et le diff, il n'a pas accès au dépôt (la chaîne Claude, elle, exécute du code).
- **Réglages** : `temperature` 0, `response_format` `json_object`, 32 000 jetons de sortie au plus, raisonnement au réglage par défaut du fournisseur, un seul appel par modèle et par story, au plus 2 appels simultanés par modèle. Une réponse vide par épuisement du budget de sortie (`finish_reason` = `length`) est reprise une fois à effort de raisonnement bas : cela a eu lieu 6 fois pour `mimo` (sans succès : la reprise épuise encore 32 000 jetons) et 2 fois pour `kimi` (S3 et S6, les deux reprises ont abouti).
- **Passes** : r1 (officielle, 4 modèles × 7 stories = 28 réponses) ; r2 (répétition à l'identique pour `luna` et `sol`, 14 réponses) ; un complément de `mimo` avec un plafond de raisonnement de 6 000 jetons sur S1 et S3 (2 réponses, sans effet : S1 reste vide). Les constats d'une réponse tronquée sont récupérés tant que leur objet JSON est complet.
- **Exécution des tests** (`executer_tests.py`) : les tests des modèles sont du code non fiable. Filtre statique avant exécution (réseau, sous-processus, suppression de fichiers, `ctypes`, `eval`/`exec`, écriture hors `tmp_path`), puis lecture humaine de chaque test (23 sur 23 lus, aucun refusé). Exécution un par un, dans un worktree jetable du dépôt à l'état fusionné de la story (`git worktree add --detach`), avec l'interpréteur du projet (`.venv`), `PYTHONPATH` pointé sur le worktree (vérifié : le module `usine` importé vient bien du worktree), `pytest -q --tb=line -x -p no:cacheprovider` sur le seul fichier, délai de 60 s, environnement minimal sans aucun secret. Le `conftest` du projet coupe en outre tout réseau. Jamais la suite complète. Worktrees supprimés en fin de run.
- **Classement des constats Important** (`classification.py`, jugement à la main, test et code lus) : `manque` (défaut connu manqué), `chaine` (déjà vu et tranché par la chaîne), `confirme` (nouveau, test qui échoue pour la bonne raison, non consigné), `discutable` (le test échoue mais c'est un écart littéral à la spec, un durcissement sans exploitation atteinte ou un comportement défendable), `rien` (non vérifiable ou déclenché par une hypothèse que le dépôt n'a pas). Un second jeu d'exécutions rejoue chaque test sur la tête de `main` : un test qui passe là prouve un défaut corrigé plus tard.

## 4. Résultats

### 4.1 Passe officielle r1

| Modèle | Réponses exploitables (sur 7) | Important | Nit | Défauts connus manqués retrouvés (sur 5) | Classes des Important | Tests : échouent / passent / hors exécution | Coût | Latence moyenne par story |
|---|---|---|---|---|---|---|---|---|
| `gpt-6-luna` | 7 | 3 | 2 | 0 | 1 chaîne, 1 confirmé, 1 rien | 3 / 0 / 0 | 0,028 $ | 39 s |
| `mimo-v2.6-pro` | 2 (5 vides, 1 tronquée récupérée) | 1 | 7 | 0 | 1 chaîne | 1 / 0 / 0 | 0,427 $ | 1 094 s |
| `gpt-6.1-sol` | 7 | 6 | 0 | 0 | 2 chaîne, 1 confirmé, 3 discutables | 6 / 0 / 0 | 0,370 $ | 20 s |
| `kimi-k3.1-pro` | 7 | 4 | 2 | 0 (1 défaut connu de la chaîne : S3 D1) | 2 chaîne, 1 confirmé, 1 discutable | 4 / 0 / 0 | 2,500 $ | 675 s |

Jetons de sortie par modèle : `luna` 25 700, `sol` 5 900, `kimi` 154 300, `mimo` 221 800. Entrée : environ 17 800 jetons par story pour `luna` et `sol`. `kimi` a répondu zéro constat (`{"constats": []}`) sur S2, S4 et S5, après 24 000 à 29 000 jetons de raisonnement chacune.

Sur la story S3, `mimo` n'a livré qu'une réponse tronquée à 32 000 jetons (1 Important et 1 Nit récupérés) ; avec le plafond de raisonnement à 6 000 jetons, il a répondu 0 constat.

### 4.2 Répétition r2 (luna et sol)

| Modèle | Important | Nit | Classes des Important | Tests : échouent / passent / hors exécution | Coût |
|---|---|---|---|---|---|
| `gpt-6-luna` | 4 | 1 | 3 chaîne, 1 discutable | 4 / 0 / 0 (dont 2 plantages valides du code testé) | 0,027 $ |
| `gpt-6.1-sol` | 5 | 0 | 2 chaîne, 1 confirmé, 1 discutable, 1 rien | 5 / 0 / 0 | 0,371 $ |

**Stabilité.** `sol` signale les mêmes 5 stories (S1, S2, S3, S6, S7) dans les deux passes et retrouve les mêmes constats sur S1, S2, S6 et S7. `luna` est moins stable : S1, S3, S6 en r1 contre S1, S2, S3, S7 en r2. Un tirage unique manque donc une partie de ce qu'un modèle sait trouver (voir aussi 4.6).

### 4.3 Défauts connus, un par un

| Story | Défaut | Retrouvé ? |
|---|---|---|
| S1 D1 (manqué) | jetons préfixés non réidentifiés | non en r1 et r2 ; oui par `sol` dans la passe exploratoire (4.6) |
| S2 D1, D2, D3 (manqués) | `ValidationError` brute, `USINE_RACINE`, `Popen` sur la console | non, par aucun modèle (une seule réponse complète de `mimo` sur S2, 6 Nit sans rapport) |
| S3 D1 (connu de la chaîne) | appel en échec absent des traces et du bilan | oui, `kimi` (le test passe sur `main` : corrigé en 6.10-b) |
| S3 D2 (connu) | relances du préchauffage non bornées | non |
| S4 D1, S5 D1 (connus) | erreur hors `UsineErreur` du moteur Presidio ; erreur réseau en `--reel` | non (aucun Important sur S4 et S5 dans r1 et r2 ; `mimo` vide ; `luna` signale un autre point sur S4 dans la passe exploratoire) |
| S7 D1 (manqué) | badge par égalité stricte | non : `sol` et `kimi` ont signalé la même fonction, mais pour la liste des outils d'un refus, pas pour la comparaison stricte |

### 4.4 Ce que valent les 23 constats Important

| Classe | r1 | r2 | Total | Exemples |
|---|---|---|---|---|
| Déjà vu et tranché par la chaîne | 6 | 5 | 11 (48 %) | clé d'un autre projet ignorée par le contrôle des citations (3 modèles, rejetée par la revue de 0.7) ; fichier de progression choisi par nom (rejetée « carried » en 0.8) ; plafond de 20 échecs au total (décision explicite de la revue de 6.10) ; appel en échec non tracé (6.10 D1) |
| Confirmé (nouveau) | 3 | 1 | 4 | progression périmée affichée en attente (S6, `luna` et `sol`, 3 occurrences) ; tabulations et sauts de ligne échappés dans la trace JSONL contre SM-7 (S3, `kimi`) |
| Discutable | 4 | 2 | 6 | liste des outils conservée au refus (S7, 3 occurrences : la matrice de la spec dit « aucun ») ; image Markdown distante non neutralisée dans la fiche ; exception inattendue de la fabrique de session en 502 au lieu de 503 |
| Rien de vérifiable | 1 | 1 | 2 | échappement ` ` propre à `json.dumps(ensure_ascii=True)` alors que le dépôt écrit `ensure_ascii=False` |

Les deux défauts confirmés demandent une lecture. Pour SM-7, la revue de 6.10 déclarait les tabulations couvertes, mais seulement dans du texte décodé : dans une trace JSONL une tabulation devient `\t`, et la compaction des blancs ne la retire pas. Le défaut est réel et non corrigé sur `main`, mais il suppose un identifiant injecté avec des tabulations, ce que le générateur ne produit pas (IBAN avec espaces). Pour la progression, l'écran affiche une ancienne exécution (étapes terminées, journal) alors que le statut est « attente », après un redémarrage de `usine ui` sur une racine qui a un historique : défaut d'affichage, sans perte de données.

### 4.5 Porte empirique

| Résultat du test sur le code fusionné | Constats Important | dont faux (`rien`) | dont discutables |
|---|---|---|---|
| échoue par assertion | 20 | 2 | 5 |
| échoue par exception levée par le code testé | 3 | 0 | 1 |
| passe | 0 | : | : |
| ne s'exécute pas, refusé ou absent | 0 | : | : |

Les 3 « exceptions » ont été relues : ce sont des erreurs levées par le code testé (par exemple `UsineErreur` après 20 échecs non consécutifs, `RuntimeError` non convertie), donc des démonstrations valides.

**Taux d'élimination des faux : 0 sur 2** (0 sur 8 si l'on range les discutables parmi les faux). Le critère de la veille (au moins la moitié des Important faux éliminés) n'est pas rempli, pour une raison simple : aucun modèle n'a livré de test qui passe ou qui ne s'exécute pas. Deux effets y contribuent. Le prompt force le modèle à écrire le test avant de classer en Important (un constat sans test devient Nit : les 12 Nit des passes r1 et r2 n'ont pas de test), ce qui joue déjà le rôle d'une porte en amont. Et le relecteur voit le diff et les noms réels des fonctions, donc n'invente pas d'API. Les faux restants ne sont pas des erreurs de test mais des erreurs de jugement (un test qui démontre fidèlement un comportement que la spec ou la revue d'origine avaient écarté).

Sur la tête de `main`, 22 des 23 tests échouent encore ; seul celui de `kimi` sur S3 D1 passe, ce qui confirme que ce défaut a bien été corrigé plus tard (6.10-b).

### 4.6 Passe exploratoire r0 (abandonnée, hors tableaux)

Une première passe (4 modèles, diffs de story concaténés commit par commit au lieu d'un diff net) a été écartée parce que les hunks contradictoires entre le commit de la story et ses correctifs de revue faisaient signaler à tort des tests « périmés » (14 réponses conservées dans `archive_v0_diff_concatene/`). Rejouée avec le même protocole d'exécution, elle donne deux informations utiles. D'abord `gpt-6.1-sol` y trouve **S1 D1** : avec un compte précédé de « IBAN » collé, le texte réidentifié garde un jeton non résolu (`IBANCOMPTE_…`) ; le test échoue sur l'état fusionné et sur `main`, le défaut n'a jamais été corrigé. Ensuite il y signale que l'étape reste « En cours » quand le processus de la Chaîne est tué, constat qui échoue aussi sur `main` mais que ni r1 ni r2 n'ont reproduit. Le coût cumulé de cette passe est de 0,24 $. Ces deux constats ne sont pas comptés dans les tableaux ci-dessus, mais ils montrent la variabilité d'un tirage à l'autre.

## 5. Coût et latence

| Poste | Coût |
|---|---|
| r1 (4 modèles) | 3,33 $ |
| r2 (luna, sol) | 0,40 $ |
| complément `mimo` | 0,09 $ |
| passe exploratoire r0 | 0,24 $ |
| **Total** | **4,05 $** (plafond 6 $) |

Par story : `luna` 0,004 $ et 39 s ; `sol` 0,053 $ et 20 s ; `kimi` 0,357 $ et 675 s (dont l'essentiel en raisonnement) ; `mimo` 0,061 $ mais 1 094 s pour presque rien d'exploitable. Pour comparaison, T1 mesure 0,03 $ par story pour le second avis Haiku et 1,4 $ par story pour le reviewer Opus de la chaîne.

## 6. Limites

1. **Vérité terrain mince et orientée.** 5 défauts manqués et 4 défauts connus, dont 3 sur une seule story (S2). Les défauts viennent d'une rétrospective et d'une revue Opus : un défaut qu'aucun Claude ne trouve n'y figure pas, ce qui avantage la chaîne et sous-estime l'apport d'une autre famille. À l'inverse, la story témoin S6 a produit 2 défauts confirmés que la vérité terrain ignorait : elle est incomplète dans les deux sens.
2. **Un seul dépôt, 7 stories, 1 à 2 tirages.** Les écarts entre modèles (un Important de plus ou de moins) ne sont pas significatifs. r2 montre qu'un tirage unique varie sensiblement pour `luna`.
3. **Comparaison inéquitable en information.** Les modèles lisent un diff et une spec, sans dépôt ni exécution ; la chaîne Claude lit et exécute. Le diff est tronqué à 60 k caractères (les tests de S1 sont coupés) et sans fichiers statiques pour S6 et S7. En contrepartie, ils relisent un diff déjà corrigé par la chaîne (correctifs de revue compris), donc ce qu'ils trouvent a bien été manqué.
4. **Classement à la main.** Le classement `confirmé`, `discutable`, `rien` est un jugement unique, non contre-lu ; la frontière entre confirmé et discutable (par exemple la liste des outils d'un refus) est discutable. Les notes de chaque décision sont dans `classification.json`.
5. **Les tests s'exécutent sur l'état de la story, avec les helpers de test du dépôt** : plusieurs tests importent `tests.unit.*` du worktree. Ils ne seraient pas portables à un autre état.
6. **`mimo-v2.6-pro`** n'a pas été évalué au fond : 5 réponses vides sur 7 sous 32 000 jetons de sortie. Une limite de sortie bien plus haute (60 000 à 100 000 jetons, 20 à 40 minutes par appel) pourrait donner un autre résultat ; non tentée.
7. **Variabilité du fournisseur** : latences mesurées à un instant donné, avec 2 appels simultanés par modèle ; des erreurs 429 ont été absorbées par `luna` au premier lancement (relancé).
8. **Incident de procédure** : le premier lancement de `revue.py` a tourné deux fois en parallèle (un processus d'arrière-plan non arrêté), d'où quelques doubles appels et un compteur de coût approximatif ; le coût de référence ci-dessus est recalculé depuis les fichiers de réponse.

## 7. Décisions proposées

1. **Critique d'une autre famille : garder, mais comme complément ciblé et bon marché, pas comme remplaçant ni comme porte de fusion.** Le critère (au moins un vrai défaut manqué sans flot de faux positifs) est rempli **au sens large** (2 défauts nouveaux confirmés, 2 Important « rien » sur 23, pas de flot) et **non rempli au sens strict** (0 des 5 défauts connus manqués retrouvés en r1 et r2 ; 1 sur 5 seulement dans la passe exploratoire). Les défauts trouvés sont mineurs (affichage périmé, tabulations dans SM-7). Modèle à retenir : `gpt-6-luna` (0,004 $ par story, 39 s) en deux tirages, ou `gpt-6.1-sol` (0,05 $, 20 s, le plus stable d'un tirage à l'autre). Écarter `kimi-k3.1-pro` (0,36 $ et 11 min par story, mêmes constats que `sol`) et `mimo-v2.6-pro` (sorties vides sous 32 000 jetons). Test de suivi : sur 20 à 30 stories futures, compter les Important « confirmés » non consignés par la chaîne avant de l'intégrer au flux.
2. **Garder la porte empirique comme preuve de reproductibilité, mais ne pas la compter comme filtre de faux positifs.** Le critère (au moins la moitié des Important faux éliminés) n'est pas rempli (0 sur 2). Elle coûte presque rien (un fichier de test par constat, de 0,1 à 19 s chacun) et empêche les constats invérifiables ; elle ne tranche pas les écarts à la spec ni les décisions déjà prises.
3. **Ajouter deux portes moins chères à placer devant l'arbitre humain** : (a) rapprocher chaque constat de la section « Revue » de la story (11 des 23 Important, 48 %, avaient déjà été tranchés : à écarter ou à fusionner sans nouveau jugement), (b) rejouer le test sur la tête de la branche après correctif (un test qui passe confirme le défaut corrigé). Ces deux contrôles seraient scriptables sans modèle.
4. **Deux tirages valent mieux qu'un** : `luna` seul perd 1 à 2 stories entre deux passes. Si un critique externe entre dans le flux, le lancer deux fois et ne retenir que les Important qui reviennent ou qui ont un test qui échoue.
5. **À traiter dans `usine-migration-jira-demo`** (hors du périmètre de T5, faits établis par ce test) : réidentification des jetons préfixés (S1 D1, toujours non corrigée), `ValidationError` brute de `Secrets` (S2 D1), `USINE_RACINE` hors `Secrets` (S2 D2), progression périmée en attente, balayage SM-7 des identifiants avec blancs échappés.

## 8. Fichiers et reproduction

Dossier `tests-pratiques/T5/` : `construire_jeu.py` (jeu de données), `revue.py` (appels OpenRouter, reprise, coût), `executer_tests.py` (filtre, worktrees, exécution, rejeu sur la tête), `classification.py` (classement manuel), `analyse.py` (agrégats vers `analyse.json`), `exploratoire_v0.py`, `voir.py` (lecture des constats), `jeu/` (diffs, specs, revues d'origine), `reponses/`, `reponses_run2/`, `reponses_complement/`, `archive_v0_diff_concatene/`, `tests_extraits/` (les tests des modèles), `execution.json`, `execution_tete.json`.

```
uv run --no-project python construire_jeu.py
uv run --no-project python revue.py                       # reprise automatique, plafond --plafond 6.0
uv run --no-project python revue.py --modeles openai/gpt-6-luna,openai/gpt-6.1-sol --dossier reponses_run2
uv run --no-project python executer_tests.py --lister     # revue des tests et filtre statique
uv run --no-project python executer_tests.py --executer   # un test à la fois, worktree jetable
uv run --no-project python executer_tests.py --tete       # rejeu sur la tête de main
uv run --no-project python executer_tests.py --nettoyer   # supprime les worktrees
uv run --no-project python classification.py && uv run --no-project python analyse.py
```
