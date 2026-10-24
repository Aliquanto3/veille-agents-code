import json
from pathlib import Path

from outils.balayer_sm7 import CHEMIN_TRACES_LLM, main


def test_fuite_iban_avec_tabulations_dans_une_trace_json(tmp_path: Path) -> None:
    iban = "FR46 9999 9143 2694 4104 2320 086"
    iban_avec_tabulations = iban.replace(" ", "\t")
    passage = tmp_path / "passage"
    traces = passage / CHEMIN_TRACES_LLM
    traces.parent.mkdir(parents=True)
    traces.write_text(
        json.dumps({"entree_pseudonymisee": f"compte {iban_avec_tabulations} débité"})
        + "\n",
        encoding="utf-8",
    )
    identifiants = tmp_path / "identifiants_injectes.json"
    identifiants.write_text(
        json.dumps([{"type": "COMPTE", "valeur": iban}]), encoding="utf-8"
    )

    assert main(
        ["--passage", str(passage), "--identifiants", str(identifiants)]
    ) == 1
