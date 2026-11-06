"""Download indexed public CTF artifacts and writeups; never execute them."""
import concurrent.futures as cf
import hashlib, io, json, re, time, zipfile
from pathlib import Path
from urllib.parse import urlparse, urljoin, unquote
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'sources'
ALIASES={'bearcat':'CTF-3046','bhackari':'CTF-3302','boroctf':'CTF-3309','gpn':'CTF-3041','la':'CTF-3015','lyknctf':'CTF-3280','ritsec':'CTF-3096','scriptctf':'CTF-3052','tjctf':'CTF-3195','trx':'CTF-3141','umdctf':'CTF-3056','bkisc':'CTF-2927','compfest':'CTF-3290','css':'CTF-3434','kbxac':'CTF-3456','uiuctf':'CTF-3148','wreckctf':'CTF-3240'}
OFFICIAL_REV={'CTF-2969','CTF-3015','CTF-3043','CTF-3110','CTF-3153'}
OFFICIAL_PWN={'CTF-2969','CTF-3015','CTF-3043','CTF-3110','CTF-3153'}

def get(url,limit=350*1024*1024):
    for n in range(2):
        try:
            r=requests.get(url,timeout=(15,80))
            r.raise_for_status()
            if len(r.content)>limit: raise ValueError('download size exceeds local limit')
            return r
        except Exception:
            if n: raise
            time.sleep(1)

def safe(s): return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_',s).strip(' .')[:90]

def resolve_ctftime():
    mapping={}
    for path in (SRC/'ctftime_resolve').glob('*.json'):
        obj=json.loads(path.read_text(encoding='utf-8'))
        txt=obj['result']
        for section in txt.split('--------------------------------------------------------------------------------'):
            ids=re.findall(r'https://ctftime.org/writeup/\d+',section)
            urls=re.findall(r'Original writeup[^\n]*?\((https?://[^\s)]+)\)',section)
            urls=[u for u in urls if 'ctftime.org' not in u]
            if not urls:
                body=section.split('Rating:',1)[-1].split('### Comments')[0]
                urls=re.findall(r'【\d+†(https?://[^†】]+)†',body)
                urls=[u for u in urls if 'ctftime.org' not in u and 'ctfti.me' not in u]
            if ids and urls: mapping[ids[0]]=urls[0]
    return mapping

def category(row):
    tags=' '.join(row['tags']).lower()
    title=row['title'].lower()
    if 'android' in tags or 'apk' in title or title.startswith('i_hate_this_app'): return 'android'
    if 'vm' in tags or 'vm' in title: return '虚拟化'
    if row['original_category']=='Pwn': return 'pwn'
    if row['original_category']=='Reverse': return '逆向'
    if any(t in tags for t in ['uart','radio','pcb','ofdm']): return 'iot'
    return None

def writeup(url,folder,artifacts,ordinal):
    if 'github.com/' in url:
        parts=unquote(urlparse(url).path).strip('/').split('/')
        if len(parts)>=5 and parts[2] in ('blob','tree'):
            owner,repo,kind,branch=parts[:4]; path='/'.join(parts[4:])
            raw=f'https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}'
            candidates=[(raw,Path(path).name)] if kind=='blob' else [(raw+'/'+n,n) for n in ['README.md','readme.md','WRITEUP.md','writeup.md','README.MD']]
            for u,name in candidates:
                try:
                    r=get(u)
                    if len(r.content)<100 or r.content.strip().lower() in [b'# todo',b'todo']: continue
                    dest=folder/f'{ordinal}_{safe(name)}'
                    dest.write_bytes(r.content)
                    artifacts.append(dict(path=dest.relative_to(ROOT).as_posix(),url=u,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),kind='writeup'))
                    return True
                except Exception: pass
            # Some directory writeups have a challenge-specific Markdown filename.
            try:
                html=get(url).text
                paths=list(dict.fromkeys(re.findall(r'"path":"([^"\n]+\.(?:md|MD))"',html)))
                for p in paths:
                    if not p.startswith(path+'/'): continue
                    u=f'https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{p}'
                    r=get(u)
                    if len(r.content)<100: continue
                    dest=folder/f'{ordinal}_{safe(Path(p).name)}'; dest.write_bytes(r.content)
                    artifacts.append(dict(path=dest.relative_to(ROOT).as_posix(),url=u,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),kind='writeup'))
                    return True
            except Exception: pass
        return False
    if 'ctftime.org' in url: return False
    try:
        r=get(url)
        s=BeautifulSoup(r.content,'html.parser')
        if len(s.get_text(' ',strip=True))<500: return False
        dest=folder/f'{ordinal}_writeup.html'; dest.write_bytes(r.content)
        artifacts.append(dict(path=dest.relative_to(ROOT).as_posix(),url=url,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),kind='writeup'))
        article=s.find('article') or s.find('main') or s.body or s
        for el in article.select('script,style,nav,footer,header'): el.decompose()
        text=article.get_text('\n',strip=True)
        (folder/f'{ordinal}_writeup.txt').write_text('Source: '+url+'\n\n'+text,encoding='utf-8')
        return True
    except Exception: return False

def collect(row):
    cat=row['category']; slug=row['url'].split('/ctfs/')[1].strip('/').split('/')
    folder=ROOT/cat/(slug[0]+'_'+slug[1])/safe(row['title'])
    meta_path=folder/'metadata.json'
    if meta_path.exists(): return dict(title=row['title'],status='existing',path=str(folder))
    folder.mkdir(parents=True,exist_ok=True)
    for name in ['attachments','writeups']: (folder/name).mkdir(exist_ok=True)
    artifacts=[]; errors=[]; gotwu=False
    for idx,u in enumerate(row['resolved_writeup_urls'],1):
        gotwu=writeup(u,folder/'writeups',artifacts,idx) or gotwu
    gotfiles=False
    for idx,u in enumerate(row['download_urls'],1):
        try:
            r=get(u)
            if not zipfile.is_zipfile(io.BytesIO(r.content)): raise ValueError('response is not a ZIP archive')
            z=zipfile.ZipFile(io.BytesIO(r.content))
            listing=[{'name':i.filename,'bytes':i.file_size,'crc32':hex(i.CRC)} for i in z.infolist()]
            # An archive containing only README is not a challenge attachment.
            real=[i for i in z.infolist() if not i.is_dir() and Path(i.filename).name.lower() not in ['readme.md','license','license.md','.gitkeep']]
            if not real: raise ValueError('archive contains only documentation; no handout payload')
            dest=folder/'attachments'/f'handout_{idx}.zip'; dest.write_bytes(r.content)
            artifacts.append(dict(path=dest.relative_to(ROOT).as_posix(),url=u,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),kind='attachment'))
            (folder/'attachments'/f'handout_{idx}_contents.json').write_text(json.dumps(listing,ensure_ascii=False,indent=2),encoding='utf-8')
            gotfiles=True
        except Exception as e: errors.append({'url':u,'error':str(e)})
    notes=['来源为公开作者writeup及公开题目镜像；未经运行验证。','题目ZIP保留原目录；contents.json列出压缩包成员。']
    if cat=='虚拟化': notes.append('本题按标签归为虚拟机/字节码/虚拟化逆向或VM漏洞；不等同于宿主机/Hypervisor逃逸。')
    if cat=='iot': notes.append('按嵌入式硬件、无线协议或PCB分析归入IoT相关题；赛事原分类为Hardware。')
    meta={k:row[k] for k in ['event_id','event_title','title']}
    meta.update(category=cat,original_category=row['original_category'],tags=row['tags'],source_urls=[row['url'],row['edition_url']]+row['handout_urls'],writeup_urls=row['resolved_writeup_urls'],attachment_urls=row['handout_urls']+row['download_urls'],writeup_status='downloaded' if gotwu else 'unavailable',attachment_status='downloaded' if gotfiles else 'unavailable',notes=notes,artifacts=artifacts,errors=errors,collector='ctf42-public-index',retrieved_date='2026-11-06')
    meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    desc=f"# {row['title']}\n\n- 比赛：{row['event_title']}（{row['event_id']}）\n- 分类：{cat}；原分类：{row['original_category']}\n- writeup：{'已下载' if gotwu else '已找到链接，正文下载未成功'}\n- 题目附件：{'已下载ZIP' if gotfiles else '未取得可下载附件'}\n\n"+'\n'.join(notes)+'\n\n## 来源\n\n'+'\n'.join('- '+u for u in meta['source_urls']+meta['writeup_urls'])+'\n'
    (folder/'README.md').write_text(desc,encoding='utf-8')
    return dict(title=row['title'],event_id=row['event_id'],category=cat,writeup=gotwu,attachment=gotfiles,errors=errors)

if __name__=='__main__':
    rows=json.loads((SRC/'ctf42_index.json').read_text(encoding='utf-8'))
    events={e['record_id']:e for e in json.loads((ROOT.parent/'CTF competion'/'2026_CTF比赛数据.json').read_text(encoding='utf-8'))['events']}
    resolved=resolve_ctftime(); (SRC/'ctftime_original_urls.json').write_text(json.dumps(resolved,ensure_ascii=False,indent=2),encoding='utf-8')
    selected=[]; skipped=[]
    for row in rows:
        slug=row['edition_url'].split('/ctfs/')[1].split('/')[0]
        if 'event_id' not in row and slug in ALIASES:
            row['event_id']=ALIASES[slug]; row['event_title']=events[row['event_id']]['title']; row['match_method']='manual-name-and-2026-edition'
        row['category']=category(row)
        if 'event_id' not in row or not row['category']:
            skipped.append(dict(title=row['title'],reason='unmatched event or category outside scope')); continue
        if (row['category']=='逆向' and row['event_id'] in OFFICIAL_REV) or (row['category']=='pwn' and row['event_id'] in OFFICIAL_PWN):
            skipped.append(dict(title=row['title'],reason='handled by official repository collector')); continue
        row['resolved_writeup_urls']=[resolved.get(u,u) for u in row['writeup_urls']]
        selected.append(row)
    (SRC/'ctf42_selected.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding='utf-8')
    (SRC/'ctf42_exclusions.json').write_text(json.dumps(skipped,ensure_ascii=False,indent=2),encoding='utf-8')
    results=[]
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(collect,selected):
            results.append(r); print(json.dumps(r,ensure_ascii=False),flush=True)
    (SRC/'ctf42_download_report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
