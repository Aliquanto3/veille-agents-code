# Digest — routage-local (r1, 2026-10-24)

Dimension : brancher Claude Code (et d'autres agents) sur plusieurs fournisseurs et sur des modèles locaux, pour comparer cloud et local.
Arrêt : budget web épuisé (25/25) au tour 3 ; 13 lectures de dépôt sur 20.

## 1. Résumé

- Claude Code se branche sur tout serveur qui parle le format **Anthropic Messages** (`ANTHROPIC_BASE_URL`), mais Anthropic **ne prend pas en charge** l'envoi vers des modèles non-Claude, quelle que soit la passerelle [A1]. Le chemin reste donc « possible mais hors support ».
- En 2026, **Ollama, LM Studio (≥ 0.4.1) et llama.cpp server exposent nativement `/v1/messages`** [A10][A12][A13]. Pour du local sous Windows, une passerelle de traduction (litellm, claude-code-router) n'est plus nécessaire. Limites d'Ollama : pas de `cache_control`, pas de `count_tokens`, pas de `tool_choice`, et le thinking n'est que partiel [A10].
- Une **passerelle avec sa propre clé fait sortir les requêtes de l'abonnement Max** : elles sont facturées au token [A2]. Router une partie du trafic vers le local en gardant l'abonnement pour le reste n'est pas un chemin documenté.
- Une requête Claude Code pèse **environ 29K tokens, dont environ 81 % de définitions d'outils** (une mesure de blog) [A31]. Ollama demande 64k de contexte ou plus [A11]. Un modèle ≤ 4B sur CPU 16 Go ne peut donc pas servir de moteur à Claude Code. Il reste utile pour des lookups et des résumés en appel direct, hors du harnais.
- Les petits modèles restent très faibles en agentique : Qwen3-8B obtient 2,5 % sur Terminal-Bench 2.0 [A34]. Un MoE de type Qwen3-Coder-Next (80B, 3B actifs) annonce 70,6 % sur SWE-bench Verified, mais c'est l'éditeur qui le déclare et le scaffold n'est pas précisé [A33].
- Nouveauté utile : les **en-têtes d'indice de passerelle** (`x-claude-code-request-class` = main/subagent/compaction/auxiliary, `x-claude-code-agent-type`, `x-claude-code-agent-id`) permettent à une passerelle d'attribuer les coûts et de **router par type de requête**. Ils sont désactivés par défaut derrière une URL personnalisée [A7][A8].
- litellm : la licence est MIT, sauf le dossier `enterprise/` [A18]. Ses paquets PyPI 1.82.7 et 1.82.8 ont été compromis en mars 2026 [A17]. agentgateway (Apache-2.0, projet AAIF depuis juin 2026) a un binaire Windows et un tutoriel Claude Code [A20][A21][A22]. tabbyAPI n'a **pas** d'endpoint Anthropic [A24].

## 2. Fiches outils

### BerriAI/litellm
- **Ce que c'est** : SDK Python et proxy (« AI Gateway ») qui appelle plus de 100 fournisseurs. Il expose notamment `/chat/completions` et `/messages` [README]. Il fournit des clés virtuelles, le suivi des dépenses, des garde-fous, l'équilibrage de charge et un tableau de bord. Un SDK « Agents » lance Claude Code, Codex, OpenCode ou pi sur n'importe quel modèle, en marquant les appels `harness,claude_code` [A19]. Rien n'est injecté dans le contexte de Claude Code : c'est un service réseau, dont la seule empreinte côté client est `ANTHROPIC_BASE_URL` et une clé.
- **Problème résolu** : une seule URL pour Claude Code, avec un mappage d'alias, par exemple `claude-haiku-*` vers `ollama/qwen…` et le reste vers Anthropic. Tutoriel officiel « Claude Code with non-Anthropic models » [A16]. Preuves d'efficacité : le README annonce « 8ms P95 à 1k RPS », un chiffre de l'éditeur que je n'ai pas vérifié. Je n'ai trouvé aucune mesure indépendante de la fidélité de traduction vers Claude Code (tool use, thinking, cache).
- **Maturité** : créé le 2023-07-27, release v1.106.3 le 2026-10-24, 5 681 issues ouvertes, 62k étoiles. `commits_90j` et `contributeurs` valent tous deux exactement 100, ce qui ressemble à un **plafond de collecte** et non à une mesure. Rythme de release quasi quotidien : il faut épingler les versions.
- **Risques** :
  - Chaîne d'approvisionnement : les versions PyPI 1.82.7 et 1.82.8 contenaient une charge malveillante (fichier `.pth` qui s'exécute sans import). L'image Docker n'était pas touchée [A17]. Il faut épingler avec hash et préférer l'image.
  - Licence : `NOASSERTION` dans les métadonnées GitHub parce que le fichier LICENSE est mixte. Il est MIT hors de `enterprise/`, qui a sa propre licence commerciale [A18]. Le SSO et une partie de la gouvernance relèvent de l'offre Enterprise [README].
  - La passerelle voit tout le contenu des prompts : sa journalisation doit être configurée.
  - Télémétrie : non vérifiée lors de ce run.
  - Toute réécriture du corps casse le cache de prompt sans erreur visible : la session est facturée comme non mise en cache [A4].
- **Compatibilité** : Python ou Docker, donc utilisable sous Windows (avec `uv`). Indépendant de l'agent : il sert aussi Codex, Cursor et Copilot via le format OpenAI.
- **Équivalent natif** : le « Claude apps gateway » d'Anthropic, auto-hébergé, avec SSO et OTLP, mais réservé aux modèles Claude [A1]. Pour le local seul, l'endpoint `/v1/messages` natif d'Ollama ou de LM Studio rend litellm inutile [A10][A12].
- **Verdict provisoire : Évaluer.** Il ne vaut que pour mesurer les coûts au token et mélanger cloud et local derrière une seule URL en facturation API. Pour un poste unique sur l'abonnement Max, il ajoute un service à exploiter et une surface d'attaque réelle [A17].

### felipevicens/aaif-labs (agentgateway/multi-provider/manifests)
- **Ce que c'est** : un dépôt **personnel** (1 contributeur, 0 étoile, **aucune licence**) de manifestes Kubernetes (`kind`) qui accompagnent des billets annoncés comme « AAIF publications ». Je n'ai pas vérifié son affiliation à l'AAIF. Le README racine ne cite que `virtual-keys`, alors que l'arbre contient aussi `multi-provider` et `observability` [arbre]. Le lab `multi-provider` place un client au format OpenAI (`/v1/chat/completions`) devant OpenAI, Gemini et Anthropic, avec des groupes de priorité. Il a été validé en direct sur agentgateway 1.5.0. **Les appels d'outils n'ont pas été testés**. Point piège documenté : l'ordre des groupes n'assure pas un basculement (failover) [A23]. Rien n'est injecté dans le contexte.
- **Le vrai sujet est agentgateway** : proxy Rust créé par Solo.io, accueilli à la Linux Foundation en août 2025, puis projet hébergé par l'**Agentic AI Foundation** (AAIF, cofondée par Anthropic, OpenAI et Block) en juin 2026, sous licence Apache-2.0 [A20]. v1.6.0 le 2026-10-02, avec des binaires `agentgateway-windows-amd64.exe` [A22]. Il couvre le trafic LLM, MCP et A2A. Son tutoriel « Claude Code proxy » demande de déclarer `/v1/messages` (type `Messages`) et une route `*` en passthrough. Si le modèle épinglé diffère de celui de Claude Code, on obtient une erreur 400 trompeuse [A21].
- **Maturité** : agentgateway compte 5,5k étoiles, a été créé en mars 2025 et publie des releases régulières (métadonnées `gh` du 2026-10-24). aaif-labs : 7 commits en 90 jours, sans licence, donc tous droits réservés par défaut. Ses manifestes ne sont pas réutilisables légalement tels quels.
- **Risques** : la gouvernance est bonne (fondation neutre). L'orientation Kubernetes est surdimensionnée pour un poste Windows, même si un mode autonome existe [A21]. Les manifestes du lab ne testent pas le tool use [A23].
- **Compatibilité** : binaire Windows natif [A22]. Le lab lui-même demande Docker et kind.
- **Équivalent natif** : Claude apps gateway [A1].
- **Verdict provisoire : Hors périmètre pour aaif-labs** (lab K8s personnel, sans licence) **et Évaluer pour agentgateway**. agentgateway est le candidat « gouvernance » à suivre si le consultant doit un jour conseiller une passerelle d'entreprise multi-agents (LLM, MCP, A2A) neutre vis-à-vis des éditeurs.

### theroyallab/tabbyAPI
- **Ce que c'est** : serveur FastAPI pour ExLlamaV3 (format EXL3), avec API **OpenAI et Kobold uniquement**. L'arbre ne contient aucun endpoint Anthropic [A24]. Il gère le batching continu, le décodage spéculatif, le tool calling « style OAI » et les grammaires JSON/regex/EBNF [README]. Rien n'est injecté dans le contexte.
- **Problème résolu** : inférence rapide sur GPU NVIDIA (Ampere ou plus récent pour le batching paginé). Les preuves de performance sont rares et informelles :
  - sur une RTX 5090, le préremplissage EXL3 est jusqu'à 2,5× plus rapide, mais llama.cpp décode 15 à 21 % plus vite [A26] ;
  - sur une RTX 3060, llama.cpp est plus rapide partout [A27].
  Pour un agent de code, où le préremplissage d'un prompt d'environ 29K tokens domine [A31], l'avantage en préremplissage pourrait compter. C'est une hypothèse, non prouvée.
- **Maturité** : 1,5k étoiles, 73 contributeurs, aucune release (« rolling release »). Il se présente lui-même comme un « hobby project… not meant to run on production servers » [A25].
- **Risques** : **AGPL-3.0**, une contrainte si on l'expose à des clients. Avertissement anti-contrefaçon dans le README. Dépendances CUDA et torch. ROCm sous Linux seulement [A25].
- **Compatibilité** : Windows via `start.bat` et CUDA 12 ou 13 [A25]. **Pas de CPU** : il est inutile sur le portable cible (CPU, 16 Go). Pour Claude Code, il faut ajouter une couche de traduction (litellm ou claude-code-router).
- **Équivalent** : llama.cpp server et LM Studio, qui sont portables CPU/GPU et ont `/v1/messages` en natif [A12][A13].
- **Verdict provisoire : Écarter** pour la configuration décrite (cible CPU, pas d'endpoint Anthropic, AGPL, projet amateur revendiqué). À reconsidérer seulement avec une machine équipée d'un GPU NVIDIA dédié au local.

### AlexsJones/llmfit
- **Ce que c'est** : CLI et TUI en Rust qui détecte le matériel et score les modèles selon l'adéquation mémoire, la vitesse estimée, la qualité et le contexte. Il a un cas d'usage `coding`, une API REST, un tableau de bord web, et sait télécharger et lancer des benchmarks via Ollama, llama.cpp, LM Studio, MLX ou Docker Model Runner [README]. La vitesse est estimée à partir de la bande passante mémoire, avec un facteur d'efficacité de 0,55 [A28]. Il fournit un skill `llmfit-advisor` d'environ 150 caractères de description (relue à chaque appel si le skill est installé) et d'environ 7 000 caractères de corps. Ce skill est **orienté OpenClaw** : il propose de modifier `openclaw.json` [A30].
- **Problème résolu** : choisir un modèle et une quantification qui tiennent sur la machine. Preuves de fiabilité :
  - estimations jugées justes sur un M2 Max de 32 Go (Better Stack) ;
  - **très optimistes sur du matériel modeste** : 800× trop rapides sur un Raspberry Pi, et trop optimistes sur un MacBook Pro de 2015 [A29], une source unique de qualité moyenne.
  Le classement « qualité » ne mesure pas la capacité agentique.
- **Maturité** : créé le **2026-02-15**, 38k étoiles en 8 mois et `commits_90j`/`contributeurs` à 100, sans doute un plafond de collecte. Ces signaux relèvent d'un effet de mode (badge Trendshift) plus que d'une qualité démontrée. Licence MIT, release v1.1.17 le 2026-10-08, binaire Windows signé via SignPath quand la tâche de signature réussit [README].
- **Risques** : aucun transfert réseau sans action de l'utilisateur, selon le README [A28]. Le script `curl | sh` concerne macOS et Linux. Sous Windows, winget, Scoop ou `uvx`. Le skill risque d'entrer en conflit d'usage s'il est chargé alors qu'on n'utilise pas OpenClaw.
- **Compatibilité** : Windows x86_64 (winget, Scoop). Interface graphique Windows tierce disponible (llmfit-gui).
- **Équivalent** : aucun dans Claude Code. Alternative citée par llmfit lui-même : llm-checker (Node), qui **mesure réellement** via Ollama mais ne gère pas les MoE [README].
- **Verdict provisoire : Essayer**, en une seule passe sur le portable cible pour présélectionner deux ou trois modèles ≤ 4B. Il faut ensuite **mesurer** (llama-bench ou son mode benchmark), sans se fier aux tok/s estimés. Ne pas installer le skill.

## 3. Analyse de catégorie

### Comment brancher Claude Code sur un autre modèle (synthèse Windows)

| Voie | Endpoint Anthropic natif | Windows | Limites connues |
|---|---|---|---|
| Ollama (local ou cloud) | oui, `/v1/messages` ; `ollama launch claude` | oui | pas de `cache_control`, `count_tokens` ni `tool_choice` ; thinking partiel ; images en base64 seulement ; contexte de 64k ou plus requis [A10][A11] |
| LM Studio ≥ 0.4.1 | oui, `/v1/messages` (2026-01-30) | oui | contexte > 25k ; `CLAUDE_CODE_ATTRIBUTION_HEADER=0` conseillé [A12] |
| llama.cpp `llama-server` | oui, `/v1/messages` et `count_tokens`, outils, thinking [A13] | binaires Windows : non vérifié lors de ce run | non vérifié en usage réel |
| vLLM ≥ 0.19 | gestionnaire Anthropic présent [A14] | Linux, ou WSL sous Windows (croyance non vérifiée) | surdimensionné pour un poste |
| OpenRouter | oui, `https://openrouter.ai/api` ; `ANTHROPIC_API_KEY=""` | oui (service) | fonctionnement garanti seulement avec le fournisseur Anthropic first-party [A15] |
| litellm | traduit `/v1/messages` vers plus de 100 fournisseurs [A16] | oui | réécriture du corps (risque pour le cache et le thinking) ; incident PyPI [A17] |
| claude-code-router | proxy Node ; v3 avec tableau de bord ; MIT ; v3.1.3 le 2026-10-09 [A40] | guide Windows tiers | les guides antérieurs à la v3 sont périmés [A40] ; tool use non documenté |
| agentgateway | route `Messages` et passthrough [A21] | binaire .exe [A22] | conçu pour K8s ; le mode autonome existe |
| tabbyAPI | **non** (OpenAI et Kobold) [A24] | oui (NVIDIA) | demande une couche de traduction |

Ce que Claude Code envoie à un modèle qu'il ne reconnaît pas : thinking adaptatif, `effort`, `context_management`, messages `system` en milieu de conversation, contexte supposé de 200K. Il **retente automatiquement** sans ces champs quand l'amont renvoie une erreur 400 au libellé reconnu [A5]. Il faut donc renvoyer les corps d'erreur tels quels. Sur une URL personnalisée, l'en-tête d'attribution est stable depuis la v2.1.181, ce qui ne casse plus le cache KV du serveur local [A6]. Les plaintes de mars 2026 sur des préremplissages de 30 à 50 s [A32] sont donc peut-être corrigées : à vérifier. La découverte de modèles (`/v1/models`) ne garde que les identifiants qui contiennent `claude` ou `anthropic` [A9], d'où les alias du type `ollama cp qwen3-coder claude-…` [A10]. Le mode fast et le contrôle de sécurité des domaines de WebFetch appellent toujours `api.anthropic.com` directement [A43].

### Doublons et complémentarités
- **litellm, claude-code-router et agentgateway** sont des doublons partiels : tous traduisent ou routent. Aucun n'est strictement meilleur que les autres.
  - litellm l'emporte sur la couverture de fournisseurs et le suivi des dépenses.
  - agentgateway l'emporte sur la gouvernance (fondation, Apache-2.0, binaire Rust, MCP et A2A).
  - claude-code-router l'emporte sur la simplicité côté poste, avec un routage par rôle pensé pour Claude Code.
- Pour du **local seul**, les trois sont dominés par l'endpoint natif d'Ollama, de LM Studio ou de llama.cpp : un composant de moins, sans réécriture du corps.
- **tabbyAPI et Ollama/llama.cpp** : tabbyAPI ne gagne que sur GPU NVIDIA, et seulement peut-être sur le préremplissage [A26]. Ollama et llama.cpp dominent sur la portabilité (CPU), l'endpoint Anthropic et la licence.
- **llmfit** est complémentaire des autres : il intervient en amont, pour le choix du modèle.

### État de l'art hors liste
- **En-têtes d'indice de passerelle** (Claude Code v2.1.273 ou ultérieur, `CLAUDE_CODE_GATEWAY_HINT_HEADERS=1`). Ils indiquent `request-class` (main, subagent, compaction, auxiliary), `agent-type` (Explore, Plan, custom…), et `prev-tool-durations` et `prompt-id`. `x-claude-code-agent-id` arrive sur toutes les requêtes de sous-agent [A7][A8]. Une passerelle peut ainsi **envoyer les sous-agents Explore ou auxiliaires vers le local** et garder la conversation principale sur Claude, et **attribuer les coûts par sous-agent** sans lire les transcriptions. C'est le mécanisme le plus prometteur pour comparer cloud et local « en situation ». Il reste hors support pour les modèles non-Claude [A1].
- **Gouvernance native** : `allowedProviders: ["customEndpoint"]` dans les managed settings épingle la passerelle (v2.1.285 ou ultérieure) [A42]. Utile pour conseiller des clients.
- **Appel headless d'un Claude Code local** : `ollama launch claude --model X --yes -- -p "…"` [A11]. Ce motif s'appelle depuis un skill ou un script pour une sous-tâche locale isolée, sans toucher la session principale sur l'abonnement.
- **Modèles locaux crédibles en 2026** : MoE à petit nombre de paramètres actifs, comme Qwen3-Coder-Next (80B, 3B actifs, 256K de contexte, compatible Claude Code selon la fiche) [A33] ou Qwen3.6-35B-A3B (62,2 % sur Aider polyglot sur un MacBook, source unique [A36]). Ils demandent 24 à 48 Go de mémoire (GPU ou mémoire unifiée), pas un portable à 16 Go.
- **Énergie** : AgentStop arrête les trajectoires vouées à l'échec et économise 15 à 20 % d'énergie pour moins de 5 % de perte d'utilité sur des agents locaux [A37]. Les estimations de type CodeCarbon (fondées sur le TDP) peuvent s'écarter de 40 % de la mesure réelle [A38]. Sous Windows, `nvidia-smi` sert pour le GPU [A39]. RAPL n'est pas disponible sous Windows : il faut un wattmètre à la prise pour le CPU.

### Problèmes de la catégorie que rien ne traite
- **Garder l'abonnement Max tout en routant une partie du trafic vers le local** : non documenté. Une clé de passerelle fait basculer en facturation API [A2], et faire passer l'OAuth de l'abonnement par un proxy qui réoriente le trafic pose une question de conditions d'utilisation que je n'ai pas vérifiée.
- Le **cache de prompt** est absent sur Ollama [A10]. Chaque tour repaie donc le préremplissage d'environ 29K tokens [A31] : rédhibitoire sur CPU.
- **Aucun benchmark public de Claude Code (le harnais) avec un modèle local**. Les scores publiés utilisent d'autres scaffolds (SWE-agent, Terminus 2, mini-swe-agent) [A33][A34].
- Pas de mesure d'énergie CPU propre sous Windows.

### Hypothèses à tester (protocole court)
1. **Viabilité d'un modèle ≤ 4B sur CPU 16 Go dans Claude Code.**
   - Tâche : « lis `app/main.py` et résume les routes ».
   - Variantes : Qwen3.5-4B (ou équivalent) via Ollama natif, contre Haiku 5.5.
   - Mesures : temps jusqu'au premier token (TTFT) du premier tour, durée totale, réussite.
   - Critère : TTFT > 60 s ou échec d'outil → réserver le ≤ 4B aux appels directs (API Ollama, prompt court, sans outils) pour lookup et résumé.
2. **Endpoint natif Ollama ou LM Studio contre litellm vers Ollama**, même modèle.
   - Tâche : 10 tâches courtes d'édition et de test sur un dépôt FastAPI.
   - Mesures : taux d'erreurs d'appel d'outil, taux de réussite des tests, latence.
   - Critère : litellm ne se justifie que s'il n'est pas pire sur les deux premières mesures.
3. **Routage des sous-agents par en-têtes d'indice** (litellm ou agentgateway).
   - Routage : `request-class=subagent` et `agent-type=Explore` vers le modèle local, le reste vers Claude, en facturation API.
   - Mesures : coût via les en-têtes `agent-id` [A8], qualité des réponses Explore (relecture à l'aveugle), latence.
   - Critère : au moins 30 % d'économie sans dégradation jugée.
4. **llmfit contre la mesure réelle** sur le portable cible : tok/s estimés contre llama-bench pour trois modèles. Critère : écart supérieur à 2× → ne garder llmfit que pour l'adéquation mémoire.
5. **Comparaison cloud et local à tâche égale (protocole de base de la veille).**
   - Corpus : N = 10 à 20 tâches figées du dépôt de l'utilisateur, avec tests cachés comme oracle.
   - Harnais : même version de Claude Code, même `CLAUDE.md`, `claude -p` en headless.
   - Variantes : Haiku, Sonnet et Opus contre deux modèles locaux.
   - Mesures :
     - qualité : réussite des tests et revue à l'aveugle ;
     - coût : tokens issus des transcriptions et équivalent API ;
     - latence : TTFT et temps total ;
     - énergie : `nvidia-smi` ou wattmètre pour le local, estimation EcoLogits pour le cloud, en signalant l'asymétrie de méthode.
   - Trois répétitions par cellule.
   - Critère : le local est retenu pour une classe de tâches s'il atteint au moins 90 % de la réussite de Haiku avec une latence au plus 3× supérieure.

## 4. Affirmations

| ref | affirmation | source (URL) | éditeur | date publi | consultée | confiance | classe |
|---|---|---|---|---|---|---|---|
| A1 | Anthropic n'avalise ni n'audite les passerelles tierces et « doesn't support routing Claude Code to non-Claude models through any gateway » | https://code.claude.com/docs/en/llm-gateway | Anthropic | n.d. (page vivante) | 2026-10-24 | haute | doc officielle |
| A2 | Avec une clé de passerelle ou `apiKeyHelper`, les requêtes n'utilisent plus l'abonnement claude.ai et sont facturées au token ; `ANTHROPIC_BASE_URL` seul garde le login de l'abonnement | https://code.claude.com/docs/en/llm-gateway | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| A3 | Format exigé : Anthropic Messages (`/v1/messages`, `count_tokens` optionnel avec repli sur une estimation par caractères) ; transmettre `anthropic-beta` et `anthropic-version` tels quels | https://code.claude.com/docs/en/llm-gateway-protocol | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| A4 | Une passerelle qui retire `cache_control` ou transforme le `system` en chaîne fait facturer toute la session comme non mise en cache, sans erreur | https://code.claude.com/docs/en/llm-gateway-protocol | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| A5 | Pour un ID de modèle inconnu, Claude Code envoie thinking adaptatif, effort et context management, suppose 200K de contexte, et retente automatiquement sans ces champs sur une erreur 400 reconnue | https://code.claude.com/docs/en/llm-gateway-protocol | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| A6 | Depuis la v2.1.181, l'en-tête d'attribution est stable pendant toute une conversation sur une URL personnalisée ; `CLAUDE_CODE_ATTRIBUTION_HEADER=0` est recommandé avant cette version ou si la passerelle remodèle le `system` | https://code.claude.com/docs/en/llm-gateway-protocol | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| A7 | En-têtes d'indice (`x-claude-code-request-class`, `agent-type`, `prev-tool-durations`, `prompt-id`) : v2.1.273 ou ultérieure, désactivés par défaut sur une URL personnalisée, activés par `CLAUDE_CODE_GATEWAY_HINT_HEADERS=1` | https://code.claude.com/docs/en/llm-gateway-protocol | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| A8 | `x-claude-code-session-id` et `x-claude-code-agent-id` (sous-agents) permettent d'attribuer les coûts par session et par agent | https://code.claude.com/docs/en/llm-gateway-protocol | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| A9 | La découverte `/v1/models` (option `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1`) ne garde que les ID qui contiennent `claude` ou `anthropic` | https://code.claude.com/docs/en/llm-gateway-protocol | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| A10 | Ollama `/v1/messages` : messages, streaming, outils et images base64 ; thinking partiel ; pas de `count_tokens`, `tool_choice`, `cache_control` ni Batches | https://docs.ollama.com/api/anthropic-compatibility | Ollama | n.d. | 2026-10-24 | haute | doc officielle |
| A11 | `ollama launch claude` ; en local, « set a 64k+ context window » ; mode headless `--yes -- -p` | https://docs.ollama.com/integrations/claude-code | Ollama | n.d. | 2026-10-24 | haute | doc officielle |
| A12 | LM Studio 0.4.1 ajoute `POST /v1/messages` ; contexte de plus de 25k recommandé ; `CLAUDE_CODE_ATTRIBUTION_HEADER=0` dans sa recette | https://www.lmstudio.ai/docs/integrations/claude-code ; https://lmstudio.ai/blog/claudecode | LM Studio | 2026-01-30 (billet) | 2026-10-24 | haute | doc officielle |
| A13 | llama.cpp server expose `/v1/messages` et `/v1/messages/count_tokens`, avec outils, vision et thinking (PR #17570) | https://huggingface.co/blog/ggml-org/anthropic-messages-api-in-llamacpp | ggml-org / HF | 2026-01 | 2026-10-24 (via résumé de recherche) | moyenne | billet de l'éditeur |
| A14 | vLLM 0.19 contient un gestionnaire Anthropic Messages | https://docs.vllm.ai/en/v0.19.0/api/vllm/entrypoints/anthropic/serving/ | vLLM | n.d. | 2026-10-24 (via résumé) | moyenne | doc API |
| A15 | OpenRouter : `ANTHROPIC_BASE_URL=https://openrouter.ai/api`, `ANTHROPIC_API_KEY=""` ; fonctionnement garanti seulement avec le fournisseur Anthropic first-party | https://openrouter.ai/docs/guides/coding-agents/claude-code-integration | OpenRouter | n.d. | 2026-10-24 (via résumé) | moyenne | doc de l'éditeur |
| A16 | Tutoriel litellm : Claude Code vers des modèles non-Anthropic via le `/v1/messages` du proxy | https://docs.litellm.ai/docs/tutorials/claude_non_anthropic_models | BerriAI | n.d. | 2026-10-24 (via résumé) | moyenne | doc de l'éditeur |
| A17 | litellm 1.82.7 et 1.82.8 sur PyPI compromis (TeamPCP, mars 2026 ; charge dans `proxy_server.py` puis dans un `.pth`) ; image Docker non touchée | https://www.helpnetsecurity.com/2026/03/25/teampcp-supply-chain-attacks/ ; https://bleepingcomputer.com/news/security/popular-litellm-pypi-package-compromised-in-teampcp-supply-chain-attack | Help Net Security, BleepingComputer | 2026-03-25 | 2026-10-24 | haute | presse sécurité (plusieurs sources) |
| A18 | LICENSE de litellm : MIT, sauf le contenu de `enterprise/`, soumis à `enterprise/LICENSE` | https://github.com/BerriAI/litellm/blob/main/LICENSE | BerriAI | — | 2026-10-24 | haute | code du dépôt |
| A19 | Le SDK Agents de litellm lance Claude Code, Codex, OpenCode et pi sur n'importe quel modèle, avec le tag `harness,claude_code` | README BerriAI/litellm | BerriAI | 2026-10 | 2026-10-24 | haute | README |
| A20 | agentgateway : créé par Solo.io, à la LF depuis août 2025, projet hébergé par l'AAIF depuis juin 2026, Apache-2.0 | https://linuxfoundation.org/press/linux-foundation-welcomes-agentgateway-project-to-accelerate-ai-agent-adoption-while-maintaining-security-observability-and-governance ; https://itbrief.co.uk/story/agentic-ai-foundation-adds-agentgateway-as-hosted-project | Linux Foundation, IT Brief | 2025-08 ; 2026-06 | 2026-10-24 | haute | communiqué et presse |
| A21 | Tutoriel agentgateway pour Claude Code : route `/v1/messages` (Messages) et `*` en passthrough ; erreur 400 trompeuse si le modèle épinglé diffère | https://agentgateway.dev/docs/kubernetes/latest/tutorials/claude-code-proxy/ | agentgateway | n.d. | 2026-10-24 (via résumé) | moyenne | doc du projet |
| A22 | agentgateway v1.6.0 (2026-10-02) publie `agentgateway-windows-amd64.exe` | https://github.com/agentgateway/agentgateway/releases | agentgateway | 2026-10-02 | 2026-10-24 | haute | dépôt |
| A23 | Lab aaif-labs multi-provider : validé sur agentgateway 1.5.0 et kind ; streaming testé, **appels d'outils non testés** ; l'ordre des groupes n'assure pas un basculement | https://github.com/felipevicens/aaif-labs/tree/main/agentgateway/multi-provider | felipevicens | 2026-09-30 | 2026-10-24 | haute (pour ce qu'il affirme) | dépôt (auteur unique) |
| A24 | tabbyAPI n'expose que les endpoints `OAI` et `Kobold`, sans `/v1/messages` | https://github.com/theroyallab/tabbyAPI/tree/main/endpoints | theroyallab | — | 2026-10-24 | haute | code du dépôt |
| A25 | tabbyAPI : « hobby project… not meant to run on production servers » ; AGPL ; `start.bat` pour Windows ; CUDA 12 et 13 ; ROCm sous Linux | README et docs/01.-Getting-Started.md | theroyallab | 2026-10 | 2026-10-24 | haute | README et doc |
| A26 | RTX 5090 : préremplissage EXL3 jusqu'à 2,5× plus rapide, décodage llama.cpp 15 à 21 % plus rapide | https://atomic.chat/blog/guides/exl3-vs-gguf | Atomic Chat | n.d. | 2026-10-24 (via résumé) | basse | blog (vendeur d'appli locale) |
| A27 | RTX 3060 : llama.cpp plus rapide qu'EXL3 (39 contre 30 t/s) | https://huggingface.co/turboderp/gemma-4-12B-it-exl3/discussions/1 | utilisateur HF | n.d. | 2026-10-24 (via résumé) | basse | retour d'usage |
| A28 | llmfit : vitesse estimée par la bande passante mémoire (facteur 0,55) ; aucun envoi réseau sans action de l'utilisateur | README AlexsJones/llmfit ; https://betterstack.com/community/guides/ai/llmfit-llm/ | AlexsJones, Better Stack | 2026 | 2026-10-24 | haute (README) | README et guide |
| A29 | llmfit très optimiste sur du matériel modeste (800× sur un Raspberry Pi ; vitesses jugées optimistes sur un MacBook Pro de 2015) | https://www.stork.ai/blog/this-tool-finds-your-perfect-ai-model | Stork.ai | 2026 | 2026-10-24 (via résumé) | basse | blog |
| A30 | Skill `llmfit-advisor` : description d'environ 150 caractères, fichier d'environ 7 000 caractères, orienté OpenClaw (modifie `openclaw.json`) | https://github.com/AlexsJones/llmfit/blob/main/skills/llmfit-advisor/SKILL.md | AlexsJones | — | 2026-10-24 | haute | mesure dans le dépôt |
| A31 | Une requête Claude Code mesurée pèse environ 29K tokens (131 Ko), dont environ 81 % de définitions d'outils ; 12 s pour « 7+5 » sur un Qwen local | https://mykolaaleksandrov.dev/posts/2026/06/claude-code-huge-prompt-investigation/ | blog personnel | 2026-06 | 2026-10-24 (via résumé) | moyenne | retour d'usage mesuré |
| A32 | Des en-têtes dynamiques invalidaient le cache KV local : 30 à 50 s de préremplissage pour 17K tokens (mars 2026) | https://reddit.sentinel-team.org/posts/1s258a7/snapshots/2026-03-27T16%3A30%3A05.15591Z | miroir Reddit r/LocalLLaMA | 2026-03 | 2026-10-24 (via résumé) | basse (peut-être corrigé, cf. A6) | retour d'usage |
| A33 | Qwen3-Coder-Next : 80B au total, 3B actifs, 256K de contexte ; SWE-bench Verified 70,6, Pro 44,3, Terminal-Bench 2.0 36,2 (scaffold non précisé) ; compatible Claude Code | https://huggingface.co/Qwen/Qwen3-Coder-Next | Qwen | 2026-02 | 2026-10-24 | haute (chiffres de l'éditeur) | fiche modèle |
| A34 | Terminal-Bench 2.0 (Terminus 2) : Qwen3-8B 2,47 %, Nemotron-Terminal-8B 13,0 % | https://arxiv.org/pdf/2602.21193 | arXiv (NVIDIA) | 2026-02 | 2026-10-24 (via résumé) | moyenne | article |
| A35 | Qwen3.5-4B de base : 0,145 sur Terminal-Bench 2.1 (contre 0,211 pour une version affinée) | https://featherless.ai/models/smirki/qwen3.5-4b-terminal-v1 | page d'hébergeur | 2026 | 2026-10-24 (via résumé) | basse | fiche tierce |
| A36 | Qwen3.6-35B-A3B Q8 à 62,2 % sur Aider polyglot sur un MacBook Pro ; Devstral-Small-2 à 4 % (format diff) | https://dev.to/defilan/628-on-aider-polyglot-from-a-macbook-pro-then-the-other-model-we-tried-scored-4-heres-what-17ed | dev.to (auteur unique) | 2026 | 2026-10-24 (via résumé) | basse | retour d'usage |
| A37 | AgentStop : les agents locaux gaspillent de l'énergie sur des trajectoires vouées à l'échec ; 15 à 20 % d'énergie économisée pour moins de 5 % de perte d'utilité | https://arxiv.org/abs/2605.15206 | arXiv (Pham et al., CAIS'26) | 2026-05-01 | 2026-10-24 | moyenne | article |
| A38 | Les estimations CodeCarbon fondées sur le TDP peuvent s'écarter jusqu'à 40 % de la mesure réelle | https://arxiv.org/html/2512.12004v1 | arXiv (EnviroLLM) | 2025-12 | 2026-10-24 (via résumé) | moyenne | article |
| A39 | `nvidia-smi` à 2 Hz est utilisé pour mesurer Ollama sur une RTX 4060 Ti (fonctionne sous Windows) | https://arxiv.org/abs/2608.00008 | arXiv | 2026-08 | 2026-10-24 (via résumé) | basse | article |
| A40 | claude-code-router : MIT, v3.1.3 (2026-10-09) ; la v3 remplace `ccr code` et la configuration par fichier par un tableau de bord | https://github.com/musistudio/claude-code-router ; https://opper.ai/blog/claude-code-router | musistudio ; Opper | 2026-10 | 2026-10-24 | moyenne (le changement v3 vient d'une source secondaire) | dépôt et blog |
| A41 | L'issue vLLM #21313 demandait `/v1/messages` pour Claude Code ; claude-code-router et claude-code-proxy servaient de rustine | https://github.com/vllm-project/vllm/issues/21313 | vLLM | 2025 | 2026-10-24 (via résumé) | moyenne | issue |
| A42 | `allowedProviders: ["customEndpoint"]` dans les managed settings n'autorise que la passerelle (v2.1.285 ou ultérieure) | https://code.claude.com/docs/en/llm-gateway | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |
| A43 | La vérification du mode fast et le contrôle de sécurité des domaines de WebFetch appellent `api.anthropic.com` directement, même derrière une passerelle | https://code.claude.com/docs/en/llm-gateway-protocol | Anthropic | n.d. | 2026-10-24 | haute | doc officielle |

## 5. Pistes non suivies et recherches infructueuses

- **Introuvable** :
  - un score SWE-bench, Aider ou Terminal-Bench **officiel** pour un modèle ≤ 4B ;
  - un benchmark public de **Claude Code (le harnais) contre un modèle local** ;
  - un retour Windows précis sur claude-code-router et les appels d'outils locaux ;
  - les vitesses de préremplissage CPU d'un 4B sur un prompt de 29K tokens.
- **Non vérifié** :
  - la télémétrie de litellm ;
  - les binaires Windows de llama.cpp et le support de vLLM sous Windows ;
  - les conditions d'utilisation de l'abonnement Max derrière un proxy qui reroute ;
  - la correction effective du problème de cache KV (A32 contre A6) ;
  - les chiffres contradictoires des agrégateurs sur Qwen3-Coder-Next (42,8, 58,7 et 70,6 sur SWE-bench Verified ; c'est la fiche officielle qui a été retenue).
- **Pistes à suivre** :
  - claude-code-proxy (autre projet) ;
  - le mode autonome d'agentgateway sur un poste Windows ;
  - EnviroLLM pour mesurer l'énergie en local ;
  - la page « Claude apps gateway » (gateway natif d'Anthropic) ;
  - les classements Terminal-Bench 2.x pour Qwen3.6 en local ;
  - Docker Model Runner (cité par llmfit) comme serveur local supplémentaire.
