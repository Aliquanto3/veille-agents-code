### Positifs par étiquette et par dépôt (positifs / stories étiquetées)

| Étiquette | Total | service-public-slm-fine-tuning | usine-migration-jira-demo | wavedevsecops | wavelibrarian | wavelocalai |
|---|---|---|---|---|---|---|
| dérapage (appels > 2 × médiane du dépôt) | 25 / 243 | 5 / 38 | 4 / 12 | 4 / 64 | 5 / 65 | 7 / 64 |
| coût au-dessus du 80e centile du dépôt | 51 / 243 | 8 / 38 | 3 / 12 | 13 / 64 | 13 / 65 | 14 / 64 |
| défaut de revue (constat medium ou high corrigé) | 184 / 241 | 35 / 37 | 6 / 11 | 42 / 64 | 53 / 65 | 48 / 64 |
| dérapage par agent (critère de T1) | 26 / 243 | 6 / 38 | 1 / 12 | 7 / 64 | 3 / 65 | 9 / 64 |
| appels au-dessus du 80e centile du dépôt | 47 / 243 | 8 / 38 | 3 / 12 | 12 / 64 | 12 / 65 | 12 / 64 |

### dérapage (appels > 2 × médiane du dépôt) : 25 positifs sur 243 (taux de base 10 %)

| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes (≤ 20 %) | Vrais positifs | Précision | Rappel | Écart à la référence [IC] | Critère |
|---|---|---|---|---|---|---|---|---|
| Heuristique : longueur seule | 0,559 [0,42 ; 0,70] | 0,560 | 48 | 9 | 19 % | 36 % | référence |  |
| Heuristique : régression logistique (CV) | 0,493 [0,37 ; 0,62] | 0,453 | 48 | 6 | 12 % | 24 % |  |  |
| Jev latest | 0,632 [0,53 ; 0,73] | 0,618 | 47 | 5 | 11 % | 20 % | 0,07 [-0,05 ; 0,20] | non |
| Jev 1,13 | 0,631 [0,53 ; 0,74] | 0,621 | 44 | 6 | 14 % | 24 % | 0,07 [-0,05 ; 0,20] | non |
| gpt-6-luna, exéc. 1 | 0,524 [0,40 ; 0,65] | 0,542 | 46 | 5 | 11 % | 20 % | -0,04 [-0,16 ; 0,08] | non |
| gpt-6-luna, exéc. 2 | 0,532 [0,42 ; 0,64] | 0,534 | 36 | 3 | 8 % | 12 % | -0,03 [-0,12 ; 0,07] | non |
| gpt-6-luna, moyenne | 0,532 [0,42 ; 0,65] | 0,550 | 47 | 4 | 8 % | 16 % | -0,03 [-0,13 ; 0,08] | non |

### coût au-dessus du 80e centile du dépôt : 51 positifs sur 243 (taux de base 21 %)

| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes (≤ 20 %) | Vrais positifs | Précision | Rappel | Écart à la référence [IC] | Critère |
|---|---|---|---|---|---|---|---|---|
| Heuristique : longueur seule | 0,590 [0,49 ; 0,69] | 0,591 | 48 | 18 | 38 % | 35 % | référence |  |
| Heuristique : régression logistique (CV) | 0,525 [0,43 ; 0,61] | 0,529 | 48 | 13 | 27 % | 26 % |  |  |
| Jev latest | 0,595 [0,51 ; 0,67] | 0,597 | 43 | 12 | 28 % | 24 % | 0,00 [-0,07 ; 0,08] | non |
| Jev 1,13 | 0,614 [0,53 ; 0,70] | 0,623 | 48 | 15 | 31 % | 29 % | 0,02 [-0,05 ; 0,10] | non |
| gpt-6-luna, exéc. 1 | 0,579 [0,49 ; 0,67] | 0,585 | 34 | 12 | 35 % | 24 % | -0,01 [-0,10 ; 0,07] | non |
| gpt-6-luna, exéc. 2 | 0,591 [0,51 ; 0,68] | 0,599 | 34 | 10 | 29 % | 20 % | 0,00 [-0,08 ; 0,08] | non |
| gpt-6-luna, moyenne | 0,592 [0,50 ; 0,67] | 0,593 | 48 | 15 | 31 % | 29 % | 0,00 [-0,07 ; 0,08] | non |

### défaut de revue (constat medium ou high corrigé) : 184 positifs sur 241 (taux de base 76 %)

| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes (≤ 20 %) | Vrais positifs | Précision | Rappel | Écart à la référence [IC] | Critère |
|---|---|---|---|---|---|---|---|---|
| Heuristique : longueur seule | 0,559 [0,46 ; 0,65] | 0,557 | 47 | 32 | 68 % | 17 % | référence |  |
| Heuristique : régression logistique (CV) | 0,518 [0,43 ; 0,60] | 0,532 | 48 | 38 | 79 % | 21 % |  |  |
| Jev latest | 0,520 [0,43 ; 0,61] | 0,526 | 38 | 29 | 76 % | 16 % | -0,04 [-0,13 ; 0,05] | non |
| Jev 1,13 | 0,577 [0,49 ; 0,66] | 0,573 | 41 | 33 | 80 % | 18 % | 0,02 [-0,07 ; 0,10] | non |
| gpt-6-luna, exéc. 1 | 0,609 [0,53 ; 0,69] | 0,601 | 25 | 23 | 92 % | 12 % | 0,05 [-0,03 ; 0,12] | non |
| gpt-6-luna, exéc. 2 | 0,543 [0,45 ; 0,63] | 0,513 | 27 | 20 | 74 % | 11 % | -0,02 [-0,09 ; 0,06] | non |
| gpt-6-luna, moyenne | 0,587 [0,50 ; 0,67] | 0,569 | 48 | 39 | 81 % | 21 % | 0,03 [-0,04 ; 0,10] | non |

### dérapage par agent (critère de T1) : 26 positifs sur 243 (taux de base 11 %)

| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes (≤ 20 %) | Vrais positifs | Précision | Rappel | Écart à la référence [IC] | Critère |
|---|---|---|---|---|---|---|---|---|
| Heuristique : longueur seule | 0,568 [0,42 ; 0,72] | 0,579 | 48 | 11 | 23 % | 42 % | référence |  |
| Heuristique : régression logistique (CV) | 0,486 [0,35 ; 0,62] | 0,454 | 48 | 6 | 12 % | 23 % |  |  |
| Jev latest | 0,608 [0,49 ; 0,73] | 0,594 | 47 | 8 | 17 % | 31 % | 0,04 [-0,04 ; 0,13] | non |
| Jev 1,13 | 0,608 [0,47 ; 0,74] | 0,593 | 44 | 9 | 20 % | 35 % | 0,04 [-0,03 ; 0,12] | non |
| gpt-6-luna, exéc. 1 | 0,542 [0,43 ; 0,65] | 0,525 | 46 | 5 | 11 % | 19 % | -0,03 [-0,13 ; 0,07] | non |
| gpt-6-luna, exéc. 2 | 0,568 [0,45 ; 0,69] | 0,554 | 36 | 6 | 17 % | 23 % | 0,00 [-0,08 ; 0,08] | non |
| gpt-6-luna, moyenne | 0,551 [0,43 ; 0,67] | 0,536 | 47 | 6 | 13 % | 23 % | -0,02 [-0,10 ; 0,06] | non |

### appels au-dessus du 80e centile du dépôt : 47 positifs sur 243 (taux de base 19 %)

| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes (≤ 20 %) | Vrais positifs | Précision | Rappel | Écart à la référence [IC] | Critère |
|---|---|---|---|---|---|---|---|---|
| Heuristique : longueur seule | 0,602 [0,50 ; 0,70] | 0,605 | 48 | 17 | 35 % | 36 % | référence |  |
| Heuristique : régression logistique (CV) | 0,547 [0,44 ; 0,65] | 0,556 | 48 | 13 | 27 % | 28 % |  |  |
| Jev latest | 0,641 [0,56 ; 0,72] | 0,639 | 47 | 13 | 28 % | 28 % | 0,04 [-0,05 ; 0,13] | non |
| Jev 1,13 | 0,649 [0,56 ; 0,73] | 0,652 | 44 | 14 | 32 % | 30 % | 0,05 [-0,04 ; 0,14] | non |
| gpt-6-luna, exéc. 1 | 0,606 [0,52 ; 0,70] | 0,608 | 46 | 15 | 33 % | 32 % | 0,01 [-0,08 ; 0,08] | non |
| gpt-6-luna, exéc. 2 | 0,614 [0,53 ; 0,70] | 0,621 | 36 | 9 | 25 % | 19 % | 0,01 [-0,06 ; 0,09] | non |
| gpt-6-luna, moyenne | 0,611 [0,52 ; 0,70] | 0,625 | 47 | 14 | 30 % | 30 % | 0,01 [-0,07 ; 0,08] | non |

### AUC par dépôt (positifs entre parenthèses ; n.d. si moins de 2 positifs ou de 2 négatifs)

| Étiquette | Bras | service-public-slm-fine-tuning | usine-migration-jira-demo | wavedevsecops | wavelibrarian | wavelocalai |
|---|---|---|---|---|---|---|
| derapage | Heuristique : longueur seule | 0,81 (5) | 0,78 (4) | 0,52 (4) | 0,62 (5) | 0,27 (7) |
| derapage | Jev latest | 0,88 (5) | 0,52 (4) | 0,57 (4) | 0,67 (5) | 0,49 (7) |
| derapage | gpt-6-luna, exéc. 1 | 0,84 (5) | 0,72 (4) | 0,52 (4) | 0,52 (5) | 0,29 (7) |
| cout80 | Heuristique : longueur seule | 0,85 (8) | 0,85 (3) | 0,64 (13) | 0,55 (13) | 0,37 (14) |
| cout80 | Jev latest | 0,88 (8) | 0,56 (3) | 0,60 (13) | 0,68 (13) | 0,36 (14) |
| cout80 | gpt-6-luna, exéc. 1 | 0,84 (8) | 0,67 (3) | 0,59 (13) | 0,60 (13) | 0,40 (14) |
| defaut_revue | Heuristique : longueur seule | 0,86 (35) | 0,77 (6) | 0,41 (42) | 0,72 (53) | 0,51 (48) |
| defaut_revue | Jev latest | 0,75 (35) | 0,47 (6) | 0,37 (42) | 0,68 (53) | 0,58 (48) |
| defaut_revue | gpt-6-luna, exéc. 1 | 0,87 (35) | 0,58 (6) | 0,46 (42) | 0,77 (53) | 0,62 (48) |

### Précision et rappel à 20 % d'alertes par dépôt (vrais positifs / alertes ; positifs du dépôt)

| Étiquette | Bras | service-public-slm-fine-tuning | usine-migration-jira-demo | wavedevsecops | wavelibrarian | wavelocalai |
|---|---|---|---|---|---|---|
| derapage | Heuristique : longueur seule | 3/7 ; 5 pos. | 1/2 ; 4 pos. | 0/12 ; 4 pos. | 3/13 ; 5 pos. | 1/12 ; 7 pos. |
| derapage | Jev latest | 3/7 ; 5 pos. | 0/1 ; 4 pos. | 0/11 ; 4 pos. | 2/12 ; 5 pos. | 2/11 ; 7 pos. |
| derapage | gpt-6-luna, exéc. 1 | 2/7 ; 5 pos. | 1/2 ; 4 pos. | 1/12 ; 4 pos. | 1/11 ; 5 pos. | 0/12 ; 7 pos. |
| cout80 | Heuristique : longueur seule | 5/7 ; 8 pos. | 1/2 ; 3 pos. | 4/12 ; 13 pos. | 5/13 ; 13 pos. | 2/12 ; 14 pos. |
| cout80 | Jev latest | 5/7 ; 8 pos. | 0/2 ; 3 pos. | 3/12 ; 13 pos. | 4/11 ; 13 pos. | 1/12 ; 14 pos. |
| cout80 | gpt-6-luna, exéc. 1 | 4/6 ; 8 pos. | 1/2 ; 3 pos. | 4/11 ; 13 pos. | 5/12 ; 13 pos. | 1/10 ; 14 pos. |
| defaut_revue | Heuristique : longueur seule | 7/7 ; 35 pos. | 1/2 ; 6 pos. | 6/12 ; 42 pos. | 11/13 ; 53 pos. | 6/12 ; 48 pos. |
| defaut_revue | Jev latest | 4/4 ; 35 pos. | 0/1 ; 6 pos. | 6/10 ; 42 pos. | 9/10 ; 53 pos. | 3/3 ; 48 pos. |
| defaut_revue | gpt-6-luna, exéc. 1 | 6/6 ; 35 pos. | 2/2 ; 6 pos. | 8/12 ; 42 pos. | 13/13 ; 53 pos. | 10/11 ; 48 pos. |

### Analyse de puissance (AUC 0,65 contre 0,5, bilatéral 5 %, puissance 80 %)

| Étiquette | Positifs | Négatifs | Taux de base | Positifs nécessaires | Stories nécessaires | Puissance actuelle (AUC 0,65) | AUC détectable aujourd'hui (80 %) | Positifs pour un écart de 0,05 à l'heuristique |
|---|---|---|---|---|---|---|---|---|
| dérapage (appels > 2 × médiane du dépôt) | 25 | 218 | 10 % | 33 | 321 | 69 % | 0,68 | 296 |
| coût au-dessus du 80e centile du dépôt | 51 | 192 | 21 % | 37 | 176 | 91 % | 0,63 | 322 |
| défaut de revue (constat medium ou high corrigé) | 184 | 57 | 76 % | 115 | 151 | 95 % | 0,62 | 823 |
| dérapage par agent (critère de T1) | 26 | 217 | 11 % | 34 | 318 | 70 % | 0,67 | 297 |
| appels au-dessus du 80e centile du dépôt | 47 | 196 | 19 % | 37 | 191 | 89 % | 0,64 | 317 |

Vérification par simulation binormale (derapage, 33 positifs et 287 négatifs, AUC 0,65) : puissance simulée 79 %.

Dernière colonne : ecart de 0,05 (AUC 0,70 contre 0,65) entre deux bras correles (r = 0,5 supposee), 5 % bilateral, puissance 80 %.
