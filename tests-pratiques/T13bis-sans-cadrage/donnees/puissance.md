# T13 bis : analyse de puissance (avant les runs)

## Variance observée en T13

| Story | D − A (points) |
|---|---|
| l23 | +0.0 |
| l27 | -11.1 |
| l51 | +10.7 |
| l63 | -12.5 |
| l65 | +25.0 |
| u25 | -30.8 |
| u45 | +0.0 |
| u51 | +16.7 |
| u75 | -25.0 |
| w91 | +0.0 |

Moyenne -2.7 points, écart type 17.6 points (10 stories, une répétition ; l51 : A moyenné sur 2).
Bruit entre deux runs du même bras (l51, A : 57.1 et 64.3 ; B : 71.4 et 42.9) : variance par run 217, écart type 14.7 points.
Si tout l'écart venait du bruit des runs, la variance d'un écart D − A à une répétition serait 2 × 217 = 434, au-dessus de la variance observée (311) : le bruit des runs explique tout l'écart observé, l'effet propre à chaque story n'est pas mesurable.

Coût moyen T13 : A (cadrage + dév.) 1.38 $, D 0.34 $.

## Puissance simulée du plan T13 bis

Modèle : écart par story ~ normal, de variance V1 × (f / r + 1 − f), V1 = variance observée à une répétition, r = répétitions, f = part du bruit des runs (1 : tout est bruit, comme l'indique l51 ; 0,5 : moitié). 2 000 simulations, bootstrap apparié percentile de 2 000 tirages, IC 95 % bilatéral ; « non-infériorité » si la borne basse de D − A dépasse −marge.

| Nouvelles stories N | f | Vrai écart | Demi-largeur IC | Marge 3 | Marge 5 | Marge 8 | Marge 10 |
|---|---|---|---|---|---|---|---|
| 8 | 1.0 | +0.0 | 6.6 | 18 % | 34 % | 64 % | 82 % |
| 8 | 1.0 | -2.7 | 6.6 | 5 % | 13 % | 37 % | 59 % |
| 8 | 0.5 | +0.0 | 7.2 | 15 % | 30 % | 58 % | 76 % |
| 8 | 0.5 | -2.7 | 7.2 | 4 % | 10 % | 31 % | 50 % |
| 10 | 1.0 | +0.0 | 6.3 | 17 % | 34 % | 67 % | 84 % |
| 10 | 1.0 | -2.7 | 6.4 | 4 % | 14 % | 40 % | 63 % |
| 10 | 0.5 | +0.0 | 6.9 | 16 % | 30 % | 60 % | 78 % |
| 10 | 0.5 | -2.7 | 6.9 | 4 % | 11 % | 32 % | 52 % |
| 12 | 1.0 | +0.0 | 6.2 | 18 % | 36 % | 69 % | 86 % |
| 12 | 1.0 | -2.7 | 6.2 | 4 % | 13 % | 40 % | 64 % |
| 12 | 0.5 | +0.0 | 6.6 | 17 % | 36 % | 67 % | 82 % |
| 12 | 0.5 | -2.7 | 6.7 | 4 % | 12 % | 37 % | 58 % |

## Budget

- N = 8 : seconde répétition des 10 stories de T13 15.8 $ ; nouvelles stories A + D 13.8 $ ; D-court sur les 18 stories 6.1 $ ; total 35.7 $ (sans D-court 29.6 $).
- N = 9 : seconde répétition des 10 stories de T13 15.8 $ ; nouvelles stories A + D 15.5 $ ; D-court sur les 19 stories 6.4 $ ; total 37.7 $ (sans D-court 31.3 $).
- N = 10 : seconde répétition des 10 stories de T13 15.8 $ ; nouvelles stories A + D 17.2 $ ; D-court sur les 20 stories 6.8 $ ; total 39.8 $ (sans D-court 33.0 $).
- N = 12 : seconde répétition des 10 stories de T13 15.8 $ ; nouvelles stories A + D 20.6 $ ; D-court sur les 22 stories 7.4 $ ; total 43.9 $ (sans D-court 36.5 $).
