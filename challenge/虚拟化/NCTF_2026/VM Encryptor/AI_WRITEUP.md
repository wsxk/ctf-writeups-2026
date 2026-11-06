# VM Encryptor — AI 可读解题说明

- 比赛：NCTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

从栈VM中识别魔改Base64编码并恢复原始输入。

官方PDF第76–79页给出VM结构、指令枚举和逆算法；校验是24位循环移位/XOR后的Base64，再逐字节异或0x63。

## 证据与输入

- [writeups/NCTF_2026_Official_Writeup.pdf](writeups/NCTF_2026_Official_Writeup.pdf)
- [../../../sources/NCTF_2026_Official_Writeup_text.txt](../../../sources/NCTF_2026_Official_Writeup_text.txt)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 只提取PDF的VM Encryptor节，忽略前面的Hook My Secret和后续Misc。VM有0x10000字节内存和0x1000个32位栈项；反汇编必须按PUSH_BYTE/PUSH_DWORD不同操作数宽度推进PC。
2. 由入口确认0x1000处42字节输入先转为0x102B处56字节编码，再转换至0x1064并与0x109D比较，避免把中间缓冲区当flag。
3. 将第78页TARGET_BYTES全部异或0x63，按标准Base64字符表反查6位值，每4个拼成24位chunk。
4. 对轮移位(5,11,20)倒序执行chunk=ror24(chunk^0x55757D,shift)，最后按高、中、低三个字节恢复明文。

## 验证标准与结果

原文给出 NCTF{1578be15-ad09-4859-9193-5d52585eb485}。正向重做三轮ROL/XOR、Base64与最终XOR，应逐字节等于56字节TARGET_BYTES；再验证原VM成功分支。

## 限制与易错点

PDF提取文本有分页行号、控制字符和断行，不能整段直接复制运行。题目目标数据和官方脚本在PDF中完整给出，本次仅静态转写；不要把邻题的Java脚本误关联本题。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
