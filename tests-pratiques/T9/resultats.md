# T9 : la spec d'une story prédit-elle un dérapage du développement ? (Jev, LLM bon marché, heuristique)

Test pratique T9 de la veille sur les agents de code (2026-10-24). Question : un modèle de décision (Jev, de TypeSafe) prédit-il, à partir de la seule spec d'une story, si le développement par `dev-story` va déraper ? Tous les chiffres sont des agrégats ; aucun texte de spec n'est recopié ici ni écrit dans le dépôt (les specs restent dans le dossier temporaire de la session).

**Conclusion courte.** Jev est appelable (via OpenRouter, sans clé TypeSafe) et presque gratuit, mais aucun bras ne prédit le dérapage : AUC de 0,47 à 0,59 pour l'étiquette principale (seuil de la veille : > 0,7 et +0,05 sur l'heuristique), y compris Jev (0,56, IC à 95 % de 0,43 à 0,69). Décision proposée : ne rien brancher dans `agent-cost-kit`.

## 1. Comment appeler Jev

Jev est un modèle de « décision » (famille « System One » de TypeSafe) : pour un état et des questions fermées, il rend une réponse typée avec une probabilité, pas du texte. Trois primitives : `noul` (oui/non, probabilité entre 0 et 1), `choice` (un choix parmi des options, avec probabilités) et `score` (échelle ordonnée). Entrée : texte seulement (strings, objets JSON). Tarif : 0,042 $ par million de tokens d'entrée, sortie gratuite.

| Voie | Appel | Accès |
|---|---|---|
| API TypeSafe native | `POST https://api.typesafe.ai/v1/systemone`, en-tête `Authorization: Bearer <clé TypeSafe>`, champs `model` (`jev-latest`, qui pointe sur `jev-1.14.0` depuis le 2026-10-14 ; `jev-1.13.0`), `state`, `questions` | Exige une clé TypeSafe. Non essayée : elle n'est pas dans l'environnement, et la doc ne dit pas comment l'obtenir ni si une passerelle est ouverte à tous. |
| OpenRouter | `POST https://openrouter.ai/api/alpha/decisions`, mêmes champs `model`, `state`, `questions`, avec la clé OpenRouter ; modèles `~typesafe/jev-latest` (alias, a répondu `typesafe/jev-1.14-20261014`) et `typesafe/jev-1.13` (a répondu `typesafe/jev-1.13-20260917`) | Fonctionne avec la clé OpenRouter existante. Réponse : `answers.<question>.noul` (probabilité de oui), `usage.input_tokens`, `usage.cost`. |

Points qui expliquent l'écart avec le constat de départ (« le modèle n'est pas listé ») :
- `GET /api/v1/models` ne montre que `typesafe/jev-router` (un routeur de modèles de chat, hors sujet ici). Jev lui-même est un modèle de sortie `decisions` : il n'apparaît pas dans le catalogue de chat mais répond sur `GET /api/v1/models/typesafe/jev-1.13/endpoints` et `~typesafe/jev-latest/endpoints` (avec une latence médiane publiée de 85 ms sur plus de 2 millions de requêtes).
- Sur `/api/v1/chat/completions`, OpenRouter refuse ces modèles (« is a decisions model ... Use the /api/alpha/decisions endpoint instead ») : `response_format`, `structured_outputs` et `logprobs` n'ont pas de sens ici (`supported_parameters` vide) ; la probabilité est la sortie native.
- `typesafe/jev-latest` sans tilde n'est pas un identifiant valide ; l'alias est `~typesafe/jev-latest`.
- Sources : doc TypeSafe (`docs.typesafe.ai`, pages `concepts/system-one`, `api`, `models`, `primitives`), tutoriel OpenRouter sur Jev, réponses de l'API OpenRouter aux sondes (`sonde_jev.py`, quatre appels refusés, coût nul). L'article de Linas Beliūnas est en grande partie payant : son passage technique n'a pas pu être lu.

Il n'a donc pas fallu s'arrêter au constat « seul `jev-router` est accessible » : Jev est testé en mode décision.

## 2. Données

**Périmètre.** Dépôts publics de la liste, pour lesquels le détail par agent de T1 contient un numéro de story : `wavedevsecops`, `wavelocalai`, `usine-migration-jira-demo`. Les autres dépôts publics n'apportent rien d'exploitable : `wavestack` n'a aucun agent `dev-story` dans la fenêtre de 45 jours de T1, `slm-quality-bench` et `agent-cost-kit` n'ont qu'une story chacun, sans section dans un `epics.md` (comptées parmi les écartées) ; les dépôts privés (`wavelibrarian`, `service-public-slm-fine-tuning`) sont exclus ; les worktrees `usine-lanes-t1-*` sont des rejeux expérimentaux, écartés.

**Volume.** 133 stories publiques avec numéro (351 agents `dev-story` au total sur 45 jours, tous dépôts), 8 écartées (6 absentes de `epics.md` à la date du développement, 2 sans version de `epics.md` antérieure) : **125 stories étiquetées**. Répartition : `wavedevsecops` 61, `wavelocalai` 54, `usine-migration-jira-demo` 10. Tous les développements datent du 2026-10-13 au 2026-10-19. Médiane des appels par story : 53 (`wavedevsecops`), 87 (`wavelocalai`), 35 (`usine-migration-jira-demo`) ; reprises regroupées par story.

**Étiquette principale « dérapage » (critère de T1).** Somme des appels propres des agents `dev-story` de la story supérieure à 2 fois la médiane de son dépôt (médiane des sommes par story) : **9 stories sur 125, soit 7,2 %** (4 + 2 + 3 par dépôt). Variantes, déclarées d'avance comme exploratoires parce que 9 positifs donnent peu de puissance :
- `derapage_par_agent` : le plus long agent de la story dépasse 2 fois la médiane par agent du dépôt (la définition exacte de T1) : 12 positives (9,6 %) ;
- `haut20` : la story est parmi les 20 % les plus longues de son dépôt : 25 positives.

**Étiquette secondaire.** La revue consigne au moins un constat de sévérité medium ou high non rejeté (lu dans la section « Revue » des fichiers de story, ou le journal de triage de l'usine) : 91 positives sur 124 stories lisibles (73 %) ; une étiquette si fréquente prédit mal par construction.

**Spec envoyée et anti-fuite.** Les fichiers de story d'`implementation-artifacts` sont écrits ou complétés pendant le développement (sections « Livré », « Revue », « Fichiers », « Auto Run Result » ; le premier commit de ces fichiers contient déjà ces sections) : ils ne conviennent pas. La spec écrite avant le développement est la section « Story X.Y » de `_bmad-output/planning-artifacts/epics.md` (titre, énoncé « en tant que », décisions d'architecture à respecter, critères d'acceptation). Pour chaque story on prend la version du fichier au dernier commit antérieur au début du premier agent (minuit UTC du jour) : 60 stories avec une version strictement antérieure, 65 avec la version de la fin du jour de démarrage (la spec a été commitée le jour même). Aucune ligne « post-développement » n'a été retirée (les sections d'`epics.md` n'en contiennent pas ; le nettoyage est néanmoins appliqué par le script). Longueur médiane d'une spec : 1 700 caractères (de 540 à 3 200), 4 scénarios « Étant donné / Given » (de 1 à 8), 1 fichier cité (de 0 à 15). Le prompt donne la définition du dérapage et les taux de base (1 sur 14 ; 3 sur 4), qui sont des priors globaux et pas des informations sur la story.

## 3. Protocole

Même question fermée, même entrée (la section de spec), quatre familles de bras :

1. **Heuristique sans modèle**, sur longueur (logarithme des caractères), nombre de scénarios, de clauses, de fichiers cités et de références `AD-n`, centrées et réduites par dépôt (sans étiquette). Deux versions : régression logistique (L2, C = 1) en validation croisée stratifiée 5 plis répétée 10 fois (probabilités hors échantillon moyennées) ; seuil sur la seule longueur (aucun apprentissage). La meilleure des deux sert de référence (comparaison prudente).
2. **Jev en mode décision**, deux questions `noul` indépendantes (dérapage ; défaut de revue) dans une seule requête, `state = {story_spec}`. Principal : `~typesafe/jev-latest` (1,14) ; secondaire : `typesafe/jev-1.13`. Une exécution chacun (déterministe, même état = même réponse).
3. **`openai/gpt-6-luna`** et **`xiaomi/mimo-v2.6-pro`** via `chat/completions`, sortie structurée JSON (schéma strict : `oui`/`non` plus `probabilite_oui` pour chaque question), effort de raisonnement bas, un prompt (la même consigne que Jev). Deux exécutions chacun pour mesurer le bruit ; la première est la mesure principale, la moyenne des deux est donnée en complément.

Mesures : AUC (IC à 95 % par bootstrap stratifié, 3 000 tirages), précision et rappel avec au plus 20 % d'alertes (les ex æquo ne sont pas séparés ; 25 alertes au plus sur 125), coût par story (champ `usage.cost`), latence mesurée côté client (2 appels en parallèle pour les LLM, séquentiel pour Jev). AUC « intra-dépôt » : scores ramenés à leur rang dans chaque dépôt, pour retirer les écarts de niveau entre dépôts. Écart d'AUC avec la référence et son IC par bootstrap apparié. Critère de la veille : AUC > 0,7 et au moins 0,05 au-dessus de l'heuristique.

## 4. Résultats

### Étiquette principale : dérapage (9 positives sur 125, taux de base 7,2 %)

| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes | Vrais positifs | Précision | Rappel | Écart à la référence [IC] |
|---|---|---|---|---|---|---|---|
| Heuristique : longueur (référence) | 0,584 [0,44 ; 0,73] | 0,589 | 25 | 1 | 4 % | 11 % | |
| Heuristique : régression logistique | 0,376 (CV) | 0,402 | 25 | 0 | 0 % | 0 % | |
| Jev latest (1,14) | 0,563 [0,43 ; 0,69] | 0,638 | 21 | 1 | 5 % | 11 % | −0,02 [−0,20 ; +0,15] |
| Jev 1,13 | 0,496 [0,32 ; 0,68] | 0,587 | 25 | 2 | 8 % | 22 % | −0,09 [−0,29 ; +0,11] |
| gpt-6-luna, exécution 1 / 2 / moyenne | 0,521 / 0,525 / 0,522 | 0,648 / 0,654 / 0,658 | 23 / 21 / 25 | 2 / 1 / 1 | 9 % / 5 % / 4 % | 22 % / 11 % / 11 % | −0,06 [−0,29 ; +0,16] (exéc. 1) |
| mimo-v2.6-pro, exécution 1 / 2 / moyenne | 0,473 / 0,568 / 0,488 | 0,467 / 0,569 / 0,516 | 23 / 25 / 24 | 2 / 2 / 2 | 9 % / 8 % / 8 % | 22 % / 22 % / 22 % | −0,11 [−0,26 ; +0,05] (exéc. 1) |

Des alertes tirées au hasard (25 stories) attraperaient 1,8 positive en moyenne : tous les bras sont à ce niveau (0 à 2 vrais positifs). **Aucun bras ne satisfait le critère.** La régression logistique est sous 0,5 en validation croisée (surapprentissage avec 9 positifs), d'où le choix de la longueur seule comme référence.

### Étiquettes exploratoires et secondaire (AUC, première exécution)

| Bras | `derapage_par_agent` (12 pos.) | `haut20` (25 pos.) | Défaut de revue (91/124) |
|---|---|---|---|
| Heuristique : longueur | 0,564 | 0,657 [0,54 ; 0,77] | 0,440 |
| Heuristique : régression logistique | 0,397 | 0,605 | 0,499 |
| Jev latest | 0,597 | 0,640 [0,53 ; 0,74] | 0,492 |
| Jev 1,13 | 0,567 | 0,595 | 0,520 |
| gpt-6-luna | 0,642 (2e exéc. 0,574) | 0,634 (2e exéc. 0,602) | 0,495 |
| mimo-v2.6-pro | 0,564 (2e exéc. 0,508) | 0,544 (2e exéc. 0,543) | 0,457 |

Sur `haut20`, qui a le plus de positifs, les bras de modèles ne battent pas la longueur de la spec (écart de Jev latest : −0,02, IC −0,14 à +0,12). Aucun bras ne prédit le défaut de revue (AUC de 0,43 à 0,52).

### Signal continu et diagnostics

- Corrélation de rang entre le score et le nombre d'appels : luna 0,43 (0,30 à l'intérieur de chaque dépôt), Jev latest 0,28 (0,14), mimo 0,20 (0,05) ; la longueur de la spec seule : 0,45 (0,43 intra-dépôt). Les scores des modèles suivent surtout la longueur de la spec (luna 0,70, Jev 0,56, mimo 0,34) : ils ne voient pas davantage que ce que l'heuristique voit.
- Bruit : deux exécutions de gpt-6-luna ont une corrélation de rang de 0,76 (écart moyen de 0,12 sur la probabilité) ; mimo-v2.6-pro 0,46, c'est-à-dire presque aucune reproductibilité (AUC de 0,47 puis 0,57 sur les mêmes stories). Jev est déterministe.
- Calibration : malgré les taux de base donnés, la probabilité moyenne de dérapage est de 0,32 pour Jev latest (0,38 pour 1,13), 0,38 pour luna (59 réponses « oui » sur 125) et 0,19 pour mimo, contre 7 % observé : seuls les rangs sont utilisables, pas les probabilités.
- Sensibilité à la version d'`epics.md` : sur les 60 stories à version strictement antérieure (17 positives en `haut20`), AUC de la longueur 0,73, de Jev latest 0,71, de luna 0,69, de mimo 0,53 : même ordre que sur l'ensemble, dans le bruit.

### Coût et latence (125 stories)

| Bras | Tokens d'entrée par story | Coût par story | Coût du jeu | Latence médiane / p90 |
|---|---|---|---|---|
| Jev latest ou 1,13 | environ 1 350 | 0,000057 $ | 0,007 $ | 0,25 s / 0,29 s |
| gpt-6-luna (effort bas) | environ 875 + 146 de sortie | 0,00015 $ | 0,019 $ par exécution | 3,0 s / 3,8 s |
| mimo-v2.6-pro | environ 860 + 890 de sortie (raisonnement) | 0,00099 $ | 0,124 $ par exécution | 16,8 s / 35 s |

Dépense totale du test : **0,39 $** sur 3 $ (`budget.json` ; inclut deux exécutions de mimo lancées par erreur en double, interrompues, sans effet sur les résultats). Coût de l'extraction des étiquettes : un passage de `T1/analyse.py` (33 s, lecture seule). Aucune charge locale notable (scripts séquentiels ou 2 fils, pas d'Ollama ni de GPU).

## 5. Limites

1. **Puissance faible.** 9 positifs : l'IC à 95 % d'une AUC est de ±0,15. Le test ne peut confirmer qu'une AUC supérieure à 0,75 ; il ne prouve pas l'absence de tout signal. Mais les estimations ponctuelles vont de 0,47 à 0,60 et la borne haute de Jev latest sur l'étiquette principale (0,69) reste sous le seuil de 0,7.
2. **Une seule source de données** : un auteur, trois dépôts, une semaine de développement (2026-10-13 au 19), une chaîne d'agents (`dev-story` surtout sur Sonnet), des specs en français ou en anglais de forme proche. Pas de généralisation à d'autres équipes ou outils.
3. **Étiquette bruitée.** Le nombre d'appels dépend de la spec mais aussi des reprises, des attentes de CI, du parallélisme et des échecs d'intégration entre stories parallèles ; le numéro de story est lu par expression régulière dans la description de l'agent (8 stories écartées, quelques reprises mal rattachées possibles). 7 % de positifs est une définition par rapport à la médiane, pas un échec avéré.
4. **La spec testée est la section d'`epics.md`**, pas le fichier de story complet que lit `dev-story` (contexte d'architecture, notes de conception, tâches) : un modèle qui aurait accès à tout ce contexte pourrait mieux faire. Le test répond à « la spec courte seule », comme demandé, pas à « le contexte complet ».
5. **Un prompt par bras**, une formulation de question pour Jev, effort de raisonnement bas pour les LLM, pas de réglage de seuil propre à Jev (la doc recommande de figer la version pour garder des seuils stables ; ici la même question est posée à deux versions). Une autre formulation (par exemple un score ordonné) n'est pas exclue, mais choisir la meilleure après coup sur 9 positifs serait du surapprentissage.
6. **Latence des LLM** mesurée avec 2 appels simultanés et des nouvelles tentatives sur erreur 429 (une partie de la première série de gpt-6-luna a dû être rejouée) : ordre de grandeur seulement.
7. La version « du jour » d'`epics.md` pour 65 stories peut contenir des retouches faites après le début du développement ; l'écart avec les 60 stories à version antérieure est dans le bruit.
8. Le test ne mesure pas directement le choix de modèle (Sonnet ou Opus) : il suppose qu'un signal de risque serait le préalable.

## 6. Décision proposée

- **Ne pas brancher Jev, ni gpt-6-luna, ni mimo-v2.6-pro dans `agent-cost-kit`** comme alerte de dérapage ni comme sélecteur de modèle : aucun n'atteint 0,7 ni ne bat la longueur de la spec de 0,05 (meilleur écart : −0,02). Leur score reflète surtout la longueur de la spec.
- Garder l'alerte déjà proposée par T1, **observée et non prédite** : notifier l'orchestrateur quand l'agent dépasse 2 fois la médiane d'appels du dépôt, avec décision manuelle.
- Jev reste intéressant pour d'autres usages de tri de texte (coût de 0,00006 $ par appel, 0,25 s, sortie typée) mais il ne sait pas ici prédire une dynamique d'exécution à partir d'un énoncé court.
- **Refaire le test si** : (a) on dispose d'au moins 40 positifs (par exemple après deux ou trois épics de plus, ou en regroupant plus de dépôts) ; (b) on lui donne un contexte plus riche et écrit avant le développement (fichier de story avec tâches et fichiers à toucher, quand l'agent de création de story le produit) ; (c) on pose une question plus proche de ce que la spec détermine (nombre de fichiers touchés, présence d'un contrat partagé) plutôt que le total d'appels. Coût d'un nouvel essai : moins de 0,50 $.

## 7. Reproduire

Depuis `tests-pratiques/T9` (un seul processus à la fois ; la clé OpenRouter est lue par `cle.py` dans l'environnement ou le registre utilisateur, jamais affichée ni écrite) :

```
uv run --no-project python -I ../T1/analyse.py --out <hors depot>/agregats.json --detail-dir <hors depot>
uv run --no-project python construire_donnees.py --agents <hors depot>/q6_agents.json --out-textes <hors depot>/textes.json
uv run --no-project python scorer.py --bras jev --modele "~typesafe/jev-latest" --textes <hors depot>/textes.json --out scores_jev_latest.json
uv run --no-project python scorer.py --bras jev --modele typesafe/jev-1.13 --textes <hors depot>/textes.json --out scores_jev_1_13.json
uv run --no-project python scorer.py --bras llm --modele openai/gpt-6-luna --textes <hors depot>/textes.json --out scores_luna_r1.json --fils 2
uv run --no-project python scorer.py --bras llm --modele xiaomi/mimo-v2.6-pro --textes <hors depot>/textes.json --out scores_mimo_r1.json --fils 2 --max-tokens 6000
uv run --no-project --with numpy --with scikit-learn python analyse.py
```

Fichiers : `cle.py` (lecture de la clé), `sonde_jev.py` (sondes d'accès), `construire_donnees.py`, `scorer.py`, `analyse.py` (les scripts propres au dépôt se lancent sans `-I`, car ils importent `cle.py` voisin), `etiquettes.csv` (clé de story, étiquettes, caractéristiques numériques : aucun texte), `scores_*.json` (probabilités, coûts, latences : aucun texte), `resultats.json` (agrégats de ce rapport), `budget.json` (cumul des coûts).
