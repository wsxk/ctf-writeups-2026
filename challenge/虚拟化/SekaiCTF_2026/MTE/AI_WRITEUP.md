# MTE — AI 可读解题说明

- 比赛：SekaiCTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

通过Binder身份、MTE/PAC门控和驱动UAF获得内核读，再读页缓存flag。

核心原语不是任意写，而是在保留24字节canary的kmalloc-96对象+0x40写固定值2；以unix_vertex.scc_index为目标诱发AF_UNIX GC和悬空oob_skb，升级为任意地址单字节读取。

## 证据与输入

- [writeups/community_writeup.md](writeups/community_writeup.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 在exec可信/bin/client前打开Binder并用SCM_RIGHTS保留fd，借opening task身份获得真实mte_driver fd；CLONE_VM sleeper保持映射。
2. 从泄露的16个MTE tag恢复小PRNG种子并生成0x100个tag；PAC因qemu_pauth.patch固定部分参数而可重放，分别通过验证IOCTL。
3. IOCTL_FREE制造悬空对象，安排unix_vertex重占且+0x48至+0x5f canary不变；IOCTL_CHECK写+0x40=2，使GC误清活socket并留下oob_skb。
4. 用pipe页占回sk_buff，伪造len=1和head/data=target，经recv(MSG_OOB|MSG_PEEK)读取；先读linux_banner的L，再改偏移读i定位命中的pipe。
5. 依据原文页缓存遍历链定位/root/flag.txt的page，将struct page转换direct-map地址逐字节读取，无须root shell。

## 验证标准与结果

验证分层记录driver fd、MTE/PAC门控、悬空skb读L→i和最终页内容。community_writeup.md含作者结果；本地solution/solver为已编译二进制，本次未执行。

## 限制与易错点

原文引用solve.c/qemu_pauth.patch，但本题writeups仅社区说明和二进制solver，完整源码需从附件核对。QEMU补丁、内核布局、slab回收策略和kmsg泄露可用性都是必要前提，不能推广到默认MTE/PAC环境。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
