# T7 ter : un `DESIGN.md` maison améliore-t-il la note humaine ? Protocole

Fixé le 2026-10-25, **avant le premier essai** (`DESIGN.md` et `tache-ecran2.md` sont figés avec ce fichier).

## 1. Question et hypothèse
Un court fichier de règles maison (`DESIGN.md`, 6 groupes de règles tirés des commentaires d'Anaël sur l'écran de T7), placé à la racine du projet à côté de la skill `frontend-design`, améliore-t-il la note humaine à l'aveugle d'écrans métier FastAPI + Jinja2 vanilla, sans surcoût notable ? Comme les règles viennent de l'écran de T7, elles doivent aussi valoir sur un écran qu'elles n'ont pas vu : l'écran 2 sert de test de généralisation.

## 2. Bras
| Bras | Skill | `DESIGN.md` | Consigne |
|---|---|---|---|
| **b2** | `frontend-design` (projet) | non | « Pour la conception de l'interface, charge et applique d'abord la skill `frontend-design` (outil Skill), puis construis l'écran. » (identique à T7) |
| **b5** | `frontend-design` (projet) | copié à la racine du projet du bras | la phrase de b2, puis « Applique aussi les règles de `DESIGN.md` à la racine du projet ; en cas de conflit avec la skill, elles l'emportent. », puis la tâche. Rien d'autre ne change. |

Le nom `b2` est repris de T7 pour garder la même référence (même consigne, même skill, même SHA) ; `b5` est le nouveau bras.

## 3. Écrans
- **Écran 1** : `T7/scripts/tache.md` tel quel (« Demandes d'achat »), sur la même base d'application que T7 (`/demandes` en liste brute, `SERVICES`, `DEMANDES` : six lignes). Donné **à titre indicatif seulement** : les règles en viennent.
- **Écran 2** : `tache-ecran2.md` (« Notes de frais »), écrit avant tout essai, même style de contrat vérifiable (formulaire à cinq champs avec erreurs, tableau avec colonne d'identité, montants, deux colonnes de catégorie (catégorie, statut), section de totaux, action principale). Il fait jouer les mêmes familles de règles sans copier l'écran 1 : autres champs (dont une date), autres libellés, un statut en plus de la catégorie, des totaux par statut, une base d'application distincte (`/notes-de-frais`, `CATEGORIES`, `STATUTS`, `NOTES` : huit lignes). Le script `scripts/verifier_vocabulaire.py` confirme qu'aucun mot propre aux règles (gras, bordure, fond, étiquette, alterné, droite, tabulaire, rouge, icône, palette…) n'est dans l'énoncé ; restent des mots du domaine inévitables (erreur, champ, formulaire, statut, catégorie, montants).

## 4. Exécutions
- **3 essais par bras et par écran**, soit 12 exécutions `claude -p` (2 bras × 2 écrans × 3), modèle `claude-sonnet-5-5`, effort `medium`.
- Réglages repris de `T7/scripts/lancer_claude.py` et `lancer_bras.py` : `--setting-sources project,local`, `--no-chrome`, `--strict-mcp-config`, `--permission-mode acceptEdits --permission-prompts none`, `--tools Read,Write,Edit,Glob,Grep,Bash,Skill`, `--allowedTools Read,Write,Edit,Glob,Grep,Skill,Bash(uv run *),Bash(node *),Bash(*impeccable*),Bash(ls *),Bash(cat *)`, `stream-json --verbose`, `--no-session-persistence`. La skill est installée au niveau du projet (`.claude/skills/frontend-design`, SHA `dbd4588f9e1033efb41dad4bef2f7947c8993d44` d'anthropics/skills, identique octet par octet à celle de T7), jamais au niveau utilisateur.
- **Au plus 2 sessions `claude -p` en même temps.** Un seul navigateur ou une seule suite de mesures à la fois, pas d'Ollama ni de GPU.
- **Plafond par exécution** : `--max-budget-usd 1.5` (T7 : 6). Écart voulu, pour que le budget global de 6 $ de ce test ne puisse pas être crevé par une seule exécution ; les exécutions de T7 coûtaient de 0,26 à 0,44 $.
- **Budget** : 6 $ au plus pour l'ensemble (estimation : 0,32 $ par essai, soit 3,8 à 4 $). Arrêt et rapport si la projection dépasse 6 $.
- Les flux bruts (`stream-json`) restent dans le scratchpad ; le dépôt ne reçoit que des métadonnées résumées et anonymisées.

## 5. Mesures automatiques par rendu (indicatives)
Comme en T7 (`scripts/mesure_page.py`, adapté de T7 pour les deux écrans) :
1. **Contrat fonctionnel** vérifié dans un vrai navigateur (Edge headless via Playwright Python) : 30 points pour l'écran 1 (identique à T7), 38 pour l'écran 2.
2. **axe-core 4.13.0** à 390, 768 et 1280 px et dans l'état d'erreur à 1280 px.
3. **`impeccable detect`** (moteur 0.1.17, sha256 `edb62bff…f94ee` vérifié identique à T7).
4. Coût, tours, tokens, durée, skills invoquées ; poids CSS ; captures aux largeurs et états de T7 ; contraste ; focus ; débordement à 390 px.
5. **Conformité à chaque règle de `DESIGN.md`**, mesurée dans le DOM et le CSS calculé (`scripts/mesure_page.py`, fonction `conformite`) :

| Règle | Contrôle | État mesuré |
|---|---|---|
| R1 : pas de contour ni de bordure d'accent autour du bloc d'alerte | aucune bordure colorée (écart entre canaux RGB supérieur à 40) ni ombre portée ou ombre interne colorée sur `[role=alert]` | erreur, 1280 |
| R1 bis : le bloc d'alerte est en haut du formulaire | le bloc est au-dessus du premier champ et à moins de 400 px au-dessus du bouton d'envoi, ou dans le formulaire | erreur, 1280 |
| R2 : champ invalide à bordure rouge, sans fond rouge | bordure du champ `aria-invalid="true"` rougeâtre (rouge dominant de 40 sur vert et bleu), fond non rougeâtre | erreur, 1280 |
| R3 : action principale en haut et repérable | bouton d'envoi dans le premier écran (haut de page à moins de 900 px à 1280 px) et plus contrasté que les autres boutons (fond plein, contraste au moins 3:1 avec le fond de page) | initial, 1280 |
| R4 : lignes alternées | fonds calculés différents entre deux lignes consécutives visibles | initial, 1280 |
| R4 bis : en-têtes distincts | le fond de `th` diffère du fond des cellules, ou le gras ou la bordure basse diffère | initial, 1280 |
| R5 : colonne d'identité en gras | `font-weight` calculé de toutes les cellules de la 1re colonne au moins 600 et strictement supérieur à celui de la colonne de description | initial, 1280 |
| R6 : montants à droite, chiffres tabulaires | `text-align` droit sur toutes les cellules et l'en-tête de la colonne Montant, `font-variant-numeric` contenant `tabular-nums` (ou police à chasse fixe) | initial, 1280 |
| R7 : valeurs de catégorie en étiquettes | pour chaque colonne de catégorie (service ; catégorie et statut), chaque cellule contient un élément à fond ou bordure visible, à coins arrondis, dont le texte est la valeur ; contraste du texte de l'étiquette au moins 4,5:1 ; une couleur de fond distincte par valeur | initial, 1280 |
| R8 : même police et mêmes styles de libellé à tous les formats | famille, graisse, casse (`text-transform`), interlettrage de `body`, `h1`, `label`, `th`, `button`, `td` identiques à 390 et à 1280 px ; la taille est notée à part | initial, 390 et 1280 |
| R9 : pas trop sobre | nombre de couleurs distinctes non neutres (écart entre canaux RGB supérieur à 40) dans les fonds, textes et bordures du DOM visible | initial, 1280 |

Chaque contrôle donne vrai, faux ou non applicable ; le score de conformité est le nombre de contrôles vrais sur les contrôles applicables. **C'est indicatif : la note humaine tranche.** Limites connues : les pseudo-éléments (`::before`, `::after`) ne sont pas lus ; R3 et R7 sont des approximations.

## 6. Note à l'aveugle
- `notation.html` : page autonome (captures en base64), les 12 rendus **groupés par écran** (écran 1 : lettres A à F ; écran 2 : lettres G à L), lettres tirées par `secrets` à l'intérieur de chaque écran. Cinq vues par rendu aux largeurs et états de T7 (1280 et 390 à l'état initial et après un envoi invalide, 768 à l'état initial). Trois grilles de 1 à 5 (lisibilité, finition, cohérence), commentaire facultatif, sauvegarde locale, export JSON `notes-t7ter.json`.
- `correspondance.json` (lettre vers bras, écran, essai) est dans le `.gitignore` du dépôt avant sa création, n'est pas référencée par la page, et n'est ouverte que par `scripts/notes.py` après la note. Les rendus ne sont pas regardés pour être jugés.
- Dépouillement : `uv run --no-project python scripts/notes.py donnees/notes-anael.json` : moyennes par bras, par écran et par critère ; écart b5 − b2 ; intervalle de bootstrap apparié (appariement par écran et par numéro d'essai : les essais ne sont pas réellement appariés, c'est une convention de calcul, qui donne 6 paires pour les deux écrans et 3 pour l'écran 2 seul, donc un intervalle large) ; verdict selon le critère ci-dessous.

## 7. Critère de décision (écrit avant les essais)
On **garde `DESIGN.md`** si, simultanément :
1. b5 gagne **au moins 0,5 point** de moyenne (moyenne des trois critères) sur l'**écran 2** ;
2. la **cohérence** de b5 sur l'écran 2 n'est pas inférieure à celle de b2 ;
3. le **surcoût de b5 est d'au plus 10 %** par essai (coût moyen par essai, b5 contre b2, sur les six essais des deux écrans).

Sinon on l'écarte (ou on le retravaille avant un nouvel essai). L'écran 1 est **indicatif seulement** (les règles en viennent) et n'entre dans aucun des trois seuils.

## 8. Limites prévues
Trois notes par rendu et par critère pour six essais par bras et par écran de trois : bruit important (T7 : écart de 0,33 au plus entre deux rendus d'un même bras) ; un seul juge, Anaël, qui est aussi l'auteur des règles (il reconnaîtra peut-être l'effet des règles : le biais joue en faveur de b5) ; consigne qui nomme le fichier (l'effet mesuré est celui d'une règle appliquée sur demande explicite, pas d'une règle découverte par l'agent) ; Sonnet 5.5 seul ; les deux écrans partagent la même architecture d'application.

## 9. Précisions apportées pendant l'exécution (avant toute lecture de note, sans effet sur les exécutions)
Écrites après le lancement des premières exécutions et avant la note : elles ne changent ni les bras, ni les écrans, ni le critère de décision.
- Seuils de couleur de `scripts/conformite.js` : une couleur est « colorée » si l'écart entre ses canaux RGB dépasse 40 et son opacité 0,3 ; une bordure de champ est « rouge » si sa teinte est entre 335° et 15° (écart de canaux d'au moins 40) ; un **fond** est « rougeâtre » dès que sa teinte est entre 335° et 15° avec un écart de canaux d'au moins 8 (un rose très pâle compte comme un fond rouge). Pour R2, une ombre portée rouge en anneau compte comme bordure rouge.
- R8 compare l'interlettrage en `em` (rapport à la taille), pas en pixels : une valeur en `em` change en pixels avec la taille sans changer de style. Le premier jet comparait des pixels ; corrigé avant les mesures finales (les deux premiers rendus ont été remesurés).
- La lecture de `DESIGN.md` par l'agent est détectée aussi bien par l'outil `Read` que par une commande `cat` (le premier essai b5 l'a lu par `cat`).
- Les captures de notation sont enregistrées en JPEG de qualité 68 (page de 8,4 Mo).
