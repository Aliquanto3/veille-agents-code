import pytest

from usine.adaptateurs.pseudonymisation import MOTIFS_PAR_DEFAUT, PseudonymiseurHmac


class TableMemoire:
    def __init__(self):
        self.valeurs = {}

    def enregistrer(self, correspondances):
        self.valeurs.update(correspondances)

    def lire(self, jetons):
        return {jeton: self.valeurs[jeton] for jeton in jetons if jeton in self.valeurs}


@pytest.mark.parametrize('prefixe,suffixe', [('IBAN', ''), ('', 'abc')])
def test_reidentifier_jeton_genere_sans_separateur(prefixe, suffixe):
    compte = 'FR76 3000 6000 0112 3456 7890 189'
    texte = prefixe + compte + suffixe
    pseudo = PseudonymiseurHmac(
        b'cle-fictive-de-test-assez-longue',
        MOTIFS_PAR_DEFAUT,
        TableMemoire(),
    )
    pseudonymise = pseudo.pseudonymiser(texte)
    assert compte not in pseudonymise
    assert pseudo.reidentifier(pseudonymise) == texte
