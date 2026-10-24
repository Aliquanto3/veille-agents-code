## Spec Change Log

### 2026-10-11 — Boucle 1 (bad_spec)

- **Déclencheur :** l'AC 1 de la story (« `USINE_CLE_PSEUDO` défini », jeton HMAC stable d'une exécution à l'autre) et la table E0 du spine (« Pseudonymisation par HMAC ») attendent une Pseudonymisation réelle. Or la spec ne prévoyait que `PseudonymiseurFactice` : aucun code de production ne lisait `USINE_CLE_PSEUDO`, et `donnees/pseudonymes.sqlite` n'existait pas.
- **Amendement :** ajout, dans *Tasks*, de `PseudonymiseurHmac` (adaptateur à motifs, sans Presidio), de `TablePseudonymesSqlite`, du branchement de la clé dans la composition, et d'un critère d'acceptation sur la stabilité du jeton. Les correctifs locaux de la passe sont intégrés à *Tasks* : citations hors codes d'indicateur et d'Entité, saut de ligne, aucun appel sans ticket en cause, délimitation des textes, `version_prompt` du gabarit envoyé, `version_modele` de la réponse, tests d'intégration.
- **État à éviter :** une passerelle « prête » dont la seule Pseudonymisation est une doublure de test ; des phrases retirées parce qu'elles citent `IND-1`.
- **KEEP :** tout le code de la passe 1 reste en place et doit être amendé, pas réécrit. On garde en particulier la passerelle et l'ordre AD-12, `CacheLLM` (`Protocol` local) et `CacheLLMSqlite`, `controler_citations` et ses tests, `expliquer` avec la régénération unique, `EtapeExplications`, `tickets_textes`, le branchement Palier 2 avec `UsineErreur` sans fournisseur, et les espions de `tests/unit/ia/espions.py`. Comme pour la Story 0.2, le code n'est pas ramené à la base, car l'opération destructive est refusée par le classifieur de permissions.

## Review Triage Log

### 2026-10-11 — Review pass
- verdicts: 36 findings — high 0, medium 5, low 27, false 4, maybe-false 0
- findings:
  - `[medium]` `[bad_spec]` (intention) `USINE_CLE_PSEUDO` jamais lu, pas de Pseudonymisation HMAC de production — `PseudonymiseurHmac`, `TablePseudonymesSqlite` et le branchement de la clé ajoutés à *Tasks*.
  - `[low]` `[bad_spec]` (intention) Stabilité du jeton prouvée dans un seul processus — critère d'acceptation sur deux instances et deux tables.
  - `[low]` `[bad_spec]` (intention) Ordre AD-12 jamais vérifié avec le vrai `controler_citations` — test à travers `expliquer`.
  - `[false]` `[reject]` (intention) AC 2 — aucune divergence relevée.
  - `[medium]` `[bad_spec]` (intention) Cache SQLite jamais relu par la passerelle — deux Passages Palier 2 successifs, `depuis_cache = true` dans `trace/llm.jsonl`.
  - `[low]` `[bad_spec]` (intention) Trace de la Chaîne sans numéro de compte — numéro fictif dans une description et vérification qu'il est absent de tout le Passage.
  - `[low]` `[reject]` (intention) Palier 2 impossible depuis la CLI — aucun fournisseur réel avant la lane L6 ; l'erreur est explicite.
  - `[false]` `[reject]` (intention) Ajouts hors « Écrit dans » (`tickets_textes`, paramètres de composition, `Protocol` local) — exigés par la tâche (textes des tickets) et par les couches (cache injecté).
  - `[low]` `[bad_spec]` (verification-gap) Prompt de `EtapeExplications` non vérifié — test ajouté à *Tasks*.
  - `[low]` `[bad_spec]` (verification-gap) Transmission par `lancer_rapport` non testée — test Palier 2 via `lancer_rapport`.
  - `[low]` `[bad_spec]` (verification-gap) `version_grille` et `version_prompt` des traces non vérifiées — assertions dans le test à deux Passages.
  - `[medium]` `[bad_spec]` (blind) `IND-1`, `UTF-8`… pris pour des clés de ticket — codes d'indicateur et d'Entité exclus des citations.
  - `[medium]` `[bad_spec]` (blind) Lignes sans ponctuation fusionnées — le saut de ligne termine une phrase.
  - `[low]` `[bad_spec]` (blind) Deux appels pour un échec certain sans ticket en cause — repli direct.
  - `[false]` `[reject]` (blind) Une erreur du fournisseur fait échouer l'étape — voulu par AD-12 (« un fournisseur injoignable au démarrage d'une étape LLM fait échouer l'étape, donc le Passage »).
  - `[low]` `[bad_spec]` (blind) Trace avec le modèle configuré et non celui qui a répondu — `version_modele` de la réponse dans la trace.
  - `[low]` `[reject]` (blind) Clé de cache sans `max_jetons_sortie` ni schéma — composition de la clé fixée par AD-12 ; un changement de prompt change `version_prompt`.
  - `[low]` `[reject]` (blind) Réponses rejetées gardées en cache — un changement de prompt ou de modèle invalide la clé ; purge hors périmètre E0.
  - `[medium]` `[bad_spec]` (blind) Pseudonymisation et cache jamais éprouvés de bout en bout — même amendement que la ligne d'intention.
  - `[low]` `[bad_spec]` (blind) `test_ordre_impose` fusionne toutes les répétitions — seules celles de `reidentifier` sont fusionnées.
  - `[low]` `[reject]` (blind) Textes des tickets en clair dans tout Passage — `tickets_textes.parquet` est un fichier de Passage prévu (AD-23), local et fictif.
  - `[low]` `[bad_spec]` (blind) Textes des tickets non délimités dans le prompt — délimiteurs et consigne ajoutés.
  - `[low]` `[bad_spec]` (blind) Consigne sur les jetons en double négation — reformulée.
  - `[low]` `[bad_spec]` (blind) `version_prompt` et gabarit lus séparément — calcul depuis les octets envoyés.
  - `[low]` `[reject]` (blind) `tickets_textes` duplique `_etats_en` — factorisation sans effet observable.
  - `[low]` `[bad_spec]` (edge) `IND-1` cité → phrase retirée — même amendement.
  - `[low]` `[bad_spec]` (edge) Code d'Entité `ENT-12` pris pour une clé — même amendement.
  - `[low]` `[bad_spec]` (edge) Puces sans ponctuation — même amendement.
  - `[low]` `[reject]` (edge) Abréviations (`p. ex.`) découpées — compte légèrement les phrases retirées ; le prompt demande des phrases simples.
  - `[low]` `[bad_spec]` (edge) Aucun ticket en cause → deux appels — même amendement.
  - `[false]` `[reject]` (edge) Erreur du fournisseur fatale au Passage — voulu par AD-12.
  - `[low]` `[reject]` (edge) Échec du cache SQLite fatal — erreur nommant le fichier ; dégrader masquerait une panne disque.
  - `[low]` `[reject]` (edge) `ValidationError` sur la sortie ré-identifiée — la ré-identification ne remplace que des jetons connus par leur valeur ; aucun chemin ne la rend invalide.
  - `[low]` `[reject]` (edge) Prompt non borné pour des centaines de tickets — 2 Entités en E0 ; plafond de coût en L6.
  - `[low]` `[bad_spec]` (edge) `version_prompt` découplée du gabarit — même amendement.
  - `[low]` `[reject]` (edge) Palier 2 sans bouchons depuis la CLI — même raison que la ligne d'intention.

### 2026-10-11 — Review pass (boucle 1)
- verdicts: 34 findings — high 0, medium 7, low 26, false 1, maybe-false 0
- findings:
  - `[low]` `[patch]` (verification-gap) Branche `config/pseudonymisation.yaml` jamais exécutée — test de composition à deux reconnaisseurs `COMPTE`, valeurs absentes des entrées du fournisseur.
  - `[medium]` `[patch]` (verification-gap) `reconnaisseurs` vide → Pseudonymisation désactivée en silence — `UsineErreur` qui nomme le fichier, avant tout Passage.
  - `[low]` `[reject]` (intention) Ordre AD-12 vérifié avec des doublures et un cache mémoire — l'ordre est propre à la passerelle ; les adaptateurs réels sont éprouvés séparément et de bout en bout.
  - `[low]` `[reject]` (intention) Stabilité « d'une exécution à l'autre » éprouvée dans un seul processus — deux instances et deux tables distinctes ; le HMAC ne dépend que de la clé et de la valeur.
  - `[low]` `[reject]` (intention) Retrait de phrase jamais exercé par la Chaîne — couvert au niveau de `SortieExplication`, la surface nommée par l'AC 2.
  - `[low]` `[reject]` (intention) Les trois clauses de l'AC 3 sont réparties entre plusieurs tests — chacune est vérifiée sur la surface qui la porte, la relecture du fichier SQLite comprise.
  - `[low]` `[reject]` (intention) `version_modele` non vérifiée de bout en bout — vérifiée en unitaire, sur la réponse et sur le cache.
  - `[false]` `[reject]` (intention) Changements sans contrepartie dans l'intention — exigés par la tâche et par les couches (voir passe 1).
  - `[medium]` `[patch]` (blind) `UTF-8`, `SHA-256` comptés comme citations — une citation exige le préfixe de projet d'un ticket autorisé.
  - `[low]` `[patch]` (blind) Exclusion `ENT-` codée en dur — remplacée par la règle du préfixe de projet.
  - `[low]` `[patch]` (blind) Succès en cache tracé avec le modèle configuré — enveloppe de cache `{brut, version_modele}`.
  - `[medium]` `[patch]` (blind) `pseudonymisation.yaml` vide → aucun motif — même correctif.
  - `[low]` `[reject]` (blind) `MOTIFS_PAR_DEFAUT` ne couvre pas toutes les graphies d'IBAN — motif de démonstration ; la lane L6 apporte Presidio et `config/pseudonymisation.yaml`.
  - `[low]` `[patch]` (blind) `brouillon_commentaire` publié sans contrôle — phrases citant un ticket non autorisé retirées.
  - `[low]` `[reject]` (blind) Régénération avec le même prompt — `tentative` change la clé ; réglage des prompts en L6.
  - `[low]` `[reject]` (blind) Collision de jetons sur 24 bits fatale — longueur fixée par AD-15 ; l'erreur nomme le jeton.
  - `[low]` `[patch]` (blind) Types de jeton non validés par le constructeur — `UsineErreur`, testée.
  - `[low]` `[patch]` (blind) Chemin du fichier de configuration non testé — même correctif que la ligne verification-gap.
  - `[low]` `[reject]` (blind) Contradictions internes de la spec — le correctif serait une édition de la spec.
  - `[low]` `[patch]` (blind) Nom de test devenu faux — renommé ; cas limites de `tickets_textes` rejetés (même logique que `_etats_en`, déjà testée).
  - `[low]` `[reject]` (blind) Répertoires temporaires de la fabrique — nettoyage `atexit` ; données fictives.
  - `[medium]` `[patch]` (edge) Correspondance qui chevauche une clé de ticket passée en clair — seule une correspondance entièrement incluse dans une clé est ignorée.
  - `[medium]` `[patch]` (edge) Motif court qui bloque un motif long — regroupement des chevauchements, remplacement du groupe entier.
  - `[low]` `[reject]` (edge) Collision HMAC — même raison que la ligne blind.
  - `[medium]` `[patch]` (edge) `reconnaisseurs` vide — même correctif.
  - `[low]` `[patch]` (edge) `USINE_CLE_PSEUDO` fait de blancs — refusée.
  - `[low]` `[reject]` (edge) Fournisseur injecté et ignoré en Palier 1 — le Palier se lit dans `config/chaine.yaml` seulement (AD-8).
  - `[low]` `[reject]` (edge) `brut` au format du fournisseur et non du schéma — contrat de `ReponseStructuree` ; vérifié par la suite de contrat des adaptateurs de L6.
  - `[low]` `[reject]` (edge) `version_modele` sans `:` — forme garantie par `contrats.versions.version_modele`.
  - `[low]` `[patch]` (edge) Mode WAL refusé sans erreur — mode relu et vérifié.
  - `[low]` `[reject]` (edge) Gabarit non UTF-8 — fichier versionné du dépôt.
  - `[low]` `[reject]` (edge) Jeton d'un autre ticket ré-identifié — un jeton ne se ré-identifie qu'en sa propre valeur ; le modèle ne voit que les jetons de son entrée.
  - `[low]` `[reject]` (edge) `tickets_textes.parquet` contient le numéro en clair — fichier de Passage prévu (AD-23), local et fictif ; les traces et les sorties LLM en sont exemptes (testé).
  - `[medium]` `[patch]` (edge) AD-12 « sans exception » non tenu en cas de chevauchement — même correctif.

### 2026-10-12 — Review pass (suivi, code actuel)
- verdicts: 36 findings — high 0, medium 4, low 29, false 3, maybe-false 0
- findings:
  - `[low]` `[reject]` (intention) Lignes Palier 2 hors du diff de suivi — tenues par la composition et `test_execution.py` (deux Passages Palier 2), hors du périmètre du diff relu.
  - `[low]` `[reject]` (intention) Pseudonymiseur HMAC de production au-delà de l'intention — ajouté par la boucle 1 (AC 1, spine E0-7).
  - `[low]` `[reject]` (intention) Clé d'un autre projet ignorée par le contrôle des citations — un seul projet Jira (`cle_projet`) en E0 ; règle du préfixe retenue pour écarter `IND-1`, `UTF-8`.
  - `[false]` `[reject]` (intention) Comportements ajoutés à l'explication (réponse vide, brouillon filtré) — correctifs des passes précédentes.
  - `[false]` `[reject]` (intention) `version_modele` de la trace tirée de la réponse — amendement de la boucle 1.
  - `[false]` `[reject]` (intention) Frontières d'import non montrées par le diff — tenues par import-linter, vert.
  - `[medium]` `[patch]` (blind) Ré-identification de jetons d'autres appels — limitée aux jetons de l'entrée pseudonymisée de l'appel ; testé.
  - `[low]` `[reject]` (blind) Collisions sur 24 bits — carried (AD-15).
  - `[medium]` `[patch]` (blind) Clé de ticket entamée par un motif à cheval — les clés ne sont jamais touchées ; seuls les fragments hors clé sont pseudonymisés (adaptateur et doublure) ; exemple de contrat ajouté.
  - `[low]` `[reject]` (blind) Clés d'un autre projet — même raison que la ligne d'intention.
  - `[low]` `[reject]` (blind) Abréviations — carried.
  - `[low]` `[reject]` (blind) Sauts de ligne perdus au filtrage — texte d'une explication ; mise en forme fine en L6.
  - `[low]` `[reject]` (blind) Régénération sans retour correctif — carried.
  - `[false]` `[reject]` (blind) Erreur d'un fournisseur fatale à l'étape — carried (AD-12).
  - `[low]` `[reject]` (blind) Taille du prompt non bornée — carried.
  - `[low]` `[reject]` (blind) Clé de cache sans `max_jetons_sortie` ni schéma — carried (AD-12).
  - `[low]` `[patch]` (blind) Ticket en cause sans texte rempli en silence — avertissement journalisé, testé.
  - `[low]` `[patch]` (blind) Clé HMAC faible acceptée — au moins 16 caractères, testé.
  - `[low]` `[patch]` (blind) `test_apercu_n_ecrit_pas_la_table` inopérant — lit le jeton réellement produit.
  - `[low]` `[reject]` (blind) Tests manquants (concurrence WAL, retour arrière, fabrique) — hors usage E0 ; fabrique carried.
  - `[medium]` `[patch]` (verification-gap) Clé à cheval non couverte par la suite de contrat — même correctif.
  - `[low]` `[patch]` (verification-gap) Règle « type de la plus longue » jamais exercée — `test_type_du_plus_long_dans_un_groupe`.
  - `[low]` `[patch]` (verification-gap) Docstrings fausses sur les clés — rendues vraies par le correctif.
  - `[medium]` `[patch]` (edge) Clé de ticket remplacée — même correctif.
  - `[low]` `[reject]` (edge) Collision HMAC — carried.
  - `[low]` `[patch]` (edge) Jeton collé à un mot non ré-identifié — candidats par lookarounds, testé.
  - `[low]` `[patch]` (edge) Jeton préfixé (`ID_COMPTE_…`) non ré-identifié — variantes de suffixe, testé.
  - `[low]` `[reject]` (edge) Échec de lecture du cache fatal — carried.
  - `[low]` `[reject]` (edge) Échec d'écriture du cache après un appel payé — erreur disque explicite ; cas improbable.
  - `[low]` `[reject]` (edge) `brut` hors JSON du schéma — carried (contrat des adaptateurs de L6).
  - `[low]` `[reject]` (edge) Clé de cache sans paramètres d'appel — carried.
  - `[low]` `[reject]` (edge) Échec du fournisseur fatal — carried (AD-12).
  - `[low]` `[reject]` (edge) Textes en double pour une clé — `tickets_textes` produit une ligne par ticket.
  - `[low]` `[reject]` (edge) Brouillon multiligne aplati — même raison que la ligne blind.
  - `[low]` `[patch]` (edge) Promesse « clés jamais touchées » non tenue — même correctif.
  - `[low]` `[reject]` (edge) Clé d'un autre projet admise — même raison que la ligne d'intention.

## Verification

**Commands:**
- `uv run ruff check . ; uv run ruff format --check .` -- expected: aucun écart.
- `uv run mypy` -- expected: aucune erreur.
- `uv run lint-imports` -- expected: tous les contrats KEPT.
- `uv run pytest` -- expected: tout vert.

## Auto Run Result

Status: done

**Résumé.** `usine.ia.passerelle` applique l'ordre AD-12 : Pseudonymisation → cache SQLite (WAL) → `FournisseurLLM` → contrôle → ré-identification → `EntreeTrace`.

- **Tâche `explication`.** `controler_citations` contrôle chaque phrase : une citation doit porter le préfixe de projet d'un ticket autorisé. La tâche régénère une seule fois puis replie sur « explication indisponible ». Le brouillon de commentaire est filtré lui aussi.
- **Pseudonymisation de production.** `PseudonymiseurHmac` dérive les jetons par HMAC de `USINE_CLE_PSEUDO` et tient la table de ré-identification `donnees/pseudonymes.sqlite`.
- **Chaîne.** En Palier 2, l'étape `explications` publie `llm/explications.json` et `trace/llm.jsonl`. Le fournisseur reste injecté : aucun fournisseur réel avant la lane L6.

**Fichiers.**
- `src/usine/ia/{controles,passerelle,explication,etape}.py`, `src/usine/ia/prompts/explication.md` : passerelle, contrôle, tâche, étape et prompt.
- `src/usine/adaptateurs/stockage_sqlite/` : `CacheLLMSqlite` et `TablePseudonymesSqlite`.
- `src/usine/adaptateurs/pseudonymisation/` : `PseudonymiseurHmac`.
- `src/usine/domaine/instantanes.py` et `src/usine/chaine/etapes.py` : sortie `tickets_textes`.
- `src/usine/composition.py` : branchement du Palier 2, de la clé et des motifs.
- Tests : `tests/unit/ia/`, `tests/unit/adaptateurs/{stockage_sqlite,pseudonymisation}/`, `tests/contrat/pseudonymiseur/` (fabrique `hmac`) et `tests/unit/chaine/`.

**Revue.**
- Passe 1 : 36 findings. Une reprise de spec (`bad_spec`) a ajouté la Pseudonymisation HMAC de production et intégré les correctifs ; le reste est rejeté avec son motif.
- Passe 2 : 34 findings. 16 lignes `patch` (7 medium, en 3 causes) ont donné 7 correctifs ; 0 différé.
- Comme en Story 0.2, le code a été amendé en place : la remise à zéro est refusée par le classifieur de permissions.

**Revue de suivi.** `true` : trois causes `medium` ont été corrigées en passe 2. Risque non vérifié : un motif qui chevauche partiellement une clé de ticket remplace désormais une partie de la clé. Le texte envoyé contient alors une clé tronquée, par exemple `ABC-IDENTIFIANT_xxxxxx`. Son effet sur `controler_citations` après ré-identification n'est pas éprouvé par un test de bout en bout.

**Vérification.** ruff, ruff format, mypy, lint-imports et pytest : 812 passés.

**Risques résiduels.**
- `cout_estime_eur` vaut 0, en attendant le registre des prix de la lane L6.
- Le Palier 2 n'est pas lançable depuis la CLI : aucun fournisseur réel n'existe encore.
- `CacheLLM` et `TablePseudonymes` sont des `Protocol` locaux. La Story 0.9 décidera s'ils deviennent des ports.

### Revue de suivi (2026-10-12)

**Résumé.** Revue du code actuel (passerelle, contrôles, explication, adaptateurs de pseudonymisation et SQLite) : 36 findings, 14 lignes `patch` (4 medium, en 2 causes) donnant 7 correctifs, 0 différé.

**Correctifs.**
- Le risque nommé lors de la passe initiale est fermé : les clés de ticket ne sont plus jamais touchées. Seuls les fragments hors clé d'une correspondance sont pseudonymisés, dans l'adaptateur comme dans la doublure, avec un exemple dans la suite de contrat.
- La ré-identification se limite aux jetons de l'entrée de l'appel : la valeur d'un autre dossier ne peut plus apparaître.
- Les jetons collés à un mot ou préfixés sont ré-identifiés.
- La clé HMAC doit compter au moins 16 caractères.
- Un ticket en cause sans texte est signalé dans le journal.
- Ajout du test de la règle « type de la plus longue », et correction de `test_apercu_n_ecrit_pas_la_table`.

**Revue de suivi.** `false` : aucun correctif `high`.

**Vérification.** ruff, ruff format, mypy, lint-imports et pytest : 864 tests passés.

**Risque résiduel.** Une citation d'un autre projet Jira n'est pas contrôlée. C'est acceptable avec un seul projet en E0 ; à revoir si L2 ou L6 introduisent plusieurs projets.
