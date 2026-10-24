import json

from outils.balayer_sm7 import balayer


def test_balayage_detecte_un_identifiant_echappe_dans_une_trace_jsonl() -> None:
    valeur = "Élodie Fictivia"
    ligne_jsonl = json.dumps({"texte": valeur})  # json.dumps échappe É par défaut

    bilan = balayer([("trace/llm.jsonl:1", ligne_jsonl)], [("CLIENT", valeur)])

    assert [(f.source, f.type, f.valeur) for f in bilan.fuites] == [
        ("trace/llm.jsonl:1", "CLIENT", valeur)
    ]