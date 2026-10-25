### Story 3.6 : Gel et séparation développement / test

As a Anaël,
I want geler un Jeu d'évaluation et le répartir en parties dev et test stratifiées,
So that aucune Exécution ne tourne sur un jeu modifié en douce et que la partie test reste réservée.

**Exigences :** FR-13, SM-C2 ; AD-15, AD-20 ; `contracts.md` §4.5, §8.

**Acceptance Criteria:**

**Given** `evalset/freeze.py` et un Jeu de 50 Questions `validated` réparties sur cinq Types
**When** on lance `wl questions geler <questions.yaml> --dev-ratio 0.4 --graine 42`
**Then** chaque Question participante reçoit `split: dev` ou `split: test`, stratifié par `type`, avec 40 % de dev dans chaque Type (arrondi documenté)
**And** `freeze` vaut `{sha256, at, seed, dev_ratio}`, où `sha256` est l'empreinte de `canonical_json` du document sans `freeze` ni `contaminated_by`
**And** un second Gel avec la même graine sur le même contenu produit la même répartition

**Given** un Jeu Gelé, puis une Question dont on modifie le texte
**When** on appelle `verify_frozen(questions)`, que le runner utilisera
**Then** elle lève une `ConfigError` qui signale une empreinte différente ; un Jeu non Gelé est refusé de même

**Given** un Jeu Gelé dont seul `contaminated_by` a changé
**When** on appelle `verify_frozen`
**Then** l'empreinte reste valide

**Given** `select_questions(questions, split="dev")`
**When** on l'appelle
**Then** elle ne renvoie que les Questions `validated` ou `corrected` de la partie dev ; la partie test n'est renvoyée que pour `split="test"` explicite

**Given** un Jeu contenant des Questions `generated`
**When** on le gèle
**Then** la commande les signale et refuse de geler tant qu'elles ne sont pas validées, corrigées ou rejetées
