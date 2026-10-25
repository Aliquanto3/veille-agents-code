import subprocess, sys, re
G = r"C:\Users\Utilisateur\Documents\GitHub"
def git(repo, *a):
    return subprocess.run(["git","-C",G + "/" + repo,*a],capture_output=True,text=True,encoding="utf-8",errors="replace").stdout
def keep(p):
    if p.startswith(("_bmad","docs/","content/","data/","demo/")): return False
    return p.endswith(".py") 
repo=sys.argv[1]; n=sys.argv[2]
for line in git(repo,"log","--first-parent","--no-merges" if repo=="wavestack" else "--merges" ,"--format=%h\t%P\t%s","-n",n).splitlines():
    h,par,s=line.split("\t",2)
    p1=par.split()[0] if par else None
    if not p1: continue
    files=git(repo,"diff","--name-only",p1,h).splitlines()
    py=[f for f in files if keep(f)]
    src=[f for f in py if "/tests/" not in "/"+f and not f.startswith("tests/")]
    tst=[f for f in py if f not in src]
    if not src or not tst: continue
    d=git(repo,"diff","-U1",p1,h,"--",*py)
    specs=[f for f in files if f.startswith("_bmad-output") and f.endswith(".md") and ("spec" in f or "story" in f or re.search(r"\d-\d",f))]
    print(h,len(d),len(src),len(tst),s[:70],"|",specs[:2])
