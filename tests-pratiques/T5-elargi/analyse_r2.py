r"""T5 elargi : seconde passe des critiques GPT (memes prompts, memes diffs) ; recalcule leur rappel et les combinaisons avec la chaine (passe unique Claude)."""
import json
from pathlib import Path
from analyse import wilson, pct
T = Path("T:/")
a = json.loads((Path(__file__).parent / "analyse.json").read_text(encoding="utf-8"))
semees = a["semees"]
d1 = json.loads((T / "detections.json").read_text(encoding="utf-8"))
d2 = json.loads((T / "detections_r2.json").read_text(encoding="utf-8"))
c2 = json.loads((T / "constats_r2.json").read_text(encoding="utf-8"))
def hits(det, r):
    return {c["story"] for c in det if c["relecteur"] == r and c["detecte"]}
def imp(det, r):
    return {c["story"] for c in det if c["relecteur"] == r and c["detecte"] and c["important"]}
chaine = hits(d1, "haiku") | hits(d1, "opus")
chaine_i = imp(d1, "haiku") | imp(d1, "opus")
out = {}
for r in ("openai/gpt-6-luna", "openai/gpt-6.1-sol"):
    h1, h2 = hits(d1, r), hits(d2, r)
    out[r] = dict(r1=len(h1), r2=len(h2), union=len(h1 | h2), inter=len(h1 & h2), gain_chaine_r1=sorted(h1 - chaine), gain_chaine_r2=sorted(h2 - chaine),
                  gain_chaine_union=sorted((h1 | h2) - chaine), imp_r2=len(imp(d2, r)),
                  important_r2=sum(c["important"] for c in c2 if c["relecteur"] == r),
                  chaine_plus_r2=len(chaine | h2), chaine_plus_union=len(chaine | h1 | h2))
n = len(semees)
print("chaine", len(chaine), "important", len(chaine_i))
for r, o in out.items():
    print(r, o)
    k = o["chaine_plus_r2"]; print("  chaine + r2 :", k, pct(k / n), wilson(k, n))
json.dump(out, open(Path(__file__).parent / "analyse_r2.json", "w", encoding="utf-8"), indent=1)
