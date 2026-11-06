"""Download public 2026 Pwn challenges and author solutions; never execute them."""
import concurrent.futures as cf
import hashlib
import json
import pathlib
import re
import time
from urllib.parse import quote
import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVENTS = {e['record_id']: e for e in json.loads((ROOT.parent/'CTF competion'/'2026_CTF比赛数据.json').read_text(encoding='utf8'))['events']}
SPECS = [
    ('UofTCTF/uoftctf-2026-chals-public','CTF-2969','UofTCTF_2026',['aes-aead','babybof','calculator','eebpf','uprobe']),
    ('PascalCTF/PascalCTF-2026','CTF-2767','PascalCTF_2026',['pwn01','pwn02','pwn03','pwn04','pwn05']),
    ('uclaacm/lactf-archive','CTF-3015','LACTF_2026','2026/pwn/'),
    ('dicegang/dicectf-quals-2026-challenges','CTF-3110','DiceCTF_Quals_2026',['pwn/bytecrusher','pwn/garden','pwn/message-store']),
    ('tamuctf/tamuctf-2026','CTF-3095','TAMUctf_2026','pwn/'),
    ('b01lers/b01lers-ctf-2026-public','CTF-3153','b01lers_CTF_2026','src/pwn/'),
    ('BYU-CSA/BYUCTF-2026','CTF-3247','BYUCTF_2026','pwn/'),
    ('srdnlen/srdnlenctf-2026_public','CTF-3043','Srdnlen_CTF_2026',['pwn_common_offset','pwn_echo','pwn_linx','pwn_registered_stack']),
    ('team-su/SUCTF-2026','CTF-3161','SUCTF_2026',['pwn/SU_Box','pwn/SU_Chronos_Ring','pwn/SU_Chronos_Ring1','pwn/SU_evbuffer','pwn/SU_fullchian','pwn/SU_minivfs']),
    ('BSidesSF/ctf-2026-release','CTF-3108','BSidesSF_CTF_2026',['blockman-builder','if-it-leads','inheritance','nameme','readme','readwritecallme','readwriteme','rugdoctor','wromwarp']),
]
SEARCH_QUERIES = [
 '2026 CTF pwn official writeups github LACTF UofTCTF',
 '2026 CTF challenges pwn solution github PascalCTF KnightCTF',
 'site:github.com "2026" "lactf" challenges',
 'site:github.com "2026" "PascalCTF" pwn',
 'site:github.com "2026" "UofTCTF" challenges solutions',
 'site:github.com "2026" "DiceCTF" pwn',
 '"2026" "pwn" "TAMUctf" github challenges',
 '"2026" "pwn" "UMDCTF" github challenges',
 '"2026" "pwn" "BITSCTF" github challenges',
 'site:github.com "TAMUctf 2026" "challenges"',
 'site:github.com "UMDCTF-2026"', 'site:github.com "BITSCTF-2026"',
 'site:github.com "BYUCTF 2026" challenges',
 'site:github.com "2026" "pwn" "squ1rrel" challenges',
 'site:github.com "2026" "pwn" "UMD-CSEC"',
 'site:github.com "2026" "pwn" "BITSkrieg"',
 'site:github.com "2026" "pwn" "Kalmar" challenges',
]

def raw(repo, path):
    return f'https://raw.githubusercontent.com/{repo}/HEAD/{quote(path, safe="/")}'

def get(url):
    for attempt in range(3):
        try:
            r=requests.get(url,timeout=(20,120));r.raise_for_status();return r.content
        except Exception:
            if attempt==2:raise
            time.sleep(attempt+1)

def is_solution(rel):
    parts=pathlib.PurePosixPath(rel).parts
    return any(x.lower() in ('solve','sol','solution','solutions','writeup','writeups','checker','exp') for x in parts[:-1]) or bool(re.match(r'(solve|solver|exploit|exp|writeup)([._-]|$)', parts[-1].lower()))

def safe(s):
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',s).strip(' .')

def main():
    records=[]
    for repo,event_id,folder,prefixes in SPECS:
        treefile=ROOT/'sources'/'pwn_trees'/(repo.replace('/','__')+'.json')
        if not treefile.exists():
            treefile.parent.mkdir(parents=True,exist_ok=True)
            treefile.write_bytes(get(f'https://api.github.com/repos/{repo}/git/trees/HEAD?recursive=1'))
        tree=json.loads(treefile.read_text(encoding='utf8'))
        if tree.get('truncated'):raise RuntimeError('Truncated repository tree: '+repo)
        blobs=[b for b in tree['tree'] if b['type']=='blob']
        if isinstance(prefixes,str):
            prefixes=sorted({prefixes+b['path'][len(prefixes):].split('/')[0] for b in blobs if b['path'].startswith(prefixes) and '/' in b['path'][len(prefixes):]})
        for prefix in prefixes:
            selected=[b for b in blobs if b['path'].startswith(prefix+'/')]
            title=prefix.split('/')[-1]
            if repo.startswith(('Pascal','srdnlen')):
                title=get(raw(repo,prefix+'/title.txt')).decode('utf8').strip()
            base=ROOT/'pwn'/folder/safe(title)
            base.mkdir(parents=True,exist_ok=True)
            artifacts=[];errors=[];jobs=[];omitted=[]
            for b in selected:
                rel=b['path'][len(prefix)+1:]
                # Avoid redundant expanded initramfs; the original image is retained.
                if '/solve/initrd/' in b['path'] or b.get('size',0)>300_000_000:
                    omitted.append({'path':b['path'],'reason':'redundant expanded initramfs or oversized build artifact'});continue
                kind='writeups' if is_solution(rel) else 'attachments'
                if pathlib.PurePosixPath(rel).name.lower()=='readme.md':
                    kind='writeups'  # official README can contain both prompt and solution
                jobs.append((b,rel,kind))
            def download(job):
                b,rel,kind=job
                dest=base/kind/rel
                url=raw(repo,b['path'])
                try:
                    data=dest.read_bytes() if dest.exists() else get(url)
                    lfs=False
                    if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
                        pointer=data.decode();url=f'https://media.githubusercontent.com/media/{repo}/HEAD/{quote(b["path"],safe="/")}'
                        data=get(url);lfs=True
                        expected=re.search(r'oid sha256:([0-9a-f]+)',pointer).group(1)
                        if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('LFS SHA256 mismatch')
                    if not data:raise ValueError('empty download')
                    if not lfs:
                        actual=hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
                        if actual!=b['sha']:
                            pointer=get(url)
                            if pointer.startswith(b'version https://git-lfs.github.com/spec/v1'):
                                expected=re.search(rb'oid sha256:([0-9a-f]+)',pointer).group(1).decode()
                                if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Cached LFS SHA256 mismatch')
                                lfs=True
                                url=f'https://media.githubusercontent.com/media/{repo}/HEAD/{quote(b["path"],safe="/")}'
                            else:raise ValueError('Git blob SHA1 mismatch')
                    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
                    return {'path':str(dest.relative_to(base)).replace('\\','/'),'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'git_blob_sha1':b['sha'],'git_mode':b['mode'],'kind':kind,'lfs_resolved':lfs}
                except Exception as ex:
                    return {'error':str(ex),'url':url,'path':rel,'kind':kind}
            with cf.ThreadPoolExecutor(max_workers=8) as pool:
                for result in pool.map(download,jobs):
                    (errors if 'error' in result else artifacts).append(result)
            # Full independent writeups supplement the official exploit-only solutions.
            if repo.startswith('dicegang'):
                for filename in ['README.md','solve.py']:
                    url=raw('hax1ng/dicectf2026-writeups',prefix+'/'+filename)
                    try:
                        data=get(url);dest=base/'writeups'/'community'/filename;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
                        artifacts.append({'path':str(dest.relative_to(base)).replace('\\','/'),'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'kind':'writeups'})
                    except Exception as ex:
                        if filename=='README.md':errors.append({'url':url,'error':str(ex),'kind':'writeups'})
            # Determine whether the local README is a real explanation, not only a prompt.
            prose=[]
            for a in artifacts:
                if a['kind']=='writeups' and pathlib.Path(a['path']).suffix.lower() in ('.md','.txt'):
                    text=(base/a['path']).read_text(encoding='utf8',errors='replace')
                    sections=re.split(r'(?im)^#{1,5}\s+(?:write.?up|solve|solution)\s*$',text,maxsplit=1)
                    body=sections[-1] if len(sections)>1 else text
                    body=re.sub(r'(?m)^\s*(?:#{1,6}.*|```.*)\s*$','',body).strip()
                    if len(body)>60 and re.search(r'(?i)solution|write.?up|exploit|buffer overflow|## solve|# solve|tcache|ret2|ROP|format string',text):prose.append(a['path'])
            sols=[a for a in artifacts if a['kind']=='writeups' and is_solution(a['path'].split('/',1)[1]) and pathlib.Path(a['path']).suffix in ('.py','.c','.zag','.rb','.sh')]
            valid=bool(prose or sols)
            meta={'event_id':event_id,'event_title':EVENTS[event_id]['title'],'category':'pwn','title':title,'source_urls':[f'https://github.com/{repo}/tree/HEAD/{quote(prefix,safe="/")}',*EVENTS[event_id]['sources']],
              'writeup_urls':[a['url'] for a in artifacts if a['kind']=='writeups'], 'attachment_urls':[a['url'] for a in artifacts if a['kind']=='attachments'],
              'writeup_status':('已下载正文及解题脚本' if prose and sols else '已下载正文' if prose else '已下载官方解题脚本（未找到独立长篇正文）' if sols else '仅题面，未确认writeup'),
              'attachment_status':'已下载（存在失败文件，见download_errors）' if any(e['kind']=='attachments' for e in errors) else '已下载官方题目附件/源码',
              'notes':['未执行题目、solver、容器或二进制。','attachments 保留公开仓库原目录；有dist/zip时为原始分发包，其余为官方公开源码/部署文件。','README可同时含题面与解答；纯solver与文字writeup在状态字段分别标记。'],
              'repository':repo,'repository_tree_sha':tree['sha'],'artifacts':artifacts,'download_errors':errors,'omitted_files':omitted,'has_verified_solution':valid,'prose_files':prose}
            (base/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
            (base/'README.md').write_text(f'# {title}\n\n比赛：{EVENTS[event_id]["title"]}（{event_id}）\n\n类别：pwn\n\n解答状态：{meta["writeup_status"]}\n\n附件状态：{meta["attachment_status"]}\n\n来源：{meta["source_urls"][0]}\n\n- `attachments/`：公开题目分发附件、源码和运行环境。\n- `writeups/`：作者说明、官方解题脚本与补充writeup。\n- `metadata.json`：逐文件URL、SHA-256、大小、下载错误与省略项。\n\n只下载保存，未运行。上游Git符号链接按链接内容保存为普通文件，原始mode记录在metadata。\n',encoding='utf8')
            records.append({'event_id':event_id,'event_title':EVENTS[event_id]['title'],'title':title,'path':str(base.relative_to(ROOT)).replace('\\','/'),'files':len(artifacts),'bytes':sum(a['bytes'] for a in artifacts),'errors':errors,'has_verified_solution':valid})
            print(f'{folder}/{title}: {len(artifacts)} files, {len(errors)} errors, solution={valid}',flush=True)
    log={'date_beijing':'2026-11-06','search_queries':SEARCH_QUERIES,'repositories':[{'repository':s[0],'event_id':s[1]} for s in SPECS], 'records':records,
         'additional_checks':[{'event_id':'CTF-2983','repository':'kalmarunionenctf/kalmarctf','result':'2026/pwn only contains .gitkeep; no public Pwn files collected from this repository'},
         {'event_id':'CTF-3056','result':'Searched UMDCTF 2026; guessed official repository UMD-CSEC/UMDCTF-2026-Challenges returned 404. Other collection agent handles found community sources.'},
         {'event_id':'CTF-3122','result':'Searched BITSCTF 2026; guessed BITSkrieg/BITSCTF-2026 returned 404. Other collection agent handles found community sources.'}]}
    out=ROOT/'sources'/'pwn_search.json'
    if out.exists():
        previous=json.loads(out.read_text(encoding='utf8'))
        merged={r['path']:r for r in previous.get('records',[])}
        merged.update({r['path']:r for r in records});log['records']=list(merged.values())
        log['repositories']=list({r['repository']+r['event_id']:r for r in previous.get('repositories',[])+log['repositories']}.values())
    out.write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':main()
