# Zigerions — AI 可读解题说明

- 比赛：PwnSec CTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

逐层提取真正承载密钥和密文的svchost数据容器并解密。

ELF→PyInstaller PE→VMProtect PE→落地文件；GameBoy ROM中的巨型VM是不可达诱饵，真实结果来自畸形ELF中的AES密钥与48字节密文。

## 证据与输入

- [writeups/1_README.md](writeups/1_README.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 从外层ELF的payload符号切取update.exe，使用节映射将VA换为文件偏移；无需执行外层下载/写入逻辑。
2. 提取PyInstaller的stub，根据marker、LE长度、重复XOR key和整体反转恢复layer2.exe。
3. 原作者通过Wine文件跟踪发现AURA.gb和5624字节svchost；若需重现该步仅在隔离副本观察，当前改写未执行任何落地程序。
4. 检查ROM在0x0af2是RET，验证VM表不可达；转向svchost的key/symbol/data，按原文AES-128-ECB解密48字节并去PKCS#7。

## 验证标准与结果

原文声称平台接受 ctf{U_sh0u1dvebeen_@_g@m3r_0rHighIQ!}，同时称解密正文前缀为psctf，须区分原始明文和平台提交形式。末尾9个0x09只支持该候选解密，不单独构成算法证明。

## 限制与易错点

没有IV只能提示ECB，不能普遍证明ECB；应以解密代码和完整明文确认。引用extract_layers.py/watch.c/solve.py未单独收录，且所需中间落地文件须先核对附件。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
