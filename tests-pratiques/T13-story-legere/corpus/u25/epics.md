### Story 2.5 : Source Journal à l'échelle et correspondance des clés

As a auteur,
I want charger le Journal d'événements complet comme seule source, avec les clés Jira appliquées,
So that toute Date d'arrêté de l'historique se calcule sans Jira, avec des clés cohérentes avec les liens.

**Exigences :** FR-8 · **AD :** AD-3, AD-4

**Acceptance Criteria:**

**Given** un Journal à la volumétrie cible et un `ManifesteInjection`
**When** `SourceJournal` le lit
**Then** il applique `correspondance_cles` à la lecture et émet des `Evenement` à clé Jira (AD-4)

**Given** `adaptateur: journal` en configuration et aucun accès réseau
**When** on calcule un Instantané pour une date quelconque de l'historique
**Then** le calcul aboutit, avec le même modèle de données en sortie que les autres sources
