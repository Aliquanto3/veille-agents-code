from pathlib import Path
import time

from usine.ui.progression import fichier_nouveau, fichiers_progression


def test_suit_le_premier_fichier_apparu(tmp_path: Path) -> None:
    repertoire = tmp_path / "sorties" / "progression"
    repertoire.mkdir(parents=True)
    avant = fichiers_progression(tmp_path)

    premier = repertoire / "20261013T070000Z-aaaaaa.jsonl"
    premier.touch()
    time.sleep(0.05)
    second = repertoire / "20261012T070000Z-bbbbbb.jsonl"
    second.touch()
    assert premier.stat().st_ctime_ns < second.stat().st_ctime_ns

    assert fichier_nouveau(avant, tmp_path) == premier
