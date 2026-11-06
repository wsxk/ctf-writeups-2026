"""Verify downloaded bytes and archives, without executing challenge files."""
from pathlib import Path
import hashlib,json,zipfile,tarfile,collections
ROOT=Path(__file__).resolve().parents[1]
report=json.loads((ROOT/'sources/reverse_progress_snapshot.json').read_text(encoding='utf-8'))
results=[]
for j in report['entries']:
    base=ROOT/j['directory'];errors=[];archives=[]
    for f in j['files']:
        p=base/f['local']
        if f['status']!='downloaded':errors.append(f['local']+': '+f['status']);continue
        if not p.exists():errors.append(f['local']+': missing');continue
        data=p.read_bytes()
        if len(data)!=f['bytes'] or hashlib.sha256(data).hexdigest()!=f['sha256']:errors.append(f['local']+': checksum mismatch')
        try:
            if p.suffix=='.zip':
                with zipfile.ZipFile(p) as z:
                    bad=z.testzip()
                    archives.append({'file':f['local'],'members':len(z.infolist()),'crc_error':bad})
                    if bad:errors.append(f['local']+': ZIP CRC error '+bad)
            elif p.name.endswith('.tar.gz'):
                with tarfile.open(p,'r:gz') as t:
                    members=t.getmembers();archives.append({'file':f['local'],'members':len(members),'readable':True})
        except Exception as e:errors.append(f['local']+': archive '+str(e))
    results.append({'event_id':j['event_id'],'title':j['title'],'category':j['category'],'directory':j['directory'],'file_count':len(j['files']),'archives':archives,'errors':errors})
out={'date_beijing':'2026-11-06','challenge_count':len(results),'categories':dict(collections.Counter(x['category'] for x in results)),'event_count':len({x['event_id'] for x in results}),'file_count':sum(x['file_count'] for x in results),'bytes':sum(f.get('bytes',0) for j in report['entries'] for f in j['files']),'error_count':sum(len(x['errors']) for x in results),'results':results}
(ROOT/'sources/reverse_validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print({k:v for k,v in out.items() if k!='results'})
for x in results:
    if x['errors']:print(x['title'],x['errors'])
