# Instructions globales

## Développement avec BMAD
À la fin de chaque étape ou workflow BMAD (brief, PRD, UX, architecture, epics/stories, sprint planning, dev story, code review, etc.), terminer toujours le message par une section **« Étape suivante recommandée »** qui contient :
- **Skill** : le skill BMAD exact à invoquer (ex. `bmad-create-prd`)
- **Prompt** : un prompt prêt à copier-coller
- **Modèle** : le modèle recommandé (voir grille ci-dessous)
- **Effort** : le niveau d'effort recommandé (low / medium / high / xhigh / max)
- Préciser s'il faut ouvrir un nouveau chat (`/clear`) avant l'étape.
- Pour implémenter et relire une story, recommander la chaîne agent-cost-kit (`dev-story` → `second-avis` → `reviewer`), jamais `bmad-build`, `bmad-build-auto` ni `bmad-code-review` (mesuré : 1,18 à 1,60 $ par story contre 6,77 à 7,31 $).

### Grille modèle / effort
D'après le guide Anthropic « What a task costs on Opus 5.5 » (sept. 2026) et la page de prix de l'API (oct. 2026). Prix par Mtok, entrée / sortie : Opus 5.5 à 4 $ / 20 $, Sonnet 5.5 à 2 $ / 10 $, Haiku 5.5 à 0,10 $ / 0,50 $, Fable 5.1 à 10 $ / 50 $.

**Modèle**
- **Opus 5.5** : par défaut pour le travail supervisé de conception et de décision (brief, PRD, UX, architecture, création des stories, debug difficile, stories transverses multi-couches), pour l'orchestration des runs autonomes et pour la recherche web qui doit éclairer une décision. Mesure du 2026-10-13, jugée en aveugle : Opus arrive premier en architecture (8,5/10, contre 7,5 pour Sonnet et 7,0 pour Haiku), en recherche web (8,4, 7,8 et 6,4) et en spec de story (8,4, 8,0 et 6,2), pour un surcoût de 20 à 80 % sur Sonnet. Haiku y commet des erreurs factuelles ou d'architecture.
- **Sonnet 5.5** (moitié du prix d'Opus) : pour les sous-agents qui implémentent une story bien cadrée et pour les sous-agents de revue. Si Sonnet échoue deux fois sur la même story, la reprendre avec Opus. Mesure du 2026-10-13 (projet slm, une tâche par cas) : même conception qu'Opus pour 55 % de moins en développement, mêmes constats pour 25 % de moins en revue.
- **Haiku 5.5** : pour les sous-agents de lookup, de lecture de logs ou de recherche factuelle simple, jamais pour écrire du code, une spec, ni une synthèse de recherche qui fonde une décision. Il convient aussi comme relecteur adversarial d'appoint, en lecture seule : sur la même mesure, ses constats valaient ceux d'Opus pour environ 5 % du prix. En développement, il livre une version minimale qui oublie des cas.
- Le coût d'un sous-agent vient surtout de la relecture du contexte (lecture et écriture du cache, environ 85 %), et la lecture du cache coûte le même prix chez Sonnet et Opus. On économise donc d'abord en réduisant le nombre de tours et la taille du contexte.
- **Fable 5.1** (~2,5× le prix d'Opus 5.5) : quand le résultat compte plus que le coût en tokens, ou quand Opus 5.5 en effort high bute deux fois sur le même problème. Revenir à Opus 5.5 une fois le problème résolu.
- Tâches mécaniques (renommages, pattern connu appliqué sur plusieurs fichiers, mise à jour du sprint status) : Opus 5.5 en effort **low** dans la session principale, ou un sous-agent Sonnet.
- Dans un projet qui définit des agents `.claude/agents/` (par ex. `dev-story`, `reviewer`, `lookup`), les utiliser : ils portent le modèle et l'effort.

**Effort**
- **low** : travail mécanique.
- **medium** : par défaut pour le travail courant bien cadré (brief, UX, create-story, dev story sur une story claire, code review).
- **high** : quand medium cale ou que les correctifs ne traitent qu'une couche. Aussi pour l'architecture et les stories transverses multi-couches, où ~20K tokens de réflexion (~0,40 $) coûtent moins qu'une boucle de retry.
- **xhigh / max** : exceptionnel, pour les problèmes les plus durs. max ne vaut que pour une session.
- Escalade : d'abord monter l'effort et ajouter des vérifications (tests, build). Ensuite seulement passer à Fable 5.1.

**Nouveau chat**
- Recommander `/clear` entre deux étapes sans rapport entre elles, et quand le modèle de la session change : ce changement invalide le cache. Un changement d'effort ne l'invalide pas avec les modèles 5.5. Une modification de CLAUDE.md ne l'invalide pas non plus, mais elle ne s'applique qu'après `/clear`.

**Sous-agents et runs autonomes**
- Un sous-agent d'implémentation ne lance pas lui-même de sous-agents : l'orchestrateur lance ensuite la revue, avec un appel qui attend le résultat. Un sous-agent parti en arrière-plan sans être attendu oblige à reprendre la story.
- Lancer les tests ciblés pendant le développement, et la suite complète une seule fois, avant l'intégration.
- Mesurer avec `/usage` avant et après un changement de méthode.
- Retour d'expérience détaillé (banc d'essai Haiku / Sonnet / Opus, agents, hook de contrôle rapide, réglages) : `<user>\Documents\GitHub\usine-migration-jira-demo\docs\retour-experience-couts-agents.md`.
- Pour une modification multi-fichiers, recommander de démarrer en plan mode.
