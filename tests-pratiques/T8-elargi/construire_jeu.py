"""T8 élargi : fusionne les 400 commandes inoffensives (out/inoffensives.json, extraites des
transcriptions) et les 200 commandes à risque (commandes_risque.py) en un seul jeu mélangé,
out/jeu.json, liste de {cmd, attendu, categorie, outil}.
"""
import json, random, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from commandes_risque import RISQUE

inoff = json.load(open("out/inoffensives.json", encoding="utf-8"))
jeu = [{"cmd": x["cmd"], "attendu": "allow", "categorie": "reelle-inoffensive", "outil": x["outil"]} for x in inoff]
for cmd, label, cat in RISQUE:
    outil = "PowerShell" if any(k in cmd for k in ("Remove-Item", "Invoke-", "Set-", "Get-", "schtasks", "wmic", "reg ", "bcdedit", "Disable-", "Add-MpPreference", "rundll32", "regsvr32", "certutil", "mshta", "forfiles", "cmdkey", "Start-BitsTransfer", "bitsadmin", "diskshadow")) else "Bash"
    jeu.append({"cmd": cmd, "attendu": label, "categorie": cat, "outil": outil})

assert len(jeu) == 600, len(jeu)
random.seed(42)
random.shuffle(jeu)
json.dump(jeu, open("out/jeu.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
from collections import Counter
print(len(jeu), "commandes ; étiquettes :", Counter(x["attendu"] for x in jeu))
