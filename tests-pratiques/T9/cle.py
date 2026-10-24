"""Lecture de la cle OpenRouter (environnement, sinon registre utilisateur). Ne jamais l'afficher ni l'ecrire."""
import os


def cle_openrouter() -> str:
    k = os.environ.get("OPENROUTER_API_KEY")
    if k:
        return k.strip()
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h:
        return winreg.QueryValueEx(h, "OPENROUTER_API_KEY")[0].strip()
