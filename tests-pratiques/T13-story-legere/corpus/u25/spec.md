<intent-contract>

## Intent

**Problem:** `SourceJournal` rend les clés générées (`DEMO-<n>` dans l'ordre de création), alors que la clé canonique en aval est la clé Jira (AD-4) : après injection, les Citations et les liens `<url_site>/browse/<clé>` d'un Passage Journal seul pointent vers d'autres tickets. Rien ne lit `donnees/injection/manifeste_injection.json`, et rien ne prouve que le Journal à la volumétrie cible (≈ 3 000 à 3 600 Anomalies, ≈ 40 000 événements depuis la 1.3) se charge et se calcule sans réseau (FR-8).

**Approach:** Ajouter à `usine.adaptateurs.journal` la lecture du manifeste (`charger_manifeste`, `CHEMIN_MANIFESTE_INJECTION`) et un paramètre `manifeste` à `SourceJournal` qui applique `correspondance_cles` à la lecture ; la composition passe le manifeste quand le fichier existe ; tests à l'échelle marqués `lent`, suite rapide sur le Programme réduit.

## Boundaries & Constraints

**Always:** sans manifeste, comportement et flux strictement inchangés ; avec manifeste : chaque `cle_ticket` remplacée par sa clé Jira, tous les autres champs (dont `id_evenement` `J-<rang>`, ordre, `source = journal`) inchangés ; clé du Journal absente de `correspondance_cles` → `UsineErreur` nommant le fichier, la ligne et la clé ; `manifeste.date_injection` ≠ `entete.date_injection` → `UsineErreur` nommant le fichier et les deux dates ; manifeste introuvable, JSON illisible, non objet ou invalide → `UsineErreur` nommant le fichier ; composition : manifeste chargé seulement si `racine / CHEMIN_MANIFESTE_INJECTION` existe, sinon Journal brut ; sélection « Journal seul » = celle de la 2.4 (pas de `config/jira.yaml`, pas de secret, ou Mode repli), `ConfigJira.mode` restant `cloud | dc` ; tests sans réseau (connexion socket interdite par fixture), données fictives `DEMO` ; tests à la volumétrie de `config/programme.yaml` marqués `lent` (sautés par défaut, marqueur enregistré dans un `conftest.py` de la lane) ; textes en français ; mypy strict, ruff, import-linter verts.

**Never:** modifier `src/usine/contrats/`, `src/usine/ports/`, `pyproject.toml`, `cli.py` racine, `tests/doublures/` ; changer `version_donnees` ni la forme de `DonneesPassage` ; source composite, coupure par instants, alignements (2.6) ; écrire le manifeste (injecteur, L1) ; toucher `verite_terrain.json` ; accès réseau ou Jira.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Sans manifeste | Journal seul | flux identique au fichier | — |
| Correspondance | Journal + manifeste `DEMO-n → DEMO-(n+500)` | mêmes événements, `cle_ticket` remplacée | — |
| Clé manquante | manifeste sans `DEMO-3` | — | `UsineErreur` : fichier, ligne, `DEMO-3` |
| Date incohérente | `date_injection` différente | — | `UsineErreur` : fichier, deux dates |
| Manifeste absent / illisible / invalide | fichier manquant, JSON cassé, tableau, champ manquant | — | `UsineErreur` nommant le fichier |
| `depuis` | avec manifeste | filtre identique, clés remplacées | sans fuseau → `UsineErreur` |
| Passage Journal seul + manifeste | mini-jeu, manifeste écrit, aucun secret, réseau coupé | Passage publié, `source == "journal"`, `tickets_etats` aux clés Jira | — |
| Passage sans manifeste | mini-jeu | clés générées (antérieur) | — |
| Échelle (`lent`) | `config/programme.yaml`, graine 42, manifeste | lecture complète, Instantanés à 1er jour, milieu, Date d'injection, schéma `SCHEMA_TICKET_ETAT`, clés toutes Jira | — |

</intent-contract>

## Code Map

- `src/usine/adaptateurs/journal/__init__.py` -- `SourceJournal(chemin)` : valide tout le Journal à la construction (≈ 0,35 s à l'échelle, mesuré), `_lire`, `_valider`, `entete`, `evenements(depuis)` ; ajouter `manifeste: ManifesteInjection | None = None` et la propriété `manifeste`. Remplacer la clé après validation (`model_copy(update=…)`, la clé Jira est déjà validée `CleTicket` par le manifeste).
- `src/usine/adaptateurs/journal/manifeste.py` (nouveau) -- `CHEMIN_MANIFESTE_INJECTION = REPERTOIRE_DONNEES / "injection" / "manifeste_injection.json"` (aucune constante dans `contrats.passage`, AD-4 donne ce chemin) et `charger_manifeste(chemin) -> ManifesteInjection` ; ré-exportés par le paquet.
- `src/usine/contrats/evenements.py:ManifesteInjection` -- lecture seule : `date_injection`, `cle_projet`, `correspondance_cles` (injective, clés Jira dans le projet).
- `src/usine/composition.py:construire_rapport` (≈ l. 284) -- `source = SourceJournal(chemin_journal)` : passer le manifeste s'il existe ; docstring du module à compléter. `empreinte_donnees` inchangée.
- `src/usine/generateur/journal.py:generer(config, graine, date_generation, cle_projet=…)` -- produit le Journal ; `config/programme.yaml` → ≈ 3 100 Anomalies, 39 800 événements, 8,6 Mo (graine 42, 2026-10-12).
- `src/usine/domaine/instantanes.py` -- `tickets_etats(evenements, dates)`, `instantane(etats)` ; `SCHEMA_TICKET_ETAT` (contrats) pour le modèle de sortie.
- `tests/unit/generateur/conftest.py` -- modèle du marqueur `lent` (enregistrement + saut sauf `-m lent`), à reproduire dans `tests/unit/adaptateurs/journal/conftest.py`.
- `tests/unit/chaine/environnement.py:preparer_racine` -- racine du mini-jeu (Programme réduit) ; `DATE_ARRETE`, `horloge_figee`.
- `tests/unit/test_composition.py:test_passage_sans_secret_journal_seul_sans_requete` -- modèle du Passage Journal seul.
- `tests/contrat/source_tickets/fabriques.py:FABRIQUES` -- ajouter `("journal_correspondance", …)`.

## Tasks & Acceptance

**Execution:**
- `src/usine/adaptateurs/journal/manifeste.py`, `src/usine/adaptateurs/journal/__init__.py` -- chemin, chargement du manifeste, paramètre `manifeste` de `SourceJournal` -- FR-8, AD-4.
- `src/usine/composition.py` -- passer le manifeste à `SourceJournal` quand `racine / CHEMIN_MANIFESTE_INJECTION` existe -- clés cohérentes avec les liens dans un vrai Passage.
- `tests/unit/adaptateurs/journal/conftest.py` -- marqueur `lent` et fixture `sans_reseau` (connexions socket interdites).
- `tests/unit/adaptateurs/journal/test_correspondance.py` -- matrice I/O côté adaptateur et manifeste.
- `tests/unit/adaptateurs/journal/test_echelle.py` -- test `lent` à la volumétrie cible.
- `tests/unit/test_composition.py` -- Passage Journal seul avec manifeste, réseau coupé.
- `tests/contrat/source_tickets/fabriques.py` -- fabrique `journal_correspondance`.

**Acceptance Criteria:**
- Given un Journal à la volumétrie cible et un `ManifesteInjection`, when `SourceJournal` le lit, then tous les `Evenement` portent la clé Jira de `correspondance_cles` et le flux est sinon identique au Journal (`uv run pytest -m lent tests/unit/adaptateurs/journal`).
- Given aucun secret Jira, un manifeste dans `donnees/injection/` et le réseau coupé, when `lancer_rapport` s'exécute, then le Passage est publié avec `source == "journal"` et `tickets_etats.parquet` ne contient que des clés Jira.
- Given les fabriques de contrat, when `uv run pytest tests/contrat` s'exécute, then la suite `SourceTickets` passe pour `journal_correspondance` comme pour `journal`.
- Given la suite par défaut, when `uv run pytest -q` s'exécute, then les tests `lent` sont sautés et aucun test nouveau ne génère le Journal complet.

## Design Notes

- **Correspondance totale** : une clé du Journal sans clé Jira produirait un flux mi-généré mi-Jira, donc des liens faux en silence ; l'injecteur injecte tous les tickets (AD-4), d'où l'erreur bruyante.
- **Sélection « journal »** : `ConfigJira.mode` est gelé à `cloud | dc` (contrats-v1) ; comme en 2.4, le Journal seul est la voie sans configuration Jira, sans secret ou en Mode repli. Le critère « `adaptateur: journal` en configuration » est tenu par cette voie.
- **`version_donnees`** : le spine la fixe à « SHA-256 du Journal + `horodatage_extraction` » ; un manifeste modifié ne la change pas. Laissé en l'état (contrat, AD-16), à reprendre avec la source composite (2.6).
- **Fichiers hors lane** : `src/usine/composition.py` (passage du manifeste, AD-1) ; `tests/unit/test_composition.py` (test de ce câblage) ; `tests/contrat/source_tickets/fabriques.py` (fabrique Journal avec correspondance, prévue par son docstring).
