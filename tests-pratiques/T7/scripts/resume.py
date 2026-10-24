import json,sys,collections
for f in sys.argv[1:]:
    d=json.load(open(f,encoding='utf-8'))
    print("==",f,d['risk_assessment'])
    print([k for k in d.keys()])
    fs=d.get('findings') or d.get('issues') or []
    print(len(fs))
    c=collections.Counter((x.get('severity'),x.get('category') or x.get('pattern_id')) for x in fs)
    for k,v in sorted(c.items(),key=lambda kv:-kv[1])[:25]: print(' ',k,v)
