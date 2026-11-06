# SU_Chronos_Ring1 — AI 可读解题说明

- 比赛：SUCTF 2026
- 分类：pwn
- 附件状态（原目录登记）：已下载
- 改写状态：基于本地文字和 solver 的静态分析
- 本次没有执行题目程序、利用脚本或远程交互；文中的地址、原作者结果不代表本次复现记录。

## 目标与漏洞根因

同Chronos Ring生命周期错配，Ring1目录另提供可审阅的exp.c。

## 证据与材料

- [writeups/exp/exp.c](writeups/exp/exp.c)
- [writeups/exp/upload.py](writeups/exp/upload.py)
- [writeups/writeup/writeup.md](writeups/writeup/writeup.md)

题目来源与采集记录见 [metadata.json](metadata.json)，本地附件见 [attachments](attachments/)。合集只取本题命名的章节；其余题目中的地址和 flag 不适用于本题。

## 利用链与操作顺序

1. 按exp.c校准KASLR侧信道并通过cookie gate。
2. 建立/tmp/job同步视图再detach保留旧指针。
3. 更新local_ring并commit覆盖只读缓存。
4. 等待root循环执行。

上述步骤存在数据依赖：先确认漏洞产生的原语，再使用前一步的泄漏或状态构造下一步。原 solver 的完整字段布局、收发同步和 payload 字节以证据文件为准。

## 约束、结果与未决问题

两目录正文相同但本目录有C利用与上传器，实际环境偏移仍需对照各自附件。

## 如何验证

1. 对照原始程序/源码核对这条机制：同Chronos Ring生命周期错配，Ring1目录另提供可审阅的exp.c。
2. 在各步之间记录地址、对象类型、长度、计数器或权限变化；若与原文不符，从第一个差异回查，不能只修改最后一个偏移。
3. 在本题环境检查最后一步的实际返回或文件输出。得到崩溃、可写内存或局部 shell，并不自动等于已取得最终 flag。
4. 未运行的部分保持“待复现”；原文若只有骨架、坐标或单行说明，不把缺失过程写成已经验证。

## AI 接续提示

先读取本文件形成利用链，再按步骤打开证据中的对应函数或代码块。地址常量属于收录的构建；ASLR 泄漏、libc 版本、内核布局、远程协议和完整目标数据须分别核对。多个来源有冲突时保留冲突，不拼接不兼容的路线。
