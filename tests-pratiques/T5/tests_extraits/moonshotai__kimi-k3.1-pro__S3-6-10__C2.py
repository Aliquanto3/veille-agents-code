from pathlib import Path

import pytest

from tests.unit.chaine import test_execution as execution
from tests.unit.chaine.environnement import preparer_racine
from usine import composition
from usine.contrats.erreurs import UsineErreur


class EchecAuPremierAppel(execution.FournisseurPalier2):
    def __init__(self) -> None:
        super().__init__()
        self.recus = 0

    def generer_structure(self, *args, **kwargs):
        self.recus += 1
        if self.recus == 1:
            raise UsineErreur("échec fournisseur de test")
        return super().generer_structure(*args, **kwargs)


def test_bilan_compte_aussi_un_appel_frais_en_echec(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("USINE_CLE_PSEUDO", "cle-de-test-fictive")
    racine = preparer_racine(tmp_path)
    execution._passer_en_palier_2(racine)
    fournisseur = EchecAuPremierAppel()

    bilan = composition.prechauffer_classification(
        racine, execution.DATE_ARRETE, 1e9, fournisseur=fournisseur
    )

    assert fournisseur.recus > 0
    assert bilan.appels == fournisseur.recus
