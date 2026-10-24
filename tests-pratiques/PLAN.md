# Tests pratiques de la veille du 2026-10-24 : état et décisions

Fichier d'état relisible après `/clear`. Protocoles d'origine : section 7 de `recherche/technical-outils-et-pratiques-des-agents-de-code-2026-10-24/research.md`.

## Contraintes
- Benchmark local d'Anaël en pause depuis le 2026-10-24 au soir pour les tests T3, T4, T6, T7, T8 (avant cela : ni Ollama ni GPU, charge locale minimale (pas de suite de tests complète ni de rejeu de stories en parallèle en local ; CI GitHub ou après le benchmark)) ; au plus 2 sessions claude -p à la fois par test.
- Appels hors Claude via OpenRouter : clé dans la variable utilisateur `OPENROUTER_API_KEY` (lire aussi la base de registre si absente de l'environnement ; ne jamais l'afficher). Modèles retenus par Anaël (frontière de Pareto d'Artificial Analysis) : `openai/gpt-6-luna`, `xiaomi/mimo-v2.6-pro`, `openai/gpt-6.1-sol`, `moonshotai/kimi-k3.1-pro`. N'envoyer que des diffs de dépôts publics.
- Projet de référence : usine-migration-jira-demo (d'autres projets possibles pour comparaison).

## État
| Test | État | Résultat ou décision |
|---|---|---|
| T1 diagnostics des transcriptions | fait (`T1/resultats.md`) | Contexte fixe 51,7 k (principale) / 38,2 k (sous-agent), dont outils 25,5 k / 17,4 k, skills 5,1 k ; 8 outils rarement appelés pèsent 17,8 k (Artifact 10,8 k) → restreindre `tools:` des agents du kit, puis A/B. Bash 13,6 % de l'entrée, dont 54 % de lecture de fichiers → pas d'outil de compression. TTL 1 h négatif → ne pas le poser. Second avis : 65,5 % de constats corrigés, 87 % medium/high, 0,03 $ par story → garder. Coupure à 2× la médiane : 6,7 % d'économie brute, 9,7 % d'agents coupés → alerte plutôt que coupure. |
| T2 OpenTelemetry contre mesurer-couts | fait (`T2/resultats.md`) | Tokens identiques à l'unité, coût à ±0,2 % → garder les transcriptions (historique), OpenTelemetry en contrôle croisé et pour les latences. |
| T3 CLAUDE.md minimal | en cours (banc de rejeu `banc-rejeu/`, 16 exécutions) | — |
| T4 tests verrouillés, anti-mock, mutation, couverture différentielle | volet mutation en cours ; volet tests verrouillés après le banc de rejeu | consigne anti-mock déjà livrée (agent-cost-kit 0.10.0) |
| T5 revue : porte empirique, convergence, critique d'une autre famille | fait (`T5/resultats.md`, 4,05 $) | 7 stories d'usine, 5 défauts manqués par la chaîne : aucun retrouvé par les 4 modèles d'autres familles ; 2 défauts mineurs nouveaux confirmés par test ; 48 % de leurs Important déjà tranchés par la chaîne ; mimo vide 5 fois sur 7. Porte empirique : 23 tests sur 23 échouent bien, 0 faux éliminé → prouve la reproductibilité, pas la pertinence. Décision : critique externe en complément seulement (luna 0,004 $ ou sol 0,05 $ par story). Vérité terrain mince. |
| T6 `/advisor` | en cours, à la suite de T3 sur le même banc | — |
| T7 front et navigateur | en cours ; page de notation à l'aveugle pour Anaël à venir | note à l'aveugle d'Anaël requise |
| T8 modèles locaux | en cours (lookup ≤ 4B, MoE dans Claude Code, modèle de décision pour les commandes) | — |
| T9 Jev (décision Sonnet/Opus, risque de dérapage d'une story) | fait (`T9/resultats.md`) | 125 stories, 9 dérapages : aucun bras ne prédit (AUC heuristique 0,58, Jev 0,56, gpt-6-luna 0,52, mimo 0,47-0,57) → rien à brancher. Jev s'appelle par `POST /api/alpha/decisions` d'OpenRouter, 0,00006 $ et 0,25 s par story. Test peu puissant (9 positifs). |

## Décisions déjà appliquées
- 2026-10-24 : réglages sans regret 1, 2 et 6 dans `~/.claude/CLAUDE.md` (section « Plugins, skills et serveurs MCP tiers ») ; 3 et 4 dans agent-cost-kit v0.10.0 (PR #22).
- 2026-10-24 : `skillOverrides` `bmad-build` et `bmad-build-auto` en `user-invocable-only` (`~/.claude/settings.json`) et ligne du CLAUDE.md racine (implémentation et revue par la chaîne agent-cost-kit).
- En cours : agent-cost-kit 0.11.0 (listes `tools:` explicites, alerte de dérapage dans mesurer-couts) ; recherche complémentaire `decision-routage` (Jev, routeurs appris, Ollama).
