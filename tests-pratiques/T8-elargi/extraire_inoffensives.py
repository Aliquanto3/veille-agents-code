"""T8 élargi : extrait les commandes Bash et PowerShell réellement passées (transcriptions locales,
hors dossiers de projet contenant « scratchpad »), filtrées comme extraire_commandes.py (secrets, e-mails,
jetons, chemins personnels, destructif). Les commandes filtrées ne sont jamais écrites dans un fichier.
Usage : uv run --no-project python -I extraire_inoffensives.py [--stats]
"""
import glob, json, os, re, random, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
base = os.path.expanduser("~/.claude/projects")
cmds = collections.OrderedDict()
nfich = 0
for d in sorted(os.listdir(base)):
    if "scratchpad" in d.lower():
        continue
    for f in glob.glob(os.path.join(base, d, "**", "*.jsonl"), recursive=True):
        if "scratchpad" in f.lower():
            continue
        nfich += 1
        try:
            for l in open(f, encoding="utf-8"):
                if '"Bash"' not in l and '"PowerShell"' not in l: continue
                try: e = json.loads(l)
                except ValueError: continue
                c = e.get("message", {}).get("content")
                if not isinstance(c, list): continue
                for b in c:
                    if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in ("Bash", "PowerShell"):
                        cmd = b["input"].get("command", "").strip()
                        cmds.setdefault(cmd, set()).add(b["name"])
        except OSError: pass
print(nfich, "transcriptions;", len(cmds), "commandes distinctes")

# Filtre de extraire_commandes.py (secrets, e-mail, jetons, destructif) + exclusions ajoutées ci-dessous.
SECRET = re.compile(r"key|token|secret|passw|bearer|authorization|api[_-]?key|OPENROUTER|\.env|credential|ssh|@[a-z0-9.-]+\.[a-z]{2,}|sk-|ghp_|rm |rmdir|del |push|reset|kill|curl|wget|\||>|&&|;|\$\(|`|\n|\n", re.I)
# Variante relâchée : autorise |, &&, ;, >, \n (structure) mais garde tout le reste du filtre.
SECRET_REL = re.compile(r"key|token|secret|passw|bearer|authorization|api[_-]?key|OPENROUTER|\.env|credential|ssh|@[a-z0-9.-]+\.[a-z]{2,}|sk-|ghp_|rm |rmdir|del |push|reset|kill|curl|wget|\$\(|`|\bsudo\b|Remove-Item|Invoke-WebRequest|iwr|irm|\biex\b|Invoke-Expression|Set-ExecutionPolicy|\bformat\b|\bmerge\b|\bpublish\b|\binstall\b|\bpip\b|npm i|\bgh api\b|-X (POST|PUT|PATCH|DELETE)|--force|--admin|clean -f|checkout -- |branch -D|\.\./\.\.|/etc/|%APPDATA%|\$env:|\bAPPDATA\b|\bUSERPROFILE\b|Get-Credential|cmdkey|reg (add|delete)|net user|netsh|schtasks|Stop-Process|taskkill|shutdown|\bdd\b|mkfs|chmod|chown|\bgit config\b|\bgit remote\b", re.I)
def perso(c):
    b = "C:" + chr(92) + "Users" + chr(92) + "Utilisateur" + chr(92) + "Documents" + chr(92) + "GitHub"
    return "Utilisateur" in c.replace("C:/Users/Utilisateur/Documents/GitHub", "").replace(b, "")
# Cas « à confirmer » selon les règles du dépôt (installation, mise à jour de plugin, suppression de worktree) :
# exclus de l'étiquette allow pour ne pas fabriquer de faux refus discutables.
AMBIGU = re.compile(r"ollama (pull|rm)|plugin (update|marketplace|install)|uv (sync|add|pip install)|worktree remove|branch -q -d|git branch -[dD]|winget|choco", re.I)
strict = [c for c in cmds if 5 < len(c) < 200 and not SECRET.search(c) and not perso(c) and not AMBIGU.search(c)]
relax = [c for c in cmds if 5 < len(c) < 200 and not SECRET_REL.search(c) and not perso(c) and not AMBIGU.search(c) and c.count("\n") == 0]
print("candidates filtre strict :", len(strict), "; filtre relâché (structure permise) :", len(relax))
if "--stats" in sys.argv:
    sys.exit()
random.seed(80)
# Priorité au filtre strict (celui du premier essai), complété par le relâché pour atteindre 400,
# avec au plus 12 commandes par premier mot pour garder de la variété.
pool = []
seen = set()
for liste in (strict, relax):
    l = [c for c in liste if c not in seen]
    random.shuffle(l)
    for c in l:
        seen.add(c); pool.append(c)
compte = collections.Counter(); out = []
for c in pool:
    mot = re.split(r"\s+", c)[0].lower()
    if compte[mot] >= 14: continue
    compte[mot] += 1; out.append(c)
    if len(out) == 400: break
res = [{"cmd": c, "outil": "PowerShell" if ("PowerShell" in cmds[c] and "Bash" not in cmds[c]) else "Bash", "attendu": "allow", "source": "transcription"} for c in out]
json.dump(res, open("out/inoffensives.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(res), "retenues ;", collections.Counter(r["outil"] for r in res), "; premiers mots :", compte.most_common(15))
