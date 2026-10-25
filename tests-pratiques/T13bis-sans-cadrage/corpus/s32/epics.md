### Story 3.2 : Bac à sable MCP : rejeu des cassettes

En tant qu'Anaël,
je veux un adaptateur qui rejoue les cassettes de façon déterministe, y compris les pannes simulées,
afin que deux évaluations du même modèle donnent les mêmes réponses d'outils et que le repli soit testable sans réseau.

**Couvre :** FR-9, FR-25, FR-40, NFR-8 ; AD-10 (appariement, rejeu) ; SPEC §4.

**Fichiers et modules :**
- `src/slmsp/mcp/bac_a_sable.py` (`BacASable`, adaptateur `ToolPort`)
- `config/outils-mcp.toml` (ajout du texte de la réponse vide normalisée)
- `tests/mcp/test_bac_a_sable.py`

**Dépendances :** 3.1.

**Critères d'acceptation :**
1. **Étant donné** les cassettes d'un item, **quand** le modèle appelle un outil avec des arguments dont le JSON canonique est égal à celui d'une interaction enregistrée, **alors** la réponse enregistrée est renvoyée, avec l'`id` JSON-RPC remplacé par celui de la requête.
2. **Étant donné** aucun appariement exact, **quand** une interaction du même outil existe, **alors** celle qui a le plus de paires (clé, valeur) égales est rejouée, l'égalité étant départagée par l'ordre dans la cassette, et un évènement « appel non prévu » est émis.
3. **Étant donné** aucun appel du même outil, **quand** le modèle appelle, **alors** la réponse vide normalisée `{"result": {"content": [{"type": "text", "text": <texte de config>}], "isError": false}}` est renvoyée avec l'évènement « appel non prévu ».
4. **Étant donné** une interaction `simulation` de type `delai_depasse`, `erreur_http` ou `injoignable`, **quand** elle est rejouée, **alors** la même exception que celle du client en direct est levée.
5. **Étant donné** une cassette dont `tools_list_sha256` diffère de `config/outils-mcp.toml`, **quand** le Bac à sable la charge, **alors** il la refuse avec `SchemaOutilModifie`.
6. **Étant donné** la même séquence d'appels, **quand** on la rejoue deux fois, **alors** les réponses sont identiques à l'octet près (adaptateur sans état).

**Stratégie de test :** cassettes R-001 et R-002 du calibrage en lecture seule ; cassettes de simulation construites dans `tmp_path` ; aucun réseau.
