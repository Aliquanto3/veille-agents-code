from datetime import UTC, datetime

from usine.contrats.passage import Etape, EvenementProgression, StatutEtape
from usine.ui.chaine import GestionChaine


def test_aucune_progression_historique_avant_un_lancement(tmp_path):
    passage_id = "20261012T073000Z-aaaaaa"
    repertoire = tmp_path / "sorties" / "progression"
    repertoire.mkdir(parents=True)
    evenement = EvenementProgression(
        passage_id=passage_id,
        etape=Etape.extraction,
        statut=StatutEtape.reussie,
        horodatage=datetime(2026, 10, 12, 7, 30, tzinfo=UTC),
    )
    (repertoire / f"{passage_id}.jsonl").write_text(
        evenement.model_dump_json() + "\n", encoding="utf-8"
    )

    vue = GestionChaine(tmp_path).vue(False, None)

    assert vue.statut == "attente"
    assert vue.terminees == 0
    assert all(etape.etat == "en_attente" for etape in vue.etapes)
    assert vue.journal == []
