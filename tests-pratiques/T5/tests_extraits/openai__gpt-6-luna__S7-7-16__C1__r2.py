import pytest

from usine.ui.ecrans import GardeSession, SessionIndisponible


class ConsultationFactice:
    passage_id = "passage-1"

    def manifeste(self):
        return self


def test_echec_de_construction_de_session_est_indisponible() -> None:
    def construire(_consultation):
        raise RuntimeError("échec pendant l'initialisation")

    garde = GardeSession(construire)
    with pytest.raises(SessionIndisponible):
        garde.repondre(ConsultationFactice(), "Question ?")