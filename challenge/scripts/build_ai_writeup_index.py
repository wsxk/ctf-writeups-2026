"""Build an AI reading index and validate documentation coverage/local links.

Reads local analysis summaries only. No challenge binaries or solvers are run.
"""
import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def build():
    catalog = json.loads((ROOT/'catalog.json').read_text('utf-8'))
    summaries = {}
    for group in ('reverse','pwn','vm','special'):
        for entry in json.loads((ROOT/f'sources/ai_rewrite_{group}_summary.json').read_text('utf-8')):
            assert entry['directory'] not in summaries, entry['directory']
            summaries[entry['directory']] = entry
    assert len(summaries) == 324
    index = []
    for x in catalog['challenges']:
        d = ROOT/x['directory']
        output = d/'AI_WRITEUP.md'
        if x.get('duplicate_of'):
            rel = Path(os.path.relpath(ROOT/x['duplicate_of']/'AI_WRITEUP.md',d)).as_posix()
            output.write_text(f"# {x['title']} — 重复来源入口\n\n本目录的规范题目为 [{x['duplicate_of']}]({quote(rel,safe='/')})，请读取该处完整改写。\n\n原始来源保留在 [writeups](writeups/)，本条不重复计数。\n",'utf-8')
            status = 'duplicate'
            s = dict(mechanism='重复副本，见 canonical_directory。',evidence=[],limitations='本地原文仍保留，统一阅读规范题目。')
        elif not x['has_writeup']:
            output.write_text(f"# {x['title']} — 资料待补（不是完整解答）\n\n比赛：{x['event_title']}；分类：{x['category']}。\n\n原目录登记为尚未取得/确认有效 writeup。现有来源不足以重写可靠的解题过程，因此不编造漏洞、算法、payload 或 flag。\n\n请先读 [题目说明](README.md) 与 [来源记录](metadata.json)，确认已有附件、链接和缺失原因。取得对应文字解答或完整可审阅 solver 后，再补充：输入与目标、关键证据、解题推导、操作顺序、中间状态及最终验证。\n\n本次未执行题目或 solver。\n",'utf-8')
            status = 'pending_source'
            s = dict(mechanism='尚未取得/确认有效解答。',evidence=['README.md','metadata.json'],limitations='缺少足以支持完整改写的原始解答。')
        else:
            assert output.exists(), x['directory']
            s = summaries[x['directory']]
            status = 'source_limited' if s['status']=='source_limited' else 'static_analysis'
        data = output.read_bytes()
        index.append(dict(category=x['category'],event=x['event_title'],title=x['title'],directory=x['directory'],writeup=output.relative_to(ROOT).as_posix(),rewrite_status=status,original_writeup_status=x['writeup_status'],original_attachment_status=x['attachment_state'],canonical_directory=x.get('duplicate_of') or x['directory'],mechanism=s['mechanism'],evidence=s['evidence'],limitations=s['limitations'],executed=False,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))

    report = dict(catalog_rows=len(index),canonical_rewritten=sum(x['rewrite_status'] in {'static_analysis','source_limited'} for x in index),duplicates=sum(x['rewrite_status']=='duplicate' for x in index),pending_sources=sum(x['rewrite_status']=='pending_source' for x in index),categories=dict(Counter(x['category'] for x in index if x['rewrite_status'] in {'static_analysis','source_limited'})),missing_files=[],broken_local_links=[],empty_sections=[],executed_challenges=False)
    for x in index:
        p=ROOT/x['writeup']
        text=p.read_text('utf-8')
        if len(text.strip()) < 100:
            report['missing_files'].append(x['writeup'])
        for label, raw in re.findall(r'\[([^\]\n]*)\]\((<[^>]+>|[^)\n]+)\)',text):
            target=raw.strip('<>')
            if urlsplit(target).scheme or target.startswith('#'):
                continue
            path=unquote(target.split('#',1)[0]).replace('\\','/')
            if path and not (p.parent/path).exists():
                report['broken_local_links'].append(dict(file=x['writeup'],target=target))
        for m in re.finditer(r'(?m)^##[^\n]*\n\s*(?=##|\Z)',text):
            report['empty_sections'].append(dict(file=x['writeup'],heading=m.group(0).strip()))
    assert report['canonical_rewritten']==324
    assert report['duplicates']==2 and report['pending_sources']==5
    output_data=dict(schema_version=1,date_beijing='2026-11-06',scope='本地原文/solver分析改写；未执行题目',stats={k:v for k,v in report.items() if k not in {'missing_files','broken_local_links','empty_sections'}},challenges=index)
    (ROOT/'AI_WRITEUP_INDEX.json').write_text(json.dumps(output_data,ensure_ascii=False,indent=2),'utf-8')
    lines=['# AI 可读 Writeup 总索引','','覆盖原目录的324道规范题目；另有2个重复入口和5个原始资料待补条目。原始 writeups、attachments、catalog.json 均保留。','','所有文档为静态分析改写，**不是324题运行复现报告**。已有来源中的缺失、矛盾、局部验证或未完成 solver 已在各题标明。','','- [阅读与字段说明](AI_WRITEUP_GUIDE.md)','- [结构化索引](AI_WRITEUP_INDEX.json)','- [资料问题与复现缺口](AI_WRITEUP_ISSUES.md)','- [覆盖及链接检查报告](sources/ai_writeup_validation_report.json)','','## 规范题目','']
    for cat in ['逆向','pwn','虚拟化','车联网','iot','android']:
        items=[x for x in index if x['category']==cat and x['rewrite_status'] in {'static_analysis','source_limited'}]
        lines += [f'### {cat}（{len(items)}）','','| 比赛 | 题目 | 核心机制 |','|---|---|---|']
        for x in items:
            mechanism=x['mechanism'].replace('|','／').replace('\n',' ')
            lines.append(f"| {x['event'].replace('|','／')} | [{x['title'].replace('|','／')}]({quote(x['writeup'],safe='/')}) | {mechanism} |")
        lines.append('')
    lines += ['## 重复与待补入口','','| 状态 | 题目目录 |','|---|---|']
    for x in index:
        if x['rewrite_status'] in {'duplicate','pending_source'}:
            label='重复副本' if x['rewrite_status']=='duplicate' else '原文待补'
            lines.append(f"| {label} | [{x['directory']}]({quote(x['writeup'],safe='/')}) |")
    (ROOT/'AI_WRITEUP_INDEX.md').write_text('\n'.join(lines)+'\n','utf-8')
    issues=['# 资料问题与复现缺口','','以下记录来自逐题分析，包含版本依赖、未收录脚本、原文缺漏及待核验结论。出现条目不代表该题无解；应按具体说明补材料或验证。所有题目均未在本次运行。','','| 分类 | 题目 | 限制与核验要求 |','|---|---|---|']
    for x in index:
        if x['rewrite_status']=='duplicate':continue
        issues.append(f"| {x['category']} | [{x['title'].replace('|','／')}]({quote(x['writeup'],safe='/')}) | {str(x['limitations']).replace('|','／').replace(chr(10),' ')} |")
    (ROOT/'AI_WRITEUP_ISSUES.md').write_text('\n'.join(issues)+'\n','utf-8')
    report['passed']=not any(report[k] for k in ('missing_files','broken_local_links','empty_sections'))
    (ROOT/'sources/ai_writeup_validation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    build()
