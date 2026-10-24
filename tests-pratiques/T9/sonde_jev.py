"""Sonde l'acces a Jev via OpenRouter (catalogue, puis appels minimaux). Ne journalise jamais la cle."""
import json, urllib.request, urllib.error
from cle import cle_openrouter

K = cle_openrouter()
H = {"Authorization": "Bearer " + K, "Content-Type": "application/json"}


def req(method, url, body=None):
    r = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers=H, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return x.status, x.read().decode()[:600]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]


# catalogue complet (avec cle) : modeles dont l'id contient jev / typesafe
s, t = req("GET", "https://openrouter.ai/api/v1/models")
print("catalogue", s)
try:
    d = json.loads(urllib.request.urlopen(urllib.request.Request("https://openrouter.ai/api/v1/models", headers=H)).read())["data"]
    print([m["id"] for m in d if "jev" in m["id"] or "typesafe" in m["id"]])
except Exception as e:
    print("err", e)
for url in ["https://openrouter.ai/api/v1/models/typesafe/jev-latest/endpoints", "https://openrouter.ai/api/v1/models/~typesafe/jev-latest/endpoints",
            "https://openrouter.ai/api/v1/models/typesafe/jev-1.13/endpoints", "https://openrouter.ai/api/v1/models/typesafe/jev-router/endpoints"]:
    print(url.split("models/")[1], *req("GET", url))
for mid in ["typesafe/jev-latest", "~typesafe/jev-latest", "typesafe/jev-1.13", "typesafe/jev-1.14"]:
    body = {"model": mid, "max_tokens": 5, "messages": [{"role": "user", "content": "ping"}]}
    print(mid, *req("POST", "https://openrouter.ai/api/v1/chat/completions", body))
