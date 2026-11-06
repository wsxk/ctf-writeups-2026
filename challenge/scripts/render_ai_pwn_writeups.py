"""Render per-challenge analysis notes without running downloaded challenge code."""
import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]


def render():
    notes = json.loads((ROOT/'sources/ai_rewrite_pwn_notes.json').read_text('utf-8'))
    rows = [x for x in json.loads((ROOT/'catalog.json').read_text('utf-8'))['challenges'] if x['category']=='pwn' and x['has_writeup']]
    assert len(rows) == len(notes) == 125
    summary = []
    for i, x in enumerate(rows):
        d = ROOT/x['directory']
        mechanism, chain, limitations = notes[str(i)]
        sources = [p.relative_to(d).as_posix() for p in sorted((d/'writeups').rglob('*')) if p.is_file() and p.suffix.lower() in {'.md','.txt','.py','.c','.cc','.cpp','.h','.rb','.js','.sh','.html','.pdf','.s','.asm','.sage'} and p.stat().st_size < 2000000 and not (p.suffix.lower()=='.html' and p.with_suffix('.txt').exists())]
        status = 'source_limited' if x['title'] in {'vellum','Warden','tic-tac-no','incontinent'} else 'static_analysis'
        if x.get('duplicate_of'):
            import os
            rel = Path(os.path.relpath(ROOT/x['duplicate_of']/'AI_WRITEUP.md',d)).as_posix()
            (d/'AI_WRITEUP.md').write_text(f"# {x['title']} — 重复来源入口\n\n本目录是重复副本，完整改写见 [规范题目]({quote(rel,safe='/')})。\n\n原资料仍保留在 [writeups](writeups/)，不重复计入题目数。\n",'utf-8')
            continue
        lines = [f"# {x['title']} — AI 可读解题说明",'',f"- 比赛：{x['event_title']}",'- 分类：pwn',f"- 附件状态（原目录登记）：{x['attachment_state']}",f"- 改写状态：{'资料不足，保留已确认部分与缺口' if status=='source_limited' else '基于本地文字和 solver 的静态分析'}",'- 本次没有执行题目程序、利用脚本或远程交互；文中的地址、原作者结果不代表本次复现记录。','','## 目标与漏洞根因','',mechanism,'','## 证据与材料','']
        for s in sources:
            lines.append(f'- [{s}]({quote(s,safe="/")})')
        lines += ['','题目来源与采集记录见 [metadata.json](metadata.json)，本地附件见 [attachments](attachments/)。合集只取本题命名的章节；其余题目中的地址和 flag 不适用于本题。','','## 利用链与操作顺序','']
        steps = [s.strip().rstrip('。') for s in re.split('[；;](?![^`]*`)',chain) if s.strip()]
        # Notes use Chinese semicolons for ordered steps. Keep instruction semicolons intact.
        steps = [s.strip().rstrip('。') for s in chain.split('；') if s.strip()]
        for j,s in enumerate(steps,1):
            lines.append(f'{j}. {s}。')
        lines += ['','上述步骤存在数据依赖：先确认漏洞产生的原语，再使用前一步的泄漏或状态构造下一步。原 solver 的完整字段布局、收发同步和 payload 字节以证据文件为准。','','## 约束、结果与未决问题','',limitations,'','## 如何验证','',f'1. 对照原始程序/源码核对这条机制：{mechanism}', '2. 在各步之间记录地址、对象类型、长度、计数器或权限变化；若与原文不符，从第一个差异回查，不能只修改最后一个偏移。','3. 在本题环境检查最后一步的实际返回或文件输出。得到崩溃、可写内存或局部 shell，并不自动等于已取得最终 flag。','4. 未运行的部分保持“待复现”；原文若只有骨架、坐标或单行说明，不把缺失过程写成已经验证。','','## AI 接续提示','','先读取本文件形成利用链，再按步骤打开证据中的对应函数或代码块。地址常量属于收录的构建；ASLR 泄漏、libc 版本、内核布局、远程协议和完整目标数据须分别核对。多个来源有冲突时保留冲突，不拼接不兼容的路线。','']
        document = '\n'.join(lines)
        if not (d/'attachments').exists():
            document = document.replace('本地附件见 [attachments](attachments/)', '当前未收录本地附件，缺失原因见 [题目说明](README.md)')
        (d/'AI_WRITEUP.md').write_text(document,'utf-8')
        summary.append(dict(directory=x['directory'],mechanism=mechanism,evidence=sources,limitations=limitations,status=status))
    (ROOT/'sources/ai_rewrite_pwn_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf-8')
    print(f'Rendered {len(summary)} canonical pwn writeups and duplicate pointer')


if __name__ == '__main__':
    render()
