"""Normalise les corps OTLP/JSON reçus par otlp_recepteur.py (ou la sortie console) en
{"metrics": [...], "events": [...], "spans": [...]}, sans données personnelles.

Usage : uv run --no-project python normaliser_otlp.py <recu.jsonl> <sortie.json>
Les métriques OTLP sont en temporalité delta : une ligne par export, à additionner.
"""
import json
import sys

PII = {"user.id", "user.email", "user.account_uuid", "user.account_id", "organization.id",
       "tool_input", "tool_parameters", "workspace.host_paths", "prompt", "prompt_text", "file_path", "full_command"}  # identité et chemins locaux


def val(v):
    k, x = next(iter(v.items()))
    return int(x) if k == "intValue" else x


def attrs(lst):
    return {a["key"]: val(a["value"]) for a in lst or [] if a["key"] not in PII}


def normaliser(path):
    out = {"metrics": [], "events": [], "spans": []}
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        b = r["body"]
        for rm in b.get("resourceMetrics", []):
            for sm in rm["scopeMetrics"]:
                for m in sm["metrics"]:
                    body = m.get("sum") or m.get("gauge")
                    for dp in body["dataPoints"]:
                        v = dp.get("asDouble", dp.get("asInt"))
                        out["metrics"].append({"name": m["name"], "attrs": attrs(dp["attributes"]),
                                               "value": float(v), "temporalite": body.get("aggregationTemporality")})
        for rl in b.get("resourceLogs", []):
            for sl in rl["scopeLogs"]:
                for lr in sl["logRecords"]:
                    out["events"].append({"name": val(lr["body"]), "ts": int(lr["timeUnixNano"]),
                                          "attrs": attrs(lr["attributes"])})
        for rs in b.get("resourceSpans", []):
            for ss in rs["scopeSpans"]:
                for sp in ss["spans"]:
                    out["spans"].append({"name": sp["name"], "id": sp["spanId"], "parent": sp.get("parentSpanId"),
                                         "ms": (int(sp["endTimeUnixNano"]) - int(sp["startTimeUnixNano"])) / 1e6,
                                         "attrs": attrs(sp["attributes"])})
    return out


if __name__ == "__main__":
    o = normaliser(sys.argv[1])
    json.dump(o, open(sys.argv[2], "w", encoding="utf-8"), indent=1)
    print({k: len(v) for k, v in o.items()})
