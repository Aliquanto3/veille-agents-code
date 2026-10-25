# T11 : réécrire un texte avec `clarity`, `humanizer`, ou les deux enchaînées

Test du 2026-10-25. Résultat provisoire : **la note à l'aveugle d'Anaël (`notation.html`) décide**. Les mesures automatiques ne départagent presque pas les conditions.

## 1. Résumé provisoire

- **Portes dures** (juge Opus aveugle, 32 sorties) : `humanizer` seul 0 essai sur 8, `clarity` seul 0 sur 8, aucune skill 1 sur 8, `clarity` puis `humanizer` 1 sur 8. Aucune condition n'est éliminée (seuil : plus d'un essai sur quatre). Ma relecture, plus sévère, ajoute 2 essais sans skill et 1 essai `clarity` pour un « aujourd'hui » inventé (section 5) : elle éliminerait la condition sans skill (3 sur 8), pas les autres.
- **Tics de surface** : presque rien à mesurer. Les textes de départ en contiennent peu (0 tiret, 0 « pas X mais Y » dans le brouillon X1), et un simple « réécris plus clair » sans skill les supprime déjà. Seul écart net : `humanizer` retire le gras décoratif (1,8 gras par texte contre 6 sans skill ou avec `clarity`) et réduit les exclamations de X3 (3,5 contre 6,5 sans skill).
- **Voix d'Anaël (X3)** : `humanizer` garde « WOUPS » 2 fois sur 2, `clarity` 1 sur 2, la condition D 1 sur 2, la condition sans skill 0 sur 2 (« OUPS »). `humanizer` fond la liste à puces en une phrase (2 fois sur 2).
- **Coût** par essai : sans skill 0,060 $, `clarity` 0,113 $, `humanizer` 0,133 $, les deux enchaînées 0,313 $ (5 fois la condition sans skill).
- **Conclusion provisoire** : rien dans les mesures ne justifie d'enchaîner les deux (D n'a ni moins de tics, ni moins d'écarts, et coûte 2,4 à 2,8 fois une skill seule). Entre A, B et C, c'est ta note qui tranche. Hypothèse « fond contre surface » : non testable ici, car les deux skills ont changé peu de choses l'une et l'autre par rapport à une réécriture simple.

## 2. Protocole

**Textes** (`textes/`)
- **X1** : brouillon de post LinkedIn de 316 mots, écrit une fois par `claude -p --model opus` (effort medium) à partir de `synthese/bilan.json` (champ `essentiel`) et de la section « 7 bis » du rapport. Figé. Le prompt est dans `textes/X1/prompt_generation.txt`. Il dépasse un peu les 300 mots demandés (326 avec le balisage). Il contient « deux jours », absent des données : c'est une faiblesse du texte source, pas des réécritures (le juge ne compare qu'à X1).
- **X2** : « Résumé exécutif » du rapport technique (579 mots, 20 renvois [n], chiffres).
- **X3** : post LinkedIn publié par Anaël (480 mots), fichier source non modifié. Porte supplémentaire : la voix. Ce qui disparaît est noté, sans échec automatique.
- **X4** : extrait de 314 mots (Observation 8 et début de la section 12.5) de Barbaste, Darrigol, Vu et Wiltberger, « Harness Engineering: Anatomy, Architecture, and Evolution of Coding Agents -- A Source-Code Study of Eleven Systems », arXiv:2609.00006v1, 15 juillet 2026, CC BY 4.0 (page arXiv vérifiée). Consigne et sorties en anglais. L'attribution est en tête du fichier et n'est pas envoyée aux modèles (marqueur `<!-- TEXTE -->`). Espaces et coupures de ligne de l'extraction PDF corrigés, apostrophes rendues droites, trois tirets cadratins gardés.

**Conditions** : Claude Code 2.1.310, `claude-opus-5-5`, effort `medium`, `claude -p`, nouvelle session à chaque essai (`--no-session-persistence`), `--setting-sources project,local` (ni plugins ni `CLAUDE.md` d'Anaël), MCP désactivés, outils `Read, Write, Edit, Glob, Grep, Skill` (pas de Bash : les scripts de `clarity` ne servent qu'au mode `lint`, que le test n'utilise pas). Texte passé dans le prompt entre `<<<` et `>>>`.
- **A** : « Réécris ce texte en français pour le rendre plus clair et plus naturel, pour [lecteur]. N'invente aucun fait, ne renforce aucune affirmation, garde les chiffres et les renvois. Rends seulement le texte. » Projet sans skill. En anglais pour X4 (« Rewrite this text in English to make it clearer and more natural, for [reader]. Do not invent... »).
- **B** : même consigne + « Utilise d'abord la skill humanizer (outil Skill). » Projet avec `humanizer` seule.
- **C** : même consigne + « Utilise d'abord la skill clarity en mode rewrite (outil Skill). » Projet avec `clarity` seule.
- **D** : la sortie de C (même essai) passée dans le projet B avec la consigne de B.
- Lecteurs : X1 et X3 « tes contacts LinkedIn, consultants et développeurs », X2 « un responsable technique qui décide de la configuration de son équipe », X4 « an engineering lead choosing a coding-agent setup ».
- 2 essais par condition et par texte, soit 32 sorties. 2 sessions au plus en même temps. La skill a été invoquée dans 24 essais sur 24 où elle était demandée (flux `*.flux.jsonl`).

**Écarts au protocole demandé**
- Format `stream-json --verbose` au lieu de `json` : le dernier événement est le même objet, et le flux prouve l'invocation de la skill.
- `clarity` a lu `references/edit.md` dans 6 essais sur 8 ; dans les 2 autres (X1 et X3, essai 2) il n'a lu aucune référence. `longform.md` et `medium.md` n'ont jamais été lus, bien que `SKILL.md` les prescrive pour la prose longue. Les modes `interview` et `review`, et les questions `[TK]`, ne sont pas joués : la consigne impose « rends seulement le texte ».
- `humanizer` prévoit, pour un texte collé, de rendre aussi le brouillon et la liste des tics restants. La consigne « rends seulement le texte » l'a emporté dans les 24 essais avec skill : aucune note parasite (recherche de `[TK]`, « Voici », liste de motifs : rien).

**Mesures**
1. Portes dures : `scripts/juge.py`, un appel `claude -p --model opus` par sortie, sans outils, prompt système court, ne voit que la source et la version réécrite (aucune étiquette de condition). Types : fait inventé, affirmation renforcée, chiffre ou renvoi perdu ou modifié, sens changé, structure ou lien abîmé (+ voix effacée pour X3). Chaque écart est noté « porte » ou « mineur ». Une sortie franchit la porte si elle a au moins un écart « porte ». Détail : `juge/` et `donnees/ecarts_juge.txt`.
2. Tics : `scripts/mesurer_tics.py` (déterministe, profil français et profil anglais `tics_en.py`). Tirets, « pas X mais Y » (9 formes), chutes en une ligne, triades, mots gonflés, gras, emojis, longueur ; contrôle mécanique des chiffres et des renvois contre la source.
3. Note à l'aveugle : `notation.html`, 4 textes, 8 sorties chacun sous des lettres tirées par `secrets`, grilles de 1 à 5 (fidélité, clarté, naturel, « je le publierais », plus « ça sonne comme moi » pour X3), commentaire, sauvegarde locale, export JSON. Correspondance dans `correspondance.json` (dans `.gitignore`, non référencée par la page).

## 3. Versions et SHA

| Élément | Version | SHA |
|---|---|---|
| `clarity` (addyosmani/clarity) | 0.2.1, commit du 2026-09-04 | `e27ceeff60368cf6966b4ea00a5b9b36418ee9a0` (épinglé) |
| `humanizer` (blader/humanizer) | 3.1.0, dernier commit du 2026-10-16 (« Update README to fix sponsorship duplication ») | `8c307f367c91bd974002f10f2be2965d642c13df` |
| SkillSpector | 2.12.0 (installation de T7, `--no-llm`) | voir T7 |
| PDF arXiv 2609.00006v1 | 83 pages, 963 456 octets | sha256 `e81b5a4855adda8cc5e46db0a05cd69e0d0d542bd49cec6b157c17e6001395d7` |
| Modèle des sessions et du juge | `claude-opus-5-5`, effort medium | n/a |
| Claude Code | 2.1.310 | n/a |

## 4. Sécurité

Dépôts clonés dans `scratchpad\t11\vendor\` (dossiers neufs), rien installé au niveau utilisateur. Skills copiées à la main dans `.claude/skills/` de projets jetables (`projets\A`, `B`, `C`). Les copies de travail ont été supprimées à la fin (`scripts/nettoyer.ps1`).

**Lu en entier**
- `clarity` : `SKILL.md`, `references/` (edit, longform, medium, review, interview), `commands/` (3 commandes de 3 lignes), `scripts/` (`prose_stats.py`, `strip_markdown.py`, `validate_package.py`), `skills.sh.json`, `.claude/launch.json`, `.github/workflows/validate.yml`, `evals/JUDGE.md`. Pas de manifeste de plugin (`.claude-plugin` absent). Les scripts ne lisent qu'un fichier ou l'entrée standard et affichent du texte : pas de réseau, pas d'exécution, pas d'écriture. `prose_stats.py` utilise des lexiques anglais (peu utile en français).
- `humanizer` : `SKILL.md` (398 lignes), `.claude-plugin/plugin.json` et `marketplace.json`, `.cursor-plugin/plugin.json`, `agents/openai.yaml`, `AGENTS.md`, `scripts/validate-package.py` (vérifications locales de cohérence), `.github/workflows/validate.yml`, `CHANGELOG.md` (début). Pas de hook, pas de commande, pas de script lancé par la skill.
- Seulement parcouru par recherche de mots (réseau, installation, hook, exécution) : `README.md` des deux dépôts, `evals/cases.json`, `samples/`, `DESIGN.md`, `PRODUCT.md` et le site Astro de `clarity` (`site/src`, `netlify/` : aucun `fetch`, `XMLHttpRequest`, `child_process` ni `eval`). Non lus : `package-lock.json`, images.

**SkillSpector 2.12.0 `--no-llm`** (`securite/clarity.json`, `securite/humanizer.json`, sur les fichiers de skill sans le site) :

| Skill | Score | Constats | Verdict après lecture |
|---|---|---|---|
| `clarity` | 7/100, LOW, CAUTION | 1 MEDIUM (LP3 : pas de portée d'outils déclarée) | Exact : la skill ne déclare pas `allowed-tools`. Sans danger ici, puisque la session n'a pas Bash |
| `humanizer` | 49/100, MEDIUM, CAUTION | 2 HIGH (AR2 anti-refus, « without warning » dans l'exemple de la règle sur les tirets), 4 MEDIUM (RP1 : `npx skills add` dans README et AGENTS), 1 MEDIUM (LP3) | Faux positifs : exemples de style et commandes d'installation de la documentation, jamais exécutés |

Comme en T7, SkillSpector sert de filtre à relire, pas de preuve. Rappel : le texte source est traité comme donnée par les deux skills, et aucune session n'avait d'accès réseau ni de Bash.

**PDF de X4** (fichier non fiable) : téléchargé dans un dossier neuf, texte extrait seulement avec `pypdf` (`uv run --with pypdf python -I scripts/extraire_x4.py`, script hors du dossier du PDF).

## 5. Résultats

### Portes dures (juge aveugle)

| Condition | X1 | X2 | X3 | X4 | Essais franchis | Taux |
|---|---|---|---|---|---|---|
| A sans skill | 0/2 | 1/2 | 0/2 | 0/2 | 1/8 | 12 % |
| B `humanizer` | 0/2 | 0/2 | 0/2 | 0/2 | 0/8 | 0 % |
| C `clarity` | 0/2 | 0/2 | 0/2 | 0/2 | 0/8 | 0 % |
| D `clarity` puis `humanizer` | 0/2 | 1/2 | 0/2 | 0/2 | 1/8 | 12 % |

Les deux portes franchies, vérifiées à la main :
- **A-2 sur X2** : « Côté recherche, quatre résultats vont dans ce sens » suivi de trois puces. La source en cite trois ([2], [3], [4]) : le décompte est inventé. Confirmé.
- **D-1 sur X2** : « D'après le mutation testing, les suites écrites par des LLM ne détectent que 36 % des mutants [18] » (la source : « des suites écrites par LLM qui... »). L'article défini généralise. Confirmé. Le même essai écrit aussi « Six réglages ne présentent aucun risque » pour « sans regret » : renforcement que le juge a classé « mineur » et que je compte comme un second écart.

**Mon échantillon de contrôle** (17 sorties relues en entier : X1 A-1, B-1, B-2, C-1, C-2, D-1, D-2 ; X2 A-2, C-1, D-1 ; X3 A-2, B-1, C-1, D-1 ; X4 A-1, B-1, C-1 ; les autres par recherche ciblée) et contrôle mécanique des chiffres. Aucun chiffre ni renvoi [n] perdu ou changé dans les 32 sorties (le seul « manque », X1 B-2, est « 8 » écrit « Huit »). Là où je serais plus sévère que le juge :
- **« que je publie aujourd'hui »** dans X3 A-1, A-2 et C-2 : fait ajouté (la source dit « que je publie »). Classé « mineur » par le juge. Je le compte comme porte franchie : sans skill passe à 3 essais sur 8 (37 %, éliminé), `clarity` à 1 sur 8, `humanizer` reste à 0 sur 8, D à 1 sur 8 (inchangé).
- **« qui grossissent sans fin »** (X2 A-2) pour « qui enflent » : renforcement.
- **« Le résultat qui m'a le plus surpris »** (X1 D-1) pour « la vraie découverte » : réaction inventée. **« Je l'ajoute comme étape optionnelle »** (X1 B-1, D-1) : engagement non présent dans la source.
- **« Cette combinaison réduit les coûts »** pour « permet de réduire » (X3, 5 sorties) : léger durcissement, mineur partout.
- Le juge me paraît juste sur le reste. Il est cohérent sur le « 36 % » (seul D-1 emploie l'article défini ; C-2 et D-2 écrivent même « certaines suites »).

**Voix de X3** (hors décompte des portes) : « WOUPS » devient « OUPS » dans A-1, A-2, C-2 et D-2. Les exclamations passent de 7 dans la source à 6,5 (A), 3,5 (B), 3 (C) et 3 (D) en moyenne. Les emojis sont tous gardés sauf 👉 dans D-1. `humanizer` remplace la liste à puces par une phrase dans B-1 et B-2. Le juge note aussi la disparition de « ... » (suspense) et de plusieurs « ! » dans B-1. Les « je » restent à 21 à 26, comme la source (23) : personne n'a changé qui parle.

### Tics de surface (moyenne par condition, 4 textes)

| Condition | mots | mots/phrase | tirets | pas X mais Y | chutes | triades | triades en fin | gonflés | gras |
|---|---|---|---|---|---|---|---|---|---|
| A sans skill | 471,5 | 14,3 | 0,0 | 0,1 | 0,2 | 1,9 | 0,9 | 1,2 | 3,4 |
| B `humanizer` | 448,8 | 16,0 | 0,0 | 0,0 | 0,2 | 2,5 | 1,1 | 0,8 | 0,9 |
| C `clarity` | 449,8 | 14,7 | 0,0 | 0,0 | 0,2 | 2,2 | 0,9 | 1,0 | 3,0 |
| D les deux | 457,4 | 15,2 | 0,0 | 0,0 | 0,2 | 2,4 | 1,0 | 0,9 | 0,5 |

Sources, pour repère : 0 tiret sauf X4 (3), 0 « pas X mais Y », 0 à 1 chute, 0 à 2 triades. Somme « tirets + contrastes + chutes + triades en fin + gonflés » par texte (source : 1, 3, 2, 5 pour X1 à X4) : A 1, 3,5, 2,5, 3 ; B 0, 3, 2,5, 3 ; C 1, 2, 3,5, 2 ; D 0, 2,5, 3,5, 2,5. Écarts d'un demi-point, sans tendance. Toutes les conditions raccourcissent les phrases (X2 : 26 à 17 à 19 mots ; X4 : 28 à 13 à 15 mots) et rallongent le texte de 7 à 12 % (sans skill 12 %, `humanizer` 6,6 %, `clarity` 6,9 %, D 9 %). Les triades en fin de phrase ne baissent pas : les réécritures en créent parfois (X3 : 1 dans la source, 1 à 3 dans les sorties). Les détails par sortie sont dans `donnees/tableaux.md` et `donnees/tics.json`. Limite : les expressions sont des heuristiques (par exemple, les triades comptent aussi des énumérations légitimes).

### Coûts (par essai ; D inclut l'essai C)

| Condition | Coût ($) | Tours | Durée (s) | Tokens de sortie |
|---|---|---|---|---|
| A | 0,060 | 1,0 | 13 | 1 356 |
| B | 0,133 | 3,0 | 26 | 2 540 |
| C | 0,113 | 3,8 | 23 | 2 247 |
| D | 0,313 | 6,8 | 47 | 4 556 |

Dépense totale du test : environ 7,2 $ d'équivalent API (32 sorties et X1 : 4,15 $ ; 32 jugements : 2,95 $ ; essais de mise au point : 0,12 $), sous le budget de 8 $. Le premier essai de chaque série paie l'écriture du cache : les moyennes sont bruitées (X1 B-1 : 0,21 $, X1 B-2 : 0,05 $).

## 6. Critère de décision (la note tranchera)

1. Une condition est éliminée si une porte dure est franchie dans plus d'un essai sur quatre. Sur 8 essais, c'est à partir de 3. Avec le juge seul : aucune. Avec ma relecture : la condition A.
2. Parmi les autres, garder la meilleure note moyenne d'Anaël. D n'est retenue que si elle dépasse C et B d'au moins 0,5 point ; sinon la plus simple (A, puis C ou B selon le surcoût de 0,05 à 0,07 $ par essai, ou B pour la voix).
3. Pour dépouiller : `uv run python scripts/agreger.py --notes notation-t11.json` (croise l'export JSON avec `correspondance.json`, moyennes par condition et par critère). Pour X3, regarder aussi le critère « ma voix ».

## 7. Limites

- **Le texte de départ est déjà propre.** X1 est un brouillon d'Opus 5.5 : il contient peu de tics, donc `humanizer` a peu à corriger. Le cas X3 (écrit par un humain) n'a pas non plus de tirets ni de « pas X mais Y ». Cette série ne teste donc pas ce pour quoi `humanizer` est conçu (du texte plein de tics). Une série avec un brouillon chargé de tics répondrait mieux à la question « surface ».
- **2 essais par cellule, 8 par condition** : un essai de plus ou de moins change le taux de 12 points. Aucune différence de porte n'est significative.
- **Le juge est de la même famille que les rédacteurs** (Opus 5.5) et ne voit pas les autres sorties : son seuil « porte » est discutable (« aujourd'hui »). J'ai relu 17 sorties sur 32 en entier, pas toutes.
- **`clarity` mal sollicité** : en mode `rewrite` avec « rends seulement le texte », ni l'interview, ni les `[TK]`, ni `longform.md` n'ont joué, et la skill a été invoquée sur de la prose dont elle sait dire qu'elle est « creuse » sans pouvoir y remédier. Une comparaison en mode `review` n'a pas été faite.
- **Tics comptés par heuristiques** (français et anglais) : le gras et les exclamations sont plus fiables que les triades et les « pas X mais Y ».
- **X4** : un extrait de 314 mots, un article de recherche en anglais. Il teste surtout la préservation des faits : les écarts entre skills y sont de même ordre qu'en français (0 porte pour toutes les conditions).
- **Ordre des essais et cache** : coûts bruités. La durée dépend de la machine.

## 8. Ce qu'Anaël doit faire

1. Ouvrir `tests-pratiques/T11-ecriture/notation.html` (4 textes, 8 versions chacun, environ 20 min) et noter. Ne pas ouvrir `correspondance.json` avant.
2. Exporter le JSON (bouton en bas) et me le transmettre, ou lancer `uv run python scripts/agreger.py --notes <fichier>`.
3. Pour X3, noter aussi « ça sonne comme moi » : c'est la porte « voix » qui tranche.
4. Décider du seuil de la porte « aujourd'hui » (mineur pour le juge, porte pour moi) si la condition A te semble par ailleurs la meilleure.
5. Pour un texte nouveau (X5...) : déposer `textes/X5/source.md` et `lecteur.txt`, puis `uv run python scripts/preparer.py` et `uv run python scripts/relancer_nouveaux.py`. Les lettres déjà tirées ne changent pas. Il faut recloner les deux dépôts aux SHA ci-dessus dans le scratchpad (`scripts/config.py`) puisque les copies de travail ont été supprimées.

## 9. Fichiers

- `notation.html`, `correspondance.json` (hors dépôt).
- `textes/X1` à `X4` (sources, lecteurs, prompt et métriques de génération de X1) ; `textes/X3/source.md` est le fichier d'Anaël, inchangé.
- `sorties/<texte>/<condition>-<essai>.md`, `.meta.json` (coût, tours, skills invoquées, fichiers lus), `.flux.jsonl` (flux brut).
- `juge/<texte>/<condition>-<essai>.json`, `donnees/` (`tics.json`, `tableaux.md`, `resume.json`, `ecarts_juge.txt`, journaux).
- `securite/` : rapports SkillSpector, sha256 du PDF.
- `scripts/` : `config.py`, `lancer_claude.py`, `preparer.py`, `generer_x1.py` (X1 et X2), `extraire_x4.py`, `lancer_conditions.py`, `juge.py`, `mesurer_tics.py`, `tics_en.py`, `generer_notation.py`, `agreger.py`, `relancer_nouveaux.py`, `nettoyer.ps1`.

## 10. Synthèse en cinq lignes

1. Portes dures : `humanizer` 0/8, `clarity` 0/8, sans skill 1/8, les deux 1/8 (juge) ; ma relecture plus sévère élimine seulement la condition sans skill (« aujourd'hui » inventé).
2. Tics : presque rien à corriger dans les textes de départ ; `humanizer` retire le gras décoratif et les exclamations, `clarity` les garde, aucun ne réduit les triades.
3. Voix d'Anaël (X3) : `humanizer` garde « WOUPS » 2/2 mais fond la liste à puces ; sans skill 0/2.
4. Coût par essai : sans skill 0,06 $, `clarity` 0,11 $, `humanizer` 0,13 $, les deux 0,31 $ ; rien ne justifie de les enchaîner.
5. À faire : ta note à l'aveugle (`notation.html`) tranche entre sans skill, `humanizer` et `clarity` ; D n'est retenue que si elle dépasse les deux de 0,5 point.
