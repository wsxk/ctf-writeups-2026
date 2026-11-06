# soul — AI 可读解题说明

- 比赛：Thryve CTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

恢复16字节密钥，使VM校验通过且密文解出合理flag。

复杂八轮key检查最终仅压缩为一个字节，ACCESS GRANTED不保证解密正确。真正可利用的信息是51字节密文的16字节重复密钥XOR及已知格式。

## 证据与输入

- [writeups/README.md](writeups/README.md)
- [writeups/solve.py](writeups/solve.py)
- [writeups/vm.asm](writeups/vm.asm)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 按solve.py从0x3060解密0x819字节bytecode，恢复16个8位寄存器、512字节内存和15种opcode；密钥在0x000，S-box在0x020，密文在0x120。
2. 确认最终输出为cipher[i]^key[i%16]，从文件0x3020提取51字节密文；不要把复杂key检查错误视为强唯一性约束。
3. 以Thryve{恢复key[0..6]，用末尾}交叉检查key[2]；对剩余9个key位置枚举使同列明文均在候选字符集内的值。
4. 将可读语义作为筛选假设，再通过真实八轮VM确认；原文候选key=4ba317f09c2e886135d47a0fc1563be9。

## 验证标准与结果

作者报告 Thryve{0n3_7h1n9_4b0u7_m3_15_1_h47e_vm_d15p47ch3r5}。需同时验证该key经VM通过且重复XOR还原完整正文；一个字节检查可能接受许多乱码key。

## 限制与易错点

已收录solve.py实际上主要解密并反汇编字节码，并非自动恢复key的完整solver；原文通过语义选择剩余候选，不能宣称字符集约束保证唯一。固定soul_dist路径需调整。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
