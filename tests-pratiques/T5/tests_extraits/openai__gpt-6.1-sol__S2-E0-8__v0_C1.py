from pathlib import Path
import time

from usine.ui.progression import fichier_nouveau, fichiers_progression


def test_suit_le_premier_fichier_apparu_dans_la_meme_seconde(tmp_path: Path) -> None:
    repertoire = tmp_path / "sorties" / "progression"
    repertoire.mkdir(parents=True)
    avant = fichiers_progression(tmp_path)

    premier = repertoire / "20261012T073000Z-bbbbbb.jsonl"
    premier.write_text("", encoding="utf-8")
    time.sleep(0.05)
    second = repertoire / "20261012T073000Z-aaaaaa.jsonl"
    second.write_text("", encoding="utf-8")

    assert fichier_nouveau(avant, tmp_path) == premier
