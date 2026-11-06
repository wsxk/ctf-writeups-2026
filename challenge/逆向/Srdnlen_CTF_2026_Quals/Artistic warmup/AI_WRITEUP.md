# Artistic warmup：AI 可读解题说明

## 任务与证据范围

- 比赛：Srdnlen CTF 2026 Quals；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeups/writeup.md 的GDI检查与参考bitmap位置。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

API hash隐藏GDI调用；输入用Consolas绘到450×50 32bpp DIB，与静态参考像素逐字节XOR0xAA后比较。直接恢复参考图即可读flag。

## 按依赖顺序求解

1. 还原export hash到CreateDIBSection/CreateFontA/TextOutA等函数，确认尺寸和像素格式。
2. 按PE节表将RVA0xc5020映到文件offset，提取90000字节并XOR0xAA。
3. 按DIB行方向与BGRA排列恢复图像，核对字形和原像素比较。

## 结果与验证标准

原文结果 srdnlen{pl5_Charles_w1n_th3_champ1on5hip}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

DIB可能自底向上；字体渲染环境差异可能影响逐像素验证，读图后仍需保持确切字符。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/writeup.md](writeups/writeup.md)
