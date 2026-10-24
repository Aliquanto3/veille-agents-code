"""Parse la sortie de l'exporteur console OpenTelemetry de Claude Code (littéraux JS, pas du JSON).

Usage : uv run --no-project python parse_console_otel.py <stdout.txt> [--out sortie.json]
Produit un JSON {"metrics": [...], "events": [...]} dont les données personnelles
(email, ids de compte/organisation/utilisateur) sont retirées.
"""
import json
import re
import sys

PII = {"user.id", "user.email", "user.account_uuid", "user.account_id", "organization.id",
       "tool_input", "tool_parameters", "workspace.host_paths", "prompt", "prompt_text", "file_path", "full_command"}  # identité et chemins locaux


def to_json(block: str):
    s = re.sub(r"\bundefined\b", "null", block)
    s = re.sub(r"^(\s*)([A-Za-z_][\w.]*):", r'\1"\2":', s, flags=re.M)  # clés nues
    s = re.sub(r",(\s*[}\]])", r"\1", s)  # virgules finales
    return json.loads(s)


def blocks(text: str):
    cur = []
    for line in text.splitlines():
        if line == "{":
            cur = [line]
        elif cur:
            cur.append(line)
            if line == "}":
                yield "\n".join(cur)
                cur = []


def parse(path: str):
    text = open(path, encoding="utf-8").read()
    metrics, events = [], []
    for b in blocks(text):
        try:
            o = to_json(b)
        except json.JSONDecodeError as e:
            print("bloc ignoré :", e, file=sys.stderr)
            continue
        if "descriptor" in o:
            for dp in o["descriptor"] and o["dataPoints"]:
                a = {k: v for k, v in dp["attributes"].items() if k not in PII}
                metrics.append({"name": o["descriptor"]["name"], "attrs": a, "value": dp["value"],
                                "start": dp["startTime"], "end": dp["endTime"]})
        elif "body" in o:
            a = {k: v for k, v in o["attributes"].items() if k not in PII}
            events.append({"name": o["body"], "ts": o["timestamp"], "attrs": a})
    return {"metrics": metrics, "events": events}


if __name__ == "__main__":
    res = parse(sys.argv[1])
    if "--out" in sys.argv:
        json.dump(res, open(sys.argv[sys.argv.index("--out") + 1], "w", encoding="utf-8"), indent=1)
    print(len(res["metrics"]), "points de métriques,", len(res["events"]), "événements")
