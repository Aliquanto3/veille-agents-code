### Story 13.2 : Vue Résumé à trois longueurs

En tant qu'Agent,
je veux choisir un résumé court, moyen ou détaillé d'un document collé,
afin d'adapter le résumé à mon usage (FR-15).

**Couvre :** FR-15.

**Fichiers et modules :** `src/slmsp/app/ui/js/vues/resume.js`, `src/slmsp/app/ui/css/resume.css`, `tests/app/ui/test_vue_resume.py` (marqué `ui`).

**Dépendances :** 12.8. **Taille :** S.

**Critères d'acceptation :**
1. **Étant donné** les trois longueurs, **quand** on en choisit une, **alors** l'entrée envoyée au Harnais porte `longueur_demandee` avec la valeur du libellé, celle du jeu gelé si elle existe, pour garder les conditions du banc.
2. **Étant donné** un document plus long que la fenêtre de contexte, **quand** on le soumet, **alors** le message d'entrée trop longue (UX-DR19) s'affiche si le Harnais le refuse.
