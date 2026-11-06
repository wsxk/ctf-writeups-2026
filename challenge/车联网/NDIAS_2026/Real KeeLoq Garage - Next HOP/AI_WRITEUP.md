# Real KeeLoq Garage - Next HOP — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：车联网｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是生成下次OPEN的逻辑帧。需要区分射频34bit固定字段和判题期待的32bit button+serial表示。

## 材料与证据

- [writeups/kn1cht_full_writeup.md](<writeups/kn1cht_full_writeup.md>)

本题在合集中的定位：kn1cht合集 Real KeeLoq Garage: Next HOP。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 使用BF61DA58FE545128解四个Hop，得到103D0040至103D0043。

2. 按`button(4)

3. status(2)

4. disc(10)

5. counter(16)`确认下一明文103D0044，再KeeLoq加密得2675F6FA。

6. 逻辑固定部为`button=1 

7.  serial=07A4C3D`，组成107A4C3D；不要对射频34bit右补零后输出041E930F4。

8. 拼接前导同步AAAAD5、Hop与逻辑固定字段。

## 结果与验证

原文记录 `flag{AAAAD52675F6FA107A4C3D}`。这是逻辑帧字符串，不能直接当作完整空中发射bitstream。

## 复现边界与易错点

原文所列路径、地址和工具行为对应比赛附件版本。先核对本地附件及参数，再进行复现；本文不承诺历史远程服务仍可用。

附件登记状态：缺失。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
