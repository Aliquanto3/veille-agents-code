### Story 3.4 : Juge LLM et correspondance exacte normalisée

As a Anaël,
I want un Juge qui note plusieurs Critères en un appel, et une correspondance exacte pour les réponses courtes,
So that le Filtre closed-book puis le Panel notent les Réponses de façon reproductible et peu coûteuse.

**Exigences :** FR-36, FR-12 (critère de réussite), FR-34 (`pass_id`) ; AD-4 (rôle `judge`), AD-14 ; `contracts.md` §2 (`Judge`, `JudgeInput`), §3.

**Acceptance Criteria:**

**Given** le Composant `components/judges/llm.py`, enregistré `("judge", "llm")` avec un `model` en `ModelRef`
**When** on appelle `judge(item, ["correctness", "completeness", "faithfulness"], pass_id=0)` avec le Faux LLM
**Then** un seul appel au rôle `judge` est émis, et le résultat donne pour chaque Critère un verdict booléen et une justification courte
**And** une sortie non conforme après un nouvel essai lève `NonConformantOutput`

**Given** deux appels identiques avec `pass_id` 0 puis 1
**When** on juge
**Then** le second n'est pas servi par le Cache de réponses (FR-34)

**Given** `scoring/answer.py` et la fonction `exact_match(reference, answer)`
**When** la référence vaut « 1 412 » et la réponse « La guilde fut fondée en 1412. »
**Then** elle renvoie vrai, après normalisation de la casse, des accents, de la ponctuation et du format des nombres
**And** « Élodie Varn » correspond à « elodie varn », « 3,5 » à « 3.5 », et « 1413 » ne correspond pas à « 1412 »
**And** la fonction `is_short_form(reference)` reconnaît un nombre, une date ou une expression d'au plus 5 mots

**Given** le Critère `faithfulness`
**When** on construit le `JudgeInput`
**Then** `context_texts` reprend les textes fournis au Generator (AD-6), jamais une reconstruction
