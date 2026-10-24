import os
from pathlib import Path

from usine.ui.progression import fichier_nouveau, fichiers_progression


def test_premier_fichier_apparu_et_non_premier_nom(tmp_path: Path) -> None:
    repertoire = tmp_path / "sorties" / "progression"
    repertoire.mkdir(parents=True)
    avant = fichiers_progression(tmp_path)

    premier = repertoire / "20261012T073000Z-ffffff.jsonl"
    premier.write_text("", encoding="utf-8")
    os.utime(premier, ns=(1_000_000_000, 1_000_000_000))

    second = repertoire / "20261012T073000Z-aaaaaa.jsonl"
    second.write_text("", encoding="utf-8")
    os.utime(second, ns=(2_000_000_000, 2_000_000_000))

    assert fichier_nouveau(avant, tmp_path) == premier
