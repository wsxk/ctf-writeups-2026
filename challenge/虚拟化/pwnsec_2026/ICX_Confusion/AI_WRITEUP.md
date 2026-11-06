# ICX_Confusion — AI 可读解题说明

- 比赛：PwnSec CTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

利用过期View改写Job能力字段，让guest读取并输出/flag。

pack将Note变为Job但保留旧View，导致类型混淆；认证值是可重算的23位算法，攻击者可修改token和manifest并重新封装。

## 证据与输入

- [writeups/1_README.md](writeups/1_README.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 先建立16槽对象地址和View偏移，所有字运算mask=0x7fffff；六位十六进制显示不代表24位。
2. 在pack之前创建View5指向将来的Job头，View6指向附带Note请求区；pack之后确认旧引用仍可编辑新结构。
3. peek泄露d[0..7]，按slot/generation/d4/d5还原seal，选择guest中读flag能力token；修改d0、manifest d3并重新计算d6/d7认证。
4. 使用version=1使run从request[1..]复制可控字段；先以5字段描述符把/flag读入VM缓冲，再改为console-write能力和2字段描述符打印该缓冲。

## 验证标准与结果

原文报告 pwnsec{bd50223d7bac573d}。验证应分开确认Job认证通过、读入缓冲成功、终端输出；输出后服务报告失败不自动否定先前已经输出的字节。

## 限制与易错点

本地仅README，引用的job_auth、完整能力token及工具需从原文代码块/附件恢复，不能替换为24位算术。对象地址0x110461/0x110481等属于特定guest布局。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
