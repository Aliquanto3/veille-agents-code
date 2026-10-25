### Story 2.7 : Paliers de volume et commande `wl corpus paliers`

As a Anaël,
I want tirer des Paliers de volume emboîtés et reproductibles,
So that je mesure l'effet du volume sans que les Documents des Ancrages de référence disparaissent d'un Palier.

**Exigences :** FR-54 (tirage) ; AD-20, AD-22 (`required_paths`) ; `contracts.md` §4.1 (`tiers`), §8.

**Acceptance Criteria:**

**Given** `corpus/tiers.py`, le Mini-corpus, `tiers: {seed: 42, sizes: [5, 10, 20]}` et une liste `required_paths` de trois Documents
**When** on tire les Paliers
**Then** le Palier 5 est inclus dans le Palier 10, lui-même inclus dans le Palier 20, et les trois `required_paths` figurent dans chacun
**And** un second tirage avec la même graine donne les mêmes Paliers, et une autre graine donne un tirage différent sur les Documents non requis

**Given** `required_paths` plus nombreux que la plus petite taille
**When** on tire les Paliers
**Then** une `ConfigError` explique que le Palier ne peut pas contenir tous les Documents requis

**Given** une taille supérieure au nombre de Documents du Corpus
**When** on tire les Paliers
**Then** une `ConfigError` signale la taille au chemin `tiers.sizes[i]`

**Given** un Palier tiré
**When** on construit le sous-corpus correspondant
**Then** c'est un `ParsedCorpus` restreint à ces Documents, avec sa propre `fingerprint`

**Given** la CLI
**When** on lance `wl corpus paliers <corpus.yaml>`
**Then** elle affiche chaque taille et ses `source_path`, en français, et sort en 0 ; sans clé `tiers`, elle l'indique et sort en 0
