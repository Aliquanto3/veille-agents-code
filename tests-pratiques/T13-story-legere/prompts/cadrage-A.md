Tu es chargé de cadrer une story avant son développement, avec la méthode BMAD reproduite ci-dessous (skill `bmad-build`, étapes « clarifier » puis « planifier », jusqu'à l'écriture du fichier de spec). Tu n'implémentes rien : un autre agent développera la story à partir de ton document.

# Cadre d'exécution (sans interaction)

- Personne ne répond à tes questions. Toute question ouverte (Open Questions, intent gap) est tranchée par toi, avec l'option la plus défendable pour ce dépôt. Note chaque décision dans une section finale `## Décisions prises sans l'utilisateur` (une ligne par décision : choix retenu, option écartée). Aucun HALT, aucun checkpoint, aucune approbation.
- Outils : Read, Glob, Grep, en lecture seule. Pas de sous-agent ni de Bash : fais toi-même l'investigation. Si `epic-N-context.md` n'existe pas, ne le compile pas : lis directement les documents de planification utiles (epics, architecture) et la spec de la story précédente de l'épopée si elle existe.
- Dans la méthode, `{{.implementation_artifacts}}` désigne `_bmad-output/implementation-artifacts` et `{{.planning_artifacts}}` désigne `_bmad-output/planning-artifacts`. Langue des échanges et du document : français.
- Ignore tout ce qui touche au contrôle de version, au sprint-status, à deferred-work, à `story_key` et à l'écriture de fichier. Prends toujours la voie complète (`route: 'dispatch'`) : tu remplis le modèle complet, sans voie one-shot. Mets `status: 'ready-for-dev'`.
- Ta réponse finale EST le contenu du fichier de spec, du frontmatter à la dernière ligne : pas de préambule, pas de bloc de code qui l'entoure, pas de commentaire après.
- Intègre l'interface imposée (section « Interface attendue ») dans la Code Map et les tâches.

# Méthode BMAD

{{METHODE}}
