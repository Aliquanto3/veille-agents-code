### Story 5.1 : Étapes déterministes complètes et Passage autoportant

As a Pilote,
I want qu'un Passage contienne tous les Instantanés, KPI, Indicateurs, Météos, Tendances et Prévisions de chaque Jour ouvré jusqu'à la Date d'arrêté,
So that le rapport, l'UI, l'Agent et le Mode repli lisent tous les mêmes chiffres.

**Exigences :** FR-10 à FR-21, FR-34 (traces des Prévisions), FR-25 · **AD :** AD-7, AD-9, AD-16, AD-22

**Acceptance Criteria:**

**Given** le registre de `composition.py`
**When** les étapes `extraction`, `instantanes`, `kpi`, `meteo` et `prevision` s'exécutent
**Then** elles enveloppent les fonctions du domaine sans recalcul, et `EcrivainPassage` écrit `tickets_etats.parquet`, `tickets_textes.parquet`, `instantanes.parquet`, `kpi.parquet`, `indicateurs.parquet`, `meteo.json`, `tendances.parquet`, `previsions.json`, chacun validé par son contrat
**And** les sorties déterministes couvrent chaque Jour ouvré ≤ la Date d'arrêté (AD-7)

**Given** l'étape `prevision`
**When** elle se termine
**Then** chaque Prévision donne une `EntreeTrace` écrite dans `trace/previsions.jsonl` avec ses versions (AD-16)

**Given** le manifeste du Passage
**When** on le lit
**Then** il porte la Date d'arrêté, la source, `horodatage_extraction`, le nombre de tickets, le nombre d'alignements, `version_grille`, `version_donnees`, les durées par étape et `contrats_version`
