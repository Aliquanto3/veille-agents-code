# wavelocalai (Python 3.12, FastAPI, Ollama, uv)
Code, commentaires, docstrings et messages d'erreur en français.
## Commandes
- Toujours `uv run ...` (jamais `python`, `pytest` ni `ruff` nus).
- Pendant le développement : tests ciblés, `uv run pytest -q <chemins>`.
- Une seule fois, à la fin : `uv run ruff check .` et `uv run ruff format --check .`.
- Les tests n'utilisent ni réseau ni LLM réel.
## Règles
- Une seule story : ce qui dépasse son périmètre n'est pas implémenté.
- Ne jamais lire ni écrire `.env`. Aucun appel réseau ni LLM réel.
- Au plus 3 cycles « correctif puis tests » sur un même échec ; au-delà, arrête-toi et explique la cause.
