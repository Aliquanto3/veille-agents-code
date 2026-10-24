"""Verifie la presence des 4 modeles et leurs tarifs (liste publique, sans cle)."""
import json
import urllib.request

from cle import lire_cle

IDS = ["openai/gpt-6-luna", "xiaomi/mimo-v2.6-pro", "openai/gpt-6.1-sol", "moonshotai/kimi-k3.1-pro"]
req = urllib.request.Request("https://openrouter.ai/api/v1/models", headers={"Authorization": "Bearer " + lire_cle()})
data = json.load(urllib.request.urlopen(req, timeout=30))["data"]
par_id = {m["id"]: m for m in data}
for i in IDS:
    m = par_id.get(i)
    if not m:
        print(i, "ABSENT")
        continue
    print(i, m.get("context_length"), json.dumps(m.get("pricing")), m.get("supported_parameters", [])[:12])
print("cle presente:", bool(lire_cle()))
