"""T8 volet 2 : Claude Code (claude -p) piloté par un modèle local via l'endpoint Anthropic d'Ollama.

Variables posées au seul sous-processus ; aucune configuration de l'utilisateur n'est modifiée.
Usage : uv run --no-project python -I volet2_run.py <nom_essai> <dossier_projet> "<prompt>" [--realiste]
Mesures : temps jusqu'au premier jeton (TTFT, depuis le lancement du processus), durée totale,
erreurs d'appel d'outil (tool_result is_error), RAM système et VRAM échantillonnées toutes les 3 s.
"""
import ctypes, json, os, subprocess, sys, threading, time
sys.stdout.reconfigure(encoding="utf-8")

BASE = os.environ.get("T8_OLLAMA", "http://127.0.0.1:11500")
MODELE = os.environ.get("T8_MODELE", "qwen3.6:35b-a3b")
DELAI = 15 * 60

class MS(ctypes.Structure):
    _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong), ("tot", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong),
                ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong), ("tv", ctypes.c_ulonglong), ("av2", ctypes.c_ulonglong),
                ("ext", ctypes.c_ulonglong)]

def ram_utilisee_go():
    m = MS(); m.l = ctypes.sizeof(MS); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return (m.tot - m.av) / 2**30

def vram_mo():
    try:
        return int(subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                  capture_output=True, text=True, timeout=10).stdout.strip().splitlines()[0])
    except Exception:
        return -1

def main():
    nom, dossier, prompt = sys.argv[1], sys.argv[2], sys.argv[3]
    realiste = "--realiste" in sys.argv
    env = dict(os.environ, ANTHROPIC_BASE_URL=BASE, ANTHROPIC_AUTH_TOKEN="ollama", ANTHROPIC_API_KEY="",
               ANTHROPIC_DEFAULT_HAIKU_MODEL=MODELE, ANTHROPIC_DEFAULT_SONNET_MODEL=MODELE, ANTHROPIC_DEFAULT_OPUS_MODEL=MODELE,
               CLAUDE_CODE_SUBAGENT_MODEL=MODELE, CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1", DISABLE_TELEMETRY="1")
    cmd = ["claude", "-p", "--model", MODELE, "--output-format", "stream-json", "--verbose", "--include-partial-messages",
           "--allowedTools", "Read,Edit,Write,Bash(uv run --no-project python -m unittest*)", "--no-session-persistence"]
    if not realiste:
        cmd += ["--setting-sources", "", "--disable-slash-commands"]
    cmd.append(prompt)
    ech = []; stop = threading.Event()
    def echantillonne():
        while not stop.is_set():
            ech.append((time.perf_counter(), ram_utilisee_go(), vram_mo())); stop.wait(3)
    ram0, vram0 = ram_utilisee_go(), vram_mo()
    threading.Thread(target=echantillonne, daemon=True).start()
    t0 = time.perf_counter()
    p = subprocess.Popen(cmd, cwd=dossier, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    killer = threading.Timer(DELAI, p.kill); killer.start()
    ttft = ttft_init = None; erreurs = []; outils = []; texte = []; res = None; n_ev = 0
    for ligne in p.stdout:
        t = time.perf_counter() - t0
        try:
            e = json.loads(ligne)
        except ValueError:
            continue
        n_ev += 1
        if e.get("type") == "system" and e.get("subtype") == "init" and ttft_init is None:
            ttft_init = t
        if e.get("type") == "stream_event":
            ev = e["event"]
            if ev.get("type") == "content_block_delta" and ttft is None:
                ttft = t
        elif e.get("type") == "assistant":
            for c in e["message"].get("content", []):
                if c.get("type") == "tool_use":
                    outils.append((round(t, 1), c["name"], json.dumps(c["input"], ensure_ascii=False)[:160]))
                if c.get("type") == "text":
                    texte.append(c["text"])
        elif e.get("type") == "user":
            c = e["message"].get("content")
            if isinstance(c, list):
                for b in c:
                    if b.get("type") == "tool_result" and b.get("is_error"):
                        erreurs.append((round(t, 1), str(b.get("content"))[:200]))
        elif e.get("type") == "result":
            res = e
    p.wait(); killer.cancel(); stop.set()
    total = time.perf_counter() - t0
    err = p.stderr.read()[:500]
    sortie = dict(essai=nom, modele=MODELE, realiste=realiste, ttft_s=ttft, init_s=ttft_init, total_s=round(total, 1),
                  code=p.returncode, timeout=total >= DELAI - 1, outils=outils, erreurs_outils=erreurs,
                  ram_base_go=round(ram0, 1), ram_pic_go=round(max(x[1] for x in ech), 1),
                  vram_base_mo=vram0, vram_pic_mo=max(x[2] for x in ech),
                  resultat=(res or {}).get("result", "")[:1500], is_error=(res or {}).get("is_error"),
                  usage=(res or {}).get("usage"), num_turns=(res or {}).get("num_turns"), stderr=err)
    json.dump(sortie, open(f"out/volet2_{nom}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: sortie[k] for k in ("essai", "ttft_s", "init_s", "total_s", "code", "ram_pic_go", "vram_pic_mo", "num_turns", "is_error")}))
    print("OUTILS", outils); print("ERREURS", erreurs); print("RESULTAT", sortie["resultat"][:600]); print("STDERR", err)

main()
