"""Finish only the already-selected missing large files, using verified ranges."""
import collect_reverse as c
import collect_reverse_extra as extra
import collect_nctf_more as more
from segmented_fetch import fetch
from concurrent.futures import ThreadPoolExecutor,as_completed
import requests,re,json

c.configurations();extra.configurations();more.configurations()
tasks=[]
for j in c.JOBS:
    base=c.ROOT/j['category']/j['dirname']/c.safe(j['title'])
    for f in j['files']:
        dst=base/f['local']
        if not dst.exists():tasks.append((j['title'],dst,f))
print('Remaining files',len(tasks),flush=True)

def one(task):
    title,dst,f=task;size=f.get('size_expected')
    try:
        if size is None:
            with requests.get(f['url'],headers={'Range':'bytes=0-0'},stream=True,timeout=(10,25)) as r:
                r.raise_for_status();size=int(r.headers['Content-Range'].rsplit('/',1)[1])
        print('START',title,f['local'],size,flush=True)
        result=fetch(f['url'],dst,size,workers=6)
        result.update(title=title,local=str(dst.relative_to(c.ROOT)),url=f['url'])
        print('DONE',title,f['local'],flush=True);return result
    except Exception as e:
        print('FAILED',title,str(e),flush=True);return {'title':title,'url':f['url'],'local':str(dst.relative_to(c.ROOT)),'status':'failed','error':str(e)}

results=[]
with ThreadPoolExecutor(max_workers=3) as pool:
    for r in pool.map(one,tasks):
        results.append(r)
        (c.ROOT/'sources/reverse_final_downloads.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print('Finished',len(results),'files',flush=True)
