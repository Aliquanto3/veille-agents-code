### Story 5.2 : Fonctions de texte partagées (normalisation, mots, nombres, Kandel-Moles)

En tant qu'Anaël,
je veux des fonctions de texte versionnées et partagées par le banc, l'anti-fuite et la construction du jeu,
afin qu'un gain de lisibilité ou un contrôle de valeur soit calculé d'une seule façon partout.

**Couvre :** FR-16 (Kandel-Moles), FR-24 (normalisation anti-fuite), FR-14 et FR-8 (extraction de nombres) ; AD-29.

**Fichiers et modules :**
- `src/slmsp/core/texte.py` (`VERSION_TEXTE`, `normaliser`, `compter_mots`, `decouper_phrases`, `extraire_nombres`, `syllabes`, `kandel_moles`, `ngrammes`)
- `tests/core/test_texte.py`

**Dépendances :** 1.1.

**Critères d'acceptation :**
1. **Étant donné** un texte, **quand** on appelle `normaliser`, **alors** le résultat est en NFKC, en minuscules, sans ponctuation, avec des espaces uniques ; la fonction est idempotente.
2. **Étant donné** des nombres écrits à la française (« 1 234,56 € », « 12,50 € », « 25 € », « 3,5 % », espace insécable), **quand** on appelle `extraire_nombres`, **alors** on obtient les valeurs décimales attendues.
3. **Étant donné** des phrases de référence dont l'indice est calculé à la main dans le test, **quand** on appelle `kandel_moles` (207 − 1,015 × mots/phrase − 73,6 × syllabes/mot, syllabation française par groupes vocaliques avec règle du e muet final), **alors** la valeur est exacte à 0,1 près ; un texte simplifié obtient un indice supérieur à sa version administrative.
4. **Étant donné** `VERSION_TEXTE`, **quand** une règle change, **alors** la version est incrémentée et le test de non-régression des valeurs de référence l'exige.

**Stratégie de test :** tests unitaires paramétrés à valeurs calculées à la main ; aucune dépendance externe.
