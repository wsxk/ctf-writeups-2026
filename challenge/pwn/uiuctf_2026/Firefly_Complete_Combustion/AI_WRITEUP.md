# Firefly_Complete_Combustion — AI 可读解题说明

- 比赛：UIUCTF 2026
- 分类：pwn
- 附件状态（原目录登记）：已下载
- 改写状态：基于本地文字和 solver 的静态分析
- 本次没有执行题目程序、利用脚本或远程交互；文中的地址、原作者结果不代表本次复现记录。

## 目标与漏洞根因

Lua FORLOOP未检验tag，仅改payload的chgivalue造成字符串/表/C函数类型混淆。

## 证据与材料

- [writeups/1_writeup.txt](writeups/1_writeup.txt)

题目来源与采集记录见 [metadata.json](metadata.json)，本地附件见 [attachments](attachments/)。合集只取本题命名的章节；其余题目中的地址和 flag 不适用于本题。

## 利用链与操作顺序

1. 使用同版luac编译后修改三条FORLOOP。
2. 构造任意TString读、Table写并把print指针变为loadfile。
3. 将fclose GOT改fflush，调用loadfile(/flag.txt)后保留解析失败的stdio缓冲。
4. 扫描堆并匹配uiuctf%b{}。

上述步骤存在数据依赖：先确认漏洞产生的原语，再使用前一步的泄漏或状态构造下一步。原 solver 的完整字段布局、收发同步和 payload 字节以证据文件为准。

## 约束、结果与未决问题

必须Lua5.5.0二进制字节码；不是Lua源码层可直接执行loadfile。

## 如何验证

1. 对照原始程序/源码核对这条机制：Lua FORLOOP未检验tag，仅改payload的chgivalue造成字符串/表/C函数类型混淆。
2. 在各步之间记录地址、对象类型、长度、计数器或权限变化；若与原文不符，从第一个差异回查，不能只修改最后一个偏移。
3. 在本题环境检查最后一步的实际返回或文件输出。得到崩溃、可写内存或局部 shell，并不自动等于已取得最终 flag。
4. 未运行的部分保持“待复现”；原文若只有骨架、坐标或单行说明，不把缺失过程写成已经验证。

## AI 接续提示

先读取本文件形成利用链，再按步骤打开证据中的对应函数或代码块。地址常量属于收录的构建；ASLR 泄漏、libc 版本、内核布局、远程协议和完整目标数据须分别核对。多个来源有冲突时保留冲突，不拼接不兼容的路线。
