### Story 9.1 : Le lanceur ouvre l'application dans le navigateur

As a utilisateur qui lance l'application,
I want que le navigateur s'ouvre tout seul sur l'application,
So that je n'aie pas à taper l'URL locale.

**Gouverné par :** AD-23. **Source :** R1.

**Acceptance Criteria:**

**Given** `uv run wavelocalai-v2` (le nom passe à `wavelocalai` à la story 8.4)
**When** le serveur écoute
**Then** le navigateur par défaut s'ouvre une seule fois sur `http://127.0.0.1:<port>/`, après que le port répond, jamais avant
**And** `--no-browser` et le réglage `[server] open_browser = false` l'empêchent ; les tests, la CI et les E2E lancent le serveur sans navigateur

**Given** aucun navigateur ou une session sans affichage
**When** l'ouverture échoue
**Then** l'URL est écrite dans la console et le journal, et le serveur continue
