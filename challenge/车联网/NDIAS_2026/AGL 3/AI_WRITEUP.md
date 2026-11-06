# AGL 3 — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：车联网｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是从AGL媒体资源恢复第三个flag。播放器中有音频，但QEMU默认启动未转发声音；提示藏在MP3末尾的人声及NATO字母拼读中。

## 材料与证据

- [writeups/NDIAS_official_explanations.pdf](<writeups/NDIAS_official_explanations.pdf>)

本题在合集中的定位：官方PDF第26—28页。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 查看Launcher的Media Player并定位`/media`中的MP3；文件名与Eine kleine Nachtmusik相关。

2. 离线提取音频并完整播放，重点听结尾。界面无声只能说明音频未重定向，不能推出文件没有隐藏内容。

3. 将结尾语音IMPERIAL OPERA与后续India、Mike、Papa等拼读互相校对，空格按明确的underscore提示转下划线。

## 结果与验证

由官方第28页文本得到 `FLAG{IMPERIAL_OPERA}`。两段语音给出的字符应一致。

## 复现边界与易错点

本次未播放附件音频，结果来自官方逐字转录。无需把整段音乐进行频谱隐写分析。

附件登记状态：缺失。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
