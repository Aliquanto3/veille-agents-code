## Spec Change Log

## Review Triage Log

### 2026-10-13 — Revue indépendante de l'orchestrateur (Opus, recoupée par Sonnet et Haiku) sur `22d7079`
- verdicts : high 1, medium 3 (dont un groupe sur `balayer_sm7`)
- findings :
  - `[high]` `[patch]` coût d'un appel en échec jamais ajouté au cumul : avec la tolérance, une alternance échec/succès pouvait dépasser le plafond sans trace — corrigé : la passerelle impute un coût majoré (3 requêtes, 2 caractères par jeton, `max_jetons_sortie` ×3) au cumul du Passage avant de relancer l'erreur ; `classer` s'arrête aussi à `MAX_ECHECS_PASSAGE` (20) échecs au total ; tests `test_cout_d_un_echec_impute_au_plafond`, `test_echecs_alternes_plafonnes_au_total`.
  - `[medium]` `[defer]` aucune `EntreeTrace` pour un appel en échec (angle mort SM-7 et `cout_llm_eur`) : l'entrée envoyée est la même entrée pseudonymisée qu'un succès, mais elle n'est pas tracée ; une trace d'échec touche `contrats.trace` (PR contrats).
  - `[medium]` `[defer]` préchauffage : échecs non mis en cache, `passage_id` neuf par tranche ; borné par tranche (20 échecs, part du plafond), relance manuelle.
  - `[medium]` `[patch]` `balayer_sm7` : faux vert sur espaces insécables et sur trace vide — corrigé : recherche sur textes compactés (tout blanc retiré), trace vide refusée (code 2) ; `--cache` reste optionnel mais la recette l'utilise.

### 2026-10-13 — Revue de suivi (constat high corrigé ; mode économique : Edge Case Hunter seul)
- verdicts : 8 constats — medium 2, low 4, false 1, rejet de conception 1
- findings :
  - `[medium]` `[defer]` coût majoré absent de `cout_llm_eur` : même report que ci-dessus. Sans effet sur la recette : aucun appel en échec dans le Passage mesuré.
  - `[medium]` `[defer]` `executer_agent` garde le défaut corrigé : Epic 7 (`ia/agent`).
  - `[low]` `[reject]` échec non facturé (HTTP, 429 épuisés) majoré quand même : prudent, le plafond s'épuise plus tôt, sans dépense.
  - `[low]` `[reject]` exception non `UsineErreur` : l'adaptateur convertit déjà toute erreur du fournisseur (`_executer`).
  - `[false]` `[reject]` `_tarif` qui lève dans le `except` : le tarif de production renvoie 0 € pour un modèle absent du registre.
  - `[low]` `[reject]` majorant sous-estimé si le schéma d'outil est volumineux : ×3 sur une entrée comptée à 2 caractères par jeton couvre largement le schéma de `ReponseClassification`.
  - `[low]` `[reject]` `balayer_sm7` en code 2 sur un Passage sans trace : voulu, l'outil sert la recette Palier 2 (pas de faux vert).
  - `[low]` `[patch]` autres blancs (U+202F, tabulation) : couverts par la recherche sur textes compactés ; test paramétré.

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports && uv run pytest -q` -- expected: tout vert.

## Auto Run Result

- **Résumé** : `classer` tolère les échecs isolés du fournisseur. Elle s'arrête à 3 échecs d'affilée ou 20 au total, et le coût majoré d'un échec compte au plafond. Le préchauffage du cache de classification (`composition.prechauffer_classification`, `outils/prechauffer_cache.py`) et le balayage SM-7 (`outils/balayer_sm7.py`) sont ajoutés. Tarifs Sonnet et Opus 5.5 recalés sur le tarif public du 13/10/2026.
- **Écart de procédure** : implémentation menée directement par l'agent de story (mode économique), sans sous-agent d'implémentation.
- **Recette réelle** (racine `sorties/recette-6-10-p2/`, Journal du Corpus définitif `llm-1` généré le 2026-10-12, source `journal`, aucune écriture Jira) :
  - **Fournisseur** : Mistral (`mistral-large-latest`, classification `mistral-small-latest`, différent du `modele_corpus` `mistral-medium-latest`). Mesuré : 0,25 m€ par Anomalie sur Haiku 5.5 (prompt réel de ~2 500 jetons). Le stock de 3 114 Anomalies aurait donc coûté ~0,93 € sur Anthropic, budget dépassé une fois SM-9 ajouté.
  - **Préchauffage** : 9 tranches de ≤ 9 min, 3 114 Anomalies classées, 0 échec. Coût estimé 0,292 €, facturé 0 € (offre gratuite, comme en 1.9).
  - **Passage mesuré** `20261013T060410Z-bf4e01` : **3 min 48 s** (manifeste), 4 min 02 s mur. 2 Entités rouges, 0 orange. Classification 3 114/3 114 servie par le cache (`classification_initiale: false`), répartition, 2 explications (ENT-A, ENT-B, 1 phrase retirée sur 4 chacune) et 2 narrations conformes. **`cout_llm_eur` 0,0105 €** (plafond du Passage 0,50 €).
  - **Rejeu** `20261013T060831Z-c15e6a` : 0 appel frais (toutes les traces `depuis_cache`), `cout_llm_eur` 0, `verifier_rejeu` **conforme** (19 différences, toutes exclues), 3 min 41 s.
  - **SM-7** : 6 236 textes balayés (traces du Passage et cache), 920 identifiants injectés, 7 607 jetons de Pseudonymisation, **0 fuite**.
  - **Verdict recette** : les 3 AC sont **atteints**.
  - **Réserves** : recette faite sur Mistral et non sur la configuration par défaut (Anthropic) ; source `journal` et non la source composite `DEMO`, dont les textes sont encore ceux du Corpus provisoire ; Mode repli non régénéré (relève de la 7.11).
- **SM-9 (report 6.9)** :
  - **Haiku 5.5, manuels réels** : F1 macro **1,000** (30/30, 0,0075 €).
  - **Haiku 5.5, générateur** : sur un échantillon des 982 premières Anomalies par clé, préchauffées dans `sorties/recette-6-10/` (2 `UnexpectedModelBehavior` tolérés, comptés faux), F1 macro **0,451**, exactitude 48 %. `donnee_test` n'est jamais proposée.
  - **mistral-small, générateur** (stock complet de la recette) : F1 macro 0,328.
  - **Verdict** : **SM-9 non atteint** sur la source générateur. Le signal cause/texte du Corpus semble faible. Résultats dans `evals/classification/resultats/`.
- **Coûts réels** :
  - **Anthropic** : ≈ **0,30 €** (0,0075 € manuels + 0,2935 € préchauffage Haiku, estimés au tarif public ; 2 appels en échec non chiffrés, < 0,002 €).
  - **Mistral** : **0 € facturé** (0,303 € estimés).
- **Vérification** : `ruff check`, `ruff format --check`, `mypy`, `lint-imports` (15 contrats) verts ; `pytest -q` 2 784 passés, 1 sauté.
