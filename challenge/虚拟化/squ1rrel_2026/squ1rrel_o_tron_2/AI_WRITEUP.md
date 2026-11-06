# squ1rrel_o_tron_2 — AI 可读解题说明

- 比赛：squ1rrel CTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

在5秒限时内回答20000个相互依赖的mix挑战。

PDF JavaScript的VM又运行组合子解释器，逐层模拟太慢；抽取等价16位轮函数可将大量解释步骤化简为每输入12轮。

## 证据与输入

- [writeups/1_README.md](writeups/1_README.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 从PDF的JS资源提取31寄存器、65536个32位内存槽和16个opcode，建立慢速oracle；原文测试mix("0000aaaaaaaa")=90aa。
2. 跟踪compile与execute阶段的乘法/XOR/移位，识别固定S-box [8,e,c,7,f,4,5,2,6,a,b,0,3,9,1,d] 与周期key [8e87,4524,b745,9e51]（十六进制）。
3. 等价轮为mul=(i==0?0x3a2a:state)，accum=uint16(ord(input[i])*mul)，state=rol16(sbox4(accum^key[i%4]),5)，共12字符，输出四位十六进制。
4. 批量接收CHALLENGES至END的20000行；prev初始0000，每次input=prev+8字符challenge，按顺序计算并更新prev，再批量发送答案减少往返。

## 验证标准与结果

先对多个输入将高层函数与VM对拍，再验证链式prev和四位补零格式。作者报告 squ1rrel{c0mp1l1ng_t0_c0mb1n4t0rs_1s_s0_r3tr0}，但性能数值仅原报告。

## 限制与易错点

原文一处写每次5.7ms，后又写5700ms，速度倍数矛盾，本文不沿用。独立mix_fast.c/solve.py未收录，README有核心函数但网络端需核对server.py实际计时方式。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
