import json,sys
d=json.load(open(sys.argv[1],encoding='utf-8'))
for x in d['issues']:
    l=x.get('location') or {}
    print(x.get('severity'),'|',x.get('id'),x.get('category'),'|',l.get('file'),l.get('start_line'),'|',(x.get('finding') or '')[:80].replace('\n',' '))
print(d['analysis_completeness'] if 'analysis_completeness' in d else '')
