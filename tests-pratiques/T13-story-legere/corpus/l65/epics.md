### Story 6.5 : CAG

As a Anaël,
I want précharger tout le Corpus dans le cache de prompt du fournisseur et poser les Questions dessus,
So that je mesure le coût et la qualité d'une approche sans recherche, avec un coût d'indexation explicite.

**Exigences :** FR-22, FR-16 (palier tarifaire), FR-3 (inapplicable), FR-29 (tokens en cache) ; AD-3 (`cache_system`), AD-8 (préchargement au poste `indexing`), AD-13 ; `contracts.md` §2.1 (`requires_prompt_cache`, `full_corpus_in_prompt`).

**Acceptance Criteria:**

**Given** l'Architecture `cag` (`requires_prompt_cache: true`, `full_corpus_in_prompt: true`) et un Generator `fake-llm-a` (`prompt_cache: true`)
**When** le runner l'indexe puis appelle `load`
**Then** `index` écrit le Corpus étiqueté (un bloc par Ancrage) dans le dossier reçu, et `load` émet un appel de préchargement dont le system contient tout le Corpus, avec `cache_system: true`, au poste `indexing`
**And** les deux chemins, index construit ou servi par le cache, préchargent de la même façon, puisque le runner appelle toujours `load`

**Given** deux Questions posées après le préchargement
**When** on lit leurs spans `query`
**Then** la seconde Question montre `wl.usage.cache_read_tokens` non nul, et ses tokens en cache sont tracés séparément des tokens d'entrée
**And** la Réponse a `retrieval_method: cited`

**Given** un Generator dont le Catalogue déclare `prompt_cache: false`
**When** on valide la Configuration
**Then** elle est refusée avant tout appel (story 1.6)

**Given** un Corpus dont l'estimation `tokens_for` dépasse la fenêtre du modèle, ou le seuil de palier de `claude-haiku-5-5` (100 000 tokens)
**When** le runner appelle `check(profile)`
**Then** la Configuration est `inapplicable`, avec une raison qui cite la fenêtre ou le palier, et aucun appel n'est émis

**Given** un Corpus plus court que `min_cacheable_tokens`
**When** on précharge
**Then** l'appel réussit sans erreur, et le Rapport montrera des tokens en cache nuls, conformément au contrat du Catalogue
