from datetime import UTC, datetime
from io import BytesIO

from usine.contrats.passage import Etape, EvenementProgression, StatutEtape
from usine.ui import lancement
from usine.ui.chaine import GestionChaine


class Processus:
    def __init__(self):
        self.code = None

    def poll(self):
        return self.code


def test_sortie_anormale_marque_l_etape_interrompue_en_echec(tmp_path, monkeypatch):
    processus = Processus()
    monkeypatch.setattr(lancement, 'fichier_erreurs', lambda: BytesIO())
    monkeypatch.setattr(lancement, 'lancer_chaine', lambda *args, **kwargs: processus)
    monkeypatch.setattr(lancement, 'lire_erreurs', lambda fichier: '')
    gestion = GestionChaine(tmp_path)
    gestion.lancer(False)

    dossier = tmp_path / 'sorties' / 'progression'
    dossier.mkdir(parents=True, exist_ok=True)
    evenement = EvenementProgression(
        passage_id='20261012T073000Z-aaaaaa',
        etape=Etape.extraction,
        statut=StatutEtape.en_cours,
        horodatage=datetime(2026, 10, 12, 7, 30, tzinfo=UTC),
    )
    (dossier / '20261012T073000Z-aaaaaa.jsonl').write_text(
        evenement.model_dump_json() + '\n', encoding='utf-8'
    )
    processus.code = -9

    vue = gestion.vue(False, None)

    assert vue.statut == 'echec'
    assert vue.etapes[0].etat == 'echouee'
    assert vue.etapes[0].libelle_etat == 'Échec'
