### Story 1.3 : Registre de Composants et commande `wl registre`

As a agent de développement,
I want enregistrer un Composant ou une Architecture par un décorateur et le voir listé,
So that ajouter un module suffise à le rendre sélectionnable, sans toucher à l'orchestration (UJ-4).

**Exigences :** FR-2 ; AD-2.

**Acceptance Criteria:**

**Given** une classe de test décorée `@register("chunker", "toy")` avec un `Params` pydantic (`extra="forbid"`, `frozen=True`) et une docstring
**When** on appelle `registry.get("chunker", "toy")` puis `list_components(kind="chunker")`
**Then** la classe est renvoyée, et la liste donne le nom, le `kind`, la description tirée de la docstring et les Params avec leurs types et leurs défauts

**Given** un `kind` hors de la liste fermée de `contracts.md` §2
**When** on décore une classe avec ce `kind`
**Then** une `ConfigError` est levée
**And** deux enregistrements du même `(kind, name)` lèvent aussi une `ConfigError`

**Given** les Composants `toy` et `toy2` enregistrés pour `chunker`
**When** on demande le nom `inconnu`
**Then** la `ConfigError` liste `toy` et `toy2`, seulement pour ce `kind`

**Given** un module ajouté sous `wavelibrarian.components` ou `wavelibrarian.architectures`
**When** on appelle `registry.discover()`
**Then** il est importé récursivement par `pkgutil` sans autre modification, et un second appel est sans effet

**Given** la CLI
**When** on lance `wl registre` puis `wl registre --kind chunker`
**Then** la sortie liste les entrées enregistrées (toutes, puis celles du `kind`), avec leur description et leurs Params, en français, et sort en 0
