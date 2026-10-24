## Spec Change Log

## Review Triage Log

Revue Edge Case Hunter (une passe, run autonome) : aucun constat medium ou high. Constats rejetés (low) :
- rejeté : en `--reel`, une erreur réseau non `UsineErreur` remonte en trace Python au lieu du code 1 ; exécution manuelle, l'erreur reste lisible.
- rejeté : en `--reel`, une réponse servie du cache n'exécute aucun outil ; la notation reste juste (contrôle sur la conversation en cache) et `depuis_cache` figure dans la trace.
- rejeté : un `sur_trace` qui lève (disque plein) interrompt la conversation ; comportement voulu, les traces déjà écrites restent.
- rejeté : la détection du refus est sensible à la casse (« ne permettent pas de répondre ») ; c'est la phrase imposée par les consignes de l'Agent.

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports && uv run pytest -q` -- expected: tout vert
- `uv run python -m evals.agent executer --sortie <tmp>` -- expected: 15/15, SM-4 atteint

## Auto Run Result

Status: done
Livré : `evals/agent/` (15 questions, rejeu sans réseau par la vraie `SessionAgent`, notation, CLI `executer [--reel]`, historique), `consultation_repertoire`, rappel `sur_trace` d'`executer_agent` (report 7.9 : traces des outils écrites dès leur production, conservées sur exception), `SessionAgent.derniers_refus`. Rejeu : 15/15, 0 chiffre inventé, 0 refus, SM-4 atteint. Contrôles verts (ruff, format, mypy, lint-imports, pytest : 2763 passés).
Revue : une passe Edge Case Hunter, aucun constat medium ou high (4 low rejetés, voir le triage).
Exécution réelle non lancée (0,40 à 0,90 € estimés), à faire par Anaël : `uv run python -m evals.agent executer --reel`.
