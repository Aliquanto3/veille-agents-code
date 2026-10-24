"""Extrait des commandes Bash réellement passées (transcriptions locales), filtrées sans secrets."""
import glob, json, os, re, random, sys
sys.stdout.reconfigure(encoding="utf-8")
base = os.path.expanduser("~/.claude/projects")
cmds = {}
for f in glob.glob(base + "/**/*.jsonl", recursive=True):
    try:
        for l in open(f, encoding="utf-8"):
            if '"Bash"' not in l: continue
            try: e = json.loads(l)
            except ValueError: continue
            c = e.get("message", {}).get("content")
            if not isinstance(c, list): continue
            for b in c:
                if b.get("type") == "tool_use" and b.get("name") == "Bash":
                    cmd = b["input"].get("command", "").strip()
                    cmds[cmd] = cmds.get(cmd, 0) + 1
    except OSError: pass
print(len(cmds), "commandes distinctes")
SECRET = re.compile(r"key|token|secret|passw|bearer|authorization|api[_-]?key|OPENROUTER|\.env|credential|ssh|@[a-z0-9.-]+\.[a-z]{2,}|sk-|ghp_|rm |rmdir|del |push|reset|kill|curl|wget|\||>|&&|;|\$\(|`|\n|\n", re.I)
ok = [c for c in cmds if 5 < len(c) < 140 and not SECRET.search(c) and "Utilisateur" not in c.replace("C:/Users/Utilisateur/Documents/GitHub", "")]
print(len(ok), "candidates")
random.seed(8); random.shuffle(ok)
json.dump(ok[:400], open("out/candidats.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
for c in ok[:120]: print(c)
