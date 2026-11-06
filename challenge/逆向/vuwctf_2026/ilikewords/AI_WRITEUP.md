# ilikewords：AI 可读解题说明

## 任务与证据范围

- 比赛：VuwCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：1_writeup.txt 的Challenge 1 — ilikewords。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

随机4位数经修复repdigit后执行Kaprekar迭代总到6174，故URL XOR key固定。最终flag的%s不是用户答案，而是解密URL的偏移28起6字节wordle。

## 按依赖顺序求解

1. 跟踪printf参数，确认来源为url_buf+0x1c。
2. 用四位补零的Kaprekar规则恢复固定key6174并解URL。
3. 取指定6字节填flag模板，核对与网络输入验证是否解耦。

## 结果与验证标准

原文结果 VuwCTF{do_you_like_wordle_as_much_as_i?}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

不需要查询当天Wordle；时间检查只影响动态运行，不能把日期当flag的一部分。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/1_writeup.txt](writeups/1_writeup.txt)
