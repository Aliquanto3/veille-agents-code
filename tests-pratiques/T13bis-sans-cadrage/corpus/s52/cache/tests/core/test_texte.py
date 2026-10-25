"""Tests de `slmsp.core.texte` (story 5.2) : règles v1, Kandel-Moles, isolement, verrou de version.

Toutes les fixtures sont des phrases courtes et artificielles écrites pour ces tests.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
import unicodedata
from decimal import Decimal
from pathlib import Path

import pytest

from slmsp.core.texte import (
    VERSION_TEXTE,
    compter_mots,
    decouper_phrases,
    extraire_nombres,
    kandel_moles,
    ngrammes,
    normaliser,
    syllabes,
)

CHEMIN_TEXTE = Path(__file__).resolve().parents[2] / "src" / "slmsp" / "core" / "texte.py"
NOMS_PUBLICS = {
    "VERSION_TEXTE",
    "normaliser",
    "compter_mots",
    "decouper_phrases",
    "extraire_nombres",
    "syllabes",
    "kandel_moles",
    "ngrammes",
}

# --- normaliser ------------------------------------------------------------------------------


def test_normaliser_exemple() -> None:
    assert normaliser("  L\u2019Usager,  DOIT\u00a0payer ! ") == "l usager doit payer"


CHAINES_IDEMPOTENCE = [
    "  L\u2019Usager,  DOIT payer ! ",
    "« Bonjour » ; dit-il… (vraiment ?)",
    "Œuvre ÉCRITE à l\u2019ÉTÉ — fin.",
    "\ufb01n de la \ufb02otte",  # ligatures fi et fl
    "Montant\u00a0: 1\u202f234,56\u00a0€",
    "ÀÉÎÕÜ Ÿ Ç",
    "x²  +  ½ = Ⅻ",
    "İstanbul et ǅemal",
    "",
    "   ,;:!?   ",
    "tab\tet\nsaut\r\nde ligne",
    "e\u0301te\u0301 de\u0301compose\u0301",
]


@pytest.mark.parametrize("chaine", CHAINES_IDEMPOTENCE)
def test_normaliser_idempotente(chaine: str) -> None:
    une_fois = normaliser(chaine)
    assert normaliser(une_fois) == une_fois
    assert une_fois == une_fois.strip()
    assert "  " not in une_fois


def test_normaliser_regles() -> None:
    assert normaliser("\ufb01n") == "fin"  # NFKC
    assert normaliser("ÉTÉ") == "été"
    assert normaliser("1\u00a0000") == "1 000"
    assert normaliser("«a»b-c") == "a b c"
    assert normaliser("50 € + 5 %") == "50 € + 5"  # % est de la ponctuation (Po), € non (Sc)


# --- mots et phrases -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("texte", "attendu"),
    [
        ("l'usager", 1),
        ("porte-monnaie", 1),
        ("€", 0),
        ("–", 0),
        ("Payer 25 € – vite", 3),
        ("un\u00a0deux", 2),
        ("", 0),
        ("  ,; ", 0),
    ],
)
def test_compter_mots(texte: str, attendu: int) -> None:
    assert compter_mots(texte) == attendu


@pytest.mark.parametrize(
    ("texte", "attendu"),
    [
        ("Le chat dort. Il fait beau.", ["Le chat dort.", "Il fait beau."]),
        ("Oui !!! Non ?! Peut-être…", ["Oui !!!", "Non ?!", "Peut-être…"]),
        ("Ligne un\nLigne deux", ["Ligne un", "Ligne deux"]),
        ("Prix : 3.5 euros.", ["Prix : 3.5 euros."]),
        ("M. Dupont arrive.", ["M.", "Dupont arrive."]),  # limite assumée
        ("Fin. ... !\n\n", ["Fin."]),
        ("", []),
        ("  ,; ", []),
    ],
)
def test_decouper_phrases(texte: str, attendu: list[str]) -> None:
    assert decouper_phrases(texte) == attendu


# --- nombres ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("texte", "attendu"),
    [
        ("1\u00a0234,56 €", [Decimal("1234.56")]),
        ("12,50 €", [Decimal("12.50")]),
        ("25 €", [Decimal("25")]),
        ("3,5 %", [Decimal("3.5")]),
        ("1 234,56", [Decimal("1234.56")]),
        ("1\u00a0234,56", [Decimal("1234.56")]),
        ("1\u202f000", [Decimal("1000")]),
        ("1\u2009000", [Decimal("1000")]),
        ("1 000", [Decimal("1000")]),
        ("1\u202f000 et 2\u2009000", [Decimal("1000"), Decimal("2000")]),
        ("2020-2021", [Decimal("2020"), Decimal("2021")]),
        ("-3,5 %", [Decimal("-3.5")]),
        ("\u22122 degrés", [Decimal("-2")]),
        ("R2D2", []),
        ("v2.5", []),
        ("A1,5", []),
        ("1.234.567", [Decimal("1.234")]),
        ("1.234,56", [Decimal("1234.56")]),
        ("3.5", [Decimal("3.5")]),
        ("25.", [Decimal("25")]),
        ("m² et 4 m²", [Decimal("4")]),
        ("12 3456", [Decimal("12"), Decimal("3456")]),
        ("de 10 à 20, puis 5", [Decimal("10"), Decimal("20"), Decimal("5")]),
        ("", []),
    ],
)
def test_extraire_nombres(texte: str, attendu: list[Decimal]) -> None:
    obtenu = extraire_nombres(texte)
    assert obtenu == attendu
    assert all(isinstance(n, Decimal) for n in obtenu)


def test_extraire_nombres_garde_les_decimales() -> None:
    assert str(extraire_nombres("12,50 €")[0]) == "12.50"


# --- syllabes --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("mot", "attendu"),
    [
        ("porte", 1),
        ("portes", 1),
        ("le", 1),
        ("arrivée", 3),
        ("administrative", 5),
        ("porte-monnaie", 3),
        ("l'usager", 3),
        ("2026", 1),
        ("hôpital", 3),
        ("forêt", 2),
        ("sûr", 1),
        ("aiguë", 2),
        ("cœur", 1),
        ("île", 1),
        ("Arrivées", 3),
        ("ÉTÉ", 2),
        ("€", 1),
    ],
)
def test_syllabes(mot: str, attendu: int) -> None:
    assert syllabes(mot) == attendu


# --- Kandel-Moles ----------------------------------------------------------------------------

# Chaque cas : texte, mots, phrases, syllabes, indice calculé à la main.
REFERENCES_KANDEL_MOLES = [
    # Le(1) chat(1) dort(1) / Il(1) fait(1) beau(1) : 6 mots, 2 phrases, 6 syllabes.
    # 207 − 1,015 × 3 − 73,6 × 1 = 130,355.
    ("Le chat dort. Il fait beau.", 6, 2, 6, 130.355),
    # Les(1) usagers(3 : u-a-e) paient(1 : aie) la(1) taxe(1 : e muet) : 5 mots, 1 phrase,
    # 7 syllabes. 207 − 1,015 × 5 − 73,6 × 7/5 = 207 − 5,075 − 103,04 = 98,885.
    ("Les usagers paient la taxe.", 5, 1, 7, 98.885),
    # Venez(2) demain(2) / Où(1) est(1) la(1) mairie(2 : e précédé d'une voyelle) /
    # Elle(1) ferme(1) à(1) midi(2) : 10 mots (« ! » et « ? » ne comptent pas), 3 phrases
    # (saut de ligne, puis « ? »), 14 syllabes.
    # 207 − 1,015 × 10/3 − 73,6 × 14/10 = 207 − 3,3833 − 103,04 = 100,5767.
    ("Venez demain !\nOù est la mairie ? Elle ferme à midi.", 10, 3, 14, 100.5767),
]


@pytest.mark.parametrize(
    ("texte", "mots", "phrases", "nb_syllabes", "indice"), REFERENCES_KANDEL_MOLES
)
def test_kandel_moles_references(
    texte: str, mots: int, phrases: int, nb_syllabes: int, indice: float
) -> None:
    assert compter_mots(texte) == mots
    assert len(decouper_phrases(texte)) == phrases
    assert sum(syllabes(m) for m in texte.split() if any(c.isalnum() for c in m)) == nb_syllabes
    assert kandel_moles(texte) == pytest.approx(indice, abs=0.1)


def test_kandel_moles_simplifie_plus_lisible() -> None:
    administratif = (
        "Conformément aux dispositions réglementaires applicables, l'administration "
        "procède à l'instruction approfondie de votre demande d'autorisation préalable."
    )
    simplifie = "Nous lisons votre demande. Vous aurez vite une réponse."
    assert kandel_moles(simplifie) > kandel_moles(administratif)


def test_kandel_moles_non_arrondi() -> None:
    assert kandel_moles("Venez demain !\nOù est la mairie ? Elle ferme à midi.") == (
        207 - 1.015 * (10 / 3) - 73.6 * (14 / 10)
    )


# --- textes vides et n-grammes ---------------------------------------------------------------


@pytest.mark.parametrize("texte", ["", "  ,; "])
def test_texte_vide(texte: str) -> None:
    assert compter_mots(texte) == 0
    assert decouper_phrases(texte) == []
    assert ngrammes(texte, 1) == []
    with pytest.raises(ValueError):
        kandel_moles(texte)


def test_ngrammes() -> None:
    assert ngrammes("Le chat, le chat !", 2) == [
        ("le", "chat"),
        ("chat", "le"),
        ("le", "chat"),
    ]
    assert ngrammes("Un deux", 3) == []
    assert ngrammes("L\u2019Usager paie", 1) == [("l",), ("usager",), ("paie",)]


@pytest.mark.parametrize("n", [0, -1])
def test_ngrammes_n_invalide(n: int) -> None:
    with pytest.raises(ValueError):
        ngrammes("un deux trois", n)


# --- isolement du module ---------------------------------------------------------------------


def test_import_par_chemin_seul() -> None:
    spec = importlib.util.spec_from_file_location("texte_isole", CHEMIN_TEXTE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert NOMS_PUBLICS <= set(vars(module))
    assert set(module.__all__) == NOMS_PUBLICS
    assert module.VERSION_TEXTE == VERSION_TEXTE


def test_import_par_chemin_sans_paquet_slmsp() -> None:
    script = (
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location('texte_isole', {str(CHEMIN_TEXTE)!r})\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(m)\n"
        "assert not [n for n in sys.modules if n == 'slmsp' or n.startswith('slmsp.')]\n"
        "print(m.kandel_moles('Le chat dort. Il fait beau.'))\n"
    )
    sortie = subprocess.run(
        [sys.executable, "-I", "-c", script], capture_output=True, text=True, check=True
    )
    assert float(sortie.stdout) == pytest.approx(130.355)


def test_texte_n_importe_que_la_bibliotheque_standard() -> None:
    arbre = ast.parse(CHEMIN_TEXTE.read_text(encoding="utf-8"))
    modules: list[str] = []
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.Import):
            modules.extend(alias.name for alias in noeud.names)
        elif isinstance(noeud, ast.ImportFrom):
            assert noeud.level == 0, "import relatif interdit dans core.texte"
            assert noeud.module is not None
            modules.append(noeud.module)
    assert modules
    hors_stdlib = [m for m in modules if m.split(".")[0] not in sys.stdlib_module_names]
    assert hors_stdlib == []


# --- verrou de version -----------------------------------------------------------------------

CORPUS_REFERENCE = [
    "",
    "  ,; ",
    "  L\u2019Usager,  DOIT payer ! ",
    "Le chat dort. Il fait beau.",
    "Les usagers paient la taxe.",
    "Venez demain !\nOù est la mairie ? Elle ferme à midi.",
    "M. Dupont arrive… Oui !!! Non ?! Fin",
    "Œuvre \ufb01nale : 1\u00a0234,56 € ; 12,50 € ; 3,5 % ; -3,5 % ; \u22122.",
    "En 2020-2021, R2D2 a payé 1.234,56 puis 3.5 et 25. Total 1 000 ou 12 3456.",
    "porte portes le arrivée administrative porte-monnaie l'usager 2026 ÉTÉ",
    "Conformément aux dispositions réglementaires, l'administration instruit la demande.",
    "1\u202f000 et 2\u2009500,5",
    "hôpital forêt sûr aiguë cœur île crème",
    "pâté Händel dîner élève là-bas Göran brûler Müller cæcum fœtus stylo",
    "bëla pïlo pùla pÿla",
    "arrivées",
    "1.234",
    "\n\u22124 %",
    "v2.5 A1,5",
    "x² + ½ = Ⅻ ; e\u0301te\u0301 ; tab\tet\r\nsaut",
]


def _sorties(texte: str) -> dict[str, object]:
    try:
        indice: str = repr(kandel_moles(texte))
    except ValueError:
        indice = "ValueError"
    return {
        "normaliser": normaliser(texte),
        "compter_mots": compter_mots(texte),
        "decouper_phrases": decouper_phrases(texte),
        "extraire_nombres": [str(n) for n in extraire_nombres(texte)],
        "syllabes": [syllabes(jeton) for jeton in texte.split()],
        "kandel_moles": indice,
        "ngrammes": {str(n): [list(g) for g in ngrammes(texte, n)] for n in (1, 2, 3, 4)},
    }


def empreinte() -> str:
    # La base Unicode de Python entre dans l'empreinte : une mise à jour qui change
    # NFKC, les catégories ou `isalpha` change les sorties à règles constantes.
    donnees = {
        "unidata_version": unicodedata.unidata_version,
        "sorties": [_sorties(texte) for texte in CORPUS_REFERENCE],
    }
    canon = json.dumps(donnees, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


EMPREINTES: dict[int, str] = {
    1: "1d591ff03e80f27c26bbca5c8429f403a66a52eb9a3bac20894f097c4cada3b5",
}


def test_verrou_de_version() -> None:
    assert VERSION_TEXTE in EMPREINTES, "Nouvelle VERSION_TEXTE : ajouter son empreinte."
    assert empreinte() == EMPREINTES[VERSION_TEXTE], (
        "Les sorties de core.texte ont changé : incrémenter VERSION_TEXTE et ajouter l'empreinte. "
        "Recalcul : appeler empreinte() de tests/core/test_texte.py (par exemple via "
        "importlib.util.spec_from_file_location) et inscrire le résultat dans EMPREINTES sous "
        "la nouvelle version. EMPREINTES garde une entrée par version : ne pas effacer les "
        "anciennes."
    )
