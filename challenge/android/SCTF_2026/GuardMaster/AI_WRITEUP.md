# GuardMaster — AI 易理解版 Writeup

> 比赛：SCTF 2026｜目录分类：android｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是从GMX容器恢复hidden DEX，再逆native终态编码和Java的77次64字节状态变换，恢复规范化后的输入。代码混淆不改变每层可逆数据流，但漏一层会产生自洽假解。

## 材料与证据

- [writeups/Writeup/writeup.md](<writeups/Writeup/writeup.md>)

## 推导与解题步骤

1. 从公开classes.dex恢复C0002.m15生成64字节loader key及m22 seed；m14将公开DEX与guard.gmx拼接，C0007.m59搜索GMX1开始解析。

2. 校验header MAC，解metadata与record表；真实DEX由type=-744419327及order_id=1定位。按dispatcher次序WB→SM4-prefix→RC4→XOR→Inflater恢复body，再恢复4096字节front。核验DEX magic、Adler32、SHA1和manifest SHA256。

3. 定位hidden Dispatcher.check：method7、code offset64BB4。记录run/step/pull/commit调用顺序及state字段，JADX无法反编译时以DEX指令和方法索引为证据。

4. 从native目标40800处192字节出发，逆final byte层、stream3、whitebox1、stream2、16轮Feistel、stream1、whitebox0、stream0及初始层，撤8字节扩展取得184字节packet。

5. packet为LE version1、command8、112字节wrapper状态、offset78处最终f8的64字节。逆wrapper并用serializer字段与f8副本交叉核验。

6. 倒序重放77条f8操作；普通m11直接逆，26个m40 wrapper先逆嵌套m11，再逆其前置28轮直接f8修改。漏前置段会使错误模型自洽但不能通过真实forward replay。

7. 恢复64字节输入后按Java NFKC/trim/replace/UTF8规则规范化，确认不改变字节；正向重放同77步与native编码再次比对。

## 结果与验证

原文候选 `SCTF{2^i-BBv#Hk@v,sVk7e+)sApDf452_cRox1iupJhKoRzQy_RLu_TE0-n%gn}`。复杂公式、大表生成及完整Exp保留在原文；至少验证GMX哈希、native192字节回环、Java77步回环。

## 复现边界与易错点

原文建立的是分析别名而非原始符号。native helper调用、状态路径与调度是否输入无关须按原文证据核实；本次仅阅读静态资料，未运行Unicorn/DEX解释器或APK。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
