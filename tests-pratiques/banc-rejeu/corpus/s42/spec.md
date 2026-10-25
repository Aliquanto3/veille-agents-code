# Story 4.2

## Énoncé (epics.md)

### Story 4.2 : Risque d'entrée en rouge

As a Pilote,
I want être prévenu qu'une Entité non rouge risque de franchir un seuil rouge la semaine prochaine,
So that j'agis avant qu'elle ne passe au rouge.

**Exigences :** FR-21, NFR-1 · **AD :** AD-9, AD-18

**Acceptance Criteria:**

**Given** les séries d'IND-1, IND-3 et IND-4 d'une Entité non rouge sur 10 Jours ouvrés
**When** le domaine calcule la régression linéaire projetée à 5 Jours ouvrés (H-8)
**Then** un `RisqueEntreeRouge` est émis si une projection franchit un seuil rouge, en nommant l'indicateur concerné et la valeur projetée

**Given** IND-4 non évaluable sur une partie de la fenêtre
**When** le risque est calculé
**Then** IND-4 est exclu de la projection, avec le motif restitué

## Spécification d'implémentation

## Intent

**Problem:** FR-21 n'a aucune implémentation : le Pilote n'est pas prévenu qu'une Entité non rouge risque de franchir un seuil rouge la semaine prochaine (H-8 : 5 Jours ouvrés).

**Approach:** une fonction pure `risques_entree_rouge(indicateurs, meteo, grille, parametres)` dans `src/usine/domaine/prevision/risque.py` : régression linéaire exacte (moindres carrés, `Fraction`) sur les 10 derniers Jours ouvrés d'IND-1, IND-3 et IND-4 de l'Entité, projetée de 1 à 5 Jours ouvrés après D ; un `RisqueEntreeRouge` par indicateur dont une projection déclenche la règle rouge de la Grille, accompagné de la valeur projetée ; les indicateurs écartés (non évaluables sur la fenêtre, historique insuffisant, sans seuil rouge actif) sont restitués avec leur motif. Paramètres H-8 dans un `ParametresRisque` (fenêtre 10, horizon 5). Les primitives partagées avec la Baseline (avance de Jours ouvrés, test de déclenchement d'un seuil) passent dans un module commun (AD-18 : une seule implémentation par calcul).

## Boundaries & Constraints

**Always:** arithmétique exacte (`Fraction`) ; Jours ouvrés par `contrats.calendrier` seulement ; seuil et opérateur rouges lus dans `grille.indicateurs[code].seuils[Couleur.rouge]` ; `date_arrete`, `entite`, `version_grille` repris de la `MeteoEntite` ; `RisqueEntreeRouge.numerateur/denominateur` = valeur de l'indicateur à D (docstring du contrat gelé : « Valeur courante ») ; résultats dans l'ordre de `CodeIndicateur` ; fonction pure, déterministe, sans horloge ni hasard.

**Never:** modifier `src/usine/contrats/`, `src/usine/ports/`, `config/` ou la Chaîne ; seconde implémentation de la Baseline ou de la vélocité nette ; projeter un autre indicateur qu'IND-1, IND-3, IND-4 ; numpy ou flottants.

## I/O & Edge-Case Matrix

Table `SCHEMA_INDICATEUR` d'ENT-C sur 10 Jours ouvrés finissant à D ; Météo orange ; Grille par défaut (rouge : IND-1 `>= 3`, IND-3 `>= 20`, IND-4 `>= 1/5`) ; paramètres par défaut. x = 0..9 rang du Jour ouvré, projection à x = 9 + h, h = 1..5.

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Franchissement IND-3 | IND-3 = 10, 11, …, 19 | risque IND-3 : franchissement à D + 1 JO, valeur projetée 20, valeur courante 19/1, seuil 20/1 | — |
| Tendance non linéaire IND-1 | IND-1 = 0,0,0,0,0,1,1,1,2,2 | pente 41/165, ordonnée −23/55 ; h = 4 → 464/165 < 3 ; h = 5 → 101/33 ≥ 3 : risque IND-1 à D + 5 JO, valeur projetée 101/33 | — |
| Hausse insuffisante IND-4 | IND-4 = 5/100, …, 14/100 | h = 5 → 19/100 < 1/5 : aucun risque IND-4 | — |
| Stable ou en baisse | séries constantes ou décroissantes | aucun risque | — |
| IND-4 non évaluable en partie | IND-4 `non_evaluable` (0/0, motif m) sur un JO de la fenêtre | IND-4 exclu, motif nommant la première date et m ; IND-1 et IND-3 projetés | — |
| Historique court | 1 seul JO pour un indicateur | indicateur exclu (« historique insuffisant ») ; 2 à 9 JO : régression sur les JO présents | — |
| Indicateur inactif ou sans seuil rouge | IND-3 `active: false` ou sans seuil rouge | IND-3 exclu avec motif, sans lecture de la table | — |
| Entrées invalides | Météo rouge, D absente pour un indicateur actif, trou ou date non ouvrée, doublon, valeur évaluée de dénominateur 0, paramètre < 1 | — | `UsineErreur` nommant l'Entité et la cause |

## Code Map
- `src/usine/contrats/prevision.py` -- `RisqueEntreeRouge` (indicateur ∈ {IND-1, IND-3, IND-4}, `date_franchissement_estimee > date_arrete`, `numerateur/denominateur` = valeur courante, seuil, `horizon_jours_ouvres`, `version_grille`). Gelé.
- `src/usine/contrats/calcul.py:72` -- `SCHEMA_INDICATEUR` (date, entite, code, statut, motif, numerateur, denominateur, couleur) ; `StatutIndicateur.non_evaluable` = 0/0 avec motif. Gelé.
- `src/usine/contrats/config.py:167-205` -- `GrilleMeteo.indicateurs[code]` → `RegleIndicateur(active, seuils: Couleur → (Operateur, Fraction))`. Gelé.
- `src/usine/contrats/meteo.py` -- `MeteoEntite`, `CodeIndicateur`, `Couleur`, `Operateur`. Gelé.
- `src/usine/contrats/calendrier.py:48-64` -- `est_jour_ouvre`, `jour_ouvre_suivant`.
- `src/usine/domaine/meteo.py:471` -- `indicateurs()` produit la table par date ; modèle du test de franchissement.
- `src/usine/domaine/prevision/baseline.py` -- `_avancer` et la comparaison de seuil IND-1 (ligne `rouge = …`) à déplacer dans le module commun ; validation de série par `_jours` à imiter.
- `tests/unit/domaine/prevision/test_baseline.py:416` -- test d'unicité AD-18, à garder vert.
- `.github/scripts/controle_lanes.py:59` -- lane 4 : `src/usine/domaine/prevision`, `evaluation`.

## Tasks & Acceptance
**Execution:**
- `src/usine/domaine/prevision/commun.py` -- `avancer(jour, n)` (Jours ouvrés) et `declenche(valeur, operateur, seuil)` (Fractions) -- primitives uniques partagées.
- `src/usine/domaine/prevision/baseline.py` -- utiliser `commun.avancer` et `commun.declenche` à la place de `_avancer` et de la comparaison locale, sans changement de comportement.
- `src/usine/domaine/prevision/risque.py` -- `ParametresRisque` (dataclass gelée : `fenetre=10`, `horizon=5`, entiers ≥ 1), `RisqueProjete(risque: RisqueEntreeRouge, valeur_projetee: Fraction)`, `IndicateurExclu(code, motif)`, `ResultatRisque(risques, exclus)` et `risques_entree_rouge(indicateurs: pl.DataFrame, meteo: MeteoEntite, grille: GrilleMeteo, parametres: ParametresRisque = ParametresRisque()) -> ResultatRisque` selon la matrice et les Design Notes.
- `tests/unit/domaine/prevision/test_risque.py` -- un test par ligne de la matrice, valeurs exactes calculées à la main ; validité des `RisqueEntreeRouge` (horizon 5, version de Grille) ; déterminisme (deux appels égaux, table non mutée) ; source sans `now(`, `today(`, `random` ; `commun` seul à définir `avancer` dans `domaine/prevision`.

**Acceptance Criteria:**
- Given les séries d'IND-1, IND-3 et IND-4 d'une Entité non rouge sur 10 Jours ouvrés, when `risques_entree_rouge` s'exécute avec les paramètres H-8, then un `RisqueEntreeRouge` est émis pour chaque indicateur dont la projection franchit le seuil rouge dans les 5 Jours ouvrés, avec l'indicateur, la date de franchissement et la valeur projetée (`RisqueProjete.valeur_projetee`).
- Given IND-4 non évaluable sur une partie de la fenêtre, when le risque est calculé, then IND-4 est absent des risques et présent dans `exclus` avec un motif qui reprend celui de l'indicateur.
- Given les tests de la Story 4.1, when ils s'exécutent après la mise en commun, then ils restent verts.
- Given les cinq contrôles, then ruff, ruff format, mypy, lint-imports et pytest passent, et `controle_lanes.py --branche lane/4-prevision --base main` réussit.

## Design Notes
**Régression.** Sur la fenêtre (les `fenetre` derniers JO de la table finissant à D pour l'Entité et l'indicateur, n ≥ 2 points, x = 0..n−1) : b = Σ(x − x̄)(y − ȳ) / Σ(x − x̄)², a = ȳ − b·x̄ ; projection p(h) = a + b·(n − 1 + h). Premier h ∈ [1, horizon] où `declenche(p(h), op, seuil)` → risque : `date_franchissement_estimee = avancer(D, h)`, `valeur_projetee = p(h)`. Une valeur évaluée vaut `numerateur/denominateur` (dénominateur > 0).

**Pourquoi pas la vélocité de la Baseline.** FR-21 et l'addendum § E fixent une régression linéaire sur les séries d'indicateurs (dont IND-3 et IND-4, sans `SerieStock`) ; la vélocité nette (Σ(Sorties − Entrées)/n sur `SerieStock`) n'a pas de sens pour un taux de KO. AD-18 reste tenu : la vélocité n'est pas réécrite, la Baseline n'a pas de variante, et les primitives communes (avance en Jours ouvrés, test de seuil) n'existent qu'une fois, dans `commun`.

**Valeur projetée hors contrat.** Le contrat gelé `RisqueEntreeRouge` porte la valeur courante, pas la valeur projetée : celle-ci est rendue à côté (`RisqueProjete`). Sa publication dans `previsions.json` exigera un champ de contrat (contrats-v2) : différé à consigner.

**Paramètres hors configuration.** Comme H-7 en Story 4.1 : `contrats/config.py` est gelé, H-8 vit dans `ParametresRisque` jusqu'au branchement de l'étape `prevision` (L5).

**Précondition.** La table couvre chaque JO de la fenêtre (la Chaîne publie les indicateurs de chaque JO ≤ D) ; lignes postérieures à D ignorées.
