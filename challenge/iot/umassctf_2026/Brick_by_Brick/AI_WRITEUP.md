# Brick_by_Brick — AI 易理解版 Writeup

> 比赛：UMassCTF 2026｜目录分类：iot｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是把时间戳/逻辑电平CSV解为UART，再从伪Linux启动日志取HEX编码flag。核心参数约30us/bit、33333baud、8N1、LSB-first。

## 材料与证据

- [writeups/1_README.md](<writeups/1_README.md>)

## 推导与解题步骤

1. 读取timestamp与logic_level，统计相邻采样间隔及高低run长度。约30/60/90us的倍数提示位周期，但需用多帧起止位验证。

2. 从空闲高到低的start边沿，以1.5T、2.5T直到8.5T取8个数据bit，用sum(bit<<位置)还原字节；9.5T应为高停止位。

3. 输出ASCII日志，定位secretflag:后的554d4153537b553452375f31355f3768335f623335372c5f72316768373f7d，再HEX解码。

## 结果与验证

原文结果 `UMASS{U4R7_15_7h3_b357,_r1gh7?}`。应核对UART停止位、可读日志和HEX转码三个层次。

## 复现边界与易错点

原文run持续时间实现用timestamps[j-1]-timestamps[i]，会少一个采样间隔；不要原样照抄。按半开区间边界计算，或直接使用时间轴中心采样。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
