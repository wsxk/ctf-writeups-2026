# Dantes_Trial — AI 可读解题说明

- 比赛：Srdnlen CTF 2026 Quals
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

恢复GBA ROM输入，使自定义64位散列达到目标。

169字节字节码封装读字符和散列循环，真正难点是正确模拟ARM移位加法链后再穷举短输入。

## 证据与输入

- [writeups/1_dantes-trial.md](writeups/1_dantes-trial.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 定位ROM偏移0x22654的程序，恢复16类置换/XOR opcode，确认主循环读字符→hash→重复。
2. 重现逐字符XOR、FNV乘法、索引混合、S-box与golden-ratio混合；finalize包含FNV_PRIME=0x100000001B3及fmix64。
3. 核对Thumb的lsls r0,r6,#0x1f为左移31位，不是右移；用原作者提到的Unicorn逐状态对拍，确认每个64位截断。
4. 固定hash=0x73f3ebcbd9b4cd93，搜索长度1–6可打印串，复用部分hash状态并并行外层；将命中串重新正向计算。

## 验证标准与结果

作者报告长度1–5无解、长度6得到W1H31l，提交 srdnlen{W1H31l}。必须以正确散列及ROM接受双重验证，较小长度无解结论仅限作者搜索范围。

## 限制与易错点

原文引用brute2.c、solve_correct.py和vm_emu2.py但本地仅README。缺失S-box/具体混合公式需从ROM补齐；不要对错误hash实现进行无界暴力。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
