# VIN Hunter — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：车联网｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是通过CAN上的UDS读取VIN数据标识符F190，题目把flag放在该DID中。关键是先发现请求/响应CAN ID，再通过ISO-TP承载UDS。

## 材料与证据

- [writeups/NDIAS_official_explanations.pdf](<writeups/NDIAS_official_explanations.pdf>)

本题在合集中的定位：官方PDF第5—7页。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 按题目canproxy连接到隔离vcan0环境；区分CAN帧、ISO-TP重组和UDS负载。

2. 使用caringcaribou的UDS发现流程确定`TX=0x7E0`、`RX=0x7E8`。

3. 对该ID对读取DID `0xF190`，正响应为`62 F1 90`后接数据。官方dump_dids直接打印的是DID值，不能再错误地裁掉三字节。

4. 将十六进制`666c61677b76316e5f723361645f737563633373737d`解为ASCII。

## 结果与验证

官方记录 `flag{v1n_r3ad_succ3ss}`。检查响应ID及DID一致，防止读取其他ECU广播。

## 复现边界与易错点

原文所列路径、地址和工具行为对应比赛附件版本。先核对本地附件及参数，再进行复现；本文不承诺历史远程服务仍可用。

附件登记状态：部分。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
