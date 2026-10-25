### Story 3.5 : Filtre closed-book et commande `wl questions closed-book`

As a Anaël,
I want poser chaque Question sans contexte à plusieurs modèles,
So that je sache quelles Questions un modèle connaît déjà et que leurs scores soient lus à part.

**Exigences :** FR-12 ; AD-8 (poste `judging`), AD-14 (Juge du Filtre closed-book), AD-15 ; `contracts.md` §3 (rôle `closed_book`), §8.

**Acceptance Criteria:**

**Given** `evalset/closed_book.py`, un fichier de Questions et les modèles `fake-llm-a` et `fake-llm-b`
**When** on lance `wl questions closed-book <questions.yaml> --modeles fake-llm-a,fake-llm-b`
**Then** chaque Question `validated` ou `corrected` est posée sans contexte à chaque modèle, au rôle `closed_book`, et les Questions `unanswerable` ne passent pas le filtre
**And** sans `--modeles`, la liste vient de `closed_book_models` du profil

**Given** une Question à réponse courte et un modèle dont la sortie scénarisée contient la Réponse de référence
**When** on applique le filtre
**Then** la Question reçoit `contaminated_by: [<modèle>]`, par correspondance exacte normalisée et sans Juge

**Given** une Question à réponse libre
**When** un modèle de famille `fake-a` y répond
**Then** le verdict de `correctness` vient du Juge `closed_book_judge` (premier modèle du réservoir d'une autre famille), et la Question est marquée contaminée si ce verdict est « oui »

**Given** le Faux LLM par défaut, qui renvoie la question inchangée
**When** on filtre le Jeu du Mini-corpus
**Then** aucune Question n'est contaminée

**Given** un Jeu déjà Gelé
**When** on relance le filtre
**Then** seul `contaminated_by` change, l'empreinte du Gel reste valide (AD-15), et les spans portent `wl.post=judging`
