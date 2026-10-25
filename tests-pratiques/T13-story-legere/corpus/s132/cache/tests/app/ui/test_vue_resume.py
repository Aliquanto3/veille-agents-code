"""Story 13.2 : vue Résumé à trois longueurs, dans Edge avec un pont factice.

Marqués `ui`. Chaînes factices (D1).
"""

from __future__ import annotations

import functools
import http.server
import threading
from collections.abc import Iterator
from pathlib import Path

import pytest

playwright_sync = pytest.importorskip("playwright.sync_api")

pytestmark = pytest.mark.ui

UI = Path(__file__).resolve().parents[3] / "src" / "slmsp" / "app" / "ui"
FIN = {"type": "fin", "raison": "terminee", "usage": None, "urls_inventees": []}
DOC = "<document-factice-1> <document-factice-2>"
RESUME = "<résumé-factice-1>"


class _Silencieux(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture(scope="module")
def base() -> Iterator[str]:
    gestionnaire = functools.partial(_Silencieux, directory=str(UI))
    serveur = http.server.ThreadingHTTPServer(("127.0.0.1", 0), gestionnaire)
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{serveur.server_port}/index.html"
    serveur.shutdown()
    serveur.server_close()


@pytest.fixture(scope="module")
def navigateur() -> Iterator[object]:
    with playwright_sync.sync_playwright() as p:
        try:
            nav = p.chromium.launch(channel="msedge", headless=True)
        except Exception as erreur:
            pytest.skip(f"Edge indisponible : {erreur}")
        yield nav
        nav.close()


@pytest.fixture
def page(navigateur, base) -> Iterator[object]:
    contexte = navigateur.new_context(viewport={"width": 1280, "height": 800})
    contexte.add_init_script(
        "try { localStorage.setItem('slmsp.bienvenue-vue', 'true'); } catch {}"
    )
    p = contexte.new_page()
    p.set_default_timeout(90_000)
    p.requetes = []
    p.on("request", lambda r: p.requetes.append(r.url))
    p.goto(base + "?pont=factice")
    p.wait_for_function("() => window.slmsp !== undefined", polling=50)
    p.evaluate(
        """(fin) => {
          window.__appels = [];
          window.__refus = null;
          const pont = window.slmsp.pont;
          pont.envoyer = async (tache, messages, options) => {
            window.__appels.push(['envoyer', tache, messages, options]);
            if (window.__refus) return window.__refus;
            window.slmsp.bus.emettre('generation:debut', { tache });
            setTimeout(() => window.slmspRecevoir([
              { type: 'jeton', texte: '<résumé-factice-1>' }, fin]), 20);
            return { ok: true };
          };
        }""",
        FIN,
    )
    page_prete = p
    page_prete.evaluate("window.slmspRecevoir({type: 'pret'})")
    page_prete.evaluate("(t) => window.slmsp.activer(t)", "RE")
    yield page_prete
    p.context.close()


def _resumer(page) -> None:
    page.fill("#redaction-saisie-RE", DOC)
    page.locator("#vue-RE .volet-pied .bouton-primaire").click()


def _options(page) -> dict:
    return page.evaluate("window.__appels.at(-1)[3]")


def test_vue_disponible_trois_longueurs_moyenne_par_defaut(page) -> None:
    vue = page.locator("#vue-RE")
    assert "non disponible" not in vue.inner_text()
    assert vue.locator(".volet-pied .bouton-primaire").inner_text() == "Résumer"
    libelles = vue.locator(".choix-option span").all_inner_texts()
    assert libelles == ["Court", "Moyen", "Détaillé"]
    assert vue.locator("input[type=radio]:checked").get_attribute("value") == "moyenne"


@pytest.mark.parametrize(
    ("libelle", "valeur"), [("Court", "courte"), ("Moyen", "moyenne"), ("Détaillé", "detaillee")]
)
def test_longueur_choisie_dans_l_entree_du_harnais(page, libelle: str, valeur: str) -> None:
    page.locator("#vue-RE .choix-option", has_text=libelle).click()
    _resumer(page)
    page.wait_for_function(
        "() => !document.querySelector('#vue-RE .resultat-actions').hidden", polling=50
    )
    assert _options(page) == {"entree": {"document": DOC, "longueur_demandee": valeur}}
    assert page.evaluate("window.__appels.at(-1)[1]") == "RE"
    assert page.locator("#vue-RE .resultat").inner_text() == RESUME


def _message_visible(page) -> bool:
    return page.locator("#vue-RE .mention-trop-longue").is_visible()


def test_document_au_dessus_du_plafond_affiche_le_message_sans_envoi(page) -> None:
    page.fill("#redaction-saisie-RE", "mot " * 4001)
    page.locator("#vue-RE .volet-pied .bouton-primaire").click()
    page.locator("#vue-RE .mention-trop-longue").wait_for(state="visible")
    assert "trop long" in page.locator("#vue-RE .mention-trop-longue").inner_text()
    assert page.evaluate("window.__appels.length") == 0
    # Un document ramené sous le plafond est envoyé et efface le message.
    page.fill("#redaction-saisie-RE", "mot " * 4000)
    page.locator("#vue-RE .volet-pied .bouton-primaire").click()
    page.wait_for_selector("#vue-RE .mention-trop-longue", state="hidden")
    assert page.evaluate("window.__appels.length") == 1


@pytest.mark.parametrize("code", ["requete-invalide", "generation-en-cours"])
def test_refus_du_pont_n_affiche_pas_le_message_trop_long(page, code: str) -> None:
    page.evaluate(
        "(c) => { window.__refus = {ok: false, erreur: {code: c, message: '<refus>'}}; }", code
    )
    _resumer(page)
    page.wait_for_function("() => window.__appels.length === 1", polling=50)
    assert not _message_visible(page)


def test_rejet_de_envoyer_affiche_le_message_generique(page) -> None:
    page.evaluate(
        """() => {
          window.slmsp.pont.envoyer = async () => { throw new Error('<rejet-factice>'); };
        }"""
    )
    _resumer(page)
    page.locator("#vue-RE .mention-echec").wait_for(state="visible")
    assert "pas pu être produit" in page.locator("#vue-RE .mention-echec").inner_text()
    assert not _message_visible(page)


def test_aucune_ressource_externe(page) -> None:
    assert all(u.startswith(("http://127.0.0.1", "data:")) for u in page.requetes)
