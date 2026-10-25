<intent-contract>

## Intent

**Problem:** L'écran « Ce qu'il faut pour le faire en vrai » n'est qu'un emplacement (« Écran livré par la Story 7.5 »). La démo ne se conclut pas sur la demande d'outillage faite au Sponsor (Story 7.5, FR-43, FR-47, AD-11).

**Approach:** Un module `ui/outillage.py` lit la fiche `docs/fiche-outillage.md` de la Story 8.1 sous la racine de l'UI. L'écran l'affiche telle quelle en Markdown (lecture seule), avec une légende qui cite le fichier source. Aucun texte de la fiche n'est recopié dans `ui/`.

## Boundaries & Constraints

**Always:**
- **Source unique.** Le chemin est `racine / "docs" / "fiche-outillage.md"` (constante `FICHIER_FICHE = Path("docs/fiche-outillage.md")`), avec la même racine que les autres écrans (`racine_ui()` : `USINE_RACINE` ou répertoire courant). Le fichier est lu en UTF-8 à chaque affichage.
- **Lecture seule.** Le contenu est rendu par un seul `st.markdown` (aucun widget de saisie). La légende `st.caption` vaut « Fiche `docs/fiche-outillage.md` (Story 8.1), affichée en lecture seule. »
- **Fiche absente.** `st.warning(FICHE_ABSENTE)` nomme `docs/fiche-outillage.md` et la Story 8.1. Pas d'exception.
- **Fiche illisible** (`OSError`, `UnicodeDecodeError`). `st.error` « Lecture de la fiche outillage impossible : … ». Pas d'exception.
- **Racine introuvable.** Même message que les autres écrans (`_racine_introuvable`).
- **Navigation.** `Ecran.outillage` sort de `STORY_A_VENIR` (seul `Ecran.agent: "7.9"` reste). L'écran reste à un clic de la carte. Le bandeau Mode repli reste en tête. Le Mode repli ne change rien : la fiche est un fichier local.
- **Couches.** `ui/outillage.py` n'importe ni `ports`, ni `config`, ni `streamlit`. `app.py` n'importe pas `ports`.
- **Tests** par `streamlit.testing.v1.AppTest`. `racine_publiee` copie aussi `docs/fiche-outillage.md` du dépôt.

**Never:**
- Recopier dans `src/usine/ui/` une phrase, un titre ou une ligne de tableau de la fiche.
- Modifier `docs/`, `src/usine/contrats/`, `src/usine/ports/`, `pyproject.toml` ou `uv.lock`, ou écrire hors de `src/usine/ui/` et `tests/unit/ui/`.
- Transformer le contenu : pas de résumé, de découpage ni de chiffre dérivé.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Nominal | racine avec `docs/fiche-outillage.md` | un `st.markdown` égal au contenu du fichier, légende citant le fichier | N/A |
| Mode repli | idem + `USINE_MODE_REPLI=1` | bandeau en tête, même contenu | N/A |
| Fiche absente | pas de `docs/fiche-outillage.md` | avertissement `FICHE_ABSENTE`, aucun contenu | pas d'exception |
| Fiche illisible | octets non UTF-8 | `st.error` « Lecture de la fiche outillage impossible : … » | pas d'exception |
| Racine introuvable | `USINE_RACINE` absente | message « Racine introuvable » commun | pas d'exception |

</intent-contract>

## Code Map

- `docs/fiche-outillage.md` -- fiche de la Story 8.1 (lane L8, lecture seule) : titre « Ce qu'il faut pour le faire en vrai », demandes, tableau de correspondance.
- `src/usine/ui/navigation.py:22` -- `STORY_A_VENIR` : retirer `Ecran.outillage`.
- `src/usine/ui/app.py:67` -- `_racine_introuvable` (réutiliser). `app.py:191` -- `afficher_avant_apres` : modèle de l'écran. `app.py:375` -- `principal` : brancher `afficher_outillage(racine)`.
- `src/usine/ui/avant_apres.py` -- modèle de module pur (constantes de messages, `FICHIER_CONFIG`).
- `tests/unit/ui/conftest.py` -- `racine_publiee` : ajouter la copie de la fiche.
- `tests/unit/ui/test_app.py:131` -- `test_navigation` : branche outillage (contenu affiché, pas d'info).
- `tests/unit/ui/test_navigation.py:27` -- attendu de `STORY_A_VENIR`.

## Tasks & Acceptance

**Execution:**
- `src/usine/ui/outillage.py` -- `FICHIER_FICHE`, `FICHE_ABSENTE`, `LEGENDE`, `lire_fiche(racine) -> str | None` (`None` si absent ; laisse remonter `OSError` / `UnicodeDecodeError`).
- `src/usine/ui/navigation.py`, `src/usine/ui/app.py` -- `afficher_outillage(racine)` selon la matrice ; docstring de `app.py` mise à jour.
- `tests/unit/ui/conftest.py` -- copie de `docs/fiche-outillage.md` dans `racine_publiee`.
- `tests/unit/ui/test_outillage.py` -- `lire_fiche` (présent, absent) ; garde anti-duplication : aucune ligne non triviale de la fiche (titres, lignes de liste ou de tableau de plus de 20 caractères) n'apparaît dans un fichier de `src/usine/ui/`.
- `tests/unit/ui/test_app.py`, `test_navigation.py` -- matrice I/O par `AppTest`.

**Acceptance Criteria:**
- Given la fiche `docs/` de la Story 8.1, when le Pilote ouvre l'écran, then l'UI affiche son contenu en lecture seule, sans en dupliquer le texte dans `ui/`.
- Given le dépôt, when `uv run ruff check . ; uv run ruff format --check . ; uv run mypy ; uv run lint-imports ; uv run pytest -q`, then tout passe.

## Design Notes

**Racine plutôt que chemin du paquet.** La fiche se lit sous la racine de l'UI, comme `config/demo.yaml` (Story 7.4). En démo, la racine est le clone du dépôt. Un chemin calculé depuis `__file__` dépendrait de l'installation en mode éditable.
