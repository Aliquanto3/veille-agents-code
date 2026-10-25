# Story 9.1 : le lanceur ouvre l'application dans le navigateur

## Objectif

`uv run wavelocalai-v2` (et `wavelocalai` après la 8.4) ouvre le navigateur par défaut sur l'application, une fois le serveur réellement prêt, sans jamais perturber les tests, la CI ni les E2E (gouverné par AD-23).

## Critères d'acceptation et preuves

1. **Ouverture unique, après que le port répond** : `_open_browser_when_ready` (`src/wavelocalai/__main__.py`) sonde le port par une vraie connexion TCP (`_port_is_open`), jamais par un délai fixe, dans un fil dédié démarré juste avant `serve(...)`. Preuve : `tests/v2/unit/test_browser_open.py::test_opens_once_after_the_port_is_ready_never_before` — `webbrowser.open` n'est pas appelé tant que rien n'écoute sur le port, puis appelé une seule fois dès qu'un socket se met à écouter.
2. **`--no-browser` et `[server] open_browser = false`** : nouvelle option CLI `--no-browser` et nouveau réglage `ServerSettings.open_browser` (défaut `true`, `src/wavelocalai/config.py`). `main()` ne lance le fil de guet que si `not args.no_browser and settings.server.open_browser`. Preuve : `test_no_browser_flag_skips_the_guard` et `test_open_browser_false_setting_skips_the_guard` (le fil n'est jamais créé, via un espion qui remplace `threading.Thread` seulement dans `__main__`).
3. **Les tests, la CI et les E2E ne lancent jamais de navigateur** : revue de toutes les façons dont `tests/v2` démarre un vrai serveur en sous-processus (`python -m wavelocalai`) — `tests/v2/web/test_real_launch.py`, `tests/v2/web/test_real_shutdown.py`, `tests/v2/e2e/conftest.py` (`Backend.start`) — chacune reçoit désormais `--no-browser`. Les tests `tests/v2/web` et `tests/v2/unit` qui passent par `create_app`/`TestClient` ou qui s'arrêtent avant `serve()` (port occupé, verrou pris, réglages invalides) n'atteignent jamais le fil de guet : aucun changement nécessaire là.
4. **Échec d'ouverture** : si `webbrowser.open` renvoie `False` ou lève, l'URL est écrite sur la console (`stderr`) et dans le journal (`logger.warning`/`logger.exception`), et la fonction revient sans exception : le serveur, déjà lancé dans le fil principal, continue. Preuve : `test_failed_open_writes_the_url_to_console_and_log`, `test_open_exception_is_caught_and_logged_without_crashing`.

## Contrat partagé

- Réglage `[server] open_browser` (booléen, défaut `true`), documenté dans `wavelocalai.toml` (commentaire à côté de `port`) et dans le README (section de lancement de la v2, à côté de `--port`/`--data-dir`/`--config`).

## Fichiers

- Code : `src/wavelocalai/__main__.py` (option `--no-browser`, `_port_is_open`, `_open_browser_when_ready`, câblage dans `main`), `src/wavelocalai/config.py` (`ServerSettings.open_browser`).
- Doc : `wavelocalai.toml`, `README.md`.
- Tests : `tests/v2/unit/test_browser_open.py` (nouveau) ; `tests/v2/web/test_real_launch.py`, `tests/v2/web/test_real_shutdown.py`, `tests/v2/e2e/conftest.py` (`--no-browser` ajouté aux lancements en sous-processus).
