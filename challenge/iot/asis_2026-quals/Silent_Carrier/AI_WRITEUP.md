# Silent_Carrier — AI 易理解版 Writeup

> 比赛：ASIS CTF Quals 2026｜目录分类：iot｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是联合USB配置抓包与DMR IQ信号恢复隐藏莫尔斯音频。关键是TYT Enhanced Privacy对49bit AMBE数据施加固定异或掩码，而非直接对PCM做AES解密。

## 材料与证据

- [writeups/1_README.md](<writeups/1_README.md>)

## 推导与解题步骤

1. 筛选USB data_len=1032的传输并按顺序拼接片段，重建0xD0000字节codeplug。核对Radio ID1234、contact1、color1、slot1与RF一致。

2. 从原始偏移59C0提取8组16字节key。CPS展示值为原始字节全反转，计算必须明确采用raw_radio_key。

3. IQ从2.4MHz移频-15500Hz、低通、50倍抽取得48kHz，再差分相位解4FSK；使用每符号10.00284采样点修正漂移，三段共594 bursts。

4. 4级[-3,-1,+1,+3]映射dibit[3,2,0,1]，按DSD-FME表解交织，经mbelib纠错后才对49bit语音数据解密。掩码为AES-128-ECB(fixed_key,raw_radio_key)的高49bit，fixed_key=6e028d8acaeb9bbe4272fb82645631fa。

5. 以已知静音帧FEA20202020800验证：第1段用K7，第2/3段用K8。FEC在隐私异或前，错误率不能判断key。

6. 将AMBE经MD380模拟codec转8kHz音频，识别1kHz莫尔斯，点约80ms、划240ms、字母间600ms、单词间2.7s。

## 结果与验证

三段解出ASISN0 K3Y / N0 / V01C3，原文合成 `ASIS{N0_K3Y_N0_V01C3}`。关键证据是多组密文映射到相同静音帧，不依赖语音识别猜测。

## 复现边界与易错点

本地README引用的direct_best.py及codec工具未在writeups目录中提供；复现还需相应实现。固定掩码不意味着真实DMR所有隐私模式都相同。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
