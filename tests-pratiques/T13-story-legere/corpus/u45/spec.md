<intent-contract>

## Intent

**Problem:** SM-6 (A sort du rouge dans l'horizon, B ne sort pas, C est signalée en Risque d'entrée en rouge) n'est vérifié par aucun test sur le chemin réel de la Chaîne. Les Risques publiés dans `previsions.json` n'ont pas de valeur projetée (`valeur_projetee_*` vides) alors que `risque.py` la calcule.

**Approach:** Reprise après contrats 1.2 (générateur déjà corrigé sur `main`). Une recette exécute un Passage (`composition.lancer_rapport`, étape `prevision` = `prevision_du_passage`) sur le Journal généré avec la configuration livrée, puis lit `previsions.json` par `ConsultationPassage` à la Date d'arrêté D. `risques_entree_rouge` remplit `valeur_projetee_*` du `RisqueEntreeRouge` avec la valeur projetée qu'il calcule déjà.

## Boundaries & Constraints

**Always:**
- `serie.py` et `prevision_du_passage` de `main` utilisés tels quels (`serie.py`/`previsions.py` de la lane abandonnés).
- Configuration livrée (`config/`), gabarits livrés, Journal de `composition.generer_journal`.
- Rapide : graine 42, génération le vendredi 2026-10-09 → D, plus une génération hors vendredi (mardi 2026-10-13, D lundi). `lent` : générations du mercredi au samedi (D mardi à vendredi) et graines 1, 7, 123.
- À D : seules A et B rouges ; A `sortie_projetee`, date ≤ D + horizon, `regles_non_projetables == ()` ; B `pas_de_sortie_projetee`, `regles_non_projetables == ()` ; C porte un Risque IND-4 quel que soit le jour de D ; tout Risque publié a `valeur_projetee_*` renseignés.
- Recoupement : `series_stock` sur l'état des tickets du Passage = IND-1 publié, pour chaque Entité et Jour ouvré.

**Never:**
- Toucher `src/usine/contrats/`, `src/usine/ports/`, `config/`, la Grille, `baseline.py` (SM-C3) ni le générateur.
- Modifier les seuils ou la logique de projection de `risque.py` : seul le remplissage du contrat change.
- Ajouter une dépendance.

</intent-contract>

## Code Map

- `src/usine/chaine/etapes.py:177` -- `prevision_du_passage` (main) : Prévisions et Risques pour chaque Jour ouvré ; `risques.extend(projete.risque ...)` (l. 219) publie le Risque tel que construit par `risque.py`.
- `src/usine/domaine/prevision/risque.py:150-163` -- construction de `RisqueEntreeRouge` ; `projetee: Fraction` disponible ; `RisqueProjete` reste (tests existants).
- `src/usine/contrats/prevision.py:119-145` -- `valeur_projetee_numerateur/denominateur` (gelé, 1.1) : les deux ou aucun, dénominateur > 0.
- `src/usine/rendu/commun.py:316` -- affiche « valeur projetée » quand renseignée : rendu Excel/PowerPoint enrichi, pas de changement de code.
- `src/usine/composition.py:445` -- `lancer_rapport(racine, D, horloge)` ; `generer_journal` l. 488.
- `tests/unit/chaine/environnement.py` -- modèle de racine d'essai (`preparer_racine` copie `config/` et `gabarits/`), `horloge_figee`.
- `src/usine/consultation/passage.py` -- `ConsultationPassage(repertoire)` : `meteo(D)`, `previsions(D)`, `risques(D)`, `indicateurs()`, `tickets_etats(jour)`.
- `src/usine/domaine/prevision/serie.py:48` -- `series_stock(etats, entites, jours)` (main) ; changement d'Entité déjà couvert par `test_transfert_d_entite`.
- `tests/unit/domaine/prevision/test_recette_scenarios.py` -- recette de la lane bloquée, à réécrire sur la Chaîne.
- Mesure exploratoire (main a663bf3) : SM-6 tenu par la Chaîne pour la graine 42 (générations du lundi 12 au samedi 17), graines 1, 7, 123 ; environ 5 s par Passage.

## Tasks & Acceptance

**Execution:**
- `src/usine/domaine/prevision/risque.py` -- passer `valeur_projetee_numerateur=projetee.numerator`, `valeur_projetee_denominateur=projetee.denominator` au `RisqueEntreeRouge` ; docstring de `RisqueProjete` ajustée.
- `tests/unit/domaine/prevision/test_risque.py` -- vérifier que chaque Risque rendu porte `valeur_projetee_*` égale à `valeur_projetee`.
- `tests/unit/domaine/prevision/test_recette_scenarios.py` -- réécriture : racine temporaire (config et gabarits livrés), `generer_journal(programme livré, graine, date)`, `lancer_rapport`, lecture `ConsultationPassage`, `_ecarts_sm6` avec les exigences d'Always ; tests rapides (vendredi, lundi) et `lent` (semaine partielle, graines).
- Tests existants impactés par `valeur_projetee_*` (attendus JSON, rendu) -- réaligner sans affaiblir.

**Acceptance Criteria:**
- Given le Journal généré (graine 42, 2026-10-12) et la Grille livrée, when la recette exécute un Passage à D = 2026-10-09 par `lancer_rapport`, then `previsions.json` à D donne A `sortie_projetee` dans l'horizon, B `pas_de_sortie_projetee` (sans règle non projetable), C un Risque IND-4, seules A et B rouges.
- Given une génération le mardi 2026-10-13 (D lundi), when la recette rapide s'exécute, then SM-6 et IND-4 pour C tiennent aussi.
- Given les graines 1, 7, 123 et les générations du mercredi au samedi, when `pytest -m lent` s'exécute, then SM-6 tient.
- Given une Entité non rouge qui porte un Risque, when l'étape `prevision` publie `previsions.json`, then `valeur_projetee_*` sont renseignés depuis `risque.py`.
- Given la story, then `git diff <baseline_revision>` ne touche ni `contrats/`, ni `ports/`, ni `config/`, ni `baseline.py`, ni `generateur/`.

## Design Notes

**Pourquoi `lancer_rapport`.** C'est l'exécution réelle d'un Passage (registre de `construire_rapport`, étape `prevision` câblée sur `prevision_du_passage`), sans réécrire la fenêtre de calcul dans le test. Le Rapport Palier 1 est produit au passage ; son coût (~5 s) reste acceptable en rapide pour deux Passages.
