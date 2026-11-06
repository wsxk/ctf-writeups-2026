"""Build a traceable Markdown/JSON catalogue from saved source snapshots."""
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'sources'
BJT = timezone(timedelta(hours=8))
YEAR_START = datetime(2026, 1, 1, tzinfo=BJT)
YEAR_END = datetime(2027, 1, 1, tzinfo=BJT)

def read(name):
    return json.loads((SRC / name).read_text(encoding='utf-8-sig'))

def write(name, value):
    (ROOT / name).write_text(value, encoding='utf-8')

def date(value):
    if not value or len(value) <= 10:
        return None
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return result if result.tzinfo else None
    except ValueError:
        return None

def display(value):
    parsed = date(value)
    if parsed:
        return parsed.astimezone(BJT).strftime('%Y-%m-%d %H:%M')
    return value or '未公布'

def clean(value):
    return str(value or '').replace('|', '\\|').replace('\n', ' ').replace('\r', ' ').replace('[', '\\[').replace(']', '\\]')

def link(label, url):
    return f'[{clean(label)}](<{url}>)' if url else clean(label)

def urls(value):
    if isinstance(value, list):
        return [u for u in value if u]
    return [value] if value else []

def phase_status(event, as_of):
    if event.get('status_override'):
        return event['status_override']
    start, end = date(event.get('start')), date(event.get('end'))
    if start and end:
        if as_of < start:
            return '待开始'
        if as_of < end:
            return '赛程内'
        return '赛程已过'
    end_day = (event.get('end') or '')[:10]
    start_day = (event.get('start') or '')[:10]
    today = as_of.astimezone(BJT).date().isoformat()
    if re.fullmatch(r'2026-\d{2}-\d{2}', end_day) and end_day < today:
        return '赛程已过'
    if re.fullmatch(r'2026-\d{2}-\d{2}', start_day) and start_day > today:
        return '待开始'
    return '见赛期说明'

def table(events):
    result = ['| 编号 | 比赛／阶段 | 开始（北京时间*） | 结束（北京时间*） | 赛制／方式 | 参赛限制 | 状态 | 来源／入口 | 备注 |',
              '|---|---|---|---|---|---|---|---|---|']
    for e in events:
        sources = e.get('sources', [])
        links = [link('CTFtime' if 'ctftime.org' in u else f'证据{i+1}', u) for i, u in enumerate(sources)]
        if e.get('official_url'):
            links.append(link('赛事入口', e['official_url']))
        if e.get('source_level'):
            links.insert(0, clean(e['source_level']))
        fields = [e['record_id'], clean(e['title']), display(e.get('start')), display(e.get('end')),
                  clean(e.get('format')) + '／' + clean(e.get('mode')), clean(e.get('restrictions', '未说明')),
                  clean(e['status']), ' · '.join(dict.fromkeys(links)), clean(e.get('notes', ''))]
        result.append('| ' + ' | '.join(fields) + ' |')
    return '\n'.join(result) + '\n'

def main():
    manifest = read('fetch_manifest.json')
    as_of = datetime.fromisoformat(manifest[0]['fetched_at_utc'])
    raw = read('ctftime_api_raw.json')
    base = [e for e in raw if e['start'].startswith('2026')]
    html_ids = set(map(int, re.findall(r'/event/(\d+)', (SRC / 'ctftime_2026.html').read_text(encoding='utf-8'))))
    assert len(raw) < 1000, 'API response may be truncated'
    assert {e['id'] for e in base} == html_ids, 'API and yearly HTML IDs differ'
    assert len({e['id'] for e in raw}) == len(raw), 'Duplicate CTFtime IDs'
    restrictions = {'Open':'公开', 'Individual':'个人', 'Casual':'休闲活动', 'Academic':'学术／学生队伍',
                    'Prequalified':'仅晋级队伍', 'High-school':'中学生', 'Invited':'受邀队伍'}
    formats = {'Jeopardy':'解题赛', 'Attack-Defense':'攻防赛', 'Hack quest':'闯关赛'}
    events, crossing = [], []
    for e in raw:
        start, end = date(e['start']), date(e['finish'])
        if not (start < YEAR_END and end >= YEAR_START):
            continue
        record = {'record_id': f"CTF-{e['id']}", 'ctftime_id': e['id'], 'title': e['title'],
                  'start': e['start'], 'end': e['finish'], 'original_start': e['start'], 'original_end': e['finish'],
                  'format': formats.get(e['format'], e['format']), 'mode': ('线下：' + (e['location'] or '地点未列出')) if e['onsite'] else '线上',
                  'restrictions': restrictions.get(e['restrictions'], e['restrictions']),
                  'organizers': [x['name'] for x in e['organizers']], 'ctftime_weight': e['weight'],
                  'official_url': e['url'], 'sources': [e['ctftime_url']], 'notes': '', 'source_group':'CTFtime'}
        (events if start >= YEAR_START else crossing).append(record)

    all_inputs = []
    for filename in ['local_overrides.json', 'global_supplement.json', 'china_supplement.json', 'domestic_calendar.json']:
        if (SRC / filename).exists():
            all_inputs.append((filename, read(filename)))
    watchlist, coverage_notes, uncertain_details = [], [], []
    by_id = {e['ctftime_id']:e for e in events + crossing}
    merged = []
    for filename, data in all_inputs:
        for override in data.get('overrides', []):
            e = by_id.get(override.get('ctftime_id'))
            if not e:
                continue
            for old, new in [('corrected_start','start'), ('corrected_end','end'), ('status_override','status_override')]:
                if override.get(old):
                    e[new] = override[old]
            if override.get('notes'):
                e['notes'] = (e['notes'] + ' ' + override['notes']).strip()
            for url in urls(override.get('source_url')) + urls(override.get('sources')) + urls(override.get('additional_sources')):
                if url not in e['sources']:
                    e['sources'].append(url)
        watchlist.extend(data.get('watchlist', []))
        watchlist.extend(dict(e, notes=e.get('reason', '')) for e in data.get('unresolved', []))
        uncertain_details.extend(data.get('date_uncertain_events', []))
        coverage_notes.extend(data.get('coverage_notes', []))
        coverage_notes.extend(data.get('audit_notes', []))
        for i, item in enumerate(data.get('events', []), 1):
            item = dict(item)
            item['official_url'] = item.get('official_url') or item.get('url', '')
            item['mode'] = item.get('mode') or item.get('location', '未说明')
            item['format'] = formats.get(item.get('format'), item.get('format', '未说明'))
            for field in ['start', 'end']:
                value = item.get(field)
                if value and len(value) > 10 and not date(value) and item.get('timezone') == 'Asia/Shanghai':
                    item[field] = datetime.fromisoformat(value).replace(tzinfo=BJT).isoformat()
            cid = item.get('ctftime_id')
            if cid and cid in by_id:
                target = by_id[cid]
                target['notes'] += ' ' + item.get('notes', '')
                if item.get('restrictions'):
                    target['restrictions'] = item['restrictions']
                if item.get('date_precision') == 'day':
                    target['notes'] += ' 本行钟点来自CTFtime，补充官网只核实到日期。'
                target['sources'] = list(dict.fromkeys(target['sources'] + urls(item.get('source_url')) + urls(item.get('sources')) + urls(item.get('additional_sources'))))
                merged.append({'source_file':filename, 'title':item['title'], 'ctftime_id':cid})
                continue
            prefix = {'global_supplement.json':'INT', 'china_supplement.json':'CN', 'domestic_calendar.json':'CAL'}[filename]
            item.update(record_id=f'{prefix}-{i:03}', source_group=filename)
            if item.get('date_precision') == 'day' and item.get('timezone') != 'Asia/Shanghai':
                item['notes'] = '日期沿用来源当地日期，未换算北京时间；' + item.get('notes', '')
            item['sources'] = list(dict.fromkeys(urls(item.get('source_url')) + urls(item.get('sources')) + urls(item.get('additional_sources'))))
            item.setdefault('notes','')
            item.setdefault('restrictions','未说明；见规则')
            events.append(item)

    for e in events + crossing:
        e['status'] = phase_status(e, as_of)
        e['start_display'] = display(e.get('start'))
        e['end_display'] = display(e.get('end'))
        e['start_beijing'] = display(e.get('start')) if date(e.get('start')) else None
        e['end_beijing'] = display(e.get('end')) if date(e.get('end')) else None
        assert e['sources'], f"Missing source: {e['title']}"
        if date(e.get('start')) and date(e.get('end')):
            assert date(e['start']) <= date(e['end']), e['title']
    events.sort(key=lambda e:(display(e.get('start')) if re.match(r'2026-\d\d', display(e.get('start'))) else '9999', e['title']))
    months = {f'2026-{m:02}':[] for m in range(1,13)}
    uncertain = []
    for e in events:
        month = display(e.get('start'))[:7]
        (months[month] if month in months else uncertain).append(e)
    stamp = as_of.astimezone(BJT).strftime('%Y-%m-%d %H:%M')
    upcoming = [e for e in events if e['status'] in ['待开始','赛程内']]
    counts = Counter(e['status'] for e in events)
    preface = f'''# 2026 年 CTF 比赛全集（公开来源汇编）

检索快照：**{stamp}（北京时间，UTC+8）**。主清单共 **{len(events)} 条比赛／阶段记录**，其中 CTFtime {len(base)} 条、其他来源补充 {len(events)-len(base)} 条；另附 {len(crossing)} 条跨入 2026 年的赛事。

**“全集”指本次取得的公开来源集合，并非保证全球所有比赛无遗漏。2026 年尚未结束，未公告、私有赛和未被公开索引的校赛无法穷尽。** 取消／延期的历史公告保留并明确标记，不表示全部已举办。补充记录区分主办方公告、社区赛历和媒体来源，未将社区记录一律视为官方确认。

按开始月份排列。预赛、资格赛、决赛、独立赛段分别计数；名称含 2025 或 2027 但实际赛期在 2026 的记录也收录。**表头星号说明：有明确时区和钟点的记录换算为北京时间；只给日期且时区不明的国际记录沿用来源日期，并在备注注明，不假定是北京时间。** 只公布月份、日期的记录保留原精度，不擅自补时刻。具体资格与报名截止请查规则，不将比赛开始时间当作报名截止。

“赛程已过／赛程内／待开始”仅按检索时刻与公布时间计算，并非对实际举办结果的逐场确认。CTFtime 权重和原始 UTC 时间保存在 JSON 中。完整方法、遗漏范围及冲突处理见 [README](README.md)。

## 月份索引

| 月份 | 记录数 |
|---|---:|
'''
    for month, group in months.items():
        preface += f'| [{month}](#{month}) | {len(group)} |\n'
    if uncertain:
        preface += f'| 日期不完整 | {len(uncertain)} |\n'
    result = preface
    for month, group in months.items():
        result += f'\n## {month}\n\n' + (table(group) if group else '本次来源暂无已公布记录。\n')
    if uncertain:
        result += '\n## 日期不完整\n\n' + table(uncertain)
    result += '\n## 跨年补充（不计入主清单数量）\n\n' + table(crossing)
    if uncertain_details:
        result += '\n## 确认存在但完整赛期未核实（不计入主清单数量）\n\n'
        for e in uncertain_details:
            result += '- ' + link(e['title'], e.get('source_url')) + '：' + clean(e.get('date_display')) + '。' + clean(e.get('notes')) + '\n'
    if watchlist:
        result += '\n## 已有线索但赛期未定（不计入主清单数量）\n\n'
        for e in watchlist:
            result += '- ' + link(e['title'], e.get('source_url') or e.get('official_url')) + '：' + clean(e.get('notes')) + '\n'
    write('2026_CTF比赛全集.md', result)
    write('2026_后续赛程.md', f'# 2026 年后续 CTF 赛程\n\n截至 {stamp} 北京时间，共 {len(upcoming)} 条尚未开始或处于公布赛期内的记录。已取消、延期未定的记录不列入本表。资格、时刻变更以每行来源为准。仅公布月份、或有开始日期但结束日期不明的条目可能未进入本表，请同时查看全集。\n\n*有钟点的时间已换算为北京时间；只给日期的国际记录沿用来源日期，详见备注。\n\n' + table(upcoming))
    output = {'snapshot_time_beijing':as_of.astimezone(BJT).isoformat(), 'timezone':'Asia/Shanghai',
              'count':len(events), 'ctftime_count':len(base), 'supplement_count':len(events)-len(base),
              'events':events, 'cross_year_events':crossing, 'date_uncertain_events':uncertain_details, 'watchlist':watchlist, 'coverage_notes':coverage_notes}
    write('2026_CTF比赛数据.json', json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    audit = {'ctftime_api_year_count':len(base), 'ctftime_html_year_count':len(html_ids), 'same_id_set':True,
             'raw_api_count_including_boundary_window':len(raw), 'requested_api_limit':1000,
             'count':len(events), 'monthly_counts':{m:len(g) for m,g in months.items()},
             'undated_count':len(uncertain), 'status_counts':dict(counts), 'cross_year_count':len(crossing),
             'upcoming_count':len(upcoming), 'merged_duplicates':merged,
             'unique_record_ids':len({e['record_id'] for e in events}), 'sources_present_for_all':True,
             'ordered_dates_valid':True}
    write('sources/validation_report.json', json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
    readme = f'''# 2026 年 CTF 比赛资料

整理日期：**2026-11-06**。状态计算基准：**{stamp}，北京时间**。

已整理 **{len(events)} 条比赛／阶段／独立赛道记录**：CTFtime {len(base)} 条，其他公开来源去重补充 {len(events)-len(base)} 条。另有 {len(crossing)} 条跨年记录、{len(uncertain_details)} 条赛期未完整核实记录，以及 {len(watchlist)} 条待核／待公告线索。

## 文件入口

- [2026_CTF比赛全集.md](2026_CTF比赛全集.md)：按月份列出所有收录记录，每行附来源和赛事入口。
- [2026_后续赛程.md](2026_后续赛程.md)：{len(upcoming)} 条待开始或处于公布赛期内的记录。
- [2026_CTF比赛数据.json](2026_CTF比赛数据.json)：用于筛选、排序、二次处理的结构化数据。
- [sources/validation_report.json](sources/validation_report.json)：数量、月份、状态、重复合并和来源检查结果。
- `sources/`：CTFtime原始JSON和全年网页、国内外补充数据、官方公开接口快照、人工修订依据。
- `scripts/`：CTFtime采集和目录生成脚本。

## 收录范围与“全集”的含义

本目录是截至检索日能够取得的公开来源汇编。**已完整取得CTFtime当前2026全年列表，不能据此声称全球所有CTF无一遗漏。** 2026年尚未结束，11—12月仍可能新增、改期或取消比赛；私有、企业内部、未公开索引的校赛，以及其他平台未检索到的赛事可能遗漏。

主清单按2026年开始的赛事收录，预赛、决赛、独立赛段和平台上独立参赛的赛道分别计数，因此总数不是赛事品牌数量。包含有明确比赛窗口的训练赛；长期靶场、无赛期练习平台、纯知识竞赛、作品评比和普通漏洞赏金计划不作为独立CTF列入。名称含2025或2027但开始时间在2026的赛事照常保留。跨入2026的旧年赛事单列，不重复计入主清单。

取消、延期的原始公告属于赛事历史记录，保留在全集并标明状态。“赛程已过”仅意味着公布结束时间早于检索时刻，**不是逐场验证已经举办成功**。赛事报名资格、人数、报名截止及最终日程仍以行内主办方规则为准。

## 时间与异常处理

- 有明确时区与钟点的时间转为北京时间UTC+8；Markdown展示到分钟，原始秒数保留在JSON。
- 只有日／月的记录保留原精度；国际来源时区不明时沿用来源日期，并在备注说明，不补零点、不假定为北京时间。
- 部分多日赛事只在每天指定时段开放；TPCTF等记录的起止是外层时间范围，实际开放窗口见备注与JSON的`sessions`。
- Google公开资格赛、DeadSec延期；DownUnder取消；BCACTF的官网取消公告与CTFtime届次不一致，已标待核。
- Scarlet采用主办方在CTFtime说明中的更正；DEF CON预赛按主办方时间修正30分钟。原始时间保存在`original_start/original_end`。
- SecLeaf存在IST与UTC冲突；Holmes的时长描述与明确起止时间冲突，均写入备注。没有以猜测覆盖来源。
- 月份级日程、已存在但完整赛期未核实的比赛不一定出现在后续赛程摘录中，完整线索请查全集末尾。

## 来源与验证

1. [CTFtime 2026全年列表](https://ctftime.org/event/list/?year=2026)与[官方API说明](https://ctftime.org/api/)：抓取范围2025-12-01 UTC至2027-01-02 UTC，limit=1000，实际返回{len(raw)}条；其中2026开始的{len(base)}个赛事ID与全年网页{len(html_ids)}个ID完全一致，没有达到返回上限。跨年补充仅来自这个边界窗口。
2. 国际补充来自主办方活动页、规则、公告，包括picoCTF、Snyk、Hack The Box、Huntress、FLARE-On等；MITRE eCTF已与CTFtime对应记录合并。
3. 国内补充来自主办方／承办高校公告、官方公开平台接口及Hello-CTF赛历。每条都保留证据链接；社区日历不能替代主办方最终通知，来源层级见备注或源JSON。
4. 已检查赛事ID、记录编号、日期先后、来源字段、按月数量；独立复核了国际补充、时间换算与取消／延期标记。详细报告见`sources/validation_report.json`。

## 数据字段与复现

`events`是主清单；`cross_year_events`是跨年补充；`date_uncertain_events`与`watchlist`不计入主清单总数。

`start/end`保留明确时区的ISO时间，或来源的YYYY-MM-DD／YYYY-MM日期；`null`表示未公布。`start_beijing/end_beijing`只在能准确换算钟点时有值，否则为null。`start_display/end_display`用于展示，可能是尚未换算的来源日期，须同时读取`timezone/date_precision/notes`。`sources`为证据；`official_url`沿用源数据字段名，表示赛事相关入口，个别为通知转载，须结合`source_level`判断。未对所有站点逐一检查当前可用性。`ctftime_weight`是抓取时快照，非固定赛事质量评级。

在本目录运行以下命令，可从现有快照重新生成清单（只依赖Python标准库）：

```powershell
python .\\scripts\\build_catalog.py
```

`fetch_ctftime.py`可重新采集CTFtime，但会覆盖同名快照。刷新前请备份；人工补充、修订与国内平台数据不会随该脚本自动更新，需重新核查。

## 进一步覆盖说明

'''
    for note in dict.fromkeys(coverage_notes):
        readme += '- ' + str(note) + '\n'
    write('README.md', readme)
    print(json.dumps(audit, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
