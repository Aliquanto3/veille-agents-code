# T12 : un sous-agent de vérification dans un vrai navigateur pendant une story front

Test du 25 octobre 2026. Question : pendant le développement d'une story front (FastAPI, HTML/CSS/JS vanilla), un sous-agent qui parcourt les critères d'acceptation avec Playwright MCP attrape-t-il des défauts que pytest ne voit pas, et à quel coût ? Prolonge T7 (Playwright MCP réussit 6 parcours sur 6 pour 0,09 $ chacun, et le parcours navigateur avait été le seul contrôle à relever un écart que pytest laissait passer).

Toutes les sessions passent par l'abonnement Max : les coûts sont l'estimation client `total_cost_usd` de Claude Code, en dollars aux tarifs catalogue, pas une facture. Coût total du test : environ 18,1 $ d'équivalent API (4,80 $ pour le volet 1, 13,32 $ pour le volet 2), sous le budget de 20 $.

## 1. Résultat en bref

- **Volet 1 (détection sur défauts semés) : critère de la veille atteint.** Sur 25 défauts d'interface que pytest ne voit pas (vérifié, un par version), le sous-agent en détecte **22, soit 88 %** (IC de Wilson à 95 % : 70 % à 96 %). Faux positifs sur les versions témoins : **0 sur 8 exécutions** (4 versions sans défaut, 2 exécutions chacune). Coût par vérification : **0,141 $** en moyenne (de 0,067 à 0,299 $), 60 s, 23 appels d'outil. pytest : 0 sur 25 par construction. axe-core 4.13 sur les mêmes pages (1280 et 390 px) : **0 sur 26** (aucune règle nouvelle par rapport à la version témoin de la story).
- **Trois défauts manqués**, tous de même nature : le sous-agent a contrôlé l'attribut DOM ou la mesure `scrollWidth` au lieu de regarder le rendu (motif de blocage masqué mais lié par `aria-describedby`, cartes côte à côte à 390 px sans débordement), ou n'a pas enchaîné les étapes dans l'ordre qui révèle le défaut (pastille de mode non relue, visible seulement avant un lancement raté).
- **Volet 2 (boucle de développement) : aucun gain mesurable.** Sur 4 cellules Sonnet (2 stories, 2 répétitions) et 2 cellules Haiku exploratoires, l'agent de développement tient déjà **6 critères sur 6** du parcours scripté avant toute vérification, et après la passe de correction (bras B = bras A, sur les 6 cellules). Les tests cachés ne bougent pas non plus. Le plafond est atteint : il n'y avait rien à corriger au sens de la spec. Le sous-agent a signalé des écarts dans 2 cellules sur 6 ; ils portaient sur des attentes de ma fiche (lien de détail par ligne, lien de retour) que la spec donnée au développeur n'exigeait pas.
- **Coût de la boucle** : vérificateur 0,10 à 0,15 $ ; mais la passe de correction renvoyée à la même session coûte 0,61 à 1,57 $ **même quand le rapport est entièrement PASS** (la reprise de session relit tout le contexte du développement). Bras B mesuré : 1,35 à 3,09 $ contre 0,59 à 1,39 $ pour le bras A. Sans correction à vide, B ne coûte que 0,10 à 0,15 $ de plus que A (9 à 13 % du coût du développement en Sonnet).
- **Décision selon le critère (rappel ≥ 60 %, au plus 1 faux positif, moins de 0,30 $) : intégrer** le sous-agent de vérification à la chaîne des stories front, après `dev-story` et avant `second-avis`, avec trois réserves (section 8) : la fiche de vérification est la spec de `dev-story` (pas une paraphrase), la correction n'est lancée que s'il y a au moins un FAIL, et le gain attendu par story est un filet de sécurité, pas une amélioration mesurée du développement.

## 2. Protocole

### Matériau
- Dépôt public `usine-migration-jira-demo` (interface FastAPI servant des pages HTML statiques et des vues JSON, JS vanilla ; il n'y a pas de Jinja dans ce dépôt). Quatre stories de l'interface web, **au commit fusionné après la revue** : 7.13 (socle et cadre commun, `bc8ab21`), 7.14 (carte météo, détail d'une Entité, livrables, `23c1fd3`), 7.15 (lancement de la Chaîne, bouton de mode, `c86b2f7`), 7.16 (Agent, Avant / après, Pseudonymisation, Outillage, `cf54141`). Le choix de 7.13 à 7.16 plutôt que 0.8 : 0.8 est l'UI Streamlit minimale, sans critères observables dans un navigateur de la même façon.
- Chaque story est extraite par `git archive` dans un dossier jetable (sans historique, sans `.claude/`, sans `_bmad-output/` dont les chemins trop longs bloquent git sous Windows), `uv sync --frozen`. Aucun worktree n'a été créé dans le dépôt d'origine, qui est resté intact (`git status` vide, `git worktree prune` passé).
- Application lancée par la commande du dépôt : `uv run usine ui --port 8765`, en Mode repli (`USINE_MODE_REPLI=1`, Passage fictif enregistré, aucun LLM ni Jira) pour 7.13, 7.14, 7.16, en Mode réel pour 7.15 (dont le lancement de la Chaîne échoue vite, faute de données de Journal : c'est le cas d'échec de la story). `USINE_CLE_PSEUDO` posée à une valeur de test pour l'écran Pseudonymisation.
- Navigateur : Chromium 1248 de Playwright, headless, via `@playwright/mcp` 0.0.83 (`--headless --isolated`, même configuration et même installation que T7). Liste d'autorisations : `Read` et `mcp__playwright` (tout le serveur), rien d'autre ; `--strict-mcp-config`, `--permission-prompts none`.
- Sous-agent de vérification : `claude -p --model claude-sonnet-5-5 --effort medium`, `--setting-sources project,local`, `claudeMdExcludes` du CLAUDE.md utilisateur, répertoire de travail vide (pas d'accès au code source). Il reçoit une **fiche** (`fiches/s713.md` à `s716.md`) : la story (énoncé et critères d'acceptation extraits d'`epics.md`, extraits du contrat d'intention) et une liste de critères C1 à C6 à parcourir, plus trois contrôles transverses communs T1 (navigation au clavier), T2 (mise en page à 390 px, `browser_resize`) et T3 (aucun message d'erreur vide, aucun lien mort). Il rend un JSON avec un verdict PASS, FAIL ou NA par critère et une preuve.
- Charge locale : un seul serveur d'application et un seul navigateur à la fois, au plus une session `claude -p` en vérification (jamais deux en même temps), ni Ollama ni GPU. La machine exécutait d'autres séries : les durées sont gonflées.

### Volet 1 : défauts semés
- **29 mutations candidates** écrites par moi (`scripts/defauts.json`), chacune dans UNE version : message de confirmation absent ou faux, bouton ou filtre inactif, état perdu après rechargement, erreur sans texte, lien mort, mauvais lien, clavier cassé, mise en page cassée à 390 px, donnée fausse. Presque toutes touchent le JS, le CSS ou le HTML statique, que les tests pytest de ce dépôt ne rendent pas dans un navigateur.
- **Vérification que pytest passe avec le défaut** (`scripts/pytest_defauts.py`, `pytest -q tests/unit/ui`, 264 à 371 tests selon la story) : 26 mutations passent. **Trois ont été attrapées par pytest** (des tests lisent les fichiers statiques) : `d02` initial (ancre du lien d'évitement inexistante : 7 tests échouent) et `d13` initial (`tabindex` retiré : 1 test), remplacés par des variantes que pytest ne voit pas, et `e11` (la fiche d'outillage insérée en texte : 1 test), **gardé dans la table mais exclu du dénominateur principal**. Dénominateur principal : **25 défauts invisibles à pytest**.
- **Défaut réellement visible dans un navigateur ?** Un oracle scripté Playwright (`scripts/verite.py`, écrit par moi depuis les critères, rejoué à la fin sur les 26 versions défectueuses et les 4 témoins) échoue sur la cible de chacun des 26 défauts et passe sur les 4 témoins. Un défaut dont l'effet visible n'était pas confirmé par l'oracle aurait été écarté.
- **Témoins** : une version sans défaut par story (4), chacune vérifiée 2 fois : 8 exécutions.
- **Exécutions** : une seule par version défectueuse (26), 34 exécutions du sous-agent au total. Détection = FAIL du sous-agent sur un critère ou un contrôle transverse cible du défaut (déclaré avant les runs dans `defauts.json`, champ `cibles`), la preuve étant relue pour vérifier que le symptôme décrit est le bon.
- **Comparaisons** : pytest seul (0 par construction), axe-core 4.13 (même moteur et même injection que T7, pages de la story à 1280 et 390 px, nombre de règles en violation comparé à la version témoin de la story).
- Le serveur d'application est démarré et arrêté par le banc, pas par le sous-agent (voir les limites).

### Volet 2 : boucle de développement
- Banc de rejeu de T3 (`banc-rejeu/banc.py`, importé tel quel) : dossier jetable à la base de la story (parent du commit de la story), spec et interface attendue, CLAUDE.md minimal de T3, réglages isolés, tests cachés retirés puis rejoués, mêmes outils et autorisations que T3. Développement par `claude -p` Sonnet 5.5, effort `medium` (`dev-story` simulé comme en T3).
- Stories rejouées : **7.15** (base `48fd534`, 27 tests cachés) et **7.14** (base `9e4639c`, 33 tests cachés ; le port `Consultation.livrable` déjà fait à la base, comme les contrats de 6.4 et 7.8 en T3). 7.16 (quatre écrans, dont l'Agent) et 7.13 n'ont pas été rejouées, faute de budget.
- **Conception appariée** (écart au brief, qui demandait deux développements indépendants par cellule) : une répétition = UN développement, évalué tel quel (**bras A**) ; puis le sous-agent de vérification parcourt cet arbre, son rapport (les critères qui ne sont pas PASS, avec preuves) est renvoyé à la MÊME session par `--resume`, une seule passe de correction, et l'arbre corrigé est évalué (**bras B**). B contient A. Cela divise par deux le coût du développement, supprime la variance entre deux développements et rend la comparaison directe, mais le coût du bras B inclut la reprise de session.
- **Vérité** : (1) oracle scripté par rôle et par texte de la spec (6 contrôles par story : `s715` ou `s714x` dans `verite.py`), écrit puis figé avant les runs du volet 2 (sha256 de `verite.py` en fin de fichier) et **non montré aux agents** ; (2) tests cachés de la story.
- 2 répétitions par cellule pour Sonnet (7.15 et 7.14). Ajout non demandé : **2 cellules exploratoires avec un développeur Haiku 5.5** (7.15 et 7.14, 1 répétition), pour voir la boucle sur des sorties moins parfaites.

## 3. Volet 1 : défauts semés et leur détection

| Id | Story | Classe | Défaut semé | pytest | Oracle scripté | Sous-agent | FAIL de l'agent | Coût ($) |
|---|---|---|---|---|---|---|---|---|
| d01 | 7.13 | message absent | Le bandeau de repli n'est plus posé par le cadre en Mode repli. | passe | KO C3 | détecté | C3 | 0.088 |
| d02 | 7.13 | navigation clavier cassée | Le lien d'évitement reste hors écran quand il reçoit le focus (le style :focus ne le ramène plus à l'écran). | passe | KO C4 | détecté | C4,T1 | 0.104 |
| d03 | 7.13 | mise en page 390 px | Le point de rupture mobile passe de 767 px à 300 px : la grille à deux colonnes reste à 390 px. | passe | KO T2,T2 | détecté | T2 | 0.067 |
| d04 | 7.14 | bouton inactif | Le filtre météo ne réagit plus au changement de valeur (écouteur retiré). | passe | KO C2 | détecté | C2,T2 | 0.156 |
| d05 | 7.14 | lien mort | Le lien de téléchargement d'un livrable pointe vers /livrable/ (404) au lieu de /livrables/. | passe | KO C3 | détecté | C3,T3 | 0.140 |
| d06 | 7.14 | erreur sans texte | Le message « Entité {entite} absente du Passage affiché. » est vide (le lien vers la carte reste). | passe | KO C5 | détecté | C5,T3 | 0.142 |
| d07 | 7.14 | message faux | L'annonce du filtre affiche le gabarit « {n} Entités affichées » sans remplacer {n}. | passe | KO C2 | détecté | C2 | 0.105 |
| d08 | 7.15 | message absent | Le bandeau d'échec (étape, code, lignes d'erreur) n'est plus affiché. | passe | KO C2,C3 | détecté | C2,C3 | 0.167 |
| d09 | 7.15 | état non rafraîchi | Après la bascule de mode, la pastille de mode de l'en-tête n'est pas relue (elle reste fausse jusqu'au rechargement). | passe | KO C2,C3,C4,C5 | manqué | T2 | 0.142 |
| d10 | 7.15 | état perdu après rechargement | Le bandeau de résultat de la Chaîne n'est affiché que dans la page qui a lancé la Chaîne : il disparaît au rechargement. | passe | KO C3 | détecté | C3 | 0.151 |
| d11 | 7.15 | bouton inactif (marquage) | Les boutons bloqués ne portent plus aria-disabled=true : ils paraissent actifs alors que le serveur refuse. | passe | KO C5 | détecté | C5,T2 | 0.133 |
| d12 | 7.16 | message absent | La mention de rejeu (agent.mention_repli) n'est plus affichée sous la réponse enregistrée. | passe | KO C1 | détecté | C1 | 0.182 |
| d13 | 7.14 | navigation clavier cassée | Les liens de téléchargement des livrables sont exclus de l'ordre de tabulation (tabindex=-1) : inaccessibles au clavier. | passe | KO C3b | détecté | T1 | 0.146 |
| d14 | 7.16 | bouton inactif | Le segment de période ne change plus les cartes au clic. | passe | KO C2 | détecté | C2 | 0.172 |
| d15 | 7.16 | mise en page 390 px | Les cartes jumelles (avant/après, pseudonymisation) restent côte à côte à 390 px (rupture à 300 px). | passe | KO T2 | manqué | - | 0.163 |
| d16 | 7.16 | lien mort | Le formulaire de sélection du ticket envoie vers /pseudonymisations (404). | passe | KO C3 | détecté | C3,T3 | 0.299 |
| e01 | 7.13 | donnée fausse | La pastille de mode affiche toujours « Mode réel », même en Mode repli. | passe | KO C3 | détecté | C3 | 0.071 |
| e02 | 7.13 | message absent | La pastille « Passage publié » n'est jamais affichée. | passe | KO C2 | détecté | C2 | 0.072 |
| e04 | 7.14 | donnée fausse | Le chiffre de chaque tuile de comptage est augmenté de 1 (incohérent avec les lignes du tableau). | passe | KO C1b | détecté | C1 | 0.148 |
| e05 | 7.14 | lien mort / mauvais lien | Le lien « Détail » de chaque ligne mène toujours à ENT-A. | passe | KO C4b | détecté | C1,C4,T3 | 0.128 |
| e06 | 7.14 | état perdu | Revenir à l'option « Toutes » du filtre n'affiche plus aucune ligne. | passe | KO C2,C4b | détecté | C1,C2,T2 | 0.135 |
| e07 | 7.15 | libellé non mis à jour | Le libellé du bouton de mode ne change plus après la bascule (reste « Passer en Mode repli »). | passe | KO C2,C3,C4,C5 | détecté | C4,T2 | 0.147 |
| e08 | 7.15 | message absent | Le motif du blocage du bouton de lancement n'est plus visible (reste lié par aria-describedby). | passe | KO C5 | manqué | - | 0.140 |
| e09 | 7.16 | donnée fausse | Les outils appelés ne sont jamais listés dans la réponse rejouée (affiche « aucun »). | passe | KO C1b | détecté | C1 | 0.167 |
| e10 | 7.16 | message absent | Le tableau des périodes de l'écran Avant / après n'est plus affiché. | passe | KO C2b | détecté | C2 | 0.187 |
| e11 | 7.16 | mise en page cassée | La fiche d'outillage affiche son HTML en texte brut (balises visibles). | échoue | KO C4 | détecté | C4 | 0.163 |

Lecture : « KO » liste les contrôles de l'oracle scripté qui échouent (préfixe = critère de la fiche) ; la cascade d'un état (d09, e07 : un contrôle échoué laisse le serveur dans un autre état) explique les KO multiples. « FAIL de l'agent » liste tous les FAIL du sous-agent.

### Synthèse
| | Résultat |
|---|---|
| Défauts invisibles à pytest, détectés par le sous-agent | **22 / 25 = 88 %** (Wilson 95 % : 70 % à 96 %) |
| Avec `e11` (visible par pytest) | 23 / 26 = 88,5 % (71 % à 96 %) |
| pytest | 0 / 25 par construction (3 mutations candidates sur 29 étaient vues par pytest) |
| axe-core 4.13 (1280 et 390 px) | 0 / 26 (aucune règle nouvelle ; ligne de base : `landmark-unique` sur 7.14 et 7.16, rien sur 7.13 et 7.15) |
| Oracle scripté (par construction : défauts retenus s'ils le font échouer) | 26 / 26 |
| Faux positifs sur les témoins | **0 / 8 exécutions** (IC de Wilson 95 % de la proportion : 0 % à 32 %) |
| FAIL non ciblés sur versions défectueuses | 11 versions sur 26 : 7 sont le même symptôme (par exemple T3 « lien mort » sur d05) ; **5 sont indépendants et tous du contrôle T2** (tableau jugé coupé à 390 px, libellé d'étape qui touche sa pastille, sur 7.14 et 7.15 ; les témoins correspondants avaient reçu PASS avec la même remarque) |
| Coût par vérification | moyenne **0,141 $**, médiane 0,144 $, min 0,067 $, max 0,299 $ ; témoins 0,135 $, défauts 0,143 $ ; total 4,80 $ (34 exécutions) |
| Durée | moyenne 60 s (médiane 59 s, de 25 à 185 s) |
| Activité | 24,3 tours et 23,3 appels d'outil en moyenne ; jetons : 17 k de création de cache, 290 k de lecture de cache, 4,4 k de sortie |

Détection par story : 7.13 5/5, 7.14 8/8, 7.15 4/6, 7.16 5/6. Par classe : bouton ou filtre inactif 3/3 ; lien mort ou mauvais lien 3/3 ; donnée fausse 3/3 ; message absent 5/6 ; clavier cassé 2/2 ; erreur sans texte 1/1 ; message faux 1/1 ; libellé non mis à jour 1/1 ; état perdu après rechargement ou filtre 2/2 ; mise en page à 390 px 1/2 ; état non rafraîchi 0/1.

Les 3 défauts manqués :
- **d09** (pastille de mode non relue après la bascule) : le défaut n'existe que si on bascule avant tout lancement ; la fiche place la bascule après le lancement raté (C4 après C2), et après un échec la page relit le cadre par un autre chemin. L'oracle réordonné (bascule d'abord) le voit, le sous-agent n'a pas suivi cet ordre.
- **d15** (deux colonnes à 390 px sur Avant / après et Pseudonymisation) : le sous-agent a mesuré `scrollWidth` (390, donc « pas de débordement ») et n'a pas relu les captures de ces deux écrans (il l'écrit).
- **e08** (motif du blocage masqué par l'attribut `hidden`) : le sous-agent a vu `aria-disabled="true"` et `aria-describedby` pointer vers un élément qui contenait le texte, sans contrôler qu'il était visible.

Comportement du sous-agent : il écrit beaucoup de JavaScript au lieu de cliquer (243 `browser_evaluate` et 37 `browser_run_code_unsafe` sur 34 exécutions, contre 64 clics et 63 snapshots) ; il vérifie donc bien les états du DOM et les réponses HTTP (`fetch`), et moins bien le rendu visuel. C'est cohérent avec les trois manques.

## 4. Volet 2 : boucle de développement

| Cellule | Dév. | Dév. : coût A ($) | durée (min) | tours | Critères tenus A | Tests cachés A | Vérificateur ($) | Correction ($) | Critères tenus B | Tests cachés B | Coût B mesuré ($) | Coût B sans correction à vide ($) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v715-r1 | sonnet-5-5 | 1.00 | 11.8 | 48 | 6/6 | 15/27 | 0.13 | 1.02 | 6/6 | 15/27 | 2.15 | 1.13 |
| v714-r1 | sonnet-5-5 | 1.17 | 17.4 | 60 | 6/6 | 18/33 | 0.12 | 1.19 | 6/6 | 18/33 | 2.48 | 1.29 |
| v715-r2 | sonnet-5-5 | 1.30 | 17.0 | 69 | 6/6 | 3/27 | 0.13 | 1.32 | 6/6 | 3/27 | 2.76 | 1.43 |
| v714-r2 | sonnet-5-5 | 1.39 | 17.6 | 77 | 6/6 | 17/33 | 0.13 | 1.57 | 6/6 | 17/33 | 3.09 | 1.52 |
| v715-r1-h | haiku-5-5 | 0.59 | 22.1 | 77 | 6/6 | 8/27 | 0.15 | 0.61 | 6/6 | 8/27 | 1.35 | 0.74 |
| v714-r1-h | haiku-5-5 | 0.63 | 19.2 | 79 | 6/6 | 4/33 | 0.10 | 0.76 | 6/6 | 4/33 | 1.49 | 0.73 |

« Critères tenus » = les 6 contrôles de l'oracle scripté (par rôle et par texte). « Coût B mesuré » = développement + vérificateur + correction par reprise de session. « Coût B sans correction à vide » = développement + vérificateur seulement (la correction n'a rien à faire quand le rapport est entièrement PASS).

Lecture :
- **Critères tenus : 6/6 en A comme en B dans les 6 cellules.** Il n'y a pas de marge : même Haiku 5.5, sans aide, livre une interface qui passe les 6 contrôles. Le volet ne peut donc pas montrer d'amélioration de B sur A ; il montre que, sur ces deux stories bien cadrées, la spec suffit à Sonnet (et à Haiku) pour tenir les critères visibles dans un navigateur.
- **Tests cachés : identiques en A et en B** (15/27, 18/33, 3/27, 17/33 en Sonnet ; 8/27 et 4/33 en Haiku). Ils mesurent surtout la proximité avec l'API interne de référence (noms et signatures que la spec ne donne pas), pas le comportement visible : la répétition 2 de 7.15 a 3/27 avec 6/6 critères tenus. Ils ne départagent rien ici.
- **Ce que le sous-agent a dit sur les 6 développements** : 4 rapports entièrement PASS (les mêmes 6 sur 6 que l'oracle). Deux rapports avec des FAIL :
  - 7.14, répétition 2 (Sonnet) : C4 FAIL parce que la page de détail n'a pas de lien de retour vers la carte. La spec donnée au développeur n'exige ce lien que pour l'Entité absente ; c'est ma fiche qui l'avait ajouté (il existe dans l'implémentation d'origine). La session de correction l'a refusé (« la spec ne le demande pas ») et n'a ajouté qu'un test.
  - 7.14, Haiku : C1 FAIL (aucun lien de détail par ligne de la carte), C4 FAIL (pas de lien de retour), C3 FAIL (cas « livrable absent » non observable, que le vérificateur compte FAIL au lieu de NA), T2 FAIL (colonnes écrasées à 390 px), T3 FAIL (conséquence du lien manquant). La correction a ajouté le lien de détail par ligne et réparé la mise en page à 390 px. **Sans écart à la spec stricte** (la spec ne parle pas de ce lien), mais c'est la seule cellule où la boucle a produit une modification utile pour un utilisateur, et mon oracle gelé ne la mesure pas (il compte les lignes, pas les liens de détail : lacune de ma vérité, qui sous-estime B).
- **Enseignement sur la fiche** : le vérificateur doit recevoir exactement la spec de `dev-story`. Quand je lui ai donné une fiche plus riche que la spec du développeur (éléments décrits d'après l'implémentation d'origine), 2 cellules sur 6 ont produit des FAIL « hors spec ». Dans le volet 1, la même fiche décrivait l'application d'origine, donc elle était cohérente.
- **Coût** : A vaut 0,59 à 1,39 $ (12 à 22 min par développement sur la machine chargée) ; le vérificateur 0,10 à 0,15 $ ; la correction par reprise de session 0,61 à 1,57 $ dans 6 cellules sur 6, y compris quand elle n'a rien fait (1 tour, « il n'y a rien à corriger »). La reprise paie la relecture de tout le contexte du développement (cache expiré après plusieurs minutes), soit autant ou plus que le développement lui-même dans les 6 cellules. Une correction par **nouvel appel avec le rapport et la spec** ne ferait pas mieux sans un contexte de dev conservé ; la règle économique est de ne la lancer que s'il y a au moins un FAIL.

## 5. Coûts

| Poste | Montant |
|---|---|
| Volet 1 : 34 exécutions du sous-agent de vérification | 4,80 $ (0,141 $ en moyenne) |
| Volet 2 : 6 développements (4 Sonnet, 2 Haiku) | 6,08 $ (Sonnet 4,86 $ ; Haiku 1,22 $) |
| Volet 2 : 6 vérifications | 0,76 $ |
| Volet 2 : 6 corrections par reprise de session | 6,47 $ |
| **Total** | **≈ 18,1 $** (budget : 20 $) |

Les oracles, axe-core et pytest ne coûtent aucun jeton (environ 45 s d'oracle par version, 1 à 2 minutes de pytest sur ce dépôt). L'orchestration de cette session n'est pas comptée.

Rapport au critère de la veille : **0,141 $ par vérification en moyenne** (maximum 0,299 $ pour `d16`, juste sous le seuil) contre le seuil de 0,30 $ par story. Si on compte la vérification sur 6 critères et 3 contrôles pour une story, c'est 9 à 13 % du coût du développement Sonnet de ces stories.

## 6. Limites

- **Défauts écrits par moi, avec la fiche sous les yeux.** 25 des 26 défauts touchent une fonction que la fiche cite explicitement dans un critère ; seul `e04` (tuiles incohérentes avec le tableau) n'est dans aucun critère et il a été trouvé. Les trois contrôles transverses (clavier, 390 px, lien mort ou message vide) énumèrent les classes de défauts semés : dans une chaîne réelle, ces contrôles seraient une liste permanente, mais cela oriente le sous-agent. Le rappel de 88 % est donc un majorant pour des défauts d'origine naturelle.
- **Mutations d'une ligne** dans du JS, CSS ou HTML statique. Les vraies erreurs d'un agent de développement sont plus tordues (logique, enchaînements, cas limites). Et dans le volet 2, l'agent n'a produit aucun écart à la spec sur 6 développements : on ne mesure pas le rappel sur des défauts naturels, parce qu'il n'y en a pas eu.
- **Une exécution du sous-agent par version défectueuse** (deux par témoin). La variance d'un même défaut d'une exécution à l'autre n'est pas mesurée : un défaut détecté une fois peut être manqué la fois suivante (et inversement).
- **Le serveur est démarré par le banc**, pas par le sous-agent (le brief demandait qu'il démarre l'application avec la commande du dépôt). Je l'ai fait pour limiter les risques (processus en arrière-plan dans `claude -p`, arrêt propre, une seule instance). Le coût de la vérification ne comprend donc pas l'écriture de cette commande ni son attente (quelques appels d'outil de plus).
- **Mode repli**, jeu de données fictif de 10 Entités : deux critères (livrable absent, singulier du filtre) ne sont pas observables et sont NA ou FAIL selon la fiche. Le critère « Palier 2 avec `?palier=1` » n'a pas été retenu : le Passage de repli est de Palier 1.
- **Petite application, écrans connus** (7.13 à 7.16, 10 Entités, 4 à 9 critères par story). La vérification d'une grosse story ou d'un écran dense coûtera plus.
- **Volet 2 réduit** : 2 stories sur 3 à 4 demandées, 2 répétitions en Sonnet (pas de répétition supplémentaire faute de budget), conception appariée (B = A + vérification + correction) au lieu de deux développements séparés, tests cachés peu discriminants, oracle de vérité sans contrôle du lien de détail par ligne de la carte (lacune relevée a posteriori). Les 2 cellules Haiku sont un ajout exploratoire de n = 1 par story.
- **Les durées** (60 s par vérification, 8 à 22 min par développement) viennent d'une machine qui exécutait d'autres séries ; elles ne se transposent pas.
- **Vérité et vérificateur partagent mon interprétation des critères.** Les deux ont été écrits par moi depuis les mêmes énoncés : leur accord ne prouve pas que l'application soit correcte pour un utilisateur, seulement qu'elle tient ces critères.
- `d02` et `d13` ont été corrigés après un premier tour (pytest les voyait). Le sous-agent n'a jamais tourné sur le `d02` initial ; il a tourné sur le `d13` initial (tabindex retiré sur la page Pseudonymisation), dont l'exécution est conservée dans `donnees/verif/` sous l'identifiant `d13old` et exclue de tous les chiffres. L'oracle scripté a été étendu (contrôles `C1b`, `C2b`, `C3b`, `C4b`, motif visible de `C5`) **après** les 34 exécutions du volet 1, pour confirmer la visibilité de défauts que l'ancienne version ne testait pas ; l'oracle du volet 2 (`s715`, `s714x`) a été figé avant les 6 cellules.
- Un effet de bord à signaler : `claude -p` avec Playwright MCP écrit des captures dans le dossier de sortie du serveur MCP (dans le scratchpad) ; supprimées avec les dossiers de travail.

## 7. Fichiers

- `fiches/` : fiches données au sous-agent. `corpus-v2/` : spec, tests cachés et interface du volet 2.
- `scripts/` : `commun.py`, `preparer_stories.py`, `defauts.json` (les 26 défauts et leurs cibles), `semer.py`, `pytest_defauts.py`, `verifier.py` (volet 1), `verite.py` et `verite_run.py` (oracle scripté et axe-core), `rejouer_oracle.py`, `v2_corpus.py`, `v2.py` (volet 2), `agreger.py`, `agreger_v2.py`, `stats_volet1.py`, `tableau_volet1.py`, `compacter.py`.
- `donnees/` : `verif_runs.jsonl` et `verif/<exécution>/flux.jsonl` (flux bruts, images retirées, chemins anonymisés), `oracle_final.jsonl`, `pytest_defauts_lot*.jsonl`, `volet1_resume.json`, `volet1_tableau.md`, `v2_runs.jsonl`, `v2/brut/` (sorties `claude -p` du volet 2), journaux `*.log`.
- Reproduire (depuis `scripts/`, un seul processus à la fois, `T12_STORIES=storiesv` pour l'arbre du vérificateur) : `preparer_stories.py`, puis `pytest_defauts.py`, `verifier.py d01 ... t716`, `rejouer_oracle.py`, `agreger.py`, puis `v2.py ref v715 v714` et `v2.py run v715 1`. Les chemins du scratchpad sont dans `commun.py`.

## 8. Décision

Critère de la veille : rappel ≥ 60 % avec au plus 1 faux positif sur les témoins, pour moins de 0,30 $ par story. Mesure : **88 % (70 à 96 %), 0 faux positif sur 8, 0,14 $ en moyenne**. Le critère est satisfait : **intégrer le sous-agent de vérification à la chaîne pour les stories front, après `dev-story` et avant `second-avis`.**

À fixer dans l'intégration, d'après ce que le test a montré :
1. **Même spec que `dev-story`.** Le vérificateur reçoit la spec et les critères d'acceptation de la story, pas une paraphrase plus riche. Il y ajoute des contrôles transverses permanents (clavier, 390 px, lien mort, message vide).
2. **Rendre visibles les attentes visuelles** : demander une capture par écran à 390 px et la relire, et contrôler la visibilité (pas seulement la présence dans le DOM) des motifs et des messages. C'est ce qui a manqué dans 2 des 3 défauts perdus.
3. **Correction conditionnelle** : ne relancer `dev-story` avec le rapport que s'il y a au moins un FAIL, et ne lui transmettre que les FAIL justifiés par la spec ; sinon on paie 0,6 à 1,6 $ pour rien (6 cellules sur 6). Pour un rapport entièrement PASS, la vérification coûte 0,10 à 0,15 $ et rien d'autre.
4. **Espérer peu de gain par story** : sur 6 développements du banc, l'agent tient déjà les critères visibles, et le sous-agent n'a rien trouvé qui soit hors de la spec ; sa valeur est un filet de sécurité (T7 : 1 défaut réel sur 16 pages ; ici : 22 sur 25 défauts semés), pas une amélioration mesurée du développement. À réévaluer sur les premières stories réelles de l'usine (mesurer combien de FAIL justifiés il relève par 10 stories).
5. **Claude in Chrome** reste la vérification manuelle (fenêtre visible, sessions ouvertes), pour les écrans que le sous-agent juge ambigus ; ce test n'a pas eu à y recourir.
6. Autoriser seulement `mcp__playwright` dans les sous-agents de vérification, et lancer l'application depuis l'orchestrateur (une instance, arrêt garanti).

Empreinte de l'oracle gelé pour le volet 2 : `verite.py` sha256 `636f2ab7133a1d86` (préfixe de 16 caractères, calculé à la fin ; seules les fonctions `s715` et `s714x` ont servi au volet 2).

## Synthèse en cinq lignes

1. Volet 1 : le sous-agent Sonnet + Playwright MCP détecte 22 défauts d'interface sur 25 que pytest ne voit pas (88 %, IC 70 à 96 %), avec 0 faux positif sur 8 exécutions de versions témoins ; pytest 0 sur 25 par construction, axe-core 0 sur 26.
2. Coût : 0,141 $ et 60 s par vérification (max 0,299 $), soit 9 à 13 % du coût du développement Sonnet ; les 3 défauts manqués relèvent de contrôles DOM sans relecture du rendu et d'un ordre d'enchaînement.
3. Volet 2 : aucun gain mesurable (6 critères sur 6 en A comme en B dans les 6 cellules, Sonnet et Haiku) ; la correction par reprise de session coûte 0,6 à 1,6 $ même à vide.
4. Décision : critère satisfait, intégrer la vérification navigateur après `dev-story` pour les stories front, avec la même spec que le développeur et une correction seulement s'il y a un FAIL.
5. Réserves : défauts semés par moi (optimistes), une exécution par défaut, serveur lancé par le banc, volet 2 réduit à 2 stories avec oracle sans contrôle du lien de détail ; budget consommé ≈ 18,1 $ sur 20 $.
