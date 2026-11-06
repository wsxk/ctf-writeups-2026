# Read the simple fob — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：车联网｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是恢复Manchester帧中同步字D5后的3字节Device ID，输入与Parking Lot Whisper相同。

## 材料与证据

- [writeups/kn1cht_full_writeup.md](<writeups/kn1cht_full_writeup.md>)

本题在合集中的定位：kn1cht合集 Keyfob / Read the simple fob。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 按433.920MHz、2Msps、500us chip提取OOK电平；每chip约1000个采样点，在内部采样避免边缘噪声。

2. 按`01→0,10→1`将两个chip还原一个bit；出现00或11时应修正帧边界或相位，而不是跳过错误。

3. 按MSB-first每8bit成字节，以`AA AA D5`作同步校验；多次重发应得到相同`AA AA D5 7A 21 CC 20 01 37 5A`。

4. 取D5后的7A 21 CC，大写十六进制无0x。

## 结果与验证

原文结果 `flag{7A21CC}`。同步字、三次重发一致性和字段长度是三个独立检查点。

## 复现边界与易错点

原文所列路径、地址和工具行为对应比赛附件版本。先核对本地附件及参数，再进行复现；本文不承诺历史远程服务仍可用。

附件登记状态：缺失。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
