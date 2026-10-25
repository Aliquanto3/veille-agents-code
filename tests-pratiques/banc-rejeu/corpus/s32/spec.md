# Story 3.2

## Énoncé (epics.md)

### Story 3.2 : KPI quotidiens

As a Pilote,
I want les stocks, flux, âges, taux et Certifications de chaque Entité et du Programme,
So that je n'ai plus à les recalculer dans Excel.

**Exigences :** FR-11, NFR-1 · **AD :** AD-9, AD-10, AD-17

**Acceptance Criteria:**

**Given** des Instantanés
**When** le domaine calcule les KPI
**Then** il produit, par Entité et pour le Programme : stock d'Anomalies ouvertes par Gravité et par Phase ; Entrées et Sorties du jour et sur la Fenêtre glissante ; âge médian et maximum des Anomalies ouvertes en Jours ouvrés depuis la dernière Entrée ; taux de KO et de non-exécution par Phase ; Certifications par statut
**And** Entrée, Sortie et Anomalie ouverte suivent les définitions du Glossaire `[HYPOTHÈSE H-17]`, la Fenêtre glissante vient de `contrats.calendrier` `[HYPOTHÈSE H-19]`

**Given** un taux
**When** on l'inspecte
**Then** il est porté en colonnes `numerateur` et `denominateur` entières, sans flottant (AD-10)

**Given** une Anomalie réouverte
**When** on calcule son âge
**Then** il part de la réouverture (dernière Entrée)

## Spécification d'implémentation

## Intent

**Problem:** FR-11 exige des KPI quotidiens par Entité et pour le Programme (stocks, flux, âges, taux, Certifications), mais `domaine/kpi` n'existe pas : `kpi.parquet` reste vide et le Pilote recalcule ces chiffres dans Excel.

**Approach:** Créer `domaine/kpi.py`, fonction pure `kpi(tickets_etats, entites)` qui produit une table `SCHEMA_KPI` dense (format long, une ligne par date, périmètre, code et dimension), en nombres entiers `numerateur`/`denominateur`, pour chaque Jour ouvré de la table d'états reçue.

## Boundaries & Constraints

**Always:** fonctions pures en Polars (AD-9) ; temps via `contrats.calendrier` seulement (`jour_ouvre_precedent`, `fenetre_glissante`, `jours_ouvres`, AD-17) ; définitions H-17 (Anomalie ouverte = statut hors `STATUTS_FERMES` ; Entrée = création ou réouverture, lue dans `date_derniere_entree` ; Sortie = passage à Fermée ou Rejetée) ; Fenêtre glissante H-19 ; aucun flottant (AD-10), taux en `numerateur`/`denominateur` ; sortie validée par `valider(…, SCHEMA_KPI)` ; erreurs en `UsineErreur`, message en français ; ordre des lignes déterministe.

**Never:** modifier `src/usine/contrats/`, `src/usine/ports/`, `src/usine/chaine/` (branchement de l'étape `kpi` : Epic 5, lane L5) ou `tests/unit/domaine/constructeur.py` ; ajouter une dépendance ; ajouter une énumération de codes de KPI dans `contrats` (D10 : `code_kpi` texte libre) ; Tendances, Indicateurs, Phase en cours ou Vague en cours (Stories 3.3 à 3.5).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Stock | 2 bloquantes ouvertes ENT-A, 1 majeure fermée ENT-B | `anomalies_ouvertes` ENT-A 2/1, ENT-B 0/1, PROGRAMME 2/1 ; `anomalies_ouvertes_gravite`/`bloquante` 2/1 ; `…/majeure` 0/1 | — |
| Flux du jour | lundi : création ; mardi : fermeture ; mercredi : réouverture puis fermeture | `entrees_jour` 1, 0, 1 ; `sorties_jour` 0, 1, 1 | — |
| Fenêtre | mouvements sur 7 Jours ouvrés | `entrees_fenetre` en D = somme des 5 Jours ouvrés finissant en D ; jours antérieurs à la table comptent 0 | — |
| Âge | 2 ouvertes, entrées jeudi 2026-10-01 et vendredi 2026-10-02, D = mercredi 2026-10-07 | âges 4 et 3 Jours ouvrés ; médiane `7/2` ; maximum `4/1` | — |
| Réouverture | créée J0, fermée J2, rouverte J5, D = J6 | âge 1 (part de J5) | — |
| Aucune ouverte | toutes fermées | âges médian et maximum `0/0` | — |
| Taux | recette : 3 OK, 1 KO, 2 non exécutés | `taux_ko_cas_de_test`/`recette` 1/4 ; `taux_non_execution_cas_de_test`/`recette` 2/6 ; Phase sans Cas de test 0/0 | — |
| Certifications | 1 accordée, 2 réservées | `certifications`/`accordee` 1/1, `reservee` 2/1, `refusee` 0/1 | — |
| Trou de dates | table avec lundi et mercredi, sans mardi | — | `UsineErreur` nommant la date manquante |
| Entités | `entites` en double ou égale à `PROGRAMME` | — | `UsineErreur` nommant la valeur |
| Table vide | aucune ligne | table vide au `SCHEMA_KPI` | — |

## Code Map
- `src/usine/domaine/kpi.py` -- à créer ; seul fichier source de la story.
- `src/usine/contrats/calcul.py` -- `SCHEMA_KPI` (l. 63, colonnes `date`, `perimetre`, `code_kpi`, `dimension`, `numerateur`, `denominateur`, toutes non nulles), `PERIMETRE_PROGRAMME` (lecture seule).
- `src/usine/contrats/tickets.py` -- `SCHEMA_TICKET_ETAT` (l. 203) : `date_derniere_entree` = Jour ouvré de la dernière Entrée, nulle hors Anomalies ; `STATUTS_FERMES`, `Gravite`, `Phase`, `StatutTest`, `StatutCertification`, `TypeTicket` (lecture seule).
- `src/usine/contrats/calendrier.py` -- `jour_ouvre_precedent`, `fenetre_glissante`, `jours_ouvres`, `est_jour_ouvre` (lecture seule).
- `src/usine/domaine/instantanes.py` -- `tickets_etats(evenements, dates)` produit l'entrée ; `instantane(etats)` sert au test de cohérence stock/Instantané.
- `src/usine/domaine/meteo.py:63-66` -- `_verifier_entites` : même contrôle de doublons à reproduire (pas d'import croisé nécessaire).
- `tests/unit/domaine/constructeur.py` -- `Flux` (`anomalie`, `transition`, `creer`, `modifier`) pour bâtir les flux (lecture seule).
- `tests/unit/domaine/test_kpi.py` -- à créer.

## Tasks & Acceptance
**Execution:**
- `src/usine/domaine/kpi.py` -- créer : constantes des codes (`CODES_KPI`, ordre figé) ; `kpi(tickets_etats, entites) -> pl.DataFrame` ; contrôles (dates contiguës en Jours ouvrés, Entités) ; mouvements par ticket et par jour (Entrée = `date_derniere_entree == date` ; Sortie = Entrée − variation du statut ouvert, voir Design Notes) ; âges via `jours_ouvres` ; médiane exacte en `Fraction` réduite ; sortie dense triée -- FR-11, AD-9, AD-10, AD-17, H-17, H-19.
- `tests/unit/domaine/test_kpi.py` -- un test par ligne de la matrice, plus : schéma validé, Programme = somme des Entités pour les comptes, stock total = somme de l'Instantané (Anomalies ouvertes), aucune colonne flottante, déterminisme (deux calculs identiques, ordre compris), conservation `stock(D) − stock(D−1) = entrées − sorties` sur le Journal du générateur.

**Acceptance Criteria:**
- Given des Instantanés (états par ticket de chaque Jour ouvré), when le domaine calcule les KPI, then il produit par Entité et pour le Programme les douze codes du catalogue, chaque taux en `numerateur`/`denominateur` entiers.
- Given une Anomalie réouverte, when on calcule son âge, then il part de la réouverture.
- Given les cinq contrôles du dépôt, when on les lance, then ruff, ruff format, mypy, lint-imports et pytest passent.

## Design Notes
**Catalogue (`code_kpi` → `dimension`), dans cet ordre** : `anomalies_ouvertes` (`""`) ; `anomalies_ouvertes_gravite` (valeurs de `Gravite`) ; `anomalies_ouvertes_phase` (valeurs de `Phase`) ; `entrees_jour`, `sorties_jour`, `entrees_fenetre`, `sorties_fenetre` (`""`) ; `age_median_anomalies_ouvertes`, `age_max_anomalies_ouvertes` (`""`) ; `taux_ko_cas_de_test`, `taux_non_execution_cas_de_test` (valeurs de `Phase`) ; `certifications` (valeurs de `StatutCertification`). Lignes triées par date, périmètre (ordre de `entites`, puis `PROGRAMME`), code, dimension (ordre de l'énumération). Sortie dense : zéro explicite, jamais de ligne absente.

**Entrée depuis les états, pas les événements.** Le spine fait dériver `Kpi` d'`Instantane` ; l'âge et les mouvements exigent le grain ticket, d'où `SCHEMA_TICKET_ETAT` (le détail de l'Instantané), même entrée que `meteo`. Précondition : la table couvre chaque Jour ouvré de sa première à sa dernière date (sinon erreur) ; à sa première date, la veille est vide (début de l'historique).

**Mouvements par ticket et par jour (Anomalies).** `E = 1` si `date_derniere_entree == D`. Avec `δ` = ouvert(D) − ouvert(D−1) (absent = 0), `S = E − δ` ∈ {0, 1, 2}. Exemples : créée et fermée le même jour → E 1, S 1 ; ouverte, fermée puis rouverte → E 1, S 1 ; ouverte puis fermée → E 0, S 1. Conséquence : stock(D) − stock(D−1) = entrées − sorties, à chaque périmètre. Limite assumée : plusieurs réouvertures d'un même ticket dans la journée comptent pour une Entrée. Périmètre d'un mouvement = Entité du ticket en D.

**Valeurs sans objet.** Âge sans Anomalie ouverte, taux sans dénominateur : `0/0` (« pas de valeur », distinct de l'infini `n/0`, n > 0). Âge = nombre de Jours ouvrés après la dernière Entrée jusqu'à D (`len(jours_ouvres(entree, D)) − 1`, 0 le jour même). Médiane d'un nombre pair d'âges = moyenne des deux centraux, en `Fraction` réduite (`7/2`). Taux de KO = KO / (OK + KO) ; taux de non-exécution = non exécutés / Cas de test de la Phase ayant un statut. Une Anomalie sans Gravité ou sans Phase, un Cas de test sans Phase compte dans les totaux mais dans aucune ventilation. Programme = toutes les lignes de la table, y compris des Entités hors de `entites`.
