# T13 bis : peut-on sauter le cadrage BMAD pour une petite story ?

Test pratique T13 bis de la veille sur les agents de code, suite du constat hors protocole de T13 (`../T13-story-legere/resultats.md`, sections 1 et 8). Mesuré le 25 octobre 2026 de 10 h 12 à 12 h 52, avec le banc de T13 importé sans modification. Coûts : estimation client `total_cost_usd` (abonnement Max, tarifs catalogue). Total engagé : **42,66 $** sur un plafond de 45 $ (cadrages 19,32 $, développements 23,34 $).

## 1. Résultat en bref

- **Réussite** : sans cadrage (D), dev-story réussit autant que le cadrage BMAD complet (A) : **−0,6 point** de tests cachés (51,9 % contre 52,4 %), IC 95 % **[−8,4 ; +7,4]**, sur 22 stories. La borne basse est au-dessus de −10 : **non-infériorité tenue à 10 points**. Elle n'est pas démontrée à 5 points (la puissance ne le permettait pas, voir section 2).
- **Coût** : D coûte **73 % de moins** que A, cadrage compris (0,35 $ contre 1,32 $ par story ; IC [−76 ; −69]). Le développement seul coûte presque pareil (−3,5 %) : tout le gain vient du cadrage supprimé.
- **Robustesse** : même conclusion sur les seuls runs de T13 bis (−0,4 point, IC [−9,4 ; +8,0]) et sans les deux stories à défaut de banc (−0,6, IC [−9,1 ; +8,2]).
- **Richesse de l'entrée** : retirer les critères Given/When/Then de l'entrée (bras D-court) ne change pas la réussite de façon mesurable : **−1,4 point** contre D, IC [−8,9 ; +5,4]. Le cadrage ne se paie donc pas grâce aux critères de l'entrée : il ne se paie pas du tout sur ces stories. Seul signal contraire : sur les 6 entrées **brèves** (un seul critère, < 1 200 caractères), D perd 11,5 points sur A (IC [−23 ; −1]) toutes données confondues, −8,0 (IC [−24 ; +8]) sur les seuls nouveaux runs, sous le seuil d'exclusion fixé (−10).
- **Décision (critère écrit d'avance)** : D est non inférieur à A à 10 points près, pour 73 % de moins. **Pour une petite story dont l'entrée `epics.md` est détaillée, dev-story peut partir directement de l'entrée.** Proposition de règle en section 9.

## 2. Protocole

Le protocole complet est dans `protocole.md`, figé à 10 h 15 avant le premier run (avenant de budget à 10 h 56, sans effet sur le critère). Résumé :

**Bras.** A : cadrage `bmad-build` (étapes clarifier et planifier, sans interaction), Opus 5.5 effort medium, puis développement. D : entrée `epics.md` et interface imposée directement au développement. Dc (D-court) : comme D, entrée réduite à son titre et à sa phrase « As a… I want… So that… ». Développement : Sonnet 5.5 effort medium, même prompt et mêmes outils que T13, 5 $ et 25 min au plus par run. Banc : `t13bis.py` importe `../T13-story-legere/t13.py` et redirige ses chemins ; consignes de cadrage et CLAUDE.md minimaux lus dans le dossier de T13.

**Analyse de puissance** (`puissance.py`, `donnees/puissance.md`, faite sur les seules données de T13). Écart type des écarts D − A par story : 17,6 points ; bruit entre deux runs du même bras (l51) : 14,7 points. Avec 10 stories à deux répétitions et 8 à 12 nouvelles à une répétition, la puissance pour démontrer la non-infériorité, si les bras sont égaux, est de 15 à 18 % à 3 points, 30 à 36 % à 5 points, 76 à 86 % à 10 points. **3 et 5 points étaient hors de portée avec ce budget** (il faudrait environ 90 stories pour 5 points). Marge principale fixée à 10 points, lecture secondaire à 5 points.

**Critère** (section 6 du protocole) : D non inférieur si la borne basse de l'IC 95 % de D − A dépasse −10 points ; D au moins 50 % moins cher ; « fragile » si la robustesse (runs de T13 bis seuls) passe sous −10 ; entrées brèves exclues de la règle si D − A y est sous −10 points sur les runs de T13 bis ; critères de l'entrée déclarés utiles si la borne haute de Dc − D est sous 0.

**Statistique.** Unité : la story (taux et coûts moyennés sur ses répétitions). Bootstrap apparié, 5 000 rééchantillonnages, graine 13. Écarts de taux en points ; coût en ratio des sommes. Les runs A et D de T13 (répétition 1) sont repris tels quels.

## 3. Stories

22 stories de trois dépôts publics (vérifiés par `gh repo view` : PUBLIC), toutes de un à trois fichiers source et moins de ~200 lignes :

- les **10 stories de T13** (l23, l27, l51, l63, l65, u25, u45, u51, u75, w91), corpus copié sans changement, avec une seconde répétition de A et de D ;
- **12 nouvelles stories** repérées par `candidats.py` (liste complète dans `donnees/candidats.md`), validées par `t13bis.py reference` : wavelibrarian l13, l34, l35, l36, l410, l71 ; usine-migration-jira-demo u57, u611, u78 ; service-public-slm-fine-tuning s32, s52, s102 (détail : `protocole.md`, section 3). wavelocalai et wavedevsecops n'ont fourni aucune nouvelle story utilisable (front, scénarios YAML) ; les autres dépôts publics n'ont pas d'`epics.md`.

**Richesse de l'entrée.** Les 22 entrées portent toutes des critères Given/When/Then (« Étant donné / quand / alors » chez service-public-slm-fine-tuning) : la strate « courte, sans critères » n'existe pas dans ces dépôts, le bras Dc la fabrique. Strates sur la longueur (seuil 1 200 caractères) : **détaillée** (16 stories, plusieurs critères) et **brève** (6 stories : u25, u57, u611, u75, u78, w91, souvent un seul critère). La strate brève est presque tout le dépôt usine-migration-jira-demo.

## 4. Résultats par bras

Toutes les exécutions, répétition 1 de T13 comprise (`donnees/analyse.md`, `donnees/agregats.json`).

| Bras | Runs | Stories | Cadrage $ | Tours | Dév. $ | Tours | Durée dév. | **Total $** | **Tests cachés** | 100 % | ruff propre | Hors périmètre |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A cadrage BMAD | 32 | 22 | 0,95 | 24,3 | 0,37 | 23,8 | 240 s | **1,32** | **58,7 %** | 4/32 | 29/30 | 11/32 |
| D sans cadrage | 32 | 22 | 0 | 0 | 0,35 | 23,2 | 211 s | **0,35** | **57,9 %** | 5/32 | 29/30 | 13/32 |
| Dc D-court | 20 | 20 | 0 | 0 | 0,39 | 23,9 | 156 s | **0,39** | **55,6 %** | 2/20 | 19/19 | 6/20 |

Aucun run en erreur ni hors délai. `ruff` n'est pas mesurable pour wavelocalai (w91). Les fichiers hors périmètre sont surtout des fichiers de tests nommés autrement que dans le commit d'origine. Les specs A produites font 9 900 caractères en moyenne (`donnees/specs/`).

### Comparaisons appariées (IC 95 % bootstrap par story)

| Comparaison | Stories | Coût total | Dév. seul | Tests cachés (points) | Mieux / égal / moins bien |
|---|---|---|---|---|---|
| **D − A, toutes les données (critère)** | 22 | **−72,7 %** [−75,9 ; −68,5] | −3,5 % | **−0,6** [−8,4 ; +7,4] | 7 / 8 / 7 |
| D − A, runs de T13 bis seuls (robustesse) | 21 | −72,0 % [−75,6 ; −67,7] | −1,4 % | −0,4 [−9,4 ; +8,0] | 7 / 8 / 6 |
| D − A, sans u57 ni l13 (sensibilité) | 20 | −74,0 % [−76,6 ; −71,2] | −9,8 % | −0,6 [−9,1 ; +8,2] | 7 / 6 / 7 |
| D − A, 10 stories de T13 (2 répétitions) | 10 | −74,7 % [−78,1 ; −70,4] | −9,5 % | −1,3 [−11,5 ; +7,6] | 3 / 4 / 3 |
| D − A, 12 nouvelles stories | 12 | −70,9 % [−76,0 ; −64,4] | +2,0 % | 0,0 [−12,1 ; +13,3] | 4 / 4 / 4 |
| **Dc − D** | 20 | +13,1 % [+3,3 ; +23,0] | +13,1 % | **−1,4** [−8,9 ; +5,4] | 7 / 7 / 6 |
| Dc − A | 20 | −70,6 % [−73,5 ; −67,5] | +2,0 % | −2,1 [−10,6 ; +5,5] | 8 / 5 / 7 |

Le constat de T13 (−2,7 points sur une répétition) se confirme et se resserre : sur les 10 mêmes stories, la seconde répétition donne −1,3 point. La moyenne des tests cachés baisse par rapport à T13 (52 % contre 72 %) parce que les nouvelles stories sont plus dures pour les deux bras (36 % en moyenne).

**Répétabilité.** Sur les 10 stories rejouées, l'écart absolu moyen entre deux runs du même bras est de 6,8 points pour A et 5,8 pour D (variance par run 71 et 50). C'est bien moins que l'estimation de T13 tirée de la seule story l51 (14,7 points d'écart type) : l'analyse de puissance était prudente.

## 5. Par strate de richesse

| Strate | Stories | D − A, toutes données | D − A, runs de T13 bis seuls (confirmatoire) | Dc − D |
|---|---|---|---|---|
| détaillée (≥ 1 200 car.) | 16 | **+3,5** [−5,9 ; +12,7] | +2,6 [−7,5 ; +12,4] | −4,1 [−12,6 ; +3,3] (15) |
| brève (< 1 200 car.) | 6 | **−11,5** [−23,0 ; −0,7] | −8,0 [−24,2 ; +7,6] | +6,5 [−6,5 ; +17,1] (5) |

- Entrées détaillées : D fait au moins aussi bien que A. C'est le cas d'usage de la règle proposée.
- Entrées brèves : A garde un avantage, surtout sur u25 (85 % contre 50 %) et u611 (30 % contre 0 %). Sur les seuls nouveaux runs, l'écart (−8,0) reste au-dessus du seuil d'exclusion fixé (−10) : selon le critère, la règle ne les exclut pas. Mais le signal va dans le même sens sur les deux jeux de données, sur 6 stories d'un seul dépôt presque : je recommande, par prudence et en dehors du critère, de garder le cadrage pour ces entrées.
- Dc − D ne montre pas d'effet des critères de l'entrée, ni sur les détaillées ni sur les brèves. Le seuil de la strate a été choisi après lecture des résultats par story de T13 (voir `protocole.md`, section 4) : sur les données de T13, cette lecture est exploratoire.

## 6. Par story

Taux des tests cachés par répétition ; coût total moyen (dont cadrage pour A).

| Story | Strate | A | D | Dc |
|---|---|---|---|---|
| l13 | détaillée | 0 % ; 0,87 $ (0,66) | 0 % ; 0,20 $ | non joué |
| l23 | détaillée | 100 / 100 % ; 0,82 $ (0,61) | 100 / 100 % ; 0,26 $ | 100 % ; 0,33 $ |
| l27 | détaillée | 89 / 78 % ; 0,99 $ (0,73) | 78 / 78 % ; 0,26 $ | 67 % ; 0,31 $ |
| l34 | détaillée | 71 % ; 1,32 $ (0,92) | 71 % ; 0,41 $ | 71 % ; 0,49 $ |
| l35 | détaillée | 73 % ; 1,65 $ (1,14) | 73 % ; 0,53 $ | 82 % ; 0,62 $ |
| l36 | détaillée | 17 % ; 0,97 $ (0,68) | 67 % ; 0,31 $ | 22 % ; 0,36 $ |
| l410 | détaillée | 17 % ; 0,81 $ (0,58) | 33 % ; 0,22 $ | 33 % ; 0,26 $ |
| l51 | détaillée | 57 / 64 % ; 1,05 $ (0,82) | 71 / 71 % ; 0,28 $ | 71 % ; 0,33 $ |
| l63 | détaillée | 88 / 88 % ; 1,31 $ (1,05) | 75 / 62 % ; 0,40 $ | 75 % ; 0,42 $ |
| l65 | détaillée | 62 / 88 % ; 1,35 $ (0,88) | 88 / 100 % ; 0,50 $ | 75 % ; 0,51 $ |
| l71 | détaillée | 57 % ; 1,36 $ (0,85) | 71 % ; 0,48 $ | 71 % ; 0,49 $ |
| s102 | détaillée | 0 % ; 1,50 $ (0,96) | 10 % ; 0,29 $ | 30 % ; 0,49 $ |
| s32 | détaillée | 56 % ; 1,60 $ (1,24) | 22 % ; 0,37 $ | 0 % ; 0,39 $ |
| s52 | détaillée | 83 % ; 0,90 $ (0,59) | 60 % ; 0,20 $ | 77 % ; 0,22 $ |
| u25 | brève | 85 / 85 % ; 1,50 $ (0,92) | 54 / 46 % ; 0,27 $ | 69 % ; 0,32 $ |
| u45 | détaillée | 100 / 100 % ; 2,23 $ (1,71) | 100 / 100 % ; 0,43 $ | 100 % ; 0,48 $ |
| u51 | détaillée | 50 / 50 % ; 2,18 $ (1,58) | 67 / 67 % ; 0,51 $ | 50 % ; 0,55 $ |
| u57 | brève | 0 % ; 1,15 $ (0,93) | 0 % ; 0,69 $ | non joué |
| u611 | brève | 30 % ; 1,23 $ (1,02) | 0 % ; 0,32 $ | 0 % ; 0,22 $ |
| u75 | brève | 62 / 38 % ; 1,14 $ (0,75) | 38 / 62 % ; 0,23 $ | 62 % ; 0,31 $ |
| u78 | brève | 26 % ; 1,49 $ (1,02) | 22 % ; 0,30 $ | 39 % ; 0,49 $ |
| w91 | brève | 33 / 33 % ; 1,10 $ (0,81) | 33 / 33 % ; 0,33 $ | 17 % ; 0,20 $ |

Lecture des échecs (patches et sorties pytest dans `donnees/patches/` et `donnees/runs.jsonl`) : les tests cachés ratés portent surtout sur la forme exacte de l'API (signature d'un faux tokenizer en s102, paramètres de `score_similarite` en u611, constructeur de `BacASable` en s32) ou sur des cas ajoutés en revue. Ni l'entrée de `epics.md` ni la spec A ne les fixent : la spec A les tranche parfois mieux (s32 : 56 % contre 22 %), parfois moins bien (l36 : 17 % contre 67 %).

## 7. Coûts

| Étape | Runs | Coût | Moyenne |
|---|---|---|---|
| Cadrages A (Opus medium) | 21 | 19,32 $ | 0,92 $ (de 0,59 à 1,51) |
| Développements A | 21 | 7,68 $ | 0,37 $ |
| Développements D | 22 | 7,87 $ | 0,36 $ |
| Développements Dc | 20 | 7,79 $ | 0,39 $ |
| **Total T13 bis** | 84 | **42,66 $** | |

Par lot : lot 1 (seconde répétition) 15,70 $ ; lot 2 (nouvelles stories, A et D) 19,17 $ ; lot 3 (Dc) 7,79 $. Le cadrage pèse 70 % du coût de A. Dc coûte 13 % de plus que D en développement : sans critères, l'agent explore davantage le dépôt.

## 8. Limites

1. **Tests cachés à plafond bas.** Ils contiennent des cas ajoutés par la revue et des détails d'API ; seuls 4 runs A sur 32 et 5 runs D sur 32 passent tout. Le banc mesure la conformité à l'implémentation d'origine, pas la qualité absolue. Il ne mesure pas non plus ce que rattraperaient le second avis et le reviewer de la chaîne agent-cost-kit.
2. **Deux défauts de banc** (constatés pendant le lot 2, avant le lot 3) : en u57, les tests importent `outils.verifier_rejeu`, hors du paquet `usine`, que l'interface imposée ne nomme pas ; en l13, la fixture des tests lit un attribut privé (`registry._decouvert`). Les deux bras font 0 %. Ces stories restent dans le critère, comme prévu ; l'analyse sans elles donne le même résultat (−0,6, IC [−9,1 ; +8,2]).
3. **Marge de 10 points.** C'est une marge large : D pourrait réussir jusqu'à 8 points de moins que A sans que ce test le voie. La lecture à 5 points n'est pas tenue (borne basse −8,4).
4. **Pas d'entrée vraiment courte.** Toutes les entrées des dépôts ont des critères ; Dc garde l'interface imposée (noms de modules et de classes), donc l'entrée courte n'est pas nue. Le cadrage sur une entrée courte (« A-court ») n'a pas été joué : on ne sait pas si le cadrage aiderait une story mal décrite.
5. **Strates confondues avec le dépôt.** La strate brève est presque toute usine-migration-jira-demo ; son seuil a été choisi après lecture de T13.
6. **Un seul auteur, trois dépôts, une chaîne BMAD** : les entrées `epics.md` sont plus riches qu'une story ordinaire. Un seul modèle de développement (Sonnet 5.5 medium).
7. **Mesures annexes.** `num_turns` est faussé quand l'agent attend une commande en arrière-plan (u78-A1 : 2 tours déclarés, 21 appels dans la transcription). Un agent (u78-A1) a lancé de lui-même la suite complète du dépôt dans son dossier jetable, malgré la consigne du CLAUDE.md minimal.

## 9. Décision

Selon le critère écrit avant les runs :

- Borne basse de D − A au-dessus de −10 points : **oui** (−8,4).
- D au moins 50 % moins cher que A : **oui** (−72,7 %).
- Robustesse sur les runs de T13 bis seuls : **tenue** (−9,4) ; décision non fragile.
- Lecture à 5 points : non tenue (puissance insuffisante, ce n'est pas une preuve d'infériorité).
- Entrées brèves : −8,0 points sur les nouveaux runs, au-dessus du seuil d'exclusion (−10) : pas d'exclusion formelle.
- Critères de l'entrée (Dc − D) : effet non démontré (−1,4, IC [−8,9 ; +5,4]).

**D est non inférieur à A à 10 points près, pour 73 % de moins. Pour une petite story à l'entrée détaillée, le cadrage BMAD complet peut être sauté.**

**Proposition pour la chaîne agent-cost-kit (non mise en œuvre)** : une règle de routage avant dev-story.

> Story petite (au plus 3 fichiers source attendus, environ 200 lignes) **et** entrée de `epics.md` avec au moins deux critères Given/When/Then (ou « Étant donné / quand / alors ») et les noms publics à créer : `dev-story` directement sur l'entrée d'epics, sans étape « clarifier / planifier » de `bmad-build`. `second-avis` puis `reviewer` inchangés. Sinon (entrée brève à un seul critère, story transverse, plus de 3 fichiers) : cadrage BMAD comme aujourd'hui.

Gain attendu : environ 0,95 $ par petite story (1,32 $ contre 0,35 $ avant revue), soit environ 70 % du coût de cadrage et de développement. La condition « au moins deux critères » est une précaution tirée de la strate brève (−8 à −12 points), pas une exigence démontrée par le critère. À suivre en production : taux de retour du reviewer sur les stories routées en direct.

## 10. Reproduire

Depuis `tests-pratiques/T13bis-sans-cadrage/` (un seul processus à la fois ; `-I` pour les scripts autonomes) :

```
uv run --no-project python -I candidats.py > donnees/candidats.md        # repérage des petites stories
uv run --no-project python -I puissance.py > donnees/puissance.md        # analyse de puissance (données de T13)
uv run --no-project python -I t13bis.py copier l23 l27 l51 l63 l65 u25 u45 u51 u75 w91
uv run --no-project python -I t13bis.py extraire tout                    # nouvelles stories de stories13bis.json
uv run --no-project python -I t13bis.py reference l35 u611 s52 l71 u78 l34 s102 l36 u57 l410 l13 s32
uv run --no-project python -I t13bis.py lot plan-lot1.json --max 2 --plafond 33.5
uv run --no-project python -I t13bis.py lot plan-lot2.json --max 2 --plafond 37.5   # deux passes (s32 sautée puis jouée)
uv run --no-project python -I t13bis.py lot plan-lot3.json --max 2 --plafond 45
uv run --no-project python -I analyse.py > donnees/analyse.md
uv run --no-project python -I ../banc-rejeu/anonymiser.py "donnees/*.jsonl" "donnees/brut/*.json" ...
uv run --no-project python -I anonymiser_complement.py "donnees/*.jsonl" "donnees/brut/*.json" ...
```

Fichiers : `protocole.md` (figé avant les runs), `t13bis.py` (banc, importe `../T13-story-legere/t13.py`), `candidats.py`, `puissance.py`, `analyse.py`, `anonymiser_complement.py` (chemins à quatre barres et fragments que `anonymiser.py` ne voit pas), `stories13bis.json`, `plan-lot1.json` à `plan-lot3.json` (u57 et l13 retirés du lot 3), `corpus/<id>/` (meta, entrée `epics.md`, `epics_court.md`, interface, tests cachés), `donnees/` (`runs.jsonl`, `cadrages.jsonl`, `specs/` produites par A, `patches/`, `brut/` JSON de sortie de `claude -p`, journaux de lots, `puissance.md`, `analyse.md`, `agregats.json`, `candidats.md`). Aucune transcription de session. Chemins locaux anonymisés.

**Écarts au protocole** : plafond relevé de 40 à 45 $ (avenant de 10 h 56, critère inchangé) ; u57 et l13 retirés du lot 3 (défaut de banc constaté avant le lot 3) et analyse de sensibilité sans elles ajoutée ; s32 sautée au lot 2 par la réservation de budget d'un run encore en cours, puis jouée dans une seconde passe sous le même plafond ; lecture par strate sur les runs de T13 bis seuls, prévue au protocole, ajoutée au script après le lot 2.

## 11. Synthèse

- Sans cadrage, dev-story réussit autant que le cadrage BMAD complet : −0,6 point de tests cachés, IC [−8,4 ; +7,4], sur 22 petites stories.
- D coûte 73 % de moins (0,35 $ contre 1,32 $ par story) ; tout le gain vient du cadrage supprimé.
- Non-infériorité tenue à 10 points (marge atteignable avec le budget) ; 3 et 5 points étaient hors de portée.
- Retirer les critères de l'entrée ne change rien de mesurable (−1,4 point) ; seules les entrées brèves montrent un avantage de A (−8 à −12 points, non concluant).
- Décision : router les petites stories à l'entrée détaillée directement vers dev-story ; garder le cadrage pour les entrées brèves par prudence. 42,66 $ engagés sur 45 $.
