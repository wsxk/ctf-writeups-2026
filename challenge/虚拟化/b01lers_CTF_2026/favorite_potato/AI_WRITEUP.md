# favorite_potato — AI 可读解题说明

- 比赛：b01lers CTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

根据6502程序执行后的三个8位寄存器值，恢复初始 A、X、Y，完成连续20轮挑战。

程序将10000轮可逆ARX完全展开；识别PHP/PLP包围的栈原语后，可提取常量并从尾到头求逆，无须枚举24位状态。

## 证据与输入

- [writeups/sol/check.py](writeups/sol/check.py)
- [writeups/sol/README.txt](writeups/sol/README.txt)
- [writeups/sol/sol+check.py](writeups/sol/sol%2Bcheck.py)
- [writeups/sol/sol.py](writeups/sol/sol.py)
- [writeups/sol/sol2.py](writeups/sol/sol2.py)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 以9字节测试程序核对寄存器和8位环绕：A+=0x2a、X+=1、Y-=2。真实程序长5820001字节，末尾RTS，每轮582字节。
2. 按PHP至PLP拆出交换、加法、循环右移、异或等9类原语；工具若限制64KiB，应分块反汇编，不得截断整份展开代码。
3. 对单轮按反序撤销：A^=Y^k5；Y=rol(Y,r3)；X^=A^k4；A=rol(A,r2)；Y-=A+k3；Y^=X^k2；X=rol(X,r1)；A-=X+k1。减法均模256。
4. 从第9999轮到第0轮应用逆变换，得到原始三元组；对应 sol.py/sol2.py 是两种解析实现，sol+check.py 以 py65 分100块做正向校验。
5. 在同一挑战交互中逐轮读输出、逆推并答复，共完成20轮；读写格式以脚本和服务源码为准。

## 验证标准与结果

必要验证是任取输入经正向程序得到输出，再逆推恢复原输入，覆盖0/255和所有旋转量；最终20轮均通过才算成功。README没有给出固定flag，最终应以服务返回为准。

## 限制与易错点

作者称 Motorola 6502，但架构名称本身不影响指令语义；必须以实际6502实现为准。code.bin.gz 位于解答目录且仅18字节，不能未经检查就把它当5820001字节真题程序。环境与完整输入文件须按附件核对。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
