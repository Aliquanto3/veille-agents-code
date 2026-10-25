"""Bac à sable MCP : rejeu déterministe des cassettes (story 3.2, AD-10)."""

from __future__ import annotations

import hashlib
import json
import tomllib
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from slmsp.core.canonique import json_canonique
from slmsp.core.erreurs import AppelNonConforme, ConfigurationInvalide, SchemaOutilModifie
from slmsp.core.evenements import Avertissement, Evenement
from slmsp.core.ports import ToolPort
from slmsp.core.schemas.cassette import Cassette, Interaction, Simulation
from slmsp.mcp.bac_a_sable import CODE_APPEL_NON_PREVU, BacASable, reponse_vide
from slmsp.mcp.cassettes import ecrire_cassette, lire_cassette
from slmsp.mcp.enregistrement import PREMIER_ID_APPEL
from slmsp.mcp.erreurs import (
    PAR_TYPE_SIMULATION,
    CassetteInvalide,
    DelaiDepasse,
    ErreurHttp,
    ErreurTransportMcp,
    Injoignable,
)
from slmsp.mcp.outils import charger_config

RACINE = Path(__file__).resolve().parents[2]
CONFIG = RACINE / "config" / "outils-mcp.toml"
EVAL = RACINE / "eval"
CALIBRAGE = EVAL / "calibrage" / "cassettes"
CASSETTES_RD = sorted((EVAL / "cassettes").glob("RD-*/s1.json"))
SHA = charger_config().tools_list_sha256
TEXTE_VIDE = "No results found."


# --- Fixtures --------------------------------------------------------------------------------


def _etat_eval() -> dict[str, tuple[str, int]]:
    return {
        str(p.relative_to(EVAL)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
        for p in sorted(EVAL.rglob("*"))
        if p.is_file()
    }


@pytest.fixture
def eval_intact() -> Iterator[None]:
    avant = _etat_eval()
    yield
    assert _etat_eval() == avant


def _requete(id_: int, nom: str, arguments: Any) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": id_,
        "method": "tools/call",
        "params": {"name": nom, "arguments": arguments},
    }


def _reponse(id_: int, texte: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": id_,
        "result": {"content": [{"type": "text", "text": texte}], "isError": False},
    }


def _interaction(
    id_: int,
    nom: str,
    arguments: dict[str, Any],
    texte: str | None = None,
    simulation: Simulation | None = None,
) -> Interaction:
    reponse = None if simulation is not None else _reponse(id_, texte or f"<réponse-factice-{id_}>")
    return Interaction(
        request=_requete(id_, nom, arguments), response=reponse, simulation=simulation
    )


def _cassette(interactions: list[Interaction], *, sha: str = SHA) -> Cassette:
    return Cassette(
        schema_version=1,
        server="http://serveur-factice.invalid/mcp",
        recorded_at=datetime(2026, 10, 12, 5, 0, tzinfo=UTC),
        initialize={"jsonrpc": "2.0", "id": 1, "result": {}},
        tools_list_sha256=sha,
        interactions=interactions,
    )


def _ecrite(tmp_path: Path, nom: str, interactions: list[Interaction], **kw: Any) -> Path:
    return ecrire_cassette(_cassette(interactions, **kw), tmp_path / nom)


@pytest.fixture
def base(tmp_path: Path) -> list[Path]:
    """Deux cassettes synthétiques : recherches, infos de jeu, et une panne simulée."""
    premiere = _ecrite(
        tmp_path,
        "a.json",
        [
            Interaction(
                request={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                response={"jsonrpc": "2.0", "id": 2, "result": {"tools": []}},
            ),
            _interaction(
                3, "search_datasets", {"query": "<a>", "page_size": 5}, "<réponse-factice-1>"
            ),
            _interaction(4, "search_datasets", {"query": "<b>"}, "<réponse-factice-2>"),
        ],
    )
    seconde = _ecrite(
        tmp_path,
        "b.json",
        [
            _interaction(3, "get_dataset_info", {"dataset_id": "<d1>"}, "<réponse-factice-3>"),
            _interaction(
                4,
                "get_dataset_info",
                {"dataset_id": "<panne>"},
                simulation=Simulation(type="erreur_http", statut=503),
            ),
            _interaction(
                5, "search_datasets", {"query": "<a>", "page_size": 5}, "<réponse-factice-4>"
            ),
        ],
    )
    return [premiere, seconde]


class _Collecte:
    def __init__(self) -> None:
        self.evenements: list[Evenement] = []

    def __call__(self, evenement: Evenement) -> None:
        self.evenements.append(evenement)


def _texte(reponse: dict[str, Any]) -> str:
    return reponse["result"]["content"][0]["text"]


# --- Port et outils --------------------------------------------------------------------------


def test_bac_a_sable_est_un_toolport(base: list[Path]) -> None:
    bac = BacASable(base)
    assert isinstance(bac, ToolPort)
    outils = bac.lister_outils()
    assert [o["function"]["name"] for o in outils][0] == "search_datasets"
    outils[0]["function"]["name"] = "modifie"
    assert bac.lister_outils()[0]["function"]["name"] == "search_datasets"


def test_config_texte_reponse_vide() -> None:
    assert charger_config().texte_reponse_vide == TEXTE_VIDE
    # La clé est ajoutée avant `[[outils]]`, l'empreinte ne change pas.
    texte = CONFIG.read_text(encoding="utf-8")
    assert texte.index("texte_reponse_vide") < texte.index("[[outils]]")
    assert SHA == "38bdeb31324b97789d0a11899aec4d560435d112a79c8da7364992576e3d5b15"


# --- Appariement -----------------------------------------------------------------------------


def test_appariement_exact(base: list[Path]) -> None:
    collecte = _Collecte()
    bac = BacASable(base, signaler=collecte)
    reponse = bac.appeler("search_datasets", {"page_size": 5, "query": "<a>"}, id_requete=7)
    assert reponse == {**_reponse(7, "<réponse-factice-1>")}
    assert _texte(bac.appeler("search_datasets", {"query": "<b>"}, id_requete=8)) == (
        "<réponse-factice-2>"
    )
    assert _texte(bac.appeler("get_dataset_info", {"dataset_id": "<d1>"})) == "<réponse-factice-3>"
    assert collecte.evenements == []


def test_id_requete_par_defaut(base: list[Path]) -> None:
    reponse = BacASable(base).appeler("search_datasets", {"query": "<b>"})
    assert reponse["id"] == PREMIER_ID_APPEL == 3


def test_reponse_est_une_copie(base: list[Path]) -> None:
    bac = BacASable(base)
    reponse = bac.appeler("search_datasets", {"query": "<b>"}, id_requete=9)
    reponse["result"]["content"][0]["text"] = "modifie"
    reponse["result"]["content"].clear()
    assert _texte(bac.appeler("search_datasets", {"query": "<b>"})) == "<réponse-factice-2>"


def test_le_plus_proche_premier_rang(base: list[Path]) -> None:
    collecte = _Collecte()
    bac = BacASable(base, signaler=collecte)
    # 1 paire égale avec chacune des deux premières : le premier rang l'emporte.
    reponse = bac.appeler("search_datasets", {"query": "<b>", "page_size": 5}, id_requete=11)
    assert reponse == _reponse(11, "<réponse-factice-1>")
    (evenement,) = collecte.evenements
    assert isinstance(evenement, Avertissement)
    assert evenement.code == CODE_APPEL_NON_PREVU == "appel-non-prevu"
    # L'avertissement cite l'origine de l'interaction rejouée, jamais les valeurs.
    assert f"{base[0]}, interaction 1" in evenement.message
    assert "<b>" not in evenement.message


def test_le_plus_proche_plus_de_paires(base: list[Path]) -> None:
    collecte = _Collecte()
    bac = BacASable(base, signaler=collecte)
    reponse = bac.appeler("search_datasets", {"query": "<b>", "page": 2})
    assert _texte(reponse) == "<réponse-factice-2>"
    assert len(collecte.evenements) == 1


def test_le_plus_proche_zero_paire(base: list[Path]) -> None:
    collecte = _Collecte()
    bac = BacASable(base, signaler=collecte)
    reponse = bac.appeler("search_datasets", {"query": "<z>"})
    assert _texte(reponse) == "<réponse-factice-1>"
    assert [e.code for e in collecte.evenements] == [CODE_APPEL_NON_PREVU]  # type: ignore[union-attr]


def test_sans_signaler_aucun_effet(base: list[Path]) -> None:
    reponse = BacASable(base).appeler("search_datasets", {"query": "<z>"}, id_requete=4)
    assert reponse == _reponse(4, "<réponse-factice-1>")


def test_reponse_vide_normalisee(base: list[Path]) -> None:
    collecte = _Collecte()
    bac = BacASable(base, signaler=collecte)
    reponse = bac.appeler("list_dataset_resources", {"dataset_id": "<d1>"}, id_requete=6)
    assert reponse == {
        "jsonrpc": "2.0",
        "id": 6,
        "result": {"content": [{"type": "text", "text": TEXTE_VIDE}], "isError": False},
    }
    assert reponse == reponse_vide(6, TEXTE_VIDE)
    (evenement,) = collecte.evenements
    assert isinstance(evenement, Avertissement) and evenement.code == CODE_APPEL_NON_PREVU
    reponse["result"]["content"].clear()
    assert _texte(bac.appeler("list_dataset_resources", {"dataset_id": "<d1>"})) == TEXTE_VIDE


def test_sans_cassette_tout_est_vide() -> None:
    reponse = BacASable([]).appeler("get_resource_info", {"resource_id": "<r>"})
    assert _texte(reponse) == TEXTE_VIDE


def test_texte_reponse_vide_de_la_config(tmp_path: Path) -> None:
    chemin = _config_modifiee(tmp_path, texte_reponse_vide="<vide-factice>")
    reponse = BacASable([], chemin_outils=chemin).appeler("get_resource_info", {"resource_id": "r"})
    assert _texte(reponse) == "<vide-factice>"


# --- Simulations -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("simulation", "classe"),
    [
        (Simulation(type="delai_depasse"), DelaiDepasse),
        (Simulation(type="erreur_http", statut=500), ErreurHttp),
        (Simulation(type="erreur_http"), ErreurHttp),
        (Simulation(type="injoignable"), Injoignable),
    ],
)
def test_simulation_exacte(tmp_path: Path, simulation: Simulation, classe: type) -> None:
    chemin = _ecrite(
        tmp_path,
        "s.json",
        [_interaction(3, "search_datasets", {"query": "<p>"}, simulation=simulation)],
    )
    collecte = _Collecte()
    bac = BacASable([chemin], signaler=collecte)
    with pytest.raises(classe) as info:
        bac.appeler("search_datasets", {"query": "<p>"})
    assert type(info.value) is PAR_TYPE_SIMULATION[simulation.type]
    if classe is ErreurHttp:
        assert info.value.statut == simulation.statut
    assert collecte.evenements == []


def test_simulation_la_plus_proche(base: list[Path]) -> None:
    collecte = _Collecte()
    bac = BacASable(base, signaler=collecte)
    with pytest.raises(ErreurHttp) as info:
        bac.appeler("get_dataset_info", {"dataset_id": "<panne>"})
    assert info.value.statut == 503
    assert collecte.evenements == []
    # `get_dataset_info` n'a qu'une clé : 0 paire égale partout, le premier rang (réponse).
    assert _texte(bac.appeler("get_dataset_info", {"dataset_id": "<x>"})) == "<réponse-factice-3>"
    # Une simulation est rejouée aussi par proximité.
    chemin = base[0].parent / "p.json"
    ecrire_cassette(
        _cassette(
            [
                _interaction(
                    3,
                    "query_resource_data",
                    {"resource_id": "<r>", "page": 1},
                    simulation=Simulation(type="delai_depasse"),
                ),
                _interaction(
                    4, "query_resource_data", {"resource_id": "<s>"}, "<réponse-factice-5>"
                ),
            ]
        ),
        chemin,
    )
    collecte = _Collecte()
    bac = BacASable([chemin], signaler=collecte)
    with pytest.raises(DelaiDepasse):
        bac.appeler("query_resource_data", {"resource_id": "<r>", "page": 2})
    assert [e.code for e in collecte.evenements] == [CODE_APPEL_NON_PREVU]  # type: ignore[union-attr]


# --- Appels non conformes --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("nom", "arguments"),
    [
        ("get_metrics", {}),
        ("search_datasets", {}),
        ("search_datasets", {"query": 3}),
        ("search_datasets", {"query": "<a>", "inconnu": 1}),
        ("search_datasets", ["<a>"]),
    ],
)
def test_appel_non_conforme(base: list[Path], nom: str, arguments: Any) -> None:
    collecte = _Collecte()
    bac = BacASable(base, signaler=collecte)
    with pytest.raises(AppelNonConforme):
        bac.appeler(nom, arguments)
    assert collecte.evenements == []


# --- Chargement ------------------------------------------------------------------------------


def test_empreinte_differente_refusee(tmp_path: Path, base: list[Path]) -> None:
    autre = "1" * 64
    fausse = _ecrite(
        tmp_path, "fausse.json", [_interaction(3, "search_datasets", {"query": "<a>"})], sha=autre
    )
    with pytest.raises(SchemaOutilModifie) as info:
        BacASable([base[0], fausse])
    ecarts = info.value.ecarts  # type: ignore[attr-defined]
    assert isinstance(ecarts, tuple) and len(ecarts) == 1
    assert "fausse.json" in ecarts[0]
    # Modèle passé directement : l'écart cite le rang.
    with pytest.raises(SchemaOutilModifie) as info:
        BacASable([_cassette([]), _cassette([], sha=autre)])
    assert info.value.ecarts == ("cassette de rang 1 : `tools_list_sha256` différent de la config",)  # type: ignore[attr-defined]
    # Plusieurs cassettes fautives : tous les écarts sont réunis, chacun cite sa source.
    with pytest.raises(SchemaOutilModifie) as info:
        BacASable([fausse, base[0], _cassette([], sha=autre)])
    ecarts = info.value.ecarts  # type: ignore[attr-defined]
    assert len(ecarts) == 2
    assert "fausse.json" in ecarts[0]
    assert ecarts[1].startswith("cassette de rang 2 :")


def test_cassette_absente(tmp_path: Path) -> None:
    with pytest.raises(CassetteInvalide):
        BacASable([tmp_path / "absente.json"])


def test_cassette_json_invalide(tmp_path: Path) -> None:
    chemin = tmp_path / "invalide.json"
    chemin.write_text("{ pas du json", encoding="utf-8")
    with pytest.raises(CassetteInvalide):
        BacASable([str(chemin)])


@pytest.mark.parametrize(
    "params",
    [
        {"name": 3, "arguments": {}},
        {"arguments": {}},
        {"name": "search_datasets", "arguments": ["<a>"]},
        {"name": "search_datasets", "arguments": None},
        "params-factices",
    ],
)
def test_tools_call_malforme(tmp_path: Path, params: Any) -> None:
    requete = {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": params}
    chemin = _ecrite(
        tmp_path,
        "m.json",
        [Interaction(request=requete, response=_reponse(3, "<réponse-factice-1>"))],
    )
    with pytest.raises(CassetteInvalide):
        BacASable([chemin])


def test_tools_call_sans_arguments(tmp_path: Path) -> None:
    # `arguments` est facultatif en MCP : l'interaction vaut un appel aux arguments vides.
    requete = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "get_resource_info"},
    }
    chemin = _ecrite(
        tmp_path,
        "sans-arguments.json",
        [Interaction(request=requete, response=_reponse(3, "<réponse-factice-1>"))],
    )
    collecte = _Collecte()
    bac = BacASable([chemin], signaler=collecte)
    reponse = bac.appeler("get_resource_info", {"resource_id": "<r>"}, id_requete=5)
    assert reponse == _reponse(5, "<réponse-factice-1>")
    assert len(collecte.evenements) == 1


def test_reponses_d_erreur_rejouees_telles_quelles(tmp_path: Path) -> None:
    erreur_jsonrpc = {
        "jsonrpc": "2.0",
        "id": 3,
        "error": {"code": -32602, "message": "<erreur-factice>"},
    }
    resultat_en_erreur = {
        "jsonrpc": "2.0",
        "id": 4,
        "result": {"content": [{"type": "text", "text": "<erreur-factice>"}], "isError": True},
    }
    chemin = _ecrite(
        tmp_path,
        "erreurs.json",
        [
            Interaction(
                request=_requete(3, "get_dataset_info", {"dataset_id": "<e1>"}),
                response=erreur_jsonrpc,
            ),
            Interaction(
                request=_requete(4, "get_dataset_info", {"dataset_id": "<e2>"}),
                response=resultat_en_erreur,
            ),
        ],
    )
    bac = BacASable([chemin])
    assert bac.appeler("get_dataset_info", {"dataset_id": "<e1>"}, id_requete=8) == {
        **erreur_jsonrpc,
        "id": 8,
    }
    assert bac.appeler("get_dataset_info", {"dataset_id": "<e2>"}, id_requete=9) == {
        **resultat_en_erreur,
        "id": 9,
    }


def test_modeles_et_chemins_melanges(base: list[Path]) -> None:
    modele = _cassette(
        [
            _interaction(3, "get_resource_info", {"resource_id": "<r>"}, "<réponse-factice-9>"),
            _interaction(
                4,
                "get_resource_info",
                {"resource_id": "<panne>"},
                simulation=Simulation(type="erreur_http", statut=503),
            ),
        ]
    )
    bac = BacASable([modele, *base])
    assert _texte(bac.appeler("get_resource_info", {"resource_id": "<r>"})) == "<réponse-factice-9>"
    # Le modèle passé n'est pas retenu par référence : ses champs imbriqués peuvent changer.
    assert modele.interactions[0].response is not None
    modele.interactions[0].response["result"]["content"][0]["text"] = "modifie"
    assert modele.interactions[1].simulation is not None
    modele.interactions[1].simulation.statut = 500
    assert _texte(bac.appeler("get_resource_info", {"resource_id": "<r>"})) == "<réponse-factice-9>"
    with pytest.raises(ErreurHttp) as info:
        bac.appeler("get_resource_info", {"resource_id": "<panne>"})
    assert info.value.statut == 503


def test_chemin_outils_respecte(tmp_path: Path) -> None:
    with CONFIG.open("rb") as flux:
        outils = tomllib.load(flux)["outils"]
    garde = [o for o in outils if o["nom"] in ("search_datasets", "get_dataset_info")]
    chemin = _config_modifiee(tmp_path, outils=garde)
    bac = BacASable([], chemin_outils=chemin)
    assert [o["function"]["name"] for o in bac.lister_outils()] == [
        "search_datasets",
        "get_dataset_info",
    ]
    with pytest.raises(AppelNonConforme):
        bac.appeler("get_resource_info", {"resource_id": "<r>"})
    assert _texte(bac.appeler("get_dataset_info", {"dataset_id": "<d>"})) == TEXTE_VIDE


def test_cassettes_doit_etre_une_sequence(base: list[Path]) -> None:
    with pytest.raises(TypeError):
        BacASable(base[0])  # type: ignore[arg-type]


# --- Config ----------------------------------------------------------------------------------


def _toml(valeur: Any) -> str:
    if isinstance(valeur, bool):
        return "true" if valeur else "false"
    if isinstance(valeur, (int, str)):
        return json.dumps(valeur, ensure_ascii=False)
    if isinstance(valeur, list):
        return "[" + ", ".join(_toml(x) for x in valeur) + "]"
    if isinstance(valeur, dict):
        return "{ " + ", ".join(f'"{k}" = {_toml(v)}' for k, v in valeur.items()) + " }"
    raise TypeError(type(valeur))


_ABSENT = object()


def _config_modifiee(tmp_path: Path, **surcharges: Any) -> Path:
    with CONFIG.open("rb") as flux:
        donnees = tomllib.load(flux)
    for cle, valeur in surcharges.items():
        if valeur is _ABSENT:
            donnees.pop(cle)
        else:
            donnees[cle] = valeur
    lignes = [f"{cle} = {_toml(v)}" for cle, v in donnees.items() if cle != "outils"]
    for outil in donnees["outils"]:
        lignes.append("[[outils]]")
        lignes.extend(f"{cle} = {_toml(v)}" for cle, v in outil.items())
    chemin = tmp_path / f"outils-{len(list(tmp_path.glob('outils-*')))}.toml"
    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return chemin


@pytest.mark.parametrize(
    "surcharges",
    [
        {"texte_reponse_vide": _ABSENT},
        {"texte_reponse_vide": ""},
        {"texte_reponse_vide_bis": "x"},
    ],
    ids=["absent", "vide", "cle_inconnue"],
)
def test_config_fautive(tmp_path: Path, surcharges: dict[str, Any]) -> None:
    chemin = _config_modifiee(tmp_path, **surcharges)
    with pytest.raises(ConfigurationInvalide):
        BacASable([], chemin_outils=chemin)


# --- Déterminisme ----------------------------------------------------------------------------

_SEQUENCE: list[tuple[str, dict[str, Any]]] = [
    ("search_datasets", {"query": "<a>", "page_size": 5}),  # exact
    ("search_datasets", {"query": "<b>", "page_size": 5}),  # le plus proche
    ("get_resource_info", {"resource_id": "<r>"}),  # réponse vide
    ("get_dataset_info", {"dataset_id": "<panne>"}),  # simulation
    ("get_dataset_info", {"dataset_id": "<d1>"}),  # exact
    ("query_resource_data", {"resource_id": "<r>", "page": 2}),  # simulation la plus proche
]


def _rejouer(bac: BacASable) -> list[bytes]:
    sorties = []
    for rang, (nom, arguments) in enumerate(_SEQUENCE):
        try:
            sorties.append(
                json_canonique(bac.appeler(nom, arguments, id_requete=PREMIER_ID_APPEL + rang))
            )
        except ErreurTransportMcp as exc:
            statut = getattr(exc, "statut", None)
            sorties.append(json_canonique({"erreur": type(exc).__name__, "statut": statut}))
    return sorties


def test_deux_rejeux_identiques(base: list[Path]) -> None:
    panne = ecrire_cassette(
        _cassette(
            [
                _interaction(
                    3,
                    "query_resource_data",
                    {"resource_id": "<r>", "page": 1},
                    simulation=Simulation(type="delai_depasse"),
                )
            ]
        ),
        base[0].parent / "panne.json",
    )
    cassettes = [*base, panne]
    premiere, seconde, troisieme = _Collecte(), _Collecte(), _Collecte()
    bac = BacASable(cassettes, signaler=premiere)
    a = _rejouer(bac)
    bac.signaler = seconde
    b = _rejouer(bac)
    c = _rejouer(BacASable(cassettes, signaler=troisieme))
    assert a == b == c
    assert a[-1] == json_canonique({"erreur": "DelaiDepasse", "statut": None})
    assert premiere.evenements == seconde.evenements == troisieme.evenements
    assert len(premiere.evenements) == 3


# --- Cassettes réelles (lecture seule) --------------------------------------------------------


def test_rejeu_cassettes_calibrage(eval_intact: None) -> None:
    chemins = [CALIBRAGE / "R-001.json", CALIBRAGE / "R-002.json", CALIBRAGE / "tools-list.json"]
    collecte = _Collecte()
    bac = BacASable(chemins, signaler=collecte)
    appels = 0
    for chemin in chemins[:2]:
        for interaction in lire_cassette(chemin).interactions:
            requete = interaction.request
            if requete["method"] != "tools/call":
                continue
            appels += 1
            reponse = bac.appeler(
                requete["params"]["name"], requete["params"]["arguments"], id_requete=requete["id"]
            )
            # R-001 et R-002 commencent par la même recherche : le premier rang l'emporte.
            attendu = next(
                i.response
                for c in chemins[:2]
                for i in lire_cassette(c).interactions
                if i.request.get("method") == "tools/call"
                and json_canonique(i.request["params"]) == json_canonique(requete["params"])
            )
            assert reponse == {**attendu, "id": requete["id"]}  # type: ignore[dict-item]
    assert appels >= 4
    assert collecte.evenements == []


def test_rejeu_cassettes_rd_gelees(eval_intact: None) -> None:
    assert len(CASSETTES_RD) == 40
    appels = simulations = 0
    for chemin in CASSETTES_RD:
        collecte = _Collecte()
        bac = BacASable([chemin], signaler=collecte)
        for interaction in lire_cassette(chemin).interactions:
            requete = interaction.request
            if requete["method"] != "tools/call":
                continue
            appels += 1
            nom, arguments = requete["params"]["name"], requete["params"]["arguments"]
            if interaction.simulation is not None:
                simulations += 1
                with pytest.raises(PAR_TYPE_SIMULATION[interaction.simulation.type]) as info:
                    bac.appeler(nom, arguments, id_requete=requete["id"])
                if interaction.simulation.type == "erreur_http":
                    assert info.value.statut == interaction.simulation.statut  # type: ignore[attr-defined]
                continue
            reponse = bac.appeler(nom, arguments, id_requete=requete["id"])
            assert reponse == interaction.response, chemin
        assert collecte.evenements == [], chemin
    assert appels == 75
    assert simulations == 4
