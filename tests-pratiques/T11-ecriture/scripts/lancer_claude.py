"""Lance une session `claude -p` (nouvelle session) et renvoie texte + métriques.

Format `stream-json --verbose` à la place de `json` : le dernier évènement `result` est le même objet,
et le flux montre en plus les appels d'outils (preuve que la skill a bien été invoquée)."""
import json, os, subprocess, time
from pathlib import Path
from config import MODELE, EFFORT, TOOLS


def analyser_flux(brut: str):
    outils, skills, lus = {}, [], []
    res, meta = None, {}
    for ligne in brut.splitlines():
        try:
            ev = json.loads(ligne)
        except Exception:
            continue
        t = ev.get("type")
        if t == "assistant":
            for b in ev.get("message", {}).get("content", []) or []:
                if b.get("type") == "tool_use":
                    n = b.get("name")
                    outils[n] = outils.get(n, 0) + 1
                    inp = b.get("input") or {}
                    if n == "Skill":
                        skills.append(inp.get("skill") or inp.get("name"))
                    if n == "Read":
                        lus.append(Path(str(inp.get("file_path", ""))).name)
        elif t == "result":
            res = ev
    texte = ""
    if res:
        u = res.get("usage") or {}
        texte = res.get("result") or ""
        meta = {
            "cout_usd": res.get("total_cost_usd"), "tours": res.get("num_turns"),
            "duree_api_ms": res.get("duration_api_ms"), "erreur": res.get("is_error"),
            "sous_type": res.get("subtype"),
            "tokens_in": u.get("input_tokens"), "tokens_out": u.get("output_tokens"),
            "cache_creation": u.get("cache_creation_input_tokens"),
            "cache_read": u.get("cache_read_input_tokens"),
            "modeles": list((res.get("modelUsage") or {}).keys()),
            "refus_permission": [x.get("tool_name") for x in (res.get("permission_denials") or [])],
        }
    meta.update({"outils": outils, "skills_invoquees": skills, "fichiers_lus": lus})
    return texte, meta


def lancer(workdir: Path, prompt: str, *, model=MODELE, effort=EFFORT, tools=TOOLS,
           budget=1.5, timeout=900, extra=()):
    workdir = Path(workdir)
    allowed = [t for t in tools.split(",") if t]
    cmd = ["claude", "-p", "--model", model, "--effort", effort,
           "--setting-sources", "project,local", "--no-chrome", "--strict-mcp-config",
           "--tools", tools, "--permission-mode", "acceptEdits",
           "--permission-prompts", "none", "--max-budget-usd", str(budget),
           "--output-format", "stream-json", "--verbose", "--no-session-persistence"]
    if allowed:
        cmd += ["--allowedTools", ",".join(allowed)]
    cmd += list(extra)
    env = dict(os.environ, NO_COLOR="1", DO_NOT_TRACK="1", NO_UPDATE_NOTIFIER="1")
    t0 = time.time()
    p = subprocess.run(cmd, cwd=workdir, env=env, input=prompt.encode("utf-8"),
                       capture_output=True, timeout=timeout)
    duree = round(time.time() - t0, 1)
    brut = p.stdout.decode("utf-8", errors="replace")
    texte, meta = analyser_flux(brut)
    meta.update({"rc": p.returncode, "duree_s": duree,
                 "stderr": p.stderr.decode("utf-8", errors="replace")[-400:]})
    return texte, meta, brut
