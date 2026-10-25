| Id | Story | Classe | Défaut semé | pytest | Oracle scripté | Sous-agent | FAIL de l'agent | Coût ($) |
|---|---|---|---|---|---|---|---|---|
| d01 | 7.13 | message absent | Le bandeau de repli n'est plus posé par le cadre en Mode repli. | passe | KO C3 | détecté | C3 | 0.088 |
| d02 | 7.13 | navigation clavier cassée | Le lien d'évitement reste hors écran quand il reçoit le focus (le style :focus ne le ramène plus à l'écran). | passe | KO C4 | détecté | C4,T1 | 0.104 |
| d03 | 7.13 | mise en page 390 px | Le point de rupture mobile passe de 767 px à 300 px : la grille à deux colonnes reste à 390 px. | passe | KO T2,T2 | détecté | T2 | 0.067 |
| d04 | 7.14 | bouton inactif | Le filtre météo ne réagit plus au changement de valeur (écouteur retiré). | passe | KO C2 | détecté | C2,T2 | 0.156 |
| d05 | 7.14 | lien mort | Le lien de téléchargement d'un livrable pointe vers /livrable/ (404) au lieu de /livrables/. | passe | KO C3 | détecté | C3,T3 | 0.140 |
| d06 | 7.14 | erreur sans texte | Le message « Entité {entite} absente du Passage affiché. » est vide (le lien vers la carte reste). | passe | KO C5 | détecté | C5,T3 | 0.142 |
| d07 | 7.14 | message faux | L'annonce du filtre affiche le gabarit « {n} Entités affichées » sans remplacer {n}. | passe | KO C2 | détecté | C2 | 0.105 |
| d08 | 7.15 | message absent | Le bandeau d'échec (étape, code, lignes d'erreur) n'est plus affiché. | passe | KO C2,C3 | détecté | C2,C3 | 0.167 |
| d09 | 7.15 | état non rafraîchi | Après la bascule de mode, la pastille de mode de l'en-tête n'est pas relue (elle reste fausse jusqu'au rechargement). | passe | KO C2,C3,C4,C5 | manqué | T2 | 0.142 |
| d10 | 7.15 | état perdu après rechargement | Le bandeau de résultat de la Chaîne n'est affiché que dans la page qui a lancé la Chaîne : il disparaît au rechargement. | passe | KO C3 | détecté | C3 | 0.151 |
| d11 | 7.15 | bouton inactif (marquage) | Les boutons bloqués ne portent plus aria-disabled=true : ils paraissent actifs alors que le serveur refuse. | passe | KO C5 | détecté | C5,T2 | 0.133 |
| d12 | 7.16 | message absent | La mention de rejeu (agent.mention_repli) n'est plus affichée sous la réponse enregistrée. | passe | KO C1 | détecté | C1 | 0.182 |
| d13 | 7.14 | navigation clavier cassée | Les liens de téléchargement des livrables sont exclus de l'ordre de tabulation (tabindex=-1) : inaccessibles au clavier. | passe | KO C3b | détecté | T1 | 0.146 |
| d14 | 7.16 | bouton inactif | Le segment de période ne change plus les cartes au clic. | passe | KO C2 | détecté | C2 | 0.172 |
| d15 | 7.16 | mise en page 390 px | Les cartes jumelles (avant/après, pseudonymisation) restent côte à côte à 390 px (rupture à 300 px). | passe | KO T2 | manqué | - | 0.163 |
| d16 | 7.16 | lien mort | Le formulaire de sélection du ticket envoie vers /pseudonymisations (404). | passe | KO C3 | détecté | C3,T3 | 0.299 |
| e01 | 7.13 | donnée fausse | La pastille de mode affiche toujours « Mode réel », même en Mode repli. | passe | KO C3 | détecté | C3 | 0.071 |
| e02 | 7.13 | message absent | La pastille « Passage publié » n'est jamais affichée. | passe | KO C2 | détecté | C2 | 0.072 |
| e04 | 7.14 | donnée fausse | Le chiffre de chaque tuile de comptage est augmenté de 1 (incohérent avec les lignes du tableau). | passe | KO C1b | détecté | C1 | 0.148 |
| e05 | 7.14 | lien mort / mauvais lien | Le lien « Détail » de chaque ligne mène toujours à ENT-A. | passe | KO C4b | détecté | C1,C4,T3 | 0.128 |
| e06 | 7.14 | état perdu | Revenir à l'option « Toutes » du filtre n'affiche plus aucune ligne. | passe | KO C2,C4b | détecté | C1,C2,T2 | 0.135 |
| e07 | 7.15 | libellé non mis à jour | Le libellé du bouton de mode ne change plus après la bascule (reste « Passer en Mode repli »). | passe | KO C2,C3,C4,C5 | détecté | C4,T2 | 0.147 |
| e08 | 7.15 | message absent | Le motif du blocage du bouton de lancement n'est plus visible (reste lié par aria-describedby). | passe | KO C5 | manqué | - | 0.140 |
| e09 | 7.16 | donnée fausse | Les outils appelés ne sont jamais listés dans la réponse rejouée (affiche « aucun »). | passe | KO C1b | détecté | C1 | 0.167 |
| e10 | 7.16 | message absent | Le tableau des périodes de l'écran Avant / après n'est plus affiché. | passe | KO C2b | détecté | C2 | 0.187 |
| e11 | 7.16 | mise en page cassée | La fiche d'outillage affiche son HTML en texte brut (balises visibles). | échoue | KO C4 | détecté | C4 | 0.163 |
