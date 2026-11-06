# Automaton — AI 可读解题说明

- 比赛：Haruulzangi CTF 2026 Qualifier
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

逆转gate.wasm的字节变换，得到check(len)=1的42字节token。

211字节数据段包括42字节目标、9字节密钥生成程序、160字节加密主程序；RC4仅用于KSA生成S-box，主变换可逐步求逆。

## 证据与输入

- [writeups/1_README.md](writeups/1_README.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 从WASM导出get_input/check和data段核对布局，输入地址为1048787，先确认长度检查。
2. 从初值109执行小VM12轮，生成key=3a88c6adf6fd92edb25349da，再运行RC4 KSA构造S与逆S；不要误加RC4 PRGA。
3. 按output=state^enc、newstate=(enc-75*oldstate+59)&255解码160字节程序，解析114条指令；递推需使用旧state。
4. 从42字节目标倒序执行指令逆运算：加减互换、左右旋互换、S-box换逆表、奇数乘法模256求逆；前缀/后缀原地链按相反索引方向撤销。

## 验证标准与结果

作者报告 HZ{TF98xY04_byt3c0d3_c0unt3rp4rt_L3XH5QDC}。应正向回算全部目标字节，再用runner.mjs或网页调用check确认返回1；格式匹配仅是初筛。

## 限制与易错点

本地README引用solve.py但未收录该脚本，需补全14类opcode的操作数宽度与语义。给出的候选为42字节，与目标长度一致。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
