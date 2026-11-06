# 3in1 — AI 可读解题说明

- 比赛：SekaiCTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

梳理Ladybird→guest提权→QEMU逃逸链，明确可读脚本与不透明二进制边界。

可读JS利用Set.intersection回调中clear/GC引发悬空元素，再伪造对象和ArrayBuffer数据指针获得进程读写；后续两个QEMU阶段以Base64 ELF嵌入，原作者文章缓存仅有简介。

## 证据与输入

- [writeups/author_writeup.txt](writeups/author_writeup.txt)
- [writeups/author_writeup_offline.html](writeups/author_writeup_offline.html)
- [writeups/solution/send.py](writeups/solution/send.py)
- [writeups/solution/solve.js](writeups/solution/solve.js)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 读fakeobj/leak_ptr_try_for：在other.has中清空Set，用0xb0字节分配或WeakMap占位，利用intersection返回旧元素作为NaN-boxed对象/指针泄露。
2. 用MapIterator内存和可控bucket伪造对象，按MAP_ENTRIES_BUCKETS_OFFSET=104与MASK_OFFSET=120定位存储；保持真实对象引用避免被GC回收。
3. 改写victim ArrayBuffer的+64数据指针，通过DataView实现read64/write64，每次访问后恢复原指针。检查0x1122334455667788哨兵，再由vtable、free GOT、environ推导LibJS/libc/栈。
4. 将ROP放入victim backing store，扫描可疑返回地址并安装pop rsp pivot；ROP执行/bin/sh -c，由DROPPER_COMMAND解码本JS的SEKAI_SOLVE_B64区间并运行ELF。
5. 后续LPE/escape必须另做ELF反汇编和对应QEMU源码核验；本地仅可见嵌入payload及其诊断字符串，不能把字符串当完整漏洞证明。

## 验证标准与结果

JS提供SEKAI_PRIMITIVE_TEST开关，可只检验进程读写原语；完整成功需分别证明JS进程控制、guest提权和宿主逃逸，不能将stage1 shell等同全链。此处没有经验证flag。

## 限制与易错点

作者writeup.txt仅620字节，HTML离线副本未含完整三个组件说明；代码含编译后ELF但无对应C源码。所有LibJS/libc偏移和对象布局针对题目构建，随机堆布局可能使重试失败。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
