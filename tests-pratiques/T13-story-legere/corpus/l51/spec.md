# Story 5.1 : Annotations humaines et kappa de Cohen

## Code Map

- `src/wavelibrarian/stats/kappa.py` : `cohen_kappa(a, b) -> float | None` (fonction pure, sans dépendance).
- `src/wavelibrarian/scoring/calibration.py` : `charger_fichier`, `charger_dossier -> Annotations` (verdicts indexés par (annotateur, `answer_id`, `criterion`)), `answer_ids_de_answers_jsonl`, `rapprocher -> Rapprochement(annotations, ignorees)`.

## Design Notes

- Erreurs en `ConfigError` au chemin pointé : `annotations[3].criterion`, `.verdict`, `.answer_id`, doublon à `annotations[3]`. Un dossier sans `*.yaml`, ou un fichier sans `annotator`, est aussi une `ConfigError` (la story 5.2 en fera le code de sortie 2).
- Contradiction relevée : le contrat §4.6 écrit `verdict: yes` sans guillemets, que PyYAML (YAML 1.1) lit comme le booléen `True`. Lecture retenue : booléens YAML et chaînes `"yes"` / `"no"` acceptés ; tout autre type ou valeur est refusé.
- Le doublon se détecte sur (annotateur, `answer_id`, Critère), y compris entre deux fichiers du même annotateur.
- Kappa : table de contingence 2x2 ; `None` si vecteurs vides ou accord attendu égal à 1 (une seule classe commune) ; longueurs différentes = `ValueError`.
- `rapprocher` compare à l'`answer_id` complet (run, config, condition, tier, phase, Question) : une autre phase ou un autre tier est ignoré et signalé, une fois par identifiant.
- `scoring` n'importe ni `report` ni `runner` (AD-1) ; `stats` n'importe rien du projet (AD-22).

## Tâches et critères

- [x] Annotations indexées par (annotateur, `answer_id`, `criterion`), verdict booléen, deux annotateurs.
- [x] Critère hors liste, verdict hors `yes`/`no`, doublon : `ConfigError` au chemin.
- [x] `answer_id` absent d'`answers.jsonl` signalé et ignoré, identifiant complet.
- [x] Table 20/5/10/15 donne 0,4 à 1e-12.
- [x] Vecteurs identiques = 1 ; une seule classe = `None` ; longueurs différentes = `ValueError`.
