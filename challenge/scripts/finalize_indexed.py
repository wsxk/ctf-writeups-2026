"""Merge verified writeup replacements and correct source-index ambiguities."""
import hashlib,json,shutil
from pathlib import Path
from collect_indexed import ROOT

def save(p,m): p.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
def flat_notes(value):
    if isinstance(value,list):return [s for item in value for s in flat_notes(item)]
    return [str(value)]

def finalize():
    if not (ROOT/'sources/indexed_repair_report.json').exists(): raise RuntimeError('Attachment repair is still running; do not race its metadata writes.')
    # CTFtime's two task lists prove these belong to the autumn edition.
    for name in ['ctf42_index.json','ctf42_selected.json']:
        p=ROOT/'sources'/name; rows=json.loads(p.read_text(encoding='utf-8'))
        for m in rows:
            if '/ctfs/kubstu/2026/' in m.get('url',''):
                m['event_id']='CTF-3446';m['event_title']='KubSTU CTF'
                m['event_match_correction']='Autumn 2026 confirmed by https://ctftime.org/event/3446/tasks/; aggregator linked spring event 3177 incorrectly.'
        save(p,rows)
    mapping=ROOT/'sources/writeup_replacements/mapping.json'
    if mapping.exists():
        data=json.loads(mapping.read_text(encoding='utf-8'))
        records=data if isinstance(data,list) else data.get('records',data.get('replacements',[]))
        for r in records:
            target=ROOT/r['target']
            if target.name!='metadata.json': target=target/'metadata.json'
            if not target.exists(): continue
            m=json.loads(target.read_text(encoding='utf-8'));added=[]
            for f in r.get('files',[]):
                src=ROOT/f['staged_path']
                if not src.exists(): src=Path(f['staged_path'])
                dest=target.parent/f['destination']
                if ROOT.resolve() not in dest.resolve().parents: raise ValueError('Unsafe destination')
                if hashlib.sha256(src.read_bytes()).hexdigest()!=f['sha256']: raise ValueError('Staged writeup hash mismatch')
                dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
                added.append(dict(path=dest.relative_to(ROOT).as_posix(),url=f.get('url',r['url']),bytes=dest.stat().st_size,sha256=f['sha256'],kind='writeup'))
            if added:
                existing={x['path'] for x in m.get('artifacts',[])}
                m.setdefault('artifacts',[]).extend(x for x in added if x['path'] not in existing)
                m['writeup_status']='downloaded'
                if r.get('writeup_kind'):
                    m['writeup_kind']=r['writeup_kind']
                if r.get('notes'):
                    note=r['notes']
                    if isinstance(m.get('notes'),list):m['notes'].extend(flat_notes(note))
                    else:m['notes']=str(m.get('notes',''))+' '+str(note)
                if r['url'] not in m['writeup_urls']:m['writeup_urls'].append(r['url'])
                save(target,m)
    corrections=[]
    for p in ROOT.rglob('metadata.json'):
        m=json.loads(p.read_text(encoding='utf-8')); rel=p.parent.relative_to(ROOT).as_posix()
        if m.get('collector')!='ctf42-public-index' and rel!='虚拟化/DiceCTF_Quals_2026/garden':continue
        if m.get('title')=='rime_scrub' and (ROOT/'sources/rime_scrub_retry.bin').exists():
            src=ROOT/'sources/rime_scrub_retry.bin';dest=p.parent/'attachments/upstream/scrubd'
            data=src.read_bytes()
            if data.startswith(b'\x7fELF'):
                dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
                artifact=dict(path=dest.relative_to(ROOT).as_posix(),url=m['errors'][-1]['url'],bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),kind='attachment')
                if not any(a['path']==artifact['path'] for a in m.get('artifacts',[])):m.setdefault('artifacts',[]).append(artifact)
                m['attachment_status']='downloaded';m['notes'].append('中断的scrubd文件已重试取得并保存哈希。')
        if '/kubstu_2026/' in rel:
            m['event_id']='CTF-3446';m['event_title']='KubSTU CTF'
            m.setdefault('source_urls',[]).append('https://ctftime.org/event/3446/tasks/')
            note='已核对CTFtime秋季赛题表；聚合站的春季赛3177关联错误，改为3446（2026-10-10至11）。'
            if isinstance(m.get('notes'),list):
                if note not in m['notes']:m['notes'].append(note)
            else:m['notes']=str(m.get('notes',''))+' '+note
            corrections.append({'path':rel,'event_id':'CTF-3446'})
        if rel=='虚拟化/DiceCTF_Quals_2026/garden':
            m['category']='虚拟化';m['directory']=rel
            if isinstance(m.get('notes'),list):m['notes'].append('主分类改为虚拟化：自定义VM及垃圾回收漏洞。')
        if rel=='虚拟化/dicectf_2026-quals/garden':m['duplicate_of']='虚拟化/DiceCTF_Quals_2026/garden'
        if rel=='pwn/sekaictf_2026/MTE':m['duplicate_of']='虚拟化/SekaiCTF_2026/MTE'
        m['notes']=list(dict.fromkeys(flat_notes(m.get('notes',[]))))
        m['source_urls']=list(dict.fromkeys(m.get('source_urls',[])))
        save(p,m)
        if m.get('collector')=='ctf42-public-index':
            notes=m.get('notes',[]);notes=[notes] if isinstance(notes,str) else notes
            text=f"# {m['title']}\n\n- 比赛：{m['event_title']}（{m['event_id']}）\n- 分类：{m['category']}\n- writeup：{m['writeup_status']}\n- 附件：{m['attachment_status']}\n"
            if m.get('duplicate_of'):text+='- 同题主目录：['+m['duplicate_of']+'](../../../'+m['duplicate_of']+'/README.md)，本副本不重复计数。\n'
            text+='\n'+'\n'.join(notes)+'\n\n## 来源\n\n'+'\n'.join('- '+u for u in m.get('source_urls',[])+m.get('writeup_urls',[]))+'\n'
            (p.parent/'README.md').write_text(text,encoding='utf-8')
    save(ROOT/'sources/index_corrections.json',corrections)
    print('Merged writeups; corrected editions; marked duplicate source copies.')

if __name__=='__main__': finalize()
