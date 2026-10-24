import json, re, sys
from pathlib import Path
T7 = Path(__file__).resolve().parent.parent
out = {}
for d in sorted((T7 / "arms").iterdir()):
    j = d / "_claude.jsonl"
    if not j.exists(): continue
    refs, scripts_, skill_calls = set(), 0, 0
    for l in j.read_text(encoding="utf-8", errors="replace").splitlines():
        try: e = json.loads(l)
        except Exception: continue
        if e.get("type") != "assistant": continue
        for b in e["message"]["content"]:
            if b.get("type") != "tool_use": continue
            s = json.dumps(b["input"], ensure_ascii=False)
            if b["name"] == "Skill": skill_calls += 1
            for m in re.findall(r"skills[/\\]+(?:hallmark|impeccable|frontend-design)[/\\]+([A-Za-z0-9_./\\-]+)", s):
                m = m.replace("\\\\", "/").replace("\\", "/")
                if m.startswith(("references/", "reference/")): refs.add(m)
                elif m.startswith("scripts/"): scripts_ += 1
    out[d.name] = {"skill_calls": skill_calls, "references_ouvertes": sorted(refs), "n_refs": len(refs), "appels_scripts_skill": scripts_}
    print(d.name, skill_calls, len(refs), scripts_, sorted(refs)[:8])
(Path(r"C:\Users\Utilisateur\Documents\GitHub\veille-agents-code\tests-pratiques\T7\donnees") / "references_ouvertes.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
