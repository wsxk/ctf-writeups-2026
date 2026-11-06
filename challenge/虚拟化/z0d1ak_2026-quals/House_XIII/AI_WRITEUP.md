# House_XIII — AI 可读解题说明

- 比赛：z0d1ak CTF Qualifiers
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

通过堆对象类型混淆与比较oracle到达预置fd13的sendfile回调。

两类对象同为0x180大小，转换释放重分配却保留旧槽；VM可向后读头部，旧类型写入口可修改新类型callback字段。随机secret又被<比较暴露。

## 证据与输入

- [writeups/1_README.md](writeups/1_README.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. STARGMTR数据区在+0x60；opcode0x19加有符号0xa0(-0x60)退至对象头，0x2d逐字节读出generation、heap地址及PIE+0x2060指针。
2. choice5转换为ORBITAL后确认stargmtr和orbital槽别名；choice2只查非NULL，仍可从+0x60写入新类型敏感字段。
3. 通过choice6的<与>=响应对64位secret作最多64次二分，在同一进程保留泄露与secret。
4. 将目标设为回调表项PIE+0x4cf0，encoded=rol64(slot^secret,17)，link=generation^(generation+1)，用原文credential函数重算+0x68校验。
5. 写入encoded/credential及fd=13、gate=13后触发choice7，走既有sendfile(1,13,...)路径；不选择打印诱饵的PIE+0x4cf8表项。

## 验证标准与结果

作者报告 zdk{0p3r470r_53ss10n_4cc3p73d}。本地应在fd13预置自选哨兵文件，输出哨兵才能证明是真实读取而非静态诱饵。

## 限制与易错点

完整credential算式见原文代码，独立solve.py未收录。fd13依赖launcher预打开；对象偏移与glibc同尺寸复用须匹配本构建，secret跨进程不可复用。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
