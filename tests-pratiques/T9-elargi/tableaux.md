### Positifs par étiquette et par dépôt (positifs / stories étiquetées)

| Étiquette | Total | service-public-slm-fine-tuning | service-public-slm-fine-tuning/avant-kit | usine-migration-jira-demo | usine-migration-jira-demo/avant-kit | wavedevsecops | wavelibrarian | wavelocalai |
|---|---|---|---|---|---|---|---|---|
| dérapage (appels > 2 × médiane du dépôt) | 32 / 339 | 5 / 38 | 1 / 32 | 4 / 12 | 6 / 64 | 4 / 64 | 5 / 65 | 7 / 64 |
| coût au-dessus du 80e centile du dépôt | 71 / 339 | 8 / 38 | 7 / 32 | 3 / 12 | 13 / 64 | 13 / 64 | 13 / 65 | 14 / 64 |
| défaut de revue (constat medium ou high corrigé) | 246 / 336 | 35 / 37 | 24 / 32 | 6 / 11 | 38 / 63 | 42 / 64 | 53 / 65 | 48 / 64 |
| dérapage par agent (critère de T1) | 30 / 339 | 6 / 38 | 0 / 32 | 1 / 12 | 4 / 64 | 7 / 64 | 3 / 65 | 9 / 64 |
| appels au-dessus du 80e centile du dépôt | 67 / 339 | 8 / 38 | 7 / 32 | 3 / 12 | 13 / 64 | 12 / 64 | 12 / 65 | 12 / 64 |

### dérapage (appels > 2 × médiane du dépôt) : 32 positifs sur 339 (taux de base 9 %)

| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes (≤ 20 %) | Vrais positifs | Précision | Rappel | Écart à la référence [IC] | Critère |
|---|---|---|---|---|---|---|---|---|
| Heuristique : longueur seule | 0,566 [0,45 ; 0,69] | 0,568 | 67 | 12 | 18 % | 38 % | référence |  |
| Heuristique : régression logistique (CV) | 0,503 [0,39 ; 0,61] | 0,520 | 67 | 8 | 12 % | 25 % |  |  |
| Jev latest | 0,617 [0,52 ; 0,70] | 0,616 | 62 | 6 | 10 % | 19 % | 0,05 [-0,05 ; 0,15] | non |
| Jev 1,13 | 0,616 [0,52 ; 0,71] | 0,621 | 66 | 10 | 15 % | 31 % | 0,05 [-0,06 ; 0,16] | non |
| gpt-6-luna, exéc. 1 | 0,552 [0,45 ; 0,65] | 0,592 | 63 | 8 | 13 % | 25 % | -0,01 [-0,12 ; 0,10] | non |
| gpt-6-luna, exéc. 2 | 0,562 [0,47 ; 0,66] | 0,573 | 67 | 5 | 8 % | 16 % | -0,00 [-0,09 ; 0,09] | non |
| gpt-6-luna, moyenne | 0,563 [0,46 ; 0,66] | 0,594 | 65 | 7 | 11 % | 22 % | -0,00 [-0,10 ; 0,10] | non |

### coût au-dessus du 80e centile du dépôt : 71 positifs sur 339 (taux de base 21 %)

| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes (≤ 20 %) | Vrais positifs | Précision | Rappel | Écart à la référence [IC] | Critère |
|---|---|---|---|---|---|---|---|---|
| Heuristique : longueur seule | 0,588 [0,50 ; 0,67] | 0,587 | 67 | 23 | 34 % | 32 % | référence |  |
| Heuristique : régression logistique (CV) | 0,561 [0,48 ; 0,64] | 0,560 | 67 | 21 | 31 % | 30 % |  |  |
| Jev latest | 0,602 [0,53 ; 0,67] | 0,613 | 66 | 19 | 29 % | 27 % | 0,01 [-0,05 ; 0,08] | non |
| Jev 1,13 | 0,607 [0,54 ; 0,68] | 0,621 | 66 | 20 | 30 % | 28 % | 0,02 [-0,05 ; 0,09] | non |
| gpt-6-luna, exéc. 1 | 0,587 [0,51 ; 0,66] | 0,604 | 66 | 24 | 36 % | 34 % | -0,00 [-0,08 ; 0,08] | non |
| gpt-6-luna, exéc. 2 | 0,600 [0,53 ; 0,67] | 0,609 | 62 | 17 | 27 % | 24 % | 0,01 [-0,07 ; 0,09] | non |
| gpt-6-luna, moyenne | 0,603 [0,53 ; 0,67] | 0,610 | 66 | 20 | 30 % | 28 % | 0,01 [-0,06 ; 0,10] | non |

### défaut de revue (constat medium ou high corrigé) : 246 positifs sur 336 (taux de base 73 %)

| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes (≤ 20 %) | Vrais positifs | Précision | Rappel | Écart à la référence [IC] | Critère |
|---|---|---|---|---|---|---|---|---|
| Heuristique : longueur seule | 0,600 [0,53 ; 0,67] | 0,595 | 67 | 46 | 69 % | 19 % | référence |  |
| Heuristique : régression logistique (CV) | 0,583 [0,51 ; 0,66] | 0,586 | 67 | 51 | 76 % | 21 % |  |  |
| Jev latest | 0,513 [0,44 ; 0,58] | 0,518 | 51 | 39 | 76 % | 16 % | -0,09 [-0,17 ; -0,01] | non |
| Jev 1,13 | 0,575 [0,51 ; 0,64] | 0,573 | 58 | 46 | 79 % | 19 % | -0,03 [-0,10 ; 0,05] | non |
| gpt-6-luna, exéc. 1 | 0,625 [0,56 ; 0,69] | 0,600 | 62 | 54 | 87 % | 22 % | 0,03 [-0,04 ; 0,09] | non |
| gpt-6-luna, exéc. 2 | 0,557 [0,49 ; 0,63] | 0,518 | 67 | 50 | 75 % | 20 % | -0,04 [-0,11 ; 0,02] | non |
| gpt-6-luna, moyenne | 0,597 [0,53 ; 0,66] | 0,567 | 58 | 48 | 83 % | 20 % | -0,00 [-0,07 ; 0,06] | non |

### dérapage par agent (critère de T1) : 30 positifs sur 339 (taux de base 9 %)

| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes (≤ 20 %) | Vrais positifs | Précision | Rappel | Écart à la référence [IC] | Critère |
|---|---|---|---|---|---|---|---|---|
| Heuristique : longueur seule | 0,597 [0,46 ; 0,72] | 0,606 | 67 | 13 | 19 % | 43 % | référence |  |
| Heuristique : régression logistique (CV) | 0,492 [0,36 ; 0,62] | 0,493 | 67 | 9 | 13 % | 30 % |  |  |
| Jev latest | 0,612 [0,51 ; 0,71] | 0,618 | 62 | 8 | 13 % | 27 % | 0,01 [-0,07 ; 0,10] | non |
| Jev 1,13 | 0,598 [0,48 ; 0,71] | 0,602 | 66 | 11 | 17 % | 37 % | 0,00 [-0,08 ; 0,09] | non |
| gpt-6-luna, exéc. 1 | 0,548 [0,45 ; 0,65] | 0,535 | 63 | 7 | 11 % | 23 % | -0,05 [-0,15 ; 0,05] | non |
| gpt-6-luna, exéc. 2 | 0,561 [0,46 ; 0,67] | 0,558 | 67 | 8 | 12 % | 27 % | -0,04 [-0,13 ; 0,05] | non |
| gpt-6-luna, moyenne | 0,549 [0,44 ; 0,66] | 0,541 | 65 | 7 | 11 % | 23 % | -0,05 [-0,14 ; 0,04] | non |

### appels au-dessus du 80e centile du dépôt : 67 positifs sur 339 (taux de base 20 %)

| Bras | AUC [IC 95 %] | AUC intra-dépôt | Alertes (≤ 20 %) | Vrais positifs | Précision | Rappel | Écart à la référence [IC] | Critère |
|---|---|---|---|---|---|---|---|---|
| Heuristique : longueur seule | 0,583 [0,50 ; 0,67] | 0,581 | 67 | 21 | 31 % | 31 % | référence |  |
| Heuristique : régression logistique (CV) | 0,543 [0,46 ; 0,62] | 0,539 | 67 | 21 | 31 % | 31 % |  |  |
| Jev latest | 0,629 [0,56 ; 0,69] | 0,632 | 62 | 16 | 26 % | 24 % | 0,04 [-0,03 ; 0,11] | non |
| Jev 1,13 | 0,631 [0,56 ; 0,70] | 0,639 | 66 | 20 | 30 % | 30 % | 0,05 [-0,03 ; 0,12] | non |
| gpt-6-luna, exéc. 1 | 0,587 [0,52 ; 0,66] | 0,599 | 63 | 18 | 29 % | 27 % | 0,00 [-0,07 ; 0,07] | non |
| gpt-6-luna, exéc. 2 | 0,613 [0,54 ; 0,69] | 0,622 | 67 | 19 | 28 % | 28 % | 0,03 [-0,04 ; 0,10] | non |
| gpt-6-luna, moyenne | 0,603 [0,53 ; 0,68] | 0,618 | 65 | 18 | 28 % | 27 % | 0,02 [-0,05 ; 0,09] | non |

### AUC par dépôt (positifs entre parenthèses ; n.d. si moins de 2 positifs ou de 2 négatifs)

| Étiquette | Bras | service-public-slm-fine-tuning | service-public-slm-fine-tuning/avant-kit | usine-migration-jira-demo | usine-migration-jira-demo/avant-kit | wavedevsecops | wavelibrarian | wavelocalai |
|---|---|---|---|---|---|---|---|---|
| derapage | Heuristique : longueur seule | 0,81 (5) | n.d. (1) | 0,78 (4) | 0,65 (6) | 0,52 (4) | 0,62 (5) | 0,27 (7) |
| derapage | Jev latest | 0,88 (5) | n.d. (1) | 0,52 (4) | 0,69 (6) | 0,57 (4) | 0,67 (5) | 0,49 (7) |
| derapage | gpt-6-luna, exéc. 1 | 0,84 (5) | n.d. (1) | 0,72 (4) | 0,74 (6) | 0,52 (4) | 0,52 (5) | 0,29 (7) |
| cout80 | Heuristique : longueur seule | 0,85 (8) | 0,48 (7) | 0,85 (3) | 0,63 (13) | 0,64 (13) | 0,55 (13) | 0,37 (14) |
| cout80 | Jev latest | 0,88 (8) | 0,61 (7) | 0,56 (3) | 0,68 (13) | 0,60 (13) | 0,68 (13) | 0,36 (14) |
| cout80 | gpt-6-luna, exéc. 1 | 0,84 (8) | 0,74 (7) | 0,67 (3) | 0,60 (13) | 0,59 (13) | 0,60 (13) | 0,40 (14) |
| defaut_revue | Heuristique : longueur seule | 0,86 (35) | 0,73 (24) | 0,77 (6) | 0,66 (38) | 0,41 (42) | 0,72 (53) | 0,51 (48) |
| defaut_revue | Jev latest | 0,75 (35) | 0,48 (24) | 0,47 (6) | 0,51 (38) | 0,37 (42) | 0,68 (53) | 0,58 (48) |
| defaut_revue | gpt-6-luna, exéc. 1 | 0,87 (35) | 0,51 (24) | 0,58 (6) | 0,64 (38) | 0,46 (42) | 0,77 (53) | 0,62 (48) |

### Précision et rappel à 20 % d'alertes par dépôt (vrais positifs / alertes ; positifs du dépôt)

| Étiquette | Bras | service-public-slm-fine-tuning | service-public-slm-fine-tuning/avant-kit | usine-migration-jira-demo | usine-migration-jira-demo/avant-kit | wavedevsecops | wavelibrarian | wavelocalai |
|---|---|---|---|---|---|---|---|---|
| derapage | Heuristique : longueur seule | 3/7 ; 5 pos. | 0/6 ; 1 pos. | 1/2 ; 4 pos. | 3/12 ; 6 pos. | 0/12 ; 4 pos. | 3/13 ; 5 pos. | 1/12 ; 7 pos. |
| derapage | Jev latest | 3/7 ; 5 pos. | 0/5 ; 1 pos. | 0/1 ; 4 pos. | 2/9 ; 6 pos. | 0/11 ; 4 pos. | 2/12 ; 5 pos. | 2/11 ; 7 pos. |
| derapage | gpt-6-luna, exéc. 1 | 2/7 ; 5 pos. | 1/5 ; 1 pos. | 1/2 ; 4 pos. | 2/10 ; 6 pos. | 1/12 ; 4 pos. | 1/11 ; 5 pos. | 0/12 ; 7 pos. |
| cout80 | Heuristique : longueur seule | 5/7 ; 8 pos. | 1/6 ; 7 pos. | 1/2 ; 3 pos. | 4/12 ; 13 pos. | 4/12 ; 13 pos. | 5/13 ; 13 pos. | 2/12 ; 14 pos. |
| cout80 | Jev latest | 5/7 ; 8 pos. | 2/6 ; 7 pos. | 0/2 ; 3 pos. | 3/12 ; 13 pos. | 3/12 ; 13 pos. | 4/11 ; 13 pos. | 1/12 ; 14 pos. |
| cout80 | gpt-6-luna, exéc. 1 | 4/6 ; 8 pos. | 3/6 ; 7 pos. | 1/2 ; 3 pos. | 2/11 ; 13 pos. | 4/11 ; 13 pos. | 5/12 ; 13 pos. | 1/10 ; 14 pos. |
| defaut_revue | Heuristique : longueur seule | 7/7 ; 35 pos. | 5/6 ; 24 pos. | 1/2 ; 6 pos. | 7/12 ; 38 pos. | 6/12 ; 42 pos. | 11/13 ; 53 pos. | 6/12 ; 48 pos. |
| defaut_revue | Jev latest | 4/4 ; 35 pos. | 3/4 ; 24 pos. | 0/1 ; 6 pos. | 6/9 ; 38 pos. | 6/10 ; 42 pos. | 9/10 ; 53 pos. | 3/3 ; 48 pos. |
| defaut_revue | gpt-6-luna, exéc. 1 | 6/6 ; 35 pos. | 3/4 ; 24 pos. | 2/2 ; 6 pos. | 4/4 ; 38 pos. | 8/12 ; 42 pos. | 13/13 ; 53 pos. | 10/11 ; 48 pos. |

### Analyse de puissance (AUC 0,65 contre 0,5, bilatéral 5 %, puissance 80 %)

| Étiquette | Positifs | Négatifs | Taux de base | Positifs nécessaires | Stories nécessaires | Puissance actuelle (AUC 0,65) | AUC détectable aujourd'hui (80 %) | Positifs pour un écart de 0,05 à l'heuristique |
|---|---|---|---|---|---|---|---|---|
| dérapage (appels > 2 × médiane du dépôt) | 32 | 307 | 9 % | 33 | 350 | 79 % | 0,66 | 294 |
| coût au-dessus du 80e centile du dépôt | 71 | 268 | 21 % | 37 | 177 | 97 % | 0,61 | 322 |
| défaut de revue (constat medium ou high corrigé) | 246 | 90 | 73 % | 103 | 141 | 99 % | 0,60 | 740 |
| dérapage par agent (critère de T1) | 30 | 309 | 9 % | 33 | 373 | 77 % | 0,66 | 293 |
| appels au-dessus du 80e centile du dépôt | 67 | 272 | 20 % | 37 | 187 | 97 % | 0,61 | 318 |

Vérification par simulation binormale (derapage, 33 positifs et 318 négatifs, AUC 0,65) : puissance simulée 80 %.

Dernière colonne : ecart de 0,05 (AUC 0,70 contre 0,65) entre deux bras correles (r = 0,5 supposee), 5 % bilateral, puissance 80 %.
