import concurrent.futures as cf
import hashlib,json,pathlib,re,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import collect_pwn as c
ROOT=c.ROOT

def save(base,repo,path,rel,kind,blob=None):
    url=c.raw(repo,path);data=c.get(url)
    if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
        oid=re.search(rb'oid sha256:([0-9a-f]+)',data).group(1).decode()
        url=url.replace('raw.githubusercontent.com/','media.githubusercontent.com/media/')
        data=c.get(url)
        assert hashlib.sha256(data).hexdigest()==oid
    elif blob:
        assert hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()==blob['sha']
    dest=base/kind/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    return dict(path=dest.relative_to(base).as_posix(),url=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),kind=kind)

def fun():
    repo='marlithor-cyber/0xfun-2026-writeups'
    tree=json.loads((ROOT/'sources/pwn_trees/marlithor-cyber__0xfun-2026-writeups.json').read_text())
    mapping=[('67_revenge',['67_revenge'],'67_revenge'),('Warden',['Warden'],'Warden'),('bit_flips',['bit_flips'],'bit_flips'),('Fridge',['fridge'],'Fridge'),('What you have',['what'],'What_you_have'),('phantom',['phantom','phantom_pwn'],None)]
    for title,wu_dirs,archive in mapping:
        base=ROOT/'pwn/0xFUN_CTF_2026'/title;base.mkdir(parents=True,exist_ok=True)
        jobs=[];artifacts=[];errors=[]
        for d in wu_dirs:
            for b in tree['tree']:
                prefix='pwn/'+d+'/'
                if b['type']=='blob' and b['path'].startswith(prefix):jobs.append((base,repo,b['path'],d+'/'+b['path'][len(prefix):],'writeups',b))
        if archive:
            archive_tree=json.loads((ROOT/'sources/pwn_trees'/('0xfun_'+archive+'.json')).read_text())
            for b in archive_tree['tree']:
                if b['type']=='blob':jobs.append((base,'sajjadium/ctf-archives','ctfs/0xFUN/2026/pwn/'+archive+'/'+b['path'],b['path'],'attachments',b))
        def download(args):
            try:return save(*args)
            except Exception as ex:return {'error':str(ex),'path':args[2]}
        with cf.ThreadPoolExecutor(max_workers=6) as e:
            for a in e.map(download,jobs):(errors if 'error' in a else artifacts).append(a)
        meta={'event_id':'CTF-3081','event_title':c.EVENTS['CTF-3081']['title'],'category':'pwn','title':title,
              'source_urls':[f'https://github.com/{repo}/tree/main/pwn/'+d for d in wu_dirs]+(['https://github.com/sajjadium/ctf-archives/tree/main/ctfs/0xFUN/2026/pwn/'+archive] if archive else [])+['https://ctftime.org/event/3081/'],
              'writeup_urls':[a['url'] for a in artifacts if a['kind']=='writeups'],
              'attachment_urls':[a['url'] for a in artifacts if a['kind']=='attachments'],
              'writeup_status':'已下载参赛者正文及解题脚本','attachment_status':'已下载题目镜像附件' if archive and not errors else '未找到可下载的题目附件' if not archive else '部分下载失败',
              'notes':['writeup来自解题者原始仓库；附件来自CTF Archives镜像。只保存文件，未执行。']+(['phantom与phantom_pwn为同一内核模块题的静态泄漏解法和实际漏洞利用解法，合并为一题；作者说明本地包flag存在差异。'] if not archive else []),
              'artifacts':artifacts,'download_errors':errors,'has_verified_solution':True,'attachment_complete':bool(archive and not errors)}
        (base/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
        (base/'README.md').write_text(f'# {title}\n\n比赛：0xFUN CTF 2026（CTF-3081）\n\n类别：pwn\n\n解答：{meta["writeup_status"]}\n\n附件：{meta["attachment_status"]}\n\n'+ '\n'.join('- '+x for x in meta['source_urls'])+'\n\n'+'\n'.join(meta['notes'])+'\n',encoding='utf8')
        print(title,len(artifacts),errors,flush=True)

def tamu():
    tree=json.loads((ROOT/'sources/pwn_trees/ACM-VIT__z0d1ak-writeups.json').read_text())
    dirs={'Goodbye libc':'goodbye-libc','Task Manager':'task-manager','meep':'meep','military-system':'military-system','zagjail':'zagjail'}
    for upstream,local in dirs.items():
        base=ROOT/'pwn/TAMUctf_2026'/local
        meta=json.loads((base/'metadata.json').read_text(encoding='utf8'))
        for b in tree['tree']:
            if b['type']=='blob' and b['path'].startswith('TAMUctf 2026/pwn/'+upstream+'/') and b['path'].endswith('.tar.gz'):
                try:
                    a=save(base,'ACM-VIT/z0d1ak-writeups',b['path'],'original_distribution/'+b['path'].split('/')[-1],'attachments',b)
                    meta['artifacts']=[x for x in meta['artifacts'] if x['path']!=a['path']]+[a]
                    meta['attachment_urls']=list(dict.fromkeys(meta['attachment_urls']+[a['url']]))
                    meta['notes'].append('补充的 original_distribution/*.tar.gz 是参赛队保存的原分发包镜像，LFS SHA-256已校验。')
                    print('TAMU archive',local,a['bytes'],flush=True)
                except Exception as ex:
                    meta['download_errors'].append({'url':c.raw('ACM-VIT/z0d1ak-writeups',b['path']),'error':str(ex),'kind':'supplemental_attachment'})
        (base/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')

def pending():
    for base in list((ROOT/'pwn/Undutmaning_2026').glob('*'))+[ROOT/'pwn/SUCTF_2026/SU_fullchian']:
        file=base/'metadata.json'
        if not file.exists():continue
        m=json.loads(file.read_text(encoding='utf8'));m['has_verified_solution']=False;m['writeup_status']='未取得有效writeup：上游解答为空占位/模板'
        if base.name=='SU_fullchian':
            m['attachment_status']='未下载完整环境；26,374,590,293字节7z已停止，因未找到有效writeup'
            m['attachment_complete']=False
            m['notes'].append('Google Drive实际可公开下载，但该题不满足已有writeup的收录条件，停止大文件下载。attachment.7z.part为65,011,712字节不完整临时文件，删除被自动审批策略拒绝，不能解压当作题目包。')
        m['prose_files']=[]
        file.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')
        (base/'README.md').write_text(f'# {m["title"]}（待补）\n\n比赛：{m["event_title"]}（{m["event_id"]}）\n\n{m["writeup_status"]}。不计入已收录有效解答题数。\n\n附件：{m["attachment_status"]}\n\n'+'\n'.join('- '+x for x in m['source_urls'])+'\n\n'+'\n'.join(m['notes'])+'\n',encoding='utf8')
    f=ROOT/'sources/pwn_fullchain_download.json'
    m=json.loads(f.read_text(encoding='utf8'));m.update(status='stopped_out_of_scope_no_writeup',bytes_downloaded=65011712,partial_cleanup_status='自动审批拒绝删除：blocked by policy，未重试');f.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':
    pending();fun();tamu()
