# redis_cli_0_day — AI 可读解题说明

- 比赛：COMPFEST CTF 2026
- 分类：pwn
- 附件状态（原目录登记）：已下载
- 改写状态：基于本地文字和 solver 的静态分析
- 本次没有执行题目程序、利用脚本或远程交互；文中的地址、原作者结果不代表本次复现记录。

## 目标与漏洞根因

CLUSTER NODES未限制slot索引，形成从node+0x54起向前写固定字节1；两次伪大块重叠最终伪造hiredis析构回调。

## 证据与材料

- [writeups/1_README.md](writeups/1_README.md)

题目来源与采集记录见 [metadata.json](metadata.json)，本地附件见 [attachments](attachments/)。合集只取本题命名的章节；其余题目中的地址和 flag 不适用于本题。

## 利用链与操作顺序

1. 保持首个CLUSTER NODES回复907字节。
2. 用slot21132/21172改F0 ip和flags，37717/71253把两个0x41 chunk size伪为0x141（本地2.42布局）。
3. F0失败释放后由F1的0x130回复重占，泄漏heap并指向unsorted残留泄漏libc。
4. 第二次F2释放、F3回复重占，伪造redisContext的privdata=命令和free_privdata=system。
5. 畸形回复触发redisFree回调，输出经存活socket fd5送出。

上述步骤存在数据依赖：先确认漏洞产生的原语，再使用前一步的泄漏或状态构造下一步。原 solver 的完整字段布局、收发同步和 payload 字节以证据文件为准。

## 约束、结果与未决问题

远端MALLOC=libc且glibc2.43，偏移不同；stdout/stderr重定向使本地日志泄漏链不可直接远用，远端改从DBSIZE获得数据并频率投票找arena。不可把Partial/Full RELRO混淆，本题Full RELRO下不覆盖GOT。

## 如何验证

1. 对照原始程序/源码核对这条机制：CLUSTER NODES未限制slot索引，形成从node+0x54起向前写固定字节1；两次伪大块重叠最终伪造hiredis析构回调。
2. 在各步之间记录地址、对象类型、长度、计数器或权限变化；若与原文不符，从第一个差异回查，不能只修改最后一个偏移。
3. 在本题环境检查最后一步的实际返回或文件输出。得到崩溃、可写内存或局部 shell，并不自动等于已取得最终 flag。
4. 未运行的部分保持“待复现”；原文若只有骨架、坐标或单行说明，不把缺失过程写成已经验证。

## AI 接续提示

先读取本文件形成利用链，再按步骤打开证据中的对应函数或代码块。地址常量属于收录的构建；ASLR 泄漏、libc 版本、内核布局、远程协议和完整目标数据须分别核对。多个来源有冲突时保留冲突，不拼接不兼容的路线。
