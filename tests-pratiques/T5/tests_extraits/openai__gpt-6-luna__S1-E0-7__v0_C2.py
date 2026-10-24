import json
from datetime import UTC, date, datetime
from types import SimpleNamespace

from pydantic import BaseModel

from usine.contrats.llm import ParametresAppel, StatutControle, Tache
from usine.ia.passerelle import ContexteAppel, Controle, Passerelle


COMPTE = "FR76 3000 6000 0112 3456 7890 189"
JETON = "COMPTE_abcdef"


class Sortie(BaseModel):
    texte: str


class Pseudonymiseur:
    def pseudonymiser(self, texte: str) -> str:
        return texte.replace(COMPTE, JETON)

    def reidentifier(self, texte: str) -> str:
        return texte.replace(JETON, COMPTE)


class Cache:
    def lire(self, cle: str) -> str | None:
        return None

    def ecrire(self, cle: str, brut: str) -> None:
        pass


class Fournisseur:
    version_modele = "factice:v1"

    def generer_structure(self, entree, schema, parametres):
        brut = json.dumps({"texte": COMPTE})
        return SimpleNamespace(
            sortie=schema.model_validate_json(brut),
            brut=brut,
            jetons_entree=1,
            jetons_sortie=1,
            version_modele=self.version_modele,
        )


def test_trace_ne_contient_pas_une_donnee_en_clair_retournee_par_le_fournisseur() -> None:
    passerelle = Passerelle(
        Fournisseur(), Pseudonymiseur(), Cache(), lambda: datetime(2025, 1, 1, tzinfo=UTC)
    )
    contexte = ContexteAppel(
        passage_id="passage-1",
        date_arrete=date(2025, 1, 1),
        cible="ENT-1",
        version_prompt="prompt-v1",
        version_grille="grille-v1",
        version_donnees="donnees-v1",
        entite="ENT-1",
    )

    resultat = passerelle.executer_structure(
        f"Compte {COMPTE}",
        Sortie,
        ParametresAppel(tache=Tache.explication, max_jetons_sortie=10, tentative=0),
        contexte,
        lambda reponse: Controle(reponse, StatutControle.conforme),
    )

    assert COMPTE not in resultat.trace.model_dump_json()
