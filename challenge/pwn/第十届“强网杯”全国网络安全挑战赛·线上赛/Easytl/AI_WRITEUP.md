# Easytl — AI 可读解题说明

- 比赛：第十届“强网杯”全国网络安全挑战赛·线上赛
- 分类：pwn
- 附件状态（原目录登记）：缺失
- 改写状态：基于本地文字和 solver 的静态分析
- 本次没有执行题目程序、利用脚本或远程交互；文中的地址、原作者结果不代表本次复现记录。

## 目标与漏洞根因

OpenSSL三个回调共用指针/长度，PSK数据指针与SNI长度混搭导致日志栈溢出。

## 证据与材料

- [writeups/chapter.txt](writeups/chapter.txt)
- [writeups/Lufer_full_writeup.html](writeups/Lufer_full_writeup.html)

题目来源与采集记录见 [metadata.json](metadata.json)，本地附件见 [attachments](attachments/)。合集只取本题命名的章节；其余题目中的地址和 flag 不适用于本题。

## 利用链与操作顺序

1. 构造magic加NUL但identity_len很长的PSK identity，并用SNI设置g_len68。
2. 触发alert调用log_error，memcpy把PSK内容按SNI长度写到0x50栈缓冲。
3. 利用fork子进程共享canary及明文error侧信道恢复保护值。
4. 按原文TLS包和ROP完成读取。

上述步骤存在数据依赖：先确认漏洞产生的原语，再使用前一步的泄漏或状态构造下一步。原 solver 的完整字段布局、收发同步和 payload 字节以证据文件为准。

## 约束、结果与未决问题

SNI最大255且不能含NUL；PSK strlen只约束前33字节，不等于identity_len；fork父进程重启会改变canary。

## 如何验证

1. 对照原始程序/源码核对这条机制：OpenSSL三个回调共用指针/长度，PSK数据指针与SNI长度混搭导致日志栈溢出。
2. 在各步之间记录地址、对象类型、长度、计数器或权限变化；若与原文不符，从第一个差异回查，不能只修改最后一个偏移。
3. 在本题环境检查最后一步的实际返回或文件输出。得到崩溃、可写内存或局部 shell，并不自动等于已取得最终 flag。
4. 未运行的部分保持“待复现”；原文若只有骨架、坐标或单行说明，不把缺失过程写成已经验证。

## AI 接续提示

先读取本文件形成利用链，再按步骤打开证据中的对应函数或代码块。地址常量属于收录的构建；ASLR 泄漏、libc 版本、内核布局、远程协议和完整目标数据须分别核对。多个来源有冲突时保留冲突，不拼接不兼容的路线。
