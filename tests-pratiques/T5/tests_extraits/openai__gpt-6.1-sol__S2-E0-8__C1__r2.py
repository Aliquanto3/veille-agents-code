import os

from usine.ui.progression import fichier_nouveau, fichiers_progression


def test_premier_fichier_apparu_dans_la_meme_seconde(tmp_path):
    repertoire = tmp_path / "sorties" / "progression"
    repertoire.mkdir(parents=True)
    avant = fichiers_progression(tmp_path)

    premier = repertoire / "20261012T073000Z-ffffff.jsonl"
    premier.write_text("", encoding="utf-8")
    os.utime(premier, ns=(1791790200100000000, 1791790200100000000))

    second = repertoire / "20261012T073000Z-aaaaaa.jsonl"
    second.write_text("", encoding="utf-8")
    os.utime(second, ns=(1791790200200000000, 1791790200200000000))

    assert fichier_nouveau(avant, tmp_path) == premier
