# back_and_forth — AI 易理解版 Writeup

> 比赛：BYUCTF 2026｜目录分类：android｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是拼合Java、SQLite、JNI和Rust/Wasm各层的局部校验。不同check约束不同输入片段，应先建立索引表，再按容易的局部约束求解。

## 材料与证据

- [writeups/brute.py](<writeups/brute.py>)
- [writeups/README.md](<writeups/README.md>)

## 推导与解题步骤

1. 从资源s确定byuctf{前缀及Java下划线位置。读取assets/mydb.sqlite恢复4ndr01d。

2. Native finalize一部分通过C++ MT19937生成值、调用Java Random再返回做整除，恢复styl3s；复制两种PRNG时需精确处理有符号int与种子扩展。

3. Finalize另一部分对相邻字符求和并与常量比较，可逆递推出thr0ugh。

4. 沿WasmRunner资源bg定位Wasm check3；将flag偏移7的8字节视作8×8 bit矩阵，目标298727A55BFEB500对应转置结果，逆转置得j0mp1n6_。

5. check1在汇编里实际调用SHA256::update(input+0x1f,4)，只哈希4字节；枚举该片段并比对抽样摘要字节，原文brute.py得到c0d3。

6. 按槽位拼合全部片段，再运行各层约束验证；不要把check1当整个flag的SHA256原像题。

## 结果与验证

原文候选 `byuctf{j0mp1n6_thr0ugh_4ndr01d_c0d3_styl3s_28f6}`。

## 复现边界与易错点

作者明确承认尾部JNI比较长度及strcmp方向有设计错误，28f6属于预期值，不应宣称当前程序唯一强制该后缀。本地只提供brute.py，文中提到的gen_bytes.cpp和Main.java未在writeups目录中。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
