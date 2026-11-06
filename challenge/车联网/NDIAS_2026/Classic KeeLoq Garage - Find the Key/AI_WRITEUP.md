# Classic KeeLoq Garage - Find the Key — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：车联网｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是由RF固定字段和安装备注恢复64位DeviceKey。备注直接给出Legacy派生式，不能将此题描述成攻击完整64位KeeLoq密钥空间。

## 材料与证据

- [writeups/kn1cht_full_writeup.md](<writeups/kn1cht_full_writeup.md>)

本题在合集中的定位：kn1cht合集 Classic KeeLoq Garage: Find the Key。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. Manchester解出`AA AA D5 | ENC32 | SERIAL32 | BTN8`；固定部分01D4A2B7 01，其中01对应OPEN。

2. 读取memo_c5c6.txt：seed=6D3A91C4，`K=SEED 

3.  (SEED XOR SERIAL)`。

4. 计算低32位6CEE3373，按高位seed、低位异或结果拼接。

5. 用同一key解多个Hop作为交叉验证：其低16位计数器应连续，参见下一题。

## 结果与验证

原文记录 `flag{6D3A91C46CEE3373}`。输出16个大写HEX字符，不是seed本身。

## 复现边界与易错点

原文所列路径、地址和工具行为对应比赛附件版本。先核对本地附件及参数，再进行复现；本文不承诺历史远程服务仍可用。

附件登记状态：缺失。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
