## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports && uv run pytest -q --tb=short` -- tout vert.
- `bash verif_nav.sh <worktree> 8765 /agent /avant-apres "/pseudonymisation?ticket=DEMO-17" /outillage / /chaine` -- sortie 0 ; DOM : cinq questions enregistrées, deux cartes (120 min / 4,4 s), 26 « Oui » dans la fiche.

## Revue

Revue unique (Opus) du 2026-10-18 sur `d347bfb..5545523`, avec la liste du second avis (Haiku).

- low · second avis 6 · corrigé · critère tenu côté navigateur (`carte.valeurs` porte les deux périodes, le segment choisit la valeur des deux cartes, vérifié par test et code) ; mais `?periode=cumul` n'était pas transmis et `vue.periode` ignoré : `avant-apres.js` envoie la période de l'URL et part de `vue.periode` renvoyée par le serveur.
- low · second avis 4 · rejeté · mesuré : 3,2 s au premier `apercu_pseudonymisation`, 0,0 s aux suivants (moteur Presidio et spaCy gardés en mémoire par l'adaptateur) ; seule la première ouverture attend, déjà notée dans `deferred`. Pas de cache à ajouter dans `ui/cli.py`.
- low · second avis 3 · corrigé · toute exception de `apercu()` hors `UsineErreur` (Presidio, spaCy, `ValueError`…) donne le bandeau « Moteur de Pseudonymisation indisponible » avec la première ligne de la cause, au lieu d'un 500 ; test ajouté.
- low · second avis 1 · corrigé · le 502 de `POST /api/agent/question` renvoie `REPONSE_IMPOSSIBLE` (générique) ; l'exception complète part au journal du serveur (`logging.exception`) ; test : ni URL ni clé dans la réponse.
- low · second avis 7 · rejeté · le `textarea` a `maxlength="2000"` (unités UTF-16, toujours au moins le nombre de points de code compté par pydantic) et le script ignore une question vide : le 422 n'est pas atteignable depuis l'écran.
- low · second avis 9 · corrigé · test de `rendre_fiche` : `<script>`, `<img onerror>` échappés et lien `javascript:` non rendu (markdown-it `validateLink`). Le contrôle « pas d'`innerHTML` » par chaîne reste suffisant pour des scripts sans dépendance.
- low · second avis 2 · rejeté · verrou tenu pendant l'appel LLM voulu (une question à la fois, FR-39) ; le délai relève du fournisseur et du plafond de `config/llm.yaml`, et l'écran bloque déjà une seconde question pendant l'attente.
- low · second avis 5 · rejeté · déjà consigné dans `deferred` : le contrat `StatutControle` n'a pas de valeur « hors périmètre » et `src/usine/contrats/` est hors périmètre de la story.
- low · second avis 8 · rejeté · serveur sur `127.0.0.1` seulement, `TrustedHostMiddleware` et `_meme_origine` comme les autres `POST` (sans `Origin`, requête non navigateur du poste local) ; coût borné par le plafond du LLM.
- low · second avis 10 · rejeté · le verrou est un `threading.Lock` sans logique propre ; un test à deux fils avec doublure n'apporterait que la preuve du verrou de la bibliothèque standard.
