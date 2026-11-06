# Boring_APK — AI 易理解版 Writeup

> 比赛：BKISC CTF 2026｜目录分类：android｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是解开APK资源后反演native的27步图路径状态机，得到27字符输入。Java层主要负责AES-GCM资产解密，实际校验位于arm64 libnative.so。

## 材料与证据

- [writeups/1_writeup.txt](<writeups/1_writeup.txt>)

## 推导与解题步骤

1. 从DEX提取32字节key和AAD=bkisc01，每个asset按nonce12|ciphertext|tag16拆分并decrypt_and_verify。得到table_a16、table_b32、table_c16、path_nodes28、required_moves27及6个checkpoint标签。

2. 定义每步的node及lookup=next_node，检查`rol8(((ch^A)+B+C)&255,3)&7 == required_moves[i]`，其中A按(node+i)&15、B取s4第i%4字节、C按node&31。

3. 初态s4=762509D3、s8=4023CC45、s12=0；按原文更新s4=(s4*83)^mix、s8旋转异或、s12按checkpoint异或，全程u32截断。

4. 在已知BKISC{与末尾}约束下，步13附近做meet-in-the-middle：前向枚举保存(s4,s8,s12)，后向从F9882DBC、FD1A9600、24F218AE逆推。

5. s4逆变换为`old=((new^mix)*0xC9484E2B)&0xffffffff`；异或的逆仍是异或，不是整数减法。s8先反旋转再异或，s12撤销标签。中间状态一致后完整正向验证。

## 结果与验证

原文结果 `BKISC{4nd0rid_m4z3_s0lving}`。本次只独立核算其长度27与83模2^32的逆C9484E2B，未运行native/搜索。

## 复现边界与易错点

README未列资产key全部字节或完整solver，需从APK补取。NDK basic_string ABI、Linux加载器patch属于可选执行方案，不能当作对任意Android so通用的方法。原文“21个free positions”亦有计数疑点：27-6-1=20，须以实际索引边界为准。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
