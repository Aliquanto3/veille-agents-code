💸 Optimisez votre consommation Claude Code

Ces dernières semaines, j'ai développé plusieurs applications avec Claude Code, dont certaines que je vous ai partagées déjà sur LinkedIn (et le reste en public dans mon GitHub). 

J'ai voulu aller toujours plus loin : 
- passer de frameworks plus simples comme OpenSpec/SpecKit à des plus avancés comme AIDD/BMAD
- développer plusieurs projets à la fois dans différents onglets
- accélérer les développements d'un même projet en parallélisant des sous-agents sur des worktrees/lanes différents...

Graduellement, pour supporter tous ces projets (et l'optimisation de mes skills de génération de slides via plusieurs dizaines de tests !), je suis monté dans les abonnements Anthropic : Pro, Max x5, jusqu'à Max x20 ce mois-ci.

Puis, cette semaine, après un pic à 3 orchestrateurs et une vingtaine d'agents tournant en parallèle sous Opus, j'ai consommé en une journée plus de 60% des crédits de ma semaine entière. WOUPS  😱 

Cela dit, ça m'a aussi offert beaucoup de données pour identifier les postes de consommation de mes projets ! J'ai donc lancé Claude à la recherche des optimisations recommandées en ligne et je l'ai fait tester sur 109 stories des trois projets des combinaisons de plusieurs paramètres : choix de modèle et d'effort, conditions de déclenchement de sous-agent, durée de mise en cache des prompts...

👉 D'où le plugin open source que je publie : Sonnet code, Haiku fait un second avis pour quelques centimes, Opus relit et corrige. Avec un script qui calcule le coût réel de chaque story depuis vos transcriptions, et les bancs de tests pour tout rejouer quand les modèles changent (environ 60 $... dans l'API !). Cette combinaison permet de réduire les coûts... et même d'optimiser la performance ! Par exemple, un de mes relecteurs Opus avait raté un changement critique qui cassait la CI, alors qu'Haiku qui réalisait la même tâche pour comparaison l'avait détecté... pour des dizaines de fois moins cher.

🏆Sur les projets où je l'ai testé, ce plugin divise environ par 5 la consommation !
(d'après l'estimation de Claude)

Ce test confirme d'ailleurs combien l'abonnement Claude est généreux : selon les mesures de consommation pour la création du plugin final et les prix de l'API Anthropic, j'aurais dû payer 1850$ 😰Alors que je n'ai consommé que 10% de ma limite hebdomadaire de la licence à 200$ pour ces tests. Je commence à comprendre le business des comptes qui sont revendus dans des routeurs...

Bien entendu, ça reste un plugin basé sur ma seule expérience dans un faible nombre de projets, donc n'hésitez pas à relancer les tests sur vos propres projets ! Et je continuerai à le mettre à jour en testant sur mes prochains repos.

Et vous, avez-vous augmenté le montant de votre licence ou optimisez-vous les coûts de vos agents ? Je serais ravi de vous faire un retour d'expérience plus détaillé sur l'optimisation des coûts de l'IA dans la stratégie plus globale de l'entreprise (et pas juste sur le code) !
