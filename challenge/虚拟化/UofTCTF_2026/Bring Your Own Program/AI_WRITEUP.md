# Bring Your Own Program — AI 可读解题说明

- 比赛：UofTCTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

利用属性重排后未失效的inline cache调用受限方法读取题目文件。

GETMETH缓存对象槽位，OPTIMIZE按keyId重排存储却未更新缓存版本；第二次经过同一取方法位置，旧槽位被解释为另一方法，形成能力检查绕过。

## 证据与输入

- [writeups/solve/solve.py](writeups/solve/solve.py)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 读取compile中的字节格式：8寄存器、3常量，c0=caps、c1=double1.0、c2=/flag.txt；整数和浮点常量宽度不可混淆。
2. LDG与GETOWN取得caps.io，在代码偏移13的GETMETH缓存KEY_READ_PUBLIC=10对应函数及receiver。
3. 首次r5为假，执行OPTIMIZE重排caps.io；ADD将r5设为2，再JMP-19回同一GETMETH位置，确保使用相同IC site。
4. 第二次r5为真，JNZ跳至偏移32，CALL使用缓存返回的函数/receiver和/flag.txt参数，再RET返回结果。
5. 以十六进制行提交编译字节；本地源码/附件应核实重排后的旧槽位到底对应哪种特权方法。

## 验证标准与结果

官方solver展示完整payload构造但未硬编码flag。验证应记录OPTIMIZE前后keyId→slot映射、缓存版本是否不变，以及CALL实际目标和返回内容。

## 限制与易错点

“重排未bump”依据solver注释及利用路径静态推断；需与题目VM源码核对后才能确定完整根因。HOST/PORT为本地默认，运行期服务并未验证。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
