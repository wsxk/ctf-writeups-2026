"""Record actual on-disk progress so interrupted network transfers remain reviewable."""
from pathlib import Path
import hashlib,json,collections
import collect_reverse as c
import collect_reverse_extra as extra
import collect_nctf_more as more
c.configurations();extra.configurations();more.configurations()
rows=[]
for j in c.JOBS:
    p=c.ROOT/j['category']/j['dirname']/c.safe(j['title']);p.mkdir(parents=True,exist_ok=True)
    files=[]
    for f in j['files']:
        q=p/f['local'];g=dict(f)
        if q.exists():
            data=q.read_bytes();g.update(status='downloaded',bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            if f.get('size_expected') is not None and len(data)!=f['size_expected']:g.update(status='invalid',error='expected byte length mismatch')
            if f.get('git_blob_sha') and hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=f['git_blob_sha']:g.update(status='invalid',error='Git blob SHA mismatch')
        else:
            part=q.with_name(q.name+'.part');g.update(status='pending',partial_bytes=part.stat().st_size if part.exists() else 0)
        files.append(g)
    j['files']=files;j['directory']=str(p.relative_to(c.ROOT)).replace('\\','/');j['retrieved_date_beijing']='2026-11-06'
    for kind,label in [('writeups/','writeup'),('attachments/','attachment')]:
        selected=[f for f in files if f['local'].startswith(kind)];good=[f for f in selected if f['status']=='downloaded']
        j[label+'_urls']=[f['url'] for f in selected]
        j[label+'_status']='downloaded' if selected and len(good)==len(selected) else 'partial' if good else 'missing'
    (p/'metadata.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# '+j['title'],'','比赛：'+j['event_title']+'（'+j['event_id']+'）','分类：'+j['category'],'',j['notes'],'','## 来源']+['- '+u for u in j['source_urls']]+['','## 本地状态','',f"Writeup：{j['writeup_status']}；附件：{j['attachment_status']}。",'','实际文件、原URL、大小、SHA-256及未完成项见metadata.json。题目和解题脚本均未执行。']
    pending=[f for f in files if f['status']!='downloaded']
    if pending:lines+=['','以下文件尚未完整下载：']+['- '+f['local'] for f in pending]
    (p/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');rows.append(j)
out={'date_beijing':'2026-11-06','challenge_count':len(rows),'categories':dict(collections.Counter(j['category'] for j in rows)),'event_count':len({j['event_id'] for j in rows}),'downloaded_files':sum(f['status']=='downloaded' for j in rows for f in j['files']),'pending_files':sum(f['status']!='downloaded' for j in rows for f in j['files']),'entries':rows}
(c.ROOT/'sources/reverse_progress_snapshot.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print({k:v for k,v in out.items() if k!='entries'})
