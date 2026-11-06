# dotsbedashing：AI 可读解题说明

## 任务与证据范围

- 比赛：VuwCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：1_writeup.txt 的Challenge 2 — dotsbedashing。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

36项Morse表以ROL8隐藏字符；target每个dword先更新key=ROR32(key,1)再XOR。解出完整(length,bits)映回字符得到预期主体。

## 按依赖顺序求解

1. 从0x4020读36个小端entry，按高字节旋转恢复a-z0-9映射。
2. 以0xb1e1e1f1为初值解0x40c0目标流并按完整Morse项查表。
3. 输入主体the0world0says0hii，检查程序包装VuwCTF。

## 结果与验证标准

原文结果 VuwCTF{the0world0says0hii}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

比较helper实际只区分Morse长度，故运行接受集合更大；应从密文完整Morse模式恢复意图答案。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/1_writeup.txt](writeups/1_writeup.txt)
