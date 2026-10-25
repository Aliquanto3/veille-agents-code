## Intent

**Problem:** la vue Résumé (RE) affiche « non disponible » (FR-15).

**Approach:** `resume.js` réutilise `monterRedaction` (12.8, sans le modifier) avec trois boutons radio de longueur (« Court », « Moyen », « Détaillé », défaut « Moyen »). L'envoi porte `options.entree = {document, longueur_demandee}` avec les valeurs du Jeu gelé v1.1 : `courte`, `moyenne`, `detaillee`. Le pont transmis au volet est enveloppé : un document de plus de 4000 mots n'est pas envoyé et affiche le message d'entrée trop longue (UX-DR19), le volet montrant son message générique d'échec. Tout autre refus ou échec du pont garde le message générique. Pour RE le Harnais ne découpe pas (seul CR découpe) et ne refuse pas sur la longueur.

## Code Map

- `js/vues/resume.js`, `css/resume.css` ; `tests/app/ui/test_vue_resume.py` (9, `ui`) ; `test_socle_statique.py` : `resume` ajouté à `VUES_REALISEES`.
