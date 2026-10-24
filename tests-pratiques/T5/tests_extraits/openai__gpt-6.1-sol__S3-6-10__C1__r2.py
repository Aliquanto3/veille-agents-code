import json

from outils.balayer_sm7 import CHEMIN_TRACES_LLM, main


def test_iban_avec_blancs_echappes_dans_trace_json(tmp_path):
    iban = "FR46 9999 9143 2694 4104 2320 086"
    identifiants = tmp_path / "identifiants.json"
    identifiants.write_text(
        json.dumps([{"type": "COMPTE", "valeur": iban}]),
        encoding="utf-8",
    )
    passage = tmp_path / "passage"
    trace = passage / CHEMIN_TRACES_LLM
    trace.parent.mkdir(parents=True)
    trace.write_text(
        json.dumps(
            {"entree_pseudonymisee": iban.replace(" ", "\u00a0")},
            ensure_ascii=True,
        ) + "\n",
        encoding="utf-8",
    )

    assert main([
        "--passage", str(passage),
        "--identifiants", str(identifiants),
    ]) == 1
