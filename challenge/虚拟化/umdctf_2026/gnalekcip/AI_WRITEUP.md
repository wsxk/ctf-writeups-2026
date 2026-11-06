# gnalekcip — AI 可读解题说明

- 比赛：UMDCTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

理解共享memo的pickle VM，并核验原作者给出的候选。

BINPERSID递归解析嵌套pickle且共享memo，形成寄存器文件和子程序；原文最终答案依赖题名/部分转录猜测，未提供可独立重做的完整hash逆解。

## 证据与输入

- [writeups/1_README.md](writeups/1_README.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 先静态读取pickelang.py的find_class白名单和persistent_load，不对未知pickle直接反序列化；识别input/add/getitem/pack/unpack调用。
2. 用pickletools静态分解736字节reader、299字节hash和637/707字节比较片段，追踪共享memo状态；原文提取51组(lo,hi)目标，首组(49047,22542)。
3. 还原输入分词及END终止条件。原文同时说逐词、逐字符且示例只有8个词，与51组目标不一致，应以reader真实消费方式核对。
4. 若复现oracle，区分C Unpickler与纯Python实现差异；MemoryError和耗时不能自动判断字符对错。
5. 将题名反转、部分转录与十六进制尾段仅作为候选生成依据，再用全部目标比较及最终Correct验证。

## 验证标准与结果

原文候选 UMDCTF{pick3l_or_elkcIP_wh1cH_0ne_1s_i7_504f4c4c5554414e54}。尾段按作者保留十六进制字面；本次没有验证其满足51组hash。

## 限制与易错点

原文从“无法逆hash”跳到语义拼接答案，缺少关键求解证据；不能把猜谜叙述改写成已证明算法。共享memo大小也应按具体opcode核对，Python pickle并非天然只支持256槽。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
