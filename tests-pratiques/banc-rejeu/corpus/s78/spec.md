# Story 7.8

## Énoncé (epics.md)

### Story 7.8 : Outils de consultation de l'Agent

As a Pilote,
I want que l'Agent dispose d'outils qui lisent la Météo, les Anomalies, les Tendances, les Prévisions et les Risques,
So that il répond à partir des chiffres du Passage, pour n'importe quelle Date d'arrêté disponible.

**Exigences :** FR-39, FR-41 · **AD :** AD-2, AD-5, AD-11

**Acceptance Criteria:**

**Given** `ia/agent`
**When** on liste ses outils
**Then** il expose exactement `get_meteo`, `list_anomalies` (filtres Entité, Gravité, Phase, statut), `get_tendance`, `get_prevision` et `get_risques`, aux signatures et résultats définis dans `contrats.agent`, servis par `Consultation`

**Given** l'inventaire des outils et des dépendances de l'Agent
**When** le test de lecture seule s'exécute
**Then** aucun outil n'écrit (Jira, mail, configuration) et l'Agent n'a aucun accès à Jira (AD-5)

**Given** une Date d'arrêté sans Passage
**When** un outil est appelé
**Then** il renvoie un résultat explicite « aucune donnée pour cette date »

## Spécification d'implémentation

Note du banc : l'ajout aux contrats décrit dans la spec (contrats 1.7, filtre `statut`, `AucuneDonnee`, commit dédié) est déjà fait à la base ; ne le refais pas.

## Intent

**Problem:** l'Agent (Story 7.9) n'a encore aucun outil : `ia/agent` ne contient que la sous-application Typer vide. Sans outils servis par `Consultation`, il ne peut répondre à partir des chiffres d'un Passage, pour une Date d'arrêté donnée (FR-39, FR-41).

**Approach:** créer `ia/agent/outils.py`, qui expose exactement cinq outils en lecture seule (`get_meteo`, `list_anomalies`, `get_tendance`, `get_prevision`, `get_risques`). Chacun prend un `Arguments*` de `contrats.agent`, rend un `Resultat*` lu par `Consultation`, ou `AucuneDonnee` si la date n'est pas couverte. Les contrats passent en 1.7.0 par un ajout additif, dans un commit dédié : filtre `statut` de `ArgumentsListAnomalies` et résultat `AucuneDonnee`.

## Boundaries & Constraints

**Always:** lecture par le seul port `Consultation` (AD-11) ; `ia/agent` n'importe que `contrats`, `ports` et `consultation` (import-linter) ; aucun chiffre calculé hors `Consultation` (le filtre `statut` ne fait que sélectionner des lignes, `total` compte les Anomalies filtrées avant la limite) ; textes en français ; tests sans LLM ni Jira.

**Never:** outil d'écriture (Jira, mail, configuration), accès à `SourceTickets` ou à `url_ticket`, import de `pydantic_ai` ; enveloppe passerelle, Pseudonymisation, trace ou conversation (Story 7.9) ; modification de `ports/consultation.py`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Date absente | `date_arrete=None` | Date d'arrêté du manifeste, résultat rempli | — |
| Date disponible | date ∈ `dates_disponibles()` | `Resultat*` à cette date | — |
| Date sans Passage | date ∉ `dates_disponibles()` (ou aucune date) | `AucuneDonnee(date_arrete=date, message="aucune donnée pour cette date")` | pas d'exception |
| Filtre statut | `statut=en_cours`, `limite=2` | seules les Anomalies de ce statut, au plus 2 ; `total` = nombre filtré | — |
| Arguments JSON | dict d'arguments invalides | `ValidationError` Pydantic remontée par `executer` | à la passerelle (7.9) |

## Code Map
- `src/usine/contrats/agent.py` -- `ArgumentsListAnomalies` (domaine mais pas statut) ; ajouter `statut: StatutAnomalie | None = None` et `class AucuneDonnee` (date_arrete, message fixe).
- `src/usine/contrats/versions.py:9` -- `CONTRATS_VERSION` → `1.7.0` ; tests de version : `tests/unit/contrats/test_{evenements,llm,passage,versions}.py` ; inventaire `tests/unit/contrats/test_inventaire.py:90` (ajouter `AucuneDonnee`).
- `src/usine/ports/consultation.py` -- lecture seule : `dates_disponibles`, `manifeste`, `meteo`, `evolution_meteo`, `anomalies(limite=None)`, `tendances` (DataFrame `_COLONNES_MESURE` = champs de `PointTendance`), `previsions`, `risques`.
- `src/usine/consultation/passage.py:386` -- `anomalies` trie par clé et compte avant limite ; réutilisé avec `limite=None` quand `statut` est filtré.
- `src/usine/contrats/llm.py:140` -- `OutilAgent` (nom, description, arguments, executer → str) : forme cible de 7.9, que la passerelle construira à partir de nos définitions.
- `tests/contrat/consultation/fabriques.py` -- `passage_palier_2()` : Passage réel avec Prévisions et Risques pour un test d'intégration.
- `pyproject.toml:195` -- contrat import-linter `ia` (adaptateurs, httpx déjà interdits).

## Tasks & Acceptance
**Execution:**
- `src/usine/contrats/agent.py`, `versions.py` + tests de version et d'inventaire -- ajout additif 1.7.0 -- commit dédié `Feat: contrats 1.7, …`.
- `src/usine/ia/agent/outils.py` -- `@dataclass(frozen=True) DefinitionOutil(nom, description, arguments: type[Enregistrement], executer: Callable[[Mapping[str, Any]], Enregistrement])` ; `class OutilsConsultation(consultation)` avec les 5 méthodes typées ; `outils_consultation(consultation) -> tuple[DefinitionOutil, ...]` ; constante `NOMS_OUTILS`.
- `pyproject.toml` -- contrat import-linter « ia.agent : lecture seule » interdisant `usine.ports.source_tickets`, `usine.ports.entrepot`, `usine.ports.etape`, `usine.ports.fournisseur_llm`, `usine.ports.cache_llm` à `usine.ia.agent` (hors `cli`).
- `tests/unit/ia/agent/test_outils.py` -- matrice I/O sur une Consultation factice, lecture seule (noms exacts, aucun verbe d'écriture, modules importés), intégration sur `passage_palier_2()`.

**Acceptance Criteria:**
- Given `ia/agent`, when on liste ses outils, then les noms sont exactement les cinq attendus et chaque `arguments`/résultat est une classe de `contrats.agent`.
- Given l'inventaire des outils et le graphe d'imports de `usine.ia.agent`, when le test de lecture seule s'exécute, then aucun outil n'écrit et aucun module de `ia.agent` n'importe un port ou un adaptateur Jira.
- Given une Date d'arrêté sans Passage, when chacun des outils datés est appelé, then il rend `AucuneDonnee` « aucune donnée pour cette date ».

## Design Notes
`get_tendance` n'a pas de date (contrat) : il ne rend jamais `AucuneDonnee`, mais une liste de points éventuellement vide. Les arguments JSON sont validés par `Arguments*.model_validate`. La sérialisation en texte et la Pseudonymisation reviennent à la passerelle (7.9).
