# Story 6.3 : HyDE

## Code Map

- `src/wavelibrarian/architectures/hyde.py` : `Hyde(NaiveRag)` enregistrée `("architecture", "hyde")` ; Params de `naive_rag` plus `mix_question: false`, `hyde_model` (défaut `generator_models[0]` du profil), `hyde_max_tokens: 256`.

## Design Notes

- Index, `update`, `load`, `embedder_dim()` et capacités hérités de `naive_rag` : même chunker, embedder et store, donc mêmes paramètres d'index (`index_key` identique à celui de `naive_rag`).
- `query_params` = `k`, `mix_question`, `hyde_model`, `hyde_max_tokens` : hors de la clé d'index, l'index est réutilisé.
- `answer` : un appel `complete` au rôle `hyde` (step `hyde`, entrée `text` = Question) puis `embed_queries` de la réponse hypothétique, vecteur passé au Retriever (`query_vector`). Le poste (`query`) vient du `scope` du Runner ; la passerelle trace le span `hyde`, distinct de `generate`. L'Architecture ne trace rien.
- `mix_question: true` : `embed_queries([hypothèse, question])`, moyenne puis renormalisation ; somme nulle : vecteur de l'hypothèse seul.
- Le texte hypothétique ne sort pas de `answer` : ni Contexte, ni prompt `generate`, ni Citation.
- Choix hors AC : une réponse hypothétique vide se rabat sur le vecteur de la Question ; le retriever `lexical` est refusé (`ConfigError`) car il ignorerait le vecteur. `dense` (défaut) et `hybrid` sont acceptés.

## Tâches et critères

- [x] Rôle `hyde`, step `hyde`, poste `query`, span distinct de `generate`.
- [x] Vecteur du Retriever = `embed_queries` de la réponse hypothétique.
- [x] `mix_question` : moyenne renormalisée, dans `query_params`, défaut `false`.
- [x] Réponse hypothétique absente du Contexte et des Citations.
- [x] Hypothèse reprenant les mots d'un Passage : ce Passage est au rang 1.
- [x] Même index que `naive_rag`. Cas limites.
