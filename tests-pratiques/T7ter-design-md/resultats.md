# T7 ter : un `DESIGN.md` maison améliore-t-il la note humaine ?

Test du 2026-10-25. Protocole : `protocole.md` (fixé avant les essais). **Statut : conclu par la note à l'aveugle d'Anaël du 2026-10-25 (section 6). Décision : ne pas garder `DESIGN.md` en l'état.** Il gagne nettement sur l'écran dont viennent ses règles (+0,89), mais presque rien sur l'écran nouveau (+0,11, cohérence −0,33). Les commentaires d'Anaël désignent les règles à corriger (section 6).

## 1. Résumé
- 12 exécutions `claude -p` (Sonnet 5.5, effort `medium`) terminées sans erreur : 2 bras (b2 `frontend-design` seul, b5 `frontend-design` + `DESIGN.md`) × 2 écrans (1 : Demandes d'achat, repris de T7 ; 2 : Notes de frais, nouveau) × 3 essais. **Coût total : 3,90 $** (budget 6 $).
- **Surcoût de b5 : −1,4 % sur les six essais** (0,323 $ contre 0,327 $ par essai), −2,5 % sur l'écran 1, −0,4 % sur l'écran 2. Le critère « au plus 10 % » est rempli, dans le bruit (les fourchettes se chevauchent : 0,27 à 0,36 $ pour b2, 0,31 à 0,36 $ pour b5).
- **Contrat fonctionnel** : b2 5 exécutions complètes sur 6 (un point raté sur l'écran 2 : `confirmation_unique`) ; b5 5 sur 6 (un point raté sur l'écran 1 : `confirmation_unique`). Même défaut que T7 : un message de confirmation à usage unique qui survit au rechargement.
- **axe-core** : 0 violation sur 11 des 12 rendus ; 1 sur `b5_e2_r3` (`scrollable-region-focusable`, impact serious, 1 nœud). **`impeccable detect`** : b2 1 rendu sur 6 avec un constat (`border-accent-on-rounded`), b5 3 sur 6 (`border-accent-on-rounded` sur deux rendus de l'écran 1, `straggler` sur un rendu de l'écran 2). Le détecteur ne confirme donc pas l'amélioration de la règle R1, mais il ne regarde pas le même objet (voir section 5).
- **Conformité aux règles de `DESIGN.md`** (indicative, mesurée dans le DOM) : **b5 98 % des contrôles (65 sur 66), b2 52 % (34 sur 66)**. Les agents ont lu `DESIGN.md` dans 6 essais sur 6 (par `cat`, jamais par l'outil `Read`) et l'ont appliqué, y compris sur l'écran 2 que les règles n'ont pas vu : 32 contrôles sur 33 pour b5, 18 sur 33 pour b2. Seule règle non respectée par b5 : étiquettes de catégorie (R7), une fois sur six (colonne « Catégorie » de l'écran 2 en texte simple).
- **Ce que ces mesures ne disent pas** : si c'est mieux à l'œil. Les règles viennent des commentaires d'Anaël et la conformité est mesurée sur les mêmes familles de règles : elle prouve que la consigne est suivie, pas qu'elle améliore la note.

## 2. Versions et dispositif
| Élément | Valeur |
|---|---|
| Claude Code, modèle | `claude -p`, `claude-sonnet-5-5`, effort `medium` ; plafond 1,5 $ par exécution (T7 : 6 $) |
| `frontend-design` | anthropics/skills, commit `dbd4588f9e1033efb41dad4bef2f7947c8993d44`, copie octet pour octet de celle de T7, installée dans `.claude/skills/` de chaque bras (jamais au niveau utilisateur) |
| `DESIGN.md` | inchangé, sha256 `ec7376fb644b6bc47b421ef9c4675a93b38f952b6a7a85e49f3edd920d1c1e22`, copié à la racine des bras b5 |
| Énoncés | `tache-ecran1.md` (identique à `T7/scripts/tache.md`, sha256 `047054a8…92ed`), `tache-ecran2.md` (sha256 `d8feb3d2…34c4`) |
| Application de base | écran 1 : `base1` = base de T7 (FastAPI 0.162, Jinja2 3.1.6, `/demandes` en liste brute, `SERVICES`, `DEMANDES` : six lignes), reconstruite par copie depuis le dossier de travail de T7, qui existait encore ; écran 2 : `base2` écrite pour ce test (`/notes-de-frais` en liste brute, `CATEGORIES`, `STATUTS`, `NOTES` : huit lignes), mêmes dépendances |
| Mesures | Playwright Python 1.64.1 sur Edge installé (`channel="msedge"`, comme en T7), axe-core 4.13.0, `impeccable detect` moteur 0.1.17 (sha256 `edb62bff…f94ee`, identique à T7) |
| Téléchargements | aucun : Playwright et Pillow viennent du cache `uv` (`--offline`), Edge est déjà installé, axe-core et le moteur sont copiés depuis T7 |

Les flux `stream-json` et les captures sont restés dans le scratchpad ; `donnees/` ne contient que des métadonnées résumées et des mesures par page (aucun chemin local à anonymiser n'y était présent : les deux scripts d'anonymisation ont été passés, 0 remplacement).

## 3. Mesures par bras et par écran (3 essais chacun)
| | b2 écran 1 | b5 écran 1 | b2 écran 2 | b5 écran 2 |
|---|---|---|---|---|
| Coût moyen (USD) | 0,325 | 0,317 | 0,330 | 0,329 |
| Fourchette | 0,31 à 0,35 | 0,31 à 0,33 | 0,27 à 0,36 | 0,31 à 0,36 |
| Durée moyenne | 101 s | 98 s | 101 s | 102 s |
| Tours | 16,3 | 14,7 | 17,0 | 16,7 |
| Tokens de sortie | 17,5 k | 16,9 k | 17,7 k | 16,8 k |
| Tokens d'entrée (cache compris) | 183 k | 176 k | 190 k | 241 k |
| Skill invoquée | 3/3 | 3/3 | 3/3 | 3/3 |
| `DESIGN.md` lu | n/a | 3/3 | n/a | 3/3 |
| Refus de permission par exécution | 1,0 | 1,0 | 1,0 | 1,3 |
| Contrat fonctionnel complet (30 ou 38 points) | 3/3 | 2/3 | 2/3 | 3/3 |
| Violations axe-core (nœuds) | 0 | 0 | 0 | 1 (1 rendu) |
| `impeccable detect` (rendus avec constat) | 1/3 | 2/3 | 0/3 | 1/3 |
| Débordement horizontal à 390 px | non | non | non | non |
| Éléments sans focus visible (1280) | 0 | 0 | 0 | 0 |
| Contraste, ratio minimal | 5,9 à 6,5 | 5,3 à 6,4 | 5,2 à 5,9 | 5,3 à 6,7 |
| Poids CSS moyen (octets) | 4 267 | 4 700 | 5 330 | 5 672 |
| Requêtes externes | 0 | 0 | 0 | 0 |

Coût par exécution : b2 écran 1 0,308 / 0,319 / 0,346 ; b5 écran 1 0,316 / 0,308 / 0,326 ; b2 écran 2 0,364 / 0,352 / 0,275 ; b5 écran 2 0,359 / 0,307 / 0,321. Les tokens d'entrée de b5 sur l'écran 2 sont plus élevés (+27 %, soit la lecture du fichier et plus de tours de cache) sans effet sur le coût total. Données : `donnees/design_runs.json`, `design_resume.json`, `runs_design/`, `mesures_pages/`.

## 4. Coûts
| | Total | Moyenne par essai | Écart b5 contre b2 |
|---|---|---|---|
| b2 (6 essais) | 1,965 $ | 0,3274 $ | référence |
| b5 (6 essais) | 1,937 $ | 0,3228 $ | **−1,4 %** |
| Écran 2 seul | b2 0,991 $ ; b5 0,987 $ | 0,330 $ ; 0,329 $ | −0,4 % |
| **Total du test** | **3,90 $** | | |

Aucune autre session `claude -p` n'a été lancée (pas de sonde). Critère de décision n° 3 (surcoût au plus 10 %) : **rempli**.

## 5. Conformité aux règles de `DESIGN.md` (indicatif)
Nombre de rendus conformes sur le nombre de rendus où la règle est applicable (3 par bras et par écran) :

| Règle | b2 écran 1 | b5 écran 1 | b2 écran 2 | b5 écran 2 |
|---|---|---|---|---|
| R1 Bloc d'alerte sans bordure ni contour colorés | 0/3 | 3/3 | 0/3 | 3/3 |
| R1 bis Bloc d'alerte en haut du formulaire | 0/3 | 3/3 | 0/3 | 3/3 |
| R2 Champ invalide : bordure rouge, pas de fond rouge | 1/3 | 3/3 | 0/3 | 3/3 |
| R3 Action principale en haut et marquée | 3/3 | 3/3 | 3/3 | 3/3 |
| R4 Lignes alternées | 2/3 | 3/3 | 0/3 | 3/3 |
| R4 bis En-têtes distincts | 3/3 | 3/3 | 3/3 | 3/3 |
| R5 Colonne d'identité en gras | 1/3 | 3/3 | 3/3 | 3/3 |
| R6 Montants à droite, chiffres tabulaires | 3/3 | 3/3 | 3/3 | 3/3 |
| R7 Catégories en étiquettes, une couleur par valeur | 0/3 | 3/3 | 0/3 | 2/3 |
| R8 Même police et mêmes styles de libellé à 390 et 1280 px | 3/3 | 3/3 | 3/3 | 3/3 |
| R9 Pas trop sobre (au moins deux familles de teintes) | 0/3 | 3/3 | 3/3 | 3/3 |
| **Score moyen** | 48 % | 100 % | 55 % | 97 % |

Lecture :
1. **Les règles sont suivies, y compris sur l'écran 2.** Les écarts viennent de R1, R2, R4, R7 et R9 : en b2, le bloc d'alerte a systématiquement une bordure d'accent (6 sur 6, avec en général une bordure gauche épaisse) et les champs invalides ont un fond teinté de rouge (5 sur 6) ; en b5, ni l'un ni l'autre.
2. **R3, R4 bis, R6 et R8 ne départagent pas** : déjà respectées par b2 (ou presque) ; la skill seule suffit.
3. **Le détecteur d'impeccable ne reproduit pas R1** : il signale `border-accent-on-rounded` plus souvent en b5 (2 rendus) qu'en b2 (1 rendu), alors que le contrôle direct du bloc d'alerte donne 6/6 pour b5. L'écart tient à l'objet : le détecteur regarde tout élément arrondi à bordure d'accent (carte du formulaire, tableau), pas seulement le bloc d'alerte. Un point à regarder sur les captures lors de la note.
4. **Limites du contrôle** : seuils de couleur arbitraires (section 9 du protocole), pseudo-éléments non lus, R3 (position) et R7 (étiquette) approximatifs. Le contrôle de R1 compte aussi un contour de focus porté par le bloc d'alerte (observé deux fois en b2, sans effet sur le résultat car une bordure colorée y était déjà). Les 11 contrôles reprennent les formulations de `DESIGN.md` ; qu'un rendu les respecte tous ne dit rien d'un défaut non codifié (un 12e problème visuel serait invisible ici).

## 6. Note à l'aveugle
`notation.html` : 12 rendus, 8,4 Mo, groupés par écran (écran 1 : lettres A à F ; écran 2 : lettres G à L), lettres tirées par `secrets` à l'intérieur de chaque écran, cinq vues par rendu (1280, 768 et 390 px à l'état initial ; 1280 et 390 px après un envoi invalide), trois grilles de 1 à 5, commentaire facultatif, sauvegarde locale, export `notes-t7ter.json`. La correspondance est dans `correspondance.json`, listée dans `.gitignore` avant sa création, non référencée par la page et **non ouverte**. Aucune capture n'a été regardée pour la juger.

**Résultat** (export d'Anaël, `donnees/notes-anael.json`, dépouillé par `uv run --no-project python scripts/notes.py donnees/notes-anael.json`) :

| Bras | Écran | lisibilité | finition | cohérence | moyenne |
|---|---|---|---|---|---|
| b2 `frontend-design` | 1 | 3,67 | 3,67 | 4,00 | 3,78 |
| b5 + `DESIGN.md` | 1 | **5,00** | **4,33** | **4,67** | **4,67** |
| b2 `frontend-design` | 2 | 4,00 | 3,67 | **4,67** | 4,11 |
| b5 + `DESIGN.md` | 2 | **4,33** | **4,00** | 4,33 | **4,22** |

Écart b5 − b2 (paires par essai, intervalle de bootstrap à 95 %) :
- écran 1 : **+0,89** [+0,33 ; +1,67] ;
- écran 2 : **+0,11** [−0,67 ; +1,00], cohérence −0,33 [−2,00 ; +1,00] ;
- deux écrans : +0,50 [−0,11 ; +1,06], lisibilité +0,83 [+0,33 ; +1,33].

Lecture :
1. **Sur l'écran 1, les règles marchent** : les trois rendus b5 sont notés 4,67, contre 3,00 à 4,33 pour b2. Les commentaires citent exactement ce que les règles demandaient : tableau aux en-têtes colorés, étiquettes de service, demandeur en gras, lignes alternées. Mais ces règles viennent de cet écran, donc ce gain ne prouve pas qu'elles valent ailleurs.
2. **Sur l'écran 2, le gain disparaît** (+0,11), et la cohérence baisse à cause d'un rendu (K, cohérence 3). Il a donné le même style d'étiquette aux colonnes Catégorie et Statut, « au risque de confondre ». Le meilleur rendu de l'écran 2 est un b5 (L, 4,67 : « respectant tous mes retours précédents »), mais l'écart de qualité entre les rendus b5 est plus grand que l'écart entre les deux bras.
3. **Trois règles ont des effets de bord que les commentaires révèlent** :
   - **Récapitulatif des erreurs** : « pas de contour coloré » a donné un bloc gris ou neutre, jugé « moins marquant » (C, E) et « pas dans la bonne couleur pour indiquer qu'il y a une erreur » (K). Anaël suggère un fond rouge clair (H). La règle doit dire : teinte d'erreur légère, sans bordure d'accent.
   - **Action principale en haut** : elle a fait ajouter un bouton « Nouvelle note » en double alors que le formulaire est déjà sur la page (H, L : « à quoi sert ce bouton ? »). La règle doit exclure le doublon.
   - **Étiquettes de catégorie** : une couleur par valeur, mais pas la même palette pour deux colonnes de catégories différentes (K, L).
4. **Il manque deux règles**, demandées plusieurs fois :
   - séparer les sections de façon marquée et identique entre blocs voisins (F, H, L) ;
   - pour les totaux et les chiffres clés, une police lisible pour les nombres, avec des libellés assez grands (G, I, H, K).
5. **Ce qui n'a pas changé de b2 à b5** : le fond rouge de tous les champs en erreur, « stressant », reste propre à b2 (B, D, I, G). La règle qui l'interdit est confirmée.

Biais et limites : Anaël est l'auteur des règles, et chaque cellule n'a que 3 rendus. L'intervalle de l'écran 2 va de −0,67 à +1,00 : le test n'exclut ni un gain réel de 0,5 ni une perte.

Méthode du script : il croise l'export avec `correspondance.json`, donne les moyennes par bras, écran et critère, l'écart b5 − b2 avec intervalle de bootstrap (paires par écran et par essai, 6 paires, ou 3 pour l'écran 2 seul : intervalle très large) et applique le critère de décision du protocole. Le script a été testé sur des notes et une correspondance factices (non conservées).

## 7. Critère de décision (protocole, section 7)
| Condition | État |
|---|---|
| 1. b5 gagne au moins 0,5 point de moyenne sur l'écran 2 | **non rempli (+0,11)** |
| 2. Cohérence de b5 sur l'écran 2 non inférieure à celle de b2 | **non rempli (−0,33, un rendu)** |
| 3. Surcoût de b5 au plus 10 % par essai | **rempli (−1,4 %)** |

L'écran 1 est indicatif seulement. Les mesures automatiques (conformité 98 % contre 52 %, surcoût nul) rendent plausible un gain, mais ne le prouvent pas : T7 a montré que des défauts mesurables à zéro et un détecteur ne prédisaient pas la note.

## 8. Limites
- **Un juge, qui est l'auteur des règles** : il reconnaîtra peut-être l'effet des règles (bloc d'alerte sans contour, champs sans fond rouge), ce qui joue en faveur de b5. À signaler dans la lecture de la note.
- **Trois rendus par cellule** : écart de 0,33 au plus entre deux rendus d'un même bras en T7 ; un gain de 0,5 est à peine au-dessus du bruit attendu. L'appariement par numéro d'essai est une convention.
- **La consigne nomme le fichier** : on mesure l'effet d'une règle appliquée sur demande explicite. Un `DESIGN.md` que l'agent devrait découvrir (sans le nommer) n'est pas testé ; la veille signale par ailleurs une lecture de fichiers de référence très partielle.
- **Les agents lisent `DESIGN.md` par `cat`** (Bash), jamais par l'outil `Read` ; les deux sont couverts par la détection.
- **Les deux écrans partagent la même architecture** (FastAPI + Jinja2, formulaire + tableau + filtres) : la généralisation testée est celle à un autre contenu, pas à une autre structure (fiche, tableau de bord).
- **Pas de boucle de vérification** pour les agents (aucun serveur ni navigateur permis), comme en T7.
- **Le contrat n'a pas réellement séparé les bras** : défaut `confirmation_unique` une fois par bras, sans lien avec `DESIGN.md`.

## 9. Écarts au protocole
1. Plafond par exécution à 1,5 $ au lieu de 6 $ (budget global de 6 $) ; aucune exécution ne l'a approché (maximum 0,364 $).
2. Seuils de couleur et détection de lecture de `DESIGN.md` précisés pendant l'exécution (protocole, section 9), avant toute note.
3. Le dossier de travail de T7 (`base`, `vendor`, `tools`, `mesures`) existait encore dans le scratchpad, contrairement à ce qu'annonçait la consigne : base, skill, axe-core et moteur en ont été copiés (aucun fichier de T7 modifié ni supprimé), à la place d'une reconstruction.
4. Écran 2 : 38 points de contrat (l'estimation de départ de 33 du premier jet du protocole a été corrigée avant les mesures).
5. `scripts/chemins.py` exige la variable `T7TER_TRAVAIL` (dossier de travail) pour ne pas écrire de chemin local dans le dépôt.

## 10. Ce qu'Anaël devait faire (fait le 2026-10-25)
1. Ouvrir `tests-pratiques/T7ter-design-md/notation.html` dans un navigateur, noter les 12 rendus (lisibilité, finition, cohérence, de 1 à 5), cliquer sur « Exporter mes notes ».
2. Enregistrer l'export sous `tests-pratiques/T7ter-design-md/donnees/notes-anael.json`, puis lancer `uv run --no-project python scripts/notes.py donnees/notes-anael.json`.
3. Ne pas ouvrir `correspondance.json` avant d'avoir noté.
4. Décider (critère du protocole, section 7) : garder, retravailler ou écarter `DESIGN.md`. Si les gains sont sur l'écran 1 seulement, l'effet vient des règles apprises sur cet écran, pas d'une généralisation.
5. Rien d'autre n'attend Anaël : aucun téléchargement n'a été fait.

## 11. Fichiers
- `protocole.md`, `tache-ecran1.md` (copie de T7), `tache-ecran2.md`, `DESIGN.md` (inchangé), `notation.html`, `correspondance.json` (ignoré par git).
- `scripts/` : `chemins.py`, `preparer_bras.py`, `lancer_claude.py`, `lancer_bras.py`, `mesure_page.py` + `conformite.js`, `mesurer_tout.py`, `agreger.py`, `generer_notation.py`, `notes.py`, `verifier_vocabulaire.py`, `pyproject-mesures.toml` et `uv-mesures.lock` (environnement de mesure).
- `donnees/` : `design_runs.json`, `design_resume.json`, `runs_design/` (méta par exécution), `mesures_pages/` (une mesure par rendu).
