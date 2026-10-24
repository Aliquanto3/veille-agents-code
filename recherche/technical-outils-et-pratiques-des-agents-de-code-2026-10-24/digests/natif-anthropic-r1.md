# Inventaire sourcé : fonctions natives Claude Code et Anthropic (état au 2026-10-24)

Agent `claude-code-guide`, sans outil d'écriture : contenu recopié par l'orchestrateur depuis son rapport, légèrement condensé. Sources lues le 2026-10-24 sur code.claude.com/docs/en/ et platform.claude.com. « non précisé » = la page ne donne pas le statut.

**Corrections au contexte de départ** : `claude plugin eval` a une page publique (https://code.claude.com/docs/en/plugin-evals.md) ; auto mode est ouvert à tous les plans ; le sandbox n'existe pas sous Windows natif (WSL2 requis) ; Code Review (GitHub) est réservé à Team et Enterprise, pas à Max.

## 1. Méthode et discipline de dev
| Fonction | Ce qu'elle fait | Statut | Windows | Max | Source |
|---|---|---|---|---|---|
| Skills | Instructions chargées à la demande, invocables par `/nom` ou déclenchées par la tâche | non précisé | oui | oui | https://code.claude.com/docs/en/skills |
| Skills intégrées | `/simplify`, `/batch`, `/debug`, `/loop`, `/verify`, `/run`, `/run-skill-generator`, `/doctor`, `/code-review`, `/claude-api`, `/workflow-authoring` | non précisé | oui | oui | même page |
| Marketplace officiel `claude-plugins-official` | Ajouté par défaut ; plugins Anthropic et partenaires ; aussi `claude-community` et `claude-code-plugins` | non précisé | oui | oui | https://code.claude.com/docs/en/plugins/anthropic-marketplaces |
| `feature-dev` | Workflow de fonctionnalité : exploration, architecture, revue, agents spécialisés (maintenu par Anthropic) | non précisé | oui | oui | même page |
| `code-review` (plugin) | Revue de PR multi-agents avec score de confiance (maintenu par Anthropic) ; distinct de `/code-review` | non précisé | oui | oui | même page |
| `commit-commands` | Commit, push, PR (maintenu par Anthropic) | non précisé | oui | oui | même page |
| `security-guidance` | Revue de sécurité automatique des modifications (voir §6) | non précisé | oui (Python) | oui | https://code.claude.com/docs/en/security-guidance |
| `frontend-design` | « Interfaces frontend distinctives et de qualité production » ; mainteneur non confirmé | non précisé | oui | oui | https://raw.githubusercontent.com/anthropics/claude-plugins-official/main/.claude-plugin/marketplace.json |
| `pr-review-toolkit`, `plugin-dev`, `skill-creator`, `hookify`, `claude-md-management`, `claude-code-setup`, `ralph-loop` | Présents dans le marketplace ; `hookify` = hooks anti-comportement, `claude-md-management` = audit de CLAUDE.md, `claude-code-setup` = suggestions d'automatisations | non confirmé | oui | oui | même fichier |
| Plan mode | Lecture seule, plan avant édition | non précisé | oui | oui | https://code.claude.com/docs/en/permission-modes |
| Checkpoints, `/rewind` | Retour arrière conversation et fichiers | non précisé | oui | oui | https://code.claude.com/docs/en/checkpointing |
| Bonnes pratiques ; grands dépôts | Pages non lues | — | — | — | https://code.claude.com/docs/en/best-practices ; https://code.claude.com/docs/en/large-codebases |

## 2. Design et front
| Fonction | Ce qu'elle fait | Statut | Windows | Max | Source |
|---|---|---|---|---|---|
| Plugin `frontend-design` | Voir §1 | non précisé | oui | oui | marketplace.json |
| Skill de design des artifacts | Cherche d'abord un design system (tokens dans CLAUDE.md ou fichier de thème) | non précisé | oui | oui | https://code.claude.com/docs/en/artifacts |
| Artifacts | Pages publiées sur claude.ai, privées par défaut ; login claude.ai, API Anthropic seulement | non précisé | oui | oui | même page |
| Templates `/slides`, `/design`, Claude Docs | Deck, canvas de design, document (v2.1.265+) | bêta | non précisé | oui | même page |
| `/design-sync` | Pousse un design system React vers claude.ai/design | non précisé | oui | non précisé | https://code.claude.com/docs/en/feature-availability |
| Computer use | Pilotage d'applications natives | non précisé | non confirmé | oui (Pro, Max) | https://code.claude.com/docs/en/computer-use |

## 3. Contexte et mémoire
| Fonction | Ce qu'elle fait | Statut | Windows | Max | Source |
|---|---|---|---|---|---|
| CLAUDE.md | Chargé au démarrage ; modifs actives après `/clear`, `/compact` ou redémarrage ; CLAUDE.md imbriqués à la demande ; AGENTS.md lu en alternative | non précisé | oui | oui | https://code.claude.com/docs/en/memory |
| `.claude/rules/` avec `paths:` | Règles limitées à des fichiers, chargées à la demande | non précisé | oui | oui | même page |
| Auto memory | Notes écrites par Claude ; 200 lignes ou 25 Ko chargés par session ; par dépôt, partagées entre worktrees | non précisé | oui | oui | même page |
| Compaction | `/compact` avec instructions ; section `# Compact instructions` ; `idleCompaction` (v2.1.290+) | non précisé | oui | oui | https://code.claude.com/docs/en/costs#reduce-token-usage |
| `/context` | Occupation de la fenêtre de contexte | non précisé | oui | oui | https://code.claude.com/docs/en/costs |
| `/clear`, `/rename`, `/resume`, `/rewind` | Gestion de session | non précisé | oui | oui | https://code.claude.com/docs/en/sessions |
| LSP (plugins code intelligence) | Diagnostics après édition, navigation par symbole ; pas en session cloud | non précisé | oui | oui | https://code.claude.com/docs/en/plugins/code-intelligence |
| Sous-agent `Explore` | Lecture seule ; démarre sans CLAUDE.md ; modèle de la conversation | non précisé | oui | oui | https://code.claude.com/docs/en/sub-agents |
| Recherche d'outils MCP | Définitions MCP différées par défaut | non précisé | oui | oui | https://code.claude.com/docs/en/mcp |

## 4. Coûts
| Fonction | Ce qu'elle fait | Statut | Windows | Max | Source |
|---|---|---|---|---|---|
| Choix du modèle | `/model`, `--model`, alias `default`, `best`, `fable`, `sonnet`, `opus`, `haiku`, `opusplan`, `[1m]` | non précisé | oui | oui | https://code.claude.com/docs/en/model-config |
| `opusplan` | Opus en plan mode, Sonnet ensuite ; **chaque bascule change de modèle et vide le cache** | non précisé | oui | oui | même page |
| Effort | `/effort`, `effortLevel`, frontmatter `effort` ; défaut `medium` sur les modèles 5.5 | non précisé | oui | oui | même page |
| Advisor | Modèle plus fort consulté aux moments clés ; `advisorModel`, `--advisor`, `/advisor` ; tokens comptés dans le quota | expérimental | oui | oui | https://code.claude.com/docs/en/advisor |
| Modèle des sous-agents | Hérite de la session ; champ `model` ; `CLAUDE_CODE_SUBAGENT_MODEL` (comportement non décrit) | non précisé | oui | oui | https://code.claude.com/docs/en/sub-agents#choose-a-model |
| Cache et TTL | 1 h pour la conversation principale sur abonnement ; **5 min pour tous les sous-agents** ; `promptCacheTtl`, `subagentPromptCacheTtl` (v2.1.242+) | non précisé | oui | oui | https://code.claude.com/docs/en/prompt-caching |
| Invalidations du cache | Changement de modèle, effort (selon modèle), fast mode, MCP ou plugin ajouté/retiré, deny d'outil entier, `/compact` ; sans effet : éditer des fichiers, `/advisor`, mode de permission, `/rewind` | non précisé | oui | oui | même page |
| `/usage` | Coût estimé, tokens par modèle, stats du cache, quota par skill / sous-agent / plugin / MCP, recommandations | non précisé | oui | oui | https://code.claude.com/docs/en/costs |
| Fast mode | Opus jusqu'à 2,5× plus rapide, 8 $ / 40 $ par Mtok sur Opus 5.5 ; sur Max, usage credits hors quota | research preview | oui | crédits | https://code.claude.com/docs/en/fast-mode |

## 5. Routage vers d'autres modèles
| Fonction | Ce qu'elle fait | Statut | Windows | Max | Source |
|---|---|---|---|---|---|
| `ANTHROPIC_BASE_URL`, gateway LLM | Route vers une passerelle ; une passerelle qui modifie les requêtes fait perdre advisor, cache 1 h, Remote Control | non précisé | oui | voir ligne suivante | https://code.claude.com/docs/en/llm-gateway ; /llm-gateway-connect ; /llm-gateway-protocol |
| Abonnement et passerelle | Avec seul `ANTHROPIC_BASE_URL`, le login claude.ai et ses quotas restent actifs ; un identifiant de passerelle remplace l'abonnement | non précisé | oui | — | https://code.claude.com/docs/en/llm-gateway |
| Modèles tiers | Anthropic ne prend pas en charge le routage de Claude Code vers des modèles non Claude | — | — | — | même page |
| `allowedProviders` (managed) | Force la sortie vers la passerelle (v2.1.285+) | non précisé | oui | — | https://code.claude.com/docs/en/settings-reference#allowedproviders |
| Claude apps gateway | Passerelle auto-hébergée d'Anthropic : SSO, politiques, OTLP, plafonds, pour Bedrock / Vertex / Foundry | non précisé | non confirmé | — | https://code.claude.com/docs/en/claude-apps-gateway |
| Bedrock, Vertex, Foundry, Platform on AWS | Sans advisor ni fast mode, entre autres | non précisé | non confirmé | — | https://code.claude.com/docs/en/feature-availability |

## 6. Revue et sécurité
| Fonction | Ce qu'elle fait | Statut | Windows | Max | Source |
|---|---|---|---|---|---|
| `/code-review` | Revue de branche ou de diff en session | non précisé | oui | oui | https://code.claude.com/docs/en/code-review-local |
| `/security-review` | Passe de sécurité ponctuelle | non précisé | oui | oui | https://code.claude.com/docs/en/commands |
| Code Review (GitHub) | Revue de PR multi-agents, vérification des constats, niveaux Quick / Standard / Deep | non précisé | — | **non** (Team, Enterprise) | https://code.claude.com/docs/en/code-review |
| Ultrareview | Revue approfondie en bac à sable cloud | non précisé | non confirmé | voir page | https://code.claude.com/docs/en/ultrareview |
| `security-guidance` | 3 couches : motifs à chaque édition, revue Opus à chaque tour, revue agentique à chaque commit/push (20/h) | non précisé | oui (`py -3`) | oui | https://code.claude.com/docs/en/security-guidance |
| `claude-security` | Analyse multi-agents d'un dépôt ou d'un diff avec correctifs (page non lue) | non confirmé | — | — | https://code.claude.com/docs/en/claude-security |
| Sandbox | Isolation OS des commandes ; macOS, Linux, WSL2 | non précisé | **non** (Windows natif) | non précisé | https://code.claude.com/docs/en/sandboxing |
| Modes de permission, auto mode | Auto mode : classifieur par action (Sonnet 5), tous plans, Windows natif v2.1.233+ | non précisé | oui | oui | https://code.claude.com/docs/en/auto-mode-config |
| Permissions allow/ask/deny | Règles par outil et motif | non précisé | oui | oui | https://code.claude.com/docs/en/permissions |
| Sécurité des plugins | Un plugin exécute du code avec les droits de l'utilisateur | non précisé | oui | oui | https://code.claude.com/docs/en/plugins/security |
| Hooks | PreToolUse, PostToolUse, Stop, UserPromptSubmit, SessionStart, PreModelSwitch | non précisé | oui | oui | https://code.claude.com/docs/en/hooks |

## 7. Tests et vérification
| Fonction | Ce qu'elle fait | Statut | Windows | Max | Source |
|---|---|---|---|---|---|
| Claude in Chrome | Pilotage de Chromium via l'extension ; login claude.ai requis ; pas sur WSL ; coûte du contexte si activé par défaut | non précisé | oui | oui | https://code.claude.com/docs/en/chrome |
| `/run`, `/verify` | Lancer l'application et la piloter ; vérifier un changement de bout en bout | non précisé | non confirmé | oui | https://code.claude.com/docs/en/skills |
| Diagnostics LSP | Erreurs dès l'édition | non précisé | oui | oui | https://code.claude.com/docs/en/plugins/code-intelligence |
| Hooks de vérification | Linter en PostToolUse, filtrage des sorties de tests en PreToolUse (exemple publié) | non précisé | oui | oui | https://code.claude.com/docs/en/hooks-guide |

## 8. Orchestration et observabilité
| Fonction | Ce qu'elle fait | Statut | Windows | Max | Source |
|---|---|---|---|---|---|
| Sous-agents | Contexte, outils et modèle propres ; 20 simultanés max, profondeur 3 | non précisé | oui | oui | https://code.claude.com/docs/en/sub-agents |
| Worktree par sous-agent | `isolation: worktree` | non précisé | non confirmé | oui | même page |
| Agent teams | Sessions coordonnées par un lead ; ~7× plus de tokens en plan mode | expérimental | non confirmé | non précisé | https://code.claude.com/docs/en/agent-teams |
| Dynamic workflows | Script JS orchestrant des sous-agents ; 16 simultanés, 1 000 par run | non précisé | non confirmé | oui | https://code.claude.com/docs/en/workflows |
| Agent view, sessions en arrière-plan | Supervision par `/tasks` et l'agent view (page non lue) | non confirmé | — | — | https://code.claude.com/docs/en/agent-view |
| Routines (`/schedule`) | Prompt exécuté dans le cloud sur calendrier, API ou événement GitHub ; 100 exécutions/h | research preview | oui | oui | https://code.claude.com/docs/en/routines |
| `/loop` | Répétition locale d'un prompt | non précisé | oui | oui | https://code.claude.com/docs/en/scheduled-tasks |
| Claude Code on the web | Sessions cloud | non précisé | — | oui | https://code.claude.com/docs/en/claude-code-on-the-web |
| OpenTelemetry | Métriques `claude_code.cost.usage`, `token.usage` ; événements `api_request`, `tool_result` ; traces en bêta | métriques non précisé, traces bêta | oui | oui | https://code.claude.com/docs/en/monitoring-usage |
| Statusline | Script recevant du JSON (contexte, coût, cache) | non précisé | oui | oui | https://code.claude.com/docs/en/statusline |
| Mods | Panneaux ou hooks JS (page non lue) | non confirmé | — | — | https://code.claude.com/docs/en/plugins/mods/overview |
| Output styles | `Default`, `Proactive`, `Concise` (v2.1.237+), `Explanatory`, `Learning` ; styles personnalisés | non précisé | oui | oui | https://code.claude.com/docs/en/output-styles |
| Channels, Remote Control | Messages poussés dans une session ; pilotage à distance | non précisé | non confirmé | oui | https://code.claude.com/docs/en/channels ; /remote-control |

## 9. Évaluation d'une configuration
| Fonction | Ce qu'elle fait | Statut | Windows | Max | Source |
|---|---|---|---|---|---|
| `claude plugin eval` | Cas (prompt + graders) rejoués avec et sans plugin ; JSON et rapport HTML ; `--runs`, `--ablation`, `--judge-model`… (v2.1.269+) | GA selon la référence CLI | oui | non précisé | https://code.claude.com/docs/en/plugin-evals ; https://code.claude.com/docs/en/plugins/cli-reference#plugin-eval |
| `claude plugin validate` | Vérifie la structure d'un plugin | non précisé | oui | — | même référence |
| `/skill-doctor` | Coût de contexte par skill, usage sur 7 jours, skills et plugins jamais utilisés (v2.1.252+) | non précisé | oui | non précisé | https://code.claude.com/docs/en/skills#find-unused-skills |
| Évals skill-creator | Format `evals/evals.json` | non précisé | oui | oui | https://code.claude.com/docs/en/skills#run-evals-with-skill-creator |

## Non confirmé
Statut GA/bêta de la plupart des fonctions ; `/cost` (la doc décrit `/usage`) ; auto memory activée par défaut ; comportement de `CLAUDE_CODE_SUBAGENT_MODEL` ; mainteneur de `frontend-design`, `pr-review-toolkit`, `skill-creator`, `hookify`, `ralph-loop` ; pages non lues : best-practices, context-window, worktrees, agent-view, security, claude-security, computer-use, remote-control, channels, mods.

## Points d'attention pour la configuration d'Anaël
- Sandbox absent sous Windows natif (WSL2).
- Code Review GitHub indisponible sur Max : `/code-review` local à la place.
- Sous-agents à 5 min de cache par défaut, même sur abonnement.
- Fast mode sur Max : crédits hors quota.
