# Story 6.4

## Énoncé (epics.md)

### Story 6.4 : Classification incrémentale des Causes racines

As a Pilote,
I want une Cause racine proposée pour chaque Anomalie,
So that je vois de quoi souffre chaque Entité sans relire les tickets un par un.

**Exigences :** FR-35, NFR-5, NFR-9 · **AD :** AD-12, AD-19, AD-23

**Acceptance Criteria:**

**Given** les `TicketTexte` du Passage
**When** l'étape `classification` s'exécute
**Then** seules les Anomalies nouvelles ou modifiées depuis le dernier Passage sont envoyées, après Pseudonymisation ; les autres viennent du cache
**And** chaque `SortieClassification` porte une des 7 Causes racines de H-18 et un `statut_controle` `[HYPOTHÈSE H-18]`

**Given** un entrepôt sans classification antérieure
**When** le stock complet est classé
**Then** le manifeste porte `classification_initiale = true`, et ce Passage est exclu des mesures de NFR-2 et NFR-9 (AD-8)

**Given** la Cause racine proposée
**When** on recherche son usage
**Then** elle n'est affichée que comme suggestion et n'est jamais écrite dans Jira

## Spécification d'implémentation

Note du banc : l'ajout aux contrats décrit dans la spec (`ReponseClassification`, contrats 1.4, commit dédié) est déjà fait à la base ; ne le refais pas.

## Intent

**Problem:** L'étape `classification` est sautée même en Palier 2 : aucune Cause racine n'est proposée, `llm/classification.json` n'est jamais écrit et le manifeste ne porte jamais `classification_initiale`. Le schéma demandé au fournisseur (`ReponseClassification`) manque aux contrats.

**Approach:** Contrats 1.4 (additif) : `ReponseClassification`. Nouvelle tâche `ia/classification.py` + prompt `ia/prompts/classification.md` : un appel par Anomalie des `TicketTexte` via la passerelle (clé de cache sans Date d'arrêté, déjà en 6.3) ; l'incrémentalité vient du cache, qui ne manque que pour une Anomalie nouvelle ou dont le texte a changé. Étape `EtapeClassification` câblée par la composition ; la Chaîne pose `classification_initiale` quand la classification a appelé le fournisseur sans aucun succès en cache.

## Boundaries & Constraints

**Always:** passage par `Passerelle.executer_structure` (ordre AD-12, Pseudonymisation de l'entrée) ; une `SortieClassification` par Anomalie classée, triée par `rang_cle`, `cause_racine` parmi les 7 `CauseRacine` (H-18) ; `statut_controle` fixé par un contrôle déterministe (`conforme`, ou `corrige` si la justification citait une autre clé de ticket, retirée) ; titres et descriptions entre délimiteurs dans le prompt (données, pas instructions) ; `version_prompt` = octets du gabarit ; commit contrats dédié `Feat: contrats 1.4, …` en tête (`CONTRATS_VERSION` 1.4.0).

**Never:** pas d'écriture dans Jira ni d'usage de la Cause racine hors suggestion ; ne pas toucher `rendu/`, `ia/explication.py`, `ia/etape.py` (lane 6.6 en parallèle) au-delà du nécessaire ; pas de répartition (6.5) ; pas d'import d'`adaptateurs` depuis `ia`/`chaine` ; aucun appel réseau dans les tests.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Premier Passage | 3 Anomalies, cache vide | 3 appels, 3 sorties, manifeste `classification_initiale = true` | — |
| Rejeu | mêmes textes, autre Date d'arrêté | 0 appel fournisseur, mêmes sorties, `classification_initiale = false` | — |
| Incrémental | 1 Anomalie nouvelle, 1 description modifiée, 1 inchangée | 2 appels, 1 succès en cache | — |
| Hors Anomalie | `cas_de_test`, `certification` dans les textes | ignorés, aucun appel | — |
| Aucune Anomalie | table vide | sortie vide, aucune trace, `classification_initiale = false` | — |
| Plafond atteint | `PlafondCoutAtteint` sur une Anomalie | Anomalie non classée (absente de la sortie), étape réussie | journal warning |
| Justification hors cible | justification citant `DEMO-9` pour `DEMO-1` | clé retirée, `corrige` | — |
| Fournisseur en erreur | `UsineErreur` | Passage en échec, « étape « classification » » | propagé |

## Code Map
- `src/usine/contrats/llm.py:~170` -- ajouter `ReponseClassification(Enregistrement)` : `cause_racine: CauseRacine`, `justification: str = ""` (à côté de `ReponseExplication`).
- `src/usine/contrats/versions.py:9` -- `CONTRATS_VERSION` → 1.4.0 ; tests `test_evenements.py:140`, `test_llm.py:70`, `test_passage.py:103,212,220,224,228-236`, `test_versions.py:24`.
- `_bmad-output/planning-artifacts/architecture/architecture-usine-migration-jira-demo-2026-10-10/ARCHITECTURE-SPINE.md:21` -- ligne d'amendement contrats 1.4.
- `src/usine/ia/passerelle.py` -- seul ajout : paramètre nommé optionnel `plafond_eur: Decimal | None = None` de `executer_structure` ; un appel frais lève `PlafondCoutAtteint` si le cumul du Passage atteint `min(plafond du Passage, plafond_eur)` ; le cache reste servi (changement additif minimal, la lane 6.6 touche aussi ce fichier). Sinon lecture seule : `executer_structure`, `ContexteAppel` (`cible` = clé du ticket), `Controle`, `PlafondCoutAtteint` ; `cle_cache` ignore déjà la Date d'arrêté pour `Tache.classification`.
- `src/usine/ia/controles.py` -- `retirer_citations_hors(texte, autorises)` réutilisable pour la justification.
- `src/usine/ia/explication.py` -- modèle à suivre (lecture seule) : `lire_prompt`, `rendre_prompt`, `DELIMITEUR`, boucle et repli plafond.
- `src/usine/ia/classification.py` (nouveau) -- `lire_prompt`, `ContexteClassification`, `classer(passerelle, textes, date_arrete, contexte) -> (sorties, traces)`, `EtapeClassification` (sortie `"classification"`).
- `src/usine/ia/prompts/classification.md` (nouveau) -- 7 catégories avec libellés de `LIBELLES_CAUSES_RACINES`/valeurs d'énumération, ticket entre délimiteurs.
- `src/usine/chaine/execution.py:~85-115` -- `classification_initiale` = au moins une trace LLM `tache=classification` et aucune `depuis_cache`.
- `src/usine/composition.py:~516` -- `registre[Etape.classification] = EtapeClassification(passerelle, empreinte_donnees, empreinte_grille)` (`version_grille` tracée seulement, AD-16). Passer aussi `plafond_eur` = plafond du Passage × `PART_PLAFOND_CLASSIFICATION` (`None` sans plafond).
- `tests/unit/ia/espions.py` -- `textes`, `pseudonymiseur`, `CacheMemoire`, `horloge_espion` ; `tests/doublures/fournisseur_factice.py` (`FournisseurFactice`, `appels`).
- `tests/unit/chaine/test_execution.py:544-840` -- `_passer_en_palier_2` pour l'essai de bout en bout (manifeste, rejeu).

## Tasks & Acceptance
**Execution:**
- `src/usine/contrats/{llm,versions}.py`, tests de version, spine -- contrats 1.4 (commit dédié) -- AD-2, AD-13.
- `src/usine/ia/prompts/classification.md`, `src/usine/ia/classification.py` -- tâche et étape -- FR-35, AD-12.
- `src/usine/chaine/execution.py` -- `classification_initiale` -- AD-8, NFR-9.
- `src/usine/composition.py` -- câblage Palier 2.
- `src/usine/ia/passerelle.py`, `src/usine/ia/classification.py` -- part du plafond réservée à la classification (`plafond_eur`, `PART_PLAFOND_CLASSIFICATION = Decimal("0.5")`, `EtapeClassification(..., plafond_eur: Decimal | None = None)`) ; tests : appel frais refusé au-delà de la part mais cache servi, et explications encore appelées après une classification arrêtée à sa part -- NFR-9.
- `tests/unit/ia/test_classification.py` -- matrice I/O (premier passage, rejeu, incrémental, hors Anomalie, vide, plafond, justification, Pseudonymisation de l'entrée) et absence de Cause racine dans les adaptateurs Jira (`adaptateurs/jira_*`, `composite`).
- `tests/unit/chaine/test_execution.py` -- manifeste : `classification_initiale` vrai au premier Passage Palier 2, faux au rejeu ; `llm/classification.json` publié.

**Acceptance Criteria:**
- Given un Passage Palier 2 sur un entrepôt sans cache, when il se publie, then `llm/classification.json` porte une Cause racine par Anomalie et le manifeste `classification_initiale = true` ; au Passage suivant à textes identiques, aucun appel de classification et `classification_initiale = false`.
- Given le code des adaptateurs Jira, when on y cherche la Cause racine proposée, then aucune référence (`SortieClassification`, `cause_racine`, `classification`).

## Design Notes
Incrémentalité par le cache plutôt que par un diff explicite avec le Passage précédent : l'entrée pseudonymisée (clé, titre, description) est dans la clé de cache, la Date d'arrêté n'y est pas ; une Anomalie inchangée est donc servie sans appel, une nouvelle ou modifiée part au fournisseur. `classification_initiale` en découle : appels frais sans aucun succès en cache = stock complet classé (premier Passage, ou changement de prompt ou de modèle, exclu à juste titre des mesures). Le plafond laisse l'Anomalie sans suggestion (pas de libellé : la Cause racine n'est qu'une suggestion). La classification ne prend qu'une part du plafond du Passage (0,5) : explications et narration gardent leur budget ; le stock initial se complète sur quelques Passages.
