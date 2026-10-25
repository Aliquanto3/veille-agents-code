"""Rendu et masque de perte (story 10.2, H-MASQUE).

Les tests unitaires utilisent un tokenizer factice (aucun `transformers`). Les tests sur les
tokenizers réels des candidats (`models/`) et sur `llama-server --jinja` sont marqués `lent`
et sautés si les fichiers ou `transformers` manquent. Les contenus sont factices.
"""

from __future__ import annotations

import json
import os
import random
import re
from pathlib import Path
from typing import Any

import pytest

from slmsp.core.config import dossier_modeles
from slmsp.fetch.config import charger_config_modele
from slmsp.train.masque import (
    IGNORE,
    ErreurMasque,
    calculer_masque,
    intervalles_assistant,
    texte_non_masque,
)
from slmsp.train.rendu import apply_chat_template, kwargs_template

JETON = re.compile(r"<\|[a-z_]+\|>|\w+|\s+|[^\w\s]")


class TokenizerFactice:
    """Template de type ChatML ; un token = balise, mot, espaces ou ponctuation."""

    def __init__(self, *, reecrit_historique: bool = False, jeton_colle: bool = False) -> None:
        self.vocab: dict[str, int] = {}
        self.appels: list[dict[str, Any]] = []
        self.reecrit_historique = reecrit_historique
        self.jeton_colle = jeton_colle

    def apply_chat_template(
        self, messages, *, tools=None, tokenize=False, add_generation_prompt=False, **kwargs
    ):
        self.appels.append({"tools": tools, "kwargs": kwargs})
        sortie = ""
        if tools:
            sortie += "<|tools|>" + json.dumps(tools) + "<|end|>\n"
        if kwargs.get("avec_amorce"):
            sortie += "<|amorce|>\n"
        dernier = len(messages) - 1
        for i, m in enumerate(messages):
            contenu = m.get("content") or ""
            if self.reecrit_historique and m["role"] == "assistant" and i < dernier:
                contenu = ""
            sortie += f"<|{m['role']}|>" + contenu
            for appel in m.get("tool_calls") or []:
                sortie += "<|call|>" + json.dumps(appel["function"], sort_keys=True)
            sortie += "<|end|>\n"
        if add_generation_prompt:
            sortie += "<|assistant|>"
        return sortie

    def __call__(self, texte, *, add_special_tokens=False, return_offsets_mapping=False):
        ids, offsets = [], []
        for m in JETON.finditer(texte):
            fin = m.end() + 1 if self.jeton_colle and m.group() == "<|assistant|>" else m.end()
            offsets.append((m.start(), fin))
            ids.append(self.vocab.setdefault(texte[m.start() : fin], len(self.vocab)))
        return {"input_ids": ids, "offset_mapping": offsets}

    def decode(self, ids):
        inverse = {v: k for k, v in self.vocab.items()}
        return "".join(inverse[i] for i in ids)


def conversation() -> list[dict[str, Any]]:
    appel = {"id": "c1", "type": "function", "function": {"name": "outil", "arguments": {"q": "x"}}}
    return [
        {"role": "system", "content": "<système-factice>"},
        {"role": "user", "content": "<question-factice-1>"},
        {"role": "assistant", "content": "", "tool_calls": [appel]},
        {"role": "tool", "tool_call_id": "c1", "content": "<résultat-factice>"},
        {"role": "assistant", "content": "<réponse-factice-1>"},
        {"role": "user", "content": "<question-factice-2>"},
        {"role": "assistant", "content": "<réponse-factice-2>"},
    ]


def attendu(tok: TokenizerFactice, messages) -> str:
    """Tours assistant d'après le rendu : de l'amorce à la fin de tour incluse."""
    sortie = ""
    for k, m in enumerate(messages):
        if m["role"] == "assistant":
            debut = len(apply_chat_template(tok, messages[:k], add_generation_prompt=True))
            sortie += apply_chat_template(tok, messages[: k + 1])[debut:]
    return sortie


def test_labels_seulement_sur_les_tours_assistant() -> None:
    tok = TokenizerFactice()
    messages = conversation()
    rendu = calculer_masque(tok, messages)
    assert len(rendu.input_ids) == len(rendu.labels)
    assert all(e in (IGNORE, i) for e, i in zip(rendu.labels, rendu.input_ids, strict=True))
    gardes = texte_non_masque(tok, rendu)
    assert gardes == attendu(tok, messages)
    assert "<|call|>" in gardes  # appels d'outils sérialisés
    assert gardes.count("<|end|>") == 3  # fin de tour incluse
    assert "<résultat-factice>" not in gardes
    assert "<question-factice-2>" not in gardes
    assert tok.decode(rendu.input_ids) == rendu.texte


def test_aucun_tour_assistant_tout_masque() -> None:
    rendu = calculer_masque(TokenizerFactice(), conversation()[:2])
    assert set(rendu.labels) == {IGNORE}
    assert rendu.tours == []


def test_conversations_aleatoires() -> None:
    tok = TokenizerFactice()
    alea = random.Random(7)
    for n in range(40):
        messages: list[dict[str, Any]] = [{"role": "user", "content": "<question-factice>"}]
        for _ in range(alea.randint(0, 5)):
            role = alea.choice(["assistant", "assistant", "user", "tool"])
            msg: dict[str, Any] = {
                "role": role,
                "content": f"<contenu-factice-{n}-{alea.random()}>",
            }
            if role == "assistant" and alea.random() < 0.5:
                msg["tool_calls"] = [
                    {"function": {"name": "o", "arguments": {"a": alea.randint(0, 9)}}}
                ]
            messages.append(msg)
        rendu = calculer_masque(tok, messages)
        assert texte_non_masque(tok, rendu) == attendu(tok, messages)
        assert rendu.texte == apply_chat_template(tok, messages)


def test_kwargs_et_outils_transmis_au_template() -> None:
    tok = TokenizerFactice()
    config = charger_config_modele("smollm3-3b")
    assert kwargs_template(config) == {"enable_thinking": False}
    assert kwargs_template(None) == {}
    outils = [{"type": "function", "function": {"name": "outil"}}]
    config2 = config.model_copy(update={"chat_template_kwargs": {"avec_amorce": True}})
    rendu = calculer_masque(tok, conversation(), tools=outils, config=config2)
    assert rendu.texte.startswith("<|tools|>")
    assert all(a["kwargs"] == {"avec_amorce": True} and a["tools"] == outils for a in tok.appels)
    assert rendu.labels[0] == IGNORE  # outils et amorce masqués


def test_template_qui_reecrit_l_historique_est_refuse() -> None:
    with pytest.raises(ErreurMasque, match="préfixe"):
        intervalles_assistant(TokenizerFactice(reecrit_historique=True), conversation())


def test_token_a_cheval_sur_une_frontiere_est_refuse() -> None:
    with pytest.raises(ErreurMasque, match="déborde|chevauche"):
        calculer_masque(TokenizerFactice(jeton_colle=True), conversation())


def test_conversation_commencant_par_assistant_refusee() -> None:
    class SansListeVide(TokenizerFactice):
        def apply_chat_template(self, messages, **kw):
            if not messages:
                raise ValueError("liste vide")
            return super().apply_chat_template(messages, **kw)

    with pytest.raises(ErreurMasque, match="amorce"):
        calculer_masque(SansListeVide(), [{"role": "assistant", "content": "<réponse-factice-1>"}])


def test_amorce_non_prefixe_du_rendu_complet_refusee() -> None:
    class Preambule(TokenizerFactice):
        def apply_chat_template(self, messages, *, add_generation_prompt=False, **kw):
            sortie = super().apply_chat_template(
                messages, add_generation_prompt=add_generation_prompt, **kw
            )
            return "<|system|>défaut<|end|>\n" + sortie if not messages else sortie

    with pytest.raises(ErreurMasque, match="préfixe"):
        intervalles_assistant(
            Preambule(), [{"role": "assistant", "content": "<réponse-factice-1>"}]
        )


def test_tokenizer_sans_offsets_refuse() -> None:
    class Lent(TokenizerFactice):
        def __call__(self, texte, **kw):
            raise NotImplementedError("offsets indisponibles")

    with pytest.raises(ErreurMasque, match="positions"):
        calculer_masque(Lent(), conversation())


def test_tour_assistant_vide_refuse() -> None:
    class Vide(TokenizerFactice):
        def apply_chat_template(self, messages, *, add_generation_prompt=False, **kw):
            return "<|user|>x<|end|>\n" + ("<|assistant|>" if add_generation_prompt else "")

    with pytest.raises(ErreurMasque, match="aucun texte"):
        intervalles_assistant(Vide(), [{"role": "user", "content": "x"}, {"role": "assistant"}])


# ---- tests lents : tokenizers réels et llama-server (jamais dans la suite par défaut) ----

CANDIDATS = ["granite-4.0-1b", "ministral-3-3b", "smollm3-3b", "qwen-4b"]
OUTIL = {
    "type": "function",
    "function": {
        "name": "rechercher",
        "description": "<description-factice>",
        "parameters": {"type": "object", "properties": {"requete": {"type": "string"}}},
    },
}


def conversation_outils() -> list[dict[str, Any]]:
    appel = {
        "id": "call00001",
        "type": "function",
        "function": {"name": "rechercher", "arguments": {"requete": "<q-factice>"}},
    }
    return [
        {"role": "system", "content": "<système-factice>"},
        {"role": "user", "content": "<question-factice-1>"},
        {"role": "assistant", "content": "<réponse-factice-0>", "tool_calls": [appel]},
        {"role": "tool", "tool_call_id": "call00001", "content": "<résultat-factice>"},
        {"role": "assistant", "content": "<réponse-factice-1>"},
    ]


def _dossier_hf(slug: str) -> Path:
    dossier = Path(os.environ.get("SLMSP_MODELS_DIR") or dossier_modeles()) / slug / "hf"
    if not (dossier / "tokenizer_config.json").is_file():
        pytest.skip(f"tokenizer absent : {dossier}")
    return dossier


@pytest.mark.lent
@pytest.mark.parametrize("slug", CANDIDATS)
def test_candidat_reel_masque_sur_les_tours_assistant(slug: str) -> None:
    pytest.importorskip("transformers")
    from slmsp.train.rendu import charger_tokenizer

    tok = charger_tokenizer(_dossier_hf(slug))
    config = charger_config_modele(slug)
    try:
        rendu = calculer_masque(tok, conversation_outils(), tools=[OUTIL], config=config)
    except ErreurMasque as e:  # critère 2 : à consigner, variante `generation` à produire
        pytest.fail(f"{slug} : masque impossible avec le template officiel ({e})")
    gardes = texte_non_masque(tok, rendu)
    assert "<réponse-factice-0>" in gardes
    assert "<réponse-factice-1>" in gardes
    assert "<résultat-factice>" not in gardes
    assert "<question-factice-1>" not in gardes
    print(f"H-MASQUE {slug} : ok, {sum(e != IGNORE for e in rendu.labels)}/{len(rendu.labels)}")


@pytest.mark.lent
@pytest.mark.parametrize("slug", ["granite-4.0-1b", "smollm3-3b"])
def test_rendu_identique_a_llama_server_jinja(slug: str) -> None:
    """Critère 3 : `/apply-template` de `llama-server --jinja` rend le même texte."""
    pytest.importorskip("transformers")
    from slmsp.inference.serveur import ServeurLlama
    from slmsp.train.rendu import charger_tokenizer

    gguf = next((dossier_modeles() / slug / "gguf").glob("*.gguf"), None)
    if gguf is None:
        pytest.skip(f"GGUF absent pour {slug}")
    tok = charger_tokenizer(_dossier_hf(slug))
    config = charger_config_modele(slug)
    messages = conversation_outils()[:4]  # se termine par le message `tool`
    local = apply_chat_template(
        tok, messages, tools=[OUTIL], config=config, add_generation_prompt=True
    )
    with ServeurLlama(config, slug=slug, gguf=gguf) as serveur, serveur.client() as client:
        corps: dict[str, Any] = {"messages": messages, "tools": [OUTIL]}
        if config.chat_template_kwargs:
            corps["chat_template_kwargs"] = config.chat_template_kwargs
        distant = client._post("/apply-template", corps)["prompt"]
    assert local == distant
