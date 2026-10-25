# usine-migration-jira-demo (Python 3.12, uv, Polars, FastAPI)

Code, commentaires, docstrings et messages d'erreur en français.

## Commandes
- Toujours `uv run ...` (jamais `python`, `pytest` ni `ruff` nus).
- Pendant le développement : tests ciblés, `uv run pytest -q <chemins>`.
- Une seule fois, à la fin : `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run lint-imports`, `uv run pytest -q`.
- Les tests marqués `reseau` et `lent` sont exclus par défaut : les tests n'utilisent ni réseau ni LLM réel.

## Règles
- `src/usine/contrats/` et `src/usine/ports/` sont gelés : changement additif seulement, dans un commit dédié « Feat: contrats x.y » ; sinon n'y touche pas.
- `lint-imports` (import-linter) impose les couches du dépôt : ne pas importer à rebours (ex. `domaine`, `ia` n'importent pas `adaptateurs`).
- Une seule story : ce qui dépasse son périmètre n'est pas implémenté.
- Ne jamais lire ni écrire `.env`. Aucun appel Jira ni LLM réel.
- Au plus 3 cycles « correctif puis tests » sur un même échec ; au-delà, arrête-toi et explique la cause.
