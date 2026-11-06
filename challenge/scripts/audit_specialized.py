"""Verify downloaded bytes/archives and consolidate the specialized collection log."""
from pathlib import Path
import collections,hashlib,json,zipfile

ROOT=Path(__file__).resolve().parents[1]
sources=ROOT/'sources'
reports=[sources/n for n in ['specialized_search.json','specialized_extra_search.json','specialized_bsides_search.json','specialized_mirror_search.json']]
paths=set()
for p in reports:
    if p.exists():
        j=json.loads(p.read_text(encoding='utf-8'))
        paths.update(r['path'] for r in j.get('records',[]))
errors=[];records=[];hashchecked=0;archivechecked=0;archive_cache={};bytes_checked=0
for rel in sorted(paths):
    folder=ROOT/rel;metadata=folder/'metadata.json';m=json.loads(metadata.read_text(encoding='utf-8'))
    if m['event_id']=='CTF-3276':
        if m['attachment_status']=='missing':
            m['notes']='已保存公开解答。原平台 https://ctf.ndias.jp/ 本次请求出现 TLS EOF；已检查公开 CTF 归档 https://github.com/sajjadium/ctf-archives/tree/main/ctfs/NDIASAutomotiveIoT/2026 ，未找到本题原始附件。没有将 writeup 插图或解题脚本冒充题目附件。'
        elif m['attachment_status']=='partial':
            m['notes']='已保存官方解说 PDF 与公开归档中的客户端/磁盘镜像资料。原题仍依赖已下线的在线服务，缺少服务器端运行环境，不能声称可完整离线复现。'
            if m['title'].startswith('Suspicious device'):m['notes']+=' Suspicious device 1–3 共用 SD 卡镜像，后两阶段涉及云服务和数据库；归档来源为第1题附件。'
        else:
            m['notes']='已保存公开解答与 sajjadium/ctf-archives 原题附件镜像。题目环境及 solver 均未执行。'
        if m['title'] in ['VIN Hunter','Seed-Key Leak','Gateway Gremlins','AGL 1','AGL 2','AGL 3','AGL 4','AGL 5','I Saw Our Time Pass','RAMN ECU D'] or m['title'].startswith('Suspicious device'):
            m['notes']+=' writeups/NDIAS_official_explanations.pdf 为 bata_24 的官方解说会完整资料，各题在第3页总目录列出。'
        metadata.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
        (folder/'README.md').write_text(f"# {m['title']}\n\n比赛：{m['event_title']}（{m['event_id']}）\n\n分类：{m['category']}\n\nWriteup：{m['writeup_status']}；附件：{m['attachment_status']}。\n\n{m['notes']}\n\n文件来源、SHA-256 与下载记录见 metadata.json。\n\n## 来源\n\n"+'\n'.join('- '+u for u in dict.fromkeys(m['source_urls']+m['writeup_urls']+m['attachment_urls']))+'\n',encoding='utf-8')
    for f in m['files']:
        p=folder/f['path']
        if not p.exists():errors.append({'path':str(p),'error':'missing'});continue
        data=p.read_bytes();sha=hashlib.sha256(data).hexdigest();hashchecked+=1;bytes_checked+=len(data)
        if sha!=f['sha256'] or len(data)!=f['bytes']:errors.append({'path':str(p),'error':'hash or length mismatch'})
        if p.suffix.lower()=='.pdf' and not data.startswith(b'%PDF'):errors.append({'path':str(p),'error':'not PDF'})
        if p.suffix.lower() in ['.zip','.apk']:
            if sha not in archive_cache:
                try:
                    with zipfile.ZipFile(p) as z:
                        bad=z.testzip();members=len(z.infolist())
                        archive_cache[sha]={'path':str(p.relative_to(ROOT)),'members':members,'bad_member':bad}
                        if bad:errors.append({'path':str(p),'error':'ZIP CRC failure','member':bad})
                    archivechecked+=1
                except Exception as e:errors.append({'path':str(p),'error':str(e)})
    records.append({'event_id':m['event_id'],'event_title':m['event_title'],'title':m['title'],'category':m['category'],'path':str(folder.relative_to(ROOT)),'writeup_status':m['writeup_status'],'attachment_status':m['attachment_status'],'writeup_kind':m.get('writeup_kind','text_or_solver_source'),'errors':m.get('errors',[])})
report={'snapshot_date':'2026-11-06','collection':'specialized','records':records,'totals':{'questions':len(records),'events':len({r['event_id'] for r in records}),'categories':dict(collections.Counter(r['category'] for r in records)),'attachment_status':dict(collections.Counter(r['attachment_status'] for r in records)),'writeup_status':dict(collections.Counter(r['writeup_status'] for r in records))},'validation':{'hashes_checked':hashchecked,'bytes_checked':bytes_checked,'unique_zip_apk_crc_checks':archivechecked,'errors':errors},'limitations':['本专项记录不是416场比赛逐场检索覆盖声明；整体覆盖由根目录总索引记录。','MTE为QEMU MTE/PAC仿真实现相关问题和guest内核提权；3in1含guest-to-host逃逸。','未运行题目附件、solver、连接脚本或归档中的AGENTS.md指令。','车联网的18题来自NDIAS2026，其中部分只取得writeup，缺失/部分附件逐题标明。','D3CTF d3llvm原APK未取得，官方中英文writeup和参赛者solver已保存。','排除不在目标比赛清单的2026极氪、Kaspersky CTF、BUET CTF。','Cryovault Mirror Garden及BKISC Boring APK交由根索引收集，未在本专项重复计数。'],'queries':['CTF 2026 android writeup github','CTF 2026 qemu escape writeup','CTF 2026 IoT hardware writeup','2026 CTF 车联网 writeup','NDIAS 2026 writeup github','NDIAS capture_c1c2.bin','NDIAS suspicious_device.zip','KnightCTF 2026 Android','0xFUN 2026 hardware writeup','BKISC CTF 2026 Boring APK','SekaiCTF 2026 ufo SekaiID MTE 3in1','SUCTF 2026 SU_EzRouter SU_flumel SU_老年固件','BYUCTF 2026 back_and_forth','Securinets 2026 Backdrop','BSidesSF 2026 doremi vinyl-drop','D3CTF 2026 d3llvm']}
(sources/'specialized_search.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(sources/'specialized_validation.json').write_text(json.dumps({'totals':report['totals'],'validation':report['validation'],'archives':list(archive_cache.values())},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'totals':report['totals'],'validation':report['validation']},ensure_ascii=False,indent=2))
