"""Profil anglais des tics de surface (X4)."""
import re

CONTRASTES_EN = [
    ("it's not X, it's Y", re.compile(r"\b(?:it|this|that)(?:'s| is|’s) not\b[^.!?\n]{0,90}?[,;:—-]\s*(?:it(?:'s| is|’s)|but|rather)\b", re.I)),
    ("not (just|only|merely) X but Y", re.compile(r"\bnot (?:just|only|merely|simply|solely)\b[^.!?\n]{0,90}\bbut\b", re.I)),
    ("not X but Y", re.compile(r"\bnot\b[^.!?\n,;]{1,50}[,;]?\s+but (?:rather |instead )?\b", re.I)),
    ("isn't/doesn't X; it Y", re.compile(r"\b(?:isn't|isn’t|aren't|aren’t|doesn't|doesn’t|don't|don’t)\b[^.!?\n]{0,70}[.;,]\s*(?:it|they|this|that)\b", re.I)),
    ("this does not mean X. It means Y", re.compile(r"\bdo(?:es)? not mean\b[^.!?\n]*[.!?]\s+it means", re.I)),
    ("the question is not X", re.compile(r"\bthe (?:question|problem|issue) (?:is not|isn't|isn’t)\b", re.I)),
]
PLUTOT_EN = re.compile(r"\brather than\b|\binstead of\b", re.I)

GONFLES_EN = [(g, re.compile(r"(?<!\w)" + m, re.I)) for g, m in [
    ("crucial", r"crucial\w*"), ("pivotal", r"pivotal\w*"), ("key (adj.)", r"key (?=[a-z]+)(?!to\b|of\b)"),
    ("landscape", r"landscape\w*"), ("robust", r"robust\w*"), ("delve", r"delv\w*"), ("tapestry", r"tapestry"),
    ("testament", r"testament"), ("underscore", r"underscor\w*"), ("seamless", r"seamless\w*"),
    ("vital", r"vital\w*"), ("essential", r"essential\w*"), ("significant", r"significant\w*"),
    ("remarkable", r"remarkabl\w*"), ("paramount", r"paramount"), ("striking", r"striking\w*"),
    ("game-changer", r"game-chang\w*"), ("at its core", r"at its core"), ("genuine", r"genuine\w*"),
    ("revolution", r"revolution\w*"), ("pioneering", r"pioneer\w*"), ("fundamental", r"fundamental\w*"),
    ("it is important to note", r"it(?: is|'s|’s) (?:important|worth noting)"),
    ("the real X", r"the real (?:story|question|win|issue)"),
    ("professionalized/maturation", r"professionali\w*|maturation"),
    ("most interesting", r"(?:most )?(?:architecturally )?interesting"),
]]

ITEM_EN = r"[^\s,.;:()\[\]!?]+(?: [^\s,.;:()\[\]!?]+){0,3}"
TRIADE_EN = re.compile(rf"(?<!\w){ITEM_EN}, {ITEM_EN},? (?:and|or) {ITEM_EN}", re.I)
