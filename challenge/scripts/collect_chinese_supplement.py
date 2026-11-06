"""Extract already-downloaded, attributed NepCTF/Qiangwang writeup sections."""
import json,re,hashlib
from pathlib import Path
from bs4 import BeautifulSoup
from collect_specialized import ROOT,record,finish,LOG

def local_source(m,data,name,url,note):
    d=m['_dir']/'writeups';d.mkdir(parents=True,exist_ok=True);p=d/name;p.write_bytes(data)
    m['writeup_urls'].append(url)
    m['files'].append({'path':'writeups/'+name,'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'note':note})

source=ROOT/'sources/nepctf2026_full_writeup.md'
t=source.read_text(encoding='utf-8');matches=list(re.finditer(r'^## #([0-9]+)\s+(.+)$',t,re.M))
targets={19:'逆向',23:'iot',24:'iot',36:'虚拟化',37:'iot',42:'虚拟化',46:'iot',47:'pwn',48:'pwn',51:'pwn',70:'逆向',72:'逆向'}
url='https://github.com/fjh1997/nepctf2026-writeup/blob/main/writeup/WriteUp_%E5%AE%8C%E6%95%B4%E8%87%AA%E5%8C%85%E5%90%AB.md'
for i,match in enumerate(matches):
    num=int(match.group(1))
    if num not in targets:continue
    title=match.group(2);block=t[match.start():matches[i+1].start() if i+1<len(matches) else len(t)]
    notes='解答摘自 fjh1997/nepctf2026-writeup 的完整自包含 writeup，保留该题原文及其中全部解题代码。原题大附件/固件/镜像未随该仓库发布；ctf-archives/NepCTF/2026 镜像路径核验为404。没有把解题代码当成题目附件，attachment_status 为 missing。本次未执行任何代码或联系文中历史服务。'
    if num==36:notes+=' 分类依据：解题脚本读取 FlipJump program.fjm 并还原 guest PRNG，属于自定义虚拟机逆向。'
    if num==42:notes+=' 分类依据：BizHawk/Mupen64Plus 游戏模拟器 guest-to-host 逃逸；原文 PoC 目标是宿主计算器。'
    if num in (23,24):notes+=' 分类依据：比赛中的软 PLC / 工控过程模拟，归入 iot（ICS）。'
    m=record('CAL-004',targets[num],title,slug=f'{num:02d}_'+title,notes=notes)
    m['source_urls'].append('https://github.com/fjh1997/nepctf2026-writeup')
    m['original_challenge_id']=num;m['writeup_kind']='community_writeup_section_with_embedded_solver';m['source_document_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    data=(f'> 来源：{url}\n> 以下为原始完整 writeup 中 #{num} 的连续章节摘录；代码未执行。\n\n'+block).encode('utf-8')
    local_source(m,data,'writeup.md',url,f'Verbatim section #{num} from locally downloaded complete source; attribution prepended')
    finish(m)

src=ROOT/'sources/qiangwang_lufer.html';html=src.read_bytes();soup=BeautifulSoup(html,'html.parser')
url='https://coder.lufer.cc/2026/11/%E7%AC%AC%E5%8D%81%E5%B1%8A%E5%BC%BA%E7%BD%91%E6%9D%AFwp/'
for title,category in [('Easytl','pwn'),('Oldsvr','pwn'),('ELFStudy','逆向')]:
    h=next(x for x in soup.find_all('h2') if x.get_text(' ',strip=True)==title)
    selected=[str(h)]
    for x in h.next_siblings:
        if getattr(x,'name',None) in ('h1','h2'):break
        selected.append(str(x))
    fragment=''.join(selected);text=BeautifulSoup(fragment,'html.parser').get_text('\n',strip=True)
    assert len(text)>300,title
    m=record('CN-001',category,title,notes=f'Lufer 原创第十届强网杯 WP，题解对应全文中的“{title}”章节。完整原始 HTML 与该章节离线正文均保存；图片可能仍引用源站。原文未提供题目附件直链，附件标 missing。解答、脚本及历史远程服务均未执行/访问。')
    m['writeup_kind']='community_writeup_html_and_section'
    local_source(m,html,'Lufer_full_writeup.html',url,'Unmodified downloaded source HTML')
    local_source(m,('<!doctype html><meta charset="utf-8"><p>来源：'+url+'</p>'+fragment).encode('utf-8'),'chapter.html',url,'Original chapter extracted; attribution prepended')
    local_source(m,('来源：'+url+'\n\n'+text).encode('utf-8'),'chapter.txt',url,'Plain-text extraction of chapter')
    finish(m)
(ROOT/'sources/chinese_supplement_search.json').write_text(json.dumps({'snapshot_date':'2026-11-06','records':LOG,'source_files':[str(source.relative_to(ROOT)),str(src.relative_to(ROOT))],'source_urls':['https://github.com/fjh1997/nepctf2026-writeup',url],'limitations':['15题均取得实际解答；原题附件均未取得，明确missing。','只提取已下载资料，未运行题目/solver/远程连接。','公开作者的成功声明未在本次独立复现。']},ensure_ascii=False,indent=2),encoding='utf-8')
print('Completed',len(LOG),'records')
