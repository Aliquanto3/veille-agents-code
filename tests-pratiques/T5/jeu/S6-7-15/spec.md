## Intent

**Problem:** l'écran `/chaine` de l'UI web n'a que le cadre commun (7.13) : le Pilote ne peut ni lancer la Chaîne, ni suivre ses 10 étapes, ni basculer en Mode repli depuis le navigateur (SCP du 2026-10-17, AD-8, AD-19, AD-25).

**Approach:** `ui/chaine.py` (`GestionChaine`, vit dans le processus serveur) démarre `usine rapport` en sous-processus, une Chaîne à la fois, et construit la vue `VueChaine` à chaque sondage ; `serveur.py` expose `GET/POST /api/chaine` et `POST /api/mode`, et tient le mode courant en mémoire ; `chaine.js` sonde chaque seconde et affiche étapes, barre, journal, bandeaux et boutons.

## Boundaries & Constraints

**Always:** `GestionChaine` reçue de `ui/cli.py` (AD-1) ; progression lue en ouvrir-lire-fermer (`progression.lire_progression`), fichier retrouvé par `fichier_nouveau` ; constantes `INTERVALLE_SONDAGE`, `LIGNES_ERREUR_MAX`, `LANCEMENT_REPLI` dans `textes.py` et réimportées par `app.py` ; boutons `aria-disabled="true"` (jamais `disabled`), motif visible lié par `aria-describedby` ; le mode de départ reste `USINE_MODE_REPLI`, il ne change que par `POST /api/mode` ; seules deux routes `POST` changent un état, aucune ne touche un Passage ni Jira ; pas d'`innerHTML` de données, pas de ressource externe.

**Never:** modifier `src/usine/contrats/` ou `src/usine/ports/` ; lancer une vraie Chaîne ou joindre Jira dans les tests ; bascule automatique du mode ; second lancement pendant une Chaîne.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Lancement | `POST /api/chaine`, Mode réel, racine présente | 202, `usine rapport` en sous-processus (`python -m usine rapport`, `cwd` racine), vue `en_cours`, boutons de lancement et de mode bloqués avec motif | démarrage en `OSError` : vue en `attente` avec `erreur` |
| Deuxième lancement | Chaîne en cours | 409, motif `MOTIF_LANCEMENT_EN_COURS`, aucun second processus | — |
| Mode repli ou racine absente | `POST /api/chaine` | 409, motif (`LANCEMENT_REPLI` sans marques, ou racine introuvable) | — |
| Suivi | sondage chaque seconde | étapes (état, durée), `terminees` = `aria-valuenow`, compteur « n / 10 », journal (récent en haut), annonce « Étape n sur 10 : … » | ligne finale partielle ignorée ; progression invalide : `erreur`, sondage maintenu |
| Reprise | retour sur `/chaine` en cours de Chaîne | même état, boutons bloqués | — |
| Fin réussie | code 0 | bandeau `status` « Chaîne terminée : Passage publié. » + lien « Voir la carte météo » ; bouton « Relancer la Chaîne » ; l'en-tête prend le nouveau Passage | — |
| Échec | code ≠ 0 | étape « Échec », bandeau `alert` : étape (ou « hors d'une étape »), code, au plus 20 dernières lignes d'erreur, `AUCUN_RAPPORT` ; le Passage affiché ailleurs ne change pas | sans sortie d'erreur : « aucun message » |
| Annonces | région `status` | change d'étape, fin, échec ; jamais à chaque sondage, ni entre deux étapes | — |
| Bascule | `POST /api/mode` `{"mode": "repli"\|"reel"}` | 200, `VueCadre` du nouveau mode ; tous les écrans lisent la copie ou le dernier Passage réel | 409 pendant une Chaîne ; 422 corps invalide ; 403 origine étrangère ; copie absente : `REPLI_ABSENT` dans le cadre, bouton de retour utilisable |

</intent-contract>

## Code Map

- `src/usine/ui/chaine.py` -- `GestionChaine` (`lancer`, `vue`, `en_cours`, verrou), `LancementRefuse`, `DESCRIPTIONS` des 10 étapes, libellés et motifs, `vue_dernier_passage`.
- `src/usine/ui/vues.py` -- `VueChaine`, `VueEtape`, `VueBouton`, `VueBandeauChaine`, `VueLigneJournal`, `VueDernierPassage`, `DemandeMode`.
- `src/usine/ui/serveur.py` -- mode en mémoire (`_Mode`), `/api/chaine` (GET, POST), `/api/mode` (POST), refus d'origine étrangère (`_meme_origine`).
- `src/usine/ui/cli.py` -- `application_web` fournit `GestionChaine(racine)`.
- `src/usine/ui/textes.py`, `app.py` -- constantes déplacées, `app.X` conservé.
- `src/usine/ui/statique/` -- `chaine.html`, `chaine.js`, `envoyer` et `rafraichirCadre` de `cadre.js`, styles de `cadre.css`.
- `tests/unit/ui/test_chaine.py` -- doublure de sous-processus et progression synthétique ; `docs/tests-manuels.md` -- 3.8.

## Tasks & Acceptance

**Execution:**
- Vues, `GestionChaine`, routes, composition (`cli`).
- Page, script, styles.
- Tests avec TestClient, `docs/tests-manuels.md` 3.8.

**Acceptance Criteria:**
- Given `/chaine`, when le Pilote clique sur le lancement, then `usine rapport` démarre en sous-processus, une Chaîne à la fois, et l'état se sonde chaque seconde.
- Given une Chaîne en cours, when on quitte puis rouvre `/chaine`, then le suivi reprend et les deux boutons restent `aria-disabled="true"` avec leur motif.
- Given une étape en échec, then « Échec », étape, code et au plus 20 lignes d'erreur ; le Passage affiché ailleurs est inchangé.
- Given la barre, then `aria-valuenow` = étapes terminées ; la région `status` n'annonce que changements d'étape, fin et échec.
- Given le bouton de mode, then bascule vers `demo/repli/passage/` et retour au dernier Passage réel ; `REPLI_ABSENT` si la copie manque ; jamais de bascule automatique.

## Design Notes

**Le bouton « Lancer la Chaîne » de l'en-tête** reste un lien vers `/chaine` qui ne lance rien (EXPERIENCE.md, Information Architecture) : inchangé, absent de `/chaine`.

**Écritures.** Le mode est un attribut du processus serveur, changé par `POST /api/mode` seul, refusé pendant une Chaîne. Un `POST` sans corps JSON (lancement) est une « requête simple » que n'importe quelle page ouverte dans le navigateur pourrait émettre : `TrustedHostMiddleware` limite `Host` à `127.0.0.1` et `localhost` sur toutes les routes (DNS rebinding : 400), et `_meme_origine` refuse un `Origin` présent qui ne nomme pas ce même hôte et ce même port (403). Bascule et lancement passent par un verrou d'écriture commun.

**Annonces.** Le serveur calcule le texte (`annonce`), vide quand rien de nouveau n'est à dire ; le script ne remplace le texte de la région que s'il diffère du précédent, donc le lecteur d'écran n'entend ni sondage, ni répétition.

**Un seul verrou.** Le lancement, la lecture de l'état et du fichier d'erreurs passent par un `threading.Lock` : deux clics quasi simultanés ne démarrent qu'un processus.

