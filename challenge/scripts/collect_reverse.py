"""Download reviewed 2026 reversing challenge sources and public solutions. Never execute them."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests, json, re, hashlib, time
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
EVENTS={e['record_id']:e for e in json.loads((ROOT.parent/'CTF competion/2026_CTF比赛数据.json').read_text(encoding='utf-8'))['events']}
JOBS=[]
REPORT_FILE='reverse_search.json'

def safe(s): return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', s).rstrip(' .')
def tree(repo):
    p=ROOT/'sources'/('reverse_'+repo.split('/')[-1]+'_tree.json')
    if not p.exists(): p=ROOT/'sources/pwn_trees'/(repo.replace('/','__')+'.json')
    if p.exists(): return json.loads(p.read_text(encoding='utf-8'))['tree']
    r=requests.get('https://api.github.com/repos/'+repo+'/git/trees/HEAD?recursive=1',timeout=(10,30));r.raise_for_status();d=r.json()
    p=ROOT/'sources'/('reverse_'+repo.split('/')[-1]+'_tree.json');p.write_text(json.dumps(d,ensure_ascii=False),encoding='utf-8');return d['tree']

def add(event,dirname,title,repo,prefix,select,extras=None,notes=''):
    files=[]
    for x in tree(repo):
        if x['type']!='blob' or not x['path'].startswith(prefix+'/'):continue
        rel=x['path'][len(prefix)+1:];kind=select(rel,x)
        if not kind:continue
        files.append({'url':'https://raw.githubusercontent.com/'+repo+'/HEAD/'+quote(x['path']), 'local':kind+'/'+rel,'size_expected':x.get('size'),'git_blob_sha':x.get('sha')})
    for url,local in extras or []: files.append({'url':url,'local':local})
    JOBS.append(dict(event_id=event,event_title=EVENTS[event]['title'],category='逆向',title=title,
      dirname=dirname,source_urls=['https://github.com/'+repo+'/tree/HEAD/'+quote(prefix)],
      files=files,notes=notes))

def configurations():
    repo='UofTCTF/uoftctf-2026-chals-public'
    titles={'baby-flag-checker':'Baby (Obfuscated) Flag Checker','symbol-of-hope':'Symbol of Hope','ml-connoisseur':'ML Connoisseur','bring-your-own-program':'Bring Your Own Program','rev-wasm-kotlin':'Will u Accept Some Magic?'}
    def uoft(rel,x):
        if rel.endswith('/.gitignore'):return None
        if rel.startswith('solve/'):return 'writeups'
        if rel.startswith('dist/'):
            if rel.startswith('dist/') and 'ml-connoisseur' in x['path'] and rel!='dist/ml-connoisseur.zip':return None
            return 'attachments'
        if rel in ('challenge.yml','README'):return 'attachments'
    for prefix,title in titles.items():
        add('CTF-2969','UofTCTF_2026',title,repo,prefix,uoft,notes='官方赛后仓库。writeups 中保留官方求解脚本；不保证每题都有叙述型解题文章。')
        if prefix=='bring-your-own-program':
            JOBS[-1]['category']='虚拟化';JOBS[-1]['notes']+=' 官方题目描述明确为未知架构模拟器。'
    repo='uclaacm/lactf-archive'
    mapping={'flag-finder':'flag_finder','helm-hell':'helm_hell','lactf-1986':'lactf_1986','ooo':'ooo','starless-c':'starless_c','the-fish':'the_fish','the-three-sat-problem':'three_sat_problem'}
    htree=tree('hax1ng/LACTF2026')
    for slug,third in mapping.items():
        extras=[('https://raw.githubusercontent.com/hax1ng/LACTF2026/HEAD/'+quote(x['path']),'writeups/community/'+x['path'].split('/',2)[2]) for x in htree if x['type']=='blob' and x['path'].startswith('rev/'+third+'/')]
        def la(rel,x):
            if rel.startswith('solve.'):return 'writeups/official'
            if '/' not in rel:return 'attachments'
            if slug=='flag-finder' and rel.startswith('src/'):return 'attachments'
        add('CTF-3015','LA_CTF_2026',slug,repo,'2026/rev/'+slug,la,extras,'官方题目附件，配官方 solver（若有）及参赛者 hax1ng 的文章/脚本。社区文章部分标题误写2025，但本题与官方2026目录的描述和flag一致，已逐题核对（ooo使用Unicode NFC比较）；保留原文。reflection另归虚拟化。')
        if slug=='helm-hell':
            JOBS[-1]['category']='虚拟化';JOBS[-1]['notes']+=' Helm模板实现Brainfuck解释器，归虚拟化专题。'
    repo='srdnlen/srdnlenctf-2026_public'
    for slug,title in [('rev_artistic_warmup','Artistic warmup'),('rev_juice','Rev Juice')]:
        def sr(rel,x):
            if rel=='writeup.md':return 'writeups'
            if rel.startswith('attachments/') or rel in ('description.md','title.txt','authors.txt'):return 'attachments'
        add('CTF-3043','Srdnlen_CTF_2026_Quals',title,repo,slug,sr,notes='官方题目附件和完整官方 writeup。')
    repo='dicegang/dicectf-quals-2026-challenges'
    for slug in ['another-onion','bedtime','explorer']:
        extras=[('https://raw.githubusercontent.com/hax1ng/dicectf2026-writeups/HEAD/rev/'+slug+'/README.md','writeups/community/README.md')]
        def dice(rel,x):
            if rel.startswith(('solution/','solution2/')):return 'writeups/official'
            if slug=='another-onion' and rel=='README.md':return 'writeups/official'
            if rel.startswith(('dist/','rootfs/','scripts/')):return 'attachments'
            if '/' not in rel and not rel.startswith('generated_code_example'):return 'attachments'
        add('CTF-3110','DiceCTF_2026_Quals',slug,repo,'rev/'+slug,dice,extras,'官方题目附件；参赛者 hax1ng 的解题文章；another-onion 另有官方多组解法。')
    repo='BYU-CSA/BYUCTF-2026'
    for slug in ['angr_management','picklerick','rcaas','yara']:
        def byu(rel,x):
            if rel.lower() in ('readme.md','writeup.md') or rel.startswith('solve.'):return 'writeups'
            if rel not in ('angr_management_test',):return 'attachments'
        add('CTF-3247','BYUCTF_2026',slug,repo,'rev/'+slug,byu,notes='官方比赛仓库，README包含Solve章节；保留官方解题脚本及附件。')
    repo='tamuctf/tamuctf-2026'
    archive=json.loads((ROOT/'sources/reverse_tamuctf_archive_files.json').read_text(encoding='utf-8'))
    archive_names={'sun-temple':'Sun_Temple','war-hymn':'War_Hymn','hyper-neighbor':'hyper_neighbor','kitchen-sink':'kitchen_sink','nucleus':'Nucleus'}
    for slug in ['acidity','challenge7','hyper-neighbor','kitchen-sink','nucleus','skretch','sun-temple','war-hymn']:
        def tamu(rel,x):
            if rel.startswith(('ai_solve/','author_solve/','solve/','poc/','scripts/find_solution')) or rel in ('solve.py','solve.c'):return 'writeups'
            if rel.startswith('.'):return None
            return 'attachments'
        extras=[(x['download_url'],'attachments/archived_handout/'+x['name']) for x in archive[archive_names.get(slug,slug)] if x['type']=='file']
        add('CTF-3095','TAMUctf_2026',slug,repo,'rev/'+slug,tamu,extras,notes='官方仓库源码/构建材料及求解脚本，另从sajjadium/ctf-archives的2026目录配对下载原始题包（archived_handout）。未构建或执行。')
        JOBS[-1]['attachment_kind']='original_package_and_official_source'
        JOBS[-1]['source_urls'].append('https://github.com/sajjadium/ctf-archives/tree/main/ctfs/TAMUctf/2026/rev/'+archive_names.get(slug,slug))
    repo='b01lers/b01lers-ctf-2026-public'
    for slug in ['favorite_potato','tiles--ai','shakespeares-revenge']:
        def bo(rel,x):
            if rel.startswith(('sol/','solve/')):return 'writeups'
            if rel.startswith('dist/') or rel=='chal.json':return 'attachments'
        add('CTF-3153','b01lers_CTF_2026',slug,repo,'src/rev/'+slug,bo,notes='官方dist题目包及sol/solve解答目录。模板README未作为writeup。')
        if slug=='favorite_potato':
            JOBS[-1]['category']='虚拟化';JOBS[-1]['notes']+=' 通过模拟器运行6502机器码，归虚拟化专题。'
    repo='PascalCTF/PascalCTF-2026'
    def pascal(rel,x):
        if rel.startswith('attachments/') or rel in ('description.md','title.txt','endpoint.txt'):return 'attachments'
    add('CTF-2767','PascalCTF_2026','Albo delle Eccellenze',repo,'rev04',pascal,
        [('https://blog.maksimhayder.com/posts/pascalctf-2026/','writeups/maksimhayder.html')],
        '官方writeup为TODO占位，未当作解答；配对Maksim Hayder公开文章中的Albo delle Eccellenze章节。HTML保存全文原始快照。官方分类Reverse，解法涉及溢出。')
    repo='team-su/SUCTF-2026'
    for slug in ['SU_Protocol','SU_easygal','SU_revird']:
        def su(rel,x):
            if not x.get('size'):return None
            if rel.startswith(('writeup/','exp/')):return 'writeups'
            if rel.startswith(('attachments/','sourcecode/')):return 'attachments'
        add('CTF-3161','SUCTF_2026',slug,repo,'re/'+slug,su,notes='官方附件、完整writeup（含仓库自带图片）及非空exp。仓库中的0字节占位文件未作为实际内容收录。')
    for slug in ['SU_Lock','SU_MvsicPlayer','SU_West']:
        def suvm(rel,x):
            if not x.get('size'):return None
            if rel.startswith(('writeup/','exp/')):return 'writeups'
            if rel.startswith('attachments/'):return 'attachments'
        add('CTF-3161','SUCTF_2026',slug,'team-su/SUCTF-2026','re/'+slug,suvm,notes='官方原分类Reverse，writeup明确分析自定义VM/虚拟化校验，主分类归虚拟化。附件分片均原样下载，不执行恢复脚本。')
        JOBS[-1]['category']='虚拟化'
    def byuvm(rel,x):
        return 'writeups' if rel=='README.md' else 'attachments'
    add('CTF-3247','BYUCTF_2026','mixed_signals','BYU-CSA/BYUCTF-2026','rev/mixed_signals',byuvm,notes='官方README有Solve章节；Linux信号实现的自定义VM，官方未提供solver。')
    JOBS[-1]['category']='虚拟化'
    for slug in ['kyotoprotocol','indirect-memory-access']:
        def bovm(rel,x):
            if rel.startswith('solve/'):return 'writeups'
            if rel.startswith('dist/') or rel=='chal.json':return 'attachments'
        add('CTF-3153','b01lers_CTF_2026',slug,'b01lers/b01lers-ctf-2026-public','src/rev/'+slug,bovm,notes='官方原分类Reverse，模拟执行/解释器或GBA模拟器相关，归入虚拟化专题。完整官方附件和求解文件。')
        JOBS[-1]['category']='虚拟化'
    def corn(rel,x):
        if rel=='writeup.md':return 'writeups'
        if rel.startswith(('attachments/','src/')) or rel in ('title.txt','description.md','authors.txt'):return 'attachments'
    add('CTF-3043','Srdnlen_CTF_2026_Quals','Cornflake v3.5','srdnlen/srdnlenctf-2026_public','rev_cornflake_v3-5',corn,notes='官方原分类Reverse；VM字节码解密与仿真恶意软件题。题目文件名malware.exe，为CTF样本，仅下载未执行。')
    JOBS[-1]['category']='虚拟化'
    def reflect(rel,x):
        if rel in ('reflection','challenge.yaml'):return 'attachments'
    add('CTF-3015','LA_CTF_2026','reflection','uclaacm/lactf-archive','2026/rev/reflection',reflect,
        [('https://ma4the.github.io/en/posts/rev-reflection-lactf2026/','writeups/ma4the.html')],
        '官方题目二进制，配参赛者ma4the的完整HTML解题文章，题目利用DWARF expression VM。')
    JOBS[-1]['category']='虚拟化'
    add('CTF-2767','PascalCTF_2026','StrangeVM','PascalCTF/PascalCTF-2026','rev03',pascal,
        [('https://vortexopsctf.github.io/writeups/2026/02/05/pascal-ctf-strange-vm/','writeups/vortexops.html')],
        '官方writeup为TODO占位，改存VortexOps参赛队公开完整文章及官方题目附件。文章解法未执行验证。')
    JOBS[-1]['category']='虚拟化'

def download(task):
    target,f=task;dst=target/f['local'];dst.parent.mkdir(parents=True,exist_ok=True)
    for attempt in range(3):
        try:
            if dst.exists():data=dst.read_bytes()
            else:
                part=dst.with_name(dst.name+'.part')
                offset=part.stat().st_size if part.exists() else 0
                headers={'Range':f'bytes={offset}-'} if offset else {}
                with requests.get(f['url'],headers=headers,stream=True,timeout=(10,30)) as r:
                    r.raise_for_status()
                    mode='ab' if r.status_code==206 and offset else 'wb'
                    with part.open(mode) as out:
                        for chunk in r.iter_content(262144):
                            if chunk:out.write(chunk)
                data=part.read_bytes()
            if data.startswith(b'version https://git-lfs.github.com/spec/v1'):raise ValueError('Git LFS pointer, not actual attachment')
            if f.get('size_expected') is not None and len(data)!=f['size_expected']:raise ValueError('size mismatch')
            if f.get('git_blob_sha') and hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=f['git_blob_sha']:raise ValueError('Git blob hash mismatch')
            if b'<!DOCTYPE html>' in data[:100] and not dst.suffix.lower() in ('.html','.htm'):raise ValueError('unexpected HTML')
            if f['local'].startswith('writeups/') and len(data)<15:raise ValueError('empty/placeholder writeup')
            dst.write_bytes(data)
            part=dst.with_name(dst.name+'.part')
            if part.exists():part.unlink()
            return {**f,'status':'downloaded','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
        except Exception as e:
            error=str(e)
            if attempt<2:time.sleep(1)
    return {**f,'status':'failed','error':error}

def main():
    configurations(); all_tasks=[]
    for j in JOBS:
        j['path']=ROOT/j['category']/j['dirname']/safe(j['title']);j['path'].mkdir(parents=True,exist_ok=True)
        all_tasks.extend((j['path'],f) for f in j['files'])
    results={}
    with ThreadPoolExecutor(max_workers=7) as pool:
        futs={pool.submit(download,t):t for t in all_tasks}
        for i,fut in enumerate(as_completed(futs),1):
            t=futs[fut];r=fut.result();results[(str(t[0]),r['local'])]=r
            if i%20==0 or r['status']=='failed':print(i,'/',len(all_tasks),r['status'],r['local'],flush=True)
    report=[]
    for j in JOBS:
        path=j.pop('path');j['files']=[results[(str(path),f['local'])] for f in j['files']]
        good=[f for f in j['files'] if f['status']=='downloaded'];j['writeup_urls']=[f['url'] for f in j['files'] if f['local'].startswith('writeups/')];j['attachment_urls']=[f['url'] for f in j['files'] if f['local'].startswith('attachments/')]
        j['writeup_status']='downloaded' if any(f['local'].startswith('writeups/') for f in good) else 'missing'
        j['attachment_status']='downloaded' if any(f['local'].startswith('attachments/') for f in good) else 'missing'
        j['retrieved_date_beijing']='2026-11-06';j['directory']=str(path.relative_to(ROOT)).replace('\\','/')
        (path/'metadata.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
        lines=['# '+j['title'],'','比赛：'+j['event_title']+'（'+j['event_id']+'）','分类：'+j['category'],'',j['notes'],'','## 来源']+['- '+u for u in j['source_urls']]+['','## 下载结果','',f"- Writeup：{j['writeup_status']}",f"- 附件：{j['attachment_status']}",'','文件的原始URL、字节数、SHA-256及失败原因见 metadata.json。仅存档，未运行题目及求解脚本。']
        for f in j['files']:
            if f['status']=='failed':lines.append('- 未下载：'+f['local']+' — '+f['error'])
        (path/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');report.append(j)
    (ROOT/'sources'/REPORT_FILE).write_text(json.dumps({'date':'2026-11-06','scope':'2026 catalog events; official repositories paired with public solutions and archived handouts','entries':report},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Finished',len(JOBS),'challenges',sum(r['status']=='downloaded' for r in results.values()),'files',sum(r['status']=='failed' for r in results.values()),'failures',flush=True)

if __name__=='__main__':main()
