=== proposal.md ===
# Proposal

## Why

Le banc d'essai doit comparer HyDE aux autres Architectures du niveau 1 (FR-20). HyDE ne cherche pas avec la Question mais avec l'embedding d'une réponse hypothétique. Il faut donc mesurer, avec les mêmes chunker, embedder et store que `naive_rag`, si cette réécriture améliore la recherche dense et combien coûte l'appel LLM en plus au poste `query`.

## What Changes

- Nouvelle Architecture enregistrée `hyde` (classe `Hyde`, module `wavelibrarian.architectures.hyde`). Son index dense a la même forme que celui de `naive_rag` : `passages.jsonl` + `vectors/`, mise à jour incrémentale, `retrieval_method: ranked`.
- Pour chaque Question, un appel au rôle LLM `hyde` (step `hyde`) produit une réponse hypothétique. Cet appel est tracé dans son propre span au poste `query`, à part du span `generate`.
- Le vecteur passé au Retriever est celui de la réponse hypothétique, encodé par `embed_queries`. Option `mix_question` (défaut `false`) : on prend la moyenne renormalisée des vecteurs de la réponse hypothétique et de la Question.
- La réponse hypothétique n'entre jamais dans le Contexte ni dans le prompt `generate`, et aucune Citation ne peut la désigner.
- `mix_question` et les réglages propres à l'appel `hyde` (modèle, `max_tokens`) font partie des `query_params`. Ils ne changent donc pas la clé d'index.
- Rien n'est cassé : le runner, la passerelle, les rôles LLM et le Faux LLM ne changent pas. Le rôle `hyde` existe déjà.

## Capabilities

### New Capabilities
- `hyde-architecture` : recherche dense guidée par une réponse hypothétique (génération, encodage, mélange optionnel avec la Question), plus le cloisonnement de cette réponse hors du Contexte et des Citations.

### Modified Capabilities
(aucune)

## Impact

- Nouveau fichier `src/wavelibrarian/architectures/hyde.py`. Il réutilise `NaiveRag` (`architectures/naive_rag.py`), le Retriever `dense` (`components/retrievers/dense.py`, paramètre `query_vector`), `ModelGateway.complete` (`ports/gateway.py`) et `build_arch_answer`.
- Il est découvert automatiquement par `registry.discover()`, sans modifier `architectures/__init__.py`.
- Nouveaux tests `tests/unit/architectures/test_story_6_3.py`, avec le Faux LLM, le faux embedder et le profil `test`. Aucun réseau.
- Aucune nouvelle dépendance. Coût : un appel LLM `hyde` et un seul appel `embed_queries` de plus par Question, au poste `query`.

## Hypothèses

- « Même index que `naive_rag` » veut dire même construction et mêmes Params d'index. `index_key()["params"]` de `hyde` est égal à celui de `naive_rag` à Composants égaux. Le cache d'index reste distinct, car la clé du runner contient le nom de l'Architecture et le runner n'est pas modifié.
- `Hyde` hérite de `NaiveRag` : `index`, `update`, `load` et `embedder_dim` sont partagés, seule `answer` est redéfinie.
- Modèle de l'appel `hyde` : Param `hyde_model`, `Annotated[str | None, ModelRefMeta("generator_models[0]")]`, sans `answer_producer`. S'il vaut `None` à la construction, on prend `self.generator.model_id`.
- `hyde_max_tokens` vaut 256 par défaut (> 0).
- `query_params` de `hyde` = `{"k", "mix_question", "hyde_model", "hyde_max_tokens"}`.
- L'appel `hyde` passe par `complete` (texte libre), avec `inputs={"text": question.text}`, `temperature` 0 et `seed=ctx.seed`. Seule la Question est envoyée, sans `question.history`.
- Le texte renvoyé est utilisé tel quel. S'il est vide ou ne contient que des blancs, on se rabat sur le vecteur de la Question (encodé par `embed_queries`), même avec `mix_question`.
- Avec `mix_question: true`, les deux textes sont encodés en un seul appel `embed_queries([hypothèse, question])`. Si la moyenne a une norme nulle (vecteurs opposés), on utilise le vecteur de la réponse hypothétique.
- Le Retriever reçoit `question.text` comme `query` en plus du `query_vector`, pour qu'un éventuel reranker ou retriever futur le lise. Avec `dense`, ce texte n'est pas utilisé.
- La réponse hypothétique n'est exposée ni dans l'`ArchAnswer` ni dans les attributs de trace : seul le span `hyde` (tokens, coût, latence) en garde la trace.
- `experiments/mini-test.yaml`, `tests/conformance/test_architectures.py` et `tests/e2e/test_sm3.py` n'existent pas dans ce dépôt. La story ne les crée pas : hors périmètre.

=== specs/hyde-architecture/spec.md ===
# Spec Delta

## Purpose

Permettre une recherche dense qui utilise l'embedding d'une réponse hypothétique générée par un LLM à la place de celui de la Question, pour mesurer l'effet de cette réécriture sur la recherche et son coût au poste `query`.

## ADDED Requirements

### Requirement: Architecture `hyde` sur l'index dense de `naive_rag`
Le système SHALL proposer une Architecture enregistrée sous le nom `hyde`. Elle indexe le Corpus exactement comme `naive_rag` (chunker, embedder, store vectoriel), prend en charge la mise à jour incrémentale et renvoie des Passages classés (`retrieval_method: ranked`) : exactement `k` Passages, de rangs 1 à `k`, à scores décroissants.

#### Scenario: Index identique à celui de naive_rag
- **WHEN** on construit `hyde` et `naive_rag` avec les mêmes chunker, embedder et store
- **THEN** leurs paramètres de clé d'index sont égaux, et le dossier d'index de `hyde` contient `passages.jsonl` et `vectors/` comme celui de `naive_rag`

#### Scenario: Passages classés
- **WHEN** on répond à une Question avec `k = 5` sur un Corpus d'au moins 5 Passages
- **THEN** la Réponse a `retrieval_method` égal à `ranked` et contient 5 Passages, de rangs 1 à 5, à scores décroissants

#### Scenario: Paramètres de requête hors de la clé d'index
- **WHEN** on change seulement `mix_question`, `k` ou le modèle de l'appel `hyde`
- **THEN** la clé d'index reste la même et l'index en cache est réutilisé

### Requirement: Génération de la réponse hypothétique tracée à part
Pour chaque Question, le système SHALL faire exactement un appel LLM au rôle `hyde`, avec l'étape `hyde`, imputé au poste `query`, qui produit une réponse hypothétique. Cet appel MUST apparaître dans un span distinct du span de l'étape `generate`, et le précéder.

#### Scenario: Span hyde distinct
- **WHEN** on répond à une Question au poste `query`
- **THEN** les traces contiennent un span LLM d'étape `hyde` au poste `query` et un span d'étape `generate`, distincts, le span `hyde` venant d'abord

#### Scenario: Un appel hyde par Question
- **WHEN** on répond à deux Questions
- **THEN** exactement deux appels au rôle `hyde` ont été faits, chacun avec le texte de sa Question

### Requirement: Vecteur de recherche issu de la réponse hypothétique
Par défaut (`mix_question = false`), le système SHALL rechercher avec le vecteur de la réponse hypothétique, obtenu par l'encodage de requête de l'embedder. La Question elle-même n'est pas encodée.

#### Scenario: Vecteur transmis au Retriever
- **WHEN** on répond avec `mix_question` à `false`
- **THEN** le vecteur reçu par le Retriever est égal à l'encodage de requête de la réponse hypothétique

#### Scenario: Passage repris mot pour mot
- **WHEN** la réponse hypothétique scénarisée reprend le texte d'un Passage précis qui n'est pas au rang 1 quand on cherche avec la Question seule
- **THEN** ce Passage est au rang 1 des Passages retrouvés

#### Scenario: Réponse hypothétique vide
- **WHEN** la réponse hypothétique est vide ou ne contient que des blancs
- **THEN** la recherche utilise l'encodage de requête de la Question

### Requirement: Mélange optionnel avec la Question
Quand `mix_question` vaut `true`, le système SHALL rechercher avec la moyenne des encodages de requête de la réponse hypothétique et de la Question, renormalisée à une norme L2 de 1. `mix_question` MUST être un paramètre de requête, `false` par défaut.

#### Scenario: Moyenne renormalisée
- **WHEN** on répond avec `mix_question` à `true`
- **THEN** le vecteur reçu par le Retriever est égal à (h + q) / ‖h + q‖, h et q étant les encodages de requête de la réponse hypothétique et de la Question

#### Scenario: Valeur par défaut et paramètre de requête
- **WHEN** on construit `hyde` sans préciser `mix_question`
- **THEN** `mix_question` vaut `false` et figure parmi les paramètres de requête de l'Architecture

#### Scenario: Moyenne de norme nulle
- **WHEN** les deux encodages sont opposés et leur somme est nulle
- **THEN** la recherche utilise l'encodage de la réponse hypothétique, sans erreur

### Requirement: Réponse hypothétique exclue du Contexte et des Citations
Le système MUST construire le Contexte et le prompt de génération uniquement à partir de la Question et des Passages retrouvés. La réponse hypothétique n'apparaît dans aucun bloc du Contexte, et aucune Citation ne peut la désigner.

#### Scenario: Absente du Contexte et du prompt
- **WHEN** la réponse hypothétique scénarisée contient un marqueur absent du Corpus
- **THEN** ce marqueur n'apparaît dans aucun bloc du Contexte ni dans les messages de l'appel `generate`

#### Scenario: Citations limitées aux Passages
- **WHEN** la génération cite toutes les étiquettes du Contexte et une étiquette inexistante
- **THEN** chaque Citation renvoie à un Ancrage d'un Passage retrouvé, et l'étiquette inexistante est retirée et comptée dans `invalid_citations`

=== tasks.md ===
# Tasks

## 1. Architecture `hyde`

- [ ] 1.1 Créer `src/wavelibrarian/architectures/hyde.py` (docstring de module en français), avec `@register("architecture", "hyde") class Hyde(NaiveRag)` : `name = "hyde"` et `capabilities` comme `NaiveRag` (`incremental_update=True`, `retrieval_method="ranked"`). Champ `query_params = frozenset({"k", "mix_question", "hyde_model", "hyde_max_tokens"})`. Classe `Params(NaiveRag.Params)` avec `mix_question: bool = False`, `hyde_model: Annotated[str | None, ModelRefMeta("generator_models[0]")] = None` et `hyde_max_tokens: int = Field(default=256, gt=0)` (`extra="forbid"` et `frozen=True` hérités). Dans `__init__`, après `super().__init__`, poser `self.hyde_model_id = params.hyde_model or self.generator.model_id`. Ne pas redéfinir `index`, `update`, `load` ni `embedder_dim`. Vérification : `registry.get("architecture", "hyde") is Hyde` ; à Composants égaux, `index_key()` de `hyde` est égal à celui de `naive_rag` ; changer `mix_question`, `k` ou `hyde_model` ne change pas `index_key()` (tests 1.4).
- [ ] 1.2 Écrire une méthode privée qui génère la réponse hypothétique. Elle construit un `LLMRequest(model_id=self.hyde_model_id, role="hyde", step="hyde", system=<consigne en français : rédiger un court passage qui répondrait à la question, dans sa langue, sans préambule>, messages=(Message(role="user", content=question.text),), max_tokens=params.hyde_max_tokens, seed=self.ctx.seed, inputs={"text": question.text})`, puis renvoie `self.ctx.gateway.complete(requete).text`. Pas de `question.history`, pas de trace manuelle : le span vient de la passerelle. Vérification : le test 1.4 trouve dans `traces.jsonl` un span `wl.step == "hyde"`, `wl.post == "query"`, `wl.kind == "llm"`, avant le span `generate`.
- [ ] 1.3 Écrire le calcul du vecteur de recherche et redéfinir `answer`. Si `self._index is None`, lever `RuntimeError("`load` doit précéder `answer`")`. Si l'hypothèse `.strip()` est vide, utiliser `embed_queries([question.text])[0]`. Sinon, sans `mix_question`, utiliser `embed_queries([hypothese])[0]`. Avec `mix_question`, faire un seul appel `embed_queries([hypothese, question.text])`, calculer `s = v[0] + v[1]` puis `s / ‖s‖` en `float32`, et revenir à `v[0]` si `‖s‖ == 0`. Appeler ensuite `self.retriever.retrieve(question.text, k, self._index, query_vector=vecteur)`, `self.context_builder.build([s.passage for s in classes])` et `self.generator.generate(question, contexte)` (la Question seule, jamais l'hypothèse), puis `build_arch_answer(contexte, resultat, classes, "ranked", tokenizer=self.ctx.tokenizer_for(self.generator.model_id))`. Vérification : tests 1.4.
- [ ] 1.4 Écrire `tests/unit/architectures/test_story_6_3.py` sur le modèle de `test_story_6_2.py` : fixture `ctx` avec `FakeProvider`, profil `test`, `ctx.parser = "markdown"` ; `_arch(ctx, **params)` avec `embedder={"name": "fake"}` et `chunker=PETITS` ; fixture `minicorpus` ; `IndexCache` ; `_spans(ctx)` sur `traces.jsonl` ; réponses dans `ctx.scope(post="query", question_id="q-001")`. Cas à couvrir :
  - enregistrement, capacités et égalité d'`index_key()` avec `naive_rag` ;
  - 5 Passages classés de rangs 1 à 5, à scores décroissants ;
  - span `hyde` distinct de `generate` et placé avant lui ; un appel `hyde` par Question, avec `inputs["text"]` égal à la Question ;
  - vecteur transmis au Retriever (espion sur `arch.retriever.retrieve` qui capture `query_vector`) égal à `arch.embedder.embed_queries([hyp])[0]` ;
  - `mix_question: true` : vecteur égal à la moyenne renormalisée calculée dans le test, et `"mix_question" in Hyde.query_params` ; `mix_question` par défaut `False` ;
  - repli sur la Question pour une hypothèse `"   "` ; repli quand la somme est nulle (espion `embed_queries` qui renvoie `v` et `-v`) ;
  - rang 1 avec `ctx.provider.script("hyde", "hyde", <texte d'un Passage du minicorpus qui n'est pas au rang 1 avec naive_rag>)` ;
  - marqueur unique (ex. `"ZZHYPOZZ"`) scénarisé dans `hyde`, absent de `contexte.blocks` et des messages ou `inputs["blocks"]` de la requête `generate` capturée par `script("generate", "generate*", ...)` ;
  - Citations ⊆ Ancrages des Passages retrouvés, et `invalid_citations == 1` pour `S99` ;
  - `answer` sans `load` lève `RuntimeError`.

  Vérification : `uv run pytest -q tests/unit/architectures/test_story_6_3.py` passe.
- [ ] 1.5 Vérifier la non-régression des Architectures voisines : `uv run pytest -q tests/unit/architectures tests/unit/llm` passe.

## 2. Contrôles finaux

- [ ] 2.1 Lancer une seule fois `uv run ruff check .` et `uv run ruff format --check .`. Vérification : les deux commandes réussissent sans erreur.
