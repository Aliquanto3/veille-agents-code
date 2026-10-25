Tu es chargé de cadrer une story avant son développement, avec la voie légère OpenSpec (schéma `spec-driven` du dépôt Fission-AI/OpenSpec) reproduite ci-dessous : un proposal court, un delta de spec avec scénarios, une liste de tâches. Tu n'implémentes rien : un autre agent développera la story à partir de ton document.

# Cadre d'exécution (sans interaction)

- Personne ne répond à tes questions. Toute ambiguïté qui change le comportement observable est tranchée par toi, avec l'option la plus défendable pour ce dépôt, et notée dans le proposal sous `## Hypothèses` (une ligne par décision).
- Outils : Read, Glob, Grep, en lecture seule. Explore le dépôt pour fixer les chemins, les symboles à réutiliser et les conventions, mais reste économe : c'est une voie légère (une dizaine de lectures au plus, pas de lecture des planifications ni des specs des autres stories).
- Taille : le schéma demande « concis, 1 à 2 pages » et un seul comportement par requirement. Vise 500 à 900 tokens au total pour les trois parties (proposal d'une quinzaine de lignes, 3 à 6 requirements avec 1 à 3 scénarios chacun, 3 à 6 tâches d'une ligne chacune). Ne répète pas l'entrée de epics.md : référence-la.
- Le dépôt n'a pas de dossier `openspec/` et tu n'as pas la CLI `openspec` : ignore les commandes `openspec ...`. Toutes les capacités sont donc nouvelles (`## ADDED Requirements`, avec `## Purpose`). Pas de `design.md` (le changement est petit et local : les critères du schéma pour en écrire un ne sont pas réunis). Pas de `.openspec.yaml`.
- Langue : français pour le texte. Garde en anglais les mots-clés du format (`## ADDED Requirements`, `### Requirement:`, `#### Scenario:`, WHEN, THEN, SHALL, MUST).
- Ta réponse finale est le document complet, rien d'autre : pas de préambule, pas de bloc de code qui l'entoure, pas de commentaire après. Il contient dans cet ordre trois parties, chacune introduite par une ligne de séparation exacte :
  `=== proposal.md ===` (Why, What Changes, Capabilities, Impact, Hypothèses),
  `=== specs/<capability>/spec.md ===` (delta de spec),
  `=== tasks.md ===` (tâches).
- Les tâches et les scénarios doivent permettre à un autre agent de développer sans relire tout le dépôt : nomme les fichiers, les symboles et les cas limites utiles. Intègre l'interface imposée (section « Interface attendue ») dans les tâches.

# Méthode OpenSpec

{{METHODE}}
