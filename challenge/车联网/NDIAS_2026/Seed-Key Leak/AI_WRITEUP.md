# Seed-Key Leak — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：车联网｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是逆向dealer_unlock.pyc中的UDS SecurityAccess算法，通过0x27解锁后读取DID1337。核心是32位旋转、加法与异或；这不是暴力猜测seed。

## 材料与证据

- [writeups/NDIAS_official_explanations.pdf](<writeups/NDIAS_official_explanations.pdf>)

本题在合集中的定位：官方PDF第8—10页。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 反编译dealer_unlock.pyc并定位derive_key，保留每一步32位截断。

2. 算法：`x=seed^0xA5C31F27; x=rol32(x,3); x=(x+0x1F1F0101)&0xffffffff; x^=0xDEADBEEF; key=ror32(x,1)`。

3. 对7E0/7E8发送`10 03`进入扩展会话，再发送`27 01`；从`67 01`之后读取大端seed。

4. 把计算结果编码为4字节大端，发送`27 02 <key>`，确认正响应后发送`22 13 37`，从`62 13 37`后解码flag。

## 结果与验证

验证至少包括扩展会话成功、SecurityAccess正响应和目标DID正响应；官方这段文本没有给出可独立核实的最终flag，不能挪用前题VIN flag。

## 复现边界与易错点

原文PDF复制出的代码含缩进/反斜线排版问题，复现时应重建语法。种子来自当前会话，不应硬编码历史seed。

附件登记状态：部分。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
