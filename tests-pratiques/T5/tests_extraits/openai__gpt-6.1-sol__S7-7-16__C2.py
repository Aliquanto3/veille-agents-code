from html.parser import HTMLParser

from usine.ui.outillage import rendre_fiche


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.sources.append(dict(attrs).get("src"))


def test_fiche_ne_charge_pas_image_distante():
    url = "https://externe.example/image.png"
    analyse = Images()
    analyse.feed(rendre_fiche(f"## Illustration\n\n![illustration]({url})\n"))

    assert url not in analyse.sources
