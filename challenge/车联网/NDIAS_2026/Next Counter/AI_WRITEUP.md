# Next Counter — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：车联网｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是预测另一Falcon X1设备下一次Unlock帧。重复发射不代表计数器每帧递增，计数器按按钮操作递增。

## 材料与证据

- [writeups/kn1cht_full_writeup.md](<writeups/kn1cht_full_writeup.md>)

本题在合集中的定位：kn1cht合集 Keyfob / Next Counter。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 用相同OOK/Manchester参数解capture_c3.bin。15帧分为每组三次重发，共5次操作。

2. 去重后帧为`AA AA D5 9C 4E 2B 20 01 NN 5A`，NN依次37、38、39、3A、3B；两字节计数器是大端0137至013B。

3. 保持前导、设备ID、命令20和尾字节5A不变，只把计数器增至013C。

## 结果与验证

原文记录 `flag{AAAAD59C4E2B20013C5A}`。先重建全部已观察帧再外推，可避免把固定尾字节当校验或错误增加重发计数。

## 复现边界与易错点

原文所列路径、地址和工具行为对应比赛附件版本。先核对本地附件及参数，再进行复现；本文不承诺历史远程服务仍可用。

附件登记状态：缺失。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
