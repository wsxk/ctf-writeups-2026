"""Build a traceable local catalog; verify bytes without running challenge code."""
import concurrent.futures as cf
import csv,hashlib,json,re,zipfile
from collections import Counter,defaultdict
from pathlib import Path
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
CATEGORIES=['逆向','pwn','虚拟化','车联网','iot','android']
DATE='2026-11-06'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()

def link(path): return quote(str(path).replace('\\','/'),safe='/')
def norm(s): return ''.join(c for c in s.casefold() if c.isalnum())

def downloaded_writeup(m):
    if m.get('has_verified_solution') is False: return False
    s=m.get('writeup_status','')
    return s=='downloaded' or (s.startswith('已下载') and '空模板' not in s)

def attachment_state(m):
    s=m.get('attachment_status','')
    if s=='downloaded' or (s.startswith('已下载') and not any(v in s for v in ['失败','不完整','仅链接','部分'])): return '已下载'
    if s in ['missing','unavailable'] or s.startswith(('未','缺')): return '缺失'
    return '部分'

def build():
    input_path=ROOT.parent/'CTF competion'/'2026_CTF比赛数据.json'
    input_data=json.loads(input_path.read_text(encoding='utf-8'))
    events={e['record_id']:e for e in input_data['events']+input_data.get('cross_year_events',[])}
    rows=[]; references={}; issues=[]; git_symlinks=set()
    for category in CATEGORIES:
        (ROOT/category).mkdir(exist_ok=True)
        for p in (ROOT/category).rglob('metadata.json'):
            try: m=json.loads(p.read_text(encoding='utf-8'))
            except Exception as e: issues.append({'path':str(p),'error':str(e)});continue
            directory=p.parent.relative_to(ROOT).as_posix()
            if m.get('event_id') not in events: issues.append({'path':directory,'error':'event_id not in input catalog'})
            wu=downloaded_writeup(m)
            if wu and not any(f.is_file() and f.stat().st_size>0 for f in (p.parent/'writeups').rglob('*')):
                issues.append({'path':directory,'error':'writeup marked downloaded but no nonempty file'});wu=False
            files=[f for f in p.parent.rglob('*') if f.is_file() and f.name not in ['README.md','metadata.json'] and not f.name.endswith('.part')]
            row=dict(event_id=m.get('event_id'),event_title=m.get('event_title'),category=category,title=m.get('title'),directory=directory,writeup_status=m.get('writeup_status'),attachment_status=m.get('attachment_status'),has_writeup=wu,attachment_state=attachment_state(m),file_count=len(files),bytes=sum(f.stat().st_size for f in files),source_urls=m.get('source_urls',[]),writeup_urls=m.get('writeup_urls',[]),attachment_urls=m.get('attachment_urls',[]),notes=m.get('notes',[]),duplicate_of=m.get('duplicate_of'))
            rows.append(row)
            for a in m.get('files',[])+m.get('artifacts',[]):
                rel=a.get('local') or a.get('path')
                if not rel or not a.get('sha256'): continue
                target=ROOT/rel
                if not target.is_file(): target=p.parent/rel
                if not target.is_file(): issues.append({'path':directory,'error':'referenced download missing','file':rel});continue
                references[target]=dict(sha256=a['sha256'],bytes=a.get('bytes'))
                if a.get('git_mode')=='120000': git_symlinks.add(target.resolve())
    # Do not count two source copies of the same event/challenge twice.
    groups=defaultdict(list)
    for r in rows: groups[(r['event_id'],norm(r['title']))].append(r)
    for key,group in groups.items():
        primary=sorted(group,key=lambda r:(bool(r['duplicate_of']),not r['has_writeup'],r['attachment_state']!='已下载',-r['bytes']))[0]
        for r in group:
            if r is not primary and not r['duplicate_of']: r['duplicate_of']=primary['directory']
    active=[r for r in rows if not r['duplicate_of']]
    collected=[r for r in active if r['has_writeup']]
    pending=[r for r in active if not r['has_writeup']]
    checks=[]
    def verify(item):
        p,a=item; actual=sha(p)
        ok=actual==a['sha256'] and (a['bytes'] is None or p.stat().st_size==a['bytes'])
        return dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=actual,ok=ok)
    with cf.ThreadPoolExecutor(max_workers=4) as pool: checks=list(pool.map(verify,references.items()))
    issues.extend({'path':c['path'],'error':'SHA256 or length mismatch'} for c in checks if not c['ok'])
    zip_checks=[]
    for p in ROOT.rglob('*.zip'):
        if 'sources' in p.relative_to(ROOT).parts: continue
        if p.resolve() in git_symlinks:
            zip_checks.append(dict(path=p.relative_to(ROOT).as_posix(),status='Git symlink target text; actual target file checked separately'))
            continue
        try:
            with zipfile.ZipFile(p) as z:
                total=sum(i.file_size for i in z.infolist())
                encrypted=any(i.flag_bits&1 for i in z.infolist())
                if encrypted: status='encrypted; integrity requires password'
                elif total>1024**3: status='central directory valid; CRC skipped for >1GiB expanded size'
                else:
                    bad=z.testzip()
                    if bad: issues.append({'path':p.relative_to(ROOT).as_posix(),'error':'ZIP CRC error: '+bad})
                    status='CRC_OK' if not bad else 'CRC_ERROR'
                zip_checks.append(dict(path=p.relative_to(ROOT).as_posix(),members=len(z.infolist()),expanded_bytes=total,status=status))
        except Exception as e: issues.append({'path':p.relative_to(ROOT).as_posix(),'error':'ZIP check: '+str(e)})
    (ROOT/'SHA256SUMS.txt').write_text('\n'.join(c['sha256']+'  '+c['path'] for c in sorted(checks,key=lambda c:c['path']))+'\n',encoding='utf-8')
    searches={}
    for p in (ROOT/'sources'/'event_search').glob('*.json'):
        obj=json.loads(p.read_text(encoding='utf-8'))
        for e in obj['events']: searches[e['id']]=p.relative_to(ROOT).as_posix()
    coverage=[]
    for e in input_data['events']:
        matches=[r for r in collected if r['event_id']==e['record_id']]
        if e['record_id'] in searches: status='已做首轮网页检索'
        elif any(x in e['status'] for x in ['待开始','取消','延期']): status='按赛期状态暂不采集'
        else: status='待检索'
        coverage.append(dict(event_id=e['record_id'],event_title=e['title'],event_status=e['status'],search_status=status,search_log=searches.get(e['record_id']),collected=len(matches),complete=sum(r['attachment_state']=='已下载' for r in matches)))
    stats=dict(input_main_events=len(input_data['events']),searched_events=len(searches),collected_challenges=len(collected),collected_events=len({r['event_id'] for r in collected}),with_attachments=sum(r['attachment_state']=='已下载' for r in collected),partial_attachments=sum(r['attachment_state']=='部分' for r in collected),missing_attachments=sum(r['attachment_state']=='缺失' for r in collected),pending_writeups=len(pending),duplicate_copies=len(rows)-len(active),categories=dict(Counter(r['category'] for r in collected)),verified_download_files=len(checks),verified_download_bytes=sum(c['bytes'] for c in checks),integrity_issues=len(issues))
    report=dict(date_beijing=DATE,stats=stats,issues=issues,zip_checks=zip_checks,partial_downloads=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size) for p in ROOT.rglob('*.part')])
    for name,data in [('catalog.json',dict(date_beijing=DATE,stats=stats,challenges=rows)),('sources/validation_report.json',report),('sources/event_coverage.json',coverage)]:
        (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    with (ROOT/'题目索引.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['category','event_id','event_title','title','has_writeup','writeup_status','attachment_state','attachment_status','directory','duplicate_of']
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    def table(items):
        out=['| 比赛 | 题目 | 解答 | 附件 |','|---|---|---|---|']
        for r in sorted(items,key=lambda r:(r['event_title'],r['title'])):
            out.append(f"| {r['event_title'].replace('|',' / ')} ({r['event_id']}) | [{r['title'].replace('|',' / ')}]({link(r['directory']+'/README.md')}) | {'已下载' if r['has_writeup'] else '待补正文/有效解答'} | {r['attachment_state']} |")
        return '\n'.join(out)
    index=['# 题目索引',f'\n检索日期：{DATE}（北京时间）。有效解答包括叙述型 writeup 和明确的官方/作者求解脚本，二者在每题 README 和 metadata.json 中区分。\n']
    for cat in CATEGORIES:
        rs=[r for r in collected if r['category']==cat]
        index.extend([f'\n## {cat}（{len(rs)}题）\n',table(rs)])
    index.extend(['\n## 待补有效解答（不计入已收录题数）\n',table(pending)])
    (ROOT/'题目索引.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
    missing=[r for r in active if not r['has_writeup'] or r['attachment_state']!='已下载']
    text=['# 缺失与待补清单','\n“缺失”只表示本次未取得，不证明网上不存在。不会把登录页、题面、空白模板或附件链接当作实际下载。\n',table(missing),'\n## 下载中断残留\n']
    text.extend('- '+p['path']+f"：{p['bytes']:,} 字节；不是完整附件，不计入已下载。" for p in report['partial_downloads'])
    if report['partial_downloads']: text.append('\nSU_fullchian 没有确认到有效解答，故停止26,374,590,293字节完整环境下载。删除新建临时文件的操作被自动审批审查拒绝，返回 `rejected: blocked by policy`；保留上述残留。')
    (ROOT/'缺失与待补.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    ctext=['# 比赛检索覆盖','\n首轮查询涵盖主清单中374条已过赛期、赛程内或赛期说明记录；42条未来、取消或延期记录按状态暂缓。首轮搜索结果不等于逐条深挖完所有搜索命中。未收录不等于没有相关题或writeup。','\n| 编号 | 比赛 | 赛事状态 | 检索 | 收录题数 | 附件齐全 |','|---|---|---|---|---:|---:|']
    for e in coverage:
        s=f"[{e['search_status']}]({link(e['search_log'])})" if e['search_log'] else e['search_status']
        ctext.append(f"| {e['event_id']} | {e['event_title'].replace('|',' / ')} | {e['event_status']} | {s} | {e['collected']} | {e['complete']} |")
    ctext.extend(['\n## 输入目录的补充记录\n','主清单之外的跨年赛事、赛期不明记录、watchlist保留在原比赛资料目录。本次主统计仅针对416条主清单；补充赛事的检索线索见sources/supplemental_search.json（如存在）。'])
    (ROOT/'比赛检索覆盖.md').write_text('\n'.join(ctext)+'\n',encoding='utf-8')
    lines=['# CTF题目与解答资料库',f'\n整理日期：**{DATE}，北京时间**。以相邻 `CTF competion/2026_CTF比赛数据.json` 为赛事范围。',f"\n已收录 **{len(collected)} 道有实际解答的题目，来自 {stats['collected_events']} 场比赛/赛段**：{stats['with_attachments']}题附件已下载，{stats['partial_attachments']}题附件不完整，{stats['missing_attachments']}题未取得附件。另有{len(pending)}题已发现线索但有效解答尚未下载/确认，单列待补。",'\n| 分类 | 有解答题数 |','|---|---:|']
    lines.extend(f'| [{c}]({link(c)}/) | {stats["categories"].get(c,0)} |' for c in CATEGORIES)
    lines.extend(['\n## 入口\n','- [题目索引](题目索引.md)：按分类、比赛、题目浏览；每题内有 attachments、writeups、README 和来源 metadata。','- [缺失与待补](缺失与待补.md)：缺附件、缺正文、下载中断的具体记录。','- [比赛检索覆盖](比赛检索覆盖.md)：416条输入记录的检索与收录情况。','- [结构化索引](catalog.json) · [CSV索引](题目索引.csv) · [下载哈希](SHA256SUMS.txt) · [验证报告](sources/validation_report.json)。','\n## 范围与分类\n','已完成374条主清单记录的首轮网页检索，并从可访问的官方仓库、作者/参赛队仓库、博客、CTFtime和题目镜像交叉配对资料。无法保证公开网络上的全部writeup均已穷尽；首轮有搜索命中不代表命中内每个仓库都已逐题审阅。未开始、取消或延期的42条主记录暂缓。','虚拟化包含两类：QEMU/Hypervisor/虚拟机逃逸，以及自定义VM、字节码、虚拟化保护逆向；每题备注区分。Android题优先放android，车载协议/ECU/CAN题优先放车联网，嵌入式、固件、无线/硬件相关题放iot。交叉题按主方向归类，来源重复副本不重复计数。','官方source、Dockerfile和构建材料可能是上游唯一公开形式；不把它们承诺为原始比赛编译包。附件齐全指本题已登记的公开附件/源码已取得，不保证远程服务、账号、设备和外部依赖可复现。','writeup保留原文语言；部分只有官方/作者solver，已在题目说明标出。只有二进制solver或空白模板的条目不作为文字解答完成。HTML保留正文，未承诺所有外链图片都能离线显示。',f"\n下载文件进行SHA-256和长度复核；本轮登记验证{len(checks)}个文件，发现{len(issues)}项需复查记录。ZIP另核验目录与可检查的CRC；加密包和大型展开包的限制见验证报告。没有执行任何题目二进制、exp或solver。",'\n## 更新\n','采集脚本与检索快照位于scripts/和sources/。`python -X utf8 scripts/build_catalog.py`可从现有metadata重建索引并重新校验；不会运行题目代码。联网采集脚本会产生网络请求，原站链接和分支内容可能变化。'])
    (ROOT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(stats,ensure_ascii=False,indent=2));print('ISSUES',json.dumps(issues[:30],ensure_ascii=False))

if __name__=='__main__': build()
