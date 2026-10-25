---
title: 'Story 13.2 — Vue Résumé à trois longueurs'
type: 'feature'
created: '2026-10-17'
status: 'review'
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/implementation-artifacts/consignes-sous-agents-nuit.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-12-8-vues-de-redaction-compte-rendu-et-langage-clair.md'
warnings: []
deferred: []
---

## Intent

**Problem:** la vue Résumé (RE) affiche « non disponible » (FR-15).

**Approach:** `resume.js` réutilise `monterRedaction` (12.8, sans le modifier) avec trois boutons radio de longueur (« Court », « Moyen », « Détaillé », défaut « Moyen »). L'envoi porte `options.entree = {document, longueur_demandee}` avec les valeurs du Jeu gelé v1.1 : `courte`, `moyenne`, `detaillee`. Le pont transmis au volet est enveloppé : un document de plus de 4000 mots n'est pas envoyé et affiche le message d'entrée trop longue (UX-DR19), le volet montrant son message générique d'échec. Tout autre refus ou échec du pont garde le message générique. Pour RE le Harnais ne découpe pas (seul CR découpe) et ne refuse pas sur la longueur.

## Code Map

- `js/vues/resume.js`, `css/resume.css` ; `tests/app/ui/test_vue_resume.py` (9, `ui`) ; `test_socle_statique.py` : `resume` ajouté à `VUES_REALISEES`.

## Auto Run Result

**Décisions prises seul :**
- Valeurs `courte|moyenne|detaillee` (Jeu gelé, plafonds 80/200/400 de `[re.longueurs]` dans `config/evaluation.toml`), et non `re_longueurs_mots = [80, 150, 250]` de l'entraînement : le critère 1 impose la valeur du jeu gelé. Aucune entrée `consigne` envoyée (pas de texte rédigé).
- Aucun nombre de mots affiché dans l'interface, pour ne pas dupliquer deux jeux de valeurs divergents.
- Libellés proposés : « Résumer », « Longueur du résumé », « Court / Moyen / Détaillé », titre de résultat « Résumé », invite « Collez le document à résumer, puis choisissez la longueur. Je ne rapporte que ce qui figure dans le texte. », message « Ce document est trop long pour être résumé tel quel. Raccourcissez-le, ou résumez-le en plusieurs parties. »

## À confirmer

- Alignement des longueurs d'entraînement (80/150/250) sur celles du jeu gelé (80/200/400) : écart existant, hors périmètre de la vue.
- Les libellés ci-dessus (à valider par Anaël).
- Plafond de 4000 mots, contrôlé dans la vue : contexte 8192 tokens des modèles (`config/modeles/*.toml`), moins ~1024 de sortie et la consigne, ~1,5 token par mot français. Aucun code d'erreur de longueur n'existe côté pont ; à affiner si le Harnais en expose un.
- Écart « N mots » d'entraînement (80/150/250) et mots du Jeu gelé (80/200/400) : déjà consigné, non corrigé ici.

## Revue

- medium, second avis (resume.js) : message « trop long » affiché sur tout refus ou exception, trompeur. Corrigé : contrôle côté vue avant envoi, plafond 4000 mots, aucun envoi au-delà ; autres cas : message générique. Spec corrigée (le Harnais ne découpe pas pour RE).
- high, reviewer : marqueurs de conflit de rebase commités dans `test_socle_statique.py` (le script de résolution n'avait pas tourné). Corrigé : union des vues, `VUES_REALISEES` complet.
- low, second avis : doublon `"resume"` dans `VUES`. Corrigé.
- low, second avis : tests manquants. Corrigé : `generation-en-cours` et `requete-invalide` sans message, rejet de `envoyer` avec message générique, plafond (4001 refusé sans envoi, 4000 envoyé). 9 tests.
- low, second avis : écart « N mots » entraînement/Jeu. Rejeté : déjà consigné, hors périmètre ; mentionné ci-dessus.
- Reporté : plafond 4000 mots à valider sur un vrai modèle (GPU/modèle non lancé ici) en collant un document de ~4000 mots et en vérifiant que la sortie n'est pas tronquée.
