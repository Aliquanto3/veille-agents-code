from datetime import UTC, datetime
from pathlib import Path

from usine.contrats.passage import Etape, EvenementProgression, StatutEtape
from usine.ui.chaine import GestionChaine


def test_ne_pas_afficher_la_progression_d_un_lancement_anterieur(tmp_path: Path) -> None:
    repertoire = tmp_path / "sorties" / "progression"
    repertoire.mkdir(parents=True)
    evenement = EvenementProgression(
        passage_id="20261012T073000Z-aaaaaa",
        etape=Etape.extraction,
        statut=StatutEtape.reussie,
        horodatage=datetime(2026, 10, 12, 7, 30, tzinfo=UTC),
    )
    (repertoire / "20261012T073000Z-aaaaaa.jsonl").write_text(
        evenement.model_dump_json() + "\n", encoding="utf-8"
    )

    vue = GestionChaine(tmp_path).vue(False, None)

    assert vue.statut == "attente"
    assert vue.terminees == 0
    assert vue.journal == []