### Story 4.10 : Statistiques : bootstrap, McNemar et fronts de Pareto

As a Anaël,
I want des intervalles de confiance et des comparaisons appariées reproductibles,
So that je sache si une différence entre deux Configurations est réelle.

**Exigences :** FR-39, FR-40 (fronts de Pareto) ; AD-20, AD-22 (`stats/` en fonctions pures) ; `contracts.md` §7.

**Acceptance Criteria:**

**Given** `stats/bootstrap.py` et un vecteur binaire de 100 valeurs avec 70 succès
**When** on calcule l'IC à 95 % avec 2 000 rééchantillons et la graine 42
**Then** l'IC par percentile reproduit, à 1e-9 près, celui de `scipy.stats.bootstrap(method="percentile")` avec le même générateur
**And** deux appels avec la même graine donnent le même IC

**Given** deux vecteurs appariés de scores continus
**When** on lance le bootstrap apparié
**Then** la différence moyenne, son IC et la p-valeur bilatérale sont renvoyés, et les valeurs se reproduisent sur des données synthétiques connues

**Given** `stats/mcnemar.py` et des paires discordantes b = 12 et c = 3
**When** on calcule le test exact
**Then** la p-valeur égale `scipy.stats.binomtest(3, 15, 0.5).pvalue`, et b = c = 0 donne une p-valeur de 1

**Given** `compare(a, b)` sur deux ensembles de Questions qui ne se recouvrent qu'en partie
**When** on compare
**Then** seules les Questions communes sont utilisées, et `n_common` est renvoyé

**Given** `stats/pareto.py` et cinq points (Qualité, coût), dont un dominé et deux à égalité
**When** on calcule le front
**Then** il contient les points non dominés (Qualité maximisée, coût minimisé), dans un ordre déterministe, ex æquo départagés par `config_id`
