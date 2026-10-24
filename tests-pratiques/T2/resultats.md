# T2 : l'export OpenTelemetry natif peut-il remplacer la reconstitution depuis les transcriptions ?

Date du test : 2026-10-24. Claude Code 2.1.310, Windows 11, Git Bash. Modèle `sonnet` (claude-sonnet-5-5).

## Contexte

`agent-cost-kit/scripts/mesurer_couts.py` reconstitue le coût des agents depuis `~/.claude/projects/<projet>/<session>.jsonl` et `<session>/subagents/agent-*.jsonl`, avec ses propres tarifs, son dédoublonnage des `message.id` et une réestimation de la sortie quand la transcription est tronquée. Claude Code exporte aussi sa télémétrie en OpenTelemetry (doc : https://code.claude.com/docs/en/monitoring-usage), avec un coût `cost_usd` calculé par Claude Code lui-même. Question : cet export suffit-il à remplacer la reconstitution ? Critère de la veille : écart de coût total inférieur ou égal à 5 %.

## Protocole

1. Dépôt jetable `scratchpad/t2-depot` : `calc.py` (`add`, `sub`) et `text.py` (`shout`, `count_words`), sans docstring. Restauré entre les deux essais.
2. Deux sessions `claude -p --model sonnet --permission-mode acceptEdits --max-budget-usd 1.5`, même invite :
   « Utilise un sous-agent Explore pour lister les fonctions des fichiers Python du dépôt, puis ajoute une docstring d'une ligne à chacune. »
   Chaque session a lancé un sous-agent Explore (mode asynchrone) puis fait 4 éditions.
3. Variables d'environnement.

   Essai 1, exporteur console (stdout redirigé vers un fichier, stderr vers un autre) :
   ```
   CLAUDE_CODE_ENABLE_TELEMETRY=1
   OTEL_METRICS_EXPORTER=console
   OTEL_LOGS_EXPORTER=console
   OTEL_METRIC_EXPORT_INTERVAL=5000
   OTEL_LOGS_EXPORT_INTERVAL=2000
   OTEL_LOG_TOOL_DETAILS=1        # inutile pour le coût ; à éviter (chemins et commandes dans l'export)
   ```
   Essai 2, OTLP `http/json` vers `otlp_recepteur.py` (`http.server`, port 4318, 127.0.0.1), avec les traces bêta :
   ```
   CLAUDE_CODE_ENABLE_TELEMETRY=1
   CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1
   OTEL_METRICS_EXPORTER=otlp
   OTEL_LOGS_EXPORTER=otlp
   OTEL_TRACES_EXPORTER=otlp
   OTEL_EXPORTER_OTLP_PROTOCOL=http/json
   OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318
   OTEL_METRIC_EXPORT_INTERVAL=5000
   OTEL_LOGS_EXPORT_INTERVAL=2000
   OTEL_TRACES_EXPORT_INTERVAL=2000
   OTEL_LOG_TOOL_DETAILS=1
   ```
4. Transcriptions retrouvées dans `~/.claude/projects/C--Users-...-scratchpad-t2-depot/<session>.jsonl` (+ `subagents/`), puis :
   `uv run --no-project python scripts/mesurer_couts.py --projet <t2-depot> --session <préfixe> --out <dossier>`
5. `comparer.py` rapproche, par agent : événements `api_request` (somme), métriques `claude_code.cost.usage` et `claude_code.token.usage` (dernier cumul en console, somme des deltas en OTLP), et transcription (usage relu directement, dédoublonné par `message.id`) avec le coût de `agents.csv`.

Charge : deux sessions de moins de 15 s chacune, un récepteur Python arrêté ensuite. Coût en équivalent API : environ 0,13 $ et 0,06 $.

## Résultats

Essai 1 (console, session `1993e1f2`) :

| Agent | Grandeur | OTel (événements = métriques) | Transcription | Écart |
|---|---|---|---|---|
| MAIN (5 appels) | coût | 0,08522 $ | 0,0852 $ | +0,02 % |
| | entrée / sortie | 10 / 1 713 | 10 / 1 713 | 0 |
| | écriture cache / lecture cache | 13 737 / 131 195 | 13 737 / 131 195 | 0 |
| Explore (3 appels) | coût | 0,04420 $ | 0,0442 $ | 0,00 % |
| | entrée / sortie | 6 / 522 | 6 / 522 | 0 |
| | écriture cache / lecture cache | 14 465 / 28 075 | 14 465 / 28 075 | 0 |
| Total | coût | 0,12942 $ | 0,1294 $ | +0,02 % |

Essai 2 (OTLP, session `8e297438`) :

| Agent | Grandeur | OTel (événements = métriques) | Transcription | Écart |
|---|---|---|---|---|
| MAIN (5 appels) | coût | 0,03865 $ | 0,0387 $ | -0,13 % |
| | entrée / sortie | 10 / 1 246 | 10 / 1 246 | 0 |
| | écriture cache / lecture cache | 3 006 / 141 440 | 3 006 / 141 440 | 0 |
| Explore (2 appels) | coût | 0,01856 $ | 0,0186 $ | -0,24 % |
| | entrée / sortie | 4 / 530 | 4 / 530 | 0 |
| | écriture cache / lecture cache | 4 342 / 23 925 | 4 342 / 23 925 | 0 |
| Total | coût | 0,05720 $ | 0,0573 $ | -0,17 % |

Lecture des écarts :
- Les tokens des quatre types concordent à l'unité, agent par agent, et le nombre d'appels est identique (8 et 7).
- L'écart de coût vient uniquement de l'arrondi à 4 décimales de la colonne `cout_usd` de `agents.csv` (0,0001 $ sur 0,04 $ fait 0,24 %). Le total interne du script (`resume.md`) n'est pas utilisé ici. Les tarifs du script (dont l'écriture 1 h à part de l'écriture 5 min) reproduisent donc ceux de Claude Code.
- Le script réestime la sortie du MAIN de l'essai 1 à 1 714 tokens (déclarée 1 713) : sans effet.
- Le critère de 5 % est tenu avec une marge d'un facteur 20.

Fichiers : `donnees/comparaison.txt` (sortie de `comparer.py`), `donnees/run1-console.otel.json`, `donnees/run2-otlp.otel.json` (exports normalisés, sans identité ni chemins), `donnees/run*-agents.csv`.

## Ce que l'OpenTelemetry donne en plus

- Temps réel et hors disque : les événements partent pendant la session (l'exporteur flush à la sortie de `-p`, vérifié). Utile pour un seuil d'alerte dans un run autonome.
- Latence par appel : `duration_ms` et `ttft_ms` sur `api_request` (médiane 2,0 à 2,2 s ici), et sur les spans `llm_request` `first_content_ms`, `stop_reason`, `attempt`, `success`.
- Durée des outils : événements `tool_result` (`duration_ms`, taille d'entrée et de sortie) et spans `claude_code.tool` / `tool.execution`.
- Attente humaine : spans `claude_code.tool.blocked_on_user` avec `duration_ms`, `decision` et `source`. Présents, mais ici 3 à 17 ms car `acceptEdits` approuve tout par configuration ; non exercé avec une vraie personne.
- Répartition 5 min / 1 h des écritures du cache directement dans l'événement (`cache_creation_5m_tokens`, `cache_creation_1h_tokens`), sans lire `usage.cache_creation`.
- `cost_usd` et `cost_usd_micros` calculés par Claude Code : plus besoin de tenir la grille de prix dans le script (elle reste nécessaire pour le contrefactuel de TTL).
- Événements `subagent_completed` (durée, `total_tokens`, nombre d'outils, `is_async`) et attributs `effort`, `speed`, `query_source` (`agent:builtin:Explore`), `agent.name`.
- Hiérarchie des spans : les appels du sous-agent sont sous `claude_code.tool.execution` de l'outil `Agent`, avec `agent_id`.

## Ce qu'il donne en moins ou autrement

- Pas d'historique : seules les sessions lancées après activation sont mesurées. Les transcriptions couvrent tout le passé (le kit s'en sert pour comparer avant et après installation).
- Les métriques n'ont pas `agent_id` (cardinalité) : seulement `query_source` (`main` ou `subagent`) et `agent.name`. Deux sous-agents de même type se confondent. Le coût par agent exige les événements `api_request`, que le console n'exporte qu'en logs.
- `agent.name` des agents personnalisés devient `custom` sauf `OTEL_LOG_TOOL_DETAILS=1`, qui expose aussi les commandes et chemins.
- Dans ces essais, `parent_agent_id` et `workflow.run_id` étaient absents (sous-agent lancé par la session principale, pas de workflow). L'arbre d'agents à plusieurs niveaux, que le script reconstruit depuis les `.meta.json`, n'est pas vérifié côté OTel.
- Dédoublonnage : un événement par requête API (`request_id`), donc pas de doublons ; mais la reprise de session et les segments recopiés ne sont pas testés. Le script, lui, traite explicitement les `message.id` recopiés.
- Réestimation de la sortie tronquée : non applicable (l'événement a l'usage final). Dans ces deux sessions `-p`, la transcription n'était pas tronquée non plus ; le cas interactif n'a pas été testé.
- Les expirations de cache, le pic de contexte, le coût par story et l'empreinte EcoLogits du script sont des calculs en aval. Ils seraient refaisables depuis les événements (horodatés, avec les tokens), mais il faudrait réécrire cette partie.

## Difficulté de mise en place sous Windows

- Variables d'environnement : simples depuis Git Bash (`export`) ; PowerShell demande `$env:...` à chaque session, ou la clé `env` de `settings.json` (non testé ici).
- Exporteur console : écrit sur stdout, mélangé à la réponse de `claude -p`, au format littéral JavaScript (clés sans guillemets, `undefined`) et non JSON. Il faut un analyseur (`parse_console_otel.py`, 50 lignes). Pas d'exporteur fichier pour les métriques et les logs (le mode `file:` n'existe que pour les corps bruts d'API). Les métriques console sont cumulées et répétées à chaque intervalle : 100 Ko de sortie pour 8 appels.
- OTLP `http/json` vers un récepteur Python standard : fonctionne du premier coup ; protocole à fixer explicitement (`OTEL_EXPORTER_OTLP_PROTOCOL`, pas de défaut). Métriques en delta : à additionner. Pas de Docker ni de collecteur nécessaire.
- Les identifiants personnels (email, ids de compte et d'organisation) sont attachés à chaque point et événement. `OTEL_METRICS_INCLUDE_ACCOUNT_UUID=false` retire l'UUID du compte, mais pas l'email. Une sortie console brute ne doit donc pas être partagée ; les fichiers de `donnees/` sont filtrés par les scripts.
- `claude -p` a émis une fois « no stdin data received in 3s » : ajouter `< /dev/null`.

## Limites du test

Deux sessions courtes, un seul modèle, un seul sous-agent par session, une seule profondeur, pas de reprise, pas de cache expiré, pas de blocage humain réel, pas d'appel interactif. Le test prouve l'équivalence de comptage sur les cas simples, pas sur les cas limites que le script corrige (transcription tronquée, reprise, expirations).

## Décision proposée pour agent-cost-kit

1. Ne pas remplacer `mesurer_couts.py` : l'historique, l'absence de configuration et les calculs en aval (expirations, TTL contrefactuel, pic de contexte, arbres, EcoLogits) restent propres aux transcriptions.
2. Garder l'OpenTelemetry comme source de contrôle et de temps réel : documenter dans `docs/mesurer-couts.md` les variables de l'essai 2 (sans `OTEL_LOG_TOOL_DETAILS`), pour qui veut un suivi en direct d'un run autonome ou un recoupement du script.
3. Ajouter, si l'on veut une preuve durable, un banc `bancs/otel_ecart.py` (reprise de `comparer.py`) à rejouer à chaque nouvelle version de Claude Code ou de tarif : l'accord à l'unité sur les tokens et à moins de 1 % sur le coût est un bon test de non-régression des tarifs du script.
4. Pistes à tester avant toute décision plus forte : sous-agents imbriqués et workflows (`parent_agent_id`, `workflow.run_id`), session interactive à sortie tronquée, reprise de session, `blocked_on_user` avec une vraie attente.

## Scripts de ce dossier

- `otlp_recepteur.py` : récepteur OTLP/HTTP minimal, écrit les corps reçus en JSONL.
- `normaliser_otlp.py` : OTLP/JSON vers `{metrics, events, spans}`, sans identité ni chemins.
- `parse_console_otel.py` : sortie console vers le même format.
- `comparer.py` : comparaison OTel et transcription.
