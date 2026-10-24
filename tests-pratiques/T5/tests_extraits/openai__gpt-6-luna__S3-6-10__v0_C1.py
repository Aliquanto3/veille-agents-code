import json
from pathlib import Path

from outils.balayer_sm7 import CHEMIN_TRACES_LLM, main


def test_identifiant_vide_retourne_code_erreur_sans_exception(
    tmp_path: Path,
) -> None:
    passage = tmp_path / "passage"
    traces = passage / CHEMIN_TRACES_LLM
    traces.parent.mkdir(parents=True)
    traces.write_text("{}\n", encoding="utf-8")

    identifiants = tmp_path / "identifiants.json"
    identifiants.write_text(
        json.dumps([{"type": "CLIENT", "valeur": ""}]), encoding="utf-8"
    )

    assert main(
        ["--passage", str(passage), "--identifiants", str(identifiants)]
    ) == 2