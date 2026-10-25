<intent-contract>

## Intent

**Problem:** Un Passage publié ne contient encore ni `kpi.parquet` ni `tendances.parquet` : l'étape `kpi` est un bouchon, et rien ne branche `domaine.kpi.tendances`. L'étape `prevision` n'a aucune enveloppe capable d'écrire `previsions.json` et une `EntreeTrace` par Prévision (AD-16, FR-34).

**Approach:** Ajouter dans `chaine/etapes.py` une `EtapeKpi` qui passe à `domaine.kpi.kpi` l'état des tickets depuis le début de l'historique, puis à `tendances(kpi, D, ancrage)`. Ajouter aussi une `EtapePrevision` générique : elle reçoit une fonction de prévision injectée, écrit `previsions.json` et rend une trace par Prévision et par Risque. Câbler `EtapeKpi` dans `composition.py`. L'étape `prevision` reste un bouchon tant que `domaine/prevision` (lane L4) n'est pas sur `main`.

## Boundaries & Constraints

**Always:** les étapes enveloppent les fonctions du domaine sans aucun recalcul ; elles lisent le Passage en cours par `ctx.consultation` et n'écrivent rien (l'`EcrivainPassage` écrit et valide chaque fichier par son contrat). L'ancrage des semaines est `EnteteJournal.ancrage_semaines`, déjà passé à `EtapeInstantanes` et `EtapeMeteo` sous le nom `premier_jour`. Les sorties de `kpi` couvrent chaque Jour ouvré de l'historique jusqu'à la Date d'arrêté. Une trace de Prévision porte `type_trace=prevision`, le `passage_id`, la Date d'arrêté de la Prévision, l'Entité en `cible`, `version_grille` de la Prévision, la `version_donnees` injectée et un horodatage pris à l'horloge injectée.

**Never:** toucher `contrats/` ou `ports/` (gelés). Inventer une Baseline ou un Risque hors de `domaine/prevision` (lane L4). Modifier le calcul du nombre d'alignements ou de `horodatage_extraction` dans `execution.py` (Story 2.6, lane L2, en cours). Configurer la journalisation ou l'encodage de la console (périmètre de la CLI, Story 5.5).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Passage nominal | Journal généré (graine 42), D = 2026-10-09 | `kpi.parquet` = `domaine.kpi.kpi(tickets_etats du Passage, entités)` ; `tendances.parquet` = `tendances(kpi, D, ancrage)` ; une date KPI par Jour ouvré de l'ancrage à D | Aucune |
| Aucun ticket à D | D antérieure à toute création | `kpi.parquet` et `tendances.parquet` écrits vides, Passage publié | Aucune |
| Prévisions injectées | `prevoir` rend 1 Prévision + 1 Risque | `previsions.json` enveloppé ; 2 lignes dans `trace/previsions.jsonl`, dans l'ordre du contenu | Aucune |
| Sans Prévision | `prevoir` rend un contenu vide | `previsions.json` écrit avec des tuples vides, aucune trace | Aucune |
| Prévision d'un autre type | `prevoir` rend autre chose qu'un `ContenuPrevisions` | Passage en échec, étape `prevision` nommée | `UsineErreur` |

</intent-contract>

## Code Map

- `src/usine/chaine/etapes.py` -- `jours_du_passage`, `EtapeInstantanes`, `EtapeMeteo` (boucle sur les jours, `ctx.consultation.tickets_etats(jour)`), `EtapeBouchon` : ajouter `EtapeKpi` et `EtapePrevision` ici.
- `src/usine/domaine/kpi.py:315` `kpi(tickets_etats, entites)` -- exige tous les Jours ouvrés de la première à la dernière date de la table ; `:360` `tendances(kpi_quotidiens, date_arrete, ancrage)` -- refuse une D absente d'une table non vide.
- `src/usine/consultation/passage.py:355` `tickets_etats(date)` -- table en cache, filtrée par date (lecture jour par jour peu coûteuse).
- `src/usine/chaine/ecrivain.py` -- `SCHEMAS_TABLES` (déjà `kpi`, `tendances`), `ajouter_traces` (déjà `trace/previsions.jsonl`) : aucune modification attendue.
- `src/usine/chaine/execution.py` -- manifeste : `source`, `nb_tickets`, `version_*`, `etapes` (durées) déjà présents ; `horodatage_extraction=None` et `nb_alignements=0` relèvent de la Story 2.6 : ne pas toucher.
- `src/usine/contrats/prevision.py` -- `ContenuPrevisions`, `Prevision`, `RisqueEntreeRouge` (lecture seule) ; `src/usine/contrats/trace.py` -- `EntreeTrace` (lecture seule).
- `src/usine/composition.py:363` -- registre : `Etape.kpi: EtapeBouchon()` à remplacer (fichier hors lane).
- `tests/unit/chaine/test_execution.py` -- `test_passage_publie` (liste des fichiers), `test_autoportance_meteo` (modèle de comparaison au domaine), `test_jours_sans_ticket_verts`.
- `tests/unit/chaine/environnement.py` -- `preparer_racine`, horloges, `DATE_ARRETE`.

## Tasks & Acceptance

**Execution:**
- `src/usine/chaine/etapes.py` -- ajouter `EtapeKpi(entites, premier_jour)` : concatène `tickets_etats` de chaque jour de `jours_du_passage`, appelle `kpi`, puis `tendances` avec `premier_jour` comme ancrage, sorties `kpi` et `tendances`. Ajouter `EtapePrevision(prevoir, version_donnees, horloge)` : `prevoir(ctx)` rend un `ContenuPrevisions` (sinon `UsineErreur`), sortie `previsions`, une `EntreeTrace` par Prévision puis par Risque (`sortie` = JSON du modèle, `entree_pseudonymisee` = JSON de l'identité : Date d'arrêté, Entité, méthode ou indicateur). Mettre à jour la docstring du module.
- `src/usine/composition.py` -- `Etape.kpi: EtapeKpi(entites, premier_jour)` ; `prevision` reste `EtapeBouchon()` avec un commentaire qui renvoie à L4 ; docstring à jour.
- `tests/unit/chaine/test_etapes.py` -- tests d'`EtapePrevision` (contenu, traces, ordre, contenu vide, type refusé) et d'`EtapeKpi` sur un historique construit (`Flux`), dont le cas sans ticket.
- `tests/unit/chaine/test_execution.py` -- liste des fichiers publiés (`kpi.parquet`, `tendances.parquet`) ; autoportance des KPI (dates = Jours ouvrés de l'ancrage à D) et égalité stricte avec un appel direct de `kpi` et de `tendances` ; manifeste complet (champs de l'AC 3, relus dans `manifeste.json`) ; Passage de bout en bout avec une `EtapePrevision` injectée qui écrit `previsions.json` et `trace/previsions.jsonl`, relus par `Consultation`.

**Acceptance Criteria:**
- Given le registre de `composition.py`, when un Passage s'exécute sur le Journal de test, then `kpi.parquet` et `tendances.parquet` sont publiés, égaux aux sorties directes de `domaine.kpi`, et les KPI couvrent chaque Jour ouvré de l'ancrage à la Date d'arrêté.
- Given une `EtapePrevision` dans le registre, when le Passage est publié, then `previsions.json` est relu par `Consultation.previsions()` / `risques()` et chaque Prévision et chaque Risque a sa ligne dans `trace/previsions.jsonl`, relue par `Consultation.traces()`.
- Given le manifeste publié, when on le relit, then il porte `date_arrete`, `source`, `horodatage_extraction` (nul sans extraction), `nb_tickets`, `nb_alignements`, `version_grille`, `version_donnees`, une exécution datée par étape et `contrats_version`.

## Design Notes

**Prévision en bouchon.** `domaine/prevision` (Stories 4.1 et 4.2, lane L4) n'est pas sur `main`. `EtapePrevision` reçoit donc la prévision sous la forme d'une fonction injectée, `Callable[[ContextePassage[Consultation]], ContenuPrevisions]`, et ne connaît aucune Baseline. Quand L4 sera sur `main`, la composition lui passera une petite fonction qui lit le Passage et appelle le domaine. Jusque-là, le registre garde `EtapeBouchon()` et le Passage réel n'a pas de `previsions.json`. Le critère AC 2 est prouvé avec une fonction de test.

**Traces.** Les Risques sont aussi tracés, car NFR-6 et FR-34 rattachent toute Prévision à ses versions, et `previsions.json` contient les deux. `version_donnees` est passée au constructeur, comme pour `EtapeExplications`.

**KPI denses.** `kpi` est dense sur les dates présentes dans la table. Les premiers Jours ouvrés sans aucun ticket n'ont donc pas de ligne : leur ajouter des zéros serait un calcul hors domaine. Avec le Journal généré, des tickets existent dès l'ancrage, et le test d'autoportance le vérifie.

**Hors périmètre, à reprendre ailleurs.**
- Story 2.6 (L2) : `horodatage_extraction`, `nb_alignements` et la `version_donnees` recalculée après extraction (AD-16). L'extraction réelle n'alimente pas encore les Instantanés, puisque `instantanes` lit seulement le Journal.
- Story 5.5 : configurer la journalisation et l'encodage UTF-8 de la console (rétrospective de l'Epic 0, constat 15).

**Fichiers hors lane.** `src/usine/composition.py`, pour câbler `EtapeKpi` dans le registre (AD-22 : seule la composition construit le registre).
