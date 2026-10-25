### Story 10.2 : Rendu en tokens et masque de perte (H-MASQUE)

En tant qu'Anaël,
je veux une seule implémentation qui rend une conversation par le chat template officiel et masque la perte hors des tours `assistant`,
afin que tous les Runs d'une campagne apprennent exactement sur les réponses de l'assistant, avec le même format qu'à l'inférence.

**Couvre :** FR-34 (même chat template, même masque) ; AD-7 (masque, rendu officiel), AD-6 (`chat_template_kwargs`) ; H-MASQUE ; D-nuit-A1-22.

**Fichiers et modules :**
- `src/slmsp/train/rendu.py` (`apply_chat_template(messages, tools=...)` avec les `chat_template_kwargs` de `ConfigModele`)
- `src/slmsp/train/masque.py` (masque par rendu incrémental : positions des tours `assistant`, labels −100 ailleurs)
- `tests/train/test_masque.py` (tokenizers réels des candidats sous `models/`, sautés s'ils sont absents ; `pytest.importorskip("transformers")`)

**Dépendances :** 10.1, 4.1.

**Critères d'acceptation :**
1. **Étant donné** une conversation multi-tours avec `tool_calls` et messages `tool`, **quand** on calcule le masque pour un candidat, **alors** les tokens non masqués décodés correspondent exactement aux tours `assistant` du rendu officiel (contenu, appels d'outils sérialisés par le template, fin de tour), et tout le reste vaut −100.
2. **Étant donné** chaque candidat (Granite 4.0 1B, Ministral 3 3B, SmolLM3 3B, témoin Qwen), **quand** le test de rendu tourne, **alors** le résultat est consigné ; en cas d'échec, la variante d'entraînement du template limitée aux balises `generation` est produite et testée par égalité de rendu avec le template officiel, et le choix est consigné.
3. **Étant donné** le rendu d'entraînement, **quand** on le compare au rendu de `llama-server --jinja` pour la même conversation (test marqué `lent`), **alors** les deux textes sont identiques.

**Stratégie de test :** conversations synthétiques aléatoires ; tokenizers réels en `lent` ; aucun réseau.
