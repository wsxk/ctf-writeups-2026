# parallax — AI 可读解题说明

- 比赛：Thryve CTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

解出动态opcode映射VM的全部字符约束。

phase在每条指令后随状态变化，错误占位符会使后续字节被错误解码；逐条满足三字符断言并从头重放比一次性反汇编可靠。

## 证据与输入

- [writeups/README.md](writeups/README.md)
- [writeups/solve.py](writeups/solve.py)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 用初始64位state=0xdd44d5bae067208d的xorshift解密0x20c0处0x2c7c字节；核对完整性0x60b315e5是在最后一次乘法之前的值。
2. 读取0x4ea0四份opcode映射与0x4d40的S-box；每步按当前phase解码并按照实际PC/r0/r3更新phase，模拟正常TracerPid=0路径。
3. 遇到第一个失败ASSERT时，抽取13指令模板的三输入位置与常量；逆MIX的右移XOR和奇数乘法，再撤销末尾加法。
4. 预计算第三字符乘积表，枚举前两字符（可打印最多95²），匹配第三字符；固定已知Thryve{和}以缩小候选。
5. 将新字符填回并从头重跑，直到181条断言全部通过且VM无错误，再交原程序验证。

## 验证标准与结果

作者报告 Thryve{Man_Am_1_n0t_th2_b2st_auth0r?_NotSaad}。strings中的static_strings_are_a_trap等为诱饵，不能作为结果。对拍重点是每次phase与取指边界，给出候选为45字节，与长度条件一致。

## 限制与易错点

本地完整solve.py读取当前目录parallax；修改路径即可定位附件，但本次未运行。若某三元组多解应回溯，不能无条件取第一个后仍声称唯一。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
