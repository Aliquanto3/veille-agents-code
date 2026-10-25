### Story 7.8 : Outils de consultation de l'Agent

As a Pilote,
I want que l'Agent dispose d'outils qui lisent la Météo, les Anomalies, les Tendances, les Prévisions et les Risques,
So that il répond à partir des chiffres du Passage, pour n'importe quelle Date d'arrêté disponible.

**Exigences :** FR-39, FR-41 · **AD :** AD-2, AD-5, AD-11

**Acceptance Criteria:**

**Given** `ia/agent`
**When** on liste ses outils
**Then** il expose exactement `get_meteo`, `list_anomalies` (filtres Entité, Gravité, Phase, statut), `get_tendance`, `get_prevision` et `get_risques`, aux signatures et résultats définis dans `contrats.agent`, servis par `Consultation`

**Given** l'inventaire des outils et des dépendances de l'Agent
**When** le test de lecture seule s'exécute
**Then** aucun outil n'écrit (Jira, mail, configuration) et l'Agent n'a aucun accès à Jira (AD-5)

**Given** une Date d'arrêté sans Passage
**When** un outil est appelé
**Then** il renvoie un résultat explicite « aucune donnée pour cette date »
