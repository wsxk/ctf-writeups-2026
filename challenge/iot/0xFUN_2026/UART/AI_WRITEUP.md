# UART — AI 易理解版 Writeup

> 比赛：0xFUN CTF 2026｜目录分类：iot｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是从Sigrok逻辑采样还原UART字节并解出flag。`.sr`本来就是ZIP容器，不应将ZIP结构本身误判为题目伪装。

## 材料与证据

- [writeups/RobinVA.md](<writeups/RobinVA.md>)

## 推导与解题步骤

1. 解开会话文件读取metadata：1通道、采样率1MHz、unitsize=1、probe标为uart.ch1；定位logic-1-1原始采样。

2. 统计最短稳定高/低脉宽，约8—9us，对应常用115200baud；采样率/9只是近似估计，不是精确波特率。

3. 在UART解码器中设置rx=0、baudrate=115200，检查起始低电平、8位LSB-first数据、停止高电平；不要将采样字节直接当串口数据。

4. 导出rx-data十六进制字节并转ASCII，查看完整内容。

## 结果与验证

原文结果 `0xfun{UART_82_M2_B392n9dn2}`。参考解码命令：`sigrok-cli -i logic-1-1 -I binary:numchannels=1:samplerate=1000000 -P uart:baudrate=115200:rx=0 -A uart=rx-data`。

## 复现边界与易错点

原文用截图展示采样细节，正文已给关键参数；本次未运行Sigrok，不将其输出当现场验证。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
