# Story 6.5 : CAG

## Code Map

- `src/wavelibrarian/architectures/cag.py` : `Cag(LongContext)` enregistrée `("architecture", "cag")`, capacités `requires_prompt_cache` et `full_corpus_in_prompt`, `retrieval_method: cited`.
- `src/wavelibrarian/components/generators/llm.py` : `LLMGenerator.preload(context)` (appel `complete`, rôle `generate`, étape `cag.preload`, `cache_system`, `max_tokens: 16`) ; le system est construit par la même fonction que pour `generate`, donc le préfixe est identique.

## Design Notes

- `Cag` hérite de `LongContext` sans la modifier : `Params` (cache_system forcé à vrai), `index` (un Passage par Ancrage, `passages.jsonl`), `check` (fenêtre = entrée + `max_tokens`, palier ×1,5 pour `reference`), `answer`. Seul `load` change : il charge puis appelle `generator.preload(contexte)`.
- Le runner appelle toujours `load` (sous le Poste `indexing`, AD-8) : index construit ou servi par le cache préchargent donc de la même façon. Corpus vide : aucun appel.
- Le préchargement est un appel `complete` en texte libre, sans schéma : sa sortie est ignorée et ne peut pas être refusée comme non conforme.
- Refus d'un Generator sans `prompt_cache` : déjà porté par `requires_prompt_cache` dans `_verifier_capacites` (1.6), aucun code nouveau.
- `min_cacheable_tokens` : aucun test d'Architecture ne peut le faire respecter par le Faux LLM ; le test utilise un faux provider qui ne lit rien sous 512 mots. L'appel réussit, les tokens en cache sont nuls.
- Le préchargement passe par le Cache de réponses de la passerelle : sur un rejeu à l'identique, il est servi sans appel fournisseur (`wl.llm_cache_hit: true`), comme tout appel rejoué (FR-34).
- Pas de Configuration `cag` dans `experiments/mini-test.yaml` ni de suite de conformité : absents du dépôt (4.14).

## Tâches et critères

- [x] `index` écrit un bloc par Ancrage, `load` précharge tout le Corpus avec `cache_system: true` au Poste `indexing`.
- [x] Index construit ou servi par le cache : même préchargement.
- [x] Seconde Question : `wl.usage.cache_read_tokens` non nul, tracé à part, `retrieval_method: cited`.
- [x] Generator `prompt_cache: false` refusé à la validation.
- [x] `check` inapplicable (fenêtre, palier de `claude-haiku-5-5`), aucun appel.
- [x] Corpus sous `min_cacheable_tokens` : succès, tokens en cache nuls.
- [x] Cas limites : `cache_system: false` refusé, Corpus vide sans appel.
