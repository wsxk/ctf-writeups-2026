"""Additional official Android and IoT challenge archives; download only."""
import json
from collect_specialized import ROOT, record, save, blog, github, finish, LOG

for category,title,prefix in [('iot','SU_老年固件','re/SU_老年固件'),('android','SU_flumel','re/SU_flumel')]:
    m=record('CTF-3161',category,title,notes='SUCTF 2026 官方归档。固件题归入 iot；Flutter/Dart/Hermes/Native APK 题归入 android。原题压缩包、源码、官方题解与 exp 一并保留。')
    github(m,'team-su/SUCTF-2026',prefix,ROOT/'sources/pwn_trees/team-su__SUCTF-2026.json');finish(m)

m=record('CTF-3247','android','back_and_forth',notes='BYUCTF 2026 官方 APK、Java 源码与 README 完整题解。附题解图片与原始 brute.py，未执行。')
tree_file=ROOT/'sources/pwn_trees/BYU-CSA__BYUCTF-2026.json'
github(m,'BYU-CSA/BYUCTF-2026','rev/back_and_forth',tree_file)
sha=json.loads(tree_file.read_text())['sha']
for p in ['README.md','brute.py','image.png']:
    save(m,'https://raw.githubusercontent.com/BYU-CSA/BYUCTF-2026/'+sha+'/rev/back_and_forth/'+p,'writeups/'+p)
finish(m)

m=record('CTF-3201','android','d3llvm',notes='D^3CTF 2026 OLLVM 混淆 Android native 逆向。官方中英文完整 writeup PDF 及参赛者 README/solver 已下载。参赛者仓库明确未上传原 APK / MNN 模型，未找到公开原题附件地址；请勿将解题脚本视为题目附件。')
github(m,'hax1ng/d3ctf-2026-writeups','rev/d3llvm',ROOT/'sources/specialized_d3ctf-2026-writeups_tree.json',all_writeup=True)
for lang in ['CN','EN']:
    save(m,'https://raw.githubusercontent.com/D-3CTF/D3CTF-2026-Official-Writeup/main/D3CTF-2026-Official-Writeup-'+lang+'.pdf','writeups/D3CTF-2026-Official-Writeup-'+lang+'.pdf')
finish(m)

m=record('CTF-3364','android','Backdrop',notes='Securinets CTF Quals 2026，Android Flutter APK / 定时器 / 渲染错误 / 签名绑定解密。两个参赛者 writeup 均已保存；原APK另查镜像。文章引用的 AGENTS.md 是赛题诱饵数据，不是本工作区指令。')
blog(m,'https://khalilammar.me/writeups/backdrop-securinets-quals','KhalilAmmar')
blog(m,'https://pentest.bi0s.in/blog/posts/securinet-quals-ctf-backdrop/','bi0s')
finish(m)
(ROOT/'sources/specialized_extra_search.json').write_text(json.dumps({'records':LOG,'queries':['SUCTF 2026 SU_flumel SU_老年固件','BYUCTF 2026 back_and_forth','d3llvm 2026 APK','Backdrop Securinets 2026 APK writeup']},ensure_ascii=False,indent=2),encoding='utf-8')
