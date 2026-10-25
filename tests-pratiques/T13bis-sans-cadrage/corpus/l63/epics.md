### Story 6.3 : HyDE

As a Anaël,
I want chercher avec l'embedding d'une réponse hypothétique,
So that je mesure si cette réécriture améliore la recherche dense, et à quel coût.

**Exigences :** FR-20 ; AD-4 (rôle `hyde`), AD-8 (poste `query`) ; `contracts.md` §2 (`Retriever.query_vector`), §2.1 (défaut `mix_question = false`).

**Acceptance Criteria:**

**Given** l'Architecture `hyde`, construite sur le même index dense que `naive_rag` (chunker, embedder, store)
**When** on répond à une Question
**Then** un appel au rôle `hyde` (step `hyde`) génère la réponse hypothétique au poste `query`, dans un span distinct de l'étape `generate`
**And** le vecteur passé au Retriever est celui de la réponse hypothétique, encodé par `embed_queries`

**Given** `mix_question: true`
**When** on répond
**Then** le vecteur de recherche est la moyenne, renormalisée, des vecteurs de la réponse hypothétique et de la Question
**And** `mix_question` est dans `query_params`

**Given** la Réponse produite
**When** on inspecte le Contexte et les Citations
**Then** la réponse hypothétique n'apparaît dans aucun bloc du Contexte, et aucune Citation ne peut la désigner

**Given** une réponse hypothétique scénarisée qui reprend les mots d'un Passage précis
**When** on répond
**Then** ce Passage est au rang 1 des Passages retrouvés, ce qui montre que le vecteur de la réponse hypothétique est bien utilisé
