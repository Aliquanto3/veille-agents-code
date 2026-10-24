"""Lance une session `claude -p` headless dans un répertoire et enregistre le flux + les métriques."""
import json, os, shutil, subprocess, sys, time
from pathlib import Path

T7 = Path(__file__).resolve().parent.parent
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def env_commun(workdir: Path) -> dict:
    e = dict(os.environ)
    e.update({
        "IMPECCABLE_NO_TELEMETRY": "1",
        "IMPECCABLE_NO_UPDATE_CHECK": "1",
        "IMPECCABLE_NO_STALENESS_CHECK": "1",
        "IMPECCABLE_HOME": str(workdir / ".impeccable-home"),
        "HALLMARK_PUPPETEER": str(T7 / "tools" / "puppeteer"),
        "CHROME_PATH": EDGE,
        "NO_UPDATE_NOTIFIER": "1",
        "DO_NOT_TRACK": "1",
        "NO_COLOR": "1",
    })
    return e

def lancer(workdir: Path, prompt: str, *, model="claude-sonnet-5-5", effort="medium",
           tools="Read,Write,Edit,Glob,Grep,Bash,Skill", allowed=(), extra=(), budget=6.0,
           timeout=2400, env_extra=None, prefix="_claude"):
    workdir = Path(workdir)
    cmd = ["claude", "-p", "--model", model, "--effort", effort,
           "--setting-sources", "project,local", "--no-chrome",
           "--tools", tools, "--permission-mode", "acceptEdits", "--permission-prompts", "none",
           "--max-budget-usd", str(budget), "--output-format", "stream-json", "--verbose",
           "--no-session-persistence"]
    if "--strict-mcp-config" not in extra:
        cmd += ["--strict-mcp-config"]
    if allowed:
        cmd += ["--allowedTools", ",".join(allowed)]
    cmd += list(extra)
    env = env_commun(workdir)
    if env_extra:
        env.update(env_extra)
    t0 = time.time()
    out = open(workdir / f"{prefix}.jsonl", "wb")
    err = open(workdir / f"{prefix}.stderr.txt", "wb")
    p = subprocess.Popen(cmd, cwd=workdir, env=env, stdin=subprocess.PIPE, stdout=out, stderr=err)
    try:
        p.communicate(prompt.encode("utf-8"), timeout=timeout)
        statut = "ok" if p.returncode == 0 else f"rc={p.returncode}"
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
        statut = "timeout"
    duree = time.time() - t0
    out.close(); err.close()
    meta = resume_flux(workdir / f"{prefix}.jsonl")
    meta.update({"statut": statut, "duree_s": round(duree, 1), "cmd": cmd[:2] + ["..."]})
    (workdir / f"{prefix}.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return meta

def resume_flux(path: Path) -> dict:
    res = {}
    outils, skills, erreurs = {}, [], 0
    mcp_calls = {}
    for ligne in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            ev = json.loads(ligne)
        except Exception:
            continue
        t = ev.get("type")
        if t == "assistant":
            for b in ev.get("message", {}).get("content", []):
                if b.get("type") == "tool_use":
                    n = b.get("name")
                    outils[n] = outils.get(n, 0) + 1
                    if n == "Skill":
                        skills.append((b.get("input") or {}).get("skill") or (b.get("input") or {}).get("name"))
        elif t == "user":
            c = ev.get("message", {}).get("content")
            if isinstance(c, list):
                for b in c:
                    if b.get("type") == "tool_result" and b.get("is_error"):
                        erreurs += 1
        elif t == "result":
            u = ev.get("usage", {}) or {}
            res.update({
                "cout_usd": ev.get("total_cost_usd"),
                "tours": ev.get("num_turns"),
                "duree_api_ms": ev.get("duration_api_ms"),
                "tokens_in": u.get("input_tokens"),
                "tokens_out": u.get("output_tokens"),
                "cache_creation": u.get("cache_creation_input_tokens"),
                "cache_read": u.get("cache_read_input_tokens"),
                "erreur": ev.get("is_error"),
                "sous_type": ev.get("subtype"),
                "refus_permission": len(ev.get("permission_denials", []) or []),
                "denials": [d.get("tool_name") for d in (ev.get("permission_denials") or [])][:20],
                "resultat_fin": (ev.get("result") or "")[-600:],
            })
    res["outils"] = outils
    res["skills_invoquees"] = skills
    res["tool_results_en_erreur"] = erreurs
    return res
