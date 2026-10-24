"""T8 volet 1 : lance les 20 questions sur un modèle (Ollama direct ou Haiku via claude -p).

Usage : uv run --no-project python -I volet1_run.py <ollama:MODELE|haiku> <sortie.jsonl>
Aucun fichier du dépôt n'est modifié ; seuls des extraits sont lus.
"""
import json, subprocess, sys, time, urllib.request, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from questions_lookup import Q, REPO

CONSIGNE = ("Tu réponds à une question factuelle sur du code Python. Appuie-toi uniquement sur les "
            "extraits fournis. Réponds en une ou deux phrases, sans mise en forme, sans préambule.")

FULL = os.environ.get("T8_FULL") == "1"  # variante B : fichiers entiers au lieu d'extraits
NUM_CTX = 16384 if FULL else 8192

def prompt(q):
    parts = [CONSIGNE, ""]
    ex = q["ex"]
    if FULL:
        ex = [(f, 1, 100000) for f in dict.fromkeys(f for f, _, _ in ex)]
    for i, (f, a, b) in enumerate(ex, 1):
        lignes = open(f"{REPO}/{f}", encoding="utf-8").read().splitlines()[a - 1:b]
        parts += [f"### Extrait {i} : {f} (lignes {a} à {b})", "```python", *lignes, "```", ""]
    parts.append("Question : " + q["q"])
    return "\n".join(parts)

def ollama(model, p):
    body = {"model": model, "stream": False, "think": False, "keep_alive": "10m",
            "messages": [{"role": "user", "content": p}],
            "options": {"num_ctx": NUM_CTX, "temperature": 0, "num_predict": 400, "seed": 1}}
    req = urllib.request.Request("http://127.0.0.1:11434/api/chat", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    t0 = time.perf_counter()
    r = json.load(urllib.request.urlopen(req, timeout=300))
    dt = time.perf_counter() - t0
    ev, evd = r.get("eval_count", 0), r.get("eval_duration", 1)
    return dict(answer=r["message"]["content"].strip(), latency_s=dt,
                load_s=r.get("load_duration", 0) / 1e9,
                prompt_tokens=r.get("prompt_eval_count"), out_tokens=ev,
                prompt_s=r.get("prompt_eval_duration", 0) / 1e9, tok_s=ev / (evd / 1e9) if evd else None)

def haiku(p):
    cwd = os.environ["T8_SCRATCH"]
    cmd = ["claude", "-p", "--model", "haiku", "--tools", "", "--no-session-persistence",
           "--disable-slash-commands", "--setting-sources", "", "--output-format", "json"]
    t0 = time.perf_counter()
    r = subprocess.run(cmd, input=p, capture_output=True, text=True, encoding="utf-8", cwd=cwd, timeout=300)
    dt = time.perf_counter() - t0
    j = json.loads(r.stdout)
    u = j.get("usage", {})
    return dict(answer=(j.get("result") or "").strip(), latency_s=dt, api_ms=j.get("duration_api_ms"),
                cost_usd=j.get("total_cost_usd"), in_tokens=u.get("input_tokens"),
                cache_creation=u.get("cache_creation_input_tokens"), cache_read=u.get("cache_read_input_tokens"),
                out_tokens=u.get("output_tokens"), is_error=j.get("is_error"))

if __name__ == "__main__":
    cible, sortie = sys.argv[1], sys.argv[2]
    if cible.startswith("ollama:"):
        m = cible[7:]
        ollama(m, "Réponds OK.")  # préchauffage : le chargement du modèle n'entre pas dans les latences
        f = lambda p: ollama(m, p)
    else:
        f = haiku
    with open(sortie, "w", encoding="utf-8") as out:
        for q in Q:
            res = f(prompt(q))
            res["id"] = q["id"]
            out.write(json.dumps(res, ensure_ascii=False) + "\n"); out.flush()
            print(q["id"], round(res["latency_s"], 2), res["answer"][:90].replace("\n", " "), flush=True)
