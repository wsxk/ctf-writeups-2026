# OutOfPhase — AI 易理解版 Writeup

> 比赛：ASIS CTF Quals 2026｜目录分类：iot｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是从相位编码的OFDM类WAV中恢复消息。编码器oopenc定义了载波置换、QPSK旋转、分块顺序及差分相位；呼号是所有伪随机变换的种子。

## 材料与证据

- [writeups/1_README.md](<writeups/1_README.md>)

## 推导与解题步骤

1. 从FANCY频域图案识别EP2AES，按base37→SplitMix64类混合→Speck类ARX生成器重建各域随机表。参数为8kHz、1440样点块、1280点FFT、160保护/重叠、256载波、6.25Hz间隔。

2. 定位前导并校正约1—2Hz载波偏移。参考前导与采集FFT相位差对时间的斜率给出delta_f，用`exp(-2j*pi*delta_f*n/8000)`消除频偏。

3. 对相邻块同载波做差分`S[t,k]/S[t-1,k]`；逆载波置换、QPSK旋转及4块顺序，将1024符号还原256字节。

4. 校验RS(255,191)，GF多项式187、fcr=5、generator=2，并核对byte255的CRC8。只拼EP2AES的part0/3、1/3、2/3，原文对应burst9、14、17。

5. 558字节拼接后逆domain2字节置换，再异或domain1密钥流；检查OOPH、u16长度、u32 CRC，最后读取message。

## 结果与验证

原文结果 `ASIS{R0t4t3dC4rri3rs_m1uAF0HBNhEJ4YJAUDQPhCNe2uk8vtY8mYVYg}`。层级校验应为前导→QPSK→RS/CRC8→OOPH及消息CRC。

## 复现边界与易错点

本地writeup仅存README，文中decode_data.py等辅助脚本是否包含在附件需另核；不能把原文列出的脚本名视为本地已存在。不可混入EP2DES等其他呼号分片。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
