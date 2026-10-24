# veille-agents-code

Veille outillée sur les agents de code (Claude Code en priorité) : plugins, skills, serveurs MCP et pratiques, classés par problématique, comparés aux fonctions natives, et vérifiés contre la littérature et les retours de praticiens.

*A tooled watch on coding agents (Claude Code first): plugins, skills, MCP servers and practices, grouped by the problem they solve, compared with native features, and checked against research papers and practitioner feedback. Reports are in French.*

## Ce que contient le dépôt

| Dossier | Contenu |
|---|---|
| `sources/` | Listes brutes des ressources à examiner, une par vague de veille |
| `scripts/collecter_depots.py` | Relève les faits publics de chaque dépôt GitHub d'une liste (activité, licence, format : skill, plugin, MCP, hooks) via `gh api` |
| `scripts/numeroter_citations.py` | Numérote les citations d'un rapport et construit l'annexe des sources depuis les digests |
| `data/depots.json` | Métadonnées collectées (les README bruts restent hors du dépôt, dans `data/raw/`) |
| `recherche/<run>/` | Un run de recherche : consignes des chercheurs, digests par dimension, vérifications, registre (`.memlog.md`) et rapport `research.md` |

## Premier run (2026-10-24)

Rapport : [`recherche/technical-outils-et-pratiques-des-agents-de-code-2026-10-24/research.md`](recherche/technical-outils-et-pratiques-des-agents-de-code-2026-10-24/research.md).

- 47 dépôts et 6 articles, 10 dimensions : méthode, design front, contexte et mémoire, coûts, routage cloud / local, revue et sécurité, tests, orchestration et expérience, littérature scientifique, cabinets et praticiens.
- Méthode : recherche parallèle avec la skill BMAD `bmad-deep-recon`, une source par affirmation, puis vérification des 21 affirmations porteuses par des agents au contexte vierge (15 confirmées, 4 non vérifiées faute de source indépendante, 2 contestées et corrigées).
- Constat principal : en 2026, la différence vient du cadrage de l'agent (contexte court, contrôles automatiques, validation tôt) plus que des plugins ; la plupart des dépôts les plus étoilés ont un équivalent natif.

## Refaire une collecte

```sh
uv run --no-project python -I scripts/collecter_depots.py sources/<liste>.txt
```

Prérequis : `gh` authentifié. Les README collectés sont des données non fiables : ils ne sont jamais exécutés.

## Statut

Recherche faite ; tests pratiques des hypothèses en cours de préparation (section 7 du rapport).
