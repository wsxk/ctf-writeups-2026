"""Render manually analysed VM notes; never executes challenge code."""
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]


def render():
    notes = json.loads((ROOT / 'sources/ai_rewrite_vm_notes.json').read_text('utf-8'))
    catalog = {x['directory']: x for x in json.loads((ROOT / 'catalog.json').read_text('utf-8'))['challenges']}
    summary = []
    for directory, n in notes.items():
        x = catalog[directory]
        d = ROOT / directory
        sources = n.get('sources') or [p.relative_to(d).as_posix() for p in sorted((d/'writeups').rglob('*')) if p.is_file() and p.suffix.lower() in {'.md', '.txt', '.py', '.c', '.js', '.pdf', '.html', '.asm'} and p.stat().st_size < 600000 and p.name not in {'constants.txt', 'dumps.txt'} and not (p.suffix=='.html' and p.with_suffix('.txt').exists())]
        lines = [f"# {x['title']} — AI 可读解题说明", '', f"- 比赛：{x['event_title']}", '- 分类：虚拟化', '- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。', f"- 附件登记状态：{x['attachment_state']}；具体文件以本题目录为准。", '', '## 目标与结论', '', n['goal'], '', n['mechanism'], '', '## 证据与输入', '']
        for p in sources:
            assert (d/p).exists(), (directory, p)
            lines.append(f'- [{p}]({quote(p, safe="/")})')
        lines += ['', '来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。', '', '## 分步推导与操作', '']
        lines += [f'{i}. {s}' for i,s in enumerate(n['steps'], 1)]
        lines += ['', '## 验证标准与结果', '', n['validation'], '', '## 限制与易错点', '', n['limitations'], '', '## AI 继续分析时的规则', '', '将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。', '']
        document = '\n'.join(lines)
        if not (d/'attachments').exists():
            document = document.replace('附件见 [attachments](attachments/)', '当前未收录本地附件，缺失原因见 [题目说明](README.md)')
        (d/'AI_WRITEUP.md').write_text(document, 'utf-8')
        summary.append(dict(directory=directory, mechanism=n['mechanism'], evidence=sources, limitations=n['limitations'], status='静态分析改写，未运行复现'))
    (ROOT/'sources/ai_rewrite_vm_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2), 'utf-8')
    print(f'Rendered {len(summary)} VM writeups')


if __name__ == '__main__':
    render()
