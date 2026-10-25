### Story 6.11 : [BONUS] Détection de doublons

As a Pilote,
I want des paires d'Anomalies probablement en doublon, avec un score,
So that je fais nettoyer le stock sans fusion automatique.

**Exigences :** FR-36 · **AD :** AD-2, AD-12

**Acceptance Criteria:**

**Given** les Anomalies ouvertes pseudonymisées
**When** la détection s'exécute
**Then** elle produit des paires avec un score, à revoir par le Pilote, sans aucune fusion ni écriture dans Jira
**And** la nouvelle tâche et son contrat de sortie sont ajoutés par une PR dédiée sur `main` (`contrats/`, liste des tâches d'AD-12), avant le code de la lane
