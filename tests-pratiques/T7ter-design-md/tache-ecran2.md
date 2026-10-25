Tâche : construire l'écran « Notes de frais » de cette petite application FastAPI + Jinja2 (le répertoire courant). Aujourd'hui, `/notes-de-frais` n'affiche qu'une liste brute. Il faut en faire un écran métier complet, soigné et utilisable au clavier, sur ordinateur comme sur un téléphone de 390 px de large.

Contrat fonctionnel (à respecter à la lettre, des contrôles automatiques le vérifient) :
1. `GET /notes-de-frais` affiche un titre `h1` « Notes de frais », une section de totaux, un formulaire de saisie et le tableau des notes. Le tableau est trié par date de dépense décroissante ; à date égale, la note saisie en dernier vient en premier.
2. Formulaire (méthode POST vers `/notes-de-frais`, attribut `novalidate`, pas de validation HTML5 native bloquante) avec exactement ces champs, chacun avec un `label` lié dont le texte est exactement :
   - « Collaborateur » (texte, obligatoire) ;
   - « Catégorie » (liste déroulante à partir de `CATEGORIES`, avec une première option vide « Choisir une catégorie », obligatoire) ;
   - « Montant (€) » (nombre à deux décimales au plus, strictement supérieur à 0 et au plus 5 000) ;
   - « Date de la dépense » (`input type="date"`, obligatoire, au plus égale à la date du jour) ;
   - « Description » (zone de texte, entre 10 et 200 caractères) ;
   - bouton de validation : « Enregistrer la note ».
3. Validation côté serveur. Si le formulaire est invalide : réponse HTTP 422 qui réaffiche la page avec les valeurs saisies conservées, un message `role="alert"` contenant « Le formulaire contient N erreur(s). » (N = nombre d'erreurs ; « 1 erreur » au singulier, « 2 erreurs » au pluriel), et sous chaque champ fautif un message lié au champ (`aria-describedby`, `aria-invalid="true"`) dont le texte est exactement :
   - « Le collaborateur est obligatoire. »
   - « Choisissez une catégorie. »
   - « Le montant doit être un nombre supérieur à 0 et au plus 5 000 €. »
   - « La date de la dépense est obligatoire et ne peut pas être dans le futur. »
   - « La description doit contenir entre 10 et 200 caractères. »
4. Si le formulaire est valide : la note est enregistrée en mémoire (liste `NOTES` de `app/main.py`, avec le statut « Soumise »), redirection 303 vers `/notes-de-frais`, et un message de confirmation `role="status"` « Note de frais enregistrée. » s'affiche (message à usage unique, par exemple via un paramètre de requête ou un cookie).
5. Totaux : une `section` dont un titre `h2` est « Total par statut » indique, pour chacun des quatre statuts de `STATUTS` (y compris à 0), le nom du statut, le nombre de notes et le montant total au format `1 249,90 €`. Ces totaux portent sur toutes les notes enregistrées (ils ne dépendent pas des filtres) et sont recalculés par le serveur à chaque affichage.
6. Tableau : colonnes « Collaborateur », « Catégorie », « Montant », « Statut », « Description », « Date » (montants au format `1 249,90 €`, dates `jj/mm/aaaa`). Filtrage immédiat côté navigateur, sans rechargement, en JavaScript vanilla dans `app/static/app.js` : un champ de recherche dont le label est « Rechercher un collaborateur » (filtre sur le nom, sans tenir compte de la casse ni des accents) et une liste dont le label est « Filtrer par statut » (première option « Tous les statuts »). Les deux filtres se combinent. Un compteur `role="status"` indique « N note(s) affichée(s) » (écrire « 1 note affichée » ou « 4 notes affichées »). Quand aucune ligne ne correspond, le tableau est remplacé ou complété par le message « Aucune note ne correspond aux filtres. »
7. Contraintes techniques : HTML, CSS et JavaScript vanilla uniquement ; aucune bibliothèque ni framework JS ou CSS, aucun CDN, aucune police ni image distante (la page doit fonctionner hors ligne) ; aucune nouvelle dépendance Python. Les styles vont dans `app/static/style.css`, le script dans `app/static/app.js`, les gabarits dans `app/templates/`.
8. Ajoute des tests pytest (dans `tests/`) pour la validation, l'ajout et les totaux, puis lance `uv run pytest -q --tb=short` jusqu'à ce qu'ils passent. Ne démarre aucun serveur (ni `uvicorn` ni autre processus durable) et n'ouvre aucun navigateur.

Ne pose aucune question : fais des choix raisonnables, applique-les, et termine par un résumé de trois lignes au plus (choix de design, fichiers modifiés, état des tests).
