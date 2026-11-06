# Oldsvr — AI 可读解题说明

- 比赛：第十届“强网杯”全国网络安全挑战赛·线上赛
- 分类：pwn
- 附件状态（原目录登记）：缺失
- 改写状态：基于本地文字和 solver 的静态分析
- 本次没有执行题目程序、利用脚本或远程交互；文中的地址、原作者结果不代表本次复现记录。

## 目标与漏洞根因

MIPS64大端MQTT的长度截断、news UAF和16位广播分配溢出组合，劫持entry表取得任意写。

## 证据与材料

- [writeups/chapter.txt](writeups/chapter.txt)
- [writeups/Lufer_full_writeup.html](writeups/Lufer_full_writeup.html)

题目来源与采集记录见 [metadata.json](metadata.json)，本地附件见 [attachments](attachments/)。合集只取本题命名的章节；其余题目中的地址和 flag 不适用于本题。

## 利用链与操作顺序

1. 单字节Q通过strncmp长度认证。
2. news回声泄漏heap，按原环境heap-0x22000求PIE。
3. payload_len65520使分配截断为2字节却复制64KiB，伪smallbin双pop覆盖entry。
4. 伪chunk释放回显泄漏uClibc，改__libc_free GOT为system并grow含/bin/sh的缓冲。

上述步骤存在数据依赖：先确认漏洞产生的原语，再使用前一步的泄漏或状态构造下一步。原 solver 的完整字段布局、收发同步和 payload 字节以证据文件为准。

## 约束、结果与未决问题

大端与uClibc1.0.32 dlmalloc，不使用glibc safe-linking；远程堆较模拟器偏0x70，栈大read路径受分段限制被弃用。

## 如何验证

1. 对照原始程序/源码核对这条机制：MIPS64大端MQTT的长度截断、news UAF和16位广播分配溢出组合，劫持entry表取得任意写。
2. 在各步之间记录地址、对象类型、长度、计数器或权限变化；若与原文不符，从第一个差异回查，不能只修改最后一个偏移。
3. 在本题环境检查最后一步的实际返回或文件输出。得到崩溃、可写内存或局部 shell，并不自动等于已取得最终 flag。
4. 未运行的部分保持“待复现”；原文若只有骨架、坐标或单行说明，不把缺失过程写成已经验证。

## AI 接续提示

先读取本文件形成利用链，再按步骤打开证据中的对应函数或代码块。地址常量属于收录的构建；ASLR 泄漏、libc 版本、内核布局、远程协议和完整目标数据须分别核对。多个来源有冲突时保留冲突，不拼接不兼容的路线。
