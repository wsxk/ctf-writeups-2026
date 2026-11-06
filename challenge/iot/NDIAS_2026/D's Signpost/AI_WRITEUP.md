# D's Signpost — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：iot｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是从五路混合RF信号恢复加密ZIP与密码。输入SigMF为cf32_le、500ksps、中心915MHz，关键信息分属+115kHz的APRS和+170kHz的DQPSK。

## 材料与证据

- [writeups/kn1cht_full_writeup.md](<writeups/kn1cht_full_writeup.md>)

本题在合集中的定位：kn1cht合集 RF / D's Signpost。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 读取SigMF元数据并组复数IQ；FFT找到-180k、-70k、+45k、+115k、+170kHz。逐通道下变频、低通后再抽取，避免混叠。

2. -180kHz包络莫尔斯提示五路信号；+45kHz语音指向APRS密码，-70kHz提示比较前后符号相位。

3. +115kHz先FM解调，再Bell202 AFSK(1200/2200Hz，1200bps)，还原NRZI、定位HDLC7E、去bit stuffing并验证AX.25 FCS，得到密码dWt4Wxm6Xfn1ot02。

4. +170kHz在21.3—25.35秒按250baud采样，25kHz基带下每符号100样本。比较相邻符号相位，四峰0、±π/2、π支持DQPSK。

5. 探索残余频偏、符号边界、4!位对映射与字节偏移；原文最终boundary=13、跳过26bit、MSB-first，定位PK0304与flag.txt。

6. 以APRS密码解压ZIP，读取flag.txt。

## 结果与验证

原文结果 `FLAG{R4D10_FR3Q_L1TTL3_M4Z3}`。有效AX.25 CRC、ZIP结构及解压CRC共同支持结果。

## 复现边界与易错点

最终solver依赖aprs_decode、clean_extract等未在本题writeups目录提供的模块，不能直接复制末尾代码就宣称可运行；正文给出算法片段，但仍需补齐辅助函数。

附件登记状态：缺失。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
