# Salvage_Protocol — AI 可读解题说明

- 比赛：z0d1ak CTF Qualifiers
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

利用代理VM的长度错配走私两条请求，并借失败AUTH遗留权限读取vault记录。

reclaimd分离保存真实body长度与声明长度，vaultd按声明长度解析多个请求；AUTH在校验token前更新connection_clearance且失败不回滚。

## 证据与输入

- [writeups/1_README.md](writeups/1_README.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 先恢复外层4字节大端帧长度，以及内层action(1)|name_len(2BE)|name|data_len(2BE)|data结构，区分两个长度层。
2. 构造bad AUTH vault/flag及随后GET vault/flag，AUTH所需body长0x400但不必知道前四字节token；错误认证仍写入权限状态。
3. 通过VM0x02选择合法scrap/0，0x11逐字节追加真实走私body，0x10把声明data_len设为0，0x30发送，再0x00停止。
4. vaultd在同一帧/连接解析成GET scrap/0→失败AUTH→受保护GET；不能拆到独立连接，否则clearance不共享。

## 验证标准与结果

原文报告 zdk{sa1VAG3d_thrOugh_7HE_53Am}。本地FLAG_NOT_PROVISIONED仅证明访问受保护读路径，不是真实flag；应记录两种AUTH结果和后续GET结果以验证状态缺陷。

## 限制与易错点

0x20单次替换body限255字节，完整0x400 AUTH不能简单塞一个指令，原代码采用逐字节构造。独立solve.py未收录；二进制硬化弱不是本题利用根因。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
