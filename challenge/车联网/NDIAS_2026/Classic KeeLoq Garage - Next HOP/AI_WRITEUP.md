# Classic KeeLoq Garage - Next HOP — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：车联网｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是用已恢复的DeviceKey解密并递增Hop计数器，再重新加密生成下一OPEN帧。

## 材料与证据

- [writeups/kn1cht_full_writeup.md](<writeups/kn1cht_full_writeup.md>)

本题在合集中的定位：kn1cht合集 Classic KeeLoq Garage: Next HOP。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 使用key=6D3A91C46CEE3373及原文528轮KeeLoq，NLF=3A5C742E；保留32位数据宽度与64位key轮转索引。

2. 四个Hop 913B00D7、0020D1FB、80ED145B、314C03E4解为ADC40040—ADC40043，说明只需递增低16位。

3. 下一明文ADC40044加密得65317ADF；固定SERIAL=01D4A2B7、BTN=01保持不变。

4. 拼接`AA AA D5 | 65317ADF | 01D4A2B7 | 01`。

## 结果与验证

原文记录 `flag{AAAAD565317ADF01D4A2B701}`。必须先验证解密历史Hop及加密回环，不对密文直接加1。

## 复现边界与易错点

原文所列路径、地址和工具行为对应比赛附件版本。先核对本地附件及参数，再进行复现；本文不承诺历史远程服务仍可用。

附件登记状态：缺失。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
