## Intent

**Problem:** La démo n'a aucune surface visible : rien n'affiche la carte météo du dernier Passage, ne lance la Chaîne ni n'en suit la progression, et le Mode repli n'est signalé nulle part (Story 0.8 de `epics.md`, amorces de FR-43 et FR-45).

**Approach:** Une page Streamlit dans `usine.ui` affiche :
- la carte météo du dernier Passage publié, lue via `Consultation` seulement ;
- un bouton qui lance `usine rapport` en sous-processus et affiche chaque `Etape` en lisant `sorties/progression/<passage_id>.jsonl` en ouvrir-lire-fermer ;
- un bandeau « Mode repli » permanent quand `USINE_MODE_REPLI=1`.

`usine ui` démarre la page.

## Boundaries & Constraints

**Always:**
- `usine.ui` n'importe que `usine.contrats`, `usine.consultation`, `usine.composition` et `streamlit` (contrat import-linter). L'accès aux Passages passe par une fonction de `composition`, qui rend une `Consultation` sur le dernier Passage publié ou `None`.
- L'UI n'ouvre jamais `donnees/entrepot.duckdb` ni un répertoire `sorties/passages/.en-cours-*`. Elle ne lit que via `Consultation` et le fichier de progression.
- Lancement : `subprocess.Popen([sys.executable, "-m", "usine", "rapport", ...], cwd=racine)`, sans bloquer la page. Un module `src/usine/__main__.py` délègue à `usine.cli.main`.
- Progression :
  - le fichier du Passage lancé est le premier `sorties/progression/*.jsonl` apparu après le lancement, absent de la liste prise juste avant ;
  - chaque sondage ouvre, lit et ferme le fichier, puis valide chaque ligne complète par `EvenementProgression` ;
  - une dernière ligne incomplète (sans `\n`) est ignorée jusqu'au sondage suivant ;
  - l'affichage donne, pour chaque `Etape` dans l'ordre d'AD-8, son dernier statut (`en_cours`, `reussie`, `sautee`, `echouee`) ou « en attente ».
- Mode repli : lu par `composition` depuis `Secrets` (racine `.env` compris), jamais activé automatiquement (H-30). Le bandeau s'affiche en haut de la page et reste visible quel que soit l'état de la page.
- Carte météo : une ligne par Entité, avec son libellé français de couleur (`contrats.tickets.LIBELLES` ou l'équivalent de `rendu`) et la Date d'arrêté du Passage. Sans Passage publié, un message explicite remplace la carte.
- Toute la logique hors affichage vit dans des fonctions pures testables sans Streamlit : sélection du fichier de progression, lecture des lignes, état par étape, lignes de la carte.

**Never:**
- Modifier `src/usine/contrats/`, `src/usine/ports/`, `pyproject.toml`, `uv.lock` ; ajouter une dépendance.
- Lire un fichier de Passage hors de `Consultation`, appeler la Chaîne dans le processus de l'UI, ou écrire dans `sorties/`.
- Construire les écrans complets (détail d'Entité, Agent, avant/après, comparaison des Paliers : lane L7).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Carte météo | Passage publié (Journal graine 42, 2026-10-09) | page avec une ligne par Entité (ENT-A, ENT-B), couleur égale à `consultation.meteo()`, Date d'arrêté 09/10/2026 | N/A |
| Sans Passage | `sorties/passages/` vide | message « aucun Passage publié », pas d'erreur | N/A |
| Mode repli | `USINE_MODE_REPLI=1` | bandeau « Mode repli » présent en tête de page | N/A |
| Hors Mode repli | variable absente | aucun bandeau | N/A |
| Lancement | clic sur « Lancer la Chaîne » (Popen injecté en test) | commande `[python, "-m", "usine", "rapport", ...]` dans la racine ; la page reste interactive | N/A |
| Progression | fichier avec `extraction` `en_cours` puis `reussie`, `instantanes` `en_cours` | `extraction` : réussie ; `instantanes` : en cours ; autres : en attente | N/A |
| Ligne partielle | dernière ligne sans `\n` | ignorée, aucune erreur | N/A |
| Choix du fichier | deux fichiers anciens et un nouveau apparu après le lancement | le nouveau est suivi | N/A |
| Échec | ligne `echouee` sur `kpi` | `kpi` affiché en échec | N/A |
| Commande | `usine ui --help` | aide de la sous-application, code 0 | N/A |

</intent-contract>

## Code Map

- `src/usine/ui/cli.py` -- sous-application `usine ui` (callback seul) : ajouter la commande qui lance `streamlit run <chemin de usine/ui/app.py>` en sous-processus.
- `src/usine/composition.py` -- `construire_rapport`, `lancer_rapport`, `Rapport.fabrique_consultation` ; ajouter `consultation_dernier_passage(racine) -> Consultation | None`. Elle utilise `ConsultationPassage(...).dernier_passage()` pour localiser `<date>/<id>/`, avec `url_jira` venant de `config/jira.yaml` et du Mode repli. Ajouter aussi `mode_repli(racine) -> bool`.
- `src/usine/consultation/passage.py` -- `ConsultationPassage(repertoire, racine_passages=, url_jira=, date_arrete=)`, `dernier_passage()`, `meteo()`.
- `src/usine/contrats/passage.py` -- `Etape` (ordre AD-8), `StatutEtape`, `EvenementProgression`.
- `src/usine/chaine/ecrivain.py:110` -- progression écrite dans `sorties/progression/<passage_id>.jsonl`, en ouvrir-ajouter-fermer.
- `src/usine/rendu/commun.py` -- libellés de couleur déjà utilisés par le rendu. `ui` ne peut pas importer `rendu` : reprendre `contrats.tickets.LIBELLES` si les couleurs y figurent, sinon un petit dictionnaire local.
- `src/usine/cli.py` -- `main()` ; enregistre déjà `ui`.
- `tests/unit/chaine/environnement.py` -- `preparer_racine` (copie `config/` et `gabarits/`) pour publier un Passage d'essai.

## Tasks & Acceptance

**Execution:**
- `src/usine/__main__.py` -- `from usine.cli import main` puis `main()`.
- `src/usine/ui/progression.py` -- `fichiers_progression(racine) -> frozenset[Path]`, `fichier_nouveau(avant, racine) -> Path | None`, `lire_progression(chemin) -> tuple[EvenementProgression, ...]` (ouvrir-lire-fermer, ligne partielle ignorée), `etat_des_etapes(evenements) -> list[tuple[Etape, str]]`.
- `src/usine/ui/carte.py` -- `lignes_carte(consultation) -> list[dict[str, str]]` (Entité, Météo) et libellés.
- `src/usine/ui/lancement.py` -- `lancer_chaine(racine, date_arrete=None, popen=subprocess.Popen) -> subprocess.Popen[bytes]`.
- `src/usine/ui/app.py` -- page Streamlit :
  - bandeau Mode repli ;
  - carte du dernier Passage ;
  - bouton de lancement, avec la liste des fichiers mémorisée dans `st.session_state` ;
  - suivi de la progression rafraîchi par sondage (`st.rerun` ou fragment à intervalle) tant que le processus tourne.
  
  La racine est le répertoire courant, ou `USINE_RACINE` si elle est définie.
- `src/usine/ui/cli.py` -- commande `usine ui` (`streamlit run`).
- `src/usine/composition.py` -- `consultation_dernier_passage`, `mode_repli`.
- `tests/unit/ui/test_progression.py`, `test_carte.py`, `test_lancement.py`, `test_app.py` (via `streamlit.testing.v1.AppTest`, `monkeypatch.chdir` sur une racine d'essai), `tests/unit/test_cli.py` ou `tests/unit/ui/test_cli.py` -- matrice I/O.

**Acceptance Criteria:**
- Given le dépôt, when `uv run ruff check . ; uv run ruff format --check . ; uv run mypy ; uv run lint-imports ; uv run pytest`, then tout passe, et `lint-imports` confirme que `usine.ui` n'importe ni `usine.chaine` ni `usine.adaptateurs`.
- Given un test qui inspecte `src/usine/ui/*.py`, when il cherche `entrepot.duckdb`, `.en-cours` et `duckdb`, then aucune occurrence n'est trouvée.

