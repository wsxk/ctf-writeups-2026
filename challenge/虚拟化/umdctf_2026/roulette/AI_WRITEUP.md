# roulette — AI 可读解题说明

- 比赛：UMDCTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

按确定的前向状态链计算校验所需的27个小端uint32。

CRT与VM输出只依赖已知索引、查表和前轮状态，每轮input_word=VM_output XOR target，因此无需逆散列。

## 证据与输入

- [writeups/1_README.md](writeups/1_README.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 按真实输入长度检查定位主验证，原文声称106字节拆为27字，末两字节来自NUL/零初始化；先核对读取函数的终止和补零行为。
2. 从0x499ee0/0x499e60/0x499de0/0x499d60提取表，用CRT组合当前两组余数和模数，记录r15/rbx更新公式。
3. 解释0x499be1处VM：8字节slot先做隐含R[dst]=R[src]；opcode2–9还从下一slot取操作数，实际消耗16字节，NOP只8字节。
4. 以R0=CRT结果、R1=rbx、R2=i、其他0执行，取R6并XOR目标得到下一个输入word，再推进运行状态。
5. 完成27轮后检查rbx=0x6286239c，小端串接并按真实长度截取，回代原程序。

## 验证标准与结果

原文报告 UMDCTF{I_R3ALLY-want-to-pl4y-the-p0werball,+but-my-d4d-said-no-so-im-b3tting-ill-win-on-POLYMARKETinstead}。该候选为106字节，与长度检查一致；仍需逐字节正向回代。

## 限制与易错点

本地仅README，完整四表和循环公式需从代码块/附件提取；原文把某些常量笼统叫MurmurHash，应保留实际VM而非替换为标准库hash。106/108字节边界也不能凭假设补零。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
