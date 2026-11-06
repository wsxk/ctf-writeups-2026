# SU_Chronos_Ring — AI 可读解题说明

- 比赛：SUCTF 2026
- 分类：pwn
- 附件状态（原目录登记）：已下载
- 改写状态：基于本地文字和 solver 的静态分析
- 本次没有执行题目程序、利用脚本或远程交互；文中的地址、原作者结果不代表本次复现记录。

## 目标与漏洞根因

DETACH_FILE切换为LOCAL但不清sync_view，COMMIT_SYNC仍写原只读文件page cache。

## 证据与材料

- [writeups/writeup/writeup.md](writeups/writeup/writeup.md)

题目来源与采集记录见 [metadata.json](metadata.json)，本地附件见 [attachments](attachments/)。合集只取本题命名的章节；其余题目中的地址和 flag 不适用于本题。

## 利用链与操作顺序

1. 用AVX masked-load时序候选扫描±32MiB并以2MiB步长试基址，计算kfree相关cookie。
2. 注册缓冲并以只读方式绑定/tmp/job，ENABLE_SYNC后DETACH。
3. UPDATE本地内容再COMMIT写入旧page cache。
4. 等待root任务执行并读取输出。

上述步骤存在数据依赖：先确认漏洞产生的原语，再使用前一步的泄漏或状态构造下一步。原 solver 的完整字段布局、收发同步和 payload 字节以证据文件为准。

## 约束、结果与未决问题

cookie=rol64((kfree>>21) XOR 0x9e3779b97f4a7c15,17) XOR session_idx；时序候选不是直接_text地址。

## 如何验证

1. 对照原始程序/源码核对这条机制：DETACH_FILE切换为LOCAL但不清sync_view，COMMIT_SYNC仍写原只读文件page cache。
2. 在各步之间记录地址、对象类型、长度、计数器或权限变化；若与原文不符，从第一个差异回查，不能只修改最后一个偏移。
3. 在本题环境检查最后一步的实际返回或文件输出。得到崩溃、可写内存或局部 shell，并不自动等于已取得最终 flag。
4. 未运行的部分保持“待复现”；原文若只有骨架、坐标或单行说明，不把缺失过程写成已经验证。

## AI 接续提示

先读取本文件形成利用链，再按步骤打开证据中的对应函数或代码块。地址常量属于收录的构建；ASLR 泄漏、libc 版本、内核布局、远程协议和完整目标数据须分别核对。多个来源有冲突时保留冲突，不拼接不兼容的路线。
