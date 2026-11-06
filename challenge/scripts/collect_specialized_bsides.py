"""BSidesSF 2026 official Android APKs, source, and solutions."""
import json
from collect_specialized import ROOT,record,github,finish,LOG

original=ROOT/'sources/pwn_trees/BSidesSF__ctf-2026-release.json'
tree=json.loads(original.read_text(encoding='utf-8'))
tree['tree']=[x for x in tree['tree'] if not x['path'].endswith(('solution/frida-server','solution/apktool_2.12.1.jar'))]
selected=ROOT/'sources/specialized_bsides_selected_tree.json'
selected.write_text(json.dumps(tree),encoding='utf-8')
for title in ['doremi','vinyl-drop']:
    m=record('CTF-3108','android',title,notes='BSidesSF 2026 官方 Android APK、源码及 solution 正文/脚本/图片。仓库内通用工具 frida-server 和 apktool JAR 未重复下载；题目APK与解题脚本已保存。')
    github(m,'BSidesSF/ctf-2026-release',title,selected);finish(m)
(ROOT/'sources/specialized_bsides_search.json').write_text(json.dumps({'records':LOG,'source':'https://github.com/BSidesSF/ctf-2026-release'},ensure_ascii=False,indent=2),encoding='utf-8')
