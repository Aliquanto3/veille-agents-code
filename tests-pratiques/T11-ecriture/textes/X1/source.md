J'ai passé deux jours à vérifier ce que valent vraiment les outils censés rendre les agents de code moins chers ou meilleurs. J'ai mené 15 tests pratiques sur mes propres projets et sur 45 jours de transcriptions Claude Code.

Verdict : aucun dépôt de ma liste de veille ne fait strictement mieux que l'option la plus simple.

**Ce qui rapporte, mesuré :**
• Réduire le contexte fixe. 8 outils rarement appelés pesaient 17,8 k tokens à chaque appel.
• Un second avis par Haiku avant la revue. 87 % de ses constats sérieux ont été corrigés, pour 0,03 $ par story.
• Sonnet seul pour implémenter. Il coûte 0,53 $ par story contre 1,33 $ pour Opus, avec le même taux de réussite.
• Vérifier les critères d'acceptation dans un vrai navigateur. C'est le seul contrôle qui a relevé un écart sur mes tests de design.

**Ce qui ne rapporte pas, mesuré aussi :**
• un relecteur d'une autre famille de modèles (+6 points, non significatif) ;
• verrouiller les tests (aucune triche sur 40 runs) ;
• /advisor ;
• les tests property-based ;
• les juges de commandes shell ;
• la compression des sorties ;
• les modèles locaux au quotidien ;
• tailler un CLAUDE.md de quelques milliers de tokens.

**La vraie découverte : la mutation guidée.** On lance une mutation sur le code de la story, puis on montre à l'agent les mutants qui survivent à ses tests. L'agent a alors bouché 134 trous non équivalents sur 134. Avec une simple consigne « renforce tes tests », il n'en bouchait que 59 %. Coût : 0,22 $ par story. Il a aussi reconnu sans erreur les 35 mutants équivalents. C'est le seul ajout à ma chaîne que les tests justifient, en étape optionnelle de la revue.

La leçon générale : avant d'ajouter un outil, il faut le mesurer sur ses propres données. Les gains viennent plus souvent de ce qu'on retire que de ce qu'on ajoute.

Et vous, qu'avez-vous mesuré dans vos chaînes d'agents ?

#ClaudeCode #AgentsIA #GénieLogiciel #Tests
