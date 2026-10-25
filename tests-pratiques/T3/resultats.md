# T3 : CLAUDE.md minimal contre CLAUDE.md actuel, sur 4 stories rejouées

Test pratique T3 de la veille sur les agents de code (`recherche/technical-outils-et-pratiques-des-agents-de-code-2026-10-24`, section 7). Mesuré les 24 et 25 octobre 2026 avec le banc de rejeu `tests-pratiques/banc-rejeu/` (réutilisé par T4 et T6). Toutes les sessions passent par l'abonnement Max (aucune clé API) : les coûts sont l'estimation client `total_cost_usd` de Claude Code, en dollars aux tarifs catalogue, pas une facture.

## 1. Résultat en quatre lignes

- **Coût** : le CLAUDE.md minimal coûte 3,6 % de moins (écart agrégé apparié, 20 couples) ; moyenne des écarts relatifs −0,4 %, IC 95 % bootstrap [−8 % ; +7 %]. Le critère de la veille (baisse d'au moins 10 %) n'est pas atteint, et l'intervalle exclut −10 %.
- **Réussite aux tests cachés** : égale. 85,6 % (actuel) contre 82,8 % (minimal), dont un seul run aberrant du minimal (22 %, erreur de signature d'un constructeur sans lien avec le CLAUDE.md) ; sans lui, 86,0 % contre 85,9 %.
- **Qualité de lint** : nettement meilleure avec le minimal, qui nomme les commandes de contrôle : 20 runs sur 20 sans erreur `ruff` ni fichier à reformater, contre 12 sur 20 avec l'actuel.
- **Plafond théorique** : le fichier actuel pèse 1,7 k tokens de plus que le minimal au premier appel ; même supprimé en entier, il ne ferait gagner que 1,5 à 2,5 % ici. Il faudrait retirer environ 10 k tokens de CLAUDE.md (de l'ordre de 200 lignes) pour tenir le critère des 10 %.

**Décision proposée.** Ne pas réduire un CLAUDE.md de cette taille pour économiser : le critère n'est pas satisfait. Garder la condition (a) pour T6, comme le protocole l'impose. À retenir à part : y mettre les commandes de lint et de test (0,4 k tokens) évite les écarts de lint ; la chaîne `agent-cost-kit` les porte déjà dans le prompt de `dev-story`, donc ce gain ne concerne que les sessions sans agent.

## 2. Protocole exact

**Stories de référence** (dépôt public `usine-migration-jira-demo`, 83 stories « Feat: Story » dans l'historique). Choix : des stories moyennes qui ajoutent un fichier de tests d'acceptation exécutable en moins de 5 s, avec une spec écrite avant le développement.

| Id banc | Story | Commit de la story | Base (parent) | Tests cachés | Taille |
|---|---|---|---|---|---|
| s32 | 3.2 KPI quotidiens | `b29755a` | `12249fd` | `tests/unit/domaine/test_kpi.py` : 23 tests | 341 lignes de code, domaine pur |
| s42 | 4.2 Risque d'entrée en rouge | `91b0d8c` | `3c9521f` | `tests/unit/domaine/prevision/test_risque.py` : 35 tests | 234 lignes + extraction de `commun.py` |
| s64 | 6.4 Classification incrémentale des Causes racines | `5eb1888` | `97deb4b` | `tests/unit/ia/test_classification.py` : 18 tests | 227 lignes + câblage Chaîne et composition, prompt |
| s78 | 7.8 Outils de consultation de l'Agent | `def3da4` | `6ccf82a` | `tests/unit/ia/agent/test_outils.py` et `__init__.py` : 23 tests | 184 lignes + contrat import-linter |

Écartées : 6.11 (sa spec a été écrite après le développement par `dev-story`, elle recopierait la solution) et 4.1 (proche de 4.2 ; préparée et validée, non jouée). Les tests cachés sont les fichiers de `tests/` **ajoutés** par le commit de la story, dans leur version finale ; les modifications de fichiers de tests existants ne sont pas cachées. Validation (`banc.py reference`) : au commit de la story les 23, 35, 18 et 23 tests passent tous ; à la base, ils échouent à la collecte (module absent).

**Spec donnée à l'agent** (`corpus/<id>/spec.md`) : la section de la story dans `epics.md` à la base ; puis, de la spec de la story, le contrat d'intention (Intent, Boundaries, matrice d'E/S), la Code Map, les Tasks & Acceptance et les Design Notes. Retirés : frontmatter, Spec Change Log, Review Triage Log, Verification, Auto Run Result, donc tout ce que le développement et la revue ont écrit. Limite : le fichier de spec n'existe qu'au commit de la story, on ne peut pas prouver que les Design Notes n'ont pas été retouchées pendant la revue.

Deux ajouts identiques pour toutes les conditions :
1. **Interface attendue** (`corpus/<id>/interface.md`) : les noms `usine.*` importés par les tests cachés et absents à la base, avec leur module (par exemple `usine.domaine.kpi` : `CODES_KPI`, `DIMENSIONS_KPI`, `kpi`). Sans cette liste, le pilote a obtenu 0/23 sur la story 3.2 : le module de l'agent fonctionnait, mais `DIMENSIONS_KPI`, qui n'est pas dans la spec, manquait et tout le fichier échouait à la collecte.
2. Pour s64 et s78 : une note qui dit que l'ajout aux contrats décrit dans la spec (commit dédié) est déjà fait à la base.

**Prompt** : « Implémente la story suivante, avec ses tests ; lance les tests ciblés avant de finir. » suivi de la spec et de l'interface, passé sur l'entrée standard de `claude -p`.

**Isolation.** Pour chaque exécution : dossier jetable `rejeu\<id>` sous le scratchpad, créé par `git archive <base> | tar -x`, puis `git init` et un commit « etat initial » : aucun historique. Les tests cachés sont retirés ; le dossier `.claude/` du dépôt (agents, 29 skills BMAD, réglages, hook d'arrêt) est supprimé ; `uv sync --frozen` prépare l'environnement (9 s).

**Commande** (`banc.py`, fonction `executer`) :

```
claude -p --model claude-sonnet-5-5 --effort medium --output-format json \
  --permission-mode acceptEdits \
  --allowedTools Read Edit Write Glob Grep "Bash(uv run *)" "Bash(uv sync*)" "Bash(python -m pytest*)" \
     "Bash(git status*)" "Bash(git diff*)" "Bash(git add*)" "Bash(git commit*)" \
  --tools "Read,Edit,Write,Glob,Grep,Bash" \
  --setting-sources project,local --settings '{"claudeMdExcludes":["**/user/.claude/CLAUDE.md"]}' \
  --session-id <uuid> --max-budget-usd 15
```

avec `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` et sans les variables d'environnement contenant KEY, TOKEN, SECRET, PASSWORD ou CREDENTIAL. Jamais `--dangerously-skip-permissions`, jamais de push. Délai maximal 25 min (aucun run ne l'a atteint ; le plus long a duré 16 min, en T6). Au plus 2 sessions `claude -p` à la fois.

## 3. Ce qui est chargé dans chaque condition

Vérifié avec `claude -p "/context"` sur un dossier de test avant les runs (puis par la taille du premier appel dans les transcriptions).

| Élément | (a) actuel | (b) minimal |
|---|---|---|
| Prompt système et définitions d'outils | par défaut, restreints à 6 outils par `--tools` | idem |
| `~/.claude/CLAUDE.md` (3,1 k tokens) | **exclu** par `claudeMdExcludes` : confirmé, `/context` ne liste plus que le CLAUDE.md du projet | idem |
| Réglages utilisateur, plugins (agent-cost-kit, pyright-lsp, mods), agents du kit | **exclus** par `--setting-sources project,local` : `/context` ne montre plus d'agents personnalisés | idem |
| Réglages et agents du dépôt (`.claude/`) | supprimés du dossier | idem |
| Mémoire automatique (`MEMORY.md`) | désactivée par variable d'environnement | idem |
| Skills | seulement les skills intégrées (environ 2,1 k tokens de liste) | idem |
| CLAUDE.md du projet | copie de `<user>\Documents\GitHub\CLAUDE.md` : 39 lignes, 5 128 octets, environ 2,1 k tokens | `banc-rejeu/claude_md/minimal.md` : 16 lignes, 1 106 octets, environ 0,4 k tokens |

Constat important : **le dépôt `usine-migration-jira-demo` n'a aucun CLAUDE.md, ni aujourd'hui ni dans aucun commit.** Le fichier chargé pour ce projet en usage réel est celui du dossier parent `GitHub`, qui vaut pour tous les projets ; il est hors de git, donc « tel qu'il était au commit de base » n'est pas datable et j'ai pris sa version du 2026-10-24. Il contient surtout des consignes BMAD (section « Étape suivante recommandée », grille modèle et effort), sans aucune commande de test ni de lint.

Le CLAUDE.md utilisateur global est donc isolé, ce qui est faisable. Il pèserait de la même façon sur les deux conditions (3,1 k tokens et un renvoi vers l'orchestration par sous-agents, étranger à une session headless).

**Le CLAUDE.md minimal** (rédigé depuis le prompt de l'agent `dev-story` du dépôt, `pyproject.toml` et la seule règle de (a) qui touche au code, « tests ciblés pendant le développement, suite complète une fois à la fin ») :

```
# usine-migration-jira-demo (Python 3.12, uv, Polars, FastAPI)
Code, commentaires, docstrings et messages d'erreur en français.
## Commandes
- Toujours `uv run ...` (jamais `python`, `pytest` ni `ruff` nus).
- Pendant le développement : tests ciblés, `uv run pytest -q <chemins>`.
- Une seule fois, à la fin : `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run lint-imports`, `uv run pytest -q`.
- Les tests marqués `reseau` et `lent` sont exclus par défaut : les tests n'utilisent ni réseau ni LLM réel.
## Règles
- `src/usine/contrats/` et `src/usine/ports/` sont gelés : changement additif seulement, dans un commit dédié « Feat: contrats x.y » ; sinon n'y touche pas.
- `lint-imports` (import-linter) impose les couches du dépôt : ne pas importer à rebours (ex. `domaine`, `ia` n'importent pas `adaptateurs`).
- Une seule story : ce qui dépasse son périmètre n'est pas implémenté.
- Ne jamais lire ni écrire `.env`. Aucun appel Jira ni LLM réel.
- Au plus 3 cycles « correctif puis tests » sur un même échec ; au-delà, arrête-toi et explique la cause.
```

## 4. Mesures

Par exécution : coût, tokens par type, tours, durée (JSON de sortie et transcription copiée dans `rejeu\_transcriptions`) ; puis `ruff check` et `ruff format --check` sur l'arbre de l'agent ; copie des tests cachés (ils écrasent un fichier de même chemin) et `pytest` dessus ; enfin la suite existante sans les tests cachés (`suite KO` = runs avec au moins un test existant en échec). Données brutes : `banc-rejeu/donnees/runs.jsonl` (76 runs au total pour T3 et T6), patches dans `donnees/patches/`.

Modèle : Sonnet 5.5, effort `medium` posé explicitement. **5 répétitions** par cellule au lieu des 2 du protocole : la première série (2 répétitions) donnait un écart de coût de ±15 % entre deux runs identiques, trop bruité pour trancher à 10 %. 4 stories × 2 conditions × 5 répétitions = 40 runs, 21 $ en équivalent API.

### Global par condition

| Condition | n | coût moyen | médiane | écart-type | tours | durée (s) | entrée neuve (k) | lecture cache (k) | sortie (k) | taux cachés | suite KO | ruff propre |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (a) CLAUDE.md actuel | 20 | 0,532 $ | 0,415 $ | 0,229 | 36,3 | 263 | 55,5 | 968 | 21,3 | 85,6 % | 6/20 | 12/20 |
| (b) CLAUDE.md minimal | 20 | 0,512 $ | 0,462 $ | 0,190 | 33,5 | 286 | 54,3 | 795 | 21,6 | 82,8 % | 5/20 | 20/20 |

### Par story (moyenne ; entre parenthèses le coût en dollars et le taux en % de chaque répétition)

| Story | (a) actuel | (b) minimal |
|---|---|---|
| s32 KPI | 0,406 $ ; 87 % (0,41 / 0,39 / 0,39 / 0,41 / 0,43 ; tous 87 %) | 0,426 $ ; 88 % (0,46 / 0,46 / 0,44 / 0,42 / 0,35 ; 87 à 91 %) |
| s42 Risque | 0,467 $ ; 83 % (0,37 / 0,56 / 0,52 / 0,42 / 0,47 ; 77 à 91 %) | 0,478 $ ; 81 % (0,53 / 0,47 / 0,40 / 0,49 / 0,50 ; 80 à 83 %) |
| s64 Classification | 0,901 $ ; 74 % (0,94 / 0,87 / 0,84 / 0,85 / 1,01 ; 72 à 78 %) | 0,807 $ ; 66 % (0,85 / 0,71 / 0,78 / 0,74 / 0,95 ; 78, 78, 72, 78, **22**) |
| s78 Outils | 0,352 $ ; 97 % (0,35 / 0,39 / 0,37 / 0,39 / 0,27 ; 87 à 100 %) | 0,339 $ ; 97 % (0,37 / 0,31 / 0,31 / 0,37 / 0,34 ; 87 à 100 %) |

Écart de coût du minimal par story : s32 +4,8 %, s42 +2,3 %, s64 −10,4 %, s78 −3,8 %. Seule s64, la story la plus longue, passe sous −10 %, avec 5 runs par cellule ; elle ne suffit pas à conclure.

### Comparaison appariée (même story, même numéro de répétition ; les runs sont indépendants, l'appariement ne sert qu'à neutraliser la story)

| Comparaison | Couples | Écart de coût agrégé | Écart relatif moyen [IC 95 % bootstrap] | Médian | Minimal moins cher | Écart de taux moyen |
|---|---|---|---|---|---|---|
| (b) minimal contre (a) actuel | 20 | −3,6 % | −0,4 % [−8 ; +7] | −4,9 % | 11 sur 20 | −2,8 pt (+6 / −5), −0,0 pt sans le run aberrant |

### Variance et contexte

- Coefficient de variation du coût entre répétitions d'une même cellule (moyenne sur les stories) : 11 % pour (a) comme pour (b). Un écart de 10 % entre conditions est donc du même ordre que le bruit d'un seul run ; il faut une vingtaine de runs par condition pour que l'IC se resserre autour de ±7 %.
- Contexte du premier appel de l'API : (a) 13,5 k, (b) 11,8 k tokens, soit 1,7 k de plus pour le fichier actuel. Une session fait en moyenne 21 appels (a) et 19 (b) ; en lecture de cache à 0,10 $ par million de tokens de Sonnet 5.5 plus une écriture, le surcoût direct du fichier actuel est d'environ 0,008 $ par run, soit 1,5 % du coût moyen. Le −3,6 % observé s'explique donc surtout par 8 % de tours en moins avec le minimal (33,5 contre 36,3), c'est-à-dire par le comportement de l'agent et le bruit, pas par la taille du fichier.
- Refus de permission (appels de `ruff` seul, de `.venv\Scripts\python.exe` ou de commandes composées avec `cd`, hors de la liste du protocole) : 5,0 par run en (a), 3,1 en (b). Sans commande nommée, l'agent essaie des outils nus.
- Plafonds de réussite : les tests cachés contiennent des cas ajoutés par la revue de la story (s32 : « historique tronqué », « hors jour ouvré », « ouverte sans date de dernière entrée », jamais atteints, 20 à 21 sur 23 dans tous les runs ; s42 : 27 à 32 sur 35 ; s64 : 13 ou 14 sur 18 hors aberrant). Le banc discrimine donc surtout le coût ; la réussite ne bouge que de 1 à 3 tests.
- Régressions de la suite existante : 6 runs sur 20 en (a), 5 sur 20 en (b), tous sur s78 (2 tests de `test_import_linter` qui exigent d'enregistrer le nouveau contrat `ia.agent`, non mentionné dans la spec) et un run de s32 en (a) ; aucun lien avec la condition.

Détail par run : `banc-rejeu/donnees/rapport-t3.md`.

## 5. Limites

- Le « CLAUDE.md actuel » est un fichier générique (BMAD, grille modèle) hors dépôt, de 2,1 k tokens, pas un CLAUDE.md de projet de 100 à 200 lignes : l'effet d'une réduction réelle serait proportionnel (environ 1 % du coût par 1 k tokens retirés pour 20 appels, plus pour les sessions longues).
- Sessions headless d'un seul agent, outils restreints, effort `medium` : ce n'est pas la chaîne `dev-story` → `second-avis` → `reviewer`, qui a son propre prompt de 0,6 k tokens.
- 4 stories d'un seul dépôt, tests cachés qui ne couvrent pas toute la spec (plafond de réussite) ; deux stories (s64, s78) portent aussi sur des fichiers hors tests cachés (câblage, import-linter) que seule la suite existante contrôle.
- Les coûts sont des estimations client ; Max ne facture pas au token. Une limite de session a interrompu deux runs (s78, répétition 5) : ils ont été relancés après la levée de la limite, les premiers sont archivés dans `donnees/pilote/runs-invalides-limite-session.jsonl`.
- Les transcriptions des runs sont dans `~/.claude/projects/C--Users-user-1-...-rejeu-*` : elles apparaîtront comme projets « autre » dans `mesurer-couts` ou T1 ; copies dans le scratchpad `rejeu\_transcriptions`.

## 6. Reproduire

Depuis `tests-pratiques/banc-rejeu/` (un seul processus à la fois ; `-I` pour les scripts autonomes) :

```
uv run --no-project python -I extraire_corpus.py              # corpus depuis le dépôt de référence
uv run --no-project python -I banc.py reference s32 s42 s64 s78   # valide les tests cachés, écrit interface.md et total_ref
uv run --no-project python -I banc.py lot plans/t3.json --max 2   # 16 premières exécutions ; plans/t3_ext.json : répétitions 3 à 5
uv run --no-project python rapport.py t3                      # tableaux ci-dessus (sans -I : importe agreger.py)
```
