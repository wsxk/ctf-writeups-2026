# SU_West — AI 可读解题说明

- 比赛：SUCTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

按实际顺序求81层输入并恢复40字节flag缓冲。

NOR VM是模板化的ARX约束载体，每轮64位输入经Feistel和组合器映射到该层target；层间s0和flag解密状态相连，不能把81层独立乱序求解。

## 证据与输入

- [writeups/writeup/writeup.md](writeups/writeup/writeup.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 提取ORDER、TARGETS及81份表常量，按constants.txt与原文TableObj的字节/字字段布局读取；所有集合长度应为81。
2. 第rnd轮选择layer=ORDER[rnd]，为x建立64位BitVec并加入原文MIN_INPUT/MAX_INPUT无符号范围。
3. 按sub_12480_sym→sub_12630_sym→sub_12940_sym计算并约束等于TARGETS[layer]，只用对应层的常量和当前s0。
4. 求解后以整数版本重算v5/v8/v9/v18，用sub_12c00_i更新flag，再用sub_12ca0_i更新s0，进入下一轮；旋转及截断必须一致。
5. 输出81个输入和最后40字节flag，使用每轮target回代定位最早差异。

## 验证标准与结果

原文结果 SUCTF{y0u_h4v3_0v3rc0m3_81_d1ff1cu1t135}。验证必须81层全部SAT且整数回算一致，不可仅最后字符串可打印；如果某层有多个模型，还需确认其后续状态能成功。

## 限制与易错点

原文exp内EMBEDDED_TABLES等常量需要与constants.txt配套，不要把省略/外部表当默认空值。s0、seed flag buffer和输入范围均为题目参数，本次未运行Z3。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
