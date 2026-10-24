"""Croise les survivants de cosmic-ray avec la couverture : un survivant sur une ligne couverte = test sans assertion utile."""
import json, sys, xml.etree.ElementTree as ET
from pathlib import Path
S, R = Path(sys.argv[1]), Path(sys.argv[2])
EQ = {"ReplaceComparisonOperator_Eq_Is", "ReplaceComparisonOperator_Is_Eq", "ReplaceComparisonOperator_IsNot_NotEq",
      "ReplaceComparisonOperator_NotEq_IsNot", "ReplaceComparisonOperator_Is_Eq"}
out = {}
for f in sorted(R.glob("*.json")):
    d = json.loads(f.read_text("utf-8"))
    cov = {}
    xml = S / d["story"] / "coverage.xml"
    for c in ET.parse(xml).getroot().iter("class"):
        fn = c.get("filename").replace("\\", "/")
        cov[fn] = {int(l.get("number")): int(l.get("hits")) for l in c.iter("line")}
    # coverage.xml est relatif a la source ; on compare par suffixe
    def hits(mod, line):
        for fn, lines in cov.items():
            if mod.endswith(fn) or fn.endswith(mod.split("src/")[-1]):
                return lines.get(line)
        return None
    tot = {"effective": 0, "done": 0, "killed": 0, "survived": 0, "pending": 0, "lines": set(), "covered": 0, "uncovered": 0, "eq": 0}
    for m in d["modules"]:
        for k in ("effective", "done", "killed", "survived", "pending"):
            tot[k] += m[k]
        for s in m["survivors"]:
            key = (m["module"], s["line"])
            if s["operator"].split("/")[1] in {e for e in EQ}:
                tot["eq"] += 1
            if key in tot["lines"]:
                continue
            tot["lines"].add(key)
            h = hits(m["module"], s["line"])
            tot["covered" if h else "uncovered"] += 1
    tot["lines"] = len(tot["lines"])
    tot["tests_seconds"] = d["tests_seconds"]; tot["total_seconds"] = d["total_seconds"]
    out[d["story"]] = tot
    print(d["story"], tot)
(R / "croisement.json").write_text(json.dumps(out, indent=1), "utf-8")
