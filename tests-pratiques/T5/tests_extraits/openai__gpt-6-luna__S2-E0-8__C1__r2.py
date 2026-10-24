from pathlib import Path
import os

from usine.ui.progression import fichier_nouveau, fichiers_progression


def test_suit_le_premier_fichier_apparu(tmp_path: Path) -> None:
    repertoire = tmp_path / "sorties" / "progression"
    repertoire.mkdir(parents=True)
    avant = fichiers_progression(tmp_path)

    premier = repertoire / "20261012T080000Z-aaaaaa.jsonl"
    second = repertoire / "20261012T070000Z-bbbbbb.jsonl"
    premier.write_text("", encoding="utf-8")
    second.write_text("", encoding="utf-8")
    os.utime(premier, ns=(1_000_000_000, 1_000_000_000))
    os.utime(second, ns=(2_000_000_000, 2_000_000_000))

    assert fichier_nouveau(avant, tmp_path) == premier