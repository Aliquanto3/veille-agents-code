### Story 5.1 : Annotations humaines et kappa de Cohen

As a Anaël,
I want annoter des Réponses dans un fichier par annotateur et disposer d'un calcul de kappa fiable,
So that l'accord entre juges et humains se mesure sur des données que je contrôle.

**Exigences :** FR-38 (format et mesure) ; AD-5, AD-12, AD-22 (`stats/` en fonctions pures) ; `contracts.md` §4.6.

**Acceptance Criteria:**

**Given** `scoring/calibration.py` et un dossier `annotations/` contenant `anael.yaml` et `collegue.yaml` au format de `contracts.md` §4.6
**When** on charge les annotations
**Then** chaque annotation est indexée par (annotateur, `answer_id`, `criterion`), avec un verdict booléen
**And** un Critère hors de `correctness`, `completeness` et `faithfulness`, un verdict hors de `yes` et `no`, ou un doublon (même annotateur, `answer_id` et Critère) lève une `ConfigError` à son chemin (`annotations[3].criterion`)

**Given** des annotations dont l'`answer_id` est absent d'`answers.jsonl` de l'Exécution visée
**When** on les rapproche des Réponses
**Then** elles sont signalées par leur `answer_id` et ignorées ; l'`answer_id` est celui d'`Answer` (`contracts.md` §1), y compris `tier` et `phase`

**Given** `stats/kappa.py` et deux vecteurs binaires dont la table de contingence est connue (par exemple 20 oui-oui, 5 oui-non, 10 non-oui, 15 non-non)
**When** on calcule le kappa de Cohen
**Then** il égale la valeur calculée à la main dans le test, à 1e-12 près, soit 0,4
**And** deux vecteurs identiques donnent 1 ; un accord parfait sur une seule classe (kappa indéfini) renvoie `None` sans exception
**And** des vecteurs de longueurs différentes lèvent une `ValueError`
