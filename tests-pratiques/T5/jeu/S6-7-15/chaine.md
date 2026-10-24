## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports && uv run pytest -q --tb=short` -- tout vert.
- `bash verif_nav.sh <worktree> 8765 /chaine / /entites/ENT-A` (Edge headless, Mode repli) -- sortie 0 ; DOM de `/chaine` : 10 étapes, bouton de lancement `aria-disabled="true"` lié à son motif, bouton « Revenir au Mode réel ».
- `curl -X POST` sur `/api/mode` (repli, réel, repli), `/api/chaine` (409 en repli), `Origin` étranger (403), corps invalide (422) -- constatés.

## Revue

Revue unique (Opus) du 2026-10-18 sur `48fd534..d58ce6c`, avec la liste du second avis (Haiku).

- medium · second avis 1 · corrigé · DNS rebinding confirmé (POST `/api/mode` avec `Host` et `Origin` `evil.test:8765` → 200) : `TrustedHostMiddleware` (`HOTES_AUTORISES` = `127.0.0.1`, `localhost`, tout port) sur toutes les routes, `Origin` analysé par `urlsplit` (hôte autorisé, même `netloc` que `Host` ; `null` ou autre port : 403) ; les `TestClient` des tests UI prennent `base_url=http://127.0.0.1`, la liste de production n'inclut pas `testserver`.
- low · second avis 2 · corrigé · fenêtre réelle entre la lecture de `mode.repli` par `lancer_chaine` et le verrou de `GestionChaine` : verrou d'écriture commun aux deux routes `POST` ; test à deux fils (échoue sans le verrou).
- low · second avis 3 · corrigé · `charger()` annule le minuteur en attente : un seul sondage programmé après `visibilitychange` ou `pageshow`.
- low · second avis 4 · corrigé · Mode repli sans Passage enregistré : `AUCUN_PASSAGE_REPLI` au lieu d'une invitation à lancer la Chaîne.
- low · second avis 5 · corrigé · fin et échec annoncés deux fois : quand un bandeau (`status` ou `alert`) est affiché, la région `#annonce` se tait ; l'API garde `annonce` inchangée.
- low · second avis 6 · corrigé · serveur muet au lancement ou à la bascule : les boutons reprennent l'état de la dernière vue (motif compris), le cadre affiche « serveur injoignable ».
- low · second avis 7 · corrigé · `OSError` de la lecture de la progression (y compris `fichiers_progression` au lancement) : signalée dans `erreur`, sondage maintenu, plus de 500 ; test ajouté.
- low · second avis 8 · rejeté · `usine rapport` manuel suivi à la place : il faudrait qu'il démarre avant le clic et écrive son premier événement après l'instantané `avant` ; `fichier_nouveau` prend le plus ancien horodatage, l'usage documenté est un seul lanceur (l'UI).
- low · second avis 9 · corrigé · tests ajoutés : `Host` forgé (400 partout, `localhost` accepté), `Origin` `null` / autre port / autre hôte (403), écriture sans `Origin` acceptée, verrou exercé sous deux fils.
- Vérification navigateur (Edge headless, Mode repli, `http://127.0.0.1:8765`) : `/chaine`, `/`, `/entites/ENT-A` en sortie 0.
