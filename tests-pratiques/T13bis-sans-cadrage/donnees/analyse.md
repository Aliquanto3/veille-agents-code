## Par bras (toutes les exécutions, T13 répétition 1 comprise)

| Bras | runs | stories | cadrage $ | tours | dév. $ | tours | s | total $ | tests cachés | 100 % | ruff propre | hors périmètre | erreurs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A cadrage BMAD | 32 | 22 | 0.95 | 24.3 | 0.37 | 23.8 | 240 | 1.32 | 58.7 % | 4/32 | 29/30 | 11/32 | 0 |
| D sans cadrage | 32 | 22 | 0.00 | 0.0 | 0.35 | 23.2 | 211 | 0.35 | 57.9 % | 5/32 | 29/30 | 13/32 | 0 |
| D-court | 20 | 20 | 0.00 | 0.0 | 0.39 | 23.9 | 156 | 0.39 | 55.6 % | 2/20 | 19/19 | 6/20 | 0 |

## Comparaisons appariées (IC 95 % bootstrap par story)

- D − A, toutes les données (critère principal) : 22 stories | coût -72.7 % [-75.9 ; -68.5] (dév. seul -3.5 %) | taux 52.4 % contre 51.9 % : **-0.6 points** [-8.4 ; +7.4] | mieux/égal/moins bien 7/8/7
- D − A, runs de T13 bis seulement (robustesse) : 21 stories | coût -72.0 % [-75.6 ; -67.7] (dév. seul -1.4 %) | taux 51.8 % contre 51.4 % : **-0.4 points** [-9.4 ; +8.0] | mieux/égal/moins bien 7/8/6
- D − A, sans u57 ni l13 (défaut de banc, sensibilité) : 20 stories | coût -74.0 % [-76.6 ; -71.2] (dév. seul -9.8 %) | taux 57.7 % contre 57.1 % : **-0.6 points** [-9.1 ; +8.2] | mieux/égal/moins bien 7/6/7
- D − A, 10 stories de T13 (2 répétitions) : 10 stories | coût -74.7 % [-78.1 ; -70.4] (dév. seul -9.5 %) | taux 72.5 % contre 71.2 % : **-1.3 points** [-11.5 ; +7.6] | mieux/égal/moins bien 3/4/3
- D − A, nouvelles stories : 12 stories | coût -70.9 % [-76.0 ; -64.4] (dév. seul +2.0 %) | taux 35.8 % contre 35.8 % : **+0.0 points** [-12.1 ; +13.3] | mieux/égal/moins bien 4/4/4
- D-court − D : 20 stories | coût +13.1 % [+3.3 ; +23.0] (dév. seul +13.1 %) | taux 57.1 % contre 55.6 % : **-1.4 points** [-8.9 ; +5.4] | mieux/égal/moins bien 7/7/6
- D-court − A : 20 stories | coût -70.6 % [-73.5 ; -67.5] (dév. seul +2.0 %) | taux 57.7 % contre 55.6 % : **-2.1 points** [-10.6 ; +5.5] | mieux/égal/moins bien 8/5/7

## Par strate de richesse de l'entrée

- détaillée (16 stories) : D − A : 16 stories | coût -73.0 % [-75.8 ; -70.0] (dév. seul -4.6 %) | taux 58.1 % contre 61.6 % : **+3.5 points** [-5.9 ; +12.7] | mieux/égal/moins bien 7/5/4 ; D − A sur les runs de T13 bis seuls (confirmatoire) : 15 stories | coût -72.0 % [-74.7 ; -69.1] (dév. seul -2.0 %) | taux 58.4 % contre 61.0 % : **+2.6 points** [-7.5 ; +12.4] | mieux/égal/moins bien 6/6/3 ; D-court − D : 15 stories | coût +14.9 % [+9.1 ; +23.0] (dév. seul +14.9 %) | taux 65.8 % contre 61.7 % : **-4.1 points** [-12.6 ; +3.3] | mieux/égal/moins bien 4/6/5
- brève (6 stories) : D − A : 6 stories | coût -71.8 % [-79.9 ; -58.3] (dév. seul -0.5 %) | taux 37.3 % contre 25.8 % : **-11.5 points** [-23.0 ; -0.7] | mieux/égal/moins bien 0/3/3 ; D − A sur les runs de T13 bis seuls (confirmatoire) : 6 stories | coût -71.8 % [-81.2 ; -58.2] (dév. seul +0.2 %) | taux 35.3 % contre 27.3 % : **-8.0 points** [-24.2 ; +7.6] | mieux/égal/moins bien 1/2/3 ; D-court − D : 5 stories | coût +6.1 % [-26.5 ; +43.4] (dév. seul +6.1 %) | taux 31.0 % contre 37.5 % : **+6.5 points** [-6.5 ; +17.1] | mieux/égal/moins bien 3/1/1

## Répétabilité (stories à 2 répétitions)

- A : 10 stories, écart absolu moyen entre répétitions 6.8 points, variance par run 71
- D : 10 stories, écart absolu moyen entre répétitions 5.8 points, variance par run 50

## Par story (taux des tests cachés par répétition ; coût total moyen, dont cadrage)

| Story | Richesse | A | D | D-court |
|---|---|---|---|---|
| l13 | détaillée | 0 % ; 0.87 $ (0.66) | 0 % ; 0.20 $ | - |
| l23 | détaillée | 100 % / 100 % ; 0.82 $ (0.61) | 100 % / 100 % ; 0.26 $ | 100 % ; 0.33 $ |
| l27 | détaillée | 89 % / 78 % ; 0.99 $ (0.73) | 78 % / 78 % ; 0.26 $ | 67 % ; 0.31 $ |
| l34 | détaillée | 71 % ; 1.32 $ (0.92) | 71 % ; 0.41 $ | 71 % ; 0.49 $ |
| l35 | détaillée | 73 % ; 1.65 $ (1.14) | 73 % ; 0.53 $ | 82 % ; 0.62 $ |
| l36 | détaillée | 17 % ; 0.97 $ (0.68) | 67 % ; 0.31 $ | 22 % ; 0.36 $ |
| l410 | détaillée | 17 % ; 0.81 $ (0.58) | 33 % ; 0.22 $ | 33 % ; 0.26 $ |
| l51 | détaillée | 57 % / 64 % ; 1.05 $ (0.82) | 71 % / 71 % ; 0.28 $ | 71 % ; 0.33 $ |
| l63 | détaillée | 88 % / 88 % ; 1.31 $ (1.05) | 75 % / 62 % ; 0.40 $ | 75 % ; 0.42 $ |
| l65 | détaillée | 62 % / 88 % ; 1.35 $ (0.88) | 88 % / 100 % ; 0.50 $ | 75 % ; 0.51 $ |
| l71 | détaillée | 57 % ; 1.36 $ (0.85) | 71 % ; 0.48 $ | 71 % ; 0.49 $ |
| s102 | détaillée | 0 % ; 1.50 $ (0.96) | 10 % ; 0.29 $ | 30 % ; 0.49 $ |
| s32 | détaillée | 56 % ; 1.60 $ (1.24) | 22 % ; 0.37 $ | 0 % ; 0.39 $ |
| s52 | détaillée | 83 % ; 0.90 $ (0.59) | 60 % ; 0.20 $ | 77 % ; 0.22 $ |
| u25 | brève | 85 % / 85 % ; 1.50 $ (0.92) | 54 % / 46 % ; 0.27 $ | 69 % ; 0.32 $ |
| u45 | détaillée | 100 % / 100 % ; 2.23 $ (1.71) | 100 % / 100 % ; 0.43 $ | 100 % ; 0.48 $ |
| u51 | détaillée | 50 % / 50 % ; 2.18 $ (1.58) | 67 % / 67 % ; 0.51 $ | 50 % ; 0.55 $ |
| u57 | brève | 0 % ; 1.15 $ (0.93) | 0 % ; 0.69 $ | - |
| u611 | brève | 30 % ; 1.23 $ (1.02) | 0 % ; 0.32 $ | 0 % ; 0.22 $ |
| u75 | brève | 62 % / 38 % ; 1.14 $ (0.75) | 38 % / 62 % ; 0.23 $ | 62 % ; 0.31 $ |
| u78 | brève | 26 % ; 1.49 $ (1.02) | 22 % ; 0.30 $ | 39 % ; 0.49 $ |
| w91 | brève | 33 % / 33 % ; 1.10 $ (0.81) | 33 % / 33 % ; 0.33 $ | 17 % ; 0.20 $ |

## Critère

Borne basse de D − A : -8.4 points. Marge principale −10 : tenue ; marge secondaire −5 : non tenue. Coût de D sous A d'au moins 50 % : oui (-72.7 %).
