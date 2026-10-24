import json

import pytest

from outils.balayer_sm7 import CHEMIN_TRACES_LLM, main


@pytest.mark.parametrize('separateur', ['\u00a0', '\t'])
def test_fuite_iban_dans_une_trace_json_avec_blancs_echappes(tmp_path, separateur):
    iban = 'FR46 9999 9143 2694 4104 2320 086'
    passage = tmp_path / 'passage'
    trace = passage / CHEMIN_TRACES_LLM
    trace.parent.mkdir(parents=True)
    trace.write_text(
        json.dumps({'entree_pseudonymisee': iban.replace(' ', separateur)}, ensure_ascii=True) + '\n',
        encoding='utf-8',
    )
    identifiants = tmp_path / 'identifiants_injectes.json'
    identifiants.write_text(
        json.dumps([{'type': 'COMPTE', 'valeur': iban}]),
        encoding='utf-8',
    )

    assert main([
        '--passage', str(passage),
        '--identifiants', str(identifiants),
    ]) == 1
