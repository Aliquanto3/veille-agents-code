import json
from pathlib import Path
p = Path(__file__).parent / "defauts.json"
d = json.loads(p.read_text(encoding="utf-8"))
cibles = {"d01":["C3"],"d02":["C4"],"d03":["T2"],"d04":["C2"],"d05":["C3"],"d06":["C5"],"d07":["C2"],"d08":["C2"],
          "d09":["C4"],"d10":["C3"],"d11":["C5"],"d12":["C1"],"d13":["C3","T1"],"d14":["C2"],"d15":["T2","C2","C3"],"d16":["C3"]}
for x in d: x["cibles"] = cibles[x["id"]]
p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
