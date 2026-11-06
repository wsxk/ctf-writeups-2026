# garden — AI 可读解题说明

- 比赛：DiceCTF 2026 Quals
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

在封闭堆VM中构造任意读写并完成原挑战控制流劫持。

GC将空引用误当作4字节对象参与压缩，破坏只向低地址移动的假设；逐对象memmove覆盖相邻对象头，可在普通数组和off-heap数组之间制造类型混淆。

## 证据与输入

- [writeups/community/README.md](writeups/community/README.md)
- [writeups/community/solve.py](writeups/community/solve.py)
- [writeups/README.md](writeups/README.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 先区分普通数值数组、引用数组和off-heap数组结构；从未初始化引用数组取null并作为根参与GC，确认本构建是否包含原文描述的mark_reachable差异。
2. 安排相邻数组[a]和[w,x,y,z]，用额外null对象使压缩向右偏4字节，让a覆盖后对象的length/mark_word。
3. 把后对象标为off-heap，使w/x/y/z被解释为data指针和size，得到宿主任意读写；反向转换可将真实off-heap指针当作整数泄露。
4. 申请大off-heap对象取得mmap相关地址，按本地libc布局算基址，再读environ得到栈指针，定位保存返回地址；原文示例environ偏移0x20ad58，栈差-0x160。
5. 因为运行期没有普通交互输入，将泄露、指针运算、ROP构造和退出都编译到同一VM字节码；community/solve.py提供另一解法的具体实现。

## 验证标准与结果

逐阶段验证GC后的头部、读写原语、libc与栈指针，再检查退出后的目标行为。原文同时记录alloc_off_heap大小整数溢出的非预期路线；两条根因不要混写为同一个漏洞。

## 限制与易错点

官方README部分措辞是条件性描述“if mark_reachable is changed”，需核对实际源码而非直接认定所有构建可用。libc和栈偏移是环境相关值。目录的另一garden副本应链接到本条，不重复算题。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
