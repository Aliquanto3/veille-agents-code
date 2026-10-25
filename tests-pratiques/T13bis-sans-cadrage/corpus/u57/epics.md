### Story 5.7 : Porte Palier 1 (M3)

As a Sponsor,
I want une démo Palier 1 complète, sans LLM, qui produit le rapport du jour en moins de 5 minutes,
So that la demande d'outillage reste recevable même si la banque refuse tout LLM.

**Exigences :** NFR-2, FR-25, FR-28 · **AD :** AD-8

**Acceptance Criteria:**

**Given** le poste de l'auteur, dont les caractéristiques figurent dans le README, et la volumétrie de FR-2
**When** l'auteur mesure `usine rapport` en Palier 1, extraction incrémentale comprise
**Then** la durée est inférieure à 5 minutes et la mesure est consignée (SM-2)

**Given** la porte M3
**When** l'auteur la passe
**Then** la CI est verte, la réconciliation est à 100 %, le Rejeu est idempotent, et le journal de fin de jalon M3 est écrit
**And** aucune story de l'Epic 6 ne démarre avant ce point
