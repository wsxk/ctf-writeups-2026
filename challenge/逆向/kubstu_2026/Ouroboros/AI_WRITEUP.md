# Ouroboros：AI 可读解题说明

## 任务与证据范围

- 比赛：KubSTU CTF；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：replacement_source.md 的自哈希链。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

fat Mach-O每个架构各自用__text哈希派生ChaCha20 key。__d3由LCG解出VM并校验activation key，__d5才是真flag密文。

## 按依赖顺序求解

1. 按架构slice提取__text/__d3/__d5，LCG种子0x1337beef解VM。
2. 逆转每字节ROL/add/XOR检查恢复activation key，再严格按原文字节拼接KDF。
3. 以派生key、各slice nonce和counter0解密__d5，交叉核对两架构明文。

## 结果与验证标准

原文activation key KUBSTU-CHR0N0S26；结果KubSTU{k3y3d_by_1ts_0wn___t3xt_s3ct10n}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

activation key为16字节，KDF拼接长度16+32+1+8=57；不能混用两slice代码哈希和密文。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/replacement_source.md](writeups/replacement_source.md)
