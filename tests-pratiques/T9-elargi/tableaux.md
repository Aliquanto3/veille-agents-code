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
