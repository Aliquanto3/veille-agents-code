### Story 5.6 : La fiche modèle explique son débit et ce qu'il donne sur d'autres postes

As a consultant face à un client qui hésite sur le matériel,
I want la fiche d'un modèle (dense ou MoE, paramètres actifs, quantification, licence, outils et raisonnement vérifiés), « Pourquoi ce débit ? » et « Sur d'autres postes »,
So that j'explique la vitesse observée et ce qu'elle serait sur un PC pro de 16 Go sans GPU.

**Gouverné par :** AD-15, AD-20, AD-22 ; AR19 ; UX-DR15, UX-DR27. **Reports :** B5.

**Acceptance Criteria:**

**Given** `models/catalog.py` qui lit `benchmarks/slm-quality/slm-quality-results.json` (modèle pydantic `extra="ignore"`, jamais par le réseau)
**When** le fichier manque ou que `schema` ne vaut pas `qb.results/1`
**Then** les références sont indisponibles avec une raison affichée, et aucune route ne dépasse 300 ms (test de budget) ; le fichier est lu une fois au démarrage et à sa modification
**And** `results[]` se joint à `models[]` sur `(model, digest)` ; un modèle installé correspond par `(tag, digest)`, à défaut par tag avec la mention « autre version » ; `ModelInfo.accuracy` est renseignée depuis ces résultats, ce qui active la règle du juge d'après la précision (1.6)

**Given** un clic sur un modèle de l'écran Modèles ou de `wl-model-picker`
**When** la fiche s'ouvre
**Then** elle montre dense ou MoE, paramètres totaux et actifs, quantification, licence, contexte, outils et raisonnement vérifiés (`/api/show` en cache `model_facts`, catalogue), avec « inconnu » pour une valeur absente, jamais 0
**And** le panneau est à droite dès 1 120 px, au-dessus de la liste en deçà, et `#/modeles/<tag>` l'ouvre directement (D-40, D-8) ; la fiche d'un modèle non installé qui ne tient pas porte « Installer quand même » (D-42)
**And** à côté de `wl-model-picker` (hors de la liste d'options), un bouton « Fiche du modèle » ouvre la même fiche en panneau sur l'écran courant, sans changer d'URL (décision du 2026-10-19)

**Given** « Pourquoi ce débit ? »
**When** on l'ouvre
**Then** il explique le débit mesuré sur ce poste par les paramètres actifs, la quantification, la bande passante mémoire et la VRAM (fiche locale, catalogue), sans calcul côté front

**Given** « Sur d'autres postes »
**When** on l'ouvre
**Then** il affiche, pour les trois postes de référence (dont le PC pro de 16 Go sans GPU), le débit et la tenue en mémoire publiés ; `null` s'affiche « inconnu », les fractions en pourcentage, `energy` seulement si `status = "measured"` (AD-22)
**And** axe-core sans violation, clair et sombre
