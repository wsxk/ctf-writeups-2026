"""Download selected 2026 CTF IoT, automotive, Android, and QEMU materials.
Only downloads bytes; never runs challenge binaries or solver code.
"""
import concurrent.futures, hashlib, json, re, time
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
EVENTS = {x['record_id']:x for x in json.loads((ROOT.parent/'CTF competion/2026_CTF比赛数据.json').read_text(encoding='utf-8'))['events']}
CACHE = ROOT/'sources/specialized_cache'
CACHE.mkdir(parents=True,exist_ok=True)
LOG=[]

def ranged(url,size,key):
    step=2*1024*1024
    def part(i):
        a=i*step;b=min(size-1,a+step-1)
        p=key.with_name(key.name+f'.part{i}')
        if p.exists() and p.stat().st_size==b-a+1:return p.read_bytes()
        for attempt in range(3):
            try:
                rr=requests.get(url,headers={'Range':f'bytes={a}-{b}'},timeout=(15,60))
                rr.raise_for_status()
                if rr.status_code!=206 or len(rr.content)!=b-a+1 or not rr.headers.get('Content-Range','').startswith(f'bytes {a}-{b}/'):
                    raise ValueError('Server did not honor requested byte range')
                p.write_bytes(rr.content);return rr.content
            except Exception:
                if attempt==2:raise
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        return b''.join(pool.map(part,range((size+step-1)//step)))

def fetch(url):
    key=CACHE/hashlib.sha256(url.encode()).hexdigest()
    if key.exists(): return key.read_bytes()
    err=None
    for _ in range(3):
        try:
            r=requests.get(url,timeout=(15,60),headers={'User-Agent':'CTF-Research-Archive/1.0'},stream=True)
            r.raise_for_status()
            size=int(r.headers.get('Content-Length','0'))
            if size>8*1024*1024 and r.headers.get('Accept-Ranges','')=='bytes':
                r.close();content=ranged(url,size,key)
            else:
                content=r.content;r.close()
            if not content: raise ValueError('empty response')
            if content.startswith(b'version https://git-lfs.github.com/spec/v1'):
                raise ValueError('Git LFS pointer, not file contents')
            key.write_bytes(content)
            return content
        except Exception as e: err=e;time.sleep(0.3)
    raise err

def safe(s): return re.sub(r'[<>:"/\\|?*]', '_', s).strip(' .')

def record(event_id,category,title,slug=None,notes=''):
    event=EVENTS[event_id]
    eventdir={'CTF-3113':'SekaiCTF_2026','CTF-3276':'NDIAS_2026','CTF-3081':'0xFUN_2026','CTF-3161':'SUCTF_2026','CTF-2927':'BKISC_2026','CTF-3441':'Cryovault_2026_Quals','CTF-3065':'BrunnerCTF_2026'}.get(event_id,safe(event['title']))
    d=ROOT/category/eventdir/safe(slug or title)
    d.mkdir(parents=True,exist_ok=True)
    return {'event_id':event_id,'event_title':event['title'],'category':category,'title':title,'source_urls':event['sources'].copy(),'writeup_urls':[],'attachment_urls':[],'writeup_status':'missing','attachment_status':'missing','notes':notes,'files':[],'errors':[],'_dir':d}

def save(m,url,rel):
    try:
        content=fetch(url); p=m['_dir']/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(content)
        item={'path':rel,'url':url,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()};m['files'].append(item)
        if rel.startswith('writeups/') and url not in m['writeup_urls']:m['writeup_urls'].append(url)
        if rel.startswith('attachments/') and url not in m['attachment_urls']:m['attachment_urls'].append(url)
        return content
    except Exception as e: m['errors'].append({'url':url,'path':rel,'error':str(e)});return None

def blog(m,url,name='writeup'):
    content=save(m,url,'writeups/'+name+'.html')
    if not content:return
    soup=BeautifulSoup(content,'html.parser');body=soup.find('article') or soup.find('main') or soup
    for el in body.find_all(['script','style','nav']):el.decompose()
    for i,img in enumerate(body.find_all('img')):
        src=img.get('data-src') or img.get('src')
        if src and not src.startswith('data:'):
            u=urljoin(url,src);ext=Path(urlparse(u).path).suffix or '.img';rel=f'writeups/{name}_assets/{i:03}{ext}'
            if save(m,u,rel):img['src']=f'{name}_assets/{i:03}{ext}'
    (m['_dir']/'writeups'/f'{name}_offline.html').write_text('<!doctype html><meta charset="utf-8"><title>'+m['title']+'</title><p>Source: '+url+'</p>'+str(body),encoding='utf-8')
    (m['_dir']/'writeups'/f'{name}.txt').write_text('Source: '+url+'\n\n'+body.get_text('\n',strip=True),encoding='utf-8')

def github(m,repo,prefix,tree_file=None,solution_segments=('solution','solve','exp','writeup','writeups'),all_writeup=False):
    if tree_file:tree=json.loads(Path(tree_file).read_text(encoding='utf-8'))
    else:tree=json.loads(fetch('https://api.github.com/repos/'+repo+'/git/trees/HEAD?recursive=1'))
    sha=tree['sha'];m['source_urls'].append('https://github.com/'+repo+'/tree/'+sha+'/'+prefix)
    jobs=[]
    for x in tree['tree']:
        path=x['path']
        if x['type']!='blob' or not path.startswith(prefix+'/'):continue
        rel=path[len(prefix)+1:]; parts=rel.lower().split('/')
        folder='writeups' if all_writeup or any(p in solution_segments for p in parts) or parts[0] in ('writeup.md','writeup.txt') else 'attachments'
        u='https://raw.githubusercontent.com/'+repo+'/'+sha+'/'+quote(path,safe='/')
        if x.get('size') == 0:
            dst=m['_dir']/folder/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b'')
            m['files'].append({'path':folder+'/'+rel,'url':u,'bytes':0,'sha256':hashlib.sha256(b'').hexdigest(),'note':'Git tree confirms this is an intentional empty upstream file'})
            if folder=='attachments':m['attachment_urls'].append(u)
            else:m['writeup_urls'].append(u)
            continue
        jobs.append((u,folder+'/'+rel))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(lambda j:save(m,*j),jobs))
    for lic in ('LICENSE','LICENSE.content.md'):
        if any(x['path']==lic for x in tree['tree']):save(m,'https://raw.githubusercontent.com/'+repo+'/'+sha+'/'+lic,'licenses/'+lic)

def finish(m):
    w=[x for x in m['files'] if x['path'].startswith('writeups/')]; a=[x for x in m['files'] if x['path'].startswith('attachments/')]
    if w:m['writeup_status']='downloaded'
    if a:m['attachment_status']='downloaded' if not any(x['path'].startswith('attachments/') for x in m['errors']) else 'partial'
    d=m.pop('_dir');(d/'metadata.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
    (d/'README.md').write_text(f"# {m['title']}\n\n比赛：{m['event_title']}（{m['event_id']}）\n\n分类：{m['category']}\n\nWriteup：{m['writeup_status']}；附件：{m['attachment_status']}。\n\n{m['notes']}\n\n原始资料仅下载保存，未执行或验证解题成功。文件来源、SHA-256和失败记录见 metadata.json。\n\n## 来源\n\n"+'\n'.join('- '+u for u in dict.fromkeys(m['source_urls']+m['writeup_urls']))+'\n',encoding='utf-8')
    LOG.append({'event_id':m['event_id'],'category':m['category'],'title':m['title'],'path':str(d.relative_to(ROOT)),'writeup_status':m['writeup_status'],'attachment_status':m['attachment_status'],'errors':m['errors']})
    print(m['category'],m['title'],len(w),len(a),len(m['errors']),flush=True)

def main():
    for title,prefix in [('3in1','pwn/3in1'),('MTE','pwn/MTE')]:
        m=record('CTF-3113','虚拟化',title,notes=('QEMU guest-to-host 逃逸 full chain；保留官方运行环境、官方 solution 和作者文字解说。' if title=='3in1' else 'QEMU ARM MTE/PAC 仿真实现相关问题与 guest 内核提权；不是 guest-to-host 逃逸。保留官方运行环境/二进制 solver，以及参赛者文字题解。题解未经过本次执行验证。'))
        github(m,'project-sekai-ctf/sekaictf-2026',prefix,ROOT/'sources/specialized_sekai_tree.json')
        m['writeup_kind']='official_solver_source_and_author_writeup' if title=='3in1' else 'official_solver_binary_and_community_writeup'
        if title=='3in1':
            soup=BeautifulSoup(fetch('https://qyn.app/'),'html.parser')
            link=next((urljoin('https://qyn.app/',a['href']) for a in soup.find_all('a',href=True) if '3in1' in a['href']),None)
            if link:blog(m,link,'author_writeup')
        else:
            save(m,'https://raw.githubusercontent.com/hax1ng/Sekai-CTF-2026/main/pwn/mte/README.md','writeups/community_writeup.md')
        finish(m)
    for title,prefix in [('SekaiID','misc/sekaiid'),('ufo','misc/ufo')]:
        m=record('CTF-3113','android',title,notes='官方 APK 与运行材料；第三方实际参赛 writeup 已另存，HTML 提供正文及离线图片副本。')
        github(m,'project-sekai-ctf/sekaictf-2026',prefix,ROOT/'sources/specialized_sekai_tree.json')
        if title=='SekaiID':github(m,'Abdelkad3r/SekaiCTF-2026',prefix,ROOT/'sources/specialized_SekaiCTF-2026_tree.json',all_writeup=True)
        else:blog(m,'https://pentest.bi0s.in/blog/posts/sekai-ctf-2026-ufo/')
        finish(m)
    m=record('CTF-3161','iot','SU_EzRouter',notes='模拟路由器，含 HTTP/CGI 服务、IPC 后端和二进制利用；原赛题类别 pwn，按题材归入 iot。原始源码、环境和官方 exp 全部保存。')
    github(m,'team-su/SUCTF-2026','pwn/SU_EzRouter',ROOT/'sources/pwn_trees/team-su__SUCTF-2026.json');finish(m)
    m=record('CTF-3081','iot','UART',notes='UART 串口信号分析，原类别 Misc/Hardware；按嵌入式通信归入 iot。附件镜像由 writeup 作者提供。')
    u='https://raw.githubusercontent.com/RobinVA-UIT/robinva-uit.github.io/main/_posts/CTF_tournament/0xFun%20CTF%202026/UART/2026-02-14-UART.md'
    save(m,u,'writeups/RobinVA.md');save(m,'https://github.com/RobinVA-UIT/robinva-uit.github.io/releases/download/v1.0/0xFunCTF2026_UART.zip','attachments/0xFunCTF2026_UART.zip');finish(m)
    # NDIAS: original platform is no longer reachable, so do not invent attachments.
    wp='https://raw.githubusercontent.com/kn1cht/kn1cht-zenn-contents/main/articles/ndias-automotive-iot-ctf-2026-kn1cht.md'
    note='原题资料来源为参赛者 writeup 与主办方解说。原平台 https://ctf.ndias.jp/ 本次访问发生 TLS EOF；未检索到公开题目附件镜像。attachments 保持缺失，不将 writeup 插图或 solver 误标为题目附件。'
    titles=['Parking Lot Whisper','Read the simple fob','Next Counter','Predict Next UNLOCK','Classic KeeLoq Garage - Find the Key','Classic KeeLoq Garage - Next HOP','Real KeeLoq Garage - Normal Learn','Real KeeLoq Garage - Next HOP']
    for title in titles:
        m=record('CTF-3276','车联网',title,notes=note+' 分类依据：车辆遥控钥匙 Keyfob / KeeLoq 射频协议。')
        save(m,wp,'writeups/kn1cht_full_writeup.md');finish(m)
    m=record('CTF-3276','iot',"D's Signpost",notes=note+' 分类依据：RF 无线信号解调。');save(m,wp,'writeups/kn1cht_full_writeup.md');finish(m)
    m=record('CTF-3276','iot','Tiny crackme',notes=note+' 分类依据：Cortex-M3 / FreeRTOS 固件分析；使用 QEMU 运行不等于虚拟化逃逸。');blog(m,'https://yusuftas.net/posts/ndias-tiny-crackme-writeup/');finish(m)
    slides='https://files.speakerdeck.com/presentations/adb64da6a13c4eda9bfcc5ba1ba95e79/NDIAS-CTF_%E5%95%8F%E9%A1%8C%E8%A7%A3%E8%AA%AC.pdf'
    for category,title in [('车联网',x) for x in ['VIN Hunter','Seed-Key Leak','Gateway Gremlins','AGL 1','AGL 2','AGL 3','AGL 4','AGL 5','I Saw Our Time Pass','RAMN ECU D']]+[('iot',f'Suspicious device {i}') for i in range(1,4)]:
        m=record('CTF-3276',category,title,notes=note+' 解答为 bata_24 官方解说会完整 PDF，同组题共用，目录/页码请查 PDF；本题在第3页目录明确列出。')
        m['source_urls'].append('https://speakerdeck.com/bata_24/ndias-ctf-2026-wen-ti-jie-shuo');save(m,slides,'writeups/NDIAS_official_explanations.pdf');finish(m)
    out=ROOT/'sources/specialized_search.json'
    out.write_text(json.dumps({'snapshot_date':'2026-11-06','records':LOG,'limitations':['不是对全部416赛事逐一检索；本文件是重点专业类别检索记录。','排除不在目标清单的2026极氪、Kaspersky CTF、BUET CTF。','BKISC Boring APK相关writeup存在，但引用仓库404；待补附件。','Cryovault Mirror Garden检索到writeup，阶段与原始附件未核实，暂不收录。','NDIAS第三方Suspicious-device文章与官方解说的题目阶段描述不一致，采用官方解说。'],'queries':['CTF 2026 android writeup github','CTF 2026 qemu escape writeup','CTF 2026 IoT hardware writeup','2026 CTF 车联网 writeup','NDIAS 2026 writeup github','NDIAS capture_c1c2.bin','NDIAS suspicious_device.zip','KnightCTF 2026 Android','0xFUN 2026 hardware writeup','BKISC CTF 2026 Boring APK','SekaiCTF 2026 ufo SekaiID MTE 3in1','SUCTF 2026 SU_EzRouter']},ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
