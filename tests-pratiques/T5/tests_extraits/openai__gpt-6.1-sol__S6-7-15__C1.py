from datetime import UTC, datetime

from usine.contrats.passage import Etape, EvenementProgression, StatutEtape
from usine.ui.chaine import GestionChaine


def test_attente_ignore_la_progression_d_un_ancien_lancement(tmp_path):
    repertoire = tmp_path / "sorties" / "progression"
    repertoire.mkdir(parents=True)
    passage_id = "20261012T073000Z-aaaaaa"
    lignes = [
        EvenementProgression(
            passage_id=passage_id,
            etape=Etape.extraction,
            statut=statut,
            horodatage=datetime(2026, 10, 12, 7, 30, seconde, tzinfo=UTC),
        ).model_dump_json()
        for seconde, statut in enumerate(
            (StatutEtape.en_cours, StatutEtape.reussie)
        )
    ]
    (repertoire / f"{passage_id}.jsonl").write_text(
        "\n".join(lignes) + "\n", encoding="utf-8"
    )

    gestion = GestionChaine(tmp_path)
    vue = gestion.vue(False, None)

    assert vue.statut == "attente"
    assert vue.terminees == 0
    assert all(etape.etat == "en_attente" for etape in vue.etapes)
    assert vue.journal == []
