from datetime import UTC, datetime

from usine.contrats.passage import Etape, EvenementProgression, StatutEtape
from usine.ui.chaine import GestionChaine


def test_attente_ne_reprend_pas_une_ancienne_progression(tmp_path):
    dossier = tmp_path / 'sorties' / 'progression'
    dossier.mkdir(parents=True)
    evenement = EvenementProgression(
        passage_id='20261012T073000Z-aaaaaa',
        etape=Etape.extraction,
        statut=StatutEtape.en_cours,
        horodatage=datetime(2026, 10, 12, 7, 30, tzinfo=UTC),
    )
    (dossier / '20261012T073000Z-aaaaaa.jsonl').write_text(
        evenement.model_dump_json() + '\n', encoding='utf-8'
    )

    vue = GestionChaine(tmp_path).vue(False, None)

    assert vue.statut == 'attente'
    assert all(etape.etat == 'en_attente' for etape in vue.etapes)
    assert vue.journal == []
