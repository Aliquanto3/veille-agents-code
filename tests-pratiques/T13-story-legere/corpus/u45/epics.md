### Story 4.5 : Recette de la Prévision sur les Scénarios de démo

As a auteur,
I want vérifier qu'en fin d'historique A sort dans l'horizon, B ne sort pas et C est signalée,
So that l'étape Prévision de la démo est garantie.

**Exigences :** FR-20, FR-21 · **AD :** AD-18 · **Prérequis externe :** Story 1.8

**Prérequis :** contrats 1.2 (flux scripté des Scénarios A et B, Certification de B réservée, C à 50 Cas de test : partie générateur livrée par la PR de contrats). La story ne garde que la recette.

**Acceptance Criteria:**

**Given** le Journal généré et la Grille par défaut
**When** le test calcule les Prévisions au dernier Jour ouvré de l'historique par le chemin de la Chaîne (`prevision_du_passage`, étape `prevision`)
**Then** A a une date de sortie dans l'horizon, B porte « pas de sortie projetée » et C porte un Risque d'entrée en rouge (SM-6)

**Given** un écart
**When** l'auteur le corrige
**Then** il le corrige dans le générateur (Epic 1), jamais par un réglage de la Baseline sur les Scénarios (SM-C3)

**Given** une Entité non rouge qui porte un Risque d'entrée en rouge
**When** l'étape `prevision` publie `previsions.json`
**Then** la valeur projetée du Risque (`valeur_projetee_*`) est remplie depuis `risque.py`
