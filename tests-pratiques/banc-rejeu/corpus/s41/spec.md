# Story 4.1

## Énoncé (epics.md)

### Story 4.1 : Prévision de sortie du rouge par Baseline

As a Pilote,
I want savoir, pour chaque Entité rouge, quand elle devrait sortir du rouge, avec une fourchette, une probabilité et les facteurs qui l'expliquent,
So that je réponds au comité « quand est-ce que ça repasse ? » avec des faits.

**Exigences :** FR-20, NFR-1 · **AD :** AD-9, AD-17, AD-18

**Acceptance Criteria:**

**Given** une `SerieStock` d'Entité (stock de bloquantes ouvertes, Entrées, Sorties par Jour ouvré) et IND-1 rouge
**When** `domaine.prevision.baseline` s'exécute avec une vélocité sur 10 Jours ouvrés et un horizon de 10 Jours ouvrés (configuration, H-7)
**Then** il renvoie une `Prevision` (`methode=baseline`) avec la date de sortie estimée (premier Jour ouvré où le stock projeté passe sous le seuil rouge d'IND-1), la fourchette des vélocités au 25ᵉ et 75ᵉ centile des fenêtres de 5 Jours ouvrés sur 20 jours, la probabilité empirique de sortie dans l'horizon et les facteurs explicatifs (stock, Entrées, Sorties, vélocité nette et sa variation)

**Given** une vélocité nette nulle ou défavorable
**When** la Baseline s'exécute
**Then** la `Prevision` porte « pas de sortie projetée », sans date

**Given** une Entité rouge aussi par IND-5
**When** la Baseline s'exécute
**Then** aucune date n'est produite et la `Prevision` porte « règle non projetable : IND-5 »

**Given** la fonction
**When** on l'inspecte
**Then** elle est pure, sans horloge ni hasard, et c'est la seule implémentation de la Baseline du dépôt (AD-18)

## Spécification d'implémentation

## Intent

**Problem:** FR-20 n'a aucune implémentation : le Pilote ne sait pas quand une Entité rouge devrait sortir du rouge. AD-18 exige une Baseline unique, dans `domaine.prevision.baseline`, sur le contrat gelé `SerieStock`, réutilisée telle quelle par l'évaluation Zenodo (Story 4.4).

**Approach:** une fonction pure `prevoir_sortie(serie, meteo, parametres)` dans `src/usine/domaine/prevision/baseline.py` qui renvoie une `Prevision` (`methode=baseline`) selon l'addendum PRD § E : vélocité nette moyenne sur 10 Jours ouvrés, date de sortie projetée, fourchette par centiles des fenêtres de 5 Jours ouvrés sur 20, probabilité empirique dans l'horizon, facteurs explicatifs. Paramètres H-7 dans un `ParametresBaseline` à valeurs par défaut (10/10/5/20).

## Boundaries & Constraints

**Always:** arithmétique exacte (`Fraction`, sorties en numérateur/dénominateur entiers) ; Jours ouvrés par `contrats.calendrier` seulement ; seuil rouge d'IND-1 lu dans la `RegleDeclenchante` IND-1 rouge de la `MeteoEntite` (opérateur et seuil) ; « sous le seuil » = la règle ne se déclenche plus (`>=` : stock < seuil ; `>` : stock ≤ seuil) ; `version_grille`, `date_arrete`, `entite` repris de la `MeteoEntite` ; fonction pure, déterministe, sans horloge ni hasard.

**Never:** modifier `src/usine/contrats/`, `src/usine/ports/`, `config/` ou la Chaîne (`chaine/`, `composition.py`) ; seconde implémentation de la Baseline ; Risque d'entrée en rouge (Story 4.2) ; Modèle ML ; numpy ou statistiques flottantes.

## I/O & Edge-Case Matrix

Série ENT-A dense sur 20 Jours ouvrés finissant à la Date d'arrêté D ; IND-1 rouge `>= 3` ; paramètres par défaut.

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Sortie projetée | S = 6 à D, Sorties − Entrées = 6 sur les 10 derniers JO (v = 3/5) | `sortie_projetee` ; t = 5 JO (6 − 3/5·5 = 3, encore rouge ; t = 6 → 2,4 < 3 → t = 6) donc date = D + 6 JO ; fourchette optimiste ≤ estimée ≤ pessimiste ; probabilité = part des fenêtres de 5 JO dont la vélocité ramène sous le seuil en ≤ 10 JO ; 5 facteurs | — |
| Vélocité nulle | Entrées = Sorties sur 10 JO | `pas_de_sortie_projetee`, aucune date, probabilité empirique conservée | — |
| Vélocité défavorable | Entrées > Sorties | `pas_de_sortie_projetee`, aucune date | — |
| Règle non projetable | Météo rouge par IND-1 et IND-5 | `regle_non_projetable`, `regles_non_projetables = (IND-5,)`, aucune date, probabilité 0/1, facteurs calculés | — |
| Rouge par IND-5 seul | aucune règle IND-1 | `regle_non_projetable` (IND-5) | — |
| Historique court | 7 JO de série seulement | vélocité sur les JO disponibles (dénominateur = nombre de JO présents) ; fenêtres de 5 JO complètes seulement ; sans fenêtre complète : la fenêtre de vélocité sert de fenêtre unique | — |
| Pessimiste non projetable | centile 25 de vélocité ≤ 0, v > 0 | `date_sortie_pessimiste = None`, optimiste et estimée renseignées | — |
| Entrées invalides | Météo non rouge, D absente de la série, trou de JO dans la série, date non ouvrée ou en double, paramètre < 1 | — | `UsineErreur` nommant l'Entité et la cause |

## Code Map
- `src/usine/contrats/prevision.py` -- `SCHEMA_SERIE_STOCK` (serie, date, stock, entrees, sorties), `Prevision` (validateur : date ssi projetée, ordre optimiste ≤ estimée ≤ pessimiste, dates > D, `regle_non_projetable` ssi liste non vide), `FacteurExplicatif`, `MethodePrevision`, `StatutPrevision`. Gelé, lecture seule.
- `src/usine/contrats/meteo.py` -- `MeteoEntite` (couleur, regles, version_grille), `RegleDeclenchante` (operateur, seuil_numerateur/denominateur), `CodeIndicateur`, `Operateur`, `Couleur`. Gelé.
- `src/usine/contrats/calendrier.py:58-100` -- `jour_ouvre_suivant`, `jour_ouvre_precedent(d, n)`, `jours_ouvres`, `est_jour_ouvre`.
- `src/usine/contrats/schemas.py:47` -- `valider(df, schema)` ; `src/usine/contrats/erreurs.py` -- `UsineErreur`.
- `src/usine/domaine/kpi.py` -- modèle de style d'un module pur du domaine (docstring, Fractions).
- `pyproject.toml:143` -- contrat import-linter « domaine : contrats seulement » (numpy, io, time, random interdits).
- `.github/scripts/controle_lanes.py` -- lane 4 : `src/usine/domaine/prevision`, `evaluation`, `tests/unit/domaine/prevision`.

## Tasks & Acceptance
**Execution:**
- `src/usine/domaine/prevision/__init__.py` -- docstring du paquet (Prévision statistique, AD-18), sans réexport.
- `src/usine/domaine/prevision/baseline.py` -- `ParametresBaseline` (dataclass gelée : `fenetre_velocite=10`, `horizon=10`, `fenetre_fourchette=5`, `profondeur_fourchette=20`, chacun ≥ 1) et `prevoir_sortie(serie: pl.DataFrame, meteo: MeteoEntite, parametres: ParametresBaseline = ParametresBaseline()) -> Prevision` selon la matrice et les Design Notes.
- `tests/unit/domaine/prevision/__init__.py`, `tests/unit/domaine/prevision/test_baseline.py` -- un test par ligne de la matrice, valeurs exactes calculées à la main ; test de déterminisme (deux appels égaux, série non mutée) ; test que le module n'utilise ni horloge ni hasard (source sans `now(`, `today(`, `random`) ; test que `prevoir_sortie` et le nom « baseline » ne sont définis comme fonction qu'une fois dans `src/` et `evaluation/` (AD-18).

**Acceptance Criteria:**
- Given une `SerieStock` d'Entité et IND-1 rouge, when `prevoir_sortie` s'exécute avec les paramètres H-7, then la `Prevision` porte `methode=baseline`, `horizon_jours_ouvres=10`, la date estimée, la fourchette, la probabilité et les facteurs `stock`, `entrees`, `sorties`, `velocite_nette`, `variation_velocite`.
- Given la fonction, when on l'inspecte, then elle est pure et c'est la seule implémentation de la Baseline du dépôt.
- Given les cinq contrôles, then ruff, ruff format, mypy, lint-imports et pytest passent, et `controle_lanes.py --branche lane/4-prevision --base main` réussit.

## Design Notes
**Formules (D = Date d'arrêté, S = stock à D).** Fenêtre de vélocité = les `fenetre_velocite` JO finissant à D, limités à ceux présents dans la série ; v = Σ(Sorties − Entrées) / nombre de JO. Variation = v − v_précédente (même calcul sur les JO précédant la fenêtre ; 0 si aucun). Jours à la sortie pour une vélocité w > 0 : `>=` → t = ⌊(S − seuil)/w⌋ + 1 ; `>` → t = ⌈(S − seuil)/w⌉ ; t ≥ 1 ; date = D avancée de t JO. Fenêtres de fourchette : toutes les fenêtres glissantes complètes de `fenetre_fourchette` JO incluses dans les `profondeur_fourchette` derniers JO (16 au plus) ; centiles 25 et 75 par interpolation linéaire exacte (méthode « type 7 ») sur les vélocités triées. Optimiste = date pour max(P75, v), pessimiste = date pour min(P25, v) si > 0, sinon `None` : l'ordre exigé par le contrat est garanti. Probabilité = nombre de fenêtres (w > 0 et t ≤ horizon) / nombre de fenêtres.

**Règle non projetable.** Toute Règle déclenchante rouge autre qu'IND-1 est non projetable (addendum § E, AC IND-5) ; aucune date, probabilité 0/1 (la sortie dépend d'une règle que la Baseline ne projette pas), facteurs conservés pour l'explication.

**Paramètres hors configuration.** H-7 place vélocité et horizon en configuration de la Chaîne, mais `contrats/config.py` est gelé (AD-19 : chaque fichier validé par un modèle de `contrats.config`). La fonction reçoit donc un `ParametresBaseline` ; le branchement à `config/chaine.yaml` se fera par une PR courte sur `main` lors de l'intégration de l'étape `prevision` (lane L5). Différé consigné.

**Évaluation (AD-18).** La Story 4.4 appellera `prevoir_sortie` avec une `MeteoEntite` construite pour le projet (règle IND-1 rouge au seuil du protocole) : aucune variante de la Baseline.
