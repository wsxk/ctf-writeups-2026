"""Render reviewed, challenge-specific reverse-engineering notes. Never execute challenges."""
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / 'sources/reverse_ai_inventory.json'
NOTES = ROOT / 'sources/reverse_ai_notes.tsv'

def main():
    challenges = json.loads(INVENTORY.read_text(encoding='utf-8'))
    rows = []
    for line in NOTES.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'): continue
        fields = line.split('\t')
        if len(fields) != 6: raise ValueError((len(fields), line))
        index, mechanism, steps, result, caveat, source_hint = fields
        item = challenges[int(index)]
        folder = ROOT / item['directory']
        files = sorted(f for f in (folder/'writeups').rglob('*') if f.is_file() and f.suffix.lower() in {'.md','.txt','.py','.c','.cpp','.js','.sage','.pdf','.sh','.rs'})
        if not files:
            files = sorted((folder/'writeups').rglob('*.html'))
        links = [f'- [{f.relative_to(folder).as_posix()}]({quote(f.relative_to(folder).as_posix(), safe="/")})' for f in files]
        if any(f.suffix.lower() == '.pdf' for f in files) and item['event_title'].startswith('NCTF'):
            links.append('- [官方 PDF 的既有文本提取（含其他题，按章节定位）](../../../sources/NCTF_2026_Official_Writeup_text.txt)')
        if not links: links = ['- [原始解答目录](writeups/)']
        body = f'''# {item['title']}：AI 可读解题说明

## 任务与证据范围

- 比赛：{item['event_title']}；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：{source_hint}
- 附件登记状态：{item['attachment_state']}。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

{mechanism}

## 按依赖顺序求解

'''
        for n, step in enumerate(steps.split(' || '), 1):
            body += f'{n}. {step}\n'
        body += f'''
## 结果与验证标准

{result}

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

{caveat}

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

'''
        body += '\n'.join(links) + '\n'
        (folder/'AI_WRITEUP.md').write_text(body, encoding='utf-8')
        rows.append({'directory':item['directory'], 'mechanism':mechanism, 'evidence':[f.relative_to(folder).as_posix() for f in files], 'limitations':caveat, 'status':'static_analysis_not_executed'})
    (ROOT/'sources/ai_rewrite_reverse_summary.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Rendered {len(rows)}/{len(challenges)} reverse writeups')

if __name__ == '__main__': main()
