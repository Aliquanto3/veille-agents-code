### Story 7.1 : RAPTOR

As a Anaël,
I want un arbre de résumés construit par regroupement récursif, interrogé sur tous ses niveaux,
So that je mesure si des résumés hiérarchiques aident les questions globales et multi-sauts.

**Exigences :** FR-23, FR-35 ; AD-4 (rôle `summarize`), AD-7, AD-8 (résumés au poste `indexing`), AD-20 ; `contracts.md` §1 (`Passage` de `level` > 0), §2.1 (`group_min = 5`, `group_max = 10`, `max_depth = 3`).

**Acceptance Criteria:**

**Given** l'Architecture `raptor` et le Mini-corpus avec le Faux LLM et le faux embedder
**When** on l'indexe
**Then** `passages.jsonl` contient les feuilles et au moins un niveau de résumés ; chaque nœud de résumé a `level` ≥ 1, `child_ids` non vide, `doc_id: null` s'il couvre plusieurs Documents, `anchor_ids` égal à l'union des Ancrages de ses feuilles, et `passage_id = sha16("node", "raptor", level, *sorted(child_ids))`
**And** les groupes comptent entre `group_min` et `group_max` nœuds, sauf le dernier groupe d'un niveau quand il reste moins de `group_min` nœuds (règle documentée), et la profondeur ne dépasse pas `max_depth`
**And** le regroupement est déterministe : deux indexations donnent les mêmes nœuds (AD-20, départage par id)
**And** les appels `summarize` portent le step `raptor.summarize.level<n>` et le poste `indexing`

**Given** une Question
**When** `raptor` répond
**Then** la recherche dense porte sur tous les nœuds (arbre aplati), et chaque Passage retrouvé expose son `level`
**And** une Citation d'un nœud de résumé devient des Citations vers les Ancrages de ses feuilles, par la table `labels` (AD-7), et toutes ces Citations désignent des Ancrages existants

**Given** les métriques de recherche
**When** un nœud de résumé est retrouvé
**Then** il est pertinent si l'union de ses `anchor_ids` recoupe les Ancrages de référence, sans traitement particulier dans `scoring/`

**Given** une mise à jour
**When** `raptor` l'applique (`incremental_update: false`)
**Then** l'arbre est reconstruit sur `corpus_after` au poste `update`, et aucun nœud ne référence un Ancrage du Document supprimé
