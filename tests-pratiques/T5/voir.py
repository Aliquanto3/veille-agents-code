"""Affiche les constats d'un modele ou d'une story (lecture seule). Usage : voir.py [filtre_modele] [filtre_story] [--tests]"""
import sys

from executer_tests import charger_constats

args = [a for a in sys.argv[1:] if not a.startswith("--")]
avec_tests = "--tests" in sys.argv
sys.stdout.reconfigure(encoding="utf-8")
for c in charger_constats():
    if args and args[0] not in c["modele"]:
        continue
    if len(args) > 1 and args[1] not in c["story"]:
        continue
    print(f"[{c['modele'].split('/')[-1]} {c['story']} {c['id']}] {c.get('severite')} {c.get('fichier')}:{c.get('ligne')}")
    print("   ", (c.get("description") or "")[:600].replace("\n", " "))
    if avec_tests and c.get("test"):
        print("   --- test\n" + c["test"])
