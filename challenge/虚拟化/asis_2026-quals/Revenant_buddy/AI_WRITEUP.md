# Revenant_buddy — AI 可读解题说明

- 比赛：ASIS CTF Quals 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

提交通过 verifier 的 VM 程序，在不知道随机 capability 的情况下完成 capability 校验。

0xD9 的执行器可复制受保护值，但 verifier 将结果标为 ordinary，造成抽象类型与运行时值不一致。两次类型洗白即可同时提供 capability 和 mix(capability)。

## 证据与输入

- [writeups/1_README.md](writeups/1_README.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 定位 worker 中程序解码和 verifier；输入为至多 64 个四字节字的十六进制串，解码首字必须是 0xefc6ab35。
2. 利用 r0=0、r7=capability，执行 D9 将 r7 复制到 r1；8D 计算 r2=mix(r7)；再次 D9 把 r2 复制到 r3。于是 r1/r3 的值正确而类型均为普通。
3. 依次使用解码字 efc6ab35、000239d9、00003a8d、000213d9、0000199e、000000dc；9E 校验 r1/r3，DC 在成功后结束并读取 flag。
4. 从文件偏移 0x93A60、0x93B60 提取混淆表，按 raw=ror32(decoded^0x7824F328,(i%29)+1)^mask[i]^xor_table[i] 编码，再封装 RUN 协议。

## 验证标准与结果

原文给出的编码串为 4285cfe9c40257076ac2e0b0dafabec8ad3e5f973bcb81d3，报告返回 OK ASIS{8bf2fd2a3f7eecec5f5fab1861e51c579975ba45}。验证重点是每条指令的运行值和 verifier 类型同时跟踪，不能仅验证 payload 长度。

## 限制与易错点

混淆表偏移和编码串依赖 worker 构建；新进程的随机秘密无须猜测，因为程序直接引用它。原文 solve.py 未作为单独文件收录，网络结果仅为作者报告。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
