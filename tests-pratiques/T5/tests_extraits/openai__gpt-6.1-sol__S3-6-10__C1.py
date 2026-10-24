import json
import sqlite3

import pytest

from outils.balayer_sm7 import CHEMIN_TRACES_LLM, main


@pytest.mark.parametrize("source", ["trace", "cache"])
@pytest.mark.parametrize("separateur", ["\u00a0", "\n"])
def test_iban_echappe_dans_json_detecte(tmp_path, source, separateur):
    iban = "FR46 9999 9143 2694 4104 2320 086"
    identifiants = tmp_path / "identifiants.json"
    identifiants.write_text(
        json.dumps([{"type": "COMPTE", "valeur": iban}]),
        encoding="utf-8",
    )
    passage = tmp_path / "passage"
    traces = passage / CHEMIN_TRACES_LLM
    traces.parent.mkdir(parents=True)
    contenu = json.dumps({"entree_pseudonymisee": iban.replace(" ", separateur)})
    traces.write_text((contenu if source == "trace" else "{}") + "\n", encoding="utf-8")
    arguments = ["--passage", str(passage), "--identifiants", str(identifiants)]
    if source == "cache":
        cache = tmp_path / "cache.sqlite"
        with sqlite3.connect(cache) as connexion:
            connexion.execute("CREATE TABLE cache_llm (cle TEXT PRIMARY KEY, brut TEXT NOT NULL)")
            connexion.execute("INSERT INTO cache_llm VALUES (?, ?)", ("test", contenu))
        arguments += ["--cache", str(cache)]
    assert main(arguments) == 1
