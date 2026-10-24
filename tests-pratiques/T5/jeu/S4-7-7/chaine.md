## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports && uv run pytest -q` -- expected: tout vert.

## Auto Run Result

- **Livré** : Explication sourcée à l'écran (texte avec clés en liens, Citations, phrases retirées, statut), narration contrôlée de la Prévision, sélecteur de Palier sur un Passage Palier 2, écran Pseudonymisation côte à côte via `composition.apercu_pseudonymisation` (table en mémoire qui refuse toute écriture, clé jamais affichée). Contrôles verts : ruff, mypy, lint-imports, 2633 tests.
- **Revue** (une passe Edge Case Hunter) : aucun constat medium/high. Notés : moteur Presidio reconstruit à chaque rendu de l'écran Pseudonymisation (lenteur, pas de cache) ; une erreur hors `UsineErreur` (ex. import Presidio) n'est pas interceptée par l'écran.
- **Reports** : sélecteur Palier 2 non vu sur un vrai Passage Palier 2 ; Brouillon de commentaire (`brouillon_commentaire`) non affiché.
