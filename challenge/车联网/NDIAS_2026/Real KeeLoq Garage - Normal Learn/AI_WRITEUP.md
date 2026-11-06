# Real KeeLoq Garage - Normal Learn — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：车联网｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是从HCS301兼容固定字段及制造商代码派生DeviceKey。与Classic题不同，本题是Normal Learn，且34位固定部不可简单按整字节截断。

## 材料与证据

- [writeups/kn1cht_full_writeup.md](<writeups/kn1cht_full_writeup.md>)

本题在合集中的定位：kn1cht合集 Real KeeLoq Garage: Normal Learn。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 在434.040MHz提取250us Manchester chip；D5后为32位Hop与34位固定字段。

2. 固定字段按`status(2)

3. button(4)

4. serial(28)`拆，得到status=00、button=1、serial=07A4C3D，与备注缺失的上位标签相符。

5. 制造商key=89ABCDEF01234567。计算SourceH=60000000|serial=607A4C3D，SourceL=20000000|serial=207A4C3D，分别执行KeeLoq解密。

6. 得到KeyH=BF61DA58、KeyL=FE545128；拼成64位DeviceKey。

7. 用新key解四个观察Hop应得103D0040—103D0043，discrimination=03D应等于serial低10位。

## 结果与验证

原文记录 `flag{BF61DA58FE545128}`。连续计数与disc一致共同支持派生正确。

## 复现边界与易错点

原文所列路径、地址和工具行为对应比赛附件版本。先核对本地附件及参数，再进行复现；本文不承诺历史远程服务仍可用。

附件登记状态：缺失。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
