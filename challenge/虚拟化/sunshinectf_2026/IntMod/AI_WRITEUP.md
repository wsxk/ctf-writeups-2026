# IntMod — AI 可读解题说明

- 比赛：SunshineCTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

从信号执行轨迹提取明文VM操作，解线性终态再逆混合。

SIGTRAP/SIGILL/SIGFPE通过ucontext改真实寄存器；90条可逆混合后用40个模65521的多项式约束检查40字节状态。

## 证据与输入

- [writeups/1_README.md](writeups/1_README.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 建立40字节/5个u64状态和正常执行信号语义，定位executor0x400ae0与unsealer0x4020e0；原文主张长度33+7字节padding。
2. 在解封装输出层收集完整逻辑指令，同时记录handler ucontext前后状态；仅hook普通executor会漏trap/JIT路径。
3. 回放每条解密op并对比下一状态，区分13个未取指诱饵；将op5/op6配成sum(F[j]*b^j)=target+c mod65521。
4. 在GF(65521)高斯消元求40个终态字节，检查值小于256；逆序撤销90条add/xor/odd-multiply/rotate/swap，乘法模2^64求逆。
5. 检查恢复的尾部填充，再把有效输入送原程序验证Correct。

## 验证标准与结果

作者报告 sun{I_L0v3_Int3rrupts&SelfMod!!!} 和七个0x07填充，该候选为33字节，与输入条件一致。只有完整状态对拍、线性系统残差为0和原程序接受才建立正确性。

## 限制与易错点

本地仅README，hook*.c/analyze.py/solve.py等未收录。原文称GDB无用属于作者经验，不能当一般限制；可用受控信号调试但需避免改变程序语义。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
