# RISC_V.：AI 可读解题说明

## 任务与证据范围

- 比赛：KubSTU CTF；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：replacement_source.md 的boot、trap ABI和Feistel。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

原始RV32固件先哈希boot stub生成xorshift流解密二阶段；非法指令trap充当调用/返回ABI。后续RC4生成Feistel轮密钥，最终状态再次驱动RC4解flag。

## 按依赖顺序求解

1. 以boot字节计算种子0xd1b83785，解0xe0后的0x4000字节。
2. 按trap分发表恢复真实函数顺序，以tr4p_d1sp4tch_v1生成轮密钥，逆8轮Feistel。
3. 正向重算四个状态word并小端拼key，解二阶段0x884的39字节密文。

## 结果与验证标准

原文access key RV32-TR4P-G4T3S!；结果KubSTU{tr4ps_4r3_th3_r34l_c0ntr0l_fl0w}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

反汇编器将自定义word标invalid不代表无用数据；它们改变实际控制流。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/replacement_source.md](writeups/replacement_source.md)
