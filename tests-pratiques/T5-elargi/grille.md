# Grille de jugement (fixée avant la première revue, ne pas modifier ensuite)

Un constat C d'un relecteur **détecte** le défaut semé D (fichier F, lignes a à b, nature N, description du comportement fautif) si les trois conditions sont réunies.

1. **Localisation.** C désigne le fichier F (chemin égal, ou même fin de chemin) et une ligne dans l'intervalle [a - 5, b + 5]. Un constat qui donne une plage de lignes compte si la plage coupe l'intervalle.
2. **Logique.** La description de C dit que le comportement introduit par la mutation est faux : condition fausse ou inversée, borne décalée, branche d'erreur absente, valeur par défaut erronée, exception avalée, selon N. Elle peut décrire la cause (« la condition est inversée ») ou l'effet (« une entrée vide est acceptée »), à condition qu'il s'agisse de l'effet de la mutation. Ne suffisent pas : la même fonction pour un autre motif, un constat de test manquant ou de style, un cas limite sans rapport. Le constat « près mais autre motif » est compté à part (non détecté).
3. **Sévérité.** Deux rappels sont publiés. Le **rappel** compte tout constat, quelle que soit sa sévérité. Le **rappel Important** ne compte que les constats Important (GPT et Opus) ou high et medium (Haiku, qui emploie high, medium, low) ; un constat Nit ou low ne compte pas.

## Procédure
- La localisation est contrôlée par script (`juger.py`). Seuls les constats qui passent la localisation sont lus.
- La lecture est faite par une seule personne, à l'aveugle du relecteur (constats mélangés, identifiant du relecteur masqué), avec la description du défaut semé sous les yeux.
- Défaut équivalent : si la lecture du code montre que la mutation ne change aucun comportement observable, le défaut est retiré du dénominateur de tous les relecteurs, et la story devient un témoin si aucun autre défaut ne peut être semé.

## Faux positifs
- **Témoins** (4 stories sans défaut semé) : tout constat Important (GPT, Opus) ou high/medium (Haiku) est compté, puis classé à la lecture du code en `démontré` (défaut réel ou écart à la spec vérifiable), `discutable` ou `faux` (le code est correct ou le constat contredit le dépôt). Le taux de faux positifs publié est le nombre de constats Important `faux` + `discutable` par témoin ; la borne haute est le nombre brut d'Important.
- **Hors semis** (stories à défaut semé) : les constats Important qui ne détectent pas D sont comptés comme « Important hors semis » (bruit, non classés).

## Combinaisons
- Chaîne actuelle : Haiku puis Opus. Ici les deux passent indépendamment sur le même diff, et la chaîne détecte D si l'un des deux le détecte (union). Limite : en production, Opus reçoit la liste de Haiku.
- Chaîne + luna, chaîne + sol : union de la chaîne et du critique externe.
- Critère de décision : garder un critique externe s'il ajoute au moins 10 points de rappel à la chaîne sans doubler le nombre de constats Important faux ou hors semis de la chaîne.
- Intervalle de confiance du rappel : Wilson à 95 %.
