"""Lecture de la cle OpenRouter (environnement, sinon registre utilisateur). Ne l affiche jamais."""
from __future__ import annotations

import os


def lire_cle() -> str:
    cle = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if cle:
        return cle
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            valeur, _ = winreg.QueryValueEx(k, "OPENROUTER_API_KEY")
            return str(valeur).strip()
    except (OSError, ImportError):
        return ""
